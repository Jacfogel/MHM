"""
Resolve identifier to user_id: get_user_id_by_identifier and by_* helpers.
"""

import os
from pathlib import Path

from core.logger import get_component_logger
from core.error_handling import handle_errors

from core.user_management import get_all_user_ids
from core.user_data_read import get_user_data

logger = get_component_logger("main")


@handle_errors("getting user id by internal username", default_return=None)
def _get_user_id_by_identifier__by_internal_username(
    internal_username: str,
) -> str | None:
    if not internal_username:
        return None
    try:
        from core.config import BASE_DATA_DIR
        from core.file_locking import safe_json_read

        index_file = str(Path(BASE_DATA_DIR) / "user_index.json")
        index_data = safe_json_read(index_file, default={})
        if internal_username in index_data:
            return index_data[internal_username]
    except Exception as e:
        logger.warning(
            f"Error looking up user by internal_username '{internal_username}' in index: {e}"
        )
    logger.debug(
        f"Falling back to directory scan for internal_username '{internal_username}'"
    )
    user_ids = get_all_user_ids()
    for user_id in user_ids:
        user_data_result = get_user_data(user_id, "account")
        account_data = user_data_result.get("account")
        if account_data and account_data.get("internal_username") == internal_username:
            return user_id
    return None


@handle_errors("getting user id by email", default_return=None)
def _get_user_id_by_identifier__by_email(email: str) -> str | None:
    if not email:
        return None
    try:
        from core.config import BASE_DATA_DIR
        from core.file_locking import safe_json_read

        index_file = str(Path(BASE_DATA_DIR) / "user_index.json")
        index_data = safe_json_read(index_file, default={})
        email_key = f"email:{email}"
        if email_key in index_data:
            return index_data[email_key]
    except Exception as e:
        logger.warning(f"Error looking up user by email '{email}' in index: {e}")
    logger.debug(f"Falling back to directory scan for email '{email}'")
    user_ids = get_all_user_ids()
    for user_id in user_ids:
        user_data_result = get_user_data(user_id, "account")
        account_data = user_data_result.get("account")
        if account_data and account_data.get("email") == email:
            return user_id
    return None


@handle_errors("getting user id by phone", default_return=None)
def _get_user_id_by_identifier__by_phone(phone: str) -> str | None:
    if not phone:
        return None
    try:
        from core.config import BASE_DATA_DIR
        from core.file_locking import safe_json_read

        index_file = str(Path(BASE_DATA_DIR) / "user_index.json")
        index_data = safe_json_read(index_file, default={})
        phone_key = f"phone:{phone}"
        if phone_key in index_data:
            return index_data[phone_key]
    except Exception as e:
        logger.warning(f"Error looking up user by phone '{phone}' in index: {e}")
    logger.debug(f"Falling back to directory scan for phone '{phone}'")
    user_ids = get_all_user_ids()
    for user_id in user_ids:
        user_data_result = get_user_data(user_id, "account")
        account_data = user_data_result.get("account")
        if account_data and account_data.get("phone") == phone:
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


@handle_errors("getting user id by discord user id", default_return=None)
def _get_user_id_by_identifier__by_discord_user_id(
    discord_user_id: str,
) -> str | None:
    if not discord_user_id:
        return None
    try:
        from core.config import BASE_DATA_DIR
        from core.file_locking import safe_json_read

        index_file = str(Path(BASE_DATA_DIR) / "user_index.json")
        index_data = safe_json_read(index_file, default={})
        discord_key = f"discord:{discord_user_id}"
        if discord_key in index_data:
            return index_data[discord_key]
    except Exception as e:
        logger.warning(
            f"Error looking up user by discord_user_id '{discord_user_id}' in index: {e}"
        )
    logger.debug(
        f"Falling back to directory scan for discord_user_id '{discord_user_id}'"
    )
    user_ids = get_all_user_ids()
    for user_id in user_ids:
        user_data_result = get_user_data(user_id, "account")
        account_data = user_data_result.get("account")
        if account_data:
            stored_discord_id = account_data.get("discord_user_id", "")
            if str(stored_discord_id) == str(discord_user_id):
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

    result = _get_user_id_by_identifier__by_internal_username(identifier)
    if result:
        return result
    result = _get_user_id_by_identifier__by_email(identifier)
    if result:
        return result
    result = _get_user_id_by_identifier__by_discord_user_id(identifier)
    if result:
        return result
    result = _get_user_id_by_identifier__by_phone(identifier)
    if result:
        return result
    return None
