"""
Validation helpers specific to notebook objects.

This module provides validation functions for notebook entries, entry references,
and related data structures. These helpers complement Pydantic schema validation
and can be used independently for validation checks.
"""

import re
from typing import Any
from uuid import UUID

from core.error_handling import handle_errors
from core.ids import (
    MAX_SHORT_ID_LENGTH,
    MIN_SHORT_ID_LENGTH,
    NOTEBOOK_KIND_PREFIXES,
    NOTEBOOK_PREFIXES,
    PREFIX_TO_NOTEBOOK_KIND,
    format_short_id as _core_format_short_id,
    is_dashed_short_id,
    is_known_prefix,
    is_notebook_prefix,
    looks_like_short_id,
    looks_like_uuid,
    parse_short_id,
)
from core.logger import get_component_logger
from notebook.notebook_schemas import EntryKind, NotebookCollectionV2Model
from storage.user_data_validation import is_valid_category_name, is_valid_string_length

logger = get_component_logger("notebook_validation")

# Validation constants
MAX_TITLE_LENGTH = 200
MAX_BODY_LENGTH = 10000
MAX_GROUP_LENGTH = 50

# Re-export shared short-ID constants for existing imports/tests
ENTRY_KIND_PREFIXES = NOTEBOOK_KIND_PREFIXES
PREFIX_TO_KIND = PREFIX_TO_NOTEBOOK_KIND

# Re-export parse_short_id from core.ids for existing imports
__all__ = [
    "MAX_TITLE_LENGTH",
    "MAX_BODY_LENGTH",
    "MAX_GROUP_LENGTH",
    "MIN_SHORT_ID_LENGTH",
    "MAX_SHORT_ID_LENGTH",
    "ENTRY_KIND_PREFIXES",
    "PREFIX_TO_KIND",
    "looks_like_structural_entry_ref",
    "is_valid_entry_reference",
    "parse_short_id",
    "format_short_id",
    "is_valid_entry_title",
    "is_valid_entry_description",
    "is_valid_entry_group",
    "is_valid_entry_kind",
    "is_valid_list_item_index",
    "normalize_list_item_index",
    "validate_entry_content",
    "validate_notebook_v2_document",
]


@handle_errors("detecting structural entry reference", default_return=False)
def looks_like_structural_entry_ref(ref: str) -> bool:
    """True when ref looks like a UUID or short ID (not a free-text title).

    Used to disambiguate dual-use commands such as `!group <ref> <name>` vs
    `!group <multi word group name>`. Title-based assignment should use
    `!setgroup <title> <group>` instead.

    Recognizes notebook short IDs (n/l/j), bare hex, UUIDs, and other known
    shared prefixes (e.g. task ``t``) so those tokens are not treated as titles.
    """
    if not isinstance(ref, str):
        return False
    value = ref.strip()
    if not value:
        return False
    if looks_like_uuid(value):
        return True
    return looks_like_short_id(value)


