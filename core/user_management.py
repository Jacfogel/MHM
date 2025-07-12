# user_management.py
"""
User management utilities for MHM.
Contains functions for user data operations, user lookup, and user preferences.
Updated to work with new data structure: account.json, preferences.json, user_context.json, schedules.json
"""

import os
import time
import uuid
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from core.logger import get_logger
from core.config import (
    USER_INFO_DIR_PATH,
    get_user_file_path, ensure_user_directory
)
from core.file_operations import load_json_data, save_json_data, determine_file_path
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_file_error, handle_errors
)

logger = get_logger(__name__)

# Cache for user data
_user_account_cache = {}
_user_preferences_cache = {}
_user_context_cache = {}
_cache_timeout = 300  # 5 minutes

# ============================================================================
# CORE USER MANAGEMENT FUNCTIONS (New Data Structure)
# ============================================================================

@handle_errors("getting all user ids", default_return=[])
def get_all_user_ids():
    """Get all user IDs from the system."""
    users_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'users')
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
def load_user_account_data(user_id: str) -> Optional[Dict[str, Any]]:
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
    
    # Load from file
    ensure_user_directory(user_id)
    account_file = get_user_file_path(user_id, 'account')
    
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
def load_user_preferences_data(user_id: str) -> Optional[Dict[str, Any]]:
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
    
    # Load from file
    ensure_user_directory(user_id)
    preferences_file = get_user_file_path(user_id, 'preferences')

    preferences_data = load_json_data(preferences_file) or {}

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
def load_user_context_data(user_id: str) -> Optional[Dict[str, Any]]:
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
    
    # Load from file
    ensure_user_directory(user_id)
    context_file = get_user_file_path(user_id, 'user_context')
    
    context_data = load_json_data(context_file) or {}
    
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
def load_user_schedules_data(user_id: str) -> Optional[Dict[str, Any]]:
    """Load user schedules data from schedules.json."""
    if not user_id:
        logger.error("load_user_schedules_data called with None user_id")
        return None
    
    # Load from file
    ensure_user_directory(user_id)
    schedules_file = get_user_file_path(user_id, 'schedules')
    
    schedules_data = load_json_data(schedules_file) or {}
    
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

@handle_errors("getting user account info", default_return=None)
def get_user_account(user_id: str, field: Optional[str] = None) -> Any:
    """Get user account information."""
    if not user_id:
        logger.error("get_user_account called with None user_id")
        return None
    
    account_data = load_user_account_data(user_id)
    if not account_data:
        return None
    
    if field:
        return account_data.get(field)
    return account_data

@handle_errors("getting user preferences", default_return=None)
def get_user_preferences(user_id: str, field: Optional[str] = None) -> Any:
    """Get user preferences."""
    if not user_id:
        logger.error("get_user_preferences called with None user_id")
        return None

    preferences_data = load_user_preferences_data(user_id)
    if not preferences_data:
        return None
    
    if field:
        # Handle both string and list field parameters for backward compatibility
        if isinstance(field, list):
            # Legacy behavior: navigate through nested structure
            field_value = preferences_data
            try:
                for key in field:
                    field_value = field_value[key]
                
                # Special handling for categories - always return a list
                if field == ['categories']:
                    if field_value is None:
                        logger.warning(f"Categories field is None for user_id {user_id}, returning empty list")
                        return []
                    elif not isinstance(field_value, list):
                        logger.warning(f"Expected list for categories, got {type(field_value)} for user '{user_id}', returning empty list")
                        return []
                    # If we get here, field_value is a valid list - return it without warning
                    return field_value
                
                return field_value
            except KeyError:
                logger.warning(f"Field path {field} not found in preferences for user_id {user_id}")
                # Special handling for categories - return empty list instead of None
                if field == ['categories']:
                    return []
                return None
        else:
            # New behavior: simple string field lookup
            return preferences_data.get(field)
    
    return preferences_data

@handle_errors("getting user context", default_return=None)
def get_user_context(user_id: str, field: Optional[str] = None) -> Any:
    """Get user context information."""
    if not user_id:
        logger.error("get_user_context called with None user_id")
        return None
    
    context_data = load_user_context_data(user_id)
    if not context_data:
        return None
    
    if field:
        return context_data.get(field)
    return context_data

@handle_errors("updating user account")
def update_user_account(user_id: str, updates: Dict[str, Any]) -> bool:
    """Update user account information."""
    if not user_id:
        logger.error("update_user_account called with None user_id")
        return False
    
    account_data = load_user_account_data(user_id) or {}
    account_data.update(updates)
    
    return save_user_account_data(user_id, account_data)

