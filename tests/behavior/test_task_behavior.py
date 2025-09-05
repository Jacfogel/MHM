"""
Tests for the task management module - Task CRUD operations and scheduling.

This module tests:
- Task creation, reading, updating, and deletion
- Task scheduling and reminders
- Task priority and status management
- Task file operations
- Task validation and formatting
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import sys
import json
from datetime import datetime, date, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the actual functions from task_management
from tasks.task_management import (
    ensure_task_directory,
    load_active_tasks,
    save_active_tasks,
    load_completed_tasks,
    save_completed_tasks,
    create_task,
    update_task,
    complete_task,
    delete_task,
    get_task_by_id,
    get_tasks_due_soon,
    are_tasks_enabled,
    get_user_task_stats,
    TaskManagementError
)
from core.config import get_user_data_dir

class TestTaskManagement:
    """Test cases for task management functions."""
    
    @pytest.fixture
    def temp_dir(self, test_path_factory):
        """Provide a per-test directory under tests/data/tmp."""
        return test_path_factory
    
    @pytest.fixture
    def user_id(self):
        """Create a test user ID."""
        return "test-user-123"
    
    @pytest.mark.tasks
    @patch('tasks.task_management.get_user_data_dir')
    def test_ensure_task_directory(self, mock_get_user_dir, user_id, temp_dir):
        """Test task directory creation."""
        mock_get_user_dir.return_value = temp_dir
        
        result = ensure_task_directory(user_id)
        
        assert result is True
        task_dir = os.path.join(temp_dir, 'tasks')
        assert os.path.exists(task_dir)
        assert os.path.exists(os.path.join(task_dir, 'active_tasks.json'))
        assert os.path.exists(os.path.join(task_dir, 'completed_tasks.json'))
        assert os.path.exists(os.path.join(task_dir, 'task_schedules.json'))
    
    @pytest.mark.tasks
    @pytest.mark.critical
    @patch('tasks.task_management.get_user_data_dir')
    def test_load_active_tasks(self, mock_get_user_dir, user_id, temp_dir):
        """Test loading active tasks."""
        mock_get_user_dir.return_value = temp_dir
        
        # Create test task file
        task_dir = os.path.join(temp_dir, 'tasks')
        os.makedirs(task_dir, exist_ok=True)
        test_tasks = {
            'tasks': [
                {'task_id': '1', 'title': 'Test Task 1', 'completed': False},
                {'task_id': '2', 'title': 'Test Task 2', 'completed': False}
            ]
        }
        with open(os.path.join(task_dir, 'active_tasks.json'), 'w') as f:
            json.dump(test_tasks, f)
        
        tasks = load_active_tasks(user_id)
        
        assert len(tasks) == 2
        assert tasks[0]['title'] == 'Test Task 1'
        assert tasks[1]['title'] == 'Test Task 2'
    
    @pytest.mark.tasks
    @pytest.mark.slow
    @patch('tasks.task_management.get_user_data_dir')
    def test_save_active_tasks(self, mock_get_user_dir, user_id, temp_dir):
        """Test saving active tasks."""
        mock_get_user_dir.return_value = temp_dir
        
        test_tasks = [
            {'task_id': '1', 'title': 'Test Task 1', 'completed': False},
            {'task_id': '2', 'title': 'Test Task 2', 'completed': False}
        ]
        
        result = save_active_tasks(user_id, test_tasks)
        
        assert result is True
        
        # Verify file was created
        task_dir = os.path.join(temp_dir, 'tasks')
        task_file = os.path.join(task_dir, 'active_tasks.json')
        assert os.path.exists(task_file)
        
        # Verify content
        with open(task_file, 'r') as f:
            saved_data = json.load(f)
        assert saved_data['tasks'] == test_tasks
    
    @pytest.mark.tasks
    @pytest.mark.regression
    @patch('tasks.task_management.get_user_data_dir')
    def test_create_task(self, mock_get_user_dir, temp_dir):
        """Test task creation with file verification."""
        user_id = "test-user-create-task"
        mock_get_user_dir.return_value = temp_dir
        
        task_id = create_task(
            user_id=user_id,
            title="Test Task",
            description="Test Description",
            priority="high",
            tags=["work"]
        )
        
        assert task_id is not None
        
        # Verify task was saved
        tasks = load_active_tasks(user_id)
        assert len(tasks) == 1
        assert tasks[0]['title'] == "Test Task"
        assert tasks[0]['description'] == "Test Description"
        assert tasks[0]['priority'] == "high"
        assert tasks[0]['tags'] == ["work"]
        assert tasks[0]['completed'] is False
        # Verify file content
        task_dir = os.path.join(temp_dir, 'tasks')
        task_file = os.path.join(task_dir, 'active_tasks.json')
        assert os.path.exists(task_file)
        with open(task_file, 'r') as f:
            data = json.load(f)
        assert any(t['task_id'] == task_id for t in data['tasks'])

    @pytest.mark.tasks
    @pytest.mark.regression
    @patch('tasks.task_management.get_user_data_dir')
    def test_update_task(self, mock_get_user_dir, temp_dir):
        """Test task updating with file verification."""
        user_id = "test-user-update-task"
        mock_get_user_dir.return_value = temp_dir
        # Create a task first
        task_id = create_task(user_id, "Original Title", "Original Description")
        # Update the task
        updates = {
            'title': 'Updated Title',
            'description': 'Updated Description',
            'priority': 'low'
        }
        result = update_task(user_id, task_id, updates)
        assert result is True
        # Verify updates
        tasks = load_active_tasks(user_id)
        assert len(tasks) == 1
        assert tasks[0]['title'] == 'Updated Title'
        assert tasks[0]['description'] == 'Updated Description'
        assert tasks[0]['priority'] == 'low'
        # Verify file content
        task_dir = os.path.join(temp_dir, 'tasks')
        task_file = os.path.join(task_dir, 'active_tasks.json')
        with open(task_file, 'r') as f:
            data = json.load(f)
        assert any(t['task_id'] == task_id and t['title'] == 'Updated Title' for t in data['tasks'])

    @pytest.mark.tasks
    @pytest.mark.critical
    @patch('tasks.task_management.get_user_data_dir')
    def test_complete_task(self, mock_get_user_dir, temp_dir):
        """Test task completion with file and side effect verification."""
        user_id = "test-user-complete-task"
        mock_get_user_dir.return_value = temp_dir
        
        # Create a task
        task_id = create_task(user_id, "Test Task")
        
        # Complete the task
        result = complete_task(user_id, task_id)
        
        assert result is True
        
        # Verify task was moved to completed
        active_tasks = load_active_tasks(user_id)
        assert len(active_tasks) == 0
        completed_tasks = load_completed_tasks(user_id)
        assert len(completed_tasks) == 1
        assert completed_tasks[0]['completed'] is True
        assert completed_tasks[0]['completed_at'] is not None
        # Verify file content
        task_dir = os.path.join(temp_dir, 'tasks')
        completed_file = os.path.join(task_dir, 'completed_tasks.json')
        assert os.path.exists(completed_file)
        with open(completed_file, 'r') as f:
            data = json.load(f)
        assert any(t['task_id'] == task_id and t['completed'] for t in data['completed_tasks'])
    
    @pytest.mark.tasks
    @pytest.mark.regression
    @patch('tasks.task_management.get_user_data_dir')
    def test_delete_task(self, mock_get_user_dir, temp_dir):
        """Test task deletion with file verification."""
        user_id = "test-user-delete-task"
        mock_get_user_dir.return_value = temp_dir
        # Create a task
        task_id = create_task(user_id, "Test Task")
        # Delete the task
        result = delete_task(user_id, task_id)
        assert result is True
        # Verify task is removed
        tasks = load_active_tasks(user_id)
        assert all(t['task_id'] != task_id for t in tasks)
        # Verify file content
        task_dir = os.path.join(temp_dir, 'tasks')
        task_file = os.path.join(task_dir, 'active_tasks.json')
        with open(task_file, 'r') as f:
            data = json.load(f)
        assert all(t['task_id'] != task_id for t in data['tasks'])

    @pytest.mark.tasks
    @pytest.mark.regression
    @patch('tasks.task_management.get_user_data_dir')
    def test_get_task_by_id(self, mock_get_user_dir, temp_dir):
        """Test getting a task by ID with file verification."""
        user_id = "test-user-get-task"
        mock_get_user_dir.return_value = temp_dir
        # Create a task
        task_id = create_task(user_id, "Test Task", "Desc")
        # Get the task by ID
        task = get_task_by_id(user_id, task_id)
        assert task is not None
        assert task['task_id'] == task_id
        assert task['title'] == "Test Task"
        # Verify file content
        task_dir = os.path.join(temp_dir, 'tasks')
        task_file = os.path.join(task_dir, 'active_tasks.json')
        with open(task_file, 'r') as f:
            data = json.load(f)
        assert any(t['task_id'] == task_id for t in data['tasks'])

    @pytest.mark.tasks
    @pytest.mark.slow
    @patch('tasks.task_management.get_user_data_dir')
    def test_get_tasks_due_soon(self, mock_get_user_dir, temp_dir):
        """Test getting tasks due soon with file verification."""
        user_id = "test-user-due-soon"
        mock_get_user_dir.return_value = temp_dir
        # Create tasks with due dates
        today = datetime.now().date()
        due_soon = (today + timedelta(days=2)).strftime('%Y-%m-%d')
        due_late = (today + timedelta(days=10)).strftime('%Y-%m-%d')
        id_soon = create_task(user_id, "Soon Task", due_date=due_soon)
        id_late = create_task(user_id, "Late Task", due_date=due_late)
        # Get tasks due soon (within 7 days)
        due_soon_tasks = get_tasks_due_soon(user_id, days_ahead=7)
        assert any(t['task_id'] == id_soon for t in due_soon_tasks)
        assert all(t['task_id'] != id_late for t in due_soon_tasks)
        # Verify file content
        task_dir = os.path.join(temp_dir, 'tasks')
        task_file = os.path.join(task_dir, 'active_tasks.json')
        with open(task_file, 'r') as f:
            data = json.load(f)
        assert any(t['task_id'] == id_soon for t in data['tasks'])
        assert any(t['task_id'] == id_late for t in data['tasks'])

    @pytest.mark.tasks
    @pytest.mark.regression
    @patch('tasks.task_management.get_user_data')
    def test_are_tasks_enabled(self, mock_get_user_data):
        """Test checking if tasks are enabled with mock user data."""
        user_id = "test-user-tasks-enabled"
        # Simulate user data with tasks enabled
        mock_get_user_data.return_value = {'account': {'features': {'task_management': 'enabled'}}}
        assert are_tasks_enabled(user_id) is True
        # Simulate user data with tasks disabled
        mock_get_user_data.return_value = {'account': {'features': {'task_management': 'disabled'}}}
        assert are_tasks_enabled(user_id) is False
        # Simulate missing account
        mock_get_user_data.return_value = {}
        assert are_tasks_enabled(user_id) is False

    @pytest.mark.tasks
    @pytest.mark.regression
    @patch('tasks.task_management.get_user_data_dir')
    def test_get_user_task_stats(self, mock_get_user_dir, temp_dir):
        """Test getting user task statistics with file verification."""
        user_id = "test-user-task-stats"
        mock_get_user_dir.return_value = temp_dir
        # Create tasks
        id1 = create_task(user_id, "Task 1")
        id2 = create_task(user_id, "Task 2")
        complete_task(user_id, id1)
        # Get stats
        stats = get_user_task_stats(user_id)
        assert stats['active_count'] == 1
        assert stats['completed_count'] == 1
        # Verify file content
        task_dir = os.path.join(temp_dir, 'tasks')
        active_file = os.path.join(task_dir, 'active_tasks.json')
        completed_file = os.path.join(task_dir, 'completed_tasks.json')
        with open(active_file, 'r') as f:
            active_data = json.load(f)
        with open(completed_file, 'r') as f:
            completed_data = json.load(f)
        assert any(t['task_id'] == id2 for t in active_data['tasks'])
        assert any(t['task_id'] == id1 for t in completed_data['completed_tasks']) 