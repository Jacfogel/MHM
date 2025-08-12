"""
Centralized User Data Handlers for MHM.

This module provides a unified API for loading, saving, and managing user data
across all data types (account, preferences, context, schedules, etc.).
"""

import os
from pathlib import Path
import traceback
from typing import Dict, Any, List, Union, Optional
from core.logger import get_logger, get_component_logger
from core.error_handling import handle_errors
from core.config import get_user_file_path
from core.user_data_validation import (
    validate_new_user_data,
    validate_user_update,
)
from core.schemas import (
    validate_account_dict,
    validate_preferences_dict,
    validate_schedules_dict,
)
# Registry functions - these should stay in user_management for now
from core.user_management import (
    USER_DATA_LOADERS,
    get_available_data_types,
)

# ---------------------------------------------------------------------------
# DATA LOADER REGISTRY (re-exported from core.user_management)
# ---------------------------------------------------------------------------

# We keep the single source of truth in *core.user_management* for now, but
# re-export everything so that future modules never need to import that file
# directly.  When we fully retire the legacy module we can move the real
# implementation here without changing import paths again.

from core.user_management import (
    USER_DATA_LOADERS as USER_DATA_LOADERS,  # shared dict – same object
    register_data_loader,
)


def register_data_loader(
    data_type: str,
    loader_func,
    file_type: str,
    default_fields: List[str] | None = None,
    metadata_fields: List[str] | None = None,
    description: str = "",
):
    """Proxy to the original *register_data_loader*.

    Imported here so callers can simply do::

        from core.user_data_handlers import register_data_loader

    …and forget about *core.user_management*.
    """

    return register_data_loader(
        data_type,
        loader_func,
        file_type,
        default_fields=default_fields,
        metadata_fields=metadata_fields,
        description=description,
    )

logger = get_logger(__name__)
handlers_logger = get_component_logger('user_activity')

@handle_errors("getting user data", default_return={})
def get_user_data(
    user_id: str,
    data_types: Union[str, List[str]] = 'all',
    fields: Optional[Union[str, List[str], Dict[str, Union[str, List[str]]]]] = None,
    auto_create: bool = True,
    include_metadata: bool = False
) -> Dict[str, Any]:
    """Migrated implementation of get_user_data."""
    logger.debug(f"get_user_data called: user_id={user_id}, data_types={data_types}")
    
    if not user_id:
        logger.error("get_user_data called with None user_id")
        return {}

    # Normalize data_types
    if data_types == 'all':
        data_types = list(USER_DATA_LOADERS.keys())
    elif isinstance(data_types, str):
        data_types = [data_types]

    # Validate data types
    available_types = get_available_data_types()
    invalid_types = [dt for dt in data_types if dt not in available_types]
    if invalid_types:
        logger.error(f"Invalid data types requested: {invalid_types}. Valid types: {available_types}")
        return {}

    result: Dict[str, Any] = {}

    for data_type in data_types:
        loader_info = USER_DATA_LOADERS.get(data_type)
        if not loader_info or not loader_info['loader']:
            logger.warning(f"No loader registered for data type: {data_type}")
            continue

        data = loader_info['loader'](user_id, auto_create=auto_create)

        # Field extraction logic
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

        # Metadata section
        if include_metadata and data is not None:
            file_path = get_user_file_path(user_id, loader_info['file_type'])
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                metadata = {
                    'file_size': stat.st_size,
                    'modified_time': stat.st_mtime,
                    'file_path': file_path,
                    'data_type': data_type,
                    'description': loader_info['description']
                }
                if isinstance(data, dict):
                    data['_metadata'] = metadata
                else:
                    data = {'data': data, '_metadata': metadata}

        if data is not None:
            result[data_type] = data

    logger.debug(f"get_user_data returning: {result}")
    return result 

@handle_errors("saving user data", default_return={})

