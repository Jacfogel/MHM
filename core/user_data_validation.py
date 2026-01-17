"""
User Data Validation utilities for MHM.
This module centralizes all rules for validating user account, preferences,
context, and schedules data.
"""

import re
import os
from typing import Dict, Any, Tuple, List, Optional
from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.service_utilities import DATE_ONLY_FORMAT, TIME_HM_FORMAT

logger = get_component_logger("main")
validation_logger = get_component_logger("user_activity")

# ---------------------------------------------------------------------------
# Primitive validators
# ---------------------------------------------------------------------------


@handle_errors("validating email", default_return=False)
def is_valid_email(email):
    if not email:
        logger.debug("Email validation failed: empty email provided")
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    is_valid = bool(re.match(pattern, email))
    if is_valid:
        logger.debug(f"Email validation passed: {email}")
    else:
        logger.warning(f"Email validation failed: invalid format for '{email}'")
    return is_valid


@handle_errors("validating phone", default_return=False)
def is_valid_phone(phone):
    if not phone:
        logger.debug("Phone validation failed: empty phone provided")
        return False
    cleaned = re.sub(r"[\s\-\(\)\.]", "", phone)
    is_valid = cleaned.isdigit() and len(cleaned) >= 10
    if is_valid:
        logger.debug(f"Phone validation passed: {phone}")
    else:
        logger.warning(
            f"Phone validation failed: invalid format for '{phone}' (cleaned: '{cleaned}')"
        )
    return is_valid


@handle_errors("validating Discord ID", default_return=False)
def is_valid_discord_id(discord_id: str) -> bool:
    """
    Validate Discord user ID format.

    Discord user IDs are snowflakes (numeric IDs) that are 17-19 digits long.
    Empty strings are allowed (Discord ID is optional).

    Args:
        discord_id: The Discord user ID to validate

    Returns:
        bool: True if valid Discord ID format or empty, False otherwise
    """
    # Handle None explicitly
    if discord_id is None:
        logger.warning("Discord ID validation failed: None value provided")
        return False

    # Empty string is allowed (optional field)
    if discord_id == "":
        return True

    if not isinstance(discord_id, str):
        logger.warning(
            f"Discord ID validation failed: expected string, got {type(discord_id).__name__}"
        )
        return False

    # Remove whitespace
    cleaned = discord_id.strip()

    # Discord snowflake IDs are 17-19 digit numbers
    # Must be all digits and between 17-19 characters
    if cleaned.isdigit() and 17 <= len(cleaned) <= 19:
        logger.debug(f"Discord ID validation passed: {cleaned}")
        return True
    else:
        logger.warning(
            f"Discord ID validation failed: invalid format for '{discord_id}' (must be 17-19 digit number)"
        )
        return False


@handle_errors("validating time format", default_return=False)
def validate_schedule_periods__validate_time_format(time_str: str) -> bool:
    if not time_str:
        logger.debug("Time format validation failed: empty time provided")
        return False
    pattern = r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
    is_valid = bool(re.match(pattern, time_str))
    if is_valid:
        logger.debug(f"Time format validation passed: {time_str}")
    else:
        logger.warning(
            f"Time format validation failed: invalid format for '{time_str}'"
        )
    return is_valid


# ---------------------------------------------------------------------------
# General string validation helpers
# ---------------------------------------------------------------------------


@handle_errors("validating string length", default_return=False)
def is_valid_string_length(
    text: str | None,
    max_length: int,
    field_name: str = "string",
    allow_none: bool = False,
) -> bool:
    """
    Validate that a string is within the specified maximum length.

    Args:
        text: String to validate (can be None if allow_none=True)
        max_length: Maximum allowed length
        field_name: Name of the field being validated (for error messages)
        allow_none: Whether None values are allowed

    Returns:
        True if string length is valid, False otherwise
    """
    if text is None:
        return allow_none

    if not isinstance(text, str):
        logger.warning(f"{field_name} must be a string, got {type(text).__name__}")
        return False

    text = text.strip()

    if len(text) > max_length:
        logger.warning(
            f"{field_name} exceeds maximum length of {max_length} characters"
        )
        return False

    return True


