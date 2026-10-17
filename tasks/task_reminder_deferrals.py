"""Bounded reminder-deferral history and useful repeated-deferral guidance."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from core.error_handling import handle_errors
from core.time_utilities import TIMESTAMP_FULL, format_timestamp, now_datetime_full, parse_timestamp_full
from tasks.task_data_handlers import runtime_task_due_date

MAX_REMINDER_DEFERRALS = 5
REPEATED_DEFERRAL_COUNT = 2
RECONSIDER_DUE_DATE_COUNT = 3

DeferralAction = Literal["snooze", "skip"]


@handle_errors("normalizing reminder deferral history", default_return=[])
def normalize_reminder_deferrals(value: Any) -> list[dict[str, str]]:
    """Return at most the five newest valid snooze and skip records."""
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        action = str(item.get("action") or "").strip().lower()
        at = str(item.get("at") or "").strip()
        until = str(item.get("until") or "").strip()
        if action not in {"snooze", "skip"} or parse_timestamp_full(at) is None:
            continue
        record = {"action": action, "at": at}
        if until and parse_timestamp_full(until) is not None:
            record["until"] = until
        normalized.append(record)
    return normalized[-MAX_REMINDER_DEFERRALS:]


@handle_errors("appending reminder deferral history", default_return=[])
def append_reminder_deferral(
    task: dict[str, Any],
    action: DeferralAction,
    *,
    occurred_at: datetime | None = None,
    until: datetime | None = None,
) -> list[dict[str, str]]:
    """Append one deferral and discard records older than the bounded history."""
    history = normalize_reminder_deferrals(task.get("reminder_deferrals"))
    record = {
        "action": action,
        "at": format_timestamp(occurred_at or now_datetime_full(), TIMESTAMP_FULL),
    }
    if until is not None:
        record["until"] = format_timestamp(until, TIMESTAMP_FULL)
    return (history + [record])[-MAX_REMINDER_DEFERRALS:]


@handle_errors("counting reminder deferrals", default_return=0)
def reminder_deferral_count(task: dict[str, Any] | None) -> int:
    """Return the number of retained snooze and skip records for a task."""
    if not isinstance(task, dict):
        return 0
    return len(normalize_reminder_deferrals(task.get("reminder_deferrals")))


@handle_errors("building repeated reminder deferral guidance", default_return="")
def repeated_deferral_advice(
    task: dict[str, Any], *, focus_step: dict[str, Any] | None = None
) -> str:
    """Change reminder guidance after repeated deferrals instead of repeating copy."""
    count = reminder_deferral_count(task)
    if count < REPEATED_DEFERRAL_COUNT:
        return ""

    if focus_step:
        advice = (
            "This has been deferred a few times, so I’m showing the next smaller step "
            "instead of the whole task."
        )
    else:
        advice = (
            "This has been deferred a few times. **Simplify** can turn it into a smaller "
            "next step."
        )
    if count >= RECONSIDER_DUE_DATE_COUNT and runtime_task_due_date(task):
        advice += " If the date no longer fits, it may be worth reconsidering the due date."
    return advice
