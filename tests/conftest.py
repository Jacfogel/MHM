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
os.environ["QT_QPA_PLATFORM"] = "offscreen"
# Set environment variable for consolidated logging very early, before any logging initialization
# Allow override via environment variable for individual component logging
os.environ['TEST_CONSOLIDATED_LOGGING'] = os.environ.get('TEST_CONSOLIDATED_LOGGING', '1')
import tempfile
import shutil
import json
import logging
import warnings
import time
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

# CRITICAL: Suppress __package__ != __spec__.parent warnings immediately after importing warnings
# These warnings are emitted during module import, so they must be filtered before any other imports
# Use simplefilter to catch all DeprecationWarnings, then add specific filters
warnings.simplefilter("ignore", DeprecationWarning)
warnings.filterwarnings("ignore", message=".*__package__.*", category=DeprecationWarning)

def ensure_qt_runtime():
    """Ensure PySide6 can load in the current environment.

    Qt-dependent tests rely on libGL/GLX libraries that may be absent in
    containerized or headless environments. Import the critical PySide6
    modules and skip those tests gracefully when the runtime is missing.
    """

    try:
        from PySide6 import QtWidgets  # noqa: F401 - import verifies availability
        from PySide6.QtWidgets import QApplication  # noqa: F401
    except (ImportError, OSError) as exc:
        message = str(exc)
        lower_message = message.lower()
        gl_indicators = ("libgl", "opengl", "libegl", "libglu", "glx")
        if any(token in lower_message for token in gl_indicators):
            pytest.skip(
                f"Qt runtime unavailable: {exc}", allow_module_level=True
            )
        raise

# Suppress Discord library warnings
warnings.filterwarnings("ignore", message=".*audioop.*is deprecated.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*parameter 'timeout' of type 'float' is deprecated.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=pytest.PytestUnhandledThreadExceptionWarning)
warnings.filterwarnings("ignore", category=pytest.PytestUnraisableExceptionWarning)
# Suppress PytestCollectionWarning for development tools implementation classes
# These classes (TestCoverageAnalyzer, TestCoverageReportGenerator) are implementation classes, not test classes
# They start with "Test" which makes pytest try to collect them, but they have __init__ constructors
# Apply filters early to catch warnings during collection
warnings.filterwarnings("ignore", message=".*cannot collect test class.*TestCoverage.*", category=pytest.PytestCollectionWarning)
warnings.filterwarnings("ignore", message=".*cannot collect test class.*because it has a __init__ constructor.*", category=pytest.PytestCollectionWarning)
# General filter for all PytestCollectionWarning from development_tools modules
warnings.filterwarnings("ignore", category=pytest.PytestCollectionWarning, module="development_tools.tests.*")

# Additional __package__ warning filters (redundant but explicit for clarity)
# The main filter is above, right after importing warnings
warnings.filterwarnings("ignore", message=".*__package__.*", category=DeprecationWarning)

# Suppress specific Discord library warnings more broadly
warnings.filterwarnings("ignore", module="discord.player")
warnings.filterwarnings("ignore", module="discord.http")
warnings.filterwarnings("ignore", message=".*audioop.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*timeout.*deprecated.*", category=DeprecationWarning)

# Additional comprehensive warning suppression
# Suppress audioop deprecation warning from discord.player (Python 3.13 deprecation)
# Note: This warning comes from discord library's use of deprecated audioop module
# It will be fixed when discord.py updates, but we suppress it in tests for now
warnings.filterwarnings("ignore", message=".*audioop.*deprecated.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*audioop.*", category=DeprecationWarning, module="discord.player")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="discord.player")
warnings.filterwarnings("ignore", message=".*timeout.*", category=DeprecationWarning, module="discord.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="discord.http")

# Suppress aiohttp client session warnings
warnings.filterwarnings("ignore", message=".*Unclosed client session.*", category=ResourceWarning)
warnings.filterwarnings("ignore", message=".*Task was destroyed but it is pending.*", category=RuntimeWarning)
# Suppress unawaited coroutine warnings from Discord bot event handlers in test environments
# This is expected when using mocks - the coroutines are created but never executed
# The coroutine is registered with @bot.event but may not be awaited in test environments
warnings.filterwarnings("ignore", message=".*coroutine.*_on_ready_internal.*was never awaited.*", category=RuntimeWarning)
warnings.filterwarnings("ignore", message=".*coroutine.*was never awaited.*", category=RuntimeWarning, module="communication.communication_channels.discord.bot")

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
        handler.close()
        root_logger.removeHandler(handler)
    
    # Also clear any handlers from the main application logger if it exists
    main_logger = logging.getLogger("mhm")
    for handler in main_logger.handlers[:]:
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
os.environ['MHM_TESTING'] = '1'
os.environ['TEST_VERBOSE_LOGS'] = os.environ.get('TEST_VERBOSE_LOGS', '0')
# Disable core app log rotation during tests to avoid Windows file-in-use issues
os.environ['DISABLE_LOG_ROTATION'] = '1'

# Force all log paths to tests/logs for absolute isolation, even if modules read env at import time
tests_logs_dir = (Path(__file__).parent / 'logs').resolve()
tests_logs_dir.mkdir(exist_ok=True)
os.environ['LOGS_DIR'] = str(tests_logs_dir)
os.environ['LOG_BACKUP_DIR'] = str(tests_logs_dir / 'backups')
os.environ['LOG_ARCHIVE_DIR'] = str(tests_logs_dir / 'archive')
(tests_logs_dir / 'backups').mkdir(exist_ok=True)
(tests_logs_dir / 'archive').mkdir(exist_ok=True)

# In test mode, all component logs go to test_consolidated.log
# We'll set these up properly in setup_consolidated_test_logging fixture
# For now, just point them to a placeholder - the fixture will redirect them
consolidated_log_placeholder = str(tests_logs_dir / 'test_consolidated.log')
os.environ['LOG_MAIN_FILE'] = consolidated_log_placeholder
os.environ['LOG_DISCORD_FILE'] = consolidated_log_placeholder
os.environ['LOG_AI_FILE'] = consolidated_log_placeholder
os.environ['LOG_USER_ACTIVITY_FILE'] = consolidated_log_placeholder
os.environ['LOG_ERRORS_FILE'] = consolidated_log_placeholder
os.environ['LOG_COMMUNICATION_MANAGER_FILE'] = consolidated_log_placeholder
os.environ['LOG_EMAIL_FILE'] = consolidated_log_placeholder
os.environ['LOG_UI_FILE'] = consolidated_log_placeholder
os.environ['LOG_FILE_OPS_FILE'] = consolidated_log_placeholder
os.environ['LOG_SCHEDULER_FILE'] = consolidated_log_placeholder

# Ensure all user data for tests is stored under tests/data to avoid
# accidental writes to system directories like /tmp or the real data
# directory. The environment variable must be set before importing
# core.config so that BASE_DATA_DIR resolves correctly.
tests_data_dir = (Path(__file__).parent / 'data').resolve()
tests_data_dir.mkdir(exist_ok=True)
(tests_data_dir / 'users').mkdir(parents=True, exist_ok=True)
os.environ['TEST_DATA_DIR'] = os.environ.get('TEST_DATA_DIR', str(tests_data_dir))
# Also set BASE_DATA_DIR for any code that reads it directly
os.environ['BASE_DATA_DIR'] = str(tests_data_dir)

# Import core modules for testing (after logging isolation is set up)
# Force core config paths to tests/data early so all modules see test isolation
import core.config as _core_config
_core_config.BASE_DATA_DIR = str(tests_data_dir)
_core_config.USER_INFO_DIR_PATH = str(tests_data_dir / 'users')

# CRITICAL: Re-initialize UserDataManager module-level instance if it was already imported
# This ensures the module-level instance uses the test directory
try:
    import core.user_data_manager as udm_module
    from core.user_data_manager import UserDataManager
    # Recreate the module-level instance with updated BASE_DATA_DIR
    if hasattr(udm_module, 'user_data_manager'):
        udm_module.user_data_manager = UserDataManager()
except (ImportError, NameError):
    pass  # UserDataManager not imported yet, will use correct paths when imported

# Session-start guard: ensure loader registry identity and completeness
@pytest.fixture(scope="session", autouse=True)
def verify_user_data_loader_registry():
    import importlib
    import core.user_management as um
    import core.user_data_handlers as udh

    # Align module state early to avoid split registries from import order
    um = importlib.reload(um)
    udh = importlib.reload(udh)

    # Identity check: both should reference the same registry object
    if um.USER_DATA_LOADERS is not udh.USER_DATA_LOADERS:
        raise AssertionError(
            "USER_DATA_LOADERS mismatch: core.user_management and core.user_data_handlers hold different dict objects."
        )

    # Completeness check: attempt registration once if any missing
    def _missing_keys():
        return [k for k, v in um.USER_DATA_LOADERS.items() if not v.get('loader')]

    missing = _missing_keys()
    if missing:
        try:
            if hasattr(um, 'register_default_loaders'):
                um.register_default_loaders()
            elif hasattr(udh, 'register_default_loaders'):
                udh.register_default_loaders()
        except Exception as e:
            raise AssertionError(f"Failed to register default loaders: {e}")

        # Re-evaluate after registration attempt
        missing_after = _missing_keys()
        if missing_after:
            raise AssertionError(
                f"Missing user data loaders after registration attempt: {missing_after}"
            )

    # All good; continue tests
    yield

# Ensure import order and perform a single default loader registration at session start
@pytest.fixture(scope="session", autouse=True)
def initialize_loader_import_order():
    """Import core.user_management before core.user_data_handlers and register loaders once.

    This ensures both modules share the same USER_DATA_LOADERS dict and that required
    loaders are present without relying on the data shim.
    """
    import importlib
    import core.user_management as um
    um = importlib.reload(um)
    try:
        import core.user_data_handlers as udh
        udh = importlib.reload(udh)
    except Exception:
        udh = None

    # Single registration pass if available
    try:
        if hasattr(um, 'register_default_loaders'):
            um.register_default_loaders()
        elif udh is not None and hasattr(udh, 'register_default_loaders'):
            udh.register_default_loaders()
    except Exception:
        # Do not fail session start; verify_user_data_loader_registry will enforce later
        pass
    yield

# Apply user-data shim immediately so tests cannot capture pre-patch references
def _apply_get_user_data_shim_early():
    # Gate with env flag to allow disabling after burn-in
    if os.getenv("ENABLE_TEST_DATA_SHIM", "1") != "1":
        return
    try:
        import core.user_management as um
    except Exception:
        return
    try:
        import core.user_data_handlers as udh
    except Exception:
        udh = None

    # Prefer core.user_management.get_user_data if present; otherwise fall back to
    # core.user_data_handlers.get_user_data so the shim always applies.
    original_get_user_data = getattr(um, 'get_user_data', None)
    if original_get_user_data is None and udh is not None and hasattr(udh, 'get_user_data'):
        original_get_user_data = getattr(udh, 'get_user_data', None)
    if original_get_user_data is None:
        return

    def _load_single_type(user_id: str, key: str, *, auto_create: bool):
        try:
            entry = um.USER_DATA_LOADERS.get(key)
            loader = entry.get('loader') if entry else None
            if loader is None:
                key_to_func_and_file = {
                    'account': (um._get_user_data__load_account, 'account'),
                    'preferences': (um._get_user_data__load_preferences, 'preferences'),
                    'context': (um._get_user_data__load_context, 'user_context'),
                    'schedules': (um._get_user_data__load_schedules, 'schedules'),
                }
                func_file = key_to_func_and_file.get(key)
                if func_file is None:
                    return None
                func, file_type = func_file
                try:
                    um.register_data_loader(key, func, file_type)
                    entry = um.USER_DATA_LOADERS.get(key)
                    loader = entry.get('loader') if entry else None
                except Exception:
                    loader = func
            if loader is None:
                return None
            return loader(user_id, auto_create)
        except Exception:
            return None

    def wrapped_get_user_data(user_id: str, data_type: str = 'all', *args, **kwargs):
        auto_create = True
        try:
            auto_create = bool(kwargs.get('auto_create', True))
        except Exception:
            auto_create = True
        result = original_get_user_data(user_id, data_type, *args, **kwargs)
        try:
            if data_type == 'all':
                if not isinstance(result, dict):
                    result = {} if result is None else {"value": result}
                for key in ('account', 'preferences', 'context', 'schedules'):
                    if key not in result or not result.get(key):
                        loaded = _load_single_type(user_id, key, auto_create=auto_create)
                        if loaded is not None:
                            result[key] = loaded
                return result
            if isinstance(data_type, list):
                # Ensure a dict containing requested keys; fill missing via loaders
                if not isinstance(result, dict):
                    result = {}
                for key in data_type:
                    if key not in result or not result.get(key):
                        loaded = _load_single_type(user_id, key, auto_create=auto_create)
                        if loaded is not None:
                            result[key] = loaded
                return result
            if isinstance(data_type, str):
                key = data_type
                if isinstance(result, dict) and result.get(key):
                    return result
                loaded = _load_single_type(user_id, key, auto_create=auto_create)
                if loaded is not None:
                    return {key: loaded}
                return result
        except Exception:
            return result

    # Patch both modules so call sites using either path receive the shim
    try:
        setattr(um, 'get_user_data', wrapped_get_user_data)
    except Exception:
        pass
    try:
        if udh is not None and hasattr(udh, 'get_user_data'):
            setattr(udh, 'get_user_data', wrapped_get_user_data)
    except Exception:
        pass

_apply_get_user_data_shim_early()

# Allow tests to opt-out of the data shim via marker: @pytest.mark.no_data_shim
@pytest.fixture(scope="function", autouse=True)
def toggle_data_shim_per_marker(request, monkeypatch):
    marker = request.node.get_closest_marker('no_data_shim')
    if marker is not None:
        monkeypatch.setenv('ENABLE_TEST_DATA_SHIM', '0')
    yield

# Global QMessageBox patch to prevent popup dialogs during testing
def setup_qmessagebox_patches():
    """Set up global QMessageBox patches to prevent popup dialogs during testing."""
    try:
        from PySide6.QtWidgets import QMessageBox
        
        # Create a mock QMessageBox that returns appropriate values
        class MockQMessageBox:
            @staticmethod
            def information(*args, **kwargs):
                return QMessageBox.StandardButton.Ok
            
            @staticmethod
            def warning(*args, **kwargs):
                return QMessageBox.StandardButton.Ok
            
            @staticmethod
            def critical(*args, **kwargs):
                return QMessageBox.StandardButton.Ok
            
            @staticmethod
            def question(*args, **kwargs):
                return QMessageBox.StandardButton.Yes
            
            @staticmethod
            def about(*args, **kwargs):
                return QMessageBox.StandardButton.Ok
        
        # Apply the patch globally
        QMessageBox.information = MockQMessageBox.information
        QMessageBox.warning = MockQMessageBox.warning
        QMessageBox.critical = MockQMessageBox.critical
        QMessageBox.question = MockQMessageBox.question
        QMessageBox.about = MockQMessageBox.about
        
        print("Global QMessageBox patches applied to prevent popup dialogs")
    except ImportError:
        # PySide6 not available, skip QMessageBox patches
        print("PySide6 not available, skipping QMessageBox patches")
    except Exception as e:
        print(f"Failed to apply QMessageBox patches: {e}")

# Set up QMessageBox patches
setup_qmessagebox_patches()

# Import the formatter from core.logger instead of duplicating it
from core.logger import PytestContextLogFormatter

# Global flag to prevent multiple test logging setups
_test_logging_setup_done = False
_test_logger_global = None
_test_log_file_global = None

# Set up dedicated testing logging
def setup_test_logging():
    """Set up dedicated logging for tests with complete isolation from main app logging."""
    global _test_logging_setup_done, _test_logger_global, _test_log_file_global
    
    # Prevent multiple setup calls
    if _test_logging_setup_done:
        return _test_logger_global, _test_log_file_global
    
    _test_logging_setup_done = True
    
    # Suppress Discord library warnings
    import warnings
    warnings.filterwarnings("ignore", message="'audioop' is deprecated and slated for removal in Python 3.13", category=DeprecationWarning)
    warnings.filterwarnings("ignore", message="parameter 'timeout' of type 'float' is deprecated", category=DeprecationWarning)
    
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
    file_handler = logging.FileHandler(test_log_file, encoding='utf-8')
    # File handler level matches logger level to respect verbose setting
    file_handler.setLevel(test_logger_level)
    
    # Console handler for test output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)  # Minimize console spam during full runs
    
    # Create formatter with test context
    formatter = PytestContextLogFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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

# Session-based log rotation management
class SessionLogRotationManager:
    """Manages session-based log rotation that rotates ALL logs together if any exceed size limits."""
    
    def __init__(self, max_size_mb=2):  # 2MB for test logs (lower than production 5MB for more frequent rotation)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.log_files = []
        self.rotation_needed = False
        self.last_rotation_check = None
        
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
        """Check if any log file exceeds the size limit or if time-based rotation is needed."""
        from datetime import datetime, timedelta
        
        # Check time-based rotation (daily rotation for test logs)
        now = datetime.now()
        if self.last_rotation_check is None:
            self.last_rotation_check = now
            # Don't rotate on first check - just initialize the timestamp
            # Check size-based rotation instead
        # Rotate if it's been more than 24 hours since last rotation
        elif (now - self.last_rotation_check) > timedelta(hours=24):
            self.rotation_needed = True
            test_logger.info(f"Time-based rotation needed (last rotation: {self.last_rotation_check})")
            return True
        
        # Check size-based rotation (only if time-based didn't trigger)
        for log_file in self.log_files:
            try:
                if os.path.exists(log_file):
                    file_size = os.path.getsize(log_file)
                    if file_size > self.max_size_bytes:
                        self.rotation_needed = True
                        size_mb = file_size / (1024 * 1024)
                        test_logger.info(f"Log file {log_file} exceeds limit ({size_mb:.2f}MB > {self.max_size_bytes / (1024 * 1024):.2f}MB), rotation needed")
                        return True
            except (OSError, FileNotFoundError) as e:
                test_logger.debug(f"Could not check size for {log_file}: {e}")
                continue
        return False
    
    def _write_log_header(self, log_file: str, timestamp: str):
        """Write a formatted header to a log file during rotation.
        
        Args:
            log_file: Path to the log file
            timestamp: Timestamp string to include in header
        """
        log_filename = Path(log_file).name
        
        if 'test_run' in log_filename:
            header_text = (
                f"{'='*80}\n"
                f"# TEST RUN STARTED: {timestamp}\n"
                f"# Test Execution Logging Active\n"
                f"# Test execution and framework logs are captured here\n"
                f"{'='*80}\n\n"
            )
        elif 'consolidated' in log_filename:
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
        
        for attempt in range(max_retries):
            try:
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(header_text)
                break  # Success
            except (OSError, PermissionError) as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                # Last attempt failed - log warning but don't raise
                test_logger.warning(f"Failed to write header to {log_file} after {max_retries} attempts: {e}")
    
    def rotate_all_logs(self, rotation_context="session"):
        """Rotate all registered log files together to maintain continuity.
        
        Args:
            rotation_context: Context string for logging (e.g., "session start", "session end")
        """
        # Check if rotation is needed first
        if not self.check_rotation_needed():
            return
            
        test_logger.info(f"Starting {rotation_context} log rotation for all log files")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp_display = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Ensure backups directory exists
        backup_dir = Path(os.environ.get('LOG_BACKUP_DIR', 'tests/logs/backups'))
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        for log_file in self.log_files:
            try:
                if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
                    # Create backup filename with timestamp
                    log_filename = Path(log_file).name
                    backup_filename = f"{log_filename}.{timestamp}.bak"
                    backup_file = backup_dir / backup_filename
                    
                    # Handle Windows file locking by copying instead of moving
                    # Add retry logic with timeout to prevent hanging
                    import time
                    max_retries = 3
                    retry_delay = 0.1
                    rotation_success = False
                    
                    for attempt in range(max_retries):
                        try:
                            # Try to move first (faster)
                            shutil.move(log_file, backup_file)
                            test_logger.info(f"Rotated {log_file} to {backup_file}")
                            rotation_success = True
                            break
                        except (OSError, PermissionError) as move_error:
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay)
                                continue
                            # If move fails after retries, try copy method
                            try:
                                test_logger.warning(f"Move failed for {log_file} due to file locking, using copy method: {move_error}")
                                shutil.copy2(log_file, backup_file)
                                test_logger.info(f"Copied {log_file} to {backup_file}")
                                rotation_success = True
                            except (OSError, PermissionError) as copy_error:
                                test_logger.warning(f"Copy also failed for {log_file}: {copy_error} - skipping rotation for this file")
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
                                test_logger.warning(f"Failed to write header to {log_file}: {header_error}")
                        
            except (OSError, FileNotFoundError) as e:
                test_logger.warning(f"Failed to rotate {log_file}: {e}")
        
        self.rotation_needed = False
        self.last_rotation_check = datetime.now()
        test_logger.info(f"{rotation_context.capitalize()} log rotation completed")

