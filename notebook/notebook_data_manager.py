"""
Notebook data manager for CRUD operations on notebook entries.

Provides high-level API for managing notebook entries (notes, lists, journal).
"""

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from pydantic import ValidationError

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.ids import is_notebook_prefix, parse_short_id
from core.tags import normalize_tags
from core.time_utilities import (
    now_timestamp_full,
    parse_timestamp_full,
    now_datetime_full,
)
from notebook.notebook_schemas import Entry, ListItem, EntryKind
from notebook.notebook_data_handlers import load_entries, update_entries
from notebook.notebook_validation import (
    is_valid_entry_reference,
    is_valid_entry_kind,
    is_valid_entry_title,
    normalize_list_item_index,
    validate_entry_content,
    MAX_BODY_LENGTH,
)
from storage.user_data_validation import is_valid_string_length


logger = get_component_logger("main")


@dataclass(frozen=True)
class EntryReferenceResolution:
    """Result of resolving a notebook reference without guessing on ambiguity."""

    entry: Entry | None
    ambiguous: bool = False
    match_count: int = 0


def _is_entry_active(entry: Entry) -> bool:
    return entry.status == "active"


def _is_entry_archived(entry: Entry) -> bool:
    return entry.status == "archived"


# ERROR_HANDLING_EXCLUDE: Pure lookup helper with explicit invalid/ambiguous results.
def _resolve_entry_by_ref(
    entries: list[Entry], ref: str
) -> EntryReferenceResolution:
    """Resolve a UUID, short ID, or title only when it identifies one entry."""
    # Validate reference format
    if not is_valid_entry_reference(ref):
        logger.warning(
            "Invalid notebook entry reference format",
            reference_type=type(ref).__name__,
        )
        return EntryReferenceResolution(None)

    ref_lower = ref.lower().strip()

    # 1. Try full UUID
    for entry in entries:
        if str(entry.id) == ref:
            return EntryReferenceResolution(entry, match_count=1)

    # 2. Exact match on persisted short_id (case-insensitive)
    exact_short_matches = [
        entry
        for entry in entries
        if isinstance(getattr(entry, "short_id", None), str)
        and str(entry.short_id).strip().lower() == ref_lower
    ]
    if len(exact_short_matches) == 1:
        return EntryReferenceResolution(exact_short_matches[0], match_count=1)
    if len(exact_short_matches) > 1:
        return EntryReferenceResolution(
            None, ambiguous=True, match_count=len(exact_short_matches)
        )

    # 3. Prefixed/bare hex fragment → UUID hex startswith (notebook prefixes or bare hex only)
    parsed = parse_short_id(ref_lower)
    if parsed is not None:
        prefix, short_fragment = parsed
        if prefix is not None and not is_notebook_prefix(prefix):
            # Wrong domain (e.g. task ``t``) - do not title-match
            return EntryReferenceResolution(None)

        matching_entries = [
            entry
            for entry in entries
            if str(entry.id).lower().replace("-", "").startswith(short_fragment)
        ]
        if len(matching_entries) == 1:
            return EntryReferenceResolution(matching_entries[0], match_count=1)
        if len(matching_entries) > 1:
            logger.warning(
                "Ambiguous notebook short ID reference",
                match_count=len(matching_entries),
            )
            return EntryReferenceResolution(
                None, ambiguous=True, match_count=len(matching_entries)
            )

    # 4. Try title (case-insensitive, exact match first)
    exact_title_matches = [
        entry for entry in entries if entry.title and entry.title.lower() == ref_lower
    ]
    if len(exact_title_matches) == 1:
        return EntryReferenceResolution(exact_title_matches[0], match_count=1)
    if len(exact_title_matches) > 1:
        return EntryReferenceResolution(
            None, ambiguous=True, match_count=len(exact_title_matches)
        )

    # 5. Try title (case-insensitive, contains match)
    partial_title_matches = [
        entry for entry in entries if entry.title and ref_lower in entry.title.lower()
    ]
    if len(partial_title_matches) == 1:
        return EntryReferenceResolution(partial_title_matches[0], match_count=1)
    if len(partial_title_matches) > 1:
        return EntryReferenceResolution(
            None, ambiguous=True, match_count=len(partial_title_matches)
        )

    return EntryReferenceResolution(None)


