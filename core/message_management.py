# message_management.py
"""
Message management utilities for MHM.
Contains functions for message categories, loading, adding, editing, deleting, and storing messages.
"""

import os
from pathlib import Path
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, cast
from core.logger import get_component_logger
from core.config import DEFAULT_MESSAGES_DIR_PATH, get_user_data_dir
from core.file_operations import load_json_data, save_json_data, determine_file_path
from core.schemas import validate_messages_file_dict
from core.error_handling import ValidationError, handle_errors
from core.time_utilities import (
    now_timestamp_filename,
    now_timestamp_full,
    parse_timestamp_full,
)
from core.user_data_v2 import SCHEMA_VERSION, MessageTemplateV2Model, generate_short_id
import contextlib
import importlib

logger = get_component_logger("message")


@handle_errors("normalizing runtime message file shape", default_return={"messages": []})
def _normalize_runtime_message_file(data: dict[str, Any]) -> dict[str, Any]:
    """
    Preserve canonical v2 template files and only apply runtime-schema validation
    to legacy message files.
    """
    if data.get("schema_version") == SCHEMA_VERSION:
        return data
    normalized_data, errors = validate_messages_file_dict(data)
    if errors:
        logger.warning(f"Validation issues in message file: {'; '.join(errors)}")
    return normalized_data


@handle_errors(
    "ensuring v2 message template file",
    default_return={"schema_version": SCHEMA_VERSION, "updated_at": "", "messages": []},
)
def _ensure_v2_message_template_file(data: Any, category: str) -> dict[str, Any]:
    """Normalize a message template file payload to canonical v2 wrapper shape."""
    if not isinstance(data, dict):
        return {
            "schema_version": SCHEMA_VERSION,
            "updated_at": now_timestamp_full(),
            "messages": [],
        }
    messages_raw = data.get("messages")
    messages_list = messages_raw if isinstance(messages_raw, list) else []
    normalized_messages = [
        _message_template_default_to_v2(message, category)
        for message in messages_list
        if isinstance(message, dict)
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": now_timestamp_full(),
        "messages": normalized_messages,
    }


@handle_errors("normalizing legacy message update payload", default_return={})
def _normalize_message_update_payload(updated_data: dict[str, Any]) -> dict[str, Any]:
    """Map legacy update fields onto canonical v2 message template fields."""
    normalized = dict(updated_data)
    if "message" in updated_data and "text" not in updated_data:
        normalized["text"] = updated_data.get("message")
    if "days" in updated_data or "time_periods" in updated_data:
        schedule = dict(normalized.get("schedule") or {})
        if "days" in updated_data:
            schedule["days"] = updated_data.get("days")
        if "time_periods" in updated_data:
            schedule["periods"] = updated_data.get("time_periods")
        normalized["schedule"] = schedule
    return normalized


@handle_errors("converting v2 message template to runtime shape", default_return={})
def _message_template_to_runtime(message: dict[str, Any], category: str) -> dict[str, Any]:
    """Return canonical template shape with legacy aliases for compatibility."""
    # LEGACY COMPATIBILITY: Temporary bridge for legacy template payloads.
    if "text" not in message and "schedule" not in message and "message" in message:
        logger.warning("LEGACY COMPATIBILITY: message template fallback used for legacy message field.")
        message = _message_template_default_to_v2(message, category)
    schedule = message.get("schedule") or {}
    message_id = message.get("id") or message.get("message_id")
    return {
        "id": message_id,
        "message_id": message_id,
        "text": message.get("text") or message.get("message") or "",
        "message": message.get("text") or message.get("message") or "",
        "category": message.get("category") or category,
        "schedule": {
            "days": schedule.get("days") or message.get("days") or ["ALL"],
            "periods": schedule.get("periods") or message.get("time_periods") or ["ALL"],
        },
        "days": schedule.get("days") or message.get("days") or ["ALL"],
        "time_periods": schedule.get("periods") or message.get("time_periods") or ["ALL"],
        "created_at": message.get("created_at"),
        "updated_at": message.get("updated_at") or message.get("created_at"),
        "timestamp": message.get("updated_at") or message.get("created_at"),
    }


