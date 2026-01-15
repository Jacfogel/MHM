# user_context.py

import threading
from core.logger import get_component_logger
from core.user_data_handlers import get_user_data
from core.error_handling import handle_errors
from core.schedule_utilities import get_active_schedules

logger = get_component_logger("user_activity")
context_logger = get_component_logger("user_activity")


class UserContext:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Create a new instance."""
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

        # Use the new user management functions directly
        user_data_result = get_user_data(user_id, "account", normalize_on_read=True)
        account_data = user_data_result.get("account") or {}
        prefs_result = get_user_data(user_id, "preferences", normalize_on_read=True)
        preferences_data = prefs_result.get("preferences") or {}
        context_result = get_user_data(user_id, "context")
        context_data = context_result.get("context") or {}

        # Store data in the new format directly - no legacy conversion needed
        self.user_data = {
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
            "schedules": {},  # Schedules are handled separately
        }

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

        # Extract data and update using new functions directly - no legacy extraction needed
        account_updates = {
            "user_id": self.user_data.get("user_id", user_id),
            "internal_username": self.user_data.get("internal_username", ""),
            "account_status": (
                "active" if self.user_data.get("active", True) else "inactive"
            ),
            "chat_id": self.user_data.get("chat_id", ""),
            "phone": self.user_data.get("phone", ""),
            "email": self.user_data.get("email", ""),
        }

        preferences_updates = self.user_data.get("preferences", {})

        context_updates = {
            "preferred_name": self.user_data.get("preferred_name", ""),
        }

        # Update all data using new functions
        from core.user_data_handlers import save_user_data

        # Save account data
        save_user_data(user_id, {"account": account_updates})

        # Save preferences data
        save_user_data(user_id, {"preferences": preferences_updates})

        # Save context data
        save_user_data(user_id, {"context": context_updates})

        logger.info(f"User data saved for user_id {user_id}")

    @handle_errors("setting user ID")
    def set_user_id(self, user_id):
        """
        Sets the user_id in the user_data dictionary.

        Args:
            user_id (str): The user ID to be set.
        """
        if user_id:
            self.user_data["user_id"] = user_id
            logger.debug(f"UserContext: set_user_id called with {user_id}")
        else:
            logger.debug("UserContext: Clearing user_id (set to None during logout)")
            self.user_data["user_id"] = None

    @handle_errors("getting user ID", default_return=None)
    def get_user_id(self):
        """
        Retrieves the user_id from the user_data dictionary.

        Returns:
            str: The current user ID, or None if not set.
        """
        return self.user_data.get("user_id")

    @handle_errors("setting internal username")
    def set_internal_username(self, internal_username):
        """
        Sets the internal_username in the user_data dictionary.

        Args:
            internal_username (str): The internal username to be set.
        """
        if internal_username:
            self.user_data["internal_username"] = internal_username
            logger.debug(
                f"UserContext: set_internal_username called with {internal_username}"
            )
        else:
            logger.debug(
                "UserContext: Clearing internal_username (set to None during logout)"
            )
            self.user_data["internal_username"] = None

    @handle_errors("getting internal username", default_return=None)
    def get_internal_username(self):
        """
        Retrieves the internal_username from the user_data dictionary.

        Returns:
            str: The current internal username, or None if not set.
        """
        return self.user_data.get("internal_username")

    @handle_errors("setting preferred name")
    def set_preferred_name(self, preferred_name):
        """
        Sets the preferred_name in the user_data dictionary.

        Args:
            preferred_name (str): The preferred name to be set.
        """
        self.user_data["preferred_name"] = preferred_name
        logger.debug(f"UserContext: set_preferred_name called with {preferred_name}")

    @handle_errors("getting preferred name", default_return=None)
    def get_preferred_name(self):
        """
        Retrieves the preferred_name from the user_data dictionary.

        Returns:
            str: The current preferred name, or None if not set.
        """
        return self.user_data.get("preferred_name")

    @handle_errors("getting instance context")
    def get_instance_context(self):
        """
        Get basic user context from the current UserContext instance.

        Returns:
            dict: Dictionary containing basic user context information
        """
        user_id = self.get_user_id()
        if not user_id:
            return {}

        # Get user data
        user_data_result = get_user_data(user_id, "account")
        account_data = user_data_result.get("account") or {}

        # Get preferences
        prefs_result = get_user_data(user_id, "preferences")
        preferences_data = prefs_result.get("preferences") or {}

        # Get context
        context_result = get_user_data(user_id, "context")
        context_data = context_result.get("context") or {}

        # Get schedules for active schedules check
        schedules_result = get_user_data(user_id, "schedules", normalize_on_read=True)
        schedules_data = (
            schedules_result.get("schedules", {})
            if isinstance(schedules_result, dict) and "schedules" in schedules_result
            else (schedules_result if isinstance(schedules_result, dict) else {})
        )

        # Build basic context
        context = {
            "user_id": user_id,
            "preferred_name": context_data.get("preferred_name", ""),
            "account_status": account_data.get("account_status", "unknown"),
            "preferences": preferences_data,
            "active_schedules": get_active_schedules(schedules_data),
        }

        return context
