# config.py
"""
Configuration management for MHM.
Handles environment variables, validation, and system settings.
"""

import os
from dotenv import load_dotenv
from typing import Dict, List, Tuple
from pathlib import Path

from core.error_handling import (
    ConfigurationError, handle_configuration_error,
    handle_errors
)

class ConfigValidationError(Exception):
    """Custom exception for configuration validation errors with detailed information."""
    @handle_errors("initializing config error", default_return=None)
    def __init__(self, message: str, missing_configs: List[str] = None, warnings: List[str] = None):
        """Initialize the object."""
        super().__init__(message)
        self.missing_configs = missing_configs or []
        self.warnings = warnings or []

# Load environment variables (tolerant mode)
try:
    # do not raise on parsing issues; warnings are logged by python-dotenv itself
    load_dotenv(override=False, verbose=False)
except Exception as _e:
    # keep startup resilient; config validation will report issues later
    pass

@handle_errors("normalizing path", default_return=None)
def _normalize_path(value: str) -> str:
    """Normalize path strings from environment to avoid Windows escape issues.
    - Removes CR/LF control chars
    - Strips surrounding quotes
    - Normalizes separators to OS-specific
    """
    try:
        if value is None:
            return value
        cleaned = value.replace('\r', '').replace('\n', '').strip().strip('"').strip("'")
        cleaned = cleaned.replace('/', os.sep).replace('\\', os.sep)
        return os.path.normpath(cleaned)
    except Exception as e:
        logger.error(f"Error normalizing path '{value}': {e}")
        return value  # Return original value on error

# Base data directory (preserve env value formatting to satisfy tests)
# During tests, redirect to TEST_DATA_DIR (defaults to tests/data) for
# complete isolation from real user data. This ensures all test
# artifacts are created under the project tree instead of system temp
# directories.
if os.getenv('MHM_TESTING') == '1':
    BASE_DATA_DIR = os.getenv('TEST_DATA_DIR', 'tests/data')
else:
    BASE_DATA_DIR = os.getenv('BASE_DATA_DIR', 'data')

# Paths - Updated for better organization
# LOG_FILE_PATH environment variable removed - using LOG_MAIN_FILE directly
USER_INFO_DIR_PATH = _normalize_path(os.getenv('USER_INFO_DIR_PATH', str(Path(BASE_DATA_DIR) / 'users')))
# Fix: Use forward slashes for cross-platform compatibility and avoid path normalization issues
DEFAULT_MESSAGES_DIR_PATH = os.getenv('DEFAULT_MESSAGES_DIR_PATH', 'resources/default_messages')
if os.getenv('MHM_TESTING') == '1':
    # Force default messages dir during tests to avoid absolute path/env variance
    DEFAULT_MESSAGES_DIR_PATH = 'resources/default_messages'

# LM Studio Configuration
# SETUP INSTRUCTIONS:
# 1. Download and install LM Studio from https://lmstudio.ai/
# 2. In LM Studio, load your downloaded Phi 2 Chat model
# 3. Start the local server (usually localhost:1234)
# 4. The server will be available at http://localhost:1234/v1 with OpenAI-compatible API
LM_STUDIO_BASE_URL = os.getenv('LM_STUDIO_BASE_URL', 'http://localhost:1234/v1')
LM_STUDIO_API_KEY = os.getenv('LM_STUDIO_API_KEY', 'lm-studio')  # LM Studio uses any key
LM_STUDIO_MODEL = os.getenv('LM_STUDIO_MODEL', 'phi-2')  # Model name for API calls

