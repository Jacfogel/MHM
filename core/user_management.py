# user_management.py
"""
User management utilities for MHM.
Contains functions for managing user accounts, preferences, context, and schedules.
"""

import os
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from core.logger import get_component_logger
from core.file_operations import load_json_data, save_json_data, get_user_file_path, determine_file_path
from core.config import ensure_user_directory
from core.error_handling import handle_errors
from core.schemas import (
    validate_account_dict,
    validate_preferences_dict,
    validate_schedules_dict,
)
from pathlib import Path

logger = get_component_logger('main')
user_logger = get_component_logger('user_activity')

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
        'default_fields': ['preferred_name', 'gender_identity'],
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

@handle_errors("registering data loader", default_return=False)
def register_data_loader(
    data_type: str,
    loader_func,
    file_type: str,
    default_fields: List[str] = None,
    metadata_fields: List[str] = None,
    description: str = "",
    *,
    force: bool = False,
):
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
    # Idempotent behavior: if an entry exists with a non-None loader and not forcing, do not overwrite
    existing = USER_DATA_LOADERS.get(data_type)
    if existing is not None and existing.get('loader') is not None and not force:
        logger.debug(
            f"register_data_loader no-op for '{data_type}' (loader already set and force=False)"
        )
        return False

    USER_DATA_LOADERS[data_type] = {
        'loader': loader_func,
        'file_type': file_type,
        'default_fields': default_fields or [],
        'metadata_fields': metadata_fields or [],
        'description': description
    }
    logger.info(f"Registered data loader for type: {data_type}")
    return True


# Once-only guard for default loader registration
_DEFAULT_LOADERS_REGISTERED = False


@handle_errors("registering default data loaders", default_return=None)
def register_default_loaders() -> None:
    """Ensure required loaders are registered (idempotent).

    Mutates the shared USER_DATA_LOADERS in-place, setting any missing/None
    loader entries for: account, preferences, context, schedules.
    """
    # Local imports of loader functions are already in this module
    required = [
        ('account', _get_user_data__load_account, 'account'),
        ('preferences', _get_user_data__load_preferences, 'preferences'),
        ('context', _get_user_data__load_context, 'user_context'),
        ('schedules', _get_user_data__load_schedules, 'schedules'),
    ]
    
    # Track which loaders are being registered for batch logging
    registered_loaders = []
    
    for key, func, ftype in required:
        entry = USER_DATA_LOADERS.get(key)
        if entry is None or entry.get('loader') is None:
            # Register without individual logging
            USER_DATA_LOADERS[key] = {
                'loader': func,
                'file_type': ftype,
                'default_fields': [],
                'metadata_fields': [],
                'description': f"Default {key} data loader"
            }
            registered_loaders.append(key)
    
    # Batch log all registered loaders at once
    if registered_loaders:
        logger.info(f"Registered data loaders: {', '.join(registered_loaders)} ({len(registered_loaders)} total)")


@handle_errors("ensuring default loaders are registered once", default_return=None)
def _ensure_default_loaders_once() -> None:
    global _DEFAULT_LOADERS_REGISTERED
    if not _DEFAULT_LOADERS_REGISTERED:
        register_default_loaders()
        _DEFAULT_LOADERS_REGISTERED = True

@handle_errors("getting available data types", default_return=[])
def get_available_data_types() -> List[str]:
    """Get list of available data types."""
    return list(USER_DATA_LOADERS.keys())

@handle_errors("getting data type info", default_return=None)
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
    users_dir = Path(USER_INFO_DIR_PATH)
    if not users_dir.exists():
        return []
    
    user_ids = []
    for item in users_dir.iterdir():
        # item from iterdir() is already a Path object relative to users_dir
        # Use it directly instead of combining with users_dir to avoid double paths
        if item.is_dir():
            # Check if this directory has the new structure
            account_file = item / 'account.json'
            if account_file.exists():
                user_ids.append(item.name)
    
    return user_ids

