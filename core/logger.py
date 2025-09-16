# logger.py

import logging
import os
import shutil
import re
import time
import json
import gzip
import sys
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

def _is_testing_environment():
    """Check if we're running in a testing environment."""
    return (os.getenv('MHM_TESTING') == '1' or 
            os.getenv('PYTEST_CURRENT_TEST') is not None or
            'pytest' in os.getenv('PYTHONPATH', '') or
            any('test' in arg.lower() for arg in os.sys.argv if arg.startswith('-')))


class TestContextFormatter(logging.Formatter):
    """Custom formatter that automatically prepends test names to log messages."""
    
    def format(self, record):
        # Get test name from pytest's environment variable
        test_name = os.environ.get('PYTEST_CURRENT_TEST', '')
        if test_name:
            # Extract just the test function name from the full test path
            test_name = test_name.split('::')[-1] if '::' in test_name else test_name
            # Only add test context if it's not already there (avoid duplication)
            if not str(record.msg).startswith(f"[{test_name}]"):
                record.msg = f"[{test_name}] {record.msg}"
        # If no test context available, don't add anything (this is normal during setup)
        
        return super().format(record)


def apply_test_context_formatter_to_all_loggers():
    """Apply TestContextFormatter to all existing loggers when in test mode."""
    if not _is_testing_environment():
        return
    
    test_formatter = TestContextFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Apply to all existing loggers
    count = 0
    for logger_name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers:
            if isinstance(handler, (RotatingFileHandler, TimedRotatingFileHandler)):
                handler.setFormatter(test_formatter)
                count += 1
    
    # Debug: Print to stderr so we can see if this function is being called
    if count > 0:
        print(f"DEBUG: Applied TestContextFormatter to {count} handlers", file=sys.stderr)

def _get_log_paths_for_environment():
    """Get appropriate log paths based on the current environment."""
    if _is_testing_environment():
        # Use test-specific paths
        base_dir = os.getenv('LOGS_DIR', 'tests/logs')
        backup_dir = os.path.join(base_dir, 'backups')
        archive_dir = os.path.join(base_dir, 'archive')
        
        # Allow override of main file via environment variable in tests
        main_file = os.getenv('LOG_MAIN_FILE', os.path.join(base_dir, 'app.log'))

        return {
            'base_dir': base_dir,
            'backup_dir': backup_dir,
            'archive_dir': archive_dir,
            'main_file': main_file,
            'discord_file': os.path.join(base_dir, 'discord.log'),
            'ai_file': os.path.join(base_dir, 'ai.log'),
            'user_activity_file': os.path.join(base_dir, 'user_activity.log'),
            'errors_file': os.path.join(base_dir, 'errors.log'),
            'communication_manager_file': os.path.join(base_dir, 'communication_manager.log'),
            'email_file': os.path.join(base_dir, 'email.log'),
            'ui_file': os.path.join(base_dir, 'ui.log'),
            'file_ops_file': os.path.join(base_dir, 'file_ops.log'),
            'scheduler_file': os.path.join(base_dir, 'scheduler.log'),
            # Additional component loggers used in the codebase
            'schedule_utilities_file': os.path.join(base_dir, 'schedule_utilities.log'),
            'analytics_file': os.path.join(base_dir, 'analytics.log'),
            'message_file': os.path.join(base_dir, 'message.log'),
            'backup_file': os.path.join(base_dir, 'backup.log'),
            'checkin_dynamic_file': os.path.join(base_dir, 'checkin_dynamic.log'),
        }
    else:
        # Use centralized paths from config - import locally to avoid circular import
        import core.config as config
        return {
            'base_dir': config.LOGS_DIR,
            'backup_dir': config.LOG_BACKUP_DIR,
            'archive_dir': config.LOG_ARCHIVE_DIR,
            'main_file': config.LOG_MAIN_FILE,
            'discord_file': config.LOG_DISCORD_FILE,
            'ai_file': config.LOG_AI_FILE,
            'user_activity_file': config.LOG_USER_ACTIVITY_FILE,
            'errors_file': config.LOG_ERRORS_FILE,
            'communication_manager_file': config.LOG_COMMUNICATION_MANAGER_FILE,
            'email_file': config.LOG_EMAIL_FILE,
            'ui_file': config.LOG_UI_FILE,
            'file_ops_file': config.LOG_FILE_OPS_FILE,
            'scheduler_file': config.LOG_SCHEDULER_FILE,
            # Additional component loggers used in the codebase
            'schedule_utilities_file': os.path.join(config.LOGS_DIR, 'schedule_utilities.log'),
            'analytics_file': os.path.join(config.LOGS_DIR, 'analytics.log'),
            'message_file': os.path.join(config.LOGS_DIR, 'message.log'),
            'backup_file': os.path.join(config.LOGS_DIR, 'backup.log'),
            'checkin_dynamic_file': os.path.join(config.LOGS_DIR, 'checkin_dynamic.log'),
        }

