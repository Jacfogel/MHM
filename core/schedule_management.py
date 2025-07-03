# schedule_management.py
"""
Schedule management utilities for MHM.
Contains functions for schedule time periods, period activation, validation, and manipulation.
"""

import time
import calendar
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from core.logger import get_logger
from core.user_management import load_user_info_data, save_user_info_data
from core.file_operations import determine_file_path, load_json_data, save_json_data, get_user_file_path
from core.service_utilities import create_reschedule_request
from user.user_context import UserContext
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)

logger = get_logger(__name__)

_schedule_periods_cache = {}
_cache_timeout = 30


@handle_errors("getting schedule time periods", default_return={})
def get_schedule_time_periods(user_id, category):
    """Get schedule time periods for a specific user and category."""
    if user_id is None:
        logger.error("get_schedule_time_periods called with None user_id")
        return {}

    # Check cache first
    current_time = time.time()
    cache_key = f"{user_id}_{category}"
    
    if cache_key in _schedule_periods_cache:
        cached_data, cache_time = _schedule_periods_cache[cache_key]
        if current_time - cache_time < _cache_timeout:
            # Use cached data without logging every access
            return cached_data
    
    user_info = load_user_info_data(user_id)
    if not user_info:
        logger.error(f"User {user_id} not found.")
        return {}

    schedules = user_info.get('schedules', {})
    periods = schedules.get(category, {})

    if periods:
        for period in periods:
            try:
                start_time_str = periods[period]['start']
                start_time_obj = datetime.strptime(start_time_str, "%H:%M")
                periods[period]['start_time_obj'] = start_time_obj
            except (KeyError, ValueError) as e:
                logger.warning(f"Error parsing start time for period {period} in category {category}: {e}")
                continue

        sorted_periods = dict(sorted(periods.items(), key=lambda item: item[1]['start_time_obj']))

        for period in sorted_periods:
            del sorted_periods[period]['start_time_obj']

        # Add the persistent "ALL" time period
        sorted_periods["ALL"] = {
            "start": "00:00",
            "end": "23:59",
            "active": True,
            "description": "Messages sent regardless of time of day"
        }

        # Cache the results
        _schedule_periods_cache[cache_key] = (sorted_periods, current_time)
        
        # Only log once per cache refresh instead of every access
        logger.debug(f"Retrieved and sorted schedule time periods for user {user_id}, category {category}")
        return sorted_periods
    else:
        # Even if no periods exist, return the "ALL" period
        all_period = {
            "ALL": {
                "start": "00:00",
                "end": "23:59",
                "active": True,
                "description": "Messages sent regardless of time of day"
            }
        }
        _schedule_periods_cache[cache_key] = (all_period, current_time)
        logger.debug(f"No schedule periods found for user {user_id}, category {category}, returning ALL period")
        return all_period

@handle_errors("setting schedule period active", default_return=False)
def set_schedule_period_active(user_id, category, period_name, active=True):
    user_info = load_user_info_data(user_id)
    if not user_info:
        logger.error(f"User {user_id} not found.")
        return False
    
    schedules = user_info.get('schedules', {})
    category_schedules = schedules.get(category, {})
    period = category_schedules.get(period_name)

    if period:
        period['active'] = active
        save_user_info_data(user_info, user_id)
        
        # Clear the cache for this user/category
        clear_schedule_periods_cache(user_id, category)
        
        status = "enabled" if active else "disabled"
        logger.info(f"Period {period_name} in category {category} for user {user_id} has been {status}.")
    else:
        logger.error(f"Period {period_name} not found in category {category} for user {user_id}.")
        return False
    return True

@handle_errors("checking if schedule period active", default_return=False)
def is_schedule_period_active(user_id, category, period_name):
    user_info = load_user_info_data(user_id)
    if not user_info:
        return False

    schedules = user_info.get('schedules', {})
    category_schedules = schedules.get(category, {})
    period = category_schedules.get(period_name, {})
    
    return period.get('active', True)  # Defaults to active if the field is missing