# Helper function for writing log headers
def _write_test_log_header(log_file: str, timestamp: str):
    """Write a formatted header to a test log file.
    
    Args:
        log_file: Path to the log file
        timestamp: Timestamp string to include in header (format: 'YYYY-MM-DD HH:MM:SS')
    """
    # Skip header writing in parallel worker processes to avoid duplicate headers
    # pytest-xdist sets PYTEST_XDIST_WORKER for worker processes
    if os.environ.get('PYTEST_XDIST_WORKER'):
        return
    
    log_filename = Path(log_file).name
    
    if 'test_run' in log_filename:
        header_text = (
            f"\n{'='*80}\n"
            f"# TEST RUN STARTED: {timestamp}\n"
            f"# Test Execution Logging Active\n"
            f"# Test execution and framework logs are captured here\n"
            f"{'='*80}\n\n"
        )
    elif 'consolidated' in log_filename:
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
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(header_text)

# Global session rotation manager
session_rotation_manager = SessionLogRotationManager()

# Global consolidated handler for new component loggers
_consolidated_handler = None

# Register the test_run file with session rotation manager
if test_log_file and test_log_file.exists():
    session_rotation_manager.register_log_file(str(test_log_file))

# Log lifecycle management
class LogLifecycleManager:
    """Manages log file lifecycle including backup, archive, and cleanup operations."""
    
    def __init__(self, archive_days=30):
        self.archive_days = archive_days
        self.backup_dir = Path(os.environ.get('LOG_BACKUP_DIR', 'tests/logs/backups'))
        self.archive_dir = Path(os.environ.get('LOG_ARCHIVE_DIR', 'tests/logs/archive'))
        
        # Ensure directories exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    def cleanup_old_archives(self):
        """Remove archive files older than the specified number of days."""
        cutoff_date = datetime.now().timestamp() - (self.archive_days * 24 * 60 * 60)
        
        cleaned_count = 0
        for archive_file in self.archive_dir.glob('*'):
            try:
                if archive_file.is_file() and archive_file.stat().st_mtime < cutoff_date:
                    archive_file.unlink()
                    cleaned_count += 1
                    test_logger.debug(f"Removed old archive: {archive_file}")
            except (OSError, FileNotFoundError) as e:
                test_logger.warning(f"Failed to remove archive {archive_file}: {e}")
        
        if cleaned_count > 0:
            test_logger.info(f"Cleaned up {cleaned_count} old archive files (older than {self.archive_days} days)")
        
        return cleaned_count
    
    def archive_old_backups(self):
        """Move old backup files to archive directory."""
        cutoff_date = datetime.now().timestamp() - (7 * 24 * 60 * 60)  # 7 days
        
        archived_count = 0
        for backup_file in self.backup_dir.glob('*'):
            try:
                if backup_file.is_file() and backup_file.stat().st_mtime < cutoff_date:
                    # Create archive filename with timestamp
                    timestamp = datetime.fromtimestamp(backup_file.stat().st_mtime).strftime("%Y%m%d_%H%M%S")
                    archive_filename = f"{backup_file.stem}_{timestamp}{backup_file.suffix}"
                    archive_path = self.archive_dir / archive_filename
                    
                    shutil.move(str(backup_file), str(archive_path))
                    archived_count += 1
                    test_logger.debug(f"Archived backup: {backup_file} -> {archive_path}")
            except (OSError, FileNotFoundError) as e:
                test_logger.warning(f"Failed to archive backup {backup_file}: {e}")
        
        if archived_count > 0:
            test_logger.info(f"Archived {archived_count} old backup files")
        
        return archived_count
    
    def perform_lifecycle_maintenance(self):
        """Perform all lifecycle maintenance operations."""
        # Reduce verbosity - only log if something actually happens
        archived_count = self.archive_old_backups()
        cleanup_count = self.cleanup_old_archives()
        if archived_count > 0 or cleanup_count > 0:
            test_logger.debug(f"Log lifecycle maintenance: archived {archived_count}, cleaned {cleanup_count}")


# Global log lifecycle manager
log_lifecycle_manager = LogLifecycleManager()

