"""
Shared tag normalization and validation for MHM.

This module provides a unified tag system used by both tasks and notebook features.
Tags are normalized (lowercase, stripped) and validated for consistency across the system.
Tags are stored in data/users/<user_id>/tags.json and created lazily on first use.
"""

import re
import json
from pathlib import Path
from typing import Any
from datetime import datetime

from core.logger import get_component_logger
from core.error_handling import handle_errors, ValidationError
from core.config import get_user_data_dir, get_user_file_path
from core.file_operations import load_json_data, save_json_data

logger = get_component_logger("tags")


@handle_errors("normalizing tag")
def normalize_tag(tag: str) -> str:
    """
    Normalizes a single tag by stripping whitespace, lowercasing, and optionally removing a leading '#'.
    """
    if not isinstance(tag, str):
        logger.warning(f"Non-string tag provided for normalization: {tag}")
        return str(tag).strip().lower().lstrip("#")
    return tag.strip().lower().lstrip("#")


@handle_errors("normalizing tags list", default_return=[])
def normalize_tags(tags: list[str]) -> list[str]:
    """
    Normalizes a list of tags and removes duplicates.
    """
    if not isinstance(tags, list):
        logger.warning(f"Non-list tags provided for normalization: {tags}")
        return []
    seen = set()
    normalized_list = []
    for tag in tags:
        normalized = normalize_tag(tag)
        if normalized and normalized not in seen:
            seen.add(normalized)
            normalized_list.append(normalized)
    return normalized_list


@handle_errors("validating tag", default_return=None)
def validate_tag(tag: str) -> None:
    """
    Validates a single normalized tag for length and allowed characters.
    Raises ValidationError if invalid.
    """
    if not isinstance(tag, str) or not tag:
        raise ValidationError("Tag cannot be empty or non-string.")
    if len(tag) > 50:
        raise ValidationError("Tag cannot exceed 50 characters.")
    if not re.fullmatch(r"^[a-z0-9\-_:]+$", tag):
        raise ValidationError(
            "Tag contains invalid characters. Only lowercase alphanumeric, hyphens, underscores, and colons are allowed."
        )


@handle_errors("parsing tags from text", default_return=("", []))
def parse_tags_from_text(text: str) -> tuple[str, list[str]]:
    """
    Extracts tags (e.g., #tag, key:value) from a text string and returns the cleaned text and normalized tags.
    """
    if not isinstance(text, str):
        return text, []

    tags = []
    # Regex to find #tag or key:value patterns
    tag_pattern = re.compile(r"(?:#(\w+)|(\w+:\w+))")

    # Find all matches and remove them from the text
    cleaned_text_parts = []
    last_end = 0
    for match in tag_pattern.finditer(text):
        # Add the text before the current tag
        cleaned_text_parts.append(text[last_end : match.start()])

        # Extract the tag, preferring #tag over key:value if both match the same span (shouldn't happen with this regex)
        if match.group(1):  # #tag
            tags.append(match.group(1))
        elif match.group(2):  # key:value
            tags.append(match.group(2))

        last_end = match.end()

    # Add any remaining text after the last tag
    cleaned_text_parts.append(text[last_end:])
    cleaned_text = "".join(cleaned_text_parts).strip()

    # Deduplicate tags
    tags = normalize_tags(tags)

    return cleaned_text, tags


# Tag storage functions - lazy initialization only


@handle_errors("ensuring user directory for tags", default_return=None)
def ensure_user_dir_for_tags(user_id: str) -> Path | None:
    """
    Ensure user directory exists for tags (lazy creation).
    Tags are stored as tags.json in the root user directory, like checkins.json and schedules.json.

    Args:
        user_id: User ID

    Returns:
        Path to user directory, or None if failed
    """
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return None

    try:
        user_dir = Path(get_user_data_dir(user_id))

        # Create directory if it doesn't exist (lazy creation)
        user_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Ensured user directory exists: {user_dir}")
        return user_dir
    except Exception as e:
        logger.error(f"Error ensuring user directory for user {user_id}: {e}")
        return None


