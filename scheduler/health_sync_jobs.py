# scheduler/health_sync_jobs.py

"""Automated Google Health sync schedule registration."""

import os

import schedule

from core.config import GOOGLE_HEALTH_ENABLED, parse_google_health_sync_times
from core.error_handling import handle_errors
from core.logger import get_component_logger
from integrations.google_health.sync_manager import sync_all_enabled_users

logger = get_component_logger("scheduler")


@handle_errors("running scheduled health sync")
def run_scheduled_health_sync() -> None:
    """Callback for schedule library — sync all enabled users."""
    if os.getenv("MHM_TESTING") == "1":
        return
    if not GOOGLE_HEALTH_ENABLED:
        return
    count = sync_all_enabled_users()
    logger.info(f"Scheduled Google Health sync finished ({count} users synced)")


@handle_errors("registering health sync jobs")
def register_health_sync_jobs() -> None:
    """Register 1–2 daily automated health sync times from config."""
    if not GOOGLE_HEALTH_ENABLED:
        logger.debug("Google Health disabled — skipping sync job registration")
        return

    for time_str in parse_google_health_sync_times():
        schedule.every().day.at(time_str).do(run_scheduled_health_sync)
        logger.info(f"Scheduled Google Health sync at {time_str}")