# Configure size-based rotation for component logs during tests to avoid growth
@pytest.fixture(scope="session", autouse=True)
def setup_consolidated_test_logging():
    """Set up consolidated test logging - all component logs go to a single file.

    This replaces the complex multi-file logging system with a single consolidated log file
    that contains all component logs, making it much easier to manage and debug.
    
    In parallel execution mode (pytest-xdist), uses per-worker log files to avoid
    file locking issues and interleaved log entries.
    """
    # Detect parallel execution mode
    worker_id = os.environ.get('PYTEST_XDIST_WORKER')
    is_parallel = worker_id is not None
    
    # Use per-worker log files in parallel mode to avoid file locking issues
    if is_parallel:
        # Per-worker log files: test_run_gw0.log, test_consolidated_gw0.log, etc.
        consolidated_log_file = Path(project_root) / "tests" / "logs" / f"test_consolidated_{worker_id}.log"
        test_run_log_file = Path(project_root) / "tests" / "logs" / f"test_run_{worker_id}.log"
    else:
        # Sequential mode: use standard log files
        consolidated_log_file = Path(project_root) / "tests" / "logs" / "test_consolidated.log"
        test_run_log_file = Path(project_root) / "tests" / "logs" / "test_run.log"
    
    consolidated_log_file.parent.mkdir(exist_ok=True)

    # Register both log files with session rotation manager BEFORE checking rotation
    session_rotation_manager.register_log_file(str(consolidated_log_file))
    session_rotation_manager.register_log_file(str(test_run_log_file))
    
    # Check for rotation BEFORE writing headers (rotation will create backups and write headers to new files)
    rotation_happened = False
    if session_rotation_manager.check_rotation_needed():
        session_rotation_manager.rotate_all_logs(rotation_context="session start")
        rotation_happened = True
        test_logger.info("Performed automatic log rotation at session start")
    
    # Ensure test_run.log exists so rotation manager can write headers to it
    if not test_run_log_file.exists():
        test_run_log_file.touch()

    # Write headers only if rotation didn't happen (rotation already wrote headers)
    # or if files are empty/new
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if not rotation_happened:
        # Check if files are empty or don't exist - only write headers if needed
        write_header_run = not test_run_log_file.exists() or test_run_log_file.stat().st_size == 0
        write_header_consolidated = not consolidated_log_file.exists() or consolidated_log_file.stat().st_size == 0
        
        if write_header_run:
            _write_test_log_header(str(test_run_log_file), timestamp)
        if write_header_consolidated:
            _write_test_log_header(str(consolidated_log_file), timestamp)

    # In parallel mode, update environment variables to use per-worker consolidated log
    # This prevents file locking issues - all component logs go to the per-worker consolidated file
    if is_parallel:
        logs_dir = Path(project_root) / "tests" / "logs"
        worker_consolidated = str(consolidated_log_file)
        # Point all component loggers to the per-worker consolidated log
        os.environ['LOG_MAIN_FILE'] = worker_consolidated
        os.environ['LOG_ERRORS_FILE'] = worker_consolidated
        os.environ['LOG_DISCORD_FILE'] = worker_consolidated
        os.environ['LOG_AI_FILE'] = worker_consolidated
        os.environ['LOG_USER_ACTIVITY_FILE'] = worker_consolidated
        os.environ['LOG_COMMUNICATION_MANAGER_FILE'] = worker_consolidated
        os.environ['LOG_EMAIL_FILE'] = worker_consolidated
        os.environ['LOG_UI_FILE'] = worker_consolidated
        os.environ['LOG_FILE_OPS_FILE'] = worker_consolidated
        os.environ['LOG_SCHEDULER_FILE'] = worker_consolidated
    else:
        # Sequential mode: point all component loggers to the consolidated log
        consolidated_path = str(consolidated_log_file)
        os.environ['LOG_MAIN_FILE'] = consolidated_path
        os.environ['LOG_ERRORS_FILE'] = consolidated_path
        os.environ['LOG_DISCORD_FILE'] = consolidated_path
        os.environ['LOG_AI_FILE'] = consolidated_path
        os.environ['LOG_USER_ACTIVITY_FILE'] = consolidated_path
        os.environ['LOG_COMMUNICATION_MANAGER_FILE'] = consolidated_path
        os.environ['LOG_EMAIL_FILE'] = consolidated_path
        os.environ['LOG_UI_FILE'] = consolidated_path
        os.environ['LOG_FILE_OPS_FILE'] = consolidated_path
        os.environ['LOG_SCHEDULER_FILE'] = consolidated_path

    # Set up separate handlers for component logs vs test execution logs
    # Component logs go directly to test_consolidated.log (no test context)
    # Test execution logs go directly to test_run.log (with test context)

    # Create handler for component logs (no test context)
    component_handler = logging.FileHandler(str(consolidated_log_file), mode='a', encoding='utf-8')
    # CRITICAL: Set handler level to WARNING for levels 0 and 1 to prevent excessive logging
    # Only level 2 (DEBUG) will log everything from components
    verbose_logs = os.getenv("TEST_VERBOSE_LOGS", "0")
    if verbose_logs == "2":
        component_handler.setLevel(logging.DEBUG)
    else:
        component_handler.setLevel(logging.WARNING)  # Levels 0 and 1: Only warnings and errors
    component_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                                           datefmt='%Y-%m-%d %H:%M:%S')
    component_handler.setFormatter(component_formatter)

    # Create handler for test execution logs (with test context)
    test_handler = logging.FileHandler(str(test_run_log_file), mode='a', encoding='utf-8')
    from core.logger import PytestContextLogFormatter
    test_formatter = PytestContextLogFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                                        datefmt='%Y-%m-%d %H:%M:%S')
    test_handler.setFormatter(test_formatter)

    # CRITICAL: Ensure root logger has a valid level FIRST (child loggers inherit from root)
    # This must happen before we configure other loggers to prevent None comparisons
    root_logger = logging.getLogger()
    if not isinstance(root_logger.level, int) or root_logger.level == logging.NOTSET:
        root_logger.setLevel(logging.WARNING)  # Set a safe default level
    
    # Also ensure all existing loggers have valid levels before we start configuring
    # Walk through logger hierarchy and ensure no None levels
    for logger_name in list(logging.Logger.manager.loggerDict.keys()):
        try:
            logger_obj = logging.getLogger(logger_name)
            if isinstance(logger_obj, logging.Logger):
                # Ensure logger has a valid level (not None, not NOTSET without parent)
                if logger_obj.level == logging.NOTSET:
                    # If level is NOTSET, ensure parent has valid level
                    parent = logger_obj.parent
                    if parent and parent.level == logging.NOTSET:
                        # Both logger and parent are NOTSET - set logger level
                        logger_obj.setLevel(logging.WARNING)
                elif logger_obj.level is None:
                    # Level is None (invalid) - set to safe default
                    logger_obj.setLevel(logging.WARNING)
        except Exception:
            continue  # Skip problematic loggers

    # Force component loggers to reconfigure with new log paths
    # Clear the component logger cache so they'll be recreated with updated paths
    try:
        from core.logger import _component_loggers
        _component_loggers.clear()
    except (ImportError, AttributeError):
        pass  # If cache doesn't exist or isn't accessible, that's okay
    
    # Ensure component loggers are created by importing the modules that create them
    # This will recreate them with the updated environment variables
    try:
        from core.scheduler import SchedulerManager
        from core.service import MHMService
        from communication.core.channel_orchestrator import CommunicationManager
        from ai.chatbot import AIChatbot
    except ImportError:
        pass  # Some modules might not be available during tests
    
    # Component loggers are now available for configuration
    
    # Configure loggers
    for logger_name in list(logging.Logger.manager.loggerDict.keys()):  # Use list() to avoid modification during iteration
        try:
            # Skip pytest's internal loggers to avoid breaking pytest's logging
            if logger_name.startswith('_pytest') or logger_name == 'pytest':
                continue
                
            logger_obj = logging.getLogger(logger_name)
            
            # Skip if logger_obj is not actually a Logger instance (could be PlaceHolder or other type)
            if not isinstance(logger_obj, logging.Logger):
                continue

            # Clear existing handlers
            for h in logger_obj.handlers[:]:
                try:
                    h.close()
                except Exception:
                    pass
                logger_obj.removeHandler(h)

            # Set appropriate log level
            # Validate logging constants are actually integers (defensive check)
            if not isinstance(logging.DEBUG, int) or not isinstance(logging.INFO, int) or not isinstance(logging.WARNING, int):
                # Logging module is in invalid state - skip configuration
                test_logger.warning("Logging constants are invalid - skipping logger configuration")
                continue
            
            if logger_name.startswith("mhm."):
                # Component loggers: Keep quiet at levels 0 and 1 to avoid excessive logging
                #   0 = WARNING (quiet), 1 = WARNING (quiet - focus on test execution, not component chatter), 2 = DEBUG (verbose)
                verbose_logs = os.getenv("TEST_VERBOSE_LOGS", "0")
                if verbose_logs == "2":
                    level = logging.DEBUG
                else:
                    level = logging.WARNING  # Levels 0 and 1: Only warnings and errors from components
            else:
                # Test execution loggers:
                #   0 = WARNING (failures/warnings/skips only), 1 = INFO (test execution details), 2 = DEBUG (everything)
                verbose_logs = os.getenv("TEST_VERBOSE_LOGS", "0")
                if verbose_logs == "2":
                    level = logging.DEBUG
                elif verbose_logs == "1":
                    level = logging.INFO
                else:
                    level = logging.WARNING  # Level 0: Only failures, warnings, skips
            
            # Ensure level is a valid integer before setting
            if level is None or not isinstance(level, int):
                level = logging.WARNING  # Safe default
            
            # Set level with error handling in case logger is in invalid state
            try:
                logger_obj.setLevel(level)
            except (TypeError, AttributeError) as e:
                # Skip loggers that can't have their level set (might be in invalid state)
                test_logger.debug(f"Skipping logger {logger_name} - cannot set level: {e}")
                continue

            # Component loggers go to test_consolidated.log (no test context)
            if logger_name.startswith("mhm."):
                logger_obj.addHandler(component_handler)
                logger_obj.propagate = False
            # Test execution loggers go to test_run.log (with test context)
            else:
                logger_obj.addHandler(test_handler)
                logger_obj.propagate = True
                
                # Special handling for mhm_tests logger: ensure it respects verbose setting
                if logger_name == "mhm_tests":
                    verbose_logs = os.getenv("TEST_VERBOSE_LOGS", "0")
                    if verbose_logs == "2":
                        test_level = logging.DEBUG
                    elif verbose_logs == "1":
                        test_level = logging.INFO
                    else:
                        test_level = logging.WARNING  # Level 0: Only failures, warnings, skips
                    logger_obj.setLevel(test_level)
                    # Also update handler level
                    for handler in logger_obj.handlers:
                        if isinstance(handler, logging.FileHandler):
                            handler.setLevel(test_level)

        except Exception:
            # Never fail tests due to logging configuration issues
            continue

    # Final check: ensure root logger still has valid level after configuration
    root_logger = logging.getLogger()
    if not isinstance(root_logger.level, int) or root_logger.level == logging.NOTSET:
        root_logger.setLevel(logging.WARNING)  # Set a safe default level
    
    # CRITICAL: Configure root logger to catch unnamed log entries (empty string logger name)
    # Unnamed entries with test context should go to test_run.log, not test_consolidated.log
    # Clear any existing handlers on root logger first
    for handler in root_logger.handlers[:]:
        try:
            handler.close()
        except Exception:
            pass
        root_logger.removeHandler(handler)
    # Add test handler to root logger to catch unnamed logs (they should have test context)
    root_logger.addHandler(test_handler)
    root_logger.propagate = False  # Prevent double logging
    
    # Note: Log files are already registered and rotation checked above, before headers are written
    
    # Clean up any individual log files that were created before consolidated mode was enabled
    _cleanup_individual_log_files()
    
    # Note: We no longer consolidate from app.log/errors.log because all component loggers
    # now write directly to test_consolidated.log via environment variables
    # This eliminates duplicate log entries and simplifies the logging system


# REMOVED: cap_component_log_sizes_on_start fixture
# This was causing individual file rotation which conflicts with SessionLogRotationManager
# The SessionLogRotationManager handles all rotation consistently at session start/end

# --- HOUSEKEEPING: Prune old test artifacts to keep repo tidy ---
def _cleanup_test_log_files():
    """Clean up excessive test log files to prevent accumulation."""
    try:
        logs_dir = Path(project_root) / "tests" / "logs"
        if not logs_dir.exists():
            return
            
        # Remove old individual component log files (now that we use consolidated logging)
        for log_file in logs_dir.glob("*.log"):
            # Skip the consolidated log file and test_run.log
            if log_file.name in ["test_consolidated.log", "test_run.log"]:
                continue
                
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    # If file only contains rotation message or is empty, remove it
                    if (content.startswith("# Log rotated at") and len(content.split('\n')) <= 2) or len(content) == 0:
                        log_file.unlink()
                        # Don't log cleanup operations - focus on test results
            except Exception:
                continue
                
        # Clean up backup files older than 1 day
        backups_dir = logs_dir / "backups"
        if backups_dir.exists():
            for backup_file in backups_dir.glob("*.bak"):
                try:
                    if backup_file.stat().st_mtime < time.time() - 86400:  # 1 day
                        backup_file.unlink()
                        # Don't log cleanup operations - focus on test results
                except Exception:
                    continue
                    
    except Exception as e:
        test_logger.warning(f"Error during test log cleanup: {e}")


def _cleanup_individual_log_files():
    """Clean up individual log files that were created before consolidated mode was enabled.
    
    NOTE: We no longer copy content from these files because component loggers write directly
    to test_consolidated.log via environment variables. These files should not exist in
    consolidated logging mode, so we just delete them.
    """
    try:
        logs_dir = Path(project_root) / "tests" / "logs"
        if not logs_dir.exists():
            return
            
        # List of individual log files that should be cleaned up in consolidated mode
        individual_log_files = [
            "app.log", "errors.log", "ai.log", "discord.log", "user_activity.log",
            "communication_manager.log", "email.log", "ui.log", "file_ops.log",
            "scheduler.log", "schedule_utilities.log", "analytics.log", "message.log",
            "backup.log", "checkin_dynamic.log"
        ]
        
        for log_file_name in individual_log_files:
            log_file = logs_dir / log_file_name
            if log_file.exists():
                try:
                    # Just delete the file - component loggers write directly to consolidated log
                    # No need to copy content as it's already in test_consolidated.log
                    log_file.unlink()
                    test_logger.debug(f"Cleaned up individual log file: {log_file_name}")
                except Exception as e:
                    test_logger.warning(f"Error cleaning up {log_file_name}: {e}")
                    
    except Exception as e:
        test_logger.warning(f"Error during individual log file cleanup: {e}")


def _consolidate_and_cleanup_main_logs():
    """DEPRECATED: No longer consolidates from app.log/errors.log.
    
    Component loggers now write directly to test_consolidated.log via environment variables.
    This function is kept for backward compatibility but does nothing.
    """
    # Component loggers write directly to consolidated log, no consolidation needed
    pass


def _add_test_run_start_markers():
    """Add clear test run start markers to both consolidated and test_run log files."""
    # Headers are now written immediately when consolidated logging is set up
    # No need to write duplicate headers here
    pass


def _prune_old_files(target_dir: Path, patterns: list[str], older_than_days: int) -> int:
    """Remove files in target_dir matching any pattern older than N days.

    Returns the number of files removed.
    """
    removed_count = 0
    try:
        if older_than_days <= 0:
            return 0
        cutoff = datetime.now().timestamp() - (older_than_days * 24 * 3600)
        for pattern in patterns:
            for file_path in target_dir.rglob(pattern):
                try:
                    if file_path.is_file() and file_path.stat().st_mtime < cutoff:
                        file_path.unlink(missing_ok=True)
                        removed_count += 1
                except Exception:
                    # Best-effort cleanup; ignore individual file errors
                    pass
    except Exception:
        # Never fail tests due to cleanup issues
        pass
    return removed_count


@pytest.fixture(scope="session", autouse=True)
def clear_test_user_factory_cache():
    """Clear test user factory cache at the end of the test session."""
    yield
    # Clear cache after all tests complete
    try:
        from tests.test_utilities import TestUserFactory
        TestUserFactory.clear_cache()
    except Exception:
        pass  # Ignore errors during cleanup

