# config.py
"""
Configuration management for MHM.
Handles environment variables, validation, and system settings.
"""

import os
from dotenv import load_dotenv
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from core.error_handling import (
    ConfigurationError, ValidationError, handle_configuration_error,
    handle_errors, error_handler
)

# Set up basic logging for config issues
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class ConfigValidationError(Exception):
    """Custom exception for configuration validation errors with detailed information."""
    def __init__(self, message: str, missing_configs: List[str] = None, warnings: List[str] = None):
        super().__init__(message)
        self.missing_configs = missing_configs or []
        self.warnings = warnings or []

# Load environment variables
load_dotenv()

# Base data directory
BASE_DATA_DIR = os.getenv('BASE_DATA_DIR', 'data')

# Paths - Updated for better organization
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'app.log')  # Move log to root
USER_INFO_DIR_PATH = os.getenv('USER_INFO_DIR_PATH', os.path.join(BASE_DATA_DIR, 'users'))
DEFAULT_MESSAGES_DIR_PATH = os.getenv('DEFAULT_MESSAGES_DIR_PATH', 'default_messages')  # Keep at root

# LM Studio Configuration (replacing GPT4All)
# SETUP INSTRUCTIONS:
# 1. Download and install LM Studio from https://lmstudio.ai/
# 2. In LM Studio, load your downloaded DeepSeek LLM 7B Chat model
# 3. Start the local server (usually localhost:1234)
# 4. The server will be available at http://localhost:1234/v1 with OpenAI-compatible API
LM_STUDIO_BASE_URL = os.getenv('LM_STUDIO_BASE_URL', 'http://localhost:1234/v1')
LM_STUDIO_API_KEY = os.getenv('LM_STUDIO_API_KEY', 'lm-studio')  # LM Studio uses any key
LM_STUDIO_MODEL = os.getenv('LM_STUDIO_MODEL', 'deepseek-llm-7b-chat')  # Model name for API calls

# Legacy support for GPT4All (deprecated, keeping for fallback)
HERMES_FILE_PATH = os.getenv('HERMES_FILE_PATH', os.path.expanduser('~/AppData/Local/nomic.ai/GPT4All/Nous-Hermes-2-Mistral-7B-DPO.Q4_0.gguf'))

# AI Performance Configuration
AI_TIMEOUT_SECONDS = int(os.getenv('AI_TIMEOUT_SECONDS', '30'))  # Increased timeout for resource-constrained systems
AI_BATCH_SIZE = int(os.getenv('AI_BATCH_SIZE', '4'))  # For batch processing
AI_CUDA_WARMUP = os.getenv('AI_CUDA_WARMUP', 'false').lower() == 'true'  # Disabled for LM Studio
AI_CACHE_RESPONSES = os.getenv('AI_CACHE_RESPONSES', 'true').lower() == 'true'

# User Context Caching
CONTEXT_CACHE_TTL = int(os.getenv('CONTEXT_CACHE_TTL', '300'))  # 5 minutes
CONTEXT_CACHE_MAX_SIZE = int(os.getenv('CONTEXT_CACHE_MAX_SIZE', '100'))

# File Organization Settings
AUTO_CREATE_USER_DIRS = os.getenv('AUTO_CREATE_USER_DIRS', 'true').lower() == 'true'

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING').upper()  # Default to WARNING for quiet operation

# Communication Channel Configurations (non-blocking)
# TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Deactivated
# if not TELEGRAM_BOT_TOKEN:
#     logger.warning("TELEGRAM_BOT_TOKEN not found - Telegram channel will be disabled")

EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER')
EMAIL_IMAP_SERVER = os.getenv('EMAIL_IMAP_SERVER')
EMAIL_SMTP_USERNAME = os.getenv('EMAIL_SMTP_USERNAME')
EMAIL_SMTP_PASSWORD = os.getenv('EMAIL_SMTP_PASSWORD')
if not all([EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD]):
    logger.warning("Email configuration incomplete - Email channel will be disabled")

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not DISCORD_BOT_TOKEN:
    logger.warning("DISCORD_BOT_TOKEN not found - Discord channel will be disabled")