# LM Studio Auto-Management Configuration
LM_STUDIO_AUTO_START = os.getenv('LM_STUDIO_AUTO_START', 'true').lower() == 'true'  # Auto-start LM Studio if not running
LM_STUDIO_AUTO_LOAD_MODEL = os.getenv('LM_STUDIO_AUTO_LOAD_MODEL', 'true').lower() == 'true'  # Auto-load model if not loaded
LM_STUDIO_STARTUP_TIMEOUT = int(os.getenv('LM_STUDIO_STARTUP_TIMEOUT', '60'))  # Timeout for LM Studio startup (seconds)
LM_STUDIO_MODEL_LOAD_TIMEOUT = int(os.getenv('LM_STUDIO_MODEL_LOAD_TIMEOUT', '30'))  # Timeout for model loading (seconds)

# AI System Prompt Configuration
AI_SYSTEM_PROMPT_PATH = os.getenv('AI_SYSTEM_PROMPT_PATH', 'resources/assistant_system_prompt.txt')
AI_USE_CUSTOM_PROMPT = os.getenv('AI_USE_CUSTOM_PROMPT', 'true').lower() == 'true'



# AI Performance Configuration
AI_TIMEOUT_SECONDS = int(os.getenv('AI_TIMEOUT_SECONDS', '30'))  # Increased timeout for resource-constrained systems
AI_BATCH_SIZE = int(os.getenv('AI_BATCH_SIZE', '4'))  # For batch processing
AI_CUDA_WARMUP = os.getenv('AI_CUDA_WARMUP', 'false').lower() == 'true'  # Disabled for LM Studio
AI_CACHE_RESPONSES = os.getenv('AI_CACHE_RESPONSES', 'true').lower() == 'true'

# LM Studio AI Model Configuration - Centralized Timeouts and Confidence Thresholds
AI_CONNECTION_TEST_TIMEOUT = int(os.getenv('AI_CONNECTION_TEST_TIMEOUT', '15'))  # Timeout for testing LM Studio connection
AI_API_CALL_TIMEOUT = int(os.getenv('AI_API_CALL_TIMEOUT', '15'))  # Default timeout for LM Studio API calls
AI_COMMAND_PARSING_TIMEOUT = int(os.getenv('AI_COMMAND_PARSING_TIMEOUT', '15'))  # Timeout for AI-enhanced command parsing
AI_PERSONALIZED_MESSAGE_TIMEOUT = int(os.getenv('AI_PERSONALIZED_MESSAGE_TIMEOUT', '40'))  # Longer timeout for personalized messages
AI_CONTEXTUAL_RESPONSE_TIMEOUT = int(os.getenv('AI_CONTEXTUAL_RESPONSE_TIMEOUT', '35'))  # Timeout for contextual responses
AI_QUICK_RESPONSE_TIMEOUT = int(os.getenv('AI_QUICK_RESPONSE_TIMEOUT', '8'))  # Shorter timeout for real-time interactions

# Command Parsing Confidence Thresholds
AI_RULE_BASED_HIGH_CONFIDENCE_THRESHOLD = float(os.getenv('AI_RULE_BASED_HIGH_CONFIDENCE_THRESHOLD', '0.8'))  # Threshold for high-confidence rule-based parsing
AI_AI_ENHANCED_CONFIDENCE_THRESHOLD = float(os.getenv('AI_AI_ENHANCED_CONFIDENCE_THRESHOLD', '0.6'))  # Threshold for using AI-enhanced parsing results
AI_RULE_BASED_FALLBACK_THRESHOLD = float(os.getenv('AI_RULE_BASED_FALLBACK_THRESHOLD', '0.3'))  # Threshold for fallback to rule-based parsing
AI_AI_PARSING_BASE_CONFIDENCE = float(os.getenv('AI_AI_PARSING_BASE_CONFIDENCE', '0.7'))  # Base confidence for successful AI parsing
AI_AI_PARSING_PARTIAL_CONFIDENCE = float(os.getenv('AI_AI_PARSING_PARTIAL_CONFIDENCE', '0.6'))  # Confidence for partial AI parsing results

