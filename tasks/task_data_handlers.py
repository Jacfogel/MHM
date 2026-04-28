"""
Task data handlers: directory setup and load/save of active and completed task JSON.

Uses core.user_item_storage for paths and I/O. No business logic.
"""

from typing import Any, cast

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.user_data_validation import is_valid_user_id
from core.user_item_storage import (
    ensure_user_subdir,
    get_user_subdir_path,
    load_user_json_file,
    save_user_json_file,
)

from tasks.task_schemas import TASKS_V2_FILENAME
from core.time_utilities import now_timestamp_full, parse_timestamp_full
from core.user_data_v2 import SCHEMA_VERSION, TaskV2Model, generate_short_id

logger = get_component_logger("tasks")

TASKS_SUBDIR = "tasks"

# Default structure for task file (used when creating or when load returns wrong type)
TASKS_V2_DEFAULT: dict = {"schema_version": SCHEMA_VERSION, "updated_at": "", "tasks": []}

TASK_V2_FIELDS = {
    "id",
    "short_id",
    "kind",
    "title",
    "description",
    "category",
    "group",
    "tags",
    "priority",
    "status",
    "due",
    "reminders",
    "recurrence",
    "completion",
    "source",
    "linked_item_ids",
    "created_at",
    "updated_at",
    "archived_at",
    "deleted_at",
    "metadata",
}


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
    path = get_user_subdir_path(user_id, TASKS_SUBDIR)
    if path is None:
        return False
    path.mkdir(parents=True, exist_ok=True)
    if (path / TASKS_V2_FILENAME).exists():
        return True
    path = ensure_user_subdir(user_id, TASKS_SUBDIR, init_files={TASKS_V2_FILENAME: TASKS_V2_DEFAULT})
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
    return [_task_v2_to_runtime(task) for task in v2_tasks if task.get("status") == "active"]


@handle_errors("saving active tasks", default_return=False)
def save_active_tasks(user_id: str, tasks: list[dict[str, Any]]) -> bool:
    """Save active tasks for a user. Returns True on success."""
    if not is_valid_user_id(user_id):
        logger.error(f"Invalid user_id for save_active_tasks: {user_id}")
        return False
    ensure_task_directory(user_id)
    v2_tasks = _load_v2_tasks(user_id)
    completed_tasks = [task for task in v2_tasks if task.get("status") == "completed"]
    active_v2 = _runtime_tasks_to_v2(tasks, status="active")
    return _save_v2_tasks(user_id, active_v2 + completed_tasks)


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
    return [_task_v2_to_runtime(task) for task in v2_tasks if task.get("status") == "completed"]


@handle_errors("saving completed tasks", default_return=False)
def save_completed_tasks(user_id: str, tasks: list[dict[str, Any]]) -> bool:
    """Save completed tasks for a user. Returns True on success."""
    if not is_valid_user_id(user_id):
        logger.error(f"Invalid user_id for save_completed_tasks: {user_id}")
        return False
    ensure_task_directory(user_id)
    v2_tasks = _load_v2_tasks(user_id)
    active_tasks = [task for task in v2_tasks if task.get("status") == "active"]
    completed_v2 = _runtime_tasks_to_v2(tasks, status="completed")
    return _save_v2_tasks(user_id, active_tasks + completed_v2)


@handle_errors("loading v2 task file", default_return=[])
def _load_v2_tasks(user_id: str) -> list[dict[str, Any]]:
    tasks_dir = get_user_subdir_path(user_id, TASKS_SUBDIR)
    if tasks_dir is None:
        return []
    if not (tasks_dir / TASKS_V2_FILENAME).exists():
        if not _save_v2_tasks(user_id, []):
            return []
        return []
    data = load_user_json_file(user_id, TASKS_SUBDIR, TASKS_V2_FILENAME, TASKS_V2_DEFAULT)
    if isinstance(data, dict) and data.get("schema_version") == SCHEMA_VERSION:
        tasks = data.get("tasks", [])
        if isinstance(tasks, list):
            return [task for task in tasks if isinstance(task, dict)]
    return []


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
    converted: list[dict[str, Any]] = []
    for task in tasks:
        task_v2 = _runtime_task_to_v2(task, status=status)
        if isinstance(task_v2, dict):
            converted.append(task_v2)
    return converted


