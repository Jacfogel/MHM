# Service-side resolution of predefined message preview text (v2-aware schedules).

from __future__ import annotations

import random
from typing import Any

from core.error_handling import handle_errors
from core.message_management import get_recent_messages, load_user_messages
from core.schedule_runtime import (
    get_current_day_names,
    get_current_time_periods_with_validation,
)


@handle_errors(
    "extracting schedule lists from message template for test preview",
    default_return=(["ALL"], ["ALL"]),
)
def message_template_schedule_lists(msg: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return day names and time periods from a v2 template ``schedule`` (or ALL defaults)."""
    raw_schedule = msg.get("schedule")
    sched: dict[str, Any] = raw_schedule if isinstance(raw_schedule, dict) else {}
    days = sched.get("days") or ["ALL"]
    periods = sched.get("periods") or ["ALL"]
    if not isinstance(days, list):
        days = ["ALL"]
    if not isinstance(periods, list):
        periods = ["ALL"]
    dlist = [d for d in days if isinstance(d, str)] or ["ALL"]
    plist = [p for p in periods if isinstance(p, str)] or ["ALL"]
    return dlist, plist


@handle_errors(
    "matching message template schedule to current window",
    default_return=False,
)
def message_schedule_matches_current_window(
    day_names: list[str],
    time_periods: list[str],
    current_days: list[str],
    matching_periods: list[str],
) -> bool:
    """True if template schedule overlaps current day/period (ALL matches any)."""
    day_ok = "ALL" in day_names or any(d in day_names for d in current_days)
    period_ok = "ALL" in time_periods or any(
        p in time_periods for p in matching_periods
    )
    return day_ok and period_ok


@handle_errors("resolving predefined message preview text", default_return=None)
def get_predefined_message_preview_text(user_id: str, category: str) -> str | None:
    """Return the text that would be chosen for a predefined-category send (mirrors orchestrator weighting)."""
    matching_periods, valid_periods = get_current_time_periods_with_validation(
        user_id, category
    )

    if "ALL" in matching_periods and len(matching_periods) > 1:
        matching_periods = [p for p in matching_periods if p != "ALL"]
    if not matching_periods and "ALL" in valid_periods:
        matching_periods = ["ALL"]

    messages = load_user_messages(user_id, category)

    if not messages:
        return None

    current_days = get_current_day_names()

    all_messages: list[dict[str, Any]] = []
    for msg in messages:
        day_names, time_periods = message_template_schedule_lists(msg)
        if message_schedule_matches_current_window(
            day_names,
            time_periods,
            current_days,
            matching_periods,
        ):
            all_messages.append(msg)

    if not all_messages:
        return None

    recent_messages = get_recent_messages(
        user_id, category=category, limit=50, days_back=60
    )
    recent_content = {
        msg.get("sent_text", "").strip().lower()
        for msg in recent_messages
        if msg.get("sent_text")
    }

    available_messages = []
    for msg in all_messages:
        message_content = msg.get("text", "").strip()
        if message_content and message_content.lower() not in recent_content:
            available_messages.append(msg)

    if not available_messages:
        available_messages = all_messages

    if not available_messages:
        return None

    specific_period_messages = []
    all_period_messages = []

    for msg in available_messages:
        _, plist = message_template_schedule_lists(msg)
        time_periods = plist
        has_specific_periods = any(period != "ALL" for period in time_periods)
        if has_specific_periods:
            specific_period_messages.append(msg)
        else:
            all_period_messages.append(msg)

    if specific_period_messages and random.random() < 0.7:
        selected_msg = random.choice(specific_period_messages)
    elif all_period_messages:
        selected_msg = random.choice(all_period_messages)
    else:
        selected_msg = random.choice(available_messages)

    return selected_msg.get("text", "")
