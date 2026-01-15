"""User package for the MHM application.

Contains user context management, user preferences handling, and context manager
utilities for maintaining user state and personalization across sessions.
"""

# Main public API - package-level exports for easier refactoring
from .context_manager import UserContextManager, user_context_manager
from .user_context import UserContext
from .user_preferences import UserPreferences

__all__ = [
    # Context management
    "UserContextManager",
    "user_context_manager",
    # User context
    "UserContext",
    # User preferences
    "UserPreferences",
]