@handle_errors("converting runtime task to v2", default_return=None)
def _runtime_task_to_v2(task: dict[str, Any], *, status: str) -> dict[str, Any] | None:
    """Convert a runtime task dictionary to a validated canonical v2 task record."""
    task_id = str(task.get("id") or task.get("task_id") or "")
    if not task_id:
        task_id = generate_short_id(now_timestamp_full(), "task", length=12)
    created_at = _canonical_timestamp(task.get("created_at")) or now_timestamp_full()
    updated_at = _canonical_timestamp(task.get("updated_at") or task.get("last_updated") or created_at) or created_at
    due_raw = task.get("due")
    recurrence_raw = task.get("recurrence")
    completion_raw = task.get("completion")
    due: dict[str, Any] = cast(dict[str, Any], due_raw) if isinstance(due_raw, dict) else {}
    recurrence: dict[str, Any] = (
        cast(dict[str, Any], recurrence_raw) if isinstance(recurrence_raw, dict) else {}
    )
    completion: dict[str, Any] = (
        cast(dict[str, Any], completion_raw) if isinstance(completion_raw, dict) else {}
    )
    completed_at = completion.get("completed_at") or task.get("completed_at")
    completed = status == "completed"
    metadata = dict(task.get("metadata") or {})
    for key, value in task.items():
        if key not in TASK_V2_FIELDS and key not in _TASK_V1_FIELDS:
            metadata[f"legacy_{key}"] = value
    v2_task = {
        "id": task_id,
        "short_id": task.get("short_id") or generate_short_id(task_id, "task"),
        "kind": "task",
        "title": str(task.get("title") or ""),
        "description": str(task.get("description") or ""),
        "category": str(task.get("category") or ""),
        "group": str(task.get("group") or ""),
        "tags": task.get("tags") or [],
        "priority": _normalized_priority(task.get("priority")) or "medium",
        "status": status,
        "due": {
            "date": due.get("date") or task.get("due_date"),
            "time": due.get("time") or task.get("due_time"),
        },
        "reminders": _runtime_reminders_to_v2(task),
        "recurrence": {
            "pattern": recurrence.get("pattern") or task.get("recurrence_pattern"),
            "interval": recurrence.get("interval") or task.get("recurrence_interval") or 1,
            "repeat_after_completion": recurrence.get("repeat_after_completion", task.get("repeat_after_completion", True)),
            "next_due_date": recurrence.get("next_due_date") or task.get("next_due_date"),
        },
        "completion": {
            "completed": completed,
            "completed_at": _nullable_timestamp(completed_at) if completed else None,
            "notes": str(completion.get("notes") or task.get("completion_notes") or ""),
        },
        "source": task.get("source") or {"system": "mhm", "channel": "", "actor": "", "migration": None},
        "linked_item_ids": task.get("linked_item_ids") or [],
        "created_at": created_at,
        "updated_at": updated_at,
        "archived_at": task.get("archived_at"),
        "deleted_at": task.get("deleted_at"),
        "metadata": metadata,
    }
    return TaskV2Model.model_validate(v2_task).model_dump(mode="json")


