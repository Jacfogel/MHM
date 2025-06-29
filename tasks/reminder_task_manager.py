# reminder_task_manager.py

"""
reminder_task_manager.py

Merged module for managing user reminders, tasks, or other scheduled items.
This consolidates the placeholder logic that was in reminder_manager.py and
task_manager.py into a single module for future expansion.

Possible expansions:
- Adding, editing, and deleting user tasks/reminders
- Persisting tasks to JSON (similar to how messages are stored)
- Interfacing with the SchedulerManager to schedule tasks
- Creating task-based notifications that go out via Telegram/Discord/Email
"""

from core.logger import get_logger
from core.file_operations import determine_file_path, load_json_data, save_json_data
from user.user_context import UserContext
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)

logger = get_logger(__name__)

class ReminderTaskManagerError(Exception):
    """Custom exception for any ReminderTaskManager issues."""
    pass

class ReminderTaskManager:
    """
    A combined manager for user reminders and tasks.

    Responsibilities:
      - Store & retrieve tasks/reminders from disk
      - Possibly interface with the SchedulerManager to schedule these tasks
      - Provide CRUD operations: create, read, update, delete tasks/reminders
    """

    def __init__(self):
        """
        Initialize any data structures needed for managing tasks or reminders.
        """
        logger.info("Initializing ReminderTaskManager.")
        # If you want in-memory caching, you could do that here
        self.tasks_cache = {}  # Example placeholder

    @handle_errors("loading tasks for user", default_return={})
    def load_tasks_for_user(self, user_id: str) -> dict:
        """
        Loads tasks/reminders for the specified user from JSON or other storage.

        Returns:
            A dictionary structure of tasks, e.g. { "tasks": [ {...}, {...} ] }
        """
        # The following code uses functions from core.file_operations
        file_path = determine_file_path('tasks', user_id)
        data = load_json_data(file_path) or {}
        logger.debug(f"Loading tasks for user: {user_id}")
        return data

    @handle_errors("saving tasks for user")
    def save_tasks_for_user(self, user_id: str, data: dict) -> None:
        """
        Saves tasks/reminders for the specified user to JSON or other storage.
        """
        logger.debug(f"Saving tasks for user: {user_id}")
        # Save tasks to file
        file_path = determine_file_path('tasks', user_id)
        save_json_data(data, file_path)

    @handle_errors("creating task")
    def create_task(self, user_id: str, task_data: dict) -> None:
        """
        Creates a new task or reminder for the user.
        """
        logger.debug(f"Creating task for user {user_id} with data: {task_data}")
        # Load current tasks
        tasks = self.load_tasks_for_user(user_id)
        if "tasks" not in tasks:
            tasks["tasks"] = []
        tasks["tasks"].append(task_data)
        self.save_tasks_for_user(user_id, tasks)

    @handle_errors("listing tasks", default_return=[])
    def list_tasks(self, user_id: str) -> list:
        """
        Returns a list of the user's tasks/reminders.
        """
        tasks = self.load_tasks_for_user(user_id)
        return tasks.get("tasks", [])

    @handle_errors("deleting task", default_return=False)
    def delete_task(self, user_id: str, task_id: str) -> bool:
        """
        Deletes a task from the user's list by matching an ID or similar field.

        Returns:
            True if the task was found and deleted, False otherwise.
        """
        tasks = self.load_tasks_for_user(user_id)
        existing = tasks.get("tasks", [])
        new_list = [t for t in existing if t.get("task_id") != task_id]
        if len(new_list) != len(existing):
            tasks["tasks"] = new_list
            self.save_tasks_for_user(user_id, tasks)
            return True
        return False

    # You could add more methods for scheduling tasks via SchedulerManager here
    # e.g., schedule_task, unschedule_task, etc.
