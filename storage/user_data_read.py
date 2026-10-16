"""
Read path for user data: get_user_data, caches, and ID helpers.

Uses storage.user_data_registry for loaders and cache clearing.
"""

import os
import uuid
from typing import Any

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.config import get_user_data_dir, get_user_file_path
from core.file_operations import load_json_data, save_json_data, determine_file_path
from core.profile_v2_io import ensure_profile_envelope
from core.profile_v2_schemas import (
    validate_account_v2_document,
    validate_preferences_v2_document,
    validate_schedules_v2_document,
)

from storage.user_data_registry import (
    USER_DATA_LOADERS,
    register_default_loaders,
    get_available_data_types,
)
from storage.user_data_registry import clear_user_caches as _registry_clear_user_caches
from storage.user_id import is_valid_user_id

logger = get_component_logger("main")


# error_handling_exclude: pure in-memory field projection; no I/O or external calls.
def _apply_fields_filter(
    data: Any,
    data_type: str,
    fields: str | list[str] | dict[str, str | list[str]] | None,
) -> Any:
    """Return *data* narrowed to the requested field selection for *data_type*."""
    if fields is None or data is None:
        return data
    if isinstance(fields, str):
        return data.get(fields) if isinstance(data, dict) else None
    if isinstance(fields, list):
        if not isinstance(data, dict):
            return None
        extracted = {f: data[f] for f in fields if f in data}
        return extracted if extracted else None
    if isinstance(fields, dict) and data_type in fields:
        type_fields = fields[data_type]
        if isinstance(type_fields, str):
            return data.get(type_fields) if isinstance(data, dict) else None
        if isinstance(type_fields, list) and isinstance(data, dict):
            extracted = {f: data[f] for f in type_fields if f in data}
            return extracted if extracted else None
    return data


def _finalize_get_user_data_payload(
    user_id: str,
    data_type: str,
    data: Any,
    *,
    fields: str | list[str] | dict[str, str | list[str]] | None,
    normalize_on_read: bool,
    include_metadata: bool,
    loader_info: dict[str, Any],
) -> Any:
    """Apply field filtering, optional validation/normalization, schedules shape, and metadata."""
    data = _apply_fields_filter(data, data_type, fields)

    if normalize_on_read and fields is None and isinstance(data, dict):
        # error_handling_exclude: best-effort read-time normalization; partial failures are skipped.
        try:
            if data_type == "account":
                envelope = ensure_profile_envelope("account", data)
                normalized, _errs = validate_account_v2_document(envelope)
                if normalized:
                    if not normalized.get("timezone"):
                        normalized["timezone"] = "UTC"
                    data = normalized
            elif data_type == "preferences":
                envelope = ensure_profile_envelope("preferences", data)
                normalized, _errs = validate_preferences_v2_document(envelope)
                if normalized:
                    try:
                        caller_categories = (
                            data.get("categories", [])
                            if isinstance(data.get("categories"), list)
                            else []
                        )
                        normalized_categories = (
                            normalized.get("categories", [])
                            if isinstance(normalized.get("categories"), list)
                            else []
                        )
                        seen = set()
                        merged = []
                        for cat in caller_categories + normalized_categories:
                            if isinstance(cat, str) and cat and cat not in seen:
                                seen.add(cat)
                                merged.append(cat)
                        normalized["categories"] = merged
                    except Exception:
                        pass
                    data = normalized
            elif data_type == "schedules":
                envelope = ensure_profile_envelope("schedules", data)
                normalized, _errs = validate_schedules_v2_document(envelope)
                if normalized and not _errs:
                    data = normalized
        except Exception:
            pass

    if data_type == "schedules" and isinstance(data, dict):
        try:
            if "schedules" in data and isinstance(data["schedules"], dict):
                data = data["schedules"]
        except Exception:
            pass

    if include_metadata and data is not None:
        ftype = loader_info.get("file_type")
        if isinstance(ftype, str) and ftype.strip():
            file_path_meta = get_user_file_path(user_id, ftype)
            if os.path.exists(file_path_meta):
                stat = os.stat(file_path_meta)
                metadata = {
                    "file_size": stat.st_size,
                    "modified_time": stat.st_mtime,
                    "file_path": file_path_meta,
                    "data_type": data_type,
                    "description": loader_info.get("description", ""),
                }
                if isinstance(data, dict):
                    data["_metadata"] = metadata
                else:
                    data = {"data": data, "_metadata": metadata}

    return data


# not_duplicate: clear_user_caches
@handle_errors("clearing user caches", default_return=None)
def clear_user_caches(user_id: str | None = None) -> None:
    """Clear user data caches (delegate to registry)."""
    _registry_clear_user_caches(user_id)


@handle_errors("ensuring unique ids", default_return=None)
def ensure_unique_ids(data: Any) -> Any:
    """Ensure all messages have unique canonical IDs."""
    if not data or "messages" not in data:
        return data
    existing_ids = set()
    for message in data["messages"]:
        if not isinstance(message, dict):
            continue
        raw_id = message.get("id")
        message_id = str(raw_id).strip() if raw_id is not None else ""
        if not message_id or message_id in existing_ids:
            message_id = str(uuid.uuid4())

        message["id"] = message_id

        existing_ids.add(message_id)
    return data