# AI Response Length Configuration - Centralized limits for AI chatbot responses only
# Note: These limits apply ONLY to AI chatbot responses, not system-generated messages
AI_MAX_RESPONSE_LENGTH = int(os.getenv('AI_MAX_RESPONSE_LENGTH', '1200'))  # Maximum character length for AI-generated responses
AI_MAX_RESPONSE_WORDS = int(os.getenv('AI_MAX_RESPONSE_WORDS', '0')) or None  # Optional word limit (0 = disabled)
AI_MAX_RESPONSE_TOKENS = int(os.getenv('AI_MAX_RESPONSE_TOKENS', '300'))  # Maximum tokens for AI responses
AI_MIN_RESPONSE_LENGTH = int(os.getenv('AI_MIN_RESPONSE_LENGTH', '50'))  # Minimum character length to avoid too-short responses

# AI Temperature Configuration - Controls response randomness for different modes
AI_CHAT_TEMPERATURE = float(os.getenv('AI_CHAT_TEMPERATURE', '0.7'))  # Chat mode: conversational and varied
AI_COMMAND_TEMPERATURE = float(os.getenv('AI_COMMAND_TEMPERATURE', '0.0'))  # Command parsing: deterministic classification
AI_CLARIFICATION_TEMPERATURE = float(os.getenv('AI_CLARIFICATION_TEMPERATURE', '0.1'))  # Clarification: consistent clarification requests

# User Context Caching
CONTEXT_CACHE_TTL = int(os.getenv('CONTEXT_CACHE_TTL', '300'))  # 5 minutes
CONTEXT_CACHE_MAX_SIZE = int(os.getenv('CONTEXT_CACHE_MAX_SIZE', '100'))

# AI Response Cache Configuration
AI_RESPONSE_CACHE_TTL = int(os.getenv('AI_RESPONSE_CACHE_TTL', '300'))  # 5 minutes

# File Organization Settings
AUTO_CREATE_USER_DIRS = os.getenv('AUTO_CREATE_USER_DIRS', 'true').lower() == 'true'

# Service and Flag Files Configuration
MHM_FLAGS_DIR = os.getenv('MHM_FLAGS_DIR')  # Directory for service flag files (defaults to project root)

# Test Environment Configuration
TEST_LOGS_DIR = os.getenv('TEST_LOGS_DIR')  # Test logs directory (defaults to tests/logs)
TEST_DATA_DIR = os.getenv('TEST_DATA_DIR')  # Test data directory (defaults to tests/data)

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING').upper()  # Default to WARNING for quiet operation
LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '5242880'))  # 5MB default
LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))  # Keep 5 backup files
LOG_COMPRESS_BACKUPS = os.getenv('LOG_COMPRESS_BACKUPS', 'false').lower() == 'true'  # Compress old logs

# New organized logging structure
# In test mode, route all logs to tests/logs/ instead of logs/
if os.getenv('MHM_TESTING') == '1':
    _default_logs_dir = os.getenv('LOGS_DIR') or str(Path('tests') / 'logs')
else:
    _default_logs_dir = 'logs'
LOGS_DIR = _normalize_path(os.getenv('LOGS_DIR', _default_logs_dir))  # Main logs directory
LOG_BACKUP_DIR = _normalize_path(os.getenv('LOG_BACKUP_DIR', str(Path(LOGS_DIR) / 'backups')))  # Backup directory for rotated logs
LOG_ARCHIVE_DIR = _normalize_path(os.getenv('LOG_ARCHIVE_DIR', str(Path(LOGS_DIR) / 'archive')))  # Archive directory for old logs