@handle_errors("converting v2 message delivery to runtime shape", default_return={})
def _delivery_to_runtime_message(delivery: dict[str, Any]) -> dict[str, Any]:
    """Return canonical delivery shape with legacy aliases for compatibility."""
    # LEGACY COMPATIBILITY: Temporary bridge for legacy sent-message payloads.
    if delivery.get("message") is not None or delivery.get("delivery_status") is not None or delivery.get("timestamp") is not None:
        logger.warning("LEGACY COMPATIBILITY: sent-message fallback used for legacy delivery fields.")
    message_id = delivery.get("message_template_id") or delivery.get("message_id")
    sent_at = delivery.get("sent_at") or delivery.get("timestamp", "")
    status = delivery.get("status") or delivery.get("delivery_status", "")
    return {
        "message_template_id": message_id,
        "message_id": message_id,
        "sent_text": delivery.get("sent_text") or delivery.get("message") or "",
        "message": delivery.get("sent_text") or delivery.get("message") or "",
        "category": delivery.get("category", ""),
        "sent_at": sent_at,
        "timestamp": sent_at,
        "status": status,
        "delivery_status": status,
        "time_period": delivery.get("time_period"),
    }


@handle_errors("converting default message template to v2", default_return={})
def _message_template_default_to_v2(message: dict[str, Any], category: str) -> dict[str, Any]:
    """Build a canonical v2 message template from default/runtime message data."""
    message_id = str(message.get("id") or message.get("message_id") or uuid.uuid4())
    created_at = _canonical_message_timestamp(message.get("created_at") or message.get("timestamp")) or now_timestamp_full()
    schedule_raw = message.get("schedule")
    schedule: dict[str, Any] = cast(dict[str, Any], schedule_raw) if isinstance(schedule_raw, dict) else {}
    # LEGACY COMPATIBILITY: Default resources are v2, but tolerate older local
    # message defaults until those files are verified clean and the fallback is removed.
    template = {
        "id": message_id,
        "kind": "message",
        "text": str(message.get("text") or message.get("message") or ""),
        "category": str(message.get("category") or category),
        "active": bool(message.get("active", True)),
        "schedule": {
            "days": schedule.get("days") or message.get("days") or ["ALL"],
            "periods": schedule.get("periods") or message.get("time_periods") or ["ALL"],
        },
        "created_at": created_at,
        "updated_at": _canonical_message_timestamp(message.get("updated_at") or created_at) or created_at,
        "archived_at": message.get("archived_at"),
        "deleted_at": message.get("deleted_at"),
        "metadata": dict(message.get("metadata") or {}),
    }
    template["metadata"].setdefault("short_id", message.get("short_id") or generate_short_id(message_id, "message"))
    try:
        return MessageTemplateV2Model.model_validate(template).model_dump(mode="json")
    except Exception as exc:
        # LEGACY COMPATIBILITY: Keep tolerant normalization for pre-v2 schedule/value shapes.
        logger.warning(
            f"LEGACY COMPATIBILITY: fallback message template normalization used for category '{category}': {exc}"
        )
        return template


@handle_errors("normalizing canonical message timestamp", default_return=None)
def _canonical_message_timestamp(value: Any) -> str | None:
    """Return a valid full timestamp string or current time when invalid."""
    if isinstance(value, str) and parse_timestamp_full(value) is not None:
        return value
    return now_timestamp_full()


@handle_errors("getting message categories", default_return=[])
def get_message_categories():
    """
    Retrieves message categories from the environment variable CATEGORIES.
    Allows for either a comma-separated string or a JSON array.

    Returns:
        List[str]: List of message categories
    """
    raw_categories = os.getenv("CATEGORIES")
    if not raw_categories:
        logger.error("No CATEGORIES found in environment. Returning empty list.")
        return []

    raw_categories = raw_categories.strip()

    # If it looks like JSON (starts with '['), try parsing it
    if raw_categories.startswith("[") and raw_categories.endswith("]"):
        try:
            parsed = json.loads(raw_categories)
            if isinstance(parsed, list):
                category_list = [
                    cat.strip()
                    for cat in parsed
                    if isinstance(cat, str) and cat.strip()
                ]
                logger.debug(
                    f"Retrieved message categories from JSON list: {category_list}"
                )
                return category_list
            else:
                # If JSON parsed but it's not a list, treat it as a fallback
                logger.warning(
                    "CATEGORIES JSON is not a list. Falling back to comma-split logic."
                )
        except json.JSONDecodeError:
            logger.warning(
                "Failed to parse CATEGORIES as JSON. Falling back to comma-split logic."
            )

    # Fallback: treat it as a comma-separated string
    category_list = [cat.strip() for cat in raw_categories.split(",") if cat.strip()]
    logger.debug(
        f"Retrieved message categories from comma-separated string: {category_list}"
    )
    return category_list


