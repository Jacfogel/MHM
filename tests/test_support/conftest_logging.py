"""
Pytest plugin: session log rotation, consolidated test logging, and logging isolation.

Fixtures and managers here use implementation from tests.test_support.conftest_logging_impl.
Root conftest remains the source of project_root, test_logger, and test_log_file.
"""

import logging
import os
import sys
import time
from pathlib import Path

import pytest

from tests.test_support.conftest_logging_impl import (
    LogLifecycleManager,
    SessionLogRotationManager,
    _write_test_log_header,
)
from tests.test_support.conftest_cleanup_impl import _cleanup_individual_log_files

# Import from root conftest (loaded first)
from tests.conftest import project_root, test_logger, test_log_file

# PytestContextLogFormatter for worker log handler (same fallback as root conftest)
try:
    from core.logger import PytestContextLogFormatter as PytestContextLogFormatter
except (ImportError, ModuleNotFoundError):
    class _FallbackPytestContextLogFormatter(logging.Formatter):
        """Minimal formatter when core.logger is not available."""

        def __init__(self, fmt=None, datefmt=None):
            super().__init__(fmt=fmt, datefmt=datefmt)

    PytestContextLogFormatter = _FallbackPytestContextLogFormatter

# Global session rotation and lifecycle managers (used by fixtures and by root's _consolidate_worker_logs)
session_rotation_manager = SessionLogRotationManager()
log_lifecycle_manager = LogLifecycleManager()

if test_log_file and test_log_file.exists():
    session_rotation_manager.register_log_file(str(test_log_file))


