"""Shared task-focus policy for reminders and conversational suggestions."""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.error_handling import handle_errors
from core.time_utilities import now_datetime_full, parse_date_only
from tasks.task_data_handlers import (
    runtime_task_due_date,
    runtime_task_due_time,
    runtime_task_is_completed,
    runtime_task_recurrence_pattern,
)
from tasks.task_effort import local_task_minutes
from tasks.task_reminder_snooze import parse_task_snooze_until, task_reminder_is_snoozed

_PRIORITY_SCORE = {
    "critical": 50,
    "urgent": 45,
    "high": 34,
    "medium": 20,
    "low": 10,
    "none": 5,
}
@dataclass(frozen=True)
class TaskFocusDecision:
    """A selected task plus the user-facing reason for selecting it."""

    task: dict[str, Any]
    reason: str
    effort_minutes: int
    energy: int | None
    gentle: bool


@dataclass(frozen=True)
class _RankedTask:
    task: dict[str, Any]
    score: float
    urgency: int
    days_until_due: int | None
    effort_minutes: int
    reasons: frozenset[str]


@handle_errors("labeling task focus time band", default_return="")
def _time_band(hour: int) -> str:
    """Return the broad day period used by task time-of-day tags."""
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    if hour < 21:
        return "evening"
    return "night"


@handle_errors("calculating task focus due distance", default_return=None)
def _days_until_due(task: dict[str, Any], now_dt: datetime) -> int | None:
    """Return calendar days until the task due date, or None without one."""
    due = runtime_task_due_date(task)
    parsed = parse_date_only(due) if due else None
    if parsed is None:
        return None
    return (parsed.date() - now_dt.date()).days


@handle_errors("classifying task focus urgency", default_return=0)
def _urgency(priority: str, days_until_due: int | None) -> int:
    """Put tasks in broad bands so energy never hides genuinely urgent work."""
    if priority in {"critical", "urgent"} or (
        days_until_due is not None and days_until_due < 0
    ):
        return 4
    if priority == "high" or days_until_due == 0:
        return 3
    if days_until_due is not None and days_until_due <= 2:
        return 2
    if days_until_due is not None and days_until_due <= 7:
        return 1
    return 0


def _rank_task(
    task: dict[str, Any], now_dt: datetime, energy: int | None
) -> _RankedTask:
    priority = str(task.get("priority") or "medium").strip().lower()
    days = _days_until_due(task, now_dt)
    effort = local_task_minutes(task)
    low_energy = energy in {1, 2}
    reasons: set[str] = set()
    score = float(_PRIORITY_SCORE.get(priority, 20))

    if days is None:
        score += 5
    elif days < 0:
        score += 80 + min(-days, 14) * 4
        reasons.add("overdue")
    elif days == 0:
        score += 60
        reasons.add("due-today")
    elif days <= 2:
        score += 40
        reasons.add("due-soon")
    elif days <= 7:
        score += 20
        reasons.add("due-week")

    if priority in {"critical", "urgent", "high"}:
        reasons.add("priority")
    tags = {
        str(tag).strip().lower()
        for tag in task.get("tags", [])
        if str(tag).strip()
    }
    if _time_band(now_dt.hour) in tags:
        score += 12
        reasons.add("time-of-day")

    due_time = runtime_task_due_time(task) or ""
    if days == 0 and len(due_time) == 5 and due_time[2] == ":":
        try:
            hour, minute = (int(part) for part in due_time.split(":"))
            delta = hour * 60 + minute - (now_dt.hour * 60 + now_dt.minute)
            if -180 <= delta <= 120:
                score += 15
                reasons.add("due-time")
        except ValueError:
            pass

    if parse_task_snooze_until(task) is not None:
        score += 18
        reasons.add("deferred")
    if runtime_task_recurrence_pattern(task):
        reasons.add("recurring")
    elif days is not None and days <= 0:
        score += 6

    reasons.add("effort")
    if low_energy:
        reasons.add("low-energy")
        score += 28 if effort <= 15 else -18
    elif effort <= 10:
        score += 22
    elif effort <= 30:
        score += 10
    else:
        score -= 8

    return _RankedTask(
        task=task,
        score=max(score, 1),
        urgency=_urgency(priority, days),
        days_until_due=days,
        effort_minutes=effort,
        reasons=frozenset(reasons),
    )


