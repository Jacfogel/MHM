"""
Pytest configuration and shared fixtures for MHM testing framework.

This file provides:
- Test configuration
- Shared fixtures for common test data
- Temporary directory management
- Mock configurations for testing
- Dedicated testing log configuration
"""

import pytest
import os
import sys  # noqa: F401 -- used in collection hooks (sys.modules) and debug logging (sys.executable, sys.version, sys.path)

os.environ["QT_QPA_PLATFORM"] = "offscreen"
# Set environment variable for consolidated logging very early, before any logging initialization
# Allow override via environment variable for individual component logging
os.environ["TEST_CONSOLIDATED_LOGGING"] = os.environ.get(
    "TEST_CONSOLIDATED_LOGGING", "1"
)
import logging
import warnings
import re
from pathlib import Path

# CRITICAL: Suppress __package__ != __spec__.parent warnings immediately after importing warnings
# These warnings are emitted during module import, so they must be filtered before any other imports
# Use simplefilter to catch all DeprecationWarnings, then add specific filters
warnings.simplefilter("ignore", DeprecationWarning)
warnings.filterwarnings(
    "ignore", message=".*__package__.*", category=DeprecationWarning
)

# Strip ANSI escape sequences from pytest longrepr before writing to log files.
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _patch_windows_pathlib_mkdir_mode() -> None:
    """Avoid Windows ACL lockout when pytest creates temp roots with mode 0o700."""
    if os.name != "nt":
        return

    original_mkdir = Path.mkdir
    if getattr(original_mkdir, "__name__", "") == "_mhm_safe_mkdir":
        return

    def _mhm_safe_mkdir(self, mode=0o777, parents=False, exist_ok=False):
        # In this environment, mode=0o700 can create unreadable directories.
        if mode == 0o700:
            mode = 0o777
        try:
            return original_mkdir(self, mode=mode, parents=parents, exist_ok=exist_ok)
        except FileNotFoundError:
            # Some cleanup fixtures remove pytest temp roots while other workers are
            # still creating basetemp/cache directories. Retry once by rebuilding
            # the missing parent chain for known pytest temp locations.
            path_str = str(self).replace("\\", "/")
            if (
                not parents
                and (
                    "/pytest_runner/" in path_str
                    or "/tests/data/tmp_pytest_runtime/" in path_str
                    or "/tests/data/tmp/" in path_str
                )
            ):
                return original_mkdir(self, mode=mode, parents=True, exist_ok=exist_ok)
            raise

    Path.mkdir = _mhm_safe_mkdir


def _patch_windows_os_mkdir_mode() -> None:
    """Normalize mode=0o700 for os.mkdir on Windows to avoid unreadable temp dirs."""
    if os.name != "nt":
        return

    original_os_mkdir = os.mkdir
    if getattr(original_os_mkdir, "__name__", "") == "_mhm_safe_os_mkdir":
        return

    def _mhm_safe_os_mkdir(path, mode=0o777, *args, **kwargs):
        if mode == 0o700:
            mode = 0o777
        return original_os_mkdir(path, mode, *args, **kwargs)

    os.mkdir = _mhm_safe_os_mkdir


def _patch_pytest_dead_symlink_cleanup() -> None:
    """Prevent teardown crashes when pytest temp roots hit transient ACL issues on Windows."""
    try:
        import importlib

        pytest_pathlib = importlib.import_module("_pytest.pathlib")
        pytest_tmpdir = importlib.import_module("_pytest.tmpdir")
    except Exception:
        return

    original = getattr(pytest_tmpdir, "cleanup_dead_symlinks", None) or getattr(
        pytest_pathlib, "cleanup_dead_symlinks", None
    )
    if original is None:
        return
    if getattr(original, "__name__", "") == "_mhm_safe_cleanup_dead_symlinks":
        return

    def _mhm_safe_cleanup_dead_symlinks(root):
        try:
            return original(root)
        except PermissionError:
            # Best-effort cleanup only: never fail an entire test session on this step.
            return None

    pytest_pathlib.cleanup_dead_symlinks = _mhm_safe_cleanup_dead_symlinks
    pytest_tmpdir.cleanup_dead_symlinks = _mhm_safe_cleanup_dead_symlinks


_patch_pytest_dead_symlink_cleanup()
_patch_windows_pathlib_mkdir_mode()
_patch_windows_os_mkdir_mode()


def ensure_qt_runtime():
    """Re-export from test_support so 'from tests.conftest import ensure_qt_runtime' still works."""
    from tests.test_support.conftest_env import ensure_qt_runtime as _fn
    return _fn()