@handle_errors("loading user account data", default_return=None)
def _get_user_data__load_account(user_id: str, auto_create: bool = True) -> Optional[Dict[str, Any]]:
    """Load user account data from account.json."""
    if not user_id:
        logger.error("_get_user_data__load_account called with None user_id")
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
            logger.debug(f"User directory doesn't exist for {user_id}, not auto-creating account file")
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
            "discord_username": "",
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
        try:
            if isinstance(account_data, dict) and not account_data.get('timezone'):
                account_data['timezone'] = 'UTC'
        except Exception:
            pass

    if isinstance(account_data, dict):
        normalized_account, errors = validate_account_dict(account_data)
        if errors:
            logger.warning(
                f"Validation issues in account data for user {user_id}: {'; '.join(errors)}"
            )
        account_data = normalized_account or account_data
    
    # Cache the data
    _user_account_cache[cache_key] = (account_data, current_time)
    
    return account_data

@handle_errors("saving user account data")
def _save_user_data__save_account(user_id: str, account_data: Dict[str, Any]) -> bool:
    """Save user account data to account.json."""
    if not user_id:
        logger.error("_save_user_data__save_account called with None user_id")
        return False
    
    ensure_user_directory(user_id)
    account_file = get_user_file_path(user_id, 'account')
    
    # Add metadata
    account_data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Validate/normalize via Pydantic schema (non-blocking)
    try:
        account_data, _errs = validate_account_dict(account_data)
    except Exception:
        pass
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
def _get_user_data__load_preferences(user_id: str, auto_create: bool = True) -> Optional[Dict[str, Any]]:
    """Load user preferences data from preferences.json."""
    if not user_id:
        logger.error("_get_user_data__load_preferences called with None user_id")
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
            logger.debug(f"User directory doesn't exist for {user_id}, not auto-creating preferences file")
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

    if isinstance(preferences_data, dict):
        normalized_preferences, errors = validate_preferences_dict(preferences_data)
        if errors:
            logger.warning(
                f"Validation issues in preferences for user {user_id}: {'; '.join(errors)}"
            )
        preferences_data = normalized_preferences or preferences_data

    # Cache the data
    _user_preferences_cache[cache_key] = (preferences_data, current_time)
    
    return preferences_data

@handle_errors("saving user preferences data")
def _save_user_data__save_preferences(user_id: str, preferences_data: Dict[str, Any]) -> bool:
    """Save user preferences data to preferences.json."""
    if not user_id:
        logger.error("_save_user_data__save_preferences called with None user_id")
        return False
    
    ensure_user_directory(user_id)
    preferences_file = get_user_file_path(user_id, 'preferences')
    
    # Validate/normalize via Pydantic schema (non-blocking)
    try:
        preferences_data, _perrs = validate_preferences_dict(preferences_data)
    except Exception:
        pass
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
def _get_user_data__load_context(user_id: str, auto_create: bool = True) -> Optional[Dict[str, Any]]:
    """Load user context data from user_context.json."""
    if not user_id:
        logger.error("_get_user_data__load_context called with None user_id")
        return None

    # Check cache first
    current_time = time.time()
    cache_key = f"context_{user_id}"
    
    if cache_key in _user_context_cache:
        cached_data, cache_time = _user_context_cache[cache_key]
        if current_time - cache_time < _cache_timeout:
            return cached_data
    
    # Check if user directory exists (indicates user was created before)
    user_dir = os.path.dirname(get_user_file_path(user_id, 'context'))
    user_dir_exists = os.path.exists(user_dir)
    
    # Check if file exists before loading
    context_file = get_user_file_path(user_id, 'context')
    if not os.path.exists(context_file):
        if not auto_create:
            if not user_dir_exists:
                return None
            else:
                return None
        
        # Only auto-create if user directory exists (user was created before)
        if not user_dir_exists:
            logger.debug(f"User directory doesn't exist for {user_id}, not auto-creating user context file")
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
def _save_user_data__save_context(user_id: str, context_data: Dict[str, Any]) -> bool:
    """Save user context data to user_context.json."""
    if not user_id:
        logger.error("_save_user_data__save_context called with None user_id")
        return False
    
    ensure_user_directory(user_id)
    context_file = get_user_file_path(user_id, 'context')
    
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
def _get_user_data__load_schedules(user_id: str, auto_create: bool = True) -> Optional[Dict[str, Any]]:
    """Load user schedules data from schedules.json."""
    if not user_id:
        logger.error("_get_user_data__load_schedules called with None user_id")
        return None
    
    # Check cache first
    current_time = time.time()
    cache_key = f"schedules_{user_id}"
    
    if cache_key in _user_schedules_cache:
        cached_data, cache_time = _user_schedules_cache[cache_key]
        if current_time - cache_time < _cache_timeout:
            return cached_data
    
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
            logger.debug(f"User directory doesn't exist for {user_id}, not auto-creating schedules file")
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
    if isinstance(schedules_data, dict):
        normalized_schedules, errors = validate_schedules_dict(schedules_data)
        if errors:
            logger.warning(
                f"Validation issues in schedules for user {user_id}: {'; '.join(errors)}"
            )
        schedules_data = normalized_schedules or schedules_data
    
    # Cache the data
    _user_schedules_cache[cache_key] = (schedules_data, current_time)
    
    return schedules_data

