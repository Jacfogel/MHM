# scheduler/health_sync_schedule.py
"""Per-user local wall-clock schedule for Google Health sync."""

from __future__ import annotations

from datetime import datetime

from core.config import parse_google_health_sync_times
from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.time_utilities import parse_time_only_minute
from scheduler.user_timezone import localized_now_for_user

logger = get_component_logger("scheduler")


@handle_errors("sorting Google Health sync times", default_return=[])
def _sorted_sync_times(sync_times: list[str]) -> list[str]:
    """Sort HH:MM sync times chronologically."""
    parsed: list[tuple[str, datetime | None]] = [
        (time_str, parse_time_only_minute(time_str)) for time_str in sync_times
    ]
    valid = [(time_str, dt) for time_str, dt in parsed if dt is not None]
    invalid = [time_str for time_str, dt in parsed if dt is None]
    for time_str in invalid:
        logger.warning(f"Ignoring invalid Google Health sync time: {time_str!r}")
    valid.sort(key=lambda item: (item[1].hour, item[1].minute))
    return [time_str for time_str, _ in valid]


@handle_errors("building local Google Health slot datetime", default_return=None)
def _slot_datetime_local(now_local: datetime, time_str: str) -> datetime | None:
    """Build timezone-aware slot datetime on the same local calendar day as now_local."""
    parsed = parse_time_only_minute(time_str)
    if parsed is None:
        return None
    return now_local.replace(
        hour=parsed.hour,
        minute=parsed.minute,
        second=0,
        microsecond=0,
    )


@handle_errors("building Google Health sync slot key", default_return="")
def build_sync_slot_key(local_date: str, time_str: str) -> str:
    """Return a stable slot identifier: ``YYYY-MM-DD_HH:MM``."""
    return f"{local_date}_{time_str}"


@handle_errors("getting due Google Health sync slot", default_return=None)
def get_due_sync_slot_key(
    user_id: str,
    *,
    now_local: datetime | None = None,
    sync_times: list[str] | None = None,
    last_scheduled_slot: str = "",
) -> str | None:
    """
    Return the latest due sync slot key for ``user_id``, or None if not due.

    Sync times from ``GOOGLE_HEALTH_SYNC_TIMES`` are interpreted in the user's
    account timezone (``account.timezone``).
    """
    if not user_id:
        return None

    if now_local is None:
        now_local = localized_now_for_user(user_id)
    if now_local is None:
        return None
    if sync_times is None:
        sync_times = parse_google_health_sync_times()

    local_date = now_local.date().isoformat()
    due_keys: list[str] = []
    for time_str in _sorted_sync_times(sync_times):
        slot_dt = _slot_datetime_local(now_local, time_str)
        if slot_dt and now_local >= slot_dt:
            due_keys.append(build_sync_slot_key(local_date, time_str))

    if not due_keys:
        return None

    latest = due_keys[-1]
    if last_scheduled_slot == latest:
        return None
    return latest
