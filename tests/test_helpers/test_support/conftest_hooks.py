"""
Pytest hooks and session/cleanup fixtures for MHM tests.

Provides: collection modifiers, configure/session/runtest hooks, worker log
consolidation, and cleanup fixtures (communication manager, conversation state,
singletons, periodic memory cleanup). Imports project_root, tests_data_dir,
test_logger, test_log_file, and _cleanup_test_user_artifacts from tests.conftest.
"""

import os
import re
from pathlib import Path
from datetime import datetime

import pytest

from core.time_utilities import (
    now_timestamp_full,
    format_timestamp_milliseconds,
)
import contextlib

# Strip ANSI escape sequences from pytest longrepr before writing to log files.
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

# Counter for periodic_memory_cleanup (avoids attaching to fixture function object)
_periodic_cleanup_test_count = 0


# Import from root conftest (loaded first); _cleanup_test_user_artifacts from user_data plugin
def _get_conftest_attrs():
    from tests import conftest as root
    from tests.test_helpers.test_support import conftest_user_data as ud

    return (
        root.project_root,
        root.tests_data_dir,
        root.test_logger,
        root.test_log_file,
        ud._cleanup_test_user_artifacts,
    )


def pytest_collection_modifyitems(config, items):
    """Exclude AI test files that are run via run_ai_functionality_tests.py from pytest collection and add default markers."""
    ai_test_files = [
        "tests/ai/test_ai_core.py",
        "tests/ai/test_ai_integration.py",
        "tests/ai/test_ai_errors.py",
        "tests/ai/test_ai_cache.py",
        "tests/ai/test_ai_performance.py",
        "tests/ai/test_ai_quality.py",
        "tests/ai/test_ai_advanced.py",
        "tests/ai/test_ai_functionality_manual.py",
    ]

    items_to_remove = []
    for item in items:
        item_path = (
            str(item.fspath)
            if hasattr(item, "fspath")
            else str(Path(item.nodeid.split("::")[0]))
        )
        normalized_item_path = item_path.replace("\\", os.sep).replace("/", os.sep)

        for ai_file in ai_test_files:
            normalized_ai_file = ai_file.replace("\\", os.sep).replace("/", os.sep)
            if normalized_ai_file in normalized_item_path or os.path.basename(
                normalized_ai_file
            ) == os.path.basename(normalized_item_path):
                items_to_remove.append(item)
                break

    for item in items_to_remove:
        items.remove(item)

    for item in items:
        if not any(item.iter_markers()):
            item.add_marker(pytest.mark.unit)


def pytest_ignore_collect(collection_path, config):
    """Ignore transient test data trees so pytest never collects generated test_*.py artifacts."""
    path_str = str(collection_path).replace("\\", "/")

    if "/tests/data/" in path_str:
        return True

    if "pytest-tmp-" in path_str or "pytest-of-" in path_str:
        if "/tests/data/" in path_str:
            return True

    if "/tests/tmp_pytest_" in path_str or "/tests/manual_mode700_dir" in path_str:
        return True

    return None


