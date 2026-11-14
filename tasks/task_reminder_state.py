"""Shared reminder delivery state for scheduling, snoozing, and occurrence skips."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.time_utilities import DATE_ONLY, TIME_ONLY_SECOND, format_timestamp

logger = get_component_logger("main")


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


@handle_errors("scheduling a deferred task reminder", default_return=False)
def schedule_deferred_task_reminder(user_id: str, task_id: str, until: datetime) -> bool:
    """Schedule the one-time reminder after a snooze or skip has been saved."""
    from scheduler.runtime_access import get_scheduler_manager

    scheduler_manager = get_scheduler_manager()
    if scheduler_manager and scheduler_manager.schedule_task_reminder_at_datetime(
        user_id,
        task_id,
        format_timestamp(until, DATE_ONLY),
        format_timestamp(until, TIME_ONLY_SECOND),
    ):
        return True
    logger.warning(
        f"Could not schedule deferred reminder for task {task_id} (user {user_id}) at {until}"
    )
    return False
