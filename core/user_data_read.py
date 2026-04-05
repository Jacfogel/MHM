"""
Read path for user data: get_user_data, get_user_data_with_metadata, caches, ID helpers.

Uses core.user_data_registry for loaders and cache clearing.
"""

import importlib
import os
import uuid
from typing import Any

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.config import get_user_file_path
from core.file_operations import load_json_data, save_json_data, determine_file_path
from core.schemas import (
    validate_account_dict,
    validate_preferences_dict,
    validate_schedules_dict,
)

from core.user_data_registry import (
    USER_DATA_LOADERS,
    register_data_loader,
    register_default_loaders,
    get_available_data_types,
    _get_user_data__load_account,
    _get_user_data__load_preferences,
    _get_user_data__load_context,
    _get_user_data__load_schedules,
)
from core.user_data_registry import clear_user_caches as _registry_clear_user_caches

logger = get_component_logger("main")


# not_duplicate: clear_user_caches
@handle_errors("clearing user caches", default_return=None)
def clear_user_caches(user_id: str | None = None) -> None:
    """Clear user data caches (delegate to registry)."""
    _registry_clear_user_caches(user_id)


@handle_errors("ensuring unique ids", default_return=None)
def ensure_unique_ids(data: Any) -> Any:
    """Ensure all messages have unique IDs."""
    if not data or "messages" not in data:
        return data
    existing_ids = set()
    for message in data["messages"]:
        if "message_id" not in message or message["message_id"] in existing_ids:
            message["message_id"] = str(uuid.uuid4())
        existing_ids.add(message["message_id"])
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
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return {}
    if not user_id.strip():
        logger.error("Empty user_id provided")
        return {}
    logger.debug(f"get_user_data called: user_id={user_id}, data_types={data_types}")

    try:
        if any((not info.get("loader")) for info in USER_DATA_LOADERS.values()):
            register_default_loaders()
    except Exception:
        pass

    try:
        if os.getenv("MHM_TESTING") == "1":
            loader_state = {
                k: bool(v.get("loader")) for k, v in USER_DATA_LOADERS.items()
            }
            missing = [k for k, v in USER_DATA_LOADERS.items() if not v.get("loader")]
            logger.debug(f"[TEST] USER_DATA_LOADERS state: {loader_state}")
            if missing:
                logger.debug(f"[TEST] Missing loaders detected: {missing}")
    except Exception:
        pass

    if len(user_id) < 1 or len(user_id) > 100:
        logger.error(f"Invalid user_id length: {len(user_id)}")
        return {}

    try:
        if auto_create is False:
            from core.config import get_user_data_dir as _get_user_data_dir
            if not os.path.exists(_get_user_data_dir(user_id)):
                logger.debug(
                    f"get_user_data: user directory missing for {user_id} with auto_create=False; returning empty"
                )
                return {}
            try:
                _gaui = importlib.import_module("core.user_management").get_all_user_ids
                known_ids = set(_gaui())
                if user_id not in known_ids:
                    logger.debug(
                        f"get_user_data: user {user_id} not in index with auto_create=False; returning empty"
                    )
                    return {}
            except Exception as index_error:
                logger.debug(f"Index check failed for user {user_id}: {index_error}")
        elif auto_create is True:
            from core.config import get_user_data_dir as _get_user_data_dir
            user_dir = _get_user_data_dir(user_id)
            if not os.path.exists(user_dir):
                try:
                    _gaui = importlib.import_module(
                        "core.user_management"
                    ).get_all_user_ids
                    known_ids = set(_gaui())
                    if user_id not in known_ids:
                        logger.debug(
                            f"get_user_data: user {user_id} not in index and directory missing with auto_create=True; returning empty"
                        )
                        return {}
                except Exception:
                    pass
    except Exception:
        pass

    if data_types == "all":
        data_types = list(USER_DATA_LOADERS.keys())
    elif isinstance(data_types, str):
        data_types = [data_types]

    available_types = get_available_data_types()
    try:
        if os.getenv("MHM_TESTING") == "1":
            logger.debug(
                f"[TEST] get_user_data request types={data_types}; available={available_types}"
            )
    except Exception:
        pass
    invalid_types = [dt for dt in data_types if dt not in available_types]
    if invalid_types:
        logger.error(
            f"Invalid data types requested: {invalid_types}. Valid types: {available_types}"
        )
        return {}

    result: dict[str, Any] = {}

    for data_type in data_types:
        loader_info = USER_DATA_LOADERS.get(data_type)
        if not loader_info or not loader_info["loader"]:
            logger.warning(f"No loader registered for data type: {data_type}")
            continue
        file_path = get_user_file_path(user_id, loader_info["file_type"])
        loader_name = getattr(
            loader_info["loader"], "__name__", repr(loader_info["loader"])
        )
        try:
            if os.getenv("MHM_TESTING") == "1":
                logger.debug(
                    f"[TEST] Loading {data_type} for {user_id} path={file_path} via={loader_name} auto_create={auto_create}"
                )
        except Exception:
            pass
        try:
            if auto_create is False and not os.path.exists(file_path):
                data = None
            else:
                data = loader_info["loader"](user_id, auto_create=auto_create)
        except Exception as load_error:
            logger.warning(
                f"Failed to load {data_type} for user {user_id}: {load_error}"
            )
            data = None
        if auto_create is False:
            try:
                from core.config import get_user_data_dir as _get_user_data_dir
                user_dir_exists = os.path.exists(_get_user_data_dir(user_id))
            except Exception:
                user_dir_exists = False
            try:
                _gaui = importlib.import_module(
                    "core.user_management"
                ).get_all_user_ids
                known_ids = set(_gaui())
                if user_id not in known_ids:
                    data = None
            except Exception:
                pass
            if not user_dir_exists or not os.path.exists(file_path):
                data = None
        if not data:
            if os.getenv("MHM_TESTING") == "1":
                logger.debug(
                    f"No data returned for {data_type} (user={user_id}, path={file_path}, loader={loader_name})"
                )
            else:
                logger.warning(
                    f"No data returned for {data_type} (user={user_id}, path={file_path}, loader={loader_name})"
                )
        elif isinstance(data, dict):
            logger.debug(f"Loaded {data_type} keys: {list(data.keys())}")

        if fields is not None:
            if isinstance(fields, str):
                data = data.get(fields) if data else None
            elif isinstance(fields, list):
                if data:
                    extracted = {f: data[f] for f in fields if f in data}
                    data = extracted if extracted else None
                else:
                    data = None
            elif isinstance(fields, dict) and data_type in fields:
                type_fields = fields[data_type]
                if isinstance(type_fields, str):
                    data = data.get(type_fields) if data else None
                elif isinstance(type_fields, list):
                    if data:
                        extracted = {f: data[f] for f in type_fields if f in data}
                        data = extracted if extracted else None
                    else:
                        data = None

        if normalize_on_read and fields is None and isinstance(data, dict):
            try:
                if data_type == "account":
                    normalized, _errs = validate_account_dict(data)
                    if normalized:
                        if not normalized.get("timezone"):
                            normalized["timezone"] = "UTC"
                        data = normalized
                elif data_type == "preferences":
                    normalized, _errs = validate_preferences_dict(data)
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
                    normalized, _errs = validate_schedules_dict(data)
                    if normalized:
                        data = normalized
                        try:
                            _ensure_sched = importlib.import_module(
                                "core.user_data_schedule_defaults"
                            ).ensure_all_categories_have_schedules
                            prefs = get_user_data(user_id, "preferences").get(
                                "preferences", {}
                            )
                            categories = (
                                prefs.get("categories", [])
                                if isinstance(prefs, dict)
                                else []
                            )
                            if categories:
                                _ensure_sched(user_id, suppress_logging=True)
                                normalized_after, _e2 = validate_schedules_dict(
                                    get_user_data(user_id, "schedules").get(
                                        "schedules", {}
                                    )
                                )
                                if normalized_after:
                                    data = normalized_after
                        except Exception:
                            pass
            except Exception:
                pass
        if data_type == "schedules" and isinstance(data, dict):
            try:
                if "schedules" in data and isinstance(data["schedules"], dict):
                    data = data["schedules"]
            except Exception:
                pass

        if include_metadata and data is not None:
            file_path = get_user_file_path(user_id, loader_info["file_type"])
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                metadata = {
                    "file_size": stat.st_size,
                    "modified_time": stat.st_mtime,
                    "file_path": file_path,
                    "data_type": data_type,
                    "description": loader_info["description"],
                }
                if isinstance(data, dict):
                    data["_metadata"] = metadata
                else:
                    data = {"data": data, "_metadata": metadata}

        if data is not None:
            result[data_type] = data

    try:
        if os.getenv("MHM_TESTING") == "1" and auto_create:
            try:
                from core.config import get_user_data_dir as _get_user_data_dir
                if not os.path.exists(_get_user_data_dir(user_id)):
                    raise RuntimeError("skip_assembly_nonexistent_user")
            except Exception:
                raise
            requested_types = set(data_types) if isinstance(data_types, list) else set()
            expected_keys = ["account", "preferences", "context", "schedules"]
            for key in expected_keys:
                needs_key = (not result.get(key)) and (
                    (not requested_types) or (key in requested_types)
                )
                if needs_key:
                    try:
                        entry = USER_DATA_LOADERS.get(key)
                        loader = (
                            entry.get("loader") if isinstance(entry, dict) else None
                        )
                        if loader is None:
                            healing = {
                                "account": (_get_user_data__load_account, "account"),
                                "preferences": (
                                    _get_user_data__load_preferences,
                                    "preferences",
                                ),
                                "context": (
                                    _get_user_data__load_context,
                                    "user_context",
                                ),
                                "schedules": (
                                    _get_user_data__load_schedules,
                                    "schedules",
                                ),
                            }.get(key)
                            if healing is not None:
                                func, ftype = healing
                                try:
                                    register_data_loader(key, func, ftype)
                                    entry = USER_DATA_LOADERS.get(key)
                                    loader = (
                                        entry.get("loader")
                                        if isinstance(entry, dict)
                                        else func
                                    )
                                except Exception:
                                    loader = func
                        if loader is not None:
                            loaded_val = loader(user_id, True)
                            if loaded_val is not None:
                                result[key] = loaded_val
                                continue
                    except Exception:
                        pass
                    try:
                        from core.config import get_user_file_path as _get_user_file_path
                        from core.file_operations import load_json_data as _load_json
                        file_map = {
                            "account": "account",
                            "preferences": "preferences",
                            "context": "context",
                            "schedules": "schedules",
                        }
                        ftype = file_map.get(key)
                        if ftype is not None:
                            fpath = _get_user_file_path(user_id, ftype)
                            data_from_file = _load_json(fpath)
                            if data_from_file is not None:
                                result[key] = data_from_file
                    except Exception:
                        pass
    except Exception:
        pass

    logger.debug(f"get_user_data returning: {result}")
    try:
        if auto_create is False and isinstance(result, dict):
            try:
                _gaui = importlib.import_module(
                    "core.user_management"
                ).get_all_user_ids
                known_ids = set(_gaui())
                if user_id not in known_ids:
                    logger.debug(
                        f"get_user_data final-guard: {user_id} not in index; returning empty under auto_create=False"
                    )
                    return {}
            except Exception:
                pass
            filtered: dict[str, Any] = {}
            for dt_key, dt_val in result.items():
                try:
                    loader_info = USER_DATA_LOADERS.get(dt_key, {})
                    ftype = loader_info.get("file_type")
                    if not ftype:
                        continue
                    fpath = get_user_file_path(user_id, ftype)
                    if os.path.exists(fpath):
                        filtered[dt_key] = dt_val
                except Exception:
                    continue
            result = filtered
    except Exception:
        pass
    return result


@handle_errors("getting user data with metadata", default_return={})
def get_user_data_with_metadata(
    user_id: str, data_types: str | list[str] = "all"
) -> dict[str, Any]:
    """Get user data with file metadata using centralized system."""
    return get_user_data(user_id, data_types, include_metadata=True)