# FAILSAFE: If running tests, forcibly remove all handlers from root logger and main logger
# This ensures test logs never go to app.log, even if logging setup is triggered early
if os.getenv('MHM_TESTING') == '1':
    # Remove all handlers from root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)
    
    # Remove all handlers from main logger (this module)
    main_logger = logging.getLogger(__name__)
    for handler in main_logger.handlers[:]:
        handler.close()
        main_logger.removeHandler(handler)
    
    # Clear any cached handlers
    root_logger.handlers.clear()
    main_logger.handlers.clear()
    
    # Set propagate to False to prevent test logs from bubbling up
    root_logger.propagate = False
    main_logger.propagate = False


class ComponentLogger:
    """
    Component-specific logger that writes to dedicated log files.
    
    Each component gets its own log file with appropriate rotation and formatting.
    """
    
    def __init__(self, component_name: str, log_file_path: str, level: int = logging.INFO):
        self.component_name = component_name
        self.log_file_path = log_file_path
        self.level = level
        
        # Create logger for this component
        self.logger = logging.getLogger(f"mhm.{component_name}")
        # Default to INFO (or provided level), but allow specific components to override below
        self.logger.setLevel(level)
        
        # Ensure no duplicate handlers
        self.logger.handlers.clear()
        # Prevent propagation to root so component logs don't appear in app.log
        self.logger.propagate = False
        
        # Create formatter with component name
        # Use TestContextFormatter in test mode, regular formatter otherwise
        if _is_testing_environment():
            formatter = TestContextFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # Get environment-specific log paths
        log_paths = _get_log_paths_for_environment()
        
        # Create file handler with rotation to backup directory
        file_handler = BackupDirectoryRotatingFileHandler(
            log_file_path,
            backup_dir=log_paths['backup_dir'],
            when='midnight',
            interval=1,
            backupCount=7,  # Keep 7 days of logs
            encoding='utf-8'
        )
        
        # Set up daily rotation
        file_handler.suffix = "%Y-%m-%d"
        file_handler.namer = lambda name: name.replace(".log", "") + ".log"
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        
        # Add main component file handler
        self.logger.addHandler(file_handler)

        # Also add a dedicated errors handler so ERROR/CRITICAL messages go to errors log
        try:
            errors_formatter = formatter
            # In test verbose mode, route errors to tests/logs as well to avoid writing to real logs
            errors_log_path = log_paths['errors_file']
            if os.getenv('MHM_TESTING') == '1' and os.getenv('TEST_VERBOSE_LOGS') == '1':
                # Use configurable test logs directory
                tests_logs_dir = log_paths['base_dir'] or os.getenv('TEST_LOGS_DIR', os.path.join('tests', 'logs'))
                try:
                    os.makedirs(tests_logs_dir, exist_ok=True)
                    errors_log_path = os.path.join(tests_logs_dir, os.path.basename(log_paths['errors_file']))
                except Exception:
                    pass
            errors_backup_dir = log_paths['backup_dir']
            if os.getenv('MHM_TESTING') == '1' and os.getenv('TEST_VERBOSE_LOGS') == '1':
                # Use configurable test logs directory
                tests_logs_dir = log_paths['base_dir'] or os.getenv('TEST_LOGS_DIR', os.path.join('tests', 'logs'))
                errors_backup_dir = os.path.join(tests_logs_dir, 'backups')
                try:
                    os.makedirs(errors_backup_dir, exist_ok=True)
                except Exception:
                    pass

            errors_handler = BackupDirectoryRotatingFileHandler(
                errors_log_path,
                backup_dir=errors_backup_dir,
                when='midnight',
                interval=1,
                backupCount=7,
                encoding='utf-8'
            )
            errors_handler.suffix = "%Y-%m-%d"
            errors_handler.namer = lambda name: name.replace(".log", "") + ".log"
            errors_handler.setFormatter(errors_formatter)
            errors_handler.setLevel(logging.ERROR)
            self.logger.addHandler(errors_handler)
        except Exception:
            # Failsafe: don't break logging if errors handler can't be added
            pass
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional structured data."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional structured data."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional structured data."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional structured data."""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with optional structured data."""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method with structured data support."""
        if kwargs:
            # Add structured data to message
            structured_data = json.dumps(kwargs, default=str)
            full_message = f"{message} | {structured_data}"
        else:
            full_message = message
        
        self.logger.log(level, full_message)