def pytest_configure(config):
    """Configure pytest for MHM testing and suppress collection warnings for development tools implementation classes."""
    project_root, tests_data_dir, test_logger, _test_log_file, _ = _get_conftest_attrs()

    config.addinivalue_line(
        "markers",
        "notebook: Notebook functionality tests (notes, lists, journal entries)",
    )

    import warnings

    warnings.filterwarnings(
        "ignore",
        message=".*cannot collect test class.*TestCoverage.*",
        category=pytest.PytestCollectionWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message=".*cannot collect test class.*because it has a __init__ constructor.*",
        category=pytest.PytestCollectionWarning,
    )
    warnings.filterwarnings(
        "ignore",
        category=pytest.PytestCollectionWarning,
        module="development_tools.tests.*",
    )

    if not os.environ.get("PYTEST_XDIST_WORKER"):
        test_logger.debug("Configuring pytest for MHM testing")

    class _NoopCache:
        def __init__(self):
            self._store = {}

        def get(self, key, default=None):
            return self._store.get(key, default)

        def set(self, key, value):
            self._store[key] = value

        def makedir(self, name):
            d = tests_data_dir / "tmp" / "pytest_cache" / str(name)
            d.mkdir(parents=True, exist_ok=True)
            return d

    try:
        cache_plugin = config.pluginmanager.getplugin("cacheprovider")
        if cache_plugin is not None:
            config.pluginmanager.unregister(cache_plugin)
        config.cache = _NoopCache()
    except Exception as exc:
        test_logger.warning(f"Failed to disable pytest cacheprovider cleanly: {exc}")

    try:
        if hasattr(config, "option") and hasattr(config.option, "tmp_path_factory"):
            config.option.tmp_path_factory = str(tests_data_dir / "tmp")
    except Exception:
        pass

    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "behavior: mark test as a behavior test")
    config.addinivalue_line("markers", "ui: mark test as testing UI components")
    config.addinivalue_line("markers", "slow: mark test as slow running (>1 second)")
    config.addinivalue_line(
        "markers", "fast: mark test as fast running (<100ms, optional)"
    )
    config.addinivalue_line(
        "markers", "asyncio: mark test as requiring asyncio support"
    )
    config.addinivalue_line(
        "markers", "file_io: mark test as having heavy file operations"
    )
    config.addinivalue_line("markers", "ai: mark test as requiring AI functionality")
    config.addinivalue_line(
        "markers", "communication: mark test as testing communication channels"
    )
    config.addinivalue_line(
        "markers",
        "tasks: mark test as task management functionality (includes reminders)",
    )
    config.addinivalue_line(
        "markers", "checkins: mark test as check-in system functionality"
    )
    config.addinivalue_line(
        "markers", "messages: mark test as message system functionality"
    )
    config.addinivalue_line(
        "markers", "analytics: mark test as analytics and reporting functionality"
    )
    config.addinivalue_line(
        "markers", "user_management: mark test as user account management functionality"
    )
    config.addinivalue_line(
        "markers", "scheduler: mark test as scheduler functionality"
    )
    config.addinivalue_line(
        "markers", "regression: mark test as preventing regression issues"
    )
    config.addinivalue_line(
        "markers", "smoke: mark test as basic functionality smoke test"
    )
    config.addinivalue_line("markers", "critical: mark test as critical path test")
    config.addinivalue_line(
        "markers",
        "no_parallel: mark test as must not run under pytest-xdist parallel execution",
    )
    config.addinivalue_line(
        "markers",
        "e2e: End-to-end tests with real tool execution (slow, excluded from regular runs)",
    )


def pytest_sessionstart(session):
    """Log test session start."""
    _project_root, _tests_data_dir, test_logger, test_log_file, _ = _get_conftest_attrs()

    if not os.environ.get("PYTEST_XDIST_WORKER"):
        test_logger.debug(f"Starting test session with {len(session.items)} tests")
        test_logger.debug(f"Test log file: {test_log_file}")

        import atexit

        def crash_recovery_handler():
            try:
                from communication.core.channel_orchestrator import CommunicationManager

                if CommunicationManager._instance is not None:
                    test_logger.warning(
                        "Crash recovery: Cleaning up CommunicationManager on unexpected exit"
                    )
                    with contextlib.suppress(Exception):
                        CommunicationManager._instance.stop_all()
                    CommunicationManager._instance = None
            except (ImportError, ModuleNotFoundError):
                pass
            except Exception as e:
                test_logger.warning(f"Error in crash recovery handler: {e}")

        atexit.register(crash_recovery_handler)

        try:
            import sys

            test_logger.debug(f"Python executable: {sys.executable}")
            test_logger.debug(f"Python version: {sys.version}")
            test_logger.debug(f"Python path: {sys.path[:3]}...")
            test_logger.debug(f"Pytest version: {pytest.__version__}")
            try:
                import pytest_xdist  # type: ignore[reportMissingImports]

                test_logger.debug(f"Pytest-xdist version: {pytest_xdist.__version__}")
            except (ImportError, AttributeError):
                test_logger.debug("Pytest-xdist: not available")
        except Exception as e:
            test_logger.warning(f"Failed to log diagnostic information: {e}")


