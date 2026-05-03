"""Notebook use-case layer.

This module owns notebook command/business operations and delegates persistence to
``notebook_data_manager``. Communication handlers should use these functions instead
of importing lower-level data-manager helpers directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.error_handling import handle_errors
from core.tags import parse_tags_from_text
from core.time_utilities import now_timestamp_full
from notebook import notebook_data_manager as data_manager
from notebook.notebook_schemas import Entry

QUICK_NOTES_GROUP = "Quick Notes"
MAX_NOTEBOOK_QUERY_RESULTS = 100


@dataclass(frozen=True)
class NotebookEntryResult:
    """Structured result for a notebook operation that targets one entry."""

    entry: Entry | None
    success: bool
    error: str | None = None


@dataclass(frozen=True)
class NotebookListResult:
    """Structured result for notebook list/query operations."""

    entries: list[Entry]
    total: int
    query: str | None = None
    filter_name: str | None = None
    filter_value: str | None = None


@handle_errors("normalizing notebook tags", default_return=[])
def normalize_command_tags(tags: Any) -> list[str]:
    """Return command tags as a mutable list of strings."""
    if tags is None:
        return []
    if isinstance(tags, str):
        return [tags]
    if isinstance(tags, list):
        return [tag for tag in tags if isinstance(tag, str)]
    return list(tags) if isinstance(tags, tuple) else []


@handle_errors("preparing note fields from command", user_friendly=False)
def prepare_note_fields(entities: dict[str, Any]) -> dict[str, Any]:
    """Normalize title/body/tag fields for a create-note command."""
    title = entities.get("title")
    description = entities.get("description")
    tags = normalize_command_tags(entities.get("tags", []))
    group = entities.get("group")

    if not title and description:
        title = description
        description = None

    if description:
        description, parsed_tags = parse_tags_from_text(description)
        tags.extend(parsed_tags)
    elif title:
        title, parsed_tags = parse_tags_from_text(title)
        tags.extend(parsed_tags)

    return {
        "title": title,
        "description": description,
        "tags": tags,
        "group": group,
    }


@handle_errors("preparing quick note fields from command", user_friendly=False)
def prepare_quick_note_fields(entities: dict[str, Any]) -> dict[str, Any]:
    """Normalize command fields for a quick note."""
    title = entities.get("title")
    tags = normalize_command_tags(entities.get("tags", []))

    if not title or not title.strip():
        title = f"Quick Note - {now_timestamp_full()}"

    title, parsed_tags = parse_tags_from_text(title)
    tags.extend(parsed_tags)
    return {
        "title": title,
        "description": None,
        "tags": tags,
        "group": QUICK_NOTES_GROUP,
    }


@handle_errors("preparing list fields from command", user_friendly=False)
def prepare_list_fields(entities: dict[str, Any]) -> dict[str, Any]:
    """Normalize command fields for list creation."""
    title = entities.get("title")
    tags = normalize_command_tags(entities.get("tags", []))
    if title:
        title, parsed_tags = parse_tags_from_text(title)
        tags.extend(parsed_tags)
    return {
        "title": title,
        "tags": tags,
        "group": entities.get("group"),
        "items": entities.get("items", []),
    }


@handle_errors("creating notebook note from command", default_return=None)
def create_note_from_command(
    user_id: str, entities: dict[str, Any]
) -> NotebookEntryResult:
    """Create a note from command entities and return a structured result."""
    fields = prepare_note_fields(entities)
    entry = data_manager.create_note(user_id, **fields)
    return NotebookEntryResult(entry=entry, success=entry is not None)


@handle_errors("creating quick notebook note from command", default_return=None)
def create_quick_note_from_command(
    user_id: str, entities: dict[str, Any]
) -> NotebookEntryResult:
    """Create a quick note from command entities."""
    fields = prepare_quick_note_fields(entities)
    entry = data_manager.create_note(user_id, **fields)
    return NotebookEntryResult(entry=entry, success=entry is not None)


@handle_errors("creating notebook list from command", default_return=None)
def create_list_from_command(
    user_id: str, entities: dict[str, Any]
) -> NotebookEntryResult:
    """Create a notebook list from command entities."""
    fields = prepare_list_fields(entities)
    entry = data_manager.create_list(user_id, **fields)
    return NotebookEntryResult(entry=entry, success=entry is not None)


@handle_errors("creating notebook journal from command", default_return=None)
def create_journal_from_command(
    user_id: str, entities: dict[str, Any]
) -> NotebookEntryResult:
    """Create a journal entry from command entities."""
    entry = data_manager.create_journal(
        user_id,
        title=entities.get("title"),
        description=entities.get("description"),
        tags=normalize_command_tags(entities.get("tags", [])),
        group=entities.get("group"),
    )
    return NotebookEntryResult(entry=entry, success=entry is not None)


@handle_errors("listing recent notebook entries", default_return=NotebookListResult([], 0))
def list_recent_entries(
    user_id: str, *, notes_only: bool = False, limit: int = MAX_NOTEBOOK_QUERY_RESULTS
) -> NotebookListResult:
    """List recent notebook entries, optionally notes only."""
    entries = data_manager.list_recent(user_id, n=limit)
    if notes_only:
        entries = [entry for entry in entries if entry.kind == "note"]
    return NotebookListResult(
        entries=entries,
        total=len(entries),
        filter_name="recent_notes" if notes_only else "recent",
    )


@handle_errors("searching notebook entries for display", default_return=NotebookListResult([], 0))
def search_entries_for_display(
    user_id: str, query: str, *, limit: int = MAX_NOTEBOOK_QUERY_RESULTS
) -> NotebookListResult:
    """Search notebook entries for command display."""
    entries = data_manager.search_entries(user_id, query, limit=limit)
    return NotebookListResult(entries=entries, total=len(entries), query=query)


@handle_errors("listing notebook entries by group", default_return=NotebookListResult([], 0))
def list_entries_by_group(
    user_id: str, group: str, *, limit: int = MAX_NOTEBOOK_QUERY_RESULTS
) -> NotebookListResult:
    """List notebook entries assigned to a group."""
    entries = data_manager.list_by_group(user_id, group, limit=limit)
    return NotebookListResult(
        entries=entries, total=len(entries), filter_name="group", filter_value=group
    )


@handle_errors("listing notebook entries by tag", default_return=NotebookListResult([], 0))
def list_entries_by_tag(
    user_id: str, tag: str, *, limit: int = MAX_NOTEBOOK_QUERY_RESULTS
) -> NotebookListResult:
    """List notebook entries with a tag."""
    entries = data_manager.list_by_tag(user_id, tag, limit=limit)
    return NotebookListResult(
        entries=entries, total=len(entries), filter_name="tag", filter_value=tag
    )


@handle_errors("listing pinned notebook entries", default_return=NotebookListResult([], 0))
def list_pinned_entries(
    user_id: str, *, limit: int = MAX_NOTEBOOK_QUERY_RESULTS
) -> NotebookListResult:
    """List pinned notebook entries."""
    entries = data_manager.list_pinned(user_id, limit=limit)
    return NotebookListResult(entries=entries, total=len(entries), filter_name="pinned")


@handle_errors("listing notebook inbox entries", default_return=NotebookListResult([], 0))
def list_inbox_entries(
    user_id: str, *, limit: int = MAX_NOTEBOOK_QUERY_RESULTS
) -> NotebookListResult:
    """List notebook inbox entries."""
    entries = data_manager.list_inbox(user_id, limit=limit)
    return NotebookListResult(entries=entries, total=len(entries), filter_name="inbox")


@handle_errors("listing archived notebook entries", default_return=NotebookListResult([], 0))
def list_archived_entries(
    user_id: str, *, limit: int = MAX_NOTEBOOK_QUERY_RESULTS
) -> NotebookListResult:
    """List archived notebook entries."""
    entries = data_manager.list_archived(user_id, limit=limit)
    return NotebookListResult(entries=entries, total=len(entries), filter_name="archived")


@handle_errors("setting notebook entry group", default_return=NotebookEntryResult(None, False))
def set_entry_group(user_id: str, entry_ref: str, group: str | None) -> NotebookEntryResult:
    """Assign or clear a notebook entry group."""
    entry = data_manager.set_group(user_id, entry_ref, group)
    return NotebookEntryResult(entry=entry, success=entry is not None)


@handle_errors("adding notebook entry tags", default_return=NotebookEntryResult(None, False))
def add_entry_tags(user_id: str, entry_ref: str, tags: list[str]) -> NotebookEntryResult:
    """Add tags to a notebook entry."""
    entry = data_manager.add_tags(user_id, entry_ref, normalize_command_tags(tags))
    return NotebookEntryResult(entry=entry, success=entry is not None)


@handle_errors("removing notebook entry tags", default_return=NotebookEntryResult(None, False))
def remove_entry_tags(
    user_id: str, entry_ref: str, tags: list[str]
) -> NotebookEntryResult:
    """Remove tags from a notebook entry."""
    entry = data_manager.remove_tags(user_id, entry_ref, normalize_command_tags(tags))
    return NotebookEntryResult(entry=entry, success=entry is not None)


@handle_errors("pinning notebook entry", default_return=NotebookEntryResult(None, False))
def pin_notebook_entry(
    user_id: str, entry_ref: str, pinned: bool = True
) -> NotebookEntryResult:
    """Pin or unpin a notebook entry."""
    entry = data_manager.pin_entry(user_id, entry_ref, pinned)
    return NotebookEntryResult(entry=entry, success=entry is not None)


@handle_errors("archiving notebook entry", default_return=NotebookEntryResult(None, False))
def archive_notebook_entry(
    user_id: str, entry_ref: str, archived: bool = True
) -> NotebookEntryResult:
    """Archive or unarchive a notebook entry."""
    entry = data_manager.archive_entry(user_id, entry_ref, archived)
    return NotebookEntryResult(entry=entry, success=entry is not None)


@handle_errors("appending notebook entry body", default_return=NotebookEntryResult(None, False))
def append_entry_body(user_id: str, entry_ref: str, text: str) -> NotebookEntryResult:
    """Append text to an entry body."""
    entry = data_manager.append_to_entry_body(user_id, entry_ref, text)
    return NotebookEntryResult(entry=entry, success=entry is not None)


@handle_errors("replacing notebook entry body", default_return=NotebookEntryResult(None, False))
def replace_entry_body(user_id: str, entry_ref: str, text: str) -> NotebookEntryResult:
    """Replace an entry body."""
    entry = data_manager.set_entry_body(user_id, entry_ref, text)
    return NotebookEntryResult(entry=entry, success=entry is not None)


@handle_errors("adding notebook list item", default_return=NotebookEntryResult(None, False))
def add_item_to_list(user_id: str, entry_ref: str, item_text: str) -> NotebookEntryResult:
    """Add an item to a notebook list entry."""
    entry = data_manager.add_list_item(user_id, entry_ref, item_text)
    return NotebookEntryResult(entry=entry, success=entry is not None)


@handle_errors("setting notebook list item done", default_return=NotebookEntryResult(None, False))
def set_list_item_done(
    user_id: str, entry_ref: str, item_index: int, done: bool
) -> NotebookEntryResult:
    """Set a notebook list item completion state."""
    entry = data_manager.toggle_list_item_done(user_id, entry_ref, item_index, done)
    return NotebookEntryResult(entry=entry, success=entry is not None)


@handle_errors("removing notebook list item", default_return=NotebookEntryResult(None, False))
def delete_list_item(user_id: str, entry_ref: str, item_index: int) -> NotebookEntryResult:
    """Remove an item from a notebook list entry."""
    entry = data_manager.remove_list_item(user_id, entry_ref, item_index)
    return NotebookEntryResult(entry=entry, success=entry is not None)


# Compatibility wrappers for callers that still use data-manager-style names.
create_note = data_manager.create_note
create_list = data_manager.create_list
create_journal = data_manager.create_journal
get_entry = data_manager.get_entry
list_recent = data_manager.list_recent
append_to_entry_body = data_manager.append_to_entry_body
set_entry_body = data_manager.set_entry_body
add_tags = data_manager.add_tags
remove_tags = data_manager.remove_tags
search_entries = data_manager.search_entries
pin_entry = data_manager.pin_entry
archive_entry = data_manager.archive_entry
add_list_item = data_manager.add_list_item
toggle_list_item_done = data_manager.toggle_list_item_done
remove_list_item = data_manager.remove_list_item
set_group = data_manager.set_group
list_by_group = data_manager.list_by_group
list_pinned = data_manager.list_pinned
list_inbox = data_manager.list_inbox
list_by_tag = data_manager.list_by_tag
list_archived = data_manager.list_archived
