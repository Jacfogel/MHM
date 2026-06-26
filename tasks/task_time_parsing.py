"""Shared task time-string parsing (no task_service imports)."""

from __future__ import annotations

import re

from core.error_handling import handle_errors


@handle_errors("parsing task time string", default_return=None)
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