# ERROR_HANDLING_EXCLUDE: Compatibility lookup delegates to the explicit resolver.
def _find_entry_by_ref(entries: list[Entry], ref: str) -> Entry | None:
    """Return a uniquely resolved entry, or None for missing/ambiguous references."""
    return _resolve_entry_by_ref(entries, ref).entry


@handle_errors(
    "resolving notebook entry reference",
    default_return=EntryReferenceResolution(None),
)
def resolve_entry_reference(user_id: str, ref: str) -> EntryReferenceResolution:
    """Resolve a notebook reference and preserve ambiguity for user-facing callers."""
    return _resolve_entry_by_ref(load_entries(user_id), ref)


@handle_errors("mutating notebook entry", default_return=None)
def _mutate_entry(
    user_id: str,
    ref: str,
    mutation: Callable[[Entry], bool],
    *,
    active_only: bool = False,
) -> Entry | None:
    """Mutate one uniquely resolved entry in a lock-scoped transaction."""
    # ERROR_HANDLING_EXCLUDE: Executed within update_entries' guarded transaction.
    def apply(entries: list[Entry]) -> Entry | None:
        """Resolve, mutate, validate, and return the updated entry."""
        entry = _resolve_entry_by_ref(entries, ref).entry
        if entry is None or (active_only and not _is_entry_active(entry)):
            return None
        candidate = entry.model_copy(deep=True)
        if not mutation(candidate):
            return None
        candidate.updated_at = now_timestamp_full()
        validated = Entry.model_validate(candidate.model_dump())
        entry_index = next(
            (index for index, candidate in enumerate(entries) if candidate is entry),
            None,
        )
        if entry_index is None:
            return None
        entries[entry_index] = validated
        return validated

    return update_entries(user_id, apply)


# Create operations
@handle_errors("creating entry")
def create_entry(
    user_id: str,
    kind: EntryKind,
    title: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    items: list[dict[str, Any]] | None = None,  # For list items
    metadata: dict[str, Any] | None = None,
) -> Entry | None:
    """
    Creates a new notebook entry of a specified kind.
    """
    if not user_id:
        logger.error("User ID is required to create an entry.")
        return None

    # Validate entry kind
    if not is_valid_entry_kind(kind):
        logger.error("Invalid notebook entry kind", kind_type=type(kind).__name__)
        return None

    # Validate entry content
    is_valid, error_msg = validate_entry_content(
        title=title, description=description, kind=kind
    )
    if not is_valid:
        logger.error("Invalid notebook entry content", entry_kind=kind)
        return None

    normalized_tags = normalize_tags(tags or [])

    now_ts = now_timestamp_full()

    entry_data = {
        "id": uuid.uuid4(),
        "kind": kind,
        "title": title,
        "description": description,
        "tags": normalized_tags,
        "created_at": now_ts,
        "updated_at": now_ts,
        "metadata": metadata or {},
    }

    if kind == "list":
        list_items = []
        if items:
            for i, item_data in enumerate(items):
                try:
                    # item_data might be a dict (from create_list) or already a ListItem
                    if isinstance(item_data, dict):
                        # Extract order if present, otherwise use index
                        item_values = dict(item_data)
                        item_order = item_values.pop("order", i)
                        list_items.append(ListItem(order=item_order, **item_values))
                    else:
                        # Already a ListItem or other type - convert
                        list_items.append(item_data)
                except (ValidationError, TypeError, ValueError) as exc:
                    errors = getattr(exc, "errors", None)
                    error_details = errors() if callable(errors) else None
                    error_count = (
                        len(error_details)
                        if isinstance(error_details, (list, tuple))
                        else 1
                    )
                    logger.error(
                        "Invalid notebook list item",
                        item_index=i,
                        validation_error_count=error_count,
                        exception_type=type(exc).__name__,
                    )
                    return None
        entry_data["items"] = list_items
    elif items is not None:
        logger.warning(
            "Items provided for non-list notebook entry; ignoring items",
            entry_kind=kind,
        )

    try:
        new_entry = Entry.model_validate(entry_data)
    except ValidationError as exc:
        logger.error(
            "Failed to validate new notebook entry",
            entry_kind=kind,
            validation_error_count=len(exc.errors()),
        )
        return None
    except Exception as exc:
        logger.error(
            "Unexpected error creating notebook entry",
            entry_kind=kind,
            exception_type=type(exc).__name__,
        )
        return None

    # ERROR_HANDLING_EXCLUDE: Executed within update_entries' guarded transaction.
    def append_entry(entries: list[Entry]) -> Entry:
        """Append the already validated entry to the current locked snapshot."""
        entries.append(new_entry)
        return new_entry

    saved_entry = update_entries(user_id, append_entry)
    if saved_entry is None:
        return None
    logger.info(
        "Created notebook entry",
        entry_kind=kind,
        entry_id=str(saved_entry.id),
        user_id=user_id,
    )
    return saved_entry


