"""Shared intent validation for message processing.

Used by EnhancedCommandParser and InteractionManager to check whether
an intent is supported by any registered handler.
"""

import re
from collections.abc import Iterable, Mapping
from typing import Any

from core.error_handling import handle_errors


@handle_errors("checking if intent is valid", default_return=False)
def is_valid_intent(intent: str, interaction_handlers: Mapping[str, Any]) -> bool:
    """Return True if any handler can handle the given intent.

    Args:
        intent: The intent string to validate.
        interaction_handlers: Mapping of handler name to handler instance;
            each value must have a can_handle(intent) method.

    Returns:
        True if any handler's can_handle(intent) returns True, False otherwise.
    """
    return any(handler.can_handle(intent) for handler in interaction_handlers.values())


@handle_errors("canonicalizing intent name", default_return="")
def canonicalize_intent_name(
    raw: str, known_intents: Iterable[str] | None = None
) -> str:
    """Normalize spaced or hyphenated ACTION names to live parser intent names.

    ``create task`` becomes ``create_task``. ``start check-in`` becomes
    ``start_checkin`` when that intent exists (hyphen compact-match).
    """
    normalized = re.sub(r"[^a-z0-9_]+", "_", (raw or "").strip().lower()).strip("_")
    if not normalized:
        return ""
    if known_intents is None:
        return normalized
    known = list(known_intents)
    if normalized in known:
        return normalized
    compact = normalized.replace("_", "")
    for name in known:
        if name.replace("_", "") == compact:
            return name
    return normalized
