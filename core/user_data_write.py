# LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_write imports.
from core._storage_bridge import bridge_storage_module
from storage.user_data_write import (
    save_user_data as save_user_data,
    save_user_data_transaction as save_user_data_transaction,
    update_channel_preferences as update_channel_preferences,
    update_user_account as update_user_account,
    update_user_context as update_user_context,
    update_user_preferences as update_user_preferences,
    update_user_schedules as update_user_schedules,
)

_module = bridge_storage_module(__name__, "storage.user_data_write")
globals().update(_module.__dict__)
