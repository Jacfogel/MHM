"""
Task data manager: CRUD, reminders, tags, stats, and recurring task logic.

Uses task_data_handlers for load/save, task_validation for validation, task_schemas for constants.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core import get_user_data
from core.time_utilities import (
    now_datetime_full,
    now_timestamp_full,
    DATE_ONLY,
    parse_date_only,
    format_timestamp,
    parse_timestamp_full,
)

from tasks.task_data_handlers import (
    load_active_tasks,
    save_active_tasks,
    load_completed_tasks,
    save_completed_tasks,
)
from tasks.task_validation import is_valid_task_title, is_valid_priority, validate_update_field
from core.user_data_v2 import generate_short_id

logger = get_component_logger("tasks")


@handle_errors("resolving canonical task ID", default_return="")
def _task_id(task: dict[str, Any]) -> str:
    """Return canonical task ID."""
    return str(task.get("id") or "")


@handle_errors("resolving canonical task short ID", default_return="")
def _task_short_id(task: dict[str, Any]) -> str:
    """Return task short ID from canonical runtime payload."""
    return str(task.get("short_id") or "")


@handle_errors("matching task identifier", default_return=False)
def _task_matches_identifier(task: dict[str, Any], task_identifier: str) -> bool:
    """Match incoming identifier against canonical id/short_id values."""
    task_identifier = str(task_identifier or "").strip().lower()
    if not task_identifier:
        return False
    return task_identifier in {
        _task_id(task).lower(),
        _task_short_id(task).lower(),
    }


@handle_errors("resolving canonical task due date", default_return=None)
def _task_due_date(task: dict[str, Any]) -> str | None:
    """Return canonical due date."""
    due = task.get("due")
    if isinstance(due, dict):
        return due.get("date")
    return None


@handle_errors("resolving canonical task due time", default_return=None)
def _task_due_time(task: dict[str, Any]) -> str | None:
    """Return canonical due time."""
    due = task.get("due")
    if isinstance(due, dict):
        return due.get("time")
    return None


@handle_errors("resolving canonical task reminder periods", default_return=[])
def _task_reminder_periods(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Return reminder periods from canonical reminders."""
    reminders = task.get("reminders")
    if isinstance(reminders, list):
        periods = []
        for reminder in reminders:
            if not isinstance(reminder, dict):
                continue
            period = reminder.get("period")
            if isinstance(period, dict):
                periods.append(period)
        if periods:
            return periods
    return []


@handle_errors("resolving canonical task recurrence", default_return={})
def _task_recurrence(task: dict[str, Any]) -> dict[str, Any]:
    """Return recurrence data from canonical structure."""
    recurrence = task.get("recurrence")
    if isinstance(recurrence, dict):
        return recurrence
    return {}


