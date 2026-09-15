"""Snooze a task reminder without changing the task due date."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.natural_language_defaults import (
    NaturalLanguageDefaults,
    get_natural_language_defaults,
    is_past_time_of_day,
)
from core.time_utilities import (
    DATE_ONLY,
    TIME_ONLY_MINUTE,
    TIMESTAMP_FULL,
    format_timestamp,
    now_datetime_full,
    parse_date_only,
    parse_timestamp_full,
)
from tasks.task_data_handlers import runtime_task_due_date, runtime_task_is_completed
from tasks.task_time_parsing import parse_time_string

logger = get_component_logger("main")

SNOOZE_1_HOUR = "1_hour"
SNOOZE_TONIGHT = "tonight"
SNOOZE_NEXT_WEEK = "next_week"
SNOOZE_CUSTOM = "custom"

_SNOOZE_OPTION_ALIASES = {
    "1_hour": SNOOZE_1_HOUR,
    "1 hour": SNOOZE_1_HOUR,
    "an hour": SNOOZE_1_HOUR,
    "one hour": SNOOZE_1_HOUR,
    "hour": SNOOZE_1_HOUR,
    "tonight": SNOOZE_TONIGHT,
    "next_week": SNOOZE_NEXT_WEEK,
    "next week": SNOOZE_NEXT_WEEK,
    "custom": SNOOZE_CUSTOM,
}

_TIME_WORD_RE = re.compile(
    r"\b(\d{1,2}:\d{2}\s*(?:am|pm)?|\d{1,2}\s*(?:am|pm)|noon|midnight|"
    r"morning|afternoon|evening|night)\b",
    re.IGNORECASE,
)
_IN_AMOUNT_RE = re.compile(
    r"^in\s+(\d+)\s+(minutes?|hours?|days?|weeks?)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TaskReminderSnoozeResult:
    """Outcome of a reminder snooze request."""

    success: bool
    message: str
    until: datetime | None = None
    option: str = ""


@handle_errors("normalizing task reminder snooze option", default_return=None)
def normalize_snooze_option(text: str | None) -> str | None:
    """Map user text to a snooze option key, or None if it is a custom when-phrase."""
    if not text or not str(text).strip():
        return None
    return _SNOOZE_OPTION_ALIASES.get(str(text).strip().lower())


@handle_errors("reading task reminder snooze timestamp", default_return=None)
def parse_task_snooze_until(task: dict[str, Any] | None) -> datetime | None:
    """Parse ``reminder_snooze_until`` from a runtime or v2 task dict."""
    if not isinstance(task, dict):
        return None
    raw = task.get("reminder_snooze_until")
    if not raw:
        return None
    return parse_timestamp_full(str(raw))


@handle_errors("checking whether a task reminder is snoozed", default_return=False)
def task_reminder_is_snoozed(
    task: dict[str, Any] | None,
    now_dt: datetime | None = None,
) -> bool:
    """True when a stored snooze timestamp is still in the future."""
    until = parse_task_snooze_until(task)
    if until is None:
        return False
    now_dt = now_dt or now_datetime_full()
    return now_dt < until


@handle_errors("checking evening or night for reminder snooze", default_return=False)
def is_evening_or_night(
    now_dt: datetime,
    defaults: NaturalLanguageDefaults,
) -> bool:
    """True when now is at or after the user's evening or night start."""
    tod = defaults.time_of_day_defaults
    evening = str(tod.get("evening") or "18:00")
    night = str(tod.get("night") or "21:00")
    return is_past_time_of_day(now_dt, evening, fallback_hour=18) or is_past_time_of_day(
        now_dt, night, fallback_hour=21
    )


@handle_errors("labeling tonight snooze button", default_return="Tonight")
def tonight_snooze_label(
    user_id: str | None,
    now_dt: datetime | None = None,
    *,
    nl_defaults: NaturalLanguageDefaults | None = None,
) -> str:
    """Return Tonight, or Tomorrow morning when it is already evening/night."""
    now_dt = now_dt or now_datetime_full()
    defaults = nl_defaults or get_natural_language_defaults(user_id)
    if is_evening_or_night(now_dt, defaults):
        return "Tomorrow morning"
    return "Tonight"


@handle_errors("combining a calendar day with HH:MM", default_return=None)
def _at_clock_time(day: datetime, hhmm: str) -> datetime | None:
    """Return *day* with hour and minute from an HH:MM string."""
    parsed = parse_time_string(hhmm) or hhmm
    parts = parsed.split(":")
    if len(parts) < 2:
        return None
    return day.replace(
        hour=int(parts[0]),
        minute=int(parts[1]),
        second=0,
        microsecond=0,
    )