def _consolidate_worker_logs():
    """Consolidate per-worker log files into main log files at the end of parallel test runs."""
    if os.environ.get("PYTEST_XDIST_WORKER"):
        return

    project_root, _tests_data_dir, test_logger, _test_log_file, _ = _get_conftest_attrs()
    from tests.test_helpers.test_support.conftest_logging import session_rotation_manager

    try:
        logs_dir = Path(project_root) / "tests" / "logs"
        if not logs_dir.exists():
            return

        import time

        time.sleep(0.5)

        worker_test_run_logs = sorted(logs_dir.glob("test_run_gw*.log"))
        worker_consolidated_logs = sorted(logs_dir.glob("test_consolidated_gw*.log"))

        if not (worker_test_run_logs or worker_consolidated_logs):
            return

        backup_dir = logs_dir / "worker_logs_backup"
        backup_dir.mkdir(exist_ok=True)
        import shutil

        for log_file in worker_test_run_logs + worker_consolidated_logs:
            try:
                backup_path = backup_dir / log_file.name
                shutil.copy2(log_file, backup_path)
            except Exception as e:
                test_logger.debug(f"Failed to backup worker log {log_file}: {e}")

        test_logger.info("Consolidating worker log files into main log files...")

        main_test_run_log = logs_dir / "test_run.log"
        if worker_test_run_logs:
            try:
                with open(main_test_run_log, "a", encoding="utf-8") as main_file:
                    main_file.write(f"\n{'=' * 80}\n")
                    main_file.write("# CONSOLIDATED FROM PARALLEL WORKERS\n")
                    main_file.write(f"{'=' * 80}\n\n")

                    for worker_log in worker_test_run_logs:
                        worker_id = worker_log.stem.replace("test_run_", "")
                        main_file.write(f"\n# --- Worker {worker_id} ---\n")
                        try:
                            max_retries = 5
                            retry_delay = 0.2
                            chunk_size = 1024 * 1024
                            max_size = 50 * 1024 * 1024

                            for attempt in range(max_retries):
                                try:
                                    file_size = worker_log.stat().st_size
                                    if file_size > max_size:
                                        test_logger.warning(
                                            f"Worker log {worker_log.name} is {file_size / (1024 * 1024):.1f}MB, truncating to last 50MB"
                                        )
                                        with open(worker_log, "rb") as f:
                                            f.seek(-max_size, 2)
                                            while True:
                                                chunk = f.read(chunk_size)
                                                if not chunk:
                                                    break
                                                main_file.write(
                                                    chunk.decode("utf-8", errors="replace")
                                                )
                                                main_file.flush()
                                    else:
                                        with open(
                                            worker_log, encoding="utf-8"
                                        ) as worker_file:
                                            while True:
                                                chunk = worker_file.read(chunk_size)
                                                if not chunk:
                                                    break
                                                main_file.write(chunk)
                                                main_file.flush()
                                    break
                                except (PermissionError, OSError) as e:
                                    if attempt < max_retries - 1:
                                        time.sleep(retry_delay)
                                        continue
                                    else:
                                        test_logger.warning(
                                            f"Failed to read worker log {worker_log.name} after {max_retries} attempts: {e}"
                                        )
                                        main_file.write(
                                            f"# Error: Could not read {worker_log.name} - file may be locked\n"
                                        )
                                        break
                        except Exception as e:
                            main_file.write(f"# Error reading {worker_log.name}: {e}\n")
                            test_logger.warning(
                                f"Error reading worker log {worker_log.name}: {e}"
                            )
                        main_file.write(f"\n# --- End Worker {worker_id} ---\n\n")
                        main_file.flush()

                test_logger.info(
                    f"Consolidated {len(worker_test_run_logs)} worker test_run logs into {main_test_run_log.name}"
                )
            except Exception as e:
                test_logger.warning(f"Error consolidating test_run logs: {e}")

        main_consolidated_log = logs_dir / "test_consolidated.log"
        if worker_consolidated_logs:
            try:
                with open(main_consolidated_log, "a", encoding="utf-8") as main_file:
                    main_file.write(f"\n{'=' * 80}\n")
                    main_file.write("# CONSOLIDATED FROM PARALLEL WORKERS\n")
                    main_file.write(f"{'=' * 80}\n\n")

                    for worker_log in worker_consolidated_logs:
                        worker_id = worker_log.stem.replace("test_consolidated_", "")
                        main_file.write(f"\n# --- Worker {worker_id} ---\n")
                        try:
                            max_retries = 5
                            retry_delay = 0.2
                            chunk_size = 1024 * 1024
                            max_size = 10 * 1024 * 1024

                            for attempt in range(max_retries):
                                try:
                                    file_size = worker_log.stat().st_size
                                    if file_size > max_size:
                                        test_logger.warning(
                                            f"Worker log {worker_log.name} is {file_size / (1024 * 1024):.1f}MB, truncating to last 10MB"
                                        )
                                        with open(worker_log, "rb") as f:
                                            f.seek(-max_size, 2)
                                            while True:
                                                chunk = f.read(chunk_size)
                                                if not chunk:
                                                    break
                                                main_file.write(
                                                    chunk.decode("utf-8", errors="replace")
                                                )
                                                main_file.flush()
                                    else:
                                        with open(
                                            worker_log, encoding="utf-8"
                                        ) as worker_file:
                                            while True:
                                                chunk = worker_file.read(chunk_size)
                                                if not chunk:
                                                    break
                                                main_file.write(chunk)
                                                main_file.flush()
                                    break
                                except (PermissionError, OSError) as e:
                                    if attempt < max_retries - 1:
                                        time.sleep(retry_delay)
                                        continue
                                    else:
                                        test_logger.warning(
                                            f"Failed to read worker log {worker_log.name} after {max_retries} attempts: {e}"
                                        )
                                        main_file.write(
                                            f"# Error: Could not read {worker_log.name} - file may be locked\n"
                                        )
                                        break
                        except Exception as e:
                            main_file.write(f"# Error reading {worker_log.name}: {e}\n")
                            test_logger.warning(
                                f"Error reading worker log {worker_log.name}: {e}"
                            )
                        main_file.write(f"\n# --- End Worker {worker_id} ---\n\n")

                test_logger.info(
                    f"Consolidated {len(worker_consolidated_logs)} worker consolidated logs into {main_consolidated_log.name}"
                )
                session_rotation_manager.register_log_file(str(main_consolidated_log))
            except Exception as e:
                test_logger.warning(f"Error consolidating consolidated logs: {e}")

        time.sleep(0.5)

        all_worker_logs = worker_test_run_logs + worker_consolidated_logs
        cleaned_count = 0
        failed_logs = []

        for worker_log in all_worker_logs:
            max_retries = 5
            retry_delay = 0.1

            for attempt in range(max_retries):
                try:
                    worker_log.unlink()
                    cleaned_count += 1
                    break
                except (OSError, PermissionError) as e:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        failed_logs.append(worker_log.name)
                        test_logger.debug(
                            f"Could not remove worker log {worker_log.name} after {max_retries} attempts: {e}"
                        )
                except Exception as e:
                    failed_logs.append(worker_log.name)
                    test_logger.debug(
                        f"Error removing worker log {worker_log.name}: {e}"
                    )
                    break

        if cleaned_count > 0:
            test_logger.debug(
                f"Cleaned up {cleaned_count} worker log files after consolidation"
            )
        if failed_logs:
            test_logger.debug(
                f"Could not clean up {len(failed_logs)} worker log files (locked by workers): {', '.join(failed_logs[:5])}{'...' if len(failed_logs) > 5 else ''}"
            )

        test_logger.info("Worker log consolidation completed")

    except Exception as e:
        test_logger.warning(f"Error during worker log consolidation: {e}")