# Scheduler Configuration
SCHEDULER_INTERVAL = int(os.getenv('SCHEDULER_INTERVAL', '60'))

# Configuration Validation Functions
@handle_errors("validating core paths", user_friendly=False)
def validate_core_paths() -> Tuple[bool, List[str], List[str]]:
    """Validate that all core paths are accessible and can be created if needed."""
    errors = []
    warnings = []
    
    paths_to_check = [
        ('BASE_DATA_DIR', BASE_DATA_DIR),
        ('USER_INFO_DIR_PATH', USER_INFO_DIR_PATH),
        ('DEFAULT_MESSAGES_DIR_PATH', DEFAULT_MESSAGES_DIR_PATH),
    ]
    
    for name, path in paths_to_check:
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                # Try to create the directory
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                    warnings.append(f"Created missing directory: {name} ({path})")
                except Exception as e:
                    error_msg = f"Cannot create directory {name} ({path}): {e}"
                    errors.append(error_msg)
                    # Use our error handling for this specific error
                    handle_configuration_error(e, name, f"creating directory {path}")
            elif not path_obj.is_dir():
                error_msg = f"Path {name} exists but is not a directory: {path}"
                errors.append(error_msg)
            elif not os.access(path, os.W_OK):
                error_msg = f"No write access to directory {name}: {path}"
                errors.append(error_msg)
        except Exception as e:
            error_msg = f"Error validating path {name} ({path}): {e}"
            errors.append(error_msg)
            # Use our error handling for this specific error
            handle_configuration_error(e, name, f"validating path {path}")
    
    return len(errors) == 0, errors, warnings

def validate_ai_configuration() -> Tuple[bool, List[str], List[str]]:
    """Validate AI-related configuration settings."""
    errors = []
    warnings = []
    
    # Check LM Studio configuration
    if not LM_STUDIO_BASE_URL:
        errors.append("LM_STUDIO_BASE_URL is not configured")
    elif not LM_STUDIO_BASE_URL.startswith(('http://', 'https://')):
        errors.append("LM_STUDIO_BASE_URL must be a valid URL starting with http:// or https://")
    
    # LM_STUDIO_API_KEY has a default value, so we only warn if it's explicitly set to empty
    if LM_STUDIO_API_KEY == '':
        warnings.append("LM_STUDIO_API_KEY is explicitly set to empty (using default)")
    
    # LM_STUDIO_MODEL has a default value, so we only warn if it's explicitly set to empty
    if LM_STUDIO_MODEL == '':
        warnings.append("LM_STUDIO_MODEL is explicitly set to empty (using default)")
    
    # Check AI performance settings
    if AI_TIMEOUT_SECONDS < 5:
        warnings.append("AI_TIMEOUT_SECONDS is very low (< 5 seconds), may cause timeouts")
    elif AI_TIMEOUT_SECONDS > 300:
        warnings.append("AI_TIMEOUT_SECONDS is very high (> 5 minutes), may cause long waits")
    
    if AI_BATCH_SIZE < 1:
        errors.append("AI_BATCH_SIZE must be at least 1")
    elif AI_BATCH_SIZE > 20:
        warnings.append("AI_BATCH_SIZE is very high (> 20), may cause memory issues")
    
    # Check cache settings
    if CONTEXT_CACHE_TTL < 60:
        warnings.append("CONTEXT_CACHE_TTL is very low (< 1 minute), may cause frequent cache misses")
    elif CONTEXT_CACHE_TTL > 3600:
        warnings.append("CONTEXT_CACHE_TTL is very high (> 1 hour), may use excessive memory")
    
    if CONTEXT_CACHE_MAX_SIZE < 10:
        warnings.append("CONTEXT_CACHE_MAX_SIZE is very low (< 10), may cause frequent cache evictions")
    elif CONTEXT_CACHE_MAX_SIZE > 1000:
        warnings.append("CONTEXT_CACHE_MAX_SIZE is very high (> 1000), may use excessive memory")
    
    return len(errors) == 0, errors, warnings

