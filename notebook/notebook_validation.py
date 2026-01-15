"""
Validation helpers specific to notebook objects.

This module provides validation functions for notebook entries, entry references,
and related data structures. These helpers complement Pydantic schema validation
and can be used independently for validation checks.
"""

import re
from typing import Optional, Tuple
from uuid import UUID

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.user_data_validation import is_valid_string_length, is_valid_category_name
from notebook.schemas import EntryKind

logger = get_component_logger("notebook_validation")

# Validation constants
MAX_TITLE_LENGTH = 200
MAX_BODY_LENGTH = 10000
MAX_GROUP_LENGTH = 50
MIN_SHORT_ID_LENGTH = 6
MAX_SHORT_ID_LENGTH = 8

# Short ID prefix mapping
ENTRY_KIND_PREFIXES = {"note": "n", "list": "l", "journal": "j"}

# Reverse mapping for prefix to kind
PREFIX_TO_KIND = {v: k for k, v in ENTRY_KIND_PREFIXES.items()}


@handle_errors("validating entry reference", default_return=False)
def is_valid_entry_reference(ref: str) -> bool:
    """
    Validate that an entry reference is in a valid format.

    Entry references can be:
    - Full UUID strings
    - Short IDs (e.g., 'n3f2a9c', 'l91ab20' - no dash for easier mobile typing)
    - Short ID fragments (e.g., '3f2a9c')
    - Non-empty title strings

    Args:
        ref: Entry reference to validate

    Returns:
        True if reference format is valid, False otherwise
    """
    if not isinstance(ref, str):
        logger.warning(f"Entry reference must be a string, got {type(ref).__name__}")
        return False

    ref = ref.strip()

    if not ref:
        logger.warning("Entry reference cannot be empty")
        return False

    # Check if it's a valid UUID format
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
    )
    if uuid_pattern.match(ref):
        return True

    # Check if it looks like a short ID with prefix but is invalid (e.g., 'n12345' - too short)
    # Reject invalid short ID formats explicitly (no dash - mobile-friendly format)
    invalid_short_id_prefix = re.compile(r"^[nlj][0-9a-f]{1,5}$", re.IGNORECASE)
    if invalid_short_id_prefix.match(ref):
        logger.warning(
            f"Short ID fragment too short: {ref} (minimum {MIN_SHORT_ID_LENGTH} characters)"
        )
        return False

    # Check if it's a valid short ID with prefix (e.g., 'n3f2a9c' - no dash for easier mobile typing)
    # Fragment must be at least MIN_SHORT_ID_LENGTH characters
    short_id_with_prefix = re.compile(
        rf"^[nlj][0-9a-f]{{{MIN_SHORT_ID_LENGTH},{MAX_SHORT_ID_LENGTH}}}$",
        re.IGNORECASE,
    )
    if short_id_with_prefix.match(ref):
        return True

    # Check if it's a valid short ID fragment (e.g., '3f2a9c')
    # Fragment must be at least MIN_SHORT_ID_LENGTH characters
    short_id_fragment = re.compile(
        rf"^[0-9a-f]{{{MIN_SHORT_ID_LENGTH},{MAX_SHORT_ID_LENGTH}}}$", re.IGNORECASE
    )
    if short_id_fragment.match(ref):
        return True

    # Check if it looks like a short ID with invalid prefix (e.g., 'x3f2a9c')
    # Only check if it's short enough to be a short ID (max 9 chars: prefix + 8 hex)
    # Longer strings are likely titles, not short IDs
    if len(ref) <= 9:
        invalid_prefix_pattern = re.compile(r"^[a-z][0-9a-f]+$", re.IGNORECASE)
        if invalid_prefix_pattern.match(ref):
            # Check if prefix is valid (n, l, j)
            prefix = ref[0].lower()
            if prefix not in ["n", "l", "j"]:
                logger.warning(f"Invalid short ID prefix: {ref} (must be n, l, or j)")
                return False

    # Any other non-empty string is valid as a title reference
    # (actual matching will be done by data manager)
    return True


@handle_errors("parsing short ID", default_return=None)
def parse_short_id(ref: str) -> tuple[str, str] | None:
    """
    Parse a short ID reference into (prefix, fragment) tuple.

    Args:
        ref: Short ID reference (e.g., 'n3f2a9c' or '3f2a9c' - no dash for easier mobile typing)

    Returns:
        Tuple of (prefix, fragment) if valid, None otherwise
        Prefix will be None if not provided (fragment-only)
    """
    if not isinstance(ref, str):
        return None

    ref = ref.strip().lower()

    # Check for prefix format (e.g., 'n3f2a9c' - no dash for easier mobile typing)
    if len(ref) > 1 and ref[0] in PREFIX_TO_KIND:
        prefix = ref[0]
        fragment = ref[1:]
        if len(fragment) >= MIN_SHORT_ID_LENGTH and re.match(r"^[0-9a-f]+$", fragment):
            return (prefix, fragment)

    # Check for fragment-only format (e.g., '3f2a9c')
    if re.match(r"^[0-9a-f]{6,8}$", ref):
        return (None, ref)

    return None


@handle_errors("formatting short ID", default_return=None)
def format_short_id(entry_id: UUID, kind: EntryKind) -> str | None:
    """
    Format a UUID into a short ID with prefix.

    Args:
        entry_id: UUID of the entry
        kind: Entry kind ('note', 'list', or 'journal')

    Returns:
        Short ID string (e.g., 'n3f2a9c' - no dash for easier mobile typing) or None if invalid
    """
    if not isinstance(entry_id, UUID):
        logger.warning(f"Entry ID must be a UUID, got {type(entry_id).__name__}")
        return None

    if kind not in ENTRY_KIND_PREFIXES:
        logger.warning(f"Invalid entry kind: {kind}")
        return None

    prefix = ENTRY_KIND_PREFIXES[kind]
    fragment = str(entry_id).replace("-", "")[:MAX_SHORT_ID_LENGTH]

    # No dash for easier mobile typing (e.g., n3f2a9c instead of n-3f2a9c)
    return f"{prefix}{fragment}"


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


@handle_errors("validating entry body", default_return=False)
def is_valid_entry_body(body: str | None, kind: EntryKind = "note") -> bool:
    """
    Validate that a notebook entry body is valid.

    Uses general string length validation with notebook-specific MAX_BODY_LENGTH.
    Lists have special rules (body is always optional).

    Args:
        body: Body text to validate (can be None)
        kind: Entry kind (affects validation rules - lists always allow None/empty)

    Returns:
        True if body is valid, False otherwise
    """
    # For lists, body is optional and can be empty (notebook-specific rule)
    if kind == "list":
        return True

    return is_valid_string_length(
        body, MAX_BODY_LENGTH, field_name="Entry body", allow_none=True
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

    valid_kinds = ["note", "list", "journal"]
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
    title: str | None = None, body: str | None = None, kind: EntryKind = "note"
) -> tuple[bool, str | None]:
    """
    Comprehensive validation of entry content.

    Args:
        title: Entry title (optional)
        body: Entry body (optional)
        kind: Entry kind

    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message is None
    """
    if not is_valid_entry_kind(kind):
        return False, f"Invalid entry kind: {kind}"

    if not is_valid_entry_title(title):
        return False, f"Invalid entry title (max {MAX_TITLE_LENGTH} characters)"

    if not is_valid_entry_body(body, kind):
        return False, f"Invalid entry body (max {MAX_BODY_LENGTH} characters)"

    # For notes and journals, at least title or body should be present
    if kind in ["note", "journal"]:
        if not title and not body:
            return False, "Note or journal entries must have at least a title or body"

    return True, None
