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
from core.logger import get_logger, get_component_logger
from core.config import (
    USER_INFO_DIR_PATH,
    DEFAULT_MESSAGES_DIR_PATH,
    get_user_file_path, ensure_user_directory, get_user_data_dir
)
from core.error_handling import (
    error_handler, FileOperationError, DataError, handle_file_error,
    handle_errors, safe_file_operation
)

logger = get_component_logger('file_ops')

@handle_errors("verifying file access", user_friendly=False)
def verify_file_access(paths):
    """
    Verify that files exist and are accessible.
    
    Args:
        paths: List of file paths to verify
        
    Raises:
        FileOperationError: If any file is not found or inaccessible
    """
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
    
    Args:
        file_type: Type of file ('users', 'messages', 'schedules', 'sent_messages', 'default_messages', 'tasks')
        identifier: Identifier for the file (format depends on file_type)
        
    Returns:
        str: Full file path
        
    Raises:
        FileOperationError: If file_type is unknown or identifier format is invalid
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
    """
    Load data from a JSON file with comprehensive error handling and auto-create user files if missing.
    
    Args:
        file_path: Path to the JSON file to load
        
    Returns:
        dict/list: Loaded JSON data, or None if loading failed
    """
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

@handle_errors("saving JSON data", user_friendly=False, default_return=False)
def save_json_data(data, file_path):
    """
    Save data to a JSON file with comprehensive error handling.
    
    Args:
        data: Data to save (must be JSON serializable)
        file_path: Path where to save the file
        
    Returns:
        bool: True if successful, False if failed
        
    Raises:
        FileOperationError: If saving fails
    """
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
        return True
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
    
    # Always use a dict for user_prefs to avoid NoneType errors
    user_prefs = user_preferences or {}
    
    # Determine which features are enabled first
    tasks_enabled = False
    checkins_enabled = False
    
    if user_prefs:
        # Check for explicit feature enablement in account_data
        features_enabled = user_prefs.get('features_enabled', {})
        if features_enabled:
            tasks_enabled = features_enabled.get('tasks', False)
            checkins_enabled = features_enabled.get('checkins', False)
        else:
            # Fallback to checking settings (legacy approach)
            checkin_settings = user_prefs.get('checkin_settings', {})
            task_settings = user_prefs.get('task_settings', {})
            tasks_enabled = task_settings.get('enabled', False)
            checkins_enabled = checkin_settings.get('enabled', False)
    else:
        # Default to not creating files if no preferences provided
        tasks_enabled = False
        checkins_enabled = False
    
    # Create account.json with actual user data
    account_file = get_user_file_path(user_id, 'account')
    if not os.path.exists(account_file):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get actual user data from user_preferences if available
        internal_username = user_prefs.get('internal_username', "")
        chat_id = user_prefs.get('chat_id', "")
        phone = user_prefs.get('phone', "")
        email = user_prefs.get('email', "")
        discord_user_id = user_prefs.get('discord_user_id', "")
        timezone = user_prefs.get('timezone', "")
        
        # Determine chat_id based on channel type
        channel = user_prefs.get('channel', {})
        channel_type = channel.get('type', 'email')
        if channel_type == 'email':
            chat_id = email
        elif channel_type == 'telegram':
            chat_id = phone
        elif channel_type == 'discord':
            chat_id = discord_user_id
        
        account_data = {
            "user_id": user_id,
            "internal_username": internal_username,
            "account_status": "active",
            "chat_id": chat_id,
            "phone": phone,
            "email": email,
            "discord_user_id": discord_user_id,
            "timezone": timezone,
            "created_at": current_time,
            "updated_at": current_time,
            "features": {
                "automated_messages": "enabled" if categories else "disabled",
                "checkins": "enabled" if checkins_enabled else "disabled",
                "task_management": "enabled" if tasks_enabled else "disabled"
            }
        }
        save_json_data(account_data, account_file)
        logger.debug(f"Created account file for user {user_id}")
    
    # Create preferences.json with actual user data
    preferences_file = get_user_file_path(user_id, 'preferences')
    if not os.path.exists(preferences_file):
        # Use actual user preferences if available, otherwise create defaults
        if user_prefs:
            default_preferences = {
                "categories": categories or [],
                "channel": user_prefs.get('channel', {"type": "email"})
            }
            # Add check-in settings if available (but remove schedule periods)
            if checkins_enabled and 'checkin_settings' in user_prefs:
                checkin_settings = user_prefs['checkin_settings'].copy()
                # Remove time_periods from preferences (they go in schedules.json)
                if 'time_periods' in checkin_settings:
                    del checkin_settings['time_periods']
                default_preferences["checkin_settings"] = checkin_settings
            # Add task settings if available (but remove schedule periods)
            if tasks_enabled and 'task_settings' in user_prefs:
                task_settings = user_prefs['task_settings'].copy()
                # Remove time_periods from preferences (they go in schedules.json)
                if 'time_periods' in task_settings:
                    del task_settings['time_periods']
                default_preferences["task_settings"] = task_settings
        else:
            default_preferences = {
                "categories": categories or [],
                "channel": {"type": "email"}
            }
            # Only add check-in settings if check-ins are enabled (without enabled flag)
            if checkins_enabled:
                default_preferences["checkin_settings"] = {}
            # Only add task settings if tasks are enabled (without enabled flag)
            if tasks_enabled:
                default_preferences["task_settings"] = {}
        save_json_data(default_preferences, preferences_file)
        logger.debug(f"Created preferences file for user {user_id}")
    
    # Create user_context.json with actual personalization data
    context_file = get_user_file_path(user_id, 'context')
    if not os.path.exists(context_file):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get actual personalization data if available
        personalization_data = user_prefs.get('personalization_data', {})
        
        # Get custom fields with proper nesting
        custom_fields = personalization_data.get('custom_fields', {})
        
        context_data = {
            "preferred_name": personalization_data.get('preferred_name', ""),
            "gender_identity": personalization_data.get('gender_identity', []),
            "date_of_birth": personalization_data.get('date_of_birth', ""),
            "custom_fields": {
                "health_conditions": custom_fields.get('health_conditions', []),
                "medications_treatments": custom_fields.get('medications_treatments', []),
                "reminders_needed": custom_fields.get('reminders_needed', []),
                "allergies_sensitivities": custom_fields.get('allergies_sensitivities', [])
            },
            "interests": personalization_data.get('interests', []),
            "goals": personalization_data.get('goals', []),
            "loved_ones": personalization_data.get('loved_ones', []),
            "activities_for_encouragement": personalization_data.get('activities_for_encouragement', []),
            "notes_for_ai": personalization_data.get('notes_for_ai', []),
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
                # Don't create schedule periods for checkin/tasks during account creation
                # These will be created when the user actually enables the features
                continue
            else:
                # Create default periods for new categories (ALL + default)
                default_periods = {
                    "ALL": {
                        "active": True,
                        "days": ["ALL"],
                        "start_time": "00:00",
                        "end_time": "23:59"
                    },
                    f"{category.replace('_', ' ').title()} Message Default": {
                        "active": True,
                        "days": ["ALL"],
                        "start_time": "18:00",
                        "end_time": "20:00"
                    }
                }
                schedules_data[category] = default_periods
    
    # Create schedule periods for tasks if enabled
    if tasks_enabled and user_prefs and 'task_settings' in user_prefs:
        task_settings = user_prefs.get('task_settings', {})
        task_time_periods = task_settings.get('time_periods', {})
        if task_time_periods:
            schedules_data['tasks'] = {
                'periods': task_time_periods
            }
            logger.debug(f"Created task schedule periods for user {user_id}")
    
    # Create schedule periods for check-ins if enabled
    if checkins_enabled and user_prefs and 'checkin_settings' in user_prefs:
        checkin_settings = user_prefs.get('checkin_settings', {})
        checkin_time_periods = checkin_settings.get('time_periods', {})
        if checkin_time_periods:
            schedules_data['checkin'] = {
                'periods': checkin_time_periods
            }
            logger.debug(f"Created check-in schedule periods for user {user_id}")
    
    save_json_data(schedules_data, schedules_file)
    logger.debug(f"Created schedules file for user {user_id}")
    
    # Initialize empty log files if they don't exist
    log_types = ["checkins", "chat_interactions"]
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


    
    # Only create task files if tasks are enabled
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
    else:
        logger.debug(f"Tasks not enabled for user {user_id}, skipping task file creation")
    
    # Create checkins.json only if checkins are enabled
    if checkins_enabled:
        checkins_file = get_user_file_path(user_id, 'checkins')
        if not os.path.exists(checkins_file):
            save_json_data([], checkins_file)
            logger.debug(f"Created checkins file for user {user_id}")
    else:
        logger.debug(f"Check-ins not enabled for user {user_id}, skipping checkins file creation")

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