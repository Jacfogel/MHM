# user_preferences.py
# module user_preferences code is not yet implemented or integrated into program

import json
import os

from core.user_management import get_user_preferences, load_user_info_data, save_user_info_data
from core.schedule_management import set_schedule_period_active, is_schedule_period_active
from core.logger import get_logger

logger = get_logger(__name__)

class UserPreferences:
    def __init__(self, user_id):
        self.user_id = user_id
        self.preferences = self.load_preferences()

    def load_preferences(self):
        """Load user preferences using the updated utils functions."""
        try:
            # Use the updated utils function that supports new structure
            preferences = get_user_preferences(self.user_id)
            return preferences or {}
        except Exception as e:
            logger.error(f"Error loading preferences for user {self.user_id}: {e}")
            return {}

    def save_preferences(self):
        """Save user preferences using the updated utils functions."""
        try:
            # Load current user data
            user_data = load_user_info_data(self.user_id) or {}
            
            # Update preferences
            user_data['preferences'] = self.preferences
            
            # Save updated user data
            save_user_info_data(user_data, self.user_id)
            logger.info(f"User preferences saved for {self.user_id}")
        except Exception as e:
            logger.error(f"Error saving preferences for user {self.user_id}: {e}")

    def set_preference(self, key, value):
        """Set a preference and save it."""
        self.preferences[key] = value
        self.save_preferences()
        logger.debug(f"Preference set for user {self.user_id}: {key} = {value}")

    def get_preference(self, key):
        """Get a preference value."""
        return self.preferences.get(key)
    
    def update_preference(self, key, value):
        """Update a preference (alias for set_preference for consistency)."""
        self.set_preference(key, value)
    
    def remove_preference(self, key):
        """Remove a preference."""
        if key in self.preferences:
            del self.preferences[key]
            self.save_preferences()
            logger.debug(f"Preference removed for user {self.user_id}: {key}")
        else:
            logger.warning(f"Preference {key} not found for user {self.user_id}")
    
    def get_all_preferences(self):
        """Get all preferences."""
        return self.preferences.copy()

    @staticmethod
    def set_schedule_period_active(user_id: str, category: str, period_name: str, is_active: bool) -> bool:
        """Wrapper for :func:`core.schedule_management.set_schedule_period_active`."""
        return set_schedule_period_active(
            user_id, category, period_name, active=is_active
        )

    @staticmethod
    def is_schedule_period_active(user_id: str, category: str, period_name: str) -> bool:
        """Wrapper for :func:`core.schedule_management.is_schedule_period_active`."""
        return is_schedule_period_active(user_id, category, period_name)