@handle_errors("validating category name", default_return=False)
def is_valid_category_name(
    name: str | None,
    max_length: int = 50,
    field_name: str = "category",
    allow_none: bool = True,
) -> bool:
    """
    Validate that a category/group name is valid.

    Category names should be simple identifiers: alphanumeric, spaces, hyphens, underscores.
    This is used for grouping/categorizing items (e.g., notebook groups, task categories).

    Args:
        name: Category name to validate (can be None if allow_none=True)
        max_length: Maximum allowed length (default: 50)
        field_name: Name of the field being validated (for error messages)
        allow_none: Whether None values are allowed (default: True)

    Returns:
        True if category name is valid, False otherwise
    """
    if name is None:
        return allow_none

    if not isinstance(name, str):
        logger.warning(f"{field_name} must be a string, got {type(name).__name__}")
        return False

    name = name.strip()

    if not name:
        logger.warning(f"{field_name} cannot be empty (use None instead)")
        return False

    if len(name) > max_length:
        logger.warning(
            f"{field_name} exceeds maximum length of {max_length} characters"
        )
        return False

    # Category names should be simple identifiers (alphanumeric, spaces, hyphens, underscores)
    if not re.match(r"^[a-zA-Z0-9\s\-_]+$", name):
        logger.warning(
            f"{field_name} contains invalid characters. Only alphanumeric, spaces, hyphens, and underscores are allowed."
        )
        return False

    return True


@handle_errors("converting to title case", default_return="")
def _shared__title_case(text: str) -> str:
    """Convert text to title case with special handling for technical terms."""
    if text is None:
        return None
    if not text:
        return ""

    # Special words that should be all uppercase
    special_words = {
        "ai",
        "api",
        "ui",
        "ux",
        "mhm",
        "id",
        "url",
        "http",
        "https",
        "json",
        "xml",
        "yaml",
        "toml",
        "ini",
        "cfg",
        "log",
        "tmp",
        "temp",
        "etc",
        "usr",
        "var",
        "bin",
        "lib",
        "src",
        "doc",
        "docs",
        "test",
        "backup",
        "config",
        "data",
        "files",
        "images",
        "media",
        "audio",
        "video",
        "photos",
        "downloads",
        "uploads",
        "cache",
        "logs",
        "html",
        "css",
        "js",
        "asp",
        "jsp",
    }

    # Special case mappings
    special_mappings = {"dotnet": ".NET", "c++": "C++", "c#": "C#"}

    # Small words that should stay lowercase (except at beginning/end)
    small_words = {
        "a",
        "an",
        "and",
        "as",
        "at",
        "but",
        "by",
        "for",
        "if",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "the",
        "to",
        "up",
        "via",
    }

    words = text.lower().split()
    result = []

    for i, word in enumerate(words):
        # Check special mappings first
        if word in special_mappings:
            result.append(special_mappings[word])
        # Check if it's a special technical word that should be uppercase
        elif word in special_words:
            result.append(word.upper())
        # First/last word or not a small word - capitalize normally
        elif i == 0 or i == len(words) - 1 or word not in small_words:
            result.append(word.capitalize())
        # Small word in middle - keep lowercase
        else:
            result.append(word)

    return " ".join(result)


# ---------------------------------------------------------------------------
# High-level validators (moved & improved)
# ---------------------------------------------------------------------------