@handle_errors("converting v2 task to runtime shape", default_return={})
def _task_v2_to_runtime(task: dict[str, Any]) -> dict[str, Any]:
    due = task.get("due") or {}
    completion = task.get("completion") or {}
    recurrence = task.get("recurrence") or {}
    runtime = {
        "id": task.get("id"),
        "short_id": task.get("short_id"),
        "kind": "task",
        "task_id": task.get("id"),
        "title": task.get("title", ""),
        "description": task.get("description", ""),
        "category": task.get("category", ""),
        "group": task.get("group", ""),
        "status": task.get("status", "active"),
        "due": due,
        "due_date": due.get("date"),
        "due_time": due.get("time"),
        "completed": task.get("status") == "completed",
        "created_at": task.get("created_at"),
        "completed_at": completion.get("completed_at"),
        "priority": task.get("priority", "medium"),
        "tags": task.get("tags", []),
        "reminders": task.get("reminders", []),
        "recurrence": recurrence,
        "completion": completion,
        "source": task.get("source"),
        "linked_item_ids": task.get("linked_item_ids", []),
        "archived_at": task.get("archived_at"),
        "deleted_at": task.get("deleted_at"),
        "metadata": task.get("metadata", {}),
        "last_updated": task.get("updated_at"),
    }
    if completion.get("notes"):
        runtime["completion_notes"] = completion.get("notes")
    if task.get("reminders"):
        reminder_periods = []
        quick_reminders = []
        for reminder in task.get("reminders", []):
            if not isinstance(reminder, dict):
                continue
            if reminder.get("kind") == "quick":
                quick_reminders.append(reminder.get("value"))
            elif reminder.get("period"):
                reminder_periods.append(reminder.get("period"))
            else:
                scheduled = {
                    key: value
                    for key, value in reminder.items()
                    if key != "kind"
                }
                if scheduled:
                    reminder_periods.append(scheduled)
        if reminder_periods:
            runtime["reminder_periods"] = reminder_periods
        if quick_reminders:
            runtime["quick_reminders"] = quick_reminders
    if recurrence.get("pattern"):
        runtime["recurrence_pattern"] = recurrence.get("pattern")
        runtime["recurrence_interval"] = recurrence.get("interval", 1)
        runtime["repeat_after_completion"] = recurrence.get("repeat_after_completion", True)
        runtime["next_due_date"] = recurrence.get("next_due_date")
    return runtime


_TASK_V1_FIELDS = {
    "task_id",
    "completed",
    "completed_at",
    "completion_notes",
    "due_date",
    "due_time",
    "reminder_periods",
    "quick_reminders",
    "recurrence_pattern",
    "recurrence_interval",
    "repeat_after_completion",
    "next_due_date",
    "last_updated",
}


@handle_errors("converting runtime reminder fields to v2", default_return=[])
def _runtime_reminders_to_v2(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert runtime reminder fields into canonical v2 reminder records."""
    if isinstance(task.get("reminders"), list) and (
        task.get("reminders")
        or ("reminder_periods" not in task and "quick_reminders" not in task)
    ):
        return [reminder for reminder in task["reminders"] if isinstance(reminder, dict)]
    reminders = []
    for period in task.get("reminder_periods") or []:
        if isinstance(period, dict):
            reminder = dict(period)
            reminder.setdefault("kind", "scheduled")
            reminders.append(reminder)
        else:
            reminders.append({"period": period, "kind": "scheduled"})
    for reminder in task.get("quick_reminders") or []:
        reminders.append({"value": reminder, "kind": "quick"})
    return reminders


@handle_errors("normalizing canonical task timestamp", default_return=None)
def _canonical_timestamp(value: Any) -> str | None:
    """Return a valid full timestamp string or a current-time fallback."""
    if isinstance(value, str) and parse_timestamp_full(value) is not None:
        return value
    return now_timestamp_full()


@handle_errors("normalizing optional task timestamp", default_return=None)
def _nullable_timestamp(value: Any) -> str | None:
    """Return a valid full timestamp string, otherwise None."""
    if isinstance(value, str) and parse_timestamp_full(value) is not None:
        return value
    return None


@handle_errors("normalizing task priority", default_return=None)
def _normalized_priority(value: Any) -> str | None:
    """Normalize task priority to a supported lower-case value."""
    priority = str(value or "medium").lower().strip()
    if priority not in {"low", "medium", "high", "urgent", "critical"}:
        return "medium"
    return priority
