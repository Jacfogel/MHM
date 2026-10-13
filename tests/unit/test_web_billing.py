from __future__ import annotations

import hashlib
import hmac
import json
from contextlib import asynccontextmanager

import pytest
from aiohttp import CookieJar
from aiohttp.test_utils import TestClient, TestServer

from core.billing import StripeAPIError, StripeBillingClient
from core.web_account_service import create_web_app

pytestmark = [pytest.mark.unit, pytest.mark.user, pytest.mark.asyncio]
ORIGIN = "http://localhost:8080"


class Accounts:
    def __init__(self):
        self.users = {
            "trial-user": {
                "email": "trial@example.com",
                "account_status": "active",
                "timezone": "America/Regina",
                "subscription_status": "trialing",
                "trial_ends_at": "2099-11-06 12:00:00",
                "stripe_customer_id": "",
                "stripe_subscription_id": "",
                "billing_grace_ends_at": "",
            }
        }

    def by_email(self, email):
        return next(
            (
                (uid, account)
                for uid, account in self.users.items()
                if account["email"] == email
            ),
            None,
        )

    def get(self, uid):
        return self.users.get(uid, {})

    def documents(self, uid):
        return {"account": self.users[uid], "context": {"preferred_name": "Trial"}}

    def update_billing(self, uid, updates):
        self.users[uid].update(updates)
        return True

    def by_billing_reference(self, customer_id="", subscription_id=""):
        return next(
            (
                (uid, account)
                for uid, account in self.users.items()
                if (customer_id and account.get("stripe_customer_id") == customer_id)
                or (
                    subscription_id
                    and account.get("stripe_subscription_id") == subscription_id
                )
            ),
            None,
        )


class Billing:
    def __init__(self):
        self.checkout = None
        self.portal = None
        self.subscriptions = {
            "sub_1": {
                "id": "sub_1",
                "customer": "cus_1",
                "status": "active",
                "metadata": {"mhm_user_id": "trial-user"},
            }
        }
        self.verifier = StripeBillingClient(
            webhook_secret="whsec_test", wall_clock=lambda: 1000
        )

    def checkout_configured(self):
        return True

    async def create_checkout_session(self, **kwargs):
        self.checkout = kwargs
        return {"url": "https://checkout.stripe.com/c/pay/test"}

    async def create_portal_session(self, **kwargs):
        self.portal = kwargs
        return {"url": "https://billing.stripe.com/p/session/test"}

    async def retrieve_subscription(self, subscription_id):
        return dict(self.subscriptions[subscription_id])

    def verify_webhook(self, payload, signature):
        return self.verifier.verify_webhook(payload, signature)


@asynccontextmanager
async def web_client(app):
    server = TestServer(app)
    await server.start_server(shutdown_timeout=1)
    client = TestClient(server, cookie_jar=CookieJar(unsafe=True))
    try:
        await client.start_server()
        yield client
    finally:
        await client.close()


async def signed_in_client(accounts, billing):
    sent = []
    app = create_web_app(
        accounts=accounts,
        billing=billing,
        mailer=lambda email, code: sent.append((email, code)),
        origin=ORIGIN,
        proxy_secret="",
    )
    context = web_client(app)
    client = await context.__aenter__()
    response = await client.post(
        "/api/auth/request-code",
        json={
            "email": "trial@example.com",
            "mode": "login",
            "timezone": "America/Regina",
        },
        headers={"Origin": ORIGIN},
    )
    challenge = (await response.json())["challenge"]
    await client.post(
        "/api/auth/verify",
        json={"challenge": challenge, "code": sent[-1][1]},
        headers={"Origin": ORIGIN},
    )
    return context, client


async def test_signed_in_trial_can_open_checkout_and_sees_safe_billing_summary():
    accounts, billing = Accounts(), Billing()
    context, client = await signed_in_client(accounts, billing)
    try:
        account = await (await client.get("/api/account")).json()
        assert account["billing"]["status"] == "trialing"
        assert "stripe_customer_id" not in account["billing"]
        response = await client.post(
            "/api/billing/checkout", json={}, headers={"Origin": ORIGIN}
        )
        assert response.status == 200
        assert (await response.json())["url"].startswith("https://checkout.stripe.com/")
        assert billing.checkout is not None
        assert billing.checkout["user_id"] == "trial-user"
        assert billing.checkout["email"] == "trial@example.com"
    finally:
        await context.__aexit__(None, None, None)