@handle_errors("saving user schedules data")
def _save_user_data__save_schedules(user_id: str, schedules_data: Dict[str, Any]) -> bool:
    """Save user schedules data to schedules.json."""
    if not user_id:
        logger.error("_save_user_data__save_schedules called with None user_id")
        return False

    ensure_user_directory(user_id)
    schedules_file = get_user_file_path(user_id, 'schedules')

    # Normalize using tolerant Pydantic schema to keep on-disk data consistent
    normalized, errors = validate_schedules_dict(schedules_data)
    if errors:
        logger.warning(
            f"Schedules validation reported {len(errors)} issue(s); saving normalized data"
        )
    schedules_data = normalized or {}

    save_json_data(schedules_data, schedules_file)
    
    # Update cache
    cache_key = f"schedules_{user_id}"
    _user_schedules_cache[cache_key] = (schedules_data, time.time())
    
    logger.debug(f"Schedules data saved for user {user_id}")
    return True

@handle_errors("updating user schedules")
def update_user_schedules(user_id: str, schedules_data: Dict[str, Any]) -> bool:
    """Update user schedules data."""
    if not user_id:
        logger.error("update_user_schedules called with None user_id")
        return False
    
    # Use the centralized save_user_data function
    from core.user_data_handlers import save_user_data
    result = save_user_data(user_id, {'schedules': schedules_data})
    return result.get('schedules', False)

@handle_errors("creating default schedule periods", default_return={})
def create_default_schedule_periods(category: str = None) -> Dict[str, Any]:
    """Create default schedule periods for a new category."""
    if category:
        # Use category-specific naming
        if category in ("tasks", "checkin"):
            # For tasks and check-ins, use the descriptive naming with title case
            if category == "tasks":
                default_period_name = "Task Reminder Default"
            else:  # checkin
                default_period_name = "Check-in Reminder Default"
        else:
            # For message categories, use category-specific naming
            # Replace underscores with spaces for better readability and use title case
            category_display = category.replace('_', ' ').title()
            default_period_name = f"{category_display} Message Default"
    else:
        # Fallback to generic naming
        default_period_name = "Default"
    
    return {
        "ALL": {
            "active": True,
            "days": ["ALL"],
            "start_time": "00:00",
            "end_time": "23:59"
        },
        default_period_name: {
            "active": True,
            "days": ["ALL"],
            "start_time": "18:00",
            "end_time": "20:00"
        }
    }

@handle_errors("migrating legacy schedules structure", default_return={})
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
                    if isinstance(period_data, dict) and ('start_time' in period_data or 'start' in period_data):
                        legacy_periods[period_name] = period_data
                
                # Add default periods if none exist
                if not legacy_periods:
                    legacy_periods = create_default_schedule_periods(category)
                
                # Convert legacy periods to include days
                for period_name, period_data in legacy_periods.items():
                    if 'days' not in period_data:
                        period_data['days'] = ["ALL"]
                
                # All categories use the periods wrapper for consistency
                migrated_data[category] = {
                    "periods": legacy_periods
                }
        else:
            # Invalid data, create default structure
            default_periods = create_default_schedule_periods(category)
            migrated_data[category] = {
                "periods": default_periods
            }
    
    return migrated_data

