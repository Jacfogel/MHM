# LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_presets imports.
from core._storage_bridge import bridge_storage_module
from storage.user_data_presets import (
    TIMEZONE_OPTIONS as TIMEZONE_OPTIONS,
    get_predefined_options as get_predefined_options,
    get_timezone_options as get_timezone_options,
)

_module = bridge_storage_module(__name__, "storage.user_data_presets")
globals().update(_module.__dict__)