# Component-specific log files
LOG_MAIN_FILE = _normalize_path(os.getenv('LOG_MAIN_FILE', str(Path(LOGS_DIR) / 'app.log')))  # Main application log
LOG_DISCORD_FILE = _normalize_path(os.getenv('LOG_DISCORD_FILE', str(Path(LOGS_DIR) / 'discord.log')))  # Discord bot log
LOG_AI_FILE = _normalize_path(os.getenv('LOG_AI_FILE', str(Path(LOGS_DIR) / 'ai.log')))  # AI interactions log
LOG_USER_ACTIVITY_FILE = _normalize_path(os.getenv('LOG_USER_ACTIVITY_FILE', str(Path(LOGS_DIR) / 'user_activity.log')))  # User activity log
LOG_ERRORS_FILE = _normalize_path(os.getenv('LOG_ERRORS_FILE', str(Path(LOGS_DIR) / 'errors.log')))  # Errors only log
LOG_COMMUNICATION_MANAGER_FILE = _normalize_path(os.getenv('LOG_COMMUNICATION_MANAGER_FILE', str(Path(LOGS_DIR) / 'communication_manager.log')))  # Communication manager log
LOG_EMAIL_FILE = _normalize_path(os.getenv('LOG_EMAIL_FILE', str(Path(LOGS_DIR) / 'email.log')))  # Email channel log
LOG_UI_FILE = _normalize_path(os.getenv('LOG_UI_FILE', str(Path(LOGS_DIR) / 'ui.log')))  # UI interactions log
LOG_FILE_OPS_FILE = _normalize_path(os.getenv('LOG_FILE_OPS_FILE', str(Path(LOGS_DIR) / 'file_ops.log')))  # File operations log
LOG_SCHEDULER_FILE = _normalize_path(os.getenv('LOG_SCHEDULER_FILE', str(Path(LOGS_DIR) / 'scheduler.log')))  # Scheduler log
LOG_AI_DEV_TOOLS_FILE = _normalize_path(os.getenv('LOG_AI_DEV_TOOLS_FILE', str(Path(LOGS_DIR) / 'ai_dev_tools.log')))  # AI development tools log

# Set up logger after path definitions to avoid circular imports
from core.logger import get_component_logger
logger = get_component_logger('main')

# Communication Channel Configurations (non-blocking)


EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER')
EMAIL_IMAP_SERVER = os.getenv('EMAIL_IMAP_SERVER')
EMAIL_SMTP_USERNAME = os.getenv('EMAIL_SMTP_USERNAME')
EMAIL_SMTP_PASSWORD = os.getenv('EMAIL_SMTP_PASSWORD')
if not all([EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD]):
    logger.warning("Email configuration incomplete - Email channel will be disabled")

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
# Optional: Discord application ID for slash command sync
_app_id_env = os.getenv('DISCORD_APPLICATION_ID')
DISCORD_APPLICATION_ID = int(_app_id_env) if _app_id_env and _app_id_env.isdigit() else None
if not DISCORD_BOT_TOKEN:
    logger.warning("DISCORD_BOT_TOKEN not found - Discord channel will be disabled")

@handle_errors("getting available channels", default_return=[])
def get_available_channels() -> List[str]:
    """
    Get list of available communication channels based on configuration.
    
    Returns:
        List[str]: List of available channel names that can be used with ChannelFactory
    """
    try:
        available_channels = []
        
        # Check email configuration
        if all([EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD]):
            available_channels.append('email')
        
        # Check Discord configuration
        if DISCORD_BOT_TOKEN:
            available_channels.append('discord')
        
        return available_channels
    except Exception as e:
        logger.error(f"Error getting available channels: {e}")
        return []

@handle_errors("getting channel class mapping", default_return={})
def get_channel_class_mapping() -> Dict[str, str]:
    """
    Get mapping of channel names to their class names for dynamic imports.
    
    Returns:
        Dict[str, str]: Mapping of channel name to fully qualified class name
    """
    try:
        return {
            'email': 'communication.communication_channels.email.bot.EmailBot',
            'discord': 'communication.communication_channels.discord.bot.DiscordBot',
            
        }
    except Exception as e:
        logger.error(f"Error getting channel class mapping: {e}")
        return {}

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
                    # Create directory
                    path_obj.mkdir(parents=True, exist_ok=True)
                    warnings.append(f"Created missing directory: {name} ({path})")
                except Exception as e:
                    error_msg = f"Cannot create directory {name} ({path}): {e}"
                    errors.append(error_msg)
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

