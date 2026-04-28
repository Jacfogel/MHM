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
    "category",
    "group",
    "status",
    "due_date",
    "due_time",
    "due",
    "reminder_periods",
    "reminders",
    "priority",
    "tags",
    "quick_reminders",
    "recurrence_pattern",
    "recurrence_interval",
    "repeat_after_completion",
    "next_due_date",
    "recurrence",
)

TASKS_V2_FILENAME = "tasks.json"