async def test_subscribed_account_can_open_customer_portal():
    accounts, billing = Accounts(), Billing()
    accounts.users["trial-user"].update(
        {
            "subscription_status": "active",
            "stripe_customer_id": "cus_1",
            "stripe_subscription_id": "sub_1",
        }
    )
    context, client = await signed_in_client(accounts, billing)
    try:
        response = await client.post(
            "/api/billing/portal", json={}, headers={"Origin": ORIGIN}
        )
        assert response.status == 200
        assert (await response.json())["url"].startswith("https://billing.stripe.com/")
        assert billing.portal is not None
        assert billing.portal["customer_id"] == "cus_1"
    finally:
        await context.__aexit__(None, None, None)


async def test_billing_failures_explain_unchanged_state_and_recovery():
    accounts, billing = Accounts(), Billing()
    context, client = await signed_in_client(accounts, billing)
    try:
        async def fail_checkout(**_kwargs):
            raise StripeAPIError("private checkout diagnostic")

        billing.create_checkout_session = fail_checkout
        checkout = await client.post(
            "/api/billing/checkout", json={}, headers={"Origin": ORIGIN}
        )
        assert checkout.status == 503
        checkout_message = (await checkout.json())["error"]
        assert checkout_message == (
            "Secure checkout is temporarily unavailable. Your current access has not "
            "changed. Please wait a moment and try again."
        )
        assert "private checkout diagnostic" not in checkout_message

        accounts.users["trial-user"].update(
            {
                "subscription_status": "active",
                "stripe_customer_id": "cus_1",
                "stripe_subscription_id": "sub_1",
            }
        )

        async def fail_portal(**_kwargs):
            raise StripeAPIError("private portal diagnostic")

        billing.create_portal_session = fail_portal
        portal = await client.post(
            "/api/billing/portal", json={}, headers={"Origin": ORIGIN}
        )
        assert portal.status == 503
        portal_message = (await portal.json())["error"]
        assert portal_message == (
            "Billing management is temporarily unavailable. Your subscription has "
            "not changed. Please wait a moment and try again."
        )
        assert "private portal diagnostic" not in portal_message
    finally:
        await context.__aexit__(None, None, None)


def signed_payload(event):
    payload = json.dumps(event, separators=(",", ":")).encode()
    digest = hmac.new(b"whsec_test", b"1000." + payload, hashlib.sha256).hexdigest()
    return payload, f"t=1000,v1={digest}"