# Suppress Discord library warnings
warnings.filterwarnings(
    "ignore", message=".*audioop.*is deprecated.*", category=DeprecationWarning
)
warnings.filterwarnings(
    "ignore",
    message=".*parameter 'timeout' of type 'float' is deprecated.*",
    category=DeprecationWarning,
)
warnings.filterwarnings("ignore", category=pytest.PytestUnhandledThreadExceptionWarning)
warnings.filterwarnings("ignore", category=pytest.PytestUnraisableExceptionWarning)
# Suppress PytestCollectionWarning for development tools implementation classes
# These classes (TestCoverageAnalyzer, TestCoverageReportGenerator) are implementation classes, not test classes
# They start with "Test" which makes pytest try to collect them, but they have __init__ constructors
# Apply filters early to catch warnings during collection
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
# General filter for all PytestCollectionWarning from development_tools modules
warnings.filterwarnings(
    "ignore",
    category=pytest.PytestCollectionWarning,
    module="development_tools.tests.*",
)

# Additional __package__ warning filters (redundant but explicit for clarity)
# The main filter is above, right after importing warnings
warnings.filterwarnings(
    "ignore", message=".*__package__.*", category=DeprecationWarning
)

# Suppress specific Discord library warnings more broadly
warnings.filterwarnings("ignore", module="discord.player")
warnings.filterwarnings("ignore", module="discord.http")
warnings.filterwarnings("ignore", message=".*audioop.*", category=DeprecationWarning)
warnings.filterwarnings(
    "ignore", message=".*timeout.*deprecated.*", category=DeprecationWarning
)

# Additional comprehensive warning suppression
# Suppress audioop deprecation warning from discord.player (Python 3.13 deprecation)
# Note: This warning comes from discord library's use of deprecated audioop module
# It will be fixed when discord.py updates, but we suppress it in tests for now
warnings.filterwarnings(
    "ignore", message=".*audioop.*deprecated.*", category=DeprecationWarning
)
warnings.filterwarnings(
    "ignore",
    message=".*audioop.*",
    category=DeprecationWarning,
    module="discord.player",
)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="discord.player")
warnings.filterwarnings(
    "ignore", message=".*timeout.*", category=DeprecationWarning, module="discord.*"
)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="discord.http")

# Suppress aiohttp client session warnings
warnings.filterwarnings(
    "ignore", message=".*Unclosed client session.*", category=ResourceWarning
)
warnings.filterwarnings(
    "ignore",
    message=".*Task was destroyed but it is pending.*",
    category=RuntimeWarning,
)
# Suppress unawaited coroutine warnings from Discord bot event handlers in test environments
# This is expected when using mocks - the coroutines are created but never executed
# The coroutine is registered with @bot.event but may not be awaited in test environments
warnings.filterwarnings(
    "ignore",
    message=".*coroutine.*_on_ready_internal.*was never awaited.*",
    category=RuntimeWarning,
)
warnings.filterwarnings(
    "ignore",
    message=".*coroutine.*was never awaited.*",
    category=RuntimeWarning,
    module="communication.communication_channels.discord.bot",
)

# Note: Do not override BASE_DATA_DIR/USER_INFO_DIR_PATH via environment here,
# as some unit tests assert the library defaults. Session fixtures below
# patch core.config attributes to isolate user data under tests/data/users.

# Ensure project root is on sys.path ONCE for all tests
project_root = Path(__file__).parent.parent


# CRITICAL: Set up logging isolation BEFORE importing any core modules
def setup_logging_isolation():
    """Set up logging isolation before any core modules are imported."""
    # Remove all handlers from root logger to prevent test logs from going to app.log
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        # Never close stream handlers during tests: closing captured stdio can
        # break pytest output streams on Windows.
        if isinstance(handler, logging.FileHandler):
            handler.close()
        root_logger.removeHandler(handler)

    # Also clear any handlers from the main application logger if it exists
    main_logger = logging.getLogger("mhm")
    for handler in main_logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
        main_logger.removeHandler(handler)

    # Set propagate to False for main loggers to prevent test logs from bubbling up
    root_logger.propagate = False
    main_logger.propagate = False


# Set up logging isolation immediately
setup_logging_isolation()

# Set environment variable to indicate we're running tests
# TEST_VERBOSE_LOGS levels:
#   '0' (quiet/default): Component loggers INFO, Test loggers WARNING
#   '1' (medium): Component loggers INFO, Test loggers INFO
#   '2' (verbose): Component loggers DEBUG, Test loggers DEBUG
os.environ["MHM_TESTING"] = "1"
os.environ["TEST_VERBOSE_LOGS"] = os.environ.get("TEST_VERBOSE_LOGS", "0")
# Disable core app log rotation during tests to avoid Windows file-in-use issues
os.environ["DISABLE_LOG_ROTATION"] = "1"

