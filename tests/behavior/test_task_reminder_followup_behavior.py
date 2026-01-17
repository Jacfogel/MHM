"""
Task Reminder Follow-up Flow Behavior Tests

Tests for the reminder period follow-up flow that occurs after task creation.
These tests verify that the flow actually works and produces expected side effects.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from communication.message_processing.conversation_flow_manager import (
    conversation_manager,
    FLOW_TASK_REMINDER,
)
from communication.command_handlers.task_handler import TaskManagementHandler
from tasks.task_management import create_task, get_task_by_id
from tests.test_utilities import TestUserFactory
from core.service_utilities import DATE_ONLY_FORMAT


class TestTaskReminderFollowupBehavior:
    """Test task reminder follow-up flow real behavior and side effects."""

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_task_creation_starts_reminder_followup_flow(self, test_data_dir):
        """Test that creating a task starts the reminder follow-up flow."""
        # Arrange
        user_id = "test_reminder_followup_start"
        TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )

        handler = TaskManagementHandler()

        # Clear any existing state (use global instance)
        conversation_manager.user_states.pop(user_id, None)

        # Act - Create a task
        entities = {
            "title": "Test reminder task",
            "due_date": (datetime.now() + timedelta(days=2)).strftime(DATE_ONLY_FORMAT),
        }
        response = handler._handle_create_task(user_id, entities)

        # Assert - Verify flow was started (check global instance)
        assert not response.completed, "Response should indicate flow is not completed"
        assert (
            user_id in conversation_manager.user_states
        ), "User should be in a flow state"
        assert (
            conversation_manager.user_states[user_id]["flow"] == FLOW_TASK_REMINDER
        ), "Should be in TASK_REMINDER flow"
        assert (
            "task_id" in conversation_manager.user_states[user_id]["data"]
        ), "Should store task_id in flow data"

        # Verify task was actually created
        task_id = conversation_manager.user_states[user_id]["data"]["task_id"]
        task = get_task_by_id(user_id, task_id)
        assert task is not None, "Task should exist"
        assert task["title"] == "Test reminder task", "Task should have correct title"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    def test_reminder_followup_handles_no_reminders_response(self, test_data_dir):
        """Test that 'no reminders' response clears the flow without setting reminders."""
        # Arrange
        user_id = "test_no_reminders"
        TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )

        # Create a task and start the flow
        task_id = create_task(
            user_id=user_id,
            title="Test task",
            due_date=(datetime.now() + timedelta(days=1)).strftime(DATE_ONLY_FORMAT),
        )
        conversation_manager.start_task_reminder_followup(user_id, task_id)

        # Act - User says "no reminders"
        reply, completed = conversation_manager._handle_task_reminder_followup(
            user_id, conversation_manager.user_states[user_id], "no reminders"
        )

        # Assert
        assert completed, "Flow should be completed"
        assert (
            user_id not in conversation_manager.user_states
        ), "Flow state should be cleared"
        assert (
            "no reminders" in reply.lower() or "got it" in reply.lower()
        ), "Should acknowledge no reminders"

        # Verify task has no reminder periods
        task = get_task_by_id(user_id, task_id)
        assert task is not None, "Task should still exist"
        assert "reminder_periods" not in task or not task.get(
            "reminder_periods"
        ), "Task should have no reminder periods"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @patch("core.service.get_scheduler_manager")
    def test_reminder_followup_parses_minutes_before(
        self, mock_get_scheduler, test_data_dir
    ):
        """Test parsing '30 minutes to an hour before' response."""
        # Arrange
        # Mock scheduler manager
        mock_scheduler = MagicMock()
        mock_get_scheduler.return_value = mock_scheduler

        user_id = "test_minutes_before"
        TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )

        due_date = (datetime.now() + timedelta(days=1)).strftime(DATE_ONLY_FORMAT)
        due_time = "14:00"  # 2 PM

        # Create a task with due date and time
        task_id = create_task(
            user_id=user_id, title="Test task", due_date=due_date, due_time=due_time
        )
        conversation_manager.start_task_reminder_followup(user_id, task_id)

        # Act - User says "30 minutes to an hour before"
        reply, completed = conversation_manager._handle_task_reminder_followup(
            user_id,
            conversation_manager.user_states[user_id],
            "30 minutes to an hour before",
        )

        # Debug: Check what was parsed
        # Assert
        assert completed, f"Flow should be completed. Reply: {reply}"
        assert (
            user_id not in conversation_manager.user_states
        ), "Flow state should be cleared"

        # Verify task has reminder periods set
        task = get_task_by_id(user_id, task_id)
        assert task is not None, "Task should exist"
        assert (
            "reminder_periods" in task
        ), f"Task should have reminder_periods. Task: {task}"
        assert (
            len(task["reminder_periods"]) > 0
        ), "Should have at least one reminder period"

        # Verify reminder period is approximately correct (30-60 min before 2 PM = 1:00-1:30 PM)
        reminder = task["reminder_periods"][0]
        assert reminder["date"] == due_date, "Reminder should be on due date"
        # Times should be around 13:00-13:30 (1:00-1:30 PM)
        start_hour = int(reminder["start_time"].split(":")[0])
        assert (
            12 <= start_hour <= 13
        ), f"Start time should be around 1 PM, got {reminder['start_time']}"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @patch("core.service.get_scheduler_manager")
    def test_reminder_followup_parses_hours_before(
        self, mock_get_scheduler, test_data_dir
    ):
        """Test parsing '3 to 5 hours before' response."""
        # Arrange
        # Mock scheduler manager
        mock_scheduler = MagicMock()
        mock_get_scheduler.return_value = mock_scheduler

        user_id = "test_hours_before"
        TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )

        due_date = (datetime.now() + timedelta(days=1)).strftime(DATE_ONLY_FORMAT)
        due_time = "15:00"  # 3 PM

        task_id = create_task(
            user_id=user_id, title="Test task", due_date=due_date, due_time=due_time
        )
        conversation_manager.start_task_reminder_followup(user_id, task_id)

        # Act - User says "3 to 5 hours before"
        reply, completed = conversation_manager._handle_task_reminder_followup(
            user_id, conversation_manager.user_states[user_id], "3 to 5 hours before"
        )

        # Assert
        assert completed, f"Flow should be completed. Reply: {reply}"

        # Verify reminder periods
        task = get_task_by_id(user_id, task_id)
        assert "reminder_periods" in task, "Task should have reminder_periods"
        reminder = task["reminder_periods"][0]

        # Should be 3-5 hours before 3 PM = 10 AM - 12 PM
        start_hour = int(reminder["start_time"].split(":")[0])
        assert (
            9 <= start_hour <= 12
        ), f"Start time should be around 10 AM-12 PM, got {reminder['start_time']}"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @patch("core.service.get_scheduler_manager")
    def test_reminder_followup_parses_days_before(
        self, mock_get_scheduler, test_data_dir
    ):
        """Test parsing '1 to 2 days before' response."""
        # Arrange
        # Mock scheduler manager
        mock_scheduler = MagicMock()
        mock_get_scheduler.return_value = mock_scheduler

        user_id = "test_days_before"
        TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )

        due_date = (datetime.now() + timedelta(days=3)).strftime(DATE_ONLY_FORMAT)

        task_id = create_task(user_id=user_id, title="Test task", due_date=due_date)
        conversation_manager.start_task_reminder_followup(user_id, task_id)

        # Act - User says "1 to 2 days before"
        reply, completed = conversation_manager._handle_task_reminder_followup(
            user_id, conversation_manager.user_states[user_id], "1 to 2 days before"
        )

        # Assert
        assert completed, "Flow should be completed"

        # Verify reminder periods
        task = get_task_by_id(user_id, task_id)
        assert "reminder_periods" in task, "Task should have reminder_periods"
        reminder = task["reminder_periods"][0]

        # Should be 1-2 days before due date
        reminder_date = datetime.strptime(reminder["date"], DATE_ONLY_FORMAT).date()
        due_date_obj = datetime.strptime(due_date, DATE_ONLY_FORMAT).date()
        days_before = (due_date_obj - reminder_date).days

        assert (
            1 <= days_before <= 2
        ), f"Reminder should be 1-2 days before, got {days_before} days"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @patch("core.service.get_scheduler_manager")
    def test_reminder_followup_handles_task_without_due_date(
        self, mock_get_scheduler, test_data_dir
    ):
        """Test that reminder follow-up handles tasks without due dates gracefully."""
        # Arrange
        user_id = "test_no_due_date"
        TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )

        # Create a task without due date
        task_id = create_task(user_id=user_id, title="Test task without due date")
        conversation_manager.start_task_reminder_followup(user_id, task_id)

        # Act - User tries to set reminders
        reply, completed = conversation_manager._handle_task_reminder_followup(
            user_id, conversation_manager.user_states[user_id], "30 minutes before"
        )

        # Assert
        assert completed, "Flow should be completed"
        assert "due date" in reply.lower(), "Should mention due date requirement"

        # Task should still exist but without reminders
        task = get_task_by_id(user_id, task_id)
        assert task is not None, "Task should exist"
        assert "reminder_periods" not in task or not task.get(
            "reminder_periods"
        ), "Task should have no reminder periods"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @patch("core.service.get_scheduler_manager")
    def test_reminder_followup_handles_unparseable_response(
        self, mock_get_scheduler, test_data_dir
    ):
        """Test that unparseable responses ask for clarification."""
        # Arrange
        user_id = "test_unparseable"
        TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )

        due_date = (datetime.now() + timedelta(days=1)).strftime(DATE_ONLY_FORMAT)

        task_id = create_task(user_id=user_id, title="Test task", due_date=due_date)
        conversation_manager.start_task_reminder_followup(user_id, task_id)

        # Act - User gives unparseable response
        reply, completed = conversation_manager._handle_task_reminder_followup(
            user_id, conversation_manager.user_states[user_id], "maybe sometime"
        )

        # Assert
        assert not completed, "Flow should continue asking for clarification"
        assert (
            user_id in conversation_manager.user_states
        ), "Flow state should still be active"
        assert (
            "not sure" in reply.lower() or "specify" in reply.lower()
        ), "Should ask for clarification"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @patch("core.service.get_scheduler_manager")
    @patch("core.scheduler.SchedulerManager.set_wake_timer")
    def test_reminder_followup_schedules_reminders(
        self, mock_wake_timer, mock_get_scheduler, test_data_dir
    ):
        """Test that reminder follow-up actually schedules reminders."""
        # Arrange
        user_id = "test_schedule_reminders"
        TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )

        # Mock scheduler manager
        mock_scheduler = MagicMock()
        mock_get_scheduler.return_value = mock_scheduler

        due_date = (datetime.now() + timedelta(days=1)).strftime(DATE_ONLY_FORMAT)
        due_time = "14:00"

        task_id = create_task(
            user_id=user_id, title="Test task", due_date=due_date, due_time=due_time
        )
        conversation_manager.start_task_reminder_followup(user_id, task_id)

        # Act - User sets reminders
        reply, completed = conversation_manager._handle_task_reminder_followup(
            user_id, conversation_manager.user_states[user_id], "1 hour before"
        )

        # Assert
        assert completed, "Flow should be completed"

        # Verify reminders were scheduled (check that schedule_task_reminders was called)
        # This is indirect - we verify the task has reminder_periods set
        task = get_task_by_id(user_id, task_id)
        assert "reminder_periods" in task, "Task should have reminder_periods"
        assert len(task["reminder_periods"]) > 0, "Should have reminder periods"