def save_user_data(
    user_id: str,
    data_updates: Dict[str, Dict[str, Any]],
    auto_create: bool = True,
    update_index: bool = True,
    create_backup: bool = True,
    validate_data: bool = True
) -> Dict[str, bool]:
    """Migrated implementation of save_user_data."""
    # -------------------------------------------------------------------
    # 0. Early sanity-checks & unified result scaffolding
    # -------------------------------------------------------------------
    if not user_id:
        logger.error("save_user_data called with None user_id")
        return {}
    if not data_updates:
        logger.warning("save_user_data called with empty data_updates")
        return {}

    # Provide a predictable result structure from the outset – every
    # requested data_type gets an entry that defaults to False until the
    # corresponding save operation succeeds.
    result: Dict[str, bool] = {dt: False for dt in data_updates}

    available_types = get_available_data_types()
    invalid_types = [dt for dt in data_updates if dt not in available_types]
    if invalid_types:
        logger.error(f"Invalid data types in save_user_data: {invalid_types}. Valid types: {available_types}")
        # Don’t raise/return early – we’ll simply skip these types and
        # keep their result as False so callers can detect the failure.

    # -------------------------------------------------------------------
    # 1. Optional backup (only when more than one valid data_type supplied)
    # -------------------------------------------------------------------
    valid_types_to_process = [dt for dt in data_updates if dt not in invalid_types]
    if create_backup and len(valid_types_to_process) > 1:
        try:
            from core.user_data_manager import UserDataManager
            backup_path = UserDataManager().backup_user_data(user_id)
            logger.info(f"Created backup before major data update: {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to create backup before data update: {e}")

    # -------------------------------------------------------------------
    # 2. Validation Phase
    # -------------------------------------------------------------------
    from core.config import get_user_data_dir
    is_new_user = not os.path.exists(get_user_data_dir(user_id))
    
    logger.debug(f"save_user_data: user_id={user_id}, is_new_user={is_new_user}, valid_types={valid_types_to_process}")

    # a) Whole-dataset validation for a brand-new user
    if validate_data and is_new_user and valid_types_to_process:
        ok, errors = validate_new_user_data(user_id, data_updates)
        if not ok:
            logger.error(f"New-user validation failed: {errors}")
            # Nothing else to do – we already defaulted all types to False
            return result

    # b) Per-data-type validation for existing users
    if validate_data and not is_new_user:
        for dt in valid_types_to_process:
            logger.debug(f"Validating {dt} for existing user {user_id}")
            ok, errors = validate_user_update(user_id, dt, data_updates[dt])
            if not ok:
                logger.error(f"Validation failed for {dt}: {errors}")
                # Mark as failed and remove from further processing
                result[dt] = False
                invalid_types.append(dt)
            else:
                logger.debug(f"Validation passed for {dt}")

    # Refresh valid list after validation failures
    valid_types_to_process = [dt for dt in valid_types_to_process if dt not in invalid_types]
    logger.debug(f"After validation: valid_types_to_process={valid_types_to_process}")

    # -------------------------------------------------------------------
    # 3. Save Phase – iterate only over types that passed validation
    # -------------------------------------------------------------------
    for dt in valid_types_to_process:
        updates = data_updates[dt]
        try:
            current = get_user_data(user_id, dt, auto_create=auto_create).get(dt, {})
            updated = current.copy() if isinstance(current, dict) else {}
            updated.update(updates)

            # LEGACY COMPATIBILITY: Preserve legacy account fields
            # TODO: Remove after callers no longer write 'channel' or 'enabled_features' into account.json
            # REMOVAL PLAN:
            # 1. Log warnings whenever legacy fields are used (below)
            # 2. Add metrics to track frequency over 2 weeks
            # 3. Remove preservation and update tests/callers accordingly
            # NOTE: Channel data lives in preferences.json; enabled feature flags live under account.features
            # This block preserves backward compatibility only.
            if dt == "account":
                if "channel" in updates:
                    updated["channel"] = updates["channel"]
                    try:
                        logger.warning(
                            "LEGACY COMPATIBILITY: 'account.channel' was provided and preserved. Move channel to preferences.channel."
                        )
                    except Exception:
                        pass
                if "enabled_features" in updates:
                    updated["enabled_features"] = updates["enabled_features"]
                    try:
                        logger.warning(
                            "LEGACY COMPATIBILITY: 'account.enabled_features' was provided and preserved. Use account.features subkeys instead."
                        )
                    except Exception:
                        pass

            # Pydantic normalization – non-blocking
            try:
                if dt == "account":
                    updated, _ = validate_account_dict(updated)
                elif dt == "preferences":
                    # LEGACY COMPATIBILITY: Detect nested 'enabled' flags in preferences and warn.
                    # TODO: Remove after all callers stop writing nested enabled flags
                    # REMOVAL PLAN:
                    # 1. Log a one-time warning when these fields are detected
                    # 2. Track usage via logs/metrics for 2 weeks
                    # 3. Start stripping in a future release and update tests/callers
                    try:
                        has_enabled = (
                            isinstance(updated.get("task_settings"), dict) and "enabled" in updated["task_settings"]
                        ) or (
                            isinstance(updated.get("checkin_settings"), dict) and "enabled" in updated["checkin_settings"]
                        )
                        if has_enabled and not globals().get("_warned_enabled_flags_present", False):
                            logger.warning(
                                "LEGACY COMPATIBILITY: Found nested 'enabled' flags under preferences. "
                                "These will be deprecated; prefer account.features."
                            )
                            globals()["_warned_enabled_flags_present"] = True
                    except Exception:
                        pass
                    # If corresponding features are disabled, remove entire settings blocks only for "full" updates
                    # (heuristic: presence of 'categories' implies a full preferences payload). Partial updates preserve blocks.
                    try:
                        acct = get_user_data(user_id, 'account').get('account', {})
                        features = acct.get('features', {}) if isinstance(acct, dict) else {}
                        is_full_update = isinstance(updates, dict) and ('categories' in updates)
                        # Task settings removal when feature disabled and caller did not re-provide the block
                        if (
                            is_full_update and
                            features.get('task_management') == 'disabled' and
                            'task_settings' not in updates and
                            'task_settings' in updated
                        ):
                            updated.pop('task_settings', None)
                            try:
                                logger.warning(
                                    "LEGACY COMPATIBILITY: Removed preferences.task_settings because tasks are disabled "
                                    "and a full preferences update omitted this block."
                                )
                            except Exception:
                                pass
                        # Check-in settings removal when feature disabled and caller did not re-provide the block
                        if (
                            is_full_update and
                            features.get('checkins') == 'disabled' and
                            'checkin_settings' not in updates and
                            'checkin_settings' in updated
                        ):
                            updated.pop('checkin_settings', None)
                            try:
                                logger.warning(
                                    "LEGACY COMPATIBILITY: Removed preferences.checkin_settings because checkins are disabled "
                                    "and a full preferences update omitted this block."
                                )
                            except Exception:
                                pass
                    except Exception:
                        pass
                    updated, _ = validate_preferences_dict(updated)
                elif dt == "schedules":
                    updated, _ = validate_schedules_dict(updated)
            except Exception:
                pass
            
            logger.debug(f"Save {dt}: current={current}, updates={updates}, merged={updated}")

            # Use the unified save approach - save the data directly
            from core.file_operations import save_json_data
            from core.config import get_user_file_path
            
            file_path = get_user_file_path(user_id, dt)
            success = save_json_data(updated, file_path)
            result[dt] = success
            logger.debug(f"Saved {dt} data for user {user_id}: success={success}")
        except Exception as e:
            logger.error(f"Error saving {dt} data for user {user_id}: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception traceback: {traceback.format_exc()}")
            result[dt] = False

    # -------------------------------------------------------------------
    # 4. Index update (only if at least one type succeeded)
    # -------------------------------------------------------------------
    if update_index and any(result.values()):
        try:
            from core.user_data_manager import update_user_index
            update_user_index(user_id)
        except Exception as e:
            logger.warning(f"Failed to update user index after data save for user {user_id}: {e}")

    # -------------------------------------------------------------------
    # 5. Cache clearing (if any saves succeeded)
    # -------------------------------------------------------------------
    if any(result.values()):
        try:
            from core.user_management import clear_user_caches
            clear_user_caches(user_id)
            logger.debug(f"Cleared cache for user {user_id} after data save")
        except Exception as e:
            logger.warning(f"Failed to clear cache for user {user_id}: {e}")

    return result