# Force all log paths to tests/logs for absolute isolation, even if modules read env at import time
tests_logs_dir = (Path(__file__).parent / "logs").resolve()
tests_logs_dir.mkdir(exist_ok=True)
os.environ["LOGS_DIR"] = str(tests_logs_dir)
os.environ["LOG_BACKUP_DIR"] = str(tests_logs_dir / "backups")
os.environ["LOG_ARCHIVE_DIR"] = str(tests_logs_dir / "archive")
(tests_logs_dir / "backups").mkdir(exist_ok=True)
(tests_logs_dir / "archive").mkdir(exist_ok=True)

# In test mode, all component logs go to test_consolidated.log
# We'll set these up properly in setup_consolidated_test_logging fixture
# For now, just point them to a placeholder - the fixture will redirect them
consolidated_log_placeholder = str(tests_logs_dir / "test_consolidated.log")
os.environ["LOG_MAIN_FILE"] = consolidated_log_placeholder
os.environ["LOG_DISCORD_FILE"] = consolidated_log_placeholder
os.environ["LOG_AI_FILE"] = consolidated_log_placeholder
os.environ["LOG_USER_ACTIVITY_FILE"] = consolidated_log_placeholder
os.environ["LOG_ERRORS_FILE"] = consolidated_log_placeholder
os.environ["LOG_COMMUNICATION_MANAGER_FILE"] = consolidated_log_placeholder
os.environ["LOG_EMAIL_FILE"] = consolidated_log_placeholder
os.environ["LOG_UI_FILE"] = consolidated_log_placeholder
os.environ["LOG_FILE_OPS_FILE"] = consolidated_log_placeholder
os.environ["LOG_SCHEDULER_FILE"] = consolidated_log_placeholder

# Ensure all user data for tests is stored under tests/data to avoid
# accidental writes to system directories like /tmp or the real data
# directory. The environment variable must be set before importing
# core.config so that BASE_DATA_DIR resolves correctly.
tests_data_dir = (Path(__file__).parent / "data").resolve()
tests_data_dir.mkdir(exist_ok=True)
(tests_data_dir / "users").mkdir(parents=True, exist_ok=True)
tests_data_tmp_dir = tests_data_dir / "tmp"
tests_data_tmp_dir.mkdir(parents=True, exist_ok=True)

# Load themed fixture/hook plugins (same namespace; development_tools/conftest overrides still apply)
pytest_plugins = ["tests.test_support.conftest_env", "tests.test_support.conftest_mocks", "tests.test_support.conftest_cleanup", "tests.test_support.conftest_logging", "tests.test_support.conftest_user_data", "tests.test_support.conftest_hooks"]

# Keep pytest runtime temp/cache under a dedicated root that cleanup fixtures do not purge.
tests_pytest_runtime_tmp_dir = tests_data_dir / "tmp_pytest_runtime"
tests_pytest_runtime_tmp_dir.mkdir(parents=True, exist_ok=True)
os.environ["TEST_DATA_DIR"] = os.environ.get("TEST_DATA_DIR", str(tests_data_dir))
# Also set BASE_DATA_DIR for any code that reads it directly
os.environ["BASE_DATA_DIR"] = str(tests_data_dir)
# Keep pytest temp/cache helper artifacts under tests/data/tmp when possible.
os.environ.setdefault("PYTEST_DEBUG_TEMPROOT", str(tests_pytest_runtime_tmp_dir))
os.environ.setdefault(
    "PYTEST_CACHE_DIR", str(tests_pytest_runtime_tmp_dir / "pytest_cache")
)
# Route service flags to tests/data/flags in test mode
flags_dir = tests_data_dir / "flags"
flags_dir.mkdir(parents=True, exist_ok=True)
os.environ["MHM_FLAGS_DIR"] = str(flags_dir)

# Import core modules for testing (after logging isolation is set up)
# Force core config paths to tests/data early so all modules see test isolation
# Note: This import may fail for development tools tests that don't need core modules
try:
    import core.config as _core_config

    _core_config.BASE_DATA_DIR = str(tests_data_dir)
    _core_config.USER_INFO_DIR_PATH = str(tests_data_dir / "users")
except (ImportError, ModuleNotFoundError):
    # Core modules not available (e.g., in development tools tests)
    # This is expected and safe to ignore for tests that don't use core functionality
    _core_config = None

# CRITICAL: Re-initialize UserDataManager module-level instance if it was already imported
# This ensures the module-level instance uses the test directory
try:
    import core.user_data_manager as udm_module
    from core.user_data_manager import UserDataManager

    # Recreate the module-level instance with updated BASE_DATA_DIR
    if hasattr(udm_module, "user_data_manager"):
        udm_module.user_data_manager = UserDataManager()
except (ImportError, NameError):
    pass  # UserDataManager not imported yet, will use correct paths when imported


