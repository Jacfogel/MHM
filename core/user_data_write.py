"""
Save pipeline for user data: validate, merge, invariants, write, save_user_data, save_user_data_transaction.
"""

import os
import contextlib
import copy
from typing import Any

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.config import get_user_file_path, get_user_data_dir
from core.user_data_validation import (
    validate_new_user_data,
    validate_user_update,
)
from core.schemas import (
    validate_account_dict,
    validate_preferences_dict,
    validate_schedules_dict,
)

from core.user_data_registry import (
    get_available_data_types,
    clear_user_caches,
)
from core.user_data_read import get_user_data
from core.user_data_schedule_defaults import ensure_all_categories_have_schedules

logger = get_component_logger("main")

_DATA_TYPE_PROCESSING_ORDER = [
    "account",
    "preferences",
    "schedules",
    "context",
    "messages",
    "tasks",
]


@handle_errors("validating input parameters", default_return=(False, {}, []))
def _save_user_data__validate_input(
    user_id: str, data_updates: dict[str, dict[str, Any]]
) -> tuple[bool, dict[str, bool], list[str]]:
    if not user_id or not isinstance(user_id, str):
        return False, {}, [f"Invalid user_id: {user_id}"]
    if not user_id.strip():
        return False, {}, ["Empty user_id provided"]
    if not data_updates or not isinstance(data_updates, dict):
        return False, {}, [f"Invalid data_updates: {type(data_updates)}"]
    if not user_id:
        logger.error("save_user_data called with None user_id")
        return False, {}, []
    if not data_updates:
        logger.warning("save_user_data called with empty data_updates")
        return False, {}, []
    result: dict[str, bool] = {dt: False for dt in data_updates}
    available_types = get_available_data_types()
    invalid_types = [dt for dt in data_updates if dt not in available_types]
    if invalid_types:
        logger.error(
            f"Invalid data types in save_user_data: {invalid_types}. Valid types: {available_types}"
        )
    return True, result, invalid_types


@handle_errors("creating user data backup", default_return=False)
def _save_user_data__create_backup(
    user_id: str, valid_types: list[str], create_backup: bool
) -> bool:
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id for backup: {user_id}")
        return False
    if not isinstance(valid_types, list):
        logger.error(f"Invalid valid_types: {valid_types}")
        return False
    if create_backup and len(valid_types) > 1:
        try:
            from core.user_data_manager import UserDataManager
            backup_path = UserDataManager().backup_user_data(user_id)
            logger.info(f"Created backup before major data update: {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to create backup before data update: {e}")
    return True


@handle_errors("validating user data", default_return=([], {}))
def _save_user_data__validate_data(
    user_id: str,
    data_updates: dict[str, dict[str, Any]],
    valid_types: list[str],
    validate_data: bool,
    is_new_user: bool,
) -> tuple[list[str], dict[str, bool]]:
    if not user_id or not isinstance(user_id, str):
        return [f"Invalid user_id: {user_id}"], {}
    if not isinstance(data_updates, dict):
        return [f"Invalid data_updates: {type(data_updates)}"], {}
    result: dict[str, bool] = {dt: False for dt in data_updates}
    invalid_types = []
    if not validate_data:
        return invalid_types, result
    if is_new_user and valid_types:
        ok, errors = validate_new_user_data(user_id, data_updates)
        if not ok:
            logger.error(f"New-user validation failed: {errors}")
            return invalid_types, result
    if not is_new_user:
        for dt in valid_types:
            logger.debug(f"Validating {dt} for existing user {user_id}")
            ok, errors = validate_user_update(user_id, dt, data_updates[dt])
            if not ok and dt == "account":
                try:
                    upd = data_updates.get(dt, {})
                    feats = upd.get("features", {}) if isinstance(upd, dict) else {}
                    if (
                        isinstance(feats, dict)
                        and feats
                        and all(v in ("enabled", "disabled") for v in feats.values())
                    ):
                        logger.debug(
                            "Bypassing strict validation for account feature-only update"
                        )
                        ok = True
                        errors = []
                except Exception:
                    pass
            if not ok and dt == "preferences":
                with contextlib.suppress(Exception):
                    logger.debug(
                        f"Preferences validation returned errors: {errors}, but checking if data is still usable"
                    )
            if not ok:
                logger.error(f"Validation failed for {dt}: {errors}")
                result[dt] = False
                invalid_types.append(dt)
            else:
                logger.debug(f"Validation passed for {dt}")
    return invalid_types, result


