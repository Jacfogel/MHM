# user_management.py
"""
User management utilities for MHM.
Contains functions for user data operations, user lookup, and user preferences.
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
    USER_INFO_DIR_PATH, USE_USER_SUBDIRECTORIES, get_user_file_path, ensure_user_directory
)
from core.file_operations import load_json_data, save_json_data, determine_file_path
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_file_error, handle_errors
)

logger = get_logger(__name__)

# Cache for user profiles
_user_profile_cache = {}
_cache_timeout = 30  # Cache for 30 seconds to reduce repeated loads

@handle_errors("getting all user ids", default_return=[])
def get_all_user_ids():
    """Get all user IDs from both legacy and new file structures."""
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

@handle_errors("loading user info data", default_return=None)
def load_user_info_data(user_id):
    """Load user info data from appropriate file structure."""
    if user_id is None:
        logger.error("load_user_info_data called with None user_id")
        return None
    # Check cache first
    current_time = time.time()
    cache_key = f"load_{user_id}"
    if cache_key in _user_profile_cache:
        cached_data, cache_time = _user_profile_cache[cache_key]
        if current_time - cache_time < _cache_timeout:
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
        if profile_data:
            logger.debug(f"User profile loaded: {user_id}")
        return profile_data if profile_data else None
    else:
        # Legacy structure
        user_info_file_path = determine_file_path('users', user_id)
        user_info = load_json_data(user_info_file_path)
        _user_profile_cache[cache_key] = (user_info, current_time)
        if user_info is None:
            logger.info(f"User file not found for user ID: {user_id} at path: {user_info_file_path}")
        else:
            logger.debug(f"User profile loaded: {user_id}")
        return user_info

@handle_errors("saving user info data")
def save_user_info_data(user_info, user_id):
    """
    Save user info data to appropriate file structure.
    - profile.json: core info only (no preferences/schedules inside)
    - preferences.json: FLAT dict of preferences (do NOT nest under 'preferences' key)
    - schedules.json: schedules dict
    WARNING: Only save the FLAT preferences dict to preferences.json. Do NOT save the whole user_data or nest under 'preferences'.
    This prevents data loss and ensures compatibility with all code that loads preferences.
    """
    if user_id is None:
        logger.error("save_user_info_data called with None user_id")
        return
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

@handle_errors("getting user info", default_return=None)
def get_user_info(user_id, field=None):
    """Get user info for a specific user and optionally a specific field."""
    if user_id is None:
        logger.error("get_user_info called with None user_id")
        return None

    # Check cache first
    current_time = time.time()
    cache_key = user_id
    
    if cache_key in _user_profile_cache:
        cached_data, cache_time = _user_profile_cache[cache_key]
        if current_time - cache_time < _cache_timeout:
            if field:
                return cached_data.get(field) if cached_data else None
            return cached_data
    
    user_info = load_user_info_data(user_id)
    
    # Cache the data
    _user_profile_cache[cache_key] = (user_info, current_time)
    
    if field:
        return user_info.get(field) if user_info else None
    return user_info

@handle_errors("getting user preferences", default_return=None)
def get_user_preferences(user_id, field=None):
    """Get user preferences for a specific user and optionally a specific field."""
    if not user_id:
        logger.error("get_user_preferences called with None user_id")
        return None

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
        # Only log if preferences exist and debug level verbosity is high
        if preferences and logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"User preferences loaded: {user_id}")
        return preferences

@handle_errors("adding user info")
def add_user_info(user_id, user_info):
    """Add or update user info for a specific user."""
    if user_id is None:
        logger.error("add_user_info called with None user_id")
        return

    file_path = determine_file_path('users', user_id)
    existing_data = load_json_data(file_path) or {}
    existing_data.update(user_info)
    save_user_info_data(existing_data, user_id)
    logger.debug(f"Added/Updated user info for user_id {user_id}: {existing_data}")

    default_messages_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'default_messages')
    user_messages_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'messages')
    for category in user_info['preferences']['categories']:
        category_file = f'{category}.json'
        user_category_path = os.path.join(user_messages_path, category, f'{user_id}.json')
        os.makedirs(os.path.dirname(user_category_path), exist_ok=True)
        
        if os.path.exists(os.path.join(default_messages_path, category_file)):
            import shutil
            shutil.copy(os.path.join(default_messages_path, category_file), user_category_path)
            logger.debug(f"Copied default {category} messages JSON for user {user_id}")
        else:
            with open(user_category_path, 'w', encoding='utf-8') as file:
                import json
                json.dump({"messages": []}, file, indent=4)
            logger.warning(f"Default messages JSON for {category} not found. Created blank JSON for user {user_id}")

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
    
    # Reduced logging to avoid spam - only log once per user instead of per category
    logger.debug(f"Ensured message ids are unique for user '{user_id}'")

@handle_errors("getting user id by internal username", default_return=None)
def get_user_id_by_internal_username(internal_username):
    """Find the internal user_id by internal username."""
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

@handle_errors("getting user id by chat id", default_return=None)
def get_user_id_by_chat_id(chat_id):
    """Find the internal user_id by chat ID."""
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

@handle_errors("getting user id by discord user id", default_return=None)
def get_user_id_by_discord_user_id(discord_user_id):
    """Find the internal user_id by Discord user ID."""
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