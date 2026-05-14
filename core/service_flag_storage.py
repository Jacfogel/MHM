# LEGACY COMPATIBILITY: Temporary bridge for old core.service_flag_storage imports.
from core._storage_bridge import bridge_storage_module
from storage.service_flag_storage import (
    read_service_flag_json as read_service_flag_json,
    write_service_flag_json as write_service_flag_json,
)

_module = bridge_storage_module(__name__, "storage.service_flag_storage")
globals().update(_module.__dict__)
