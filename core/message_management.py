# message_management.py
"""
Message management utilities for MHM.
Contains functions for message categories, loading, adding, editing, deleting, and storing messages.
"""

import os
from pathlib import Path
import json
import uuid
from datetime import datetime
from core.logger import get_logger, get_component_logger
from core.config import DEFAULT_MESSAGES_DIR_PATH, get_user_data_dir
from core.file_operations import load_json_data, save_json_data, determine_file_path
from core.schemas import validate_messages_file_dict
from core.error_handling import (
    error_handler, DataError, FileOperationError, ValidationError,
    handle_file_error, handle_errors
)
from typing import List

# Use component logger for message management
logger = get_component_logger('message')
message_logger = logger  # Alias for backward compatibility

@handle_errors("getting message categories", default_return=[])
def get_message_categories():
    """
    Retrieves message categories from the environment variable CATEGORIES.
    Allows for either a comma-separated string or a JSON array.
    
    Returns:
        List[str]: List of message categories
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
    """Load default messages for a specific category."""
    try:
        # Add debug logging to see what path is being used
        logger.info(f"Loading default messages for category: {category}")
        logger.info(f"DEFAULT_MESSAGES_DIR_PATH: {DEFAULT_MESSAGES_DIR_PATH}")
        logger.info(f"Current working directory: {os.getcwd()}")
        
        default_messages_file = Path(DEFAULT_MESSAGES_DIR_PATH) / f"{category}.json"
        
        # Add debug logging to see what path is being used
        logger.info(f"Looking for default messages file: {default_messages_file}")
        logger.info(f"File exists: {default_messages_file.exists()}")
        logger.info(f"Absolute path: {default_messages_file.absolute()}")
        
        try:
            with open(default_messages_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                messages = data.get('messages', [])
                logger.info(f"Loaded {len(messages)} default messages for category {category}")
                return messages
        except FileNotFoundError:
            logger.error(f"Default messages file not found for category: {category}")
            logger.error(f"Attempted path: {default_messages_file}")
            logger.error(f"Absolute path: {default_messages_file.absolute()}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in default messages file for category {category}: {e}")
            return []
    except Exception as e:
        logger.error(f"Error loading default messages for category {category}: {e}")
        return []

@handle_errors("adding message")
def add_message(user_id, category, message_data, index=None):
    """
    Add a new message to a user's category.
    
    Args:
        user_id: The user ID
        category: The message category
        message_data: Dictionary containing message data
        index: Optional position to insert the message (None for append)
    """
    if user_id is None:
        logger.error("add_message called with None user_id")
        return

    # Use new user-specific message file structure
    user_messages_dir = Path(get_user_data_dir(user_id)) / 'messages'
    file_path = user_messages_dir / f"{category}.json"
    
    data = load_json_data(file_path)
    
    if data is None:
        data = {'messages': []}
    
    if 'message_id' not in message_data:
        message_data['message_id'] = str(uuid.uuid4())
    
    if index is not None and 0 <= index < len(data['messages']):
        data['messages'].insert(index, message_data)
    else:
        data['messages'].append(message_data)
    
    # Validate/normalize via Pydantic schema (non-blocking)
    try:
        data, _errs = validate_messages_file_dict(data)
    except Exception:
        pass
    save_json_data(data, file_path)
    
    # Update user index
    try:
        from core.user_data_manager import update_user_index
        update_user_index(user_id)
    except Exception as e:
        logger.warning(f"Failed to update user index after message addition for user {user_id}: {e}")
    
    logger.info(f"Added message to category {category} for user {user_id}: {message_data}")

@handle_errors("editing message")
def edit_message(user_id, category, message_id, updated_data):
    """
    Edit an existing message in a user's category.
    
    Args:
        user_id: The user ID
        category: The message category
        message_id: The ID of the message to edit
        updated_data: Dictionary containing updated message data
        
    Raises:
        ValidationError: If message ID is not found or category is invalid
    """
    if user_id is None:
        logger.error("edit_message called with None user_id")
        return

    # Use new user-specific message file structure
    user_messages_dir = Path(get_user_data_dir(user_id)) / 'messages'
    file_path = user_messages_dir / f"{category}.json"
    
    data = load_json_data(file_path)
    
    if data is None or 'messages' not in data:
        raise ValidationError("Invalid category or data file.")
    
    message_index = next((i for i, msg in enumerate(data['messages']) if msg['message_id'] == message_id), None)
    
    if message_index is None:
        raise ValidationError("Message ID not found.")
    
    # Update the message
    data['messages'][message_index].update(updated_data)
    try:
        data, _errs = validate_messages_file_dict(data)
    except Exception:
        pass
    save_json_data(data, file_path)
    
    # Update user index
    try:
        from core.user_data_manager import update_user_index
        update_user_index(user_id)
    except Exception as e:
        logger.warning(f"Failed to update user index after message edit for user {user_id}: {e}")
    
    logger.info(f"Edited message with ID {message_id} in category {category} for user {user_id}.")

@handle_errors("updating message by ID")
def update_message(user_id, category, message_id, new_message_data):
    """
    Update a message by its message_id.
    
    Args:
        user_id: The user ID
        category: The message category
        message_id: The ID of the message to update
        new_message_data: Complete new message data to replace the existing message
        
    Raises:
        ValidationError: If message ID is not found or category is invalid
    """
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
    """
    Delete a specific message from a user's category.
    
    Args:
        user_id: The user ID
        category: The message category
        message_id: The ID of the message to delete
        
    Raises:
        ValidationError: If the message ID is not found or the category is invalid
    """
    if user_id is None:
        logger.error("delete_message called with None user_id")
        return

    # Use new user-specific message file structure
    user_messages_dir = Path(get_user_data_dir(user_id)) / 'messages'
    file_path = user_messages_dir / f"{category}.json"
    
    data = load_json_data(file_path)
    
    if data is None or 'messages' not in data:
        raise ValidationError("Invalid category or data file.")
    
    message_to_delete = next((msg for msg in data['messages'] if msg['message_id'] == message_id), None)
    
    if not message_to_delete:
        raise ValidationError("Message ID not found.")
    
    data['messages'].remove(message_to_delete)
    save_json_data(data, file_path)
    
    # Update user index
    try:
        from core.user_data_manager import update_user_index
        update_user_index(user_id)
    except Exception as e:
        logger.warning(f"Failed to update user index after message deletion for user {user_id}: {e}")
    
    logger.info(f"Deleted message with ID {message_id} in category {category} for user {user_id}.")

@handle_errors("getting last 10 messages", default_return=[])
def get_last_10_messages(user_id, category):
    """
    Get the last 10 messages for a user and category, sorted by timestamp descending.
    
    Args:
        user_id: The user ID
        category: The message category
        
    Returns:
        List[dict]: List of the last 10 sent messages for the category
    """
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
    sorted_data = sorted(messages, key=get_timestamp_for_sorting, reverse=True)
    last_10_messages = sorted_data[:10]
    logger.debug(f"Retrieved last 10 messages for user {user_id} in category {category}.")
    return last_10_messages

@handle_errors("storing sent message")
def store_sent_message(user_id, category, message_id, message):
    """
    Store a sent message for a user and category, with per-category grouping and cleanup.
    
    Args:
        user_id: The user ID
        category: The message category
        message_id: The ID of the sent message
        message: The message content that was sent
    """
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

@handle_errors("creating message file from defaults")
def create_message_file_from_defaults(user_id: str, category: str) -> bool:
    """
    Create a user's message file for a specific category from default messages.
    This is the actual worker function that creates the file.
    
    Args:
        user_id: The user ID
        category: The specific category to create a message file for
        
    Returns:
        bool: True if file was created successfully
    """
    if not user_id or not category:
        logger.error(f"Invalid parameters: user_id={user_id}, category={category}")
        return False
    
    try:
        # Load default messages for the category
        default_messages = load_default_messages(category)
        if not default_messages:
            logger.warning(f"No default messages found for category {category}")
            return False
        
        # Ensure default messages are in the correct format
        formatted_messages = []
        for message in default_messages:
            if isinstance(message, dict):
                # Already in correct format, just ensure it has all required fields
                if 'message' not in message:
                    logger.warning(f"Default message missing 'message' field: {message}")
                    continue
                if 'message_id' not in message:
                    message['message_id'] = str(uuid.uuid4())
                if 'days' not in message:
                    message['days'] = ['ALL']
                if 'time_periods' not in message:
                    message['time_periods'] = ['ALL']
                formatted_messages.append(message)
            else:
                logger.warning(f"Invalid message format in defaults: {message}")
                continue
        
        if not formatted_messages:
            logger.error(f"No valid messages found in defaults for category {category}")
            return False
        
        # Create user message file with proper format
        # Note: messages directory should be created by create_user_files() during account creation
        user_messages_dir = Path(get_user_data_dir(user_id)) / 'messages'
        category_message_file = user_messages_dir / f"{category}.json"
        message_data = {"messages": formatted_messages}
        try:
            message_data, _errs = validate_messages_file_dict(message_data)
        except Exception:
            pass
        save_json_data(message_data, category_message_file)
        logger.info(f"Created message file for user {user_id}, category {category} from defaults ({len(formatted_messages)} messages)")
        return True
        
    except Exception as e:
        logger.error(f"Error creating message file for user {user_id}, category {category}: {e}")
        return False

@handle_errors("ensuring user message files exist")
def ensure_user_message_files(user_id: str, categories: List[str]) -> dict:
    """
    Ensure user has message files for specified categories.
    Creates messages directory if missing, checks which files are missing, and creates them.
    
    Args:
        user_id: The user ID
        categories: List of categories to check/create message files for (can be subset of user's categories)
        
    Returns:
        dict: Summary of the operation with keys:
            - success: bool - True if all files were created/validated successfully
            - directory_created: bool - True if messages directory was created
            - files_checked: int - Number of categories checked
            - files_created: int - Number of new files created
            - files_existing: int - Number of files that already existed
    """
    if not user_id or not categories:
        logger.error(f"Invalid parameters: user_id={user_id}, categories={categories}")
        return {
            "success": False,
            "directory_created": False,
            "files_checked": 0,
            "files_created": 0,
            "files_existing": 0
        }
    
    try:
        # Create messages directory for user if it doesn't exist
        user_messages_dir = Path(get_user_data_dir(user_id)) / 'messages'
        directory_created = not user_messages_dir.exists()
        user_messages_dir.mkdir(parents=True, exist_ok=True)
        
        # Check which categories are missing message files
        missing_categories = []
        for category in categories:
            category_message_file = user_messages_dir / f"{category}.json"
            if not category_message_file.exists():
                missing_categories.append(category)
        
        # Create missing files
        success_count = 0
        for category in missing_categories:
            if create_message_file_from_defaults(user_id, category):
                success_count += 1
                logger.debug(f"Created missing message file for category {category} for user {user_id}")
            else:
                logger.warning(f"Failed to create missing message file for category {category} for user {user_id}")
        
        # Count existing files as successes
        existing_count = len(categories) - len(missing_categories)
        total_success = success_count + existing_count
        
        result = {
            "success": total_success == len(categories),
            "directory_created": directory_created,
            "files_checked": len(categories),
            "files_created": success_count,
            "files_existing": existing_count
        }
        
        logger.info(f"Ensured message files for user {user_id}: {total_success}/{len(categories)} categories (created {success_count} new files, directory_created={directory_created})")
        return result
        
    except Exception as e:
        logger.error(f"Error ensuring user message files for user {user_id}: {e}")
        return {
            "success": False,
            "directory_created": False,
            "files_checked": len(categories),
            "files_created": 0,
            "files_existing": 0
        }


def get_timestamp_for_sorting(item):
    """
    Convert timestamp to float for consistent sorting.
    
    Args:
        item: Dictionary containing a timestamp field or other data type
        
    Returns:
        float: Timestamp as float for sorting, or 0.0 for invalid items
    """
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