class BackupDirectoryRotatingFileHandler(TimedRotatingFileHandler):
    """
    Custom rotating file handler that moves rotated files to a backup directory.
    """
    
    def __init__(self, filename, backup_dir, maxBytes=0, backupCount=0, encoding=None, delay=False, when='midnight', interval=1):
        # TimedRotatingFileHandler expects: filename, when='h', interval=1, backupCount=0, encoding=None, delay=False, utc=False, atTime=None
        super().__init__(filename, when=when, interval=interval, backupCount=backupCount, encoding=encoding, delay=delay)
        self.backup_dir = backup_dir
        self.base_filename = filename
        
        # Ensure backup directory exists (even during tests, as tests may need it)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def doRollover(self):
        """
        Do a rollover, as described in __init__().
        """
        # Skip rollover if disabled (e.g., during tests)
        if os.environ.get('DISABLE_LOG_ROTATION') == '1':
            return
        
        # Close the current stream
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # Get the rollover filename from parent class
        current_time = int(time.time())
        dst_time = self.rolloverAt - self.interval
        time_tuple = time.localtime(dst_time)
        dfn = self.rotation_filename(self.baseFilename + "." + time.strftime(self.suffix, time_tuple))
        
        # Try to handle the rollover with Windows-safe logic
        if os.path.exists(self.baseFilename):
            backup_name = f"{os.path.basename(self.baseFilename)}.{time.strftime(self.suffix, time_tuple)}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Windows-safe file move with retry logic
            try:
                # Try to rename the file (this is what the parent class would do)
                if os.path.exists(dfn):
                    os.unlink(dfn)  # Remove existing rollover file if it exists
                os.rename(self.baseFilename, dfn)
                
                # Now move to backup directory
                try:
                    shutil.move(dfn, backup_path)
                except (PermissionError, OSError) as move_error:
                    # If move to backup fails, at least we have the rotated file
                    print(f"Warning: Could not move rotated log to backup directory: {move_error}")
                    
            except PermissionError as e:
                # File is locked, try alternative approach
                try:
                    # Try to copy the file instead of moving it
                    shutil.copy2(self.baseFilename, backup_path)
                    # Don't try to delete the original - let it be overwritten
                    print(f"Info: Copied log file to backup (original file is locked): {backup_path}")
                except (PermissionError, OSError) as copy_error:
                    # Even copy failed, skip rollover for this time
                    print(f"Warning: Could not backup log file {self.baseFilename}: {copy_error}")
                    # Reopen the current file and continue
                    self.stream = self._open()
                    return
            except Exception as e:
                # Any other error, log it but continue
                print(f"Warning: Error during log rollover: {e}")
                # Reopen the current file and continue
                self.stream = self._open()
                return
        
        # Call parent's doRollover to handle the actual rollover logic
        # But only if we successfully handled the file movement above
        try:
            super().doRollover()
        except Exception as e:
            # If parent rollover fails, at least reopen the current file
            print(f"Warning: Parent rollover failed: {e}")
            self.stream = self._open()