# Import the formatter from core.logger instead of duplicating it
# Note: This import may fail for development tools tests that don't need core modules
try:
    from core.logger import PytestContextLogFormatter as PytestContextLogFormatter
except (ImportError, ModuleNotFoundError):
    # Core modules not available (e.g., in development tools tests)
    # Define a minimal formatter for tests that don't use core.logger available.
    class _FallbackPytestContextLogFormatter(logging.Formatter):
        """Minimal formatter for tests that don't have core.logger available."""

        def __init__(self, fmt=None, datefmt=None):
            super().__init__(fmt=fmt, datefmt=datefmt)

    PytestContextLogFormatter: type[logging.Formatter] = (
        _FallbackPytestContextLogFormatter
    )

# Global flag to prevent multiple test logging setups
_test_logging_setup_done = False
_test_logger_global: logging.Logger | None = None
_test_log_file_global: Path | None = None


# Set up dedicated testing logging
def setup_test_logging() -> tuple[logging.Logger, Path]:
    """Set up dedicated logging for tests with complete isolation from main app logging."""
    global _test_logging_setup_done, _test_logger_global, _test_log_file_global

    # Prevent multiple setup calls
    if _test_logging_setup_done:
        assert _test_logger_global is not None and _test_log_file_global is not None
        return _test_logger_global, _test_log_file_global

    _test_logging_setup_done = True

    # Suppress Discord library warnings
    import warnings

    warnings.filterwarnings(
        "ignore",
        message="'audioop' is deprecated and slated for removal in Python 3.13",
        category=DeprecationWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message="parameter 'timeout' of type 'float' is deprecated",
        category=DeprecationWarning,
    )

    # Create test logs directory
    test_logs_dir = Path(project_root) / "tests" / "logs"
    test_logs_dir.mkdir(exist_ok=True)
    (test_logs_dir / "backups").mkdir(exist_ok=True)

    # Create test log filename with consistent naming (one per session)
    test_log_file = test_logs_dir / "test_run.log"

    # Configure test logger
    test_logger = logging.getLogger("mhm_tests")
    # Respect TEST_VERBOSE_LOGS:
    #   0 = WARNING (failures/warnings/skips only), 1 = INFO (test execution details), 2 = DEBUG (everything)
    # All levels log failures, warnings, and skips - the difference is in infrastructure logging
    verbose_logs = os.getenv("TEST_VERBOSE_LOGS", "0")
    if verbose_logs == "2":
        test_logger_level = logging.DEBUG
    elif verbose_logs == "1":
        test_logger_level = logging.INFO
    else:
        test_logger_level = logging.WARNING  # Level 0: Only failures, warnings, skips
    test_logger.setLevel(test_logger_level)

    # Clear any existing handlers
    test_logger.handlers.clear()

    # Use simple file handler for test logs (no size-based rotation during session)
    file_handler = logging.FileHandler(test_log_file, encoding="utf-8")
    # File handler level matches logger level to respect verbose setting
    file_handler.setLevel(test_logger_level)

    # Console handler for test output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)  # Minimize console spam during full runs

    # Create formatter with test context
    formatter = PytestContextLogFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to test logger only
    test_logger.addHandler(file_handler)
    test_logger.addHandler(console_handler)

    # Prevent test logger from propagating to root logger
    test_logger.propagate = False

    # Also set up a handler for any "mhm" loggers to go to test logs
    mhm_logger = logging.getLogger("mhm")
    # Keep component loggers quiet at levels 0 and 1 to avoid excessive logging
    # Level 1 focuses on test execution details, not component infrastructure chatter
    # 0 = WARNING, 1 = WARNING (quiet), 2 = DEBUG
    verbose_logs = os.getenv("TEST_VERBOSE_LOGS", "0")
    if verbose_logs == "2":
        mhm_logger.setLevel(logging.DEBUG)
    else:
        mhm_logger.setLevel(logging.WARNING)  # Levels 0 and 1: Only warnings and errors
    mhm_logger.handlers.clear()
    mhm_logger.addHandler(file_handler)
    mhm_logger.propagate = False

    # Store for reuse
    _test_logger_global = test_logger
    _test_log_file_global = test_log_file

    return test_logger, test_log_file


# Set up test logging
test_logger, test_log_file = setup_test_logging()


def _consolidate_and_cleanup_main_logs():
    """DEPRECATED: No longer consolidates from app.log/errors.log.

    Component loggers now write directly to test_consolidated.log via environment variables.
    This function is a deprecated no-op placeholder.
    """
    pass


def _add_test_run_start_markers():
    """Add clear test run start markers to both consolidated and test_run log files."""
    pass


# Standalone helpers wait_until and materialize_user_minimal_via_public_apis live in
# tests.test_support.test_helpers; import from there in test code.



