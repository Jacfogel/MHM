#!/usr/bin/env python3
"""
Automated cleanup module for Python cache and data directory.
Tracks when cleanup was last performed and only runs if more than 30 days have passed.

Also provides data directory cleanup (backups, requests, archives) that can run
independently and more frequently.
"""

import os
import shutil
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.service_utilities import DATE_ONLY_FORMAT

CLEANUP_TRACKER_FILENAME = ".last_cache_cleanup"

try:
    from core.config import (
        BASE_DATA_DIR,
    )
except Exception:  # pragma: no cover - fallback for early import failures
    BASE_DATA_DIR = None

# Get component logger for this module
logger = get_component_logger("main")

# File to track last cleanup timestamp
if BASE_DATA_DIR:
    CLEANUP_TRACKER_FILE = str(Path(BASE_DATA_DIR) / CLEANUP_TRACKER_FILENAME)
else:
    CLEANUP_TRACKER_FILE = str(Path("data") / CLEANUP_TRACKER_FILENAME)
DEFAULT_CLEANUP_INTERVAL_DAYS = 30


@handle_errors("getting last cleanup timestamp", default_return=0)
def get_last_cleanup_timestamp() -> float:
    """Get the timestamp of the last cleanup from tracker file."""
    if os.path.exists(CLEANUP_TRACKER_FILE):
        with open(CLEANUP_TRACKER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

            # Store is expected to be epoch seconds
            raw = data.get("last_cleanup_timestamp", 0)

            # IMPORTANT:
            # - 0 means "never cleaned"
            # - -1 means "tracker exists but timestamp is invalid/corrupt"
            if raw in (None, "", 0, "0"):
                return 0.0

            try:
                return float(raw)
            except Exception:
                logger.warning(
                    f"Invalid last_cleanup_timestamp in tracker file: {raw!r}"
                )
                return -1.0

    logger.debug("No valid cleanup tracker file found")
    return 0.0


@handle_errors("updating cleanup timestamp")
def update_cleanup_timestamp() -> None:
    """Update the cleanup tracker file with current timestamp."""
    tracker_path = Path(CLEANUP_TRACKER_FILE)
    tracker_path.parent.mkdir(parents=True, exist_ok=True)

    from core.service_utilities import now_readable_timestamp

    data = {
        # Machine-friendly
        "last_cleanup_timestamp": time.time(),
        # Canonical readable metadata timestamp
        "last_cleanup_date": now_readable_timestamp(),
        # Human-friendly date-only display
        "last_cleanup_date_display": datetime.now().strftime(DATE_ONLY_FORMAT),
    }

    with tracker_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.debug(f"Updated cleanup timestamp: {data['last_cleanup_date_display']}")


@handle_errors("getting invalid tracker status", default_return={})
def _get_cleanup_status__get_invalid_tracker_status():
    """Get status when cleanup tracker exists but contains an invalid timestamp."""
    return {
        "error": "Invalid last_cleanup_timestamp in cleanup tracker file",
        "last_cleanup": "Invalid",
        "days_since": float("inf"),
        "next_cleanup": "On next startup",
    }


@handle_errors("checking if cleanup should run", default_return=False)
def should_run_cleanup(interval_days=DEFAULT_CLEANUP_INTERVAL_DAYS):
    """Check if cleanup should run based on last cleanup time."""
    last_cleanup = get_last_cleanup_timestamp()
    if last_cleanup == 0:
        # Never cleaned up before
        return True

    time_since_cleanup = time.time() - last_cleanup
    days_since_cleanup = time_since_cleanup / (24 * 60 * 60)

    should_cleanup = days_since_cleanup >= interval_days

    if should_cleanup:
        logger.info(
            f"Cache cleanup needed: {days_since_cleanup:.1f} days since last cleanup"
        )
    else:
        logger.debug(
            f"Cache cleanup not needed: {days_since_cleanup:.1f} days since last cleanup"
        )

    return should_cleanup


@handle_errors("finding pycache directories", default_return=[])
def find_pycache_dirs(root_path):
    """Find all __pycache__ directories recursively."""
    pycache_dirs = []
    for root, dirs, _files in os.walk(root_path):
        if "__pycache__" in dirs:
            pycache_path = Path(root) / "__pycache__"
            pycache_dirs.append(str(pycache_path))
    return pycache_dirs


@handle_errors("finding pyc files", default_return=[])
def find_pyc_files(root_path):
    """Find all .pyc files recursively."""
    pyc_files = []
    for root, _dirs, files in os.walk(root_path):
        for file in files:
            if file.endswith(".pyc") or file.endswith(".pyo"):
                pyc_files.append(str(Path(root) / file))
    return pyc_files


@handle_errors("calculating cache size", default_return=0)
def _calculate_cache_size__calculate_pycache_directories_size(pycache_dirs):
    """Calculate total size of __pycache__ directories."""
    total_size = 0

    for pycache_dir in pycache_dirs:
        try:
            if os.path.exists(pycache_dir):
                for root, _dirs, files in os.walk(pycache_dir):
                    for file in files:
                        filepath = str(Path(root) / file)
                        if os.path.exists(filepath):
                            total_size += os.path.getsize(filepath)
        except Exception as e:
            logger.warning(f"Error calculating size for {pycache_dir}: {e}")

    return total_size


@handle_errors("calculating cache size", default_return=0)
def _calculate_cache_size__calculate_pyc_files_size(pyc_files):
    """Calculate total size of standalone .pyc files."""
    total_size = 0

    for pyc_file in pyc_files:
        try:
            if os.path.exists(pyc_file):
                total_size += os.path.getsize(pyc_file)
        except Exception as e:
            logger.warning(f"Error calculating size for {pyc_file}: {e}")

    return total_size


@handle_errors("calculating cache size", default_return=0)
def calculate_cache_size(pycache_dirs, pyc_files):
    """Calculate total size of cache files."""
    # Calculate size of __pycache__ directories
    pycache_size = _calculate_cache_size__calculate_pycache_directories_size(
        pycache_dirs
    )

    # Calculate size of standalone .pyc files
    pyc_files_size = _calculate_cache_size__calculate_pyc_files_size(pyc_files)

    return pycache_size + pyc_files_size


@handle_errors("discovering cache files", default_return=([], []))
def _perform_cleanup__discover_cache_files(root_path):
    """Discover all cache files and directories in the given root path."""
    pycache_dirs = find_pycache_dirs(root_path)
    pyc_files = find_pyc_files(root_path)
    return pycache_dirs, pyc_files


@handle_errors("logging discovery results", default_return=0)
def _perform_cleanup__log_discovery_results(pycache_dirs, pyc_files):
    """Calculate total size and log discovery results."""
    total_size = calculate_cache_size(pycache_dirs, pyc_files)

    logger.info(
        f"Found {len(pycache_dirs)} __pycache__ directories and {len(pyc_files)} .pyc files"
    )
    logger.info(
        f"Total cache size: {total_size / 1024:.1f} KB ({total_size / (1024*1024):.2f} MB)"
    )

    return total_size


@handle_errors("removing cache files", default_return=(0, 0))
def _perform_cleanup__remove_cache_files(pycache_dirs, pyc_files):
    """Remove all discovered cache directories and files."""
    # Remove __pycache__ directories
    removed_dirs = _perform_cleanup__remove_cache_directories(pycache_dirs)

    # Remove standalone .pyc files
    removed_files = _perform_cleanup__remove_cache_files_list(pyc_files)

    return removed_dirs, removed_files


@handle_errors("removing cache directories", default_return=0)
def _perform_cleanup__remove_cache_directories(pycache_dirs):
    """Remove all __pycache__ directories."""
    removed_dirs = 0
    for pycache_dir in pycache_dirs:
        try:
            if os.path.exists(pycache_dir):
                shutil.rmtree(pycache_dir)
                removed_dirs += 1
                logger.debug(f"Removed directory: {pycache_dir}")
        except Exception as e:
            logger.warning(f"Failed to remove directory {pycache_dir}: {e}")
    return removed_dirs


@handle_errors("removing cache files list", default_return=0)
def _perform_cleanup__remove_cache_files_list(pyc_files):
    """Remove all standalone .pyc files."""
    removed_files = 0
    for pyc_file in pyc_files:
        try:
            if os.path.exists(pyc_file):
                os.remove(pyc_file)
                removed_files += 1
                logger.debug(f"Removed file: {pyc_file}")
        except Exception as e:
            logger.warning(f"Failed to remove file {pyc_file}: {e}")
    return removed_files


@handle_errors("logging completion results")
def _perform_cleanup__log_completion_results(removed_dirs, removed_files, total_size):
    """Log the final cleanup results and statistics."""
    logger.info(
        f"Cleanup complete: Removed {removed_dirs} directories and {removed_files} files"
    )
    logger.info(
        f"Freed up {total_size / 1024:.1f} KB ({total_size / (1024*1024):.2f} MB)"
    )


@handle_errors("performing cleanup", default_return=False)
def perform_cleanup(root_path="."):
    """Perform the actual cleanup of cache files."""
    root_path = Path(root_path).resolve()

    logger.info(f"Starting automatic cache cleanup in: {root_path}")

    # Find cache files
    pycache_dirs, pyc_files = _perform_cleanup__discover_cache_files(root_path)

    if not pycache_dirs and not pyc_files:
        logger.info("No cache files found to clean up")
        return True

    # Calculate total size and log discovery results
    total_size = _perform_cleanup__log_discovery_results(pycache_dirs, pyc_files)

    # Remove cache files
    removed_dirs, removed_files = _perform_cleanup__remove_cache_files(
        pycache_dirs, pyc_files
    )

    # Log final results
    _perform_cleanup__log_completion_results(removed_dirs, removed_files, total_size)

    return True


@handle_errors("cleaning up old backup files", default_return=False)
def cleanup_old_backup_files():
    """
    Clean up old backup files from data/backups directory.
    Uses same retention policy as BackupManager (30 days by default, max 10 files).
    """
    try:
        from core.config import get_backups_dir

        backup_dir = Path(get_backups_dir())

        if not backup_dir.exists():
            return True

        # Get retention settings (same as BackupManager)
        try:
            backup_retention_days = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
        except Exception:
            backup_retention_days = 30
        max_backups = 10

        # Gather .zip backups with mtime
        backup_files = []
        now_ts = time.time()

        for file_path in backup_dir.iterdir():
            if file_path.is_file() and file_path.suffix == ".zip":
                try:
                    mtime = file_path.stat().st_mtime
                    backup_files.append((str(file_path), mtime))
                except Exception:
                    continue

        if not backup_files:
            return True

        removed_count = 0

        # Age-based retention: remove files older than retention_days
        age_cutoff = now_ts - (backup_retention_days * 24 * 3600)
        for file_path, mtime in list(backup_files):
            if mtime < age_cutoff:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(
                            f"Removed old backup file (> {backup_retention_days}d): {file_path}"
                        )
                        backup_files.remove((file_path, mtime))
                        removed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to remove old backup {file_path}: {e}")

        # Count-based retention: keep newest max_backups
        backup_files.sort(key=lambda x: x[1], reverse=True)
        for file_path, _ in backup_files[max_backups:]:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(
                        f"Removed old backup file (>{max_backups} backups): {file_path}"
                    )
                    removed_count += 1
            except Exception as e:
                logger.warning(f"Failed to remove old backup {file_path}: {e}")

        if removed_count > 0:
            logger.info(f"Backup cleanup: removed {removed_count} old backup file(s)")

        return True
    except Exception as e:
        logger.warning(f"Backup cleanup failed (non-critical): {e}")
        return False


@handle_errors("cleaning up old request files", default_return=False)
def cleanup_old_request_files():
    """
    Clean up old request files from data/requests directory.
    Removes request files older than 7 days.
    """
    try:
        from core.config import BASE_DATA_DIR

        requests_dir = Path(BASE_DATA_DIR) / "requests"

        if not requests_dir.exists():
            return True

        # Remove request files older than 7 days
        request_retention_days = 7
        age_cutoff = time.time() - (request_retention_days * 24 * 3600)
        removed_count = 0

        for file_path in requests_dir.iterdir():
            if file_path.is_file():
                try:
                    mtime = file_path.stat().st_mtime
                    if mtime < age_cutoff:
                        os.remove(file_path)
                        logger.info(
                            f"Removed old request file (> {request_retention_days}d): {file_path.name}"
                        )
                        removed_count += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to remove old request file {file_path}: {e}"
                    )

        if removed_count > 0:
            logger.info(f"Request cleanup: removed {removed_count} old request file(s)")

        return True
    except Exception as e:
        logger.warning(f"Request cleanup failed (non-critical): {e}")
        return False