@handle_errors("creating note")
def create_note(
    user_id: str,
    title: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
) -> Entry | None:
    """Creates a note entry."""
    return create_entry(
        user_id, "note", title=title, description=description, tags=tags
    )


@handle_errors("creating list")
def create_list(
    user_id: str,
    title: str,
    tags: list[str] | None = None,
    items: list[str | dict[str, Any]] | None = None,
) -> Entry | None:
    """Create a list entry with final item text and completion state in one write."""
    if not items:
        # List must have at least one item - use a default placeholder
        items = ["New item"]

    list_items = []
    for i, item in enumerate(items):
        if isinstance(item, str) and item.strip():
            list_items.append({"text": item.strip(), "done": False, "order": i})
        elif (
            isinstance(item, dict)
            and isinstance(item.get("text"), str)
            and item["text"].strip()
            and type(item.get("done", False)) is bool
        ):
            list_items.append(
                {
                    "text": item["text"].strip(),
                    "done": item.get("done", False),
                    "order": i,
                }
            )

    # Ensure at least one item (shouldn't happen if items was provided, but safety check)
    if not list_items:
        list_items.append({"text": "New item", "order": 0})

    return create_entry(
        user_id, "list", title=title, tags=tags, items=list_items
    )


@handle_errors("creating journal")
def create_journal(
    user_id: str,
    title: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
) -> Entry | None:
    """Creates a journal entry."""
    return create_entry(
        user_id,
        "journal_entry",
        title=title,
        description=description,
        tags=tags,
    )


# Read operations
@handle_errors("getting entry", default_return=None)
def get_entry(user_id: str, ref: str) -> Entry | None:
    """Gets an entry by reference (UUID, short ID, or title)."""
    entries = load_entries(user_id)
    return _find_entry_by_ref(entries, ref)


@handle_errors("listing recent entries", default_return=[])
def list_recent(
    user_id: str, n: int = 5, include_archived: bool = False
) -> list[Entry]:
    """Lists the N most recently updated entries."""
    entries = load_entries(user_id)

    if not include_archived:
        entries = [e for e in entries if _is_entry_active(e)]

    # Sort by updated_at descending (parse timestamp strings for comparison)
    entries.sort(
        key=lambda e: (
            (parse_timestamp_full(e.updated_at) or datetime.min)
            if isinstance(e.updated_at, str)
            else datetime.min
        ),
        reverse=True,
    )

    return entries[:n]


