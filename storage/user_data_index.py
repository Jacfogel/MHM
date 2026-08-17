"""User index update, rebuild, and search (ops/admin)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from core.error_handling import handle_errors
from core.file_operations import get_user_data_dir
from core.logger import get_component_logger
from core.time_utilities import now_timestamp_full
from core.user_management import get_all_user_ids
from storage.user_data_read import get_user_data
from storage.user_data_summaries import get_user_data_summary
from storage.user_data_user_info import (
    _get_user_categories,
    get_user_info_for_data_manager,
)
from storage.user_data_v2_base import SCHEMA_VERSION
from storage.user_data_v2_envelopes import validate_v2_document

logger = get_component_logger("main")


@handle_errors("resolving user index path", re_raise=True)
def _index_file_path(index_file: str | None = None) -> str:
    """Return the user_index.json path, using BASE_DATA_DIR when none is given."""
    if index_file:
        return index_file
    from core.config import BASE_DATA_DIR as current_base_dir

    return str(Path(current_base_dir) / "user_index.json")


# not_duplicate: update_user_index
@handle_errors("updating user index", default_return=False)
def update_user_index(user_id: str, index_file: str | None = None) -> bool:
    """
    Update the user index with current information for a specific user.

    Creates flat lookup mappings for fast O(1) user lookups:
    - {"internal_username": "UUID", "email:email": "UUID", "discord:discord_id": "UUID", "phone:phone": "UUID"}
    """
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return False

    if not user_id.strip():
        logger.error("Empty user_id provided")
        return False

    try:
        from core.file_locking import safe_json_read, safe_json_write

        index_path = _index_file_path(index_file)
        index_data = safe_json_read(index_path, default={"last_updated": None})

        user_data_result = None
        user_account = {}
        max_retries = 5
        retry_delay = 0.2

        for attempt in range(max_retries):
            try:
                user_data_result = get_user_data(user_id, "account")
                user_account = user_data_result.get("account") or {}
                if user_account and user_account.get("internal_username"):
                    break
            except Exception as e:
                logger.debug(
                    f"Attempt {attempt + 1}/{max_retries} to get account data for {user_id} failed: {e}"
                )

            if attempt < max_retries - 1:
                time.sleep(retry_delay)

        internal_username = user_account.get("internal_username", "")
        email = user_account.get("email", "")
        discord_user_id = user_account.get("discord_user_id", "")
        phone = user_account.get("phone", "")

        if not internal_username:
            if os.getenv("MHM_TESTING") == "1":
                logger.debug(
                    f"No internal_username found for user {user_id} after {max_retries} attempts (account keys: {list(user_account.keys())})"
                )
            else:
                logger.warning(
                    f"No internal_username found for user {user_id} after {max_retries} attempts (account keys: {list(user_account.keys())})"
                )
            return False

        if (
            internal_username not in index_data
            or index_data[internal_username] == user_id
        ):
            index_data[internal_username] = user_id

        if email:
            index_data[f"email:{email}"] = user_id
        if discord_user_id:
            index_data[f"discord:{discord_user_id}"] = user_id
        if phone:
            index_data[f"phone:{phone}"] = user_id

        index_data["last_updated"] = now_timestamp_full()

        max_write_retries = 3
        write_retry_delay = 0.15
        for write_attempt in range(max_write_retries):
            if safe_json_write(index_path, index_data, indent=4):
                logger.debug(
                    f"Updated user index for user {user_id} (internal_username: {internal_username})"
                )
                return True
            if write_attempt < max_write_retries - 1:
                logger.debug(
                    f"Write attempt {write_attempt + 1}/{max_write_retries} failed for {user_id}, retrying..."
                )
                time.sleep(write_retry_delay)

        logger.error(
            f"Failed to save user index for user {user_id} after {max_write_retries} attempts"
        )
        return False
    except Exception as e:
        logger.error(f"Error updating user index for user {user_id}: {e}")
        return False


@handle_errors("removing from index", default_return=False)
def remove_from_index(user_id: str, index_file: str | None = None) -> bool:
    """Remove all identifier mappings for a user from the index."""
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return False

    if not user_id.strip():
        logger.error("Empty user_id provided")
        return False

    try:
        from core.file_locking import safe_json_read, safe_json_write

        index_path = _index_file_path(index_file)
        index_data = safe_json_read(index_path, default={"last_updated": None})

        user_data_result = get_user_data(user_id, "account")
        user_account = user_data_result.get("account") or {}

        internal_username = user_account.get("internal_username")
        email = user_account.get("email")
        discord_user_id = user_account.get("discord_user_id")
        phone = user_account.get("phone")

        if internal_username and internal_username in index_data:
            del index_data[internal_username]
        if email and f"email:{email}" in index_data:
            del index_data[f"email:{email}"]
        if discord_user_id and f"discord:{discord_user_id}" in index_data:
            del index_data[f"discord:{discord_user_id}"]
        if phone and f"phone:{phone}" in index_data:
            del index_data[f"phone:{phone}"]

        index_data["last_updated"] = now_timestamp_full()

        if not safe_json_write(index_path, index_data, indent=4):
            logger.error(f"Failed to save user index after removing user {user_id}")
            return False

        logger.info(
            f"Removed user {user_id} (internal_username: {internal_username}) from index"
        )
        return True

    except Exception as e:
        logger.error(f"Error removing user {user_id} from index: {e}")
        return False


@handle_errors("rebuilding full index", default_return=False)
def rebuild_full_index(index_file: str | None = None) -> bool:
    """Rebuild the complete user index from scratch."""
    try:
        logger.info("Starting full user index rebuild...")

        user_ids = get_all_user_ids()
        if not user_ids:
            logger.warning("No users found during index rebuild")
            return True

        from core.file_locking import safe_json_write

        index_path = _index_file_path(index_file)
        index_data = {"last_updated": now_timestamp_full()}
        successful_count = 0
        failed_count = 0
        max_retries = 3
        retry_delay = 0.2

        for user_id in user_ids:
            if not user_id:
                continue

            user_account = {}
            for attempt in range(max_retries):
                try:
                    user_data_result = get_user_data(user_id, "account")
                    user_account = user_data_result.get("account") or {}
                    if user_account and user_account.get("internal_username"):
                        break
                except Exception as e:
                    logger.debug(
                        f"Attempt {attempt + 1}/{max_retries} to get account data for {user_id} during rebuild failed: {e}"
                    )

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

            internal_username = user_account.get("internal_username", "")
            email = user_account.get("email", "")
            discord_user_id = user_account.get("discord_user_id", "")
            phone = user_account.get("phone", "")

            if not internal_username:
                if os.getenv("MHM_TESTING") == "1":
                    logger.debug(
                        f"No internal_username found for user {user_id} after {max_retries} attempts, skipping"
                    )
                else:
                    logger.warning(
                        f"No internal_username found for user {user_id} after {max_retries} attempts, skipping"
                    )
                failed_count += 1
                continue

            index_data[internal_username] = user_id
            if email:
                index_data[f"email:{email}"] = user_id
            if discord_user_id:
                index_data[f"discord:{discord_user_id}"] = user_id
            if phone:
                index_data[f"phone:{phone}"] = user_id
            successful_count += 1

        max_write_retries = 3
        write_retry_delay = 0.15
        write_success = False
        for write_attempt in range(max_write_retries):
            if safe_json_write(index_path, index_data, indent=4):
                write_success = True
                break
            if write_attempt < max_write_retries - 1:
                logger.debug(
                    f"Write attempt {write_attempt + 1}/{max_write_retries} failed during rebuild, retrying..."
                )
                time.sleep(write_retry_delay)

        if not write_success:
            logger.error("Failed to save rebuilt user index after retries")
            return False

        if successful_count > 0:
            logger.info(
                f"Rebuilt user index with {successful_count} users (skipped {failed_count} users)"
            )
            return True
        if failed_count > 0:
            logger.error(
                f"Failed to index any users during rebuild ({failed_count} users failed)"
            )
            return False
        logger.info("Rebuilt user index (no users to index)")
        return True

    except Exception as e:
        logger.error(f"Error rebuilding full user index: {e}", exc_info=True)
        return False


@handle_errors("rebuilding user index", default_return=False)
def rebuild_user_index() -> bool:
    """Rebuild the complete user index."""
    return rebuild_full_index()


@handle_errors("searching users", default_return=[])
def search_users(
    query: str, search_fields: list[str] | None = None
) -> list[dict[str, Any]]:
    """Search for users based on query string and specified fields."""
    if not query or not isinstance(query, str):
        logger.error(f"Invalid query: {query}")
        return []

    if not query.strip():
        logger.error("Empty query provided")
        return []

    if search_fields is not None and not isinstance(search_fields, list):
        logger.error(f"Invalid search_fields: {search_fields}")
        return []
    if search_fields is None:
        search_fields = ["internal_username", "email", "discord_user_id", "phone"]

    if not query.strip():
        return []

    user_ids = get_all_user_ids()
    if not user_ids:
        return []

    matches = []
    for user_id in user_ids:
        user_data_result = get_user_data(user_id, "account")
        user_account = user_data_result.get("account") or {}

        match_found = False
        for field in search_fields:
            field_value = str(user_account.get(field, "")).lower()
            if query.lower() in field_value:
                match_found = True
                break

        if match_found:
            user_summary = get_user_data_summary(user_id)
            matches.append(
                {
                    "user_id": user_id,
                    "profile": user_account,
                    "summary": user_summary,
                }
            )

    return matches


@handle_errors("building user index", default_return={})
def build_user_index() -> dict[str, Any]:
    """Build an index of all users and their message data."""
    try:
        user_ids = get_all_user_ids()
        index_data = {}

        for user_id in user_ids:
            try:
                user_info = get_user_info_for_data_manager(user_id)
                if not user_info:
                    from core.file_locking import safe_json_read

                    account_path = Path(get_user_data_dir(user_id)) / "account.json"
                    if account_path.exists():
                        account_data = safe_json_read(str(account_path), default={})
                        if isinstance(account_data, dict) and account_data.get(
                            "internal_username"
                        ):
                            user_info = {
                                "user_id": user_id,
                                "internal_username": account_data.get(
                                    "internal_username", ""
                                ),
                                "preferred_name": "",
                                "account_status": account_data.get(
                                    "account_status", "unknown"
                                ),
                                "email": account_data.get("email", ""),
                                "message_files": {},
                            }
                    if not user_info:
                        continue

                message_count = 0
                categories = _get_user_categories(user_id)

                for category in categories:
                    category_path = str(
                        Path(get_user_data_dir(user_id))
                        / "messages"
                        / f"{category}.json"
                    )
                    if os.path.exists(category_path):
                        try:
                            with open(category_path, encoding="utf-8") as f:
                                data = json.load(f)
                                if (
                                    not isinstance(data, dict)
                                    or data.get("schema_version") != SCHEMA_VERSION
                                ):
                                    logger.warning(
                                        f"Skipping non-v2 message template file for index count: {category_path}"
                                    )
                                    continue
                                normalized, errors = validate_v2_document(
                                    "messages", data
                                )
                                if errors:
                                    logger.warning(
                                        f"Validation issues in {category_path}: {'; '.join(errors)}"
                                    )
                                message_count += len(normalized.get("messages", []))
                        except Exception as e:
                            logger.warning(
                                f"Error reading message file {category_path}: {e}"
                            )

                index_data[user_id] = {
                    "active": True,
                    "categories": sorted(set(categories)),
                    "last_updated": now_timestamp_full(),
                    "message_count": message_count,
                }

            except Exception as e:
                logger.error(f"Error processing user {user_id} for index: {e}")
                continue

        return index_data

    except Exception as e:
        logger.error(f"Error building user index: {e}")
        return {}