@handle_errors("validating AI configuration", default_return=(False, ["Validation failed"], []))
def validate_ai_configuration() -> Tuple[bool, List[str], List[str]]:
    """Validate AI-related configuration settings."""
    try:
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
    except Exception as e:
        logger.error(f"Error validating AI configuration: {e}")
        return False, [f"AI configuration validation failed: {e}"], []

@handle_errors("validating communication channels", default_return=(False, ["Validation failed"], []))
def validate_communication_channels() -> Tuple[bool, List[str], List[str]]:
    """Validate communication channel configurations."""
    try:
        errors = []
        warnings = []
        available_channels = []
        
        # Check email configuration dynamically from environment
        email_config = {
            'EMAIL_SMTP_SERVER': os.getenv('EMAIL_SMTP_SERVER'),
            'EMAIL_IMAP_SERVER': os.getenv('EMAIL_IMAP_SERVER'),
            'EMAIL_SMTP_USERNAME': os.getenv('EMAIL_SMTP_USERNAME'),
            'EMAIL_SMTP_PASSWORD': os.getenv('EMAIL_SMTP_PASSWORD')
        }

        email_missing = [key for key, value in email_config.items() if not value]
        if email_missing:
            warnings.append(f"Email channel disabled - missing: {', '.join(email_missing)}")
        else:
            available_channels.append('email')
            # Validate email format
            email_user = email_config['EMAIL_SMTP_USERNAME']
            if email_user and '@' not in email_user:
                warnings.append("EMAIL_SMTP_USERNAME doesn't appear to be a valid email address")

        # Check Discord configuration dynamically from environment
        discord_token = os.getenv('DISCORD_BOT_TOKEN')
        if not discord_token:
            warnings.append("Discord channel disabled - DISCORD_BOT_TOKEN not configured")
        else:
            available_channels.append('discord')
            # Basic Discord token validation (should start with specific pattern)
            if not discord_token.startswith(('MT', 'OT', 'NT')):
                warnings.append("DISCORD_BOT_TOKEN doesn't match expected Discord bot token format")
        
        # If no channels are configured, treat as warning for flexibility
        if not available_channels:
            warnings.append("No communication channels are properly configured. At least one channel (Email or Discord) should be configured.")

        return len(errors) == 0, errors, warnings
    except Exception as e:
        logger.error(f"Error validating communication channels: {e}")
        return False, [f"Communication channels validation failed: {e}"], []

@handle_errors("validating logging configuration", default_return=(False, ["Validation failed"], []))
def validate_logging_configuration() -> Tuple[bool, List[str], List[str]]:
    """Validate logging configuration."""
    try:
        errors = []
        warnings = []
        
        # Check log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if LOG_LEVEL not in valid_log_levels:
            errors.append(f"Invalid LOG_LEVEL '{LOG_LEVEL}'. Must be one of: {', '.join(valid_log_levels)}")
        
        # Check log file path
        try:
            log_path = Path(LOG_MAIN_FILE)
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
            errors.append(f"Error validating log file path {LOG_MAIN_FILE}: {e}")
        
        # Validate log rotation settings
        if LOG_MAX_BYTES < 1024 * 1024:  # Less than 1MB
            warnings.append(f"LOG_MAX_BYTES ({LOG_MAX_BYTES}) is very small, consider increasing")
        
        if LOG_BACKUP_COUNT < 1:
            errors.append("LOG_BACKUP_COUNT must be at least 1")
        elif LOG_BACKUP_COUNT > 20:
            warnings.append(f"LOG_BACKUP_COUNT ({LOG_BACKUP_COUNT}) is very high, consider reducing")
        
        # Check current log file size if it exists
        if os.path.exists(LOG_MAIN_FILE):
            current_size = os.path.getsize(LOG_MAIN_FILE)
            current_size_mb = current_size / (1024 * 1024)
            if current_size_mb > 10:  # More than 10MB
                warnings.append(f"Current log file is {current_size_mb:.1f}MB, consider reducing LOG_LEVEL or increasing LOG_MAX_BYTES")
        
        return len(errors) == 0, errors, warnings
    except Exception as e:
        logger.error(f"Error validating logging configuration: {e}")
        return False, [f"Logging configuration validation failed: {e}"], []