# Update operations
@handle_errors("updating entry")
def update_entry(
    user_id: str, ref: str, changes: dict[str, Any]
) -> Entry | None:
    """Validate and persist a set of entry changes in one save operation."""
    allowed = {"title", "description", "items", "tags", "pinned"}
    if (
        not user_id
        or not isinstance(changes, dict)
        or not changes
        or set(changes) - allowed
    ):
        logger.error("Entry updates require a user, a reference, and supported fields.")
        return None

    # ERROR_HANDLING_EXCLUDE: Validation callback runs inside _mutate_entry.
    def apply(entry: Entry) -> bool:
        """Apply all validated field changes to the locked entry snapshot."""
        if "title" in changes:
            title = changes["title"]
            if not isinstance(title, str) or not is_valid_entry_title(title):
                logger.error("A valid entry title is required.")
                return False
            entry.title = title.strip()

        if "description" in changes:
            description = changes["description"]
            if (
                entry.kind == "list"
                or not isinstance(description, str)
                or not is_valid_string_length(
                    description,
                    MAX_BODY_LENGTH,
                    field_name="Entry description",
                    allow_none=False,
                )
            ):
                logger.error("A valid description is required for a non-list entry.")
                return False
            entry.description = description

        if "items" in changes:
            items = changes["items"]
            if (
                entry.kind != "list"
                or not isinstance(items, list)
                or not 1 <= len(items) <= 50
            ):
                logger.error("List entries require between 1 and 50 valid items.")
                return False
            updated_items: list[ListItem] = []
            now_ts = now_timestamp_full()
            existing_items = entry.items or []
            for index, value in enumerate(items):
                if (
                    not isinstance(value, dict)
                    or set(value) != {"text", "done"}
                    or not isinstance(value["text"], str)
                    or not value["text"].strip()
                    or len(value["text"]) > 500
                    or type(value["done"]) is not bool
                ):
                    logger.error(
                        "Notebook list item has invalid text or completion state",
                        item_index=index,
                    )
                    return False
                if index < len(existing_items):
                    item_values = existing_items[index].model_dump()
                    item_values.update(
                        {
                            "text": value["text"].strip(),
                            "done": value["done"],
                            "order": index,
                            "updated_at": now_ts,
                        }
                    )
                    updated_items.append(ListItem.model_validate(item_values))
                else:
                    updated_items.append(
                        ListItem(
                            text=value["text"].strip(),
                            done=value["done"],
                            order=index,
                        )
                    )
            entry.items = updated_items

        if "tags" in changes:
            tags = changes["tags"]
            if not isinstance(tags, list) or any(
                not isinstance(tag, str) for tag in tags
            ):
                logger.error("Tags must be a list of strings.")
                return False
            entry.tags = normalize_tags(tags)

        if "pinned" in changes:
            if type(changes["pinned"]) is not bool:
                logger.error("Pinned must be a boolean.")
                return False
            entry.pinned = changes["pinned"]
        return True

    return _mutate_entry(user_id, ref, apply, active_only=True)


@handle_errors("appending to entry description")
def append_to_entry_body(user_id: str, ref: str, text: str) -> Entry | None:
    """Appends text to an entry's description (command surface retains legacy name)."""
    if not user_id:
        logger.error("User ID is required to append to entry description.")
        return None

    # Validate text length
    if not is_valid_string_length(
        text, MAX_BODY_LENGTH, field_name="Appended text", allow_none=False
    ):
        logger.error(
            f"Text to append exceeds maximum length of {MAX_BODY_LENGTH} characters"
        )
        return None

    # ERROR_HANDLING_EXCLUDE: Validation callback runs inside _mutate_entry.
    def apply(entry: Entry) -> bool:
        """Append text to the locked entry snapshot."""
        if entry.kind == "list":
            logger.error(
                "Cannot append to list entry description. Use add_list_item instead."
            )
            return False
        current_desc = entry.description or ""
        separator = "\n" if current_desc else ""
        if len(current_desc) + len(separator) + len(text) > MAX_BODY_LENGTH:
            logger.error(
                f"Combined description length would exceed maximum of {MAX_BODY_LENGTH} characters"
            )
            return False
        entry.description = f"{current_desc}{separator}{text}"
        return True

    return _mutate_entry(user_id, ref, apply)


@handle_errors("setting entry description")
def set_entry_body(user_id: str, ref: str, text: str) -> Entry | None:
    """Sets (replaces) an entry's description (command surface retains legacy name)."""
    if not user_id:
        logger.error("User ID is required to set entry description.")
        return None

    # Validate text length
    if not is_valid_string_length(
        text, MAX_BODY_LENGTH, field_name="Entry description", allow_none=True
    ):
        logger.error(
            f"Description text exceeds maximum length of {MAX_BODY_LENGTH} characters"
        )
        return None

    # ERROR_HANDLING_EXCLUDE: Validation callback runs inside _mutate_entry.
    def apply(entry: Entry) -> bool:
        """Replace text on the locked entry snapshot."""
        if entry.kind == "list":
            logger.error(
                "Cannot set description for list entry. Use list item operations instead."
            )
            return False
        entry.description = text
        return True

    return _mutate_entry(user_id, ref, apply)