@pytest.fixture(scope="session", autouse=True)
def setup_consolidated_test_logging():
    """Set up consolidated test logging - all component logs go to a single file.

    This replaces the complex multi-file logging system with a single consolidated log file
    that contains all component logs, making it much easier to manage and debug.

    In parallel execution mode (pytest-xdist), uses per-worker log files to avoid
    file locking issues and interleaved log entries.
    """
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    is_parallel = worker_id is not None

    if is_parallel:
        consolidated_log_file = (
            Path(project_root) / "tests" / "logs" / f"test_consolidated_{worker_id}.log"
        )
        test_run_log_file = (
            Path(project_root) / "tests" / "logs" / f"test_run_{worker_id}.log"
        )
    else:
        consolidated_log_file = (
            Path(project_root) / "tests" / "logs" / "test_consolidated.log"
        )
        test_run_log_file = Path(project_root) / "tests" / "logs" / "test_run.log"

    consolidated_log_file.parent.mkdir(exist_ok=True)

    rotation_happened = False

    if not is_parallel:
        session_rotation_manager.register_log_file(str(consolidated_log_file))
        session_rotation_manager.register_log_file(str(test_run_log_file))
        rotation_needed = session_rotation_manager.check_rotation_needed()
    else:
        rotation_needed = False

    if rotation_needed and not is_parallel:
        files_safe_to_rotate = True
        for log_file in session_rotation_manager.log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r+b") as f:
                        f.seek(0, 2)
                        f.flush()
                except (OSError, PermissionError) as e:
                    test_logger.warning(
                        f"Cannot rotate {log_file} - file is locked (likely still being written to): {e}"
                    )
                    files_safe_to_rotate = False
                    break

        if files_safe_to_rotate:
            loggers_to_check = [
                test_logger,
                logging.getLogger("mhm"),
                logging.getLogger("mhm.error_handler"),
                logging.getLogger("mhm_tests"),
                logging.getLogger("mhm_tests.run_tests"),
                logging.root,
            ]
            for logger_name in logging.Logger.manager.loggerDict:
                loggers_to_check.append(logging.getLogger(logger_name))

            handlers_closed = 0
            for logger in loggers_to_check:
                for handler in list(logger.handlers):
                    if isinstance(handler, logging.FileHandler):
                        try:
                            handler.flush()
                            handler.close()
                            logger.removeHandler(handler)
                            handlers_closed += 1
                        except Exception:
                            pass

            if handlers_closed > 0:
                test_logger.debug(
                    f"Closed {handlers_closed} file handlers before rotation"
                )

            time.sleep(0.2)

            import threading

            rotation_complete = threading.Event()
            rotation_error: list[Exception | None] = [None]
            rotation_success = [False]

            def do_rotation():
                try:
                    session_rotation_manager.rotate_all_logs(
                        rotation_context="session start"
                    )
                    rotation_success[0] = True
                    test_logger.info(
                        "Performed automatic log rotation at session start"
                    )
                except Exception as e:
                    rotation_error[0] = e
                    test_logger.warning(f"Log rotation failed: {e}")
                finally:
                    rotation_complete.set()

            rotation_thread = threading.Thread(target=do_rotation, daemon=True)
            rotation_thread.start()

            if rotation_complete.wait(timeout=5.0):
                if rotation_error[0]:
                    test_logger.warning(
                        f"Log rotation completed with errors: {rotation_error[0]}"
                    )
                elif rotation_success[0]:
                    rotation_happened = True
            else:
                test_logger.warning(
                    "Log rotation timed out after 5 seconds - continuing without rotation (logs will rotate on next run)"
                )
        else:
            test_logger.info(
                "Skipping log rotation - files are locked (likely from previous session still cleaning up)"
            )

    if not test_run_log_file.exists():
        test_run_log_file.touch()

    from core.time_utilities import now_timestamp_full

    timestamp = now_timestamp_full()

    if not rotation_happened:
        write_header_run = (
            not test_run_log_file.exists() or test_run_log_file.stat().st_size == 0
        )
        write_header_consolidated = (
            not consolidated_log_file.exists()
            or consolidated_log_file.stat().st_size == 0
        )
        if write_header_run:
            _write_test_log_header(str(test_run_log_file), timestamp)
        if write_header_consolidated:
            _write_test_log_header(str(consolidated_log_file), timestamp)

    if is_parallel:
        worker_consolidated = str(consolidated_log_file)
        os.environ["LOG_MAIN_FILE"] = worker_consolidated
        os.environ["LOG_ERRORS_FILE"] = worker_consolidated
        os.environ["LOG_DISCORD_FILE"] = worker_consolidated
        os.environ["LOG_AI_FILE"] = worker_consolidated
        os.environ["LOG_USER_ACTIVITY_FILE"] = worker_consolidated
        os.environ["LOG_COMMUNICATION_MANAGER_FILE"] = worker_consolidated
        os.environ["LOG_EMAIL_FILE"] = worker_consolidated
        os.environ["LOG_UI_FILE"] = worker_consolidated
        os.environ["LOG_FILE_OPS_FILE"] = worker_consolidated
        os.environ["LOG_SCHEDULER_FILE"] = worker_consolidated

        if test_logger:
            if test_logger.level > logging.INFO:
                test_logger.setLevel(logging.INFO)
            for handler in list(test_logger.handlers):
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    test_logger.removeHandler(handler)
            worker_test_run_handler = logging.FileHandler(
                test_run_log_file, encoding="utf-8", mode="a"
            )
            worker_test_run_handler.setLevel(logging.INFO)
            current_module = sys.modules[__name__]
            formatter = current_module.PytestContextLogFormatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            worker_test_run_handler.setFormatter(formatter)
            test_logger.addHandler(worker_test_run_handler)
    else:
        consolidated_path = str(consolidated_log_file)
        os.environ["LOG_MAIN_FILE"] = consolidated_path
        os.environ["LOG_ERRORS_FILE"] = consolidated_path
        os.environ["LOG_DISCORD_FILE"] = consolidated_path
        os.environ["LOG_AI_FILE"] = consolidated_path
        os.environ["LOG_USER_ACTIVITY_FILE"] = consolidated_path
        os.environ["LOG_COMMUNICATION_MANAGER_FILE"] = consolidated_path
        os.environ["LOG_EMAIL_FILE"] = consolidated_path
        os.environ["LOG_UI_FILE"] = consolidated_path
        os.environ["LOG_FILE_OPS_FILE"] = consolidated_path
        os.environ["LOG_SCHEDULER_FILE"] = consolidated_path

    component_handler = logging.FileHandler(
        str(consolidated_log_file), mode="a", encoding="utf-8"
    )
    verbose_logs = os.getenv("TEST_VERBOSE_LOGS", "0")
    if verbose_logs == "2":
        component_handler.setLevel(logging.DEBUG)
    else:
        component_handler.setLevel(logging.WARNING)
    component_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    component_handler.setFormatter(component_formatter)

    test_handler = logging.FileHandler(
        str(test_run_log_file), mode="a", encoding="utf-8"
    )
    try:
        from core.logger import PytestContextLogFormatter

        test_formatter = PytestContextLogFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    except (ImportError, ModuleNotFoundError):
        test_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    test_handler.setFormatter(test_formatter)

    root_logger = logging.getLogger()
    if not isinstance(root_logger.level, int) or root_logger.level == logging.NOTSET:
        root_logger.setLevel(logging.WARNING)

    for logger_name in list(logging.Logger.manager.loggerDict.keys()):
        try:
            logger_obj = logging.getLogger(logger_name)
            if isinstance(logger_obj, logging.Logger):
                if logger_obj.level == logging.NOTSET:
                    parent = logger_obj.parent
                    if parent and parent.level == logging.NOTSET:
                        logger_obj.setLevel(logging.WARNING)
                elif logger_obj.level is None:
                    logger_obj.setLevel(logging.WARNING)
        except Exception:
            continue

    try:
        from core.logger import _component_loggers

        _component_loggers.clear()
    except (ImportError, AttributeError):
        pass

    try:
        from core.scheduler import SchedulerManager
        from core.service import MHMService
        from communication.core.channel_orchestrator import CommunicationManager
        from ai.chatbot import AIChatBotSingleton
        _ = (
            SchedulerManager,
            MHMService,
            CommunicationManager,
            AIChatBotSingleton,
        )
    except ImportError:
        pass

    for logger_name in list(logging.Logger.manager.loggerDict.keys()):
        try:
            if logger_name.startswith("_pytest") or logger_name == "pytest":
                continue
            logger_obj = logging.getLogger(logger_name)
            if not isinstance(logger_obj, logging.Logger):
                continue
            for h in logger_obj.handlers[:]:
                try:
                    if isinstance(h, logging.FileHandler):
                        h.close()
                except Exception:
                    pass
                logger_obj.removeHandler(h)

            if (
                not isinstance(logging.DEBUG, int)
                or not isinstance(logging.INFO, int)
                or not isinstance(logging.WARNING, int)
            ):
                continue

            if logger_name.startswith("mhm."):
                verbose_logs = os.getenv("TEST_VERBOSE_LOGS", "0")
                if verbose_logs == "2":
                    level = logging.DEBUG
                else:
                    level = logging.WARNING
            else:
                verbose_logs = os.getenv("TEST_VERBOSE_LOGS", "0")
                if verbose_logs == "2":
                    level = logging.DEBUG
                elif verbose_logs == "1":
                    level = logging.INFO
                else:
                    level = logging.WARNING

            if level is None or not isinstance(level, int):
                level = logging.WARNING

            try:
                logger_obj.setLevel(level)
            except (TypeError, AttributeError) as e:
                test_logger.debug(
                    f"Skipping logger {logger_name} - cannot set level: {e}"
                )
                continue

            if logger_name.startswith("mhm."):
                logger_obj.addHandler(component_handler)
                logger_obj.propagate = False
            else:
                logger_obj.addHandler(test_handler)
                logger_obj.propagate = True
                if logger_name == "mhm_tests":
                    verbose_logs = os.getenv("TEST_VERBOSE_LOGS", "0")
                    if verbose_logs == "2":
                        test_level = logging.DEBUG
                    elif verbose_logs == "1":
                        test_level = logging.INFO
                    else:
                        test_level = logging.WARNING
                    logger_obj.setLevel(test_level)
                    for handler in logger_obj.handlers:
                        if isinstance(handler, logging.FileHandler):
                            handler.setLevel(test_level)

        except Exception:
            continue

    root_logger = logging.getLogger()
    if not isinstance(root_logger.level, int) or root_logger.level == logging.NOTSET:
        root_logger.setLevel(logging.WARNING)

    for handler in root_logger.handlers[:]:
        try:
            if isinstance(handler, logging.FileHandler):
                handler.close()
        except Exception:
            pass
        root_logger.removeHandler(handler)
    root_logger.addHandler(test_handler)
    root_logger.propagate = False

    _cleanup_individual_log_files(project_root)


