"""
User Data Validation utilities for MHM.
This module centralizes all rules for validating user account, preferences,
context, and schedules data.  It supersedes the old core.validation helpers.
"""

# NOTE: This file is largely copied from the former core.validation.py and
# augmented; the old path now re-exports these symbols for backward
# compatibility.

import re
import os
from typing import Dict, Any, Tuple, List
from core.logger import get_logger, get_component_logger
from core.error_handling import handle_errors

logger = get_component_logger('main')
validation_logger = get_component_logger('user_activity')

# ---------------------------------------------------------------------------
# Primitive validators retained from old validation.py
# ---------------------------------------------------------------------------

@handle_errors("validating email", default_return=False)
def is_valid_email(email):
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

@handle_errors("validating phone", default_return=False)
def is_valid_phone(phone):
    if not phone:
        return False
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
    return cleaned.isdigit() and len(cleaned) >= 10

@handle_errors("validating time format", default_return=False)
def validate_time_format(time_str: str) -> bool:
    if not time_str:
        return False
    pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
    return bool(re.match(pattern, time_str))

@handle_errors("converting to title case", default_return="")
def title_case(text: str) -> str:
    """Convert text to title case while keeping certain small words lowercase."""
    if not text:
        return ""
    text = text.lower()
    abbreviations = ['a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'if', 'in', 'is', 'it', 'of', 'on', 'or', 'the', 'to', 'up', 'via']
    words = text.split()
    result = []
    for i, word in enumerate(words):
        if i == 0 or i == len(words)-1 or word not in abbreviations:
            result.append(word.capitalize())
        else:
            result.append(word)
    return ' '.join(result)

# ---------------------------------------------------------------------------
# High-level validators (moved & improved)
# ---------------------------------------------------------------------------

@handle_errors("validating user update", default_return=(False, ["Validation failed"]))
def validate_user_update(user_id: str, data_type: str, updates: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate partial updates to an existing user's data."""
    errors: List[str] = []
    if not user_id:
        errors.append("user_id is required")
    if not updates:
        errors.append("updates cannot be empty")

    # ACCOUNT ----------------------------------------------------------------
    if data_type == 'account':
        # Account validation is now handled by Pydantic models in core/schemas.py
        # This function is kept for backward compatibility but delegates to Pydantic
        from core.schemas import validate_account_dict
        try:
            # For updates, we need to merge with existing data to get a complete account
            # This maintains backward compatibility with the old validation approach
            try:
                from core.user_data_handlers import get_user_data
                current_account = get_user_data(user_id, 'account').get('account', {})
            except Exception:
                current_account = {}
            
            # Merge updates with current account for validation
            merged_account = current_account.copy()
            merged_account.update(updates)
            
            # Add user_id if not present (required by Pydantic)
            if 'user_id' not in merged_account:
                merged_account['user_id'] = user_id
            
            # Use Pydantic validation for account data
            _, validation_errors = validate_account_dict(merged_account)
            if validation_errors:
                errors.extend(validation_errors)
        except Exception as e:
            errors.append(f"Account validation error: {e}")

    # PREFERENCES -------------------------------------------------------------
    elif data_type == 'preferences':
        # Preferences validation is now handled by Pydantic models in core/schemas.py
        # This function is kept for backward compatibility but delegates to Pydantic
        from core.schemas import validate_preferences_dict
        try:
            # For updates, we need to merge with existing data to get complete preferences
            try:
                from core.user_data_handlers import get_user_data
                current_preferences = get_user_data(user_id, 'preferences').get('preferences', {})
            except Exception:
                current_preferences = {}
            
            # Merge updates with current preferences for validation
            merged_preferences = current_preferences.copy()
            merged_preferences.update(updates)
            
            # Use Pydantic validation for preferences data
            _, validation_errors = validate_preferences_dict(merged_preferences)
            if validation_errors:
                errors.extend(validation_errors)
        except Exception as e:
            errors.append(f"Preferences validation error: {e}")

    # CONTEXT -----------------------------------------------------------------
    elif data_type == 'context':
        dob = updates.get('date_of_birth')
        if dob:
            try:
                from datetime import datetime as _dt
                _dt.strptime(dob, '%Y-%m-%d')
            except ValueError:
                errors.append("date_of_birth must be in YYYY-MM-DD format")
        if 'custom_fields' in updates and not isinstance(updates['custom_fields'], dict):
            errors.append("custom_fields must be a dictionary")

    # SCHEDULES ---------------------------------------------------------------
    elif data_type == 'schedules':
        # Schedules validation is now handled by Pydantic models in core/schemas.py
        # This function is kept for backward compatibility but delegates to Pydantic
        from core.schemas import validate_schedules_dict
        try:
            # For updates, we need to merge with existing data to get complete schedules
            try:
                from core.user_data_handlers import get_user_data
                current_schedules = get_user_data(user_id, 'schedules').get('schedules', {})
            except Exception:
                current_schedules = {}
            
            # Merge updates with current schedules for validation
            merged_schedules = current_schedules.copy()
            merged_schedules.update(updates)
            
            # Use Pydantic validation for schedules data
            _, validation_errors = validate_schedules_dict(merged_schedules)
            if validation_errors:
                errors.extend(validation_errors)
        except Exception as e:
            errors.append(f"Schedules validation error: {e}")

    return len(errors) == 0, errors


@handle_errors("validating schedule periods", default_return=(False, ["Validation failed"]))
def validate_schedule_periods(periods: Dict[str, Dict[str, Any]], category: str = "unknown") -> Tuple[bool, List[str]]:
    """Validate schedule periods and return (is_valid, error_messages).
    
    Args:
        periods: Dictionary of period_name -> period_data
        category: Category name for error messages (e.g., "tasks", "check-ins")
    
    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors: List[str] = []
    
    if not periods:
        return False, [f"At least one time period is required for {category}."]
    
    # Check if any periods are active (excluding "ALL" period)
    active_periods = [name for name, data in periods.items() 
                     if isinstance(data, dict) and data.get('active', False) and name.upper() != "ALL"]
    if not active_periods:
        return False, [f"At least one time period must be enabled for {category}."]
    
    # Validate each period
    valid_days = ['ALL', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for period_name, period_data in periods.items():
        if not isinstance(period_data, dict):
            errors.append(f"Period '{period_name}' data must be a dictionary")
            continue
            
        # Check required fields - name is the dictionary key, so we don't need to check period_data.get('name')
        # The period_name is already validated by being a valid dictionary key
        
        # Validate times
        start_time = period_data.get('start_time')
        end_time = period_data.get('end_time')
        
        if not start_time or not end_time:
            errors.append(f"Period '{period_name}' must have both start_time and end_time")
            continue
            
        if not validate_time_format(start_time):
            errors.append(f"Period '{period_name}' has invalid start_time format: {start_time}")
            
        if not validate_time_format(end_time):
            errors.append(f"Period '{period_name}' has invalid end_time format: {end_time}")
            
        # Validate time ordering
        if start_time and end_time and validate_time_format(start_time) and validate_time_format(end_time):
            try:
                from datetime import datetime as _dt
                st = _dt.strptime(start_time, "%H:%M")
                et = _dt.strptime(end_time, "%H:%M")
                if st >= et:
                    errors.append(f"Period '{period_name}' start_time must be before end_time")
            except ValueError:
                # Already caught by format validation
                pass
        
        # Validate days for active periods
        if period_data.get('active', False):
            days = period_data.get('days', [])
            if not isinstance(days, list):
                errors.append(f"Period '{period_name}' days must be a list")
            elif not days:
                errors.append(f"Active period '{period_name}' must have at least one day selected")
            else:
                invalid_days = [d for d in days if d not in valid_days]
                if invalid_days:
                    errors.append(f"Period '{period_name}' has invalid days: {invalid_days}")
    
    return len(errors) == 0, errors


@handle_errors("validating new user data", default_return=(False, ["Validation failed"]))
def validate_new_user_data(user_id: str, data_updates: Dict[str, Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Validate complete dataset required for a brand-new user."""
    errors: List[str] = []
    if not user_id:
        errors.append("user_id is required")
    if not data_updates:
        errors.append("data_updates cannot be empty")

    from core.config import get_user_data_dir
    if os.path.exists(get_user_data_dir(user_id)):
        errors.append(f"User {user_id} already exists")

    # ACCOUNT (mandatory)
    account = data_updates.get('account')
    if not account:
        errors.append("account data is required for new user creation")
    else:
        if not account.get('internal_username'):
            errors.append("internal_username is required for new user creation")
        if account.get('email') and not is_valid_email(account['email']):
            errors.append("Invalid email format")
        if 'account_status' in account and account['account_status'] not in ['active', 'inactive', 'suspended']:
            errors.append("Invalid account_status. Must be one of: active, inactive, suspended")

    # PREFERENCES (mandatory for channel type)
    prefs = data_updates.get('preferences', {})
    if 'categories' in prefs and isinstance(prefs['categories'], list):
        from core.message_management import get_message_categories
        invalid = [c for c in prefs['categories'] if c not in get_message_categories()]
        if invalid:
            errors.append(f"Invalid categories: {invalid}")
    
    # Channel type validation - moved from account to preferences where it actually belongs
    channel = prefs.get('channel')
    if not isinstance(channel, dict) or not channel.get('type'):
        errors.append("channel.type is required for new user creation")
    elif channel['type'] not in ['email', 'discord', 'telegram']:
        errors.append("Invalid channel type. Must be one of: email, discord, telegram")

    # CONTEXT (optional)
    context = data_updates.get('context', {})
    if context.get('date_of_birth') and not validate_user_update(user_id, 'context', {'date_of_birth': context['date_of_birth']})[0]:
        errors.append("Invalid date_of_birth format")

    return len(errors) == 0, errors

# ---------------------------------------------------------------------------
# PERSONALIZATION VALIDATOR (moved from core.user_management)
# ---------------------------------------------------------------------------




@handle_errors("validating personalization data", default_return=(False, ["Validation failed"]))
def validate_personalization_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate *context/personalization* structure.

    No field is required; we only type-check fields that are present.
    This logic previously lived in ``core.user_management``.
    """

    errors: List[str] = []

    # Optional string fields
    for field in ("date_of_birth", "timezone"):
        if field in data and not isinstance(data[field], str):
            errors.append(f"Field {field} must be a string if present")

    # Optional list fields
    optional_lists = [
        "gender_identity",
        "reminders_needed",
        "loved_ones",
        "interests",
        "activities_for_encouragement",
        "notes_for_ai",
        "goals",
    ]
    for field in optional_lists:
        if field in data and not isinstance(data[field], list):
            errors.append(f"Field {field} must be a list if present")

    # custom_fields (dict of lists)
    custom_fields = data.get("custom_fields", {})
    if "custom_fields" in data and not isinstance(custom_fields, dict):
        errors.append("custom_fields must be a dictionary if present")
    else:
        for key in ("health_conditions", "medications_treatments"):
            if key in custom_fields and not isinstance(custom_fields[key], list):
                errors.append(f"Field {key} (in custom_fields) must be a list if present")

    # date_of_birth format
    if dob := data.get("date_of_birth"):
        try:
            from datetime import datetime as _dt
            _dt.strptime(dob, "%Y-%m-%d")
        except ValueError:
            errors.append("date_of_birth must be in YYYY-MM-DD format")

    # loved_ones list of dicts
    loved_ones = data.get("loved_ones", [])
    if not isinstance(loved_ones, list):
        errors.append("loved_ones must be a list if present")
    else:
        for idx, item in enumerate(loved_ones):
            if not isinstance(item, dict):
                errors.append(f"loved_one at index {idx} must be a dictionary")

    return len(errors) == 0, errors 