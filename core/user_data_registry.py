# LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_registry imports.
from core._storage_bridge import bridge_storage_module
from storage.user_data_registry import (
    USER_DATA_LOADERS as USER_DATA_LOADERS,
    _get_user_data__load_account as _get_user_data__load_account,
    _get_user_data__load_context as _get_user_data__load_context,
    _get_user_data__load_preferences as _get_user_data__load_preferences,
    _get_user_data__load_schedules as _get_user_data__load_schedules,
    _save_user_data__save_account as _save_user_data__save_account,
    _save_user_data__save_context as _save_user_data__save_context,
    _save_user_data__save_preferences as _save_user_data__save_preferences,
    _save_user_data__save_schedules as _save_user_data__save_schedules,
    clear_user_caches as clear_user_caches,
    get_available_data_types as get_available_data_types,
    get_data_type_info as get_data_type_info,
    register_data_loader as register_data_loader,
    register_default_loaders as register_default_loaders,
)

_module = bridge_storage_module(__name__, "storage.user_data_registry")
globals().update(_module.__dict__)