@handle_errors("creating new task", default_return=None)
def create_task(
    user_id: str,
    title: str,
    description: str = "",
    due_date: str | None = None,
    due_time: str | None = None,
    priority: str = "medium",
    reminder_periods: list | None = None,
    tags: list | None = None,
    quick_reminders: list | None = None,
    recurrence_pattern: str | None = None,
    recurrence_interval: int = 1,
    repeat_after_completion: bool = True,
    category: str = "",
    group: str = "",
) -> str | None:
    """Create a new task for a user."""
    if not user_id or not isinstance(user_id, str):
        logger.error("Valid user ID required for task creation")
        return None
    if not is_valid_task_title(title):
        logger.error(f"Invalid or missing title: {title}")
        return None
    if description is not None and not isinstance(description, str):
        logger.error(f"Invalid description type: {type(description)}")
        return None
    if due_date and parse_date_only(due_date) is None:
        logger.warning(
            f"Invalid due_date format '{due_date}', expected YYYY-MM-DD. Task will be created without a due date."
        )
        due_date = None
        due_time = None
    if priority and not isinstance(priority, str):
        logger.error(f"Invalid priority type: {type(priority)}")
        return None
    if priority and not is_valid_priority(priority):
        logger.warning(f"Using default priority 'medium' for task '{title}'")
        priority = "medium"
    if reminder_periods is not None and not isinstance(reminder_periods, list):
        logger.error(f"Invalid reminder_periods type: {type(reminder_periods)}")
        return None
    if tags is not None and not isinstance(tags, list):
        logger.error(f"Invalid tags type: {type(tags)}")
        return None

    task_id = str(uuid.uuid4())
    short_id = generate_short_id(task_id, "task")
    reminders: list[dict[str, Any]] = []
    for period in reminder_periods or []:
        if isinstance(period, dict):
            reminders.append({"kind": "scheduled", "period": period})
    for quick in quick_reminders or []:
        reminders.append({"kind": "quick", "value": quick})
    task = {
        "id": task_id,
        "short_id": short_id,
        "kind": "task",
        "title": title,
        "description": description or "",
        "category": str(category or ""),
        "group": str(group or ""),
        "tags": [str(tag) for tag in (tags or []) if isinstance(tag, str)],
        "status": "active",
        "due": {"date": due_date, "time": due_time},
        "created_at": now_timestamp_full(),
        "updated_at": now_timestamp_full(),
        "priority": priority,
        "completion": {"completed": False, "completed_at": None, "notes": ""},
    }
    if reminders:
        task["reminders"] = reminders
    if recurrence_pattern:
        task["recurrence"] = {
            "pattern": recurrence_pattern,
            "interval": recurrence_interval,
            "repeat_after_completion": repeat_after_completion,
            "next_due_date": due_date,
        }

    tasks = load_active_tasks(user_id)
    tasks.append(task)
    if not save_active_tasks(user_id, tasks):
        logger.error(f"Failed to save task for user {user_id}")
        return None
    logger.info(f"Created task '{title}' for user {user_id} with ID {task_id}")
    if reminder_periods:
        schedule_task_reminders(user_id, task_id, reminder_periods)
    return task_id


@handle_errors("updating task", default_return=False)
def update_task(user_id: str, task_id: str, updates: dict[str, Any]) -> bool:
    """Update an existing task."""
    if not user_id or not task_id:
        logger.error("User ID and task ID are required for task update")
        return False
    tasks = load_active_tasks(user_id)
    for task in tasks:
        if _task_matches_identifier(task, task_id):
            canonical_task_id = _task_id(task)
            updated_fields = []
            for field, value in updates.items():
                ok, reason = validate_update_field(field, value)
                if not ok:
                    if reason:
                        logger.warning(f"Task {task_id}: {reason}")
                    continue
                old_value = task.get(field, "None")
                if field == "due_date":
                    task.setdefault("due", {})["date"] = value
                elif field == "due_time":
                    task.setdefault("due", {})["time"] = value
                elif field == "reminder_periods":
                    reminder_periods = value if isinstance(value, list) else []
                    task["reminders"] = [{"kind": "scheduled", "period": p} for p in reminder_periods if isinstance(p, dict)]
                elif field == "quick_reminders":
                    existing = [r for r in task.get("reminders", []) if isinstance(r, dict) and r.get("kind") == "scheduled"]
                    quick = [{"kind": "quick", "value": q} for q in (value if isinstance(value, list) else [])]
                    task["reminders"] = existing + quick
                elif field in {"recurrence_pattern", "recurrence_interval", "repeat_after_completion", "next_due_date"}:
                    recurrence = task.setdefault("recurrence", {})
                    key_map = {
                        "recurrence_pattern": "pattern",
                        "recurrence_interval": "interval",
                        "repeat_after_completion": "repeat_after_completion",
                        "next_due_date": "next_due_date",
                    }
                    recurrence[key_map[field]] = value
                else:
                    task[field] = value
                updated_fields.append(f"{field}: {old_value} -> {value}")
            task["updated_at"] = now_timestamp_full()
            if not save_active_tasks(user_id, tasks):
                logger.error(f"Failed to save updated task for user {user_id}")
                return False
            logger.info(f"Updated task {canonical_task_id} for user {user_id} | Fields: {', '.join(updated_fields)}")
            if "reminder_periods" in updates:
                cleanup_task_reminders(user_id, canonical_task_id)
                new_reminder_periods = updates.get("reminder_periods")
                if new_reminder_periods:
                    try:
                        schedule_task_reminders(user_id, canonical_task_id, new_reminder_periods)
                    except Exception as schedule_error:
                        logger.warning(
                            f"Failed to schedule reminders for task {canonical_task_id}, but task was updated: {schedule_error}"
                        )
            return True
    logger.warning(f"Task {task_id} not found for user {user_id}")
    return False


