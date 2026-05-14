# LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_validation imports.
from core._storage_bridge import bridge_storage_module
from storage.user_data_validation import (
    _shared__title_case as _shared__title_case,
    is_valid_category_name as is_valid_category_name,
    is_valid_discord_id as is_valid_discord_id,
    is_valid_email as is_valid_email,
    is_valid_phone as is_valid_phone,
    is_valid_string_length as is_valid_string_length,
    is_valid_user_id as is_valid_user_id,
    validate_new_user_data as validate_new_user_data,
    validate_personalization_data as validate_personalization_data,
    validate_schedule_periods as validate_schedule_periods,
    validate_schedule_periods__validate_time_format as validate_schedule_periods__validate_time_format,
    validate_user_update as validate_user_update,
)

_module = bridge_storage_module(__name__, "storage.user_data_validation")
globals().update(_module.__dict__)