@handle_errors("loading user messages", default_return=[])
def load_user_messages(user_id, category):
    """
    Load user's message templates for a specific category.

    Args:
        user_id: The user ID
        category: The message category

    Returns:
        List[dict]: List of message templates for the category
    """
    if user_id is None:
        logger.error("load_user_messages called with None user_id")
        return []

    try:
        # Use new user-specific message file structure
        user_messages_dir = Path(get_user_data_dir(user_id)) / "messages"
        file_path = user_messages_dir / f"{category}.json"

        if not file_path.exists():
            logger.debug(
                f"No message file found for user {user_id}, category {category}"
            )
            return []

        data = load_json_data(str(file_path))

        if data is None or "messages" not in data:
            logger.debug(
                f"No messages found in file for user {user_id}, category {category}"
            )
            return []

        messages = [_message_template_to_runtime(msg, category) for msg in data["messages"]]
        logger.debug(
            f"Loaded {len(messages)} messages for user {user_id}, category {category}"
        )
        return messages

    except Exception as e:
        logger.error(
            f"Error loading user messages for user {user_id}, category {category}: {e}"
        )
        return []


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
            with open(default_messages_file, encoding="utf-8") as f:
                data = json.load(f)
                messages = data.get("messages", [])
                logger.info(
                    f"Loaded {len(messages)} default messages for category {category}"
                )
                return messages
        except FileNotFoundError:
            logger.error(f"Default messages file not found for category: {category}")
            logger.error(f"Attempted path: {default_messages_file}")
            logger.error(f"Absolute path: {default_messages_file.absolute()}")
            return []
        except json.JSONDecodeError as e:
            logger.error(
                f"Invalid JSON in default messages file for category {category}: {e}"
            )
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
    user_messages_dir = Path(get_user_data_dir(user_id)) / "messages"
    # Ensure the messages directory exists
    user_messages_dir.mkdir(parents=True, exist_ok=True)
    file_path = user_messages_dir / f"{category}.json"

    data = _ensure_v2_message_template_file(load_json_data(str(file_path)), category)

    message_v2 = _message_template_default_to_v2(message_data, category)

    if index is not None and 0 <= index < len(data["messages"]):
        data["messages"].insert(index, message_v2)
    else:
        data["messages"].append(message_v2)
    data["updated_at"] = now_timestamp_full()

    # Validate/normalize via Pydantic schema (non-blocking)
    with contextlib.suppress(Exception):
        data = _ensure_v2_message_template_file(data, category)
    save_json_data(data, str(file_path))

    try:
        importlib.import_module("core.user_data_manager").update_user_index(user_id)
    except Exception as e:
        logger.warning(
            f"Failed to update user index after message addition for user {user_id}: {e}"
        )

    logger.info(
        f"Added message to category {category} for user {user_id}: {message_v2}"
    )


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
    user_messages_dir = Path(get_user_data_dir(user_id)) / "messages"
    user_messages_dir.mkdir(parents=True, exist_ok=True)
    file_path = user_messages_dir / f"{category}.json"

    data = _ensure_v2_message_template_file(load_json_data(str(file_path)), category)

    if "messages" not in data:
        raise ValidationError("Invalid category or data file.")

    message_index = next(
        (
            i
            for i, msg in enumerate(data["messages"])
            if (msg.get("id") or msg.get("message_id")) == message_id
        ),
        None,
    )

    if message_index is None:
        raise ValidationError("Message ID not found.")

    # Update the message
    merged = dict(data["messages"][message_index])
    merged.update(_normalize_message_update_payload(updated_data))
    data["messages"][message_index] = _message_template_default_to_v2(merged, category)
    data["updated_at"] = now_timestamp_full()
    with contextlib.suppress(Exception):
        data = _ensure_v2_message_template_file(data, category)
    save_json_data(data, str(file_path))

    try:
        importlib.import_module("core.user_data_manager").update_user_index(user_id)
    except Exception as e:
        logger.warning(
            f"Failed to update user index after message edit for user {user_id}: {e}"
        )

    logger.info(
        f"Edited message with ID {message_id} in category {category} for user {user_id}."
    )


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

    file_path = determine_file_path("messages", f"{category}/{user_id}")
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    data = _ensure_v2_message_template_file(load_json_data(file_path), category)

    if "messages" not in data:
        raise ValidationError("Invalid category or data file.")

    # Find the message by ID
    for i, msg in enumerate(data["messages"]):
        if (msg.get("id") or msg.get("message_id")) == message_id:
            normalized_new_data = _normalize_message_update_payload(new_message_data)
            if not normalized_new_data.get("id"):
                normalized_new_data["id"] = message_id
            data["messages"][i] = _message_template_default_to_v2(normalized_new_data, category)
            data["updated_at"] = now_timestamp_full()
            save_json_data(data, file_path)
            logger.info(
                f"Updated message with ID {message_id} in category {category} for user {user_id}"
            )
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
    user_messages_dir = Path(get_user_data_dir(user_id)) / "messages"
    # Ensure the messages directory exists
    user_messages_dir.mkdir(parents=True, exist_ok=True)
    file_path = user_messages_dir / f"{category}.json"

    data = _ensure_v2_message_template_file(load_json_data(str(file_path)), category)

    if "messages" not in data:
        raise ValidationError("Invalid category or data file.")

    message_to_delete = next(
        (msg for msg in data["messages"] if (msg.get("id") or msg.get("message_id")) == message_id), None
    )

    if not message_to_delete:
        raise ValidationError("Message ID not found.")

    data["messages"].remove(message_to_delete)
    # If no messages remain, keep an empty file (tests expect file to exist post-delete)
    if not data.get("messages"):
        data = {
            "schema_version": SCHEMA_VERSION,
            "updated_at": now_timestamp_full(),
            "messages": [],
        }
    else:
        data["updated_at"] = now_timestamp_full()
    save_json_data(data, str(file_path))

    try:
        importlib.import_module("core.user_data_manager").update_user_index(user_id)
    except Exception as e:
        logger.warning(
            f"Failed to update user index after message deletion for user {user_id}: {e}"
        )

    logger.info(
        f"Deleted message with ID {message_id} in category {category} for user {user_id}."
    )


