"""
Task data handlers: directory setup and load/save of active and completed task JSON.

Uses core.user_item_storage for paths and I/O. No business logic.
"""

from typing import Any

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.user_data_validation import is_valid_user_id
from core.user_item_storage import (
    ensure_user_subdir,
    load_user_json_file,
    save_user_json_file,
)

from tasks.task_schemas import (
    ACTIVE_TASKS_FILENAME,
    COMPLETED_TASKS_FILENAME,
    TASK_SCHEDULES_FILENAME,
)

logger = get_component_logger("tasks")

TASKS_SUBDIR = "tasks"

# Default structure for task files (used when creating or when load returns wrong type)
ACTIVE_DEFAULT: dict = {"tasks": []}
COMPLETED_DEFAULT: dict = {"completed_tasks": []}
SCHEDULES_DEFAULT: dict = {"task_schedules": {}}


@handle_errors("creating task directory structure", default_return=False)
def ensure_task_directory(user_id: str) -> bool:
    """
    Ensure the task directory and default JSON files exist for a user.

    Returns:
        True if successful, False if user_id invalid or creation failed.
    """
    if not is_valid_user_id(user_id):
        logger.error(f"Invalid user_id for ensure_task_directory: {user_id}")
        return False
    path = ensure_user_subdir(
        user_id,
        TASKS_SUBDIR,
        init_files={
            ACTIVE_TASKS_FILENAME: ACTIVE_DEFAULT,
            COMPLETED_TASKS_FILENAME: COMPLETED_DEFAULT,
            TASK_SCHEDULES_FILENAME: SCHEDULES_DEFAULT,
        },
    )
    return path is not None


@handle_errors("loading active tasks", default_return=[])
def load_active_tasks(user_id: str) -> list[dict[str, Any]]:
    """
    Load active tasks for a user.

    Returns:
        List of task dicts; empty list if user_id invalid or load failed.
    """
    if not is_valid_user_id(user_id):
        logger.error(f"Invalid user_id for load_active_tasks: {user_id}")
        return []
    ensure_task_directory(user_id)
    data = load_user_json_file(
        user_id, TASKS_SUBDIR, ACTIVE_TASKS_FILENAME, ACTIVE_DEFAULT
    )
    if isinstance(data, dict):
        return data.get("tasks", [])
    return []


@handle_errors("saving active tasks", default_return=False)
def save_active_tasks(user_id: str, tasks: list[dict[str, Any]]) -> bool:
    """Save active tasks for a user. Returns True on success."""
    if not is_valid_user_id(user_id):
        logger.error(f"Invalid user_id for save_active_tasks: {user_id}")
        return False
    ensure_task_directory(user_id)
    return save_user_json_file(user_id, TASKS_SUBDIR, ACTIVE_TASKS_FILENAME, {"tasks": tasks})


@handle_errors("loading completed tasks", default_return=[])
def load_completed_tasks(user_id: str) -> list[dict[str, Any]]:
    """
    Load completed tasks for a user.

    Returns:
        List of task dicts; empty list if user_id invalid or load failed.
    """
    if not is_valid_user_id(user_id):
        logger.error(f"Invalid user_id for load_completed_tasks: {user_id}")
        return []
    ensure_task_directory(user_id)
    data = load_user_json_file(
        user_id, TASKS_SUBDIR, COMPLETED_TASKS_FILENAME, COMPLETED_DEFAULT
    )
    if isinstance(data, dict):
        return data.get("completed_tasks", [])
    return []


@handle_errors("saving completed tasks", default_return=False)
def save_completed_tasks(user_id: str, tasks: list[dict[str, Any]]) -> bool:
    """Save completed tasks for a user. Returns True on success."""
    if not is_valid_user_id(user_id):
        logger.error(f"Invalid user_id for save_completed_tasks: {user_id}")
        return False
    ensure_task_directory(user_id)
    return save_user_json_file(
        user_id, TASKS_SUBDIR, COMPLETED_TASKS_FILENAME, {"completed_tasks": tasks}
    )