class HeartbeatWarningFilter(logging.Filter):
    """
    Filter to suppress excessive Discord heartbeat warnings while keeping track of them.
    
    - Allows first 3 heartbeat warnings to pass through
    - Suppresses subsequent warnings for 10 minutes
    - Logs a summary every hour with total count
    """
    
    def __init__(self):
        super().__init__()
        self.heartbeat_warnings = 0
        self.last_warning_time = 0
        self.last_summary_time = 0
        self.suppression_start_time = 0
        self.is_suppressing = False
        
    def filter(self, record):
        # Check if this is a Discord heartbeat warning
        if (record.name == 'discord.gateway' and 
            record.levelno == logging.WARNING and
            'heartbeat blocked' in record.getMessage()):
            
            current_time = time.time()
            self.heartbeat_warnings += 1
            
            # Allow first 3 warnings to pass through
            if self.heartbeat_warnings <= 3:
                self.last_warning_time = current_time
                return True
            
            # Start suppression after 3rd warning
            if not self.is_suppressing:
                self.is_suppressing = True
                self.suppression_start_time = current_time
                # Log that we're starting suppression
                record.msg = f"Discord heartbeat warnings detected - suppressing further warnings for 10 minutes (total: {self.heartbeat_warnings})"
                return True
            
            # Check if suppression period has ended (10 minutes)
            if current_time - self.suppression_start_time > 600:  # 10 minutes
                self.is_suppressing = False
                self.heartbeat_warnings = 0
                # Allow this warning through to restart the cycle
                return True
            
            # Log summary every hour
            if current_time - self.last_summary_time > 3600:  # 1 hour
                self.last_summary_time = current_time
                record.msg = f"Discord heartbeat warnings suppressed - {self.heartbeat_warnings} total warnings in the last hour"
                return True
            
            # Suppress this warning
            return False
        
        # Allow all non-heartbeat messages through
        return True


class ExcludeLoggerNamesFilter(logging.Filter):
    """
    Filter to exclude records for specific logger name prefixes.
    Example use: prevent Discord-related logs from going to app.log.
    """
    def __init__(self, excluded_prefixes: list[str]):
        super().__init__()
        self.excluded_prefixes = excluded_prefixes or []

    def filter(self, record: logging.LogRecord) -> bool:
        name = record.name or ""
        for prefix in self.excluded_prefixes:
            if name.startswith(prefix):
                return False
        return True


# Global variable to track current verbosity mode
_verbose_mode = False
_original_levels = {}

# Component loggers
_component_loggers = {}


def get_log_level_from_env():
    """
    Get log level from environment variable, default to WARNING for quiet mode.
    
    Returns:
        int: Logging level constant (e.g., logging.WARNING, logging.DEBUG)
    """
    log_level = os.getenv('LOG_LEVEL', 'WARNING').upper()
    return getattr(logging, log_level, logging.WARNING)


def ensure_logs_directory():
    """Ensure the logs directory structure exists."""
    log_paths = _get_log_paths_for_environment()
    os.makedirs(log_paths['base_dir'], exist_ok=True)
    os.makedirs(log_paths['backup_dir'], exist_ok=True)
    os.makedirs(log_paths['archive_dir'], exist_ok=True)


