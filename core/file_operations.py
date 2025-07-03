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
    DEFAULT_MESSAGES_DIR_PATH, USE_USER_SUBDIRECTORIES, get_user_file_path, ensure_user_directory, get_user_data_dir
)
from core.error_handling import (
    error_handler, FileOperationError, DataError, handle_file_error,
    handle_errors, safe_file_operation
)

logger = get_logger(__name__)

@handle_errors("verifying file access", user_friendly=False)
def verify_file_access(paths):
    """Verify that files exist and are accessible"""
    for path in paths:
        if not os.path.exists(path):
            raise FileOperationError(f"File not found at path: {path}")
        else:
            logger.debug(f"File verified: {path}")

@handle_errors("determining file path", user_friendly=False)
def determine_file_path(file_type, identifier):
    """
    Determine file path based on file type and identifier.
    Updated to support new organized structure.
    """
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
            raise FileOperationError(f"Invalid identifier format '{identifier}': expected 'category/user_id'")
    elif file_type == 'sent_messages':
        if USE_USER_SUBDIRECTORIES:
            # New structure: sent messages are in user directory
            return get_user_file_path(identifier, 'sent_messages')
        else:
            # Legacy structure
            path = os.path.join(SENT_MESSAGES_DIR_PATH, f"{identifier}.json")
    elif file_type == 'default_messages':
        path = os.path.join(DEFAULT_MESSAGES_DIR_PATH, f"{identifier}.json")
    elif file_type == 'tasks':
        # New task file structure: data/users/{user_id}/tasks/{task_file}.json
        try:
            user_id, task_file = identifier.split('/')
            if USE_USER_SUBDIRECTORIES:
                # New structure: tasks are in user subdirectory
                user_dir = get_user_file_path(user_id, 'profile').replace('/profile.json', '')
                path = os.path.join(user_dir, 'tasks', f"{task_file}.json")
            else:
                # Legacy structure: tasks would be in main user directory
                user_dir = os.path.join(USER_INFO_DIR_PATH, user_id)
                path = os.path.join(user_dir, 'tasks', f"{task_file}.json")
        except ValueError as e:
            raise FileOperationError(f"Invalid task identifier format '{identifier}': expected 'user_id/task_file'")
    else:
        raise FileOperationError(f"Unknown file type: {file_type}")

    # Only log file paths for non-routine operations (not messages or user data operations)
    if file_type not in ['messages', 'users', 'sent_messages']:
        logger.debug(f"Determined file path for {file_type}: {path}")
    return path

@handle_errors("loading JSON data", default_return=None)
def load_json_data(file_path):
    """Load data from a JSON file with comprehensive error handling and auto-create user files if missing."""
    context = {'file_path': file_path}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError as e:
        # Try to auto-create user files if this is a user file
        # Detect user files by path
        if 'users' in file_path:
            # Try to extract user_id from the path
            import re
            match = re.search(r'users[\\/](.*?)[\\/]', file_path)
            user_id = None
            if match:
                user_id = match.group(1)
            else:
                # Try legacy structure
                match = re.search(r'users[\\/](.*?)(?:\\|/|\.|$)', file_path)
                if match:
                    user_id = match.group(1)
            if user_id:
                # Try to guess categories if possible (for schedules/messages)
                categories = []
                if 'schedules' in file_path or 'messages' in file_path:
                    # Try to find categories from existing files or default to ['motivational']
                    categories = ['motivational']
                create_user_files(user_id, categories)
                logger.info(f"Auto-created missing user files for user_id {user_id}")
                # Try loading again
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        return json.load(file)
                except Exception as e2:
                    logger.error(f"Failed to load file after auto-creation: {e2}")
                    return None
        if handle_file_error(e, file_path, "loading JSON data"):
            # Recovery was successful, try loading again
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    return json.load(file)
            except Exception as e2:
                logger.error(f"Failed to load file after recovery: {e2}")
                return None
        else:
            logger.error(f"File not found and recovery failed: {file_path}")
            return None
    except json.JSONDecodeError as e:
        if handle_file_error(e, file_path, "decoding JSON data"):
            # Recovery was successful, try loading again
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    return json.load(file)
            except Exception as e2:
                logger.error(f"Failed to load file after JSON recovery: {e2}")
                return None
        else:
            logger.error(f"JSON decode error and recovery failed: {file_path}")
            return None
    except Exception as e:
        logger.error(f"Unexpected error loading data from {file_path}: {e}")
        return None

@handle_errors("saving JSON data", user_friendly=False)
def save_json_data(data, file_path):
    """Save data to a JSON file with comprehensive error handling"""
    directory = os.path.dirname(file_path)
    
    # Ensure directory exists
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
        except Exception as e:
            raise FileOperationError(f"Failed to create directory {directory}: {e}")
    
    # Save the data
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        logger.debug(f"Successfully saved data to {file_path}")
    except Exception as e:
        raise FileOperationError(f"Failed to save data to {file_path}: {e}")

@handle_errors("creating user files", user_friendly=True)
def create_user_files(user_id, categories):
    """
    Creates files for a new user in the appropriate structure.
    """
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
        default_preferences = {
            "categories": [],  # Initialize with empty list instead of missing field
            "messaging_service": "email",
            "tasks_enabled": False  # Task management is disabled by default
        }
        save_json_data(default_preferences, preferences_file)
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

    # Create task files if they don't exist
    try:
        # Get user directory path using the correct function
        user_dir = get_user_data_dir(user_id)
        tasks_dir = os.path.join(user_dir, 'tasks')
        
        # Create tasks directory if it doesn't exist
        if not os.path.exists(tasks_dir):
            os.makedirs(tasks_dir, exist_ok=True)
            logger.debug(f"Created tasks directory for user {user_id}")
        
        # Create initial task files
        task_files = {
            'active_tasks': [],
            'completed_tasks': [],
            'task_schedules': {}
        }
        
        for task_file, default_data in task_files.items():
            task_file_path = os.path.join(tasks_dir, f"{task_file}.json")
            if not os.path.exists(task_file_path):
                save_json_data(default_data, task_file_path)
                logger.debug(f"Created {task_file} file for user {user_id}")
    except Exception as e:
        logger.error(f"Error creating task files for user {user_id}: {e}")

    # Create message files for each category
    for category in categories:
        try:
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
        except Exception as e:
            logger.error(f"Error creating message file for category {category} and user {user_id}: {e}")
            # Continue with other categories even if one fails
    
    # Auto-update message references and user index
    try:
        from core.user_data_manager import update_message_references, update_user_index
        update_message_references(user_id)
        update_user_index(user_id)
    except ImportError:
        logger.debug("User data manager not available, skipping reference updates")
    except Exception as e:
        logger.warning(f"Failed to update message references for user {user_id}: {e}")
                
    logger.info(f"Successfully created all user files for user {user_id}") 