@handle_errors("validating scheduler configuration", default_return=(False, ["Validation failed"], []))
def validate_scheduler_configuration() -> Tuple[bool, List[str], List[str]]:
    """Validate scheduler configuration."""
    try:
        errors = []
        warnings = []
        
        if SCHEDULER_INTERVAL < 10:
            errors.append("SCHEDULER_INTERVAL must be at least 10 seconds")
        elif SCHEDULER_INTERVAL < 30:
            warnings.append("SCHEDULER_INTERVAL is very low (< 30 seconds), may cause high CPU usage")
        elif SCHEDULER_INTERVAL > 3600:
            warnings.append("SCHEDULER_INTERVAL is very high (> 1 hour), may cause delayed responses")
        
        return len(errors) == 0, errors, warnings
    except Exception as e:
        logger.error(f"Error validating scheduler configuration: {e}")
        return False, [f"Scheduler configuration validation failed: {e}"], []

@handle_errors("validating file organization settings", default_return=(False, ["Validation failed"], []))
def validate_file_organization_settings() -> Tuple[bool, List[str], List[str]]:
    """Validate file organization settings."""
    try:
        errors = []
        warnings = []
        
        # These are boolean settings, so just check they're valid
        if not isinstance(AUTO_CREATE_USER_DIRS, bool):
            errors.append("AUTO_CREATE_USER_DIRS must be a boolean value")
        
        # Check for potential conflicts
        if AUTO_CREATE_USER_DIRS:
            warnings.append("AUTO_CREATE_USER_DIRS is enabled - user directories will be created automatically")
        
        return len(errors) == 0, errors, warnings
    except Exception as e:
        logger.error(f"Error validating file organization settings: {e}")
        return False, [f"File organization settings validation failed: {e}"], []

@handle_errors("validating environment variables", default_return=(False, ["Validation failed"], []))
def validate_environment_variables() -> Tuple[bool, List[str], List[str]]:
    """Check for common environment variable issues."""
    try:
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
    except Exception as e:
        logger.error(f"Error validating environment variables: {e}")
        return False, [f"Environment variables validation failed: {e}"], []

@handle_errors("validating all configuration", default_return={'valid': False, 'errors': ['Validation failed'], 'warnings': [], 'available_channels': [], 'summary': 'Configuration validation failed'})
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
    try:
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
    except Exception as e:
        logger.error(f"Error validating all configuration: {e}")
        return {
            'valid': False,
            'errors': [f"Configuration validation failed: {e}"],
            'warnings': [],
            'available_channels': [],
            'summary': 'Configuration validation failed'
        }

def validate_and_raise_if_invalid() -> List[str]:
    """Validate configuration and raise ConfigValidationError if invalid.
    
    Note: This function intentionally does not use @handle_errors decorator
    because it is designed to raise ConfigValidationError exceptions, which
    should propagate to the caller for proper error handling.
    
    Returns:
        List of available communication channels if validation passes.
    
    Raises:
        ConfigValidationError: If configuration is invalid with detailed error information.
    """
    try:
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
    except ConfigValidationError:
        # Re-raise configuration errors as-is
        raise
    except Exception as e:
        logger.error(f"Error validating and raising if invalid: {e}")
        raise ConfigValidationError(
            f"Configuration validation failed: {e}",
            missing_configs=[str(e)],
            warnings=[]
        )

