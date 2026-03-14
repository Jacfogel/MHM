"""
Factory for creating specific test user data structures.
"""

from typing import Any


class TestUserDataFactory:
    """Factory for creating specific test user data structures"""

    @staticmethod
    def create_account_data(user_id: str, **overrides) -> dict[str, Any]:
        """
        Create standard account data structure with optional overrides

        Args:
            user_id: User identifier
            **overrides: Optional field overrides

        Returns:
            Dict containing account data
        """
        base_data = {
            "user_id": user_id,
            "internal_username": user_id,
            "account_status": "active",
            "name": f"Test User {user_id}",
            "pronouns": "they/them",
            "timezone": "UTC",
            "created_at": "2025-01-01 00:00:00",
            "updated_at": "2025-01-01 00:00:00",
        }
        base_data.update(overrides)
        return base_data

    @staticmethod
    def create_preferences_data(user_id: str, **overrides) -> dict[str, Any]:
        """
        Create standard preferences data structure with optional overrides

        Args:
            user_id: User identifier
            **overrides: Optional field overrides

        Returns:
            Dict containing preferences data
        """
        base_data = {
            "categories": ["motivational", "health"],
            "channel": {"type": "discord"},
            "notification_settings": {
                "morning_reminders": True,
                "task_reminders": True,
                "checkin_reminders": True,
            },
        }
        base_data.update(overrides)
        return base_data

    @staticmethod
    def create_schedules_data(**overrides) -> dict[str, Any]:
        """
        Create standard schedules data structure with optional overrides

        Args:
            **overrides: Optional field overrides

        Returns:
            Dict containing schedules data
        """
        base_data = {
            "motivational": {
                "periods": {
                    "morning": {
                        "active": True,
                        "days": [
                            "monday",
                            "tuesday",
                            "wednesday",
                            "thursday",
                            "friday",
                        ],
                        "start_time": "09:00",
                        "end_time": "12:00",
                    }
                }
            }
        }
        base_data.update(overrides)
        return base_data

    @staticmethod
    def create_context_data(**overrides) -> dict[str, Any]:
        """
        Create standard context data structure with optional overrides

        Args:
            **overrides: Optional field overrides

        Returns:
            Dict containing context data
        """
        base_data = {
            "preferred_name": "Test User",
            "timezone": "UTC",
            "language": "en",
            "created_date": "2025-01-01",
        }
        base_data.update(overrides)
        return base_data