@handle_errors("getting current time periods with validation")
def get_current_time_periods_with_validation(user_id, category):
    """
    Returns the current active time periods for a user and category.
    If no active period is found, defaults to the first available period.
    """
    if user_id is None:
        logger.error("get_current_time_periods_with_validation called with None user_id")
        return [], []

    current_datetime = datetime.now().time()  # Get current time
    current_time_str = current_datetime.strftime('%H:%M')
    time_periods = get_schedule_time_periods(user_id, category)

    valid_periods = list(time_periods.keys())
    matching_periods = []

    # Always include "ALL" period if it exists and is active
    if "ALL" in time_periods and time_periods["ALL"].get('active', True):
        matching_periods.append("ALL")

    # Check if current time falls within any defined periods (excluding "ALL")
    for period, times in time_periods.items():
        if period == "ALL":
            continue  # Skip "ALL" as it's already handled above
        
        if times.get('active', True):  # Check if period is active
            start_time, end_time = times['start'], times['end']
            if start_time <= current_time_str <= end_time:
                matching_periods.append(period)

    if not matching_periods:
        # Defaulting to the first available period if no match is found
        # This prevents multiple messages from being sent
        if valid_periods:
            logger.info(f"Current time is not within any defined period, defaulting to first period: {valid_periods[0]}. Available periods: {valid_periods}")
            return [valid_periods[0]], valid_periods
        else:
            logger.warning("No valid periods found for user and category")
            return [], []

    # Only log current time periods when everything is working normally
    logger.debug(f"Current time periods: {matching_periods}")
    return matching_periods, valid_periods

@handle_errors("adding schedule period")
def add_schedule_period(category, period_name, start_time, end_time, scheduler_manager=None):
    user_id = UserContext().get_user_id()
    internal_username = UserContext().get_internal_username()
    logger.debug(f"Retrieved user_id: {user_id}, internal_username: {internal_username}")
    
    if not user_id:
        logger.error("User ID is not set in UserContext (add_schedule_period).")
        return
    
    user_info = load_user_info_data(user_id) or {}

    if user_info.get("user_id") != user_id:
        logger.error(f"Mismatch in user_id for user info data: expected {user_id}, found {user_info.get('user_id')}")
        return

    user_schedules = user_info.setdefault('schedules', {})
    category_schedules = user_schedules.setdefault(category, {})

    formatted_start_time = validate_and_format_time(start_time)
    formatted_end_time = validate_and_format_time(end_time)

    category_schedules[period_name.lower()] = {'start': formatted_start_time, 'end': formatted_end_time}

    save_user_info_data(user_info, user_id)
    clear_schedule_periods_cache(user_id, category)
    logger.info(f"Added schedule period for user {internal_username}, category {category}: {category_schedules[period_name.lower()]}")
    
    # Only reset scheduler if available
    if scheduler_manager:
        scheduler_manager.reset_and_reschedule_daily_messages(category)
    else:
        logger.debug("No scheduler manager available for rescheduling")
        # Create a reschedule request for the service to pick up
        create_reschedule_request(user_id, category)

@handle_errors("editing schedule period")
def edit_schedule_period(category, period_name, new_start_time, new_end_time, scheduler_manager=None):
    user_id = UserContext().get_user_id()
    internal_username = UserContext().get_internal_username()
    
    if not user_id:
        logger.error("User ID is not set in UserContext (edit_schedule_period).")
        return
    
    logger.debug(f"Attempting to edit period {period_name} for user {user_id} in category {category}")
    user_info = load_user_info_data(user_id) or {}

    if user_info.get("user_id") != user_id:
        logger.error(f"User ID {user_id} not found in user info data. Loaded user ID: {user_info.get('user_id')}")
        return

    schedules = user_info.get('schedules', {})
    category_schedules = schedules.get(category, {})

    if period_name not in category_schedules:
        logger.error(f"Period name {period_name} not found in category {category}.")
        return

    formatted_new_start_time = validate_and_format_time(new_start_time)
    formatted_new_end_time = validate_and_format_time(new_end_time)

    category_schedules[period_name] = {'start': formatted_new_start_time, 'end': formatted_new_end_time}

    save_user_info_data(user_info, user_id)
    clear_schedule_periods_cache(user_id, category)
    logger.info(f"Edited schedule period for user {internal_username}, category {category}, period {period_name}: {category_schedules[period_name]}")
    
    # Only reset scheduler if available
    if scheduler_manager:
        scheduler_manager.reset_and_reschedule_daily_messages(category)
    else:
        logger.debug("No scheduler manager available for rescheduling")
        # Create a reschedule request for the service to pick up
        create_reschedule_request(user_id, category)

@handle_errors("deleting schedule period")
def delete_schedule_period(category, period_name, scheduler_manager=None):
    user_id = UserContext().get_user_id()
    internal_username = UserContext().get_internal_username()
    
    if not user_id:
        logger.error("User ID is not set in UserContext (delete_schedule_period).")
        return
    
    logger.debug(f"Attempting to delete period {period_name} for user {user_id} in category {category}")
    user_info = load_user_info_data(user_id) or {}

    if user_info.get("user_id") != user_id:
        logger.error(f"User ID {user_id} not found in user info data. Loaded user ID: {user_info.get('user_id')}")
        return

    schedules = user_info.get('schedules', {})
    category_schedules = schedules.get(category, {})

    if period_name not in category_schedules:
        logger.error(f"Period name {period_name} not found in category {category}.")
        return

    del category_schedules[period_name]

    save_user_info_data(user_info, user_id)
    clear_schedule_periods_cache(user_id, category)
    logger.info(f"Deleted schedule period for user {internal_username}, category {category}, period {period_name}")
    
    # Only reset scheduler if available
    if scheduler_manager:
        scheduler_manager.reset_and_reschedule_daily_messages(category)
    else:
        logger.debug("No scheduler manager available for rescheduling")
        # Create a reschedule request for the service to pick up
        create_reschedule_request(user_id, category)

