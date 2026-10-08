"""Subscription billing helpers and the small Stripe HTTP boundary.

MHM stores only Stripe object identifiers and subscription state. Card and
payment-method data stay on Stripe-hosted Checkout and Customer Portal pages.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import math
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from core import config
from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.time_utilities import (
    TIMESTAMP_FULL,
    format_timestamp,
    now_datetime_full,
    parse_timestamp_full,
)

logger = get_component_logger("main")

TRIAL_DAYS = 30
DEFAULT_GRACE_DAYS = 3
WEBHOOK_TOLERANCE_SECONDS = 300
SUBSCRIPTION_STATUSES = {"trialing", "active", "past_due", "canceled", "comped"}


class StripeAPIError(RuntimeError):
    """Raised when Stripe cannot create a hosted billing session."""


class StripeWebhookError(ValueError):
    """Raised when a webhook payload is invalid or unauthenticated."""


@handle_errors("creating new-account billing state", user_friendly=False, re_raise=True)
def new_account_billing(created_at: str) -> dict[str, str]:
    """Return the explicit 30-day billing state for a new account."""
    created = parse_timestamp_full(created_at) or now_datetime_full()
    return {
        "trial_ends_at": format_timestamp(
            created + timedelta(days=TRIAL_DAYS), TIMESTAMP_FULL
        ),
        "subscription_status": "trialing",
        "stripe_customer_id": "",
        "stripe_subscription_id": "",
        "billing_grace_ends_at": "",
    }


@handle_errors(
    "normalizing account billing status",
    user_friendly=False,
    default_return="canceled",
)
def billing_status(account: dict[str, Any]) -> str:
    """Return a safe local status; accounts without one retain complimentary access."""
    value = str(account.get("subscription_status") or "comped").strip().lower()
    return value if value in SUBSCRIPTION_STATUSES else "canceled"


@handle_errors(
    "checking account service access", user_friendly=False, default_return=False
)
def has_service_access(account: dict[str, Any], *, now: datetime | None = None) -> bool:
    """Whether automated MHM deliveries are currently entitled to run."""
    status = billing_status(account)
    if status in {"active", "comped"}:
        return True
    current = now or now_datetime_full()
    if status == "trialing":
        trial_end = parse_timestamp_full(str(account.get("trial_ends_at") or ""))
        return trial_end is not None and current < trial_end
    if status == "past_due":
        grace_end = parse_timestamp_full(
            str(account.get("billing_grace_ends_at") or "")
        )
        return grace_end is not None and current < grace_end
    return False

@handle_errors("building account billing summary", user_friendly=False, re_raise=True)
def account_billing_summary(
    account: dict[str, Any], *, configured: bool, now: datetime | None = None
) -> dict[str, Any]:
    """Build the non-sensitive billing view returned to the signed-in website."""
    current = now or now_datetime_full()
    status = billing_status(account)
    trial_end = parse_timestamp_full(str(account.get("trial_ends_at") or ""))
    days_remaining = 0
    if status == "trialing" and trial_end is not None:
        days_remaining = max(
            0, math.ceil((trial_end - current).total_seconds() / 86400)
        )
    return {
        "status": status,
        "access_active": has_service_access(account, now=current),
        "trial_ends_at": str(account.get("trial_ends_at") or ""),
        "trial_days_remaining": days_remaining,
        "grace_ends_at": str(account.get("billing_grace_ends_at") or ""),
        "customer_exists": bool(account.get("stripe_customer_id")),
        "subscription_exists": bool(account.get("stripe_subscription_id")),
        "checkout_available": configured,
    }


@handle_errors(
    "mapping Stripe subscription status",
    user_friendly=False,
    default_return="canceled",
)
def local_status_for_stripe(status: str) -> str:
    """Map Stripe's richer subscription lifecycle to MHM's access states."""
    normalized = str(status or "").strip().lower()
    if normalized == "trialing":
        return "trialing"
    if normalized == "active":
        return "active"
    if normalized in {"past_due", "unpaid", "incomplete"}:
        return "past_due"
    return "canceled"


class StripeBillingClient:
    """Minimal async client for Stripe-hosted Checkout, Portal, and webhooks."""

    api_origin = "https://api.stripe.com"

    @handle_errors(
        "initializing Stripe billing client", user_friendly=False, re_raise=True
    )
    def __init__(
        self,
        *,
        secret_key: str = "",
        price_id: str = "",
        webhook_secret: str = "",
        wall_clock: Callable[[], float] = time.time,
    ) -> None:
        self.secret_key = secret_key.strip()
        self.price_id = price_id.strip()
        self.webhook_secret = webhook_secret.strip()
        self.wall_clock = wall_clock

    @classmethod
    @handle_errors(
        "loading Stripe billing configuration", user_friendly=False, re_raise=True
    )
    def from_config(cls) -> StripeBillingClient:
        """Build a Stripe client from the configured secret values."""
        return cls(
            secret_key=str(getattr(config, "STRIPE_SECRET_KEY", "") or ""),
            price_id=str(getattr(config, "STRIPE_PRICE_ID", "") or ""),
            webhook_secret=str(getattr(config, "STRIPE_WEBHOOK_SECRET", "") or ""),
        )

    @handle_errors(
        "checking Stripe Checkout configuration",
        user_friendly=False,
        default_return=False,
    )
    def checkout_configured(self) -> bool:
        """Return whether Checkout has both required Stripe identifiers."""
        return bool(self.secret_key and self.price_id)

    async def _post(
        self,
        path: str,
        fields: list[tuple[str, str]],
        *,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if not self.secret_key:
            raise StripeAPIError("Stripe billing is not configured")
        headers = {"Accept": "application/json"}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        timeout = aiohttp.ClientTimeout(total=15)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.api_origin}{path}",
                    data=fields,
                    auth=aiohttp.BasicAuth(self.secret_key, ""),
                    headers=headers,
                ) as response:
                    payload = await response.json(content_type=None)
                    if response.status >= 400 or not isinstance(payload, dict):
                        raise StripeAPIError("Stripe rejected the billing request")
                    return payload
        except StripeAPIError:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as exc:
            raise StripeAPIError("Stripe could not be reached") from exc

    @handle_errors(
        "creating Stripe Checkout session", user_friendly=False, re_raise=True
    )
    async def create_checkout_session(
        self,
        *,
        user_id: str,
        email: str,
        customer_id: str,
        success_url: str,
        cancel_url: str,
        trial_end: datetime | None,
    ) -> dict[str, Any]:
        """Create one hosted monthly-subscription Checkout Session."""
        if not self.checkout_configured():
            raise StripeAPIError("Stripe Checkout is not configured")
        fields = [
            ("mode", "subscription"),
            ("line_items[0][price]", self.price_id),
            ("line_items[0][quantity]", "1"),
            ("client_reference_id", user_id),
            ("metadata[mhm_user_id]", user_id),
            ("subscription_data[metadata][mhm_user_id]", user_id),
            ("success_url", success_url),
            ("cancel_url", cancel_url),
            ("allow_promotion_codes", "true"),
        ]
        if customer_id:
            fields.append(("customer", customer_id))
        else:
            fields.append(("customer_email", email))
        # Stripe requires a future trial_end. Inside 48 hours, start billing now
        # rather than asking Stripe to accept an invalid near-past timestamp.
        if trial_end and trial_end.timestamp() >= self.wall_clock() + (2 * 86400):
            fields.append(
                ("subscription_data[trial_end]", str(int(trial_end.timestamp())))
            )
        bucket = int(self.wall_clock() // 60)
        return await self._post(
            "/v1/checkout/sessions",
            fields,
            idempotency_key=f"mhm-checkout-{user_id}-{bucket}",
        )

    @handle_errors(
        "creating Stripe customer portal session", user_friendly=False, re_raise=True
    )
    async def create_portal_session(
        self, *, customer_id: str, return_url: str
    ) -> dict[str, Any]:
        """Create a short-lived Stripe Customer Portal session."""
        return await self._post(
            "/v1/billing_portal/sessions",
            [("customer", customer_id), ("return_url", return_url)],
        )

    def verify_webhook(self, payload: bytes, signature_header: str) -> dict[str, Any]:
        """Verify Stripe's signed raw body and return its snapshot event."""
        if not self.webhook_secret:
            raise StripeWebhookError("Stripe webhooks are not configured")
        timestamp: int | None = None
        signatures: list[str] = []
        for part in signature_header.split(","):
            key, separator, value = part.strip().partition("=")
            if not separator:
                continue
            if key == "t":
                try:
                    timestamp = int(value)
                except ValueError:
                    timestamp = None
            elif key == "v1":
                signatures.append(value)
        if timestamp is None or not signatures:
            raise StripeWebhookError("Stripe signature is missing")
        if abs(self.wall_clock() - timestamp) > WEBHOOK_TOLERANCE_SECONDS:
            raise StripeWebhookError("Stripe signature has expired")
        signed = str(timestamp).encode("ascii") + b"." + payload
        expected = hmac.new(
            self.webhook_secret.encode("utf-8"), signed, hashlib.sha256
        ).hexdigest()
        if not any(
            hmac.compare_digest(expected, candidate) for candidate in signatures
        ):
            raise StripeWebhookError("Stripe signature does not match")
        try:
            event = json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise StripeWebhookError("Stripe payload is invalid") from exc
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            raise StripeWebhookError("Stripe event is invalid")
        return event
