# file_operations.py
"""
File operations utilities for MHM.
Contains functions for file I/O, path determination, and file management.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from core.logger import get_component_logger
from core.config import (
    DEFAULT_MESSAGES_DIR_PATH,
    get_user_file_path,
    ensure_user_directory,
    get_user_data_dir,
)
from core.error_handling import FileOperationError, handle_file_error, handle_errors
from core.service_utilities import now_readable_timestamp

try:
    from core.file_auditor import record_created as _record_created
except Exception:
    _record_created = None

logger = get_component_logger("file_ops")


@handle_errors("verifying file access", user_friendly=False, default_return=False)
def verify_file_access(paths):
    """
    Verify that files exist and are accessible.

    Args:
        paths: List of file paths to verify

    Returns:
        bool: True if all files exist and are accessible, False otherwise

    Raises:
        FileOperationError: If any file is not found or inaccessible
    """
    # Validate input
    if not paths or not isinstance(paths, (list, tuple)):
        logger.error(f"Invalid paths provided: {paths}")
        return False

    for path in paths:
        if not path or not isinstance(path, str):
            logger.error(f"Invalid path in list: {path}")
            return False

        if not os.path.exists(path):
            raise FileOperationError(f"File not found at path: {path}")
        else:
            logger.debug(f"File verified: {path}")

    return True


@handle_errors("determining file path", user_friendly=False, default_return="")
def determine_file_path(file_type, identifier):
    """
    Determine file path based on file type and identifier.
    Updated to support new organized structure.

    Args:
        file_type: Type of file ('users', 'messages', 'schedules', 'sent_messages', 'default_messages', 'tasks')
        identifier: Identifier for the file (format depends on file_type)

    Returns:
        str: Full file path, empty string if invalid

    Raises:
        FileOperationError: If file_type is unknown or identifier format is invalid
    """
    # Validate inputs
    if not file_type or not isinstance(file_type, str):
        logger.error(f"Invalid file_type: {file_type}")
        return ""

    if not identifier or not isinstance(identifier, str):
        logger.error(f"Invalid identifier: {identifier}")
        return ""
    if file_type == "users":
        return get_user_file_path(identifier, "account")
    elif file_type == "messages":
        # New structure: data/users/{user_id}/messages/{category}.json
        try:
            category, user_id = identifier.split("/")
            user_dir = Path(get_user_data_dir(user_id))
            path = user_dir / "messages" / f"{category}.json"
        except ValueError as e:
            raise FileOperationError(
                f"Invalid identifier format '{identifier}': expected 'category/user_id'"
            )
    elif file_type == "schedules":
        # Optional: per-category schedules
        try:
            category, user_id = identifier.split("/")
            user_dir = Path(get_user_data_dir(user_id))
            path = user_dir / "schedules" / f"{category}.json"
        except ValueError:
            # Default to single schedules.json if not per-category
            user_dir = Path(get_user_data_dir(identifier))
            path = user_dir / "schedules.json"
    elif file_type == "sent_messages":
        return get_user_file_path(identifier, "sent_messages")
    elif file_type == "default_messages":
        path = Path(DEFAULT_MESSAGES_DIR_PATH) / f"{identifier}.json"
    elif file_type == "tasks":
        # New task file structure: data/users/{user_id}/tasks/{task_file}.json
        try:
            user_id, task_file = identifier.split("/")
            user_dir = Path(get_user_data_dir(user_id))
            path = user_dir / "tasks" / f"{task_file}.json"
        except ValueError as e:
            raise FileOperationError(
                f"Invalid task identifier format '{identifier}': expected 'user_id/task_file'"
            )
    else:
        raise FileOperationError(f"Unknown file type: {file_type}")

    # Only log file paths for non-routine operations (not messages or user data operations)
    if file_type not in ["messages", "users", "sent_messages"]:
        logger.debug(f"Determined file path for {file_type}: {path}")
    return str(path)


@handle_errors("loading JSON data", default_return={})
def load_json_data(file_path):
    """
    Load data from a JSON file with comprehensive error handling and auto-create user files if missing.

    Args:
        file_path: Path to the JSON file to load

    Returns:
        dict/list: Loaded JSON data, or empty dict if loading failed
    """
    # Validate input
    if not file_path or not isinstance(file_path, str):
        logger.error(f"Invalid file_path: {file_path}")
        return {}

    if not file_path.strip():
        logger.error("Empty file_path provided")
        return {}

    context = {"file_path": file_path}

    try:
        with open(file_path, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as e:
        # Use specialized file error handler for better recovery
        if not handle_file_error(e, file_path, "loading JSON data"):
            logger.error(f"File not found and recovery failed: {file_path}")
            return {}
        # Try to auto-create user files if this is a user file
        # NOTE: Don't auto-create message files - let add_message handle that
        # Only auto-create core user files (account, preferences, etc.)
        # Detect user files by path
        if "users" in file_path and "messages" not in file_path:
            # Try to extract user_id from the path
            import re

            match = re.search(r"users[\\/](.*?)[\\/]", file_path)
            user_id = None
            if match:
                user_id = match.group(1)
            else:
                # Try legacy structure
                match = re.search(r"users[\\/](.*?)(?:\\|/|\.|$)", file_path)
                if match:
                    user_id = match.group(1)
            if user_id:
                # Try to guess categories if possible (for schedules)
                categories = []
                if "schedules" in file_path:
                    # Try to find categories from existing files or default to ['motivational']
                    categories = ["motivational"]
                create_user_files(
                    user_id, categories, None
                )  # No user preferences available in auto-creation
                logger.info(f"Auto-created missing user files for user_id {user_id}")
                # Try loading again
                try:
                    with open(file_path, encoding="utf-8") as file:
                        return json.load(file)
                except Exception as e2:
                    logger.error(f"Failed to load file after auto-creation: {e2}")
                    return None
        if handle_file_error(e, file_path, "loading JSON data"):
            # Recovery was successful, try loading again
            try:
                with open(file_path, encoding="utf-8") as file:
                    return json.load(file)
            except Exception as e2:
                logger.error(f"Failed to load file after recovery: {e2}")
                return None
        else:
            logger.error(f"File not found and recovery failed: {file_path}")
            return None
    except json.JSONDecodeError as e:
        if handle_file_error(e, file_path, "decoding JSON data"):
            # Recovery was successful, try loading again
            try:
                with open(file_path, encoding="utf-8") as file:
                    return json.load(file)
            except Exception as e2:
                logger.error(f"Failed to load file after JSON recovery: {e2}")
                return {}
        else:
            logger.error(f"JSON decode error and recovery failed: {file_path}")
            return {}
    except Exception as e:
        logger.error(f"Unexpected error loading data from {file_path}: {e}")
        return {}


@handle_errors("saving JSON data", user_friendly=False, default_return=False)
def save_json_data(data, file_path):
    """
    Save data to a JSON file with comprehensive error handling.

    Args:
        data: Data to save (must be JSON serializable)
        file_path: Path where to save the file

    Returns:
        bool: True if successful, False if failed

    Raises:
        FileOperationError: If saving fails
    """
    # Validate inputs
    if file_path is None or not isinstance(file_path, str):
        logger.error(f"Invalid file_path: {file_path}")
        return False

    if not file_path.strip():
        logger.error("Empty file_path provided")
        return False

    if data is None:
        logger.error("None data provided to save_json_data")
        return False
    # Atomic write with temp file and replace to avoid partial writes
    file_path = Path(file_path)
    directory = file_path.parent

    # Ensure directory exists
    if not directory.exists():
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
        except Exception as e:
            raise FileOperationError(f"Failed to create directory {directory}: {e}")

    # Save the data
    tmp_path = None
    try:
        # Ensure directory exists before writing (race condition fix)
        directory.mkdir(parents=True, exist_ok=True)

        tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        try:
            os.replace(tmp_path, file_path)
            # On successful replace, tmp_path no longer exists (it became file_path)
        except PermissionError:
            # Windows can hold the target briefly; retry once after short delay
            try:
                import time as _t

                _t.sleep(0.05)
                os.replace(tmp_path, file_path)
                # On successful replace, tmp_path no longer exists
            except Exception as e:
                # As a last resort, attempt shutil.move
                try:
                    import shutil as _sh

                    _sh.move(str(tmp_path), str(file_path))
                    # On successful move, tmp_path no longer exists
                except Exception:
                    # All attempts failed - re-raise the original error
                    raise
        logger.debug(f"Successfully saved data to {file_path}")
        try:
            if _record_created:
                _record_created(str(file_path), reason="save_json_data")
        except Exception:
            pass
        return True
    except Exception as e:
        # Clean up temp file if it exists and wasn't successfully moved/replaced
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                # Best effort cleanup - log but don't fail on cleanup error
                logger.debug(
                    f"Failed to clean up temp file {tmp_path}, but continuing with error handling"
                )
        raise FileOperationError(f"Failed to save data to {file_path}: {e}")


@handle_errors("creating user files", user_friendly=True, default_return=False)
def create_user_files(user_id, categories, user_preferences=None):
    """
    Creates files for a new user in the appropriate structure.
    Ensures schedules.json contains a block for each category, plus checkin and task reminder blocks.

    Args:
        user_id: The user ID
        categories: List of message categories the user is opted into
        user_preferences: Optional user preferences dict to determine which files to create

    Returns:
        bool: True if successful, False if failed
    """
    # Validate inputs
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return False

    if not user_id.strip():
        logger.error("Empty user_id provided")
        return False

    if categories is not None and not isinstance(categories, (list, tuple)):
        logger.error(f"Invalid categories type: {type(categories)}")
        return False
    ensure_user_directory(user_id)

    # Always use a dict for user_prefs to avoid NoneType errors
    user_prefs = user_preferences or {}

    tasks_enabled, checkins_enabled = _create_user_files__determine_feature_enablement(
        user_prefs
    )

    _create_user_files__account_file(
        user_id, user_prefs, categories, tasks_enabled, checkins_enabled
    )
    _create_user_files__preferences_file(
        user_id, user_prefs, categories, tasks_enabled, checkins_enabled
    )
    _create_user_files__context_file(user_id, user_prefs)
    _create_user_files__schedules_file(
        user_id, categories, user_prefs, tasks_enabled, checkins_enabled
    )
    _create_user_files__log_files(user_id)
    _create_user_files__sent_messages_file(user_id)
    # Note: tags/ and notebook/ directories are created lazily on first use (not during account creation)

    if tasks_enabled:
        _create_user_files__task_files(user_id)

    # Create checkins file if enabled
    if checkins_enabled:
        _create_user_files__checkins_file(user_id)

    # Create message files for categories
    if categories:
        _create_user_files__message_files(user_id, categories)

    _create_user_files__update_user_references(user_id)

    logger.info(f"Successfully created all user files for user {user_id}")


@handle_errors("determining feature enablement", default_return=(False, False))
def _create_user_files__determine_feature_enablement(user_prefs):
    """
    Determine which features are enabled based on user preferences.

    Args:
        user_prefs: User preferences dictionary

    Returns:
        tuple: (tasks_enabled, checkins_enabled)
    """
    try:
        if not user_prefs:
            return False, False

        # Check for explicit feature enablement in account_data
        features_enabled = user_prefs.get("features_enabled", {})
        if features_enabled:
            tasks_enabled = features_enabled.get("tasks", False)
            checkins_enabled = features_enabled.get("checkins", False)
        else:
            # Fallback to checking settings (legacy approach)
            checkin_settings = user_prefs.get("checkin_settings", {})
            task_settings = user_prefs.get("task_settings", {})
            tasks_enabled = task_settings.get("enabled", False)
            checkins_enabled = checkin_settings.get("enabled", False)

        return tasks_enabled, checkins_enabled
    except Exception as e:
        logger.error(f"Error determining feature enablement: {e}")
        return False, False


@handle_errors("creating account file", default_return=False)
def _create_user_files__account_file(
    user_id, user_prefs, categories, tasks_enabled, checkins_enabled
):
    """Create account.json with actual user data."""
    try:
        account_file = get_user_file_path(user_id, "account")
        if os.path.exists(account_file):
            return

        # Canonical readable timestamp for metadata fields
        current_time = now_readable_timestamp()

        internal_username = user_prefs.get("internal_username", "")
        chat_id = user_prefs.get("chat_id", "")
        phone = user_prefs.get("phone", "")
        email = user_prefs.get("email", "")
        discord_user_id = user_prefs.get("discord_user_id", "")
        discord_username = user_prefs.get("discord_username", "")
        timezone = user_prefs.get("timezone", "")

        channel = user_prefs.get("channel", {})
        channel_type = channel.get("type", "email")
        if channel_type == "email":
            chat_id = email

        elif channel_type == "discord":
            chat_id = discord_user_id

        account_data = {
            "user_id": user_id,
            "internal_username": internal_username,
            "account_status": "active",
            "chat_id": chat_id,
            "phone": phone,
            "email": email,
            "discord_user_id": discord_user_id,
            "discord_username": discord_username,
            "timezone": timezone,
            "created_at": current_time,
            "updated_at": current_time,
            "features": {
                "automated_messages": "enabled" if categories else "disabled",
                "checkins": "enabled" if checkins_enabled else "disabled",
                "task_management": "enabled" if tasks_enabled else "disabled",
            },
        }
        save_json_data(account_data, account_file)
        logger.debug(f"Created account file for user {user_id}")
    except Exception as e:
        logger.error(f"Error creating account file for user {user_id}: {e}")
        raise


@handle_errors("creating preferences file", default_return=False)
def _create_user_files__preferences_file(
    user_id, user_prefs, categories, tasks_enabled, checkins_enabled
):
    """Create preferences.json with actual user data."""
    try:
        preferences_file = get_user_file_path(user_id, "preferences")
        if os.path.exists(preferences_file):
            return

        # Use actual user preferences if available, otherwise create defaults
        if user_prefs:
            default_preferences = {
                "categories": categories or [],
                "channel": user_prefs.get("channel", {"type": "email"}),
            }
            # Add check-in settings if available (but remove schedule periods)
            if checkins_enabled and "checkin_settings" in user_prefs:
                checkin_settings = user_prefs["checkin_settings"].copy()
                # Remove time_periods from preferences (they go in schedules.json)
                if "time_periods" in checkin_settings:
                    del checkin_settings["time_periods"]
                default_preferences["checkin_settings"] = checkin_settings
            # Add task settings if available (but remove schedule periods)
            if tasks_enabled and "task_settings" in user_prefs:
                task_settings = user_prefs["task_settings"].copy()
                # Remove time_periods from preferences (they go in schedules.json)
                if "time_periods" in task_settings:
                    del task_settings["time_periods"]
                default_preferences["task_settings"] = task_settings
        else:
            default_preferences = {
                "categories": categories or [],
                "channel": {"type": "email"},
            }
            # Only add check-in settings if check-ins are enabled (without enabled flag)
            if checkins_enabled:
                default_preferences["checkin_settings"] = {}
            # Only add task settings if tasks are enabled (without enabled flag)
            if tasks_enabled:
                default_preferences["task_settings"] = {}

        save_json_data(default_preferences, preferences_file)
        logger.debug(f"Created preferences file for user {user_id}")
    except Exception as e:
        logger.error(f"Error creating preferences file for user {user_id}: {e}")
        raise


@handle_errors("creating context file", default_return=False)
def _create_user_files__context_file(user_id, user_prefs):
    """Create user_context.json with actual personalization data."""
    try:
        context_file = get_user_file_path(user_id, "context")
        if os.path.exists(context_file):
            return

        # Canonical readable timestamp for metadata fields
        current_time = now_readable_timestamp()

        personalization_data = user_prefs.get("personalization_data", {})

        # Get custom fields with proper nesting
        custom_fields = personalization_data.get("custom_fields", {})

        context_data = {
            "preferred_name": personalization_data.get("preferred_name", ""),
            "gender_identity": personalization_data.get("gender_identity", []),
            "date_of_birth": personalization_data.get("date_of_birth", ""),
            "custom_fields": {
                "health_conditions": custom_fields.get("health_conditions", []),
                "medications_treatments": custom_fields.get(
                    "medications_treatments", []
                ),
                "reminders_needed": custom_fields.get("reminders_needed", []),
                "allergies_sensitivities": custom_fields.get(
                    "allergies_sensitivities", []
                ),
            },
            "interests": personalization_data.get("interests", []),
            "goals": personalization_data.get("goals", []),
            "loved_ones": personalization_data.get("loved_ones", []),
            "activities_for_encouragement": personalization_data.get(
                "activities_for_encouragement", []
            ),
            "notes_for_ai": personalization_data.get("notes_for_ai", []),
            "created_at": current_time,
            "last_updated": current_time,
        }
        save_json_data(context_data, context_file)
        logger.debug(f"Created user_context file for user {user_id}")
    except Exception as e:
        logger.error(f"Error creating context file for user {user_id}: {e}")
        raise


@handle_errors("creating schedules file", default_return=False)
def _create_user_files__schedules_file(
    user_id, categories, user_prefs, tasks_enabled, checkins_enabled
):
    """Create schedules file with appropriate structure."""
    try:
        schedules_file = get_user_file_path(user_id, "schedules")
        if not os.path.exists(schedules_file):
            schedules_data = {}
        else:
            schedules_data = load_json_data(schedules_file) or {}

        # Ensure each category has a default schedule block
        for category in categories:
            if category not in schedules_data:
                if category in ("checkin", "tasks"):
                    # Don't create schedule periods for checkin/tasks during account creation
                    # These will be created when the user actually enables the features
                    continue
                else:
                    # Create default periods for new categories (ALL + default)
                    default_periods = {
                        "ALL": {
                            "active": True,
                            "days": ["ALL"],
                            "start_time": "00:00",
                            "end_time": "23:59",
                        },
                        f"{category.replace('_', ' ').title()} Message Default": {
                            "active": True,
                            "days": ["ALL"],
                            "start_time": "18:00",
                            "end_time": "20:00",
                        },
                    }
                    schedules_data[category] = default_periods

        # Create schedule periods for tasks if enabled
        if tasks_enabled and user_prefs and "task_settings" in user_prefs:
            task_settings = user_prefs.get("task_settings", {})
            task_time_periods = task_settings.get("time_periods", {})
            if task_time_periods:
                schedules_data["tasks"] = {"periods": task_time_periods}
                logger.debug(f"Created task schedule periods for user {user_id}")

        # Create schedule periods for check-ins if enabled
        if checkins_enabled and user_prefs and "checkin_settings" in user_prefs:
            checkin_settings = user_prefs.get("checkin_settings", {})
            checkin_time_periods = checkin_settings.get("time_periods", {})
            if checkin_time_periods:
                schedules_data["checkin"] = {"periods": checkin_time_periods}
                logger.debug(f"Created check-in schedule periods for user {user_id}")

        save_json_data(schedules_data, schedules_file)
        logger.debug(f"Created schedules file for user {user_id}")
    except Exception as e:
        logger.error(f"Error creating schedules file for user {user_id}: {e}")
        raise


@handle_errors("creating log files", default_return=False)
def _create_user_files__log_files(user_id):
    """Initialize empty log files if they don't exist."""
    try:
        log_types = ["checkins", "chat_interactions"]
        for log_type in log_types:
            log_file = get_user_file_path(user_id, log_type)
            if not os.path.exists(log_file):
                save_json_data([], log_file)
                logger.debug(f"Created {log_type} file for user {user_id}")
    except Exception as e:
        logger.error(f"Error creating log files for user {user_id}: {e}")
        raise


