"""Shared phone ownership and consent boundaries for SMS account setup."""

from core import config, get_user_data, update_user_account
from core.error_handling import ValidationError, handle_errors
from communication.communication_channels.sms.phone import normalize_phone
from storage.sms_state import SmsState
from core.channel_access import channel_allowed


@handle_errors("checking SMS availability", user_friendly=False, default_return=False)
def sms_available():
    """Report whether the operator configured live SMS."""
    return bool(config.SMS_TWILIO_ENABLED and not config.SMS_SIMULATION_ENABLED
                and config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN
                and config.TWILIO_PHONE_NUMBER and config.SMS_PUBLIC_BASE_URL)


@handle_errors("resolving SMS account", user_friendly=False, default_return=None)
def sms_user_for_phone(phone, require_paid=True):
    """Recheck account state and saved phone on every outbound or inbound operation."""
    phone = normalize_phone(phone)
    if not phone:
        return None
    user_id = SmsState().enrolled_user(phone)
    if not user_id:
        return None
    account = get_user_data(user_id, "account").get("account") or {}
    if account.get("account_status") != "active" or normalize_phone(account.get("phone", "")) != phone:
        return None
    if require_paid and not channel_allowed(account, "sms"):
        return None
    return user_id


@handle_errors("starting phone verification", user_friendly=False, re_raise=True)
def begin_sms_enrollment(phone, consent, owner=""):
    """Prepare a code the owner must text from the requested number."""
    phone = normalize_phone(phone)
    if not sms_available():
        raise ValidationError("SMS is not configured by the MHM administrator.")
    if not phone or consent is not True:
        raise ValidationError("Enter an international phone number and consent to MHM texts.")
    if owner:
        account = get_user_data(owner, "account").get("account") or {}
        if not channel_allowed(account, "sms"):
            raise ValidationError("SMS requires an active paid Discord + SMS plan. Trial accounts use Discord.")
    return SmsState().begin_enrollment(phone, owner)


@handle_errors("connecting verified SMS phone", user_friendly=False, re_raise=True)
def connect_sms(user_id, phone, token, consent, owner=""):
    """Save a verified phone and consent without changing the preferred channel."""
    phone = normalize_phone(phone)
    state = SmsState()
    account = get_user_data(user_id, "account").get("account") or {}
    if not channel_allowed(account, "sms"):
        raise ValidationError("SMS requires an active paid Discord + SMS plan. Trial accounts use Discord.")
    if not sms_available() or not phone or consent is not True or not state.enrollment_verified(phone, token, owner):
        raise ValidationError("Text the connection code from this phone, then verify again before it expires.")
    existing = state.enrolled_user(phone)
    if existing and existing != user_id:
        raise ValidationError("This phone is already connected to another account.")
    if not update_user_account(user_id, {"phone": phone}, auto_create=False):
        raise ValidationError("MHM could not confirm the phone was saved. Check account settings before retrying.")
    if not state.bind_enrollment(user_id, phone, token, owner):
        raise ValidationError("MHM could not confirm SMS connection. Check account settings before retrying.")
    return True
