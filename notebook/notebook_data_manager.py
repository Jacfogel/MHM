"""
Notebook data manager for CRUD operations on notebook entries.

Provides high-level API for managing notebook entries (notes, lists, journal).
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import ValidationError

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.tags import normalize_tags

from notebook.schemas import Entry, ListItem, EntryKind, TIMESTAMP_FORMAT
from notebook.notebook_data_handlers import load_entries, save_entries
from notebook.notebook_validation import (
    is_valid_entry_reference,
    is_valid_entry_group,
    is_valid_entry_kind,
    normalize_list_item_index,
    validate_entry_content,
    MAX_BODY_LENGTH
)
from core.user_data_validation import is_valid_string_length

logger = get_component_logger('notebook_data_manager')

# Helper to save changes to an entry and persist
@handle_errors("saving updated entry")
def _save_updated_entry(user_id: str, entry: Entry, all_entries: List[Entry]) -> Entry:
    """Updates the entry's updated_at timestamp and saves all entries."""
    from notebook.schemas import TIMESTAMP_FORMAT
    entry.updated_at = datetime.now().strftime(TIMESTAMP_FORMAT)
    save_entries(user_id, all_entries)
    return entry

# Helper to find an entry by various references
@handle_errors("finding entry by reference", default_return=None)
def _find_entry_by_ref(entries: List[Entry], ref: str) -> Optional[Entry]:
    """Finds an entry by full UUID, short ID fragment, or title."""
    # Validate reference format
    if not is_valid_entry_reference(ref):
        logger.warning(f"Invalid entry reference format: {ref}")
        return None
    
    ref_lower = ref.lower().strip()

    # 1. Try full UUID
    for entry in entries:
        if str(entry.id) == ref:
            return entry

    # 2. Try short ID fragment (e.g., 'n-3f2a9c' or '3f2a9c')
    # Extract fragment if prefixed
    short_fragment = ref_lower
    if '-' in ref_lower and len(ref_lower.split('-')) == 2:
        prefix, frag = ref_lower.split('-')
        if prefix in ['n', 'l', 'j']:  # note, list, journal
            short_fragment = frag
    
    if len(short_fragment) >= 6:  # Minimum length for short ID lookup
        matching_entries = [
            entry for entry in entries 
            if str(entry.id).lower().startswith(short_fragment)
        ]
        if len(matching_entries) == 1:
            return matching_entries[0]
        elif len(matching_entries) > 1:
            logger.warning(f"Multiple entries found for short ID fragment '{ref}'. Returning first match.")
            return matching_entries[0]

    # 3. Try title (case-insensitive, exact match first)
    for entry in entries:
        if entry.title and entry.title.lower() == ref_lower:
            return entry
    
    # 4. Try title (case-insensitive, contains match)
    for entry in entries:
        if entry.title and ref_lower in entry.title.lower():
            return entry

    return None