@handle_errors("creating sent messages file", default_return=False)
def _create_user_files__sent_messages_file(user_id):
    """Create sent_messages.json in messages/ subdirectory."""
    try:
        from pathlib import Path

        user_messages_dir = Path(get_user_data_dir(user_id)) / "messages"
        os.makedirs(user_messages_dir, exist_ok=True)
        sent_messages_file = user_messages_dir / "sent_messages.json"
        if not os.path.exists(sent_messages_file):
            save_json_data({}, str(sent_messages_file))
            logger.debug(f"Created sent_messages file for user {user_id}")
    except Exception as e:
        logger.error(f"Error creating sent messages file for user {user_id}: {e}")
        raise


@handle_errors("creating task files", default_return=False)
def _create_user_files__task_files(user_id):
    """Create task files if tasks are enabled."""
    try:
        user_dir = Path(get_user_data_dir(user_id))
        tasks_dir = user_dir / "tasks"

        # Create tasks directory if it doesn't exist
        if not os.path.exists(tasks_dir):
            os.makedirs(tasks_dir, exist_ok=True)
            logger.debug(f"Created tasks directory for user {user_id}")

        # Create initial task files
        task_files = {"active_tasks": [], "completed_tasks": [], "task_schedules": {}}

        for task_file, default_data in task_files.items():
            task_file_path = tasks_dir / f"{task_file}.json"
            if not os.path.exists(task_file_path):
                save_json_data(default_data, str(task_file_path))
                logger.debug(f"Created {task_file} file for user {user_id}")
    except Exception as e:
        logger.error(f"Error creating task files for user {user_id}: {e}")
        raise