@handle_errors("getting recent messages", default_return=[])
def get_recent_messages(
    user_id: str,
    category: str | None = None,
    limit: int = 10,
    days_back: int | None = None,
) -> list[dict[str, Any]]:
    """
    Get recent messages with flexible filtering.

    This function replaces get_last_10_messages() with enhanced functionality
    that supports both category-specific and cross-category queries.

    Args:
        user_id: The user ID
        category: Optional category filter (None = all categories)
        limit: Maximum number of messages to return
        days_back: Only include messages from last N days

    Returns:
        List[dict]: List of recent messages, sorted by timestamp descending
    """
    if user_id is None:
        logger.error("get_recent_messages called with None user_id")
        return []

    try:
        file_path = determine_file_path("sent_messages", user_id)
        data = load_json_data(file_path)

        if not data:
            logger.debug(f"No sent messages found for user {user_id}")
            return []

        _normalize_message_timestamps(data, file_path)

        if data.get("schema_version") == SCHEMA_VERSION and isinstance(data.get("deliveries"), list):
            messages = [_delivery_to_runtime_message(delivery) for delivery in data["deliveries"]]
            normalized_data = {"messages": messages}
        else:

            # Normalize/validate to drop malformed entries and apply defaults
            normalized_data, errors = validate_messages_file_dict(data)
            if errors:
                logger.warning(
                    f"Validation issues in sent messages for user {user_id}: {'; '.join(errors)}"
                )

            # Preserve categories from the source data for filtering
            source_messages = data.get("messages", [])
            if isinstance(source_messages, list):
                id_to_category = {
                    msg.get("message_id"): msg.get("category")
                    for msg in source_messages
                    if isinstance(msg, dict) and msg.get("message_id")
                }
                for message in normalized_data.get("messages", []):
                    if "category" not in message:
                        category_value = id_to_category.get(message.get("message_id"))
                        if category_value:
                            message["category"] = category_value

        if "messages" in normalized_data:
            messages = normalized_data["messages"]
        else:
            logger.debug(
                f"No 'messages' key found in normalized data for user {user_id}, using empty list"
            )
            messages = []

        if not messages:
            logger.debug(f"No messages found for user {user_id}")
            return []

        # Apply filters
        filtered_messages = messages

        # Filter by category if specified
        if category:
            filtered_messages = [
                msg for msg in filtered_messages if msg.get("category") == category
            ]

        # Filter by days_back if specified
        if days_back:
            # NOTE: This is timezone-aware UTC state used for retention filtering.
            # core.time_utilities currently provides local-naive "now" helpers only,
            # so this usage does not map cleanly without adding new helpers.
            # Keep as-is for correctness.
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            filtered_messages = [
                msg
                for msg in filtered_messages
                if _parse_message_timestamp(msg.get("timestamp", "")) >= cutoff_date
            ]

        # Sort by timestamp descending (newest first)
        filtered_messages.sort(
            key=lambda msg: _parse_message_timestamp(msg.get("timestamp", "")), reverse=True
        )

        # Apply limit
        result = filtered_messages[:limit]

        logger.debug(
            f"Retrieved {len(result)} recent messages for user {user_id}, category={category}, limit={limit}, days_back={days_back}"
        )
        return result

    except Exception as e:
        logger.error(f"Error getting recent messages for user {user_id}: {e}")
        return []


