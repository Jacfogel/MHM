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
    USER_INFO_DIR_PATH,
    DEFAULT_MESSAGES_DIR_PATH,
    get_user_file_path, ensure_user_directory, get_user_data_dir
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
        # New structure: return account file path
        return get_user_file_path(identifier, 'account')
    elif file_type == 'messages':
        # New structure: data/users/{user_id}/messages/{category}.json
        try:
            category, user_id = identifier.split('/')
            user_dir = get_user_data_dir(user_id)
            path = os.path.join(user_dir, 'messages', f"{category}.json")
        except ValueError as e:
            raise FileOperationError(f"Invalid identifier format '{identifier}': expected 'category/user_id'")
    elif file_type == 'schedules':
        # Optional: per-category schedules
        try:
            category, user_id = identifier.split('/')
            user_dir = get_user_data_dir(user_id)
            path = os.path.join(user_dir, 'schedules', f"{category}.json")
        except ValueError:
            # Default to single schedules.json if not per-category
            user_dir = get_user_data_dir(identifier)
            path = os.path.join(user_dir, 'schedules.json')
    elif file_type == 'sent_messages':
        # Sent messages are now stored in user directories
        return get_user_file_path(identifier, 'sent_messages')
    elif file_type == 'default_messages':
        path = os.path.join(DEFAULT_MESSAGES_DIR_PATH, f"{identifier}.json")
    elif file_type == 'tasks':
        # New task file structure: data/users/{user_id}/tasks/{task_file}.json
        try:
            user_id, task_file = identifier.split('/')
            user_dir = get_user_data_dir(user_id)
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
                create_user_files(user_id, categories, None)  # No user preferences available in auto-creation
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
def create_user_files(user_id, categories, user_preferences=None):
    """
    Creates files for a new user in the appropriate structure.
    Ensures schedules.json contains a block for each category, plus checkin and task reminder blocks.
    
    Args:
        user_id: The user ID
        categories: List of message categories the user is opted into
        user_preferences: Optional user preferences dict to determine which files to create
    """
    ensure_user_directory(user_id)
    
    # Create account.json if it doesn't exist
    account_file = get_user_file_path(user_id, 'account')
    if not os.path.exists(account_file):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        account_data = {
            "user_id": user_id,
            "internal_username": "",
            "account_status": "active",
            "chat_id": "",
            "phone": "",
            "email": "",
            "discord_user_id": "",
            "created_at": current_time,
            "updated_at": current_time,
            "features": {
                "automated_messages": "enabled" if categories else "disabled",
                "checkins": "disabled",
                "task_management": "disabled"
            }
        }
        save_json_data(account_data, account_file)
        logger.debug(f"Created account file for user {user_id}")
    
    # Create preferences.json if it doesn't exist
    preferences_file = get_user_file_path(user_id, 'preferences')
    if not os.path.exists(preferences_file):
        default_preferences = {
            "categories": categories or [],
            "channel": {
                "type": "email"
            },
            "checkin_settings": {
                "enabled": False
            },
            "task_settings": {
                "enabled": False
            }
        }
        save_json_data(default_preferences, preferences_file)
        logger.debug(f"Created preferences file for user {user_id}")
    
    # Create user_context.json if it doesn't exist
    context_file = get_user_file_path(user_id, 'user_context')
    if not os.path.exists(context_file):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        context_data = {
            "preferred_name": "",
            "pronouns": [],
            "date_of_birth": "",
            "custom_fields": {
                "health_conditions": [],
                "medications_treatments": [],
                "reminders_needed": []
            },
            "interests": [],
            "goals": [],
            "loved_ones": [],
            "activities_for_encouragement": [],
            "notes_for_ai": [],
            "created_at": current_time,
            "last_updated": current_time
        }
        save_json_data(context_data, context_file)
        logger.debug(f"Created user_context file for user {user_id}")
    
    # Create schedules file if it doesn't exist
    schedules_file = get_user_file_path(user_id, 'schedules')
    if not os.path.exists(schedules_file):
        schedules_data = {}
    else:
        schedules_data = load_json_data(schedules_file) or {}
    # Ensure each category has a default schedule block
    for category in categories:
        if category not in schedules_data:
            if category in ("checkin", "tasks"):
                # Only create a 'default' period for checkin and tasks
                if category == "checkin":
                    default_period = {
                        "default": {
                            "active": True,
                            "days": ["ALL"],
                            "start_time": "10:00",
                            "end_time": "12:00"
                        }
                    }
                else:  # tasks
                    default_period = {
                        "default": {
                            "active": True,
                            "days": ["ALL"],
                            "start_time": "18:00",
                            "end_time": "20:00"
                        }
                    }
                schedules_data[category] = default_period
            else:
                # Create default periods for new categories (ALL + default)
                default_periods = {
                    "ALL": {
                        "active": True,
                        "days": ["ALL"],
                        "start_time": "00:00",
                        "end_time": "23:59"
                    },
                    "default": {
                        "active": True,
                        "days": ["ALL"],
                        "start_time": "18:00",
                        "end_time": "20:00"
                    }
                }
                schedules_data[category] = default_periods
    # Ensure checkin and tasks blocks exist
    if 'checkin' not in schedules_data:
        schedules_data['checkin'] = {
            "default": {
                "active": True,
                "days": ["ALL"],
                "start_time": "10:00",
                "end_time": "12:00"
            }
        }
    if 'tasks' not in schedules_data:
        schedules_data['tasks'] = {
            "default": {
                "active": True,
                "days": ["ALL"],
                "start_time": "18:00",
                "end_time": "20:00"
            }
        }
    save_json_data(schedules_data, schedules_file)
    logger.debug(f"Created schedules file for user {user_id}")
    
    # Initialize empty log files if they don't exist
    log_types = ["daily_checkins", "chat_interactions"]
    for log_type in log_types:
        log_file = get_user_file_path(user_id, log_type)
        if not os.path.exists(log_file):
            save_json_data([], log_file)
            logger.debug(f"Created {log_type} file for user {user_id}")
    
    # Create sent_messages.json in messages/ subdirectory
    user_messages_dir = os.path.join(get_user_data_dir(user_id), 'messages')
    os.makedirs(user_messages_dir, exist_ok=True)
    sent_messages_file = os.path.join(user_messages_dir, 'sent_messages.json')
    if not os.path.exists(sent_messages_file):
        save_json_data({}, sent_messages_file)
        logger.debug(f"Created sent_messages file for user {user_id}")

    # Determine which features are enabled
    tasks_enabled = False
    checkins_enabled = False
    
    if user_preferences:
        # Use provided preferences
        checkin_settings = user_preferences.get('checkin_settings', {})
        task_settings = user_preferences.get('task_settings', {})
        tasks_enabled = task_settings.get('enabled', False)
        checkins_enabled = checkin_settings.get('enabled', False)
    else:
        # Try to load user preferences from file
        try:
            from core.user_management import get_user_data
            user_data = get_user_data(user_id, 'preferences', auto_create=True)
            loaded_preferences = user_data.get('preferences')
            if loaded_preferences:
                checkin_settings = loaded_preferences.get('checkin_settings', {})
                task_settings = loaded_preferences.get('task_settings', {})
                tasks_enabled = task_settings.get('enabled', False)
                checkins_enabled = checkin_settings.get('enabled', False)
            else:
                # Default to creating files if no preferences found
                tasks_enabled = True
                checkins_enabled = True
        except Exception as e:
            logger.warning(f"Could not load user preferences for {user_id}, defaulting to create files: {e}")
            tasks_enabled = True
            checkins_enabled = True
    
    if tasks_enabled:
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
    
    # Create daily_checkins.json only if checkins are enabled
    if checkins_enabled:
        daily_checkins_file = get_user_file_path(user_id, 'daily_checkins')
        if not os.path.exists(daily_checkins_file):
            save_json_data([], daily_checkins_file)
            logger.debug(f"Created daily_checkins file for user {user_id}")

    # Create message files for each enabled category directly
    if categories:
        try:
            # Create messages directory for user
            user_messages_dir = os.path.join(get_user_data_dir(user_id), 'messages')
            os.makedirs(user_messages_dir, exist_ok=True)
            
            # Create message files for each category
            from core.message_management import create_message_file_from_defaults
            success_count = 0
            for category in categories:
                if create_message_file_from_defaults(user_id, category):
                    success_count += 1
                    logger.debug(f"Created message file for category {category} for user {user_id}")
                else:
                    logger.warning(f"Failed to create message file for category {category} for user {user_id}")
            
            if success_count == len(categories):
                logger.debug(f"Created all message files for user {user_id}")
            else:
                logger.warning(f"Failed to create {len(categories) - success_count} message files for user {user_id}")
        except Exception as e:
            logger.error(f"Error creating message files for user {user_id}: {e}")
    
    # Auto-update message references and user index
    try:
        from core.user_data_manager import update_message_references, update_user_index
        update_message_references(user_id)
        # Skip user index update during initial file creation to avoid circular dependency
        # The index will be updated when the user is actually created
    except ImportError:
        logger.debug("User data manager not available, skipping reference updates")
    except Exception as e:
        logger.warning(f"Failed to update message references for user {user_id}: {e}")
                
    logger.info(f"Successfully created all user files for user {user_id}") 