@handle_errors("saving user data with transaction", default_return=False)

def save_user_data_transaction(
    user_id: str,
    data_updates: Dict[str, Dict[str, Any]],
    auto_create: bool = True
) -> bool:
    """Atomic wrapper copied from user_management."""
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

# ---------------------------------------------------------------------------
# CORE UTILITY WRAPPERS (TEMPORARY)
# ---------------------------------------------------------------------------

# These wrappers expose commonly-used utilities from *user_management* so that
# external modules can depend on ``core.user_data_handlers`` only.  They simply
# delegate to the original implementations while we migrate call-sites.  Once
# every caller is updated, the real implementation can be moved here and the
# legacy exports removed.


@handle_errors("getting all user IDs (centralised)", default_return=[])
def get_all_user_ids() -> List[str]:
    """Return a list of *all* user IDs known to the system."""
    from core.user_management import get_all_user_ids as management_get_all_user_ids
    return management_get_all_user_ids()


@handle_errors("updating user schedules (centralised)", default_return=False)
def update_user_schedules(user_id: str, schedules_data: Dict[str, Any]) -> bool:
    """Persist a complete schedules dict for *user_id*.

    Wrapper around the original helper in **core.user_management** – keeps
    outside modules decoupled from the legacy path.
    """
    from core.user_management import update_user_schedules as management_update_user_schedules
    return management_update_user_schedules(user_id, schedules_data)