@handle_errors("cleaning up old message archives", default_return=False)
def cleanup_old_message_archives():
    """
    Clean up old message archive files from user directories.
    Removes archive files older than 90 days (archives are already compressed).
    """
    try:
        from core.config import BASE_DATA_DIR
        from core.user_data_handlers import get_all_user_ids

        user_ids = get_all_user_ids()
        if not user_ids:
            return True

        # Remove archive files older than 90 days
        archive_retention_days = 90
        age_cutoff = time.time() - (archive_retention_days * 24 * 3600)
        removed_count = 0

        for user_id in user_ids:
            try:
                user_dir = (
                    Path(BASE_DATA_DIR) / "users" / user_id / "messages" / "archives"
                )
                if not user_dir.exists():
                    continue

                for archive_file in user_dir.iterdir():
                    if archive_file.is_file() and archive_file.name.startswith(
                        "sent_messages_archive_"
                    ):
                        try:
                            mtime = archive_file.stat().st_mtime
                            if mtime < age_cutoff:
                                os.remove(archive_file)
                                logger.debug(
                                    f"Removed old message archive (> {archive_retention_days}d): {archive_file.name}"
                                )
                                removed_count += 1
                        except Exception as e:
                            logger.warning(
                                f"Failed to remove old archive {archive_file}: {e}"
                            )
            except Exception as e:
                logger.warning(f"Failed to clean archives for user {user_id}: {e}")

        if removed_count > 0:
            logger.info(
                f"Archive cleanup: removed {removed_count} old message archive file(s)"
            )

        return True
    except Exception as e:
        logger.warning(f"Archive cleanup failed (non-critical): {e}")
        return False