@handle_errors("creating checkins file", default_return=None)
def _create_user_files__checkins_file(user_id):
    """Create checkins.json only if checkins are enabled."""
    checkins_file = get_user_file_path(user_id, "checkins")
    if not os.path.exists(checkins_file):
        save_json_data([], checkins_file)
        logger.debug(f"Created checkins file for user {user_id}")


@handle_errors("creating message files", default_return=None)
def _create_user_files__message_files(user_id, categories):
    """Create message files for each enabled category directly."""
    try:
        # Create messages directory for user
        user_messages_dir = Path(get_user_data_dir(user_id)) / "messages"
        user_messages_dir.mkdir(parents=True, exist_ok=True)

        # Create message files for each category
        from core.message_management import create_message_file_from_defaults

        success_count = 0
        for category in categories:
            if create_message_file_from_defaults(user_id, category):
                success_count += 1
                logger.debug(
                    f"Created message file for category {category} for user {user_id}"
                )
            else:
                logger.warning(
                    f"Failed to create message file for category {category} for user {user_id}"
                )

        if success_count == len(categories):
            logger.debug(f"Created all message files for user {user_id}")
        else:
            logger.warning(
                f"Failed to create {len(categories) - success_count} message files for user {user_id}"
            )
    except Exception as e:
        logger.error(f"Error creating message files for user {user_id}: {e}")


@handle_errors("updating user references", default_return=None)
def _create_user_files__update_user_references(user_id):
    """Auto-update message references and user index."""
    try:
        from core.user_data_manager import update_message_references, update_user_index

        update_message_references(user_id)
        # Skip user index update during initial file creation to avoid circular dependency
        # The index will be updated when the user is actually created
    except ImportError:
        logger.debug("User data manager not available, skipping reference updates")
    except Exception as e:
        logger.warning(f"Failed to update message references for user {user_id}: {e}")
