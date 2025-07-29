# logger.py

import logging
import os
import shutil
from logging.handlers import RotatingFileHandler
from core.config import LOG_FILE_PATH, LOG_MAX_BYTES, LOG_BACKUP_COUNT, LOG_COMPRESS_BACKUPS, LOG_BACKUP_DIR

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

class BackupDirectoryRotatingFileHandler(RotatingFileHandler):
    """
    Custom rotating file handler that moves rotated files to a backup directory.
    """
    
    def __init__(self, filename, backup_dir, maxBytes=0, backupCount=0, encoding=None, delay=False):
        super().__init__(filename, maxBytes, backupCount, encoding, delay)
        self.backup_dir = backup_dir
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def doRollover(self):
        """
        Do a rollover, as described in __init__().
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # Move existing backup files to backup directory
        for i in range(self.backupCount - 1, 0, -1):
            sfn = f"{self.baseFilename}.{i}"
            dfn = f"{self.baseFilename}.{i + 1}"
            if os.path.exists(sfn):
                if os.path.exists(dfn):
                    os.remove(dfn)
                # Move to backup directory with timestamp
                backup_name = f"{os.path.basename(self.baseFilename)}.{i}"
                backup_path = os.path.join(self.backup_dir, backup_name)
                shutil.move(sfn, backup_path)
        
        # Move current log file to backup directory
        if os.path.exists(self.baseFilename):
            backup_name = f"{os.path.basename(self.baseFilename)}.1"
            backup_path = os.path.join(self.backup_dir, backup_name)
            shutil.move(self.baseFilename, backup_path)
        
        # Create new log file
        if not self.delay:
            self.stream = self._open()

# Global variable to track current verbosity mode
_verbose_mode = False
_original_levels = {}

def get_log_level_from_env():
    """
    Get log level from environment variable, default to WARNING for quiet mode.
    
    Returns:
        int: Logging level constant (e.g., logging.WARNING, logging.DEBUG)
    """
    log_level = os.getenv('LOG_LEVEL', 'WARNING').upper()
    return getattr(logging, log_level, logging.WARNING)

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
    
    root_logger = logging.getLogger()
    
    # Check if logging is already set up properly
    if root_logger.hasHandlers():
        # Verify we have both file and console handlers
        has_file_handler = any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers)
        has_console_handler = any(isinstance(h, logging.StreamHandler) and 
                                not isinstance(h, RotatingFileHandler) for h in root_logger.handlers)
        
        if has_file_handler and has_console_handler:
            # Logging is already properly set up
            return
        else:
            # Incomplete setup, clear and reinitialize
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
    
    try:
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        # Set up file handler with UTF-8 encoding (always logs everything)
        file_handler = BackupDirectoryRotatingFileHandler(LOG_FILE_PATH, LOG_BACKUP_DIR, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding='utf-8')
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(logging.DEBUG)  # File gets everything

        # Set up console handler (respects verbosity setting)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(log_formatter)
        
        # Get initial log level from environment or default to WARNING for quiet console output
        console_level = get_log_level_from_env()
        stream_handler.setLevel(console_level)

        # Add handlers to the root logger
        root_logger.setLevel(logging.DEBUG)  # Root logger captures everything
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)

        # Suppress noisy third-party libraries
        suppress_noisy_logging()

        status_logger = logging.getLogger(__name__)
        status_logger.info(
            "Logging initialized - Console level: %s, File level: DEBUG",
            logging.getLevelName(console_level),
        )
        status_logger.info(
            "Use LOG_LEVEL environment variable or toggle_verbose_logging() to change verbosity"
        )
        
    except Exception as e:
        # Fallback to basic logging that writes to stderr
        logging.basicConfig(
            level=logging.WARNING,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        fallback_logger = logging.getLogger(__name__)
        fallback_logger.error("Failed to set up logging: %s", e)
        fallback_logger.warning("Using fallback logging configuration")


def get_logger(name):
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (usually __name__ from the calling module)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    setup_logging()
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
        backup_files = []
        backup_total_size = 0
        if os.path.exists(LOG_BACKUP_DIR):
            backup_pattern = os.path.join(LOG_BACKUP_DIR, f"{os.path.basename(LOG_FILE_PATH)}*")
            backup_log_files = glob.glob(backup_pattern)
            
            for log_file in backup_log_files:
                if os.path.exists(log_file):
                    size = os.path.getsize(log_file)
                    backup_total_size += size
                    backup_files.append({
                        'name': os.path.basename(log_file),
                        'location': 'backup',
                        'size_bytes': size,
                        'size_mb': round(size / (1024 * 1024), 2)
                    })
        
        # Calculate totals
        total_size = current_log_size + backup_total_size
        total_files = (1 if current_log_info else 0) + len(backup_files)
        
        return {
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'current_log': current_log_info,
            'backup_files': backup_files,
            'backup_directory': LOG_BACKUP_DIR
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
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(log_formatter)
        
        # Use current verbose mode setting or default to quiet
        console_level = logging.DEBUG if _verbose_mode else logging.WARNING
        stream_handler.setLevel(console_level)

        # Add handlers to the root logger
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)

        # Suppress noisy third-party libraries
        suppress_noisy_logging()
        
        return True
        
    except Exception as e:
        logging.basicConfig(
            level=logging.ERROR,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        logging.getLogger(__name__).error("Failed to force restart logging: %s", e)
        return False
