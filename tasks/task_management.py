# task_management.py
"""
Task management utilities for MHM.
Contains functions for task CRUD operations, task scheduling, and task data management.
"""

import os
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from core.logger import get_logger
from core.file_operations import load_json_data, save_json_data, determine_file_path
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)
from core.config import get_user_data_dir
from core.user_data_handlers import get_user_data

logger = get_logger(__name__)

class TaskManagementError(Exception):
    """Custom exception for task management errors."""
    pass

@handle_errors("creating task directory structure")
def ensure_task_directory(user_id: str) -> bool:
    """Ensure the task directory structure exists for a user."""
    try:
        if not user_id:
            logger.error("User ID is required for task directory creation")
            return False
            
        # Get the user directory path using the correct function
        user_dir = get_user_data_dir(user_id)
        task_dir = os.path.join(user_dir, 'tasks')
        
        # Create the directory if it doesn't exist
        if not os.path.exists(task_dir):
            os.makedirs(task_dir, exist_ok=True)
            logger.debug(f"Created task directory for user {user_id}: {task_dir}")
        
        # Initialize task files if they don't exist
        task_files = {
            'active_tasks': {'tasks': []},
            'completed_tasks': {'completed_tasks': []},
            'task_schedules': {'task_schedules': {}}
        }
        
        for filename, default_data in task_files.items():
            file_path = os.path.join(task_dir, f"{filename}.json")
            if not os.path.exists(file_path):
                save_json_data(default_data, file_path)
                logger.debug(f"Created {filename}.json for user {user_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating task directory structure for user {user_id}: {e}")
        return False

@handle_errors("loading active tasks", default_return=[])
def load_active_tasks(user_id: str) -> List[Dict[str, Any]]:
    """Load active tasks for a user."""
    try:
        if not user_id:
            logger.error("User ID is required for loading tasks")
            return []
        
        # Ensure task directory exists
        ensure_task_directory(user_id)
        
        # Load active tasks using correct path
        user_dir = get_user_data_dir(user_id)
        task_dir = os.path.join(user_dir, 'tasks')
        active_tasks_file = os.path.join(task_dir, 'active_tasks.json')
        
        data = load_json_data(active_tasks_file) or {'tasks': []}
        tasks = data.get('tasks', [])
        
        logger.debug(f"Loaded {len(tasks)} active tasks for user {user_id}")
        return tasks
        
    except Exception as e:
        logger.error(f"Error loading active tasks for user {user_id}: {e}")
        return []

@handle_errors("saving active tasks")
def save_active_tasks(user_id: str, tasks: List[Dict[str, Any]]) -> bool:
    """Save active tasks for a user."""
    try:
        if not user_id:
            logger.error("User ID is required for saving tasks")
            return False
        
        # Ensure task directory exists
        ensure_task_directory(user_id)
        
        # Save active tasks using correct path
        user_dir = get_user_data_dir(user_id)
        task_dir = os.path.join(user_dir, 'tasks')
        active_tasks_file = os.path.join(task_dir, 'active_tasks.json')
        
        data = {'tasks': tasks}
        save_json_data(data, active_tasks_file)
        
        logger.debug(f"Saved {len(tasks)} active tasks for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving active tasks for user {user_id}: {e}")
        return False

@handle_errors("loading completed tasks", default_return=[])
def load_completed_tasks(user_id: str) -> List[Dict[str, Any]]:
    """Load completed tasks for a user."""
    try:
        if not user_id:
            logger.error("User ID is required for loading completed tasks")
            return []
        
        # Ensure task directory exists
        ensure_task_directory(user_id)
        
        # Load completed tasks using correct path
        user_dir = get_user_data_dir(user_id)
        task_dir = os.path.join(user_dir, 'tasks')
        completed_tasks_file = os.path.join(task_dir, 'completed_tasks.json')
        
        data = load_json_data(completed_tasks_file) or {'completed_tasks': []}
        tasks = data.get('completed_tasks', [])
        
        logger.debug(f"Loaded {len(tasks)} completed tasks for user {user_id}")
        return tasks
        
    except Exception as e:
        logger.error(f"Error loading completed tasks for user {user_id}: {e}")
        return []

