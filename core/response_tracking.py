"""
Response tracking utilities for MHM.
Contains functions for storing and retrieving user responses, check-ins, and interactions.
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from core.logger import get_logger
from core.user_management import get_user_info
from core.file_operations import load_json_data, save_json_data, get_user_file_path
from core.config import (
    USER_INFO_DIR_PATH, USE_USER_SUBDIRECTORIES,
    ensure_user_directory
)
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)

logger = get_logger(__name__)

def _get_response_log_filename(response_type: str) -> str:
    """Get the filename for a response log type."""
    filename_mapping = {
        "daily_checkin": "daily_checkin_log.json",
        "chat_interaction": "chat_interaction_log.json", 
        "survey_response": "survey_response_log.json"
    }
    return filename_mapping.get(response_type, f"{response_type}_log.json")

@handle_errors("storing user response")
def store_user_response(user_id: str, response_data: dict, response_type: str = "daily_checkin"):
    """
    Store user response data in appropriate file structure.
    """
    # New structure: store in appropriate log file
    if response_type == "daily_checkin":
        log_file = get_user_file_path(user_id, 'daily_checkins')
    elif response_type == "chat_interaction":
        log_file = get_user_file_path(user_id, 'chat_interactions')
    elif response_type == "survey_response":
        log_file = get_user_file_path(user_id, 'survey_responses')
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

@handle_errors("storing daily checkin response")
def store_daily_checkin_response(user_id: str, response_data: dict):
    """Store a daily check-in response."""
    store_user_response(user_id, response_data, "daily_checkin")

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

@handle_errors("storing survey response")
def store_survey_response(user_id: str, survey_name: str, responses: dict):
    """Store a survey response."""
    response_data = {
        'survey_name': survey_name,
        'responses': responses,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    store_user_response(user_id, response_data, "survey_response")

@handle_errors("getting recent responses", default_return=[])
def get_recent_responses(user_id: str, response_type: str = "daily_checkin", limit: int = 5):
    """Get recent responses for a user from appropriate file structure."""
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

@handle_errors("getting recent daily checkins", default_return=[])
def get_recent_daily_checkins(user_id: str, limit: int = 7):
    """Get recent daily check-in responses for a user."""
    return get_recent_responses(user_id, "daily_checkin", limit)

@handle_errors("getting recent chat interactions", default_return=[])
def get_recent_chat_interactions(user_id: str, limit: int = 10):
    """Get recent chat interactions for a user."""
    return get_recent_responses(user_id, "chat_interaction", limit)

@handle_errors("getting recent survey responses", default_return=[])
def get_recent_survey_responses(user_id: str, limit: int = 5):
    """Get recent survey responses for a user."""
    return get_recent_responses(user_id, "survey_response", limit)

@handle_errors("getting user checkin preferences", default_return={})
def get_user_checkin_preferences(user_id: str) -> dict:
    """Get user's check-in preferences from their user info."""
    user_info = get_user_info(user_id)
    if not user_info:
        return {}
    
    return user_info.get('preferences', {}).get('checkins', {})

@handle_errors("checking if user checkins enabled", default_return=False)
def is_user_checkins_enabled(user_id: str) -> bool:
    """Check if check-ins are enabled for a user."""
    checkin_prefs = get_user_checkin_preferences(user_id)
    return checkin_prefs.get('enabled', False)

@handle_errors("getting user checkin questions", default_return={})
def get_user_checkin_questions(user_id: str) -> dict:
    """Get the enabled check-in questions for a user."""
    checkin_prefs = get_user_checkin_preferences(user_id)
    return checkin_prefs.get('questions', {}) 