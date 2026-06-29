# scheduler/health_sync_jobs.py

"""Automated Google Health sync schedule registration."""

import os

import schedule

from core.config import GOOGLE_HEALTH_ENABLED
from core.error_handling import handle_errors
from core.logger import get_component_logger
from integrations.google_health.sync_manager import sync_users_due_for_schedule

logger = get_component_logger("scheduler")

# Poll interval — sync times from GOOGLE_HEALTH_SYNC_TIMES are evaluated per-user
# in account timezone during each poll.
HEALTH_SYNC_POLL_MINUTES = 30


@handle_errors("running scheduled health sync")
def run_scheduled_health_sync() -> None:
    """Callback for schedule library — sync users due in their local timezone."""
    if os.getenv("MHM_TESTING") == "1":
        return
    if not GOOGLE_HEALTH_ENABLED:
        return
    count = sync_users_due_for_schedule()
    logger.info(f"Scheduled Google Health sync finished ({count} users synced)")


@handle_errors("registering health sync jobs")
def register_health_sync_jobs() -> None:
    """Register periodic poll for per-user timezone-aware health sync."""
    if not GOOGLE_HEALTH_ENABLED:
        logger.debug("Google Health disabled — skipping sync job registration")
        return

    schedule.every(HEALTH_SYNC_POLL_MINUTES).minutes.do(run_scheduled_health_sync)
    logger.info(
        f"Scheduled Google Health sync poll every {HEALTH_SYNC_POLL_MINUTES} minutes "
        "(per-user account timezone)"
    )
