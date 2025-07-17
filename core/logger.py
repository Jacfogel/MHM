# logger.py

import logging
import os
from logging.handlers import RotatingFileHandler
from core.config import LOG_FILE_PATH

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
        logging.basicConfig(
            level=logging.ERROR,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        logging.getLogger(__name__).error("Failed to force restart logging: %s", e)
        return False