# ---------------------------------------------------------------------------
# HIGH-LEVEL UPDATE HELPERS (migrated from core.user_management)
# ---------------------------------------------------------------------------

# NOTE:  These helper functions intentionally *duplicate* the public update
# API provided by ``core.user_management`` so that other modules can migrate
# to importing directly from ``core.user_data_handlers``.  Once all callers
# have switched over we can remove the legacy versions (see TODO.md).


@handle_errors("updating user account (centralised)", default_return=False)
def update_user_account(user_id: str, updates: Dict[str, Any], *, auto_create: bool = True) -> bool:
    """Update (part of) a user’s *account.json* file.

    This is a thin convenience wrapper around :pyfunc:`save_user_data` that
    scopes *updates* to the ``account`` data-type.
    """
    if not user_id:
        logger.error("update_user_account called with None user_id")
        return False

    result = save_user_data(user_id, {"account": updates}, auto_create=auto_create)
    return result.get("account", False)


@handle_errors("updating user preferences (centralised)", default_return=False)
def update_user_preferences(user_id: str, updates: Dict[str, Any], *, auto_create: bool = True) -> bool:
    """Update *preferences.json*.

    Includes the extra bookkeeping originally implemented in
    ``core.user_management.update_user_preferences`` (default schedule creation
    for new categories, message-file creation, etc.) so behaviour remains
    unchanged.
    """
    if not user_id:
        logger.error("update_user_preferences called with None user_id")
        return False

    # -------------------------------------------------------------------
    # Extra category bookkeeping (imported lazily to avoid circular deps)
    # -------------------------------------------------------------------
    if "categories" in updates:
        try:
            from core.user_management import (
                ensure_category_has_default_schedule,
                ensure_all_categories_have_schedules,
            )
            from core.message_management import ensure_user_message_files

            preferences_data = get_user_data(user_id, "preferences")
            if preferences_data is None:
                logger.warning(f"Could not load or create preferences for user {user_id}")
            else:
                old_categories = set(preferences_data.get("categories", []))
                new_categories = set(updates["categories"])
                added_categories = new_categories - old_categories

                if added_categories:
                    logger.info(
                        f"Categories update detected for user {user_id}: added={added_categories}"
                    )

                # Create default schedules for any new categories
                for category in added_categories:
                    ensure_category_has_default_schedule(user_id, category)

                # Double-check all categories have schedules
                ensure_all_categories_have_schedules(user_id)

                # Ensure message files exist for newly added categories
                if added_categories:
                    try:
                        result_files = ensure_user_message_files(user_id, list(added_categories))
                        logger.info(
                            "Category update for user %s: created %s message files for %d new "
                            "categories (directory_created=%s)",
                            user_id,
                            result_files.get("files_created"),
                            len(added_categories),
                            result_files.get("directory_created"),
                        )
                    except Exception as e:
                        logger.error(
                            "Error creating message files for user %s after category update: %s", user_id, e
                        )
        except Exception as err:
            logger.warning(
                "Category bookkeeping skipped for user %s due to import error: %s", user_id, err
            )

    # -------------------------------------------------------------------
    # Persist updates via the central save path
    # -------------------------------------------------------------------
    result = save_user_data(user_id, {"preferences": updates}, auto_create=auto_create)
    return result.get("preferences", False)


@handle_errors("updating user context (centralised)", default_return=False)
def update_user_context(user_id: str, updates: Dict[str, Any], *, auto_create: bool = True) -> bool:
    """Update *user_context.json* for the given user."""
    if not user_id:
        logger.error("update_user_context called with None user_id")
        return False

    result = save_user_data(user_id, {"context": updates}, auto_create=auto_create)
    return result.get("context", False)


@handle_errors("updating channel preferences (centralised)", default_return=False)
def update_channel_preferences(user_id: str, updates: Dict[str, Any], *, auto_create: bool = True) -> bool:
    """Specialised helper – update only the *preferences.channel* subtree."""
    if not user_id:
        logger.error("update_channel_preferences called with None user_id")
        return False

    result = save_user_data(user_id, {"preferences": updates}, auto_create=auto_create)
    return result.get("preferences", False) 