@handle_errors("cleaning up tests data directory", default_return=False)
def cleanup_tests_data_directory():
    """
    Clean up temporary files and directories in tests/data/ directory.
    Removes tmp_* directories, test JSON files, and other test artifacts.
    This is separate from production data cleanup.
    """
    try:
        # Find project root by looking for tests/data directory
        # Start from current file location and walk up to find project root
        current_file = Path(__file__).resolve()
        project_root = (
            current_file.parent.parent
        )  # core/auto_cleanup.py -> core -> project_root
        tests_data_dir = project_root / "tests" / "data"

        # If that doesn't exist, try relative to BASE_DATA_DIR
        if not tests_data_dir.exists():
            from core.config import BASE_DATA_DIR

            if BASE_DATA_DIR:
                base_path = Path(BASE_DATA_DIR).resolve()
                # If BASE_DATA_DIR is already tests/data, use it directly
                if base_path.name == "data" and base_path.parent.name == "tests":
                    tests_data_dir = base_path
                else:
                    # Otherwise, try to find tests/data relative to BASE_DATA_DIR
                    potential_tests_data = base_path.parent.parent / "tests" / "data"
                    if potential_tests_data.exists():
                        tests_data_dir = potential_tests_data

        if not tests_data_dir.exists():
            return True

        removed_dirs = 0
        removed_files = 0

        # Remove tmp* directories directly in tests/data (but not the "tmp" directory itself)
        # Matches: tmp_*, tmp*, pytest-of-*
        for item in tests_data_dir.iterdir():
            try:
                if item.is_dir():
                    # Match tmp_*, tmp* (but not just "tmp"), and pytest-of-*
                    if (
                        item.name.startswith("tmp_")
                        or (item.name.startswith("tmp") and item.name != "tmp")
                        or item.name.startswith("pytest-of-")
                    ):
                        shutil.rmtree(item, ignore_errors=True)
                        removed_dirs += 1
                elif item.is_file():
                    # Clean up test JSON files
                    if item.suffix == ".json":
                        test_json_patterns = ["test_", ".tmp_", "welcome_tracking.json"]
                        if any(
                            item.name.startswith(pattern)
                            for pattern in test_json_patterns
                        ):
                            item.unlink(missing_ok=True)
                            removed_files += 1
                    # Clean up .last_cache_cleanup file
                    elif item.name == ".last_cache_cleanup":
                        item.unlink(missing_ok=True)
                        removed_files += 1
            except Exception as e:
                logger.debug(f"Failed to remove {item}: {e}")

        if removed_dirs > 0 or removed_files > 0:
            logger.info(
                f"Tests data cleanup: removed {removed_dirs} directory(ies) and {removed_files} file(s)"
            )

        return True
    except Exception as e:
        logger.warning(f"Tests data cleanup failed (non-critical): {e}")
        return False


