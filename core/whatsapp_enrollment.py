"""Independent WhatsApp ownership proof, consent, and paid access."""

from core import config, get_user_data, update_user_account
from core.channel_access import channel_allowed
from core.error_handling import ValidationError, handle_errors
from communication.communication_channels.sms.phone import normalize_phone
from storage.whatsapp_state import WhatsAppState


@handle_errors("checking WhatsApp availability", default_return=False, user_friendly=False)
def whatsapp_available():
    return bool(config.WHATSAPP_ENABLED and config.WHATSAPP_ACCESS_TOKEN
                and config.WHATSAPP_PHONE_NUMBER_ID and config.WHATSAPP_BUSINESS_ACCOUNT_ID
                and config.WHATSAPP_APP_SECRET and config.WHATSAPP_VERIFY_TOKEN
                and normalize_phone(config.WHATSAPP_PHONE_NUMBER))


@handle_errors("resolving WhatsApp account", default_return=None, user_friendly=False, retry_after_recovery=False)
def whatsapp_user_for_phone(phone, require_paid=True):
    phone = normalize_phone(phone)
    if not phone:
        return None
    uid = WhatsAppState().enrolled_user(phone)
    if not uid:
        return None
    account = get_user_data(uid, "account").get("account") or {}
    if account.get("account_status") != "active" or normalize_phone(account.get("whatsapp_phone", "")) != phone:
        return None
    if require_paid and not channel_allowed(account, "whatsapp"):
        return None
    return uid


@handle_errors("starting WhatsApp verification", re_raise=True, user_friendly=False, retry_after_recovery=False)
def begin_whatsapp_enrollment(phone, consent, owner):
    phone = normalize_phone(phone)
    account = get_user_data(owner, "account").get("account") or {}
    if not owner or account.get("account_status") != "active" or not channel_allowed(account, "whatsapp"):
        raise ValidationError("WhatsApp requires an active paid WhatsApp plan ($20 CAD/month).")
    if not whatsapp_available():
        raise ValidationError("WhatsApp is not configured by the MHM administrator.")
    if not phone or consent is not True:
        raise ValidationError("Enter an international phone number and consent to MHM WhatsApp messages.")
    return WhatsAppState().begin_enrollment(phone, owner)


@handle_errors("connecting WhatsApp phone", re_raise=True, user_friendly=False, retry_after_recovery=False)
def connect_whatsapp(user_id, phone, token, consent, owner):
    phone = normalize_phone(phone)
    state = WhatsAppState()
    account = get_user_data(user_id, "account").get("account") or {}
    if owner != user_id or account.get("account_status") != "active" or not channel_allowed(account, "whatsapp"):
        raise ValidationError("WhatsApp requires an active paid WhatsApp plan ($20 CAD/month).")
    if not whatsapp_available() or not phone or consent is not True:
        raise ValidationError("Send the connection code from WhatsApp on this phone, then verify before it expires.")
    existing = state.enrolled_user(phone)
    if existing == user_id and normalize_phone(account.get("whatsapp_phone", "")) == phone:
        state.clear_former_pending(user_id, phone)
        return True
    if not state.enrollment_verified(phone, token, owner):
        raise ValidationError("Send the connection code from WhatsApp on this phone, then verify before it expires.")
    if existing and existing != user_id:
        raise ValidationError("This WhatsApp number is already connected to another account.")
    if not update_user_account(user_id, {"whatsapp_phone": phone}, auto_create=False):
        raise ValidationError("Could not confirm the saved WhatsApp number. Reload settings before retrying.")
    if not state.bind_enrollment(user_id, phone, token, owner):
        raise ValidationError("Could not confirm WhatsApp connection. Reload settings before retrying.")
    # A changed number must never inherit an earlier recipient's saved text.
    state.clear_former_pending(user_id, phone)
    return True


@handle_errors("disconnecting WhatsApp", re_raise=True, user_friendly=False, retry_after_recovery=False)
def disconnect_whatsapp(user_id):
    """Revoke consent while preserving a different preferred channel."""
    data = get_user_data(user_id, "account", "preferences")
    selected = ((data.get("preferences") or {}).get("channel") or {}).get("type", "whatsapp")
    if selected == "whatsapp":
        if not update_user_account(user_id, {"chat_id": ""}, auto_create=False):
            raise ValidationError("Could not confirm the delivery contact. Reload before retrying.")
    WhatsAppState().disconnect_enrollment(user_id)
    return selected
