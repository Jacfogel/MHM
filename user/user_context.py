# user_context.py

import json
import os
import threading
from core.logger import get_logger
from core.user_management import load_user_info_data, save_user_info_data
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
        Loads user data using the updated utils functions that support new file structure.
        
        Args:
            user_id (str): The user ID whose data needs to be loaded.
        """
        if not user_id:
            logger.error("Attempted to load user data with None user_id")
            return
        # Use the updated utils function that handles both old and new structures
        user_data = load_user_info_data(user_id)
        if user_data:
            self.user_data = user_data
            logger.info(f"User data loaded for user_id {user_id}")
        else:
            logger.warning(f"No user data found for user_id {user_id}")
            self.user_data = {}

    @handle_errors("saving user data")
    def save_user_data(self, user_id):
        """
        Saves user data using the updated utils functions that support new file structure.
        WARNING: Only the flat preferences dict is saved to preferences.json. Always load, update, and save the full dict to avoid data loss.
        
        Args:
            user_id (str): The user ID whose data needs to be saved.
        """
        if not user_id:
            logger.error("Attempted to save user data with None user_id")
            return
        # Use the updated utils function that handles both old and new structures
        save_user_info_data(self.user_data, user_id)
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
        WARNING: Always update the full preferences dict and save the whole thing, not just a single key, to avoid overwriting other preferences.
        
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
