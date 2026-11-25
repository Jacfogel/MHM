"""Coordinate account lifecycle across independent phone-channel stores."""

from core.error_handling import handle_errors
from storage.runtime_state_storage import get_runtime_state_path
from storage.sms_state import SmsState
from storage.whatsapp_state import WhatsAppState


@handle_errors("opening existing phone stores", re_raise=True, user_friendly=False)
def existing_phone_states():
    """Open existing stores without creating disabled channels' databases."""
    stores = {}
    for name, factory in (("sms", SmsState), ("whatsapp", WhatsAppState)):
        path = get_runtime_state_path(f"{name}_state.sqlite3")
        if path.exists():
            stores[name] = factory(path)
    return stores
