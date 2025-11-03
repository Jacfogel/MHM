"""Message processing package.

Contains utilities for processing inbound and outbound communication messages,
including conversation flow management, command parsing, message routing,
and interaction management.
"""

# Main public API - package-level exports for easier refactoring
# Note: EnhancedCommandParser is exported from parent communication package
from .interaction_manager import (
    InteractionManager,
    handle_user_message,
    get_interaction_manager,
    CommandDefinition,
)

__all__ = [
    # Interaction management
    'InteractionManager',
    'handle_user_message',
    'get_interaction_manager',
    'CommandDefinition',
]
