"""
Response tracking utilities for MHM.
Contains functions for storing and retrieving user responses, check-ins, and interactions.
"""

from datetime import datetime
from typing import Any
from core.logger import get_component_logger
from core.user_data_handlers import get_user_data
from core.file_operations import load_json_data, save_json_data, get_user_file_path
from core.error_handling import handle_errors
from core.service_utilities import now_readable_timestamp


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
    user_id: str, response_data: dict, response_type: str = "checkin"
):
    """
    Store user response data in appropriate file structure.
    """
    if response_type == "checkin":
        log_file = get_user_file_path(user_id, "checkins")
    elif response_type == "chat_interaction":
        log_file = get_user_file_path(user_id, "chat_interactions")
    else:
        log_file = get_user_file_path(user_id, f"{response_type}_log")

    existing_data = load_json_data(log_file) or []

    if "timestamp" not in response_data:
        # Canonical readable timestamp for stored interaction metadata
        response_data["timestamp"] = now_readable_timestamp()

    existing_data.append(response_data)

    save_json_data(existing_data, log_file)
    logger.debug(f"Stored {response_type} response for user {user_id}")


@handle_errors("storing chat interaction")
def store_chat_interaction(
    user_id: str, user_message: str, ai_response: str, context_used: bool = False
):
    """Store a chat interaction between user and AI."""
    response_data = {
        "user_message": user_message,
        "ai_response": ai_response,
        "context_used": context_used,
        "message_length": len(user_message),
        "response_length": len(ai_response),
        # Canonical readable timestamp for stored interaction metadata
        "timestamp": now_readable_timestamp(),
    }
    store_user_response(user_id, response_data, "chat_interaction")
    logger.info(f"Stored chat_interaction response for user {user_id}: {response_data}")


@handle_errors("getting recent responses", default_return=[])
def get_recent_responses(user_id: str, response_type: str = "checkin", limit: int = 5):
    """Get recent responses for a user from appropriate file structure."""
    # New structure
    if response_type == "checkin":
        log_file = get_user_file_path(user_id, "checkins")
    elif response_type == "chat_interaction":
        log_file = get_user_file_path(user_id, "chat_interactions")
    else:
        log_file = get_user_file_path(user_id, f"{response_type}_log")

    data = load_json_data(log_file) or []

    if data:

        def get_timestamp_for_sorting(item):
            """Convert timestamp to float for consistent sorting"""
            # Handle case where item might be a string instead of a dictionary
            if isinstance(item, str):
                # If it's a string, it's probably a malformed entry - assign it a very old timestamp
                return 0.0
            elif not isinstance(item, dict):
                # If it's not a dict or string, treat as very old
                return 0.0

            timestamp = item.get("timestamp", "1970-01-01 00:00:00")
            try:
                # Parse human-readable format
                dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                return dt.timestamp()
            except (ValueError, TypeError):
                # If parsing fails, use 0
                return 0.0

        sorted_data = sorted(data, key=get_timestamp_for_sorting, reverse=True)
        return sorted_data[:limit]
    return []


@handle_errors("getting recent checkins", default_return=[])
def get_recent_checkins(user_id: str, limit: int = 7):
    """Get recent check-in responses for a user."""
    return get_recent_responses(user_id, "checkin", limit)


@handle_errors("getting checkins by days", default_return=[])
def get_checkins_by_days(user_id: str, days: int = 7):
    """Get check-ins from the last N calendar days."""
    from datetime import datetime, timedelta

    # Get all check-ins first
    all_checkins = get_recent_responses(
        user_id, "checkin", limit=1000
    )  # Get a large number

    if not all_checkins:
        return []

    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=days)

    # Filter check-ins by date
    recent_checkins = []
    for checkin in all_checkins:
        if "timestamp" in checkin:
            try:
                checkin_date = datetime.strptime(
                    checkin["timestamp"], "%Y-%m-%d %H:%M:%S"
                )
                if checkin_date >= cutoff_date:
                    recent_checkins.append(checkin)
            except (ValueError, TypeError):
                continue

    return recent_checkins


@handle_errors("getting recent chat interactions", default_return=[])
def get_recent_chat_interactions(user_id: str, limit: int = 10):
    """Get recent chat interactions for a user."""
    return get_recent_responses(user_id, "chat_interaction", limit)


@handle_errors("checking if user checkins enabled", default_return=False)
def is_user_checkins_enabled(user_id: str) -> bool:
    """Check if check-ins are enabled for a user."""
    user_data_result = get_user_data(user_id, "account")
    user_account = user_data_result.get("account")
    if not user_account:
        return False

    return user_account.get("features", {}).get("checkins") == "enabled"


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
def track_user_response(user_id: str, category: str, response_data: dict[str, Any]):
    """Track a user's response to a message."""
    try:
        user_data_result = get_user_data(user_id, "account")
        user_account = user_data_result.get("account")
        if not user_account:
            logger.error(f"User account not found for tracking: {user_id}")
            return

        if category == "checkin":
            store_user_response(user_id, response_data, "checkin")
        elif category == "chat_interaction":
            # For chat interactions, we need user_message and ai_response
            user_message = response_data.get("user_message", "")
            ai_response = response_data.get("ai_response", "")
            context_used = response_data.get("context_used", False)
            store_chat_interaction(user_id, user_message, ai_response, context_used)
        else:
            # For other categories, store as generic response
            store_user_response(user_id, response_data, category)

        logger.info(f"Tracked {category} response for user {user_id}")

    except Exception as e:
        logger.error(f"Error tracking user response: {e}")