@handle_errors("saving completed tasks")
def save_completed_tasks(user_id: str, tasks: List[Dict[str, Any]]) -> bool:
    """Save completed tasks for a user."""
    try:
        if not user_id:
            logger.error("User ID is required for saving completed tasks")
            return False
        
        # Ensure task directory exists
        ensure_task_directory(user_id)
        
        # Save completed tasks using correct path
        user_dir = get_user_data_dir(user_id)
        task_dir = os.path.join(user_dir, 'tasks')
        completed_tasks_file = os.path.join(task_dir, 'completed_tasks.json')
        
        data = {'completed_tasks': tasks}
        save_json_data(data, completed_tasks_file)
        
        logger.debug(f"Saved {len(tasks)} completed tasks for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving completed tasks for user {user_id}: {e}")
        return False

@handle_errors("creating new task")
def create_task(user_id: str, title: str, description: str = "", due_date: str = None, 
                due_time: str = None, priority: str = "medium", category: str = "", 
                reminder_periods: Optional[list] = None) -> Optional[str]:
    """Create a new task for a user."""
    try:
        if not user_id or not title:
            logger.error("User ID and title are required for task creation")
            return None
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Create task object
        task = {
            "task_id": task_id,
            "title": title,
            "description": description,
            "due_date": due_date,
            "due_time": due_time,
            "completed": False,
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "completed_at": None,
            "priority": priority,
            "category": category
        }
        
        # Only add reminder_periods if provided and non-empty
        if reminder_periods:
            task["reminder_periods"] = reminder_periods
        
        # Load existing tasks
        tasks = load_active_tasks(user_id)
        
        # Add new task
        tasks.append(task)
        
        # Save updated tasks
        if save_active_tasks(user_id, tasks):
            logger.info(f"Created task '{title}' for user {user_id} with ID {task_id}")
            return task_id
        else:
            logger.error(f"Failed to save task for user {user_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating task for user {user_id}: {e}")
        return None

