"""
Real bug verification tests - tests actual system behavior to find bugs.

Following testing guidelines:
- Verify actual system changes (files, state, scheduler jobs)
- Mock Windows task creation (set_wake_timer) per guidelines
- Test real scheduler logic and job management
- Verify side effects and document failures
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import schedule

from core.time_utilities import DATE_ONLY, format_timestamp
from tasks.task_management import (
    create_task,
    complete_task,
    cleanup_task_reminders,
    schedule_task_reminders,
)
from tests.test_utilities import TestUserFactory


class TestTaskCleanupBugVerification:
    """Test to verify the actual cleanup bug exists in real system."""

    def _create_test_user(self, user_id: str, test_data_dir: str = None) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(
            user_id, enable_checkins=False, test_data_dir=test_data_dir
        )

    @pytest.mark.integration
    @pytest.mark.tasks
    @pytest.mark.critical
    @pytest.mark.file_io
    def test_cleanup_task_reminders_fails_in_real_system(self, test_data_dir):
        """
        Test: cleanup_task_reminders() fails in real system because method doesn't exist.

        This test verifies the actual bug by calling the real cleanup function
        and documenting what happens.
        """
        # Arrange: Create user and task
        user_id = "test_user_cleanup_bug_real"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        task_id = create_task(user_id=user_id, title="Task with Reminders")

        # Act: Try to clean up reminders using REAL system (mock Windows tasks per guidelines)
        with patch(
            "core.scheduler.SchedulerManager.set_wake_timer"
        ):  # Prevent Windows task creation
            # Call the real cleanup function - this will fail because method doesn't exist
            result = cleanup_task_reminders(user_id, task_id)

        # Assert: Verify what actually happens
        # The function catches the AttributeError and returns False
        # This documents the bug: cleanup fails silently
        assert result is False, (
            "BUG CONFIRMED: cleanup_task_reminders returns False because "
            "SchedulerManager.cleanup_task_reminders() method doesn't exist. "
            "Reminders are never cleaned up."
        )

    @pytest.mark.integration
    @pytest.mark.tasks
    @pytest.mark.critical
    @pytest.mark.file_io
    def test_complete_task_cleanup_fails_silently(self, test_data_dir):
        """
        Test: Completing a task attempts cleanup but fails silently.

        Verifies actual system behavior: task completes but cleanup fails.
        """
        # Arrange: Create user and task
        user_id = "test_user_complete_cleanup_fail"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        task_id = create_task(user_id=user_id, title="Task to Complete")

        # Act: Complete task (mock Windows tasks per guidelines)
        with patch(
            "core.scheduler.SchedulerManager.set_wake_timer"
        ):  # Prevent Windows task creation
            result = complete_task(user_id, task_id)

        # Assert: Task completes successfully (bug doesn't prevent completion)
        assert result is True, "Task should complete even if cleanup fails"

        # But cleanup failed silently - this is the bug
        # In a real scenario, if this task had reminders, they would still be scheduled
        # We can't easily verify this without checking scheduler jobs, but we know cleanup was called
        # and it failed because the method doesn't exist

    @pytest.mark.integration
    @pytest.mark.tasks
    @pytest.mark.critical
    @pytest.mark.file_io
    def test_schedule_reminders_creates_jobs_but_cleanup_cant_remove_them(
        self, test_data_dir
    ):
        """
        Test: Scheduling reminders creates scheduler jobs, but cleanup can't remove them.

        This test verifies the full bug: reminders are scheduled but can't be cleaned up.
        """
        # Arrange: Create user and task
        user_id = "test_user_reminder_accumulation"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        task_id = create_task(user_id=user_id, title="Task with Reminders")

        reminder_periods = [
            {
                "date": format_timestamp(datetime.now() + timedelta(days=1), DATE_ONLY),
                "start_time": "09:00",
                "end_time": "10:00",
            }
        ]

        # Count scheduler jobs before
        jobs_before = len(schedule.jobs)

        # Act: Schedule reminders (mock Windows tasks per guidelines)
        with patch(
            "core.scheduler.SchedulerManager.set_wake_timer"
        ):  # Prevent Windows task creation
            schedule_result = schedule_task_reminders(
                user_id, task_id, reminder_periods
            )

            # Count jobs after scheduling
            jobs_after_schedule = len(schedule.jobs)

            # Try to clean up (this will fail)
            cleanup_result = cleanup_task_reminders(user_id, task_id)

            # Count jobs after cleanup attempt
            jobs_after_cleanup = len(schedule.jobs)

        # Assert: Verify what actually happens
        # Scheduling should succeed (if scheduler available)
        # But cleanup should fail
        assert cleanup_result is False, (
            "BUG CONFIRMED: cleanup_task_reminders returns False. "
            "Reminders cannot be removed because cleanup method doesn't exist."
        )

        # If reminders were scheduled, they should still be there after cleanup attempt
        # (because cleanup failed)
        if schedule_result:
            # Reminders were scheduled
            # After cleanup attempt, they should still exist (because cleanup failed)
            # Note: This assumes scheduler is available - if not, no jobs are created
            # But the key point is: cleanup fails, so if jobs exist, they remain
            assert jobs_after_cleanup >= jobs_after_schedule, (
                "BUG: If reminders were scheduled, they should still exist after cleanup "
                "(because cleanup failed). This demonstrates reminder accumulation."
            )
