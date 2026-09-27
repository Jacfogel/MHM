"""Suggest smaller steps for a task and save the chosen ones as subtasks."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger
from tasks.task_validation import is_valid_task_title

logger = get_component_logger(__name__)

MAX_SUGGESTED_STEPS = 5
MAX_OPEN_SUBTASKS = 8
_STEP_PREFIX = re.compile(r"^(?:[-*•]+|\d+[.)])\s*")


@dataclass(frozen=True)
class TaskBreakdownResult:
    """Suggested steps, or the subtasks that were saved."""

    success: bool
    message: str
    steps: list[str] = field(default_factory=list)
    unavailable: bool = False


@handle_errors("reading suggested task steps", default_return=[])
def parse_task_step_lines(text: str) -> list[str]:
    """Keep short, unique task titles from a model reply."""
    found: list[str] = []
    seen: set[str] = set()
    for raw_line in str(text or "").splitlines():
        line = _STEP_PREFIX.sub("", raw_line.strip()).strip(" \"'")
        if not line or len(line) > 120 or not is_valid_task_title(line):
            continue
        if line.endswith(":") and len(line.split()) <= 4:
            continue
        key = line.casefold()
        if key in seen:
            continue
        seen.add(key)
        found.append(line)
        if len(found) == MAX_SUGGESTED_STEPS:
            break
    return found


@handle_errors("reading a task parent id", default_return="")
def _parent_id(task: dict[str, Any]) -> str:
    """Return the parent task id, or an empty string when this task is top-level."""
    return str(task.get("parent_id") or "").strip()


@handle_errors("reading a task id", default_return="")
def _task_id(task: dict[str, Any]) -> str:
    """Return the task id, or an empty string when it is missing."""
    return str(task.get("id") or "").strip()


@handle_errors("listing open subtasks", default_return=[])
def _open_children(tasks: list[dict[str, Any]], parent_id: str) -> list[dict[str, Any]]:
    """Return active tasks saved under this parent."""
    return [
        task
        for task in tasks
        if _parent_id(task) == parent_id and str(task.get("status") or "active") == "active"
    ]


@handle_errors("suggesting smaller task steps", default_return=None)
def suggest_breakdown(user_id: str, task_id: str) -> TaskBreakdownResult | None:
    """Ask the model for a few concrete steps under this task."""
    if not user_id or not task_id:
        return TaskBreakdownResult(False, "I need a task to break down.")
    from tasks.task_data_manager import get_task_by_id
    from tasks.task_service import load_active_tasks

    task = get_task_by_id(user_id, task_id)
    if not task:
        return TaskBreakdownResult(False, "I could not find that task.")
    if str(task.get("status") or "") == "completed":
        return TaskBreakdownResult(False, "That task is already done.")
    if _parent_id(task):
        return TaskBreakdownResult(
            False, "That step is already a smaller part of another task."
        )
    title = str(task.get("title") or "").strip()
    if not title:
        return TaskBreakdownResult(False, "That task needs a title before it can be broken down.")
    parent_id = _task_id(task)
    existing = _open_children(load_active_tasks(user_id) or [], parent_id)
    if len(existing) >= MAX_OPEN_SUBTASKS:
        return TaskBreakdownResult(
            False,
            "This task already has enough smaller steps. Finish one of those first.",
        )
    from ai.chat.chatbot import get_ai_chatbot
    from ai.client.lm_studio_client import call_lm_studio_api
    from core.config import AI_COMMAND_PARSING_TIMEOUT

    if not get_ai_chatbot().is_ai_available():
        logger.info("Skipping task breakdown because the model is unavailable")
        return TaskBreakdownResult(
            False,
            "MHM could not suggest smaller steps just now. Please try again.",
            unavailable=True,
        )
    description = str(task.get("description") or "").replace("\n", " ").strip()[:400]
    notes = f"\nNotes: {description}" if description else ""
    already = "\n".join(
        f"Already added: {str(child.get('title') or '').strip()}"
        for child in existing
        if str(child.get("title") or "").strip()
    )
    already_block = f"\n{already}" if already else ""
    messages = [
        {
            "role": "system",
            "content": (
                "Break this task into 3 to 5 smaller steps one person can do in one sitting. "
                "Each line is a short task title under 80 characters. "
                "Reply with one title per line. No numbers, bullets, or explanation. "
                "Do not repeat the original task or a step that was already added."
            ),
        },
        {"role": "user", "content": f"Task: {title}{notes}{already_block}"},
    ]
    raw = call_lm_studio_api(
        messages=messages,
        max_tokens=220,
        temperature=0.2,
        timeout=AI_COMMAND_PARSING_TIMEOUT,
    )
    existing_titles = {
        str(child.get("title") or "").strip().casefold() for child in existing
    }
    steps = [
        step
        for step in parse_task_step_lines(raw or "")
        if step.casefold() != title.casefold() and step.casefold() not in existing_titles
    ]
    if not steps:
        return TaskBreakdownResult(
            False,
            "MHM could not find smaller steps for this. Please try again.",
            unavailable=True,
        )
    return TaskBreakdownResult(True, "Here are a few smaller steps.", steps=steps)


@handle_errors("adding task subtasks", default_return=None)
def add_task_subtasks(
    user_id: str,
    task_id: str,
    titles: list[str] | None,
) -> TaskBreakdownResult | None:
    """Save chosen steps as tasks under the original task. The original title stays."""
    if not user_id or not task_id:
        return TaskBreakdownResult(False, "I need a task to add steps to.")
    from tasks.task_data_manager import get_task_by_id
    from tasks.task_service import create_task, load_active_tasks

    task = get_task_by_id(user_id, task_id)
    if not task:
        return TaskBreakdownResult(False, "I could not find that task.")
    if str(task.get("status") or "") == "completed":
        return TaskBreakdownResult(False, "That task is already done.")
    if _parent_id(task):
        return TaskBreakdownResult(
            False, "That step is already a smaller part of another task."
        )
    parent_id = _task_id(task)
    parent_title = str(task.get("title") or "").strip() or "this task"
    active = load_active_tasks(user_id) or []
    existing = _open_children(active, parent_id)
    room = MAX_OPEN_SUBTASKS - len(existing)
    if room <= 0:
        return TaskBreakdownResult(
            False,
            "This task already has enough smaller steps. Finish one of those first.",
        )
    seen = {str(child.get("title") or "").strip().casefold() for child in existing}
    chosen: list[str] = []
    for raw_title in titles or []:
        title = str(raw_title or "").strip()
        if not is_valid_task_title(title) or len(title) > 120:
            continue
        key = title.casefold()
        if key in seen or key == parent_title.casefold():
            continue
        seen.add(key)
        chosen.append(title)
        if len(chosen) >= min(MAX_SUGGESTED_STEPS, room):
            break
    if not chosen:
        return TaskBreakdownResult(
            False, "Those steps were empty or already on this task."
        )
    due = task.get("due") if isinstance(task.get("due"), dict) else {}
    due_date = due.get("date")
    due_time = due.get("time")
    tags = task.get("tags") if isinstance(task.get("tags"), list) else []
    priority = str(task.get("priority") or "medium")
    saved = 0
    for title in chosen:
        created_id = create_task(
            user_id,
            title=title,
            due_date=due_date,
            due_time=due_time,
            priority=priority,
            tags=tags,
            parent_id=parent_id,
        )
        if created_id:
            saved += 1
    if saved == 0:
        return TaskBreakdownResult(False, "I could not save those steps. Please try again.")
    step_word = "step" if saved == 1 else "steps"
    logger.info(
        f"Added {saved} subtask(s) under {parent_id} for user {user_id}"
    )
    return TaskBreakdownResult(
        True,
        f"Added {saved} smaller {step_word} under {parent_title}. The original task stays.",
        steps=chosen[:saved],
    )