def get_component_logger(component_name: str) -> ComponentLogger:
    """
    Get or create a component-specific logger.
    
    Args:
        component_name: Name of the component (e.g., 'discord', 'ai', 'user_activity')
    
    Returns:
        ComponentLogger: Logger for the specified component
    """
    # Testing mode: optionally enable verbose per-component logs under tests/logs
    if os.getenv('MHM_TESTING') == '1':
        if os.getenv('TEST_VERBOSE_LOGS') == '1':
            try:
                # Use configurable test logs directory
                tests_logs_dir = os.getenv('LOGS_DIR') or os.getenv('TEST_LOGS_DIR', os.path.join('tests', 'logs'))
                os.makedirs(tests_logs_dir, exist_ok=True)
            except Exception:
                pass
            # In verbose test mode, continue and create real component loggers that write under tests/logs
        else:
            # Default for tests: no-op logger for clean test output
            class _DummyLogger:
                def __init__(self, name: str):
                    self.name = name
            class DummyComponentLogger:
                def __init__(self, name: str):
                    self.component_name = name
                    self.logger = _DummyLogger(f"mhm.{name}")
                def debug(self, message: str, **kwargs): pass
                def info(self, message: str, **kwargs): pass
                def warning(self, message: str, **kwargs): pass
                def error(self, message: str, **kwargs): pass
                def critical(self, message: str, **kwargs): pass
            return DummyComponentLogger(component_name)
    
    # Enforce canonical component names (channels -> communication_manager was migrated)
    if component_name == 'channels':
        component_name = 'communication_manager'

    if component_name not in _component_loggers:
        # Get environment-specific log paths
        log_paths = _get_log_paths_for_environment()
        
        # Map component names to log file paths
        log_file_map = {
            'discord': log_paths['discord_file'],
            'ai': log_paths['ai_file'],
            'user_activity': log_paths['user_activity_file'],
            'errors': log_paths['errors_file'],
            'communication_manager': log_paths['communication_manager_file'],
            'email': log_paths['email_file'],
            'ui': log_paths['ui_file'],
            'file_ops': log_paths['file_ops_file'],
            'scheduler': log_paths['scheduler_file'],
            'main': log_paths['main_file'],
            # Additional component loggers used in the codebase
            'schedule_utilities': log_paths['schedule_utilities_file'],
            'analytics': log_paths['analytics_file'],
            'message': log_paths['message_file'],
            'backup': log_paths['backup_file'],
            'checkin_dynamic': log_paths['checkin_dynamic_file']
        }
        
        log_file = log_file_map.get(component_name, log_paths['main_file'])
        # Create the component logger
        comp_logger = ComponentLogger(component_name, log_file)
        # For Discord, increase verbosity to DEBUG so we capture more detail in discord.log
        if component_name == 'discord':
            try:
                comp_logger.logger.setLevel(logging.DEBUG)
                # Ensure only the primary component file handler logs DEBUG, not the errors handler
                for handler in comp_logger.logger.handlers:
                    if isinstance(handler, (RotatingFileHandler, TimedRotatingFileHandler)):
                        base_filename = getattr(handler, 'baseFilename', '')
                        log_paths = _get_log_paths_for_environment()
                        if base_filename and os.path.basename(base_filename) == os.path.basename(log_paths['discord_file']):
                            handler.setLevel(logging.DEBUG)
            except Exception:
                pass
        _component_loggers[component_name] = comp_logger
    
    return _component_loggers[component_name]


def setup_logging():
    """
    Set up logging with file and console handlers. Ensure it is called only once.
    
    Creates a dual-handler logging system:
    - File handler: Always logs at DEBUG level with rotation
    - Console handler: Respects verbosity settings (WARNING by default)
    
    Automatically suppresses noisy third-party library logging.
    """
    # Skip logging setup if running tests - tests handle their own logging
    if _is_testing_environment():
        return
    
    # Get environment-specific log paths
    log_paths = _get_log_paths_for_environment()
    
    # Ensure logs directory exists
    ensure_logs_directory()
    
    root_logger = logging.getLogger()
    
    # Check if logging is already set up properly
    if root_logger.hasHandlers():
        # Logging already set up, just return
        return
    
    # Get log level from environment
    log_level = get_log_level_from_env()
    
    # Create formatter with component name
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Set up file handler with UTF-8 encoding (always DEBUG) for app.log
    import core.config as config
    file_handler = BackupDirectoryRotatingFileHandler(
        log_paths['main_file'],
        log_paths['backup_dir'],
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG)

    # Set up console handler (respects current verbosity setting)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(log_level)

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.DEBUG)  # Root logger captures all levels

    # Set up dedicated error handler for third-party library errors
    setup_third_party_error_logging()

    # Suppress noisy third-party logging
    suppress_noisy_logging()
    
    # Log successful setup
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Console level: {logging.getLevelName(log_level)}, File level: DEBUG")
    logger.info("Use LOG_LEVEL environment variable or toggle_verbose_logging() to change verbosity")


