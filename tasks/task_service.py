# Use-case facade for task commands; delegates to the tasks package public API.

from __future__ import annotations

from typing import Any

from core.error_handling import handle_errors
from core.time_utilities import DATE_ONLY, format_timestamp, now_datetime_full, parse_date_only
from tasks.task_data_handlers import runtime_task_due_date


@handle_errors("loading tasks package", default_return=None, re_raise=True)
def _tasks():
    import tasks as t

    return t


@handle_errors("task service: create_task", user_friendly=False, re_raise=True)
def create_task(user_id: str, **kwargs: Any):
    return _tasks().create_task(user_id=user_id, **kwargs)


@handle_errors("task service: load_active_tasks", user_friendly=False, re_raise=True)
def load_active_tasks(user_id: str):
    return _tasks().load_active_tasks(user_id)


@handle_errors("task service: load_completed_tasks", user_friendly=False, re_raise=True)
def load_completed_tasks(user_id: str):
    return _tasks().load_completed_tasks(user_id)


@handle_errors("task service: get_tasks_due_soon", user_friendly=False, re_raise=True)
def get_tasks_due_soon(user_id: str, *, days_ahead: int = 7):
    return _tasks().get_tasks_due_soon(user_id, days_ahead=days_ahead)


@handle_errors("task service: complete_task", user_friendly=False, re_raise=True)
def complete_task(user_id: str, task_id: str) -> bool:
    return _tasks().complete_task(user_id, task_id)


@handle_errors("task service: restore_task", user_friendly=False, re_raise=True)
def restore_task(user_id: str, task_id: str) -> bool:
    return _tasks().restore_task(user_id, task_id)


@handle_errors("task service: delete_task", user_friendly=False, re_raise=True)
def delete_task(user_id: str, task_id: str) -> bool:
    return _tasks().delete_task(user_id, task_id)


@handle_errors("task service: update_task", user_friendly=False, re_raise=True)
def update_task(user_id: str, task_id: str, updates: dict[str, Any]) -> bool:
    return _tasks().update_task(user_id, task_id, updates)


@handle_errors("task service: get_user_task_stats", user_friendly=False, re_raise=True)
def get_user_task_stats(user_id: str):
    return _tasks().get_user_task_stats(user_id)


@handle_errors("task service: task identifier", default_return="")
def task_identifier(task: dict[str, Any]) -> str:
    """Return canonical task id for matching and mutations."""
    return str(task.get("id") or "")


@handle_errors("task service: task short identifier", default_return="")
def task_short_identifier(task: dict[str, Any]) -> str:
    """Return canonical task short_id for matching and display."""
    return str(task.get("short_id") or "")


# not_duplicate: task_identifier_service_facade
@handle_errors("task service: find task by identifier", default_return=None)
def find_task_by_identifier(
    tasks: list[dict[str, Any]], identifier: str
) -> dict[str, Any] | None:
    """Find a task by number, name, canonical id, or short_id."""
    if not identifier or not tasks:
        return None

    for task in tasks:
        if task_identifier(task) == identifier or task_short_identifier(task) == identifier:
            return task

    try:
        task_num = int(identifier)
        if 1 <= task_num <= len(tasks):
            return tasks[task_num - 1]
    except ValueError:
        pass

    identifier_lower = identifier.lower().strip()
    for task in tasks:
        if identifier_lower == task.get("title", "").lower():
            return task

    for task in tasks:
        if identifier_lower in task.get("title", "").lower():
            return task

    identifier_words = set(identifier_lower.split())
    for task in tasks:
        task_words = set(task.get("title", "").lower().split())
        if identifier_words & task_words:
            return task

    common_variations = {
        "teeth": ["brush", "brushing", "tooth", "dental"],
        "hair": ["wash", "washing", "shampoo"],
        "dishes": ["wash", "washing", "clean", "cleaning"],
        "laundry": ["wash", "washing", "clothes"],
        "exercise": ["workout", "gym", "run", "running", "walk", "walking"],
        "medication": ["meds", "medicine", "pill", "pills"],
        "appointment": ["doctor", "dentist", "meeting", "call"],
    }

    for task in tasks:
        task_lower = task.get("title", "").lower()
        for variation_key, variations in common_variations.items():
            if (
                identifier_lower in variations or identifier_lower == variation_key
            ) and any(var in task_lower for var in variations + [variation_key]):
                return task

    return None


@handle_errors("task service: get task candidates", default_return=[])
def get_task_candidates(
    tasks: list[dict[str, Any]], identifier: str
) -> list[dict[str, Any]]:
    """Return candidate tasks matching identifier by id, number, or name."""
    for task in tasks:
        if identifier == task_identifier(task) or identifier == task_short_identifier(task):
            return [task]
    try:
        task_num = int(identifier)
        if 1 <= task_num <= len(tasks):
            return [tasks[task_num - 1]]
    except ValueError:
        pass

    ident = str(identifier).lower().strip()
    exact = [task for task in tasks if task.get("title", "").lower() == ident]
    if exact:
        return exact
    contains = [task for task in tasks if ident in task.get("title", "").lower()]
    if contains:
        return contains
    words = set(ident.split())
    word_hits = [
        task for task in tasks if words & set(task.get("title", "").lower().split())
    ]
    if word_hits:
        return word_hits
    return []


@handle_errors("task service: find most urgent task", default_return=None)
def find_most_urgent_task(tasks: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Find the most urgent task based on overdue status, priority, and due date."""
    if not tasks:
        return None

    today = format_timestamp(now_datetime_full(), DATE_ONLY)
    today_dt = parse_date_only(today)
    priority_order = {"critical": 5, "high": 4, "medium": 3, "low": 2}

    most_urgent = None
    highest_score = -1
    for task in tasks:
        score = 0
        due_date = runtime_task_due_date(task)
        if due_date and due_date < today:
            score += 1000

        priority = task.get("priority", "medium")
        score += priority_order.get(priority, 0)
        due_dt = parse_date_only(due_date) if due_date else None
        if due_dt and today_dt:
            days_until_due = (due_dt - today_dt).days
            if days_until_due <= 0:
                score += 50
            elif days_until_due <= 1:
                score += 30
            elif days_until_due <= 3:
                score += 10

        if score > highest_score:
            highest_score = score
            most_urgent = task

    return most_urgent
