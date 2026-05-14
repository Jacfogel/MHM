# LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_v2_envelopes imports.
from core._storage_bridge import bridge_storage_module
from storage.user_data_v2_envelopes import (
    SCHEMA_VERSION as SCHEMA_VERSION,
    CheckinCollectionV2Model as CheckinCollectionV2Model,
    CheckinV2Model as CheckinV2Model,
    ItemKind as ItemKind,
    MessageDeliveryCollectionV2Model as MessageDeliveryCollectionV2Model,
    MessageDeliveryV2Model as MessageDeliveryV2Model,
    MessageTemplateCollectionV2Model as MessageTemplateCollectionV2Model,
    MessageTemplateV2Model as MessageTemplateV2Model,
    NotebookCollectionV2Model as NotebookCollectionV2Model,
    NotebookV2Model as NotebookV2Model,
    ScheduleModel as ScheduleModel,
    SourceModel as SourceModel,
    TaskCollectionV2Model as TaskCollectionV2Model,
    TaskV2Model as TaskV2Model,
    generate_short_id as generate_short_id,
    validate_v2_document as validate_v2_document,
)

_module = bridge_storage_module(__name__, "storage.user_data_v2_envelopes")
globals().update(_module.__dict__)