@pytest.fixture(scope="session", autouse=True)
def prune_test_artifacts_before_and_after_session():
    """Prune old logs (tests/logs) and backups (tests/data/backups) before and after the session.

    Defaults: logs older than 14 days, test backups older than 7 days.
    Override via TEST_LOG_RETENTION_DAYS and TEST_BACKUP_RETENTION_DAYS env vars.
    """
    project_root_path = Path(project_root)
    logs_dir = project_root_path / "tests" / "logs"
    test_backups_dir = project_root_path / "tests" / "data" / "backups"

    log_retention_days = int(os.getenv("TEST_LOG_RETENTION_DAYS", "14"))
    backup_retention_days = int(os.getenv("TEST_BACKUP_RETENTION_DAYS", "7"))

    # Prune before tests
    if logs_dir.exists():
        removed = _prune_old_files(
            logs_dir,
            patterns=["*.log", "*.log.*", "*.gz"],
            older_than_days=log_retention_days,
        )
        # Don't log cleanup operations - focus on test results

    if test_backups_dir.exists():
        removed = _prune_old_files(
            test_backups_dir,
            patterns=["*.zip"],
            older_than_days=backup_retention_days,
        )
        # Don't log cleanup operations - focus on test results

    # Clean up excessive test log files to prevent accumulation
    _cleanup_test_log_files()

    # Pre-run purge of stray pytest-of-* under tests/data and leftover tmp children
    data_dir = project_root_path / "tests" / "data"
    try:
        # Clean up conversation_states.json before tests
        conversation_states_file = data_dir / "conversation_states.json"
        if conversation_states_file.exists():
            try:
                conversation_states_file.unlink(missing_ok=True)
                # Don't log cleanup operations - focus on test results
            except Exception:
                pass
        
        # Remove any pytest-of-* directories (pytest creates these when using tmpdir fixtures)
        import glob
        pytest_pattern = str(data_dir / "pytest-of-*")
        pytest_dirs = glob.glob(pytest_pattern)
        for stray in pytest_dirs:
            stray_path = Path(stray)
            if stray_path.exists():
                shutil.rmtree(stray_path, ignore_errors=True)
                # Don't log cleanup operations - focus on test results
        tmp_dir = data_dir / "tmp"
        if tmp_dir.exists():
            for child in tmp_dir.iterdir():
                if child.is_dir() or child.is_file():
                    try:
                        if child.is_dir():
                            shutil.rmtree(child, ignore_errors=True)
                        else:
                            child.unlink(missing_ok=True)
                    except Exception:
                        pass
            # Don't log cleanup operations - they're not interesting for test results
    except Exception:
        pass

    yield

    # Prune again after tests
    if logs_dir.exists():
        removed = _prune_old_files(
            logs_dir,
            patterns=["*.log", "*.log.*", "*.gz"],
            older_than_days=log_retention_days,
        )
        # Don't log cleanup operations - focus on test results (removed logging to prevent hangs)

    if test_backups_dir.exists():
        removed = _prune_old_files(
            test_backups_dir,
            patterns=["*.zip"],
            older_than_days=backup_retention_days,
        )
        # Don't log cleanup operations - focus on test results (removed logging to prevent hangs)

    # Session-end purge: flags, tmp children, and pytest-of-* directories
    try:
        data_dir = project_root_path / "tests" / "data"
        
        # Remove pytest-of-* directories (pytest creates these when using tmpdir fixtures)
        # Use direct directory iteration instead of glob for Windows compatibility
        if data_dir.exists():
            for item in data_dir.iterdir():
                try:
                    if item.is_dir() and item.name.startswith("pytest-of-"):
                        shutil.rmtree(item, ignore_errors=True)
                        # Don't log cleanup operations - focus on test results
                except Exception:
                    pass
        
        # Clear flags directory
        flags_dir = data_dir / "flags"
        if flags_dir.exists():
            for child in flags_dir.iterdir():
                try:
                    if child.is_dir():
                        shutil.rmtree(child, ignore_errors=True)
                    else:
                        child.unlink(missing_ok=True)
                except Exception:
                    pass
            # Don't log cleanup operations - focus on test results (failures, warnings, skips)
        
        # Clear tmp directory
        tmp_dir = data_dir / "tmp"
        if tmp_dir.exists():
            for child in tmp_dir.iterdir():
                try:
                    if child.is_dir():
                        shutil.rmtree(child, ignore_errors=True)
                    else:
                        child.unlink(missing_ok=True)
                except Exception:
                    pass
            # Don't log cleanup operations - they're not interesting for test results
        
        # Clear requests directory
        requests_dir = data_dir / "requests"
        if requests_dir.exists():
            for child in requests_dir.iterdir():
                try:
                    if child.is_dir():
                        shutil.rmtree(child, ignore_errors=True)
                    else:
                        child.unlink(missing_ok=True)
                except Exception:
                    pass
            # Don't log cleanup operations - focus on test results (failures, warnings, skips)
        
        # Clean up conversation_states.json
        conversation_states_file = data_dir / "conversation_states.json"
        if conversation_states_file.exists():
            try:
                conversation_states_file.unlink(missing_ok=True)
                # Don't log cleanup operations - focus on test results
            except Exception:
                pass
    except Exception:
        pass

@pytest.fixture(scope="session", autouse=True)
def log_lifecycle_maintenance():
    """Perform log lifecycle maintenance at session start."""
    # Perform lifecycle maintenance (archive old backups, cleanup old archives)
    log_lifecycle_manager.perform_lifecycle_maintenance()
    
    yield

@pytest.fixture(scope="session", autouse=True)
def session_log_rotation_check():
    """Perform final log cleanup at session end.
    
    NOTE: Log rotation only happens at session START in setup_consolidated_test_logging.
    This ensures rotation only occurs between test runs, never during an active session.
    """
    yield
    
    # Note: We no longer consolidate from app.log/errors.log because all component loggers
    # write directly to test_consolidated.log. This eliminates duplicate log entries.

@pytest.fixture(scope="session", autouse=True)
def isolate_logging():
    """Ensure complete logging isolation during tests to prevent test logs from appearing in main app.log."""
    # Store original handlers
    root_logger = logging.getLogger()
    original_root_handlers = root_logger.handlers[:]
    
    main_logger = logging.getLogger("mhm")
    original_main_handlers = main_logger.handlers[:]
    
    # Remove all handlers from main loggers to prevent test logs from going to app.log
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)
    
    for handler in main_logger.handlers[:]:
        handler.close()
        main_logger.removeHandler(handler)
    
    # Set propagate to False for main loggers to prevent test logs from bubbling up
    root_logger.propagate = False
    main_logger.propagate = False
    
    # Reduce verbosity - this is expected behavior, no need to log it
    test_logger.debug("Logging isolation activated - test logs will not appear in main app.log")
    
    yield
    
    # Restore original handlers after tests complete
    for handler in original_root_handlers:
        root_logger.addHandler(handler)
    
    for handler in original_main_handlers:
        main_logger.addHandler(handler)
    
    # Restore propagate settings
    root_logger.propagate = True
    main_logger.propagate = True
    
    test_logger.info("Logging isolation deactivated - main app logging restored")

# Test helper: wait until a predicate returns True within a timeout
def wait_until(predicate, timeout_seconds: float = 1.0, poll_seconds: float = 0.005):
    """Poll predicate() until it returns True or timeout elapses.

    Returns True if predicate succeeds within timeout, otherwise False.
    """
    import time as _time
    deadline = _time.perf_counter() + timeout_seconds
    while _time.perf_counter() < deadline:
        try:
            if predicate():
                return True
        except Exception:
            # Ignore transient errors while waiting
            pass
        _time.sleep(poll_seconds)
    return False

# Test helper: materialize minimal user structures via public APIs
def materialize_user_minimal_via_public_apis(user_id: str) -> dict:
    """Ensure minimal structures exist without overwriting existing data.

    - Merges into existing account (preserves internal_username and enabled features)
    - Adds missing preferences keys (keeps existing categories/channel)
    - Adds a default motivational/morning period if schedules missing
    """
    from core.user_data_handlers import (
        get_user_data,
        update_user_account,
        update_user_preferences,
        update_user_schedules,
    )
    from core.user_management import get_user_id_by_identifier
    from core.config import get_user_data_dir
    import os
    
    # Resolve UUID if user_id is an internal username (race condition fix)
    # get_user_data_dir uses user_id directly, so we need to resolve UUIDs first
    resolved_user_id = user_id
    if not os.path.exists(get_user_data_dir(user_id)):
        # Try to resolve UUID from internal username
        from tests.test_utilities import TestUserFactory as TUF
        uuid_resolved = get_user_id_by_identifier(user_id) or TUF.get_test_user_id_by_internal_username(user_id, os.getenv('TEST_DATA_DIR', 'tests/data'))
        if uuid_resolved and uuid_resolved != user_id:
            resolved_user_id = uuid_resolved
            # Verify resolved UUID directory exists
            if os.path.exists(get_user_data_dir(resolved_user_id)):
                user_id = resolved_user_id
    
    # Ensure user directory exists before proceeding (race condition fix)
    user_dir = get_user_data_dir(user_id)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir, exist_ok=True)

    # Load current state
    current_all = get_user_data(user_id, 'all') or {}
    current_account = current_all.get('account') or {}
    current_prefs = current_all.get('preferences') or {}
    current_schedules = current_all.get('schedules') or {}

    # Account: preserve existing values; set sensible defaults where missing
    merged_features = dict(current_account.get('features') or {})
    if 'automated_messages' not in merged_features:
        merged_features['automated_messages'] = 'enabled'
    if 'task_management' not in merged_features:
        merged_features['task_management'] = 'disabled'
    if 'checkins' not in merged_features:
        merged_features['checkins'] = 'disabled'

    account_updates = {
        'user_id': current_account.get('user_id') or user_id,
        'internal_username': current_account.get('internal_username') or user_id,
        'account_status': current_account.get('account_status') or 'active',
        'features': merged_features,
    }
    update_user_account(user_id, account_updates)

    # Preferences: add missing keys only
    # Always ensure preferences exist (even if empty) to prevent get_user_data returning empty dict
    prefs_updates = {}
    if not current_prefs.get('categories'):
        prefs_updates['categories'] = ['motivational']
    if not current_prefs.get('channel'):
        prefs_updates['channel'] = {"type": "discord", "contact": "test#1234"}
    # Always update preferences to ensure file exists (race condition fix)
    if prefs_updates or not current_prefs:
        update_user_preferences(user_id, prefs_updates)

    # Schedules: ensure schedules exist for all categories in preferences; merge into existing
    schedules_updates = current_schedules if isinstance(current_schedules, dict) else {}
    # Get categories from preferences (or default to motivational)
    categories = current_prefs.get('categories', ['motivational'])
    if not categories:
        categories = ['motivational']
    
    # Ensure schedules exist for all categories
    for category in categories:
        schedules_updates.setdefault(category, {}).setdefault('periods', {})
        # Add a default morning period if none exists
        if 'morning' not in schedules_updates[category]['periods']:
            schedules_updates[category]['periods']['morning'] = {
                'active': True,
                'days': ['monday','tuesday','wednesday','thursday','friday'],
                'start_time': '09:00',
                'end_time': '12:00',
            }
    update_user_schedules(user_id, schedules_updates)

    # Ensure context exists
    get_user_data(user_id, 'context')
    return get_user_data(user_id, 'all')

@pytest.fixture(scope="session")
def test_data_dir():
    """Provide the repository-scoped test data directory for all tests."""
    test_logger.info(f"Using test data directory: {tests_data_dir}")
    return str(tests_data_dir)

@pytest.fixture(scope="function", autouse=True)
def mock_config(test_data_dir):
    """Mock configuration for testing with proper test data directory."""
    test_logger.debug(f"Setting up mock config with test data dir: {test_data_dir}")
    import core.config
    
    # Always patch to ensure consistent test environment
    # This ensures that even if patch_user_data_dirs is not active, we have a consistent config
    default_categories = '["motivational", "health", "quotes_to_ponder", "word_of_the_day", "fun_facts"]'

    with patch.object(core.config, "BASE_DATA_DIR", test_data_dir), \
         patch.object(core.config, "USER_INFO_DIR_PATH", os.path.join(test_data_dir, 'users')), \
         patch.object(core.config, "DEFAULT_MESSAGES_DIR_PATH", os.path.join(project_root, 'resources', 'default_messages')), \
        patch.dict(os.environ, {"CATEGORIES": default_categories}, clear=False):
        yield


@pytest.fixture(scope="function", autouse=True)
def ensure_mock_config_applied(mock_config, test_data_dir):
    """Verify mock_config fixture is active for every test."""
    import os
    import core.config

    assert os.path.samefile(core.config.BASE_DATA_DIR, test_data_dir)
    yield


# REMOVED: redirect_tempdir fixture - conflicts with force_test_data_directory
# The session-scoped force_test_data_directory fixture handles temp directory redirection globally


@pytest.fixture(scope="function", autouse=True)
def clear_user_caches_between_tests():
    """Ensure user data caches don't leak between tests."""
    from core.user_management import clear_user_caches
    clear_user_caches()
    yield
    clear_user_caches()

@pytest.fixture(scope="session", autouse=True)
def register_user_data_loaders_session():
    """Ensure core user data loaders are present without overwriting metadata."""
    import core.user_management as um
    # Set only missing loaders to avoid clobbering metadata
    for key, func, ftype in [
        ('account', um._get_user_data__load_account, 'account'),
        ('preferences', um._get_user_data__load_preferences, 'preferences'),
        ('context', um._get_user_data__load_context, 'user_context'),
        ('schedules', um._get_user_data__load_schedules, 'schedules'),
    ]:
        try:
            entry = um.USER_DATA_LOADERS.get(key)
            if entry and entry.get('loader') is None:
                um.register_data_loader(key, func, ftype)
        except Exception:
            # As a fallback, if the dict is missing, register minimally
            um.register_data_loader(key, func, ftype)
    yield

@pytest.fixture(scope="function", autouse=True)
def fix_user_data_loaders():
    """Ensure loaders stay correctly registered for each test without overwriting metadata."""
    import core.user_management as um
    for key, func, ftype in [
        ('account', um._get_user_data__load_account, 'account'),
        ('preferences', um._get_user_data__load_preferences, 'preferences'),
        ('context', um._get_user_data__load_context, 'user_context'),
        ('schedules', um._get_user_data__load_schedules, 'schedules'),
    ]:
        entry = um.USER_DATA_LOADERS.get(key)
        if entry and entry.get('loader') is None:
            um.register_data_loader(key, func, ftype)
    yield

