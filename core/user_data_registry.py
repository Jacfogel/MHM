"""
Loader registry and default per-type load/save for user data.

Provides USER_DATA_LOADERS, register_data_loader, register_default_loaders,
get_available_data_types, get_data_type_info, and the default load/save
implementations for account, preferences, context, schedules, tags.
"""

import os
import time
import contextlib
from typing import Any
from collections.abc import Callable

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.config import ensure_user_directory, get_user_file_path
from core.file_operations import load_json_data, save_json_data
from core.time_utilities import now_timestamp_full
from core.schemas import (
    validate_account_dict,
    validate_preferences_dict,
    validate_schedules_dict,
)

logger = get_component_logger("main")

# Cache configuration (used by load_impl and clear_user_caches)
_cache_timeout = 300  # 5 minutes
_user_account_cache: dict = {}
_user_preferences_cache: dict = {}
_user_context_cache: dict = {}
_user_schedules_cache: dict = {}

_DEFAULT_USER_DATA_LOADERS: dict = {
    "account": {
        "loader": None,
        "file_type": "account",
        "default_fields": ["user_id", "internal_username", "account_status"],
        "metadata_fields": ["created_at", "updated_at"],
        "description": "User account information and settings",
    },
    "preferences": {
        "loader": None,
        "file_type": "preferences",
        "default_fields": ["categories", "channel"],
        "metadata_fields": ["last_updated"],
        "description": "User preferences and configuration",
    },
    "context": {
        "loader": None,
        "file_type": "user_context",
        "default_fields": ["preferred_name", "gender_identity"],
        "metadata_fields": ["created_at", "last_updated"],
        "description": "User context and personal information",
    },
    "schedules": {
        "loader": None,
        "file_type": "schedules",
        "default_fields": [],
        "metadata_fields": ["last_updated"],
        "description": "User schedule and timing preferences",
    },
    "tags": {
        "loader": None,
        "file_type": "tags",
        "default_fields": ["tags"],
        "metadata_fields": ["created_at", "updated_at"],
        "description": "User tags for tasks and notebook entries",
    },
}

if "USER_DATA_LOADERS" not in globals():
    USER_DATA_LOADERS: dict = {}

if not USER_DATA_LOADERS:
    USER_DATA_LOADERS.update(_DEFAULT_USER_DATA_LOADERS)


@handle_errors("registering data loader", default_return=False)
def register_data_loader(
    data_type: str,
    loader_func: Callable,
    file_type: str,
    default_fields: list[str] | None = None,
    metadata_fields: list[str] | None = None,
    description: str = "",
    *,
    force: bool = False,
) -> bool:
    """Register a new data loader for the centralized system."""
    if not data_type or not isinstance(data_type, str):
        logger.error(f"Invalid data_type: {data_type}")
        return False
    if not file_type or not isinstance(file_type, str):
        logger.error(f"Invalid file_type: {file_type}")
        return False
    if not callable(loader_func):
        logger.error(f"Invalid loader_func: {loader_func}")
        return False
    existing = USER_DATA_LOADERS.get(data_type)
    if existing is not None and existing.get("loader") is not None and not force:
        logger.debug(
            f"register_data_loader no-op for '{data_type}' (loader already set and force=False)"
        )
        return False
    USER_DATA_LOADERS[data_type] = {
        "loader": loader_func,
        "file_type": file_type,
        "default_fields": default_fields or [],
        "metadata_fields": metadata_fields or [],
        "description": description,
    }
    logger.info(f"Registered data loader for type: {data_type}")
    return True


_DEFAULT_LOADERS_REGISTERED = False


@handle_errors("registering default data loaders", default_return=None)
def register_default_loaders() -> None:
    """Ensure required loaders are registered (idempotent)."""
    required = [
        ("account", _get_user_data__load_account, "account"),
        ("preferences", _get_user_data__load_preferences, "preferences"),
        ("context", _get_user_data__load_context, "user_context"),
        ("schedules", _get_user_data__load_schedules, "schedules"),
        ("tags", _get_user_data__load_tags, "tags"),
    ]
    registered_loaders = []
    for key, func, ftype in required:
        entry = USER_DATA_LOADERS.get(key)
        if entry is None or entry.get("loader") is None:
            USER_DATA_LOADERS[key] = {
                "loader": func,
                "file_type": ftype,
                "default_fields": [],
                "metadata_fields": [],
                "description": f"Default {key} data loader",
            }
            registered_loaders.append(key)
    if registered_loaders:
        logger.debug(
            f"Registered data loaders: {', '.join(registered_loaders)} ({len(registered_loaders)} total)"
        )