# Create operations
@handle_errors("creating entry")
def create_entry(
    user_id: str,
    kind: EntryKind,
    title: Optional[str] = None,
    body: Optional[str] = None,
    tags: Optional[List[str]] = None,
    group: Optional[str] = None,
    items: Optional[List[Dict[str, Any]]] = None  # For list items
) -> Optional[Entry]:
    """
    Creates a new notebook entry of a specified kind.
    """
    if not user_id:
        logger.error("User ID is required to create an entry.")
        return None
    
    # Validate entry kind
    if not is_valid_entry_kind(kind):
        logger.error(f"Invalid entry kind: {kind}")
        return None
    
    # Validate entry content
    is_valid, error_msg = validate_entry_content(title=title, body=body, kind=kind)
    if not is_valid:
        logger.error(f"Invalid entry content: {error_msg}")
        return None

    normalized_tags = normalize_tags(tags or [])
    
    entry_data = {
        "id": uuid.uuid4(),
        "kind": kind,
        "title": title,
        "body": body,
        "tags": normalized_tags,
        "group": group,
        "created_at": datetime.now().strftime(TIMESTAMP_FORMAT),
        "updated_at": datetime.now().strftime(TIMESTAMP_FORMAT),
    }

    if kind == 'list':
        list_items = []
        if items:
            for i, item_data in enumerate(items):
                try:
                    # item_data might be a dict (from create_list) or already a ListItem
                    if isinstance(item_data, dict):
                        # Extract order if present, otherwise use index
                        item_order = item_data.pop('order', i)
                        list_items.append(ListItem(order=item_order, **item_data))
                    else:
                        # Already a ListItem or other type - convert
                        list_items.append(item_data)
                except (ValidationError, TypeError, ValueError) as e:
                    logger.error(f"Invalid list item data: {item_data} - {e}")
                    return None
        entry_data["items"] = list_items
    elif items is not None:
        logger.warning(f"Items provided for non-list entry kind '{kind}'. Ignoring items.")

    try:
        new_entry = Entry.model_validate(entry_data)
    except ValidationError as e:
        logger.error(f"Failed to validate new entry: {e} - Data: {entry_data}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating new entry: {e} - Data: {entry_data}")
        return None

    all_entries = load_entries(user_id)
    all_entries.append(new_entry)
    save_entries(user_id, all_entries)
    logger.info(f"Created new {kind} entry '{new_entry.title or new_entry.body[:30] if new_entry.body else new_entry.id}' for user {user_id}.")
    return new_entry

@handle_errors("creating note")
def create_note(
    user_id: str,
    title: Optional[str] = None,
    body: Optional[str] = None,
    tags: Optional[List[str]] = None,
    group: Optional[str] = None
) -> Optional[Entry]:
    """Creates a note entry."""
    return create_entry(user_id, 'note', title=title, body=body, tags=tags, group=group)

@handle_errors("creating list")
def create_list(
    user_id: str,
    title: str,
    tags: Optional[List[str]] = None,
    group: Optional[str] = None,
    items: Optional[List[str]] = None
) -> Optional[Entry]:
    """Creates a list entry with initial items."""
    if not items:
        # List must have at least one item - use a default placeholder
        items = ["New item"]
    
    list_items = []
    for i, item_text in enumerate(items):
        if item_text and item_text.strip():  # Only add non-empty items
            list_items.append({"text": item_text.strip(), "order": i})
    
    # Ensure at least one item (shouldn't happen if items was provided, but safety check)
    if not list_items:
        list_items.append({"text": "New item", "order": 0})
    
    return create_entry(user_id, 'list', title=title, tags=tags, group=group, items=list_items)

@handle_errors("creating journal")
def create_journal(
    user_id: str,
    title: Optional[str] = None,
    body: Optional[str] = None,
    tags: Optional[List[str]] = None,
    group: Optional[str] = None
) -> Optional[Entry]:
    """Creates a journal entry."""
    return create_entry(user_id, 'journal', title=title, body=body, tags=tags, group=group)

# Read operations
@handle_errors("getting entry", default_return=None)
def get_entry(user_id: str, ref: str) -> Optional[Entry]:
    """Gets an entry by reference (UUID, short ID, or title)."""
    entries = load_entries(user_id)
    return _find_entry_by_ref(entries, ref)

@handle_errors("listing recent entries", default_return=[])
def list_recent(user_id: str, n: int = 5, include_archived: bool = False) -> List[Entry]:
    """Lists the N most recently updated entries."""
    entries = load_entries(user_id)
    
    # Filter archived if needed
    if not include_archived:
        entries = [e for e in entries if not e.archived]
    
    # Sort by updated_at descending (parse timestamp strings for comparison)
    entries.sort(key=lambda e: datetime.strptime(e.updated_at, TIMESTAMP_FORMAT) if isinstance(e.updated_at, str) else datetime.min, reverse=True)
    
    return entries[:n]

