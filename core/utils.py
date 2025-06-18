# utils.py

import os
import re
import json
import shutil
import uuid
import time
import socket
import calendar
import logging
from datetime import datetime, timedelta
from threading import Lock
import pytz
from core.logger import get_logger
from core.config import (
    USER_INFO_DIR_PATH, MESSAGES_BY_CATEGORY_DIR_PATH, SENT_MESSAGES_DIR_PATH, 
    DEFAULT_MESSAGES_DIR_PATH, SCHEDULER_INTERVAL, USE_USER_SUBDIRECTORIES,
    get_user_data_dir, get_user_file_path, ensure_user_directory
)
from user.user_context import UserContext
import core.scheduler

logger = get_logger(__name__)

# Add a simple cache for user profile loading
_user_profile_cache = {}
_cache_timeout = 30  # Cache for 30 seconds to reduce repeated loads

# Add cache for schedule time periods as well
_schedule_periods_cache = {}

def create_reschedule_request(user_id, category):
    """Create a reschedule request flag file for the service to pick up"""
    try:
        # First check if service is running - if not, no need to reschedule
        # The service will pick up changes on next startup
        if not is_service_running():
            logger.debug(f"Service not running - schedule changes will be picked up on next startup")
            return
            
        import json
        import time
        import os
        
        # Create request data
        request_data = {
            'user_id': user_id,
            'category': category,
            'timestamp': time.time(),
            'source': 'ui_schedule_editor'
        }
        
        # Create unique filename
        timestamp = int(time.time() * 1000)  # milliseconds for uniqueness
        filename = f"reschedule_request_{user_id}_{category}_{timestamp}.flag"
        
        # Get the base directory (where the service looks for flag files)
        base_dir = os.path.dirname(os.path.dirname(__file__))
        request_file = os.path.join(base_dir, filename)
        
        # Write the request file
        with open(request_file, 'w') as f:
            json.dump(request_data, f)
        
        logger.info(f"Created reschedule request: {filename}")
        
    except Exception as e:
        logger.error(f"Failed to create reschedule request for user {user_id}, category {category}: {e}")

def is_service_running():
    """Check if the MHM service is currently running"""
    try:
        import psutil
        
        # Look for python processes running service.py
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if not proc.info['name'] or 'python' not in proc.info['name'].lower():
                    continue
                
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('service.py' in arg for arg in cmdline):
                    if proc.is_running():
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return False
    except Exception as e:
        logger.debug(f"Error checking service status: {e}")
        return False  # Assume not running if we can't check