@handle_errors("updating task")
def update_task(user_id: str, task_id: str, updates: Dict[str, Any]) -> bool:
    """Update an existing task."""
    try:
        if not user_id or not task_id:
            logger.error("User ID and task ID are required for task update")
            return False
        
        # Load existing tasks
        tasks = load_active_tasks(user_id)
        
        # Find and update the task
        for task in tasks:
            if task.get('task_id') == task_id:
                # Update allowed fields
                allowed_fields = ['title', 'description', 'due_date', 'due_time', 
                                'reminder_periods', 'priority', 'category']
                for field, value in updates.items():
                    if field in allowed_fields:
                        task[field] = value
                
                # Add last updated timestamp
                task['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Save updated tasks
                if save_active_tasks(user_id, tasks):
                    logger.info(f"Updated task {task_id} for user {user_id}")
                    return True
                else:
                    logger.error(f"Failed to save updated task for user {user_id}")
                    return False
        
        logger.warning(f"Task {task_id} not found for user {user_id}")
        return False
        
    except Exception as e:
        logger.error(f"Error updating task {task_id} for user {user_id}: {e}")
        return False

@handle_errors("completing task")
def complete_task(user_id: str, task_id: str) -> bool:
    """Mark a task as completed."""
    try:
        if not user_id or not task_id:
            logger.error("User ID and task ID are required for task completion")
            return False
        
        # Load active tasks
        active_tasks = load_active_tasks(user_id)
        
        # Find the task to complete
        task_to_complete = None
        updated_active_tasks = []
        
        for task in active_tasks:
            if task.get('task_id') == task_id:
                task_to_complete = task.copy()
                task_to_complete['completed'] = True
                task_to_complete['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                updated_active_tasks.append(task)
        
        if not task_to_complete:
            logger.warning(f"Task {task_id} not found for user {user_id}")
            return False
        
        # Load completed tasks
        completed_tasks = load_completed_tasks(user_id)
        
        # Add to completed tasks
        completed_tasks.append(task_to_complete)
        
        # Save both updated lists
        if (save_active_tasks(user_id, updated_active_tasks) and 
            save_completed_tasks(user_id, completed_tasks)):
            logger.info(f"Completed task {task_id} for user {user_id}")
            return True
        else:
            logger.error(f"Failed to save task completion for user {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error completing task {task_id} for user {user_id}: {e}")
        return False

@handle_errors("deleting task")
def delete_task(user_id: str, task_id: str) -> bool:
    """Delete a task (permanently remove it)."""
    try:
        if not user_id or not task_id:
            logger.error("User ID and task ID are required for task deletion")
            return False
        
        # Load active tasks
        tasks = load_active_tasks(user_id)
        
        # Remove the task
        original_count = len(tasks)
        tasks = [task for task in tasks if task.get('task_id') != task_id]
        
        if len(tasks) == original_count:
            logger.warning(f"Task {task_id} not found for user {user_id}")
            return False
        
        # Save updated tasks
        if save_active_tasks(user_id, tasks):
            logger.info(f"Deleted task {task_id} for user {user_id}")
            return True
        else:
            logger.error(f"Failed to save task deletion for user {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting task {task_id} for user {user_id}: {e}")
        return False

@handle_errors("getting task by ID", default_return=None)
def get_task_by_id(user_id: str, task_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific task by ID."""
    try:
        if not user_id or not task_id:
            logger.error("User ID and task ID are required for task lookup")
            return None
        
        # Check active tasks first
        active_tasks = load_active_tasks(user_id)
        for task in active_tasks:
            if task.get('task_id') == task_id:
                return task
        
        # Check completed tasks
        completed_tasks = load_completed_tasks(user_id)
        for task in completed_tasks:
            if task.get('task_id') == task_id:
                return task
        
        logger.debug(f"Task {task_id} not found for user {user_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error getting task {task_id} for user {user_id}: {e}")
        return None

@handle_errors("getting tasks due soon", default_return=[])
def get_tasks_due_soon(user_id: str, days_ahead: int = 7) -> List[Dict[str, Any]]:
    """Get tasks due within the specified number of days."""
    try:
        if not user_id:
            logger.error("User ID is required for getting tasks due soon")
            return []
        
        active_tasks = load_active_tasks(user_id)
        due_soon = []
        
        cutoff_date = datetime.now() + timedelta(days=days_ahead)
        
        for task in active_tasks:
            if task.get('due_date'):
                try:
                    due_date = datetime.strptime(task['due_date'], '%Y-%m-%d')
                    if due_date <= cutoff_date:
                        due_soon.append(task)
                except ValueError:
                    logger.warning(f"Invalid due date format for task {task.get('task_id')}")
                    continue
        
        # Sort by due date
        due_soon.sort(key=lambda x: x.get('due_date', '9999-12-31'))
        
        logger.debug(f"Found {len(due_soon)} tasks due within {days_ahead} days for user {user_id}")
        return due_soon
        
    except Exception as e:
        logger.error(f"Error getting tasks due soon for user {user_id}: {e}")
        return []

@handle_errors("checking if tasks are enabled", default_return=False)
def are_tasks_enabled(user_id: str) -> bool:
    """Check if task management is enabled for a user."""
    try:
        if not user_id:
            logger.error("User ID is required for checking task status")
            return False
        
        # Get user account to check if task management is enabled
        user_data_result = get_user_data(user_id, 'account')
        user_account = user_data_result.get('account')
        if not user_account or user_account.get('features', {}).get('task_management') != 'enabled':
            logger.warning(f"Task management not enabled for user {user_id}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking task status for user {user_id}: {e}")
        return False

@handle_errors("getting user task statistics", default_return={})
def get_user_task_stats(user_id: str) -> Dict[str, int]:
    """Get task statistics for a user."""
    try:
        if not user_id:
            logger.error("User ID is required for getting task statistics")
            return {}
        
        # Load active and completed tasks
        active_tasks = load_active_tasks(user_id)
        completed_tasks = load_completed_tasks(user_id)
        
        # Calculate statistics
        stats = {
            'active_count': len(active_tasks),
            'completed_count': len(completed_tasks),
            'total_count': len(active_tasks) + len(completed_tasks)
        }
        
        logger.debug(f"Task statistics for user {user_id}: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting task statistics for user {user_id}: {e}")
        return {
            'active_count': 0,
            'completed_count': 0,
            'total_count': 0
        } 