@handle_errors("setting entry title")
def set_entry_title(user_id: str, ref: str, title: str) -> Entry | None:
    """Replace an entry title while preserving its identity and other fields."""
    if not user_id or not isinstance(title, str) or not title.strip() or not is_valid_entry_title(title):
        logger.error("A valid entry title is required.")
        return None
    # ERROR_HANDLING_EXCLUDE: Mutation callback runs inside _mutate_entry.
    def apply(entry: Entry) -> bool:
        """Replace the title on the locked entry snapshot."""
        entry.title = title.strip()
        return True

    return _mutate_entry(user_id, ref, apply)


@handle_errors("adding tags to entry")
def add_tags(user_id: str, ref: str, tags: list[str]) -> Entry | None:
    """Adds tags to an entry."""
    normalized_tags = normalize_tags(tags)

    # ERROR_HANDLING_EXCLUDE: Mutation callback runs inside _mutate_entry.
    def apply(entry: Entry) -> bool:
        """Add normalized tags to the locked entry snapshot."""
        for tag in normalized_tags:
            if tag not in entry.tags:
                entry.tags.append(tag)
        return True

    return _mutate_entry(user_id, ref, apply)


@handle_errors("removing tags from entry")
def remove_tags(user_id: str, ref: str, tags: list[str]) -> Entry | None:
    """Removes tags from an entry."""
    normalized_tags = normalize_tags(tags)

    # ERROR_HANDLING_EXCLUDE: Mutation callback runs inside _mutate_entry.
    def apply(entry: Entry) -> bool:
        """Remove normalized tags from the locked entry snapshot."""
        entry.tags = [tag for tag in entry.tags if tag not in normalized_tags]
        return True

    return _mutate_entry(user_id, ref, apply)


@handle_errors("pinning entry")
def pin_entry(user_id: str, ref: str, pinned: bool = True) -> Entry | None:
    """Pins or unpins an entry."""
    # ERROR_HANDLING_EXCLUDE: Mutation callback runs inside _mutate_entry.
    def apply(entry: Entry) -> bool:
        """Apply the active-entry pinning rule to the locked snapshot."""
        entry.pinned = bool(pinned) if _is_entry_active(entry) else False
        return True

    return _mutate_entry(user_id, ref, apply)


@handle_errors("archiving entry")
def archive_entry(user_id: str, ref: str, archived: bool = True) -> Entry | None:
    """Archives or unarchives an entry."""
    # ERROR_HANDLING_EXCLUDE: Mutation callback runs inside _mutate_entry.
    def apply(entry: Entry) -> bool:
        """Apply archive state to the locked entry snapshot."""
        entry.status = "archived" if archived else "active"
        entry.archived_at = now_timestamp_full() if archived else None
        if archived:
            entry.pinned = False
        return True

    return _mutate_entry(user_id, ref, apply)


# Search operations
# ERROR_HANDLING_EXCLUDE: Pure selector over an already loaded notebook snapshot.
def search_entries_from_snapshot(
    entries: list[Entry], query: str, limit: int = 100
) -> list[Entry]:
    """Search one in-memory snapshot without performing additional file reads."""
    query_lower = query.lower().strip()
    matches = [
        entry
        for entry in entries
        if _is_entry_active(entry)
        and (
            (entry.title and query_lower in entry.title.lower())
            or (entry.description and query_lower in entry.description.lower())
            or (
                entry.kind == "list"
                and entry.items
                and any(query_lower in item.text.lower() for item in entry.items)
            )
        )
    ]
    try:
        matches.sort(
            key=lambda entry: (
                (parse_timestamp_full(entry.updated_at) or datetime.min)
                if isinstance(entry.updated_at, str)
                else datetime.min
            ),
            reverse=True,
        )
    except Exception:
        logger.warning("Failed to sort notebook search results")
    return matches[:limit]