@handle_errors("completing task", default_return=False)
def complete_task(
    user_id: str, task_id: str, completion_data: dict[str, Any] | None = None
) -> bool:
    """Mark a task as completed."""
    if not user_id or not task_id:
        logger.error("User ID and task ID are required for task completion")
        return False
    active_tasks = load_active_tasks(user_id)
    task_to_complete = None
    updated_active_tasks = []
    for task in active_tasks:
        if _task_matches_identifier(task, task_id):
            task_to_complete = task.copy()
            task_to_complete["status"] = "completed"
            if completion_data:
                completion_date = completion_data.get("completion_date")
                completion_time = completion_data.get("completion_time")
                completion_notes = completion_data.get("completion_notes", "")
                if completion_date and completion_time:
                    task_to_complete["completion"] = {
                        "completed": True,
                        "completed_at": f"{completion_date} {completion_time}:00",
                        "notes": completion_notes or "",
                    }
                else:
                    task_to_complete["completion"] = {
                        "completed": True,
                        "completed_at": now_timestamp_full(),
                        "notes": completion_notes or "",
                    }
            else:
                task_to_complete["completion"] = {
                    "completed": True,
                    "completed_at": now_timestamp_full(),
                    "notes": "",
                }
        else:
            updated_active_tasks.append(task)

    if not task_to_complete:
        logger.warning(f"Task {task_id} not found for user {user_id}")
        return False

    completed_tasks = load_completed_tasks(user_id)
    completed_tasks.append(task_to_complete)
    if not (save_active_tasks(user_id, updated_active_tasks) and save_completed_tasks(user_id, completed_tasks)):
        logger.error(f"Failed to save task completion for user {user_id}")
        return False

    task_title = task_to_complete.get("title", "Unknown")
    completion_time_str = (task_to_complete.get("completion") or {}).get("completed_at", "Unknown")
    logger.info(f"Completed task '{task_title}' (ID: {task_id}) for user {user_id} at {completion_time_str}")
    cleanup_task_reminders(user_id, task_id)
    if _task_recurrence(task_to_complete).get("pattern"):
        if _create_next_recurring_task_instance(user_id, task_to_complete):
            logger.info(f"Created next recurring task instance for task '{task_title}' (ID: {task_id})")
    return True


@handle_errors("restoring task", default_return=False)
def restore_task(user_id: str, task_id: str) -> bool:
    """Restore a completed task to active status."""
    if not user_id or not task_id:
        logger.error("User ID and task ID are required for task restoration")
        return False
    completed_tasks = load_completed_tasks(user_id)
    task_to_restore = None
    updated_completed_tasks = []
    for task in completed_tasks:
        if _task_matches_identifier(task, task_id):
            task_to_restore = task.copy()
            task_to_restore["status"] = "active"
            task_to_restore["completion"] = {"completed": False, "completed_at": None, "notes": ""}
        else:
            updated_completed_tasks.append(task)
    if not task_to_restore:
        logger.warning(f"Completed task {task_id} not found for user {user_id}")
        return False
    active_tasks = load_active_tasks(user_id)
    active_tasks.append(task_to_restore)
    if not (save_completed_tasks(user_id, updated_completed_tasks) and save_active_tasks(user_id, active_tasks)):
        logger.error(f"Failed to save task restoration for user {user_id}")
        return False
    logger.info(f"Restored task {task_id} for user {user_id}")
    reminder_periods = _task_reminder_periods(task_to_restore)
    if reminder_periods:
        schedule_task_reminders(user_id, task_id, reminder_periods)
    return True


