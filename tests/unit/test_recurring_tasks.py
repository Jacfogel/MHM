# test_recurring_tasks.py
"""
Test recurring tasks functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import tempfile
import os
import shutil

from tasks.task_management import (
    create_task, complete_task, load_active_tasks, load_completed_tasks,
    _create_next_recurring_task_instance, _calculate_next_due_date
)


class TestRecurringTasks:
    """Test recurring tasks functionality."""
    
    @pytest.fixture
    def temp_user_dir(self, test_path_factory):
        """Provide a per-test user directory under tests/data/tmp."""
        temp_dir = test_path_factory
        user_id = "test_user_recurring"
        user_dir = os.path.join(temp_dir, user_id)
        os.makedirs(user_dir)
        
        # Create tasks subdirectory
        tasks_dir = os.path.join(user_dir, 'tasks')
        os.makedirs(tasks_dir)
        
        # Create initial task files
        active_tasks_file = os.path.join(tasks_dir, 'active_tasks.json')
        completed_tasks_file = os.path.join(tasks_dir, 'completed_tasks.json')
        
        with open(active_tasks_file, 'w') as f:
            f.write('{"tasks": []}')
        with open(completed_tasks_file, 'w') as f:
            f.write('{"completed_tasks": []}')
        
        yield user_id, temp_dir
    
    @patch('tasks.task_management.get_user_data_dir')
    def test_create_recurring_task(self, mock_get_user_data_dir, temp_user_dir):
        """Test creating a recurring task."""
        user_id, temp_dir = temp_user_dir
        mock_get_user_data_dir.return_value = os.path.join(temp_dir, user_id)
        
        # Create a daily recurring task
        task_id = create_task(
            user_id=user_id,
            title="Take medication",
            description="Daily medication reminder",
            due_date="2025-01-15",
            priority="high",
            recurrence_pattern="daily",
            recurrence_interval=1,
            repeat_after_completion=True
        )
        
        assert task_id is not None
        
        # Load the task and verify recurring fields
        tasks = load_active_tasks(user_id)
        assert len(tasks) == 1
        
        task = tasks[0]
        assert task['title'] == "Take medication"
        assert task['recurrence_pattern'] == "daily"
        assert task['recurrence_interval'] == 1
        assert task['repeat_after_completion'] is True
        assert task['next_due_date'] == "2025-01-15"
    
    @patch('tasks.task_management.get_user_data_dir')
    def test_complete_recurring_task_creates_next_instance(self, mock_get_user_data_dir, temp_user_dir):
        """Test that completing a recurring task creates the next instance."""
        user_id, temp_dir = temp_user_dir
        mock_get_user_data_dir.return_value = os.path.join(temp_dir, user_id)
        
        # Create a daily recurring task
        task_id = create_task(
            user_id=user_id,
            title="Take medication",
            description="Daily medication reminder",
            due_date="2025-01-15",
            priority="high",
            recurrence_pattern="daily",
            recurrence_interval=1,
            repeat_after_completion=True
        )
        
        # Complete the task
        success = complete_task(user_id, task_id)
        assert success is True
        
        # Check that the original task is in completed tasks
        completed_tasks = load_completed_tasks(user_id)
        assert len(completed_tasks) == 1
        assert completed_tasks[0]['task_id'] == task_id
        assert completed_tasks[0]['completed'] is True
        
        # Check that a new task instance was created
        active_tasks = load_active_tasks(user_id)
        assert len(active_tasks) == 1
        
        new_task = active_tasks[0]
        assert new_task['task_id'] != task_id  # Different task ID
        assert new_task['title'] == "Take medication"  # Same title
        assert new_task['recurrence_pattern'] == "daily"  # Same recurrence pattern
        assert new_task['completed'] is False  # Not completed
    
    def test_calculate_next_due_date_daily(self):
        """Test calculating next due date for daily recurrence."""
        base_date = datetime(2025, 1, 15)
        
        # Daily recurrence
        next_date = _calculate_next_due_date(base_date, "daily", 1, True)
        expected_date = datetime(2025, 1, 16)
        assert next_date == expected_date
        
        # Every 2 days
        next_date = _calculate_next_due_date(base_date, "daily", 2, True)
        expected_date = datetime(2025, 1, 17)
        assert next_date == expected_date
    
    def test_calculate_next_due_date_weekly(self):
        """Test calculating next due date for weekly recurrence."""
        base_date = datetime(2025, 1, 15)  # Wednesday
        
        # Weekly recurrence
        next_date = _calculate_next_due_date(base_date, "weekly", 1, True)
        expected_date = datetime(2025, 1, 22)
        assert next_date == expected_date
        
        # Every 2 weeks
        next_date = _calculate_next_due_date(base_date, "weekly", 2, True)
        expected_date = datetime(2025, 1, 29)
        assert next_date == expected_date
    
    def test_calculate_next_due_date_monthly(self):
        """Test calculating next due date for monthly recurrence."""
        base_date = datetime(2025, 1, 15)
        
        # Monthly recurrence
        next_date = _calculate_next_due_date(base_date, "monthly", 1, True)
        expected_date = datetime(2025, 2, 15)
        assert next_date == expected_date
        
        # Every 2 months
        next_date = _calculate_next_due_date(base_date, "monthly", 2, True)
        expected_date = datetime(2025, 3, 15)
        assert next_date == expected_date
    
    def test_calculate_next_due_date_yearly(self):
        """Test calculating next due date for yearly recurrence."""
        base_date = datetime(2025, 1, 15)
        
        # Yearly recurrence
        next_date = _calculate_next_due_date(base_date, "yearly", 1, True)
        expected_date = datetime(2026, 1, 15)
        assert next_date == expected_date
        
        # Every 2 years
        next_date = _calculate_next_due_date(base_date, "yearly", 2, True)
        expected_date = datetime(2027, 1, 15)
        assert next_date == expected_date
    
    def test_calculate_next_due_date_invalid_pattern(self):
        """Test calculating next due date with invalid pattern."""
        base_date = datetime(2025, 1, 15)
        
        next_date = _calculate_next_due_date(base_date, "invalid_pattern", 1, True)
        assert next_date is None
    
    @patch('tasks.task_management.get_user_data_dir')
    def test_non_recurring_task_completion(self, mock_get_user_data_dir, temp_user_dir):
        """Test that completing a non-recurring task doesn't create a new instance."""
        user_id, temp_dir = temp_user_dir
        mock_get_user_data_dir.return_value = os.path.join(temp_dir, user_id)
        
        # Create a regular (non-recurring) task
        task_id = create_task(
            user_id=user_id,
            title="One-time task",
            description="This is a one-time task",
            due_date="2025-01-15",
            priority="medium"
        )
        
        # Complete the task
        success = complete_task(user_id, task_id)
        assert success is True
        
        # Check that the task is in completed tasks
        completed_tasks = load_completed_tasks(user_id)
        assert len(completed_tasks) == 1
        assert completed_tasks[0]['task_id'] == task_id
        
        # Check that no new task was created
        active_tasks = load_active_tasks(user_id)
        assert len(active_tasks) == 0
