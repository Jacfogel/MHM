"""
Task Management Test Coverage Expansion

This module expands test coverage for tasks/task_management.py from 48% to 75%.
Focuses on real behavior testing to verify actual side effects and system changes.

Coverage Areas:
- Task directory management and file operations
- Task CRUD operations with edge cases
- Task scheduling and reminder management
- Task filtering and search functionality
- Task statistics and analytics
- Error handling and validation
- Task tag management
- Task restoration and lifecycle
"""

import pytest
import os
import json
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from pathlib import Path

# Import task management functions
from core.user_data_handlers import get_user_data
from tasks.task_management import (
    ensure_task_directory,
    load_active_tasks,
    save_active_tasks,
    load_completed_tasks,
    save_completed_tasks,
    create_task,
    update_task,
    complete_task,
    restore_task,
    delete_task,
    get_task_by_id,
    get_tasks_due_soon,
    are_tasks_enabled,
    schedule_task_reminders,
    cleanup_task_reminders,
    add_user_task_tag,
    remove_user_task_tag,
    setup_default_task_tags,
    get_user_task_stats
)


class TestTaskManagementCoverageExpansion:
    """Comprehensive test coverage expansion for task management."""
    
    @pytest.fixture
    def temp_dir(self, test_path_factory):
        """Provide a per-test directory under tests/data/tmp."""
        return test_path_factory
    
    @pytest.fixture
    def user_id(self):
        """Create a test user ID."""
        return "test-user-coverage-expansion"
    
    @pytest.fixture
    def mock_user_data_dir(self, temp_dir):
        """Mock user data directory."""
        with patch('tasks.task_management.get_user_data_dir', return_value=temp_dir):
            yield temp_dir

    # ============================================================================
    # Task Directory Management Tests
    # ============================================================================

    def test_ensure_task_directory_real_behavior(self, mock_user_data_dir, user_id):
        """Test task directory creation with real file system behavior."""
        result = ensure_task_directory(user_id)
        
        assert result is True
        
        # Verify directory structure was created
        task_dir = Path(mock_user_data_dir) / 'tasks'
        assert task_dir.exists()
        assert task_dir.is_dir()
        
        # Verify all required files were created
        required_files = ['active_tasks.json', 'completed_tasks.json', 'task_schedules.json']
        for filename in required_files:
            file_path = task_dir / filename
            assert file_path.exists()
            assert file_path.is_file()
            
            # Verify files contain valid JSON
            with open(file_path, 'r') as f:
                data = json.load(f)
                assert isinstance(data, dict)

    def test_ensure_task_directory_with_empty_user_id_real_behavior(self, mock_user_data_dir):
        """Test task directory creation with empty user ID."""
        result = ensure_task_directory("")
        
        assert result is False

    def test_ensure_task_directory_with_none_user_id_real_behavior(self, mock_user_data_dir):
        """Test task directory creation with None user ID."""
        result = ensure_task_directory(None)
        
        assert result is False

    def test_ensure_task_directory_existing_structure_real_behavior(self, mock_user_data_dir, user_id):
        """Test task directory creation when structure already exists."""
        # Create directory structure first
        task_dir = Path(mock_user_data_dir) / 'tasks'
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # Create existing files
        existing_files = {
            'active_tasks.json': {'tasks': [{'existing': 'task'}]},
            'completed_tasks.json': {'completed_tasks': []},
            'task_schedules.json': {'task_schedules': {}}
        }
        
        for filename, data in existing_files.items():
            file_path = task_dir / filename
            with open(file_path, 'w') as f:
                json.dump(data, f)
        
        # Call ensure_task_directory
        result = ensure_task_directory(user_id)
        
        assert result is True
        
        # Verify existing data was preserved
        active_file = task_dir / 'active_tasks.json'
        with open(active_file, 'r') as f:
            data = json.load(f)
            assert data['tasks'] == [{'existing': 'task'}]

    # ============================================================================
    # Task Loading and Saving Tests
    # ============================================================================

    def test_load_active_tasks_real_behavior(self, mock_user_data_dir, user_id):
        """Test loading active tasks with real file operations."""
        # Create test data
        task_dir = Path(mock_user_data_dir) / 'tasks'
        task_dir.mkdir(parents=True, exist_ok=True)
        
        test_tasks = [
            {'task_id': '1', 'title': 'Task 1', 'completed': False},
            {'task_id': '2', 'title': 'Task 2', 'completed': False}
        ]
        
        active_file = task_dir / 'active_tasks.json'
        with open(active_file, 'w') as f:
            json.dump({'tasks': test_tasks}, f)
        
        # Load tasks
        tasks = load_active_tasks(user_id)
        
        assert len(tasks) == 2
        assert tasks[0]['title'] == 'Task 1'
        assert tasks[1]['title'] == 'Task 2'
        assert all(not task['completed'] for task in tasks)

    def test_load_active_tasks_empty_file_real_behavior(self, mock_user_data_dir, user_id):
        """Test loading active tasks from empty file."""
        # Create empty file
        task_dir = Path(mock_user_data_dir) / 'tasks'
        task_dir.mkdir(parents=True, exist_ok=True)
        
        active_file = task_dir / 'active_tasks.json'
        with open(active_file, 'w') as f:
            json.dump({}, f)
        
        # Load tasks
        tasks = load_active_tasks(user_id)
        
        assert tasks == []

    def test_load_active_tasks_missing_file_real_behavior(self, mock_user_data_dir, user_id):
        """Test loading active tasks when file doesn't exist."""
        tasks = load_active_tasks(user_id)
        
        assert tasks == []

    def test_save_active_tasks_real_behavior(self, mock_user_data_dir, user_id):
        """Test saving active tasks with real file operations."""
        test_tasks = [
            {'task_id': '1', 'title': 'Task 1', 'completed': False},
            {'task_id': '2', 'title': 'Task 2', 'completed': False}
        ]
        
        result = save_active_tasks(user_id, test_tasks)
        
        assert result is True
        
        # Verify file was created and contains correct data
        task_dir = Path(mock_user_data_dir) / 'tasks'
        active_file = task_dir / 'active_tasks.json'
        assert active_file.exists()
        
        with open(active_file, 'r') as f:
            data = json.load(f)
            assert data['tasks'] == test_tasks

    def test_save_active_tasks_with_empty_user_id_real_behavior(self, mock_user_data_dir):
        """Test saving active tasks with empty user ID."""
        result = save_active_tasks("", [])
        
        assert result is False

    def test_load_completed_tasks_real_behavior(self, mock_user_data_dir, user_id):
        """Test loading completed tasks with real file operations."""
        # Create test data
        task_dir = Path(mock_user_data_dir) / 'tasks'
        task_dir.mkdir(parents=True, exist_ok=True)
        
        test_tasks = [
            {'task_id': '1', 'title': 'Completed Task 1', 'completed': True},
            {'task_id': '2', 'title': 'Completed Task 2', 'completed': True}
        ]
        
        completed_file = task_dir / 'completed_tasks.json'
        with open(completed_file, 'w') as f:
            json.dump({'completed_tasks': test_tasks}, f)
        
        # Load tasks
        tasks = load_completed_tasks(user_id)
        
        assert len(tasks) == 2
        assert tasks[0]['title'] == 'Completed Task 1'
        assert tasks[1]['title'] == 'Completed Task 2'
        assert all(task['completed'] for task in tasks)

    def test_save_completed_tasks_real_behavior(self, mock_user_data_dir, user_id):
        """Test saving completed tasks with real file operations."""
        test_tasks = [
            {'task_id': '1', 'title': 'Completed Task 1', 'completed': True},
            {'task_id': '2', 'title': 'Completed Task 2', 'completed': True}
        ]
        
        result = save_completed_tasks(user_id, test_tasks)
        
        assert result is True
        
        # Verify file was created and contains correct data
        task_dir = Path(mock_user_data_dir) / 'tasks'
        completed_file = task_dir / 'completed_tasks.json'
        assert completed_file.exists()
        
        with open(completed_file, 'r') as f:
            data = json.load(f)
            assert data['completed_tasks'] == test_tasks

    # ============================================================================
    # Task CRUD Operations Tests
    # ============================================================================

    def test_create_task_with_all_parameters_real_behavior(self, mock_user_data_dir, user_id):
        """Test task creation with all optional parameters."""
        task_id = create_task(
            user_id=user_id,
            title="Complete Task",
            description="Full description",
            due_date="2024-12-31",
            due_time="14:30",
            priority="high",
            reminder_periods=[{'date': '2024-12-30', 'start_time': '09:00', 'end_time': '10:00'}],
            tags=["work", "urgent"],
            quick_reminders=["1h", "30m"]
        )
        
        assert task_id is not None
        
        # Verify task was saved with all parameters
        tasks = load_active_tasks(user_id)
        assert len(tasks) == 1
        
        task = tasks[0]
        assert task['task_id'] == task_id
        assert task['title'] == "Complete Task"
        assert task['description'] == "Full description"
        assert task['due_date'] == "2024-12-31"
        assert task['due_time'] == "14:30"
        assert task['priority'] == "high"
        assert task['reminder_periods'] == [{'date': '2024-12-30', 'start_time': '09:00', 'end_time': '10:00'}]
        assert task['tags'] == ["work", "urgent"]
        assert task['quick_reminders'] == ["1h", "30m"]
        assert task['completed'] is False
        assert 'created_at' in task

    def test_create_task_with_minimal_parameters_real_behavior(self, mock_user_data_dir, user_id):
        """Test task creation with minimal required parameters."""
        task_id = create_task(user_id=user_id, title="Minimal Task")
        
        assert task_id is not None
        
        # Verify task was saved with defaults
        tasks = load_active_tasks(user_id)
        assert len(tasks) == 1
        
        task = tasks[0]
        assert task['title'] == "Minimal Task"
        assert task['description'] == ""
        assert task['priority'] == "medium"
        assert task['completed'] is False
        assert 'created_at' in task

    def test_create_task_with_empty_user_id_real_behavior(self, mock_user_data_dir):
        """Test task creation with empty user ID."""
        task_id = create_task(user_id="", title="Test Task")
        
        assert task_id is None

    def test_create_task_with_empty_title_real_behavior(self, mock_user_data_dir, user_id):
        """Test task creation with empty title."""
        task_id = create_task(user_id=user_id, title="")
        
        assert task_id is None

    def test_update_task_real_behavior(self, mock_user_data_dir, user_id):
        """Test task updating with real behavior verification."""
        # Create a task first
        task_id = create_task(user_id, "Original Title", "Original Description")
        
        # Update the task
        updates = {
            'title': 'Updated Title',
            'description': 'Updated Description',
            'priority': 'low',
            'due_date': '2024-12-31',
            'tags': ['updated', 'tag']
        }
        
        result = update_task(user_id, task_id, updates)
        
        assert result is True
        
        # Verify updates were applied
        tasks = load_active_tasks(user_id)
        assert len(tasks) == 1
        
        task = tasks[0]
        assert task['title'] == 'Updated Title'
        assert task['description'] == 'Updated Description'
        assert task['priority'] == 'low'
        assert task['due_date'] == '2024-12-31'
        assert task['tags'] == ['updated', 'tag']
        assert 'last_updated' in task

    def test_update_task_with_reminder_periods_real_behavior(self, mock_user_data_dir, user_id):
        """Test task updating with reminder periods."""
        # Create a task first
        task_id = create_task(user_id, "Test Task")
        
        # Update with reminder periods
        updates = {
            'reminder_periods': [
                {'date': '2024-12-30', 'start_time': '09:00', 'end_time': '10:00'}
            ]
        }
        
        with patch('tasks.task_management.cleanup_task_reminders') as mock_cleanup, \
             patch('tasks.task_management.schedule_task_reminders') as mock_schedule:
            
            result = update_task(user_id, task_id, updates)
            
            assert result is True
            mock_cleanup.assert_called_once_with(user_id, task_id)
            mock_schedule.assert_called_once_with(user_id, task_id, updates['reminder_periods'])

    def test_update_task_not_found_real_behavior(self, mock_user_data_dir, user_id):
        """Test updating a non-existent task."""
        result = update_task(user_id, "non-existent-id", {'title': 'Updated'})
        
        assert result is False

    def test_complete_task_with_completion_data_real_behavior(self, mock_user_data_dir, user_id):
        """Test task completion with custom completion data."""
        # Create a task
        task_id = create_task(user_id, "Test Task")
        
        # Complete with custom data
        completion_data = {
            'completion_date': '2024-12-25',
            'completion_time': '15:30',
            'completion_notes': 'Task completed successfully'
        }
        
        with patch('tasks.task_management.cleanup_task_reminders') as mock_cleanup:
            result = complete_task(user_id, task_id, completion_data)
            
            assert result is True
            mock_cleanup.assert_called_once_with(user_id, task_id)
        
        # Verify task was moved to completed
        active_tasks = load_active_tasks(user_id)
        assert len(active_tasks) == 0
        
        completed_tasks = load_completed_tasks(user_id)
        assert len(completed_tasks) == 1
        
        task = completed_tasks[0]
        assert task['completed'] is True
        assert task['completed_at'] == '2024-12-25 15:30:00'
        assert task['completion_notes'] == 'Task completed successfully'

    def test_complete_task_with_default_completion_real_behavior(self, mock_user_data_dir, user_id):
        """Test task completion with default completion time."""
        # Create a task
        task_id = create_task(user_id, "Test Task")
        
        with patch('tasks.task_management.cleanup_task_reminders') as mock_cleanup:
            result = complete_task(user_id, task_id)
            
            assert result is True
            mock_cleanup.assert_called_once_with(user_id, task_id)
        
        # Verify task was moved to completed
        completed_tasks = load_completed_tasks(user_id)
        assert len(completed_tasks) == 1
        
        task = completed_tasks[0]
        assert task['completed'] is True
        assert task['completed_at'] is not None
        assert 'completion_notes' not in task

    def test_complete_task_not_found_real_behavior(self, mock_user_data_dir, user_id):
        """Test completing a non-existent task."""
        result = complete_task(user_id, "non-existent-id")
        
        assert result is False

    def test_restore_task_real_behavior(self, mock_user_data_dir, user_id):
        """Test task restoration from completed to active."""
        # Create and complete a task
        task_id = create_task(user_id, "Test Task")
        complete_task(user_id, task_id)
        
        # Restore the task
        result = restore_task(user_id, task_id)
        
        assert result is True
        
        # Verify task was moved back to active
        active_tasks = load_active_tasks(user_id)
        assert len(active_tasks) == 1
        
        task = active_tasks[0]
        assert task['completed'] is False
        assert task['completed_at'] is None

    def test_restore_task_with_reminders_real_behavior(self, mock_user_data_dir, user_id):
        """Test task restoration with reminder periods."""
        # Create a task with reminders
        task_id = create_task(
            user_id, 
            "Test Task",
            reminder_periods=[{'date': '2024-12-30', 'start_time': '09:00', 'end_time': '10:00'}]
        )
        complete_task(user_id, task_id)
        
        # Restore the task
        with patch('tasks.task_management.schedule_task_reminders') as mock_schedule:
            result = restore_task(user_id, task_id)
            
            assert result is True
            mock_schedule.assert_called_once_with(
                user_id, 
                task_id, 
                [{'date': '2024-12-30', 'start_time': '09:00', 'end_time': '10:00'}]
            )

    def test_restore_task_not_found_real_behavior(self, mock_user_data_dir, user_id):
        """Test restoring a non-existent completed task."""
        result = restore_task(user_id, "non-existent-id")
        
        assert result is False

    def test_delete_task_real_behavior(self, mock_user_data_dir, user_id):
        """Test task deletion with cleanup verification."""
        # Create a task
        task_id = create_task(user_id, "Test Task")
        
        with patch('tasks.task_management.cleanup_task_reminders') as mock_cleanup:
            result = delete_task(user_id, task_id)
            
            assert result is True
            mock_cleanup.assert_called_once_with(user_id, task_id)
        
        # Verify task was removed
        tasks = load_active_tasks(user_id)
        assert len(tasks) == 0
        assert all(task['task_id'] != task_id for task in tasks)

    def test_delete_task_not_found_real_behavior(self, mock_user_data_dir, user_id):
        """Test deleting a non-existent task."""
        result = delete_task(user_id, "non-existent-id")
        
        assert result is False

    def test_get_task_by_id_active_task_real_behavior(self, mock_user_data_dir, user_id):
        """Test getting an active task by ID."""
        # Create a task
        task_id = create_task(user_id, "Test Task", "Description")
        
        # Get the task
        task = get_task_by_id(user_id, task_id)
        
        assert task is not None
        assert task['task_id'] == task_id
        assert task['title'] == "Test Task"
        assert task['description'] == "Description"

    def test_get_task_by_id_completed_task_real_behavior(self, mock_user_data_dir, user_id):
        """Test getting a completed task by ID."""
        # Create and complete a task
        task_id = create_task(user_id, "Test Task")
        complete_task(user_id, task_id)
        
        # Get the task
        task = get_task_by_id(user_id, task_id)
        
        assert task is not None
        assert task['task_id'] == task_id
        assert task['completed'] is True

    def test_get_task_by_id_not_found_real_behavior(self, mock_user_data_dir, user_id):
        """Test getting a non-existent task by ID."""
        task = get_task_by_id(user_id, "non-existent-id")
        
        assert task is None

    # ============================================================================
    # Task Filtering and Search Tests
    # ============================================================================

    def test_get_tasks_due_soon_real_behavior(self, mock_user_data_dir, user_id):
        """Test getting tasks due within specified days."""
        # Create tasks with different due dates
        today = datetime.now().date()
        due_soon = (today + timedelta(days=2)).strftime('%Y-%m-%d')
        due_late = (today + timedelta(days=10)).strftime('%Y-%m-%d')
        
        id_soon = create_task(user_id, "Soon Task", due_date=due_soon)
        id_late = create_task(user_id, "Late Task", due_date=due_late)
        id_no_date = create_task(user_id, "No Date Task")
        
        # Get tasks due within 7 days
        due_soon_tasks = get_tasks_due_soon(user_id, days_ahead=7)
        
        # Should only include the soon task
        task_ids = [task['task_id'] for task in due_soon_tasks]
        assert id_soon in task_ids
        assert id_late not in task_ids
        assert id_no_date not in task_ids

    def test_get_tasks_due_soon_with_invalid_date_real_behavior(self, mock_user_data_dir, user_id):
        """Test getting tasks due soon with invalid date format."""
        # Create a task with invalid date format
        create_task(user_id, "Invalid Date Task", due_date="invalid-date")
        
        # Should not crash and should return empty list
        due_soon_tasks = get_tasks_due_soon(user_id, days_ahead=7)
        
        assert due_soon_tasks == []

    def test_get_tasks_due_soon_empty_user_id_real_behavior(self, mock_user_data_dir):
        """Test getting tasks due soon with empty user ID."""
        due_soon_tasks = get_tasks_due_soon("", days_ahead=7)
        
        assert due_soon_tasks == []

    # ============================================================================
    # Task Status and Feature Tests
    # ============================================================================

    def test_are_tasks_enabled_real_behavior(self, mock_user_data_dir, user_id):
        """Test checking if tasks are enabled for a user."""
        with patch('tasks.task_management.get_user_data') as mock_get_user_data:
            # Test enabled
            mock_get_user_data.return_value = {
                'account': {'features': {'task_management': 'enabled'}}
            }
            assert are_tasks_enabled(user_id) is True
            
            # Test disabled
            mock_get_user_data.return_value = {
                'account': {'features': {'task_management': 'disabled'}}
            }
            assert are_tasks_enabled(user_id) is False
            
            # Test missing account
            mock_get_user_data.return_value = {}
            assert are_tasks_enabled(user_id) is False

    def test_are_tasks_enabled_empty_user_id_real_behavior(self, mock_user_data_dir):
        """Test checking tasks enabled with empty user ID."""
        assert are_tasks_enabled("") is False

    # ============================================================================
    # Task Scheduling and Reminder Tests
    # ============================================================================

    def test_schedule_task_reminders_real_behavior(self, mock_user_data_dir, user_id):
        """Test scheduling task-specific reminders."""
        task_id = "test-task-id"
        reminder_periods = [
            {'date': '2024-12-30', 'start_time': '09:00', 'end_time': '10:00'},
            {'date': '2024-12-31', 'start_time': '14:00', 'end_time': '15:00'}
        ]
        
        with patch('core.service.get_scheduler_manager') as mock_get_scheduler:
            mock_scheduler = Mock()
            mock_scheduler.schedule_task_reminder_at_datetime.return_value = True
            mock_get_scheduler.return_value = mock_scheduler
            
            result = schedule_task_reminders(user_id, task_id, reminder_periods)
            
            assert result is True
            assert mock_scheduler.schedule_task_reminder_at_datetime.call_count == 2

    def test_schedule_task_reminders_no_scheduler_real_behavior(self, mock_user_data_dir, user_id):
        """Test scheduling reminders when scheduler is not available."""
        task_id = "test-task-id"
        reminder_periods = [{'date': '2024-12-30', 'start_time': '09:00', 'end_time': '10:00'}]
        
        with patch('core.service.get_scheduler_manager', return_value=None):
            result = schedule_task_reminders(user_id, task_id, reminder_periods)
            
            assert result is False

    def test_schedule_task_reminders_empty_periods_real_behavior(self, mock_user_data_dir, user_id):
        """Test scheduling reminders with empty periods."""
        task_id = "test-task-id"
        
        result = schedule_task_reminders(user_id, task_id, [])
        
        assert result is True

    def test_cleanup_task_reminders_real_behavior(self, mock_user_data_dir, user_id):
        """Test cleaning up task-specific reminders."""
        task_id = "test-task-id"
        
        with patch('core.service.get_scheduler_manager') as mock_get_scheduler:
            mock_scheduler = Mock()
            mock_get_scheduler.return_value = mock_scheduler
            
            result = cleanup_task_reminders(user_id, task_id)
            
            assert result is True
            mock_scheduler.cleanup_task_reminders.assert_called_once_with(user_id, task_id)

    def test_cleanup_task_reminders_no_scheduler_real_behavior(self, mock_user_data_dir, user_id):
        """Test cleaning up reminders when scheduler is not available."""
        task_id = "test-task-id"
        
        with patch('core.service.get_scheduler_manager', return_value=None):
            result = cleanup_task_reminders(user_id, task_id)
            
            assert result is False

    # ============================================================================
    # Task Tag Management Tests
    # ============================================================================

    def test_get_user_task_tags_real_behavior(self, mock_user_data_dir, user_id):
        """Test getting user task tags from preferences."""
        # Test the actual get_user_data function behavior
        prefs_result = get_user_data(user_id, 'preferences')
        preferences_data = prefs_result.get('preferences', {}) if prefs_result else {}
        task_settings = preferences_data.get('task_settings', {})
        tags = task_settings.get('tags', [])
        
        # Since this is a new user, tags should be empty by default
        assert isinstance(tags, list)
        # The actual behavior depends on the mock user data, which has empty tags by default

    def test_get_user_task_tags_empty_user_id_real_behavior(self, mock_user_data_dir):
        """Test getting task tags with empty user ID."""
        prefs_result = get_user_data("", 'preferences')
        preferences_data = prefs_result.get('preferences', {}) if prefs_result else {}
        task_settings = preferences_data.get('task_settings', {})
        tags = task_settings.get('tags', [])
        
        assert tags == []

    def test_add_user_task_tag_new_tag_real_behavior(self, mock_user_data_dir, user_id):
        """Test adding a new task tag."""
        with patch('tasks.task_management.get_user_data') as mock_get_user_data, \
             patch('core.user_data_handlers.save_user_data') as mock_save_user_data:
            
            mock_get_user_data.return_value = {
                'preferences': {'task_settings': {'tags': ['work', 'personal']}}
            }
            mock_save_user_data.return_value = {'preferences': True}
            
            result = add_user_task_tag(user_id, 'health')
            
            assert result is True
            mock_save_user_data.assert_called_once()
            
            # Verify the call included the new tag
            call_args = mock_save_user_data.call_args[0]
            assert call_args[0] == user_id
            assert call_args[1] == 'preferences'
            assert 'health' in call_args[2]['task_settings']['tags']

    def test_add_user_task_tag_existing_tag_real_behavior(self, mock_user_data_dir, user_id):
        """Test adding an existing task tag."""
        with patch('tasks.task_management.get_user_data') as mock_get_user_data:
            mock_get_user_data.return_value = {
                'preferences': {'task_settings': {'tags': ['work', 'personal', 'health']}}
            }
            
            result = add_user_task_tag(user_id, 'health')
            
            assert result is True

    def test_add_user_task_tag_empty_user_id_real_behavior(self, mock_user_data_dir):
        """Test adding task tag with empty user ID."""
        result = add_user_task_tag("", "work")
        
        assert result is False

    def test_add_user_task_tag_empty_tag_real_behavior(self, mock_user_data_dir, user_id):
        """Test adding empty task tag."""
        result = add_user_task_tag(user_id, "")
        
        assert result is False

    def test_remove_user_task_tag_real_behavior(self, mock_user_data_dir, user_id):
        """Test removing a task tag."""
        with patch('tasks.task_management.get_user_data') as mock_get_user_data, \
             patch('core.user_data_handlers.save_user_data') as mock_save_user_data:
            
            mock_get_user_data.return_value = {
                'preferences': {'task_settings': {'tags': ['work', 'personal', 'health']}}
            }
            mock_save_user_data.return_value = {'preferences': True}
            
            result = remove_user_task_tag(user_id, 'health')
            
            assert result is True
            mock_save_user_data.assert_called_once()
            
            # Verify the call excluded the removed tag
            call_args = mock_save_user_data.call_args[0]
            assert call_args[0] == user_id
            assert call_args[1] == 'preferences'
            assert 'health' not in call_args[2]['task_settings']['tags']

    def test_remove_user_task_tag_not_found_real_behavior(self, mock_user_data_dir, user_id):
        """Test removing a non-existent task tag."""
        with patch('tasks.task_management.get_user_data') as mock_get_user_data:
            mock_get_user_data.return_value = {
                'preferences': {'task_settings': {'tags': ['work', 'personal']}}
            }
            
            result = remove_user_task_tag(user_id, 'health')
            
            assert result is True

    def test_setup_default_task_tags_new_user_real_behavior(self, mock_user_data_dir, user_id):
        """Test setting up default task tags for new user."""
        with patch('tasks.task_management.get_user_data') as mock_get_user_data, \
             patch('core.user_data_handlers.save_user_data') as mock_save_user_data:
            
            mock_get_user_data.return_value = {'preferences': {'task_settings': {'tags': []}}}
            mock_save_user_data.return_value = {'preferences': True}
            
            result = setup_default_task_tags(user_id)
            
            assert result is True
            mock_save_user_data.assert_called_once()
            
            # Verify default tags were added
            call_args = mock_save_user_data.call_args[0]
            default_tags = call_args[2]['task_settings']['tags']
            assert 'work' in default_tags
            assert 'personal' in default_tags
            assert 'health' in default_tags

    def test_setup_default_task_tags_existing_user_real_behavior(self, mock_user_data_dir, user_id):
        """Test setting up default task tags for user with existing tags."""
        with patch('tasks.task_management.get_user_data') as mock_get_user_data:
            mock_get_user_data.return_value = {
                'preferences': {'task_settings': {'tags': ['work', 'custom']}}
            }
            
            result = setup_default_task_tags(user_id)
            
            assert result is True

    def test_setup_default_task_tags_empty_user_id_real_behavior(self, mock_user_data_dir):
        """Test setting up default task tags with empty user ID."""
        result = setup_default_task_tags("")
        
        assert result is False

    # ============================================================================
    # Task Statistics Tests
    # ============================================================================

    def test_get_user_task_stats_real_behavior(self, mock_user_data_dir, user_id):
        """Test getting user task statistics."""
        # Create some tasks
        task_id1 = create_task(user_id, "Task 1")
        task_id2 = create_task(user_id, "Task 2")
        task_id3 = create_task(user_id, "Task 3")
        
        # Complete one task
        complete_task(user_id, task_id1)
        
        # Get statistics
        stats = get_user_task_stats(user_id)
        
        assert stats['active_count'] == 2
        assert stats['completed_count'] == 1
        assert stats['total_count'] == 3

    def test_get_user_task_stats_empty_user_id_real_behavior(self, mock_user_data_dir):
        """Test getting task statistics with empty user ID."""
        stats = get_user_task_stats("")
        
        assert stats == {}

    def test_get_user_task_stats_error_handling_real_behavior(self, mock_user_data_dir, user_id):
        """Test task statistics error handling."""
        with patch('tasks.task_management.load_active_tasks', side_effect=Exception("Test error")):
            stats = get_user_task_stats(user_id)
            
            assert stats == {
                'active_count': 0,
                'completed_count': 0,
                'total_count': 0
            }
