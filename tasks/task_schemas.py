"""
Task domain types, constants, and exception.

Used by task_validation and task_data_manager. No business logic.
"""

# Domain exception for task operations
class TaskManagementError(Exception):
    """Custom exception for task management errors."""

    pass


# Valid priority values for tasks
VALID_PRIORITIES: tuple[str, ...] = ("low", "medium", "high", "urgent", "critical")

# Fields that may be updated via update_task
ALLOWED_UPDATE_FIELDS: tuple[str, ...] = (
    "title",
    "description",
    "due_date",
    "due_time",
    "reminder_periods",
    "priority",
    "tags",
    "quick_reminders",
    "recurrence_pattern",
    "recurrence_interval",
    "repeat_after_completion",
    "next_due_date",
)

# Task file names under user tasks/ subdir (for reference; actual paths built in task_data_handlers)
ACTIVE_TASKS_FILENAME = "active_tasks.json"
COMPLETED_TASKS_FILENAME = "completed_tasks.json"
TASK_SCHEDULES_FILENAME = "task_schedules.json"
