# Orphaned scheduled task-reminder cleanup (schedule library job scan).

from __future__ import annotations

import schedule
from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger
from tasks import get_task_by_id
from tasks.task_data_handlers import runtime_task_is_completed

logger = get_component_logger("scheduler")


@handle_errors("cleaning up orphaned task reminders")
def cleanup_orphaned_task_reminders(scheduler_manager: Any) -> None:
    try:
        logger.info("Starting periodic cleanup of orphaned task reminders")
        from core import get_all_user_ids

        get_all_user_ids()

        orphaned_count = 0
        total_checked = 0
        jobs_to_check = []
        handle_fn = scheduler_manager.handle_task_reminder

        for job in schedule.jobs:
            try:
                job_func = job.job_func
                if not job_func:
                    continue
                if (
                    hasattr(job_func, "func") and job_func.func == handle_fn
                ) and hasattr(job_func, "keywords"):
                    kwargs = job_func.keywords
                    user_id = kwargs.get("user_id")
                    task_identifier = kwargs.get("task_identifier")
                    if user_id and task_identifier:
                        jobs_to_check.append((job, user_id, task_identifier))
                        total_checked += 1
            except Exception as e:
                logger.debug(f"Could not inspect job for orphaned cleanup: {e}")
                continue

        for job, user_id, task_identifier in jobs_to_check:
            try:
                task = get_task_by_id(user_id, task_identifier)
                if not task:
                    try:
                        schedule.jobs.remove(job)
                        orphaned_count += 1
                        logger.info(
                            f"Removed orphaned reminder for non-existent task {task_identifier}, user {user_id}"
                        )
                    except ValueError:
                        pass
                elif runtime_task_is_completed(task):
                    try:
                        schedule.jobs.remove(job)
                        orphaned_count += 1
                        logger.info(
                            f"Removed reminder for completed task {task_identifier}, user {user_id}"
                        )
                    except ValueError:
                        pass
            except Exception as e:
                logger.debug(
                    f"Error checking task {task_identifier} for user {user_id}: {e}"
                )
                continue

        logger.info(
            f"Orphaned reminder cleanup complete: checked {total_checked} reminders, removed {orphaned_count} orphaned reminders"
        )
    except Exception as e:
        logger.error(
            f"Error during orphaned task reminder cleanup: {e}", exc_info=True
        )
