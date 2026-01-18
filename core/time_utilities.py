# core/time_utilities.py
"""
Canonical time and date utilities for MHM.

This module is the single source of truth for:
- Timestamp/date/time format strings
- Timestamp/date/time formatting helpers
- Timestamp/date/time parsing helpers (return None on invalid input)

Design goals:
- Dependency-light (avoid logger/config to prevent circular imports)
- Descriptive, intuitive names
- Strict parse helpers for critical state
- Optional flexible parse for "messy" inputs from outside the app
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Literal

# ---------------------------------------------------------------------------
# Canonical formats (project-wide)
# ---------------------------------------------------------------------------

# Primary internal timestamp (full precision to seconds)
TIMESTAMP_FULL = "%Y-%m-%d %H:%M:%S"

# Timestamp rounded to minutes (scheduler, UI state)
TIMESTAMP_MINUTE = "%Y-%m-%d %H:%M"

# Date only (no time)
DATE_ONLY = "%Y-%m-%d"

# Time only (hour + minute)
TIME_ONLY_MINUTE = "%H:%M"

# Filename-safe timestamp (no spaces or colons)
TIMESTAMP_FILENAME = "%Y-%m-%d_%H-%M-%S"

# Display-only formats (never for parsing critical state)
DATE_DISPLAY_MONTH_DAY = "%b %d"
DATE_DISPLAY_WEEKDAY = "%A"

# Full timestamp with sub-second precision (debug only)
TIMESTAMP_WITH_MICROSECONDS = "%Y-%m-%d %H:%M:%S.%f"

# External timestamp inputs we may encounter (parse-only; never emit)
# (These are common machine timestamp shapes you might receive from other tools/services.)
EXTERNAL_TIMESTAMP_VARIANTS: list[str] = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S.%fZ",
]

# ---------------------------------------------------------------------------
# "Now" helpers
# ---------------------------------------------------------------------------


def now_timestamp_full() -> str:
    """Current local timestamp formatted with TIMESTAMP_FULL."""
    return datetime.now().strftime(TIMESTAMP_FULL)


def now_timestamp_minute() -> str:
    """Current local timestamp formatted with TIMESTAMP_MINUTE."""
    return datetime.now().strftime(TIMESTAMP_MINUTE)


def now_timestamp_filename() -> str:
    """Current local timestamp formatted with TIMESTAMP_FILENAME."""
    return datetime.now().strftime(TIMESTAMP_FILENAME)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def format_timestamp(dt: datetime | None, fmt: str) -> str:
    """Format a datetime using a provided format string. Returns "" for None."""
    if dt is None:
        return ""
    return dt.strftime(fmt)


def format_timestamp_milliseconds(dt: datetime | None) -> str:
    """
    Debug-only: format to milliseconds (3 decimals).
    Example output: "2026-01-18 12:34:56.789"
    """
    if dt is None:
        return ""
    # %f is microseconds; trim to milliseconds
    return dt.strftime(TIMESTAMP_WITH_MICROSECONDS)[:-3]


# ---------------------------------------------------------------------------
# Strict parsing helpers (preferred for critical state)
# ---------------------------------------------------------------------------


def parse_timestamp_full(value: str) -> datetime | None:
    """Parse TIMESTAMP_FULL. Returns None on invalid input."""
    if not value:
        return None
    try:
        return datetime.strptime(value, TIMESTAMP_FULL)
    except (ValueError, TypeError):
        return None


def parse_timestamp_minute(value: str) -> datetime | None:
    """Parse TIMESTAMP_MINUTE. Returns None on invalid input."""
    if not value:
        return None
    try:
        return datetime.strptime(value, TIMESTAMP_MINUTE)
    except (ValueError, TypeError):
        return None


def parse_date_only(value: str) -> datetime | None:
    """Parse DATE_ONLY (date at 00:00). Returns None on invalid input."""
    if not value:
        return None
    try:
        return datetime.strptime(value, DATE_ONLY)
    except (ValueError, TypeError):
        return None


def parse_time_only_minute(value: str) -> datetime | None:
    """
    Parse TIME_ONLY_MINUTE.
    Note: datetime.strptime() will produce a datetime with a default date (1900-01-01).
    Returns None on invalid input.
    """
    if not value:
        return None
    try:
        return datetime.strptime(value, TIME_ONLY_MINUTE)
    except (ValueError, TypeError):
        return None


def parse_date_and_time_minute(date_str: str, time_str: str) -> datetime | None:
    """
    Parse a DATE_ONLY + TIME_ONLY_MINUTE combination into a datetime.
    Returns None on invalid input.
    """
    if not date_str or not time_str:
        return None
    try:
        return datetime.strptime(
            f"{date_str} {time_str}", f"{DATE_ONLY} {TIME_ONLY_MINUTE}"
        )
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Flexible parsing (use only when multiple inputs are legitimately expected)
# ---------------------------------------------------------------------------

TimestampKind = Literal["full", "minute", "microseconds", "external"]


def parse_timestamp(
    value: str,
    *,
    allowed: Iterable[TimestampKind] = ("full", "minute"),
) -> datetime | None:
    """
    Parse a timestamp string using an allowed set of formats.
    Returns None if no allowed format matches.

    Use this only when multiple inputs are expected.
    Prefer parse_timestamp_full / parse_timestamp_minute for critical state.
    """
    if not value:
        return None

    formats: list[str] = []
    for kind in allowed:
        if kind == "full":
            formats.append(TIMESTAMP_FULL)
        elif kind == "minute":
            formats.append(TIMESTAMP_MINUTE)
        elif kind == "microseconds":
            formats.append(TIMESTAMP_WITH_MICROSECONDS)
        elif kind == "external":
            formats.extend(EXTERNAL_TIMESTAMP_VARIANTS)

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except (ValueError, TypeError):
            continue

    return None