@handle_errors("ensuring category has default schedule", default_return=False)
def ensure_category_has_default_schedule(user_id: str, category: str) -> bool:
    """Ensure a category has default schedule periods if it doesn't exist."""
    if not user_id or not category:
        logger.warning(f"Invalid parameters: user_id={user_id}, category={category}")
        return False
    
    try:
        schedules_data = _get_user_data__load_schedules(user_id) or {}
        logger.debug(f"Current schedules data for user {user_id}: {schedules_data}")
        
        # Migrate legacy structure if needed
        if schedules_data and any(isinstance(v, dict) and 'periods' not in v for v in schedules_data.values()):
            logger.info(f"Migrating legacy schedules structure for user {user_id}")
            schedules_data = migrate_legacy_schedules_structure(schedules_data)
            _save_user_data__save_schedules(user_id, schedules_data)
        
        # Check if category exists and has periods
        category_exists = category in schedules_data
        has_periods = schedules_data.get(category, {}).get('periods') if category_exists else False
        
        logger.debug(f"Category '{category}' exists: {category_exists}, has periods: {has_periods}")
        
        if not category_exists or not has_periods:
            # Create default periods for this category
            default_periods = create_default_schedule_periods(category)
            logger.debug(f"Creating default periods for category '{category}': {default_periods}")
            
            if not category_exists:
                # All categories use the periods wrapper for consistency
                schedules_data[category] = {
                    "periods": default_periods
                }
            else:
                # Category exists but has no periods
                schedules_data[category]['periods'] = default_periods
            
            # Save the updated schedules
            _save_user_data__save_schedules(user_id, schedules_data)
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
    
    # Use the centralized save_user_data function
    from core.user_data_handlers import save_user_data
    result = save_user_data(user_id, {'account': updates}, auto_create=auto_create)
    return result.get('account', False)

@handle_errors("updating user context")
def update_user_context(user_id: str, updates: Dict[str, Any], auto_create: bool = True) -> bool:
    """Update user context information."""
    if not user_id:
        logger.error("update_user_context called with None user_id")
        return False
    
    # Use the centralized save_user_data function
    from core.user_data_handlers import save_user_data
    result = save_user_data(user_id, {'context': updates}, auto_create=auto_create)
    return result.get('context', False)

@handle_errors("updating channel preferences")
def update_channel_preferences(user_id: str, updates: Dict[str, Any], auto_create: bool = True) -> bool:
    """Update channel preferences without triggering category schedule creation."""
    if not user_id:
        logger.error("update_channel_preferences called with None user_id")
        return False
    
    # Use the centralized save_user_data function directly to avoid category schedule creation
    from core.user_data_handlers import save_user_data
    result = save_user_data(user_id, {'preferences': updates}, auto_create=auto_create)
    return result.get('preferences', False)

@handle_errors("creating new user", default_return=None)
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
            # Check for explicit messages_enabled flag first, then fall back to categories check (for backward compatibility)
            "automated_messages": "enabled" if (
                user_data.get('messages_enabled', False) or 
                (user_data.get('categories') and len(user_data.get('categories', [])) > 0)
            ) else "disabled",
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
        "checkin_settings": user_data.get('checkin_settings', {}),
        "task_settings": user_data.get('task_settings', {})
    }
    
    # Remove redundant enabled flags from preferences since they're in account.json features
    if 'checkin_settings' in preferences_data and 'enabled' in preferences_data['checkin_settings']:
        del preferences_data['checkin_settings']['enabled']
    if 'task_settings' in preferences_data and 'enabled' in preferences_data['task_settings']:
        del preferences_data['task_settings']['enabled']
    
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
    
    # Save all data using centralized save_user_data
    from core.user_data_handlers import save_user_data
    save_result = save_user_data(user_id, {
        'account': account_data,
        'preferences': preferences_data,
        'context': context_data
    })
    
    # Check if save was successful
    if not all(save_result.values()):
        logger.error(f"Failed to save user data for {user_id}: {save_result}")
        return None
    
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
def _get_user_id_by_identifier__by_internal_username(internal_username: str) -> Optional[str]:
    """Helper function: Get user ID by internal username using the user index for fast lookup."""
    if not internal_username:
        return None
    
    # Try fast lookup from user index first
    try:
        from core.config import BASE_DATA_DIR
        
        # Use file locking for user_index.json to prevent race conditions in parallel execution
        from core.file_locking import safe_json_read
        index_file = str(Path(BASE_DATA_DIR) / "user_index.json")
        index_data = safe_json_read(index_file, default={})
        
        # Check mapping (fast O(1) lookup)
        if internal_username in index_data:
            return index_data[internal_username]
                
    except Exception as e:
        logger.warning(f"Error looking up user by internal_username '{internal_username}' in index: {e}")
    
    # Fallback: scan all user directories (slow but reliable)
    logger.debug(f"Falling back to directory scan for internal_username '{internal_username}'")
    user_ids = get_all_user_ids()
    for user_id in user_ids:
        from core.user_data_handlers import get_user_data
        user_data_result = get_user_data(user_id, 'account')
        account_data = user_data_result.get('account')
        if account_data and account_data.get('internal_username') == internal_username:
            return user_id
    
    return None