# Throttler class
class Throttler:
    def __init__(self, interval):
        self.interval = interval
        self.last_run = None

    def should_run(self):
        from datetime import datetime, timedelta
        
        current_time = datetime.now()
        
        if self.last_run is None:
            return True
        
        # Parse human-readable timestamp format
        try:
            last_run_date = datetime.strptime(self.last_run, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            # If parsing fails, allow run
            return True
        
        time_since_last_run = (current_time - last_run_date).total_seconds()
        if time_since_last_run >= self.interval:
            self.last_run = current_time.strftime('%Y-%m-%d %H:%M:%S')
            return True
        
        return False

throttler = Throttler(SCHEDULER_INTERVAL)  # Updated to use SCHEDULER_INTERVAL

class InvalidTimeFormatError(Exception):
    pass

def verify_file_access(paths):
    # Removed throttler check to ensure file access is always verified
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

        # Log the path that will be returned
        logger.debug(f"Determined file path for {file_type}: {path}")
        return path
        
    except Exception as e:
        logger.error(f"Error determining file path for {file_type} with identifier {identifier}: {e}", exc_info=True)
        raise

def load_json_data(file_path):
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
            logger.debug(f"Data saved to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save data to {file_path}: {e}")
        raise

def get_all_user_ids():
    """Get all user IDs from both legacy and new file structures."""
    try:
        user_ids = set()
        
        if USE_USER_SUBDIRECTORIES:
            # New structure: look for user directories
            if os.path.exists(USER_INFO_DIR_PATH):
                for item in os.listdir(USER_INFO_DIR_PATH):
                    item_path = os.path.join(USER_INFO_DIR_PATH, item)
                    if os.path.isdir(item_path) and '-' in item and len(item) >= 8:
                        user_ids.add(item)
        
        # Always check for legacy files as well during transition
        if os.path.exists(USER_INFO_DIR_PATH):
            for filename in os.listdir(USER_INFO_DIR_PATH):
                if filename.endswith('.json') and not os.path.isdir(os.path.join(USER_INFO_DIR_PATH, filename)):
                    user_id = os.path.splitext(filename)[0]
                    if '-' in user_id and len(user_id) >= 8:
                        user_ids.add(user_id)
        
        valid_user_ids = [user_id for user_id in user_ids if user_id]  # Ensure no None values
        if None in valid_user_ids:
            logger.error("Found None in user IDs")
        return valid_user_ids
    except Exception as e:
        logger.error(f"Failed to get user IDs: {e}", exc_info=True)
        return []

def load_user_info_data(user_id):
    """Load user info data from appropriate file structure."""
    if user_id is None:
        logger.error("load_user_info_data called with None user_id")
        return None

    try:
        # Check cache first
        current_time = time.time()
        cache_key = f"load_{user_id}"
        
        if cache_key in _user_profile_cache:
            cached_data, cache_time = _user_profile_cache[cache_key]
            if current_time - cache_time < _cache_timeout:
                # Use cached data without logging every access
                return cached_data
        
        if USE_USER_SUBDIRECTORIES:
            # New structure: load from profile file
            ensure_user_directory(user_id)
            profile_file = get_user_file_path(user_id, 'profile')
            preferences_file = get_user_file_path(user_id, 'preferences')
            schedules_file = get_user_file_path(user_id, 'schedules')
            
            # Load profile data
            profile_data = load_json_data(profile_file) or {}
            
            # Load preferences and merge
            preferences_data = load_json_data(preferences_file) or {}
            if preferences_data:
                profile_data['preferences'] = preferences_data
            
            # Load schedules and merge
            schedules_data = load_json_data(schedules_file) or {}
            if schedules_data:
                profile_data['schedules'] = schedules_data
            
            # Add discord_user_id to top level if it exists in preferences
            if preferences_data.get('discord_user_id'):
                profile_data['discord_user_id'] = preferences_data['discord_user_id']
            
            # Cache the data
            _user_profile_cache[cache_key] = (profile_data, current_time)
            
            # Only log if data was actually loaded (avoid spam)
            if profile_data:
                logger.debug(f"User profile loaded: {user_id}")
            return profile_data if profile_data else None
        else:
            # Legacy structure
            user_info_file_path = determine_file_path('users', user_id)
            user_info = load_json_data(user_info_file_path)
            
            # Cache the data
            _user_profile_cache[cache_key] = (user_info, current_time)
            
            if user_info is None:
                logger.info(f"User file not found for user ID: {user_id} at path: {user_info_file_path}")
            else:
                logger.debug(f"User profile loaded: {user_id}")
            return user_info
    except Exception as e:
        logger.error(f"Error loading user info data for user {user_id}: {e}", exc_info=True)
        raise

def save_user_info_data(user_info, user_id):
    """Save user info data to appropriate file structure."""
    if user_id is None:
        logger.error("save_user_info_data called with None user_id")
        return

    try:
        if USE_USER_SUBDIRECTORIES:
            # New structure: split into profile, preferences, and schedules
            ensure_user_directory(user_id)
            
            # Extract profile data (core user info only, NO nested preferences/schedules)
            user_info_to_save = {
                "user_id": user_info.get("user_id", user_id),
                "internal_username": user_info.get("internal_username", ""),
                "active": user_info.get("active", True),
                "preferred_name": user_info.get("preferred_name", ""),
                "chat_id": user_info.get("chat_id", ""),
                "phone": user_info.get("phone", ""),
                "email": user_info.get("email", ""),
                "discord_user_id": user_info.get("discord_user_id", ""),
                "created_at": user_info.get("created_at", datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Extract preferences data
            preferences_data = user_info.get("preferences", {})
            if user_info.get("discord_user_id"):
                preferences_data["discord_user_id"] = user_info["discord_user_id"]
            
            # Extract schedules data
            schedules_data = user_info.get("schedules", {})
            
            # Add file tracking to profile for reference purposes only
            user_info_to_save["message_files"] = {}
            if preferences_data.get("categories"):
                for category in preferences_data["categories"]:
                    message_file_path = determine_file_path('messages', f'{category}/{user_id}')
                    user_info_to_save["message_files"][category] = {
                        "path": message_file_path,
                        "exists": os.path.exists(message_file_path),
                        "last_modified": datetime.fromtimestamp(os.path.getmtime(message_file_path)).strftime('%Y-%m-%d %H:%M:%S') if os.path.exists(message_file_path) else None
                    }
            
            # Save all files
            profile_file = get_user_file_path(user_id, 'profile')
            preferences_file = get_user_file_path(user_id, 'preferences')
            schedules_file = get_user_file_path(user_id, 'schedules')
            
            save_json_data(user_info_to_save, profile_file)
            save_json_data(preferences_data, preferences_file)
            save_json_data(schedules_data, schedules_file)
            
            logger.debug(f"User info saved for user {user_id}")
        else:
            # Legacy structure
            file_path = determine_file_path('users', user_id)
            save_json_data(user_info, file_path)
            logger.debug(f"User info saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving user info data for user {user_id}: {e}", exc_info=True)
        raise

def get_user_info(user_id, field=None):
    """Get user info for a specific user and optionally a specific field."""
    if user_id is None:
        logger.error("get_user_info called with None user_id")
        return None

    try:
        # Check cache first
        current_time = time.time()
        cache_key = user_id
        
        if cache_key in _user_profile_cache:
            cached_data, cache_time = _user_profile_cache[cache_key]
            if current_time - cache_time < _cache_timeout:
                # Use cached data without logging every access
                if field:
                    return cached_data.get(field)
                return cached_data
        
        # Check for new JSON structure first (profile data)
        user_info_file_path = determine_file_path('users', user_id)
        profile_data = load_json_data(user_info_file_path)
        
        if profile_data and 'profile' in profile_data:
            # Cache the data
            _user_profile_cache[cache_key] = (profile_data['profile'], current_time)
            
            # Only log if data was actually loaded (avoid spam)
            if profile_data:
                logger.debug(f"User profile loaded: {user_id}")
            
            if field:
                return profile_data['profile'].get(field)
            return profile_data['profile']
        else:
            # Legacy structure
            user_info_file_path = determine_file_path('users', user_id)
            user_info = load_json_data(user_info_file_path)
            
            if user_info:
                # Cache the data
                _user_profile_cache[cache_key] = (user_info, current_time)
                # Only log if data was actually loaded (avoid spam)
                logger.debug(f"User profile loaded: {user_id}")
            else:
                logger.info(f"User file not found for user ID: {user_id} at path: {user_info_file_path}")
            
            if field:
                return user_info.get(field) if user_info else None
            return user_info
    except Exception as e:
        logger.error(f"Error getting user info for user {user_id}: {e}", exc_info=True)
        raise

def get_user_preferences(user_id, field=None):
    if not user_id:
        logger.error("get_user_preferences called with None user_id")
        return None

    try:
        if USE_USER_SUBDIRECTORIES:
            # New structure: load directly from preferences file
            preferences_file = get_user_file_path(user_id, 'preferences')
            preferences = load_json_data(preferences_file) or {}
            
            # Also get email from profile if not in preferences
            if not preferences.get('email'):
                profile_file = get_user_file_path(user_id, 'profile')
                profile_data = load_json_data(profile_file) or {}
                if profile_data.get('email'):
                    preferences['email'] = profile_data['email']
        else:
            # Legacy structure
            preferences = get_user_info(user_id, ['preferences']) or {}
            preferences['email'] = get_user_info(user_id, ['email']) or ''  # Include email if available
        
        preferences['messaging_service'] = preferences.get('messaging_service', 'email')  # Default to 'email'
        
        if field:
            field_value = preferences
            try:
                for key in field:
                    field_value = field_value[key]
                return field_value
            except KeyError:
                logger.warning(f"Field path {field} not found in preferences for user_id {user_id}")
                return None
        else:
            # Only log if preferences exist and debug level verbosity is high
            if preferences and logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"User preferences loaded: {user_id}")
            return preferences
    except Exception as e:
        logger.error(f"Error getting user preferences for user {user_id}, field {field}: {e}", exc_info=True)
        raise
    
def ensure_unique_ids(data):
    try:
        existing_ids = set()
        for message in data['messages']:
            if 'message_id' not in message or message['message_id'] in existing_ids:
                message['message_id'] = str(uuid.uuid4())
            existing_ids.add(message['message_id'])
        return data
    except Exception as e:
        logger.error(f"Error ensuring unique IDs in data: {e}", exc_info=True)
        raise

def load_and_ensure_ids(user_id):
    if user_id is None:
        logger.error("load_and_ensure_ids called with None user_id")
        return

    try:
        categories = get_user_preferences(user_id, ['categories'])
        if categories is not None and isinstance(categories, list):
            for category in categories:
                try:
                    file_path = determine_file_path('messages', f'{category}/{user_id}')
                    data = load_json_data(file_path)
                    if data is None:
                        logger.info(f"No data found for category '{category}' and user '{user_id}', creating new data structure.")
                        data = {'messages': []}
                    data = ensure_unique_ids(data)
                    save_json_data(data, file_path)
                    logger.debug(f"Ensured message ids are unique for user '{user_id}'")
                except Exception as e:
                    logger.error(f"Error processing category '{category}' for user '{user_id}': {e}", exc_info=True)
        else:
            logger.error(f"Expected list for categories, got {type(categories)} for user '{user_id}'")
    except Exception as e:
        logger.error(f"Error loading and ensuring IDs for user {user_id}: {e}", exc_info=True)
        raise

def get_schedule_time_periods(user_id, category):
    """Get schedule time periods for a specific user and category."""
    if user_id is None:
        logger.error("get_schedule_time_periods called with None user_id")
        return {}

    try:
        # Check cache first
        current_time = time.time()
        cache_key = f"{user_id}_{category}"
        
        if cache_key in _schedule_periods_cache:
            cached_data, cache_time = _schedule_periods_cache[cache_key]
            if current_time - cache_time < _cache_timeout:
                # Use cached data without logging every access
                return cached_data
        
        user_info = load_user_info_data(user_id)
        if not user_info:
            logger.error(f"User {user_id} not found.")
            return {}

        schedules = user_info.get('schedules', {})
        periods = schedules.get(category, {})

        if periods:
            for period in periods:
                try:
                    start_time_str = periods[period]['start']
                    start_time_obj = datetime.strptime(start_time_str, "%H:%M")
                    periods[period]['start_time_obj'] = start_time_obj
                except (KeyError, ValueError) as e:
                    logger.warning(f"Error parsing start time for period {period} in category {category}: {e}")
                    continue

            if periods:
                periods[period]['start_time_obj'] = start_time_obj

            sorted_periods = dict(sorted(periods.items(), key=lambda item: item[1]['start_time_obj']))

            for period in sorted_periods:
                del sorted_periods[period]['start_time_obj']

            # Cache the results
            _schedule_periods_cache[cache_key] = (sorted_periods, current_time)
            
            # Only log once per cache refresh instead of every access
            logger.debug(f"Retrieved and sorted schedule time periods for user {user_id}, category {category}")
            return sorted_periods
        else:
            logger.error(f"No schedule data found for category: {category}.")
            return {}
    except Exception as e:
        logger.error(f"Error getting schedule time periods for user {user_id}, category {category}: {e}", exc_info=True)
        raise

def set_schedule_period_active(user_id, category, period_name, active=True):
    user_info = load_user_info_data(user_id)
    if not user_info:
        logger.error(f"User {user_id} not found.")
        return False
    
    schedules = user_info.get('schedules', {})
    category_schedule = schedules.get(category, {})
    period = category_schedule.get(period_name)

    if period:
        period['active'] = active
        save_user_info_data(user_info, user_id)
        status = "enabled" if active else "disabled"
        logger.info(f"Period {period_name} in category {category} for user {user_id} has been {status}.")
    else:
        logger.error(f"Period {period_name} not found in category {category} for user {user_id}.")
        return False
    return True

def is_schedule_period_active(user_id, category, period_name):
    user_info = load_user_info_data(user_id)
    if not user_info:
        return False

    schedules = user_info.get('schedules', {})
    category_schedule = schedules.get(category, {})
    period = category_schedule.get(period_name, {})
    
    return period.get('active', True)  # Defaults to active if the field is missing

def get_current_time_periods_with_validation(user_id, category):
    """
    Returns the current active time periods for a user and category.
    If no active period is found, defaults to all periods.
    """
    if user_id is None:
        logger.error("get_current_time_periods_with_validation called with None user_id")
        return [], []

    try:
        current_datetime = datetime.now().time()  # Get current time
        current_time_str = current_datetime.strftime('%H:%M')
        time_periods = get_schedule_time_periods(user_id, category)

        valid_periods = list(time_periods.keys())
        matching_periods = []

        # Check if current time falls within any defined periods
        for period, times in time_periods.items():
            start_time, end_time = times['start'], times['end']
            if start_time <= current_time_str <= end_time:
                matching_periods.append(period)

        if not matching_periods:
            # Defaulting to all periods if no match is found
            logger.info("Current time is not within any defined period, defaulting to all periods.")
            return valid_periods, valid_periods

        logger.debug(f"Current time periods: {matching_periods}, Valid periods: {valid_periods}")
        return matching_periods, valid_periods
    except Exception as e:
        logger.error(f"Error getting current time periods for user {user_id}, category {category}: {e}", exc_info=True)
        raise

def add_user_info(user_id, user_info):
    if user_id is None:
        logger.error("add_user_info called with None user_id")
        return

    try:
        file_path = determine_file_path('users', user_id)
        existing_data = load_json_data(file_path) or {}
        existing_data.update(user_info)
        save_user_info_data(existing_data, user_id)
        logger.debug(f"Added/Updated user info for user_id {user_id}: {existing_data}")

        default_messages_path = DEFAULT_MESSAGES_DIR_PATH
        user_messages_path = MESSAGES_BY_CATEGORY_DIR_PATH
        for category in user_info['preferences']['categories']:
            category_file = f'{category}.json'
            user_category_path = os.path.join(user_messages_path, category, f'{user_id}.json')
            os.makedirs(os.path.dirname(user_category_path), exist_ok=True)
            
            if os.path.exists(os.path.join(default_messages_path, category_file)):
                shutil.copy(os.path.join(default_messages_path, category_file), user_category_path)
                logger.debug(f"Copied default {category} messages JSON for user {user_id}")
            else:
                with open(user_category_path, 'w', encoding='utf-8') as file:
                    json.dump({"messages": []}, file, indent=4)
                logger.warning(f"Default messages JSON for {category} not found. Created blank JSON for user {user_id}")
    except Exception as e:
        logger.error(f"Error adding user info for user {user_id}: {e}", exc_info=True)
        raise

def validate_and_format_time(time_str):
    hh_mm_pattern = r"^(2[0-3]|[01]?[0-9]):([0-5][0-9])$"
    h_hh_pattern = r"^(2[0-3]|[01]?[0-9])$"
    am_pm_pattern = r"^(1[0-2]|0?[1-9]):?([0-5][0-9])?\s*([AaPp][Mm])$"

    try:
        if re.match(hh_mm_pattern, time_str):
            return time_str

        if re.match(h_hh_pattern, time_str):
            return time_str + ":00"

        match = re.match(am_pm_pattern, time_str)
        if match:
            hour = int(match.group(1))
            minute = match.group(2) if match.group(2) else "00"
            period = match.group(3).lower()

            if period == "pm" and hour != 12:
                hour += 12
            if period == "am" and hour == 12:
                hour = 0

            return f"{hour:02}:{minute}"

        raise InvalidTimeFormatError(f"Invalid time format: {time_str}")
    except Exception as e:
        logger.error(f"Error validating and formatting time '{time_str}': {e}", exc_info=True)
        raise

def get_message_categories():
    """
    Retrieves message categories from the environment variable CATEGORIES.
    Allows for either a comma-separated string or a JSON array.
    """
    try:
        raw_categories = os.getenv('CATEGORIES')
        if not raw_categories:
            logger.error("No CATEGORIES found in environment. Returning empty list.")
            return []

        raw_categories = raw_categories.strip()

        # If it looks like JSON (starts with '['), try parsing it
        if raw_categories.startswith('[') and raw_categories.endswith(']'):
            try:
                parsed = json.loads(raw_categories)
                if isinstance(parsed, list):
                    category_list = [cat.strip() for cat in parsed if isinstance(cat, str) and cat.strip()]
                    logger.debug(f"Retrieved message categories from JSON list: {category_list}")
                    return category_list
                else:
                    # If JSON parsed but it's not a list, treat it as a fallback
                    logger.warning("CATEGORIES JSON is not a list. Falling back to comma-split logic.")
            except json.JSONDecodeError:
                logger.warning("Failed to parse CATEGORIES as JSON. Falling back to comma-split logic.")

        # Fallback: treat it as a comma-separated string
        category_list = [cat.strip() for cat in raw_categories.split(',') if cat.strip()]
        logger.debug(f"Retrieved message categories from comma-separated string: {category_list}")
        return category_list

    except Exception as e:
        logger.error(f"Error retrieving message categories: {e}", exc_info=True)
        raise

def load_default_messages(category):
    default_messages_file = os.path.join("C:/Users/Julie/projects/MHM/MHM/default_messages", f"{category}.json")
    try:
        with open(default_messages_file, 'r') as file:
            default_messages = json.load(file)
            logger.debug(f"Loaded default messages for category {category}")
            return default_messages
    except FileNotFoundError:
        logger.error(f"Default messages file not found for category: {category}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from the default messages file for category {category}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error occurred while loading default messages for category {category}: {e}", exc_info=True)
        return []

def is_valid_email(email):
    try:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    except Exception as e:
        logger.error(f"Error validating email '{email}': {e}", exc_info=True)
        raise

def is_valid_phone(phone):
    try:
        pattern = r'^\+?[1-9]\d{1,14}$'
        return re.match(pattern, phone) is not None
    except Exception as e:
        logger.error(f"Error validating phone '{phone}': {e}", exc_info=True)
        raise

def add_message(user_id, category, message_data, index=None):
    if user_id is None:
        logger.error("add_message called with None user_id")
        return

    try:
        file_path = determine_file_path('messages', f'{category}/{user_id}')
        data = load_json_data(file_path)
        
        if data is None:
            data = {'messages': []}
        
        if 'message_id' not in message_data:
            message_data['message_id'] = str(uuid.uuid4())
        
        if index is not None and 0 <= index < len(data['messages']):
            data['messages'].insert(index, message_data)
        else:
            data['messages'].append(message_data)
        
        save_json_data(data, file_path)
        logger.info(f"Added message to category {category} for user {user_id}: {message_data}")
    except Exception as e:
        logger.error(f"Error adding message for user {user_id}, category {category}: {e}", exc_info=True)
        raise

def edit_message(user_id, category, index, new_message_data):
    if user_id is None:
        logger.error("edit_message called with None user_id")
        return

    try:
        file_path = determine_file_path('messages', f'{category}/{user_id}')
        data = load_json_data(file_path)
        
        if data is None or 'messages' not in data or index >= len(data['messages']):
            raise ValueError("Invalid message index or category.")
        
        data['messages'][index] = new_message_data
        save_json_data(data, file_path)
        logger.info(f"Edited message in category {category} for user {user_id}, : {new_message_data}")
    except ValueError as ve:
        logger.error(f"ValueError in editing message: {ve}")
        raise
    except Exception as e:
        logger.error(f"Error editing message for user {user_id}, category {category}: {e}", exc_info=True)
        raise

def delete_message(user_id, category, message_id):
    if user_id is None:
        logger.error("delete_message called with None user_id")
        return

    try:
        file_path = determine_file_path('messages', f'{category}/{user_id}')
        data = load_json_data(file_path)
        
        if data is None or 'messages' not in data:
            raise ValueError("Invalid category or data file.")
        
        message_to_delete = next((msg for msg in data['messages'] if msg['message_id'] == message_id), None)
        
        if not message_to_delete:
            raise ValueError("Message ID not found.")
        
        data['messages'].remove(message_to_delete)
        save_json_data(data, file_path)
        logger.info(f"Deleted message with ID {message_id} in category {category} for user {user_id}.")
    except ValueError as ve:
        logger.error(f"ValueError in deleting message: {ve}")
        raise
    except Exception as e:
        logger.error(f"Error deleting message for user {user_id}, category {category}: {e}", exc_info=True)
        raise

def get_current_day_names():
    """Returns the name of the current day."""
    try:
        day_index = datetime.today().weekday()
        return [list(calendar.day_name)[day_index]]
    except Exception as e:
        logger.error(f"Error getting current day names: {e}", exc_info=True)
        return []

def store_sent_message(user_id, category, message_id, message):
    try:
        sent_messages_file_path = determine_file_path('sent_messages', user_id)
        sent_messages = load_json_data(sent_messages_file_path) or {}
        
        # Add the new message
        sent_messages.setdefault(category, []).append({
            "message_id": message_id,
            "message": message,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Clean up messages older than 1 year
        one_year_ago = datetime.now() - timedelta(days=365)
        cutoff_date = one_year_ago.strftime('%Y-%m-%d %H:%M:%S')
        
        for cat in sent_messages:
            if isinstance(sent_messages[cat], list):
                original_count = len(sent_messages[cat])
                # Keep only messages newer than 1 year
                sent_messages[cat] = [
                    msg for msg in sent_messages[cat] 
                    if msg.get('timestamp', '0000-00-00 00:00:00') > cutoff_date
                ]
                cleaned_count = len(sent_messages[cat])
                if original_count > cleaned_count:
                    logger.info(f"Cleaned up {original_count - cleaned_count} old messages from {cat} category for user {user_id}")
        
        save_json_data(sent_messages, sent_messages_file_path)
        logger.debug(f"Stored sent message for user {user_id}, category {category}.")
    except Exception as e:
        logger.error(f"Error storing sent message for user {user_id}, category {category}: {e}", exc_info=True)
        raise

def get_last_10_messages(user_id, category):
    if user_id is None:
        logger.error("get_last_10_messages called with None user_id")
        return []

    try:
        file_path = determine_file_path('sent_messages', user_id)
        data = load_json_data(file_path)
        
        if data is None:
            logger.warning(f"No sent messages found for user {user_id} in category {category}.")
            return []

        # Support both old and new formats
        messages = []
        if 'sent_messages' in data:
            # Old format: {"sent_messages": [{"category": [messages...]}, ...]}
            for entry in data['sent_messages']:
                if category in entry:
                    messages = entry[category]
                    break
        elif category in data:
            # New format: {"category": [messages...], ...}
            messages = data[category]
        
        if not messages:
            logger.info(f"No messages found in category {category} for user {user_id}.")
            return []

        # Return most recent responses (sorted by timestamp descending)
        if data:
            def get_timestamp_for_sorting(item):
                """Convert timestamp to float for consistent sorting"""
                # Handle case where item might be a string instead of a dictionary
                if isinstance(item, str):
                    # If it's a string, it's probably a malformed entry - assign it a very old timestamp
                    return 0.0
                elif not isinstance(item, dict):
                    # If it's not a dict or string, treat as very old
                    return 0.0
                
                timestamp = item.get('timestamp', '1970-01-01 00:00:00')
                try:
                    # Parse human-readable format
                    from datetime import datetime
                    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    return dt.timestamp()
                except (ValueError, TypeError):
                    # If parsing fails, use 0
                    return 0.0
            
            sorted_data = sorted(data, key=get_timestamp_for_sorting, reverse=True)
            last_10_messages = sorted_data[:10]

            logger.debug(f"Retrieved last 10 messages for user {user_id} in category {category}.")
            return last_10_messages
        return []
    except Exception as e:
        logger.error(f"Error retrieving last 10 messages for user {user_id}, category {category}: {e}", exc_info=True)
        return []

def add_schedule_period(category, period_name, start_time, end_time, scheduler_manager=None):
    try:
        user_id = UserContext().get_user_id()
        internal_username = UserContext().get_internal_username()
        logger.debug(f"Retrieved user_id: {user_id}, internal_username: {internal_username}")
        
        if not user_id:
            logger.error("User ID is not set in UserContext (add_schedule_period).")
            return
        
        user_info = load_user_info_data(user_id) or {}

        if user_info.get("user_id") != user_id:
            logger.error(f"Mismatch in user_id for user info data: expected {user_id}, found {user_info.get('user_id')}")
            return

        user_schedules = user_info.setdefault('schedules', {})
        category_schedules = user_schedules.setdefault(category, {})

        formatted_start_time = validate_and_format_time(start_time)
        formatted_end_time = validate_and_format_time(end_time)

        category_schedules[period_name.lower()] = {'start': formatted_start_time, 'end': formatted_end_time}

        save_user_info_data(user_info, user_id)
        logger.info(f"Added schedule period for user {internal_username}, category {category}: {category_schedules[period_name.lower()]}")
        
        # Only reset scheduler if available
        if scheduler_manager:
            scheduler_manager.reset_and_reschedule_daily_messages(category)
        else:
            logger.debug("No scheduler manager available for rescheduling")
            # Create a reschedule request for the service to pick up
            create_reschedule_request(user_id, category)
    except Exception as e:
        logger.error(f"Error adding schedule period: {e}", exc_info=True)
        raise

def edit_schedule_period(category, period_name, new_start_time, new_end_time, scheduler_manager=None):
    try:
        user_id = UserContext().get_user_id()
        internal_username = UserContext().get_internal_username()
        
        if not user_id:
            logger.error("User ID is not set in UserContext (edit_schedule_period).")
            return
        
        logger.debug(f"Attempting to edit period {period_name} for user {user_id} in category {category}")
        user_info = load_user_info_data(user_id) or {}

        if user_info.get("user_id") != user_id:
            logger.error(f"User ID {user_id} not found in user info data. Loaded user ID: {user_info.get('user_id')}")
            return

        schedules = user_info.get('schedules', {})
        category_schedules = schedules.get(category, {})

        if period_name not in category_schedules:
            logger.error(f"Period name {period_name} not found in category {category}.")
            return

        formatted_new_start_time = validate_and_format_time(new_start_time)
        formatted_new_end_time = validate_and_format_time(new_end_time)

        category_schedules[period_name] = {'start': formatted_new_start_time, 'end': formatted_new_end_time}

        save_user_info_data(user_info, user_id)
        logger.info(f"Edited schedule period for user {internal_username}, category {category}, period {period_name}: {category_schedules[period_name]}")
        
        # Only reset scheduler if available
        if scheduler_manager:
            scheduler_manager.reset_and_reschedule_daily_messages(category)
        else:
            logger.debug("No scheduler manager available for rescheduling")
            # Create a reschedule request for the service to pick up
            create_reschedule_request(user_id, category)
    except Exception as e:
        logger.error(f"Error editing schedule period: {e}", exc_info=True)
        raise

def delete_schedule_period(category, period_name, scheduler_manager=None):
    try:
        user_id = UserContext().get_user_id()
        internal_username = UserContext().get_internal_username()
        
        if not user_id:
            logger.error("User ID is not set in UserContext (delete_schedule_period).")
            return
        
        logger.debug(f"Attempting to delete period {period_name} for user {user_id} in category {category}")
        user_info = load_user_info_data(user_id) or {}

        if user_info.get("user_id") != user_id:
            logger.error(f"User ID {user_id} not found in user info data. Loaded user ID: {user_info.get('user_id')}")
            return

        schedules = user_info.get('schedules', {})
        category_schedules = schedules.get(category, {})

        if period_name not in category_schedules:
            logger.error(f"Period name {period_name} not found in category {category}.")
            return

        del category_schedules[period_name]

        save_user_info_data(user_info, user_id)
        logger.info(f"Deleted schedule period for user {internal_username}, category {category}, period {period_name}")
        
        # Only reset scheduler if available
        if scheduler_manager:
            scheduler_manager.reset_and_reschedule_daily_messages(category)
        else:
            logger.debug("No scheduler manager available for rescheduling")
            # Create a reschedule request for the service to pick up
            create_reschedule_request(user_id, category)
    except Exception as e:
        logger.error(f"Error deleting schedule period: {e}", exc_info=True)
        raise

def title_case(text: str) -> str:
    try:
        exceptions = ['a', 'an', 'and', 'at', 'but', 'by', 'for', 'in', 'nor', 'of', 'on', 'or', 'so', 'the', 'to', 'up', 'yet']
        words = text.split()
        title_cased_words = [word.capitalize() if word.lower() not in exceptions or idx == 0 else word.lower() for idx, word in enumerate(words)]
        result = ' '.join(title_cased_words)
        logger.debug(f"Converted '{text}' to title case: '{result}'")
        return result
    except Exception as e:
        logger.error(f"Error converting text to title case: {e}", exc_info=True)
        raise

def store_user_response(user_id: str, response_data: dict, response_type: str = "daily_checkin"):
    """
    Store user response data in appropriate file structure.
    """
    try:
        if USE_USER_SUBDIRECTORIES:
            # New structure: store in appropriate log file
            if response_type == "daily_checkin":
                log_file = get_user_file_path(user_id, 'daily_checkins')
            elif response_type == "chat_interaction":
                log_file = get_user_file_path(user_id, 'chat_interactions')
            elif response_type == "survey_response":
                log_file = get_user_file_path(user_id, 'survey_responses')
            else:
                log_file = get_user_file_path(user_id, f'{response_type}_log')
            
            ensure_user_directory(user_id)
            
            # Load existing data
            existing_data = load_json_data(log_file) or []
            
            # Add timestamp if not present
            if 'timestamp' not in response_data:
                response_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Append new response
            existing_data.append(response_data)
            
            # Save updated data
            save_json_data(existing_data, log_file)
            logger.debug(f"Stored {response_type} response for user {user_id}")
        else:
            # Legacy structure: store in user subdirectory
            user_dir = os.path.join(USER_INFO_DIR_PATH, user_id)
            os.makedirs(user_dir, exist_ok=True)
            
            filename = _get_response_log_filename(response_type)
            file_path = os.path.join(user_dir, filename)
            
            existing_data = load_json_data(file_path) or []
            if 'timestamp' not in response_data:
                response_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            existing_data.append(response_data)
            save_json_data(existing_data, file_path)
            logger.debug(f"Stored {response_type} response for user {user_id}")
    except Exception as e:
        logger.error(f"Error storing {response_type} response for user {user_id}: {e}", exc_info=True)
        raise

def store_daily_checkin_response(user_id: str, response_data: dict):
    """Store daily check-in response."""
    store_user_response(user_id, response_data, "daily_checkin")

def store_chat_interaction(user_id: str, user_message: str, ai_response: str, context_used: bool = False):
    """Store chat interaction for analysis and context."""
    interaction_data = {
        "user_message": user_message,
        "ai_response": ai_response,
        "context_used": context_used,
        "message_length": len(user_message),
        "response_length": len(ai_response),
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    store_user_response(user_id, interaction_data, "chat_interaction")
    logger.info(f"Stored chat_interaction response for user {user_id}: {interaction_data}")

def store_survey_response(user_id: str, survey_name: str, responses: dict):
    """Store survey response."""
    survey_data = {
        "survey_name": survey_name,
        "responses": responses
    }
    store_user_response(user_id, survey_data, "survey_response")

def _get_response_log_filename(response_type: str) -> str:
    """Get the filename for a response log type."""
    filename_mapping = {
        "daily_checkin": "daily_checkin_log.json",
        "chat_interaction": "chat_interaction_log.json", 
        "survey_response": "survey_response_log.json"
    }
    return filename_mapping.get(response_type, f"{response_type}_log.json")

def get_recent_responses(user_id: str, response_type: str = "daily_checkin", limit: int = 5):
    """Get recent responses for a user from appropriate file structure."""
    try:
        if USE_USER_SUBDIRECTORIES:
            # New structure
            if response_type == "daily_checkin":
                log_file = get_user_file_path(user_id, 'daily_checkins')
            elif response_type == "chat_interaction":
                log_file = get_user_file_path(user_id, 'chat_interactions')
            elif response_type == "survey_response":
                log_file = get_user_file_path(user_id, 'survey_responses')
            else:
                log_file = get_user_file_path(user_id, f'{response_type}_log')
            
            data = load_json_data(log_file) or []
        else:
            # Legacy structure
            user_dir = os.path.join(USER_INFO_DIR_PATH, user_id)
            filename = _get_response_log_filename(response_type)
            file_path = os.path.join(user_dir, filename)
            data = load_json_data(file_path) or []
        
        # Return most recent responses (sorted by timestamp descending)
        if data:
            def get_timestamp_for_sorting(item):
                """Convert timestamp to float for consistent sorting"""
                # Handle case where item might be a string instead of a dictionary
                if isinstance(item, str):
                    # If it's a string, it's probably a malformed entry - assign it a very old timestamp
                    return 0.0
                elif not isinstance(item, dict):
                    # If it's not a dict or string, treat as very old
                    return 0.0
                
                timestamp = item.get('timestamp', '1970-01-01 00:00:00')
                try:
                    # Parse human-readable format
                    from datetime import datetime
                    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    return dt.timestamp()
                except (ValueError, TypeError):
                    # If parsing fails, use 0
                    return 0.0
            
            sorted_data = sorted(data, key=get_timestamp_for_sorting, reverse=True)
            return sorted_data[:limit]
        return []
    except Exception as e:
        logger.error(f"Error getting recent {response_type} responses for user {user_id}: {e}")
        return []

def get_recent_daily_checkins(user_id: str, limit: int = 7):
    """Get the most recent daily check-ins for a user"""
    return get_recent_responses(user_id, "daily_checkin", limit)

def get_recent_chat_interactions(user_id: str, limit: int = 10):
    """Get recent chat interactions for a user."""
    return get_recent_responses(user_id, "chat_interaction", limit)

def get_recent_survey_responses(user_id: str, limit: int = 5):
    """Get recent survey responses for a user."""
    return get_recent_responses(user_id, "survey_response", limit)

def load_and_localize_datetime(datetime_str, timezone_str='America/Regina'):
    try:
        tz = pytz.timezone(timezone_str)
        naive_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        aware_datetime = tz.localize(naive_datetime)
        logger.debug(f"Localized datetime '{datetime_str}' to timezone '{timezone_str}': '{aware_datetime}'")
        return aware_datetime
    except Exception as e:
        logger.error(f"Error loading and localizing datetime '{datetime_str}' to timezone '{timezone_str}': {e}", exc_info=True)
        raise

def get_user_id_by_internal_username(internal_username):
    """
    Find the internal user_id by internal username.
    Updated to work with new file structure.
    """
    try:
        logger.info(f"Searching for internal_username: {internal_username}")
        
        # Use get_all_user_ids to get user IDs from both structures
        user_ids = get_all_user_ids()
        
        for user_id in user_ids:
            try:
                user_info = load_user_info_data(user_id)
                if user_info and user_info.get('internal_username') == internal_username:
                    logger.info(f"internal_username found: {internal_username} with user ID: {user_id}")
                    return user_id
            except Exception as e:
                logger.warning(f"Error loading user info for {user_id}: {e}")
                continue
        
        logger.info(f"internal_username not found: {internal_username}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving user ID by internal username '{internal_username}': {e}", exc_info=True)
        raise

def get_user_id_by_chat_id(chat_id):
    """
    Find the internal user_id by chat ID.
    Updated to work with new file structure.
    """
    try:
        logger.info(f"Searching for chat_id: {chat_id}")
        
        # Use get_all_user_ids to get user IDs from both structures
        user_ids = get_all_user_ids()
        
        for user_id in user_ids:
            try:
                user_info = load_user_info_data(user_id)
                if user_info and user_info.get('chat_id') == chat_id:
                    logger.info(f"chat_id found: {chat_id} with user ID: {user_id}")
                    return user_id
            except Exception as e:
                logger.warning(f"Error loading user info for {user_id}: {e}")
                continue
        
        logger.info(f"chat_id not found: {chat_id}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving user ID by chat ID '{chat_id}': {e}", exc_info=True)
        raise

def get_user_id_by_discord_user_id(discord_user_id):
    """
    Find the internal user_id by Discord user ID.
    Updated to work with new file structure.
    """
    try:
        logger.info(f"Searching for discord_user_id: {discord_user_id}")
        
        # Use get_all_user_ids to get user IDs from both structures
        user_ids = get_all_user_ids()
        
        for user_id in user_ids:
            try:
                user_info = load_user_info_data(user_id)
                if user_info:
                    # Check if discord_user_id matches in preferences
                    preferences = user_info.get('preferences', {})
                    stored_discord_id = preferences.get('discord_user_id', '')
                    
                    # Handle both string and integer comparisons
                    if str(stored_discord_id) == str(discord_user_id):
                        logger.info(f"discord_user_id found: {discord_user_id} with internal user ID: {user_id}")
                        return user_id
            except Exception as e:
                logger.warning(f"Error loading user info for {user_id}: {e}")
                continue
        
        logger.info(f"discord_user_id not found: {discord_user_id}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving user ID by Discord user ID '{discord_user_id}': {e}", exc_info=True)
        return None

def create_user_files(user_id, categories):
    """
    Creates files for a new user in the appropriate structure.
    Updated to support both legacy and new file structures.
    """
    try:
        if USE_USER_SUBDIRECTORIES:
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
            
        else:
            # Legacy structure: create sent messages file
            sent_messages_path = determine_file_path('sent_messages', user_id)
            if not os.path.exists(sent_messages_path):
                save_json_data({"messages": []}, sent_messages_path)
                logger.debug(f"Created blank sent messages JSON for user {user_id}")

            # Create user directory for response logs
            user_dir = os.path.join(USER_INFO_DIR_PATH, user_id)
            if not os.path.exists(user_dir):
                os.makedirs(user_dir, exist_ok=True)
                logger.debug(f"Created user directory: {user_dir}")

            # Create response log files
            response_log_types = ["daily_checkin", "chat_interaction", "survey_response"]
            for response_type in response_log_types:
                log_filename = _get_response_log_filename(response_type)
                log_path = os.path.join(user_dir, log_filename)
                if not os.path.exists(log_path):
                    save_json_data([], log_path)
                    logger.debug(f"Created {response_type} log: {log_filename}")

        # Create message files for each category (same for both structures)
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

def wait_for_network(timeout=60):
    """Wait for the network to be available, retrying every 5 seconds up to a timeout."""
    import time
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Attempt to connect to a common DNS server (Google DNS as an example)
            socket.create_connection(("8.8.8.8", 53))
            logger.debug("Network is available.")
            return True
        except OSError:
            logger.warning("Network not available, retrying...")
            time.sleep(5)  # Wait for 5 seconds before retrying
    logger.error("Network not available after waiting.")
    return False

def get_user_checkin_preferences(user_id: str) -> dict:
    """Get user's check-in preferences from their user info"""
    try:
        user_info = get_user_info(user_id)
        if not user_info:
            return {}
        
        return user_info.get('preferences', {}).get('checkins', {})
    except Exception as e:
        logger.error(f"Error getting check-in preferences for user {user_id}: {e}")
        return {}

def is_user_checkins_enabled(user_id: str) -> bool:
    """Check if check-ins are enabled for a user"""
    try:
        checkin_prefs = get_user_checkin_preferences(user_id)
        return checkin_prefs.get('enabled', False)
    except Exception as e:
        logger.error(f"Error checking if check-ins enabled for user {user_id}: {e}")
        return False

def get_user_checkin_questions(user_id: str) -> dict:
    """Get the enabled check-in questions for a user"""
    try:
        checkin_prefs = get_user_checkin_preferences(user_id)
        return checkin_prefs.get('questions', {})
    except Exception as e:
        logger.error(f"Error getting check-in questions for user {user_id}: {e}")
        return {}
