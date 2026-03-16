"""
High-level update helpers: update_user_schedules, update_user_account,
update_user_preferences, update_user_context, update_channel_preferences.
"""

import os
from typing import Any

from core.logger import get_component_logger
from core.error_handling import handle_errors

from core.user_data_read import get_user_data
from core.user_data_write import save_user_data
from core.user_data_schedule_defaults import (
    ensure_category_has_default_schedule,
    ensure_all_categories_have_schedules,
)

logger = get_component_logger("main")


@handle_errors("validating user_id", default_return=False)
def _validate_user_id(user_id: str) -> bool:
    """Validate user_id is a non-empty string. Log and return False if invalid."""
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return False
    if not user_id.strip():
        logger.error("Empty user_id provided")
        return False
    return True


@handle_errors("validating user_id and dict", default_return=False)
def _validate_user_id_and_dict(
    user_id: str, data: Any, dict_name: str
) -> bool:
    """Validate user_id and that data is a dict. Log and return False if invalid."""
    if not _validate_user_id(user_id):
        return False
    if not isinstance(data, dict):
        logger.error(f"Invalid {dict_name}: {type(data)}")
        return False
    return True


@handle_errors("updating user section", default_return=False)
def _update_user_section(
    user_id: str,
    section_key: str,
    data: dict[str, Any],
    *,
    auto_create: bool = True,
) -> bool:
    """Save a single user-data section and return whether that section was saved."""
    result = save_user_data(
        user_id, {section_key: data}, auto_create=auto_create
    )
    return result.get(section_key, False)


# not_duplicate: user_data_updates_section
@handle_errors("updating user schedules (centralised)", default_return=False)
def update_user_schedules(user_id: str, schedules_data: dict[str, Any]) -> bool:
    if not _validate_user_id(user_id):
        return False
    if not isinstance(schedules_data, dict):
        logger.error(f"Invalid schedules_data: {type(schedules_data)}")
        return False
    return _update_user_section(user_id, "schedules", schedules_data)


# not_duplicate: user_data_updates_section
@handle_errors("updating user account (centralised)", default_return=False)
def update_user_account(
    user_id: str, updates: dict[str, Any], *, auto_create: bool = True
) -> bool:
    if not _validate_user_id_and_dict(user_id, updates, "updates"):
        return False
    return _update_user_section(
        user_id, "account", updates, auto_create=auto_create
    )


@handle_errors("updating user preferences (centralised)", default_return=False)
def update_user_preferences(
    user_id: str, updates: dict[str, Any], *, auto_create: bool = True
) -> bool:
    if not _validate_user_id_and_dict(user_id, updates, "updates"):
        return False

    if not auto_create:
        try:
            from core.config import get_user_data_dir as _get_user_data_dir
            if not os.path.exists(_get_user_data_dir(user_id)):
                return False
        except Exception:
            return False

    if "categories" in updates:
        try:
            from core.message_management import ensure_user_message_files

            preferences_data = get_user_data(user_id, "preferences")
            if preferences_data is None:
                logger.warning(
                    f"Could not load or create preferences for user {user_id}"
                )
            else:
                prefs_dict = (
                    preferences_data.get("preferences", {})
                    if isinstance(preferences_data, dict)
                    else {}
                )
                old_categories = set(
                    prefs_dict.get("categories", [])
                    if isinstance(prefs_dict, dict)
                    else []
                )
                new_categories = set(updates["categories"])
                added_categories = new_categories - old_categories

                if added_categories:
                    logger.info(
                        f"Categories update detected for user {user_id}: added={added_categories}"
                    )
                for category in added_categories:
                    ensure_category_has_default_schedule(user_id, category)
                ensure_all_categories_have_schedules(user_id, suppress_logging=True)
                if added_categories:
                    try:
                        result_files = ensure_user_message_files(
                            user_id, list(added_categories)
                        )
                        if result_files.get("success"):
                            logger.info(
                                f"Category update for user {user_id}: created {result_files.get('files_created')} message files for {len(added_categories)} new categories (directory_created={result_files.get('directory_created')})"
                            )
                        else:
                            logger.warning(
                                f"Category update for user {user_id}: message file creation partially failed - created {result_files.get('files_created')}/{len(added_categories)} files"
                            )
                    except Exception as e:
                        logger.error(
                            f"Error creating message files for user {user_id} after category update: {e}",
                            exc_info=True,
                        )
                else:
                    if new_categories:
                        try:
                            result_files = ensure_user_message_files(
                                user_id, list(new_categories)
                            )
                            if result_files.get("files_created", 0) > 0:
                                logger.info(
                                    f"Category update for user {user_id}: created {result_files.get('files_created')} missing message files for existing categories"
                                )
                        except Exception as e:
                            logger.warning(
                                f"Error ensuring message files for user {user_id} existing categories: {e}"
                            )
        except Exception as err:
            logger.warning(
                f"Category bookkeeping skipped for user {user_id} due to import error: {err}"
            )

    result = save_user_data(user_id, {"preferences": updates}, auto_create=auto_create)
    return result.get("preferences", False)


# not_duplicate: user_data_updates_section
@handle_errors("updating user context (centralised)", default_return=False)
def update_user_context(
    user_id: str, updates: dict[str, Any], *, auto_create: bool = True
) -> bool:
    if not _validate_user_id_and_dict(user_id, updates, "updates"):
        return False
    return _update_user_section(
        user_id, "context", updates, auto_create=auto_create
    )


# not_duplicate: user_data_updates_section
@handle_errors("updating channel preferences (centralised)", default_return=False)
def update_channel_preferences(
    user_id: str, updates: dict[str, Any], *, auto_create: bool = True
) -> bool:
    if not _validate_user_id_and_dict(user_id, updates, "updates"):
        return False
    return _update_user_section(
        user_id, "preferences", updates, auto_create=auto_create
    )