@handle_errors("getting user id by email", default_return=None)
def _get_user_id_by_identifier__by_email(email: str) -> Optional[str]:
    """Helper function: Get user ID by email using the user index for fast lookup."""
    if not email:
        return None
    
    # Try fast lookup from user index first
    try:
        from core.config import BASE_DATA_DIR
        
        # Use file locking for user_index.json to prevent race conditions in parallel execution
        from core.file_locking import safe_json_read
        index_file = str(Path(BASE_DATA_DIR) / "user_index.json")
        index_data = safe_json_read(index_file, default={})
        
        # Check email mapping (fast O(1) lookup)
        email_key = f"email:{email}"
        if email_key in index_data:
            return index_data[email_key]
                
    except Exception as e:
        logger.warning(f"Error looking up user by email '{email}' in index: {e}")
    
    # Fallback: scan all user directories (slow but reliable)
    logger.debug(f"Falling back to directory scan for email '{email}'")
    user_ids = get_all_user_ids()
    for user_id in user_ids:
        from core.user_data_handlers import get_user_data
        user_data_result = get_user_data(user_id, 'account')
        account_data = user_data_result.get('account')
        if account_data and account_data.get('email') == email:
            return user_id
    
    return None

@handle_errors("getting user id by phone", default_return=None)
def _get_user_id_by_identifier__by_phone(phone: str) -> Optional[str]:
    """Helper function: Get user ID by phone using the user index for fast lookup."""
    if not phone:
        return None
    
    # Try fast lookup from user index first
    try:
        from core.config import BASE_DATA_DIR
        
        # Use file locking for user_index.json to prevent race conditions in parallel execution
        from core.file_locking import safe_json_read
        index_file = str(Path(BASE_DATA_DIR) / "user_index.json")
        index_data = safe_json_read(index_file, default={})
        
        # Check phone mapping (fast O(1) lookup)
        phone_key = f"phone:{phone}"
        if phone_key in index_data:
            return index_data[phone_key]
                
    except Exception as e:
        logger.warning(f"Error looking up user by phone '{phone}' in index: {e}")
    
    # Fallback: scan all user directories (slow but reliable)
    logger.debug(f"Falling back to directory scan for phone '{phone}'")
    user_ids = get_all_user_ids()
    for user_id in user_ids:
        from core.user_data_handlers import get_user_data
        user_data_result = get_user_data(user_id, 'account')
        account_data = user_data_result.get('account')
        if account_data and account_data.get('phone') == phone:
            return user_id
    
    return None

@handle_errors("getting user id by chat id", default_return=None)
def _get_user_id_by_identifier__by_chat_id(chat_id: str) -> Optional[str]:
    """Helper function: Get user ID by chat ID."""
    if not chat_id:
        return None
    
    user_ids = get_all_user_ids()
    for user_id in user_ids:
        from core.user_data_handlers import get_user_data
        user_data_result = get_user_data(user_id, 'account')
        account_data = user_data_result.get('account')
        if account_data and account_data.get('chat_id') == chat_id:
            return user_id
    
    return None