@handle_errors("deleting task", default_return=False)
def delete_task(user_id: str, task_id: str) -> bool:
    """Delete a task (permanently remove it)."""
    if not user_id or not task_id:
        logger.error("User ID and task ID are required for task deletion")
        return False
    tasks = load_active_tasks(user_id)
    task_to_delete = None
    for task in tasks:
        if _task_matches_identifier(task, task_id):
            task_to_delete = task
            break
    original_count = len(tasks)
    tasks = [t for t in tasks if not _task_matches_identifier(t, task_id)]
    if len(tasks) == original_count:
        logger.warning(f"Task {task_id} not found for deletion for user {user_id}")
        return False
    if not save_active_tasks(user_id, tasks):
        logger.error(f"Failed to save task deletion for user {user_id}")
        return False
    task_title = task_to_delete.get("title", "Unknown") if task_to_delete else "Unknown"
    logger.info(f"Deleted task '{task_title}' (ID: {task_id}) for user {user_id}")
    cleanup_task_reminders(user_id, task_id)
    return True


@handle_errors("getting task by ID", default_return=None)
def get_task_by_id(user_id: str, task_id: str) -> dict[str, Any] | None:
    """Get a specific task by ID."""
    if not user_id or not task_id:
        logger.error("User ID and task ID are required for task lookup")
        return None
    for task in load_active_tasks(user_id):
        if _task_matches_identifier(task, task_id):
            return task
    for task in load_completed_tasks(user_id):
        if _task_matches_identifier(task, task_id):
            return task
    logger.debug(f"Task {task_id} not found for user {user_id}")
    return None


@handle_errors("getting tasks due soon", default_return=[])
def get_tasks_due_soon(user_id: str, days_ahead: int = 7) -> list[dict[str, Any]]:
    """Get tasks due within the specified number of days."""
    if not user_id:
        logger.error("User ID is required for getting tasks due soon")
        return []
    active_tasks = load_active_tasks(user_id)
    cutoff_date = now_datetime_full() + timedelta(days=days_ahead)
    due_soon = []
    for task in active_tasks:
        due_date_value = _task_due_date(task)
        if not due_date_value:
            continue
        due_date_dt = parse_date_only(due_date_value)
        if due_date_dt is None:
            logger.warning(f"Invalid due date format for task {_task_id(task)}")
            continue
        if due_date_dt <= cutoff_date:
            due_soon.append(task)
    due_soon.sort(key=lambda x: _task_due_date(x) or "9999-12-31")
    return due_soon


@handle_errors("checking if tasks are enabled", default_return=False)
def are_tasks_enabled(user_id: str) -> bool:
    """Check if task management is enabled for a user."""
    if not user_id:
        logger.error("User ID is required for checking task status")
        return False
    user_data_result = get_user_data(user_id, "account")
    user_account = user_data_result.get("account")
    return not (not user_account or user_account.get("features", {}).get("task_management") != "enabled")


