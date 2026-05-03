# Use-case facade for task commands; delegates to the tasks package public API.

from __future__ import annotations

from typing import Any

from core.error_handling import handle_errors


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
