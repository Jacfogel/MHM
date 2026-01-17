# service_utilities.py
"""
Service utilities for MHM.
Contains functions for service management, network operations, and datetime handling.
"""

import os
import json
import time
import socket
import psutil
from datetime import datetime
from pathlib import Path
import pytz
from core.logger import get_component_logger

try:
    from core.file_auditor import record_created as _record_created
except Exception:
    _record_created = None
from core.config import SCHEDULER_INTERVAL
from core.error_handling import handle_errors

logger = get_component_logger("main")
service_logger = get_component_logger("main")

# Timestamp formatting conventions (project-wide)
# - READABLE: for logs/metadata fields (readable, sortable)
# - FILENAME: for filenames/IDs on Windows (no ":" or spaces)
READABLE_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
FILENAME_TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"

# Additional canonical formats used across scheduler + UI
DATE_ONLY_FORMAT = "%Y-%m-%d"
TIME_HM_FORMAT = "%H:%M"
READABLE_MINUTE_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"


# Throttler class
class Throttler:
    """
    A utility class for throttling operations based on time intervals.

    Prevents operations from running too frequently by tracking the last execution time.
    """

    @handle_errors("initializing throttler", default_return=None)
    def __init__(self, interval):
        """
        Initialize the throttler with a specified interval.

        Args:
            interval: Time interval in seconds between allowed operations
        """
        # Force float so comparisons are consistent even if an int is passed.
        self.interval = float(interval)

        # Use a monotonic clock for throttling. This avoids issues where the system clock
        # changes (NTP adjustment, manual change, DST, VM time drift).
        #
        # Note: This is intentionally NOT a datetime object anymore; it's internal-only state.
        self.last_run: float | None = None

    @handle_errors("checking if throttler should run", default_return=False)
    def should_run(self):
        """
        Check if enough time has passed since the last run to allow another execution.

        IMPORTANT:
        - Uses monotonic time (safe for measuring intervals).
        - Does NOT update last_run when returning False.
        """
        import time

        current_time = time.monotonic()

        if self.last_run is None:
            # Set first-run timestamp so we actually throttle subsequent calls
            self.last_run = current_time
            return True

        # Defensive: last_run is internal state and should always be a float,
        # but tests (and potentially older call sites) may still inject invalid values.
        # If last_run is invalid, fail open and reset state.
        if not isinstance(self.last_run, (int, float)):
            self.last_run = current_time
            return True

        time_since_last_run = current_time - float(self.last_run)

        # Small epsilon helps avoid edge flakiness when interval == timeout and the scheduler
        # wakes up *just* under the boundary (common on Windows/xdist).
        epsilon = 0.002  # 2ms is tiny, but enough to reduce boundary flake
        if time_since_last_run + epsilon >= self.interval:
            self.last_run = current_time
            return True

        return False


class InvalidTimeFormatError(Exception):
    """
    Exception raised when time format is invalid.

    Used for time parsing and validation operations.
    """

    pass


# Global throttler instance
throttler = Throttler(SCHEDULER_INTERVAL)


def now_readable_timestamp() -> str:
    """Readable timestamp for logs and metadata."""
    return datetime.now().strftime(READABLE_TIMESTAMP_FORMAT)


def now_filename_timestamp() -> str:
    """Filename-safe timestamp for filenames and identifiers."""
    return datetime.now().strftime(FILENAME_TIMESTAMP_FORMAT)


@handle_errors("getting flags directory", default_return="")
def get_flags_dir() -> Path:
    """Get the directory for service flag files."""
    if os.environ.get("MHM_TESTING") == "1":
        test_data_dir = os.getenv("TEST_DATA_DIR", str(Path("tests") / "data"))
        flags_dir = Path(test_data_dir) / "flags"
    else:
        flags_dir = Path(os.getenv("MHM_FLAGS_DIR", str(Path(__file__).parent.parent)))

    try:
        flags_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    return flags_dir


@handle_errors("creating reschedule request", default_return=False)
def create_reschedule_request(user_id: str, category: str) -> bool:
    """
    Create a reschedule request file that the service will pick up.

    Args:
        user_id: The user ID
        category: The category to reschedule

    Returns:
        bool: True if request was created successfully
    """
    # First check if service is running - if not, no need to reschedule
    # The service will pick up changes on next startup
    if not is_service_running():
        logger.debug(
            "Service not running - schedule changes will be picked up on next startup"
        )
        return False

    # Human-readable timestamp for JSON (preferred where humans might read it)
    requested_at_readable = now_readable_timestamp()

    # ISO 8601 should come from a datetime object (not from strings).
    # Optional, but useful if you later sort/process these programmatically.
    requested_at_iso = datetime.now().isoformat()

    # Create request data
    request_data = {
        "user_id": user_id,
        "category": category,
        "requested_at_readable": requested_at_readable,
        "requested_at_iso": requested_at_iso,
        "source": "ui_schedule_editor",
    }

    # Create unique filename:
    # - Human-readable base (Windows-safe)
    # - Millisecond suffix for uniqueness (not a "policy timestamp", just an ID component)
    ms_suffix = int(time.time() * 1000) % 1000
    filename_timestamp = f"{now_filename_timestamp()}_{ms_suffix:03d}"
    filename = f"reschedule_request_{user_id}_{category}_{filename_timestamp}.flag"

    base_dir = get_flags_dir()
    request_file = Path(base_dir) / filename

    # Write the request file
    with open(str(request_file), "w", encoding="utf-8") as f:
        json.dump(request_data, f, indent=2)

    logger.info(f"Created reschedule request: {filename}")
    try:
        if _record_created:
            _record_created(
                request_file,
                reason="create_reschedule_request",
                extra={
                    "user_id": user_id,
                    "category": category,
                    "source": request_data["source"],
                },
            )
    except Exception:
        pass

    return True