@handle_errors("ensuring default loaders are registered once", default_return=None)
def _ensure_default_loaders_once() -> None:
    global _DEFAULT_LOADERS_REGISTERED
    if not _DEFAULT_LOADERS_REGISTERED:
        register_default_loaders()
        _DEFAULT_LOADERS_REGISTERED = True


@handle_errors("getting available data types", default_return=[])
def get_available_data_types() -> list[str]:
    """Get list of available data types."""
    return list(USER_DATA_LOADERS.keys())


@handle_errors("getting data type info", default_return=None)
def get_data_type_info(data_type: str) -> dict[str, Any] | None:
    """Get information about a specific data type."""
    return USER_DATA_LOADERS.get(data_type)


@handle_errors("loading user data via shared loader", default_return=None)
def _get_user_data__load_impl(
    user_id: str,
    auto_create: bool,
    cache_key_prefix: str,
    file_key: str,
    cache_dict: dict,
    default_data_factory: Callable[[str], dict[str, Any] | None],
    validate_fn: Callable[..., tuple[dict[str, Any], list]] | None,
    log_name: str,
    normalize_after_load: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Internal: common load flow for user data (cache, file, default, validate)."""
    if not user_id:
        return None
    current_time = time.time()
    cache_key = f"{cache_key_prefix}_{user_id}"
    if cache_key in cache_dict:
        cached_data, cache_time = cache_dict[cache_key]
        if current_time - cache_time < _cache_timeout:
            return cached_data
    user_dir = os.path.dirname(get_user_file_path(user_id, file_key))
    user_dir_exists = os.path.exists(user_dir)
    file_path = get_user_file_path(user_id, file_key)
    if not os.path.exists(file_path):
        if not auto_create:
            return None
        if not user_dir_exists:
            logger.debug(
                f"User directory doesn't exist for {user_id}, not auto-creating {log_name} file"
            )
            return None
        logger.info(
            f"Auto-creating missing {log_name} file for user {user_id} (user directory exists)"
        )
        ensure_user_directory(user_id)
        data = default_data_factory(user_id)
        if data is None:
            return None
        save_json_data(data, file_path)
    else:
        ensure_user_directory(user_id)
        data = load_json_data(file_path)
        if data is None and not auto_create:
            return None
        data = data or {}
        if normalize_after_load and isinstance(data, dict):
            data = normalize_after_load(data)
    if validate_fn and isinstance(data, dict):
        normalized, errors = validate_fn(data)
        if errors:
            logger.warning(
                f"Validation issues in {log_name} for user {user_id}: {'; '.join(errors)}"
            )
        if normalized and isinstance(normalized, dict) and len(normalized) > 0:
            data = normalized
    cache_dict[cache_key] = (data, current_time)
    return data


@handle_errors("building default account data", default_return=None)
def _account_default_data(user_id: str) -> dict[str, Any] | None:
    """Return default account dict for a user (e.g. when auto-creating)."""
    current_time_str = now_timestamp_full()
    return {
        "user_id": user_id,
        "internal_username": "",
        "account_status": "active",
        "chat_id": "",
        "phone": "",
        "email": "",
        "discord_user_id": "",
        "discord_username": "",
        "created_at": current_time_str,
        "updated_at": current_time_str,
        "features": {
            "automated_messages": "disabled",
            "checkins": "disabled",
            "task_management": "disabled",
        },
    }


def _account_normalize_after_load(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize account dict after load (ensure email, timezone)."""
    # error_handling_exclude: try/except preserves in-place mutation; caller is decorated
    try:
        if isinstance(data, dict):
            if "email" not in data:
                data["email"] = ""
            if not data.get("timezone"):
                data["timezone"] = "UTC"
    except Exception as e:
        logger.warning(f"Account normalize after load failed: {e}")
    return data


@handle_errors("loading user account data", default_return=None)
def _get_user_data__load_account(
    user_id: str, auto_create: bool = True
) -> dict[str, Any] | None:
    if not user_id:
        logger.error("_get_user_data__load_account called with None user_id")
        return None
    return _get_user_data__load_impl(
        user_id,
        auto_create,
        cache_key_prefix="account",
        file_key="account",
        cache_dict=_user_account_cache,
        default_data_factory=_account_default_data,
        validate_fn=validate_account_dict,
        log_name="account",
        normalize_after_load=_account_normalize_after_load,
    )


@handle_errors("saving user account data")
def _save_user_data__save_account(user_id: str, account_data: dict[str, Any]) -> bool:
    if not user_id:
        logger.error("_save_user_data__save_account called with None user_id")
        return False
    ensure_user_directory(user_id)
    account_file = get_user_file_path(user_id, "account")
    account_data["updated_at"] = now_timestamp_full()
    with contextlib.suppress(Exception):
        account_data, _errs = validate_account_dict(account_data)
    save_json_data(account_data, account_file)
    cache_key = f"account_{user_id}"
    _user_account_cache[cache_key] = (account_data, time.time())
    try:
        from core.user_data_manager import update_user_index
        update_user_index(user_id)
    except Exception as e:
        logger.warning(
            f"Failed to update user index after account update for user {user_id}: {e}"
        )
    logger.debug(f"Account data saved for user {user_id}")
    return True


@handle_errors("building default preferences data", default_return=None)
def _preferences_default_data(user_id: str) -> dict[str, Any] | None:
    """Return default preferences dict for a user (e.g. when auto-creating)."""
    return {
        "categories": [],
        "channel": {"type": "email"},
        "checkin_settings": {"enabled": False},
        "task_settings": {"enabled": False},
    }


@handle_errors("loading user preferences data", default_return=None)
def _get_user_data__load_preferences(
    user_id: str, auto_create: bool = True
) -> dict[str, Any] | None:
    if not user_id:
        logger.error("_get_user_data__load_preferences called with None user_id")
        return None
    return _get_user_data__load_impl(
        user_id,
        auto_create,
        cache_key_prefix="preferences",
        file_key="preferences",
        cache_dict=_user_preferences_cache,
        default_data_factory=_preferences_default_data,
        validate_fn=validate_preferences_dict,
        log_name="preferences",
    )


@handle_errors("saving user preferences data")
def _save_user_data__save_preferences(
    user_id: str, preferences_data: dict[str, Any]
) -> bool:
    if not user_id:
        logger.error("_save_user_data__save_preferences called with None user_id")
        return False
    ensure_user_directory(user_id)
    preferences_file = get_user_file_path(user_id, "preferences")
    with contextlib.suppress(Exception):
        preferences_data, _perrs = validate_preferences_dict(preferences_data)
    save_json_data(preferences_data, preferences_file)
    cache_key = f"preferences_{user_id}"
    _user_preferences_cache[cache_key] = (preferences_data, time.time())
    try:
        from core.user_data_manager import update_user_index
        update_user_index(user_id)
    except Exception as e:
        logger.warning(
            f"Failed to update user index after preferences update for user {user_id}: {e}"
        )
    logger.debug(f"Preferences data saved for user {user_id}")
    return True


@handle_errors("building default context data", default_return=None)
def _context_default_data(user_id: str) -> dict[str, Any] | None:
    """Return default user context dict (e.g. when auto-creating)."""
    current_time_str = now_timestamp_full()
    return {
        "preferred_name": "",
        "gender_identity": [],
        "date_of_birth": "",
        "custom_fields": {
            "reminders_needed": [],
            "health_conditions": [],
            "medications_treatments": [],
            "allergies_sensitivities": [],
        },
        "interests": [],
        "goals": [],
        "loved_ones": [],
        "activities_for_encouragement": [],
        "notes_for_ai": [],
        "created_at": current_time_str,
        "last_updated": current_time_str,
    }


@handle_errors("loading user context data", default_return=None)
def _get_user_data__load_context(
    user_id: str, auto_create: bool = True
) -> dict[str, Any] | None:
    if not user_id:
        logger.error("_get_user_data__load_context called with None user_id")
        return None
    return _get_user_data__load_impl(
        user_id,
        auto_create,
        cache_key_prefix="context",
        file_key="context",
        cache_dict=_user_context_cache,
        default_data_factory=_context_default_data,
        validate_fn=None,
        log_name="user context",
    )


@handle_errors("saving user context data")
def _save_user_data__save_context(user_id: str, context_data: dict[str, Any]) -> bool:
    if not user_id:
        logger.error("_save_user_data__save_context called with None user_id")
        return False
    ensure_user_directory(user_id)
    context_file = get_user_file_path(user_id, "context")
    context_data["last_updated"] = now_timestamp_full()
    save_json_data(context_data, context_file)
    cache_key = f"context_{user_id}"
    _user_context_cache[cache_key] = (context_data, time.time())
    try:
        from core.user_data_manager import update_user_index
        update_user_index(user_id)
    except Exception as e:
        logger.warning(
            f"Failed to update user index after context update for user {user_id}: {e}"
        )
    logger.debug(f"User context data saved for user {user_id}")
    return True


@handle_errors("building default schedules data", default_return=None)
def _schedules_default_data(user_id: str) -> dict[str, Any] | None:
    """Return default schedules dict for a user (e.g. when auto-creating)."""
    return {}


@handle_errors("loading user schedules data", default_return=None)
def _get_user_data__load_schedules(
    user_id: str, auto_create: bool = True
) -> dict[str, Any] | None:
    if not user_id:
        logger.error("_get_user_data__load_schedules called with None user_id")
        return None
    return _get_user_data__load_impl(
        user_id,
        auto_create,
        cache_key_prefix="schedules",
        file_key="schedules",
        cache_dict=_user_schedules_cache,
        default_data_factory=_schedules_default_data,
        validate_fn=validate_schedules_dict,
        log_name="schedules",
    )


@handle_errors("saving user schedules data")
def _save_user_data__save_schedules(
    user_id: str, schedules_data: dict[str, Any]
) -> bool:
    if not user_id:
        logger.error("_save_user_data__save_schedules called with None user_id")
        return False
    ensure_user_directory(user_id)
    schedules_file = get_user_file_path(user_id, "schedules")
    normalized, errors = validate_schedules_dict(schedules_data)
    if errors:
        logger.warning(
            f"Schedules validation reported {len(errors)} issue(s); saving normalized data"
        )
    schedules_data = normalized or {}
    save_json_data(schedules_data, schedules_file)
    cache_key = f"schedules_{user_id}"
    _user_schedules_cache[cache_key] = (schedules_data, time.time())
    logger.debug(f"Schedules data saved for user {user_id}")
    return True


@handle_errors("loading user tags data", default_return=None)
def _get_user_data__load_tags(
    user_id: str, auto_create: bool = True
) -> dict[str, Any] | None:
    if not user_id:
        logger.error("_get_user_data__load_tags called with None user_id")
        return None
    try:
        from core.tags import load_user_tags
        tags_data = load_user_tags(user_id)
        if not tags_data and not auto_create:
            return None
        if not tags_data:
            return {"tags": []}
        return tags_data
    except Exception as e:
        logger.error(f"Error loading tags for user {user_id}: {e}")
        return None


@handle_errors("saving user tags data")
def _save_user_data__save_tags(user_id: str, tags_data: dict[str, Any]) -> bool:
    if not user_id:
        logger.error("_save_user_data__save_tags called with None user_id")
        return False
    try:
        from core.tags import save_user_tags
        return save_user_tags(user_id, tags_data)
    except Exception as e:
        logger.error(f"Error saving tags for user {user_id}: {e}")
        return False


@handle_errors("clearing user caches")
def clear_user_caches(user_id: str | None = None) -> None:
    """Clear user data caches."""
    global _user_account_cache, _user_preferences_cache, _user_context_cache, _user_schedules_cache
    if user_id:
        account_key = f"account_{user_id}"
        preferences_key = f"preferences_{user_id}"
        context_key = f"context_{user_id}"
        schedules_key = f"schedules_{user_id}"
        if account_key in _user_account_cache:
            del _user_account_cache[account_key]
        if preferences_key in _user_preferences_cache:
            del _user_preferences_cache[preferences_key]
        if context_key in _user_context_cache:
            del _user_context_cache[context_key]
        if schedules_key in _user_schedules_cache:
            del _user_schedules_cache[schedules_key]
        logger.debug(f"Cleared cache for user {user_id}")
    else:
        _user_account_cache.clear()
        _user_preferences_cache.clear()
        _user_context_cache.clear()
        _user_schedules_cache.clear()
        logger.debug("Cleared all user caches")