def pytest_sessionfinish(session, exitstatus):
    """Log test session finish, check for log rotation, consolidate worker logs, and handle crash recovery."""
    _project_root, _tests_data_dir, test_logger, _test_log_file, _cleanup_test_user_artifacts = _get_conftest_attrs()

    test_logger.info(f"Test session finished with exit status: {exitstatus}")
    if hasattr(session, "testscollected"):
        test_logger.info(f"Tests collected: {session.testscollected}")

    if os.environ.get("PYTEST_XDIST_WORKER"):
        return

    if exitstatus == 3:
        test_logger.error(
            "Test session crashed (internal error) - saving crash diagnostics"
        )
        crash_log_file = Path("tests/logs/crash_diagnostics.log")
        try:
            crash_log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(crash_log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'=' * 80}\n")
                f.write(f"CRASH DETECTED: {now_timestamp_full()}\n")
                f.write(f"Exit Status: {exitstatus}\n")
                f.write(
                    f"Tests Run: {getattr(session, 'testsfailed', 0)} failed, {getattr(session, 'testscollected', 0)} collected\n"
                )
                f.write(f"{'=' * 80}\n")
        except Exception as e:
            test_logger.warning(f"Could not save crash diagnostics: {e}")

    try:
        from communication.core.channel_orchestrator import CommunicationManager

        if CommunicationManager._instance is not None:
            test_logger.debug("Session finish: Ensuring CommunicationManager cleanup")
            with contextlib.suppress(Exception):
                CommunicationManager._instance.stop_all()
            CommunicationManager._instance = None
    except (ImportError, ModuleNotFoundError):
        pass
    except Exception as e:
        test_logger.warning(f"Error during session finish cleanup: {e}")

    _consolidate_worker_logs()

    is_xdist = bool(getattr(session.config.option, "numprocesses", 0))
    if is_xdist:
        _cleanup_test_user_artifacts()


