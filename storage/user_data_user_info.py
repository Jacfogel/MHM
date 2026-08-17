"""Shared user-info helpers for storage ops (index, backup, summaries).

Leaf module: no imports from user_data_backup, user_data_index, or
user_data_summaries. Used to list message files and build the lightweight
user-info dict consumed by admin operations.
"""

from __future__ import annotations

import importlib
import os
import time
from pathlib import Path
from typing import Any

from core.error_handling import handle_errors
from core.file_operations import get_user_data_dir
from core.logger import get_component_logger
from storage.user_data_read import get_user_data

logger = get_component_logger("main")


# duplicate_functions_exclude: importlib delegate to core.user_management.get_user_categories.
@handle_errors("resolving user categories", default_return=[])
def _get_user_categories(user_id: str):
    """Resolve categories without a static import (breaks user_management cycle in tooling)."""
    return importlib.import_module("core.user_management").get_user_categories(user_id)


@handle_errors("getting user info for data manager", default_return=None)
def get_user_info_for_data_manager(user_id: str) -> dict[str, Any] | None:
    """
    Get user info using the centralized data structure with validation.

    Returns:
        Optional[Dict[str, Any]]: User info dict or None if failed
    """
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return None

    if not user_id.strip():
        logger.error("Empty user_id provided")
        return None

    try:
        user_data = None
        max_retries = 5
        retry_delay = 0.2
        for attempt in range(max_retries):
            user_data = get_user_data(user_id, "all", auto_create=True)
            if user_data and isinstance(user_data, dict) and len(user_data) > 0:
                account_data = user_data.get("account", {})
                if account_data and account_data.get("internal_username"):
                    break
            if attempt < max_retries - 1:
                time.sleep(retry_delay)

        if not user_data or (isinstance(user_data, dict) and len(user_data) == 0):
            return None

        account_data = user_data.get("account", {})
        context_data = user_data.get("context", {})

        user_info = {
            "user_id": user_id,
            "internal_username": account_data.get("internal_username", ""),
            "preferred_name": context_data.get("preferred_name", ""),
            "account_status": account_data.get("account_status", "unknown"),
            "email": account_data.get("email", ""),
            "message_files": {},
        }

        categories = _get_user_categories(user_id)
        for category in categories:
            category_path = str(
                Path(get_user_data_dir(user_id)) / "messages" / f"{category}.json"
            )
            user_info["message_files"][category] = {
                "path": category_path,
                "exists": os.path.exists(category_path),
            }

        return user_info

    except Exception as e:
        logger.error(f"Error getting user info for data manager: {e}")
        return None


@handle_errors("getting user message files", default_return={})
def get_user_message_files(user_id: str) -> dict[str, str]:
    """Get all existing message file paths for a user."""
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return {}

    if not user_id.strip():
        logger.error("Empty user_id provided")
        return {}

    user_info = get_user_info_for_data_manager(user_id)
    if not user_info:
        return {}

    if "message_files" in user_info:
        return {
            cat: info["path"]
            for cat, info in user_info["message_files"].items()
            if info["exists"]
        }

    prefs_result = get_user_data(user_id, "preferences")
    categories = prefs_result.get("preferences", {}).get("categories", [])
    if not categories:
        return {}

    message_files = {}
    for category in categories:
        message_file = str(
            Path(get_user_data_dir(user_id)) / "messages" / f"{category}.json"
        )
        if os.path.exists(message_file):
            message_files[category] = message_file

    return message_files


@handle_errors("updating message references", default_return=False)
def update_message_references(user_id: str) -> bool:
    """Add/update message file references for a user (logged; not persisted)."""
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return False

    if not user_id.strip():
        logger.error("Empty user_id provided")
        return False

    user_dir = get_user_data_dir(user_id)
    if not os.path.exists(user_dir):
        logger.error(f"User {user_id} not found: user directory does not exist")
        return False

    user_info = None
    for attempt in range(3):
        user_info = get_user_info_for_data_manager(user_id)
        if user_info:
            break
        if attempt < 2:
            time.sleep(0.1)

    if not user_info:
        logger.error(f"User {user_id} not found after retries")
        return False

    account_data = {}
    for attempt in range(3):
        account_result = get_user_data(user_id, "account")
        account_data = account_result.get("account", {})
        if account_data:
            break
        if attempt < 2:
            time.sleep(0.1)

    features = account_data.get("features", {})
    automated_messages_enabled = (
        features.get("automated_messages", "disabled") == "enabled"
    )

    categories = []
    for attempt in range(3):
        prefs_result = get_user_data(user_id, "preferences")
        categories = prefs_result.get("preferences", {}).get("categories", [])
        if categories or attempt == 2:
            break
        if attempt < 2:
            time.sleep(0.1)
    if not categories:
        if automated_messages_enabled:
            logger.warning(
                f"No categories found for user {user_id} (automated messages enabled)"
            )
        else:
            logger.debug(
                f"No categories found for user {user_id} (automated messages disabled)"
            )
        return True

    message_refs = {}
    for category in categories:
        message_file = str(
            Path(get_user_data_dir(user_id)) / "messages" / f"{category}.json"
        )
        if os.path.exists(message_file):
            message_refs[category] = {
                "path": message_file,
                "exists": True,
                "last_modified": os.path.getmtime(message_file),
            }
        else:
            message_refs[category] = {
                "path": message_file,
                "exists": False,
                "last_modified": None,
            }

    logger.info(
        f"Updated message references for user {user_id}: {list(message_refs.keys())}"
    )
    return True
