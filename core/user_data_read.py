# LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_read imports.
from core._storage_bridge import bridge_storage_module
from storage.user_data_read import (
    clear_user_caches as clear_user_caches,
    ensure_unique_ids as ensure_unique_ids,
    get_user_data as get_user_data,
    get_user_data_with_metadata as get_user_data_with_metadata,
    load_and_ensure_ids as load_and_ensure_ids,
)

_module = bridge_storage_module(__name__, "storage.user_data_read")
globals().update(_module.__dict__)