@handle_errors("resolving morning clock time", default_return="09:00")
def _morning_clock(defaults: NaturalLanguageDefaults) -> str:
    """Return the user's morning default as HH:MM."""
    return parse_time_string(str(defaults.time_of_day_defaults.get("morning") or "9:00")) or "09:00"


@handle_errors("resolving tomorrow-morning snooze time", default_return=None)
def _tomorrow_morning(now_dt: datetime, defaults: NaturalLanguageDefaults) -> datetime | None:
    """Return tomorrow at the user's morning default."""
    return _at_clock_time(now_dt + timedelta(days=1), _morning_clock(defaults))


@handle_errors("resolving 1-hour reminder snooze", default_return=None)
def _resolve_one_hour(now_dt: datetime) -> datetime:
    """Return one hour from *now_dt*."""
    return now_dt + timedelta(hours=1)


@handle_errors("resolving tonight-or-morning reminder snooze", default_return=None)
def _resolve_tonight_or_morning(
    now_dt: datetime, defaults: NaturalLanguageDefaults
) -> datetime | None:
    """Snooze until tonight, or tomorrow morning when evening/night has started."""
    if is_evening_or_night(now_dt, defaults):
        return _tomorrow_morning(now_dt, defaults)
    tonight = parse_time_string(defaults.tonight_start_time) or "18:00"
    candidate = _at_clock_time(now_dt, tonight)
    if candidate is None or candidate <= now_dt:
        return _tomorrow_morning(now_dt, defaults)
    return candidate


@handle_errors("resolving next-week reminder snooze", default_return=None)
def _resolve_next_week(now_dt: datetime, defaults: NaturalLanguageDefaults) -> datetime | None:
    """Snooze until the same weekday next week at morning."""
    return _at_clock_time(now_dt + timedelta(days=7), _morning_clock(defaults))


@handle_errors("stripping clock words from a snooze phrase", default_return="")
def _strip_time_words(phrase: str) -> str:
    """Remove clock and time-of-day words so a date phrase remains."""
    cleaned = _TIME_WORD_RE.sub(" ", phrase)
    return re.sub(r"\s+", " ", cleaned).strip(" ,")


@handle_errors("resolving time-of-day word in a snooze phrase", default_return=None)
def _time_of_day_from_phrase(
    phrase: str, defaults: NaturalLanguageDefaults
) -> str | None:
    """Return HH:MM when the phrase names morning/afternoon/evening/night."""
    lowered = phrase.lower()
    for name in ("morning", "afternoon", "evening", "night"):
        if re.search(rf"\b{name}\b", lowered):
            raw = defaults.time_of_day_defaults.get(name)
            if raw:
                return parse_time_string(str(raw))
    return parse_time_string(phrase)


@handle_errors("parsing an in-N-units snooze phrase", default_return=None)
def _resolve_in_amount(phrase: str, now_dt: datetime) -> datetime | None:
    """Parse phrases like 'in 20 minutes' or 'in 2 hours'."""
    match = _IN_AMOUNT_RE.match(phrase.strip())
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2).lower()
    if unit.startswith("minute"):
        return now_dt + timedelta(minutes=amount)
    if unit.startswith("hour"):
        return now_dt + timedelta(hours=amount)
    if unit.startswith("day"):
        return now_dt + timedelta(days=amount)
    return now_dt + timedelta(weeks=amount)


@handle_errors("parsing a custom reminder snooze time", default_return=None)
def parse_custom_snooze_when(
    phrase: str,
    *,
    user_id: str | None = None,
    now_dt: datetime | None = None,
    nl_defaults: NaturalLanguageDefaults | None = None,
) -> datetime | None:
    """Parse a free-form when-phrase into a future local datetime."""
    from tasks.task_service import parse_relative_date

    text = (phrase or "").strip()
    if not text:
        return None
    now_dt = now_dt or now_datetime_full()
    defaults = nl_defaults or get_natural_language_defaults(user_id)
    relative = _resolve_in_amount(text, now_dt)
    if relative is not None:
        return relative

    clock = _time_of_day_from_phrase(text, defaults)
    date_phrase = _strip_time_words(text)
    date_str = ""
    if date_phrase:
        date_str = parse_relative_date(
            date_phrase, now_dt, user_id=user_id, nl_defaults=defaults
        )
    day = parse_date_only(date_str) if date_str else None
    if day is None and clock:
        candidate = _at_clock_time(now_dt, clock)
        if candidate is None:
            return None
        if candidate <= now_dt:
            candidate = candidate + timedelta(days=1)
        return candidate
    if day is None:
        return None
    combined = _at_clock_time(day, clock or _morning_clock(defaults))
    if combined is None:
        return None
    if combined <= now_dt:
        combined = combined + timedelta(days=1)
    return combined


