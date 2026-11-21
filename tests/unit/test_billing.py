from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timedelta

import pytest

from core.billing import (
    StripeBillingClient,
    StripeWebhookError,
    account_billing_summary,
    has_service_access,
    new_account_billing,
)

pytestmark = [pytest.mark.unit, pytest.mark.user]


def test_new_accounts_receive_a_30_day_trial():
    billing = new_account_billing("2026-10-07 12:00:00")
    assert billing == {
        "trial_ends_at": "2026-11-06 12:00:00",
        "subscription_status": "trialing",
        "stripe_customer_id": "",
        "stripe_subscription_id": "",
        "subscription_plan": "",
        "stripe_price_id": "",
        "billing_livemode": False,
        "billing_grace_ends_at": "",
    }


def test_access_states_preserve_legacy_accounts_and_enforce_expiry():
    now = datetime(2026, 10, 7, 12, 0, 0)
    assert has_service_access({}, now=now) is True
    assert has_service_access({"subscription_status": "comped"}, now=now) is True
    assert has_service_access({"subscription_status": "active"}, now=now) is True
    assert (
        has_service_access(
            {"subscription_status": "trialing", "trial_ends_at": "2026-10-08 12:00:00"},
            now=now,
        )
        is True
    )
    assert (
        has_service_access(
            {"subscription_status": "trialing", "trial_ends_at": "2026-10-07 11:59:59"},
            now=now,
        )
        is False
    )
    assert (
        has_service_access(
            {
                "subscription_status": "past_due",
                "billing_grace_ends_at": "2026-10-08 12:00:00",
            },
            now=now,
        )
        is True
    )
    assert has_service_access({"subscription_status": "canceled"}, now=now) is False


def test_account_summary_reports_rounded_up_trial_days_without_ids():
    summary = account_billing_summary(
        {
            "subscription_status": "trialing",
            "trial_ends_at": "2026-10-08 12:00:01",
            "stripe_customer_id": "cus_test",
        },
        configured=True,
        now=datetime(2026, 10, 7, 12, 0, 0),
    )
    assert summary["trial_days_remaining"] == 2
    assert summary["customer_exists"] is True
    assert summary["checkout_available"] is True
    assert summary["checkout_defers_charge"] is False
    assert "stripe_customer_id" not in summary


def test_account_summary_reports_when_checkout_preserves_the_trial():
    summary = account_billing_summary(
        {
            "subscription_status": "trialing",
            "trial_ends_at": "2026-10-10 12:00:00",
        },
        configured=True,
        now=datetime(2026, 10, 7, 12, 0, 0),
    )
    assert summary["checkout_defers_charge"] is True


