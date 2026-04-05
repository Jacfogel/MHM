"""
User lifecycle and listing: get_all_user_ids, create_new_user, get_user_categories.
"""

import importlib
import os
import uuid
from pathlib import Path
from typing import Any

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.time_utilities import now_timestamp_full

from core.user_data_read import get_user_data
from core.user_data_write import save_user_data
from core.user_data_schedule_defaults import ensure_category_has_default_schedule

logger = get_component_logger("main")


@handle_errors(
    "resolving users directory for listing",
    default_return=None,
)
def _users_dir_for_listing() -> Path | None:
    """Resolve the directory that contains per-user folders (each with account.json).

    - Behavior tests patch ``core.config.USER_INFO_DIR_PATH`` to a custom tree; we must
      honor that (users live directly under that path).
    - Under pytest-xdist, ``core`` may be imported before ``MHM_TESTING=1`` is visible,
      so ``USER_INFO_DIR_PATH`` can still match the import-time default while the real
      test data lives under ``TEST_DATA_DIR/users``. When the configured path still
      equals ``Path(BASE_DATA_DIR) / "users"`` from that import, prefer the runtime
      default under testing.

    Returns None if path resolution fails (caller treats as no users dir).
    """
    import core.config as config
    from core.config import _normalize_path

    configured = Path(_normalize_path(str(config.USER_INFO_DIR_PATH)))
    import_time_default = Path(
        _normalize_path(str(Path(config.BASE_DATA_DIR) / "users"))
    )

    if os.getenv("MHM_TESTING") == "1":
        test_base = Path(
            _normalize_path(os.getenv("TEST_DATA_DIR", str(Path("tests") / "data")))
        )
        runtime_default_users = Path(_normalize_path(str(test_base / "users")))
    else:
        runtime_default_users = Path(
            _normalize_path(str(Path(config.BASE_DATA_DIR) / "users"))
        )

    cfg_s = os.path.normpath(str(configured))
    imp_s = os.path.normpath(str(import_time_default))
    if cfg_s == imp_s:
        return runtime_default_users
    return configured


@handle_errors("getting all user ids", default_return=[])
def get_all_user_ids() -> list[str]:
    """Get all user IDs from the system."""
    users_dir = _users_dir_for_listing()
    if users_dir is None or not users_dir.exists():
        return []
    user_ids = []
    for item in users_dir.iterdir():
        if item.is_dir():
            account_file = item / "account.json"
            if account_file.exists():
                user_ids.append(item.name)
    return user_ids


@handle_errors("creating new user", default_return=None)
def create_new_user(user_data: dict[str, Any]) -> str | None:
    """Create a new user with the new data structure."""
    user_id = str(uuid.uuid4())
    created_ts = now_timestamp_full()

    account_data = {
        "user_id": user_id,
        "internal_username": user_data.get("internal_username", ""),
        "account_status": "active",
        "chat_id": user_data.get("chat_id", ""),
        "phone": user_data.get("phone", ""),
        "email": user_data.get("email", ""),
        "discord_user_id": user_data.get("discord_user_id", ""),
        "created_at": created_ts,
        "updated_at": created_ts,
        "features": {
            "automated_messages": (
                "enabled" if user_data.get("messages_enabled", False) else "disabled"
            ),
            "checkins": (
                "enabled"
                if user_data.get("checkin_settings", {}).get("enabled", False)
                else "disabled"
            ),
            "task_management": (
                "enabled"
                if user_data.get("task_settings", {}).get("enabled", False)
                else "disabled"
            ),
        },
        "timezone": user_data.get("timezone", ""),
    }

    preferences_data = {
        "categories": user_data.get("categories", []),
        "channel": {"type": user_data.get("channel", {}).get("type", "email")},
        "checkin_settings": user_data.get("checkin_settings", {}),
        "task_settings": user_data.get("task_settings", {}),
    }
    if (
        "checkin_settings" in preferences_data
        and "enabled" in preferences_data["checkin_settings"]
    ):
        del preferences_data["checkin_settings"]["enabled"]
    if (
        "task_settings" in preferences_data
        and "enabled" in preferences_data["task_settings"]
    ):
        del preferences_data["task_settings"]["enabled"]

    context_data = {
        "preferred_name": user_data.get("preferred_name", ""),
        "gender_identity": user_data.get("gender_identity", []),
        "date_of_birth": user_data.get("date_of_birth", ""),
        "custom_fields": {
            "reminders_needed": user_data.get("reminders_needed", []),
            "health_conditions": user_data.get("custom_fields", {}).get(
                "health_conditions", []
            ),
            "medications_treatments": user_data.get("custom_fields", {}).get(
                "medications_treatments", []
            ),
            "allergies_sensitivities": user_data.get("custom_fields", {}).get(
                "allergies_sensitivities", []
            ),
        },
        "interests": user_data.get("interests", []),
        "goals": user_data.get("goals", []),
        "loved_ones": user_data.get("loved_ones", []),
        "activities_for_encouragement": user_data.get(
            "activities_for_encouragement", []
        ),
        "notes_for_ai": user_data.get("notes_for_ai", []),
        "created_at": created_ts,
        "last_updated": created_ts,
    }

    save_result = save_user_data(
        user_id,
        {
            "account": account_data,
            "preferences": preferences_data,
            "context": context_data,
        },
    )

    if not all(save_result.values()):
        logger.error(f"Failed to save user data for {user_id}: {save_result}")
        return None

    categories = user_data.get("categories", [])
    for category in categories:
        ensure_category_has_default_schedule(user_id, category)

    try:
        importlib.import_module("core.user_data_manager").update_user_index(user_id)
    except Exception as e:
        logger.warning(f"Failed to update user index for new user {user_id}: {e}")

    logger.info(
        f"Created new user: {user_id} ({user_data.get('internal_username', '')})"
    )
    return user_id


@handle_errors("getting user categories", default_return=[])
def get_user_categories(user_id: str) -> list[str]:
    """Get user's message categories using centralized data access."""
    user_data = get_user_data(user_id, "preferences")
    if isinstance(user_data, dict):
        preferences = user_data.get("preferences", {})
        if isinstance(preferences, dict):
            categories = preferences.get("categories", [])
            if isinstance(categories, list):
                return categories
    elif isinstance(user_data, list):
        return user_data
    return []
