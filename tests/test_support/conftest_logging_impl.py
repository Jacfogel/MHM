"""
Logging implementation for test conftest.

SessionLogRotationManager, LogLifecycleManager, and _write_test_log_header live here.
Conftest keeps fixture/hook definitions and instantiates these; this module holds
the implementation to keep conftest manageable.
"""

import os
import re
import shutil
import hashlib
from pathlib import Path

from core.time_utilities import (
    now_datetime_full,
    now_timestamp_filename,
    now_timestamp_full,
    parse_timestamp_full,
    format_timestamp,
    TIMESTAMP_FULL,
)


def _get_test_logger():
    """Lazy import to avoid circular import (conftest imports this module)."""
    from tests.conftest import test_logger
    return test_logger


def _write_test_log_header(log_file: str, timestamp: str):
    """Write a formatted header to a test log file.

    Args:
        log_file: Path to the log file
        timestamp: Timestamp string to include in header (format: 'YYYY-MM-DD HH:MM:SS')
    """
    # Skip header writing in parallel worker processes to avoid duplicate headers
    # pytest-xdist sets PYTEST_XDIST_WORKER for worker processes
    if os.environ.get("PYTEST_XDIST_WORKER"):
        return

    log_filename = Path(log_file).name

    if "test_run" in log_filename:
        header_text = (
            f"\n{'='*80}\n"
            f"# TEST RUN STARTED: {timestamp}\n"
            f"# Test Execution Logging Active\n"
            f"# Test execution and framework logs are captured here\n"
            f"{'='*80}\n\n"
        )
    elif "consolidated" in log_filename:
        header_text = (
            f"\n{'='*80}\n"
            f"# TEST RUN STARTED: {timestamp}\n"
            f"# Component Logging Active\n"
            f"# Real component logs from application components are captured here\n"
            f"{'='*80}\n\n"
        )
    else:
        # Default header for other log files
        header_text = f"# Log rotated at {timestamp}\n"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(header_text)


