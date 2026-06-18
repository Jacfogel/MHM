"""
Admin account provisioning - channel-agnostic account creation from admin UI data.

Extracted from ui/dialogs/account_creator_dialog.py so provisioning logic is
shared, testable, and not tied to Qt widgets.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

from core.error_handling import handle_errors
from core.file_operations import create_user_files
from core.logger import get_component_logger
from storage.user_data_operations import update_user_index

logger = get_component_logger("user_management")


@handle_errors("determining chat ID", default_return="")
def determine_chat_id(
    channel_type: str, email: str, phone: str, discord_user_id: str
) -> str:
    """Determine chat_id based on channel type."""
    if channel_type == "email":
        return email
    if channel_type == "discord":
        return discord_user_id
    return ""


@handle_errors("building features dictionary", default_return={})
def build_features_dict(features_enabled: dict[str, bool]) -> dict[str, str]:
    """Build features dictionary in the account.json format."""
    return {
        "automated_messages": (
            "enabled" if features_enabled.get("messages", False) else "disabled"
        ),
        "checkins": (
            "enabled" if features_enabled.get("checkins", False) else "disabled"
        ),
        "task_management": (
            "enabled" if features_enabled.get("tasks", False) else "disabled"
        ),
    }


@handle_errors("building user preferences from account data", default_return={})
def build_user_preferences_from_account_data(
    account_data: dict[str, Any],
) -> dict[str, Any]:
    """Build the user_preferences dict passed to create_user_files."""
    contact_info = account_data["contact_info"]
    features_enabled = account_data.get("features_enabled", {})

    email = contact_info.get("email", "")
    phone = contact_info.get("phone", "")
    discord_user_id = contact_info.get("discord", "")

    chat_id = determine_chat_id(
        account_data["channel"]["type"], email, phone, discord_user_id
    )
    features = build_features_dict(features_enabled)

    user_preferences: dict[str, Any] = {
        "internal_username": account_data["username"],
        "chat_id": chat_id,
        "phone": phone,
        "email": email,
        "discord_user_id": discord_user_id,
        "discord_username": contact_info.get("discord_username", ""),
        "timezone": account_data["timezone"],
        "channel": account_data["channel"],
        "categories": account_data["categories"],
        "features": features,
        "personalization_data": account_data.get("personalization_data", {}),
        "features_enabled": features_enabled,
    }

    if features_enabled.get("tasks", False):
        task_settings = account_data.get("task_settings", {}).copy()
        task_settings.pop("enabled", None)
        user_preferences["task_settings"] = task_settings

    if features_enabled.get("checkins", False):
        checkin_settings = account_data.get("checkin_settings", {}).copy()
        checkin_settings.pop("enabled", None)
        user_preferences["checkin_settings"] = checkin_settings

    return user_preferences


@handle_errors("waiting for user files", default_return=None)
def wait_for_user_files_ready(user_id: str, max_wait_attempts: int = 10) -> bool:
    """Wait until account.json and preferences.json are readable with expected data."""
    from core import get_user_data
    from core.config import get_user_data_dir

    account_file = Path(get_user_data_dir(user_id)) / "account.json"
    preferences_file = Path(get_user_data_dir(user_id)) / "preferences.json"
    wait_delay = 0.05

    for attempt in range(max_wait_attempts):
        try:
            if account_file.exists() and preferences_file.exists():
                test_account = get_user_data(user_id, "account")
                test_prefs = get_user_data(user_id, "preferences")
                if (
                    test_account
                    and test_account.get("account", {}).get("internal_username")
                    and test_prefs
                    and test_prefs.get("preferences")
                ):
                    return True
        except Exception:
            pass

        if attempt < max_wait_attempts - 1:
            time.sleep(wait_delay)

    return False


@handle_errors("setting up task tags for new user", default_return=None)
def setup_task_tags_for_new_user(user_id: str, account_data: dict[str, Any]) -> None:
    """Set up custom or default task tags when task management is enabled."""
    features_enabled = account_data.get("features_enabled", {})
    if not features_enabled.get("tasks", False):
        return

    task_settings = account_data.get("task_settings", {})
    custom_tags = task_settings.get("tags", [])

    if custom_tags:
        from tasks import add_user_task_tag

        for tag in custom_tags:
            add_user_task_tag(user_id, tag)
        logger.info(
            f"Saved {len(custom_tags)} custom tags for new user {user_id}: {custom_tags}"
        )
        return

    from tasks import setup_default_task_tags

    setup_default_task_tags(user_id)
    logger.info(f"Set up default task tags for new user {user_id}")


@handle_errors("updating user index with retry", default_return=None)
def update_user_index_with_retry(user_id: str, max_retries: int = 5) -> None:
    """Update user index with retries to handle parallel test race conditions."""
    from core import get_user_data, get_user_id_by_identifier

    retry_delay = 0.1

    for attempt in range(max_retries):
        try:
            test_data = get_user_data(user_id, "account")
            if not test_data or not test_data.get("account", {}).get(
                "internal_username"
            ):
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                logger.warning(
                    f"Account data not ready for user {user_id} after {max_retries} attempts"
                )
                return

            success = update_user_index(user_id)
            if not success:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                logger.warning(
                    f"Failed to update user index for user {user_id} after {max_retries} attempts"
                )
                return

            internal_username = test_data.get("account", {}).get("internal_username")
            if not internal_username:
                break

            time.sleep(0.2)
            found_user_id = None
            for verify_attempt in range(3):
                found_user_id = get_user_id_by_identifier(internal_username)
                if found_user_id == user_id:
                    time.sleep(0.1)
                    break
                if verify_attempt < 2:
                    time.sleep(0.1)

            if found_user_id == user_id:
                break
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            logger.warning(
                f"User index not updated correctly for user {user_id} "
                f"(internal_username: {internal_username}) after {max_retries} attempts"
            )
        except Exception as retry_error:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            logger.warning(
                f"Error updating user index for user {user_id} "
                f"after {max_retries} attempts: {retry_error}"
            )


@handle_errors("scheduling new user", default_return=None)
def schedule_new_user_if_available(user_id: str) -> None:
    """Register the new user with the scheduler when the service is running."""
    try:
        from core.service import get_scheduler_manager

        scheduler_manager = get_scheduler_manager()
        if scheduler_manager:
            scheduler_manager.schedule_new_user(user_id)
            logger.info(f"Scheduled new user {user_id} in scheduler")
        else:
            logger.warning(
                f"Scheduler manager not available, new user {user_id} not scheduled"
            )
    except Exception as e:
        logger.warning(f"Failed to schedule new user {user_id} in scheduler: {e}")


@handle_errors("provisioning admin account", default_return=None)
def provision_admin_account(account_data: dict[str, Any]) -> str | None:
    """
    Create a full admin-provisioned user account from collected dialog data.

    Returns the new user_id on success, or None on failure.
    """
    user_id = str(uuid.uuid4())
    user_preferences = build_user_preferences_from_account_data(account_data)

    create_user_files(user_id, account_data["categories"], user_preferences)

    if not wait_for_user_files_ready(user_id):
        logger.warning(
            f"User files not fully readable after wait for user {user_id}; continuing"
        )

    setup_task_tags_for_new_user(user_id, account_data)

    # Ensure preferences are saved before index update (parallel test safety).
    time.sleep(0.1)

    update_user_index_with_retry(user_id)
    schedule_new_user_if_available(user_id)

    logger.info(f"Created new user: {user_id} ({account_data['username']})")
    return user_id
