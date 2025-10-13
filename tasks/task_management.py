# task_management.py
"""
Task management utilities for MHM.
Contains functions for task CRUD operations, task scheduling, and task data management.
"""

from pathlib import Path
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from core.logger import get_component_logger
from core.file_operations import load_json_data, save_json_data
from core.error_handling import handle_errors
from core.config import get_user_data_dir
from core.user_data_handlers import get_user_data

logger = get_component_logger('tasks')
task_logger = get_component_logger('main')

class TaskManagementError(Exception):
    """Custom exception for task management errors."""
    pass

@handle_errors("creating task directory structure", default_return=False)
def ensure_task_directory(user_id: str) -> bool:
    """
    Ensure the task directory structure exists for a user with validation.
    
    Returns:
        bool: True if successful, False if failed
    """
    # Validate user_id
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return False
        
    if not user_id.strip():
        logger.error("Empty user_id provided")
        return False
    """Ensure the task directory structure exists for a user."""
    try:
        if not user_id:
            logger.error("User ID is required for task directory creation")
            return False
            
        # Get the user directory path using the correct function
        user_dir = Path(get_user_data_dir(user_id))
        task_dir = user_dir / 'tasks'
        
        # Create the directory if it doesn't exist
        if not task_dir.exists():
            task_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created task directory for user {user_id}: {task_dir}")
        
        # Initialize task files if they don't exist
        task_files = {
            'active_tasks': {'tasks': []},
            'completed_tasks': {'completed_tasks': []},
            'task_schedules': {'task_schedules': {}}
        }
        
        for filename, default_data in task_files.items():
            file_path = task_dir / f"{filename}.json"
            if not file_path.exists():
                save_json_data(default_data, str(file_path))
                logger.debug(f"Created {filename}.json for user {user_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating task directory structure for user {user_id}: {e}")
        return False

@handle_errors("loading active tasks", default_return=[])
def load_active_tasks(user_id: str) -> List[Dict[str, Any]]:
    """
    Load active tasks for a user with validation.
    
    Returns:
        List[Dict[str, Any]]: List of active tasks, empty list if failed
    """
    # Validate user_id
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return []
        
    if not user_id.strip():
        logger.error("Empty user_id provided")
        return []
    """Load active tasks for a user."""
    try:
        if not user_id:
            logger.error("User ID is required for loading tasks")
            return []
        
        # Ensure task directory exists
        ensure_task_directory(user_id)
        
        # Load active tasks using correct path
        user_dir = Path(get_user_data_dir(user_id))
        task_dir = user_dir / 'tasks'
        active_tasks_file = task_dir / 'active_tasks.json'
        
        data = load_json_data(str(active_tasks_file)) or {'tasks': []}
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
        user_dir = Path(get_user_data_dir(user_id))
        task_dir = user_dir / 'tasks'
        active_tasks_file = task_dir / 'active_tasks.json'
        
        data = {'tasks': tasks}
        save_json_data(data, str(active_tasks_file))
        
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
        user_dir = Path(get_user_data_dir(user_id))
        task_dir = user_dir / 'tasks'
        completed_tasks_file = task_dir / 'completed_tasks.json'
        
        data = load_json_data(str(completed_tasks_file)) or {'completed_tasks': []}
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
        user_dir = Path(get_user_data_dir(user_id))
        task_dir = user_dir / 'tasks'
        completed_tasks_file = task_dir / 'completed_tasks.json'
        
        data = {'completed_tasks': tasks}
        save_json_data(data, str(completed_tasks_file))
        
        logger.debug(f"Saved {len(tasks)} completed tasks for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving completed tasks for user {user_id}: {e}")
        return False

