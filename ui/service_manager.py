import os
import subprocess
import time
from importlib import import_module
from pathlib import Path

import psutil
from PySide6.QtWidgets import QMessageBox


_lazy_dependencies = import_module("ui.lazy_dependencies")
handle_errors = _lazy_dependencies.handle_errors
logger = _lazy_dependencies.get_component_logger("ui")
validate_all_configuration = _lazy_dependencies.validate_all_configuration
resolve_python_interpreter = _lazy_dependencies.resolve_python_interpreter
prepare_launch_environment = _lazy_dependencies.prepare_launch_environment
get_flags_dir = _lazy_dependencies.get_flags_dir


class ServiceManager:
    """Manages the MHM backend service process."""

    @handle_errors("initializing service manager", default_return=None)
    def __init__(self):
        """Initialize the object."""
        self.service_process = None

    @handle_errors("validating configuration before start", default_return=False)
    def validate_configuration_before_start(self):
        """Validate configuration before attempting to start the service."""
        result = validate_all_configuration()

        if not result["valid"]:
            error_message = "Configuration validation failed:\n\n"
            for error in result["errors"]:
                error_message += f"- {error}\n"

            if result["warnings"]:
                error_message += "\nWarnings:\n"
                for warning in result["warnings"]:
                    error_message += f"- {warning}\n"

            QMessageBox.critical(None, "Configuration Error", error_message)
            return False

        critical_warnings = []
        for warning in result["warnings"]:
            if any(
                skip_phrase in warning.lower()
                for skip_phrase in [
                    "using default",
                    "auto_create_user_dirs is enabled",
                    "not set (using default)",
                ]
            ):
                logger.info(f"Configuration note: {warning}")
                continue
            critical_warnings.append(warning)

        if critical_warnings:
            warning_message = "Configuration warnings:\n\n"
            for warning in critical_warnings:
                warning_message += f"- {warning}\n"
            warning_message += (
                "\nThe service will start, but you may want to address these warnings."
            )
            QMessageBox.warning(None, "Configuration Warnings", warning_message)

        if not result["available_channels"]:
            QMessageBox.warning(
                None,
                "No Communication Channels",
                "No communication channels are configured. The service will start but won't be able to send messages.",
            )

        return True

    # not_duplicate: service_status_detection_variants
    @handle_errors("checking service status", default_return=(False, None))
    def is_service_running(self):
        """
        Check if the MHM service is running with validation.

        Returns:
            tuple: (is_running, process_info)
        """
        service_pids = []
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            if not proc.info["name"] or "python" not in proc.info["name"].lower():
                continue

            cmdline = proc.info.get("cmdline", [])
            if (
                cmdline
                and len(cmdline) >= 2
                and cmdline[-1].endswith("service.py")
                and "service.py" in cmdline[-1]
            ):
                if proc.is_running():
                    service_pids.append(proc.info["pid"])

        if service_pids:
            return True, service_pids[0]
        return False, None

    @handle_errors("starting service", default_return=False)
    def start_service(self):
        """
        Start the MHM backend service with validation.

        Returns:
            bool: True if successful, False if failed
        """
        if not self.validate_configuration_before_start():
            return False

        is_running, pid = self.is_service_running()
        if is_running:
            logger.debug(f"Service already running with PID {pid}")
            QMessageBox.information(
                None, "Service Status", f"MHM Service is already running (PID: {pid})"
            )
            return True

        service_path = Path(__file__).parent.parent / "core" / "service.py"

        logger.debug(f"Service path: {service_path}")

        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        python_executable = resolve_python_interpreter(script_dir)

        logger.debug(f"Using Python: {python_executable}")

        env = prepare_launch_environment(script_dir)
        env["MHM_UI_MANAGED_SERVICE"] = "1"
        env["MHM_SERVICE_TYPE"] = "ui"

        if os.name == "nt":
            self.service_process = subprocess.Popen(
                [python_executable, service_path],
                env=env,
                cwd=script_dir,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            self.service_process = subprocess.Popen(
                [python_executable, service_path],
                env=env,
                cwd=script_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        logger.debug("Service process started, waiting for initialization...")
        time.sleep(2)

        is_running, pid = self.is_service_running()
        if is_running:
            logger.info(f"Service started with PID {pid}")
            QMessageBox.information(
                None, "Service Status", f"MHM Service started successfully (PID: {pid})"
            )
            return True

        logger.error("Failed to start service")
        QMessageBox.critical(None, "Service Error", "Failed to start MHM Service")
        return False

    @handle_errors("stopping service", default_return=False)
    def stop_service(self):
        """
        Stop the MHM backend service with validation.

        Returns:
            bool: True if successful, False if failed
        """
        is_running, pid = self.is_service_running()
        if not is_running:
            logger.info("Stop service requested but service is not running")
            QMessageBox.information(
                None, "Service Status", "MHM Service is not running"
            )
            return True

        logger.info(f"Stop service requested for PID: {pid}")

        shutdown_file = get_flags_dir() / "shutdown_request.flag"
        try:
            with open(shutdown_file, "w") as f:
                f.write(f"SHUTDOWN_REQUESTED_BY_UI_{time.time()}")
            logger.info(f"Created shutdown request file: {shutdown_file}")
        except Exception as e:
            logger.warning(f"Could not create shutdown file: {e}")

        logger.info("Waiting for graceful shutdown...")
        max_wait_time = 20
        wait_interval = 0.5
        waited = 0

        while waited < max_wait_time:
            is_running, current_pid = self.is_service_running()
            if not is_running:
                logger.info("Service stopped gracefully")
                QMessageBox.information(
                    None, "Service Status", "MHM Service stopped successfully"
                )
                return True
            time.sleep(wait_interval)
            waited += wait_interval
            if int(waited) % 5 == 0:
                logger.debug(
                    f"Still waiting for graceful shutdown... ({int(waited)}s elapsed)"
                )

        logger.warning("Graceful shutdown timeout - forcing termination")

        found_processes = []
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if not proc.info["name"] or "python" not in proc.info["name"].lower():
                    continue
                cmdline = proc.info.get("cmdline", [])
                if (
                    cmdline
                    and len(cmdline) >= 2
                    and cmdline[-1].endswith("service.py")
                    and "service.py" in cmdline[-1]
                ) and proc.is_running():
                    found_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        if not found_processes:
            logger.info("Service is not running - stop operation successful")
            QMessageBox.information(
                None, "Service Status", "Service is already stopped"
            )
            return True

        if len(found_processes) > 1:
            logger.info(
                f"Found {len(found_processes)} service processes, cleaning up all instances"
            )
        else:
            logger.info(f"Found {len(found_processes)} service process, terminating")

        for proc in found_processes:
            proc_pid = proc.info["pid"]
            try:
                proc.terminate()
                logger.debug(f"Terminated process {proc_pid}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                logger.debug(f"Process {proc_pid} already terminated or access denied")
                continue

        time.sleep(2)

        for proc in found_processes:
            try:
                if proc.is_running():
                    proc.kill()
                    logger.debug(f"Force killed process {proc.info['pid']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        time.sleep(0.5)
        is_running, current_pid = self.is_service_running()
        if not is_running:
            logger.info("Service stopped successfully (force termination)")
            QMessageBox.information(
                None, "Service Status", "MHM Service stopped successfully"
            )
            return True

        logger.warning(
            f"Service still running with PID {current_pid} after termination attempts"
        )
        QMessageBox.warning(
            None,
            "Service Status",
            f"Service may still be running (PID: {current_pid})",
        )
        return False

    @handle_errors("restarting service", default_return=False)
    def restart_service(self):
        """
        Restart the MHM backend service with validation.

        Returns:
            bool: True if successful, False if failed
        """
        logger.info("Restart service requested")

        if not self.stop_service():
            logger.error("Failed to stop service during restart")
            return False

        time.sleep(1)

        if not self.start_service():
            logger.error("Failed to start service during restart")
            return False

        logger.info("Service restart completed successfully")
        return True