def setup_third_party_error_logging():
    """
    Set up dedicated error logging for third-party libraries.
    
    Routes ERROR and CRITICAL messages from asyncio, discord, and aiohttp
    to the errors.log file instead of app.log.
    """
    try:
        # Get environment-specific log paths
        log_paths = _get_log_paths_for_environment()
        
        # Create error formatter
        error_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        
        # Create error file handler
        import core.config as config
        error_handler = BackupDirectoryRotatingFileHandler(
            log_paths['errors_file'],
            log_paths['backup_dir'],
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        error_handler.setFormatter(error_formatter)
        error_handler.setLevel(logging.ERROR)  # Only ERROR and CRITICAL
        
        # Set up error logging for third-party libraries
        third_party_loggers = [
            "asyncio",
            "discord",
            "discord.client", 
            "discord.gateway",
            "aiohttp",
            "aiohttp.client",
            "aiohttp.connector"
        ]
        
        for logger_name in third_party_loggers:
            logger = logging.getLogger(logger_name)
            # Add error handler to route ERROR/CRITICAL to errors.log
            logger.addHandler(error_handler)
            # Set level to ERROR to capture only errors
            logger.setLevel(logging.ERROR)
            # Prevent propagation to root logger to avoid duplicates in app.log
            logger.propagate = False
            
    except Exception as e:
        # Failsafe: don't break logging if error handler setup fails
        logging.getLogger(__name__).warning(f"Failed to setup third-party error logging: {e}")


def get_logger(name):
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        logging.Logger: Configured logger
    """
    return logging.getLogger(name)


def suppress_noisy_logging():
    """
    Suppress excessive logging from third-party libraries.
    
    Sets logging level to WARNING for common noisy libraries to reduce log spam
    while keeping important warnings and errors visible.
    """
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    # Route discord library logs to the discord component logger only
    for discord_logger_name in ["discord", "discord.client", "discord.gateway"]:
        dl = logging.getLogger(discord_logger_name)
        dl.setLevel(logging.WARNING)
        dl.propagate = False
    
    # Apply heartbeat warning filter to Discord gateway logger
    try:
        discord_gateway_logger = logging.getLogger("discord.gateway")
        heartbeat_filter = HeartbeatWarningFilter()
        discord_gateway_logger.addFilter(heartbeat_filter)
    except Exception:
        pass
    
    # Suppress debug logging from schedule library to reduce "Running job" spam
    logging.getLogger("schedule").setLevel(logging.WARNING)


def set_console_log_level(level):
    """
    Set the console logging level while keeping file logging at DEBUG.
    
    Args:
        level: logging level (e.g., logging.DEBUG, logging.INFO, logging.WARNING)
    """
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
            handler.setLevel(level)
            logging.getLogger(__name__).info(
                "Console logging level set to: %s",
                logging.getLevelName(level),
            )
            break


def toggle_verbose_logging():
    """
    Toggle between verbose (DEBUG/INFO) and quiet (WARNING+) logging for console output.
    File logging always remains at DEBUG level.
    
    Returns:
        bool: True if verbose mode is now enabled, False if quiet mode
    """
    global _verbose_mode
    
    _verbose_mode = not _verbose_mode
    
    if _verbose_mode:
        # Enable verbose mode - show DEBUG and INFO
        set_console_log_level(logging.DEBUG)
        logging.getLogger(__name__).info(
            "Verbose logging enabled (DEBUG/INFO messages will be shown)"
        )
        return True
    else:
        # Enable quiet mode - show only WARNING and above
        set_console_log_level(logging.WARNING)
        logging.getLogger(__name__).info(
            "Quiet logging enabled (only WARNING/ERROR messages will be shown)"
        )
        return False


def get_verbose_mode():
    """
    Get current verbose mode status.
    
    Returns:
        bool: True if verbose mode is enabled
    """
    return _verbose_mode


def set_verbose_mode(enabled):
    """
    Explicitly set verbose mode.
    
    Args:
        enabled (bool): True to enable verbose mode, False for quiet mode
    """
    global _verbose_mode
    _verbose_mode = enabled
    
    if enabled:
        set_console_log_level(logging.DEBUG)
        logging.getLogger(__name__).info("Verbose logging enabled")
    else:
        set_console_log_level(logging.WARNING)
        logging.getLogger(__name__).info("Quiet logging enabled")


def disable_module_logging(module_name):
    """
    Disable debug logging for a specific module.
    
    Args:
        module_name: Name of the module to disable debug logging for
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.WARNING)
    for handler in logger.handlers:
        handler.setLevel(logging.WARNING)