@handle_errors("getting user id by discord user id", default_return=None)
def _get_user_id_by_identifier__by_discord_user_id(discord_user_id: str) -> Optional[str]:
    """Helper function: Get user ID by Discord user ID using the user index for fast lookup."""
    if not discord_user_id:
        return None
    
    # Try fast lookup from user index first
    try:
        from core.config import BASE_DATA_DIR
        
        # Use file locking for user_index.json to prevent race conditions in parallel execution
        from core.file_locking import safe_json_read
        index_file = str(Path(BASE_DATA_DIR) / "user_index.json")
        index_data = safe_json_read(index_file, default={})
        
        # Check discord mapping (fast O(1) lookup)
        discord_key = f"discord:{discord_user_id}"
        if discord_key in index_data:
            return index_data[discord_key]
                
    except Exception as e:
        logger.warning(f"Error looking up user by discord_user_id '{discord_user_id}' in index: {e}")
    
    # Fallback: scan all user directories (slow but reliable)
    logger.debug(f"Falling back to directory scan for discord_user_id '{discord_user_id}'")
    user_ids = get_all_user_ids()
    for user_id in user_ids:
        from core.user_data_handlers import get_user_data
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
    global _user_account_cache, _user_preferences_cache, _user_context_cache, _user_schedules_cache
    
    if user_id:
        # Clear specific user's cache
        account_key = f"account_{user_id}"
        preferences_key = f"preferences_{user_id}"
        context_key = f"context_{user_id}"
        schedules_key = f"schedules_{user_id}"
        
        if account_key in _user_account_cache:
            del _user_account_cache[account_key]
        if preferences_key in _user_preferences_cache:
            del _user_preferences_cache[preferences_key]
        if context_key in _user_context_cache:
            del _user_context_cache[context_key]
        if schedules_key in _user_schedules_cache:
            del _user_schedules_cache[schedules_key]
        
        logger.debug(f"Cleared cache for user {user_id}")
    else:
        # Clear all caches
        _user_account_cache.clear()
        _user_preferences_cache.clear()
        _user_context_cache.clear()
        _user_schedules_cache.clear()
        logger.debug("Cleared all user caches")

# ============================================================================
# UTILITY FUNCTIONS (Keep these)
# ============================================================================

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

@handle_errors("loading and ensuring ids", default_return=None)
def load_and_ensure_ids(user_id):
    """Load messages for all categories and ensure IDs are unique for a user."""
    from core.user_data_handlers import get_user_data
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

@handle_errors("ensuring all categories have schedules", default_return=False)
def ensure_all_categories_have_schedules(user_id: str, suppress_logging: bool = False) -> bool:
    """Ensure all categories in user preferences have corresponding schedules."""
    if not user_id:
        logger.warning(f"Invalid user_id: {user_id}")
        return False
    
    try:
        from core.user_data_handlers import get_user_data
        user_data = get_user_data(user_id, 'preferences')
        if not user_data or 'preferences' not in user_data:
            logger.warning(f"User preferences not found for user_id: {user_id}")
            return False
            
        preferences_data = user_data['preferences']
        categories = preferences_data.get('categories', [])
        
        if not categories:
            logger.debug(f"No categories found for user {user_id}")
            return True
        
        # Track which schedules are actually created (not just verified)
        created_schedules = []
        
        # Ensure each category has a default schedule
        for category in categories:
            if ensure_category_has_default_schedule(user_id, category):
                created_schedules.append(category)
        
        # Only log when schedules are actually created, not when they already exist
        # Suppress logging for internal calls to avoid duplicate messages
        if created_schedules and not suppress_logging:
            logger.info(f"Created schedules for user {user_id}: {created_schedules}")
        elif not suppress_logging:
            logger.debug(f"Verified schedules exist for user {user_id}: {categories}")
        
        return True
    except Exception as e:
        logger.error(f"Error ensuring all categories have schedules for user {user_id}: {e}")
        return False

# ============================================================================
# REGISTER LOADERS IN CENTRALIZED REGISTRY
# ============================================================================

# Register all data loaders in the centralized registry
# This happens after all functions are defined
_ensure_default_loaders_once()

logger.info(f"Registered {len(USER_DATA_LOADERS)} data loaders in centralized registry")

# ============================================================================
# USER DATA UTILITY FUNCTIONS
# ============================================================================

@handle_errors("getting user categories", default_return=[])
def get_user_categories(user_id: str) -> List[str]:
    """Get user's message categories using centralized system."""
    from core.user_data_handlers import get_user_data
    user_data = get_user_data(user_id, 'preferences')
    # Extract categories from the preferences structure
    if isinstance(user_data, dict):
        preferences = user_data.get('preferences', {})
        if isinstance(preferences, dict):
            categories = preferences.get('categories', [])
            if isinstance(categories, list):
                return categories
    # Fallback: if user_data is already a list (legacy format)
    elif isinstance(user_data, list):
        return user_data
    return []

