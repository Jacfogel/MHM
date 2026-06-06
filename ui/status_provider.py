import re
from importlib import import_module
from pathlib import Path

import psutil


_lazy_dependencies = import_module("ui.lazy_dependencies")
DataError = _lazy_dependencies.DataError
handle_errors = _lazy_dependencies.handle_errors
logger = _lazy_dependencies.get_component_logger("ui")
now_datetime_full = _lazy_dependencies.now_datetime_full
parse_timestamp_full = _lazy_dependencies.parse_timestamp_full
core_config = import_module("core.config")


def _load_attr(module_name: str, attr_name: str):
    """Load a project attribute through the UI lazy dependency boundary."""
    # ERROR_HANDLING_EXCLUDE: low-level lazy import helper; callers are decorated or fail fast.
    return _lazy_dependencies.load_attr(module_name, attr_name)


@handle_errors(
    "reading tail of channel log file for status",
    default_return=[],
)
def tail_file_lines(path: Path, max_lines: int) -> list[str]:
    """Return up to the last max_lines lines from a text file."""
    if not path.is_file():
        return []
    with open(path, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    if len(lines) <= max_lines:
        return lines
    return lines[-max_lines:]


@handle_errors(
    "merging rotated channel log files for status",
    default_return=[],
)
def merge_rotated_channel_log_lines(
    primary: Path,
    backup_dir: Path,
    *,
    max_lines_per_file: int = 2500,
) -> list[str]:
    """
    Merge recent lines from the primary channel log and TimedRotating backups.

    Rotated files use ``{primary.name}.{date_suffix}`` under ``backup_dir``.
    Order is oldest backup -> newest -> primary, so the combined sequence is
    roughly chronological.
    """
    merged: list[str] = []
    name = primary.name
    bdir = Path(backup_dir)
    if bdir.is_dir():
        rotated = sorted(
            bdir.glob(f"{name}.*"),
            key=lambda p: (p.stat().st_mtime, p.name),
        )
        for rot_path in rotated:
            merged.extend(tail_file_lines(rot_path, max_lines_per_file))
    merged.extend(tail_file_lines(primary, max_lines_per_file))
    return merged


class StatusProvider:
    """Collect service, channel, and tunnel status for the admin UI."""

    @handle_errors("initializing status provider", default_return=None)
    def __init__(self, service_manager):
        self.service_manager = service_manager

    @handle_errors("checking service status", default_return=(False, None))
    def check_service_status(self):
        """Return the current backend service process status."""
        return self.service_manager.is_service_running()

    # not_duplicate: channel_status_detection_variants
    @handle_errors("checking Discord channel status", default_return=False)
    def check_discord_status(self) -> bool:
        """Check if Discord channel is actually running and connected."""
        try:
            is_running, _service_pid = self.service_manager.is_service_running()
            if not is_running:
                return False

            discord_bot_token = _load_attr("core.config", "DISCORD_BOT_TOKEN")
            if not discord_bot_token:
                return False

            try:
                discord_log_file = Path(core_config.LOG_DISCORD_FILE)
                lines = merge_rotated_channel_log_lines(
                    discord_log_file,
                    Path(core_config.LOG_BACKUP_DIR),
                )
                if lines:
                    last_init_time = None
                    last_shutdown_time = None
                    last_activity_time = None

                    activity_indicators = [
                        "DISCORD_MESSAGE_RECEIVED",
                        "DISCORD_MESSAGE_PROCESS",
                        "Discord message handled successfully",
                        "Discord channel message sent",
                        "Discord healthy",
                    ]

                    for line in reversed(lines):
                        if (
                            "Discord bot initialized successfully" in line
                            or "Discord connection status changed to: connected" in line
                        ):
                            timestamp_match = re.search(
                                r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line
                            )
                            if timestamp_match and last_init_time is None:
                                try:
                                    last_init_time = parse_timestamp_full(
                                        timestamp_match.group(1)
                                    )
                                    if last_init_time is None:
                                        raise DataError(
                                            "Invalid Discord initialization timestamp"
                                        )
                                except DataError:
                                    pass

                        if "Discord bot shutdown completed" in line:
                            timestamp_match = re.search(
                                r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line
                            )
                            if timestamp_match and last_shutdown_time is None:
                                try:
                                    last_shutdown_time = parse_timestamp_full(
                                        timestamp_match.group(1)
                                    )
                                    if last_shutdown_time is None:
                                        raise DataError(
                                            "Invalid Discord shutdown timestamp"
                                        )
                                except DataError:
                                    pass

                        if any(indicator in line for indicator in activity_indicators):
                            timestamp_match = re.search(
                                r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line
                            )
                            if timestamp_match and last_activity_time is None:
                                try:
                                    last_activity_time = parse_timestamp_full(
                                        timestamp_match.group(1)
                                    )
                                    if last_activity_time is None:
                                        raise DataError(
                                            "Invalid Discord activity timestamp"
                                        )
                                except DataError:
                                    pass

                    if last_activity_time:
                        time_since_activity = (
                            now_datetime_full() - last_activity_time
                        ).total_seconds()
                        if time_since_activity < 300:
                            return True

                    if last_init_time:
                        time_since_init = (
                            now_datetime_full() - last_init_time
                        ).total_seconds()

                        if (
                            last_shutdown_time is None
                            or last_shutdown_time < last_init_time
                        ):
                            if time_since_init < 3600:
                                return True
                            return True

                        for line in lines:
                            if (
                                "Discord bot initialized successfully" in line
                                or "Discord connection status changed to: connected"
                                in line
                            ):
                                timestamp_match = re.search(
                                    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line
                                )
                                if timestamp_match:
                                    try:
                                        init_time = parse_timestamp_full(
                                            timestamp_match.group(1)
                                        )
                                        if init_time is None:
                                            raise DataError(
                                                "Invalid Discord restart timestamp"
                                            )
                                        if init_time > last_shutdown_time:
                                            time_since_restart = (
                                                now_datetime_full() - init_time
                                            ).total_seconds()
                                            if time_since_restart < 3600:
                                                return True
                                    except DataError:
                                        pass
                    elif last_activity_time:
                        time_since_activity = (
                            now_datetime_full() - last_activity_time
                        ).total_seconds()
                        if time_since_activity < 3600:
                            return True
            except Exception as e:
                logger.debug(f"Error checking Discord logs: {e}")
                return True

            return True
        except Exception as e:
            logger.debug(f"Error checking Discord status: {e}")
            return False

    # not_duplicate: channel_status_detection_variants
    @handle_errors("checking Email channel status", default_return=False)
    def check_email_status(self) -> bool:
        """Check if Email channel is actually initialized and running."""
        try:
            is_running, _service_pid = self.service_manager.is_service_running()
            if not is_running:
                return False

            email_smtp_server = _load_attr("core.config", "EMAIL_SMTP_SERVER")
            email_imap_server = _load_attr("core.config", "EMAIL_IMAP_SERVER")
            email_smtp_username = _load_attr("core.config", "EMAIL_SMTP_USERNAME")
            email_smtp_password = _load_attr("core.config", "EMAIL_SMTP_PASSWORD")

            if not all(
                [
                    email_smtp_server,
                    email_imap_server,
                    email_smtp_username,
                    email_smtp_password,
                ]
            ):
                return False

            try:
                email_log_file = Path(core_config.LOG_EMAIL_FILE)
                lines = merge_rotated_channel_log_lines(
                    email_log_file,
                    Path(core_config.LOG_BACKUP_DIR),
                )
                if lines:
                    last_init_time = None
                    last_shutdown_time = None
                    last_activity_time = None

                    activity_indicators = [
                        "Email sent to",
                        "Received ",
                        "new email(s)",
                        "Processing ",
                        " new emails",
                    ]

                    for line in reversed(lines):
                        if "EmailBot initialized successfully" in line:
                            timestamp_match = re.search(
                                r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line
                            )
                            if timestamp_match and last_init_time is None:
                                try:
                                    last_init_time = parse_timestamp_full(
                                        timestamp_match.group(1)
                                    )
                                    if last_init_time is None:
                                        raise DataError(
                                            "Invalid Email initialization timestamp"
                                        )
                                except DataError:
                                    pass

                        if "EmailBot stopped" in line:
                            timestamp_match = re.search(
                                r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line
                            )
                            if timestamp_match and last_shutdown_time is None:
                                try:
                                    last_shutdown_time = parse_timestamp_full(
                                        timestamp_match.group(1)
                                    )
                                    if last_shutdown_time is None:
                                        raise DataError(
                                            "Invalid Email shutdown timestamp"
                                        )
                                except DataError:
                                    pass

                        if any(indicator in line for indicator in activity_indicators):
                            timestamp_match = re.search(
                                r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line
                            )
                            if timestamp_match and last_activity_time is None:
                                try:
                                    last_activity_time = parse_timestamp_full(
                                        timestamp_match.group(1)
                                    )
                                    if last_activity_time is None:
                                        raise DataError(
                                            "Invalid Email activity timestamp"
                                        )
                                except DataError:
                                    pass

                    if last_activity_time:
                        time_since_activity = (
                            now_datetime_full() - last_activity_time
                        ).total_seconds()
                        if time_since_activity < 300:
                            return True

                    if last_init_time:
                        time_since_init = (
                            now_datetime_full() - last_init_time
                        ).total_seconds()
                        if (
                            last_shutdown_time is None
                            or last_shutdown_time < last_init_time
                        ):
                            if time_since_init < 3600:
                                return True
                            return True

                        for line in lines:
                            if "EmailBot initialized successfully" in line:
                                timestamp_match = re.search(
                                    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line
                                )
                                if timestamp_match:
                                    try:
                                        init_time = parse_timestamp_full(
                                            timestamp_match.group(1)
                                        )
                                        if init_time is None:
                                            raise DataError(
                                                "Invalid Email restart timestamp"
                                            )
                                        if init_time > last_shutdown_time:
                                            time_since_restart = (
                                                now_datetime_full() - init_time
                                            ).total_seconds()
                                            if time_since_restart < 3600:
                                                return True
                                    except DataError:
                                        pass
                    elif last_activity_time:
                        time_since_activity = (
                            now_datetime_full() - last_activity_time
                        ).total_seconds()
                        if time_since_activity < 3600:
                            return True
            except Exception as e:
                logger.debug(f"Error checking Email logs: {e}")
                return True

            return True
        except Exception as e:
            logger.debug(f"Error checking Email status: {e}")
            return False

    @handle_errors(
        "checking ngrok tunnel status", default_return={"running": False, "pid": None}
    )
    def check_ngrok_status(self) -> dict:
        """Check if ngrok tunnel is running and return PID."""
        try:
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if not proc.info["name"]:
                        continue

                    proc_name = proc.info["name"].lower()
                    if "ngrok" in proc_name and proc.is_running():
                        cmdline = proc.info.get("cmdline", [])
                        if cmdline and "http" in " ".join(cmdline).lower():
                            return {"running": True, "pid": proc.info["pid"]}
                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue

            return {"running": False, "pid": None}
        except Exception as e:
            logger.debug(f"Error checking ngrok status: {e}")
            return {"running": False, "pid": None}