@handle_errors("storing sent message", default_return=False)
def store_sent_message(
    user_id: str,
    category: str,
    message_id: str,
    message: str,
    delivery_status: str = "sent",
    time_period: str | None = None,
) -> bool:
    """
    Store sent message in chronological order.

    This function maintains the chronological structure by inserting new messages
    in the correct position based on timestamp.

    Args:
        user_id: The user ID
        category: The message category
        message_id: The message ID
        message: The message content
        delivery_status: Delivery status (default: "sent")
        time_period: The time period when the message was sent (e.g., "morning", "evening")

    Returns:
        bool: True if message stored successfully
    """
    if user_id is None:
        logger.error("store_sent_message called with None user_id")
        return False

    try:
        file_path = determine_file_path("sent_messages", user_id)
        data = load_json_data(file_path) or {}
        _normalize_message_timestamps(data, file_path)

        sent_at = now_timestamp_full()
        new_delivery = {
            "id": str(uuid.uuid4()),
            "message_template_id": message_id,
            "sent_text": message,
            "category": category,
            "channel": "",
            "status": delivery_status,
            "source": {
                "system": "mhm",
                "channel": "",
                "actor": "scheduler",
                "migration": None,
            },
            "sent_at": sent_at,
            "time_period": time_period,
            "metadata": {},
        }
        deliveries = data.get("deliveries", [])
        deliveries.insert(0, new_delivery)
        data = {
            "schema_version": SCHEMA_VERSION,
            "updated_at": now_timestamp_full(),
            "deliveries": deliveries,
        }
        save_json_data(data, file_path)
        logger.debug(f"Stored v2 sent message delivery for user {user_id}, category {category}")
        return True

    except Exception as e:
        logger.error(f"Error storing sent message for user {user_id}: {e}")
        return False