@handle_errors("loading and ensuring ids", default_return=None)
def load_and_ensure_ids(user_id: str) -> None:
    """Load messages for all categories and ensure IDs are unique for a user."""
    user_data = get_user_data(user_id, "preferences")
    if not user_data or "preferences" not in user_data:
        logger.warning(f"User preferences not found for user_id: {user_id}")
        return
    preferences = user_data["preferences"]
    categories = preferences.get("categories", [])
    if not categories:
        logger.debug(f"No categories found for user {user_id}")
        return
    for category in categories:
        file_path = determine_file_path("messages", f"{category}/{user_id}")
        data = load_json_data(file_path)
        if data:
            data = ensure_unique_ids(data)
            save_json_data(data, file_path)
    logger.debug(f"Ensured message ids are unique for user '{user_id}'")


# ERROR_HANDLING_EXCLUDE: pure registry-state inspection.
def _default_loaders_are_missing() -> bool:
    """Return whether any registered data type lacks a callable loader."""
    return any(
        not isinstance(info, dict) or not callable(info.get("loader"))
        for info in USER_DATA_LOADERS.values()
    )


# ERROR_HANDLING_EXCLUDE: pure request normalization.
def _requested_data_types(data_types: str | list[str]) -> list[str]:
    """Normalize the public ``data_types`` argument to a new list."""
    if data_types == "all":
        return list(USER_DATA_LOADERS)
    if isinstance(data_types, str):
        return [data_types]
    return list(data_types)


@handle_errors("checking whether user data may be read", default_return=False)
def _user_read_is_allowed(user_id: str, *, auto_create: bool) -> bool:
    """Return whether the requested read may access or create user documents.

    A user directory must already exist for every read. Non-creating reads also
    require the canonical account document, matching ``get_all_user_ids``'s
    definition of an existing user without importing the user-management layer.
    """
    user_dir = get_user_data_dir(user_id)
    if not user_dir or not os.path.isdir(user_dir):
        logger.debug(
            f"get_user_data: user directory missing for {user_id}; returning empty"
        )
        return False
    if auto_create:
        return True
    account_path = get_user_file_path(user_id, "account")
    if not account_path or not os.path.isfile(account_path):
        logger.debug(
            f"get_user_data: account missing for {user_id} with auto_create=False; returning empty"
        )
        return False
    return True


@handle_errors("loading a requested user document", default_return=(None, {}))
def _load_requested_document(
    user_id: str,
    data_type: str,
    *,
    auto_create: bool,
) -> tuple[Any, dict[str, Any]]:
    """Load one requested document and return it with its registry metadata."""
    loader_info = USER_DATA_LOADERS.get(data_type)
    if not isinstance(loader_info, dict) or not callable(loader_info.get("loader")):
        logger.warning(f"No loader registered for data type: {data_type}")
        return None, {}

    file_type = loader_info.get("file_type")
    if not isinstance(file_type, str) or not file_type:
        logger.warning(f"No file type registered for data type: {data_type}")
        return None, loader_info

    file_path = get_user_file_path(user_id, file_type)
    loader = loader_info["loader"]
    loader_name = getattr(loader, "__name__", repr(loader))
    if not auto_create and (not file_path or not os.path.isfile(file_path)):
        data = None
    else:
        data = loader(user_id, auto_create=auto_create)

    # A concurrent delete must not leak a cached document through a
    # non-creating read.
    if not auto_create and (not file_path or not os.path.isfile(file_path)):
        data = None

    if not data:
        log = logger.debug if os.getenv("MHM_TESTING") == "1" else logger.warning
        log(
            f"No data returned for {data_type} "
            f"(user={user_id}, path={file_path}, loader={loader_name})"
        )
    elif isinstance(data, dict):
        logger.debug(f"Loaded {data_type} keys: {list(data.keys())}")
    return data, loader_info


@handle_errors("getting user data", default_return={})
def get_user_data(
    user_id: str,
    data_types: str | list[str] = "all",
    fields: str | list[str] | dict[str, str | list[str]] | None = None,
    auto_create: bool = True,
    include_metadata: bool = False,
    normalize_on_read: bool = False,
) -> dict[str, Any]:
    """
    Get user data with comprehensive validation.

    Returns:
        Dict[str, Any]: User data dictionary, empty dict if failed
    """
    if not is_valid_user_id(user_id):
        logger.error(f"Invalid user_id: {user_id}")
        return {}
    logger.debug(f"get_user_data called: user_id={user_id}, data_types={data_types}")

    if _default_loaders_are_missing():
        register_default_loaders()
    if not _user_read_is_allowed(user_id, auto_create=auto_create):
        return {}

    requested_types = _requested_data_types(data_types)
    available_types = get_available_data_types()
    invalid_types = [dt for dt in requested_types if dt not in available_types]
    if invalid_types:
        logger.error(
            f"Invalid data types requested: {invalid_types}. Valid types: {available_types}"
        )
        return {}

    result: dict[str, Any] = {}

    for data_type in requested_types:
        data, loader_info = _load_requested_document(
            user_id,
            data_type,
            auto_create=auto_create,
        )
        data = _finalize_get_user_data_payload(
            user_id,
            data_type,
            data,
            fields=fields,
            normalize_on_read=normalize_on_read,
            include_metadata=include_metadata,
            loader_info=loader_info,
        )

        if data is not None:
            result[data_type] = data

    logger.debug(f"get_user_data returning data types: {sorted(result)}")
    return result