def get_log_file_info():
    """
    Get information about current log files and their sizes.
    
    Returns:
        dict: Information about log files including total size and file count
    """
    try:
        import glob
        
        # Get environment-specific log paths
        log_paths = _get_log_paths_for_environment()
        
        # Get current log file
        current_log_size = 0
        current_log_info = None
        if os.path.exists(log_paths['main_file']):
            current_log_size = os.path.getsize(log_paths['main_file'])
            current_log_info = {
                'name': os.path.basename(log_paths['main_file']),
                'location': 'current',
                'size_bytes': current_log_size,
                'size_mb': round(current_log_size / (1024 * 1024), 2)
            }
        
        # Get backup log files
        backup_file_paths = []
        backup_file_info = []
        backup_total_size = 0
        if os.path.exists(log_paths['backup_dir']):
            backup_pattern = os.path.join(log_paths['backup_dir'], f"{os.path.basename(log_paths['main_file'])}*")
            backup_file_paths = glob.glob(backup_pattern)
            
            for backup_file in backup_file_paths:
                if os.path.exists(backup_file):
                    file_size = os.path.getsize(backup_file)
                    backup_total_size += file_size
                    backup_file_info.append({
                        'name': os.path.basename(backup_file),
                        'location': 'backup',
                        'size_bytes': file_size,
                        'size_mb': round(file_size / (1024 * 1024), 2)
                    })
        
        # Calculate total size
        total_size = current_log_size + backup_total_size
        
        # Calculate total files count
        total_files = 0
        if current_log_info:
            total_files += 1
        total_files += len(backup_file_info)
        
        return {
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'current_log': current_log_info,
            'backup_files': backup_file_info,
            'backup_directory': log_paths['backup_dir'],
            'total_files': total_files
        }
    except Exception as e:
        logging.getLogger(__name__).error(f"Error getting log file info: {e}")
        return None


def cleanup_old_logs(max_total_size_mb=50):
    """
    Clean up old log files if total size exceeds the limit.
    
    Args:
        max_total_size_mb (int): Maximum total size in MB before cleanup (default 50MB)
    
    Returns:
        bool: True if cleanup was performed, False otherwise
    """
    try:
        log_info = get_log_file_info()
        if not log_info:
            return False
            
        if log_info['total_size_mb'] <= max_total_size_mb:
            return False
            
        # Get all backup log files sorted by modification time (oldest first)
        import glob
        backup_files = []
        log_paths = _get_log_paths_for_environment()
        if os.path.exists(log_paths['backup_dir']):
            backup_pattern = os.path.join(log_paths['backup_dir'], f"{os.path.basename(log_paths['main_file'])}*")
            backup_files = glob.glob(backup_pattern)
        
        log_files_with_time = []
        
        for log_file in backup_files:
            if os.path.exists(log_file):
                mtime = os.path.getmtime(log_file)
                log_files_with_time.append((log_file, mtime))
        
        # Sort by modification time (oldest first)
        log_files_with_time.sort(key=lambda x: x[1])
        
        # Remove oldest files until we're under the limit
        removed_count = 0
        for log_file, _ in log_files_with_time:
            try:
                os.remove(log_file)
                removed_count += 1
                logging.getLogger(__name__).info(f"Removed old log file: {log_file}")
                
                # Check if we're under the limit now
                log_info = get_log_file_info()
                if log_info and log_info['total_size_mb'] <= max_total_size_mb:
                    break
                    
            except Exception as e:
                logging.getLogger(__name__).warning(f"Failed to remove log file {log_file}: {e}")
        
        if removed_count > 0:
            logging.getLogger(__name__).info(f"Log cleanup completed: removed {removed_count} files")
            return True
            
        return False
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error during log cleanup: {e}")
        return False


def compress_old_logs():
    """
    Compress log files older than 7 days and move them to archive directory.
    
    Returns:
        int: Number of files compressed and archived
    """
    try:
        import glob
        compressed_count = 0
        
        # Get environment-specific log paths
        log_paths = _get_log_paths_for_environment()
        
        # Get all log files in logs directory and backup directory
        log_patterns = [
            os.path.join(log_paths['base_dir'], "*.log.*"),  # Rotated log files
            os.path.join(log_paths['backup_dir'], "*.log*")  # Backup log files
        ]
        
        cutoff_time = time.time() - (7 * 24 * 3600)  # 7 days ago
        
        for pattern in log_patterns:
            if os.path.exists(os.path.dirname(pattern)):
                log_files = glob.glob(pattern)
                
                for log_file in log_files:
                    if os.path.exists(log_file):
                        mtime = os.path.getmtime(log_file)
                        
                        # Skip if already compressed or too recent
                        if log_file.endswith('.gz') or mtime > cutoff_time:
                            continue
                        
                        # Compress the file
                        try:
                            with open(log_file, 'rb') as f_in:
                                # Create archive filename
                                filename = os.path.basename(log_file)
                                archive_file = os.path.join(log_paths['archive_dir'], filename + '.gz')
                                
                                with gzip.open(archive_file, 'wb') as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                            
                            # Remove original file
                            os.remove(log_file)
                            compressed_count += 1
                            logging.getLogger(__name__).info(f"Compressed and archived: {log_file}")
                            
                        except Exception as e:
                            logging.getLogger(__name__).warning(f"Failed to compress {log_file}: {e}")
        
        if compressed_count > 0:
            logging.getLogger(__name__).info(f"Log archival completed: {compressed_count} files compressed and archived")
        
        return compressed_count
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error during log archival: {e}")
        return 0