def clear_schedule_periods_cache(user_id=None, category=None):
    """Clear the schedule periods cache for a specific user/category or all."""
    global _schedule_periods_cache
    
    if user_id is None and category is None:
        # Clear all cache
        _schedule_periods_cache.clear()
        logger.debug("Cleared all schedule periods cache")
    elif user_id is not None and category is not None:
        # Clear specific user/category cache
        cache_key = f"{user_id}_{category}"
        if cache_key in _schedule_periods_cache:
            del _schedule_periods_cache[cache_key]
            logger.debug(f"Cleared schedule periods cache for user {user_id}, category {category}")
    elif user_id is not None:
        # Clear all cache entries for a specific user
        keys_to_remove = [key for key in _schedule_periods_cache.keys() if key.startswith(f"{user_id}_")]
        for key in keys_to_remove:
            del _schedule_periods_cache[key]
        logger.debug(f"Cleared all schedule periods cache for user {user_id}")

@handle_errors("validating and formatting time")
def validate_and_format_time(time_str):
    import re
    hh_mm_pattern = r"^(2[0-3]|[01]?[0-9]):([0-5][0-9])$"
    h_hh_pattern = r"^(2[0-3]|[01]?[0-9])$"
    am_pm_pattern = r"^(1[0-2]|0?[1-9]):?([0-5][0-9])?\s*([AaPp][Mm])$"

    if re.match(hh_mm_pattern, time_str):
        return time_str

    if re.match(h_hh_pattern, time_str):
        return time_str + ":00"

    match = re.match(am_pm_pattern, time_str)
    if match:
        hour = int(match.group(1))
        minute = match.group(2) if match.group(2) else "00"
        period = match.group(3).lower()

        if period == "pm" and hour != 12:
            hour += 12
        if period == "am" and hour == 12:
            hour = 0

        return f"{hour:02}:{minute}"

    raise ValueError(f"Invalid time format: {time_str}")

@handle_errors("getting current day names", default_return=[])
def get_current_day_names():
    """Returns the name of the current day plus 'ALL' for universal day messages."""
    day_index = datetime.today().weekday()
    current_day = list(calendar.day_name)[day_index]
    return [current_day, 'ALL']

def get_reminder_periods_and_days(user_id, category):
    """Load reminder periods and days for a category (e.g., 'tasks') from schedules.json."""
    schedules_file = get_user_file_path(user_id, 'schedules')
    schedules_data = load_json_data(schedules_file) or {}
    cat_data = schedules_data.get(category, {})
    periods = cat_data.get('reminder_periods', [])
    days = cat_data.get('reminder_days', [])
    return periods, days

def set_reminder_periods_and_days(user_id, category, periods, days):
    """Save reminder periods and days for a category to schedules.json."""
    schedules_file = get_user_file_path(user_id, 'schedules')
    schedules_data = load_json_data(schedules_file) or {}
    if category not in schedules_data:
        schedules_data[category] = {}
    schedules_data[category]['reminder_periods'] = periods
    schedules_data[category]['reminder_days'] = days
    save_json_data(schedules_data, schedules_file)

def set_schedule_periods(user_id, category, periods_dict):
    """Replace all schedule periods for a category with the given dict (period_name: {start, end, active})."""
    user_info = load_user_info_data(user_id) or {}
    if 'schedules' not in user_info:
        user_info['schedules'] = {}
    user_info['schedules'][category] = user_info['schedules'].get(category, {})
    # Remove all existing periods except 'days' and 'description'
    keep_keys = {'days', 'description'}
    user_info['schedules'][category] = {k: v for k, v in user_info['schedules'][category].items() if k in keep_keys}
    # Add new periods
    for period_name, period_data in periods_dict.items():
        user_info['schedules'][category][period_name] = period_data
    save_user_info_data(user_info, user_id)
    clear_schedule_periods_cache(user_id, category)

def get_schedule_days(user_id, category):
    user_info = load_user_info_data(user_id) or {}
    return user_info.get('schedules', {}).get(category, {}).get('days', ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])

def set_schedule_days(user_id, category, days):
    user_info = load_user_info_data(user_id) or {}
    if 'schedules' not in user_info:
        user_info['schedules'] = {}
    if category not in user_info['schedules']:
        user_info['schedules'][category] = {}
    user_info['schedules'][category]['days'] = days
    save_user_info_data(user_info, user_id) 