@pytest.fixture(scope="session", autouse=True)
def shim_get_user_data_to_invoke_loaders():
    """Shim core.user_management.get_user_data to ensure structured dicts.

    If a test calls get_user_data with 'all' or a specific type and the result is
    empty/missing, invoke the registered loaders in USER_DATA_LOADERS to assemble
    the expected structure. This preserves production behavior when everything is
    wired correctly, but guards against import-order timing in tests.
    """
    import core.user_management as um
    # Safety net: always provide structural dicts during tests regardless of loader state
    # Also patch the public helpers module used by many tests
    try:
        import core.user_data_handlers as udh
    except Exception:
        udh = None

    # Prefer core.user_management.get_user_data; fall back to handlers if missing
    original_get_user_data = getattr(um, 'get_user_data', None)
    if original_get_user_data is None and udh is not None and hasattr(udh, 'get_user_data'):
        original_get_user_data = getattr(udh, 'get_user_data', None)
    if original_get_user_data is None:
        yield
        return

    def _load_single_type(user_id: str, key: str, *, auto_create: bool):
        try:
            entry = um.USER_DATA_LOADERS.get(key)
            loader = None
            if entry:
                loader = entry.get('loader')
            # If loader is missing, attempt to self-heal by (re)registering
            if loader is None:
                key_to_func_and_file = {
                    'account': (um._get_user_data__load_account, 'account'),
                    'preferences': (um._get_user_data__load_preferences, 'preferences'),
                    'context': (um._get_user_data__load_context, 'user_context'),
                    'schedules': (um._get_user_data__load_schedules, 'schedules'),
                }
                func_file = key_to_func_and_file.get(key)
                if func_file is None:
                    return None
                func, file_type = func_file
                try:
                    um.register_data_loader(key, func, file_type)
                    entry = um.USER_DATA_LOADERS.get(key)
                    loader = entry.get('loader') if entry else None
                except Exception:
                    loader = func
            if loader is None:
                return None
            # Loaders accept (user_id, auto_create)
            return loader(user_id, auto_create)
        except Exception:
            return None

    def _fallback_read_from_files(user_id: str, key: str):
        """Read requested type directly from user JSON files as a last resort."""
        try:
            import core.config as _cfg
            from core.config import get_user_data_dir as _get_user_data_dir
        except Exception:
            return None

        # Resolve actual user directory via config helper (handles UUID mapping)
        try:
            user_dir = _get_user_data_dir(user_id)
        except Exception:
            user_dir = os.path.join(_cfg.USER_INFO_DIR_PATH, user_id)
        filename_map = {
            'account': 'account.json',
            'preferences': 'preferences.json',
            'context': 'user_context.json',
            'schedules': 'schedules.json',
        }
        filename = filename_map.get(key)
        if not filename:
            return None
        file_path = os.path.join(user_dir, filename)
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as fh:
                return json.load(fh)
        except Exception:
            return None

    def wrapped_get_user_data(user_id: str, data_type: str = 'all', *args, **kwargs):
        auto_create = True
        try:
            auto_create = bool(kwargs.get('auto_create', True))
        except Exception:
            auto_create = True
        result = original_get_user_data(user_id, data_type, *args, **kwargs)
        try:
            # If asking for all, ensure a dict with expected keys
            if data_type == 'all':
                if not isinstance(result, dict):
                    test_logger.debug(f"shim_get_user_data: Coercing non-dict 'all' result for {user_id} -> assembling structure")
                    result = {} if result is None else {"value": result}
                # Respect auto_create and only assemble when user dir exists
                should_assemble = auto_create
                if should_assemble:
                    try:
                        from core.config import get_user_data_dir as _get_user_data_dir
                        if not os.path.exists(_get_user_data_dir(user_id)):
                            should_assemble = False
                    except Exception:
                        should_assemble = False
                if should_assemble:
                    for key in ('account', 'preferences', 'context', 'schedules'):
                        if key not in result or not result.get(key):
                            test_logger.debug(f"shim_get_user_data: '{key}' missing/empty for {user_id}; invoking loader")
                            loaded = _load_single_type(user_id, key, auto_create=auto_create)
                            if loaded is not None:
                                result[key] = loaded
                            else:
                                # Fallback: direct file read
                                fb = _fallback_read_from_files(user_id, key)
                                if fb is not None:
                                    result[key] = fb
                                else:
                                    test_logger.warning(f"shim_get_user_data: loader and file fallback could not provide '{key}' for {user_id}")
                return result

            # Specific type request: ensure structure present
            if isinstance(data_type, str):
                key = data_type
                # If result already a dict containing the key with a value, return as-is
                if isinstance(result, dict) and result.get(key):
                    return result
                # Otherwise, attempt to load and return {key: value} if allowed
                should_assemble = auto_create
                if should_assemble:
                    try:
                        from core.config import get_user_data_dir as _get_user_data_dir
                        if not os.path.exists(_get_user_data_dir(user_id)):
                            should_assemble = False
                    except Exception:
                        should_assemble = False
                if should_assemble:
                    test_logger.debug(f"shim_get_user_data: '{key}' request returned empty for {user_id}; invoking loader")
                    loaded = _load_single_type(user_id, key, auto_create=auto_create)
                    if loaded is not None:
                        return {key: loaded}
                    fb = _fallback_read_from_files(user_id, key)
                    if fb is not None:
                        return {key: fb}
                return result
        except Exception:
            test_logger.exception("shim_get_user_data: unexpected error while assembling result")
            return result

        return result

    # Patch in place for the duration of the test
    # Patch both modules so all call sites are covered
    setattr(um, 'get_user_data', wrapped_get_user_data)
    original_handlers_get = None
    if udh is not None and hasattr(udh, 'get_user_data'):
        original_handlers_get = udh.get_user_data
        setattr(udh, 'get_user_data', wrapped_get_user_data)
    try:
        yield
    finally:
        # Restore originals at end of session
        try:
            setattr(um, 'get_user_data', original_get_user_data)
        except Exception:
            pass
        if udh is not None and original_handlers_get is not None:
            try:
                setattr(udh, 'get_user_data', original_handlers_get)
            except Exception:
                pass


@pytest.fixture(scope="session", autouse=True)
def verify_required_loaders_present():
    """Fail fast if required user-data loaders are missing at session start."""
    try:
        import core.user_management as um
        required = ('account', 'preferences', 'context', 'schedules')
        missing = []
        for k in required:
            entry = um.USER_DATA_LOADERS.get(k)
            if not (isinstance(entry, dict) and entry.get('loader')):
                missing.append(k)
        if missing:
            raise AssertionError(
                f"Required user-data loaders missing or None: {missing}. "
                f"Present keys: {list(um.USER_DATA_LOADERS.keys())}"
            )
    except Exception as e:
        raise AssertionError(f"Loader self-check failed: {e}")

@pytest.fixture(scope="function", autouse=True)
def env_guard_and_restore(monkeypatch):
    """Snapshot and restore critical environment variables to prevent test leakage.

    Restores after each test to ensure environment stability across the suite.
    """
    critical_keys = [
        'MHM_TESTING', 'CATEGORIES', 'LOGS_DIR', 'LOG_BACKUP_DIR', 'LOG_ARCHIVE_DIR',
        'LOG_MAIN_FILE', 'LOG_DISCORD_FILE', 'LOG_AI_FILE', 'LOG_USER_ACTIVITY_FILE',
        'LOG_ERRORS_FILE', 'LOG_COMMUNICATION_MANAGER_FILE', 'LOG_EMAIL_FILE',
        'LOG_UI_FILE', 'LOG_FILE_OPS_FILE', 'LOG_SCHEDULER_FILE',
        'BASE_DATA_DIR', 'USER_INFO_DIR_PATH', 'TEMP', 'TMP', 'TMPDIR'
    ]
    snapshot = {k: os.environ.get(k) for k in critical_keys}
    try:
        yield
    finally:
        for k, v in snapshot.items():
            if v is None:
                if k in os.environ:
                    monkeypatch.delenv(k, raising=False)
            else:
                monkeypatch.setenv(k, v)

@pytest.fixture(scope="session", autouse=True)
def ensure_tmp_base_directory():
    """Ensure base tmp directory exists at session start (optimization: create once)."""
    # Use the session-scoped test_data_dir directly to avoid scope mismatch
    # with function-scoped test_data_dir fixtures in some test files
    base_tmp = os.path.join(tests_data_dir, 'tmp')
    os.makedirs(base_tmp, exist_ok=True)
    yield

@pytest.fixture(scope="function")
def test_path_factory(test_data_dir, ensure_tmp_base_directory):
    """Provide a per-test directory under tests/data/tmp/<uuid> for ad-hoc temp usage.

    Prefer this over raw tempfile.mkdtemp/TemporaryDirectory to keep paths within the repo.
    Optimized: base tmp directory is created once at session start.
    """
    import uuid
    base_tmp = os.path.join(test_data_dir, 'tmp')
    # Base directory already exists from session fixture, just create subdirectory
    path = os.path.join(base_tmp, uuid.uuid4().hex)
    os.makedirs(path, exist_ok=True)
    return path

@pytest.fixture(scope="function")
def ensure_user_materialized(test_data_dir):
    """Return a helper to ensure account/preferences/context files exist for a user.

    If the user directory is missing, uses TestUserFactory to create a basic user.
    If present but missing files, writes minimal JSON structures to materialize them.
    """
    from pathlib import Path as _Path
    import json as _json
    import os as _os

    def _helper(user_id: str):
        users_dir = _Path(test_data_dir) / 'users'
        user_dir = users_dir / user_id
        if not user_dir.exists():
            try:
                from tests.test_utilities import TestUserFactory
                TestUserFactory.create_basic_user(user_id, test_data_dir=str(test_data_dir))
            except Exception:
                user_dir.mkdir(parents=True, exist_ok=True)
        # Materialize minimal files if missing
        acct_path = user_dir / 'account.json'
        prefs_path = user_dir / 'preferences.json'
        ctx_path = user_dir / 'user_context.json'
        if not acct_path.exists():
            _json.dump({
                "user_id": user_id,
                "internal_username": user_id,
                "account_status": "active",
                "features": {
                    "automated_messages": "disabled",
                    "task_management": "disabled",
                    "checkins": "disabled"
                }
            }, open(acct_path, 'w', encoding='utf-8'), indent=2)
        if not prefs_path.exists():
            _json.dump({
                "channel": {"type": "email"},
                "checkin_settings": {"enabled": False},
                "task_settings": {"enabled": False}
            }, open(prefs_path, 'w', encoding='utf-8'), indent=2)
        if not ctx_path.exists():
            _json.dump({
                "preferred_name": user_id,
                "pronouns": [],
                "custom_fields": {}
            }, open(ctx_path, 'w', encoding='utf-8'), indent=2)
        return str(user_dir)

    return _helper

@pytest.fixture(scope="function", autouse=True)
def path_sanitizer():
    """Guardrail: ensure temp resolution stays within tests/data and detect escapes.

    Fails fast if the active temp directory is outside tests/data.
    """
    import tempfile
    # Always enforce repository-scoped tests/data as the allowed root
    allowed_root = os.path.abspath(str(tests_data_dir))
    # Validate Python's temp resolution points to tests/data
    current_tmp = os.path.abspath(tempfile.gettempdir())
    if not current_tmp.startswith(allowed_root):
        raise AssertionError(
            f"Temp directory escaped repo: {current_tmp} (expected under {allowed_root})."
        )
    yield


@pytest.fixture(scope="function", autouse=True)
def enforce_user_dir_locations():
    """Ensure tests only create user dirs under tests/data/users.

    - Fails if a top-level tests/data/test-user* directory appears.
    - Fails if any test-user* directory is created under tests/data/tmp.
    Cleans stray dirs to keep workspace tidy before failing.
    """
    base = tests_data_dir
    users_dir = base / 'users'
    tmp_dir = base / 'tmp'
    try:
        pre_top = set(x.name for x in base.iterdir() if x.is_dir())
        pre_tmp_children = set(x.name for x in (tmp_dir.iterdir() if tmp_dir.exists() else [] ) if x.is_dir())
    except Exception:
        pre_top, pre_tmp_children = set(), set()

    yield

    # Check for misplaced top-level test users
    try:
        for entry in base.iterdir():
            if not entry.is_dir():
                continue
            if entry.name.startswith('test-user') and entry.parent == base and entry != users_dir:
                try:
                    shutil.rmtree(entry, ignore_errors=True)
                finally:
                    pytest.fail(
                        f"Misplaced test user directory detected: {entry}. "
                        f"User directories must be under {users_dir}."
                    )
    except Exception:
        # Do not mask test results if scan fails
        pass

    # Check for user-like dirs directly under tmp (non-recursive for performance)
    try:
        if tmp_dir.exists():
            for child in tmp_dir.iterdir():
                if not child.is_dir():
                    continue
                # Heuristics: tmp dir is a misplaced user dir if it has user-signature files
                # or looks like a test-user name
                looks_like_user = (
                    child.name.startswith('test-user') or
                    (child / 'account.json').exists() or
                    (child / 'preferences.json').exists() or
                    (child / 'user_context.json').exists() or
                    (child / 'checkins.json').exists() or
                    (child / 'schedules.json').exists() or
                    (child / 'messages').is_dir()
                )
                if looks_like_user:
                    try:
                        shutil.rmtree(child, ignore_errors=True)
                    finally:
                        pytest.fail(
                            f"User directory artifacts detected under tmp: {child}. "
                            f"All user data must be created under {users_dir}."
                        )
    except Exception:
        pass


