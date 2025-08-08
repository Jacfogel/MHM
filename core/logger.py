# logger.py

import logging
import os
import shutil
import re
import time
import json
import gzip
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
# Define logging paths directly to avoid circular imports
LOGS_DIR = os.getenv('LOGS_DIR', 'logs')
LOG_BACKUP_DIR = os.getenv('LOG_BACKUP_DIR', os.path.join(LOGS_DIR, 'backups'))
LOG_ARCHIVE_DIR = os.getenv('LOG_ARCHIVE_DIR', os.path.join(LOGS_DIR, 'archive'))

# Component-specific log files
LOG_MAIN_FILE = os.getenv('LOG_MAIN_FILE', os.path.join(LOGS_DIR, 'app.log'))
LOG_DISCORD_FILE = os.getenv('LOG_DISCORD_FILE', os.path.join(LOGS_DIR, 'discord.log'))
LOG_AI_FILE = os.getenv('LOG_AI_FILE', os.path.join(LOGS_DIR, 'ai.log'))
LOG_USER_ACTIVITY_FILE = os.getenv('LOG_USER_ACTIVITY_FILE', os.path.join(LOGS_DIR, 'user_activity.log'))
LOG_ERRORS_FILE = os.getenv('LOG_ERRORS_FILE', os.path.join(LOGS_DIR, 'errors.log'))

# Legacy support - these will be imported from config when available
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', LOG_MAIN_FILE)
LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '5242880'))  # 5MB default
LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
LOG_COMPRESS_BACKUPS = os.getenv('LOG_COMPRESS_BACKUPS', 'false').lower() == 'true'

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
        self.logger.setLevel(level)
        
        # Ensure no duplicate handlers
        self.logger.handlers.clear()
        
        # Create formatter with component name
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Create file handler with rotation to backup directory
        file_handler = BackupDirectoryRotatingFileHandler(
            log_file_path,
            backup_dir=LOG_BACKUP_DIR,
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
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
    
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
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # Get the rollover filename from parent class
        current_time = int(time.time())
        dst_time = self.rolloverAt - self.interval
        time_tuple = time.localtime(dst_time)
        dfn = self.rotation_filename(self.baseFilename + "." + time.strftime(self.suffix, time_tuple))
        
        # Move current log file to backup directory if it exists
        if os.path.exists(self.baseFilename):
            backup_name = f"{os.path.basename(self.baseFilename)}.{time.strftime(self.suffix, time_tuple)}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            shutil.move(self.baseFilename, backup_path)
        
        # Call parent's doRollover to handle the actual rollover logic
        super().doRollover()


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
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(LOG_BACKUP_DIR, exist_ok=True)
    os.makedirs(LOG_ARCHIVE_DIR, exist_ok=True)


def get_component_logger(component_name: str) -> ComponentLogger:
    """
    Get or create a component-specific logger.
    
    Args:
        component_name: Name of the component (e.g., 'discord', 'ai', 'user_activity')
    
    Returns:
        ComponentLogger: Logger for the specified component
    """
    # Skip component logging if running tests to prevent test logs from going to main component logs
    if os.getenv('MHM_TESTING') == '1':
        # Return a dummy logger that does nothing during tests
        class DummyComponentLogger:
            def debug(self, message: str, **kwargs): pass
            def info(self, message: str, **kwargs): pass
            def warning(self, message: str, **kwargs): pass
            def error(self, message: str, **kwargs): pass
            def critical(self, message: str, **kwargs): pass
        return DummyComponentLogger()
    
    if component_name not in _component_loggers:
        # Map component names to log files
        log_file_map = {
            'discord': LOG_DISCORD_FILE,
            'ai': LOG_AI_FILE,
            'user_activity': LOG_USER_ACTIVITY_FILE,
            'errors': LOG_ERRORS_FILE,
            'main': LOG_MAIN_FILE
        }
        
        log_file = log_file_map.get(component_name, LOG_MAIN_FILE)
        _component_loggers[component_name] = ComponentLogger(component_name, log_file)
    
    return _component_loggers[component_name]


def setup_logging():
    """
    Set up logging with file and console handlers. Ensure it is called only once.
    
    Creates a dual-handler logging system:
    - File handler: Always logs at DEBUG level with rotation
    - Console handler: Respects verbosity settings (WARNING by default)
    
    Automatically suppresses noisy third-party library logging.
    """
    # Skip logging setup if running tests
    if os.getenv('MHM_TESTING') == '1':
        return
    
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

    # Set up file handler with UTF-8 encoding (always DEBUG)
    file_handler = BackupDirectoryRotatingFileHandler(LOG_FILE_PATH, LOG_BACKUP_DIR, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding='utf-8')
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

    # Suppress noisy third-party logging
    suppress_noisy_logging()
    
    # Log successful setup
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized - Console level: %s, File level: DEBUG", logging.getLevelName(log_level))
    logger.info("Use LOG_LEVEL environment variable or toggle_verbose_logging() to change verbosity")


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
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("telegram.ext").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.client").setLevel(logging.WARNING)
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)
    
    # Apply heartbeat warning filter to Discord gateway logger
    discord_gateway_logger = logging.getLogger("discord.gateway")
    heartbeat_filter = HeartbeatWarningFilter()
    discord_gateway_logger.addFilter(heartbeat_filter)
    
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
        
        # Get current log file
        current_log_size = 0
        current_log_info = None
        if os.path.exists(LOG_FILE_PATH):
            current_log_size = os.path.getsize(LOG_FILE_PATH)
            current_log_info = {
                'name': os.path.basename(LOG_FILE_PATH),
                'location': 'current',
                'size_bytes': current_log_size,
                'size_mb': round(current_log_size / (1024 * 1024), 2)
            }
        
        # Get backup log files
        backup_file_paths = []
        backup_file_info = []
        backup_total_size = 0
        if os.path.exists(LOG_BACKUP_DIR):
            backup_pattern = os.path.join(LOG_BACKUP_DIR, f"{os.path.basename(LOG_FILE_PATH)}*")
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
            'backup_directory': LOG_BACKUP_DIR,
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
        if os.path.exists(LOG_BACKUP_DIR):
            backup_pattern = os.path.join(LOG_BACKUP_DIR, f"{os.path.basename(LOG_FILE_PATH)}*")
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
        
        # Get all log files in logs directory and backup directory
        log_patterns = [
            os.path.join(LOGS_DIR, "*.log.*"),  # Rotated log files
            os.path.join(LOG_BACKUP_DIR, "*.log*")  # Backup log files
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
                                archive_file = os.path.join(LOG_ARCHIVE_DIR, filename + '.gz')
                                
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
        
        if os.path.exists(LOG_ARCHIVE_DIR):
            archive_pattern = os.path.join(LOG_ARCHIVE_DIR, "*.gz")
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
        
        # Force setup new logging
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        # Set up file handler with UTF-8 encoding (always DEBUG)
        file_handler = BackupDirectoryRotatingFileHandler(LOG_FILE_PATH, LOG_BACKUP_DIR, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding='utf-8')
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
        print(f"Error restarting logging system: {e}")
        return False