@handle_errors("preserving preference settings", default_return=False)
def _save_user_data__preserve_preference_settings(
    updated: dict[str, Any], updates: dict[str, Any], user_id: str
) -> bool:
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id for preference settings: {user_id}")
        return False
    if not isinstance(updated, dict):
        logger.error(f"Invalid updated data: {type(updated)}")
        return False
    return True


@handle_errors("normalizing user data", default_return=False)
def _save_user_data__normalize_data(dt: str, updated: dict[str, Any]) -> bool:
    if not dt or not isinstance(dt, str):
        logger.error(f"Invalid data type: {dt}")
        return False
    if not isinstance(updated, dict):
        logger.error(f"Invalid updated data: {type(updated)}")
        return False
    try:
        if dt == "account":
            normalized, errors = validate_account_dict(updated)
            if normalized:
                updated.clear()
                updated.update(normalized)
        elif dt == "preferences":
            normalized, errors = validate_preferences_dict(updated)
            if not errors and normalized:
                try:
                    original_categories = set(
                        updated.get("categories", [])
                        if isinstance(updated.get("categories"), list)
                        else []
                    )
                    normalized_categories = set(
                        normalized.get("categories", [])
                        if isinstance(normalized.get("categories"), list)
                        else []
                    )
                    merged_categories = sorted(
                        original_categories | normalized_categories
                    )
                    normalized["categories"] = merged_categories
                except Exception:
                    pass
                updated.clear()
                updated.update(normalized)
        elif dt == "schedules":
            normalized, errors = validate_schedules_dict(updated)
            if not errors and normalized:
                updated.clear()
                updated.update(normalized)
    except Exception:
        pass
    return True


@handle_errors("merging data type updates", default_return=None)
def _save_user_data__merge_single_type(
    user_id: str, dt: str, updates: dict[str, Any], auto_create: bool
) -> dict[str, Any] | None:
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id: {user_id}")
        return None
    if not dt or not isinstance(dt, str):
        logger.error(f"Invalid data type: {dt}")
        return None
    if not isinstance(updates, dict):
        logger.error(f"Invalid updates: {type(updates)}")
        return None
    try:
        if not auto_create:
            user_dir = get_user_data_dir(user_id)
            if not os.path.exists(user_dir):
                logger.debug(
                    f"User directory doesn't exist for {user_id} and auto_create=False, skipping merge"
                )
                return None
        current = get_user_data(user_id, dt, auto_create=auto_create).get(dt, {})
        updated = current.copy() if isinstance(current, dict) else {}
        preserve_categories_order: list | None = None
        if (
            dt == "preferences"
            and isinstance(updates, dict)
            and isinstance(updates.get("categories"), list)
        ):
            preserve_categories_order = list(updates["categories"])
        for key, value in updates.items():
            if value is None:
                updated.pop(key, None)
            elif (
                key == "features"
                and isinstance(value, dict)
                and isinstance(updated.get(key), dict)
            ):
                updated[key].update(value)
            else:
                updated[key] = value
        if dt == "account":
            if "email" in updates and not updated.get("email"):
                updated["email"] = updates["email"]
        elif dt == "preferences":
            _save_user_data__preserve_preference_settings(updated, updates, user_id)
        _save_user_data__normalize_data(dt, updated)
        if dt == "account":
            try:
                if not updated.get("internal_username"):
                    prior_username = (
                        current.get("internal_username")
                        if isinstance(current, dict)
                        else None
                    )
                    updated["internal_username"] = prior_username or user_id
            except Exception:
                pass
        if dt == "preferences" and preserve_categories_order is not None:
            try:
                seen = set()
                ordered_unique = []
                for cat in preserve_categories_order:
                    if isinstance(cat, str) and cat and cat not in seen:
                        seen.add(cat)
                        ordered_unique.append(cat)
                updated["categories"] = ordered_unique
            except Exception:
                pass
        logger.debug(
            f"Merge {dt}: current={current}, updates={updates}, merged={updated}"
        )
        return updated
    except Exception as e:
        logger.error(f"Error merging {dt} data for user {user_id}: {e}")
        return None


@handle_errors("updating user index", default_return=False)
def _save_user_data__update_index(
    user_id: str, result: dict[str, bool], update_index: bool
) -> bool:
    if not user_id or not isinstance(user_id, str):
        logger.error(f"Invalid user_id for index update: {user_id}")
        return False
    if not isinstance(result, dict):
        logger.error(f"Invalid result: {type(result)}")
        return False
    if update_index and any(result.values()):
        try:
            from core.user_data_manager import update_user_index
            update_user_index(user_id)
        except Exception as e:
            logger.warning(
                f"Failed to update user index after data save for user {user_id}: {e}"
            )
    if any(result.values()):
        try:
            clear_user_caches(user_id)
            logger.debug(f"Cleared cache for user {user_id} after data save")
        except Exception as e:
            logger.warning(f"Failed to clear cache for user {user_id}: {e}")
    return True


