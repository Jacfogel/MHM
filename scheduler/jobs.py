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

    try:
        from scheduler.health_sync_jobs import register_health_sync_jobs

        register_health_sync_jobs()
    except Exception as e:
        logger.warning(f"Failed to register Google Health sync jobs: {e}")


@handle_errors("registering full daily maintenance schedule jobs")
def register_full_daily_maintenance_jobs(scheduler_manager) -> None:
    """Register maintenance jobs refreshed during the full daily scheduler run."""
    register_system_daily_jobs(scheduler_manager)

    schedule.every().day.at("03:00").do(
        scheduler_manager.cleanup_orphaned_task_reminders
    )
    logger.info("Scheduled daily orphaned task reminder cleanup at 03:00")

    try:
        from core.auto_cleanup import (
            cleanup_data_directory,
            cleanup_tests_data_directory,
        )

        schedule.every().day.at("04:00").do(cleanup_data_directory)
        logger.info("Scheduled daily data directory cleanup at 04:00")
        schedule.every().day.at("04:05").do(cleanup_tests_data_directory)
        logger.info("Scheduled daily tests data directory cleanup at 04:05")
    except Exception as e:
        logger.warning(f"Failed to schedule data directory cleanup: {e}")