def cleanup_old_archives(max_days=30):
    """
    Remove archived log files older than specified days.
    
    Args:
        max_days (int): Maximum age in days for archived files (default 30)
    
    Returns:
        int: Number of files removed
    """
    try:
        import glob
        removed_count = 0
        
        log_paths = _get_log_paths_for_environment()
        if os.path.exists(log_paths['archive_dir']):
            archive_pattern = os.path.join(log_paths['archive_dir'], "*.gz")
            archive_files = glob.glob(archive_pattern)
            
            cutoff_time = time.time() - (max_days * 24 * 3600)
            
            for archive_file in archive_files:
                if os.path.exists(archive_file):
                    mtime = os.path.getmtime(archive_file)
                    
                    if mtime < cutoff_time:
                        try:
                            os.remove(archive_file)
                            removed_count += 1
                            logging.getLogger(__name__).info(f"Removed old archive: {archive_file}")
                        except Exception as e:
                            logging.getLogger(__name__).warning(f"Failed to remove {archive_file}: {e}")
        
        if removed_count > 0:
            logging.getLogger(__name__).info(f"Archive cleanup completed: {removed_count} files removed")
        
        return removed_count
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error during archive cleanup: {e}")
        return 0


def force_restart_logging():
    """
    Force restart the logging system by clearing all handlers and reinitializing.
    
    Useful when logging configuration becomes corrupted or needs to be reset.
    
    Returns:
        bool: True if restart was successful, False otherwise
    """
    try:
        # Get the root logger
        root_logger = logging.getLogger()
        
        # Remove all existing handlers
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)
        
        # Clear any cached loggers
        logging.getLogger().handlers.clear()
        
        # Get environment-specific log paths
        log_paths = _get_log_paths_for_environment()
        
        # Force setup new logging
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        # Set up file handler with UTF-8 encoding (always DEBUG)
        import core.config as config
        file_handler = BackupDirectoryRotatingFileHandler(
            log_paths['main_file'],
            log_paths['backup_dir'],
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(logging.DEBUG)

        # Set up console handler (respects current verbosity setting)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        console_handler.setLevel(get_log_level_from_env())

        # Add handlers to root logger
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        root_logger.setLevel(logging.DEBUG)

        # Suppress noisy logging
        suppress_noisy_logging()
        
        logging.getLogger(__name__).info("Logging system restarted successfully")
        return True
        
    except Exception as e:
        print(f"Failed to restart logging system: {e}")
        return False


def clear_log_file_locks():
    """
    Clear any file locks that might be preventing log rotation.
    
    This function attempts to handle Windows file locking issues by:
    1. Temporarily disabling log rotation
    2. Closing all log file handlers
    3. Reopening them with fresh file handles
    
    Returns:
        bool: True if locks were cleared successfully, False otherwise
    """
    try:
        # Temporarily disable log rotation
        os.environ['DISABLE_LOG_ROTATION'] = '1'
        
        # Close all handlers that might be holding file locks
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if hasattr(handler, 'stream') and handler.stream:
                try:
                    handler.stream.close()
                except:
                    pass
            handler.close()
        
        # Clear component loggers too
        for component_name, component_logger in _component_loggers.items():
            for handler in component_logger.logger.handlers[:]:
                if hasattr(handler, 'stream') and handler.stream:
                    try:
                        handler.stream.close()
                    except:
                        pass
                handler.close()
        
        # Remove the temporary environment variable
        if 'DISABLE_LOG_ROTATION' in os.environ:
            del os.environ['DISABLE_LOG_ROTATION']
        
        return True
        
    except Exception as e:
        print(f"Failed to clear log file locks: {e}")
        # Make sure to remove the environment variable even if there was an error
        if 'DISABLE_LOG_ROTATION' in os.environ:
            del os.environ['DISABLE_LOG_ROTATION']
        return False
