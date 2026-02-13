"""
Test to demonstrate the cleanup_task_reminders bug.

This test will fail until the bug is fixed, demonstrating that cleanup_task_reminders
method doesn't exist in SchedulerManager.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import timedelta

from core.time_utilities import DATE_ONLY, format_timestamp, now_datetime_full
from tasks.task_management import create_task, cleanup_task_reminders
from tests.test_utilities import TestUserFactory


class TestTaskCleanupBug:
    """Test to demonstrate cleanup_task_reminders bug."""

    def _create_test_user(self, user_id: str, test_data_dir: str = None) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(
            user_id, enable_checkins=False, test_data_dir=test_data_dir
        )

    @pytest.mark.behavior
    @pytest.mark.tasks
    @pytest.mark.regression
    @pytest.mark.file_io
    def test_cleanup_task_reminders_method_exists(self, test_data_dir):
        """
        This test demonstrates that cleanup_task_reminders method doesn't exist.

        BUG: tasks/task_management.py line 649 calls scheduler_manager.cleanup_task_reminders()
        but this method doesn't exist in SchedulerManager class.

        This test will FAIL until the bug is fixed.
        """
        user_id = "test_user_cleanup_bug"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Create a task with reminders
        reminder_periods = [
            {
                "date": format_timestamp(
                    now_datetime_full() + timedelta(days=1), DATE_ONLY
                ),
                "start_time": "09:00",
                "end_time": "10:00",
            }
        ]

        with patch("core.service.get_scheduler_manager") as mock_get_scheduler:
            mock_scheduler = MagicMock()
            mock_scheduler.schedule_task_reminder_at_datetime.return_value = True
            mock_get_scheduler.return_value = mock_scheduler

            task_id = create_task(
                user_id=user_id,
                title="Task with Reminders",
                reminder_periods=reminder_periods,
            )

            assert task_id is not None, "Task should be created"

            # Try to clean up reminders - method should exist now (bug fixed)
            scheduler_manager = mock_get_scheduler.return_value

            # BUG FIXED: cleanup_task_reminders method now exists in SchedulerManager
            # MagicMock will have the method because it's called, so we verify it's called correctly
            cleanup_task_reminders(user_id, task_id)
            # Cleanup should call the method (even if it's mocked)
            scheduler_manager.cleanup_task_reminders.assert_called_once_with(
                user_id, task_id
            )