@handle_errors(
    "explaining task focus ranking",
    default_return="This is the next task selected by your current priorities.",
)
def _focus_reason(ranked: _RankedTask) -> str:
    """Turn ranking evidence into a short, nonjudgmental explanation."""
    reasons = ranked.reasons
    minutes = ranked.effort_minutes
    if "low-energy" in reasons and minutes <= 15:
        return "Your energy is low today, so this is a small step among the most urgent options."
    if "low-energy" in reasons and minutes > 15 and (
        "overdue" in reasons or "due-today" in reasons or "priority" in reasons
    ):
        return "This is still urgent today. Breaking it down may make the first step easier."
    if "overdue" in reasons:
        return "This is overdue, so it stays visible ahead of less urgent tasks."
    if "due-today" in reasons:
        return "This is due today."
    if "priority" in reasons:
        return "Its priority keeps it ahead of less urgent tasks."
    if "due-soon" in reasons or "due-week" in reasons:
        return "This is coming up soon, so a start now can keep it from becoming urgent."
    if "time-of-day" in reasons:
        return "This fits the current time of day."
    return "No deadline is pressing, so this is a manageable next task."


@handle_errors("filtering actionable task focus candidates", default_return=[])
def _leaf_candidates(tasks: list[dict[str, Any]], now_dt: datetime) -> list[dict[str, Any]]:
    """Return unsnoozed open leaf tasks, falling back to eligible parents."""
    eligible = [
        task
        for task in tasks
        if isinstance(task, dict)
        and not runtime_task_is_completed(task)
        and not task_reminder_is_snoozed(task, now_dt=now_dt)
    ]
    parents_with_steps = {
        str(task.get("parent_id") or "").strip()
        for task in eligible
        if str(task.get("parent_id") or "").strip()
    }
    leaf_tasks = [
        task
        for task in eligible
        if str(task.get("id") or "").strip() not in parents_with_steps
    ]
    return leaf_tasks or eligible


@handle_errors("choosing shared task focus", default_return=None)
def choose_task_focus(
    tasks: list[dict[str, Any]] | None,
    *,
    now_dt: datetime | None = None,
    energy: int | None = None,
    gentle: bool = False,
    random_value: Callable[[], float] | None = None,
) -> TaskFocusDecision | None:
    """Choose one actionable task while preserving urgency guardrails."""
    now_dt = now_dt or now_datetime_full()
    candidates = _leaf_candidates(tasks or [], now_dt)
    if not candidates:
        return None

    ranked = [_rank_task(task, now_dt, energy) for task in candidates]
    highest_urgency = max(item.urgency for item in ranked)
    comparable = [item for item in ranked if item.urgency == highest_urgency]
    comparable.sort(
        key=lambda item: (-item.score, str(item.task.get("title") or "").casefold())
    )
    total = sum(item.score for item in comparable)
    roll = (random_value or random.random)()
    cursor = min(max(float(roll), 0.0), 0.999999) * total
    selected = comparable[-1]
    for item in comparable:
        cursor -= item.score
        if cursor < 0:
            selected = item
            break
    return TaskFocusDecision(
        task=selected.task,
        reason=_focus_reason(selected),
        effort_minutes=selected.effort_minutes,
        energy=energy,
        gentle=gentle or energy in {1, 2},
    )


@handle_errors("reading task focus signals", default_return=(None, False))
def task_focus_signals(user_id: str) -> tuple[int | None, bool]:
    """Return today's energy and whether reminders should avoid pressure."""
    from core.message_pressure import resolve_message_pressure

    policy = resolve_message_pressure(user_id)
    return policy.energy, policy.gentle


@handle_errors("choosing task focus for user", default_return=None)
def choose_task_focus_for_user(
    user_id: str,
    tasks: list[dict[str, Any]] | None,
    *,
    now_dt: datetime | None = None,
    random_value: Callable[[], float] | None = None,
) -> TaskFocusDecision | None:
    """Choose a focus task with the user's reliable energy and health guidance."""
    energy, gentle = task_focus_signals(user_id)
    return choose_task_focus(
        tasks,
        now_dt=now_dt,
        energy=energy,
        gentle=gentle,
        random_value=random_value,
    )


@handle_errors("explaining focused task", default_return="")
def explain_task_focus(
    task: dict[str, Any], *, now_dt: datetime | None = None, energy: int | None = None
) -> str:
    """Explain a task's own urgency and effort without exposing health details."""
    return _focus_reason(_rank_task(task, now_dt or now_datetime_full(), energy))
