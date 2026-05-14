# LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_operations imports.
from core._storage_bridge import bridge_storage_module
from storage.user_data_operations import (
    UserDataManager as UserDataManager,
    backup_user_data as backup_user_data,
    build_user_index as build_user_index,
    delete_user_completely as delete_user_completely,
    export_user_data as export_user_data,
    get_all_user_summaries as get_all_user_summaries,
    get_user_analytics_summary as get_user_analytics_summary,
    get_user_data_summary as get_user_data_summary,
    get_user_info_for_data_manager as get_user_info_for_data_manager,
    get_user_summary as get_user_summary,
    rebuild_user_index as rebuild_user_index,
    update_message_references as update_message_references,
    update_user_index as update_user_index,
    user_data_manager as user_data_manager,
)

_module = bridge_storage_module(__name__, "storage.user_data_operations")
globals().update(_module.__dict__)
