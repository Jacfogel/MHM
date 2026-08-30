"""Resolve pronoun task references such as 'that' from recent chat and recency."""

from __future__ import annotations

import re
from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.response_tracking import get_recent_chat_interactions
from core.time_utilities import now_datetime_full, parse_timestamp_full, timestamp_sort_key_from_dict
from tasks.task_data_handlers import load_active_tasks, load_completed_tasks

logger = get_component_logger("main")

PRONOUN_TASK_IDENTIFIERS = frozenset(
    {
        "that",
        "it",
        "this",
        "that task",
        "this task",
        "the task",
        "it task",
    }
)

_PRONOUN_FOLLOW_UP_RE = re.compile(
    r"(?i)(?:"
    r"\b(?:make|set|change|update|mark|cross|check)\s+(?:that|it|this)\b"
    r"|(?:that|it|this)(?:'s|\s+is)\s+(?:due|urgent|critical|high|medium|low)"
    r"|\b(?:done|complete(?:d)?)\s+with\s+(?:that|it|this)\b"
    r"|\bnote\s+to\s+(?:that|it|this)\b"
    r"|\b(?:cross|check)\s+(?:that|it|this)\s+off\b"
    r"|\blink\s+to\s+(?:that|it|this)\b"
    r")"
)

_RECENT_TOUCH_MINUTES = 30
_TITLE_MATCH_MIN_LENGTH = 3

_PRONOUN_RESOLVABLE_ACTIONS = frozenset(
    {
        "update_task",
        "complete_task",
        "append_note_to_task",
        "add_link_to_task",
    }
)


@handle_errors("checking pronoun task identifier", default_return=False)
def is_pronoun_task_identifier(identifier: str | None) -> bool:
    """Return True when the identifier is a follow-up pronoun, not a real task name."""
    return str(identifier or "").strip().casefold() in PRONOUN_TASK_IDENTIFIERS


@handle_errors("detecting pronoun task follow-up", default_return=False)
def message_uses_task_pronoun(text: str | None) -> bool:
    """Return True when the message updates/completes a previously mentioned task."""
    return bool(_PRONOUN_FOLLOW_UP_RE.search(str(text or "")))


@handle_errors("checking if action can use a pronoun task", default_return=False)
def action_accepts_pronoun_task(action_name: str | None) -> bool:
    """Return True when a planned action can fill TASK_IDENTIFIER with 'that'."""
    return str(action_name or "").strip() in _PRONOUN_RESOLVABLE_ACTIONS


@handle_errors("loading recent user turns for task reference", default_return=[])
def _recent_user_turns(user_id: str) -> list[str]:
    """Return recent user chat lines, oldest first."""
    if not user_id:
        return []
    turns: list[str] = []
    seen: set[str] = set()
    for exchange in reversed(get_recent_chat_interactions(user_id, limit=5) or []):
        text = str(exchange.get("user_message") or "").strip()
        key = text.casefold()
        if not text or key in seen:
            continue
        seen.add(key)
        turns.append(text)
        if len(turns) >= 2:
            break
    turns.reverse()
    return turns


@handle_errors("scoring task recency", default_return=0.0)
def _task_recency_key(task: dict[str, Any]) -> float:
    """Return a sort key from completion, updated_at, then created_at."""
    completion = task.get("completion")
    if isinstance(completion, dict):
        completed_at = parse_timestamp_full(str(completion.get("completed_at") or ""))
        if completed_at is not None:
            return completed_at.timestamp()
    updated = timestamp_sort_key_from_dict(task, "updated_at")
    if updated:
        return updated
    return timestamp_sort_key_from_dict(task, "created_at")


@handle_errors("checking whether a task was touched recently", default_return=False)
def _is_recently_touched(task: dict[str, Any], *, minutes: int = _RECENT_TOUCH_MINUTES) -> bool:
    """Return True when the task was created, updated, or completed recently."""
    raw = str(task.get("updated_at") or task.get("created_at") or "")
    touched = parse_timestamp_full(raw)
    completion = task.get("completion")
    if isinstance(completion, dict):
        completed_at = parse_timestamp_full(str(completion.get("completed_at") or ""))
        if completed_at is not None and (touched is None or completed_at > touched):
            touched = completed_at
    if touched is None:
        return False
    delta_seconds = (now_datetime_full() - touched).total_seconds()
    return 0 <= delta_seconds <= minutes * 60


@handle_errors("matching tasks mentioned in recent turns", default_return=[])
def _tasks_mentioned_in_turns(
    tasks: list[dict[str, Any]], recent_turns: list[str]
) -> list[dict[str, Any]]:
    """Return tasks whose titles appear in recent user turns, longest title first."""
    if not tasks or not recent_turns:
        return []
    combined = "\n".join(recent_turns).casefold()
    ranked: list[tuple[int, dict[str, Any]]] = []
    for task in tasks:
        title = str(task.get("title") or "").strip()
        if len(title) < _TITLE_MATCH_MIN_LENGTH:
            continue
        if title.casefold() in combined:
            ranked.append((len(title), task))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [task for _, task in ranked]


@handle_errors("resolving a pronoun to an active task", default_return=None)
def resolve_pronoun_task(
    user_id: str,
    *,
    recent_turns: list[str] | None = None,
) -> dict[str, Any] | None:
    """Choose the task a follow-up like 'make that due tomorrow' refers to.

    Prefers a title mentioned in recent chat, then a uniquely recent active
    task. Does not fall back to a leftover task after a more recent
    completion. Returns None when the reference is ambiguous.
    """
    if not user_id:
        return None
    tasks = load_active_tasks(user_id) or []
    if not tasks:
        return None

    turns = list(recent_turns) if recent_turns is not None else _recent_user_turns(user_id)
    mentioned = _tasks_mentioned_in_turns(tasks, turns)
    if len(mentioned) == 1:
        return mentioned[0]
    if mentioned:
        return max(mentioned, key=_task_recency_key)

    recent_completed = [
        task for task in (load_completed_tasks(user_id) or []) if _is_recently_touched(task)
    ]
    latest_completed = max((_task_recency_key(task) for task in recent_completed), default=0.0)
    recent_active = [task for task in tasks if _is_recently_touched(task)]
    if not recent_active:
        return None
    latest_active = max(recent_active, key=_task_recency_key)
    if latest_completed >= _task_recency_key(latest_active):
        return None
    if len(recent_active) == 1:
        return recent_active[0]
    return latest_active


@handle_errors("resolving lookup identifier for a task command", default_return=None)
def resolve_lookup_identifier(
    user_id: str,
    identifier: str | None,
    *,
    recent_turns: list[str] | None = None,
) -> str | None:
    """Return a concrete task id for pronoun identifiers, or the original identifier."""
    if not is_pronoun_task_identifier(identifier):
        text = str(identifier or "").strip()
        return text or None
    task = resolve_pronoun_task(user_id, recent_turns=recent_turns)
    if not task:
        return None
    task_id = str(task.get("id") or "").strip()
    return task_id or None
