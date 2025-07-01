# message_management.py
"""
Message management utilities for MHM.
Contains functions for message categories, loading, adding, editing, deleting, and storing messages.
"""

import os
import json
import uuid
from datetime import datetime
from core.logger import get_logger
from core.config import DEFAULT_MESSAGES_DIR_PATH
from core.file_operations import load_json_data, save_json_data, determine_file_path
from core.error_handling import (
    error_handler, DataError, FileOperationError, ValidationError,
    handle_file_error, handle_errors
)

logger = get_logger(__name__)

@handle_errors("getting message categories", default_return=[])
def get_message_categories():
    """
    Retrieves message categories from the environment variable CATEGORIES.
    Allows for either a comma-separated string or a JSON array.
    """
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

@handle_errors("loading default messages", default_return=[])
def load_default_messages(category):
    """Load default messages for the given category."""
    default_messages_file = os.path.join(DEFAULT_MESSAGES_DIR_PATH, f"{category}.json")
    
    try:
        with open(default_messages_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            # Extract the messages list from the JSON object
            messages = data.get("messages", []) if isinstance(data, dict) else data
            logger.debug(f"Loaded default messages for category {category}")
            return messages
    except FileNotFoundError:
        logger.error(f"Default messages file not found for category: {category}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from the default messages file for category {category}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error occurred while loading default messages for category {category}: {e}")
        return []

@handle_errors("adding message")
def add_message(user_id, category, message_data, index=None):
    if user_id is None:
        logger.error("add_message called with None user_id")
        return

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

@handle_errors("editing message")
def edit_message(user_id, category, index, new_message_data):
    if user_id is None:
        logger.error("edit_message called with None user_id")
        return

    file_path = determine_file_path('messages', f'{category}/{user_id}')
    data = load_json_data(file_path)
    
    if data is None or 'messages' not in data or index >= len(data['messages']):
        raise ValidationError("Invalid message index or category.")
    
    data['messages'][index] = new_message_data
    save_json_data(data, file_path)
    logger.info(f"Edited message in category {category} for user {user_id}, : {new_message_data}")

@handle_errors("updating message by ID")
def update_message(user_id, category, message_id, new_message_data):
    """Update a message by its message_id."""
    if user_id is None:
        logger.error("update_message called with None user_id")
        return

    file_path = determine_file_path('messages', f'{category}/{user_id}')
    data = load_json_data(file_path)
    
    if data is None or 'messages' not in data:
        raise ValidationError("Invalid category or data file.")
    
    # Find the message by ID
    for i, msg in enumerate(data['messages']):
        if msg.get('message_id') == message_id:
            data['messages'][i] = new_message_data
            save_json_data(data, file_path)
            logger.info(f"Updated message with ID {message_id} in category {category} for user {user_id}")
            return
    
    raise ValidationError("Message ID not found.")

@handle_errors("deleting message")
def delete_message(user_id, category, message_id):
    if user_id is None:
        logger.error("delete_message called with None user_id")
        return

    file_path = determine_file_path('messages', f'{category}/{user_id}')
    data = load_json_data(file_path)
    
    if data is None or 'messages' not in data:
        raise ValidationError("Invalid category or data file.")
    
    message_to_delete = next((msg for msg in data['messages'] if msg['message_id'] == message_id), None)
    
    if not message_to_delete:
        raise ValidationError("Message ID not found.")
    
    data['messages'].remove(message_to_delete)
    save_json_data(data, file_path)
    logger.info(f"Deleted message with ID {message_id} in category {category} for user {user_id}.")

@handle_errors("getting last 10 messages", default_return=[])
def get_last_10_messages(user_id, category):
    """Get the last 10 messages for a user and category, sorted by timestamp descending."""
    if user_id is None:
        logger.error("get_last_10_messages called with None user_id")
        return []
    
    file_path = determine_file_path('sent_messages', user_id)
    data = load_json_data(file_path)
    if data is None:
        logger.warning(f"No sent messages found for user {user_id} in category {category}.")
        return []
    messages = []
    if category in data:
        messages = data[category]
    if not messages:
        logger.info(f"No messages found in category {category} for user {user_id}.")
        return []
    # Sort by timestamp descending
    def get_timestamp_for_sorting(item):
        if isinstance(item, str):
            return 0.0
        elif not isinstance(item, dict):
            return 0.0
        timestamp = item.get('timestamp', '1970-01-01 00:00:00')
        try:
            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            return dt.timestamp()
        except (ValueError, TypeError):
            return 0.0
    sorted_data = sorted(messages, key=get_timestamp_for_sorting, reverse=True)
    last_10_messages = sorted_data[:10]
    logger.debug(f"Retrieved last 10 messages for user {user_id} in category {category}.")
    return last_10_messages

@handle_errors("storing sent message")
def store_sent_message(user_id, category, message_id, message):
    """Store a sent message for a user and category, with per-category grouping and cleanup."""
    file_path = determine_file_path('sent_messages', user_id)
    sent_messages = load_json_data(file_path) or {}
    # Add the new message under the correct category
    sent_messages.setdefault(category, []).append({
        "message_id": message_id,
        "message": message,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    # Clean up messages older than 1 year
    from datetime import timedelta
    one_year_ago = datetime.now() - timedelta(days=365)
    cutoff_date = one_year_ago.strftime('%Y-%m-%d %H:%M:%S')
    for cat in sent_messages:
        if isinstance(sent_messages[cat], list):
            original_count = len(sent_messages[cat])
            sent_messages[cat] = [
                msg for msg in sent_messages[cat]
                if msg.get('timestamp', '0000-00-00 00:00:00') > cutoff_date
            ]
            cleaned_count = len(sent_messages[cat])
            if original_count > cleaned_count:
                logger.info(f"Cleaned up {original_count - cleaned_count} old messages from {cat} category for user {user_id}")
    save_json_data(sent_messages, file_path)
    logger.debug(f"Stored sent message for user {user_id}, category {category}.") 