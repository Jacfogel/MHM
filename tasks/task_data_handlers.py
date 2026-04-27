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
    get_user_subdir_path,
    load_user_json_file,
    save_user_json_file,
)

from tasks.task_schemas import (
    ACTIVE_TASKS_FILENAME,
    COMPLETED_TASKS_FILENAME,
    TASK_SCHEDULES_FILENAME,
    TASKS_V2_FILENAME,
)
from core.time_utilities import now_timestamp_full
from core.user_data_v2 import SCHEMA_VERSION, migrate_task_collections

logger = get_component_logger("tasks")

TASKS_SUBDIR = "tasks"

# Default structure for task files (used when creating or when load returns wrong type)
ACTIVE_DEFAULT: dict = {"tasks": []}
COMPLETED_DEFAULT: dict = {"completed_tasks": []}
SCHEDULES_DEFAULT: dict = {"task_schedules": {}}
TASKS_V2_DEFAULT: dict = {"schema_version": SCHEMA_VERSION, "updated_at": "", "tasks": []}


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
    existing_path = get_user_subdir_path(user_id, TASKS_SUBDIR)
    if existing_path is not None and (existing_path / TASKS_V2_FILENAME).exists():
        existing_path.mkdir(parents=True, exist_ok=True)
        return True
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
    v2_tasks = _load_v2_tasks(user_id)
    if v2_tasks is not None:
        return [_task_v2_to_runtime(task) for task in v2_tasks if task.get("status") == "active"]
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
    v2_tasks = _load_v2_tasks(user_id)
    if v2_tasks is not None:
        completed_tasks = [task for task in v2_tasks if task.get("status") == "completed"]
        active_v2 = _runtime_tasks_to_v2(tasks, status="active")
        return _save_v2_tasks(user_id, active_v2 + completed_tasks)
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
    v2_tasks = _load_v2_tasks(user_id)
    if v2_tasks is not None:
        return [_task_v2_to_runtime(task) for task in v2_tasks if task.get("status") == "completed"]
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
    v2_tasks = _load_v2_tasks(user_id)
    if v2_tasks is not None:
        active_tasks = [task for task in v2_tasks if task.get("status") == "active"]
        completed_v2 = _runtime_tasks_to_v2(tasks, status="completed")
        return _save_v2_tasks(user_id, active_tasks + completed_v2)
    return save_user_json_file(
        user_id, TASKS_SUBDIR, COMPLETED_TASKS_FILENAME, {"completed_tasks": tasks}
    )


@handle_errors("loading v2 task file", default_return=None)
def _load_v2_tasks(user_id: str) -> list[dict[str, Any]] | None:
    tasks_dir = get_user_subdir_path(user_id, TASKS_SUBDIR)
    if tasks_dir is None or not (tasks_dir / TASKS_V2_FILENAME).exists():
        return None
    data = load_user_json_file(user_id, TASKS_SUBDIR, TASKS_V2_FILENAME, TASKS_V2_DEFAULT)
    if isinstance(data, dict) and data.get("schema_version") == SCHEMA_VERSION:
        tasks = data.get("tasks", [])
        if isinstance(tasks, list):
            return [task for task in tasks if isinstance(task, dict)]
    return None


@handle_errors("saving v2 task file", default_return=False)
def _save_v2_tasks(user_id: str, tasks: list[dict[str, Any]]) -> bool:
    return save_user_json_file(
        user_id,
        TASKS_SUBDIR,
        TASKS_V2_FILENAME,
        {"schema_version": SCHEMA_VERSION, "updated_at": now_timestamp_full(), "tasks": tasks},
    )


@handle_errors("converting runtime tasks to v2", default_return=[])
def _runtime_tasks_to_v2(tasks: list[dict[str, Any]], *, status: str) -> list[dict[str, Any]]:
    active_data = {"tasks": tasks if status == "active" else []}
    completed_data = {"completed_tasks": tasks if status == "completed" else []}
    migrated, _report = migrate_task_collections(active_data, completed_data)
    return migrated["tasks"]


@handle_errors("converting v2 task to runtime shape", default_return={})
def _task_v2_to_runtime(task: dict[str, Any]) -> dict[str, Any]:
    due = task.get("due") or {}
    completion = task.get("completion") or {}
    recurrence = task.get("recurrence") or {}
    runtime = {
        "task_id": task.get("id"),
        "title": task.get("title", ""),
        "description": task.get("description", ""),
        "due_date": due.get("date"),
        "due_time": due.get("time"),
        "completed": task.get("status") == "completed",
        "created_at": task.get("created_at"),
        "completed_at": completion.get("completed_at"),
        "priority": task.get("priority", "medium"),
        "tags": task.get("tags", []),
        "last_updated": task.get("updated_at"),
    }
    if completion.get("notes"):
        runtime["completion_notes"] = completion.get("notes")
    if task.get("reminders"):
        runtime["reminder_periods"] = [
            reminder.get("period")
            for reminder in task.get("reminders", [])
            if isinstance(reminder, dict) and reminder.get("period")
        ]
    if recurrence.get("pattern"):
        runtime["recurrence_pattern"] = recurrence.get("pattern")
        runtime["recurrence_interval"] = recurrence.get("interval", 1)
        runtime["repeat_after_completion"] = recurrence.get("repeat_after_completion", True)
        runtime["next_due_date"] = recurrence.get("next_due_date")
    return runtime
