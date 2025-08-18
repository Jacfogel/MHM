"""
Response tracking utilities for MHM.
Contains functions for storing and retrieving user responses, check-ins, and interactions.
"""

import os
from pathlib import Path
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from core.logger import get_logger, get_component_logger
from core.user_data_handlers import get_user_data
from core.file_operations import load_json_data, save_json_data, get_user_file_path
from core.config import (
    USER_INFO_DIR_PATH,
    get_user_file_path, ensure_user_directory
)
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)

logger = get_component_logger('user_activity')
tracking_logger = get_component_logger('user_activity')

# LEGACY COMPATIBILITY: Backward-compatible aliases for renamed functions
# TODO: Remove after tests and codebase have been migrated to new names
# REMOVAL PLAN:
# 1. Log all legacy calls to identify remaining call sites
# 2. Update imports in remaining modules/tests
# 3. Remove these aliases after 2 weeks of no usage

@handle_errors("legacy get_recent_checkins", default_return=[])
def get_recent_checkins(user_id: str, limit: int = 7):
    logger.warning("LEGACY COMPATIBILITY: get_recent_checkins() called; use get_recent_checkins() instead")
    return get_recent_checkins(user_id, limit)

@handle_errors("legacy store_checkin_response")
def store_checkin_response(user_id: str, response_data: dict):
    logger.warning("LEGACY COMPATIBILITY: store_checkin_response() called; use store_user_response() instead")
    return store_user_response(user_id, response_data, "checkin")

def _get_response_log_filename(response_type: str) -> str:
    """Get the filename for a response log type."""
    filename_mapping = {
        "checkin": "checkin_log.json",
        "chat_interaction": "chat_interaction_log.json"
    }
    return filename_mapping.get(response_type, f"{response_type}_log.json")

@handle_errors("storing user response")
def store_user_response(user_id: str, response_data: dict, response_type: str = "checkin"):
    """
    Store user response data in appropriate file structure.
    """
    # New structure: store in appropriate log file
    if response_type == "checkin":
        log_file = get_user_file_path(user_id, 'checkins')
    elif response_type == "chat_interaction":
        log_file = get_user_file_path(user_id, 'chat_interactions')
    else:
        log_file = get_user_file_path(user_id, f'{response_type}_log')
    
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

@handle_errors("storing checkin response")
def store_checkin_response(user_id: str, response_data: dict):
    """Store a check-in response."""
    store_user_response(user_id, response_data, "checkin")

@handle_errors("storing chat interaction")
def store_chat_interaction(user_id: str, user_message: str, ai_response: str, context_used: bool = False):
    """Store a chat interaction between user and AI."""
    response_data = {
        'user_message': user_message,
        'ai_response': ai_response,
        'context_used': context_used,
        'message_length': len(user_message),
        'response_length': len(ai_response),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    store_user_response(user_id, response_data, "chat_interaction")
    logger.info(f"Stored chat_interaction response for user {user_id}: {response_data}")



@handle_errors("getting recent responses", default_return=[])
def get_recent_responses(user_id: str, response_type: str = "checkin", limit: int = 5):
    """Get recent responses for a user from appropriate file structure."""
    # New structure
    if response_type == "checkin":
        log_file = get_user_file_path(user_id, 'checkins')
    elif response_type == "chat_interaction":
        log_file = get_user_file_path(user_id, 'chat_interactions')
    else:
        log_file = get_user_file_path(user_id, f'{response_type}_log')
    
    data = load_json_data(log_file) or []
    
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
                dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                return dt.timestamp()
            except (ValueError, TypeError):
                # If parsing fails, use 0
                return 0.0
        
        sorted_data = sorted(data, key=get_timestamp_for_sorting, reverse=True)
        return sorted_data[:limit]
    return []

@handle_errors("getting recent checkins", default_return=[])
def get_recent_checkins(user_id: str, limit: int = 7):
    """Get recent check-in responses for a user."""
    return get_recent_responses(user_id, "checkin", limit)

@handle_errors("getting recent chat interactions", default_return=[])
def get_recent_chat_interactions(user_id: str, limit: int = 10):
    """Get recent chat interactions for a user."""
    return get_recent_responses(user_id, "chat_interaction", limit)



@handle_errors("getting user checkin preferences", default_return={})
def get_user_checkin_preferences(user_id: str) -> dict:
    """Get user's check-in preferences from their preferences file."""
    prefs_result = get_user_data(user_id, 'preferences')
    user_preferences = prefs_result.get('preferences')
    if not user_preferences:
        return {}
    
    return user_preferences.get('checkin_settings', {})

@handle_errors("checking if user checkins enabled", default_return=False)
def is_user_checkins_enabled(user_id: str) -> bool:
    """Check if check-ins are enabled for a user."""
    user_data_result = get_user_data(user_id, 'account')
    user_account = user_data_result.get('account')
    if not user_account:
        return False
    
    return user_account.get('features', {}).get('checkins') == 'enabled'

@handle_errors("getting user checkin questions", default_return={})
def get_user_checkin_questions(user_id: str) -> dict:
    """Get the enabled check-in questions for a user."""
    checkin_prefs = get_user_checkin_preferences(user_id)
    return checkin_prefs.get('questions', {})

def get_user_info_for_tracking(user_id: str) -> Dict[str, Any]:
    """Get user information for response tracking."""
    try:
        user_data_result = get_user_data(user_id, 'account')
        user_account = user_data_result.get('account')
        prefs_result = get_user_data(user_id, 'preferences')
        user_preferences = prefs_result.get('preferences')
        # Get user context
        context_result = get_user_data(user_id, 'context')
        user_context = context_result.get('context')
        
        if not user_account:
            return {}
        
        return {
            "user_id": user_id,
            "internal_username": user_account.get("internal_username", ""),
            "preferred_name": user_context.get("preferred_name", "") if user_context else "",
            "categories": user_preferences.get("categories", []) if user_preferences else [],
            "messaging_service": user_preferences.get("channel", {}).get("type", "") if user_preferences else "",
            "created_at": user_account.get("created_at", ""),
            "last_updated": user_account.get("last_updated", "")
        }
    except Exception as e:
        logger.error(f"Error getting user info for tracking {user_id}: {e}")
        return {}

def track_user_response(user_id: str, category: str, response_data: Dict[str, Any]):
    """Track a user's response to a message."""
    try:
        # Get user info using new functions
        user_data_result = get_user_data(user_id, 'account')
        user_account = user_data_result.get('account')
        if not user_account:
            logger.error(f"User account not found for tracking: {user_id}")
            return
        
        # Store the response data based on category
        if category == "checkin":
            store_checkin_response(user_id, response_data)
        elif category == "checkin":  # LEGACY category name used by some tests
            store_checkin_response(user_id, response_data)
        elif category == "chat_interaction":
            # For chat interactions, we need user_message and ai_response
            user_message = response_data.get('user_message', '')
            ai_response = response_data.get('ai_response', '')
            context_used = response_data.get('context_used', False)
            store_chat_interaction(user_id, user_message, ai_response, context_used)
        else:
            # For other categories, store as generic response
            store_user_response(user_id, response_data, category)
        
        logger.info(f"Tracked {category} response for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error tracking user response: {e}") 