@handle_errors("archiving old messages", default_return=False)
def archive_old_messages(user_id: str, days_to_keep: int = 365) -> bool:
    """
    Archive messages older than specified days.

    This function implements file rotation by moving old messages to archive files,
    keeping the active sent_messages.json file manageable in size.

    Args:
        user_id: The user ID
        days_to_keep: Number of days to keep in active file

    Returns:
        bool: True if archiving successful
    """
    if user_id is None:
        logger.error("archive_old_messages called with None user_id")
        return False

    try:
        file_path = determine_file_path("sent_messages", user_id)
        data = load_json_data(file_path)

        if data:
            _normalize_message_timestamps(data, file_path)

        if not data:
            logger.debug(f"No messages to archive for user {user_id}")
            return True
        if data.get("schema_version") == SCHEMA_VERSION and isinstance(data.get("deliveries"), list):
            deliveries = data["deliveries"]
            if not deliveries:
                logger.debug(f"No deliveries to archive for user {user_id}")
                return True
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            active_deliveries = []
            archived_deliveries = []
            for delivery in deliveries:
                sent_at = _parse_message_timestamp(str(delivery.get("sent_at") or ""))
                if sent_at >= cutoff_date:
                    active_deliveries.append(delivery)
                else:
                    archived_deliveries.append(delivery)
            if not archived_deliveries:
                logger.debug(f"No deliveries to archive for user {user_id}")
                return True
            archive_filename = f"sent_messages_archive_{now_timestamp_filename()}.json"
            archive_path = Path(file_path).parent / archive_filename
            archive_data = {
                "schema_version": SCHEMA_VERSION,
                "archived_date": now_timestamp_full(),
                "deliveries": archived_deliveries,
                "metadata": {
                    "count": len(archived_deliveries),
                    "oldest_message": min(
                        (msg.get("sent_at", "") for msg in archived_deliveries), default=""
                    ),
                    "newest_message": max(
                        (msg.get("sent_at", "") for msg in archived_deliveries), default=""
                    ),
                },
            }
            save_json_data(archive_data, str(archive_path))
            data["deliveries"] = active_deliveries
            data["updated_at"] = now_timestamp_full()
            save_json_data(data, file_path)
            logger.info(
                f"Archived {len(archived_deliveries)} sent deliveries for user {user_id} to {archive_filename}"
            )
            return True

        # Calculate cutoff date
        # NOTE: This is timezone-aware UTC state used for retention filtering.
        # core.time_utilities currently provides local-naive "now" helpers only,
        # so this usage does not map cleanly without adding new helpers.
        # Keep as-is for correctness.
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        messages = data["messages"]
        active_messages = []
        archived_messages = []

        for message in messages:
            message_timestamp = _parse_message_timestamp(message.get("timestamp", ""))
            if message_timestamp >= cutoff_date:
                active_messages.append(message)
            else:
                archived_messages.append(message)

        if not archived_messages:
            logger.debug(f"No messages to archive for user {user_id}")
            return True

        # Create archive file
        archive_dir = Path(file_path).parent / "archives"
        archive_dir.mkdir(exist_ok=True)

        archive_filename = f"sent_messages_archive_{now_timestamp_filename()}.json"
        archive_path = archive_dir / archive_filename

        # Save archived messages
        archive_data = {
            "metadata": {
                "version": "2.0",
                # Canonical readable timestamp for metadata/log display fields
                "archived_date": now_timestamp_full(),
                "original_file": str(file_path),
                "total_messages": len(archived_messages),
                "date_range": {
                    "oldest": min(
                        msg.get("timestamp", "") for msg in archived_messages
                    ),
                    "newest": max(
                        msg.get("timestamp", "") for msg in archived_messages
                    ),
                },
            },
            "messages": archived_messages,
        }

        save_json_data(archive_data, str(archive_path))

        # Update active file
        data["messages"] = active_messages
        data["metadata"]["total_messages"] = len(active_messages)
        # Canonical readable timestamp for metadata/log display fields
        data["metadata"]["last_archived"] = now_timestamp_full()
        data["metadata"]["archived_count"] = len(archived_messages)

        save_json_data(data, file_path)

        logger.info(
            f"Archived {len(archived_messages)} old messages for user {user_id} to {archive_path}"
        )
        return True

    except Exception as e:
        logger.error(f"Error archiving old messages for user {user_id}: {e}")
        return False


@handle_errors(
    "parsing message timestamp",
    # IMPORTANT: avoid datetime.now() here (it would be evaluated at import time).
    # Use the same "invalid timestamp" sentinel the function already returns.
    default_return=datetime.min.replace(tzinfo=timezone.utc),
)
def _parse_message_timestamp(timestamp_str: str) -> datetime:
    """
    Parse timestamp string to datetime object.

    Args:
        timestamp_str: Timestamp string to parse

    Returns:
        datetime: Parsed datetime object (UTC) or sentinel minimum
    """
    if not timestamp_str:
        return datetime.min.replace(tzinfo=timezone.utc)

    parsed = parse_timestamp_full(timestamp_str)
    if parsed is None:
        return datetime.min.replace(tzinfo=timezone.utc)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)

    return parsed