@handle_errors("printing configuration report", default_return=False)
def print_configuration_report():
    """Print a detailed configuration report to the console."""
    try:
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
        print(f"  Log File: {LOG_MAIN_FILE}")
        print(f"  Log Level: {LOG_LEVEL}")
        print(f"  LM Studio URL: {LM_STUDIO_BASE_URL}")
        print(f"  AI Timeout: {AI_TIMEOUT_SECONDS}s")
        print(f"  Scheduler Interval: {SCHEDULER_INTERVAL}s")
        print(f"  Auto Create User Dirs: {AUTO_CREATE_USER_DIRS}")
        
        print("\n" + "="*60)
        
        return result['valid']
    except Exception as e:
        logger.error(f"Error printing configuration report: {e}")
        print(f"\nError generating configuration report: {e}")
        return False

# Data Management Functions
@handle_errors("getting user data directory", default_return="")
def get_user_data_dir(user_id: str) -> str:
    """Get the data directory for a specific user."""
    try:
        if not user_id:
            logger.error(f"Invalid user_id: {user_id}")
            # Return empty string to prevent creating files in root
            return ""
        return str(Path(BASE_DATA_DIR) / 'users' / user_id)
    except Exception as e:
        logger.error(f"Error getting user data directory for user {user_id}: {e}")
        return ""

@handle_errors("getting backups directory", default_return="data/backups")
def get_backups_dir() -> str:
    """Get the backups directory, redirected under tests when MHM_TESTING=1.
    Returns tests/data/backups if testing, otherwise BASE_DATA_DIR/backups.
    """
    if os.getenv('MHM_TESTING') == '1':
        # Use configurable test data directory
        test_data_dir = os.getenv('TEST_DATA_DIR', str(Path('tests') / 'data'))
        return str(Path(test_data_dir) / 'backups')
    return str(Path(BASE_DATA_DIR) / 'backups')

@handle_errors("getting user file path", default_return="")
def get_user_file_path(user_id: str, file_type: str) -> str:
    """Get the file path for a specific user file type."""
    user_dir = get_user_data_dir(user_id)
    
    # Prevent creating files in root directory
    if not user_dir or not user_dir.strip():
        logger.error(f"Invalid user_id: {user_id} - cannot create file path")
        return ""
    
    file_mapping = {
        # New structure
        'account': 'account.json',
        'preferences': 'preferences.json',
        'context': 'user_context.json',
        'schedules': 'schedules.json',
        # Other files
        'checkins': 'checkins.json',
        'chat_interactions': 'chat_interactions.json',
        'sent_messages': 'messages/sent_messages.json',
        'conversation_history': 'conversation_history.json'
    }
    return str(Path(user_dir) / file_mapping.get(file_type, f'{file_type}.json'))

@handle_errors("ensuring user directory exists", default_return=False)
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


@handle_errors("validating email configuration", user_friendly=False)
def validate_email_config():
    """Validate email configuration settings.
    
    Returns:
        bool: True if email configuration is valid
        
    Raises:
        ConfigurationError: If required email configuration variables are missing
    """
    required_vars = [EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD]
    if not all(required_vars):
        missing = [var for var in ['EMAIL_SMTP_SERVER', 'EMAIL_IMAP_SERVER', 'EMAIL_SMTP_USERNAME', 'EMAIL_SMTP_PASSWORD'] 
                  if not globals()[var]]
        raise ConfigurationError(f"Missing email configuration variables: {', '.join(missing)}")
    return True

@handle_errors("validating Discord configuration", user_friendly=False)
def validate_discord_config():
    """Validate Discord configuration settings.
    
    Returns:
        bool: True if Discord configuration is valid
        
    Raises:
        ConfigurationError: If DISCORD_BOT_TOKEN is missing
    """
    if not DISCORD_BOT_TOKEN:
        raise ConfigurationError("DISCORD_BOT_TOKEN is missing from environment configuration.")
    return True

@handle_errors("validating minimum configuration", user_friendly=False)
def validate_minimum_config():
    """Ensure at least one communication channel is configured"""
    available = get_available_channels()
    if not available:
        raise ConfigurationError("No communication channels are properly configured. Please set up at least one channel (Email or Discord).")
    return available