"""Task management package.

Contains task management utilities and operations for creating,
updating, and managing user tasks within the MHM system.

This file deliberately modified to test coverage caching.
"""

# Main public API - package-level exports for easier refactoring
from .task_management import (
    TaskManagementError,
    create_task,
    update_task,
    complete_task,
    delete_task,
    load_active_tasks,
    save_active_tasks,
    get_task_by_id,
    get_tasks_due_soon,
    get_user_task_stats,
    ensure_task_directory,
    add_user_task_tag,
    remove_user_task_tag,
    setup_default_task_tags,
    are_tasks_enabled,  # High usage
    load_completed_tasks,  # Medium usage
    restore_task,  # Low usage
    save_completed_tasks,  # Public API
    schedule_task_reminders,  # Public API
    cleanup_task_reminders,  # Public API
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