@handle_errors("scheduling task-specific reminders", default_return=False)
def schedule_task_reminders(
    user_id: str, task_id: str, reminder_periods: list[dict[str, Any]]
) -> bool:
    """Schedule reminders for a specific task based on its reminder periods."""
    if not user_id or not task_id or not reminder_periods:
        logger.debug(f"No reminder periods to schedule for task {task_id}")
        return True
    from core.service import get_scheduler_manager
    scheduler_manager = get_scheduler_manager()
    if not scheduler_manager:
        logger.error("Scheduler manager not available for scheduling task reminders")
        return False
    scheduled_count = 0
    for period in reminder_periods:
        date = period.get("date")
        start_time = period.get("start_time")
        end_time = period.get("end_time")
        if not date or not start_time or not end_time:
            logger.warning(f"Incomplete reminder period data for task {task_id}: {period}")
            continue
        if scheduler_manager.schedule_task_reminder_at_datetime(user_id, task_id, date, start_time):
            scheduled_count += 1
            logger.info(f"Scheduled reminder for task {task_id} at {date} {start_time}")
        else:
            logger.warning(f"Failed to schedule reminder for task {task_id} at {date} {start_time}")
    logger.info(f"Scheduled {scheduled_count} reminders for task {task_id}")
    return scheduled_count > 0


@handle_errors("cleaning up task reminders", default_return=False)
def cleanup_task_reminders(user_id: str, task_id: str) -> bool:
    """Clean up all reminders for a specific task."""
    from core.service import get_scheduler_manager
    scheduler_manager = get_scheduler_manager()
    if not scheduler_manager:
        logger.warning(f"Scheduler manager not available for cleaning up task reminders for task {task_id}, user {user_id}")
        return False
    result = scheduler_manager.cleanup_task_reminders(user_id, task_id)
    if result:
        logger.info(f"Successfully cleaned up reminders for task {task_id}, user {user_id}")
    else:
        logger.warning(f"Failed to clean up reminders for task {task_id}, user {user_id} - cleanup returned False")
    return result


@handle_errors("adding user task tag", default_return=False)
def add_user_task_tag(user_id: str, tag: str) -> bool:
    """Add a new tag to the user's tag list (shared tag system)."""
    if not user_id or not tag:
        logger.error("User ID and tag are required for adding task tag")
        return False
    from core.tags import add_user_tag
    return add_user_tag(user_id, tag)


@handle_errors("setting up default task tags", default_return=False)
def setup_default_task_tags(user_id: str) -> bool:
    """Set up default tags for a user when task management is first enabled."""
    if not user_id:
        logger.error("User ID is required for setting up default task tags")
        return False
    from core.tags import get_user_tags
    existing_tags = get_user_tags(user_id)
    if existing_tags:
        logger.debug(f"User {user_id} already has tags, skipping default setup")
        return True
    logger.info(f"Tags initialized for user {user_id} with default tags from resources")
    return True


@handle_errors("removing user task tag", default_return=False)
def remove_user_task_tag(user_id: str, tag: str) -> bool:
    """Remove a tag from the user's tag list (shared tag system)."""
    if not user_id or not tag:
        logger.error("User ID and tag are required for removing task tag")
        return False
    from core.tags import remove_user_tag
    return remove_user_tag(user_id, tag)


@handle_errors("getting user task statistics", default_return={"active_count": 0, "completed_count": 0, "total_count": 0})
def get_user_task_stats(user_id: str) -> dict[str, int]:
    """Get task statistics for a user."""
    if not user_id:
        logger.error("User ID is required for getting task statistics")
        return {"active_count": 0, "completed_count": 0, "total_count": 0}
    active_tasks = load_active_tasks(user_id)
    completed_tasks = load_completed_tasks(user_id)
    stats = {
        "active_count": len(active_tasks),
        "completed_count": len(completed_tasks),
        "total_count": len(active_tasks) + len(completed_tasks),
    }
    logger.debug(f"Task statistics for user {user_id}: {stats}")
    return stats