@handle_errors("searching entries", default_return=[])
def search_entries(user_id: str, query: str, limit: int = 100) -> list[Entry]:
    """
    Searches entries by case-insensitive substring across title, description, and list item texts.
    Returns up to limit entries (pagination handled in handler).
    """
    if not user_id:
        logger.error("User ID is required for search.")
        return []

    if not query or not isinstance(query, str) or not query.strip():
        logger.error("Search query cannot be empty.")
        return []

    try:
        return search_entries_from_snapshot(load_entries(user_id), query, limit)
    except Exception:
        logger.warning("Failed to search notebook snapshot")
        return []


# List operations (for lists)
@handle_errors("adding list item")
def add_list_item(user_id: str, ref: str, text: str) -> Entry | None:
    """Adds an item to a list entry."""
    if not user_id:
        logger.error("User ID is required to add list item.")
        return None

    # Validate list item text (should not be empty)
    if not text or not text.strip():
        logger.error("List item text cannot be empty")
        return None

    # ERROR_HANDLING_EXCLUDE: Mutation callback runs inside _mutate_entry.
    def apply(entry: Entry) -> bool:
        """Append a new item to the locked list snapshot."""
        if entry.kind != "list":
            logger.error("Notebook entry is not a list")
            return False
        if entry.items is None:
            entry.items = []
        entry.items.append(ListItem(text=text.strip(), order=len(entry.items)))
        return True

    return _mutate_entry(user_id, ref, apply)


@handle_errors("toggling list item done")
def toggle_list_item_done(
    user_id: str, ref: str, item_index: int, done: bool = True
) -> Entry | None:
    """Marks a list item as done or undone."""
    # ERROR_HANDLING_EXCLUDE: Mutation callback runs inside _mutate_entry.
    def apply(entry: Entry) -> bool:
        """Update one completion state in the locked list snapshot."""
        if entry.kind != "list" or not entry.items:
            logger.error("Notebook entry is not a list or has no items")
            return False
        normalized_index = normalize_list_item_index(item_index, len(entry.items))
        if normalized_index is None:
            logger.error("Invalid notebook list item index", item_index=item_index)
            return False
        entry.items[normalized_index].done = done
        entry.items[normalized_index].updated_at = now_timestamp_full()
        return True

    return _mutate_entry(user_id, ref, apply)


@handle_errors("removing list item")
def remove_list_item(user_id: str, ref: str, item_index: int) -> Entry | None:
    """Removes an item from a list entry."""
    # ERROR_HANDLING_EXCLUDE: Mutation callback runs inside _mutate_entry.
    def apply(entry: Entry) -> bool:
        """Remove and reorder one item in the locked list snapshot."""
        if entry.kind != "list" or not entry.items:
            logger.error("Notebook entry is not a list or has no items")
            return False
        normalized_index = normalize_list_item_index(item_index, len(entry.items))
        if normalized_index is None:
            logger.error("Invalid notebook list item index", item_index=item_index)
            return False
        entry.items.pop(normalized_index)
        now_ts = now_timestamp_full()
        for index, item in enumerate(entry.items):
            item.order = index
            item.updated_at = now_ts
        return True

    return _mutate_entry(user_id, ref, apply)


