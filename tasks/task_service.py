# Use-case facade for task commands; delegates to the tasks package public API.

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from core.error_handling import handle_errors
from core import get_user_data
from core.time_utilities import DATE_ONLY, format_timestamp, now_datetime_full, parse_date_only
from tasks.task_data_handlers import runtime_task_due_date
from tasks.task_schemas import VALID_PRIORITIES


@dataclass(frozen=True)
class PreparedTaskCreateData:
    """Normalized task fields for command-driven task creation."""

    task_data: dict[str, Any]
    priority_was_provided: bool
    valid_due_date: str | None
    valid_due_time: str | None
    recurrence_pattern: str | None
    recurrence_interval: int
    priority: str
    tags: list[str]


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


# duplicate_functions_intentional: task_stats_facade
@handle_errors("task service: get_user_task_stats", user_friendly=False, re_raise=True)
def get_user_task_stats(user_id: str):
    return _tasks().get_user_task_stats(user_id)


@handle_errors("task service: load recurring defaults", default_return={})
def get_recurring_task_defaults(user_id: str) -> dict[str, Any]:
    """Return recurring-task preference defaults for command task creation."""
    user_data = get_user_data(user_id, "preferences")
    preferences = user_data.get("preferences", {}) if user_data else {}
    task_settings = preferences.get("task_settings", {})
    return task_settings.get("recurring_settings", {})


# not_duplicate: task_identifier_service_facade
@handle_errors("task service: task identifier", default_return="")
def task_identifier(task: dict[str, Any]) -> str:
    """Return canonical task id for matching and mutations."""
    return str(task.get("id") or "")


# not_duplicate: task_identifier_service_facade
@handle_errors("task service: task short identifier", default_return="")
def task_short_identifier(task: dict[str, Any]) -> str:
    """Return canonical task short_id for matching and display."""
    return str(task.get("short_id") or "")


@handle_errors("task service: advancing one calendar month", re_raise=True)
def add_one_calendar_month(dt: datetime) -> datetime:
    """Advance *dt* by one calendar month, clamping the day if necessary."""
    if dt.month == 12:
        year, month = dt.year + 1, 1
    else:
        year, month = dt.year, dt.month + 1
    last_day = calendar.monthrange(year, month)[1]
    return dt.replace(year=year, month=month, day=min(dt.day, last_day))


@handle_errors("task service: parsing time string", default_return=None)
def parse_time_string(time_str: str) -> str | None:
    """Parse user-facing time text into HH:MM format."""
    time_str_lower = time_str.lower().strip()

    if time_str_lower == "noon":
        return "12:00"
    if time_str_lower == "midnight":
        return "00:00"

    time_patterns = [
        r"(\d{1,2}):(\d{2})\s*(am|pm)?",
        r"(\d{1,2})\s*(am|pm)",
    ]

    for pattern in time_patterns:
        match = re.search(pattern, time_str_lower)
        if not match:
            continue

        groups = match.groups()
        hour = int(groups[0])
        minute = (
            int(groups[1])
            if len(groups) > 1 and groups[1] and groups[1].isdigit()
            else 0
        )

        if len(groups) > 2 and groups[-1]:
            am_pm = groups[-1].lower()
            if am_pm == "pm" and hour != 12:
                hour += 12
            elif am_pm == "am" and hour == 12:
                hour = 0
        elif hour < 12 and "pm" in time_str_lower:
            hour += 12
        elif hour == 12 and "am" in time_str_lower:
            hour = 0

        return f"{hour:02d}:{minute:02d}"

    return None


@handle_errors("task service: defaulting recurring due date", default_return=None)
def default_due_date_for_recurring_time(
    due_time: str, now_dt: datetime | None = None
) -> str | None:
    """Return today for future recurring times, otherwise tomorrow."""
    now_dt = now_dt or now_datetime_full()
    try:
        hour_text, minute_text = due_time.split(":", 1)
        due_hour = int(hour_text)
        due_minute = int(minute_text)
    except (TypeError, ValueError):
        return format_timestamp(now_dt, DATE_ONLY)

    due_today = now_dt.replace(
        hour=due_hour,
        minute=due_minute,
        second=0,
        microsecond=0,
    )
    if due_today <= now_dt:
        due_today += timedelta(days=1)
    return format_timestamp(due_today, DATE_ONLY)