def validate_communication_channels() -> Tuple[bool, List[str], List[str]]:
    """Validate communication channel configurations."""
    errors = []
    warnings = []
    available_channels = []
    
    # Check email configuration
    email_config = {
        'EMAIL_SMTP_SERVER': EMAIL_SMTP_SERVER,
        'EMAIL_IMAP_SERVER': EMAIL_IMAP_SERVER,
        'EMAIL_SMTP_USERNAME': EMAIL_SMTP_USERNAME,
        'EMAIL_SMTP_PASSWORD': EMAIL_SMTP_PASSWORD
    }
    
    email_missing = [key for key, value in email_config.items() if not value]
    if email_missing:
        warnings.append(f"Email channel disabled - missing: {', '.join(email_missing)}")
    else:
        available_channels.append('email')
        # Validate email format
        if EMAIL_SMTP_USERNAME and '@' not in EMAIL_SMTP_USERNAME:
            warnings.append("EMAIL_SMTP_USERNAME doesn't appear to be a valid email address")
    
    # Check Discord configuration
    if not DISCORD_BOT_TOKEN:
        warnings.append("Discord channel disabled - DISCORD_BOT_TOKEN not configured")
    else:
        available_channels.append('discord')
        # Basic Discord token validation (should start with specific pattern)
        if not DISCORD_BOT_TOKEN.startswith(('MT', 'OT', 'NT')):
            warnings.append("DISCORD_BOT_TOKEN doesn't match expected Discord bot token format")
    
    # Check if any channels are available
    if not available_channels:
        errors.append("No communication channels are properly configured. At least one channel (Email or Discord) must be configured.")
    
    return len(errors) == 0, errors, warnings

def validate_logging_configuration() -> Tuple[bool, List[str], List[str]]:
    """Validate logging configuration."""
    errors = []
    warnings = []
    
    # Check log level
    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if LOG_LEVEL not in valid_log_levels:
        errors.append(f"Invalid LOG_LEVEL '{LOG_LEVEL}'. Must be one of: {', '.join(valid_log_levels)}")
    
    # Check log file path
    try:
        log_path = Path(LOG_FILE_PATH)
        log_dir = log_path.parent
        if log_dir.exists() and not os.access(log_dir, os.W_OK):
            errors.append(f"Cannot write to log directory: {log_dir}")
        elif not log_dir.exists():
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
                warnings.append(f"Created log directory: {log_dir}")
            except Exception as e:
                errors.append(f"Cannot create log directory {log_dir}: {e}")
    except Exception as e:
        errors.append(f"Error validating log file path {LOG_FILE_PATH}: {e}")
    
    return len(errors) == 0, errors, warnings

def validate_scheduler_configuration() -> Tuple[bool, List[str], List[str]]:
    """Validate scheduler configuration."""
    errors = []
    warnings = []
    
    if SCHEDULER_INTERVAL < 10:
        errors.append("SCHEDULER_INTERVAL must be at least 10 seconds")
    elif SCHEDULER_INTERVAL < 30:
        warnings.append("SCHEDULER_INTERVAL is very low (< 30 seconds), may cause high CPU usage")
    elif SCHEDULER_INTERVAL > 3600:
        warnings.append("SCHEDULER_INTERVAL is very high (> 1 hour), may cause delayed responses")
    
    return len(errors) == 0, errors, warnings

def validate_file_organization_settings() -> Tuple[bool, List[str], List[str]]:
    """Validate file organization settings."""
    errors = []
    warnings = []
    
    # These are boolean settings, so just check they're valid
    if not isinstance(AUTO_CREATE_USER_DIRS, bool):
        errors.append("AUTO_CREATE_USER_DIRS must be a boolean value")
    
    # Check for potential conflicts
    if AUTO_CREATE_USER_DIRS:
        warnings.append("AUTO_CREATE_USER_DIRS is enabled - user directories will be created automatically")
    
    return len(errors) == 0, errors, warnings