@handle_errors(
    "normalizing message timestamps",
    default_return=False,
    user_friendly=False,
)
def _normalize_message_timestamps(
    data: dict[str, Any], file_path: str | Path
) -> bool:
    """
    Normalize timestamps in persisted sent_messages data to the canonical TIMESTAMP_FULL shape.

    Returns:
        bool: True if any timestamps were rewritten.
    """
    messages = data.get("messages")
    if not isinstance(messages, list):
        return False

    normalized_count = 0
    for message in messages:
        timestamp_value = message.get("timestamp", "")
        if not timestamp_value:
            continue

        if parse_timestamp_full(timestamp_value) is not None:
            continue

        # Legacy fallback removed: data should be pre-migrated via scripts/migrate_sent_messages_timestamps.py
        logger.debug(
            f"Skipping non-TIMESTAMP_FULL timestamp in {file_path}: {timestamp_value!r}"
        )
        continue

    if not normalized_count:
        return False

    file_path_obj = Path(file_path)
    save_json_data(data, str(file_path_obj))
    logger.info(
        f"Normalized {normalized_count} legacy timestamps in {file_path_obj}"
    )

    return True


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

        formatted_messages = [message for message in default_messages if isinstance(message, dict)]

        if not formatted_messages:
            logger.error(f"No valid messages found in defaults for category {category}")
            return False

        # Create user message file with proper format
        # Note: messages directory should be created by create_user_files() during account creation
        user_messages_dir = Path(get_user_data_dir(user_id)) / "messages"
        # Ensure the messages directory exists
        user_messages_dir.mkdir(parents=True, exist_ok=True)
        category_message_file = user_messages_dir / f"{category}.json"
        message_data = {
            "schema_version": SCHEMA_VERSION,
            "category": category,
            "updated_at": now_timestamp_full(),
            "messages": [
                _message_template_default_to_v2(message, category)
                for message in formatted_messages
            ],
        }
        # Convert Path to string for save_json_data
        success = save_json_data(message_data, str(category_message_file))
        if not success:
            logger.error(
                f"Failed to save message file for user {user_id}, category {category}"
            )
            return False
        logger.info(
            f"Created message file for user {user_id}, category {category} from defaults ({len(formatted_messages)} messages)"
        )
        return True

    except Exception as e:
        logger.error(
            f"Error creating message file for user {user_id}, category {category}: {e}"
        )
        return False


@handle_errors("ensuring user message files exist")
def ensure_user_message_files(user_id: str, categories: list[str]) -> dict:
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
            "files_existing": 0,
        }

    try:
        # Create messages directory for user if it doesn't exist
        user_messages_dir = Path(get_user_data_dir(user_id)) / "messages"
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
                logger.debug(
                    f"Created missing message file for category {category} for user {user_id}"
                )
            else:
                logger.warning(
                    f"Failed to create missing message file for category {category} for user {user_id}"
                )

        # Count existing files as successes
        existing_count = len(categories) - len(missing_categories)
        total_success = success_count + existing_count

        result = {
            "success": total_success == len(categories),
            "directory_created": directory_created,
            "files_checked": len(categories),
            "files_created": success_count,
            "files_existing": existing_count,
        }

        # Only log if files were actually created or if there were issues
        if success_count > 0 or not result["success"]:
            logger.info(
                f"Ensured message files for user {user_id}: {total_success}/{len(categories)} categories (created {success_count} new files, directory_created={directory_created})"
            )
        else:
            logger.debug(
                f"Verified message files for user {user_id}: {total_success}/{len(categories)} categories (all files already exist)"
            )
        return result

    except Exception as e:
        logger.error(f"Error ensuring user message files for user {user_id}: {e}")
        return {
            "success": False,
            "directory_created": False,
            "files_checked": len(categories),
            "files_created": 0,
            "files_existing": 0,
        }


@handle_errors("getting timestamp for sorting", default_return=0.0)
def get_timestamp_for_sorting(item):
    """
    Convert timestamp to float for consistent sorting.

    Args:
        item: Dictionary containing a timestamp field or other data type

    Returns:
        float: Timestamp as float for sorting, or 0.0 for invalid items
    """
    if isinstance(item, str) or not isinstance(item, dict):
        return 0.0
    timestamp = item.get("timestamp", "1970-01-01 00:00:00")
    try:
        dt = parse_timestamp_full(timestamp)
        if dt is None:
            return 0.0
        return dt.timestamp()
    except (ValueError, TypeError):
        return 0.0
