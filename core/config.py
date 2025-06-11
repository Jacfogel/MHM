# config.py

import os
from dotenv import load_dotenv
import logging

# Set up basic logging for config issues
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Custom exception for configuration-related errors."""
    pass

# Load environment variables
load_dotenv()

# Base data directory
BASE_DATA_DIR = os.getenv('BASE_DATA_DIR', 'data')

# Paths - Updated for better organization
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'app.log')  # Move log to root
USER_INFO_DIR_PATH = os.getenv('USER_INFO_DIR_PATH', os.path.join(BASE_DATA_DIR, 'users'))
MESSAGES_BY_CATEGORY_DIR_PATH = os.getenv('MESSAGES_BY_CATEGORY_DIR_PATH', os.path.join(BASE_DATA_DIR, 'messages'))
SENT_MESSAGES_DIR_PATH = os.getenv('SENT_MESSAGES_DIR_PATH', os.path.join(BASE_DATA_DIR, 'sent_messages'))
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
AI_TIMEOUT_SECONDS = int(os.getenv('AI_TIMEOUT_SECONDS', '15'))  # Increased timeout
AI_BATCH_SIZE = int(os.getenv('AI_BATCH_SIZE', '4'))  # For batch processing
AI_CUDA_WARMUP = os.getenv('AI_CUDA_WARMUP', 'false').lower() == 'true'  # Disabled for LM Studio
AI_CACHE_RESPONSES = os.getenv('AI_CACHE_RESPONSES', 'true').lower() == 'true'

# User Context Caching
CONTEXT_CACHE_TTL = int(os.getenv('CONTEXT_CACHE_TTL', '300'))  # 5 minutes
CONTEXT_CACHE_MAX_SIZE = int(os.getenv('CONTEXT_CACHE_MAX_SIZE', '100'))

# File Organization Settings
USE_USER_SUBDIRECTORIES = os.getenv('USE_USER_SUBDIRECTORIES', 'true').lower() == 'true'
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

# Data Management Functions
def get_user_data_dir(user_id: str) -> str:
    """Get the data directory for a specific user."""
    if USE_USER_SUBDIRECTORIES:
        return os.path.join(BASE_DATA_DIR, 'users', user_id)
    else:
        return USER_INFO_DIR_PATH

def get_user_file_path(user_id: str, file_type: str) -> str:
    """Get the file path for a specific user file type."""
    user_dir = get_user_data_dir(user_id)
    
    if USE_USER_SUBDIRECTORIES:
        file_mapping = {
            'profile': 'profile.json',
            'preferences': 'preferences.json',
            'schedules': 'schedules.json',
            'daily_checkins': 'daily_checkins.json',
            'chat_interactions': 'chat_interactions.json',
            'survey_responses': 'survey_responses.json',
            'sent_messages': 'sent_messages.json',
            'conversation_history': 'conversation_history.json'
        }
        return os.path.join(user_dir, file_mapping.get(file_type, f'{file_type}.json'))
    else:
        # Legacy flat structure
        return os.path.join(USER_INFO_DIR_PATH, f"{user_id}.json")

def ensure_user_directory(user_id: str) -> bool:
    """Ensure user directory exists if using subdirectories."""
    if not USE_USER_SUBDIRECTORIES or not AUTO_CREATE_USER_DIRS:
        return True
    
    user_dir = get_user_data_dir(user_id)
    try:
        os.makedirs(user_dir, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create user directory {user_dir}: {e}")
        return False

# Validation functions (for when strict validation is needed)
def validate_telegram_config():
    # Deactivated - Telegram channel is disabled
    raise ConfigError("Telegram channel has been deactivated.")
    # if not TELEGRAM_BOT_TOKEN:
    #     raise ConfigError("TELEGRAM_BOT_TOKEN is missing from environment configuration.")
    # return True

def validate_email_config():
    required_vars = [EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD]
    if not all(required_vars):
        missing = [var for var in ['EMAIL_SMTP_SERVER', 'EMAIL_IMAP_SERVER', 'EMAIL_SMTP_USERNAME', 'EMAIL_SMTP_PASSWORD'] 
                  if not globals()[var]]
        raise ConfigError(f"Missing email configuration variables: {', '.join(missing)}")
    return True

def validate_discord_config():
    if not DISCORD_BOT_TOKEN:
        raise ConfigError("DISCORD_BOT_TOKEN is missing from environment configuration.")
    return True

def get_available_channels():
    """Return list of channels that have complete configuration"""
    available = []
    
    # if TELEGRAM_BOT_TOKEN:  # Deactivated
    #     available.append('telegram')
    
    if all([EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD]):
        available.append('email')
    
    if DISCORD_BOT_TOKEN:
        available.append('discord')
    
    return available

def validate_minimum_config():
    """Ensure at least one communication channel is configured"""
    available = get_available_channels()
    if not available:
        raise ConfigError("No communication channels are properly configured. Please set up at least one channel (Telegram, Email, or Discord).")
    return available