@pytest.fixture(scope="session", autouse=True)
def log_lifecycle_maintenance():
    """Perform log lifecycle maintenance at session start."""
    log_lifecycle_manager.perform_lifecycle_maintenance()
    yield


@pytest.fixture(scope="session", autouse=True)
def session_log_rotation_check():
    """Perform final log cleanup at session end.

    NOTE: Log rotation only happens at session START in setup_consolidated_test_logging.
    """
    yield


@pytest.fixture(scope="session", autouse=True)
def isolate_logging():
    """Ensure complete logging isolation during tests to prevent test logs from appearing in main app.log."""
    root_logger = logging.getLogger()
    original_root_handlers = root_logger.handlers[:]
    main_logger = logging.getLogger("mhm")
    original_main_handlers = main_logger.handlers[:]

    for handler in root_logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
        root_logger.removeHandler(handler)
    for handler in main_logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
        main_logger.removeHandler(handler)

    root_logger.propagate = False
    main_logger.propagate = False
    test_logger.debug(
        "Logging isolation activated - test logs will not appear in main app.log"
    )

    yield

    for handler in original_root_handlers:
        root_logger.addHandler(handler)
    for handler in original_main_handlers:
        main_logger.addHandler(handler)
    root_logger.propagate = True
    main_logger.propagate = True
    test_logger.info("Logging isolation deactivated - main app logging restored")
