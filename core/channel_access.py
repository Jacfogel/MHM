"""Account-plan rules shared by delivery and channel settings."""

from core.billing import billing_status
from core.error_handling import handle_errors


@handle_errors("checking account channel access", user_friendly=False, default_return=False)
def channel_allowed(account, channel):
    """Email and Discord are available; phone channels require live-paid plans."""
    status = billing_status(account)
    if channel == "whatsapp":
        return status == "active" and account.get("subscription_plan") == "whatsapp" and account.get("billing_livemode") is True
    if channel == "sms":
        return status == "active" and account.get("subscription_plan") == "phone" and account.get("billing_livemode") is True
    if status == "trialing":
        return channel in {"email", "discord"}
    return channel in {"email", "discord"}


@handle_errors("checking outbound channel access", user_friendly=False, default_return=False)
def delivery_channel_allowed(user_id, channel):
    """Apply account rules to both synchronous and asynchronous send entry points."""
    from core import get_user_data

    if not user_id or channel not in {"email", "discord", "sms", "whatsapp"}:
        return True
    account = get_user_data(user_id, "account").get("account") or {}
    return channel_allowed(account, channel)