@handle_errors("resolving task reminder snooze datetime", default_return=None)
def resolve_snooze_until(
    option: str | None,
    *,
    user_id: str | None = None,
    custom_when: str | None = None,
    now_dt: datetime | None = None,
    nl_defaults: NaturalLanguageDefaults | None = None,
) -> datetime | None:
    """Return the datetime a snoozed reminder should fire."""
    now_dt = now_dt or now_datetime_full()
    defaults = nl_defaults or get_natural_language_defaults(user_id)
    normalized = normalize_snooze_option(option) or option
    if normalized == SNOOZE_1_HOUR:
        return _resolve_one_hour(now_dt)
    if normalized == SNOOZE_TONIGHT:
        return _resolve_tonight_or_morning(now_dt, defaults)
    if normalized == SNOOZE_NEXT_WEEK:
        return _resolve_next_week(now_dt, defaults)
    if normalized == SNOOZE_CUSTOM or (custom_when and not normalized):
        return parse_custom_snooze_when(
            custom_when or "",
            user_id=user_id,
            now_dt=now_dt,
            nl_defaults=defaults,
        )
    if option and normalize_snooze_option(option) is None:
        return parse_custom_snooze_when(
            option,
            user_id=user_id,
            now_dt=now_dt,
            nl_defaults=defaults,
        )
    return None


@handle_errors("scheduling a snoozed task reminder", default_return=False)
def _schedule_snooze_fire(
    user_id: str, task_id: str, until: datetime
) -> bool:
    """Schedule a one-time reminder job at *until*."""
    from scheduler.runtime_access import get_scheduler_manager

    scheduler_manager = get_scheduler_manager()
    if not scheduler_manager:
        logger.warning(
            f"Scheduler unavailable while snoozing task {task_id} for user {user_id}"
        )
        return False
    date_str = format_timestamp(until, DATE_ONLY)
    time_str = format_timestamp(until, TIME_ONLY_MINUTE)
    return bool(
        scheduler_manager.schedule_task_reminder_at_datetime(
            user_id, task_id, date_str, time_str
        )
    )


@handle_errors("snoozing a task reminder", default_return=None)
def snooze_task_reminder(
    user_id: str,
    task_id: str,
    option: str | None = None,
    *,
    custom_when: str | None = None,
    now_dt: datetime | None = None,
) -> TaskReminderSnoozeResult:
    """Snooze one task's reminder. Does not change the task due date."""
    if not user_id or not task_id:
        return TaskReminderSnoozeResult(
            False, "I need a task to snooze that reminder for."
        )
    from tasks.task_data_manager import get_task_by_id, update_task

    task = get_task_by_id(user_id, task_id)
    if not task:
        return TaskReminderSnoozeResult(
            False, "I could not find that task, so I did not change the reminder."
        )
    if runtime_task_is_completed(task):
        return TaskReminderSnoozeResult(
            False, "That task is already completed, so there is nothing to remind you about."
        )

    now_dt = now_dt or now_datetime_full()
    until = resolve_snooze_until(
        option,
        user_id=user_id,
        custom_when=custom_when,
        now_dt=now_dt,
    )
    if until is None:
        return TaskReminderSnoozeResult(
            False,
            "I could not tell when to remind you. Try 1 hour, tonight, next week, "
            "or a time like Friday 3pm.",
        )
    if until <= now_dt:
        until = now_dt + timedelta(minutes=1)

    due_before = runtime_task_due_date(task)
    until_stamp = format_timestamp(until, TIMESTAMP_FULL)
    saved = update_task(
        user_id,
        task_id,
        {
            "reminder_sent": True,
            "reminder_snooze_until": until_stamp,
        },
    )
    if not saved:
        return TaskReminderSnoozeResult(
            False, "I could not save that snooze. Please try again."
        )

    refreshed = get_task_by_id(user_id, task_id) or task
    due_after = runtime_task_due_date(refreshed)
    if due_before != due_after:
        logger.error(
            f"Snooze unexpectedly changed due date for task {task_id}: {due_before} -> {due_after}"
        )
        return TaskReminderSnoozeResult(
            False, "Something went wrong saving the snooze. The due date may need a check."
        )

    _schedule_snooze_fire(user_id, str(refreshed.get("id") or task_id), until)
    title = str(refreshed.get("title") or "that task")
    when_text = format_timestamp(until, TIMESTAMP_FULL)
    logger.info(
        f"Snoozed reminder for task {task_id} user {user_id} until {when_text} "
        f"(due date unchanged: {due_after})"
    )
    return TaskReminderSnoozeResult(
        True,
        f"I'll remind you about **{title}** at {when_text}. The due date stays the same.",
        until=until,
        option=normalize_snooze_option(option) or SNOOZE_CUSTOM,
    )
