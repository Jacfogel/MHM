"""Rewrite a task into a smaller version without changing the due date."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger
from tasks.task_data_handlers import runtime_task_due_date, runtime_task_is_completed
from tasks.task_validation import is_valid_task_title

logger = get_component_logger("main")


@dataclass(frozen=True)
class TaskSimplifyResult:
    """Outcome of shrinking a task title."""

    success: bool
    message: str
    previous_title: str = ""
    new_title: str = ""
    needs_title: bool = False


@handle_errors("keeping the previous title in task notes", default_return="")
def _description_with_previous_title(task: dict[str, Any], previous_title: str) -> str:
    """Remember the larger title in notes when the visible title shrinks."""
    existing = str(task.get("description") or "").strip()
    note = f"Was: {previous_title}"
    if note in existing:
        return existing
    return f"{note}\n\n{existing}" if existing else note


@handle_errors("simplifying a task", default_return=None)
def simplify_task(
    user_id: str,
    task_id: str,
    new_title: str | None,
) -> TaskSimplifyResult:
    """Replace the task title with a smaller version. Due date stays the same."""
    if not user_id or not task_id:
        return TaskSimplifyResult(False, "I need a task to simplify.")
    from tasks.task_data_manager import get_task_by_id, update_task

    task = get_task_by_id(user_id, task_id)
    if not task:
        return TaskSimplifyResult(
            False, "I could not find that task, so I did not change it."
        )
    if runtime_task_is_completed(task):
        return TaskSimplifyResult(
            False, "That task is already completed, so there is nothing to simplify."
        )
    previous_title = str(task.get("title") or "").strip() or "this task"
    cleaned = str(new_title or "").strip()
    if not is_valid_task_title(cleaned):
        return TaskSimplifyResult(
            True,
            f"What's a smaller version of **{previous_title}**?\n"
            "Reply like `simplify that to wipe the kitchen counter`.",
            previous_title=previous_title,
            needs_title=True,
        )
    if cleaned.casefold() == previous_title.casefold():
        return TaskSimplifyResult(
            True,
            f"**{previous_title}** is already that small. You can still complete it, "
            "skip this time, or snooze the reminder.",
            previous_title=previous_title,
            new_title=cleaned,
        )
    saved = update_task(
        user_id,
        task_id,
        {
            "title": cleaned,
            "description": _description_with_previous_title(task, previous_title),
        },
    )
    if not saved:
        return TaskSimplifyResult(
            False, "I could not simplify that task. Please try again."
        )
    due = runtime_task_due_date(task)
    due_bit = f" Due date stays {due}." if due else " Due date stays the same."
    logger.info(
        f"Simplified task {task_id} for user {user_id} from '{previous_title}' to '{cleaned}'"
    )
    return TaskSimplifyResult(
        True,
        f"Okay. I shrunk **{previous_title}** to **{cleaned}**.{due_bit}",
        previous_title=previous_title,
        new_title=cleaned,
    )
