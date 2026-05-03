# Log archival and backup checks invoked by SchedulerManager.

from core.backup_manager import backup_manager
from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.time_utilities import (
    now_datetime_full,
    now_timestamp_filename,
    parse_timestamp_full,
)

logger = get_component_logger("scheduler")


@handle_errors("cleaning up scheduler wake tasks")
def cleanup_scheduler_wake_tasks() -> None:
    """Delete stale Windows wake tasks created by scheduler jobs."""
    import subprocess

    from core import get_all_user_ids

    logger.info("Starting system task cleanup for all users...")

    try:
        result = subprocess.run(
            ["schtasks", "/query", "/fo", "LIST", "/v"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.debug(f"Could not query system tasks: {result.stderr}")
            logger.info("System task cleanup completed (no tasks to clean).")
            return

        tasks = result.stdout.splitlines()
        tasks_deleted = 0
        user_ids = get_all_user_ids()

        for line in tasks:
            if line.startswith("TaskName:"):
                task_name = line.split(":")[1].strip()
                if "Wake_" in task_name and any(
                    user_id in task_name for user_id in user_ids
                ):
                    logger.info(f"Deleting old system task: {task_name}")
                    try:
                        del_result = subprocess.run(
                            ["schtasks", "/delete", "/tn", task_name, "/f"],
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        if del_result.returncode == 0:
                            tasks_deleted += 1
                            logger.debug(f"Successfully deleted task: {task_name}")
                        else:
                            logger.debug(
                                f"Task {task_name} may already be deleted: {del_result.stderr}"
                            )
                    except Exception as del_error:
                        logger.debug(f"Error deleting task {task_name}: {del_error}")

        logger.info(f"System task cleanup completed: {tasks_deleted} tasks deleted.")
        if tasks_deleted > 0:
            logger.debug(f"Deleted {tasks_deleted} old system tasks")

    except Exception as query_error:
        logger.debug(f"Error querying system tasks for cleanup: {query_error}")
        logger.info("System task cleanup skipped (query failed).")


@handle_errors("performing daily log archival")
def perform_daily_log_archival() -> None:
    try:
        from core.logger import compress_old_logs, cleanup_old_archives

        logger.info("Starting daily log archival process")
        compressed_count = compress_old_logs()
        logger.info(f"Daily log archival: compressed {compressed_count} old log files")
        cleaned_count = cleanup_old_archives()
        logger.info(f"Daily log archival: cleaned {cleaned_count} old archive files")
        logger.info("Daily log archival process completed successfully")
    except Exception as e:
        logger.error(f"Error during daily log archival: {e}")


@handle_errors("checking and performing weekly backup")
def check_and_perform_weekly_backup() -> None:
    try:
        backups = backup_manager.list_backups()

        @handle_errors(
            "checking weekly backup entry during scheduler backup check",
            default_return=False,
        )
        def _is_weekly_backup_entry(backup_entry: dict) -> bool:
            if not isinstance(backup_entry, dict):
                return False
            backup_name = str(backup_entry.get("backup_name") or "")
            file_name = str(backup_entry.get("file_name") or "")
            return backup_name.startswith("weekly_backup_") or file_name.startswith(
                "weekly_backup_"
            )

        weekly_backups = [b for b in backups if _is_weekly_backup_entry(b)]
        needs_backup = False
        if not weekly_backups:
            logger.info("No weekly backups found - creating weekly backup")
            needs_backup = True
        else:
            last_backup = weekly_backups[0]
            created_at_str = last_backup.get("created_at") or ""
            last_backup_time = parse_timestamp_full(created_at_str)
            if last_backup_time is None:
                logger.warning(
                    f"Latest weekly backup has invalid created_at timestamp '{created_at_str}' - creating a new backup for safety"
                )
                needs_backup = True
            else:
                days_since_backup = (now_datetime_full() - last_backup_time).days
                if days_since_backup >= 7:
                    logger.info(
                        f"Last weekly backup was {days_since_backup} days ago - creating new weekly backup"
                    )
                    needs_backup = True
                else:
                    logger.debug(
                        f"Weekly backup not needed - latest weekly backup was {days_since_backup} days ago"
                    )

        if needs_backup:
            logger.info("Starting weekly backup process")
            backup_path = backup_manager.create_backup(
                backup_name=f"weekly_backup_{now_timestamp_filename()}",
                include_users=True,
                include_config=True,
                include_logs=False,
            )
            if backup_path:
                logger.info(f"Weekly backup completed successfully: {backup_path}")
                backups = backup_manager.list_backups()
                latest_weekly = [b for b in backups if _is_weekly_backup_entry(b)]
                if latest_weekly:
                    latest_backup = latest_weekly[0]
                    latest_created_at_str = latest_backup.get("created_at") or ""
                    backup_time = parse_timestamp_full(latest_created_at_str)
                    if backup_time is None:
                        logger.warning(
                            f"Backup health: Latest weekly backup has invalid created_at '{latest_created_at_str}'"
                        )
                    else:
                        days_old = (now_datetime_full() - backup_time).days
                        backup_size_mb = latest_backup.get("file_size", 0) / (1024 * 1024)
                        logger.info(
                            f"Backup health: Latest weekly backup is {days_old} days old, size: {backup_size_mb:.2f} MB"
                        )
                else:
                    logger.warning(
                        "No weekly backups found after creation - backup health check failed"
                    )
            else:
                logger.error("Weekly backup failed - no backup path returned")
    except Exception as e:
        logger.error(f"Error during weekly backup check: {e}")