@handle_errors("cleaning up data directory", default_return=False)
def cleanup_data_directory():
    """
    Clean up old files in the data directory (backups, requests, archives).
    This can be called independently of the full auto_cleanup cycle.
    Returns True if cleanup was performed, False otherwise.
    """
    logger.info("Starting data directory cleanup...")

    results = {"backups": False, "requests": False, "archives": False}

    try:
        results["backups"] = cleanup_old_backup_files()
    except Exception as e:
        logger.warning(f"Backup cleanup failed: {e}")

    try:
        results["requests"] = cleanup_old_request_files()
    except Exception as e:
        logger.warning(f"Request cleanup failed: {e}")

    try:
        results["archives"] = cleanup_old_message_archives()
    except Exception as e:
        logger.warning(f"Archive cleanup failed: {e}")

    success = any(results.values())
    if success:
        logger.info("Data directory cleanup completed")
    else:
        logger.debug("Data directory cleanup: no files to clean")

    return success


@handle_errors("auto cleanup if needed", default_return=False)
def auto_cleanup_if_needed(root_path=".", interval_days=DEFAULT_CLEANUP_INTERVAL_DAYS):
    """
    Main function to check if cleanup is needed and perform it if so.
    Returns True if cleanup was performed, False if not needed.
    """
    if not should_run_cleanup(interval_days):
        return False

    success = perform_cleanup(root_path)
    if success:
        # Also archive old messages during monthly cleanup
        try:
            archive_old_messages_for_all_users()
        except Exception as e:
            logger.warning(
                f"Message archiving failed during cleanup (non-critical): {e}"
            )

        # Clean up data directory files (backups, requests, archives)
        try:
            cleanup_old_backup_files()
        except Exception as e:
            logger.warning(
                f"Backup cleanup failed during auto cleanup (non-critical): {e}"
            )

        try:
            cleanup_old_request_files()
        except Exception as e:
            logger.warning(
                f"Request cleanup failed during auto cleanup (non-critical): {e}"
            )

        try:
            cleanup_old_message_archives()
        except Exception as e:
            logger.warning(
                f"Archive cleanup failed during auto cleanup (non-critical): {e}"
            )

        update_cleanup_timestamp()
        return True
    else:
        logger.error("Cleanup failed")
        return False