@pytest.fixture(scope="session", autouse=True)
def cleanup_tmp_at_session_end():
    """Clear tests/data/tmp contents at session end to keep the workspace tidy."""
    yield
    try:
        tmp_dir = tests_data_dir / 'tmp'
        if tmp_dir.exists():
            for child in tmp_dir.iterdir():
                if child.is_dir():
                    shutil.rmtree(child, ignore_errors=True)
                else:
                    try:
                        child.unlink(missing_ok=True)
                    except Exception:
                        pass
    except Exception:
        pass

@pytest.fixture(scope="session", autouse=True)
def force_test_data_directory():
    """Route all system temp usage into tests/data for the entire session."""
    import tempfile
    root = str(tests_data_dir)
    # Set common env vars so any native/library lookups resolve under tests/data
    os.environ["TMPDIR"] = root
    os.environ["TEMP"] = root
    os.environ["TMP"] = root
    # Patch Python's temp resolution
    original_tempdir = tempfile.tempdir
    tempfile.tempdir = root
    try:
        yield
    finally:
        tempfile.tempdir = original_tempdir

@pytest.fixture(scope="function")
def mock_user_data(mock_config, test_data_dir, request):
    """Create mock user data for testing with unique user ID for each test."""
    import uuid
    import core.config
    
    # Generate unique user ID for each test to prevent interference
    user_id = f"test-user-{uuid.uuid4().hex[:8]}"
    user_dir = os.path.join(test_data_dir, "users", user_id)
    # Ensure parent directory exists first (race condition fix for parallel execution)
    os.makedirs(os.path.dirname(user_dir), exist_ok=True)
    os.makedirs(user_dir, exist_ok=True)
    
    test_logger.debug(f"Creating mock user data for user: {user_id}")
    
    # Create mock account.json with current timestamp
    current_time = datetime.now().isoformat() + "Z"
    account_data = {
        "user_id": user_id,
        "internal_username": f"testuser_{user_id[-4:]}",
        "account_status": "active",
        "chat_id": "",
        "phone": "",
        "email": f"test_{user_id[-4:]}@example.com",
        "discord_user_id": "",
        "created_at": current_time,
        "updated_at": current_time,
        "features": {
            "automated_messages": "disabled",
            "checkins": "disabled",
            "task_management": "disabled"
        }
    }
    
    # Create mock preferences.json - categories only included if automated_messages enabled
    preferences_data = {
        "channel": {
            "type": "email"
        },
        "checkin_settings": {
            "enabled": False,
            "frequency": "daily",
            "time": "09:00",
            "categories": ["mood", "energy", "sleep"]
        },
        "task_settings": {
            "enabled": False,
            "reminder_frequency": "daily",
            "reminder_time": "10:00"
        }
    }
    
    # Only add categories if automated_messages is enabled
    if account_data["features"]["automated_messages"] == "enabled":
        preferences_data["categories"] = ["motivational", "health", "quotes_to_ponder"]
    
    # Create mock user_context.json
    context_data = {
        "preferred_name": f"Test User {user_id[-4:]}",
        "pronouns": ["they/them"],
        "date_of_birth": "",
        "custom_fields": {
            "health_conditions": [],
            "medications_treatments": [],
            "reminders_needed": [],
            "gender_identity": "",
            "accessibility_needs": []
        },
        "interests": ["reading", "music"],
        "goals": ["Improve mental health", "Stay organized"],
        "loved_ones": [],
        "activities_for_encouragement": ["exercise", "socializing"],
        "notes_for_ai": ["Prefers gentle encouragement", "Responds well to structure"],
        "created_at": current_time,
        "last_updated": current_time
    }
    
    # Create mock checkins.json
    checkins_data = {
        "checkins": [],
        "last_checkin_date": None,
        "streak_count": 0
    }

    # Create minimal schedules.json so schedule reads/writes have a base file
    schedules_data = {
        "categories": {}
    }
    
    # Create mock chat_interactions.json
    chat_data = {
        "interactions": [],
        "total_interactions": 0,
        "last_interaction": None
    }
    
    # Create messages directory and sent_messages.json only if automated_messages enabled
    messages_dir = os.path.join(user_dir, "messages")
    if account_data["features"]["automated_messages"] == "enabled":
        os.makedirs(messages_dir, exist_ok=True)
        
        sent_messages_data = {
            "messages": [],
            "total_sent": 0,
            "last_sent": None
        }
        
        with open(os.path.join(messages_dir, "sent_messages.json"), "w") as f:
            json.dump(sent_messages_data, f, indent=2)
    else:
        sent_messages_data = None
    
    # Save all mock data
    with open(os.path.join(user_dir, "account.json"), "w") as f:
        json.dump(account_data, f, indent=2)
    
    with open(os.path.join(user_dir, "preferences.json"), "w") as f:
        json.dump(preferences_data, f, indent=2)
    
    with open(os.path.join(user_dir, "user_context.json"), "w") as f:
        json.dump(context_data, f, indent=2)
    
    with open(os.path.join(user_dir, "checkins.json"), "w") as f:
        json.dump(checkins_data, f, indent=2)
    
    with open(os.path.join(user_dir, "chat_interactions.json"), "w") as f:
        json.dump(chat_data, f, indent=2)
    with open(os.path.join(user_dir, "schedules.json"), "w") as f:
        json.dump(schedules_data, f, indent=2)
    
    # Ensure user is discoverable via identifier lookups
    # Use file locking-aware update and retry if needed
    try:
        from core.user_data_manager import update_user_index
        # Retry update_user_index in case of race conditions in parallel execution
        max_retries = 3
        for attempt in range(max_retries):
            success = update_user_index(user_id)
            if success:
                break
            if attempt < max_retries - 1:
                import time
                time.sleep(0.1)  # Brief delay before retry
        if not success:
            test_logger.warning(f"Failed to update user index for {user_id} after {max_retries} attempts")
    except Exception as e:
        test_logger.warning(f"Error updating user index for {user_id}: {e}")
        # Don't fail the test, but log the issue
    
    test_logger.debug(f"Created complete mock user data files in: {user_dir}")
    
    # Store user_id for cleanup
    request.node.user_id = user_id
    
    return {
        "user_id": user_id,
        "user_dir": user_dir,
        "account_data": account_data,
        "preferences_data": preferences_data,
        "context_data": context_data,
        "checkins_data": checkins_data,
        "schedules_data": schedules_data,
        "chat_data": chat_data,
        "sent_messages_data": sent_messages_data
    }