_test_start_times = {}


def pytest_runtest_setup(item):
    """Log when a test starts with timestamp (DEBUG level only)."""
    _project_root, _tests_data_dir, test_logger, _test_log_file, _ = _get_conftest_attrs()

    test_id = item.nodeid
    start_time = datetime.now()
    _test_start_times[test_id] = start_time
    timestamp = format_timestamp_milliseconds(start_time)

    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "main")
    test_logger.info(f"[WORKER-TEST] [{worker_id}] START: {test_id}")
    test_logger.debug(f"[TEST-START] [{worker_id}] {timestamp} - {test_id}")


def pytest_runtest_teardown(item, nextitem):
    """Log when a test ends with timestamp and duration (DEBUG level only)."""
    _project_root, _tests_data_dir, test_logger, _test_log_file, _ = _get_conftest_attrs()

    test_id = item.nodeid
    end_time = datetime.now()
    timestamp = format_timestamp_milliseconds(end_time)

    duration = None
    if test_id in _test_start_times:
        start_time = _test_start_times[test_id]
        duration_seconds = (end_time - start_time).total_seconds()
        duration = f"{duration_seconds:.3f}s"
        del _test_start_times[test_id]

    if duration:
        test_logger.debug(f"[TEST-END] {timestamp} - {test_id} (duration: {duration})")
    else:
        test_logger.debug(f"[TEST-END] {timestamp} - {test_id}")


def pytest_runtest_logreport(report):
    """Log individual test results with timestamps."""
    _project_root, _tests_data_dir, test_logger, _test_log_file, _ = _get_conftest_attrs()

    if report.when == "call":
        timestamp = format_timestamp_milliseconds(datetime.now())
        verbose_logs = os.getenv("TEST_VERBOSE_LOGS", "0")
        if report.passed:
            if verbose_logs == "2":
                test_logger.debug(
                    f"[TEST-RESULT] {timestamp} - PASSED: {report.nodeid}"
                )
        elif report.failed:
            worker_id = os.environ.get("PYTEST_XDIST_WORKER", "main")
            test_logger.info(f"[WORKER-TEST] [{worker_id}] FAILED: {report.nodeid}")
            test_logger.error(
                f"[TEST-RESULT] [{worker_id}] {timestamp} - FAILED: {report.nodeid}"
            )
            if report.longrepr:
                clean_longrepr = ANSI_ESCAPE_RE.sub("", str(report.longrepr))
                test_logger.error(f"Error details: {clean_longrepr}")
        elif report.skipped:
            worker_id = os.environ.get("PYTEST_XDIST_WORKER", "main")
            test_logger.warning(
                f"[TEST-RESULT] [{worker_id}] {timestamp} - SKIPPED: {report.nodeid}"
            )
        elif report.passed:
            worker_id = os.environ.get("PYTEST_XDIST_WORKER", "main")
            test_logger.info(f"[WORKER-TEST] [{worker_id}] PASSED: {report.nodeid}")


