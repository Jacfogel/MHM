"""
Shared external short-ID helpers for MHM.

Canonical format: ``{prefix}{hex}`` with no hyphen (mobile-friendly).
Prefixes include task ``t``, notebook ``n``/``l``/``j``, plus message/delivery/checkin.
"""

from __future__ import annotations

import re
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("ids")

DEFAULT_SHORT_ID_LENGTH = 6
MIN_SHORT_ID_LENGTH = 6
MAX_SHORT_ID_LENGTH = 8

# Kind -> single-letter prefix (persistence and display)
KIND_PREFIXES: dict[str, str] = {
    "task": "t",
    "note": "n",
    "list": "l",
    "journal": "j",
    "journal_entry": "j",
    "message": "m",
    "delivery": "d",
    "checkin": "c",
}

TASK_PREFIX = "t"
NOTEBOOK_PREFIXES: frozenset[str] = frozenset({"n", "l", "j"})
KNOWN_PREFIXES: frozenset[str] = frozenset(KIND_PREFIXES.values())

# Notebook kind -> prefix (subset used by notebook validation/display)
NOTEBOOK_KIND_PREFIXES: dict[str, str] = {
    "note": "n",
    "list": "l",
    "journal_entry": "j",
}
PREFIX_TO_NOTEBOOK_KIND: dict[str, str] = {v: k for k, v in NOTEBOOK_KIND_PREFIXES.items()}

_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_HEX_FRAGMENT_PATTERN = re.compile(
    rf"^[0-9a-f]{{{MIN_SHORT_ID_LENGTH},{MAX_SHORT_ID_LENGTH}}}$",
    re.IGNORECASE,
)


@handle_errors("coercing stable uuid for short id", re_raise=True)
def _stable_uuid(value: str) -> UUID:
    """Return value as a UUID, deriving a deterministic UUID when not UUID-shaped."""
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return uuid5(NAMESPACE_URL, str(value))


@handle_errors("checking known short-id prefix", default_return=False)
def is_known_prefix(prefix: str | None) -> bool:
    """True when *prefix* is a registered short-ID letter (t/n/l/j/m/d/c)."""
    if not isinstance(prefix, str) or len(prefix) != 1:
        return False
    return prefix.lower() in KNOWN_PREFIXES


@handle_errors("checking notebook short-id prefix", default_return=False)
def is_notebook_prefix(prefix: str | None) -> bool:
    """True when *prefix* is a notebook entry prefix (n/l/j)."""
    if not isinstance(prefix, str) or len(prefix) != 1:
        return False
    return prefix.lower() in NOTEBOOK_PREFIXES


@handle_errors("checking dashed short-id form", default_return=False)
def is_dashed_short_id(ref: str) -> bool:
    """True for obsolete prefix + hyphen + hex forms (6-8 hex digits after the hyphen)."""
    if not isinstance(ref, str):
        return False
    value = ref.strip()
    if not value:
        return False
    pattern = re.compile(
        rf"^[{''.join(sorted(KNOWN_PREFIXES))}]-[0-9a-f]{{{MIN_SHORT_ID_LENGTH},{MAX_SHORT_ID_LENGTH}}}$",
        re.IGNORECASE,
    )
    return bool(pattern.match(value))


@handle_errors("generating short id", re_raise=True)
def generate_short_id(record_id: str, kind: str, length: int = DEFAULT_SHORT_ID_LENGTH) -> str:
    """Generate a mobile-friendly no-dash short ID from a UUID-like value."""
    prefix = KIND_PREFIXES.get(kind, kind[:1].lower() if kind else "?")
    uuid_value = _stable_uuid(str(record_id))
    fragment = str(uuid_value).replace("-", "")[:length]
    return f"{prefix}{fragment}"


@handle_errors("formatting short id", default_return=None)
def format_short_id(entry_id: UUID | str, kind: str) -> str | None:
    """
    Format an ID into a short ID with kind prefix (default length 6).

    Accepts ``UUID`` or UUID-shaped / arbitrary strings (non-UUID strings use
    the same stable mapping as ``generate_short_id``). Returns ``None`` for
    unknown kinds that are not notebook/task/message/etc. and empty kind.
    """
    if kind not in KIND_PREFIXES:
        logger.warning(f"Invalid short-id kind: {kind}")
        return None

    if isinstance(entry_id, UUID):
        record_id = str(entry_id)
    elif isinstance(entry_id, str) and entry_id.strip():
        record_id = entry_id.strip()
    else:
        logger.warning(f"Entry ID must be a UUID or string, got {type(entry_id).__name__}")
        return None

    return generate_short_id(record_id, kind, length=DEFAULT_SHORT_ID_LENGTH)


@handle_errors("parsing short ID", default_return=None)
def parse_short_id(ref: str) -> tuple[str | None, str] | None:
    """
    Parse a short ID into ``(prefix, fragment)``.

    Prefix is ``None`` for bare hex fragments (6-8 chars).
    Accepts all known prefixes including task ``t``.
    """
    if not isinstance(ref, str):
        return None

    value = ref.strip().lower()
    if not value:
        return None

    if len(value) > 1 and value[0] in KNOWN_PREFIXES:
        prefix = value[0]
        fragment = value[1:]
        if (
            MIN_SHORT_ID_LENGTH <= len(fragment) <= MAX_SHORT_ID_LENGTH
            and re.fullmatch(r"[0-9a-f]+", fragment)
        ):
            return (prefix, fragment)
        # Wrong length for a prefixed id: may still be a bare hex fragment
        # (prefixes ``c``/``d`` overlap hex digits). Fall through.

    if _HEX_FRAGMENT_PATTERN.fullmatch(value):
        return (None, value)

    return None


@handle_errors("detecting short-id shape", default_return=False)
def looks_like_short_id(ref: str) -> bool:
    """True when *ref* looks like a prefixed or bare hex short ID (any known prefix)."""
    if not isinstance(ref, str):
        return False
    value = ref.strip()
    if not value or is_dashed_short_id(value):
        return False
    return parse_short_id(value) is not None


@handle_errors("detecting UUID shape", default_return=False)
def looks_like_uuid(ref: str) -> bool:
    """True when *ref* is a full UUID string."""
    if not isinstance(ref, str):
        return False
    return bool(_UUID_PATTERN.match(ref.strip()))


@handle_errors("displaying short id", default_return="")
def display_short_id(
    *,
    short_id: str | None = None,
    record_id: Any = None,
    kind: str | None = None,
) -> str:
    """Prefer persisted ``short_id``; otherwise generate from ``record_id`` + ``kind``."""
    if isinstance(short_id, str) and short_id.strip():
        return short_id.strip()

    if record_id is None or not kind:
        return ""

    formatted = format_short_id(record_id if isinstance(record_id, UUID) else str(record_id), kind)
    return formatted or ""