@handle_errors("validating entry reference", default_return=False)
def is_valid_entry_reference(ref: str) -> bool:
    """
    Validate that an entry reference is in a valid format.

    Entry references can be:
    - Full UUID strings
    - Notebook short IDs (e.g., 'n3f2a9c', 'l91ab20' - no dash)
    - Short ID fragments (e.g., '3f2a9c')
    - Non-empty title strings

    Task short IDs (``t...``) and other non-notebook known prefixes are rejected
    (wrong domain - not treated as free-text titles).
    """
    if not isinstance(ref, str):
        logger.warning(f"Entry reference must be a string, got {type(ref).__name__}")
        return False

    ref = ref.strip()

    if not ref:
        logger.warning("Entry reference cannot be empty")
        return False

    if is_dashed_short_id(ref):
        logger.warning(
            f"Entry reference uses obsolete dashed short-id format: {ref!r} (use no-dash form)"
        )
        return False

    if looks_like_uuid(ref):
        return True

    parsed = parse_short_id(ref)
    if parsed is not None:
        prefix, _fragment = parsed
        if prefix is None:
            return True  # bare hex fragment
        if is_notebook_prefix(prefix):
            return True
        # Known non-notebook prefix (e.g. task ``t``) - wrong domain for notebook refs
        logger.warning(
            f"Short ID prefix {prefix!r} is not valid for notebook entries "
            f"(expected one of {sorted(NOTEBOOK_PREFIXES)})"
        )
        return False

    # Too-short notebook-prefixed forms (e.g. 'n12345')
    too_short = re.compile(
        rf"^[{''.join(sorted(NOTEBOOK_PREFIXES))}][0-9a-f]{{1,{MIN_SHORT_ID_LENGTH - 1}}}$",
        re.IGNORECASE,
    )
    if too_short.match(ref):
        logger.warning(
            f"Short ID fragment too short: {ref} (minimum {MIN_SHORT_ID_LENGTH} characters)"
        )
        return False

    # Short token that looks like prefix+hex with unknown / wrong-domain prefix
    if len(ref) <= 1 + MAX_SHORT_ID_LENGTH:
        maybe_prefixed = re.compile(r"^[a-z][0-9a-f]+$", re.IGNORECASE)
        if maybe_prefixed.match(ref):
            prefix = ref[0].lower()
            if is_known_prefix(prefix) and not is_notebook_prefix(prefix):
                logger.warning(
                    f"Short ID prefix {prefix!r} is not valid for notebook entries "
                    f"(expected one of {sorted(NOTEBOOK_PREFIXES)})"
                )
                return False
            if not is_notebook_prefix(prefix):
                logger.warning(
                    f"Invalid short ID prefix: {ref} (must be n, l, or j)"
                )
                return False

    # Any other non-empty string is valid as a title reference
    return True


@handle_errors("formatting notebook short ID", default_return=None)
def format_short_id(entry_id: UUID, kind: EntryKind) -> str | None:
    """
    Format a UUID into a notebook short ID with prefix (canonical length 6).

    Args:
        entry_id: UUID of the entry
        kind: Entry kind ('note', 'list', or 'journal_entry')

    Returns:
        Short ID string (e.g., 'n3f2a9c') or None if invalid
    """
    if not isinstance(entry_id, UUID):
        logger.warning(f"Entry ID must be a UUID, got {type(entry_id).__name__}")
        return None

    if kind not in ENTRY_KIND_PREFIXES:
        logger.warning(f"Invalid entry kind: {kind}")
        return None

    return _core_format_short_id(entry_id, kind)


@handle_errors("validating entry title", default_return=False)
def is_valid_entry_title(title: str | None) -> bool:
    """
    Validate that a notebook entry title is valid.

    Uses general string length validation with notebook-specific MAX_TITLE_LENGTH.

    Args:
        title: Title to validate (can be None for quick capture notes)

    Returns:
        True if title is valid, False otherwise
    """
    return is_valid_string_length(
        title, MAX_TITLE_LENGTH, field_name="Entry title", allow_none=True
    )


@handle_errors("validating entry description", default_return=False)
def is_valid_entry_description(description: str | None, kind: EntryKind = "note") -> bool:
    """
    Validate that a notebook entry description is valid.

    Uses general string length validation with notebook-specific MAX_BODY_LENGTH
    (description text length limit).
    Lists have special rules (description is always optional).

    Args:
        description: Description text to validate (can be None)
        kind: Entry kind (affects validation rules - lists always allow None/empty)

    Returns:
        True if description is valid, False otherwise
    """
    if kind == "list":
        return True

    return is_valid_string_length(
        description, MAX_BODY_LENGTH, field_name="Entry description", allow_none=True
    )