@pytest.fixture(scope="session", autouse=True)
def cleanup_communication_manager():
    """Clean up CommunicationManager singleton after all tests complete."""
    _project_root, _tests_data_dir, test_logger, _test_log_file, _ = _get_conftest_attrs()

    yield

    import threading

    cleanup_complete = threading.Event()
    cleanup_error: list[Exception | None] = [None]

    def do_cleanup():
        try:
            from communication.core.channel_orchestrator import CommunicationManager

            if CommunicationManager._instance is not None:
                cm_instance = CommunicationManager._instance
                test_logger.debug("Cleaning up CommunicationManager singleton...")
                stop_complete = threading.Event()
                stop_error: list[Exception | None] = [None]

                def stop_worker():
                    try:
                        cm_instance.stop_all()
                    except Exception as e:
                        stop_error[0] = e
                    finally:
                        stop_complete.set()

                stop_thread = threading.Thread(target=stop_worker, daemon=True)
                stop_thread.start()

                if not stop_complete.wait(timeout=10.0):
                    test_logger.warning(
                        "CommunicationManager.stop_all() timed out after 10 seconds - forcing cleanup"
                    )
                    try:
                        cm_instance._running = False
                        if hasattr(cm_instance, "_channels_dict"):
                            cm_instance._channels_dict.clear()
                    except Exception:
                        pass
                elif stop_error[0]:
                    test_logger.warning(f"Error during stop_all(): {stop_error[0]}")

                CommunicationManager._instance = None
                test_logger.debug("CommunicationManager cleanup completed")
        except (ImportError, ModuleNotFoundError):
            pass
        except Exception as e:
            cleanup_error[0] = e
        finally:
            cleanup_complete.set()

    cleanup_thread = threading.Thread(target=do_cleanup, daemon=True)
    cleanup_thread.start()

    if not cleanup_complete.wait(timeout=15.0):
        test_logger.warning("CommunicationManager cleanup timed out after 15 seconds")
    elif cleanup_error[0]:
        test_logger.warning(
            f"Error during CommunicationManager cleanup: {cleanup_error[0]}"
        )


@pytest.fixture(autouse=True)
def cleanup_conversation_manager():
    """Clean up ConversationManager state before each test."""
    _project_root, _tests_data_dir, test_logger, _test_log_file, _ = _get_conftest_attrs()

    try:
        from communication.message_processing.conversation_flow_manager import (
            conversation_manager,
        )

        conversation_manager.clear_all_states()
    except (ImportError, ModuleNotFoundError):
        pass
    except Exception as e:
        test_logger.warning(f"Error clearing conversation manager state: {e}")

    yield

    try:
        from communication.message_processing.conversation_flow_manager import (
            conversation_manager,
        )

        conversation_manager.clear_all_states()
    except (ImportError, ModuleNotFoundError):
        pass
    except Exception as e:
        test_logger.warning(f"Error clearing conversation manager state: {e}")


@pytest.fixture(autouse=True)
def cleanup_conversation_history():
    """Clean up ConversationHistory singleton state before and after each test."""
    _project_root, _tests_data_dir, test_logger, _test_log_file, _ = _get_conftest_attrs()

    try:
        from ai.conversation_history import get_conversation_history

        history = get_conversation_history()
        if history is not None:
            if hasattr(history, "_sessions"):
                history._sessions.clear()
            if hasattr(history, "_active_sessions"):
                history._active_sessions.clear()
    except (ImportError, ModuleNotFoundError):
        pass
    except Exception as e:
        test_logger.warning(f"Error clearing conversation history state: {e}")

    yield

    try:
        from ai.conversation_history import get_conversation_history

        history = get_conversation_history()
        if history is not None:
            if hasattr(history, "_sessions"):
                history._sessions.clear()
            if hasattr(history, "_active_sessions"):
                history._active_sessions.clear()
    except (ImportError, ModuleNotFoundError):
        pass
    except Exception as e:
        test_logger.warning(f"Error clearing conversation history state: {e}")