def validate_environment_variables() -> Tuple[bool, List[str], List[str]]:
    """Check for common environment variable issues."""
    errors = []
    warnings = []
    
    # Check if .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        warnings.append("No .env file found - using default configuration values")
    
    # Check for potentially problematic environment variables
    problematic_vars = []
    for key, value in os.environ.items():
        if key.startswith('MHM_') and not value:
            problematic_vars.append(key)
    
    if problematic_vars:
        warnings.append(f"Empty environment variables found: {', '.join(problematic_vars)}")
    
    return len(errors) == 0, errors, warnings

def validate_all_configuration() -> Dict[str, any]:
    """Comprehensive configuration validation that checks all aspects of the configuration.
    
    Returns:
        Dict containing validation results with the following structure:
        {
            'valid': bool,
            'errors': List[str],
            'warnings': List[str],
            'available_channels': List[str],
            'summary': str
        }
    """
    all_errors = []
    all_warnings = []
    
    # Run all validation functions
    validators = [
        ('Core Paths', validate_core_paths),
        ('AI Configuration', validate_ai_configuration),
        ('Communication Channels', validate_communication_channels),
        ('Logging Configuration', validate_logging_configuration),
        ('Scheduler Configuration', validate_scheduler_configuration),
        ('File Organization Settings', validate_file_organization_settings),
        ('Environment Variables', validate_environment_variables),
    ]
    
    for name, validator in validators:
        try:
            is_valid, errors, warnings = validator()
            if errors:
                all_errors.extend([f"{name}: {error}" for error in errors])
            if warnings:
                all_warnings.extend([f"{name}: {warning}" for warning in warnings])
        except Exception as e:
            all_errors.append(f"{name}: Validation failed with exception: {e}")
    
    # Get available channels
    available_channels = get_available_channels()
    
    # Create summary
    if all_errors:
        summary = f"Configuration validation failed with {len(all_errors)} error(s) and {len(all_warnings)} warning(s)"
    elif all_warnings:
        summary = f"Configuration validation passed with {len(all_warnings)} warning(s)"
    else:
        summary = "Configuration validation passed successfully"
    
    if available_channels:
        summary += f" - Available channels: {', '.join(available_channels)}"
    else:
        summary += " - No communication channels available"
    
    return {
        'valid': len(all_errors) == 0,
        'errors': all_errors,
        'warnings': all_warnings,
        'available_channels': available_channels,
        'summary': summary
    }

def validate_and_raise_if_invalid() -> List[str]:
    """Validate configuration and raise ConfigValidationError if invalid.
    
    Returns:
        List of available communication channels if validation passes.
    
    Raises:
        ConfigValidationError: If configuration is invalid with detailed error information.
    """
    result = validate_all_configuration()
    
    if not result['valid']:
        raise ConfigValidationError(
            f"Configuration validation failed: {result['summary']}",
            missing_configs=result['errors'],
            warnings=result['warnings']
        )
    
    if result['warnings']:
        logger.warning(f"Configuration warnings: {'; '.join(result['warnings'])}")
    
    logger.info(f"Configuration validation passed: {result['summary']}")
    return result['available_channels']