@handle_errors("validating entry group", default_return=False)
def is_valid_entry_group(group: str | None) -> bool:
    """
    Validate that a notebook entry group name is valid.

    Uses general category name validation with notebook-specific MAX_GROUP_LENGTH.

    Args:
        group: Group name to validate (can be None)

    Returns:
        True if group is valid, False otherwise
    """
    return is_valid_category_name(
        group, max_length=MAX_GROUP_LENGTH, field_name="Entry group", allow_none=True
    )


@handle_errors("validating entry kind", default_return=False)
def is_valid_entry_kind(kind: str) -> bool:
    """
    Validate that an entry kind is valid.

    Args:
        kind: Entry kind to validate

    Returns:
        True if kind is valid, False otherwise
    """
    if not isinstance(kind, str):
        logger.warning(f"Entry kind must be a string, got {type(kind).__name__}")
        return False

    valid_kinds = ["note", "list", "journal_entry"]
    if kind.lower() not in valid_kinds:
        logger.warning(f"Invalid entry kind: {kind}. Must be one of {valid_kinds}")
        return False

    return True


@handle_errors("validating list item index", default_return=False)
def is_valid_list_item_index(index: int, list_length: int) -> bool:
    """
    Validate that a list item index is valid for a given list.

    Args:
        index: Item index (0-based or 1-based)
        list_length: Length of the list

    Returns:
        True if index is valid, False otherwise
    """
    if not isinstance(index, int):
        logger.warning(
            f"List item index must be an integer, got {type(index).__name__}"
        )
        return False

    # Accept both 0-based and 1-based indexing
    if index < 0:
        logger.warning(f"List item index cannot be negative: {index}")
        return False

    # Check 1-based indexing (user-friendly) - range 1 to list_length
    if 1 <= index <= list_length:
        return True

    # Check 0-based indexing (programmer-friendly) - range 0 to list_length-1
    if 0 <= index < list_length:
        return True

    logger.warning(
        f"List item index {index} is out of range for list of length {list_length}"
    )
    return False


@handle_errors("normalizing list item index", default_return=None)
def normalize_list_item_index(index: int, list_length: int) -> int | None:
    """
    Normalize a list item index to 0-based.

    Handles both 0-based and 1-based input, converting to 0-based output.
    When an index is valid in both systems (ambiguous), prioritizes 0-based interpretation
    (programming convention). Only converts to 0-based if index is ONLY valid as 1-based.

    Args:
        index: Item index (0-based or 1-based)
        list_length: Length of the list

    Returns:
        Normalized 0-based index, or None if invalid
    """
    if not isinstance(index, int) or index < 0:
        return None

    # Check 0-based indexing first (programming convention)
    # If index is in 0-based range, return as-is
    if 0 <= index < list_length:
        return index

    # Check 1-based indexing (user-friendly)
    # Only if not in 0-based range
    if 1 <= index <= list_length:
        return index - 1

    return None


@handle_errors("validating entry content", default_return=False)
def validate_entry_content(
    title: str | None = None,
    description: str | None = None,
    kind: EntryKind = "note",
) -> tuple[bool, str | None]:
    """
    Comprehensive validation of entry content.

    Args:
        title: Entry title (optional)
        description: Entry description (optional)
        kind: Entry kind

    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message is None
    """
    if not is_valid_entry_kind(kind):
        return False, f"Invalid entry kind: {kind}"

    if not is_valid_entry_title(title):
        return False, f"Invalid entry title (max {MAX_TITLE_LENGTH} characters)"

    if not is_valid_entry_description(description, kind):
        return False, f"Invalid entry description (max {MAX_BODY_LENGTH} characters)"

    if kind in ["note", "journal_entry"] and not title and not description:
        return False, "Note or journal entries must have at least a title or description"

    return True, None


# error_handling_exclude: This validation API returns Pydantic errors as data.
def validate_notebook_v2_document(data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validate a v2 notebook/entries.json envelope and return normalized data plus errors."""
    try:
        model = NotebookCollectionV2Model.model_validate(data)
        return model.model_dump(mode="json"), []
    except Exception as exc:
        return data, [str(exc)]
