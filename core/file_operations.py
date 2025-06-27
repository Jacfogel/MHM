# file_operations.py
"""
File operations utilities for MHM.
Contains functions for file I/O, path determination, and file management.
"""

import os
import json
import shutil
import time
from datetime import datetime
from core.logger import get_logger
from core.config import (
    USER_INFO_DIR_PATH, MESSAGES_BY_CATEGORY_DIR_PATH, SENT_MESSAGES_DIR_PATH, 
    DEFAULT_MESSAGES_DIR_PATH, USE_USER_SUBDIRECTORIES, get_user_file_path, ensure_user_directory
)

logger = get_logger(__name__)

def verify_file_access(paths):
    """Verify that files exist and are accessible"""
    try:
        for path in paths:
            if not os.path.exists(path):
                logger.error(f"File not found at path: {path}")
            else:
                logger.debug(f"File verified: {path}")
    except Exception as e:
        logger.error(f"Error verifying file access: {e}", exc_info=True)
        raise

def determine_file_path(file_type, identifier):
    """
    Determine file path based on file type and identifier.
    Updated to support new organized structure.
    """
    try:
        if file_type == 'users':
            if USE_USER_SUBDIRECTORIES:
                # New structure: return profile file path
                return get_user_file_path(identifier, 'profile')
            else:
                # Legacy structure
                path = os.path.join(USER_INFO_DIR_PATH, f"{identifier}.json")
        elif file_type == 'messages':
            try:
                category, user_id = identifier.split('/')
                path = os.path.join(MESSAGES_BY_CATEGORY_DIR_PATH, category, f"{user_id}.json")
            except ValueError as e:
                logger.error(f"Error splitting identifier '{identifier}': {e}")
                raise
        elif file_type == 'sent_messages':
            if USE_USER_SUBDIRECTORIES:
                # New structure: sent messages are in user directory
                return get_user_file_path(identifier, 'sent_messages')
            else:
                # Legacy structure
                path = os.path.join(SENT_MESSAGES_DIR_PATH, f"{identifier}.json")
        elif file_type == 'default_messages':
            path = os.path.join(DEFAULT_MESSAGES_DIR_PATH, f"{identifier}.json")
        else:
            logger.error(f"Unknown file type: {file_type}")
            raise ValueError(f"Unknown file type: {file_type}")

        # Only log file paths for non-routine operations (not messages or user data operations)
        if file_type not in ['messages', 'users', 'sent_messages']:
            logger.debug(f"Determined file path for {file_type}: {path}")
        return path
        
    except Exception as e:
        logger.error(f"Error determining file path for {file_type} with identifier {identifier}: {e}", exc_info=True)
        raise

def load_json_data(file_path):
    """Load data from a JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from the file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error occurred when loading data from {file_path}: {e}")
    return None

def save_json_data(data, file_path):
    """Save data to a JSON file"""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            raise
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save data to {file_path}: {e}")
        raise

def create_user_files(user_id, categories):
    """
    Creates files for a new user in the appropriate structure.
    """
    try:
        # New structure: ensure user directory exists and create organized files
        ensure_user_directory(user_id)
        
        # Create profile file if it doesn't exist
        profile_file = get_user_file_path(user_id, 'profile')
        if not os.path.exists(profile_file):
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            profile_data = {
                "user_id": user_id,
                "internal_username": "",
                "active": True,
                "preferred_name": "",
                "chat_id": "",
                "phone": "",
                "email": "",
                "created_at": current_time,
                "last_updated": current_time
            }
            save_json_data(profile_data, profile_file)
            logger.debug(f"Created profile file for user {user_id}")
        
        # Create preferences file if it doesn't exist
        preferences_file = get_user_file_path(user_id, 'preferences')
        if not os.path.exists(preferences_file):
            save_json_data({}, preferences_file)
            logger.debug(f"Created preferences file for user {user_id}")
        
        # Create schedules file if it doesn't exist
        schedules_file = get_user_file_path(user_id, 'schedules')
        if not os.path.exists(schedules_file):
            save_json_data({}, schedules_file)
            logger.debug(f"Created schedules file for user {user_id}")
        
        # Initialize empty log files if they don't exist
        log_types = ["daily_checkins", "chat_interactions", "survey_responses", "sent_messages"]
        for log_type in log_types:
            log_file = get_user_file_path(user_id, log_type)
            if not os.path.exists(log_file):
                save_json_data([], log_file)
                logger.debug(f"Created {log_type} file for user {user_id}")

        # Create message files for each category
        for category in categories:
            category_path = determine_file_path('messages', f'{category}/{user_id}')
            if not os.path.exists(category_path):
                default_category_path = determine_file_path('default_messages', category)
                if os.path.exists(default_category_path):
                    # Ensure directory exists before copying
                    os.makedirs(os.path.dirname(category_path), exist_ok=True)
                    shutil.copy(default_category_path, category_path)
                    logger.debug(f"Copied default {category} messages JSON for user {user_id}")
                else:
                    # Ensure directory exists before creating file
                    os.makedirs(os.path.dirname(category_path), exist_ok=True)
                    save_json_data({"messages": []}, category_path)
                    logger.warning(f"Default messages JSON for {category} not found. Created blank JSON for user {user_id}")
        
        # Auto-update message references and user index
        try:
            from core.user_data_manager import update_message_references, update_user_index
            update_message_references(user_id)
            update_user_index(user_id)
        except ImportError:
            pass  # User data manager not available yet
                    
        logger.info(f"Successfully created all user files for user {user_id}")
    except Exception as e:
        logger.error(f"Error creating user files for user {user_id}: {e}", exc_info=True)
        raise 