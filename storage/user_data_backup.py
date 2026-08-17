"""Per-user backup, export, and complete deletion (ops/admin)."""

from __future__ import annotations

import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import Any

from core.config import BASE_DATA_DIR, get_backups_dir
from core.error_handling import handle_errors
from core.file_operations import get_user_data_dir, get_user_file_path, load_json_data
from core.logger import get_component_logger
from core.time_utilities import now_timestamp_filename, now_timestamp_full
from storage.user_data_index import remove_from_index
from storage.user_data_user_info import (
    get_user_info_for_data_manager,
    get_user_message_files,
)

logger = get_component_logger("main")


@handle_errors("resolving backup directory", re_raise=True)
def _backup_dir(backup_dir: str | None = None) -> str:
    """Return the backup directory path, creating it if needed."""
    dest = backup_dir or get_backups_dir()
    os.makedirs(dest, exist_ok=True)
    return dest


# not_duplicate: user_data_manager_api
@handle_errors("backing up user data", default_return="")
def backup_user_data(
    user_id: str, include_messages: bool = True, backup_dir: str | None = None
) -> str:
    """
    Create a complete backup of user's data with validation.

    Returns:
        str: Path to backup file, empty string if failed
    """
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return ""

    if not user_id.strip():
        logger.error("Empty user_id provided")
        return ""

    if not isinstance(include_messages, bool):
        logger.error(f"Invalid include_messages: {include_messages}")
        return ""

    try:
        dest = _backup_dir(backup_dir)
        timestamp = now_timestamp_filename()
        backup_filename = f"user_backup_{user_id}_{timestamp}.zip"
        backup_path = str(Path(dest) / backup_filename)
        Path(dest).mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            added_files = set()
            user_dir = Path(get_user_data_dir(user_id))
            if user_dir.exists():
                for file_path in user_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = os.path.relpath(str(file_path), BASE_DATA_DIR)
                        if arcname not in added_files:
                            zipf.write(str(file_path), arcname)
                            added_files.add(arcname)

            if include_messages:
                message_files = get_user_message_files(user_id)
                for _category, file_path in message_files.items():
                    if os.path.exists(file_path):
                        arcname = os.path.relpath(file_path, BASE_DATA_DIR)
                        if arcname not in added_files:
                            zipf.write(file_path, arcname)
                            added_files.add(arcname)

            metadata = {
                "user_id": user_id,
                "backup_date": now_timestamp_full(),
                "backup_type": "complete",
                "includes_messages": include_messages,
                "files_backed_up": zipf.namelist(),
            }
            zipf.writestr("backup_metadata.json", json.dumps(metadata, indent=2))

        logger.info(f"User backup created: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Error creating backup for user {user_id}: {e}")
        return ""


# not_duplicate: user_data_manager_api
@handle_errors("exporting user data", default_return={})
def export_user_data(user_id: str, export_format: str = "json") -> dict[str, Any]:
    """Export all user data to a structured format with validation."""
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return {}

    if not user_id.strip():
        logger.error("Empty user_id provided")
        return {}

    if not export_format or not isinstance(export_format, str):
        logger.error(f"Invalid export_format: {export_format}")
        return {}

    if export_format not in ["json", "csv", "yaml"]:
        logger.error(f"Unsupported export_format: {export_format}")
        return {}

    export_data: dict[str, Any] = {
        "user_id": user_id,
        "export_date": now_timestamp_full(),
        "profile": {},
        "preferences": {},
        "schedules": {},
        "messages": {},
        "sent_messages": {},
        "logs": {},
    }

    user_info = get_user_info_for_data_manager(user_id)
    if user_info:
        export_data["profile"] = user_info

    prefs_file = get_user_file_path(user_id, "preferences")
    if os.path.exists(prefs_file):
        export_data["preferences"] = load_json_data(prefs_file) or {}

    schedules_file = get_user_file_path(user_id, "schedules")
    if os.path.exists(schedules_file):
        export_data["schedules"] = load_json_data(schedules_file) or {}

    message_files = get_user_message_files(user_id)
    for category, file_path in message_files.items():
        if os.path.exists(file_path):
            export_data["messages"][category] = load_json_data(file_path) or {}

    sent_file = get_user_file_path(user_id, "sent_messages")
    if os.path.exists(sent_file):
        export_data["sent_messages"] = load_json_data(sent_file) or {}

    for log_type in ["checkins", "chat_interactions"]:
        log_file = get_user_file_path(user_id, log_type)
        if os.path.exists(log_file):
            export_data["logs"][log_type] = load_json_data(log_file) or []

    logger.info(f"User data exported for user {user_id}")
    return export_data


# not_duplicate: delete_user_completely
@handle_errors("deleting user completely", default_return=False)
def delete_user_completely(
    user_id: str,
    create_backup: bool = True,
    backup_dir: str | None = None,
    index_file: str | None = None,
) -> bool:
    """Completely remove all traces of a user from the system with validation."""
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return False

    if not user_id.strip():
        logger.error("Empty user_id provided")
        return False

    if not isinstance(create_backup, bool):
        logger.error(f"Invalid create_backup: {create_backup}")
        return False

    if create_backup:
        backup_path = backup_user_data(
            user_id, include_messages=True, backup_dir=backup_dir
        )
        if backup_path:
            logger.info(f"Backup created before deletion: {backup_path}")

    user_dir = get_user_data_dir(user_id)
    if os.path.exists(user_dir):
        try:
            shutil.rmtree(user_dir)
            logger.info(f"Deleted user directory: {user_dir}")
        except Exception as e:
            logger.warning(f"Error deleting user directory {user_dir}: {e}")

    try:
        message_files = get_user_message_files(user_id)
        for _category, file_path in message_files.items():
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted message file: {file_path}")
                except Exception as e:
                    logger.warning(f"Error deleting message file {file_path}: {e}")
    except Exception as e:
        logger.warning(f"Error getting message files for user {user_id}: {e}")

    try:
        remove_from_index(user_id, index_file=index_file)
    except Exception as e:
        logger.warning(f"Error removing user {user_id} from index: {e}")

    logger.info(f"User {user_id} completely removed from system")
    return True