# Update operations
@handle_errors("appending to entry body")
def append_to_entry_body(user_id: str, ref: str, text: str) -> Optional[Entry]:
    """Appends text to an entry's body."""
    if not user_id:
        logger.error("User ID is required to append to entry body.")
        return None
    
    # Validate text length
    if not is_valid_string_length(text, MAX_BODY_LENGTH, field_name="Appended text", allow_none=False):
        logger.error(f"Text to append exceeds maximum length of {MAX_BODY_LENGTH} characters")
        return None
    
    entries = load_entries(user_id)
    entry = _find_entry_by_ref(entries, ref)
    
    if not entry:
        logger.error(f"Entry not found for ref '{ref}'")
        return None
    
    if entry.kind == 'list':
        logger.error("Cannot append to list entry body. Use add_list_item instead.")
        return None
    
    # Check if combined length would exceed limit
    current_body = entry.body or ""
    combined_length = len(current_body) + len("\n") + len(text)
    if combined_length > MAX_BODY_LENGTH:
        logger.error(f"Combined body length would exceed maximum of {MAX_BODY_LENGTH} characters")
        return None
    
    if entry.body:
        entry.body = entry.body + "\n" + text
    else:
        entry.body = text
    
    return _save_updated_entry(user_id, entry, entries)

@handle_errors("setting entry body")
def set_entry_body(user_id: str, ref: str, text: str) -> Optional[Entry]:
    """Sets (replaces) an entry's body."""
    if not user_id:
        logger.error("User ID is required to set entry body.")
        return None
    
    # Validate text length
    if not is_valid_string_length(text, MAX_BODY_LENGTH, field_name="Entry body", allow_none=True):
        logger.error(f"Body text exceeds maximum length of {MAX_BODY_LENGTH} characters")
        return None
    
    entries = load_entries(user_id)
    entry = _find_entry_by_ref(entries, ref)
    
    if not entry:
        logger.error(f"Entry not found for ref '{ref}'")
        return None
    
    if entry.kind == 'list':
        logger.error("Cannot set body for list entry. Use list item operations instead.")
        return None
    
    entry.body = text
    return _save_updated_entry(user_id, entry, entries)

@handle_errors("adding tags to entry")
def add_tags(user_id: str, ref: str, tags: List[str]) -> Optional[Entry]:
    """Adds tags to an entry."""
    entries = load_entries(user_id)
    entry = _find_entry_by_ref(entries, ref)
    
    if not entry:
        logger.error(f"Entry not found for ref '{ref}'")
        return None
    
    normalized_tags = normalize_tags(tags)
    for tag in normalized_tags:
        if tag not in entry.tags:
            entry.tags.append(tag)
    
    return _save_updated_entry(user_id, entry, entries)

@handle_errors("removing tags from entry")
def remove_tags(user_id: str, ref: str, tags: List[str]) -> Optional[Entry]:
    """Removes tags from an entry."""
    entries = load_entries(user_id)
    entry = _find_entry_by_ref(entries, ref)
    
    if not entry:
        logger.error(f"Entry not found for ref '{ref}'")
        return None
    
    normalized_tags = normalize_tags(tags)
    entry.tags = [t for t in entry.tags if t not in normalized_tags]
    
    return _save_updated_entry(user_id, entry, entries)

@handle_errors("pinning entry")
def pin_entry(user_id: str, ref: str, pinned: bool = True) -> Optional[Entry]:
    """Pins or unpins an entry."""
    entries = load_entries(user_id)
    entry = _find_entry_by_ref(entries, ref)
    
    if not entry:
        logger.error(f"Entry not found for ref '{ref}'")
        return None
    
    entry.pinned = pinned
    return _save_updated_entry(user_id, entry, entries)

@handle_errors("archiving entry")
def archive_entry(user_id: str, ref: str, archived: bool = True) -> Optional[Entry]:
    """Archives or unarchives an entry."""
    entries = load_entries(user_id)
    entry = _find_entry_by_ref(entries, ref)
    
    if not entry:
        logger.error(f"Entry not found for ref '{ref}'")
        return None
    
    entry.archived = archived
    return _save_updated_entry(user_id, entry, entries)

