"""
Real integration test for task cleanup - tests actual system behavior.

Following testing guidelines:
- Verify actual system changes (files, state)
- Mock Windows task creation (set_wake_timer)
- Test real scheduler logic and job management
- Verify side effects and data persistence
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

from tasks.task_management import (
    create_task, complete_task, delete_task, update_task,
    load_active_tasks, load_completed_tasks, get_task_by_id
)
from tests.test_utilities import TestUserFactory


class TestTaskCleanupReal:
    """Test task cleanup with real system calls - verifies actual behavior."""
    
    def _create_test_user(self, user_id: str, test_data_dir: str = None) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(user_id, enable_checkins=False, test_data_dir=test_data_dir)
    
    @pytest.mark.integration
    @pytest.mark.tasks
    @pytest.mark.critical
    @pytest.mark.file_io
    def test_complete_task_verifies_actual_system_changes(self, test_data_dir):
        """
        Test: Completing a task moves it to completed_tasks.json and removes from active_tasks.json.
        
        Verifies actual system changes per testing guidelines.
        """
        # Arrange: Create user and task
        user_id = "test_user_complete_verify"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        task_id = create_task(
            user_id=user_id,
            title="Task to Complete",
            description="Test task"
        )
        
        assert task_id is not None, "Task should be created"
        
        # Verify task exists in active_tasks before completion
        active_before = load_active_tasks(user_id)
        assert any(t['task_id'] == task_id for t in active_before), "Task should be in active_tasks"
        
        completed_before = load_completed_tasks(user_id)
        assert not any(t['task_id'] == task_id for t in completed_before), "Task should not be in completed_tasks"
        
        # Act: Complete the task (mock scheduler to prevent Windows task creation and document cleanup bug)
        with patch('core.service.get_scheduler_manager') as mock_get_scheduler:
            # Mock scheduler that doesn't have cleanup_task_reminders (simulating the bug)
            mock_scheduler = MagicMock()
            mock_scheduler.set_wake_timer = MagicMock()  # Prevent Windows task creation
            # Don't add cleanup_task_reminders to simulate the bug
            mock_get_scheduler.return_value = mock_scheduler
            
            result = complete_task(user_id, task_id)
        
        # Assert: Verify actual system changes
        assert result is True, "Task completion should succeed"
        
        # Verify task moved from active to completed
        active_after = load_active_tasks(user_id)
        assert not any(t['task_id'] == task_id for t in active_after), "Task should be removed from active_tasks"
        
        completed_after = load_completed_tasks(user_id)
        assert any(t['task_id'] == task_id for t in completed_after), "Task should be in completed_tasks"
        
        # Verify task has completion timestamp
        completed_task = next(t for t in completed_after if t['task_id'] == task_id)
        assert completed_task['completed'] is True, "Task should be marked completed"
        assert completed_task.get('completed_at') is not None, "Task should have completion timestamp"
        
        # Verify file persistence - reload from disk
        from core.config import get_user_data_dir
        user_dir = Path(get_user_data_dir(user_id))
        completed_file = user_dir / 'tasks' / 'completed_tasks.json'
        assert completed_file.exists(), "completed_tasks.json should exist"
        
        with open(completed_file, 'r') as f:
            file_data = json.load(f)
            assert any(t['task_id'] == task_id for t in file_data.get('completed_tasks', [])), \
                "Task should persist in completed_tasks.json file"
    
    @pytest.mark.integration
    @pytest.mark.tasks
    @pytest.mark.critical
    @pytest.mark.file_io
    def test_delete_task_verifies_actual_removal(self, test_data_dir):
        """
        Test: Deleting a task removes it from active_tasks.json and file system.
        
        Verifies actual system changes per testing guidelines.
        """
        # Arrange: Create user and task
        user_id = "test_user_delete_verify"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        task_id = create_task(
            user_id=user_id,
            title="Task to Delete",
            description="Test task"
        )
        
        assert task_id is not None, "Task should be created"
        
        # Verify task exists before deletion
        active_before = load_active_tasks(user_id)
        assert any(t['task_id'] == task_id for t in active_before), "Task should exist before deletion"
        
        # Act: Delete the task (mock scheduler to prevent Windows task creation and document cleanup bug)
        with patch('core.service.get_scheduler_manager') as mock_get_scheduler:
            # Mock scheduler that doesn't have cleanup_task_reminders (simulating the bug)
            mock_scheduler = MagicMock()
            mock_scheduler.set_wake_timer = MagicMock()  # Prevent Windows task creation
            # Don't add cleanup_task_reminders to simulate the bug
            mock_get_scheduler.return_value = mock_scheduler
            
            result = delete_task(user_id, task_id)
        
        # Assert: Verify actual system changes
        assert result is True, "Task deletion should succeed"
        
        # Verify task removed from active_tasks
        active_after = load_active_tasks(user_id)
        assert not any(t['task_id'] == task_id for t in active_after), "Task should be removed from active_tasks"
        
        # Verify task not in completed_tasks either
        completed_after = load_completed_tasks(user_id)
        assert not any(t['task_id'] == task_id for t in completed_after), "Task should not be in completed_tasks"
        
        # Verify task cannot be retrieved
        task = get_task_by_id(user_id, task_id)
        assert task is None, "Deleted task should not be retrievable"
        
        # Verify file persistence - reload from disk
        from core.config import get_user_data_dir
        user_dir = Path(get_user_data_dir(user_id))
        active_file = user_dir / 'tasks' / 'active_tasks.json'
        
        with open(active_file, 'r') as f:
            file_data = json.load(f)
            assert not any(t['task_id'] == task_id for t in file_data.get('tasks', [])), \
                "Task should not persist in active_tasks.json file"
    
    @pytest.mark.integration
    @pytest.mark.tasks
    @pytest.mark.file_io
    @pytest.mark.no_parallel
    def test_update_task_verifies_actual_changes_persist(self, test_data_dir):
        """
        Test: Updating a task modifies task data and persists to file system.
        
        Verifies actual system changes per testing guidelines.
        """
        # Arrange: Create user and task
        user_id = "test_user_update_verify"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        task_id = create_task(
            user_id=user_id,
            title="Original Title",
            description="Original description",
            priority="low"
        )
        
        assert task_id is not None, "Task should be created"
        
        # Verify original values
        task_before = get_task_by_id(user_id, task_id)
        assert task_before['title'] == "Original Title", "Task should have original title"
        assert task_before['priority'] == "low", "Task should have original priority"
        
        # Act: Update task (mock scheduler to prevent Windows task creation and document cleanup bug)
        updates = {
            'title': 'Updated Title',
            'description': 'Updated description',
            'priority': 'high'
        }
        
        with patch('core.service.get_scheduler_manager') as mock_get_scheduler:
            # Mock scheduler that doesn't have cleanup_task_reminders (simulating the bug)
            mock_scheduler = MagicMock()
            mock_scheduler.set_wake_timer = MagicMock()  # Prevent Windows task creation
            mock_scheduler.schedule_task_reminder_at_datetime = MagicMock(return_value=True)
            # Don't add cleanup_task_reminders to simulate the bug
            mock_get_scheduler.return_value = mock_scheduler
            
            result = update_task(user_id, task_id, updates)
        
        # Assert: Verify actual system changes
        assert result is True, "Task update should succeed"
        
        # Verify task updated in memory
        task_after = get_task_by_id(user_id, task_id)
        assert task_after['title'] == 'Updated Title', "Title should be updated"
        assert task_after['description'] == 'Updated description', "Description should be updated"
        assert task_after['priority'] == 'high', "Priority should be updated"
        assert task_after.get('last_updated') is not None, "Task should have last_updated timestamp"
        
        # Verify file persistence - reload from disk
        from core.config import get_user_data_dir
        user_dir = Path(get_user_data_dir(user_id))
        active_file = user_dir / 'tasks' / 'active_tasks.json'
        
        with open(active_file, 'r') as f:
            file_data = json.load(f)
            file_task = next((t for t in file_data.get('tasks', []) if t['task_id'] == task_id), None)
            assert file_task is not None, "Task should exist in file"
            assert file_task['title'] == 'Updated Title', "Title should persist in file"
            assert file_task['priority'] == 'high', "Priority should persist in file"
    
    @pytest.mark.integration
    @pytest.mark.tasks
    @pytest.mark.critical
    @pytest.mark.file_io
    def test_cleanup_task_reminders_method_exists(self):
        """
        Test: SchedulerManager has cleanup_task_reminders method.
        
        This test documents a CRITICAL BUG: the method doesn't exist.
        Verifies actual system state per testing guidelines.
        """
        # Arrange: Import scheduler components
        try:
            from communication.core.channel_orchestrator import CommunicationManager
            from core.scheduler import SchedulerManager
            
            # Act: Create scheduler manager
            comm_manager = CommunicationManager()
            scheduler = SchedulerManager(comm_manager)
            
            # Assert: Verify method exists (this will FAIL, documenting the bug)
            assert hasattr(scheduler, 'cleanup_task_reminders'), \
                "CRITICAL BUG: SchedulerManager.cleanup_task_reminders() method doesn't exist! " \
                "This causes silent failures when completing/deleting tasks with reminders. " \
                "Reminders accumulate forever because cleanup never happens."
            
            # Verify it's callable
            assert callable(getattr(scheduler, 'cleanup_task_reminders', None)), \
                "cleanup_task_reminders exists but is not callable"
                
        except ImportError as e:
            pytest.skip(f"Could not import required modules: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error checking scheduler: {e}")