@handle_errors("checking cross-file invariants", default_return=None)
def _save_user_data__check_cross_file_invariants(
    user_id: str, merged_data: dict[str, dict[str, Any]], valid_types: list[str]
) -> dict[str, dict[str, Any]] | None:
    try:
        account_data = merged_data.get("account")
        preferences_data = merged_data.get("preferences")
        if "account" not in valid_types:
            account_result = get_user_data(user_id, "account", auto_create=False)
            account_data = account_result.get("account", {})
        if "preferences" not in valid_types:
            prefs_result = get_user_data(user_id, "preferences", auto_create=False)
            preferences_data = prefs_result.get("preferences", {})
        if preferences_data:
            categories_list = preferences_data.get("categories", [])
            if isinstance(categories_list, list) and len(categories_list) > 0:
                if not account_data:
                    account_result = get_user_data(
                        user_id, "account", auto_create=False
                    )
                    account_data = account_result.get("account", {})
                if account_data:
                    feats = (
                        dict(account_data.get("features", {}))
                        if isinstance(account_data.get("features"), dict)
                        else {}
                    )
                    if feats.get("automated_messages") != "enabled":
                        feats["automated_messages"] = "enabled"
                        if "account" in valid_types:
                            merged_data["account"]["features"] = feats
                        else:
                            if "account" not in merged_data:
                                merged_account = (
                                    copy.deepcopy(account_data) if account_data else {}
                                )
                                _save_user_data__normalize_data(
                                    "account", merged_account
                                )
                                merged_data["account"] = merged_account
                            if "features" not in merged_data["account"]:
                                merged_data["account"]["features"] = {}
                            merged_data["account"]["features"].update(feats)
                with contextlib.suppress(Exception):
                    ensure_all_categories_have_schedules(user_id, suppress_logging=True)
        return merged_data
    except Exception as e:
        logger.error(f"Error checking cross-file invariants for user {user_id}: {e}")
        return None


@handle_errors("merging all data types in-memory", default_return=None)
def _save_user_data__merge_all_types(
    user_id: str,
    data_updates: dict[str, dict[str, Any]],
    valid_types: list[str],
    auto_create: bool,
) -> dict[str, dict[str, Any]] | None:
    merged_data = {}
    for dt in valid_types:
        updates = data_updates.get(dt, {})
        merged = _save_user_data__merge_single_type(user_id, dt, updates, auto_create)
        if merged is None:
            logger.error(f"Failed to merge {dt} for user {user_id}")
            return None
        merged_data[dt] = merged
    return merged_data


@handle_errors("writing all data types to disk", default_return={})
def _save_user_data__write_all_types(
    user_id: str, merged_data: dict[str, dict[str, Any]], valid_types: list[str]
) -> dict[str, bool]:
    from core.file_operations import save_json_data
    result = {}
    for dt in valid_types:
        if dt not in merged_data:
            result[dt] = False
            continue
        try:
            user_dir = get_user_data_dir(user_id)
            os.makedirs(user_dir, exist_ok=True)
            file_path = get_user_file_path(user_id, dt)
            success = save_json_data(merged_data[dt], file_path)
            result[dt] = success
            logger.debug(f"Wrote {dt} data for user {user_id}: success={success}")
        except Exception as e:
            logger.error(f"Error writing {dt} data for user {user_id}: {e}")
            result[dt] = False
    return result


