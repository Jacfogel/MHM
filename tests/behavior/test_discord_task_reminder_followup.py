"""
Discord Task Reminder Follow-up Flow Tests

Tests the complete Discord flow for task creation with reminder follow-up.
"""

from unittest.mock import patch, MagicMock
from uuid import uuid4

import pytest

from communication.message_processing.interaction_manager import InteractionManager
from tasks import load_active_tasks
from tasks.task_data_handlers import runtime_task_scheduled_reminder_periods
from communication.message_processing.conversation_flow_manager import conversation_manager
from communication.message_processing.flows.flow_constants import (
    FLOW_TASK_DUE_DATE,
    FLOW_TASK_PRIORITY,
    FLOW_TASK_REMINDER,
    TASK_DUE_DATE_SUGGESTIONS,
    TASK_PRIORITY_SUGGESTIONS,
)
from tests.test_helpers.test_utilities import TestUserFactory

# Global conversation_manager.user_states is process-wide; parallel workers can interleave flows.
pytestmark = pytest.mark.no_parallel


class TestDiscordTaskReminderFollowup:
    """Test Discord task reminder follow-up flow."""

    def _unique_user_id(self, name: str) -> str:
        return f"test_discord_{name}_{uuid4().hex[:8]}"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @patch('core.service.get_scheduler_manager')
    def test_discord_task_creation_triggers_reminder_followup(self, mock_get_scheduler, test_data_dir):
        """Test that creating a task via Discord triggers reminder follow-up flow."""
        # Arrange
        mock_scheduler = MagicMock()
        mock_get_scheduler.return_value = mock_scheduler

        user_id = self._unique_user_id("reminder_flow")
        assert TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        
        manager = InteractionManager()
        conversation_manager.user_states.pop(user_id, None)
        
        # Act - Create task via Discord message
        message = "create task to call dentist tomorrow"
        response = manager.handle_message(user_id, message, channel_type="discord")
        
        # Assert - Should ask about priority before reminders
        assert not response.completed, "Response should indicate flow is not completed"
        assert "priority" in response.message.lower(), "Should mention priority"
        assert user_id in conversation_manager.user_states, "User should be in flow state"
        assert conversation_manager.user_states[user_id]['flow'] == FLOW_TASK_PRIORITY, "Should be in TASK_PRIORITY flow"
        
        # Verify task was created
        tasks = load_active_tasks(user_id)
        assert len(tasks) > 0, "Task should be created"
        task = tasks[-1]  # Most recent task
        assert "dentist" in task['title'].lower(), "Task should have correct title"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @patch('core.service.get_scheduler_manager')
    def test_discord_reminder_followup_complete_flow(self, mock_get_scheduler, test_data_dir):
        """Test complete Discord flow: create task -> set reminders."""
        # Arrange
        mock_scheduler = MagicMock()
        mock_get_scheduler.return_value = mock_scheduler

        user_id = self._unique_user_id("complete_flow")
        assert TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        
        manager = InteractionManager()
        conversation_manager.user_states.pop(user_id, None)
        
        # Step 1: Create task
        message1 = "create task to buy groceries tomorrow at 2pm"
        response1 = manager.handle_message(user_id, message1, channel_type="discord")

        assert not response1.completed, "Should ask about priority"
        assert user_id in conversation_manager.user_states, "Should be in flow"
        assert load_active_tasks(user_id), "Task should exist before priority follow-up"

        # Step 2: Skip priority, moving into reminder setup
        response2 = manager.handle_message(user_id, "skip", channel_type="discord")
        assert not response2.completed, "Should ask about reminders"
        assert "reminder" in response2.message.lower(), "Should mention reminders"
        assert conversation_manager.user_states[user_id]['flow'] == FLOW_TASK_REMINDER

        # Step 3: Set reminders
        message3 = "30 minutes to an hour before"
        response3 = manager.handle_message(user_id, message3, channel_type="discord")
        
        # Assert
        assert response3.completed, "Flow should be completed"
        assert user_id not in conversation_manager.user_states, "Flow should be cleared"
        assert "reminder" in response3.message.lower() or "set" in response3.message.lower(), "Should confirm reminders set"
        
        # Verify task has scheduled reminder periods (canonical reminders[])
        tasks = load_active_tasks(user_id)
        task = tasks[-1]  # Most recent task
        periods = runtime_task_scheduled_reminder_periods(task)
        assert periods, "Task should have scheduled reminder periods"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @patch("core.service.get_scheduler_manager")
    def test_nt_call_dentist_skip_due_date_shows_priority_buttons(
        self, mock_get_scheduler, test_data_dir
    ):
        """Live-validation path: nt shorthand -> due-date skip -> priority suggestions."""
        mock_get_scheduler.return_value = MagicMock()

        user_id = self._unique_user_id("nt_dentist_priority")
        assert TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )

        manager = InteractionManager()
        conversation_manager.user_states.pop(user_id, None)

        response1 = manager.handle_message(user_id, "nt call dentist", channel_type="discord")
        assert not response1.completed
        assert "due date" in response1.message.lower()
        assert response1.suggestions == list(TASK_DUE_DATE_SUGGESTIONS)
        assert conversation_manager.user_states[user_id]["flow"] == FLOW_TASK_DUE_DATE

        response2 = manager.handle_message(
            user_id, "Skip Question", channel_type="discord"
        )
        assert not response2.completed
        assert "priority" in response2.message.lower()
        assert response2.suggestions == list(TASK_PRIORITY_SUGGESTIONS)
        assert conversation_manager.user_states[user_id]["flow"] == FLOW_TASK_PRIORITY

        tasks = load_active_tasks(user_id)
        assert tasks, "Task should exist after due-date skip"
        assert "dentist" in tasks[-1]["title"].lower()

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @patch('core.service.get_scheduler_manager')
    def test_discord_reminder_followup_no_reminders(self, mock_get_scheduler, test_data_dir):
        """Test Discord flow: create task -> decline reminders."""
        # Arrange
        mock_scheduler = MagicMock()
        mock_get_scheduler.return_value = mock_scheduler

        user_id = self._unique_user_id("no_reminders")
        assert TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        
        manager = InteractionManager()
        conversation_manager.user_states.pop(user_id, None)
        
        # Step 1: Create task
        message1 = "create task to water plants tomorrow"
        response1 = manager.handle_message(user_id, message1, channel_type="discord")

        assert not response1.completed, "Should ask about priority"
        assert user_id in conversation_manager.user_states, "Should be in flow"
        assert load_active_tasks(user_id), "Task should exist before reminder decline"
        
        # Step 2: Skip priority, moving into reminder setup
        response2 = manager.handle_message(user_id, "skip", channel_type="discord")
        assert not response2.completed, "Should ask about reminders"
        assert conversation_manager.user_states[user_id]['flow'] == FLOW_TASK_REMINDER

        # Step 3: Decline reminders
        message3 = "no reminders"
        response3 = manager.handle_message(user_id, message3, channel_type="discord")
        
        # Assert
        assert response3.completed, "Flow should be completed"
        assert "no reminders" in response3.message.lower() or "got it" in response3.message.lower(), "Should acknowledge no reminders"
        
        # Verify task exists but has no reminder periods
        tasks = load_active_tasks(user_id)
        task = tasks[-1]
        assert 'reminder_periods' not in task or not task.get('reminder_periods'), "Task should have no reminder periods"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @patch("core.service.get_scheduler_manager")
    def test_discord_tomorrow_at_2pm_reminder_uses_due_time(
        self, mock_get_scheduler, test_data_dir
    ):
        """Live-validation path: tomorrow at 2pm -> reminders 30-60 min before due time."""
        mock_get_scheduler.return_value = MagicMock()

        user_id = self._unique_user_id("tomorrow_2pm_reminder")
        assert TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )

        manager = InteractionManager()
        conversation_manager.user_states.pop(user_id, None)

        response1 = manager.handle_message(
            user_id,
            "create task to buy groceries tomorrow at 2pm",
            channel_type="discord",
        )
        assert not response1.completed
        assert "priority" in response1.message.lower()

        tasks = load_active_tasks(user_id)
        assert tasks
        task = tasks[-1]
        assert task["title"].lower() == "buy groceries"
        assert task["due"]["time"] == "14:00"

        response2 = manager.handle_message(user_id, "low", channel_type="discord")
        assert not response2.completed
        assert "reminder" in response2.message.lower()

        response3 = manager.handle_message(
            user_id, "30 minutes to an hour before", channel_type="discord"
        )
        assert response3.completed

        task = load_active_tasks(user_id)[-1]
        periods = runtime_task_scheduled_reminder_periods(task)
        assert periods, "Task should have scheduled reminder periods"
        reminder = periods[0]
        start_hour = int(reminder["start_time"].split(":")[0])
        end_hour = int(reminder["end_time"].split(":")[0])
        assert start_hour == 13, f"Expected 13:00 start, got {reminder['start_time']}"
        assert end_hour == 13, f"Expected 13:30 end, got {reminder['end_time']}"
        assert reminder["end_time"].endswith(":30")
