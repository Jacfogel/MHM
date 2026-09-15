"""Skip one task occurrence without treating it as completed work."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.natural_language_defaults import get_natural_language_defaults
from core.time_utilities import (
    DATE_ONLY,
    TIME_ONLY_MINUTE,
    TIMESTAMP_FULL,
    format_timestamp,
    now_datetime_full,
    parse_date_only,
)
from tasks.task_data_handlers import (
    runtime_task_due_date,
    runtime_task_due_time,
    runtime_task_is_completed,
    runtime_task_recurrence_interval,
    runtime_task_recurrence_pattern,
)
from tasks.task_reminder_snooze import snooze_task_reminder
from tasks.task_time_parsing import parse_time_string

logger = get_component_logger("main")


@dataclass(frozen=True)
class TaskOccurrenceSkipResult:
    """Outcome of skipping one task occurrence."""

    success: bool
    message: str
    next_due: str | None = None
    recurring: bool = False


@handle_errors("combining skip due date and time", default_return=None)
def _due_datetime(day: datetime, due_time: str | None, user_id: str | None) -> datetime:
    """Return *day* at the task due time, or the user's morning default."""
    clock = parse_time_string(due_time or "") or ""
    if not clock:
        defaults = get_natural_language_defaults(user_id)
        clock = (
            parse_time_string(str(defaults.time_of_day_defaults.get("morning") or "9:00"))
            or "09:00"
        )
    parts = clock.split(":")
    hour = int(parts[0]) if parts else 9
    minute = int(parts[1]) if len(parts) > 1 else 0
    return day.replace(hour=hour, minute=minute, second=0, microsecond=0)


@handle_errors("choosing skip recurrence base date", default_return=None)
def _skip_recurrence_base(task: dict[str, Any], now_dt: datetime) -> datetime:
    """Use today's or a still-future due date as the skipped occurrence."""
    due_raw = runtime_task_due_date(task)
    due_day = parse_date_only(due_raw) if due_raw else None
    if due_day is not None and due_day.date() >= now_dt.date():
        return due_day
    return now_dt


@handle_errors("appending a skipped-occurrence note", default_return="")
def _with_skip_note(task: dict[str, Any], skipped_on: str, next_due: str) -> str:
    """Keep existing notes and record that this occurrence was skipped."""
    existing = str(task.get("description") or "").strip()
    note = f"Skipped this time on {skipped_on}. Next due {next_due}."
    return f"{existing}\n\n{note}" if existing else note


@handle_errors("skipping a recurring task occurrence", default_return=None)
def _skip_recurring_occurrence(
    user_id: str,
    task_id: str,
    task: dict[str, Any],
    now_dt: datetime,
) -> TaskOccurrenceSkipResult:
    """Advance the due date to the next occurrence and wait to ping until then."""
    from tasks.task_data_manager import _calculate_next_due_date, update_task

    pattern = runtime_task_recurrence_pattern(task)
    interval = runtime_task_recurrence_interval(task)
    next_due_dt = _calculate_next_due_date(
        _skip_recurrence_base(task, now_dt), pattern, interval, True
    )
    if next_due_dt is None:
        return TaskOccurrenceSkipResult(
            False,
            "I could not figure out the next time for that repeating task.",
        )
    if next_due_dt.date() <= now_dt.date():
        next_due_dt = _calculate_next_due_date(now_dt, pattern, interval, True)
    if next_due_dt is None:
        return TaskOccurrenceSkipResult(
            False,
            "I could not figure out the next time for that repeating task.",
        )
    next_due = format_timestamp(next_due_dt, DATE_ONLY)
    skipped_on = format_timestamp(now_dt, DATE_ONLY)
    ping_at = _due_datetime(next_due_dt, runtime_task_due_time(task), user_id)
    if ping_at <= now_dt:
        ping_at = now_dt + timedelta(minutes=1)
    title = str(task.get("title") or "this task")
    saved = update_task(
        user_id,
        task_id,
        {
            "due_date": next_due,
            "next_due_date": next_due,
            "description": _with_skip_note(task, skipped_on, next_due),
            "reminder_sent": True,
            "reminder_snooze_until": format_timestamp(ping_at, TIMESTAMP_FULL),
        },
    )
    if not saved:
        return TaskOccurrenceSkipResult(
            False, "I could not skip that occurrence. Please try again."
        )
    from scheduler.runtime_access import get_scheduler_manager

    scheduler_manager = get_scheduler_manager()
    if scheduler_manager:
        scheduler_manager.schedule_task_reminder_at_datetime(
            user_id,
            task_id,
            format_timestamp(ping_at, DATE_ONLY),
            format_timestamp(ping_at, TIME_ONLY_MINUTE),
        )
    logger.info(
        f"Skipped occurrence of task {task_id} for user {user_id}; next due {next_due}"
    )
    return TaskOccurrenceSkipResult(
        True,
        f"Okay. I skipped this time for **{title}**. Next one is due {next_due}. "
        "That is not a failure.",
        next_due=next_due,
        recurring=True,
    )


@handle_errors("skipping a one-off task reminder", default_return=None)
def _skip_one_off_occurrence(
    user_id: str,
    task_id: str,
    task: dict[str, Any],
    now_dt: datetime,
) -> TaskOccurrenceSkipResult:
    """Leave a one-off task on the list and stop pinging until tomorrow morning."""
    snoozed = snooze_task_reminder(
        user_id,
        task_id,
        "custom",
        custom_when="tomorrow morning",
        now_dt=now_dt,
    )
    if not snoozed.success:
        return TaskOccurrenceSkipResult(
            False, snoozed.message or "I could not skip that reminder right now."
        )
    title = str(task.get("title") or "this task")
    due = runtime_task_due_date(task)
    due_bit = f" It is still due {due}." if due else ""
    return TaskOccurrenceSkipResult(
        True,
        f"Okay. **{title}** stays on your list.{due_bit} "
        "I will not ping you about it until tomorrow morning.",
        next_due=due,
        recurring=False,
    )


@handle_errors("skipping a task occurrence", default_return=None)
def skip_task_occurrence(
    user_id: str,
    task_id: str,
    *,
    now_dt: datetime | None = None,
) -> TaskOccurrenceSkipResult:
    """Skip this occurrence. Recurring tasks roll forward; one-off tasks stay due."""
    if not user_id or not task_id:
        return TaskOccurrenceSkipResult(False, "I need a task to skip.")
    from tasks.task_data_manager import get_task_by_id

    task = get_task_by_id(user_id, task_id)
    if not task:
        return TaskOccurrenceSkipResult(
            False, "I could not find that task, so I did not skip it."
        )
    if runtime_task_is_completed(task):
        return TaskOccurrenceSkipResult(
            False, "That task is already completed, so there is nothing to skip."
        )
    now_dt = now_dt or now_datetime_full()
    if runtime_task_recurrence_pattern(task):
        return _skip_recurring_occurrence(user_id, task_id, task, now_dt)
    return _skip_one_off_occurrence(user_id, task_id, task, now_dt)
