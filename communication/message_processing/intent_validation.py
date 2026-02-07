"""Shared intent validation for message processing.

Used by EnhancedCommandParser and InteractionManager to check whether
an intent is supported by any registered handler.
"""

from typing import Any, Mapping

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
    for handler in interaction_handlers.values():
        if handler.can_handle(intent):
            return True
    return False
