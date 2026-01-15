# user_preferences.py
#
# NOTE: This module is available for use but is not currently integrated into the codebase.
# The codebase currently accesses preferences directly via get_user_data() and update_user_preferences().
#
# When to use UserPreferences:
# - When making multiple preference changes in sequence (avoids multiple update calls)
# - When you need to track preference state changes during a workflow
# - For future preference management UI features that need object-oriented access
#
# When to use direct access (get_user_data/update_user_preferences):
# - For single preference reads/writes (current pattern, works well)
# - When you only need one preference value
#
# See development_docs/PLANS.md "User Context & Preferences Integration Investigation" for details.

from core.user_data_handlers import get_user_data, update_user_preferences
from core.schedule_management import (
    set_schedule_period_active,
    is_schedule_period_active,
)
from core.logger import get_component_logger
from core.error_handling import handle_errors

logger = get_component_logger("user_activity")
preferences_logger = get_component_logger("user_activity")


class UserPreferences:
    """
    Manages user preferences and settings.

    Provides methods for loading, saving, and managing user preferences
    including schedule period settings and general user preferences.

    Note: This class is available but currently unused in the codebase. Most code
    accesses preferences directly via get_user_data() and update_user_preferences().
    This class is useful for workflows that need to make multiple preference changes
    or track preference state during operations.

    Example usage:
        prefs = UserPreferences(user_id)
        prefs.set_preference('theme', 'dark')
        prefs.set_preference('notifications', True)
        # Both changes saved automatically
    """

    # ERROR_HANDLING_EXCLUDE: Simple constructor that only sets attributes
    def __init__(self, user_id):
        """
        Initialize UserPreferences for a specific user.

        Args:
            user_id: The user's unique identifier
        """
        self.user_id = user_id
        self.preferences = self.load_preferences()

    @handle_errors("loading preferences", default_return={})
    def load_preferences(self):
        """Load user preferences using the new user management functions."""
        # Use the new user management functions
        prefs_result = get_user_data(self.user_id, "preferences")
        preferences = prefs_result.get("preferences") or {}
        return preferences or {}

    @handle_errors("saving preferences")
    def save_preferences(self):
        """Save user preferences using the new user management functions."""
        # Use the new update function
        update_user_preferences(self.user_id, self.preferences)
        logger.info(f"User preferences saved for {self.user_id}")

    @handle_errors("setting preference")
    def set_preference(self, key, value):
        """Set a preference and save it."""
        self.preferences[key] = value
        self.save_preferences()
        logger.debug(f"Preference set for user {self.user_id}: {key} = {value}")

    @handle_errors("getting preference", default_return=None)
    def get_preference(self, key):
        """Get a preference value."""
        return self.preferences.get(key)

    @handle_errors("updating preference")
    def update_preference(self, key, value):
        """Update a preference (alias for set_preference for consistency)."""
        self.set_preference(key, value)

    @handle_errors("removing preference")
    def remove_preference(self, key):
        """Remove a preference."""
        if key in self.preferences:
            del self.preferences[key]
            self.save_preferences()
            logger.debug(f"Preference removed for user {self.user_id}: {key}")
        else:
            logger.warning(f"Preference {key} not found for user {self.user_id}")

    @handle_errors("getting all preferences", default_return={})
    def get_all_preferences(self):
        """Get all preferences."""
        return self.preferences.copy()

    @staticmethod
    @handle_errors("setting schedule period active", default_return=False)
    def set_schedule_period_active(
        user_id: str, category: str, period_name: str, is_active: bool
    ) -> bool:
        """Wrapper for :func:`core.schedule_management.set_schedule_period_active`."""
        return set_schedule_period_active(
            user_id, category, period_name, active=is_active
        )

    @staticmethod
    @handle_errors("checking if schedule period active", default_return=False)
    def is_schedule_period_active(
        user_id: str, category: str, period_name: str
    ) -> bool:
        """Wrapper for :func:`core.schedule_management.is_schedule_period_active`."""
        return is_schedule_period_active(user_id, category, period_name)