@handle_errors("archiving old messages for all users", default_return=False)
def archive_old_messages_for_all_users():
    """
    Archive old messages for all users during monthly cleanup.
    This runs alongside the cache cleanup to maintain message file sizes.
    """
    try:
        from core.user_data_handlers import get_all_user_ids
        from core.message_management import archive_old_messages

        user_ids = get_all_user_ids()
        if not user_ids:
            logger.debug("No users found for message archiving")
            return True

        logger.info(f"Starting message archiving for {len(user_ids)} users")

        archived_count = 0
        for user_id in user_ids:
            try:
                if archive_old_messages(user_id, days_to_keep=365):
                    archived_count += 1
                    logger.debug(f"Successfully archived messages for user {user_id}")
                else:
                    logger.debug(f"No messages to archive for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to archive messages for user {user_id}: {e}")

        logger.info(
            f"Message archiving completed: {archived_count}/{len(user_ids)} users processed"
        )
        return True

    except Exception as e:
        logger.error(f"Error during message archiving: {e}")
        return False


@handle_errors("getting never cleaned status", default_return={})
def _get_cleanup_status__get_never_cleaned_status():
    """Get status when cleanup has never been performed."""
    return {
        "last_cleanup": "Never",
        "days_since": float("inf"),
        "next_cleanup": "On next startup",
    }


