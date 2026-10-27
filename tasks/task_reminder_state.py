"""Shared reminder delivery state for scheduling, snoozing, and occurrence skips."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from core.error_handling import handle_errors
from core.time_utilities import DATE_ONLY, format_timestamp


@handle_errors("building today's reminder sent fields", default_return={})
def reminder_sent_fields(user_id: str, now_dt: datetime | None = None) -> dict[str, Any]:
    """Mark a reminder handed off on the user's local calendar date.

    ``reminder_sent`` stays true after the first handoff. ``reminder_sent_on``
    is the date that blocks a second copy. A later day can send again.
    """
    from scheduler.user_timezone import user_local_now_naive

    moment = now_dt if now_dt is not None else user_local_now_naive(user_id)
    sent_on = format_timestamp(moment, DATE_ONLY)
    if not sent_on:
        return {"reminder_sent": True}
    return {"reminder_sent": True, "reminder_sent_on": sent_on}
