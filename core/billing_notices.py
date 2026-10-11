"""One-time customer notices for trial and subscription access changes."""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any

from core.billing import billing_status, has_service_access
from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.time_utilities import now_datetime_full, parse_timestamp_full

logger = get_component_logger("scheduler")

TRIAL_NOTICE_DAYS = 3
MAX_BILLING_NOTICE_KEYS = 20


@handle_errors(
    "building billing lifecycle notice", user_friendly=False, default_return=None
)
def pending_billing_notice(
    account: dict[str, Any], *, now: datetime | None = None
) -> tuple[str, str] | None:
    """Return the next unsent billing notice identity and customer-facing text."""
    current = now or now_datetime_full()
    status = billing_status(account)
    sent = {
        value
        for value in (account.get("billing_notice_keys") or [])
        if isinstance(value, str) and value
    }

    if status == "trialing":
        trial_end_text = str(account.get("trial_ends_at") or "")
        trial_end = parse_timestamp_full(trial_end_text)
        if trial_end is None:
            return None
        if current < trial_end <= current + timedelta(days=TRIAL_NOTICE_DAYS):
            key = f"trial-ending:{trial_end_text}"
            if key not in sent:
                days = max(1, math.ceil((trial_end - current).total_seconds() / 86400))
                return (
                    key,
                    f"Your MHM free trial ends in {days} day{'s' if days != 1 else ''}. "
                    "Subscribe from Account settings to keep scheduled messages, "
                    "check-ins, and task reminders active.",
                )
        if current >= trial_end:
            key = f"trial-paused:{trial_end_text}"
            if key not in sent:
                return (
                    key,
                    "Your MHM free trial has ended, so scheduled messages, check-ins, "
                    "and task reminders are paused. Your account and saved data remain "
                    "available; subscribe from Account settings to resume scheduled support.",
                )

    if status == "past_due":
        grace_end_text = str(account.get("billing_grace_ends_at") or "")
        key_prefix = "payment-attention" if has_service_access(account, now=current) else "payment-paused"
        key = f"{key_prefix}:{grace_end_text}"
        if key not in sent:
            if key_prefix == "payment-attention":
                return (
                    key,
                    "Your latest MHM payment needs attention. Scheduled support remains "
                    "active during the short grace period. Open Account settings and use "
                    "Manage billing to update your payment method.",
                )
            return (
                key,
                "Scheduled MHM support is paused because the latest payment was not "
                "completed before the grace period ended. Your account and saved data "
                "remain available; use Manage billing to restore service.",
            )

    if status == "canceled":
        subscription_id = str(account.get("stripe_subscription_id") or "none")
        key = f"subscription-canceled:{subscription_id}"
        if key not in sent:
            return (
                key,
                "Your MHM subscription has ended, so scheduled messages, check-ins, and "
                "task reminders are paused. Your account and saved data remain available, "
                "and you can subscribe again from Account settings.",
            )
    return None


@handle_errors("delivering billing lifecycle notices", default_return=0)
def process_billing_notices(delivery: Any) -> int:
    """Deliver and persist each account's next one-time billing notice."""
    from core import get_all_user_ids, get_user_data, update_user_account

    sender = getattr(delivery, "send_account_notice", None)
    if not callable(sender):
        logger.warning("Billing notices are unavailable: delivery port has no notice sender")
        return 0

    delivered = 0
    for user_id in get_all_user_ids():
        account = get_user_data(user_id, "account").get("account") or {}
        notice = pending_billing_notice(account)
        if notice is None:
            continue
        notice_key, message = notice
        if not sender(user_id, message):
            logger.warning(f"Billing notice could not be delivered for user {user_id}")
            continue
        existing = [
            value
            for value in (account.get("billing_notice_keys") or [])
            if isinstance(value, str) and value
        ]
        keys = [*existing[-(MAX_BILLING_NOTICE_KEYS - 1) :], notice_key]
        if update_user_account(
            user_id, {"billing_notice_keys": keys}, auto_create=False
        ):
            delivered += 1
        else:
            logger.error(f"Billing notice state could not be saved for user {user_id}")
    return delivered
