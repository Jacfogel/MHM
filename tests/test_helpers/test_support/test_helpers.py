"""Standalone test helpers (not pytest fixtures).

These functions are used by tests and optionally by fixtures. They live here to keep
tests/conftest.py focused on configuration and fixtures. Import from this module or
from tests.conftest (re-exported for convenience).
"""


def wait_until(predicate, timeout_seconds: float = 1.0, poll_seconds: float = 0.005):
    """Poll predicate() until it returns True or timeout elapses.

    Returns True if predicate succeeds within timeout, otherwise False.
    """
    import time as _time

    deadline = _time.perf_counter() + timeout_seconds
    while _time.perf_counter() < deadline:
        try:
            if predicate():
                return True
        except Exception:
            # Ignore transient errors while waiting
            pass
        _time.sleep(poll_seconds)
    return False


def materialize_user_minimal_via_public_apis(user_id: str) -> dict:
    """Ensure minimal structures exist without overwriting existing data.

    - Merges into existing account (preserves internal_username and enabled features)
    - Adds missing preferences keys (keeps existing categories/channel)
    - Adds a default motivational/morning period if schedules missing
    """
    from core.user_data_handlers import (
        get_user_data,
        update_user_account,
        update_user_preferences,
        update_user_schedules,
    )
    from core.user_data_handlers import get_user_id_by_identifier
    from core.config import get_user_data_dir
    import os

    # Resolve UUID if user_id is an internal username (race condition fix)
    # get_user_data_dir uses user_id directly, so we need to resolve UUIDs first
    resolved_user_id = user_id
    if not os.path.exists(get_user_data_dir(user_id)):
        # Try to resolve UUID from internal username
        from tests.test_helpers.test_utilities import TestUserFactory as TUF

        uuid_resolved = get_user_id_by_identifier(
            user_id
        ) or TUF.get_test_user_id_by_internal_username(
            user_id, os.getenv("TEST_DATA_DIR", "tests/data")
        )
        if uuid_resolved and uuid_resolved != user_id:
            resolved_user_id = uuid_resolved
            # Verify resolved UUID directory exists
            if os.path.exists(get_user_data_dir(resolved_user_id)):
                user_id = resolved_user_id

    # Ensure user directory exists before proceeding (race condition fix)
    user_dir = get_user_data_dir(user_id)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir, exist_ok=True)

    # Load current state
    current_all = get_user_data(user_id, "all") or {}
    current_account = current_all.get("account") or {}
    current_prefs = current_all.get("preferences") or {}
    current_schedules = current_all.get("schedules") or {}

    # Account: preserve existing values; set sensible defaults where missing
    merged_features = dict(current_account.get("features") or {})
    if "automated_messages" not in merged_features:
        merged_features["automated_messages"] = "enabled"
    if "task_management" not in merged_features:
        merged_features["task_management"] = "disabled"
    if "checkins" not in merged_features:
        merged_features["checkins"] = "disabled"

    account_updates = {
        "user_id": current_account.get("user_id") or user_id,
        "internal_username": current_account.get("internal_username") or user_id,
        "account_status": current_account.get("account_status") or "active",
        "features": merged_features,
    }
    update_user_account(user_id, account_updates)

    # Preferences: add missing keys only
    # Always ensure preferences exist (even if empty) to prevent get_user_data returning empty dict
    prefs_updates = {}
    if not current_prefs.get("categories"):
        prefs_updates["categories"] = ["motivational"]
    if not current_prefs.get("channel"):
        prefs_updates["channel"] = {"type": "discord", "contact": "test#1234"}
    # Always update preferences to ensure file exists (race condition fix)
    if prefs_updates or not current_prefs:
        update_user_preferences(user_id, prefs_updates)

    # Schedules: ensure schedules exist for all categories in preferences; merge into existing
    schedules_updates = current_schedules if isinstance(current_schedules, dict) else {}
    # Get categories from preferences (or default to motivational)
    categories = current_prefs.get("categories", ["motivational"])
    if not categories:
        categories = ["motivational"]

    # Ensure schedules exist for all categories
    for category in categories:
        schedules_updates.setdefault(category, {}).setdefault("periods", {})
        # Add a default morning period if none exists
        if "morning" not in schedules_updates[category]["periods"]:
            schedules_updates[category]["periods"]["morning"] = {
                "active": True,
                "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "start_time": "09:00",
                "end_time": "12:00",
            }
    update_user_schedules(user_id, schedules_updates)

    # Ensure context exists
    get_user_data(user_id, "context")
    return get_user_data(user_id, "all")