@pytest.fixture(autouse=True)
def cleanup_singletons():
    """Clean up singleton instances before each test to ensure isolation."""
    original_instances = {}

    try:
        try:
            from ai.chatbot import AIChatBotSingleton

            original_instances["ai_chatbot"] = AIChatBotSingleton._instance
        except (ImportError, AttributeError):
            pass

        try:
            import communication.message_processing.message_router as router_module

            original_instances["message_router"] = router_module._message_router
        except (ImportError, AttributeError):
            pass

        try:
            import ai.cache_manager as cache_module

            original_instances["response_cache"] = getattr(
                cache_module, "_response_cache", None
            )
            original_instances["context_cache"] = getattr(
                cache_module, "_context_cache", None
            )
        except (ImportError, AttributeError):
            pass

        yield

    finally:
        try:
            from ai.chatbot import AIChatBotSingleton

            if "ai_chatbot" in original_instances:
                AIChatBotSingleton._instance = original_instances["ai_chatbot"]
                if AIChatBotSingleton._instance is not None:
                    if hasattr(AIChatBotSingleton._instance, "_locks_by_user"):
                        AIChatBotSingleton._instance._locks_by_user.clear()
        except (ImportError, AttributeError):
            pass

        try:
            import communication.message_processing.message_router as router_module

            if "message_router" in original_instances:
                router_module._message_router = original_instances["message_router"]
        except (ImportError, AttributeError):
            pass

        try:
            import ai.cache_manager as cache_module

            if (
                hasattr(cache_module, "_response_cache")
                and cache_module._response_cache is not None
            ):
                if hasattr(cache_module._response_cache, "clear"):
                    cache_module._response_cache.clear()
                cache_module._response_cache = None
            if (
                hasattr(cache_module, "_context_cache")
                and cache_module._context_cache is not None
            ):
                if hasattr(cache_module._context_cache, "clear"):
                    cache_module._context_cache.clear()
                cache_module._context_cache = None
        except (ImportError, AttributeError):
            pass


@pytest.fixture(autouse=True)
def cleanup_communication_threads():
    """
    Lightweight cleanup of CommunicationManager state between tests.
    Full cleanup is handled by cleanup_communication_manager at session end.
    """
    _project_root, _tests_data_dir, test_logger, _test_log_file, _ = _get_conftest_attrs()

    yield

    try:
        from communication.core.channel_orchestrator import CommunicationManager

        if CommunicationManager._instance is not None:
            try:
                if hasattr(CommunicationManager._instance, "_channels_dict"):
                    CommunicationManager._instance._channels_dict.clear()
            except Exception:
                pass
    except (ImportError, ModuleNotFoundError):
        pass
    except Exception:
        pass


@pytest.fixture(autouse=True)
def periodic_memory_cleanup(request):
    """
    Periodic memory cleanup to prevent accumulation during long test runs.
    """
    global _periodic_cleanup_test_count
    _project_root, _tests_data_dir, test_logger, _test_log_file, _ = _get_conftest_attrs()

    yield

    _periodic_cleanup_test_count += 1
    test_count = _periodic_cleanup_test_count

    is_parallel = "PYTEST_XDIST_WORKER" in os.environ
    gc_interval = 5 if is_parallel else 20

    if test_count % gc_interval == 0:
        import gc

        collected = gc.collect()
        if collected > 0:
            test_logger.debug(
                f"Garbage collection freed {collected} objects after {test_count} tests"
            )

        try:
            import ai.cache_manager as cache_module

            if (
                hasattr(cache_module, "_response_cache")
                and cache_module._response_cache is not None
            ) and hasattr(cache_module._response_cache, "clear"):
                cache_module._response_cache.clear()
            if (
                hasattr(cache_module, "_context_cache")
                and cache_module._context_cache is not None
            ) and hasattr(cache_module._context_cache, "clear"):
                cache_module._context_cache.clear()
        except (ImportError, AttributeError):
            pass

        try:
            from ai.chatbot import AIChatBotSingleton

            if AIChatBotSingleton._instance is not None:
                if hasattr(AIChatBotSingleton._instance, "_locks_by_user"):
                    AIChatBotSingleton._instance._locks_by_user.clear()
        except (ImportError, AttributeError):
            pass
