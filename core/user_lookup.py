"""
Resolve identifier to user_id.
"""

import os
from pathlib import Path

from core.logger import get_component_logger
from core.error_handling import handle_errors

from core.user_management import get_all_user_ids
from core.user_data_read import get_user_data

logger = get_component_logger("main")


def _scan_user_accounts_for_field(
    field_name: str, value: str, label: str, *, compare_as_string: bool = False
) -> str | None:
    """Fallback directory scan for account fields not found in user_index.json."""
    logger.debug(f"Falling back to directory scan for {label} '{value}'")
    user_ids = get_all_user_ids()
    for user_id in user_ids:
        user_data_result = get_user_data(user_id, "account")
        account_data = user_data_result.get("account")
        if not account_data:
            continue
        stored_value = account_data.get(field_name, "")
        if compare_as_string:
            if str(stored_value) == str(value):
                return user_id
        elif stored_value == value:
            return user_id
    return None


@handle_errors("getting user id by chat id", default_return=None)
def _get_user_id_by_identifier__by_chat_id(chat_id: str) -> str | None:
    if not chat_id:
        return None
    user_ids = get_all_user_ids()
    for user_id in user_ids:
        user_data_result = get_user_data(user_id, "account")
        account_data = user_data_result.get("account")
        if account_data and account_data.get("chat_id") == chat_id:
            return user_id
    return None


@handle_errors("getting user id by identifier", default_return=None)
def get_user_id_by_identifier(identifier: str) -> str | None:
    """
    Get user ID by any identifier (internal_username, email, discord_user_id, phone).
    """
    if not identifier:
        return None
    try:
        from core.config import BASE_DATA_DIR
        from core.file_locking import safe_json_read

        index_file = str(Path(BASE_DATA_DIR) / "user_index.json")
        index_data = safe_json_read(index_file, default={})
        if identifier in index_data:
            mapped = index_data[identifier]
            if isinstance(mapped, str) and mapped:
                return mapped
            try:
                users_dir = str(Path(BASE_DATA_DIR) / "users" / identifier)
                if os.path.isdir(users_dir):
                    return identifier
            except Exception:
                pass
        email_key = f"email:{identifier}"
        if email_key in index_data:
            return index_data[email_key]
        discord_key = f"discord:{identifier}"
        if discord_key in index_data:
            return index_data[discord_key]
        phone_key = f"phone:{identifier}"
        if phone_key in index_data:
            return index_data[phone_key]
    except Exception as e:
        logger.warning(
            f"Error looking up user by identifier '{identifier}' in index: {e}"
        )

    account_field_lookups = [
        ("internal_username", "internal_username", False),
        ("email", "email", False),
        ("discord_user_id", "discord_user_id", True),
        ("phone", "phone", False),
    ]
    for account_field, label, compare_as_string in account_field_lookups:
        result = _scan_user_accounts_for_field(
            account_field,
            identifier,
            label,
            compare_as_string=compare_as_string,
        )
        if result:
            return result
    return None
