# user_management.py
"""
User management utilities for MHM.
Contains functions for managing user accounts, preferences, context, and schedules.
"""

import os
import json
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from core.logger import get_logger
from core.file_operations import load_json_data, save_json_data, get_user_file_path, get_user_data_dir, determine_file_path
from core.config import ensure_user_directory
from core.error_handling import handle_errors

logger = get_logger(__name__)

# Cache configuration
_cache_timeout = 300  # 5 minutes
_user_account_cache = {}
_user_preferences_cache = {}
_user_context_cache = {}
_user_schedules_cache = {}

# Centralized registry for user data loaders
# This makes the system modular and easily expandable
USER_DATA_LOADERS = {
    'account': {
        'loader': None,  # Will be set after function definition
        'file_type': 'account',
        'default_fields': ['user_id', 'internal_username', 'account_status'],
        'metadata_fields': ['created_at', 'updated_at'],
        'description': 'User account information and settings'
    },
    'preferences': {
        'loader': None,  # Will be set after function definition
        'file_type': 'preferences',
        'default_fields': ['categories', 'channel'],
        'metadata_fields': ['last_updated'],
        'description': 'User preferences and configuration'
    },
    'context': {
        'loader': None,  # Will be set after function definition
        'file_type': 'user_context',
        'default_fields': ['preferred_name', 'pronouns'],
        'metadata_fields': ['created_at', 'last_updated'],
        'description': 'User context and personal information'
    },
    'schedules': {
        'loader': None,  # Will be set after function definition
        'file_type': 'schedules',
        'default_fields': [],
        'metadata_fields': ['last_updated'],
        'description': 'User schedule and timing preferences'
    }
}

def register_data_loader(data_type: str, loader_func, file_type: str, 
                        default_fields: List[str] = None, 
                        metadata_fields: List[str] = None,
                        description: str = ""):
    """
    Register a new data loader for the centralized system.
    
    Args:
        data_type: Unique identifier for the data type
        loader_func: Function that loads the data
        file_type: File type identifier
        default_fields: Commonly accessed fields
        metadata_fields: Fields that contain metadata
        description: Human-readable description
    """
    USER_DATA_LOADERS[data_type] = {
        'loader': loader_func,
        'file_type': file_type,
        'default_fields': default_fields or [],
        'metadata_fields': metadata_fields or [],
        'description': description
    }
    logger.info(f"Registered data loader for type: {data_type}")

def get_available_data_types() -> List[str]:
    """Get list of available data types."""
    return list(USER_DATA_LOADERS.keys())

def get_data_type_info(data_type: str) -> Optional[Dict[str, Any]]:
    """Get information about a specific data type."""
    return USER_DATA_LOADERS.get(data_type)

# ============================================================================
# CORE USER MANAGEMENT FUNCTIONS (New Data Structure)
# ============================================================================

@handle_errors("getting all user ids", default_return=[])
def get_all_user_ids():
    """Get all user IDs from the system."""
    from core.config import USER_INFO_DIR_PATH
    users_dir = USER_INFO_DIR_PATH
    if not os.path.exists(users_dir):
        return []
    
    user_ids = []
    for item in os.listdir(users_dir):
        item_path = os.path.join(users_dir, item)
        if os.path.isdir(item_path):
            # Check if this directory has the new structure
            account_file = os.path.join(item_path, 'account.json')
            if os.path.exists(account_file):
                user_ids.append(item)
    
    return user_ids

@handle_errors("loading user account data", default_return=None)
def load_user_account_data(user_id: str, auto_create: bool = True) -> Optional[Dict[str, Any]]:
    """Load user account data from account.json."""
    if not user_id:
        logger.error("load_user_account_data called with None user_id")
        return None
    
    # Check cache first
    current_time = time.time()
    cache_key = f"account_{user_id}"
    
    if cache_key in _user_account_cache:
        cached_data, cache_time = _user_account_cache[cache_key]
        if current_time - cache_time < _cache_timeout:
            return cached_data
    
    # Check if user directory exists (indicates user was created before)
    user_dir = os.path.dirname(get_user_file_path(user_id, 'account'))
    user_dir_exists = os.path.exists(user_dir)
    
    # Check if file exists before loading
    account_file = get_user_file_path(user_id, 'account')
    if not os.path.exists(account_file):
        if not auto_create:
            if not user_dir_exists:
                return None
            else:
                return None
        
        # Only auto-create if user directory exists (user was created before)
        if not user_dir_exists:
            logger.warning(f"User directory doesn't exist for {user_id}, not auto-creating account file")
            return None
        
        # Auto-create the file with default data
        logger.info(f"Auto-creating missing account file for user {user_id} (user directory exists)")
        ensure_user_directory(user_id)
        # Create default account data
        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        default_account = {
            "user_id": user_id,
            "internal_username": "",
            "account_status": "active",
            "chat_id": "",
            "phone": "",
            "email": "",
            "discord_user_id": "",
            "created_at": current_time_str,
            "updated_at": current_time_str,
            "features": {
                "automated_messages": "disabled",
                "checkins": "disabled",
                "task_management": "disabled"
            }
        }
        save_json_data(default_account, account_file)
        account_data = default_account
    else:
        # Load from file
        ensure_user_directory(user_id)
        account_data = load_json_data(account_file)
    
    # Cache the data
    _user_account_cache[cache_key] = (account_data, current_time)
    
    return account_data

