"""Command handlers package.

Contains handlers that process incoming communication commands,
including task management, check-ins, scheduling, analytics, and profiles.
"""

# Main public API - package-level exports for easier refactoring
from .shared_types import InteractionResponse, ParsedCommand
from .base_handler import InteractionHandler
from .interaction_handlers import (
    get_all_handlers,
    get_interaction_handler,
)

__all__ = [
    # Shared types
    'InteractionResponse',
    'ParsedCommand',
    # Interaction handlers
    'InteractionHandler',
    'get_all_handlers',
    'get_interaction_handler',
]
