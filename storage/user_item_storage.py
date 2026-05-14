"""
Shared user-scoped JSON storage helpers for notebook, tasks, and future item types (e.g. events).

Provides a single pattern for path building, directory creation, and load/save of
user subdir JSON files. Uses only core.config.get_user_data_dir and
core.file_operations load/save; no domain-specific logic.
"""

from pathlib import Path

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.config import get_user_data_dir
from core.file_operations import load_json_data, save_json_data

logger = get_component_logger("user_item_storage")


@handle_errors("getting user subdir path", default_return=None)
def get_user_subdir_path(user_id: str, subdir: str) -> Path | None:
    """
    Return the path for a user's subdirectory (e.g. notebook, tasks, events).

    Args:
        user_id: User identifier.
        subdir: Subdirectory name under the user data dir (e.g. 'notebook', 'tasks').

    Returns:
        Path to the subdir, or None if user_id is invalid.
    """
    if not user_id or not isinstance(user_id, str) or not user_id.strip():
        logger.warning("get_user_subdir_path: invalid or empty user_id")
        return None
    base = get_user_data_dir(user_id)
    if not base:
        return None
    return Path(base) / subdir


@handle_errors("ensuring user subdir", default_return=None)
def ensure_user_subdir(
    user_id: str,
    subdir: str,
    init_files: dict[str, dict | list] | None = None,
) -> Path | None:
    """
    Ensure the user's subdirectory exists and optionally create default JSON files.

    Args:
        user_id: User identifier.
        subdir: Subdirectory name (e.g. 'notebook', 'tasks').
        init_files: Optional mapping of filename -> default JSON-serializable data.
                    Files are created only if missing (e.g. {"tasks.json": {"schema_version": 2, "tasks": []}}).

    Returns:
        Path to the subdir, or None on failure.
    """
    path = get_user_subdir_path(user_id, subdir)
    if path is None:
        return None
    path.mkdir(parents=True, exist_ok=True)
    if init_files:
        for filename, default_data in init_files.items():
            file_path = path / filename
            if not file_path.exists():
                save_json_data(default_data, str(file_path))
                logger.debug(f"Created {filename} in {subdir} for user {user_id}")
    return path


# not_duplicate: load_save_user_json
@handle_errors("loading user JSON file", default_return=None)
def load_user_json_file(
    user_id: str,
    subdir: str,
    filename: str,
    default_data: dict | list,
) -> dict | list | None:
    """
    Load a JSON file from a user's subdirectory.

    Args:
        user_id: User identifier.
        subdir: Subdirectory name (e.g. 'notebook', 'tasks').
        filename: JSON filename (e.g. 'entries.json', 'tasks.json').
        default_data: Returned when file is missing or load fails (must match expected type).

    Returns:
        Loaded data (dict or list), or default_data on failure. None if path invalid.
    """
    path = get_user_subdir_path(user_id, subdir)
    if path is None:
        return default_data
    file_path = path / filename
    raw = load_json_data(str(file_path))
    if raw is None:
        return default_data
    if isinstance(default_data, list) and not isinstance(raw, list):
        if isinstance(raw, dict) and len(raw) == 1:
            for v in raw.values():
                if isinstance(v, list):
                    return v
        logger.warning(f"Expected list from {filename}, got {type(raw).__name__}; returning default")
        return default_data
    if isinstance(default_data, dict) and not isinstance(raw, dict):
        logger.warning(f"Expected dict from {filename}, got {type(raw).__name__}; returning default")
        return default_data
    return raw


# not_duplicate: load_save_user_json
@handle_errors("saving user JSON file", default_return=False)
def save_user_json_file(
    user_id: str,
    subdir: str,
    filename: str,
    data: dict | list,
) -> bool:
    """
    Save JSON data to a user's subdirectory. Creates subdir if missing.

    Args:
        user_id: User identifier.
        subdir: Subdirectory name (e.g. 'notebook', 'tasks').
        filename: JSON filename.
        data: JSON-serializable dict or list.

    Returns:
        True if save succeeded, False otherwise.
    """
    path = ensure_user_subdir(user_id, subdir, init_files=None)
    if path is None:
        return False
    file_path = path / filename
    return save_json_data(data, str(file_path))
