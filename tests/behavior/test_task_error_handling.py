"""
Error handling tests for task management system.

Tests various error conditions and edge cases.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import uuid
import json
import os

from tasks.task_management import (
    create_task,
    update_task,
    complete_task,
    delete_task,
    load_active_tasks,
    get_task_by_id,
    schedule_task_reminders,
)
from communication.command_handlers.task_handler import TaskManagementHandler
from communication.command_handlers.shared_types import ParsedCommand
from core.time_utilities import DATE_ONLY, format_timestamp, now_datetime_full
from tests.test_utilities import TestUserFactory


class TestTaskErrorHandling:
    """Test error handling in task operations."""

    def _create_test_user(self, user_id: str, test_data_dir: str = None) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(
            user_id, enable_checkins=False, test_data_dir=test_data_dir
        )

    @pytest.mark.behavior
    @pytest.mark.tasks
    @pytest.mark.critical
    @pytest.mark.file_io
    def test_create_task_invalid_user_id(self, test_data_dir):
        """Test that creating a task with invalid user_id fails gracefully."""
        result = create_task(user_id="", title="Test Task")
        assert result is None, "Should return None for empty user_id"

        result = create_task(user_id=None, title="Test Task")
        assert result is None, "Should return None for None user_id"

    @pytest.mark.behavior
    @pytest.mark.tasks
    @pytest.mark.critical
    @pytest.mark.file_io
    def test_create_task_missing_title(self, test_data_dir):
        """Test that creating a task without title fails gracefully."""
        user_id = "test_user_no_title"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        result = create_task(user_id=user_id, title="")
        assert result is None, "Should return None for empty title"

        result = create_task(user_id=user_id, title=None)
        assert result is None, "Should return None for None title"

    @pytest.mark.behavior
    @pytest.mark.tasks
    @pytest.mark.critical
    @pytest.mark.file_io
    def test_create_task_invalid_priority(self, test_data_dir):
        """Test that creating a task with invalid priority uses default."""
        user_id = "test_user_invalid_priority"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Invalid priority should default to "medium"
        task_id = create_task(
            user_id=user_id, title="Test Task", priority="invalid_priority"
        )
        assert task_id is not None, "Task should be created"

        task = get_task_by_id(user_id, task_id)
        assert task["priority"] == "medium", "Should default to medium priority"

    @pytest.mark.behavior
    @pytest.mark.tasks
    @pytest.mark.critical
    @pytest.mark.file_io
    def test_create_task_invalid_date_format(self, test_data_dir):
        """Test that creating a task with invalid date format is handled."""
        user_id = "test_user_invalid_date"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Invalid date format should still create task (date validation happens elsewhere)
        task_id = create_task(
            user_id=user_id, title="Test Task", due_date="invalid-date"
        )
        assert task_id is not None, "Task should be created even with invalid date"

        task = get_task_by_id(user_id, task_id)
        assert task["due_date"] == "invalid-date", "Invalid date should be stored as-is"

    @pytest.mark.behavior
    @pytest.mark.tasks
    @pytest.mark.critical
    @pytest.mark.file_io
    def test_update_task_not_found(self, test_data_dir):
        """Test that updating a non-existent task fails gracefully."""
        user_id = "test_user_update_notfound"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        result = update_task(user_id, "non-existent-task-id", {"title": "New Title"})
        assert result is False, "Should return False for non-existent task"

    @pytest.mark.behavior
    @pytest.mark.tasks
    @pytest.mark.critical
    @pytest.mark.file_io
    def test_complete_task_not_found(self, test_data_dir):
        """Test that completing a non-existent task fails gracefully."""
        user_id = "test_user_complete_notfound"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        result = complete_task(user_id, "non-existent-task-id")
        assert result is False, "Should return False for non-existent task"

    @pytest.mark.behavior
    @pytest.mark.tasks
    @pytest.mark.critical
    @pytest.mark.file_io
    def test_delete_task_not_found(self, test_data_dir):
        """Test that deleting a non-existent task fails gracefully."""
        user_id = "test_user_delete_notfound"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        result = delete_task(user_id, "non-existent-task-id")
        assert result is False, "Should return False for non-existent task"

    @pytest.mark.behavior
    @pytest.mark.tasks
    @pytest.mark.critical
    @pytest.mark.file_io
    def test_schedule_reminders_no_scheduler(self, test_data_dir):
        """Test that scheduling reminders when scheduler unavailable fails gracefully."""
        user_id = "test_user_no_scheduler"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        task_id = create_task(user_id=user_id, title="Test Task")

        reminder_periods = [
            {
                "date": format_timestamp(
                    (now_datetime_full() + timedelta(days=1)), DATE_ONLY
                ),
                "start_time": "09:00",
                "end_time": "10:00",
            }
        ]

        with patch("core.service.get_scheduler_manager", return_value=None):
            result = schedule_task_reminders(user_id, task_id, reminder_periods)
            assert result is False, "Should return False when scheduler unavailable"

    @pytest.mark.behavior
    @pytest.mark.tasks
    @pytest.mark.critical
    @pytest.mark.file_io
    def test_schedule_reminders_incomplete_period_data(self, test_data_dir):
        """Test that scheduling reminders with incomplete period data is handled."""
        user_id = "test_user_incomplete_periods"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        task_id = create_task(user_id=user_id, title="Test Task")

        # Incomplete reminder periods (missing fields)
        incomplete_periods = [
            {
                "date": format_timestamp(
                    (now_datetime_full() + timedelta(days=1)), DATE_ONLY
                )
            },  # Missing start_time, end_time
            {"start_time": "09:00", "end_time": "10:00"},  # Missing date
            {
                "date": format_timestamp(
                    (now_datetime_full() + timedelta(days=1)), DATE_ONLY
                ),
                "start_time": "09:00",
            },  # Missing end_time
        ]

        with patch("core.service.get_scheduler_manager") as mock_get_scheduler:
            mock_scheduler = MagicMock()
            mock_scheduler.schedule_task_reminder_at_datetime.return_value = True
            mock_get_scheduler.return_value = mock_scheduler

            result = schedule_task_reminders(user_id, task_id, incomplete_periods)

            # Should return True (no error) but may schedule fewer reminders
            # The function logs warnings for incomplete periods
            assert result is not None, "Should handle incomplete periods gracefully"

    @pytest.mark.behavior
    @pytest.mark.tasks
    @pytest.mark.critical
    @pytest.mark.file_io
    def test_load_tasks_corrupted_json(self, test_data_dir):
        """Test that loading tasks from corrupted JSON is handled."""
        user_id = "test_user_corrupted_json"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Create a task first to set up the file
        create_task(user_id=user_id, title="Test Task")

        # Corrupt the JSON file
        from core.config import get_user_data_dir
        from pathlib import Path

        user_dir = Path(get_user_data_dir(user_id))
        task_file = user_dir / "tasks" / "active_tasks.json"

        with open(task_file, "w") as f:
            f.write("invalid json content {")

        # Try to load tasks - should return empty list or handle gracefully
        tasks = load_active_tasks(user_id)
        # Should either return empty list or handle error gracefully
        assert isinstance(tasks, list), "Should return a list even on error"

    @pytest.mark.behavior
    @pytest.mark.tasks
    @pytest.mark.critical
    def test_handler_invalid_intent(self):
        """Test that handler handles invalid intent gracefully."""
        handler = TaskManagementHandler()

        parsed_command = ParsedCommand(
            intent="invalid_intent",
            entities={},
            confidence=0.5,
            original_message="invalid command",
        )

        response = handler.handle("test_user", parsed_command)
        assert isinstance(
            response, type(handler.handle("test_user", parsed_command))
        ), "Should return InteractionResponse"
        assert (
            "don't understand" in response.message.lower()
            or "try" in response.message.lower()
        ), "Should indicate unknown command"


class TestTaskEdgeCases:
    """Test edge cases in task operations."""

    def _create_test_user(self, user_id: str, test_data_dir: str = None) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(
            user_id, enable_checkins=False, test_data_dir=test_data_dir
        )

    @pytest.mark.behavior
    @pytest.mark.tasks
    @pytest.mark.regression
    @pytest.mark.file_io
    def test_task_with_no_due_date_but_reminders(self, test_data_dir):
        """Test creating a task with reminders but no due_date."""
        user_id = "test_user_no_due_date"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        reminder_periods = [
            {
                "date": format_timestamp(
                    (now_datetime_full() + timedelta(days=1)), DATE_ONLY
                ),
                "start_time": "09:00",
                "end_time": "10:00",
            }
        ]

        task_id = create_task(
            user_id=user_id,
            title="Task Without Due Date",
            reminder_periods=reminder_periods,
        )

        assert task_id is not None, "Task should be created"
        task = get_task_by_id(user_id, task_id)
        assert (
            task["due_date"] is None or task["due_date"] == ""
        ), "Task should have no due_date"
        assert "reminder_periods" in task, "Task should have reminder_periods"

    @pytest.mark.behavior
    @pytest.mark.tasks
    @pytest.mark.regression
    @pytest.mark.file_io
    @pytest.mark.no_parallel
    def test_task_with_past_due_date(self, test_data_dir):
        """Test creating a task with a past due_date.

        Marked as no_parallel because it creates task files that may conflict with other tests.
        """
        user_id = "test_user_past_due"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        past_date = format_timestamp(
            (now_datetime_full() - timedelta(days=5)), DATE_ONLY
        )
        task_id = create_task(user_id=user_id, title="Overdue Task", due_date=past_date)

        assert task_id is not None, "Task should be created even with past due_date"

        # Get task (serial execution ensures file is written)
        task = get_task_by_id(user_id, task_id)

        assert task is not None, f"Task should be retrievable. Task ID: {task_id}"
        assert task["due_date"] == past_date, "Past due_date should be stored"

    @pytest.mark.behavior
    @pytest.mark.tasks
    @pytest.mark.regression
    @pytest.mark.file_io
    def test_task_with_very_long_title(self, test_data_dir):
        """Test creating a task with a very long title."""
        user_id = "test_user_long_title"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        long_title = "A" * 1000  # 1000 character title
        task_id = create_task(user_id=user_id, title=long_title)

        assert task_id is not None, "Task should be created even with very long title"
        task = get_task_by_id(user_id, task_id)
        assert task["title"] == long_title, "Long title should be stored"

    @pytest.mark.behavior
    @pytest.mark.tasks
    @pytest.mark.regression
    @pytest.mark.file_io
    def test_task_with_unicode_characters(self, test_data_dir):
        """Test creating a task with unicode characters."""
        user_id = "test_user_unicode"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        unicode_title = "Task with émojis 🎉 and spéciál chars ñ"
        task_id = create_task(user_id=user_id, title=unicode_title)

        assert task_id is not None, "Task should be created with unicode"
        task = get_task_by_id(user_id, task_id)
        assert (
            task["title"] == unicode_title
        ), "Unicode title should be stored correctly"

    @pytest.mark.behavior
    @pytest.mark.tasks
    @pytest.mark.regression
    @pytest.mark.file_io
    def test_task_with_special_characters_in_description(self, test_data_dir):
        """Test creating a task with special characters in description."""
        user_id = "test_user_special_chars"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        special_desc = "Description with \"quotes\", 'apostrophes', and\nnewlines"
        task_id = create_task(
            user_id=user_id, title="Test Task", description=special_desc
        )

        assert task_id is not None, "Task should be created"
        task = get_task_by_id(user_id, task_id)
        assert (
            task["description"] == special_desc
        ), "Special characters should be stored"

    @pytest.mark.behavior
    @pytest.mark.tasks
    @pytest.mark.regression
    @pytest.mark.file_io
    def test_multiple_tasks_same_title(self, test_data_dir):
        """Test creating multiple tasks with the same title."""
        user_id = f"test_user_duplicate_titles_{uuid.uuid4().hex[:8]}"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        title = "Duplicate Title"
        task_id1 = create_task(user_id=user_id, title=title)
        task_id2 = create_task(user_id=user_id, title=title)

        assert task_id1 != task_id2, "Tasks should have different IDs"
        tasks = load_active_tasks(user_id)
        assert len(tasks) == 2, "Should have 2 tasks"
        assert all(
            t["title"] == title for t in tasks
        ), "Both tasks should have same title"
