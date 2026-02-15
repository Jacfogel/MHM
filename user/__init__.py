"""User package for the MHM application.

Contains user context management, user preferences handling, and context manager
utilities for maintaining user state and personalization across sessions.
"""

__all__ = [
    # Context management
    "UserContextManager",
    "user_context_manager",
    # User context
    "UserContext",
    # User preferences
    "UserPreferences",
]


def __getattr__(name):
    """Lazy-load user package exports to avoid import cycles during module init."""
    if name in ("UserContextManager", "user_context_manager"):
        from .context_manager import UserContextManager, user_context_manager

        return (
            UserContextManager
            if name == "UserContextManager"
            else user_context_manager
        )
    if name == "UserContext":
        from .user_context import UserContext

        return UserContext
    if name == "UserPreferences":
        from .user_preferences import UserPreferences

        return UserPreferences
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