@handle_errors("setting entry group")
def set_group(user_id: str, ref: str, group: Optional[str]) -> Optional[Entry]:
    """Sets the group for an entry."""
    # Validate group if provided
    if group is not None and not is_valid_entry_group(group):
        logger.error(f"Invalid group name: {group}")
        return None
    
    entries = load_entries(user_id)
    entry = _find_entry_by_ref(entries, ref)
    
    if not entry:
        logger.error(f"Entry not found for ref '{ref}'")
        return None
    
    entry.group = group.strip() if group and group.strip() else None
    return _save_updated_entry(user_id, entry, entries)

# Search operations
@handle_errors("searching entries", default_return=[])
def search_entries(user_id: str, query: str, limit: int = 10) -> List[Entry]:
    """
    Searches entries by case-insensitive substring across title, body, and list item texts.
    """
    if not user_id:
        logger.error("User ID is required for search.")
        return []
    
    if not query or not isinstance(query, str) or not query.strip():
        logger.error("Search query cannot be empty.")
        return []

    entries = load_entries(user_id)
    query_lower = query.lower().strip()
    
    matching_entries: List[Entry] = []
    for entry in entries:
        # Check title
        if entry.title and query_lower in entry.title.lower():
            matching_entries.append(entry)
            continue  # Skip other checks to avoid duplicates
        
        # Check body
        if entry.body and query_lower in entry.body.lower():
            matching_entries.append(entry)
            continue  # Skip other checks to avoid duplicates
        
        # Check list items
        if entry.kind == 'list' and entry.items:
            if any(query_lower in item.text.lower() for item in entry.items):
                matching_entries.append(entry)
    
    # Remove duplicates by ID (preserves order)
    seen_ids = set()
    unique_matches = []
    for entry in matching_entries:
        if entry.id not in seen_ids:
            seen_ids.add(entry.id)
            unique_matches.append(entry)
    
    # Sort by updated_at (handle timestamp parsing errors gracefully)
    try:
        unique_matches.sort(
            key=lambda e: datetime.strptime(e.updated_at, TIMESTAMP_FORMAT) 
            if isinstance(e.updated_at, str) 
            else datetime.min, 
            reverse=True
        )
    except Exception:
        # If sorting fails, just return unsorted results rather than failing completely
        logger.warning("Failed to sort search results by timestamp, returning unsorted")

    return unique_matches[:limit]

# List operations (for lists)
@handle_errors("adding list item")
def add_list_item(user_id: str, ref: str, text: str) -> Optional[Entry]:
    """Adds an item to a list entry."""
    if not user_id:
        logger.error("User ID is required to add list item.")
        return None
    
    # Validate list item text (should not be empty)
    if not text or not text.strip():
        logger.error("List item text cannot be empty")
        return None
    
    entries = load_entries(user_id)
    entry = _find_entry_by_ref(entries, ref)
    
    if not entry:
        logger.error(f"Entry not found for ref '{ref}'")
        return None
    
    if entry.kind != 'list':
        logger.error(f"Entry '{ref}' is not a list entry.")
        return None
    
    if not entry.items:
        entry.items = []
    
    new_item = ListItem(text=text.strip(), order=len(entry.items))
    entry.items.append(new_item)
    
    return _save_updated_entry(user_id, entry, entries)

@handle_errors("toggling list item done")
def toggle_list_item_done(user_id: str, ref: str, item_index: int, done: bool = True) -> Optional[Entry]:
    """Marks a list item as done or undone."""
    entries = load_entries(user_id)
    entry = _find_entry_by_ref(entries, ref)
    
    if not entry:
        logger.error(f"Entry not found for ref '{ref}'")
        return None
    
    if entry.kind != 'list' or not entry.items:
        logger.error(f"Entry '{ref}' is not a list entry or has no items.")
        return None
    
    # Normalize item index (handles both 0-based and 1-based)
    normalized_index = normalize_list_item_index(item_index, len(entry.items))
    if normalized_index is None:
        logger.error(f"Invalid item index {item_index} for list '{ref}'")
        return None
    
    entry.items[normalized_index].done = done
    entry.items[normalized_index].updated_at = datetime.now().strftime(TIMESTAMP_FORMAT)
    
    return _save_updated_entry(user_id, entry, entries)