@handle_errors("task service: parsing relative date")
def parse_relative_date(date_str: str, now_dt: datetime | None = None) -> str:
    """Convert relative task due-date strings to YYYY-MM-DD where possible."""
    date_str_lower = date_str.lower().strip()
    now_dt = now_dt or now_datetime_full()

    if date_str_lower == "today":
        return format_timestamp(now_dt, DATE_ONLY)
    if date_str_lower == "tomorrow":
        return format_timestamp(now_dt + timedelta(days=1), DATE_ONLY)
    if date_str_lower == "next week":
        return format_timestamp(now_dt + timedelta(days=7), DATE_ONLY)
    if date_str_lower == "next month":
        return format_timestamp(add_one_calendar_month(now_dt), DATE_ONLY)
    if date_str_lower.startswith("in "):
        hours_match = re.search(r"in\s+(\d+)\s+hours?", date_str_lower)
        if hours_match:
            hours = int(hours_match.group(1))
            return format_timestamp(now_dt + timedelta(hours=hours), DATE_ONLY)
        days_match = re.search(r"in\s+(\d+)\s+days?", date_str_lower)
        if days_match:
            days = int(days_match.group(1))
            return format_timestamp(now_dt + timedelta(days=days), DATE_ONLY)
        weeks_match = re.search(r"in\s+(\d+)\s+weeks?", date_str_lower)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            return format_timestamp(now_dt + timedelta(weeks=weeks), DATE_ONLY)
    elif date_str_lower.startswith("next "):
        days_of_week = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        day_match = re.search(
            r"next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            date_str_lower,
        )
        if day_match:
            day_name = day_match.group(1).lower()
            day_index = days_of_week.index(day_name)
            days_ahead = (day_index - now_dt.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            else:
                days_ahead += 7
            return format_timestamp(now_dt + timedelta(days=days_ahead), DATE_ONLY)
        if "next week" in date_str_lower:
            return format_timestamp(now_dt + timedelta(days=7), DATE_ONLY)
        if "next month" in date_str_lower:
            return format_timestamp(add_one_calendar_month(now_dt), DATE_ONLY)
    elif re.match(
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
        date_str_lower,
    ):
        days_of_week = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        day_match = re.search(
            r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            date_str_lower,
        )
        if day_match:
            day_name = day_match.group(1).lower()
            day_index = days_of_week.index(day_name)
            days_ahead = (day_index - now_dt.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return (now_dt + timedelta(days=days_ahead)).date().isoformat()

    return date_str


@handle_errors("task service: preparing create task data", re_raise=True)
def prepare_create_task_data(
    user_id: str, entities: dict[str, Any], now_dt: datetime | None = None
) -> PreparedTaskCreateData:
    """Normalize ParsedCommand entities into task creation fields."""
    now_dt = now_dt or now_datetime_full()
    title = entities.get("title")
    description = entities.get("description", "")
    due_date = entities.get("due_date")
    due_time = entities.get("due_time")
    raw_priority = entities.get("priority")
    priority_was_provided = raw_priority in VALID_PRIORITIES
    priority = raw_priority or "medium"
    tags = entities.get("tags", [])
    recurrence_pattern = entities.get("recurrence_pattern")
    recurrence_interval = entities.get("recurrence_interval", 1)

    recurring_settings: dict[str, Any] = {}
    if not recurrence_pattern:
        recurring_settings = get_recurring_task_defaults(user_id)
        default_pattern = recurring_settings.get("default_recurrence_pattern")
        if default_pattern:
            recurrence_pattern = default_pattern
            recurrence_interval = recurring_settings.get(
                "default_recurrence_interval", 1
            )

    valid_due_time = None
    if due_date:
        time_match = re.search(
            r"(?:next\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|noon|midnight)",
            due_date.lower(),
        )
        if not time_match:
            time_match = re.search(
                r"at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|noon|midnight)",
                due_date.lower(),
            )
        if time_match:
            parsed_time = parse_time_string(time_match.group(1))
            if parsed_time:
                valid_due_time = parsed_time
            due_date = re.sub(r"\s+at\s+.*", "", due_date, flags=re.IGNORECASE)
        due_date = parse_relative_date(due_date, now_dt=now_dt)

    if due_time and not valid_due_time:
        parsed_time = parse_time_string(due_time)
        if parsed_time:
            valid_due_time = parsed_time

    if recurrence_pattern and valid_due_time and not due_date:
        due_date = default_due_date_for_recurring_time(valid_due_time, now_dt=now_dt)

    if priority not in VALID_PRIORITIES:
        priority = "medium"

    valid_patterns = ["daily", "weekly", "monthly", "yearly"]
    if recurrence_pattern and recurrence_pattern not in valid_patterns:
        recurrence_pattern = None

    valid_due_date = None
    if due_date and due_date.strip():
        valid_due_date = due_date if parse_date_only(due_date) is not None else None

    task_data = {
        "title": title,
        "description": description,
        "due_date": valid_due_date,
        "due_time": valid_due_time if valid_due_date else None,
        "priority": priority,
        "tags": tags,
    }

    if recurrence_pattern:
        if not recurring_settings:
            recurring_settings = get_recurring_task_defaults(user_id)
        task_data["recurrence_pattern"] = recurrence_pattern
        task_data["recurrence_interval"] = recurrence_interval
        task_data["repeat_after_completion"] = recurring_settings.get(
            "default_repeat_after_completion", True
        )

    return PreparedTaskCreateData(
        task_data=task_data,
        priority_was_provided=priority_was_provided,
        valid_due_date=valid_due_date,
        valid_due_time=valid_due_time,
        recurrence_pattern=recurrence_pattern,
        recurrence_interval=recurrence_interval,
        priority=priority,
        tags=tags,
    )


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


@handle_errors("task service: get completed task candidates", default_return=[])
def get_completed_task_candidates(
    tasks: list[dict[str, Any]], identifier: str
) -> list[dict[str, Any]]:
    """Return completed-task candidates matching id, short_id, number, or title."""
    identifier_text = str(identifier).strip()
    identifier_lower = identifier_text.lower()
    candidates = [
        task
        for task in tasks
        if identifier_lower
        in (
            task_identifier(task).lower(),
            task_short_identifier(task).lower(),
            (task.get("title") or "").lower(),
        )
        or (identifier_text.isdigit() and task_identifier(task) == identifier_text)
    ]
    if candidates:
        return candidates
    return [
        task
        for task in tasks
        if identifier_lower in (task.get("title") or "").lower()
    ]


@handle_errors("task service: filtering tasks", default_return=[])
def filter_tasks(
    user_id: str,
    tasks: list[dict[str, Any]],
    filter_type: str | None,
    priority_filter: str | None,
    tag_filter: str | None,
    now_dt: datetime | None = None,
) -> list[dict[str, Any]]:
    """Apply command task-list filters."""
    filtered_tasks = tasks.copy()

    if filter_type == "due_soon":
        filtered_tasks = get_tasks_due_soon(user_id, days_ahead=7)
    elif filter_type == "overdue":
        today = format_timestamp(now_dt or now_datetime_full(), DATE_ONLY)
        filtered_tasks = [
            task for task in filtered_tasks if (d := runtime_task_due_date(task)) and d < today
        ]
    elif filter_type == "high_priority":
        filtered_tasks = [
            task for task in filtered_tasks if task.get("priority") == "high"
        ]

    if priority_filter and priority_filter in VALID_PRIORITIES:
        filtered_tasks = [
            task for task in filtered_tasks if task.get("priority") == priority_filter
        ]

    if tag_filter:
        filtered_tasks = [
            task for task in filtered_tasks if tag_filter in task.get("tags", [])
        ]

    return filtered_tasks


@handle_errors("task service: sorting tasks", default_return=[])
def sort_tasks_by_priority_and_due_date(
    tasks: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Sort active tasks by priority, then due date."""
    priority_order = {"high": 0, "medium": 1, "low": 2}
    return sorted(
        tasks,
        key=lambda task: (
            priority_order.get(task.get("priority", "medium"), 1),
            runtime_task_due_date(task) or "9999-12-31",
        ),
    )


@handle_errors("task service: formatting due date", default_return="")
def format_due_date_status(
    due_date: str | None, now_dt: datetime | None = None
) -> str:
    """Format due-date status for command display."""
    if not due_date:
        return ""

    today = format_timestamp(now_dt or now_datetime_full(), DATE_ONLY)
    if due_date < today:
        return f" (OVERDUE: {due_date})"
    if due_date == today:
        return f" (due TODAY: {due_date})"
    return f" (due: {due_date})"


@handle_errors("task service: contextual task suggestion", default_return=None)
def get_contextual_task_suggestion(
    tasks: list[dict[str, Any]], now_dt: datetime | None = None
) -> str | None:
    """Return a state-based suggestion for a task list."""
    now_dt = now_dt or now_datetime_full()
    today = format_timestamp(now_dt, DATE_ONLY)

    overdue_count = sum(
        1 for task in tasks if (d := runtime_task_due_date(task)) and d < today
    )
    if overdue_count > 0:
        return f"Show {overdue_count} overdue tasks"

    high_priority_count = sum(1 for task in tasks if task.get("priority") == "high")
    if high_priority_count > 0:
        return f"Show {high_priority_count} high priority tasks"

    soon_cutoff = format_timestamp(now_dt + timedelta(days=3), DATE_ONLY)
    due_soon_count = sum(
        1 for task in tasks if (d := runtime_task_due_date(task)) and d <= soon_cutoff
    )
    if due_soon_count > 0:
        return f"Show {due_soon_count} tasks due soon"

    return None


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
