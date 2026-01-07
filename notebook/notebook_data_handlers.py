"""
Notebook data handlers for loading and saving notebook entries.

Handles JSON persistence for notebook entries with lazy directory creation.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.logger import get_component_logger
from core.error_handling import handle_errors, FileOperationError
from core.config import get_user_data_dir
from core.file_operations import load_json_data, save_json_data

from notebook.schemas import Entry

logger = get_component_logger('notebook_data_handlers')

SCHEMA_VERSION = 1
NOTEBOOK_FILE_NAME = "entries.json"

@handle_errors("ensuring notebook directories")
def ensure_notebook_dirs(user_id: str) -> Path:
    """
    Ensures the notebook directory structure exists for a user.
    Creates directory lazily on first use if it doesn't exist.
    
    Returns:
        Path to the user's notebook directory
    """
    user_dir = Path(get_user_data_dir(user_id))
    notebook_dir = user_dir / 'notebook'
    notebook_dir.mkdir(parents=True, exist_ok=True)
    return notebook_dir

@handle_errors("getting notebook file path")
def _get_notebook_file_path(user_id: str) -> Path:
    """Returns the full path to the user's notebook entries.json file."""
    notebook_dir = ensure_notebook_dirs(user_id)
    return notebook_dir / NOTEBOOK_FILE_NAME

@handle_errors("loading notebook entries", default_return=[])
def load_entries(user_id: str) -> List[Entry]:
    """
    Loads all notebook entries for a user from entries.json.
    Creates directory and file if they don't exist (lazy initialization).
    Also ensures tags are initialized (tags are created when first notebook entry is accessed).
    
    Returns:
        List of Entry objects, empty list if file is missing or corrupted
    """
    # Ensure tags are initialized when notebook is first accessed
    from core.tags import ensure_tags_initialized
    ensure_tags_initialized(user_id)
    
    file_path = _get_notebook_file_path(user_id)
    
    # If file doesn't exist, return empty list (will be created on first save)
    if not file_path.exists():
        logger.debug(f"Notebook file not found for user {user_id}, returning empty list.")
        return []

    raw_data = load_json_data(str(file_path))
    if not raw_data:
        logger.warning(f"Failed to load raw data from {file_path}, returning empty list.")
        return []

    if not isinstance(raw_data, dict) or "entries" not in raw_data:
        logger.error(f"Invalid notebook file format for user {user_id}: missing 'entries' key or not a dict.")
        return []

    entries_data = raw_data.get("entries", [])
    loaded_entries: List[Entry] = []
    for entry_data in entries_data:
        try:
            entry = Entry.model_validate(entry_data)
            loaded_entries.append(entry)
        except Exception as e:
            logger.error(f"Failed to validate notebook entry for user {user_id}: {e} - Data: {entry_data}")
    
    logger.debug(f"Loaded {len(loaded_entries)} notebook entries for user {user_id}.")
    return loaded_entries

@handle_errors("saving notebook entries")
def save_entries(user_id: str, entries: List[Entry]) -> None:
    """
    Saves all notebook entries for a user to entries.json with atomic write.
    Creates directory and file if they don't exist.
    Also ensures tags are initialized (tags are created when first notebook entry is saved).
    """
    # Ensure tags are initialized when notebook is first used
    from core.tags import ensure_tags_initialized
    ensure_tags_initialized(user_id)
    
    # Ensure directory exists
    ensure_notebook_dirs(user_id)
    file_path = _get_notebook_file_path(user_id)
    
    # Convert Pydantic models to dictionaries
    entries_data = [entry.model_dump(mode='json') for entry in entries]
    
    data_to_save = {
        "schema_version": SCHEMA_VERSION,
        "entries": entries_data,
        "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Use core.file_operations.save_json_data for atomic write
    success = save_json_data(data_to_save, str(file_path))
    if success:
        logger.debug(f"Saved {len(entries)} notebook entries for user {user_id}.")
    else:
        logger.error(f"Failed to save notebook entries for user {user_id}.")
        raise FileOperationError(f"Failed to save notebook entries for user {user_id}.")