@handle_errors("saving user data", default_return={})
def save_user_data(
    user_id: str,
    data_updates: dict[str, dict[str, Any]],
    auto_create: bool = True,
    update_index: bool = True,
    create_backup: bool = True,
    validate_data: bool = True,
) -> dict[str, bool]:
    """
    Save user data with two-phase approach: merge/validate in Phase 1, write in Phase 2.
    """
    is_valid, result, invalid_types = _save_user_data__validate_input(
        user_id, data_updates
    )
    if not is_valid:
        return result

    valid_types_to_process = [dt for dt in data_updates if dt not in invalid_types]
    valid_types_to_process.sort(
        key=lambda dt: (
            _DATA_TYPE_PROCESSING_ORDER.index(dt)
            if dt in _DATA_TYPE_PROCESSING_ORDER
            else len(_DATA_TYPE_PROCESSING_ORDER)
        )
    )

    account_file = get_user_file_path(user_id, "account")
    is_new_user = not os.path.exists(account_file)
    logger.debug(
        f"save_user_data: user_id={user_id}, is_new_user={is_new_user}, account_file_exists={os.path.exists(account_file)}, valid_types={valid_types_to_process}"
    )

    merged_data = _save_user_data__merge_all_types(
        user_id, data_updates, valid_types_to_process, auto_create
    )
    if merged_data is None:
        return {dt: False for dt in valid_types_to_process}

    if validate_data:
        merged_updates = {dt: merged_data[dt] for dt in valid_types_to_process}
        invalid_types_from_validation, validation_result = (
            _save_user_data__validate_data(
                user_id,
                merged_updates,
                valid_types_to_process,
                validate_data,
                is_new_user,
            )
        )
        result.update(validation_result)
        if (
            "preferences" in invalid_types_from_validation
            and "preferences" in merged_data
        ):
            try:
                normalized_prefs, pref_errors = validate_preferences_dict(
                    merged_data["preferences"]
                )
                if not pref_errors or (
                    len(pref_errors) == 1
                    and "Invalid categories" in str(pref_errors[0])
                ):
                    logger.debug(
                        "Preferences validation had non-critical errors, allowing save after normalization"
                    )
                    merged_data["preferences"] = normalized_prefs
                    invalid_types_from_validation.remove("preferences")
                    result["preferences"] = True
            except Exception as e:
                logger.debug(f"Could not normalize preferences: {e}")
        if "schedules" in invalid_types_from_validation and "schedules" in merged_data:
            try:
                normalized_schedules, schedule_errors = validate_schedules_dict(
                    merged_data["schedules"]
                )
                if not schedule_errors:
                    logger.debug(
                        "Schedules validation had non-critical errors, allowing save after normalization"
                    )
                    merged_data["schedules"] = normalized_schedules
                    invalid_types_from_validation.remove("schedules")
                    result["schedules"] = True
            except Exception as e:
                logger.debug(f"Could not normalize schedules: {e}")
        valid_types_to_process = [
            dt
            for dt in valid_types_to_process
            if dt not in invalid_types_from_validation
        ]
        for dt in invalid_types_from_validation:
            merged_data.pop(dt, None)

    updated_merged_data = _save_user_data__check_cross_file_invariants(
        user_id, merged_data, valid_types_to_process
    )
    if updated_merged_data is None:
        logger.error(f"Cross-file invariants check failed for user {user_id}")
        return {dt: False for dt in valid_types_to_process}

    merged_data = updated_merged_data

    for dt in merged_data:
        if (
            dt not in valid_types_to_process
            and (dt == "account" or dt in data_updates)
        ):
            valid_types_to_process.append(dt)
    valid_types_to_process.sort(
        key=lambda dt: (
            _DATA_TYPE_PROCESSING_ORDER.index(dt)
            if dt in _DATA_TYPE_PROCESSING_ORDER
            else len(_DATA_TYPE_PROCESSING_ORDER)
        )
    )

    logger.debug(f"After invariants: valid_types_to_process={valid_types_to_process}")
    _save_user_data__create_backup(user_id, valid_types_to_process, create_backup)

    write_results = _save_user_data__write_all_types(
        user_id, merged_data, valid_types_to_process
    )
    result.update(write_results)
    _save_user_data__update_index(user_id, result, update_index)
    return result


@handle_errors("saving user data with transaction", default_return=False)
def save_user_data_transaction(
    user_id: str, data_updates: dict[str, dict[str, Any]], auto_create: bool = True
) -> bool:
    """Atomic wrapper for user data updates."""
    if not user_id or not data_updates:
        return False
    try:
        from core.user_data_manager import UserDataManager
        backup_path = UserDataManager().backup_user_data(user_id)
        logger.info(f"Created backup before transaction: {backup_path}")
    except Exception as e:
        logger.warning(f"Failed to create backup before transaction: {e}")

    result = save_user_data(
        user_id=user_id,
        data_updates=data_updates,
        auto_create=auto_create,
        update_index=False,
        create_backup=False,
        validate_data=True,
    )
    success = all(result.values())
    if success:
        try:
            from core.user_data_manager import update_user_index
            update_user_index(user_id)
        except Exception as e:
            logger.error(f"Transaction succeeded but failed to update index: {e}")
            success = False
    else:
        failed = [dt for dt, ok in result.items() if not ok]
        logger.error(f"Transaction failed for user {user_id}. Failed types: {failed}")
    return success
