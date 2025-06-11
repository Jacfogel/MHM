# logger.py

import logging
import os
from logging.handlers import RotatingFileHandler
from core.config import LOG_FILE_PATH

# Global variable to track current verbosity mode
_verbose_mode = False
_original_levels = {}

def get_log_level_from_env():
    """Get log level from environment variable, default to WARNING for quiet mode"""
    log_level = os.getenv('LOG_LEVEL', 'WARNING').upper()
    return getattr(logging, log_level, logging.WARNING)

def setup_logging():
    """
    Set up logging with file and console handlers. Ensure it is called only once.
    """
    if not logging.getLogger().hasHandlers():
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        # Set up file handler with UTF-8 encoding (always logs everything)
        file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=5000000, backupCount=5, encoding='utf-8')
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(logging.DEBUG)  # File gets everything

        # Set up console handler (respects verbosity setting)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(log_formatter)
        
        # Get initial log level from environment or default to WARNING for quiet console output
        console_level = get_log_level_from_env()
        stream_handler.setLevel(console_level)

        # Add handlers to the root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Root logger captures everything
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)

        # Suppress noisy third-party libraries
        suppress_noisy_logging()

        print(f"Logging initialized - Console level: {logging.getLevelName(console_level)}, File level: DEBUG")
        print("Use LOG_LEVEL environment variable or toggle_verbose_logging() to change verbosity")


def get_logger(name):
    """
    Get a logger with the specified name.
    """
    setup_logging()
    return logging.getLogger(name)



def suppress_noisy_logging():
    """
    Suppress excessive logging from third-party libraries.
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
            print(f"Console logging level set to: {logging.getLevelName(level)}")
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
        print("Verbose logging enabled (DEBUG/INFO messages will be shown)")
        return True
    else:
        # Enable quiet mode - show only WARNING and above
        set_console_log_level(logging.WARNING)
        print("Quiet logging enabled (only WARNING/ERROR messages will be shown)")
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
        print("Verbose logging enabled")
    else:
        set_console_log_level(logging.WARNING)
        print("Quiet logging enabled")

def disable_module_logging(module_name):
    """
    Disable debug logging for a specific module.
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.WARNING)
    for handler in logger.handlers:
        handler.setLevel(logging.WARNING)

def force_restart_logging():
    """
    Force restart the logging system by clearing all handlers and reinitializing
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
        file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=5000000, backupCount=5, encoding='utf-8')
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
        print(f"Failed to force restart logging: {e}")
        return False