@handle_errors("checking if service is running", default_return=False)
def is_service_running():
    """Check if the MHM service is currently running"""
    # Look for python processes running service.py
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if not proc.info["name"] or "python" not in proc.info["name"].lower():
                continue

            cmdline = proc.info.get("cmdline", [])
            if cmdline and any("service.py" in arg for arg in cmdline):
                if proc.is_running():
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return False


@handle_errors("checking service process details", default_return=[])
def get_service_processes():
    """Get detailed information about all MHM service processes"""
    service_processes = []
    seen_processes = set()  # Track processes to avoid duplicates

    for proc in psutil.process_iter(
        ["pid", "name", "cmdline", "create_time", "environ"]
    ):
        try:
            if not proc.info["name"] or "python" not in proc.info["name"].lower():
                continue

            cmdline = proc.info.get("cmdline", [])
            if (
                cmdline
                and any("service.py" in arg for arg in cmdline)
                and not any("run_headless_service.py" in arg for arg in cmdline)
            ):
                if proc.is_running():
                    # Create a unique identifier for this process to avoid duplicates
                    process_key = f"{proc.info['pid']}_{proc.info['create_time']}"
                    if process_key in seen_processes:
                        continue
                    seen_processes.add(process_key)

                    # Determine if this is a UI-managed or headless service
                    # UI-managed: has 'ui' in the path (launched by UI)
                    # Headless: runs core/service.py directly without 'ui' in path
                    full_cmdline = " ".join(cmdline)
                    is_ui_managed = (
                        "ui" in full_cmdline and "service.py" in full_cmdline
                    )
                    is_headless = (
                        "core/service.py" in full_cmdline
                        or "core\\service.py" in full_cmdline
                        or full_cmdline.endswith("core/service.py")
                        or full_cmdline.endswith("core\\service.py")
                    ) and not is_ui_managed

                    # Check for environment markers to better identify service type
                    try:
                        environ = proc.info.get("environ", {})
                        if environ and "MHM_HEADLESS_SERVICE" in environ:
                            is_headless = True
                            is_ui_managed = False
                    except (psutil.AccessDenied, KeyError):
                        pass  # Can't access environment, use cmdline detection

                    service_processes.append(
                        {
                            "pid": proc.info["pid"],
                            "cmdline": cmdline,
                            "create_time": proc.info["create_time"],
                            "is_ui_managed": is_ui_managed,
                            "is_headless": is_headless,
                            "process_type": (
                                "ui_managed"
                                if is_ui_managed
                                else "headless" if is_headless else "unknown"
                            ),
                        }
                    )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return service_processes


@handle_errors("checking if headless service is running", default_return=False)
def is_headless_service_running():
    """Check if a headless MHM service is currently running"""
    processes = get_service_processes()
    return any(proc["is_headless"] for proc in processes)


@handle_errors("checking if UI service is running", default_return=False)
def is_ui_service_running():
    """Check if a UI-managed MHM service is currently running"""
    processes = get_service_processes()
    return any(proc["is_ui_managed"] for proc in processes)


@handle_errors("waiting for network", default_return=False)
def wait_for_network(timeout=60):
    """Wait for the network to be available, retrying every 5 seconds up to a timeout."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        connection = None
        try:
            # Attempt to connect to a common DNS server (Google DNS as an example)
            connection = socket.create_connection(("8.8.8.8", 53))
            logger.debug("Network is available.")
            return True
        except OSError:
            logger.info("Network not available yet, retrying...")
            time.sleep(5)  # Wait for 5 seconds before retrying
        finally:
            if connection is not None:
                try:
                    connection.close()
                except OSError:
                    logger.debug("Error closing network probe socket", exc_info=True)
    logger.error("Network not available after waiting.")
    return False


@handle_errors("loading and localizing datetime")
def load_and_localize_datetime(datetime_str, timezone_str="America/Regina"):
    """
    Load and localize a datetime string to a specific timezone.

    Args:
        datetime_str: Datetime string in format "YYYY-MM-DD HH:MM"
        timezone_str: Timezone string (default: 'America/Regina')

    Returns:
        datetime: Timezone-aware datetime object

    Raises:
        InvalidTimeFormatError: If datetime_str format is invalid
    """
    try:
        tz = pytz.timezone(timezone_str)
        naive_datetime = datetime.strptime(
            datetime_str, READABLE_MINUTE_TIMESTAMP_FORMAT
        )
        aware_datetime = tz.localize(naive_datetime)
        logger.debug(
            f"Localized datetime '{datetime_str}' to timezone '{timezone_str}': '{aware_datetime}'"
        )
        return aware_datetime
    except ValueError as e:
        raise InvalidTimeFormatError(f"Invalid datetime format '{datetime_str}': {e}")
    except pytz.exceptions.UnknownTimeZoneError as e:
        raise InvalidTimeFormatError(f"Unknown timezone '{timezone_str}': {e}")