@handle_errors("removing list item")
def remove_list_item(user_id: str, ref: str, item_index: int) -> Optional[Entry]:
    """Removes an item from a list entry."""
    entries = load_entries(user_id)
    entry = _find_entry_by_ref(entries, ref)
    
    if not entry:
        logger.error(f"Entry not found for ref '{ref}'")
        return None
    
    if entry.kind != 'list' or not entry.items:
        logger.error(f"Entry '{ref}' is not a list entry or has no items.")
        return None
    
    # Normalize item index (handles both 0-based and 1-based)
    normalized_index = normalize_list_item_index(item_index, len(entry.items))
    if normalized_index is None:
        logger.error(f"Invalid item index {item_index} for list '{ref}'")
        return None
    
    entry.items.pop(normalized_index)
    # Reorder remaining items
    for i, item in enumerate(entry.items):
        item.order = i
        item.updated_at = datetime.now().strftime(TIMESTAMP_FORMAT)
    
    return _save_updated_entry(user_id, entry, entries)

# Organization operations
@handle_errors("listing entries by group", default_return=[])
def list_by_group(user_id: str, group: str, limit: int = 20) -> List[Entry]:
    """Lists entries in a specific group."""
    entries = load_entries(user_id)
    matching = [e for e in entries if e.group and e.group.lower() == group.lower()]
    matching.sort(key=lambda e: datetime.strptime(e.updated_at, TIMESTAMP_FORMAT) if isinstance(e.updated_at, str) else datetime.min, reverse=True)
    return matching[:limit]

@handle_errors("listing pinned entries", default_return=[])
def list_pinned(user_id: str) -> List[Entry]:
    """Lists all pinned entries."""
    entries = load_entries(user_id)
    pinned = [e for e in entries if e.pinned and not e.archived]
    pinned.sort(key=lambda e: datetime.strptime(e.updated_at, TIMESTAMP_FORMAT) if isinstance(e.updated_at, str) else datetime.min, reverse=True)
    return pinned

@handle_errors("listing inbox entries", default_return=[])
def list_inbox(user_id: str, days: int = 30) -> List[Entry]:
    """Lists inbox entries (untagged, unarchived, recent)."""
    entries = load_entries(user_id)
    cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
    
    inbox = []
    for e in entries:
        if not e.archived and not e.tags:
            # Parse timestamp string to compare
            try:
                entry_timestamp = datetime.strptime(e.updated_at, TIMESTAMP_FORMAT).timestamp()
                if entry_timestamp >= cutoff:
                    inbox.append(e)
            except (ValueError, TypeError) as err:
                logger.warning(f"Invalid timestamp format for entry {e.id}: {e.updated_at} - {err}")
                # Include entry if timestamp parsing fails (better to show than hide)
                inbox.append(e)
    
    inbox.sort(key=lambda e: datetime.strptime(e.updated_at, TIMESTAMP_FORMAT) if isinstance(e.updated_at, str) else datetime.min, reverse=True)
    return inbox

@handle_errors("listing entries by tag", default_return=[])
def list_by_tag(user_id: str, tag: str, limit: int = 20) -> List[Entry]:
    """Lists entries with a specific tag."""
    from core.tags import normalize_tag
    
    entries = load_entries(user_id)
    normalized_tag = normalize_tag(tag)
    
    matching = [e for e in entries if normalized_tag in e.tags]
    matching.sort(key=lambda e: datetime.strptime(e.updated_at, TIMESTAMP_FORMAT) if isinstance(e.updated_at, str) else datetime.min, reverse=True)
    return matching[:limit]
