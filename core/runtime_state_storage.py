# LEGACY COMPATIBILITY: Temporary bridge for old core.runtime_state_storage imports.
from core._storage_bridge import bridge_storage_module
from storage.runtime_state_storage import (
    get_runtime_state_path as get_runtime_state_path,
    load_runtime_state_json as load_runtime_state_json,
    save_runtime_state_json as save_runtime_state_json,
)

_module = bridge_storage_module(__name__, "storage.runtime_state_storage")
globals().update(_module.__dict__)