def _signature(secret: str, timestamp: int, payload: bytes) -> str:
    digest = hmac.new(
        secret.encode(), str(timestamp).encode() + b"." + payload, hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={digest}"


def test_stripe_webhook_verification_uses_raw_body_signature_and_tolerance():
    payload = json.dumps({"id": "evt_1", "type": "invoice.paid"}).encode()
    client = StripeBillingClient(webhook_secret="whsec_test", wall_clock=lambda: 1000)
    event = client.verify_webhook(payload, _signature("whsec_test", 1000, payload))
    assert event["id"] == "evt_1"
    with pytest.raises(StripeWebhookError):
        client.verify_webhook(payload + b" ", _signature("whsec_test", 1000, payload))
    with pytest.raises(StripeWebhookError):
        client.verify_webhook(payload, _signature("whsec_test", 1, payload))


@pytest.mark.asyncio
@pytest.mark.parametrize("plan,expected_price", [("discord", "price_monthly"), ("phone", "price_phone")])
async def test_checkout_reuses_customer_and_carries_trial_and_mhm_identity(monkeypatch, plan, expected_price):
    captured = {}
    client = StripeBillingClient(
        secret_key="sk_test",
        price_ids={"discord": "price_monthly", "phone": "price_phone"},
        wall_clock=lambda: 1_000_000,
    )

    async def fake_post(path, fields, *, idempotency_key=None):
        captured.update(path=path, fields=dict(fields), key=idempotency_key)
        return {"url": "https://checkout.stripe.com/test"}

    monkeypatch.setattr(client, "_post", fake_post)
    result = await client.create_checkout_session(
        user_id="user-1",
        plan=plan,
        email="person@example.com",
        customer_id="cus_1",
        success_url="https://mhm.example/app.html?billing=success",
        cancel_url="https://mhm.example/app.html?billing=cancelled",
        trial_end=datetime.fromtimestamp(1_000_000) + timedelta(days=10),
    )
    assert result["url"].startswith("https://checkout.stripe.com/")
    assert captured["path"] == "/v1/checkout/sessions"
    assert captured["fields"]["mode"] == "subscription"
    assert captured["fields"]["line_items[0][price]"] == expected_price
    assert captured["fields"]["metadata[mhm_plan]"] == plan
    assert f"-{plan}-" in captured["key"]
    assert captured["fields"]["customer"] == "cus_1"
    assert captured["fields"]["client_reference_id"] == "user-1"
    assert captured["fields"]["subscription_data[metadata][mhm_user_id]"] == "user-1"
    assert "subscription_data[trial_end]" in captured["fields"]


@pytest.mark.parametrize("price,expected", [("price_discord", "discord"), ("price_phone", "phone"), ("price_unknown", "")])
def test_plan_comes_from_subscription_price_not_requested_metadata(monkeypatch, price, expected):
    from core import config
    from core.billing import subscription_price_plan

    monkeypatch.setattr(config, "STRIPE_DISCORD_PRICE_ID", "price_discord")
    monkeypatch.setattr(config, "STRIPE_PHONE_PRICE_ID", "price_phone")
    subscription = {"metadata": {"mhm_plan": "phone"}, "items": {"data": [
        {"price": {"id": price}, "quantity": 1},
    ]}}
    assert subscription_price_plan(subscription) == (expected, price)
    subscription["items"]["data"].append({"price": {"id": "price_phone"}})
    assert subscription_price_plan(subscription) == ("", "")


@pytest.mark.asyncio
async def test_subscription_retrieval_uses_an_encoded_stripe_resource_path(monkeypatch):
    captured = {}
    client = StripeBillingClient(secret_key="sk_test")

    async def fake_get(path):
        captured["path"] = path
        return {"id": "sub_1", "status": "active"}

    monkeypatch.setattr(client, "_get", fake_get)
    subscription = await client.retrieve_subscription("sub_1")
    assert subscription["status"] == "active"
    assert captured["path"] == "/v1/subscriptions/sub_1"


@pytest.mark.asyncio
async def test_portal_session_uses_the_mhm_two_plan_configuration(monkeypatch):
    captured = {}
    client = StripeBillingClient(secret_key="sk_test", portal_configuration_id="bpc_mhm_tiers")

    async def fake_post(path, fields):
        captured.update(path=path, fields=dict(fields))
        return {"url": "https://billing.stripe.test/session"}

    monkeypatch.setattr(client, "_post", fake_post)
    await client.create_portal_session(customer_id="cus_1", return_url="https://mhm.example/app.html")
    assert captured["fields"]["configuration"] == "bpc_mhm_tiers"


@pytest.mark.parametrize("key, expected", [("sk_test_example", True), ("rk_test_example", True), ("sk_live_example", False), ("", False)])
def test_billing_mode_detection(key, expected):
    assert StripeBillingClient(secret_key=key).test_mode is expected


def test_billing_mode_failure_is_reported_and_not_misclassified(monkeypatch):
    from unittest.mock import Mock
    from core.error_handling import error_handler

    report = Mock(return_value=False)
    monkeypatch.setattr(error_handler, "handle_error", report)
    client = StripeBillingClient()
    monkeypatch.setattr(client, "secret_key", None)
    with pytest.raises(AttributeError):
        _ = client.test_mode
    report.assert_called_once()
