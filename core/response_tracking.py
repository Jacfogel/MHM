"""Generic response tracking utilities.

Check-in persistence lives in ``checkins.checkin_data_manager``. This module keeps
chat-interaction storage and generic response logs in core.
"""

from __future__ import annotations

from typing import Any

from core import get_user_data
from core.error_handling import handle_errors
from core.file_operations import get_user_file_path, load_json_data, save_json_data
from core.logger import get_component_logger
from core.time_utilities import now_timestamp_full

logger = get_component_logger("user_activity")
tracking_logger = get_component_logger("user_activity")


@handle_errors("getting response log filename", default_return="response_log.json")
def _get_response_log_filename(response_type: str) -> str:
    """Get the filename for a response log type."""
    filename_mapping = {
        "checkin": "checkin_log.json",
        "chat_interaction": "chat_interaction_log.json",
    }
    return filename_mapping.get(response_type, f"{response_type}_log.json")


@handle_errors("storing user response")
def store_user_response(
    user_id: str, response_data: dict[str, Any], response_type: str = "checkin"
) -> None:
    """Store a generic user response, delegating check-ins to the check-in domain."""
    if response_type == "checkin":
        from checkins.checkin_data_manager import store_checkin_response

        store_checkin_response(user_id, response_data)
        return

    if response_type == "chat_interaction":
        log_file = get_user_file_path(user_id, "chat_interactions")
    else:
        log_file = get_user_file_path(user_id, f"{response_type}_log")

    existing_data = load_json_data(log_file)
    if "timestamp" not in response_data:
        response_data["timestamp"] = now_timestamp_full()

    if not isinstance(existing_data, list):
        existing_data = []
    existing_data.append(response_data)

    save_json_data(existing_data, log_file)
    logger.debug(f"Stored {response_type} response for user {user_id}")


@handle_errors("storing chat interaction")
def store_chat_interaction(
    user_id: str, user_message: str, ai_response: str, context_used: bool = False
) -> None:
    """Store a chat interaction between user and AI."""
    response_data = {
        "user_message": user_message,
        "ai_response": ai_response,
        "context_used": context_used,
        "message_length": len(user_message),
        "response_length": len(ai_response),
        "timestamp": now_timestamp_full(),
    }
    store_user_response(user_id, response_data, "chat_interaction")
    logger.info(f"Stored chat_interaction response for user {user_id}: {response_data}")


@handle_errors("getting recent responses", default_return=[])
def get_recent_responses(
    user_id: str, response_type: str = "checkin", limit: int = 5
) -> list[dict[str, Any]]:
    """Get recent responses for a user."""
    if response_type == "checkin":
        from checkins.checkin_data_manager import get_recent_checkins

        return get_recent_checkins(user_id, limit=limit)

    if response_type == "chat_interaction":
        log_file = get_user_file_path(user_id, "chat_interactions")
    else:
        log_file = get_user_file_path(user_id, f"{response_type}_log")

    data = load_json_data(log_file) or []
    if not isinstance(data, list):
        return []
    return sorted(data, key=_get_response_timestamp_for_sorting, reverse=True)[:limit]


@handle_errors("getting recent chat interactions", default_return=[])
def get_recent_chat_interactions(user_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """Get recent chat interactions for a user."""
    return get_recent_responses(user_id, "chat_interaction", limit)


# duplicate_functions_exclude: field-specific wrapper; see core.time_utilities.timestamp_sort_key_from_dict.
@handle_errors("getting response timestamp for sorting", default_return=0.0)
def _get_response_timestamp_for_sorting(item: Any) -> float:
    from core.time_utilities import timestamp_sort_key_from_dict

    return timestamp_sort_key_from_dict(item, "timestamp")


@handle_errors("checking if automated messages enabled", default_return=False)
def is_automated_messages_enabled(user_id: str) -> bool:
    """Check if automated outbound messages are enabled for a user."""
    from messages.message_data_manager import is_automated_messages_enabled as _enabled

    return _enabled(user_id)


@handle_errors("getting user info for tracking", default_return={})
def get_user_info_for_tracking(user_id: str) -> dict[str, Any]:
    """Get user information for response tracking."""
    try:
        user_data_result = get_user_data(user_id, "account")
        user_account = user_data_result.get("account")
        prefs_result = get_user_data(user_id, "preferences")
        user_preferences = prefs_result.get("preferences")
        context_result = get_user_data(user_id, "context")
        user_context = context_result.get("context")

        if not user_account:
            return {}

        return {
            "user_id": user_id,
            "internal_username": user_account.get("internal_username", ""),
            "preferred_name": (
                user_context.get("preferred_name", "") if user_context else ""
            ),
            "categories": (
                user_preferences.get("categories", []) if user_preferences else []
            ),
            "messaging_service": (
                user_preferences.get("channel", {}).get("type", "")
                if user_preferences
                else ""
            ),
            "created_at": user_account.get("created_at", ""),
            "last_updated": user_account.get("last_updated", ""),
        }
    except Exception as e:
        logger.error(f"Error getting user info for tracking {user_id}: {e}")
        return {}


@handle_errors("tracking user response", default_return=None)
def track_user_response(user_id: str, category: str, response_data: dict[str, Any]) -> None:
    """Track a user's response to a message."""
    try:
        user_data_result = get_user_data(user_id, "account")
        user_account = user_data_result.get("account")
        if not user_account:
            logger.error(f"User account not found for tracking: {user_id}")
            return

        if category == "chat_interaction":
            user_message = response_data.get("user_message", "")
            ai_response = response_data.get("ai_response", "")
            context_used = response_data.get("context_used", False)
            store_chat_interaction(user_id, user_message, ai_response, context_used)
        else:
            store_user_response(user_id, response_data, category)

        logger.info(f"Tracked {category} response for user {user_id}")

    except Exception as e:
        logger.error(f"Error tracking user response: {e}")
