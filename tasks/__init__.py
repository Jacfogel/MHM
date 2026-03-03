"""Task management package.

Contains task management utilities and operations for creating,
updating, and managing user tasks within the MHM system.

This file deliberately modified to test coverage caching.
"""

# Main public API - package-level exports from split modules
from .task_schemas import TaskManagementError
from .task_data_handlers import (
    ensure_task_directory,
    load_active_tasks,
    save_active_tasks,
    load_completed_tasks,
    save_completed_tasks,
)
from .task_data_manager import (
    create_task,
    update_task,
    complete_task,
    delete_task,
    restore_task,
    get_task_by_id,
    get_tasks_due_soon,
    get_user_task_stats,
    add_user_task_tag,
    remove_user_task_tag,
    setup_default_task_tags,
    are_tasks_enabled,
    schedule_task_reminders,
    cleanup_task_reminders,
)

__all__ = [
    # Error class
    "TaskManagementError",
    # Task CRUD operations
    "create_task",
    "update_task",
    "complete_task",
    "delete_task",
    # Task loading/saving
    "load_active_tasks",
    "save_active_tasks",
    "get_task_by_id",
    "get_tasks_due_soon",
    # Task utilities
    "get_user_task_stats",
    "ensure_task_directory",
    "add_user_task_tag",
    "remove_user_task_tag",
    "setup_default_task_tags",
    # High usage
    "are_tasks_enabled",
    # Medium usage
    "load_completed_tasks",
    # Low usage
    "restore_task",
    # Public API
    "save_completed_tasks",
    "schedule_task_reminders",
    "cleanup_task_reminders",
]
