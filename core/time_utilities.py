# core/time_utilities.py
"""
Canonical time and date utilities for MHM.

This module is the single source of truth for:
- Timestamp/date/time format strings
- Timestamp/date/time formatting helpers
- Timestamp/date/time parsing helpers (return None on invalid input)

Design goals:
- Dependency-light (avoid logger/config/error_handling to prevent circular imports)
- Descriptive, intuitive names
- Strict parse helpers for critical state
- Optional flexible parse for "messy" inputs from outside the app
"""

from __future__ import annotations

import functools
import logging
from datetime import datetime
from typing import Literal, TypeVar, cast
from collections.abc import Callable, Iterable

from core.time_format_constants import (
    DATE_ONLY,
    EXTERNAL_TIMESTAMP_VARIANTS,
    TIME_ONLY_MINUTE,
    TIMESTAMP_FILENAME,
    TIMESTAMP_FULL,
    TIMESTAMP_MINUTE,
    TIMESTAMP_WITH_MICROSECONDS,
)

_time_logger = logging.getLogger("mhm.time_utilities")

F = TypeVar("F", bound=Callable[..., object])


def _guard(operation: str, default_return: object) -> Callable[[F], F]:
    """Log failures and return default_return (mirrors handle_errors defaults for time ops)."""

    def decorator(func: F) -> F:
        """Wrap ``func`` so failures are logged and ``default_return`` is used."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
            """Run the wrapped time helper; log and return the guard default on failure."""
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _time_logger.error(
                    f"{operation} failed: {e}", exc_info=True
                )
                return default_return

        return cast(F, wrapper)

    return decorator


@_guard("getting canonical timestamp", "")
def now_timestamp_full() -> str:
    """Current local timestamp formatted with TIMESTAMP_FULL."""
    return datetime.now().strftime(TIMESTAMP_FULL)


@_guard("getting canonical minute timestamp", "")
def now_timestamp_minute() -> str:
    """Current local timestamp formatted with TIMESTAMP_MINUTE."""
    return datetime.now().strftime(TIMESTAMP_MINUTE)


@_guard("getting filename-safe timestamp", "")
def now_timestamp_filename() -> str:
    """Current local timestamp formatted with TIMESTAMP_FILENAME."""
    return datetime.now().strftime(TIMESTAMP_FILENAME)


# ---------------------------------------------------------------------------
# "Now" helpers (datetime objects)
# ---------------------------------------------------------------------------


@_guard("building canonical datetime", datetime.min)
def now_datetime_full() -> datetime:
    """
    Current local-naive datetime with second precision matching TIMESTAMP_FULL.

    This is the canonical replacement for datetime.now() in places that need a
    datetime object (arithmetic/comparisons) rather than a formatted string.
    """
    value = now_timestamp_full()
    dt = parse_timestamp_full(value)
    if dt is None:
        return datetime.min
    return dt


@_guard("building canonical minute datetime", datetime.min)
def now_datetime_minute() -> datetime:
    """
    Current local-naive datetime rounded to minute precision matching TIMESTAMP_MINUTE.

    Use for scheduler/UI state where minute precision is the canonical persisted shape.
    """
    value = now_timestamp_minute()
    dt = parse_timestamp_minute(value)
    if dt is None:
        return datetime.min
    return dt


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


@_guard("formatting timestamp", "")
def format_timestamp(dt: datetime | None, fmt: str) -> str:
    """Format a datetime using a provided format string. Returns "" for None."""
    if dt is None:
        return ""
    return dt.strftime(fmt)


@_guard("formatting timestamp with milliseconds", "")
def format_timestamp_milliseconds(dt: datetime | None) -> str:
    """
    Debug-only: format to milliseconds (3 decimals).
    Example output: "2026-01-18 12:34:56.789"
    """
    if dt is None:
        return ""
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
