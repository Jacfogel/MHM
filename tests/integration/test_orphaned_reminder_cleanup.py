"""
Orphaned Reminder Cleanup Integration Tests

Tests for the periodic cleanup job that removes reminders for non-existent or completed tasks.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import schedule

from core.scheduler import SchedulerManager
from tasks.task_management import (
    create_task,
    complete_task,
    delete_task,
    get_task_by_id,
)
from tests.test_utilities import TestUserFactory
from core.time_utilities import DATE_ONLY


class TestOrphanedReminderCleanup:
    """Test orphaned reminder cleanup functionality."""

    @pytest.mark.integration
    @pytest.mark.scheduler
    @pytest.mark.tasks
    @patch("core.service.get_scheduler_manager")
    @patch("core.scheduler.SchedulerManager.set_wake_timer")
    def test_cleanup_removes_reminders_for_deleted_tasks(
        self, mock_wake_timer, mock_get_scheduler, test_data_dir
    ):
        """Test that cleanup removes reminders for tasks that have been deleted."""
        # Arrange
        user_id = "test_cleanup_deleted"
        TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )

        # Create a task with reminders
        due_date = (datetime.now() + timedelta(days=1)).strftime(DATE_ONLY)
        task_id = create_task(
            user_id=user_id,
            title="Test task for cleanup",
            due_date=due_date,
            reminder_periods=[
                {"date": due_date, "start_time": "09:00", "end_time": "10:00"}
            ],
        )

        # Create a real scheduler instance (needed for cleanup to work)
        from communication.core.channel_orchestrator import CommunicationManager

        communication_manager = CommunicationManager()
        real_scheduler = SchedulerManager(communication_manager)
        real_scheduler.handle_task_reminder = (
            MagicMock()
        )  # Mock only the reminder handler
        mock_get_scheduler.return_value = real_scheduler

        # Get scheduler and manually schedule a reminder job (simulating what happens)
        from core.service import get_scheduler_manager

        scheduler = get_scheduler_manager()
        assert scheduler is not None, "Scheduler should be available"

        # Manually add a reminder job to simulate what would be scheduled
        schedule.every().day.at("09:00").do(
            scheduler.handle_task_reminder, user_id=user_id, task_id=task_id
        )

        # Verify job exists
        initial_job_count = len(schedule.jobs)
        assert initial_job_count > 0, "Should have reminder job scheduled"

        # Delete the task
        delete_task(user_id, task_id)

        # Verify task is gone
        assert get_task_by_id(user_id, task_id) is None, "Task should be deleted"

        # Act - Run cleanup (now uses real cleanup method)
        scheduler.cleanup_orphaned_task_reminders()

        # Assert - Verify reminder job was removed
        final_job_count = len(schedule.jobs)
        # Job count should be reduced (at least by 1, possibly more if other jobs exist)
        # We check that the specific reminder job is gone by checking all jobs
        reminder_jobs = [
            job
            for job in schedule.jobs
            if hasattr(job.job_func, "func")
            and job.job_func.func == scheduler.handle_task_reminder
        ]

        # Should not find a job for the deleted task
        found_deleted_task_job = False
        for job in reminder_jobs:
            if hasattr(job.job_func, "keywords"):
                kwargs = job.job_func.keywords
                if (
                    kwargs.get("user_id") == user_id
                    and kwargs.get("task_id") == task_id
                ):
                    found_deleted_task_job = True
                    break

        assert (
            not found_deleted_task_job
        ), "Reminder job for deleted task should be removed"

    @pytest.mark.integration
    @pytest.mark.scheduler
    @pytest.mark.tasks
    @patch("core.service.get_scheduler_manager")
    @patch("core.scheduler.SchedulerManager.set_wake_timer")
    def test_cleanup_removes_reminders_for_completed_tasks(
        self, mock_wake_timer, mock_get_scheduler, test_data_dir
    ):
        """Test that cleanup removes reminders for tasks that have been completed."""
        # Arrange
        user_id = "test_cleanup_completed"
        TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )

        # Create a task with reminders
        due_date = (datetime.now() + timedelta(days=1)).strftime(DATE_ONLY)
        task_id = create_task(
            user_id=user_id,
            title="Test task for cleanup",
            due_date=due_date,
            reminder_periods=[
                {"date": due_date, "start_time": "09:00", "end_time": "10:00"}
            ],
        )

        # Create a real scheduler instance (needed for cleanup to work)
        from communication.core.channel_orchestrator import CommunicationManager

        communication_manager = CommunicationManager()
        real_scheduler = SchedulerManager(communication_manager)
        real_scheduler.handle_task_reminder = (
            MagicMock()
        )  # Mock only the reminder handler
        mock_get_scheduler.return_value = real_scheduler

        # Get scheduler and manually schedule a reminder job
        from core.service import get_scheduler_manager

        scheduler = get_scheduler_manager()
        assert scheduler is not None, "Scheduler should be available"

        schedule.every().day.at("09:00").do(
            scheduler.handle_task_reminder, user_id=user_id, task_id=task_id
        )

        # Complete the task
        complete_task(user_id, task_id)

        # Verify task is completed
        task = get_task_by_id(user_id, task_id)
        # Note: completed tasks are moved to completed_tasks.json, so get_task_by_id might return None
        # We'll check that the task is no longer in active tasks
        from tasks.task_management import load_active_tasks

        active_tasks = load_active_tasks(user_id)
        active_task_ids = [t.get("task_id") for t in active_tasks]
        assert task_id not in active_task_ids, "Task should not be in active tasks"

        # Act - Run cleanup (now uses real cleanup method)
        scheduler.cleanup_orphaned_task_reminders()

        # Assert - Verify reminder job was removed
        reminder_jobs = [
            job
            for job in schedule.jobs
            if hasattr(job.job_func, "func")
            and job.job_func.func == scheduler.handle_task_reminder
        ]

        # Should not find a job for the completed task
        found_completed_task_job = False
        for job in reminder_jobs:
            if hasattr(job.job_func, "keywords"):
                kwargs = job.job_func.keywords
                if (
                    kwargs.get("user_id") == user_id
                    and kwargs.get("task_id") == task_id
                ):
                    found_completed_task_job = True
                    break

        assert (
            not found_completed_task_job
        ), "Reminder job for completed task should be removed"

    @pytest.mark.integration
    @pytest.mark.scheduler
    @pytest.mark.tasks
    @patch("core.service.get_scheduler_manager")
    @patch("core.scheduler.SchedulerManager.set_wake_timer")
    def test_cleanup_preserves_reminders_for_active_tasks(
        self, mock_wake_timer, mock_get_scheduler, test_data_dir
    ):
        """Test that cleanup does NOT remove reminders for active tasks."""
        # Arrange
        user_id = "test_cleanup_preserve"
        TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )

        # Create a task with reminders
        due_date = (datetime.now() + timedelta(days=1)).strftime(DATE_ONLY)
        task_id = create_task(
            user_id=user_id,
            title="Test active task",
            due_date=due_date,
            reminder_periods=[
                {"date": due_date, "start_time": "09:00", "end_time": "10:00"}
            ],
        )

        # Mock scheduler manager
        mock_scheduler = MagicMock()
        mock_scheduler.handle_task_reminder = MagicMock()
        mock_get_scheduler.return_value = mock_scheduler

        # Get scheduler and manually schedule a reminder job
        from core.service import get_scheduler_manager

        scheduler = get_scheduler_manager()
        assert scheduler is not None, "Scheduler should be available"

        schedule.every().day.at("09:00").do(
            scheduler.handle_task_reminder, user_id=user_id, task_id=task_id
        )

        # Verify task exists and is active
        task = get_task_by_id(user_id, task_id)
        assert task is not None, "Task should exist"
        assert not task.get("completed", False), "Task should not be completed"

        # Count reminder jobs before cleanup
        reminder_jobs_before = [
            job
            for job in schedule.jobs
            if hasattr(job.job_func, "func")
            and job.job_func.func == scheduler.handle_task_reminder
            and hasattr(job.job_func, "keywords")
            and job.job_func.keywords.get("user_id") == user_id
            and job.job_func.keywords.get("task_id") == task_id
        ]
        assert len(reminder_jobs_before) > 0, "Should have reminder job before cleanup"

        # Act - Run cleanup
        scheduler.cleanup_orphaned_task_reminders()

        # Assert - Verify reminder job still exists
        reminder_jobs_after = [
            job
            for job in schedule.jobs
            if hasattr(job.job_func, "func")
            and job.job_func.func == scheduler.handle_task_reminder
            and hasattr(job.job_func, "keywords")
            and job.job_func.keywords.get("user_id") == user_id
            and job.job_func.keywords.get("task_id") == task_id
        ]

        assert (
            len(reminder_jobs_after) > 0
        ), "Reminder job for active task should be preserved"
        assert len(reminder_jobs_after) == len(
            reminder_jobs_before
        ), "Should have same number of reminder jobs"

    @pytest.mark.integration
    @pytest.mark.scheduler
    @pytest.mark.tasks
    @pytest.mark.no_parallel
    @patch("core.service.get_scheduler_manager")
    @patch("core.scheduler.SchedulerManager.set_wake_timer")
    def test_cleanup_handles_multiple_users(
        self, mock_wake_timer, mock_get_scheduler, test_data_dir
    ):
        """Test that cleanup handles reminders for multiple users correctly."""
        # Arrange
        user1_id = "test_cleanup_user1"
        user2_id = "test_cleanup_user2"
        TestUserFactory.create_basic_user(
            user1_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        TestUserFactory.create_basic_user(
            user2_id, enable_tasks=True, test_data_dir=test_data_dir
        )

        # Create tasks for both users
        due_date = (datetime.now() + timedelta(days=1)).strftime(DATE_ONLY)

        task1_id = create_task(user_id=user1_id, title="User1 task", due_date=due_date)
        task2_id = create_task(user_id=user2_id, title="User2 task", due_date=due_date)

        # Delete task1, keep task2
        delete_task(user1_id, task1_id)

        # Create a real scheduler instance (needed for cleanup to work)
        from communication.core.channel_orchestrator import CommunicationManager

        communication_manager = CommunicationManager()
        real_scheduler = SchedulerManager(communication_manager)
        real_scheduler.handle_task_reminder = (
            MagicMock()
        )  # Mock only the reminder handler
        mock_get_scheduler.return_value = real_scheduler

        # Get scheduler and schedule reminders
        from core.service import get_scheduler_manager

        scheduler = get_scheduler_manager()
        assert scheduler is not None, "Scheduler should be available"

        # Store initial job count for cleanup
        initial_jobs = list(schedule.jobs)

        schedule.every().day.at("09:00").do(
            scheduler.handle_task_reminder, user_id=user1_id, task_id=task1_id
        )
        schedule.every().day.at("10:00").do(
            scheduler.handle_task_reminder, user_id=user2_id, task_id=task2_id
        )

        # Verify task2 exists before cleanup
        task2 = get_task_by_id(user2_id, task2_id)
        assert task2 is not None, "Task2 should exist before cleanup"
        assert not task2.get("completed", False), "Task2 should not be completed"

        # Act - Run cleanup (now uses real cleanup method)
        scheduler.cleanup_orphaned_task_reminders()

        # Assert
        # Task1 reminder should be removed (task deleted)
        reminder_jobs = [
            job
            for job in schedule.jobs
            if hasattr(job.job_func, "func")
            and job.job_func.func == scheduler.handle_task_reminder
        ]

        found_task1_job = any(
            hasattr(job.job_func, "keywords")
            and job.job_func.keywords.get("user_id") == user1_id
            and job.job_func.keywords.get("task_id") == task1_id
            for job in reminder_jobs
        )
        assert not found_task1_job, "Reminder for deleted task1 should be removed"

        # Task2 reminder should be preserved (task still exists)
        found_task2_job = any(
            hasattr(job.job_func, "keywords")
            and job.job_func.keywords.get("user_id") == user2_id
            and job.job_func.keywords.get("task_id") == task2_id
            for job in reminder_jobs
        )
        assert found_task2_job, "Reminder for active task2 should be preserved"

        # Cleanup: Remove jobs we added
        jobs_to_remove = []
        for job in schedule.jobs:
            if hasattr(job.job_func, "keywords"):
                kwargs = job.job_func.keywords
                if kwargs.get("user_id") in (user1_id, user2_id) and kwargs.get(
                    "task_id"
                ) in (task1_id, task2_id):
                    jobs_to_remove.append(job)
        for job in jobs_to_remove:
            try:
                schedule.jobs.remove(job)
            except ValueError:
                pass  # Already removed
