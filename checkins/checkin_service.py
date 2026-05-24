"""Check-in use-case helpers for command handlers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from core.error_handling import handle_errors
from checkins.checkin_data_manager import (
    checkin_runtime_timestamp,
    get_recent_checkins,
    is_user_checkins_enabled,
)
from core.time_utilities import parse_timestamp_full


@dataclass(frozen=True)
class CheckinStartStatus:
    """Preflight status for starting a check-in."""

    enabled: bool
    already_completed_today: bool
    last_checkin_timestamp: str | None = None


@dataclass(frozen=True)
class RecentCheckinSummary:
    """Recent check-in data normalized for command display."""

    entries: list[dict[str, Any]]
    enabled: bool


@handle_errors("checkin service: start preflight", default_return=CheckinStartStatus(False, False))
def get_checkin_start_status(
    user_id: str,
    *,
    is_enabled=None,
    load_recent=None,
    runtime_timestamp=None,
) -> CheckinStartStatus:
    """Return whether a user can start a new check-in right now."""
    is_enabled = is_enabled or is_user_checkins_enabled
    load_recent = load_recent or get_recent_checkins
    runtime_timestamp = runtime_timestamp or checkin_runtime_timestamp
    if not is_enabled(user_id):
        return CheckinStartStatus(enabled=False, already_completed_today=False)

    recent_checkins = load_recent(user_id, limit=1)
    if recent_checkins:
        last_checkin = recent_checkins[0]
        last_checkin_timestamp = runtime_timestamp(last_checkin)
        last_checkin_dt = parse_timestamp_full(last_checkin_timestamp)
        if last_checkin_dt is not None and last_checkin_dt.date() == date.today():
            return CheckinStartStatus(
                enabled=True,
                already_completed_today=True,
                last_checkin_timestamp=last_checkin_timestamp,
            )

    return CheckinStartStatus(enabled=True, already_completed_today=False)


@handle_errors("checkin service: recent checkin summary", default_return=RecentCheckinSummary([], False))
def get_recent_checkin_summary(
    user_id: str,
    *,
    limit: int = 7,
    is_enabled=None,
    load_recent=None,
) -> RecentCheckinSummary:
    """Return recent check-ins if check-ins are enabled for the user."""
    is_enabled = is_enabled or is_user_checkins_enabled
    load_recent = load_recent or get_recent_checkins
    if not is_enabled(user_id):
        return RecentCheckinSummary(entries=[], enabled=False)
    return RecentCheckinSummary(
        entries=load_recent(user_id, limit=limit),
        enabled=True,
    )


@handle_errors("checkin service: checkin display date", default_return="Unknown date")
def checkin_display_date(checkin: dict[str, Any]) -> str:
    """Return a stable display date for a check-in."""
    checkin_date = checkin.get("date")
    if checkin_date:
        return checkin_date
    timestamp = checkin_runtime_timestamp(checkin)
    parsed_dt = parse_timestamp_full(timestamp) if timestamp else None
    return parsed_dt.date().isoformat() if parsed_dt else "Unknown date"
