# user_preferences.py
# module user_preferences code is not yet implemented or integrated into program

import json
import os

import core.utils
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
            preferences = core.utils.get_user_preferences(self.user_id)
            return preferences or {}
        except Exception as e:
            logger.error(f"Error loading preferences for user {self.user_id}: {e}")
            return {}

    def save_preferences(self):
        """Save user preferences using the updated utils functions."""
        try:
            # Load current user data
            user_data = core.utils.load_user_info_data(self.user_id) or {}
            
            # Update preferences
            user_data['preferences'] = self.preferences
            
            # Save updated user data
            core.utils.save_user_info_data(user_data, self.user_id)
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

    def set_schedule_period_active(user_id: str, category: str, period_name: str, is_active: bool) -> bool:
        """
        Sets the active status of a specific schedule period for a user.
        """
        user_info = core.utils.load_user_info_data(user_id)
        if user_info is None:
            logger.error(f"User {user_id} not found.")
            return False
    
        schedules = user_info.get('schedules', {})
        category_schedule = schedules.get(category, {})
        period = category_schedule.get(period_name)
    
        if period is None:
            logger.error(f"Schedule period '{period_name}' not found in category '{category}' for user {user_id}.")
            return False
    
        period['active'] = is_active
        core.utils.save_user_info_data(user_info, user_id)
        status = "activated" if is_active else "deactivated"
        logger.info(f"Schedule period '{period_name}' in category '{category}' for user {user_id} has been {status}.")
        return True

    def is_schedule_period_active(user_id: str, category: str, period_name: str) -> bool:
        """
        Checks if a specific schedule period is active for a user.
        """
        user_info = core.utils.load_user_info_data(user_id)
        if user_info is None:
            logger.error(f"User {user_id} not found.")
            return False
    
        schedules = user_info.get('schedules', {})
        category_schedule = schedules.get(category, {})
        period = category_schedule.get(period_name)
    
        if period is None:
            logger.error(f"Schedule period '{period_name}' not found in category '{category}' for user {user_id}.")
            return False
    
        return period.get('active', True)