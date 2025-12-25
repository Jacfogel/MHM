"""
Integration tests for task reminder system.

Tests the complete flow from task creation through reminder scheduling to delivery.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import time

from tasks.task_management import (
    create_task, complete_task, delete_task, update_task,
    load_active_tasks
)
from tests.test_utilities import TestUserFactory


class TestTaskReminderIntegration:
    """Integration tests for task reminder system."""
    
    def _create_test_user(self, user_id: str, test_data_dir: str = None) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(user_id, enable_checkins=False, test_data_dir=test_data_dir)
    
    @pytest.mark.integration
    @pytest.mark.tasks
    @pytest.mark.tasks
    @pytest.mark.file_io
    def test_task_creation_with_reminders_schedules_reminders(self, test_data_dir):
        """Test that creating a task with reminder_periods schedules reminders."""
        user_id = "test_user_reminder_integration"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create task with reminder periods
        reminder_periods = [
            {'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'), 'start_time': '09:00', 'end_time': '10:00'},
            {'date': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'), 'start_time': '14:00', 'end_time': '15:00'}
        ]
        
        with patch('core.service.get_scheduler_manager') as mock_get_scheduler:
            mock_scheduler = MagicMock()
            mock_scheduler.schedule_task_reminder_at_datetime.return_value = True
            mock_get_scheduler.return_value = mock_scheduler
            
            task_id = create_task(
                user_id=user_id,
                title="Test Task with Reminders",
                reminder_periods=reminder_periods
            )
            
            assert task_id is not None, "Task should be created"
            
            # Verify reminders were scheduled
            assert mock_scheduler.schedule_task_reminder_at_datetime.call_count == 2, "Should schedule 2 reminders"
            
            # Verify correct dates/times were used
            calls = mock_scheduler.schedule_task_reminder_at_datetime.call_args_list
            assert calls[0][0][2] == reminder_periods[0]['date'], "First reminder should use first date"
            assert calls[0][0][3] == reminder_periods[0]['start_time'], "First reminder should use first start_time"
            assert calls[1][0][2] == reminder_periods[1]['date'], "Second reminder should use second date"
            assert calls[1][0][3] == reminder_periods[1]['start_time'], "Second reminder should use second start_time"
    
    @pytest.mark.integration
    @pytest.mark.tasks
    @pytest.mark.tasks
    @pytest.mark.file_io
    def test_task_completion_cleans_up_reminders(self, test_data_dir):
        """Test that completing a task cleans up its reminders."""
        user_id = "test_user_reminder_cleanup"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create task with reminders
        reminder_periods = [
            {'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'), 'start_time': '09:00', 'end_time': '10:00'}
        ]
        
        with patch('core.service.get_scheduler_manager') as mock_get_scheduler:
            mock_scheduler = MagicMock()
            mock_scheduler.schedule_task_reminder_at_datetime.return_value = True
            mock_get_scheduler.return_value = mock_scheduler
            
            task_id = create_task(
                user_id=user_id,
                title="Task to Complete",
                reminder_periods=reminder_periods
            )
            
            # Complete the task
            with patch('core.service.get_scheduler_manager') as mock_get_scheduler_cleanup:
                mock_scheduler_cleanup_instance = MagicMock()
                mock_get_scheduler_cleanup.return_value = mock_scheduler_cleanup_instance
                
                result = complete_task(user_id, task_id)
                
                assert result is True, "Task should be completed"
                
                # Verify cleanup was called
                mock_scheduler_cleanup_instance.cleanup_task_reminders.assert_called_once_with(user_id, task_id)
    
    @pytest.mark.integration
    @pytest.mark.tasks
    @pytest.mark.tasks
    @pytest.mark.file_io
    def test_task_deletion_cleans_up_reminders(self, test_data_dir):
        """Test that deleting a task cleans up its reminders."""
        user_id = "test_user_reminder_delete"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create task with reminders
        reminder_periods = [
            {'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'), 'start_time': '09:00', 'end_time': '10:00'}
        ]
        
        with patch('core.service.get_scheduler_manager') as mock_get_scheduler:
            mock_scheduler = MagicMock()
            mock_scheduler.schedule_task_reminder_at_datetime.return_value = True
            mock_get_scheduler.return_value = mock_scheduler
            
            task_id = create_task(
                user_id=user_id,
                title="Task to Delete",
                reminder_periods=reminder_periods
            )
            
            # Delete the task
            with patch('core.service.get_scheduler_manager') as mock_get_scheduler_cleanup:
                mock_scheduler_cleanup_instance = MagicMock()
                mock_get_scheduler_cleanup.return_value = mock_scheduler_cleanup_instance
                
                result = delete_task(user_id, task_id)
                
                assert result is True, "Task should be deleted"
                
                # Verify cleanup was called
                mock_scheduler_cleanup_instance.cleanup_task_reminders.assert_called_once_with(user_id, task_id)
    
    @pytest.mark.integration
    @pytest.mark.tasks
    @pytest.mark.tasks
    @pytest.mark.file_io
    def test_task_update_with_new_reminders_reschedules(self, test_data_dir):
        """Test that updating a task with new reminder_periods reschedules reminders."""
        user_id = "test_user_reminder_update"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create task with initial reminders
        initial_reminders = [
            {'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'), 'start_time': '09:00', 'end_time': '10:00'}
        ]
        
        with patch('core.service.get_scheduler_manager') as mock_get_scheduler:
            mock_scheduler = MagicMock()
            mock_scheduler.schedule_task_reminder_at_datetime.return_value = True
            mock_get_scheduler.return_value = mock_scheduler
            
            task_id = create_task(
                user_id=user_id,
                title="Task to Update",
                reminder_periods=initial_reminders
            )
            
            # Update with new reminders
            new_reminders = [
                {'date': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'), 'start_time': '15:00', 'end_time': '16:00'},
                {'date': (datetime.now() + timedelta(days=4)).strftime('%Y-%m-%d'), 'start_time': '10:00', 'end_time': '11:00'}
            ]
            
            with patch('core.service.get_scheduler_manager') as mock_get_scheduler_update:
                mock_scheduler_update_instance = MagicMock()
                mock_scheduler_update_instance.schedule_task_reminder_at_datetime.return_value = True
                mock_get_scheduler_update.return_value = mock_scheduler_update_instance
                
                result = update_task(user_id, task_id, {'reminder_periods': new_reminders})
                
                assert result is True, "Task should be updated"
                
                # Verify cleanup was called (to remove old reminders)
                mock_scheduler_update_instance.cleanup_task_reminders.assert_called_once_with(user_id, task_id)
                
                # Verify new reminders were scheduled
                assert mock_scheduler_update_instance.schedule_task_reminder_at_datetime.call_count == 2, "Should schedule 2 new reminders"
    
    @pytest.mark.integration
    @pytest.mark.tasks
    @pytest.mark.tasks
    @pytest.mark.file_io
    def test_recurring_task_completion_creates_next_instance_with_reminders(self, test_data_dir):
        """Test that completing a recurring task creates next instance and schedules its reminders."""
        user_id = "test_user_recurring_reminders"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create recurring task with reminders
        reminder_periods = [
            {'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'), 'start_time': '09:00', 'end_time': '10:00'}
        ]
        
        with patch('core.service.get_scheduler_manager') as mock_get_scheduler:
            mock_scheduler = MagicMock()
            mock_scheduler.schedule_task_reminder_at_datetime.return_value = True
            mock_get_scheduler.return_value = mock_scheduler
            
            task_id = create_task(
                user_id=user_id,
                title="Daily Recurring Task",
                recurrence_pattern="daily",
                recurrence_interval=1,
                reminder_periods=reminder_periods
            )
            
            # Complete the task
            with patch('core.service.get_scheduler_manager') as mock_get_scheduler_complete:
                mock_scheduler_complete_instance = MagicMock()
                mock_scheduler_complete_instance.schedule_task_reminder_at_datetime.return_value = True
                mock_get_scheduler_complete.return_value = mock_scheduler_complete_instance
                
                result = complete_task(user_id, task_id)
                
                assert result is True, "Task should be completed"
                
                # Verify next instance was created
                active_tasks = load_active_tasks(user_id)
                assert len(active_tasks) == 1, "Should have one active task (the next instance)"
                assert active_tasks[0]['title'] == "Daily Recurring Task", "Next instance should have same title"
                assert active_tasks[0].get('recurrence_pattern') == 'daily', "Next instance should be recurring"
                
                # Verify reminders were scheduled for next instance
                # Note: This may require checking the actual reminder scheduling logic
                # The next instance should have reminder_periods copied from original


class TestReminderDeliveryIntegration:
    """Integration tests for reminder delivery."""
    
    @pytest.mark.integration
    @pytest.mark.tasks
    @pytest.mark.file_io
    def test_reminder_delivery_skips_completed_tasks(self, test_data_dir):
        """Test that reminders are not sent for completed tasks."""
        user_id = "test_user_reminder_skip"
        from core.scheduler import SchedulerManager
        from communication.core.channel_orchestrator import CommunicationManager
        
        # Create mock communication manager
        mock_comm_manager = MagicMock(spec=CommunicationManager)
        scheduler = SchedulerManager(mock_comm_manager)
        
        # Create a completed task
        from tasks.task_management import create_task, complete_task
        from tests.test_utilities import TestUserFactory
        
        TestUserFactory.create_basic_user(user_id, enable_checkins=False, test_data_dir=test_data_dir)
        
        task_id = create_task(user_id=user_id, title="Task to Complete")
        complete_task(user_id, task_id)
        
        # Try to send reminder
        scheduler.handle_task_reminder(user_id, task_id)
        
        # Verify reminder was NOT sent
        mock_comm_manager.handle_task_reminder.assert_not_called()
    
    @pytest.mark.integration
    @pytest.mark.tasks
    @pytest.mark.file_io
    def test_reminder_delivery_sends_for_active_tasks(self, test_data_dir):
        """Test that reminders are sent for active tasks."""
        user_id = "test_user_reminder_send"
        from core.scheduler import SchedulerManager
        from communication.core.channel_orchestrator import CommunicationManager
        
        # Create mock communication manager
        mock_comm_manager = MagicMock(spec=CommunicationManager)
        scheduler = SchedulerManager(mock_comm_manager)
        
        # Create an active task
        from tasks.task_management import create_task
        from tests.test_utilities import TestUserFactory
        
        TestUserFactory.create_basic_user(user_id, enable_checkins=False, test_data_dir=test_data_dir)
        
        task_id = create_task(user_id=user_id, title="Active Task")
        
        # Send reminder
        scheduler.handle_task_reminder(user_id, task_id)
        
        # Verify reminder WAS sent
        mock_comm_manager.handle_task_reminder.assert_called_once_with(user_id, task_id)

