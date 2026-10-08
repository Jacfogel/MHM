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
    assert "stripe_customer_id" not in summary


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
async def test_checkout_reuses_customer_and_carries_trial_and_mhm_identity(monkeypatch):
    captured = {}
    client = StripeBillingClient(
        secret_key="sk_test",
        price_id="price_monthly",
        wall_clock=lambda: 1_000_000,
    )

    async def fake_post(path, fields, *, idempotency_key=None):
        captured.update(path=path, fields=dict(fields), key=idempotency_key)
        return {"url": "https://checkout.stripe.com/test"}

    monkeypatch.setattr(client, "_post", fake_post)
    result = await client.create_checkout_session(
        user_id="user-1",
        email="person@example.com",
        customer_id="cus_1",
        success_url="https://mhm.example/app.html?billing=success",
        cancel_url="https://mhm.example/app.html?billing=cancelled",
        trial_end=datetime.fromtimestamp(1_000_000) + timedelta(days=10),
    )
    assert result["url"].startswith("https://checkout.stripe.com/")
    assert captured["path"] == "/v1/checkout/sessions"
    assert captured["fields"]["mode"] == "subscription"
    assert captured["fields"]["customer"] == "cus_1"
    assert captured["fields"]["client_reference_id"] == "user-1"
    assert captured["fields"]["subscription_data[metadata][mhm_user_id]"] == "user-1"
    assert "subscription_data[trial_end]" in captured["fields"]