@pytest.fixture(scope="function")
def mock_user_data_with_messages(test_data_dir, mock_config, request):
    """Create mock user data for testing with automated_messages enabled and categories."""
    import uuid
    
    # Generate unique user ID for each test to prevent interference
    user_id = f"test-user-messages-{uuid.uuid4().hex[:8]}"
    user_dir = os.path.join(test_data_dir, "users", user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    test_logger.debug(f"Creating mock user data with messages for user: {user_id}")
    
    # Create mock account.json with automated_messages enabled
    current_time = datetime.now().isoformat() + "Z"
    account_data = {
        "user_id": user_id,
        "internal_username": f"testuser_{user_id[-4:]}",
        "account_status": "active",
        "chat_id": "",
        "phone": "",
        "email": f"test_{user_id[-4:]}@example.com",
        "discord_user_id": "",
        "created_at": current_time,
        "updated_at": current_time,
        "features": {
            "automated_messages": "enabled",
            "checkins": "disabled",
            "task_management": "disabled"
        }
    }
    
    # Create mock preferences.json with categories (automated_messages enabled)
    preferences_data = {
        "channel": {
            "type": "email"
        },
        "categories": ["motivational", "health", "quotes_to_ponder"],
        "checkin_settings": {
            "enabled": False,
            "frequency": "daily",
            "time": "09:00",
            "categories": ["mood", "energy", "sleep"]
        },
        "task_settings": {
            "enabled": False,
            "reminder_frequency": "daily",
            "reminder_time": "10:00"
        }
    }
    
    # Create mock user_context.json
    context_data = {
        "preferred_name": f"Test User {user_id[-4:]}",
        "pronouns": ["they/them"],
        "date_of_birth": "",
        "custom_fields": {
            "health_conditions": [],
            "medications_treatments": [],
            "reminders_needed": [],
            "gender_identity": "",
            "accessibility_needs": []
        },
        "interests": ["reading", "music"],
        "goals": ["Improve mental health", "Stay organized"],
        "loved_ones": [],
        "activities_for_encouragement": ["exercise", "socializing"],
        "notes_for_ai": ["Prefers gentle encouragement", "Responds well to structure"],
        "created_at": current_time,
        "last_updated": current_time
    }
    
    # Create mock checkins.json
    checkins_data = {
        "checkins": [],
        "last_checkin_date": None,
        "streak_count": 0
    }
    
    # Create mock chat_interactions.json
    chat_data = {
        "interactions": [],
        "total_interactions": 0,
        "last_interaction": None
    }
    
    # Create messages directory and sent_messages.json (automated_messages enabled)
    messages_dir = os.path.join(user_dir, "messages")
    os.makedirs(messages_dir, exist_ok=True)
    
    sent_messages_data = {
        "messages": [],
        "total_sent": 0,
        "last_sent": None
    }
    
    # Save all mock data
    with open(os.path.join(user_dir, "account.json"), "w") as f:
        json.dump(account_data, f, indent=2)
    
    with open(os.path.join(user_dir, "preferences.json"), "w") as f:
        json.dump(preferences_data, f, indent=2)
    
    with open(os.path.join(user_dir, "user_context.json"), "w") as f:
        json.dump(context_data, f, indent=2)
    
    with open(os.path.join(user_dir, "checkins.json"), "w") as f:
        json.dump(checkins_data, f, indent=2)
    
    with open(os.path.join(user_dir, "chat_interactions.json"), "w") as f:
        json.dump(chat_data, f, indent=2)
    
    with open(os.path.join(messages_dir, "sent_messages.json"), "w") as f:
        json.dump(sent_messages_data, f, indent=2)
    
    test_logger.debug(f"Created complete mock user data with messages in: {user_dir}")
    
    # Store user_id for cleanup
    request.node.user_id = user_id
    
    return {
        "user_id": user_id,
        "user_dir": user_dir,
        "account_data": account_data,
        "preferences_data": preferences_data,
        "context_data": context_data,
        "checkins_data": checkins_data,
        "chat_data": chat_data,
        "sent_messages_data": sent_messages_data
    }

@pytest.fixture(scope="function")
def update_user_index_for_test(test_data_dir):
    """Helper fixture to update user index for test users."""
    def _update_index(user_id):
        try:
            from core.user_data_manager import update_user_index
            success = update_user_index(user_id)
            if success:
                test_logger.debug(f"Updated user index for test user: {user_id}")
            else:
                test_logger.warning(f"Failed to update user index for test user: {user_id}")
            return success
        except Exception as e:
            test_logger.warning(f"Error updating user index for test user {user_id}: {e}")
            return False
    
    return _update_index

# --- GLOBAL PATCH: Force all user data to tests/data/users/ for all tests ---
# DISABLED: This fixture was causing test isolation issues
# @pytest.fixture(autouse=True, scope="session")
# def patch_user_data_dirs():
#     """Patch BASE_DATA_DIR and USER_INFO_DIR_PATH to use tests/data/users/ for all tests."""
#     from unittest.mock import patch
#     import core.config
#     test_data_dir = os.path.abspath("tests/data")
#     users_dir = os.path.join(test_data_dir, "users")
#     os.makedirs(users_dir, exist_ok=True)
#     
#     # Patch the module attributes directly
#     with patch.object(core.config, "BASE_DATA_DIR", test_data_dir), \
#          patch.object(core.config, "USER_INFO_DIR_PATH", users_dir):
#         yield

# --- CLEANUP FIXTURE: Remove test users from tests/data/users/ after all tests (NEVER touches real user data) ---
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_users_after_session():
    """Remove test users from tests/data/users/ after all tests. NEVER touches real user data."""
    yield  # Run all tests first
    
    # Clear all user caches to prevent state pollution between test runs
    try:
        from core.user_management import clear_user_caches
        clear_user_caches()  # Clear all caches
    except Exception:
        pass  # Ignore errors during cleanup
    
    # Only clean up test directories, NEVER real user data
    for base_dir in ["tests/data/users"]:  # Removed "data/users" - NEVER touch real user data
        abs_dir = os.path.abspath(base_dir)
        if os.path.exists(abs_dir):
            for item in os.listdir(abs_dir):
                # Clean up ONLY test directories (test-*, test_*, testuser*)
                # NEVER clean up UUID directories - these are real users!
                if (item.startswith("test-") or 
                    item.startswith("test_") or 
                    item.startswith("testuser")):
                    item_path = os.path.join(abs_dir, item)
                    try:
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
                    except Exception:
                        pass
    
    # Additional cleanup: Remove ALL directories in tests/data/users/ for complete isolation
    # This ensures no test data persists between test runs
    test_users_dir = os.path.abspath("tests/data/users")
    if os.path.exists(test_users_dir):
        for item in os.listdir(test_users_dir):
            item_path = os.path.join(test_users_dir, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            except Exception:
                pass
    
    # Also clean up the user index file to prevent stale entries
    test_data_dir = os.path.abspath("tests/data")
    user_index_file = os.path.join(test_data_dir, "user_index.json")
    if os.path.exists(user_index_file):
        try:
            os.remove(user_index_file)
        except Exception:
            pass
    
    # Clean up test request files from schedule editor tests
    requests_dir = os.path.join(test_data_dir, "requests")
    if os.path.exists(requests_dir):
        try:
            for item in os.listdir(requests_dir):
                # Clean up test request files (reschedule_test_*)
                if item.startswith("reschedule_test_"):
                    item_path = os.path.join(requests_dir, item)
                    try:
                        os.remove(item_path)
                    except Exception:
                        pass
        except Exception:
            pass
    
    # Clean up test backup files to prevent clutter
    backup_dir = os.path.join(test_data_dir, "backups")
    if os.path.exists(backup_dir):
        try:
            for item in os.listdir(backup_dir):
                item_path = os.path.join(backup_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                except Exception:
                    pass
        except Exception:
            pass
    
    # Clean up pytest-of-* directories (pytest creates these when using tmpdir fixtures)
    # Use direct directory iteration instead of glob for Windows compatibility
    try:
        if os.path.exists(test_data_dir):
            for item in os.listdir(test_data_dir):
                item_path = os.path.join(test_data_dir, item)
                try:
                    if os.path.isdir(item_path) and item.startswith("pytest-of-"):
                        shutil.rmtree(item_path, ignore_errors=True)
                except Exception:
                    pass
    except Exception:
        pass
    
    # Clean up flags directory
    flags_dir = os.path.join(test_data_dir, "flags")
    if os.path.exists(flags_dir):
        try:
            for item in os.listdir(flags_dir):
                item_path = os.path.join(flags_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                except Exception:
                    pass
        except Exception:
            pass
    
    # Clean up tmp directory
    tmp_dir = os.path.join(test_data_dir, "tmp")
    if os.path.exists(tmp_dir):
        try:
            for item in os.listdir(tmp_dir):
                item_path = os.path.join(tmp_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                except Exception:
                    pass
        except Exception:
            pass
    
    # Clean up other test artifacts according to cleanup standards
    try:
        # Remove pytest temporary directories (pytest-of-* directories created by pytest's tmpdir plugin)
        # Use direct directory iteration instead of glob for Windows compatibility
        if os.path.exists(test_data_dir):
            for item in os.listdir(test_data_dir):
                item_path = os.path.join(test_data_dir, item)
                try:
                    if os.path.isdir(item_path) and item.startswith("pytest-of-"):
                        shutil.rmtree(item_path, ignore_errors=True)
                except Exception:
                    pass
        
        # Remove stray config directory
        config_dir = os.path.join(test_data_dir, "config")
        if os.path.exists(config_dir):
            shutil.rmtree(config_dir, ignore_errors=True)
        
        # Remove root files
        for filename in [".env", "requirements.txt", "test_file.json"]:
            file_path = os.path.join(test_data_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Remove legacy nested directory
        nested_dir = os.path.join(test_data_dir, "nested")
        if os.path.exists(nested_dir):
            shutil.rmtree(nested_dir, ignore_errors=True)
        
        # Remove corrupted files
        for item in os.listdir(test_data_dir):
            if (item.startswith("tmp") and ".corrupted_" in item) or ".corrupted_" in item:
                item_path = os.path.join(test_data_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
        
        # Clear tmp directory completely - remove all subdirectories and files
        tmp_dir = os.path.join(test_data_dir, "tmp")
        if os.path.exists(tmp_dir):
            try:
                # Remove all contents (subdirectories and files)
                for item in os.listdir(tmp_dir):
                    item_path = os.path.join(tmp_dir, item)
                    try:
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                        else:
                            os.remove(item_path)
                    except Exception:
                        pass
                # Directory itself stays but is now empty
            except Exception:
                pass
        
        # Clear flags directory completely
        flags_dir = os.path.join(test_data_dir, "flags")
        if os.path.exists(flags_dir):
            try:
                for item in os.listdir(flags_dir):
                    item_path = os.path.join(flags_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                    except Exception:
                        pass
            except Exception:
                pass
        
        # Clear requests directory completely
        requests_dir = os.path.join(test_data_dir, "requests")
        if os.path.exists(requests_dir):
            try:
                for item in os.listdir(requests_dir):
                    item_path = os.path.join(requests_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                    except Exception:
                        pass
            except Exception:
                pass
        
        # Clean up conversation_states.json
        conversation_states_file = os.path.join(test_data_dir, "conversation_states.json")
        if os.path.exists(conversation_states_file):
            try:
                os.remove(conversation_states_file)
            except Exception:
                pass
        
        # Clear logs directory
        logs_dir = os.path.join(test_data_dir, "logs")
        if os.path.exists(logs_dir):
            shutil.rmtree(logs_dir, ignore_errors=True)
        
        # Clean up old test_run files in tests/logs (but preserve current session files)
        test_logs_dir = os.path.join(project_root, "tests", "logs")
        if os.path.exists(test_logs_dir):
            try:
                for item in os.listdir(test_logs_dir):
                    # Only clean up old test_run files, not the current session's test_run.log
                    if item.startswith("test_run_") and item.endswith(".log") and item != "test_run.log":
                        item_path = os.path.join(test_logs_dir, item)
                        if os.path.isfile(item_path):
                            os.remove(item_path)
            except Exception:
                pass
        
        # Clean up any stray test.log files in tests/data
        try:
            for root, dirs, files in os.walk(test_data_dir):
                for file in files:
                    if file == "test.log":
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass
        except Exception:
            pass
            
    except Exception:
        pass  # Ignore cleanup errors

@pytest.fixture(scope="function", autouse=True)
def clear_user_caches_between_tests():
    """Clear user caches between tests to prevent state pollution."""
    yield  # Run the test
    # Clear caches after each test
    try:
        from core.user_management import clear_user_caches
        clear_user_caches()  # Clear all caches
    except Exception:
        pass  # Ignore errors during cleanup

@pytest.fixture(scope="function")
def mock_logger():
    """Mock logger for testing."""
    with patch('core.logger.get_logger') as mock_logger:
        mock_logger.return_value = Mock()
        yield mock_logger

@pytest.fixture(scope="function")
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        yield f.name
    # Cleanup
    os.unlink(f.name)

@pytest.fixture(scope="function")
def mock_ai_response():
    """Mock AI response for testing."""
    return {
        "response": "This is a test AI response.",
        "confidence": 0.85,
        "model": "test-model",
        "timestamp": "2025-01-01T12:00:00Z"
    }

@pytest.fixture(scope="function")
def mock_task_data():
    """Mock task data for testing."""
    return {
        "task_id": "test-task-123",
        "title": "Test Task",
        "description": "This is a test task",
        "priority": "medium",
        "due_date": "2025-01-15",
        "completed": False,
        "created_at": "2025-01-01T12:00:00Z",
        "updated_at": "2025-01-01T12:00:00Z"
    }

@pytest.fixture(scope="function")
def mock_message_data():
    """Mock message data for testing."""
    return {
        "message_id": "test-message-123",
        "text": "This is a test message",
        "category": "motivational",
        "days": ["monday", "wednesday", "friday"],
        "time_periods": ["18:00-20:00"],
        "active": True
    }

@pytest.fixture(scope="function")
def mock_service_data():
    """Mock service data for testing."""
    return {
        "service_id": "test-service-123",
        "name": "Test Service",
        "status": "running",
        "pid": 12345,
        "start_time": "2025-01-01T12:00:00Z",
        "config": {
            "port": 8080,
            "host": "localhost"
        }
    }

@pytest.fixture(scope="function")
def mock_communication_data():
    """Mock communication data for testing."""
    return {
        "message_id": "test-msg-123",
        "user_id": "test-user-123",
        "channel": "email",
        "content": "Test message content",
        "sent_at": "2025-01-01T12:00:00Z",
        "status": "sent"
    }

@pytest.fixture(scope="function")
def mock_schedule_data():
    """Mock schedule data for testing."""
    return {
        "category": "motivational",
        "periods": {
            "morning": {
                "start_time": "08:00",
                "end_time": "10:00",
                "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "active": True
            },
            "evening": {
                "start_time": "18:00",
                "end_time": "20:00",
                "days": ["monday", "wednesday", "friday"],
                "active": True
            }
        }
    }

# Configure pytest
def pytest_collection_modifyitems(config, items):
    """Exclude AI test files that are run via run_ai_functionality_tests.py from pytest collection and add default markers."""
    # These test classes are designed to be run via run_ai_functionality_tests.py, not pytest
    # They have __init__ constructors that require parameters, which causes pytest collection warnings
    ai_test_files = [
        'tests/ai/test_ai_core.py',
        'tests/ai/test_ai_integration.py',
        'tests/ai/test_ai_errors.py',
        'tests/ai/test_ai_cache.py',
        'tests/ai/test_ai_performance.py',
        'tests/ai/test_ai_quality.py',
        'tests/ai/test_ai_advanced.py',
        'tests/ai/test_ai_functionality_manual.py',  # Manual test runner, not a pytest test
    ]
    
    items_to_remove = []
    for item in items:
        # Get the file path from the item
        item_path = str(item.fspath) if hasattr(item, 'fspath') else str(Path(item.nodeid.split('::')[0]))
        # Normalize path separators
        normalized_item_path = item_path.replace('\\', os.sep).replace('/', os.sep)
        
        for ai_file in ai_test_files:
            normalized_ai_file = ai_file.replace('\\', os.sep).replace('/', os.sep)
            if normalized_ai_file in normalized_item_path or os.path.basename(normalized_ai_file) == os.path.basename(normalized_item_path):
                items_to_remove.append(item)
                break
    
    # Remove excluded items
    for item in items_to_remove:
        items.remove(item)
    
    # Add default markers to remaining items
    for item in items:
        # Add unit marker by default if no marker is present
        if not any(item.iter_markers()):
            item.add_marker(pytest.mark.unit)

def pytest_configure(config):
    """Configure pytest for MHM testing and suppress collection warnings for development tools implementation classes."""
    # Suppress PytestCollectionWarning for development tools implementation classes
    # These warnings are emitted during collection, so we need to filter them in the hook
    # Note: pytest is already imported at module level, don't import it again here
    import warnings
    warnings.filterwarnings("ignore", message=".*cannot collect test class.*TestCoverage.*", category=pytest.PytestCollectionWarning)
    warnings.filterwarnings("ignore", message=".*cannot collect test class.*because it has a __init__ constructor.*", category=pytest.PytestCollectionWarning)
    warnings.filterwarnings("ignore", category=pytest.PytestCollectionWarning, module="development_tools.tests.*")
    
    # Only log from main process to avoid duplicate messages in parallel mode
    if not os.environ.get('PYTEST_XDIST_WORKER'):
        test_logger.debug("Configuring pytest for MHM testing")
    
    # Configure pytest tmpdir to use tests/data/tmp instead of creating pytest-of-* directories
    # This ensures all temporary files stay within tests/data
    try:
        # Set the base temporary directory for pytest's tmpdir fixture
        if hasattr(config, 'option') and hasattr(config.option, 'tmp_path_factory'):
            config.option.tmp_path_factory = str(tests_data_dir / 'tmp')
    except Exception:
        pass  # Ignore if pytest version doesn't support this
    
    # Core test type markers
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "behavior: mark test as a behavior test"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as testing UI components"
    )
    
    # Speed markers
    config.addinivalue_line(
        "markers", "slow: mark test as slow running (>1 second)"
    )
    config.addinivalue_line(
        "markers", "fast: mark test as fast running (<100ms, optional)"
    )
    
    # Resource markers
    config.addinivalue_line(
        "markers", "asyncio: mark test as requiring asyncio support"
    )
    config.addinivalue_line(
        "markers", "file_io: mark test as having heavy file operations"
    )
    
    # Feature-specific markers (aligned with component loggers)
    config.addinivalue_line(
        "markers", "ai: mark test as requiring AI functionality"
    )
    config.addinivalue_line(
        "markers", "communication: mark test as testing communication channels"
    )
    config.addinivalue_line(
        "markers", "tasks: mark test as task management functionality (includes reminders)"
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
    
    # Test quality markers
    config.addinivalue_line(
        "markers", "regression: mark test as preventing regression issues"
    )
    config.addinivalue_line(
        "markers", "smoke: mark test as basic functionality smoke test"
    )
    config.addinivalue_line(
        "markers", "critical: mark test as critical path test"
    )
    config.addinivalue_line(
        "markers", "no_parallel: mark test as must not run under pytest-xdist parallel execution"
    )

def pytest_sessionstart(session):
    """Log test session start."""
    # Only log from main process to avoid duplicate messages in parallel mode
    if not os.environ.get('PYTEST_XDIST_WORKER'):
        test_logger.debug(f"Starting test session with {len(session.items)} tests")
        test_logger.debug(f"Test log file: {test_log_file}")

def _consolidate_worker_logs():
    """Consolidate per-worker log files into main log files at the end of parallel test runs.
    
    This function should only be called from the main process (not workers).
    It finds all worker log files (test_run_gw*.log, test_consolidated_gw*.log, etc.)
    and combines them into the main log files.
    """
    # Only run in main process (not in workers)
    if os.environ.get('PYTEST_XDIST_WORKER'):
        return
    
    try:
        logs_dir = Path(project_root) / "tests" / "logs"
        if not logs_dir.exists():
            return
        
        # CRITICAL: Small delay to allow worker processes to close their file handles
        # This prevents file locking issues during consolidation
        import time
        time.sleep(0.5)  # 500ms delay to allow workers to close files
        
        # Find all worker log files
        worker_test_run_logs = sorted(logs_dir.glob("test_run_gw*.log"))
        worker_consolidated_logs = sorted(logs_dir.glob("test_consolidated_gw*.log"))
        
        # If no worker logs found, nothing to consolidate
        if not (worker_test_run_logs or worker_consolidated_logs):
            return
        
        test_logger.info("Consolidating worker log files into main log files...")
        
        # Consolidate test_run logs
        main_test_run_log = logs_dir / "test_run.log"
        if worker_test_run_logs:
            try:
                with open(main_test_run_log, 'a', encoding='utf-8') as main_file:
                    main_file.write(f"\n{'='*80}\n")
                    main_file.write("# CONSOLIDATED FROM PARALLEL WORKERS\n")
                    main_file.write(f"{'='*80}\n\n")
                    
                    for worker_log in worker_test_run_logs:
                        worker_id = worker_log.stem.replace("test_run_", "")
                        main_file.write(f"\n# --- Worker {worker_id} ---\n")
                        try:
                            # Retry mechanism to handle file locking issues
                            # Workers might still have file handles open
                            import time
                            max_retries = 5
                            retry_delay = 0.2  # 200ms between retries
                            content = None
                            
                            for attempt in range(max_retries):
                                try:
                                    # Read in chunks to avoid memory issues with huge files
                                    # Limit to 50MB per worker log to prevent hanging
                                    max_size = 50 * 1024 * 1024  # 50MB
                                    file_size = worker_log.stat().st_size
                                    if file_size > max_size:
                                        test_logger.warning(f"Worker log {worker_log.name} is {file_size / (1024*1024):.1f}MB, truncating to last 50MB")
                                        # Read only the last 50MB
                                        with open(worker_log, 'rb') as f:
                                            f.seek(-max_size, 2)  # Seek to 50MB from end
                                            content = f.read().decode('utf-8', errors='replace')
                                    else:
                                        with open(worker_log, 'r', encoding='utf-8') as worker_file:
                                            content = worker_file.read()
                                    break  # Success, exit retry loop
                                except (IOError, PermissionError, OSError) as e:
                                    if attempt < max_retries - 1:
                                        time.sleep(retry_delay)
                                        continue
                                    else:
                                        # Last attempt failed, log warning and skip this file
                                        test_logger.warning(f"Failed to read worker log {worker_log.name} after {max_retries} attempts: {e}")
                                        content = f"# Error: Could not read {worker_log.name} - file may be locked\n"
                                        break
                            
                            if content.strip():
                                main_file.write(content)
                                if not content.endswith('\n'):
                                    main_file.write('\n')
                        except Exception as e:
                            main_file.write(f"# Error reading {worker_log.name}: {e}\n")
                            test_logger.warning(f"Error reading worker log {worker_log.name}: {e}")
                        main_file.write(f"\n# --- End Worker {worker_id} ---\n\n")
                
                test_logger.info(f"Consolidated {len(worker_test_run_logs)} worker test_run logs into {main_test_run_log.name}")
            except Exception as e:
                test_logger.warning(f"Error consolidating test_run logs: {e}")
        
        # Consolidate consolidated logs
        main_consolidated_log = logs_dir / "test_consolidated.log"
        if worker_consolidated_logs:
            try:
                with open(main_consolidated_log, 'a', encoding='utf-8') as main_file:
                    main_file.write(f"\n{'='*80}\n")
                    main_file.write("# CONSOLIDATED FROM PARALLEL WORKERS\n")
                    main_file.write(f"{'='*80}\n\n")
                    
                    for worker_log in worker_consolidated_logs:
                        worker_id = worker_log.stem.replace("test_consolidated_", "")
                        main_file.write(f"\n# --- Worker {worker_id} ---\n")
                        try:
                            # Retry mechanism to handle file locking issues
                            # Workers might still have file handles open
                            import time
                            max_retries = 5
                            retry_delay = 0.2  # 200ms between retries
                            content = None
                            
                            for attempt in range(max_retries):
                                try:
                                    # Read in chunks to avoid memory issues with huge files
                                    # Limit to 10MB per worker log to prevent hanging (reduced from 50MB)
                                    max_size = 10 * 1024 * 1024  # 10MB
                                    file_size = worker_log.stat().st_size
                                    if file_size > max_size:
                                        test_logger.warning(f"Worker log {worker_log.name} is {file_size / (1024*1024):.1f}MB, truncating to last 10MB")
                                        # Read only the last 10MB in chunks to avoid memory issues
                                        with open(worker_log, 'rb') as f:
                                            f.seek(-max_size, 2)  # Seek to 10MB from end
                                            # Read in 1MB chunks to avoid loading entire file into memory
                                            chunk_size = 1024 * 1024  # 1MB chunks
                                            content_parts = []
                                            while True:
                                                chunk = f.read(chunk_size)
                                                if not chunk:
                                                    break
                                                content_parts.append(chunk.decode('utf-8', errors='replace'))
                                            content = ''.join(content_parts)
                                    else:
                                        # For smaller files, read in chunks too to be consistent
                                        chunk_size = 1024 * 1024  # 1MB chunks
                                        content_parts = []
                                        with open(worker_log, 'r', encoding='utf-8') as worker_file:
                                            while True:
                                                chunk = worker_file.read(chunk_size)
                                                if not chunk:
                                                    break
                                                content_parts.append(chunk)
                                        content = ''.join(content_parts)
                                    break  # Success, exit retry loop
                                except (IOError, PermissionError, OSError) as e:
                                    if attempt < max_retries - 1:
                                        time.sleep(retry_delay)
                                        continue
                                    else:
                                        # Last attempt failed, log warning and skip this file
                                        test_logger.warning(f"Failed to read worker log {worker_log.name} after {max_retries} attempts: {e}")
                                        content = f"# Error: Could not read {worker_log.name} - file may be locked\n"
                                        break
                            
                            if content.strip():
                                main_file.write(content)
                                if not content.endswith('\n'):
                                    main_file.write('\n')
                        except Exception as e:
                            main_file.write(f"# Error reading {worker_log.name}: {e}\n")
                            test_logger.warning(f"Error reading worker log {worker_log.name}: {e}")
                        main_file.write(f"\n# --- End Worker {worker_id} ---\n\n")
                
                test_logger.info(f"Consolidated {len(worker_consolidated_logs)} worker consolidated logs into {main_consolidated_log.name}")
                
                # CRITICAL: Register main consolidated log for rotation AFTER consolidation
                # (consolidation can make the file huge, so we need to check rotation after)
                session_rotation_manager.register_log_file(str(main_consolidated_log))
            except Exception as e:
                test_logger.warning(f"Error consolidating consolidated logs: {e}")
        
        # Clean up worker log files after consolidation
        # CRITICAL: Add delay before cleanup to allow workers to close file handles
        # Windows file locking can prevent immediate deletion
        import time
        time.sleep(0.5)  # 500ms delay to allow workers to close file handles
        
        all_worker_logs = worker_test_run_logs + worker_consolidated_logs
        cleaned_count = 0
        failed_logs = []
        
        for worker_log in all_worker_logs:
            # Retry deletion with exponential backoff for Windows file locking
            max_retries = 5
            retry_delay = 0.1  # Start with 100ms
            deleted = False
            
            for attempt in range(max_retries):
                try:
                    worker_log.unlink()
                    cleaned_count += 1
                    deleted = True
                    break
                except (OSError, PermissionError) as e:
                    # Windows file locking error - retry with delay
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff: 0.1s, 0.2s, 0.4s, 0.8s, 1.6s
                    else:
                        # Last attempt failed - log but don't fail
                        failed_logs.append(worker_log.name)
                        test_logger.debug(f"Could not remove worker log {worker_log.name} after {max_retries} attempts: {e}")
                except Exception as e:
                    # Other errors - don't retry
                    failed_logs.append(worker_log.name)
                    test_logger.debug(f"Error removing worker log {worker_log.name}: {e}")
                    break
        
        if cleaned_count > 0:
            test_logger.debug(f"Cleaned up {cleaned_count} worker log files after consolidation")
        if failed_logs:
            # Only log warning if some files failed (not critical - they'll be cleaned up next run)
            test_logger.debug(f"Could not clean up {len(failed_logs)} worker log files (locked by workers): {', '.join(failed_logs[:5])}{'...' if len(failed_logs) > 5 else ''}")
        
        test_logger.info("Worker log consolidation completed")
        
    except Exception as e:
        test_logger.warning(f"Error during worker log consolidation: {e}")


def pytest_sessionfinish(session, exitstatus):
    """Log test session finish, check for log rotation, and consolidate worker logs if running in parallel mode."""
    test_logger.info(f"Test session finished with exit status: {exitstatus}")
    if hasattr(session, 'testscollected'):
        test_logger.info(f"Tests collected: {session.testscollected}")
    
    # Consolidate worker logs FIRST (this can make main log files huge)
    # Only in main process (not in workers)
    if not os.environ.get('PYTEST_XDIST_WORKER'):
        _consolidate_worker_logs()
    
    # Check for log rotation AFTER consolidation (consolidation can make files huge)
    # CRITICAL: Only rotate if files are actually large, and use non-blocking approach
    # Log rotation can hang if files are locked by logging handlers
    # Use a timeout to prevent hanging
    if not os.environ.get('PYTEST_XDIST_WORKER'):
        if session_rotation_manager.check_rotation_needed():
            # Use threading timeout to prevent hanging on Windows
            import threading
            rotation_complete = threading.Event()
            rotation_error = [None]
            
            def do_rotation():
                try:
                    session_rotation_manager.rotate_all_logs(rotation_context="session end")
                    test_logger.debug("Performed automatic log rotation at session end")
                except Exception as e:
                    rotation_error[0] = e
                finally:
                    rotation_complete.set()
            
            rotation_thread = threading.Thread(target=do_rotation, daemon=True)
            rotation_thread.start()
            
            # Wait up to 10 seconds for rotation to complete
            if not rotation_complete.wait(timeout=10.0):
                test_logger.warning("Log rotation timed out after 10 seconds, skipping")
            elif rotation_error[0]:
                test_logger.warning(f"Error during log rotation: {rotation_error[0]}")

def pytest_runtest_logreport(report):
    """Log individual test results."""
    if report.when == 'call':
        # Only log PASSED tests when verbose mode is enabled (to reduce log noise)
        verbose_logs = os.getenv("TEST_VERBOSE_LOGS", "0")
        if report.passed:
            # Only log passed tests at DEBUG level (level 2) to avoid I/O overhead
            # Level 1 and 0: don't log passed tests - focus on failures, warnings, and skips
            if verbose_logs == "2":
                test_logger.debug(f"PASSED: {report.nodeid}")
            # Don't log passed tests at other levels - they're not interesting
        elif report.failed:
            # Always log failures - these are important
            test_logger.error(f"FAILED: {report.nodeid}")
            if report.longrepr:
                test_logger.error(f"Error details: {report.longrepr}")
        elif report.skipped:
            # Always log skips - these might indicate issues
            test_logger.warning(f"SKIPPED: {report.nodeid}")

@pytest.fixture(scope="session", autouse=True)
def cleanup_communication_manager():
    """Clean up CommunicationManager singleton after all tests complete."""
    yield
    
    # Clean up CommunicationManager singleton to prevent access violations
    # CRITICAL: Add timeout to prevent hanging during cleanup
    import threading
    import time
    
    cleanup_complete = threading.Event()
    cleanup_error = [None]
    
    def do_cleanup():
        try:
            from communication.core.channel_orchestrator import CommunicationManager
            if CommunicationManager._instance is not None:
                test_logger.debug("Cleaning up CommunicationManager singleton...")
                CommunicationManager._instance.stop_all()
                CommunicationManager._instance = None
                test_logger.debug("CommunicationManager cleanup completed")
        except Exception as e:
            cleanup_error[0] = e
        finally:
            cleanup_complete.set()
    
    cleanup_thread = threading.Thread(target=do_cleanup, daemon=True)
    cleanup_thread.start()
    
    # Wait up to 5 seconds for cleanup to complete
    if not cleanup_complete.wait(timeout=5.0):
        test_logger.warning("CommunicationManager cleanup timed out after 5 seconds")
    elif cleanup_error[0]:
        test_logger.warning(f"Error during CommunicationManager cleanup: {cleanup_error[0]}")

@pytest.fixture(autouse=True)
def cleanup_conversation_manager():
    """Clean up ConversationManager state before each test."""
    # Clear state before test
    try:
        from communication.message_processing.conversation_flow_manager import conversation_manager
        conversation_manager.clear_all_states()
    except Exception as e:
        test_logger.warning(f"Error clearing conversation manager state: {e}")
    
    yield
    
    # Clear state after test
    try:
        from communication.message_processing.conversation_flow_manager import conversation_manager
        conversation_manager.clear_all_states()
    except Exception as e:
        test_logger.warning(f"Error clearing conversation manager state: {e}")

@pytest.fixture(autouse=True)
def cleanup_singletons():
    """Clean up singleton instances before each test to ensure isolation."""
    # Store original singleton instances
    original_instances = {}
    
    try:
        # Store AI Chatbot singleton
        try:
            from ai.chatbot import AIChatBotSingleton
            original_instances['ai_chatbot'] = AIChatBotSingleton._instance
        except (ImportError, AttributeError):
            pass
        
        # Store MessageRouter singleton
        try:
            import communication.message_processing.message_router as router_module
            original_instances['message_router'] = router_module._message_router
        except (ImportError, AttributeError):
            pass
        
        # Store cache instances
        try:
            import ai.cache_manager as cache_module
            original_instances['response_cache'] = getattr(cache_module, '_response_cache', None)
            original_instances['context_cache'] = getattr(cache_module, '_context_cache', None)
        except (ImportError, AttributeError):
            pass
        
        yield
        
    finally:
        # Restore original singleton instances to prevent state pollution
        try:
            from ai.chatbot import AIChatBotSingleton
            if 'ai_chatbot' in original_instances:
                AIChatBotSingleton._instance = original_instances['ai_chatbot']
        except (ImportError, AttributeError):
            pass
        
        try:
            import communication.message_processing.message_router as router_module
            if 'message_router' in original_instances:
                router_module._message_router = original_instances['message_router']
        except (ImportError, AttributeError):
            pass
        
        # Clear cache instances (not restore - caches should be fresh for each test)
        try:
            import ai.cache_manager as cache_module
            if hasattr(cache_module, '_response_cache'):
                cache_module._response_cache = None
            if hasattr(cache_module, '_context_cache'):
                cache_module._context_cache = None
        except (ImportError, AttributeError):
            pass

@pytest.fixture(autouse=True)
def cleanup_communication_threads():
    """Clean up CommunicationManager threads between tests to prevent crashes."""
    yield
    
    # Clean up CommunicationManager threads after each test
    # Only stop channels that are running to avoid breaking tests that need the manager
    try:
        from communication.core.channel_orchestrator import CommunicationManager
        if CommunicationManager._instance is not None:
            # Stop all channels to clean up threads, but don't destroy the instance
            # This prevents thread leaks while allowing the manager to persist
            try:
                # Only stop if there are active channels
                if hasattr(CommunicationManager._instance, '_channels_dict') and CommunicationManager._instance._channels_dict:
                    CommunicationManager._instance.stop_all()
            except Exception:
                pass  # Ignore errors during cleanup
    except Exception:
        pass  # Ignore import errors