@handle_errors("getting user data with metadata", default_return={})
def get_user_data_with_metadata(user_id: str, data_types: Union[str, List[str]] = 'all') -> Dict[str, Any]:
    """Get user data with file metadata using centralized system."""
    from core.user_data_handlers import get_user_data
    return get_user_data(user_id, data_types, include_metadata=True)

# ============================================================================
# PERSONALIZATION UTILITY FUNCTIONS
# ============================================================================

# Predefined options for various personalization fields
PREDEFINED_OPTIONS = {
    "gender_identity": [
        "Male", "Female", "Non-binary", "Genderfluid", "Agender", "Bigender", "Demiboy", "Demigirl",
        "Genderqueer", "Two-spirit", "Other", "Prefer not to say"
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
    "America/Port_of_Spain", "Europe/London", "Europe/Paris", "Europe/Berlin", "Europe/Rome",
    "Asia/Tokyo", "Asia/Shanghai", "Asia/Kolkata", "Australia/Sydney",
    "Pacific/Auckland", "UTC"
]

# ---------------------------------------------------------------------------
# PRESET OPTIONS – now loaded from JSON at runtime
# ---------------------------------------------------------------------------

_PRESETS_CACHE: Dict[str, List[str]] | None = None


@handle_errors("loading presets JSON", default_return=PREDEFINED_OPTIONS)
def _load_presets_json() -> Dict[str, List[str]]:
    """Load presets from resources/presets.json (cached)."""
    global _PRESETS_CACHE
    if _PRESETS_CACHE is not None:
        return _PRESETS_CACHE

    import json, pkgutil, os
    presets_path = Path(__file__).parent.parent / "resources" / "presets.json"
    try:
        with open(presets_path, "r", encoding="utf-8") as f:
            _PRESETS_CACHE = json.load(f)
    except FileNotFoundError:
        logger.warning("presets.json not found – falling back to hard-coded options")
        _PRESETS_CACHE = PREDEFINED_OPTIONS  # fallback
    return _PRESETS_CACHE


@handle_errors("getting predefined options", default_return=[])
def get_predefined_options(field: str) -> List[str]:
    """Return predefined options for a personalization field."""
    presets = _load_presets_json()
    return presets.get(field, [])

def get_timezone_options() -> List[str]:
    """Get timezone options."""
    try:
        import pytz
        return pytz.all_timezones
    except ImportError:
        # Fallback to hardcoded list if pytz is not available
        return TIMEZONE_OPTIONS

@handle_errors("creating default personalization data", default_return={})
def create_default_personalization_data() -> Dict[str, Any]:
    """Create default personalization data structure."""
    return {
        "preferred_name": "",
        "gender_identity": "",
        "date_of_birth": "",
        "custom_fields": {
            "health_conditions": [],
            "medications_treatments": [],
            "allergies": []
        },
        "interests": [],
        "goals": [],
        "loved_ones": [],
        "notes_for_ai": [],
        "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

@handle_errors("getting personalization field", default_return=None)
def get_personalization_field(user_id: str, field: str) -> Any:
    """Get a specific field from personalization data using centralized system."""
    if not user_id or not field:
        logger.error("get_personalization_field called with invalid parameters")
        return None
    
    from core.user_data_handlers import get_user_data
    user_data = get_user_data(user_id, 'context', fields=field)
    context_data = user_data.get('context', {})
    return context_data.get(field)

@handle_errors("updating personalization field", default_return=False)
def update_personalization_field(user_id: str, field: str, value: Any) -> bool:
    """Update a specific field in personalization data using centralized system."""
    if not user_id or not field:
        logger.error("update_personalization_field called with invalid parameters")
        return False
    
    # Use the centralized save system
    from core.user_data_handlers import save_user_data
    result = save_user_data(user_id, {
        'context': {field: value}
    })
    return result.get('context', False)

@handle_errors("adding item to personalization list", default_return=False)
def add_personalization_item(user_id: str, field: str, item: Any) -> bool:
    """Add an item to a list field in personalization data using centralized system."""
    if not user_id or not field:
        logger.error("add_personalization_item called with invalid parameters")
        return False
    
    # Get current list
    from core.user_data_handlers import get_user_data
    current_data = get_user_data(user_id, 'context', fields=field)
    current_list = current_data.get('context', {}).get(field, [])
    
    if not isinstance(current_list, list):
        logger.error(f"Field {field} is not a list")
        return False
    
            # Add item if not already present
        if item not in current_list:
            current_list.append(item)
            from core.user_data_handlers import save_user_data
            result = save_user_data(user_id, {
                'context': {field: current_list}
            })
            return result.get('context', False)
    
    return True  # Item already exists

@handle_errors("removing item from personalization list", default_return=False)
def remove_personalization_item(user_id: str, field: str, item: Any) -> bool:
    """Remove an item from a list field in personalization data using centralized system."""
    if not user_id or not field:
        logger.error("remove_personalization_item called with invalid parameters")
        return False
    
    # Get current list
    from core.user_data_handlers import get_user_data
    current_data = get_user_data(user_id, 'context', fields=field)
    current_list = current_data.get('context', {}).get(field, [])
    
    if not isinstance(current_list, list):
        return False
    
    # Remove item if present
    if item in current_list:
        current_list.remove(item)
        from core.user_data_handlers import save_user_data
        result = save_user_data(user_id, {
            'context': {field: current_list}
        })
        return result.get('context', False)
    
    return True  # Item doesn't exist

@handle_errors("clearing personalization cache", default_return=None)
def clear_personalization_cache(user_id: str = None) -> None:
    """Clear the personalization cache for a specific user or all users."""
    # Use the centralized cache clearing system
    clear_user_caches(user_id)

@handle_errors("getting user id by identifier", default_return=None)
def get_user_id_by_identifier(identifier: str) -> Optional[str]:
    """
    Get user ID by any identifier (internal_username, email, discord_user_id, phone).
    
    Automatically detects the identifier type and uses the appropriate lookup method.
    
    Args:
        identifier: The identifier to look up (can be any supported type)
        
    Returns:
        Optional[str]: User ID if found, None otherwise
    """
    if not identifier:
        return None
    
    # Try fast lookup from user index first
    try:
        from core.config import BASE_DATA_DIR
        
        # Use file locking for user_index.json to prevent race conditions in parallel execution
        from core.file_locking import safe_json_read
        index_file = str(Path(BASE_DATA_DIR) / "user_index.json")
        index_data = safe_json_read(index_file, default={})
        
        # Check all possible mappings in order of likelihood
        # 1. Direct internal_username mapping (most common)
        if identifier in index_data:
            mapped = index_data[identifier]
            # If mapping is a UUID/string, return it directly
            if isinstance(mapped, str) and mapped:
                return mapped
            # Some tests write detailed objects instead of UUIDs. In that case, if a user
            # directory exists with the identifier as the folder name, treat the identifier
            # itself as the user_id (legacy-style id equal to internal_username).
            try:
                users_dir = str(Path(BASE_DATA_DIR) / "users" / identifier)
                if os.path.isdir(users_dir):
                    return identifier
            except Exception:
                pass
        
        # 2. Email mapping
        email_key = f"email:{identifier}"
        if email_key in index_data:
            return index_data[email_key]
        
        # 3. Discord user ID mapping
        discord_key = f"discord:{identifier}"
        if discord_key in index_data:
            return index_data[discord_key]
        
        # 4. Phone mapping
        phone_key = f"phone:{identifier}"
        if phone_key in index_data:
            return index_data[phone_key]
                
    except Exception as e:
        logger.warning(f"Error looking up user by identifier '{identifier}' in index: {e}")
    
    # Fallback: try specific lookup functions
    # Try internal_username first (most common)
    result = _get_user_id_by_identifier__by_internal_username(identifier)
    if result:
        return result
    
    # Try email
    result = _get_user_id_by_identifier__by_email(identifier)
    if result:
        return result
    
    # Try discord_user_id
    result = _get_user_id_by_identifier__by_discord_user_id(identifier)
    if result:
        return result
    
    # Try phone
    result = _get_user_id_by_identifier__by_phone(identifier)
    if result:
        return result
    
    return None 