class SessionLogRotationManager:
    """Manages session-based log rotation that rotates ALL logs together if any exceed size limits."""

    def __init__(
        self, max_size_mb=2
    ):  # 2MB for test logs (lower than production 5MB for more frequent rotation)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.log_files = []
        self.rotation_needed = False
        self.last_rotation_check = self._load_last_rotation_time()

    def _get_rotation_state_file(self):
        """Get the path to the file that stores last rotation time."""
        rotation_state_file = (
            Path(os.environ.get("LOG_BACKUP_DIR", "tests/logs/backups"))
            / ".last_rotation"
        )
        return rotation_state_file

    def _load_last_rotation_time(self):
        """Load the last rotation time from persistent storage."""
        rotation_state_file = self._get_rotation_state_file()
        try:
            if rotation_state_file.exists():
                with open(rotation_state_file, "r", encoding="utf-8") as f:
                    timestamp_str = f.read().strip()
                    if timestamp_str:
                        return parse_timestamp_full(timestamp_str)
        except (OSError, ValueError) as e:
            _get_test_logger().debug(f"Could not load last rotation time: {e}")
        return None

    def _save_last_rotation_time(self, timestamp):
        """Save the last rotation time to persistent storage."""
        rotation_state_file = self._get_rotation_state_file()
        try:
            rotation_state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(rotation_state_file, "w", encoding="utf-8") as f:
                f.write(format_timestamp(timestamp, TIMESTAMP_FULL))
        except OSError as e:
            _get_test_logger().debug(f"Could not save last rotation time: {e}")

    def register_log_file(self, file_path):
        """Register a log file for session-based rotation monitoring.

        Files are registered even if they don't exist yet - they'll be checked
        for rotation when they're created.
        """
        if file_path:
            # Convert to absolute path for consistency
            abs_path = os.path.abspath(file_path)
            if abs_path not in self.log_files:
                self.log_files.append(abs_path)

    def check_rotation_needed(self):
        """Check if any log file exceeds the size limit or if time-based rotation is needed.

        This method checks rotation conditions but does NOT update last_rotation_check.
        The timestamp is only updated after rotation actually completes in rotate_all_logs().
        """
        from datetime import timedelta

        now = now_datetime_full()

        # Check time-based rotation (daily rotation for test logs)
        if self.last_rotation_check is not None:
            # We have a previous rotation timestamp - check elapsed time
            time_since_last = now - self.last_rotation_check
            if time_since_last > timedelta(hours=24):
                self.rotation_needed = True
                _get_test_logger().info(
                    f"Time-based rotation needed (last rotation: {self.last_rotation_check}, elapsed: {time_since_last})"
                )
                return True
        else:
            # First time checking - use the oldest log entry timestamp to determine if rotation is needed
            # This handles the case where logs are old but we've never rotated before
            # File modification time is unreliable because it gets updated on every write
            for log_file in self.log_files:
                try:
                    if os.path.exists(log_file):
                        # Try to parse the header timestamp to find when logs actually started
                        oldest_timestamp = self._get_oldest_log_timestamp(log_file)
                        if oldest_timestamp:
                            time_since_oldest = now - oldest_timestamp
                            if time_since_oldest > timedelta(hours=24):
                                self.rotation_needed = True
                                _get_test_logger().info(
                                    f"Time-based rotation needed (log file {log_file} has entries from {oldest_timestamp}, {time_since_oldest} old, no previous rotation)"
                                )
                                return True
                except (OSError, FileNotFoundError) as e:
                    _get_test_logger().debug(
                        f"Could not check oldest log timestamp for {log_file}: {e}"
                    )
                    continue

        # Check size-based rotation
        for log_file in self.log_files:
            try:
                if os.path.exists(log_file):
                    file_size = os.path.getsize(log_file)
                    if file_size > self.max_size_bytes:
                        self.rotation_needed = True
                        size_mb = file_size / (1024 * 1024)
                        _get_test_logger().info(
                            f"Log file {log_file} exceeds limit ({size_mb:.2f}MB > {self.max_size_bytes / (1024 * 1024):.2f}MB), rotation needed"
                        )
                        return True
            except (OSError, FileNotFoundError) as e:
                _get_test_logger().debug(f"Could not check size for {log_file}: {e}")
                continue

        return False

    def _get_oldest_log_timestamp(self, log_file: str):
        """Extract the oldest timestamp from a log file by checking the header or first log entry.

        Returns the datetime of the oldest entry, or None if it can't be determined.
        """
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                # Read first few lines to find header or first log entry
                for i, line in enumerate(f):
                    if i > 20:  # Don't read too far
                        break

                    # Check for header timestamp: "# TEST RUN STARTED: YYYY-MM-DD HH:MM:SS"
                    if "TEST RUN STARTED:" in line:
                        try:
                            # Extract timestamp from header
                            match = re.search(
                                r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", line
                            )
                            if match:
                                timestamp_str = match.group(1)
                                parsed = parse_timestamp_full(timestamp_str)
                                if parsed is not None:
                                    return parsed
                        except (ValueError, AttributeError):
                            pass

                    # Check for log entry timestamp: "YYYY-MM-DD HH:MM:SS - ..."
                    if re.match(r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}", line):
                        try:
                            timestamp_str = line[
                                :19
                            ]  # First 19 chars are "YYYY-MM-DD HH:MM:SS"
                            parsed = parse_timestamp_full(timestamp_str)
                            if parsed is not None:
                                return parsed
                        except ValueError:
                            pass
        except (OSError, FileNotFoundError, UnicodeDecodeError):
            pass
        return None

    def _write_log_header(self, log_file: str, timestamp: str):
        """Write a formatted header to a log file during rotation.

        Args:
            log_file: Path to the log file
            timestamp: Timestamp string to include in header
        """
        log_filename = Path(log_file).name

        if "test_run" in log_filename:
            header_text = (
                f"{'='*80}\n"
                f"# TEST RUN STARTED: {timestamp}\n"
                f"# Test Execution Logging Active\n"
                f"# Test execution and framework logs are captured here\n"
                f"{'='*80}\n\n"
            )
        elif "consolidated" in log_filename:
            header_text = (
                f"{'='*80}\n"
                f"# TEST RUN STARTED: {timestamp}\n"
                f"# Component Logging Active\n"
                f"# Real component logs from application components are captured here\n"
                f"{'='*80}\n\n"
            )
        else:
            # Default header for other log files
            header_text = f"# Log rotated at {timestamp}\n"

        # Use 'w' mode for rotation (creates new file)
        # Add retry logic to handle file locking
        import time

        max_retries = 3
        retry_delay = 0.1
        test_logger = _get_test_logger()

        for attempt in range(max_retries):
            try:
                with open(log_file, "w", encoding="utf-8") as f:
                    f.write(header_text)
                break  # Success
            except (OSError, PermissionError) as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                # Last attempt failed - log warning but don't raise
                test_logger.warning(
                    f"Failed to write header to {log_file} after {max_retries} attempts: {e}"
                )

    def rotate_all_logs(self, rotation_context="session"):
        """Rotate all registered log files together to maintain continuity.

        Args:
            rotation_context: Context string for logging (e.g., "session start", "session end")
        """
        test_logger = _get_test_logger()

        # Check if rotation is needed first
        if not self.check_rotation_needed():
            # If no rotation needed, initialize last_rotation_check on first call
            # This prevents time-based rotation from triggering immediately on next check
            if self.last_rotation_check is None:
                self.last_rotation_check = now_datetime_full()
            return

        test_logger.info(f"Starting {rotation_context} log rotation for all log files")
        timestamp = now_timestamp_filename()
        timestamp_display = now_timestamp_full()

        # Ensure backups directory exists
        backup_dir = Path(os.environ.get("LOG_BACKUP_DIR", "tests/logs/backups"))
        backup_dir.mkdir(parents=True, exist_ok=True)

        rotated_files = []
        failed_files = []

        for log_file in self.log_files:
            try:
                if not os.path.exists(log_file):
                    test_logger.debug(f"Skipping {log_file} - file does not exist")
                    continue

                file_size = os.path.getsize(log_file)
                if file_size == 0:
                    test_logger.debug(f"Skipping {log_file} - file is empty")
                    continue

                # Create backup filename with timestamp
                log_filename = Path(log_file).name
                backup_filename = f"{log_filename}.{timestamp}.bak"
                backup_file = backup_dir / backup_filename

                # Handle Windows file locking by copying instead of moving
                # Add retry logic with timeout to prevent hanging
                import time

                max_retries = 5  # Increased retries
                retry_delay = 0.2  # Longer delay between retries
                rotation_success = False

                for attempt in range(max_retries):
                    try:
                        # Try to move first (faster and atomic)
                        shutil.move(log_file, backup_file)
                        # Verify backup was created and has content
                        if backup_file.exists():
                            backup_size = backup_file.stat().st_size
                            if backup_size > 0:
                                test_logger.info(
                                    f"Rotated {log_file} ({file_size} bytes) to {backup_file} ({backup_size} bytes)"
                                )
                                rotation_success = True
                                rotated_files.append(log_file)
                                break
                            else:
                                test_logger.warning(
                                    f"Move succeeded but backup file is empty: {backup_file}"
                                )
                        else:
                            test_logger.warning(
                                f"Move succeeded but backup file is missing: {backup_file}"
                            )
                    except (OSError, PermissionError) as move_error:
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        # If move fails after retries, try copy method
                        try:
                            test_logger.warning(
                                f"Move failed for {log_file} due to file locking, using copy method: {move_error}"
                            )
                            # Read entire file first to ensure we get all content
                            with open(log_file, "rb") as src:
                                with open(backup_file, "wb") as dst:
                                    shutil.copyfileobj(src, dst)
                            # Verify backup was created and has content
                            if backup_file.exists():
                                backup_size = backup_file.stat().st_size
                                if backup_size > 0:
                                    test_logger.info(
                                        f"Copied {log_file} ({file_size} bytes) to {backup_file} ({backup_size} bytes)"
                                    )
                                    rotation_success = True
                                    rotated_files.append(log_file)
                                    break
                                else:
                                    test_logger.warning(
                                        f"Copy succeeded but backup file is empty: {backup_file}"
                                    )
                            else:
                                test_logger.warning(
                                    f"Copy succeeded but backup file is missing: {backup_file}"
                                )
                        except (OSError, PermissionError) as copy_error:
                            test_logger.warning(
                                f"Copy also failed for {log_file}: {copy_error}"
                            )
                            failed_files.append((log_file, str(copy_error)))
                            continue

                if rotation_success:
                    # Truncate the original file and write formatted header
                    # Add retry for header writing too
                    for attempt in range(max_retries):
                        try:
                            self._write_log_header(log_file, timestamp_display)
                            if attempt > 0:
                                test_logger.info(f"Truncated {log_file} after copy")
                            break
                        except (OSError, PermissionError) as header_error:
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay)
                                continue
                            test_logger.warning(
                                f"Failed to write header to {log_file}: {header_error}"
                            )
                else:
                    failed_files.append((log_file, "Rotation failed after all retries"))

            except (OSError, FileNotFoundError) as e:
                test_logger.warning(f"Failed to rotate {log_file}: {e}")
                failed_files.append((log_file, str(e)))

        # Log summary
        if rotated_files:
            test_logger.info(
                f"Successfully rotated {len(rotated_files)} log file(s): {', '.join(Path(f).name for f in rotated_files)}"
            )
        if failed_files:
            test_logger.warning(
                f"Failed to rotate {len(failed_files)} log file(s): {', '.join(f'{Path(f).name} ({err})' for f, err in failed_files)}"
            )

        self.rotation_needed = False
        rotation_time = now_datetime_full()
        self.last_rotation_check = rotation_time
        self._save_last_rotation_time(rotation_time)
        test_logger.info(f"{rotation_context.capitalize()} log rotation completed")