@handle_errors("loading default tags from resources", default_return=[])
def _load_default_tags_from_resources() -> list[str]:
    """
    Load default tags from resources/default_tags.json.

    Returns:
        List of default tag strings, empty list if file not found or invalid
    """
    try:
        default_tags_file = (
            Path(__file__).parent.parent / "resources" / "default_tags.json"
        )
        if not default_tags_file.exists():
            logger.warning(f"Default tags file not found: {default_tags_file}")
            return []

        with open(default_tags_file, encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict) and "tags" in data:
            tags = data.get("tags", [])
            if isinstance(tags, list):
                return normalize_tags(tags)

        logger.warning(f"Invalid format in default tags file: {default_tags_file}")
        return []
    except Exception as e:
        logger.error(f"Error loading default tags from resources: {e}")
        return []


@handle_errors("loading user tags", default_return={})
def load_user_tags(user_id: str) -> dict[str, Any]:
    """
    Load user tags data from tags.json (lazy initialization).
    Creates directory and file with default tags if they don't exist.

    Args:
        user_id: User ID

    Returns:
        Dictionary with tags data: {'tags': [...], 'metadata': {...}}
    """
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return {}

    try:
        # Ensure user directory exists (lazy creation)
        ensure_user_dir_for_tags(user_id)

        # Use get_user_file_path to get the tags file path (consistent with checkins, schedules, etc.)
        tags_file_path = get_user_file_path(user_id, "tags")
        tags_file = Path(tags_file_path)

        # If file doesn't exist, initialize with default tags
        if not tags_file.exists():
            logger.debug(
                f"Tags file not found for user {user_id}, initializing with defaults"
            )
            default_tags = _load_default_tags_from_resources()
            tags_data = {
                "tags": default_tags,
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "initialized_with_defaults": True,
                },
            }
            # Save the initialized file
            save_json_data(tags_data, str(tags_file))
            logger.info(
                f"Initialized tags file for user {user_id} with {len(default_tags)} default tags"
            )
            return tags_data

        # Load existing JSON data
        data = load_json_data(str(tags_file))

        # If file doesn't exist or is corrupted, initialize with defaults
        if data is None:
            logger.warning(
                f"Tags file corrupted for user {user_id}, reinitializing with defaults"
            )
            default_tags = _load_default_tags_from_resources()
            tags_data = {
                "tags": default_tags,
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "initialized_with_defaults": True,
                    "reinitialized": True,
                },
            }
            save_json_data(tags_data, str(tags_file))
            return tags_data

        # Ensure structure has required fields
        if not isinstance(data, dict):
            logger.warning(f"Invalid tags data structure for user {user_id}")
            default_tags = _load_default_tags_from_resources()
            return {
                "tags": default_tags,
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                },
            }

        # Normalize existing tags
        if "tags" in data and isinstance(data["tags"], list):
            data["tags"] = normalize_tags(data["tags"])

        return data

    except Exception as e:
        logger.error(f"Error loading tags for user {user_id}: {e}")
        return {}


@handle_errors("saving user tags", default_return=False)
def save_user_tags(user_id: str, tags_data: dict[str, Any]) -> bool:
    """
    Save user tags data to tags.json (lazy initialization).
    Tags are now registered in USER_DATA_LOADERS, so this function can be called
    directly or through save_user_data().

    Args:
        user_id: User ID
        tags_data: Dictionary with tags data

    Returns:
        True if successful, False otherwise
    """
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return False

    if not isinstance(tags_data, dict):
        logger.error(f"Invalid tags_data type: {type(tags_data)}")
        return False

    try:
        # Ensure user directory exists (lazy creation)
        ensure_user_dir_for_tags(user_id)

        # Use get_user_file_path to get the tags file path (consistent with checkins, schedules, etc.)
        tags_file_path = get_user_file_path(user_id, "tags")

        # Normalize tags before saving
        if "tags" in tags_data and isinstance(tags_data["tags"], list):
            tags_data["tags"] = normalize_tags(tags_data["tags"])

        # Update metadata
        if "metadata" not in tags_data:
            tags_data["metadata"] = {}
        tags_data["metadata"]["updated_at"] = datetime.now().isoformat()
        if "created_at" not in tags_data["metadata"]:
            tags_data["metadata"]["created_at"] = datetime.now().isoformat()

        # Use save_json_data directly (this is called by save_user_data internally)
        success = save_json_data(tags_data, tags_file_path)

        if success:
            logger.debug(f"Saved tags for user {user_id}")
        else:
            logger.error(f"Failed to save tags for user {user_id}")

        return success

    except Exception as e:
        logger.error(f"Error saving tags for user {user_id}: {e}")
        return False