@handle_errors("validating user update", default_return=(False, ["Validation failed"]))
def validate_user_update(
    user_id: str, data_type: str, updates: dict[str, Any]
) -> tuple[bool, list[str]]:
    """Validate partial updates to an existing user's data."""
    logger.debug(
        f"Validating user update for user {user_id}, data_type: {data_type}, fields: {list(updates.keys())}"
    )
    errors: list[str] = []
    if not user_id:
        errors.append("user_id is required")
    if not updates:
        errors.append("updates cannot be empty")

    # ACCOUNT ----------------------------------------------------------------
    if data_type == "account":
        # Account validation is now handled by Pydantic models in core/schemas.py
        # This function is kept for backward compatibility but delegates to Pydantic
        from core.schemas import validate_account_dict

        try:
            # This maintains backward compatibility with the old validation approach
            try:
                from core.user_data_handlers import get_user_data

                current_account = get_user_data(user_id, "account").get("account", {})
            except Exception:
                current_account = {}

            # Merge updates with current account for validation
            merged_account = current_account.copy()
            merged_account.update(updates)

            # Add user_id if not present (required by Pydantic)
            if "user_id" not in merged_account:
                merged_account["user_id"] = user_id

            # Use Pydantic validation for account data
            _, validation_errors = validate_account_dict(merged_account)
            if validation_errors:
                errors.extend(validation_errors)

            # Additional strict validation for critical fields
            if (
                "internal_username" in updates
                and not updates["internal_username"].strip()
            ):
                errors.append("internal_username cannot be empty")

            if "channel" in updates:
                channel = updates["channel"]
                if isinstance(channel, dict) and "type" in channel:
                    valid_channel_types = ["email", "discord", "sms", "webhook"]
                    if channel["type"] not in valid_channel_types:
                        errors.append(
                            f"Invalid channel type: {channel['type']}. Must be one of: {valid_channel_types}"
                        )
        except Exception as e:
            errors.append(f"Account validation error: {e}")

    # PREFERENCES -------------------------------------------------------------
    elif data_type == "preferences":
        # Preferences validation is now handled by Pydantic models in core/schemas.py
        # This function is kept for backward compatibility but delegates to Pydantic
        from core.schemas import validate_preferences_dict

        try:
            # Retry in case of race conditions with file reads in parallel execution
            import time

            current_preferences = {}
            for attempt in range(3):
                try:
                    from core.user_data_handlers import get_user_data

                    current_preferences = get_user_data(user_id, "preferences").get(
                        "preferences", {}
                    )
                    if (
                        current_preferences or attempt == 2
                    ):  # Accept empty on last attempt
                        break
                except Exception:
                    pass
                if attempt < 2:
                    time.sleep(0.05)  # Brief delay before retry

            merged_preferences = (
                current_preferences.copy()
                if isinstance(current_preferences, dict)
                else {}
            )
            merged_preferences.update(updates)

            # Use Pydantic validation for preferences data
            _, validation_errors = validate_preferences_dict(merged_preferences)
            if validation_errors:
                errors.extend(validation_errors)
        except Exception as e:
            logger.warning(f"Preferences validation error for user {user_id}: {e}")
            # Don't fail validation on exceptions - let Pydantic handle it
            pass

    # CONTEXT -----------------------------------------------------------------
    elif data_type == "context":
        dob = updates.get("date_of_birth")
        if dob:
            try:
                from datetime import datetime as _dt

                _dt.strptime(dob, DATE_ONLY_FORMAT)
            except ValueError:
                errors.append("date_of_birth must be in YYYY-MM-DD format")
        if "custom_fields" in updates and not isinstance(
            updates["custom_fields"], dict
        ):
            errors.append("custom_fields must be a dictionary")

    # SCHEDULES ---------------------------------------------------------------
    elif data_type == "schedules":
        # Schedules validation is now handled by Pydantic models in core/schemas.py
        # This function is kept for backward compatibility but delegates to Pydantic
        from core.schemas import validate_schedules_dict

        try:
            try:
                from core.user_data_handlers import get_user_data

                current_schedules = get_user_data(user_id, "schedules").get(
                    "schedules", {}
                )
            except Exception:
                current_schedules = {}

            merged_schedules = current_schedules.copy()
            merged_schedules.update(updates)

            # Use Pydantic validation for schedules data
            _, validation_errors = validate_schedules_dict(merged_schedules)
            if validation_errors:
                errors.extend(validation_errors)
        except Exception as e:
            errors.append(f"Schedules validation error: {e}")

    is_valid = len(errors) == 0
    if is_valid:
        logger.debug(
            f"User update validation passed for user {user_id}, data_type: {data_type}"
        )
    else:
        logger.warning(
            f"User update validation failed for user {user_id}, data_type: {data_type} - errors: {errors}"
        )
    return is_valid, errors