@handle_errors("updating user preferences")
def update_user_preferences(user_id: str, updates: Dict[str, Any]) -> bool:
    """Update user preferences."""
    if not user_id:
        logger.error("update_user_preferences called with None user_id")
        return False
    
    preferences_data = load_user_preferences_data(user_id) or {}
    
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
def update_user_context(user_id: str, updates: Dict[str, Any]) -> bool:
    """Update user context information."""
    if not user_id:
        logger.error("update_user_context called with None user_id")
        return False
    
    context_data = load_user_context_data(user_id) or {}
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
        }
    }
    
    # Create preferences data
    preferences_data = {
        "categories": user_data.get('categories', []),
        "channel": {
            "type": user_data.get('messaging_service', 'email')
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
        "pronouns": user_data.get('pronouns', []),
        "date_of_birth": user_data.get('date_of_birth', ''),
        "custom_fields": {
            "health_conditions": user_data.get('health_conditions', []),
            "medications_treatments": user_data.get('medications_treatments', []),
            "reminders_needed": user_data.get('reminders_needed', [])
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
        account_data = get_user_account(user_id)
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
        account_data = get_user_account(user_id)
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
        account_data = get_user_account(user_id)
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
# LEGACY COMPATIBILITY FUNCTIONS (TO BE REMOVED AFTER MIGRATION)
# ============================================================================
# TODO: Remove these functions after all code has been updated to use the new structure

@handle_errors("loading user info data (legacy)", default_return=None)
def load_user_info_data(user_id):
    """Load user info data - legacy compatibility function."""
    if not user_id:
        return None
    
    # Load all data from new structure
    account_data = load_user_account_data(user_id) or {}
    preferences_data = load_user_preferences_data(user_id) or {}
    context_data = load_user_context_data(user_id) or {}
    
    # Combine into legacy format
    user_info = {
        "user_id": account_data.get("user_id", user_id),
        "internal_username": account_data.get("internal_username", ""),
        "active": account_data.get("account_status") == "active",
        "preferred_name": context_data.get("preferred_name", ""),
        "chat_id": account_data.get("chat_id", ""),
        "phone": account_data.get("phone", ""),
        "email": account_data.get("email", ""),
        "discord_user_id": account_data.get("discord_user_id", ""),
        "created_at": account_data.get("created_at", ""),
        "last_updated": account_data.get("updated_at", ""),
        "preferences": preferences_data,
        "schedules": {}  # Schedules are handled separately
    }
    
    return user_info

@handle_errors("saving user info data (legacy)")
def save_user_info_data(user_info, user_id):
    """Save user info data - legacy compatibility function."""
    if not user_id:
        return

    # Extract data from legacy format
    account_updates = {
        "user_id": user_info.get("user_id", user_id),
        "internal_username": user_info.get("internal_username", ""),
        "account_status": "active" if user_info.get("active", True) else "inactive",
        "chat_id": user_info.get("chat_id", ""),
        "phone": user_info.get("phone", ""),
        "email": user_info.get("email", ""),
    }
    
    preferences_updates = user_info.get("preferences", {})
    
    context_updates = {
        "preferred_name": user_info.get("preferred_name", ""),
    }
    
    # Update all data
    update_user_account(user_id, account_updates)
    update_user_preferences(user_id, preferences_updates)
    update_user_context(user_id, context_updates)

@handle_errors("getting user info (legacy)", default_return=None)
def get_user_info(user_id, field=None):
    """Get user info - legacy compatibility function."""
    user_info = load_user_info_data(user_id)
    
    if field:
        return user_info.get(field) if user_info else None
    return user_info

@handle_errors("adding user info (legacy)")
def add_user_info(user_id, user_info):
    """Add or update user info - legacy compatibility function."""
    save_user_info_data(user_info, user_id)
    
    # Create message files for categories
    categories = user_info.get('preferences', {}).get('categories', [])
    if categories:
        user_messages_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'messages')
        
        for category in categories:
            category_file = f'{category}.json'
            user_category_path = os.path.join(user_messages_path, category, f'{user_id}.json')
            os.makedirs(os.path.dirname(user_category_path), exist_ok=True)
            
            # Load existing messages or create a new one
            data = load_json_data(user_category_path) or {"messages": []}
            
            # Ensure unique IDs for messages
            data = ensure_unique_ids(data)
            
            # Save the updated data
            save_json_data(data, user_category_path)
            logger.debug(f"Ensured message ids are unique for user '{user_id}' in category '{category}'")

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
    user_info = get_user_info(user_id)
    if not user_info:
        logger.warning(f"User info not found for user_id: {user_id}")
        return

    categories = user_info.get('preferences', {}).get('categories', [])
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
        preferences_data = load_user_preferences_data(user_id) or {}
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