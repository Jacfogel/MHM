"""
Discord Task Reminder Follow-up Flow Tests

Tests the complete Discord flow for task creation with reminder follow-up.
"""

import pytest
from unittest.mock import patch, MagicMock

from communication.message_processing.interaction_manager import InteractionManager
from tasks.task_management import load_active_tasks
from communication.message_processing.conversation_flow_manager import conversation_manager, FLOW_TASK_REMINDER
from tests.test_utilities import TestUserFactory


class TestDiscordTaskReminderFollowup:
    """Test Discord task reminder follow-up flow."""
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @pytest.mark.communication
    @patch('core.service.get_scheduler_manager')
    def test_discord_task_creation_triggers_reminder_followup(self, mock_get_scheduler, test_data_dir):
        """Test that creating a task via Discord triggers reminder follow-up flow."""
        # Arrange
        mock_scheduler = MagicMock()
        mock_get_scheduler.return_value = mock_scheduler
        
        user_id = "test_discord_reminder_flow"
        TestUserFactory.create_basic_user(user_id, enable_tasks=True, test_data_dir=test_data_dir)
        
        manager = InteractionManager()
        conversation_manager.user_states.pop(user_id, None)
        
        # Act - Create task via Discord message
        message = "create task to call dentist tomorrow"
        response = manager.handle_message(user_id, message, channel_type="discord")
        
        # Assert - Should ask about reminders
        assert not response.completed, "Response should indicate flow is not completed"
        assert "reminder" in response.message.lower(), "Should mention reminders"
        assert user_id in conversation_manager.user_states, "User should be in flow state"
        assert conversation_manager.user_states[user_id]['flow'] == FLOW_TASK_REMINDER, "Should be in TASK_REMINDER flow"
        
        # Verify task was created
        tasks = load_active_tasks(user_id)
        assert len(tasks) > 0, "Task should be created"
        task = tasks[-1]  # Most recent task
        assert "dentist" in task['title'].lower(), "Task should have correct title"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @pytest.mark.communication
    @patch('core.service.get_scheduler_manager')
    def test_discord_reminder_followup_complete_flow(self, mock_get_scheduler, test_data_dir):
        """Test complete Discord flow: create task -> set reminders."""
        # Arrange
        mock_scheduler = MagicMock()
        mock_get_scheduler.return_value = mock_scheduler
        
        user_id = "test_discord_complete_flow"
        TestUserFactory.create_basic_user(user_id, enable_tasks=True, test_data_dir=test_data_dir)
        
        manager = InteractionManager()
        conversation_manager.user_states.pop(user_id, None)
        
        # Step 1: Create task
        message1 = "create task to buy groceries tomorrow at 2pm"
        response1 = manager.handle_message(user_id, message1, channel_type="discord")
        
        assert not response1.completed, "Should ask about reminders"
        assert user_id in conversation_manager.user_states, "Should be in flow"
        
        # Step 2: Set reminders
        message2 = "30 minutes to an hour before"
        response2 = manager.handle_message(user_id, message2, channel_type="discord")
        
        # Assert
        assert response2.completed, "Flow should be completed"
        assert user_id not in conversation_manager.user_states, "Flow should be cleared"
        assert "reminder" in response2.message.lower() or "set" in response2.message.lower(), "Should confirm reminders set"
        
        # Verify task has reminder periods
        tasks = load_active_tasks(user_id)
        task = tasks[-1]  # Most recent task
        assert 'reminder_periods' in task, "Task should have reminder_periods"
        assert len(task['reminder_periods']) > 0, "Should have reminder periods"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.tasks
    @pytest.mark.communication
    @patch('core.service.get_scheduler_manager')
    def test_discord_reminder_followup_no_reminders(self, mock_get_scheduler, test_data_dir):
        """Test Discord flow: create task -> decline reminders."""
        # Arrange
        mock_scheduler = MagicMock()
        mock_get_scheduler.return_value = mock_scheduler
        
        user_id = "test_discord_no_reminders"
        TestUserFactory.create_basic_user(user_id, enable_tasks=True, test_data_dir=test_data_dir)
        
        manager = InteractionManager()
        conversation_manager.user_states.pop(user_id, None)
        
        # Step 1: Create task
        message1 = "create task to water plants tomorrow"
        response1 = manager.handle_message(user_id, message1, channel_type="discord")
        
        assert not response1.completed, "Should ask about reminders"
        
        # Step 2: Decline reminders
        message2 = "no reminders"
        response2 = manager.handle_message(user_id, message2, channel_type="discord")
        
        # Assert
        assert response2.completed, "Flow should be completed"
        assert "no reminders" in response2.message.lower() or "got it" in response2.message.lower(), "Should acknowledge no reminders"
        
        # Verify task exists but has no reminder periods
        tasks = load_active_tasks(user_id)
        task = tasks[-1]
        assert 'reminder_periods' not in task or not task.get('reminder_periods'), "Task should have no reminder periods"

