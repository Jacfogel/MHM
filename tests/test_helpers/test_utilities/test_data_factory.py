"""
Factory for creating test data for various scenarios.
"""

import json
import logging
import os
import uuid
from datetime import timedelta
from typing import Any

from core.time_utilities import (
    DATE_ONLY,
    format_timestamp,
    now_datetime_full,
    now_timestamp_full,
)

logger = logging.getLogger(__name__)


class TestDataFactory:
    """Factory for creating test data for various scenarios"""

    @staticmethod
    def create_corrupted_user_data(
        user_id: str, corruption_type: str = "invalid_json"
    ) -> bool:
        """
        Create a user with corrupted data for testing error handling

        Args:
            user_id: Unique identifier for the test user
            corruption_type: Type of corruption ("invalid_json", "missing_file", "empty_file")

        Returns:
            bool: True if corrupted user was created successfully, False otherwise
        """
        try:
            from core.config import get_user_data_dir

            # Create user directory
            user_dir = get_user_data_dir(user_id)
            os.makedirs(user_dir, exist_ok=True)

            if corruption_type == "invalid_json":
                # Create file with invalid JSON
                with open(os.path.join(user_dir, "account.json"), "w") as f:
                    f.write("invalid json content")
                with open(os.path.join(user_dir, "preferences.json"), "w") as f:
                    f.write("{ invalid json }")
                with open(os.path.join(user_dir, "user_context.json"), "w") as f:
                    f.write("not json at all")

            elif corruption_type == "missing_file":
                # Create only some files, leave others missing
                with open(os.path.join(user_dir, "account.json"), "w") as f:
                    json.dump({"user_id": user_id}, f)
                # Don't create preferences.json or user_context.json

            elif corruption_type == "empty_file":
                # Create empty files
                with open(os.path.join(user_dir, "account.json"), "w") as f:
                    f.write("")
                with open(os.path.join(user_dir, "preferences.json"), "w") as f:
                    f.write("")
                with open(os.path.join(user_dir, "user_context.json"), "w") as f:
                    f.write("")

            return True

        except Exception as e:
            logger.error(f"Error creating corrupted user data for {user_id}: {e}")
            return False

    @staticmethod
    def create_test_schedule_data(
        categories: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Create test schedule data for testing schedule management

        Args:
            categories: List of categories to create schedules for

        Returns:
            Dict containing schedule data
        """
        if categories is None:
            categories = ["motivational", "health"]

        schedule_data = {}
        for category in categories:
            schedule_data[category] = {
                "periods": {
                    "Default": {
                        "active": True,
                        "days": ["ALL"],
                        "start_time": "18:00",
                        "end_time": "21:30",
                    }
                }
            }

        return schedule_data

    @staticmethod
    def create_test_task_data(task_count: int = 3) -> list[dict[str, Any]]:
        """
        Create test task data for testing task management

        Args:
            task_count: Number of tasks to create

        Returns:
            List of task dictionaries
        """
        tasks = []
        for i in range(task_count):
            task = {
                "task_id": str(uuid.uuid4()),
                "title": f"Test Task {i + 1}",
                "description": f"Description for test task {i + 1}",
                "priority": "medium",
                "status": "active",
                "due_date": format_timestamp(
                    now_datetime_full() + timedelta(days=i + 1), DATE_ONLY
                ),
                "created_at": now_timestamp_full(),
                "updated_at": now_timestamp_full(),
            }
            tasks.append(task)

        return tasks

    @staticmethod
    def create_test_message_data(
        category: str = "motivational", message_count: int = 5
    ) -> list[dict[str, Any]]:
        """
        Create test message data for testing message management

        Args:
            category: Message category
            message_count: Number of messages to create

        Returns:
            List of message dictionaries
        """

        messages = []
        for i in range(message_count):
            message = {
                "message_id": str(uuid.uuid4()),
                "content": f"Test message {i + 1} for {category}",
                "category": category,
                "created_at": now_timestamp_full(),
                "sent": False,
                "scheduled_for": now_timestamp_full(),
            }
            messages.append(message)

        return messages
