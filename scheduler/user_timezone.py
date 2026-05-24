# scheduler/user_timezone.py
"""Resolve account timezone for scheduler wall-clock comparisons."""

from __future__ import annotations

from datetime import datetime

import pytz

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.time_utilities import now_datetime_full

logger = get_component_logger("scheduler")

DEFAULT_SCHEDULER_TIMEZONE = "America/Regina"

# Safe aware sentinel for @handle_errors default_return (pytz cannot localize datetime.min).
_FALLBACK_LOCALIZED_NOW = pytz.timezone(DEFAULT_SCHEDULER_TIMEZONE).localize(
    datetime(1970, 1, 1, 12, 0, 0)
)


@handle_errors("resolving user timezone", default_return=DEFAULT_SCHEDULER_TIMEZONE)
def resolve_user_timezone_str(user_id: str) -> str:
    """Return a valid pytz timezone name for ``user_id`` (account ``timezone`` field)."""
    if not user_id:
        return DEFAULT_SCHEDULER_TIMEZONE

    from core import get_user_data

    result = get_user_data(user_id, "account")
    account = result.get("account") or {}
    tz_name = (account.get("timezone") or "").strip()
    if not tz_name:
        return DEFAULT_SCHEDULER_TIMEZONE

    try:
        pytz.timezone(tz_name)
        return tz_name
    except pytz.exceptions.UnknownTimeZoneError:
        logger.warning(
            f"Unknown timezone {tz_name!r} for user {user_id}; "
            f"using {DEFAULT_SCHEDULER_TIMEZONE}"
        )
        return DEFAULT_SCHEDULER_TIMEZONE


@handle_errors("localizing now for user", default_return=_FALLBACK_LOCALIZED_NOW)
def localized_now_for_user(user_id: str) -> datetime:
    """Timezone-aware 'now' in the user's account timezone."""
    tz = pytz.timezone(resolve_user_timezone_str(user_id))
    return tz.localize(now_datetime_full())
