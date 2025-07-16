# user_context.py

import json
import os
import threading
from core.logger import get_logger
from core.user_management import get_user_data, update_user_account, update_user_preferences, update_user_context
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)

logger = get_logger(__name__)

class UserContext:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(UserContext, cls).__new__(cls)
                cls._instance.user_data = {}
        return cls._instance

    @handle_errors("loading user data")
    def load_user_data(self, user_id):
        """
        Loads user data using the new user management functions.
        
        Args:
            user_id (str): The user ID whose data needs to be loaded.
        """
        if not user_id:
            logger.error("Attempted to load user data with None user_id")
            return
        
        # Use the new user management functions
        user_data_result = get_user_data(user_id, 'account')
        account_data = user_data_result.get('account') or {}
        prefs_result = get_user_data(user_id, 'preferences')
        preferences_data = prefs_result.get('preferences') or {}
        context_result = get_user_data(user_id, 'context')
        context_data = context_result.get('context') or {}
        
        # Combine into legacy format for compatibility
        user_data = {
            "user_id": account_data.get("user_id", user_id),
            "internal_username": account_data.get("internal_username", ""),
            "active": account_data.get("account_status") == "active",
            "preferred_name": context_data.get("preferred_name", ""),
            "chat_id": account_data.get("chat_id", ""),
            "phone": account_data.get("phone", ""),
            "email": account_data.get("email", ""),
            "discord_user_id": account_data.get("discord_user_id", ""),
            "created_at": account_data.get("created_at", ""),
            "last_updated": account_data.get("updated_at", ""),
            "preferences": preferences_data,
            "schedules": {}  # Schedules are handled separately
        }
        
        self.user_data = user_data
        logger.info(f"User data loaded for user_id {user_id}")

    @handle_errors("saving user data")
    def save_user_data(self, user_id):
        """
        Saves user data using the new user management functions.
        
        Args:
            user_id (str): The user ID whose data needs to be saved.
        """
        if not user_id:
            logger.error("Attempted to save user data with None user_id")
            return
        
        # Extract data from legacy format and update using new functions
        account_updates = {
            "user_id": self.user_data.get("user_id", user_id),
            "internal_username": self.user_data.get("internal_username", ""),
            "account_status": "active" if self.user_data.get("active", True) else "inactive",
            "chat_id": self.user_data.get("chat_id", ""),
            "phone": self.user_data.get("phone", ""),
            "email": self.user_data.get("email", ""),
        }
        
        preferences_updates = self.user_data.get("preferences", {})
        
        context_updates = {
            "preferred_name": self.user_data.get("preferred_name", ""),
        }
        
        # Update all data using new functions
        update_user_account(user_id, account_updates)
        update_user_preferences(user_id, preferences_updates)
        update_user_context(user_id, context_updates)
        
        logger.info(f"User data saved for user_id {user_id}")

    @handle_errors("setting user ID")
    def set_user_id(self, user_id):
        """
        Sets the user_id in the user_data dictionary.
        
        Args:
            user_id (str): The user ID to be set.
        """
        if user_id:
            self.user_data['user_id'] = user_id
            logger.debug(f"UserContext: set_user_id called with {user_id}")
        else:
            logger.debug("UserContext: Clearing user_id (set to None during logout)")
            self.user_data['user_id'] = None

    @handle_errors("getting user ID", default_return=None)
    def get_user_id(self):
        """
        Retrieves the user_id from the user_data dictionary.
        
        Returns:
            str: The current user ID, or None if not set.
        """
        return self.user_data.get('user_id')

    @handle_errors("setting internal username")
    def set_internal_username(self, internal_username):
        """
        Sets the internal_username in the user_data dictionary.
        
        Args:
            internal_username (str): The internal username to be set.
        """
        if internal_username:
            self.user_data['internal_username'] = internal_username
            logger.debug(f"UserContext: set_internal_username called with {internal_username}")
        else:
            logger.debug("UserContext: Clearing internal_username (set to None during logout)")
            self.user_data['internal_username'] = None

    @handle_errors("getting internal username", default_return=None)
    def get_internal_username(self):
        """
        Retrieves the internal_username from the user_data dictionary.
        
        Returns:
            str: The current internal username, or None if not set.
        """
        return self.user_data.get('internal_username')

    @handle_errors("setting preferred name")
    def set_preferred_name(self, preferred_name):
        """
        Sets the preferred_name in the user_data dictionary.
        
        Args:
            preferred_name (str): The preferred name to be set.
        """
        self.user_data['preferred_name'] = preferred_name
        logger.debug(f"UserContext: set_preferred_name called with {preferred_name}")

    @handle_errors("getting preferred name", default_return=None)
    def get_preferred_name(self):
        """
        Retrieves the preferred_name from the user_data dictionary.
        
        Returns:
            str: The current preferred name, or None if not set.
        """
        return self.user_data.get('preferred_name')

    @handle_errors("setting preference")
    def set_preference(self, key, value):
        """
        Sets a user preference in the user_data dictionary.
        
        Args:
            key (str): The preference key to be set.
            value (any): The preference value to be set.
        """
        self.user_data.setdefault('preferences', {})[key] = value
        logger.debug(f"UserContext: set_preference called with {key} = {value}")

    @handle_errors("getting preference", default_return=None)
    def get_preference(self, key):
        """
        Retrieves a user preference from the user_data dictionary.
        
        Args:
            key (str): The preference key to retrieve.
        
        Returns:
            any: The current preference value, or None if not set.
        """
        return self.user_data.get('preferences', {}).get(key)

    @handle_errors("updating preference")
    def update_preference(self, key, value):
        """
        Updates a user preference and saves the data.
        
        Args:
            key (str): The preference key to be updated.
            value (any): The preference value to be set.
        """
        self.set_preference(key, value)
        user_id = self.get_user_id()
        if user_id:
            self.save_user_data(user_id)
        else:
            logger.warning("Cannot save preference update: no user_id set")

    @handle_errors("getting active schedules")
    def _get_active_schedules(self, schedules):
        """
        Retrieves active schedules from the user_data dictionary.
        
        Args:
            schedules (dict): The current schedules dictionary.
        
        Returns:
            dict: The updated schedules dictionary.
        """
        active_schedules = {}
        for schedule_id, schedule in schedules.items():
            if schedule.get('active', False):
                active_schedules[schedule_id] = schedule
        return active_schedules

    @handle_errors("getting user context")
    def get_user_context(self):
        """
        Retrieves user context data.
        
        Returns:
            dict: The user context data.
        """
        user_id = self.get_user_id()
        if not user_id:
            logger.warning("Cannot get user context: no user_id set")
            return {}
        
        # Use the new user management functions
        user_data_result = get_user_data(user_id, 'account')
        account_data = user_data_result.get('account') or {}
        prefs_result = get_user_data(user_id, 'preferences')
        preferences_data = prefs_result.get('preferences') or {}
        context_result = get_user_data(user_id, 'context')
        context_data = context_result.get('context') or {}
        
        return {
            'preferred_name': self.get_preferred_name() or context_data.get('preferred_name', ''),
            'active_categories': self.get_preference('categories') or self.user_data.get('categories', []),
            'messaging_service': self.get_preference('channel', {}).get('type', ''),
            'active_schedules': self._get_active_schedules(self.user_data.get('schedules', {})),  # Schedules handled separately
            'discord_user_id': account_data.get("discord_user_id", "")
        }
