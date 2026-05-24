"""Automated message domain package."""

from .message_data_manager import (
    add_message,
    archive_old_messages,
    create_message_file_from_defaults,
    delete_message,
    edit_message,
    ensure_user_message_files,
    get_message_categories,
    get_recent_messages,
    get_timestamp_for_sorting,
    is_automated_messages_enabled,
    load_default_messages,
    load_user_messages,
    store_sent_message,
    update_message,
)
from .message_analytics import MessageAnalytics
from .message_service import (
    get_predefined_message_preview_text,
    message_schedule_matches_current_window,
    message_template_schedule_lists,
)

__all__ = [
    "MessageAnalytics",
    "add_message",
    "archive_old_messages",
    "create_message_file_from_defaults",
    "delete_message",
    "edit_message",
    "ensure_user_message_files",
    "get_message_categories",
    "get_predefined_message_preview_text",
    "get_recent_messages",
    "get_timestamp_for_sorting",
    "is_automated_messages_enabled",
    "load_default_messages",
    "load_user_messages",
    "message_schedule_matches_current_window",
    "message_template_schedule_lists",
    "store_sent_message",
    "update_message",
]