@handle_errors(
    "validating schedule periods", default_return=(False, ["Validation failed"])
)
def validate_schedule_periods(
    periods: dict[str, dict[str, Any]], category: str = "unknown"
) -> tuple[bool, list[str]]:
    """Validate schedule periods and return (is_valid, error_messages).

    Args:
        periods: Dictionary of period_name -> period_data
        category: Category name for error messages (e.g., "tasks", "check-ins")

    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors: list[str] = []

    if not periods:
        return False, [f"At least one time period is required for {category}."]

    # Check if any periods are active (excluding "ALL" period)
    active_periods = [
        name
        for name, data in periods.items()
        if isinstance(data, dict)
        and data.get("active", False)
        and name.upper() != "ALL"
    ]
    if not active_periods:
        return False, [f"At least one time period must be enabled for {category}."]

    # Validate each period
    valid_days = [
        "ALL",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    for period_name, period_data in periods.items():
        if not isinstance(period_data, dict):
            errors.append(f"Period '{period_name}' data must be a dictionary")
            continue

        # Check required fields - name is the dictionary key, so we don't need to check period_data.get('name')
        # The period_name is already validated by being a valid dictionary key

        # Validate times
        start_time = period_data.get("start_time")
        end_time = period_data.get("end_time")

        if not start_time or not end_time:
            errors.append(
                f"Period '{period_name}' must have both start_time and end_time"
            )
            continue

        if not validate_schedule_periods__validate_time_format(start_time):
            errors.append(
                f"Period '{period_name}' has invalid start_time format: {start_time}"
            )

        if not validate_schedule_periods__validate_time_format(end_time):
            errors.append(
                f"Period '{period_name}' has invalid end_time format: {end_time}"
            )

        # Validate time ordering
        if (
            start_time
            and end_time
            and validate_schedule_periods__validate_time_format(start_time)
            and validate_schedule_periods__validate_time_format(end_time)
        ):
            try:
                from datetime import datetime as _dt

                st = _dt.strptime(start_time, TIME_HM_FORMAT)
                et = _dt.strptime(end_time, TIME_HM_FORMAT)
                if st >= et:
                    errors.append(
                        f"Period '{period_name}' start_time must be before end_time"
                    )
            except ValueError:
                # Already caught by format validation
                pass

        # Validate days for active periods
        if period_data.get("active", False):
            days = period_data.get("days", [])
            if not isinstance(days, list):
                errors.append(f"Period '{period_name}' days must be a list")
            elif not days:
                errors.append(
                    f"Active period '{period_name}' must have at least one day selected"
                )
            else:
                invalid_days = [d for d in days if d not in valid_days]
                if invalid_days:
                    errors.append(
                        f"Period '{period_name}' has invalid days: {invalid_days}"
                    )

    return len(errors) == 0, errors


@handle_errors(
    "validating new user data", default_return=(False, ["Validation failed"])
)
def validate_new_user_data(
    user_id: str, data_updates: dict[str, dict[str, Any]]
) -> tuple[bool, list[str]]:
    """Validate complete dataset required for a brand-new user."""
    errors: list[str] = []
    if not user_id:
        errors.append("user_id is required")
    if not data_updates:
        errors.append("data_updates cannot be empty")

    from core.config import get_user_data_dir

    if os.path.exists(get_user_data_dir(user_id)):
        errors.append(f"User {user_id} already exists")

    # ACCOUNT (mandatory)
    account = data_updates.get("account")
    if not account:
        errors.append("account data is required for new user creation")
    else:
        if not account.get("internal_username"):
            errors.append("internal_username is required for new user creation")
        if account.get("email") and not is_valid_email(account["email"]):
            errors.append("Invalid email format")
        if "account_status" in account and account["account_status"] not in [
            "active",
            "inactive",
            "suspended",
        ]:
            errors.append(
                "Invalid account_status. Must be one of: active, inactive, suspended"
            )

    # PREFERENCES (mandatory for channel type)
    prefs = data_updates.get("preferences", {})
    if "categories" in prefs and isinstance(prefs["categories"], list):
        from core.message_management import get_message_categories

        invalid = [c for c in prefs["categories"] if c not in get_message_categories()]
        if invalid:
            errors.append(f"Invalid categories: {invalid}")

    # Channel type validation
    channel = prefs.get("channel")
    if not isinstance(channel, dict) or not channel.get("type"):
        errors.append("channel.type is required for new user creation")
    elif channel["type"] not in ["email", "discord"]:
        errors.append("Invalid channel type. Must be one of: email, discord")

    # CONTEXT (optional)
    context = data_updates.get("context", {})
    if (
        context.get("date_of_birth")
        and not validate_user_update(
            user_id, "context", {"date_of_birth": context["date_of_birth"]}
        )[0]
    ):
        errors.append("Invalid date_of_birth format")

    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# PERSONALIZATION VALIDATOR
# ---------------------------------------------------------------------------


@handle_errors(
    "validating personalization data", default_return=(False, ["Validation failed"])
)
def validate_personalization_data(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate *context/personalization* structure.

    No field is required; we only type-check fields that are present.
    This logic previously lived in the legacy user management utilities.
    """

    errors: list[str] = []

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
                errors.append(
                    f"Field {key} (in custom_fields) must be a list if present"
                )

    # date_of_birth format
    if dob := data.get("date_of_birth"):
        try:
            from datetime import datetime as _dt

            _dt.strptime(dob, DATE_ONLY_FORMAT)
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
