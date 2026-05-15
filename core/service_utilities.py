# service_utilities.py
"""
Service utilities for MHM.
Contains service process inspection, service flag path helpers, and throttling.

Request flag processing lives in ``core.service_requests``. Scheduler timestamp
parsing/localization lives in ``core.time_utilities``.
"""

import os
import psutil
from pathlib import Path
from core.logger import get_component_logger

from core.config import SCHEDULER_INTERVAL
from core.error_handling import handle_errors
import contextlib

logger = get_component_logger("main")
service_logger = get_component_logger("main")


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


# Global throttler instance
throttler = Throttler(SCHEDULER_INTERVAL)


@handle_errors("getting flags directory", default_return="")
def get_flags_dir() -> Path:
    """Get the directory for service flag files."""
    if os.environ.get("MHM_TESTING") == "1":
        test_data_dir = os.getenv("TEST_DATA_DIR", str(Path("tests") / "data"))
        flags_dir = Path(test_data_dir) / "flags"
    else:
        flags_dir = Path(os.getenv("MHM_FLAGS_DIR", str(Path(__file__).parent.parent)))

    with contextlib.suppress(Exception):
        flags_dir.mkdir(parents=True, exist_ok=True)

    return flags_dir


# not_duplicate: service_status_detection_variants
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
            ) and proc.is_running():
                # Create a unique identifier for this process to avoid duplicates
                process_key = f"{proc.info['pid']}_{proc.info['create_time']}"
                if process_key in seen_processes:
                    continue
                seen_processes.add(process_key)

                # Classify UI-managed vs headless. Prefer explicit env markers (reliable);
                # cmdline-only rules are fallbacks when environ is unavailable.
                full_cmdline = " ".join(cmdline) if cmdline else ""
                is_ui_managed = False
                is_headless = False

                environ: dict | None = None
                try:
                    environ = proc.info.get("environ")
                except (psutil.AccessDenied, KeyError):
                    environ = None
                if not isinstance(environ, dict):
                    environ = {}

                if environ.get("MHM_HEADLESS_SERVICE") == "1":
                    is_headless = True
                elif environ.get("MHM_UI_MANAGED_SERVICE") == "1":
                    is_ui_managed = True
                else:
                    # Legacy / no env access: avoid treating arbitrary path segments as "UI"
                    # (substring "ui" matches folder names like "rapidui"). Prefer marker from UI launcher.
                    is_ui_managed = (
                        "ui/service.py" in full_cmdline
                        or "ui\\service.py" in full_cmdline
                    )
                    norm = full_cmdline.replace("/", "\\")
                    looks_like_core_service = (
                        "core/service.py" in full_cmdline
                        or "core\\service.py" in full_cmdline
                        or norm.rstrip().endswith("core\\service.py")
                    )
                    is_headless = looks_like_core_service and not is_ui_managed

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
    return _is_service_process_type_running("is_headless")


@handle_errors("checking if UI service is running", default_return=False)
def is_ui_service_running():
    """Check if a UI-managed MHM service is currently running"""
    return _is_service_process_type_running("is_ui_managed")


@handle_errors("checking service process type", default_return=False)
def _is_service_process_type_running(process_flag: str) -> bool:
    """Return True when any known service process has the requested flag."""
    processes = get_service_processes()
    return any(bool(proc.get(process_flag)) for proc in processes)