@handle_errors("replacing list items")
def set_list_items(user_id: str, ref: str, items: list[dict[str, Any]]) -> Entry | None:
    """Replace a list's editable item text and completion states in one save."""
    if not user_id or not isinstance(items, list) or not 1 <= len(items) <= 50:
        logger.error("Lists require between 1 and 50 items.")
        return None
    # ERROR_HANDLING_EXCLUDE: Mutation callback runs inside _mutate_entry.
    def apply(entry: Entry) -> bool:
        """Replace editable list items in the locked snapshot."""
        if entry.kind != "list":
            logger.error("Notebook entry is not a list")
            return False
        updated_items: list[ListItem] = []
        now_ts = now_timestamp_full()
        for index, value in enumerate(items):
            if (
                not isinstance(value, dict)
                or not isinstance(value.get("text"), str)
                or not value["text"].strip()
                or type(value.get("done", False)) is not bool
            ):
                logger.error(
                    "Notebook list item has invalid text or completion state",
                    item_index=index,
                )
                return False
            if entry.items and index < len(entry.items):
                item = entry.items[index]
                item.text = value["text"].strip()
                item.done = value.get("done", False)
                item.order = index
                item.updated_at = now_ts
            else:
                item = ListItem(
                    text=value["text"],
                    done=value.get("done", False),
                    order=index,
                )
            updated_items.append(item)
        entry.items = updated_items
        return True

    return _mutate_entry(user_id, ref, apply)


# Organization operations
# ERROR_HANDLING_EXCLUDE: Pure selector over an already loaded notebook snapshot.
def list_pinned_from_snapshot(
    entries: list[Entry], limit: int = 100
) -> list[Entry]:
    """Return active pinned entries from an in-memory snapshot."""
    pinned = [entry for entry in entries if entry.pinned and _is_entry_active(entry)]
    pinned.sort(
        key=lambda entry: (
            (parse_timestamp_full(entry.updated_at) or datetime.min)
            if isinstance(entry.updated_at, str)
            else datetime.min
        ),
        reverse=True,
    )
    return pinned[:limit]


@handle_errors("listing pinned entries", default_return=[])
def list_pinned(user_id: str, limit: int = 100) -> list[Entry]:
    """Lists pinned entries (up to limit - pagination handled in handler)."""
    return list_pinned_from_snapshot(load_entries(user_id), limit)


# ERROR_HANDLING_EXCLUDE: Pure selector over an already loaded notebook snapshot.
def list_inbox_from_snapshot(
    entries: list[Entry], days: int = 30, limit: int = 100
) -> list[Entry]:
    """Return recent active untagged entries from an in-memory snapshot."""
    cutoff = now_datetime_full().timestamp() - (days * 24 * 60 * 60)
    inbox = []
    for entry in entries:
        if not _is_entry_active(entry) or entry.tags:
            continue
        parsed_updated_at = parse_timestamp_full(entry.updated_at)
        if parsed_updated_at is None or parsed_updated_at.timestamp() >= cutoff:
            inbox.append(entry)
    inbox.sort(
        key=lambda entry: (
            (parse_timestamp_full(entry.updated_at) or datetime.min)
            if isinstance(entry.updated_at, str)
            else datetime.min
        ),
        reverse=True,
    )
    return inbox[:limit]


@handle_errors("listing inbox entries", default_return=[])
def list_inbox(user_id: str, days: int = 30, limit: int = 100) -> list[Entry]:
    """Lists inbox entries (untagged, unarchived, recent) - up to limit (pagination handled in handler)."""
    return list_inbox_from_snapshot(load_entries(user_id), days, limit)


@handle_errors("listing archived entries", default_return=[])
def list_archived(user_id: str, limit: int = 100) -> list[Entry]:
    """Lists archived entries - up to limit (pagination handled in handler)."""
    entries = load_entries(user_id)
    archived = [e for e in entries if _is_entry_archived(e)]
    archived.sort(
        key=lambda e: (
            (parse_timestamp_full(e.updated_at) or datetime.min)
            if isinstance(e.updated_at, str)
            else datetime.min
        ),
        reverse=True,
    )
    return archived[:limit]


@handle_errors("listing entries by tag", default_return=[])
def list_by_tag(user_id: str, tag: str, limit: int = 100) -> list[Entry]:
    """Lists entries with a specific tag - up to limit (pagination handled in handler)."""
    from core.tags import normalize_tag

    entries = load_entries(user_id)
    normalized_tag = normalize_tag(tag)

    matching = [e for e in entries if normalized_tag in e.tags]
    matching.sort(
        key=lambda e: (
            (parse_timestamp_full(e.updated_at) or datetime.min)
            if isinstance(e.updated_at, str)
            else datetime.min
        ),
        reverse=True,
    )
    return matching[:limit]
