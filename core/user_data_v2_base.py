# LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_v2_base imports.
from core._storage_bridge import bridge_storage_module
from storage.user_data_v2_base import (
    SCHEMA_VERSION as SCHEMA_VERSION,
    BaseItemModel as BaseItemModel,
    ItemKind as ItemKind,
    SourceModel as SourceModel,
    generate_short_id as generate_short_id,
    v2_schema_validation_error as v2_schema_validation_error,
)

_module = bridge_storage_module(__name__, "storage.user_data_v2_base")
globals().update(_module.__dict__)
