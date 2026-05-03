# Registration of system-wide schedule jobs (daily maintenance, full daily run).

import schedule

from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("scheduler")


@handle_errors("registering system daily schedule jobs", user_friendly=False, re_raise=True)
def register_system_daily_jobs(scheduler_manager) -> None:
    """Register 02:00 log archival and 01:00 full daily scheduler jobs on the global ``schedule`` queue."""
    schedule.every().day.at("02:00").do(scheduler_manager.perform_daily_log_archival)
    logger.info("Scheduled new daily job for log archival at 02:00")
    schedule.every().day.at("01:00").do(scheduler_manager.run_full_daily_scheduler)
    logger.info(
        "Scheduled full daily scheduler job at 01:00 (includes checkins, task reminders, cleanup, and backup check)"
    )
