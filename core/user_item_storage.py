# LEGACY COMPATIBILITY: Temporary bridge for old core.user_item_storage imports.
from core._storage_bridge import bridge_storage_module
from storage.user_item_storage import (
    ensure_user_subdir as ensure_user_subdir,
    get_user_subdir_path as get_user_subdir_path,
    load_user_json_file as load_user_json_file,
    save_user_json_file as save_user_json_file,
)

_module = bridge_storage_module(__name__, "storage.user_item_storage")
globals().update(_module.__dict__)
