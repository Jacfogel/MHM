"""Route an email reply to the check-in or task it answers."""

from __future__ import annotations

import re

from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from communication.message_processing.conversation_flow_manager import (
    conversation_manager,
)
from core.error_handling import handle_errors
from core.logger import get_component_logger
from tasks.task_reminder_snooze import normalize_snooze_option

logger = get_component_logger("communication_manager")

_COMPLETE = {
    "done",
    "complete",
    "completed",
    "finished",
    "did it",
    "i did it",
    "yes",
    "yep",
    "mark done",
    "mark it done",
}
_COMPLETE_FIRST = {"done", "complete", "completed", "finished"}
_SNOOZE_BARE = {"later", "not now", "remind me later", "snooze", "remind me"}
_SKIP = {"skip", "skip this", "skip this time", "not this time", "skip it"}
_TASK_HELP = (
    "Reply with done, later, skip, or simplify to <smaller step>. "
    "Example: simplify to wipe the kitchen counter. "
    "For later, you can also say 1 hour, tonight, next week, or until Friday 3pm."
)


@handle_errors("building a task reply command", default_return=None)
def build_task_reply_command(text: str, task_id: str) -> ParsedCommand | None:
    """Map a short email reply onto the task it is answering."""
    if not text or not task_id:
        return None
    original = text.strip()
    cleaned = " ".join(original.lower().split())
    if not cleaned:
        return None
    first = cleaned.split(" ", 1)[0]
    if cleaned in _COMPLETE or first in _COMPLETE_FIRST:
        return ParsedCommand(
            "complete_task", {"task_identifier": task_id}, 1.0, original
        )
    if cleaned in _SKIP or first == "skip":
        return ParsedCommand(
            "skip_task_occurrence", {"task_identifier": task_id}, 1.0, original
        )
    if cleaned == "simplify" or cleaned.startswith("simplify "):
        title = original[8:].strip() if original.lower().startswith("simplify") else ""
        if title.lower().startswith("to "):
            title = title[3:].strip()
        entities: dict[str, str] = {"task_identifier": task_id}
        if title:
            entities["simplified_title"] = title
        return ParsedCommand("simplify_task", entities, 1.0, original)
    if cleaned in _SNOOZE_BARE or first in {"later", "snooze"}:
        return ParsedCommand(
            "snooze_task_reminder", {"task_identifier": task_id}, 1.0, original
        )
    snooze_text = cleaned[3:].strip() if cleaned.startswith("in ") else cleaned
    option = normalize_snooze_option(snooze_text)
    if option and option != "custom":
        return ParsedCommand(
            "snooze_task_reminder",
            {"task_identifier": task_id, "snooze_option": option},
            1.0,
            original,
        )
    if cleaned.startswith("until "):
        when = original.split(" ", 1)[1].strip() if " " in original else original
        return ParsedCommand(
            "snooze_task_reminder",
            {
                "task_identifier": task_id,
                "snooze_option": "custom",
                "snooze_when": when,
            },
            1.0,
            original,
        )
    if re.match(r"^in \d+ (minutes?|hours?|days?|weeks?)$", cleaned):
        return ParsedCommand(
            "snooze_task_reminder",
            {
                "task_identifier": task_id,
                "snooze_option": "custom",
                "snooze_when": original.strip(),
            },
            1.0,
            original,
        )
    if cleaned in {"tomorrow morning", "tomorrow"}:
        return ParsedCommand(
            "snooze_task_reminder",
            {"task_identifier": task_id, "snooze_option": "tonight"},
            1.0,
            original,
        )
    return None


@handle_errors("routing a check-in email reply", default_return=None)
def route_checkin_reply(user_id: str, text: str) -> InteractionResponse | None:
    """Answer the open check-in. Return None when that check-in is no longer active."""
    result = conversation_manager.answer_active_checkin(user_id, text)
    if result is None:
        return None
    reply, completed = result
    return InteractionResponse(reply or "", bool(completed))


@handle_errors(
    "routing a task reminder email reply",
    default_return=InteractionResponse(_TASK_HELP, True),
)
def route_task_reply(user_id: str, text: str, task_id: str) -> InteractionResponse:
    """Apply a reply to the task reminder it answers, without using another open flow."""
    if not task_id:
        logger.warning(f"Task reminder email reply for user {user_id} had no task id")
        return InteractionResponse(_TASK_HELP, True)

    from communication.command_handlers.task_handler import (
        PENDING_SIMPLIFY,
        TaskManagementHandler,
    )

    command = build_task_reply_command(text, task_id)
    if command is None and user_id in PENDING_SIMPLIFY and text.strip():
        command = ParsedCommand(
            "simplify_task",
            {"task_identifier": task_id, "simplified_title": text.strip()},
            1.0,
            text.strip(),
        )
    if command is None:
        return InteractionResponse(_TASK_HELP, True)
    return TaskManagementHandler().handle(user_id, command)