class LogLifecycleManager:
    """Manages log file lifecycle including backup, archive, and cleanup operations."""

    def __init__(self, archive_days=30):
        self.archive_days = archive_days
        self.backup_dir = Path(os.environ.get("LOG_BACKUP_DIR", "tests/logs/backups"))
        self.archive_dir = Path(os.environ.get("LOG_ARCHIVE_DIR", "tests/logs/archive"))

        # Ensure directories exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def cleanup_old_archives(self):
        """Remove archive files older than the specified number of days."""
        test_logger = _get_test_logger()
        cutoff_date = now_datetime_full().timestamp() - (
            self.archive_days * 24 * 60 * 60
        )

        cleaned_count = 0
        for archive_file in self.archive_dir.glob("*"):
            try:
                if (
                    archive_file.is_file()
                    and archive_file.stat().st_mtime < cutoff_date
                ):
                    archive_file.unlink()
                    cleaned_count += 1
                    test_logger.debug(f"Removed old archive: {archive_file}")
            except (OSError, FileNotFoundError) as e:
                test_logger.warning(f"Failed to remove archive {archive_file}: {e}")

        if cleaned_count > 0:
            test_logger.info(
                f"Cleaned up {cleaned_count} old archive files (older than {self.archive_days} days)"
            )

        return cleaned_count

    def archive_old_backups(self):
        """Move old backup files to archive directory."""
        test_logger = _get_test_logger()
        cutoff_date = now_datetime_full().timestamp() - (7 * 24 * 60 * 60)  # 7 days

        archived_count = 0
        for backup_file in self.backup_dir.glob("*"):
            try:
                if backup_file.is_file() and backup_file.stat().st_mtime < cutoff_date:
                    # Keep archive naming stable: avoid repeatedly appending timestamps,
                    # and shorten oversized names for Windows path safety.
                    archive_name = backup_file.name
                    if len(archive_name) > 150:
                        digest = hashlib.sha1(
                            archive_name.encode("utf-8", errors="ignore")
                        ).hexdigest()[:10]
                        suffix = backup_file.suffix
                        stem_budget = max(32, 150 - len(suffix) - 11)
                        archive_name = f"{backup_file.stem[:stem_budget]}_{digest}{suffix}"
                    archive_path = self.archive_dir / archive_name
                    if archive_path.exists():
                        digest = hashlib.sha1(
                            str(backup_file).encode("utf-8", errors="ignore")
                        ).hexdigest()[:8]
                        suffix = backup_file.suffix
                        stem_budget = max(24, 140 - len(suffix) - 9)
                        archive_path = (
                            self.archive_dir
                            / f"{backup_file.stem[:stem_budget]}_{digest}{suffix}"
                        )

                    shutil.move(str(backup_file), str(archive_path))
                    archived_count += 1
                    test_logger.debug(
                        f"Archived backup: {backup_file} -> {archive_path}"
                    )
            except (OSError, FileNotFoundError) as e:
                test_logger.warning(f"Failed to archive backup {backup_file}: {e}")

        if archived_count > 0:
            test_logger.info(f"Archived {archived_count} old backup files")

        return archived_count

    def perform_lifecycle_maintenance(self):
        """Perform all lifecycle maintenance operations."""
        test_logger = _get_test_logger()
        # Reduce verbosity - only log if something actually happens
        archived_count = self.archive_old_backups()
        cleanup_count = self.cleanup_old_archives()
        if archived_count > 0 or cleanup_count > 0:
            test_logger.debug(
                f"Log lifecycle maintenance: archived {archived_count}, cleaned {cleanup_count}"
            )
