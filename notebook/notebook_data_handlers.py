"""
Notebook data handlers for loading and saving notebook entries.

Handles JSON persistence for notebook entries with lazy directory creation.
"""

from pathlib import Path

from core.logger import get_component_logger
from core.error_handling import handle_errors, FileOperationError
from core.config import get_user_data_dir
from core.file_operations import load_json_data, save_json_data
from core.time_utilities import now_timestamp_full
from core.user_data_v2 import (
    SCHEMA_VERSION as V2_SCHEMA_VERSION,
    NotebookV2Model,
    generate_short_id,
)

from notebook.notebook_schemas import Entry

logger = get_component_logger("notebook_data_handlers")

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
    notebook_dir = user_dir / "notebook"
    notebook_dir.mkdir(parents=True, exist_ok=True)
    return notebook_dir


@handle_errors("getting notebook file path")
def _get_notebook_file_path(user_id: str) -> Path:
    """Returns the full path to the user's notebook entries.json file."""
    notebook_dir = ensure_notebook_dirs(user_id)
    return notebook_dir / NOTEBOOK_FILE_NAME


@handle_errors("loading notebook entries", default_return=[])
def load_entries(user_id: str) -> list[Entry]:
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
        logger.debug(
            f"Notebook file not found for user {user_id}, returning empty list."
        )
        return []

    raw_data = load_json_data(str(file_path))
    if not raw_data:
        logger.warning(
            f"Failed to load raw data from {file_path}, returning empty list."
        )
        return []

    if not isinstance(raw_data, dict) or "entries" not in raw_data:
        logger.error(
            f"Invalid notebook file format for user {user_id}: missing 'entries' key or not a dict."
        )
        return []

    entries_data = raw_data.get("entries", [])
    entries_data = [_entry_v2_to_runtime(entry) for entry in entries_data if isinstance(entry, dict)]
    loaded_entries: list[Entry] = []
    for entry_data in entries_data:
        try:
            entry = Entry.model_validate(entry_data)
            loaded_entries.append(entry)
        except Exception as e:
            logger.error(
                f"Failed to validate notebook entry for user {user_id}: {e} - Data: {entry_data}"
            )

    logger.debug(f"Loaded {len(loaded_entries)} notebook entries for user {user_id}.")
    return loaded_entries


@handle_errors("saving notebook entries")
def save_entries(user_id: str, entries: list[Entry]) -> None:
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
    entries_data = [entry.model_dump(mode="json") for entry in entries]
    data_to_save = {
        "schema_version": V2_SCHEMA_VERSION,
        "entries": [_entry_runtime_to_v2(entry) for entry in entries_data],
        "updated_at": now_timestamp_full(),
    }

    # Use core.file_operations.save_json_data for atomic write
    success = save_json_data(data_to_save, str(file_path))
    if success:
        logger.debug(f"Saved {len(entries)} v2 notebook entries for user {user_id}.")
    else:
        logger.error(f"Failed to save notebook entries for user {user_id}.")
        raise FileOperationError(f"Failed to save notebook entries for user {user_id}.")


def _entry_v2_to_runtime(entry: dict) -> dict:
    runtime = {
        "id": entry.get("id"),
        "short_id": entry.get("short_id"),
        "kind": entry.get("kind"),
        "title": entry.get("title") or None,
        "description": entry.get("description") or None,
        "body": entry.get("description") or None,
        "status": entry.get("status") or "active",
        "category": entry.get("category") or "",
        "tags": entry.get("tags") or [],
        "group": entry.get("group") or None,
        "pinned": entry.get("pinned", False),
        "archived": entry.get("status") == "archived",
        "submitted_at": entry.get("submitted_at"),
        "source": entry.get("source"),
        "linked_item_ids": entry.get("linked_item_ids") or [],
        "created_at": entry.get("created_at"),
        "updated_at": entry.get("updated_at"),
        "archived_at": entry.get("archived_at"),
        "deleted_at": entry.get("deleted_at"),
        "metadata": entry.get("metadata") or {},
    }
    if runtime.get("kind") == "list":
        runtime["items"] = entry.get("items")
        runtime["body"] = None
    return runtime


def _entry_runtime_to_v2(entry: dict) -> dict:
    entry_id = str(entry.get("id") or "")
    kind = entry.get("kind")
    created_at = entry.get("created_at") or now_timestamp_full()
    updated_at = entry.get("updated_at") or created_at
    status = entry.get("status") or ("archived" if entry.get("archived") else "active")
    description = entry.get("body")
    if description is None:
        description = entry.get("description") or ""
    v2_entry = {
        "id": entry_id,
        "short_id": entry.get("short_id") or generate_short_id(entry_id, str(kind)),
        "kind": kind,
        "title": entry.get("title") or "",
        "description": description or "",
        "category": entry.get("category") or "",
        "group": entry.get("group") or "",
        "tags": entry.get("tags") or [],
        "status": status,
        "pinned": bool(entry.get("pinned", False)),
        "submitted_at": entry.get("submitted_at") or (created_at if kind == "journal_entry" else None),
        "items": entry.get("items") if kind == "list" else None,
        "source": entry.get("source") or {"system": "mhm", "channel": "", "actor": "", "migration": None},
        "linked_item_ids": entry.get("linked_item_ids") or [],
        "created_at": created_at,
        "updated_at": updated_at,
        "archived_at": entry.get("archived_at") or (updated_at if status == "archived" else None),
        "deleted_at": entry.get("deleted_at"),
        "metadata": entry.get("metadata") or {},
    }
    return NotebookV2Model.model_validate(v2_entry).model_dump(mode="json")