@handle_errors("saving user account data")
def save_user_account_data(user_id: str, account_data: Dict[str, Any]) -> bool:
    """Save user account data to account.json."""
    if not user_id:
        logger.error("save_user_account_data called with None user_id")
        return False
    
    ensure_user_directory(user_id)
    account_file = get_user_file_path(user_id, 'account')
    
    # Add metadata
    account_data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    save_json_data(account_data, account_file)
    
    # Update cache
    cache_key = f"account_{user_id}"
    _user_account_cache[cache_key] = (account_data, time.time())
    
    # Update user index
    try:
        from core.user_data_manager import update_user_index
        update_user_index(user_id)
    except Exception as e:
        logger.warning(f"Failed to update user index after account update for user {user_id}: {e}")
    
    logger.debug(f"Account data saved for user {user_id}")
    return True

@handle_errors("loading user preferences data", default_return=None)
def load_user_preferences_data(user_id: str, auto_create: bool = True) -> Optional[Dict[str, Any]]:
    """Load user preferences data from preferences.json."""
    if not user_id:
        logger.error("load_user_preferences_data called with None user_id")
        return None
    
    # Check cache first
    current_time = time.time()
    cache_key = f"preferences_{user_id}"
    
    if cache_key in _user_preferences_cache:
        cached_data, cache_time = _user_preferences_cache[cache_key]
        if current_time - cache_time < _cache_timeout:
            return cached_data
    
    # Check if user directory exists (indicates user was created before)
    user_dir = os.path.dirname(get_user_file_path(user_id, 'preferences'))
    user_dir_exists = os.path.exists(user_dir)
    
    # Check if file exists before loading
    preferences_file = get_user_file_path(user_id, 'preferences')
    if not os.path.exists(preferences_file):
        if not auto_create:
            if not user_dir_exists:
                return None
            else:
                return None
        
        # Only auto-create if user directory exists (user was created before)
        if not user_dir_exists:
            logger.warning(f"User directory doesn't exist for {user_id}, not auto-creating preferences file")
            return None
        
        # Auto-create the file with default data
        logger.info(f"Auto-creating missing preferences file for user {user_id} (user directory exists)")
        ensure_user_directory(user_id)
        # Create default preferences data
        default_preferences = {
            "categories": [],
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
        preferences_data = default_preferences
    else:
        # Load from file
        ensure_user_directory(user_id)
        preferences_data = load_json_data(preferences_file)
        
        # If load_json_data returned None (corrupted file) and auto_create is False, return None
        if preferences_data is None and not auto_create:
            return None
        
        # Use empty dict as fallback only when auto_create is True
        preferences_data = preferences_data or {}

    # Cache the data
    _user_preferences_cache[cache_key] = (preferences_data, current_time)
    
    return preferences_data

@handle_errors("saving user preferences data")
def save_user_preferences_data(user_id: str, preferences_data: Dict[str, Any]) -> bool:
    """Save user preferences data to preferences.json."""
    if not user_id:
        logger.error("save_user_preferences_data called with None user_id")
        return False
    
    ensure_user_directory(user_id)
    preferences_file = get_user_file_path(user_id, 'preferences')
    
    save_json_data(preferences_data, preferences_file)
    
    # Update cache
    cache_key = f"preferences_{user_id}"
    _user_preferences_cache[cache_key] = (preferences_data, time.time())
    
    # Update user index
    try:
        from core.user_data_manager import update_user_index
        update_user_index(user_id)
    except Exception as e:
        logger.warning(f"Failed to update user index after preferences update for user {user_id}: {e}")
    
    logger.debug(f"Preferences data saved for user {user_id}")
    return True

@handle_errors("loading user context data", default_return=None)
def load_user_context_data(user_id: str, auto_create: bool = True) -> Optional[Dict[str, Any]]:
    """Load user context data from user_context.json."""
    if not user_id:
        logger.error("load_user_context_data called with None user_id")
        return None

    # Check cache first
    current_time = time.time()
    cache_key = f"context_{user_id}"
    
    if cache_key in _user_context_cache:
        cached_data, cache_time = _user_context_cache[cache_key]
        if current_time - cache_time < _cache_timeout:
            return cached_data
    
    # Check if user directory exists (indicates user was created before)
    user_dir = os.path.dirname(get_user_file_path(user_id, 'user_context'))
    user_dir_exists = os.path.exists(user_dir)
    
    # Check if file exists before loading
    context_file = get_user_file_path(user_id, 'user_context')
    if not os.path.exists(context_file):
        if not auto_create:
            if not user_dir_exists:
                return None
            else:
                return None
        
        # Only auto-create if user directory exists (user was created before)
        if not user_dir_exists:
            logger.warning(f"User directory doesn't exist for {user_id}, not auto-creating user context file")
            return None
        
        # Auto-create the file with default data
        logger.info(f"Auto-creating missing user context file for user {user_id} (user directory exists)")
        ensure_user_directory(user_id)
        # Create default context data
        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        default_context = {
            "preferred_name": "",
            "gender_identity": [],
            "date_of_birth": "",
            "custom_fields": {
                "reminders_needed": [],
                "health_conditions": [],
                "medications_treatments": [],
                "allergies_sensitivities": []
            },
            "interests": [],
            "goals": [],
            "loved_ones": [],
            "activities_for_encouragement": [],
            "notes_for_ai": [],
            "created_at": current_time_str,
            "last_updated": current_time_str
        }
        save_json_data(default_context, context_file)
        context_data = default_context
    else:
        # Load from file
        ensure_user_directory(user_id)
        context_data = load_json_data(context_file)
        
        # If load_json_data returned None (corrupted file) and auto_create is False, return None
        if context_data is None and not auto_create:
            return None
        
        # Use empty dict as fallback only when auto_create is True
        context_data = context_data or {}

    # Cache the data
    _user_context_cache[cache_key] = (context_data, current_time)
    
    return context_data

@handle_errors("saving user context data")
def save_user_context_data(user_id: str, context_data: Dict[str, Any]) -> bool:
    """Save user context data to user_context.json."""
    if not user_id:
        logger.error("save_user_context_data called with None user_id")
        return False
    
    ensure_user_directory(user_id)
    context_file = get_user_file_path(user_id, 'user_context')
    
    # Add metadata
    context_data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    save_json_data(context_data, context_file)
    
    # Update cache
    cache_key = f"context_{user_id}"
    _user_context_cache[cache_key] = (context_data, time.time())
    
    # Update user index
    try:
        from core.user_data_manager import update_user_index
        update_user_index(user_id)
    except Exception as e:
        logger.warning(f"Failed to update user index after context update for user {user_id}: {e}")
    
    logger.debug(f"User context data saved for user {user_id}")
    return True

@handle_errors("loading user schedules data", default_return=None)
def load_user_schedules_data(user_id: str, auto_create: bool = True) -> Optional[Dict[str, Any]]:
    """Load user schedules data from schedules.json."""
    if not user_id:
        logger.error("load_user_schedules_data called with None user_id")
        return None
    
    user_dir = os.path.dirname(get_user_file_path(user_id, 'schedules'))
    user_dir_exists = os.path.exists(user_dir)
    schedules_file = get_user_file_path(user_id, 'schedules')
    if not os.path.exists(schedules_file):
        if not auto_create:
            if not user_dir_exists:
                return None
            else:
                return None
        if not user_dir_exists:
            logger.warning(f"User directory doesn't exist for {user_id}, not auto-creating schedules file")
            return None
        # Auto-create the file with default data
        logger.info(f"Auto-creating missing schedules file for user {user_id} (user directory exists)")
        ensure_user_directory(user_id)
        default_schedules = {}
        save_json_data(default_schedules, schedules_file)
        schedules_data = default_schedules
    else:
        ensure_user_directory(user_id)
        schedules_data = load_json_data(schedules_file)
        if schedules_data is None and not auto_create:
            return None
        schedules_data = schedules_data or {}
    return schedules_data

@handle_errors("saving user schedules data")
def save_user_schedules_data(user_id: str, schedules_data: Dict[str, Any]) -> bool:
    """Save user schedules data to schedules.json."""
    if not user_id:
        logger.error("save_user_schedules_data called with None user_id")
        return False
    
    ensure_user_directory(user_id)
    schedules_file = get_user_file_path(user_id, 'schedules')
    
    save_json_data(schedules_data, schedules_file)
    
    logger.debug(f"Schedules data saved for user {user_id}")
    return True

@handle_errors("updating user schedules")
def update_user_schedules(user_id: str, schedules_data: Dict[str, Any]) -> bool:
    """Update user schedules data."""
    if not user_id:
        logger.error("update_user_schedules called with None user_id")
        return False
    
    return save_user_schedules_data(user_id, schedules_data)

def create_default_schedule_periods() -> Dict[str, Any]:
    """Create default schedule periods for a new category."""
    return {
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

def migrate_legacy_schedules_structure(schedules_data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate legacy schedules structure to new format."""
    migrated_data = {}
    
    for category, category_data in schedules_data.items():
        if isinstance(category_data, dict):
            # Check if this is already in new format
            if 'periods' in category_data:
                migrated_data[category] = category_data
            else:
                # This is legacy format - convert to new format
                legacy_periods = {}
                for period_name, period_data in category_data.items():
                    if isinstance(period_data, dict) and 'start' in period_data and 'end' in period_data:
                        legacy_periods[period_name] = period_data
                
                # Add default periods if none exist
                if not legacy_periods:
                    legacy_periods = create_default_schedule_periods()
                
                # Convert legacy periods to include days
                for period_name, period_data in legacy_periods.items():
                    if 'days' not in period_data:
                        period_data['days'] = ["ALL"]
                
                migrated_data[category] = {
                    "enabled": True,
                    "periods": legacy_periods
                }
        else:
            # Invalid data, create default structure
            migrated_data[category] = {
                "enabled": True,
                "periods": create_default_schedule_periods()
            }
    
    return migrated_data

def ensure_category_has_default_schedule(user_id: str, category: str) -> bool:
    """Ensure a category has default schedule periods if it doesn't exist."""
    if not user_id or not category:
        logger.warning(f"Invalid parameters: user_id={user_id}, category={category}")
        return False
    
    try:
        schedules_data = load_user_schedules_data(user_id) or {}
        logger.debug(f"Current schedules data for user {user_id}: {schedules_data}")
        
        # Migrate legacy structure if needed
        if schedules_data and any(isinstance(v, dict) and 'periods' not in v for v in schedules_data.values()):
            logger.info(f"Migrating legacy schedules structure for user {user_id}")
            schedules_data = migrate_legacy_schedules_structure(schedules_data)
            save_user_schedules_data(user_id, schedules_data)
        
        # Check if category exists and has periods
        category_exists = category in schedules_data
        has_periods = schedules_data.get(category, {}).get('periods') if category_exists else False
        
        logger.debug(f"Category '{category}' exists: {category_exists}, has periods: {has_periods}")
        
        if not category_exists or not has_periods:
            # Create default periods for this category
            default_periods = create_default_schedule_periods()
            logger.debug(f"Creating default periods for category '{category}': {default_periods}")
            
            if not category_exists:
                schedules_data[category] = {
                    "enabled": True,
                    "periods": default_periods
                }
            else:
                schedules_data[category]['periods'] = default_periods
            
            # Save the updated schedules
            save_user_schedules_data(user_id, schedules_data)
            logger.info(f"Created default schedule periods for category '{category}' for user {user_id}")
            return True
        
        logger.debug(f"Category '{category}' already has periods, skipping default creation")
        return True
    except Exception as e:
        logger.error(f"Error ensuring default schedule for category '{category}' for user {user_id}: {e}")
        return False

@handle_errors("updating user account")
def update_user_account(user_id: str, updates: Dict[str, Any], auto_create: bool = True) -> bool:
    """Update user account information."""
    if not user_id:
        logger.error("update_user_account called with None user_id")
        return False
    
    account_data = load_user_account_data(user_id, auto_create=auto_create)
    if account_data is None:
        logger.warning(f"Could not load or create account for user {user_id}")
        return False
    account_data.update(updates)
    return save_user_account_data(user_id, account_data)

@handle_errors("updating user preferences")
def update_user_preferences(user_id: str, updates: Dict[str, Any], auto_create: bool = True) -> bool:
    """Update user preferences."""
    if not user_id:
        logger.error("update_user_preferences called with None user_id")
        return False
    
    preferences_data = load_user_preferences_data(user_id, auto_create=auto_create)
    # If user didn't exist and couldn't be auto-created, preferences_data will be None
    if preferences_data is None:
        logger.warning(f"Could not load or create preferences for user {user_id}")
        return False
    
    # Check if categories are being updated
    if 'categories' in updates:
        old_categories = set(preferences_data.get('categories', []))
        new_categories = set(updates['categories'])
        added_categories = new_categories - old_categories
        
        logger.info(f"Categories update detected for user {user_id}: old={old_categories}, new={new_categories}, added={added_categories}")
        
        # Create default schedule periods for newly added categories
        for category in added_categories:
            logger.info(f"Creating default schedule for category '{category}' for user {user_id}")
            ensure_category_has_default_schedule(user_id, category)
        
        # Also ensure all categories have schedules (in case some were missing)
        ensure_all_categories_have_schedules(user_id)
        
        # Ensure message files exist for newly added categories
        if added_categories:
            try:
                from core.message_management import ensure_user_message_files
                result = ensure_user_message_files(user_id, list(added_categories))
                if result["success"]:
                    logger.info(f"Category update for user {user_id}: created {result['files_created']} message files for {len(added_categories)} new categories, directory_created={result['directory_created']}")
                else:
                    logger.warning(f"Category update for user {user_id}: created {result['files_created']} message files for {len(added_categories)} new categories, some failures occurred")
            except Exception as e:
                logger.error(f"Error creating message files for user {user_id} after category update: {e}")
    
    preferences_data.update(updates)
    return save_user_preferences_data(user_id, preferences_data)

@handle_errors("updating user context")
def update_user_context(user_id: str, updates: Dict[str, Any], auto_create: bool = True) -> bool:
    """Update user context information."""
    if not user_id:
        logger.error("update_user_context called with None user_id")
        return False
    
    context_data = load_user_context_data(user_id, auto_create=auto_create)
    if context_data is None:
        logger.warning(f"Could not load or create context for user {user_id}")
        return False
    context_data.update(updates)
    return save_user_context_data(user_id, context_data)

@handle_errors("creating new user")
def create_new_user(user_data: Dict[str, Any]) -> str:
    """Create a new user with the new data structure."""
    user_id = str(uuid.uuid4())
    
    # Create account data
    account_data = {
        "user_id": user_id,
        "internal_username": user_data.get('internal_username', ''),
        "account_status": "active",
        "chat_id": user_data.get('chat_id', ''),
        "phone": user_data.get('phone', ''),
        "email": user_data.get('email', ''),
        "discord_user_id": user_data.get('discord_user_id', ''),
        "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "features": {
            "automated_messages": "enabled" if user_data.get('categories') else "disabled",
            "checkins": "enabled" if user_data.get('checkin_settings', {}).get('enabled', False) else "disabled",
            "task_management": "enabled" if user_data.get('task_settings', {}).get('enabled', False) else "disabled"
        },
        "timezone": user_data.get("timezone", "")
    }
    
    # Create preferences data
    preferences_data = {
        "categories": user_data.get('categories', []),
        "channel": {
            "type": user_data.get('channel', {}).get('type', 'email')
        },
        "checkin_settings": user_data.get('checkin_settings', {})
    }
    
    # Remove redundant enabled flags from preferences since they're in account.json features
    if 'checkin_settings' in preferences_data and 'enabled' in preferences_data['checkin_settings']:
        del preferences_data['checkin_settings']['enabled']
    if 'task_management' in preferences_data and 'enabled' in preferences_data['task_management']:
        del preferences_data['task_management']['enabled']
    
    # Create user context data
    context_data = {
        "preferred_name": user_data.get('preferred_name', ''),
        "gender_identity": user_data.get('gender_identity', []),
        "date_of_birth": user_data.get('date_of_birth', ''),
        "custom_fields": {
            "reminders_needed": user_data.get('reminders_needed', []),
            "health_conditions": user_data.get('custom_fields', {}).get('health_conditions', []),
            "medications_treatments": user_data.get('custom_fields', {}).get('medications_treatments', []),
            "allergies_sensitivities": user_data.get('custom_fields', {}).get('allergies_sensitivities', [])
        },
        "interests": user_data.get('interests', []),
        "goals": user_data.get('goals', []),
        "loved_ones": user_data.get('loved_ones', []),
        "activities_for_encouragement": user_data.get('activities_for_encouragement', []),
        "notes_for_ai": user_data.get('notes_for_ai', []),
        "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Save all data
    save_user_account_data(user_id, account_data)
    save_user_preferences_data(user_id, preferences_data)
    save_user_context_data(user_id, context_data)
    
    # Create default schedule periods for initial categories
    categories = user_data.get('categories', [])
    for category in categories:
        ensure_category_has_default_schedule(user_id, category)
    
    # Update user index
    try:
        from core.user_data_manager import update_user_index
        update_user_index(user_id)
    except Exception as e:
        logger.warning(f"Failed to update user index for new user {user_id}: {e}")
    
    logger.info(f"Created new user: {user_id} ({user_data.get('internal_username', '')})")
    return user_id

@handle_errors("getting user id by internal username", default_return=None)
def get_user_id_by_internal_username(internal_username: str) -> Optional[str]:
    """Get user ID by internal username."""
    if not internal_username:
        return None
    
    user_ids = get_all_user_ids()
    for user_id in user_ids:
        user_data_result = get_user_data(user_id, 'account')
        account_data = user_data_result.get('account')
        if account_data and account_data.get('internal_username') == internal_username:
            return user_id
    
    return None

@handle_errors("getting user id by chat id", default_return=None)
def get_user_id_by_chat_id(chat_id: str) -> Optional[str]:
    """Get user ID by chat ID."""
    if not chat_id:
        return None
    
    user_ids = get_all_user_ids()
    for user_id in user_ids:
        user_data_result = get_user_data(user_id, 'account')
        account_data = user_data_result.get('account')
        if account_data and account_data.get('chat_id') == chat_id:
            return user_id
    
    return None

@handle_errors("getting user id by discord user id", default_return=None)
def get_user_id_by_discord_user_id(discord_user_id: str) -> Optional[str]:
    """Get user ID by Discord user ID."""
    if not discord_user_id:
        return None
    
    user_ids = get_all_user_ids()
    for user_id in user_ids:
        user_data_result = get_user_data(user_id, 'account')
        account_data = user_data_result.get('account')
        if account_data:
            stored_discord_id = account_data.get("discord_user_id", "")
            
            # Handle both string and integer comparisons
            if str(stored_discord_id) == str(discord_user_id):
                return user_id
    
    return None

@handle_errors("clearing user caches")
def clear_user_caches(user_id: Optional[str] = None):
    """Clear user data caches."""
    global _user_account_cache, _user_preferences_cache, _user_context_cache
    
    if user_id:
        # Clear specific user's cache
        account_key = f"account_{user_id}"
        preferences_key = f"preferences_{user_id}"
        context_key = f"context_{user_id}"
        
        if account_key in _user_account_cache:
            del _user_account_cache[account_key]
        if preferences_key in _user_preferences_cache:
            del _user_preferences_cache[preferences_key]
        if context_key in _user_context_cache:
            del _user_context_cache[context_key]
        
        logger.debug(f"Cleared cache for user {user_id}")
    else:
        # Clear all caches
        _user_account_cache.clear()
        _user_preferences_cache.clear()
        _user_context_cache.clear()
        logger.debug("Cleared all user caches")

# ============================================================================
# MAIN PUBLIC API - HYBRID APPROACH
# ============================================================================

@handle_errors("getting user data", default_return={})
def get_user_data(
    user_id: str, 
    data_types: Union[str, List[str]] = 'all',
    fields: Optional[Union[str, List[str], Dict[str, Union[str, List[str]]]]] = None,
    auto_create: bool = True,
    include_metadata: bool = False
) -> Dict[str, Any]:
    """
    Central handler for all user data access.
    
    Args:
        user_id: User identifier
        data_types: 'all', single type, or list of types
        fields: 
            - None: Return full data
            - "field_name": Extract single field from all types
            - ["field1", "field2"]: Extract multiple fields from all types  
            - {"account": "email", "preferences": ["categories", "channel"]}: Type-specific fields
        auto_create: Whether to create missing files
        include_metadata: Include file metadata (size, timestamps, etc.)
    
    Returns:
        Dict with requested data types and fields
    """
    if not user_id:
        logger.error("get_user_data called with None user_id")
        return {}
    
    # Normalize data_types
    if data_types == 'all':
        data_types = list(USER_DATA_LOADERS.keys())
    elif isinstance(data_types, str):
        data_types = [data_types]
    
    # Validate data types
    available_types = get_available_data_types()
    invalid_types = [dt for dt in data_types if dt not in available_types]
    if invalid_types:
        logger.error(f"Invalid data types requested: {invalid_types}. Valid types: {available_types}")
        return {}
    
    result = {}
    
    # Load requested data types using registry
    for data_type in data_types:
        loader_info = USER_DATA_LOADERS.get(data_type)
        if not loader_info or not loader_info['loader']:
            logger.warning(f"No loader registered for data type: {data_type}")
            continue
        
        # Load data using registered loader
        data = loader_info['loader'](user_id, auto_create=auto_create)
        
        # Handle field extraction
        if fields is not None:
            if isinstance(fields, str):
                # Single field from all types
                data = data.get(fields) if data else None
            elif isinstance(fields, list):
                # Multiple fields from all types
                if data:
                    extracted_data = {}
                    for field in fields:
                        if field in data:
                            extracted_data[field] = data[field]
                    data = extracted_data if extracted_data else None
                else:
                    data = None
            elif isinstance(fields, dict) and data_type in fields:
                # Type-specific field extraction
                type_fields = fields[data_type]
                if isinstance(type_fields, str):
                    data = data.get(type_fields) if data else None
                elif isinstance(type_fields, list):
                    if data:
                        extracted_data = {}
                        for field in type_fields:
                            if field in data:
                                extracted_data[field] = data[field]
                        data = extracted_data if extracted_data else None
                    else:
                        data = None
        
        # Add metadata if requested
        if include_metadata and data is not None:
            file_path = get_user_file_path(user_id, loader_info['file_type'])
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                metadata = {
                    'file_size': stat.st_size,
                    'modified_time': stat.st_mtime,
                    'file_path': file_path,
                    'data_type': data_type,
                    'description': loader_info['description']
                }
                if isinstance(data, dict):
                    data['_metadata'] = metadata
                else:
                    data = {'data': data, '_metadata': metadata}
        
        # Only include in result if data exists
        if data is not None:
            result[data_type] = data
    
    return result

# ============================================================================
# UTILITY FUNCTIONS (Keep these)
# ============================================================================

@handle_errors("ensuring unique ids", default_return=None)
def ensure_unique_ids(data):
    """Ensure all messages have unique IDs."""
    if not data or 'messages' not in data:
        return data
    
    existing_ids = set()
    for message in data['messages']:
        if 'message_id' not in message or message['message_id'] in existing_ids:
            message['message_id'] = str(uuid.uuid4())
        existing_ids.add(message['message_id'])
    
    return data

@handle_errors("loading and ensuring ids")
def load_and_ensure_ids(user_id):
    """Load messages for all categories and ensure IDs are unique for a user."""
    user_data = get_user_data(user_id, 'preferences')
    if not user_data or 'preferences' not in user_data:
        logger.warning(f"User preferences not found for user_id: {user_id}")
        return

    preferences = user_data['preferences']
    categories = preferences.get('categories', [])
    if not categories:
        logger.debug(f"No categories found for user {user_id}")
        return

    for category in categories:
        file_path = determine_file_path('messages', f'{category}/{user_id}')
        data = load_json_data(file_path)
        if data:
            data = ensure_unique_ids(data)
            save_json_data(data, file_path)
    
    logger.debug(f"Ensured message ids are unique for user '{user_id}'")

def ensure_all_categories_have_schedules(user_id: str) -> bool:
    """Ensure all categories in user preferences have corresponding schedules."""
    if not user_id:
        logger.warning(f"Invalid user_id: {user_id}")
        return False
    
    try:
        user_data = get_user_data(user_id, 'preferences')
        if not user_data or 'preferences' not in user_data:
            logger.warning(f"User preferences not found for user_id: {user_id}")
            return False
            
        preferences_data = user_data['preferences']
        categories = preferences_data.get('categories', [])
        
        if not categories:
            logger.debug(f"No categories found for user {user_id}")
            return True
        
        logger.info(f"Ensuring schedules exist for all categories for user {user_id}: {categories}")
        
        # Ensure each category has a default schedule
        for category in categories:
            ensure_category_has_default_schedule(user_id, category)
        
        return True
    except Exception as e:
        logger.error(f"Error ensuring all categories have schedules for user {user_id}: {e}")
        return False

# ============================================================================
# REGISTER LOADERS IN CENTRALIZED REGISTRY
# ============================================================================

# Register all data loaders in the centralized registry
# This happens after all functions are defined
register_data_loader('account', load_user_account_data, 'account')
register_data_loader('preferences', load_user_preferences_data, 'preferences')
register_data_loader('context', load_user_context_data, 'user_context')
register_data_loader('schedules', load_user_schedules_data, 'schedules')

logger.info(f"Registered {len(USER_DATA_LOADERS)} data loaders in centralized registry")

# ============================================================================
# CONVENIENCE FUNCTIONS USING CENTRALIZED SYSTEM
# ============================================================================

def get_user_email(user_id: str) -> Optional[str]:
    """Get user's email address using centralized system."""
    user_data = get_user_data(user_id, 'account', fields='email')
    return user_data.get('account')

def get_user_categories(user_id: str) -> List[str]:
    """Get user's message categories using centralized system."""
    user_data = get_user_data(user_id, 'preferences', fields='categories')
    categories = user_data.get('preferences', [])
    if isinstance(categories, dict):
        return list(categories.keys())
    elif isinstance(categories, list):
        return categories
    return []

def get_user_channel_type(user_id: str) -> str:
    """Get user's communication channel type using centralized system."""
    user_data = get_user_data(user_id, 'preferences', fields={'preferences': ['channel']})
    channel_data = user_data.get('preferences', {}).get('channel', {})
    return channel_data.get('type', 'email')

def get_user_preferred_name(user_id: str) -> str:
    """Get user's preferred name using centralized system."""
    user_data = get_user_data(user_id, 'context', fields='preferred_name')
    return user_data.get('context', '')

def get_user_account_status(user_id: str) -> str:
    """Get user's account status using centralized system."""
    user_data = get_user_data(user_id, 'account', fields='account_status')
    return user_data.get('account', 'inactive')

def get_user_data_with_metadata(user_id: str, data_types: Union[str, List[str]] = 'all') -> Dict[str, Any]:
    """Get user data with file metadata using centralized system."""
    return get_user_data(user_id, data_types, include_metadata=True)

def get_user_essential_info(user_id: str) -> Dict[str, Any]:
    """Get essential user information using centralized system."""
    return get_user_data(user_id, 'all', fields={
        'account': ['user_id', 'internal_username', 'email', 'account_status'],
        'preferences': ['categories', 'channel'],
        'context': ['preferred_name']
    })

# ============================================================================
# PERSONALIZATION UTILITY FUNCTIONS (Moved from personalization_management)
# ============================================================================

# Predefined options for various personalization fields
PREDEFINED_OPTIONS = {
    "pronouns": [
        "she/her", "he/him", "they/them", "she/they", "he/they", 
        "any pronouns", "prefer not to say"
    ],
    "health_conditions": [
        "ADHD", "Anxiety", "Depression", "Bipolar Disorder", "PTSD", 
        "OCD", "Autism", "Chronic Pain", "Diabetes", "Asthma",
        "Sleep Disorders", "Eating Disorders", "Substance Use Disorder"
    ],
    "medications_treatments": [
        "Antidepressant", "Anti-anxiety medication", "Stimulant for ADHD",
        "Mood stabilizer", "Antipsychotic", "Sleep medication",
        "Therapy", "Counseling", "Support groups", "Exercise",
        "Meditation", "Yoga", "CPAP", "Inhaler", "Insulin"
    ],
    "reminders_needed": [
        "medications_treatments", "hydration", "movement/stretch breaks",
        "healthy meals/snacks", "mental health check-ins", "appointments",
        "exercise", "sleep schedule", "self-care activities"
    ],
    "loved_one_types": [
        "human", "dog", "cat", "bird", "fish", "reptile", "horse",
        "rabbit", "hamster", "guinea pig", "ferret", "other"
    ],
    "relationship_types": [
        "partner", "spouse", "parent", "child", "sibling", "friend",
        "roommate", "colleague", "therapist", "doctor", "teacher"
    ],
    "interests": [
        "Reading", "Writing", "Gaming", "Music", "Art", "Cooking",
        "Baking", "Gardening", "Hiking", "Swimming", "Running",
        "Yoga", "Meditation", "Photography", "Crafts", "Knitting",
        "Painting", "Drawing", "Sewing", "Woodworking", "Programming",
        "Math", "Science", "History", "Languages", "Travel"
    ],
    "activities_for_encouragement": [
        "exercise", "healthy eating", "sleep hygiene", "social activities",
        "hobbies", "work/projects", "self-care", "therapy appointments",
        "medication adherence", "stress management"
    ]
}

# Timezone options (common ones)
TIMEZONE_OPTIONS = [
    "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
    "America/Regina", "America/Toronto", "America/Vancouver", "America/Edmonton",
    "Europe/London", "Europe/Paris", "Europe/Berlin", "Europe/Rome",
    "Asia/Tokyo", "Asia/Shanghai", "Asia/Kolkata", "Australia/Sydney",
    "Pacific/Auckland", "UTC"
]

def get_predefined_options(field: str) -> List[str]:
    """Get predefined options for a specific personalization field."""
    return PREDEFINED_OPTIONS.get(field, [])

def get_timezone_options() -> List[str]:
    """Get timezone options."""
    return TIMEZONE_OPTIONS

def validate_personalization_data(data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Validate personalization data structure and content. No fields are required, only type-checked if present."""
    errors = []
    
    # Optional string fields
    optional_string_fields = ["date_of_birth", "timezone"]
    for field in optional_string_fields:
        if field in data and not isinstance(data[field], str):
            errors.append(f"Field {field} must be a string if present")
    
    # Optional list fields
    optional_list_fields = [
        "pronouns", "reminders_needed",
        "loved_ones", "interests", "activities_for_encouragement", "notes_for_ai", "goals"
    ]
    for field in optional_list_fields:
        if field in data and not isinstance(data[field], list):
            errors.append(f"Field {field} must be a list if present")
    
    # Optional custom_fields
    custom_fields = data.get('custom_fields', {})
    if isinstance(custom_fields, dict):
        if 'health_conditions' in custom_fields and not isinstance(custom_fields['health_conditions'], list):
            errors.append("Field health_conditions (in custom_fields) must be a list if present")
        if 'medications_treatments' in custom_fields and not isinstance(custom_fields['medications_treatments'], list):
            errors.append("Field medications_treatments (in custom_fields) must be a list if present")
    elif 'custom_fields' in data:
        errors.append("custom_fields must be a dictionary if present")
    
    # Validate date_of_birth format if provided
    if data.get("date_of_birth"):
        try:
            datetime.strptime(data["date_of_birth"], "%Y-%m-%d")
        except ValueError:
            errors.append("date_of_birth must be in YYYY-MM-DD format")
    
    # Validate loved_ones structure if present
    loved_ones = data.get("loved_ones", [])
    if isinstance(loved_ones, list):
        for i, loved_one in enumerate(loved_ones):
            if not isinstance(loved_one, dict):
                errors.append(f"loved_one at index {i} must be a dictionary if present")
    
    return len(errors) == 0, errors