async def test_signed_webhooks_reconcile_current_state_and_ignore_replays():
    accounts, billing = Accounts(), Billing()
    app = create_web_app(
        accounts=accounts,
        billing=billing,
        mailer=lambda _email, _code: None,
        origin=ORIGIN,
        proxy_secret="",
    )
    async with web_client(app) as client:
        completed, signature = signed_payload(
            {
                "id": "evt_checkout",
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "client_reference_id": "trial-user",
                        "customer": "cus_1",
                        "subscription": "sub_1",
                        "payment_status": "paid",
                    }
                },
            }
        )
        response = await client.post(
            "/api/billing/webhook",
            data=completed,
            headers={"Content-Type": "application/json", "Stripe-Signature": signature},
        )
        assert response.status == 200
        assert accounts.users["trial-user"]["subscription_status"] == "active"
        assert accounts.users["trial-user"]["stripe_customer_id"] == "cus_1"
        assert accounts.users["trial-user"]["billing_processed_event_ids"] == [
            "evt_checkout"
        ]

        duplicate = await client.post(
            "/api/billing/webhook",
            data=completed,
            headers={"Content-Type": "application/json", "Stripe-Signature": signature},
        )
        assert duplicate.status == 200
        assert (await duplicate.json())["duplicate"] is True

        billing.subscriptions["sub_1"]["status"] = "past_due"

        failed, signature = signed_payload(
            {
                "id": "evt_failed",
                "type": "invoice.payment_failed",
                "data": {"object": {"customer": "cus_1", "subscription": "sub_1"}},
            }
        )
        response = await client.post(
            "/api/billing/webhook",
            data=failed,
            headers={"Content-Type": "application/json", "Stripe-Signature": signature},
        )
        assert response.status == 200
        assert accounts.users["trial-user"]["subscription_status"] == "past_due"
        assert accounts.users["trial-user"]["billing_grace_ends_at"]

        grace_end = accounts.users["trial-user"]["billing_grace_ends_at"]
        repeated_failure, repeated_signature = signed_payload(
            {
                "id": "evt_failed_again",
                "type": "invoice.payment_failed",
                "data": {"object": {"customer": "cus_1", "subscription": "sub_1"}},
            }
        )
        response = await client.post(
            "/api/billing/webhook",
            data=repeated_failure,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": repeated_signature,
            },
        )
        assert response.status == 200
        assert accounts.users["trial-user"]["billing_grace_ends_at"] == grace_end

        billing.subscriptions["sub_1"]["status"] = "active"
        recovered, recovered_signature = signed_payload(
            {
                "id": "evt_recovered",
                "type": "invoice.paid",
                "data": {"object": {"customer": "cus_1", "subscription": "sub_1"}},
            }
        )
        response = await client.post(
            "/api/billing/webhook",
            data=recovered,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": recovered_signature,
            },
        )
        assert response.status == 200
        assert accounts.users["trial-user"]["subscription_status"] == "active"
        assert accounts.users["trial-user"]["billing_grace_ends_at"] == ""

        delayed_failure, delayed_signature = signed_payload(
            {
                "id": "evt_delayed_failure",
                "type": "invoice.payment_failed",
                "data": {"object": {"customer": "cus_1", "subscription": "sub_1"}},
            }
        )
        response = await client.post(
            "/api/billing/webhook",
            data=delayed_failure,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": delayed_signature,
            },
        )
        assert response.status == 200
        assert accounts.users["trial-user"]["subscription_status"] == "active"
        assert accounts.users["trial-user"]["billing_grace_ends_at"] == ""
        assert grace_end

        billing.subscriptions["sub_1"]["status"] = "canceled"
        canceled, canceled_signature = signed_payload(
            {
                "id": "evt_canceled",
                "type": "customer.subscription.deleted",
                "data": {
                    "object": {
                        "id": "sub_1",
                        "customer": "cus_1",
                        "status": "canceled",
                        "metadata": {"mhm_user_id": "trial-user"},
                    }
                },
            }
        )
        response = await client.post(
            "/api/billing/webhook",
            data=canceled,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": canceled_signature,
            },
        )
        assert response.status == 200
        assert accounts.users["trial-user"]["subscription_status"] == "canceled"

        delayed_paid, delayed_paid_signature = signed_payload(
            {
                "id": "evt_delayed_paid",
                "type": "invoice.paid",
                "data": {"object": {"customer": "cus_1", "subscription": "sub_1"}},
            }
        )
        response = await client.post(
            "/api/billing/webhook",
            data=delayed_paid,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": delayed_paid_signature,
            },
        )
        assert response.status == 200
        assert accounts.users["trial-user"]["subscription_status"] == "canceled"

        bad = await client.post(
            "/api/billing/webhook",
            data=failed,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "t=1000,v1=bad",
            },
        )
        assert bad.status == 400


async def test_invoice_parent_subscription_can_resolve_account_before_checkout_event():
    accounts, billing = Accounts(), Billing()
    app = create_web_app(
        accounts=accounts,
        billing=billing,
        mailer=lambda _email, _code: None,
        origin=ORIGIN,
        proxy_secret="",
    )
    event, signature = signed_payload(
        {
            "id": "evt_invoice_first",
            "type": "invoice.paid",
            "data": {
                "object": {
                    "customer": "cus_1",
                    "parent": {
                        "subscription_details": {"subscription": "sub_1"}
                    },
                }
            },
        }
    )
    async with web_client(app) as client:
        response = await client.post(
            "/api/billing/webhook",
            data=event,
            headers={"Content-Type": "application/json", "Stripe-Signature": signature},
        )
        assert response.status == 200
    assert accounts.users["trial-user"]["subscription_status"] == "active"
    assert accounts.users["trial-user"]["stripe_subscription_id"] == "sub_1"
