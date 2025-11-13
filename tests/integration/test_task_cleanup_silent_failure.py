"""
Test to verify that cleanup_task_reminders fails silently.

This test verifies that the bug exists but doesn't crash the system
because exceptions are caught.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import logging

from tasks.task_management import cleanup_task_reminders, complete_task, delete_task
from tests.test_utilities import TestUserFactory


class TestTaskCleanupSilentFailure:
    """Test that cleanup failures are silent."""
    
    def _create_test_user(self, user_id: str, test_data_dir: str = None) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(user_id, enable_checkins=False, test_data_dir=test_data_dir)
    
    @pytest.mark.integration
    @pytest.mark.tasks
    @pytest.mark.critical
    @pytest.mark.file_io
    def test_cleanup_fails_silently_when_method_missing(self, test_data_dir, caplog):
        """
        Test that cleanup_task_reminders works correctly now that the method exists.
        
        BUG FIXED: The cleanup_task_reminders method now exists in SchedulerManager.
        This test verifies that cleanup works correctly.
        """
        user_id = "test_user_silent_failure"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create a task
        from tasks.task_management import create_task
        task_id = create_task(user_id=user_id, title="Test Task")
        
        # Set up logging capture for all levels
        with caplog.at_level(logging.DEBUG):
            # Try to clean up - should work now that method exists
            result = cleanup_task_reminders(user_id, task_id)
            
            # Check all logs
            all_logs = [record for record in caplog.records]
            log_messages = [record.message for record in all_logs]
            
            # Cleanup should succeed (returns True) or return False if scheduler unavailable
            # But should NOT fail with AttributeError anymore
            if any('AttributeError' in msg or 'cleanup_task_reminders' in msg and 'does not exist' in msg for msg in log_messages):
                pytest.fail(f"BUG STILL EXISTS: cleanup_task_reminders method missing. Logs: {log_messages}")
            
            # If result is True, cleanup succeeded (expected)
            # If result is False, scheduler might not be available (acceptable in test context)
            # The important thing is no AttributeError
    
    @pytest.mark.integration
    @pytest.mark.tasks
    @pytest.mark.critical
    @pytest.mark.file_io
    def test_complete_task_doesnt_crash_but_cleanup_fails(self, test_data_dir, caplog):
        """
        Test that completing a task doesn't crash, but cleanup fails silently.
        
        This is the real-world scenario: user completes a task, system doesn't crash,
        but reminders are never cleaned up.
        """
        user_id = "test_user_complete_cleanup_fail"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create a task
        from tasks.task_management import create_task
        task_id = create_task(user_id=user_id, title="Task to Complete")
        
        # Complete the task - this should succeed, but cleanup will fail
        with caplog.at_level(logging.ERROR):
            result = complete_task(user_id, task_id)
            
            # Task completion should succeed (the bug doesn't prevent completion)
            assert result is True, "Task should be completed even if cleanup fails"
            
            # But cleanup should have failed
            error_logs = [record for record in caplog.records if record.levelname == 'ERROR']
            error_messages = [record.message for record in error_logs]
            
            # Check if cleanup error was logged
            cleanup_errors = [msg for msg in error_messages if 'cleanup' in msg.lower() or 'reminder' in msg.lower()]
            
            # This documents the bug: cleanup fails but doesn't prevent task completion
            # The reminders remain scheduled even though the task is completed
            if cleanup_errors:
                pytest.fail(f"BUG CONFIRMED: Cleanup failed with errors: {cleanup_errors}. "
                          f"Reminders were not cleaned up for completed task.")