@handle_errors("creating new task")
def create_task(user_id: str, title: str, description: str = "", due_date: str = None, 
                due_time: str = None, priority: str = "medium", 
                reminder_periods: Optional[list] = None, tags: Optional[list] = None,
                quick_reminders: Optional[list] = None, recurrence_pattern: str = None,
                recurrence_interval: int = 1, repeat_after_completion: bool = True) -> Optional[str]:
    """Create a new task for a user."""
    try:
        if not user_id or not isinstance(user_id, str):
            logger.error("Valid user ID required for task creation")
            return None
            
        if not title or not isinstance(title, str):
            logger.error("Valid title required for task creation")
            return None
            
        # Validate description parameter
        if description is not None and not isinstance(description, str):
            logger.error(f"Invalid description type: {type(description)}")
            return None
        
        # Validate priority parameter
        valid_priorities = ["low", "medium", "high", "urgent"]
        if priority and not isinstance(priority, str):
            logger.error(f"Invalid priority type: {type(priority)}")
            return None
        if priority and priority.lower() not in valid_priorities:
            logger.error(f"Invalid priority value: {priority}. Must be one of {valid_priorities}")
            return None
        
        # Validate reminder_periods parameter
        if reminder_periods is not None and not isinstance(reminder_periods, list):
            logger.error(f"Invalid reminder_periods type: {type(reminder_periods)}")
            return None
        
        # Validate tags parameter
        if tags is not None and not isinstance(tags, list):
            logger.error(f"Invalid tags type: {type(tags)}")
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
            "priority": priority
        }
        
        # Only add reminder_periods if provided and non-empty
        if reminder_periods:
            task["reminder_periods"] = reminder_periods
        
        # Add tags if provided
        if tags:
            task["tags"] = tags
        
        # Add quick_reminders if provided
        if quick_reminders:
            task["quick_reminders"] = quick_reminders
        
        # Add recurring task fields if provided
        if recurrence_pattern:
            task["recurrence_pattern"] = recurrence_pattern
            task["recurrence_interval"] = recurrence_interval
            task["repeat_after_completion"] = repeat_after_completion
            task["next_due_date"] = due_date  # Initial next due date is the original due date
        
        # Load existing tasks
        tasks = load_active_tasks(user_id)
        
        # Add new task
        tasks.append(task)
        
        # Save updated tasks
        if save_active_tasks(user_id, tasks):
            logger.info(f"Created task '{title}' for user {user_id} with ID {task_id}")
            
            # Schedule task-specific reminders if provided
            if reminder_periods:
                schedule_task_reminders(user_id, task_id, reminder_periods)
            
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
                # Track what fields are being updated
                updated_fields = []
                allowed_fields = ['title', 'description', 'due_date', 'due_time', 
                                'reminder_periods', 'priority', 'tags', 'quick_reminders',
                                'recurrence_pattern', 'recurrence_interval', 'repeat_after_completion', 'next_due_date']
                for field, value in updates.items():
                    if field in allowed_fields:
                        old_value = task.get(field, 'None')
                        task[field] = value
                        updated_fields.append(f"{field}: {old_value} -> {value}")
                    else:
                        logger.warning(f"Attempted to update disallowed field '{field}' for task {task_id}")
                
                # Add last updated timestamp
                task['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Save updated tasks
                if save_active_tasks(user_id, tasks):
                    logger.info(f"Updated task {task_id} for user {user_id} | Fields: {', '.join(updated_fields)}")
                    
                    # Handle reminder updates
                    if 'reminder_periods' in updates:
                        # Clean up existing reminders
                        cleanup_task_reminders(user_id, task_id)
                        # Schedule new reminders
                        new_reminder_periods = updates['reminder_periods']
                        if new_reminder_periods:
                            schedule_task_reminders(user_id, task_id, new_reminder_periods)
                    
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
def complete_task(user_id: str, task_id: str, completion_data: Optional[Dict[str, Any]] = None) -> bool:
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
                
                # Use provided completion data or default to current time
                if completion_data:
                    completion_date = completion_data.get('completion_date')
                    completion_time = completion_data.get('completion_time')
                    completion_notes = completion_data.get('completion_notes', '')
                    
                    if completion_date and completion_time:
                        task_to_complete['completed_at'] = f"{completion_date} {completion_time}:00"
                    else:
                        task_to_complete['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    if completion_notes:
                        task_to_complete['completion_notes'] = completion_notes
                else:
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
            # Enhanced completion logging with task details
            task_title = task_to_complete.get('title', 'Unknown')
            completion_time = task_to_complete.get('completed_at', 'Unknown')
            logger.info(f"Completed task '{task_title}' (ID: {task_id}) for user {user_id} at {completion_time}")
            
            # Clean up task-specific reminders when task is completed
            cleanup_task_reminders(user_id, task_id)
            logger.debug(f"Cleaned up reminders for completed task {task_id}")
            
            # Handle recurring tasks - create next instance if needed
            if task_to_complete.get('recurrence_pattern'):
                next_task_created = _create_next_recurring_task_instance(user_id, task_to_complete)
                if next_task_created:
                    logger.info(f"Created next recurring task instance for task '{task_title}' (ID: {task_id})")
            
            return True
        else:
            logger.error(f"Failed to save task completion for user {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error completing task {task_id} for user {user_id}: {e}")
        return False

@handle_errors("restoring task")
def restore_task(user_id: str, task_id: str) -> bool:
    """Restore a completed task to active status."""
    try:
        if not user_id or not task_id:
            logger.error("User ID and task ID are required for task restoration")
            return False
        
        # Load completed tasks
        completed_tasks = load_completed_tasks(user_id)
        
        # Find the task to restore
        task_to_restore = None
        updated_completed_tasks = []
        
        for task in completed_tasks:
            if task.get('task_id') == task_id:
                task_to_restore = task.copy()
                task_to_restore['completed'] = False
                task_to_restore['completed_at'] = None
            else:
                updated_completed_tasks.append(task)
        
        if not task_to_restore:
            logger.warning(f"Completed task {task_id} not found for user {user_id}")
            return False
        
        # Load active tasks
        active_tasks = load_active_tasks(user_id)
        
        # Add to active tasks
        active_tasks.append(task_to_restore)
        
        # Save both updated lists
        if (save_completed_tasks(user_id, updated_completed_tasks) and 
            save_active_tasks(user_id, active_tasks)):
            logger.info(f"Restored task {task_id} for user {user_id}")
            
            # Reschedule task-specific reminders when task is restored
            if task_to_restore.get('reminder_periods'):
                schedule_task_reminders(user_id, task_id, task_to_restore['reminder_periods'])
            
            return True
        else:
            logger.error(f"Failed to save task restoration for user {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error restoring task {task_id} for user {user_id}: {e}")
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
        
        # Find the task to get its details before deletion
        task_to_delete = None
        for task in tasks:
            if task.get('task_id') == task_id:
                task_to_delete = task
                break
        
        # Remove the task
        original_count = len(tasks)
        tasks = [task for task in tasks if task.get('task_id') != task_id]
        
        if len(tasks) == original_count:
            logger.warning(f"Task {task_id} not found for deletion for user {user_id}")
            return False
        
        # Save updated tasks
        if save_active_tasks(user_id, tasks):
            # Enhanced deletion logging with task details
            task_title = task_to_delete.get('title', 'Unknown') if task_to_delete else 'Unknown'
            logger.info(f"Deleted task '{task_title}' (ID: {task_id}) for user {user_id}")
            
            # Clean up task-specific reminders when task is deleted
            cleanup_task_reminders(user_id, task_id)
            logger.debug(f"Cleaned up reminders for deleted task {task_id}")
            
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
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking task status for user {user_id}: {e}")
        return False

@handle_errors("scheduling task-specific reminders")
def schedule_task_reminders(user_id: str, task_id: str, reminder_periods: List[Dict[str, Any]]) -> bool:
    """Schedule reminders for a specific task based on its reminder periods."""
    try:
        if not user_id or not task_id or not reminder_periods:
            logger.debug(f"No reminder periods to schedule for task {task_id}")
            return True
        
        # Import scheduler here to avoid circular imports
        from core.service import get_scheduler_manager
        
        scheduler_manager = get_scheduler_manager()
        if not scheduler_manager:
            logger.error("Scheduler manager not available for scheduling task reminders")
            return False
        
        scheduled_count = 0
        
        for period in reminder_periods:
            date = period.get('date')
            start_time = period.get('start_time')
            end_time = period.get('end_time')
            
            if not date or not start_time or not end_time:
                logger.warning(f"Incomplete reminder period data for task {task_id}: {period}")
                continue
            
            # Schedule reminder at the start time of the period
            if scheduler_manager.schedule_task_reminder_at_datetime(user_id, task_id, date, start_time):
                scheduled_count += 1
                logger.info(f"Scheduled reminder for task {task_id} at {date} {start_time}")
            else:
                logger.warning(f"Failed to schedule reminder for task {task_id} at {date} {start_time}")
        
        logger.info(f"Scheduled {scheduled_count} reminders for task {task_id}")
        return scheduled_count > 0
        
    except Exception as e:
        logger.error(f"Error scheduling task reminders for task {task_id}: {e}")
        return False

@handle_errors("cleaning up task reminders")
def cleanup_task_reminders(user_id: str, task_id: str) -> bool:
    """Clean up all reminders for a specific task."""
    try:
        # Import scheduler here to avoid circular imports
        from core.service import get_scheduler_manager
        
        scheduler_manager = get_scheduler_manager()
        if not scheduler_manager:
            logger.error("Scheduler manager not available for cleaning up task reminders")
            return False
        
        scheduler_manager.cleanup_task_reminders(user_id, task_id)
        logger.info(f"Cleaned up reminders for task {task_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error cleaning up task reminders for task {task_id}: {e}")
        return False

# Removed unnecessary wrapper function - use get_user_data() directly

@handle_errors("adding user task tag")
def add_user_task_tag(user_id: str, tag: str) -> bool:
    """Add a new tag to the user's task settings."""
    try:
        if not user_id or not tag:
            logger.error("User ID and tag are required for adding task tag")
            return False
        
        from core.user_data_handlers import save_user_data
        
        preferences_result = get_user_data(user_id, 'preferences')
        preferences_data = preferences_result.get('preferences', {}) if preferences_result else {}
        task_settings = preferences_data.get('task_settings', {})
        tags = task_settings.get('tags', [])
        
        if tag not in tags:
            tags.append(tag)
            task_settings['tags'] = tags
            preferences_data['task_settings'] = task_settings
            
            if save_user_data(user_id, 'preferences', preferences_data):
                logger.info(f"Added tag '{tag}' for user {user_id}")
                return True
            else:
                logger.error(f"Failed to save tag for user {user_id}")
                return False
        else:
            logger.debug(f"Tag '{tag}' already exists for user {user_id}")
            return True
            
    except Exception as e:
        logger.error(f"Error adding task tag for user {user_id}: {e}")
        return False

@handle_errors("setting up default task tags")
def setup_default_task_tags(user_id: str) -> bool:
    """Set up default task tags for a user when task management is first enabled."""
    try:
        if not user_id:
            logger.error("User ID is required for setting up default task tags")
            return False
        
        from core.user_data_handlers import save_user_data
        
        # Default tags to set up
        default_tags = ["work", "personal", "health"]
        
        preferences_result = get_user_data(user_id, 'preferences')
        preferences_data = preferences_result.get('preferences', {}) if preferences_result else {}
        task_settings = preferences_data.get('task_settings', {})
        existing_tags = task_settings.get('tags', [])
        
        # Only add default tags if no tags exist yet
        if not existing_tags:
            task_settings['tags'] = default_tags
            preferences_data['task_settings'] = task_settings
            
            if save_user_data(user_id, 'preferences', preferences_data):
                logger.info(f"Set up default task tags for user {user_id}: {default_tags}")
                return True
            else:
                logger.error(f"Failed to save default task tags for user {user_id}")
                return False
        else:
            logger.debug(f"User {user_id} already has task tags, skipping default setup")
            return True
            
    except Exception as e:
        logger.error(f"Error setting up default task tags for user {user_id}: {e}")
        return False

@handle_errors("removing user task tag")
def remove_user_task_tag(user_id: str, tag: str) -> bool:
    """Remove a tag from the user's task settings."""
    try:
        if not user_id or not tag:
            logger.error("User ID and tag are required for removing task tag")
            return False
        
        from core.user_data_handlers import save_user_data
        
        preferences_result = get_user_data(user_id, 'preferences')
        preferences_data = preferences_result.get('preferences', {}) if preferences_result else {}
        task_settings = preferences_data.get('task_settings', {})
        tags = task_settings.get('tags', [])
        
        if tag in tags:
            tags.remove(tag)
            task_settings['tags'] = tags
            preferences_data['task_settings'] = task_settings
            
            if save_user_data(user_id, 'preferences', preferences_data):
                logger.info(f"Removed tag '{tag}' for user {user_id}")
                return True
            else:
                logger.error(f"Failed to save tag removal for user {user_id}")
                return False
        else:
            logger.debug(f"Tag '{tag}' not found for user {user_id}")
            return True
            
    except Exception as e:
        logger.error(f"Error removing task tag for user {user_id}: {e}")
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

def _create_next_recurring_task_instance(user_id: str, completed_task: Dict[str, Any]) -> bool:
    """Create the next instance of a recurring task when the current one is completed."""
    try:
        if not user_id or not completed_task:
            logger.error("User ID and completed task are required for creating next recurring task")
            return False
        
        # Extract recurring task information
        recurrence_pattern = completed_task.get('recurrence_pattern')
        recurrence_interval = completed_task.get('recurrence_interval', 1)
        repeat_after_completion = completed_task.get('repeat_after_completion', True)
        
        if not recurrence_pattern:
            logger.debug("No recurrence pattern found, skipping next instance creation")
            return False
        
        # Calculate the next due date based on completion date and recurrence pattern
        completion_date_str = completed_task.get('completed_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        completion_date = datetime.strptime(completion_date_str.split()[0], '%Y-%m-%d')
        
        next_due_date = _calculate_next_due_date(completion_date, recurrence_pattern, recurrence_interval, repeat_after_completion)
        
        if not next_due_date:
            logger.warning(f"Could not calculate next due date for recurring task {completed_task.get('task_id')}")
            return False
        
        # Create the next task instance
        next_task = {
            "task_id": str(uuid.uuid4()),
            "title": completed_task.get('title'),
            "description": completed_task.get('description', ''),
            "due_date": next_due_date.strftime('%Y-%m-%d'),
            "due_time": completed_task.get('due_time'),
            "completed": False,
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "completed_at": None,
            "priority": completed_task.get('priority', 'medium'),
            "recurrence_pattern": recurrence_pattern,
            "recurrence_interval": recurrence_interval,
            "repeat_after_completion": repeat_after_completion,
            "next_due_date": next_due_date.strftime('%Y-%m-%d')
        }
        
        # Copy over optional fields
        if completed_task.get('reminder_periods'):
            next_task["reminder_periods"] = completed_task["reminder_periods"]
        if completed_task.get('tags'):
            next_task["tags"] = completed_task["tags"]
        if completed_task.get('quick_reminders'):
            next_task["quick_reminders"] = completed_task["quick_reminders"]
        
        # Load existing tasks and add the new one
        tasks = load_active_tasks(user_id)
        tasks.append(next_task)
        
        # Save updated tasks
        if save_active_tasks(user_id, tasks):
            logger.info(f"Created next recurring task instance for task {completed_task.get('task_id')} with due date {next_due_date.strftime('%Y-%m-%d')}")
            
            # Schedule reminders for the new task if needed
            if next_task.get('reminder_periods'):
                schedule_task_reminders(user_id, next_task['task_id'], next_task['reminder_periods'])
            
            return True
        else:
            logger.error(f"Failed to save next recurring task instance for user {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating next recurring task instance for user {user_id}: {e}")
        return False

def _calculate_next_due_date(completion_date: datetime, recurrence_pattern: str, 
                           recurrence_interval: int, repeat_after_completion: bool) -> Optional[datetime]:
    """Calculate the next due date for a recurring task."""
    try:
        if repeat_after_completion:
            # Calculate from completion date
            base_date = completion_date
        else:
            # Calculate from original due date (would need to be passed in)
            # For now, use completion date as fallback
            base_date = completion_date
        
        if recurrence_pattern == 'daily':
            next_date = base_date + timedelta(days=recurrence_interval)
        elif recurrence_pattern == 'weekly':
            next_date = base_date + timedelta(weeks=recurrence_interval)
        elif recurrence_pattern == 'monthly':
            # Simple monthly calculation (add months)
            year = base_date.year
            month = base_date.month + recurrence_interval
            while month > 12:
                year += 1
                month -= 12
            try:
                next_date = base_date.replace(year=year, month=month)
            except ValueError:
                # Handle edge case where day doesn't exist in target month
                next_date = base_date.replace(year=year, month=month, day=1)
        elif recurrence_pattern == 'yearly':
            next_date = base_date.replace(year=base_date.year + recurrence_interval)
        else:
            logger.warning(f"Unknown recurrence pattern: {recurrence_pattern}")
            return None
        
        return next_date
        
    except Exception as e:
        logger.error(f"Error calculating next due date: {e}")
        return None 