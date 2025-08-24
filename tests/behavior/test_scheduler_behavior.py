"""
Tests for core scheduler module.

Tests scheduling logic, time management, and task execution.
"""

import pytest
import os
import json
import tempfile
import time
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, timedelta
import pytz

from core.user_data_handlers import get_user_data
from core.scheduler import (
    SchedulerManager,
    schedule_all_task_reminders,
    cleanup_task_reminders,
    get_user_categories,
    process_user_schedules
)
from core.error_handling import SchedulerError

@pytest.fixture
def mock_communication_manager():
    """Create a mock communication manager."""
    mock_cm = Mock()
    mock_cm.send_message = Mock(return_value=True)
    return mock_cm

class TestSchedulerManager:
    """Test SchedulerManager functionality."""
    
    @pytest.fixture
    def scheduler_manager(self, mock_communication_manager):
        """Create a SchedulerManager instance for testing."""
        return SchedulerManager(mock_communication_manager)
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    @pytest.mark.critical
    @pytest.mark.regression
    def test_scheduler_manager_initialization(self, mock_communication_manager):
        """Test SchedulerManager initialization."""
        scheduler = SchedulerManager(mock_communication_manager)
        
        assert scheduler.communication_manager == mock_communication_manager
        assert scheduler.scheduler_thread is None
        assert scheduler.running is False
        assert scheduler._stop_event is not None
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    @pytest.mark.critical
    @pytest.mark.regression
    def test_stop_scheduler_no_thread(self, scheduler_manager):
        """Test stopping scheduler when no thread is running."""
        # Should not raise any exceptions
        scheduler_manager.stop_scheduler()
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    @pytest.mark.critical
    @pytest.mark.regression
    def test_is_job_for_category_no_jobs(self, scheduler_manager):
        """Test checking for jobs when no jobs exist."""
        result = scheduler_manager.is_job_for_category(None, 'test-user', 'motivational')
        assert result is False
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    @pytest.mark.critical
    @pytest.mark.regression
    def test_is_job_for_category_with_matching_job(self, scheduler_manager):
        """Test checking for jobs when a matching job exists."""
        # Mock schedule.jobs to contain a matching job
        mock_job = Mock()
        mock_job.job_func.args = ['test-user', 'motivational']
        
        with patch('core.scheduler.schedule') as mock_schedule:
            mock_schedule.jobs = [mock_job]
            
            result = scheduler_manager.is_job_for_category(None, 'test-user', 'motivational')
            assert result is True
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    @pytest.mark.critical
    @pytest.mark.regression
    def test_is_job_for_category_with_non_matching_job(self, scheduler_manager):
        """Test checking for jobs when no matching job exists."""
        # Mock schedule.jobs to contain a non-matching job
        mock_job = Mock()
        mock_job.job_func.args = ['other-user', 'health']
        
        with patch('core.scheduler.schedule') as mock_schedule:
            mock_schedule.jobs = [mock_job]
            
            result = scheduler_manager.is_job_for_category(None, 'test-user', 'motivational')
            assert result is False
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_random_time_within_period_valid_times(self, scheduler_manager):
        """Test getting random time within a valid time period."""
        user_id = 'test-user'
        category = 'motivational'
        period_name = 'morning'
        timezone_str = 'America/Regina'
        
        # Mock get_schedule_time_periods to return a valid period
        with patch('core.scheduler.get_schedule_time_periods') as mock_get_periods:
            mock_get_periods.return_value = {
                period_name: {'start_time': '09:00', 'end_time': '17:00', 'active': True, 'days': ['ALL']}
            }
            
            result = scheduler_manager.get_random_time_within_period(user_id, category, period_name, timezone_str)
            
            # Test real behavior: function returns a string, not datetime
            assert result is not None
            assert isinstance(result, str)
            
            # Parse the result to verify it's a valid datetime string
            result_dt = datetime.strptime(result, "%Y-%m-%d %H:%M")
            assert isinstance(result_dt, datetime)
            
            # Verify the time is within the specified range (9:00-17:00)
            result_time = result_dt.time()
            start_time = datetime.strptime('09:00', "%H:%M").time()
            end_time = datetime.strptime('17:00', "%H:%M").time()
            assert start_time <= result_time <= end_time
            
            # Verify side effect: function should have called get_schedule_time_periods
            mock_get_periods.assert_called_once_with(user_id, category)
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_random_time_within_period_invalid_times(self, scheduler_manager):
        """Test getting random time with invalid time format."""
        user_id = 'test-user'
        category = 'motivational'
        period_name = 'morning'
        timezone_str = 'America/Regina'
        
        with patch('core.scheduler.get_schedule_time_periods') as mock_get_periods:
            mock_get_periods.return_value = {
                period_name: {'start_time': 'invalid', 'end_time': '17:00', 'active': True, 'days': ['ALL']}
            }
            
            # Test real behavior: function returns None when error occurs (due to @handle_errors decorator)
            result = scheduler_manager.get_random_time_within_period(user_id, category, period_name, timezone_str)
            assert result is None
            
            # Verify side effect: function should have called get_schedule_time_periods
            mock_get_periods.assert_called_once_with(user_id, category)
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    @pytest.mark.critical
    @pytest.mark.regression
    def test_is_time_conflict_no_conflicts(self, scheduler_manager):
        """Test time conflict detection when no conflicts exist."""
        schedule_datetime = datetime.now() + timedelta(hours=1)
        
        result = scheduler_manager.is_time_conflict('test-user', schedule_datetime)
        assert result is False
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    @pytest.mark.critical
    @pytest.mark.regression
    def test_cleanup_old_tasks(self, scheduler_manager, test_data_dir):
        """Test cleaning up old scheduled tasks."""
        user_id = 'test-cleanup-user'
        category = 'motivational'
        
        # Create some test data
        user_dir = os.path.join(test_data_dir, 'users', user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Mock schedule.jobs to contain old tasks
        mock_job = Mock()
        mock_job.job_func.args = [user_id, category]
        mock_job.next_run = datetime.now() - timedelta(days=2)  # Old job
        
        with patch('core.scheduler.schedule') as mock_schedule:
            mock_schedule.jobs = [mock_job]
            
            # Should not raise any exceptions
            scheduler_manager.cleanup_old_tasks(user_id, category)
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    @pytest.mark.critical
    @pytest.mark.regression
    def test_log_scheduled_tasks(self, scheduler_manager):
        """Test logging of scheduled tasks."""
        # Mock schedule.jobs
        mock_job1 = Mock()
        mock_job1.job_func.args = ['user1', 'motivational']
        mock_job1.next_run = datetime.now() + timedelta(hours=1)
        
        mock_job2 = Mock()
        mock_job2.job_func.args = ['user2', 'health']
        mock_job2.next_run = datetime.now() + timedelta(hours=2)
        
        with patch('core.scheduler.schedule') as mock_schedule:
            mock_schedule.jobs = [mock_job1, mock_job2]
            
            # Should not raise any exceptions
            scheduler_manager.log_scheduled_tasks()

class TestSchedulerFunctions:
    """Test standalone scheduler functions."""
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    def test_get_user_categories_success(self, mock_user_data):
        """Test getting user categories successfully."""
        user_id = mock_user_data['user_id']
        
        with patch('core.user_data_handlers.get_user_data') as mock_get_data:
            # get_user_data with fields='categories' returns the list directly
            mock_get_data.return_value = ['motivational', 'health', 'fun_facts']
            
            categories = get_user_categories(user_id)
            
            assert isinstance(categories, list)
            assert 'motivational' in categories
            assert 'health' in categories
            assert 'fun_facts' in categories
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    def test_get_user_categories_no_user(self):
        """Test getting categories for non-existent user."""
        with patch('core.user_data_handlers.get_user_data') as mock_get_data:
            mock_get_data.return_value = {}
            
            categories = get_user_categories('nonexistent-user')
            
            assert isinstance(categories, list)
            assert len(categories) == 0
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    def test_get_user_task_preferences_success(self, mock_user_data):
        """Test getting user task preferences successfully."""
        user_id = mock_user_data['user_id']

        # Test the actual get_user_data function with real data
        prefs_result = get_user_data(user_id, 'preferences')
        prefs = prefs_result.get('preferences', {}).get('task_settings', {})

        # Test real behavior: function returns the task_settings dict
        assert isinstance(prefs, dict)
        # Note: mock_user_data has task_settings.enabled = False by default
        assert prefs.get('enabled') is False
        assert prefs.get('reminder_time') == '10:00'
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    def test_get_user_task_preferences_no_user(self):
        """Test getting task preferences for non-existent user."""
        prefs_result = get_user_data('nonexistent-user', 'preferences')
        prefs = prefs_result.get('preferences', {}).get('task_settings', {})
        
        assert isinstance(prefs, dict)
        assert len(prefs) == 0
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    def test_get_user_checkin_preferences_success(self, mock_user_data):
        """Test getting user check-in preferences successfully."""
        user_id = mock_user_data['user_id']
        
        # Test the actual get_user_data function with real data
        prefs_result = get_user_data(user_id, 'preferences')
        prefs = prefs_result.get('preferences', {}).get('checkin_settings', {})
        
        assert isinstance(prefs, dict)
        # Note: mock_user_data has checkin_settings.enabled = False by default
        assert prefs.get('enabled') is False
        assert prefs.get('frequency') == 'daily'
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    def test_get_user_checkin_preferences_no_user(self):
        """Test getting check-in preferences for non-existent user."""
        prefs_result = get_user_data('nonexistent-user', 'preferences')
        prefs = prefs_result.get('preferences', {}).get('checkin_settings', {})
        
        assert isinstance(prefs, dict)
        assert len(prefs) == 0

class TestSchedulerIntegration:
    """Test scheduler integration scenarios."""
    
    @pytest.mark.integration
    def test_scheduler_lifecycle(self, mock_communication_manager, test_data_dir):
        """Test complete scheduler lifecycle."""
        scheduler = SchedulerManager(mock_communication_manager)
        
        # Test initialization
        assert scheduler.communication_manager == mock_communication_manager
        assert scheduler.scheduler_thread is None
        
        # Test stopping when not running (should not raise)
        scheduler.stop_scheduler()
        
        # Verify cleanup
        assert scheduler.scheduler_thread is None
    
    @pytest.mark.integration
    def test_scheduler_with_mock_users(self, mock_communication_manager):
        """Test scheduler with mock user data."""
        scheduler = SchedulerManager(mock_communication_manager)
        
        with patch('core.scheduler.get_all_user_ids') as mock_get_users:
            mock_get_users.return_value = ['user1', 'user2']
            
            with patch('core.scheduler.get_user_data') as mock_get_data:
                mock_get_data.return_value = {
                    'preferences': {
                        'categories': ['motivational']
                    }
                }
                
                # Test scheduling all users immediately
                scheduler.schedule_all_users_immediately()
                
                # Verify communication manager was not called (since we're not actually running)
                mock_communication_manager.send_message.assert_not_called()

class TestSchedulerEdgeCases:
    """Test scheduler edge cases and error conditions."""
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    def test_scheduler_with_empty_user_list(self, mock_communication_manager):
        """Test scheduler behavior with no users."""
        scheduler = SchedulerManager(mock_communication_manager)
        
        with patch('core.scheduler.get_all_user_ids') as mock_get_users:
            mock_get_users.return_value = []
            
            # Should not raise any exceptions
            scheduler.schedule_all_users_immediately()
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    def test_scheduler_with_invalid_user_data(self, mock_communication_manager):
        """Test scheduler behavior with invalid user data."""
        scheduler = SchedulerManager(mock_communication_manager)
        
        with patch('core.scheduler.get_all_user_ids') as mock_get_users:
            mock_get_users.return_value = ['invalid-user']
            
            with patch('core.scheduler.get_user_data') as mock_get_data:
                mock_get_data.return_value = {}  # Empty data
                
                # Should handle gracefully without raising exceptions
                scheduler.schedule_all_users_immediately()
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    def test_random_time_generation_consistency(self, mock_communication_manager):
        """Test that random time generation is consistent within bounds."""
        scheduler = SchedulerManager(mock_communication_manager)

        user_id = 'test-user'
        category = 'motivational'
        period_name = 'morning'
        timezone_str = 'America/Regina'

        # Mock get_schedule_time_periods to return a valid period
        with patch('core.scheduler.get_schedule_time_periods') as mock_get_periods:
            mock_get_periods.return_value = {
                period_name: {'start_time': '10:00', 'end_time': '12:00', 'active': True, 'days': ['ALL']}
            }

            # Generate multiple times and verify they're all within bounds
            times = []
            for _ in range(10):
                result = scheduler.get_random_time_within_period(
                    user_id, category, period_name, timezone_str
                )
                if result is not None:  # Only add valid results
                    times.append(result)

            # All times should be within the specified range
            start_dt = datetime.strptime('10:00', "%H:%M").time()
            end_dt = datetime.strptime('12:00', "%H:%M").time()

            for time_str in times:
                result_dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                result_time = result_dt.time()
                assert start_dt <= result_time <= end_dt, f"Time {result_time} not in range {start_dt}-{end_dt}"

            # Verify side effect: function should have been called multiple times
            assert mock_get_periods.call_count == 10

class TestTaskReminderFunctions:
    """Test task reminder specific functions."""
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    def test_schedule_all_task_reminders_success(self, test_data_dir):
        """Test scheduling all task reminders for a user."""
        user_id = 'test-task-user'
        
        with patch('core.scheduler.get_user_data') as mock_get_data:
            mock_get_data.return_value = {
                'account': {
                    'features': {
                        'task_management': 'enabled'
                    }
                },
                'preferences': {
                    'task_settings': {
                        'enabled': True,
                        'default_reminder_time': '18:00'
                    }
                }
            }
            
            # Should not raise any exceptions
            schedule_all_task_reminders(user_id)
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    def test_schedule_all_task_reminders_disabled(self, test_data_dir):
        """Test scheduling task reminders when task management is disabled."""
        user_id = 'test-task-user'
        
        with patch('core.scheduler.get_user_data') as mock_get_data:
            mock_get_data.return_value = {
                'account': {
                    'features': {
                        'task_management': 'disabled'
                    }
                }
            }
            
            # Should not raise any exceptions
            schedule_all_task_reminders(user_id)
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    def test_cleanup_task_reminders_success(self):
        """Test cleaning up task reminders."""
        user_id = 'test-task-user'
        
        # Mock schedule.jobs
        mock_job = Mock()
        mock_job.job_func.args = [user_id, 'task_reminder']
        
        with patch('core.scheduler.schedule') as mock_schedule:
            mock_schedule.jobs = [mock_job]
            
            # Should not raise any exceptions
            cleanup_task_reminders(user_id)
    
    @pytest.mark.behavior
    @pytest.mark.schedules
    def test_cleanup_task_reminders_specific_task(self):
        """Test cleaning up specific task reminders."""
        user_id = 'test-task-user'
        task_id = 'task-123'
        
        # Mock schedule.jobs
        mock_job = Mock()
        mock_job.job_func.args = [user_id, 'task_reminder', task_id]
        
        with patch('core.scheduler.schedule') as mock_schedule:
            mock_schedule.jobs = [mock_job]
            
            # Should not raise any exceptions
            cleanup_task_reminders(user_id, task_id) 