def print_configuration_report():
    """Print a detailed configuration report to the console."""
    result = validate_all_configuration()
    
    print("\n" + "="*60)
    print("MHM CONFIGURATION VALIDATION REPORT")
    print("="*60)
    
    print(f"\nSUMMARY: {result['summary']}")
    
    if result['available_channels']:
        print(f"\nAVAILABLE CHANNELS: {', '.join(result['available_channels'])}")
    else:
        print("\nAVAILABLE CHANNELS: None")
    
    if result['errors']:
        print(f"\nERRORS ({len(result['errors'])}):")
        for i, error in enumerate(result['errors'], 1):
            print(f"  {i}. {error}")
    
    if result['warnings']:
        print(f"\nWARNINGS ({len(result['warnings'])}):")
        for i, warning in enumerate(result['warnings'], 1):
            print(f"  {i}. {warning}")
    
    # Print current configuration values
    print(f"\nCURRENT CONFIGURATION:")
    print(f"  Base Data Directory: {BASE_DATA_DIR}")
    print(f"  Log File: {LOG_FILE_PATH}")
    print(f"  Log Level: {LOG_LEVEL}")
    print(f"  LM Studio URL: {LM_STUDIO_BASE_URL}")
    print(f"  AI Timeout: {AI_TIMEOUT_SECONDS}s")
    print(f"  Scheduler Interval: {SCHEDULER_INTERVAL}s")
    print(f"  Auto Create User Dirs: {AUTO_CREATE_USER_DIRS}")
    
    print("\n" + "="*60)
    
    return result['valid']

# Data Management Functions
def get_user_data_dir(user_id: str) -> str:
    """Get the data directory for a specific user."""
    return os.path.join(BASE_DATA_DIR, 'users', user_id)

def get_user_file_path(user_id: str, file_type: str) -> str:
    """Get the file path for a specific user file type."""
    user_dir = get_user_data_dir(user_id)
    
    file_mapping = {
        # New structure
        'account': 'account.json',
        'preferences': 'preferences.json',
        'user_context': 'user_context.json',
        'schedules': 'schedules.json',
        # Other files
        'daily_checkins': 'daily_checkins.json',
        'chat_interactions': 'chat_interactions.json',
        'sent_messages': 'messages/sent_messages.json',
        'conversation_history': 'conversation_history.json'
    }
    return os.path.join(user_dir, file_mapping.get(file_type, f'{file_type}.json'))

def ensure_user_directory(user_id: str) -> bool:
    """Ensure user directory exists if using subdirectories."""
    if not AUTO_CREATE_USER_DIRS:
        return True
    
    user_dir = get_user_data_dir(user_id)
    try:
        os.makedirs(user_dir, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create user directory {user_dir}: {e}")
        return False

# Legacy validation functions (kept for backward compatibility)
def validate_telegram_config():
    # Deactivated - Telegram channel is disabled
    raise ConfigurationError("Telegram channel has been deactivated.")
    # if not TELEGRAM_BOT_TOKEN:
    #     raise ConfigError("TELEGRAM_BOT_TOKEN is missing from environment configuration.")
    # return True

@handle_errors("validating email configuration", user_friendly=False)
def validate_email_config():
    required_vars = [EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD]
    if not all(required_vars):
        missing = [var for var in ['EMAIL_SMTP_SERVER', 'EMAIL_IMAP_SERVER', 'EMAIL_SMTP_USERNAME', 'EMAIL_SMTP_PASSWORD'] 
                  if not globals()[var]]
        raise ConfigurationError(f"Missing email configuration variables: {', '.join(missing)}")
    return True

@handle_errors("validating Discord configuration", user_friendly=False)
def validate_discord_config():
    if not DISCORD_BOT_TOKEN:
        raise ConfigurationError("DISCORD_BOT_TOKEN is missing from environment configuration.")
    return True

@handle_errors("getting available channels", user_friendly=False)
def get_available_channels():
    """Get list of available communication channels based on configuration."""
    available_channels = []
    
    # Check email configuration
    if all([EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD]):
        available_channels.append('email')
    
    # Check Discord configuration
    if DISCORD_BOT_TOKEN:
        available_channels.append('discord')
    
    return available_channels

@handle_errors("validating minimum configuration", user_friendly=False)
def validate_minimum_config():
    """Ensure at least one communication channel is configured"""
    available = get_available_channels()
    if not available:
        raise ConfigurationError("No communication channels are properly configured. Please set up at least one channel (Telegram, Email, or Discord).")
    return available