@handle_errors("creating next recurring task instance", default_return=False)
def _create_next_recurring_task_instance(user_id: str, completed_task: dict[str, Any]) -> bool:
    """Create the next instance of a recurring task when the current one is completed."""
    if not user_id or not completed_task:
        logger.error("User ID and completed task are required for creating next recurring task")
        return False
    recurrence = _task_recurrence(completed_task)
    recurrence_pattern = recurrence.get("pattern")
    recurrence_interval = recurrence.get("interval", 1)
    repeat_after_completion = recurrence.get("repeat_after_completion", True)
    if not recurrence_pattern:
        logger.debug("No recurrence pattern found, skipping next instance creation")
        return False

    completion_date_str = (completed_task.get("completion") or {}).get("completed_at") or now_timestamp_full()
    completion_dt = parse_timestamp_full(completion_date_str)
    if completion_dt is None:
        completion_dt = parse_date_only(str(completion_date_str).split()[0])
    if completion_dt is None:
        logger.warning(f"Could not parse completion date '{completion_date_str}' for recurring task {_task_id(completed_task)}")
        return False

    next_due_date = _calculate_next_due_date(
        completion_dt, recurrence_pattern, recurrence_interval, repeat_after_completion
    )
    if not next_due_date:
        logger.warning(f"Could not calculate next due date for recurring task {_task_id(completed_task)}")
        return False
    next_due_date_str = format_timestamp(next_due_date, DATE_ONLY)

    next_task_id = str(uuid.uuid4())
    next_task = {
        "id": next_task_id,
        "short_id": generate_short_id(next_task_id, "task"),
        "kind": "task",
        "title": completed_task.get("title"),
        "description": completed_task.get("description", ""),
        "category": completed_task.get("category", ""),
        "group": completed_task.get("group", ""),
        "status": "active",
        "due": {"date": next_due_date_str, "time": _task_due_time(completed_task)},
        "created_at": now_timestamp_full(),
        "updated_at": now_timestamp_full(),
        "priority": completed_task.get("priority", "medium"),
        "recurrence": {
            "pattern": recurrence_pattern,
            "interval": recurrence_interval,
            "repeat_after_completion": repeat_after_completion,
            "next_due_date": next_due_date_str,
        },
    }
    reminder_periods = _task_reminder_periods(completed_task)
    if reminder_periods:
        next_task["reminders"] = [{"kind": "scheduled", "period": p} for p in reminder_periods if isinstance(p, dict)]
    if completed_task.get("tags"):
        next_task["tags"] = completed_task["tags"]
    for reminder in completed_task.get("reminders", []):
        if isinstance(reminder, dict) and reminder.get("kind") == "quick":
            next_task.setdefault("reminders", []).append(reminder)

    tasks = load_active_tasks(user_id)
    tasks.append(next_task)
    if not save_active_tasks(user_id, tasks):
        logger.error(f"Failed to save next recurring task instance for user {user_id}")
        return False
    logger.info(f"Created next recurring task instance for task {_task_id(completed_task)} with due date {next_due_date_str}")
    if next_task.get("reminders"):
        reminder_periods = [r.get("period") for r in next_task["reminders"] if isinstance(r, dict) and r.get("period")]
        if reminder_periods:
            schedule_task_reminders(user_id, _task_id(next_task), reminder_periods)
    return True


@handle_errors("calculating next due date for recurring task", default_return=None)
def _calculate_next_due_date(
    completion_date: datetime,
    recurrence_pattern: str,
    recurrence_interval: int,
    repeat_after_completion: bool,
) -> datetime | None:
    """Calculate the next due date for a recurring task."""
    base_date = completion_date
    if recurrence_pattern == "daily":
        return base_date + timedelta(days=recurrence_interval)
    if recurrence_pattern == "weekly":
        return base_date + timedelta(weeks=recurrence_interval)
    if recurrence_pattern == "monthly":
        year = base_date.year
        month = base_date.month + recurrence_interval
        while month > 12:
            year += 1
            month -= 12
        try:
            return base_date.replace(year=year, month=month)
        except ValueError:
            return base_date.replace(year=year, month=month, day=1)
    if recurrence_pattern == "yearly":
        return base_date.replace(year=base_date.year + recurrence_interval)
    logger.warning(f"Unknown recurrence pattern: {recurrence_pattern}")
    return None