@handle_errors("calculating days since cleanup", default_return=0)
def _get_cleanup_status__calculate_days_since_cleanup(last_cleanup_timestamp):
    """Calculate days since last cleanup."""
    last_date = datetime.fromtimestamp(last_cleanup_timestamp)
    days_since = (datetime.now() - last_date).days
    return days_since, last_date


@handle_errors("formatting next cleanup date", default_return="Unknown")
def _get_cleanup_status__format_next_cleanup_date(last_date: datetime) -> str:
    """Format the next cleanup date or return 'Overdue'."""
    next_cleanup_date = last_date + timedelta(days=DEFAULT_CLEANUP_INTERVAL_DAYS)
    now = datetime.now()

    # Show "Overdue" if the next cleanup date is today or in the past
    # Use date comparison (ignoring time) to avoid microsecond timing issues
    if next_cleanup_date.date() <= now.date():
        return "Overdue"

    # Date-only output for status display
    return next_cleanup_date.strftime(DATE_ONLY_FORMAT)


@handle_errors("building status response", default_return={})
def _get_cleanup_status__build_status_response(last_date, days_since, next_cleanup):
    """Build the final status response dictionary."""
    return {
        # Use canonical readable format for display/metadata text.
        "last_cleanup": last_date.strftime(DATE_ONLY_FORMAT),
        "days_since": days_since,
        "next_cleanup": next_cleanup,
    }


@handle_errors(
    "getting cleanup status", default_return={"error": "Failed to get status"}
)
def get_cleanup_status():
    """Get information about the cleanup status."""
    last_cleanup_timestamp = get_last_cleanup_timestamp()

    # Handle case where cleanup has never been performed
    if last_cleanup_timestamp == 0:
        return _get_cleanup_status__get_never_cleaned_status()

    # Handle case where tracker file exists but is malformed/corrupt
    if last_cleanup_timestamp < 0:
        return _get_cleanup_status__get_invalid_tracker_status()

    # Calculate days since cleanup and get last date
    days_since, last_date = _get_cleanup_status__calculate_days_since_cleanup(
        last_cleanup_timestamp
    )

    # Format next cleanup date
    next_cleanup = _get_cleanup_status__format_next_cleanup_date(last_date)

    # Build and return status response
    return _get_cleanup_status__build_status_response(
        last_date, days_since, next_cleanup
    )


if __name__ == "__main__":
    # For testing purposes
    import sys
    from core.logger import setup_logging

    setup_logging()

    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        print("Force cleaning...")
        perform_cleanup()
        update_cleanup_timestamp()
    elif len(sys.argv) > 1 and sys.argv[1] == "--status":
        status = get_cleanup_status()
        print(f"Last cleanup: {status['last_cleanup']}")
        print(f"Days since cleanup: {status['days_since']}")
        print(f"Next cleanup: {status['next_cleanup']}")
    else:
        result = auto_cleanup_if_needed()
        print(f"Cleanup performed: {result}")