@handle_errors("getting user tag list", default_return=[])
def get_user_tags(user_id: str) -> list[str]:
    """
    Get list of user's tags (lazy initialization).

    Args:
        user_id: User ID

    Returns:
        List of normalized tag strings
    """
    tags_data = load_user_tags(user_id)
    return tags_data.get("tags", [])


@handle_errors("adding user tag", default_return=False)
def add_user_tag(user_id: str, tag: str) -> bool:
    """
    Add a tag to user's tag list (lazy initialization).

    Args:
        user_id: User ID
        tag: Tag to add

    Returns:
        True if successful, False otherwise
    """
    if not user_id or not tag:
        logger.error(f"Invalid parameters: user_id={user_id}, tag={tag}")
        return False

    try:
        normalized_tag = normalize_tag(tag)
        if not normalized_tag:
            logger.error(f"Invalid tag format: '{tag}'")
            return False

        # Validate tag
        try:
            validate_tag(normalized_tag)
        except ValueError as e:
            logger.error(f"Invalid tag '{normalized_tag}': {e}")
            return False

        tags_data = load_user_tags(user_id)
        tags = tags_data.get("tags", [])

        if normalized_tag not in tags:
            tags.append(normalized_tag)
            tags_data["tags"] = tags

            if save_user_tags(user_id, tags_data):
                logger.info(f"Added tag '{normalized_tag}' for user {user_id}")
                return True
            else:
                logger.error(f"Failed to save tag for user {user_id}")
                return False
        else:
            logger.debug(f"Tag '{normalized_tag}' already exists for user {user_id}")
            return True

    except Exception as e:
        logger.error(f"Error adding tag for user {user_id}: {e}")
        return False


@handle_errors("removing user tag", default_return=False)
def remove_user_tag(user_id: str, tag: str) -> bool:
    """
    Remove a tag from user's tag list.

    Args:
        user_id: User ID
        tag: Tag to remove

    Returns:
        True if successful, False otherwise
    """
    if not user_id or not tag:
        logger.error(f"Invalid parameters: user_id={user_id}, tag={tag}")
        return False

    try:
        normalized_tag = normalize_tag(tag)
        if not normalized_tag:
            logger.error(f"Invalid tag format: '{tag}'")
            return False

        tags_data = load_user_tags(user_id)
        tags = tags_data.get("tags", [])

        if normalized_tag in tags:
            tags.remove(normalized_tag)
            tags_data["tags"] = tags

            if save_user_tags(user_id, tags_data):
                logger.info(f"Removed tag '{normalized_tag}' for user {user_id}")
                return True
            else:
                logger.error(f"Failed to save tag removal for user {user_id}")
                return False
        else:
            logger.debug(f"Tag '{normalized_tag}' not found for user {user_id}")
            return True

    except Exception as e:
        logger.error(f"Error removing tag for user {user_id}: {e}")
        return False


@handle_errors("ensuring tags initialized", default_return=None)
def ensure_tags_initialized(user_id: str) -> None:
    """
    Ensure tags.json is initialized for a user (lazy creation).
    This is called when tasks are enabled or when the first notebook entry is created,
    whichever happens first. Safe to call multiple times.

    Args:
        user_id: User ID
    """
    if not user_id:
        return

    try:
        # This will create tags.json file with defaults if it doesn't exist
        get_user_tags(user_id)
        logger.debug(f"Ensured tags initialized for user {user_id}")
    except Exception as e:
        logger.error(f"Error ensuring tags initialized for user {user_id}: {e}")
