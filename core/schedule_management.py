# schedule_management.py
"""
Schedule management utilities for MHM.
Contains functions for schedule time periods, period activation, validation, and manipulation.
"""

import time
import calendar
from datetime import datetime
from typing import Dict, Any, Optional
from core.logger import get_component_logger
from core.user_data_handlers import get_user_data

from core.service_utilities import create_reschedule_request
from user.user_context import UserContext
from core.error_handling import handle_errors, ValidationError, DataError

logger = get_component_logger('scheduler')
schedule_logger = get_component_logger('main')

_schedule_periods_cache = {}
_cache_timeout = 30


@handle_errors("getting schedule time periods", default_return={})
def get_schedule_time_periods(user_id, category):
    """Get schedule time periods for a specific user and category (new format)."""
    if user_id is None:
        logger.error("get_schedule_time_periods called with None user_id")
        return {}

    # Check cache first
    current_time = time.time()
    cache_key = f"{user_id}_{category}"
    
    if cache_key in _schedule_periods_cache:
        cached_data, cache_time = _schedule_periods_cache[cache_key]
        if current_time - cache_time < _cache_timeout:
            return cached_data
    
    # Get user schedules
    schedules_result = get_user_data(user_id, 'schedules', normalize_on_read=True)
    # Support both shapes: either a wrapper {'schedules': {...}} or the schedules dict itself
    schedules_data = (
        schedules_result.get('schedules', {})
        if isinstance(schedules_result, dict) and 'schedules' in schedules_result
        else (schedules_result if isinstance(schedules_result, dict) else {})
    )
    user_info = {'schedules': schedules_data}

    if not user_info:
        logger.error(f"User {user_id} not found.")
        return {}

    schedules = user_info.get('schedules', {})
    category_data = schedules.get(category, {})
    
    # Get periods from the wrapper (all data now uses periods wrapper format)
    periods = category_data.get('periods', {}) if isinstance(category_data, dict) else {}

    if periods:
        # Sort periods by start_time (canonical)
        sorted_periods = {}
        for period_name, period_data in periods.items():
            if not isinstance(period_data, dict):
                logger.warning(f"Period {period_name} in category {category} is not a dictionary: {period_data}")
                continue
            # Get start and end times (all data now uses canonical keys)
            start_time = period_data.get('start_time')
            end_time = period_data.get('end_time')
            if not start_time or not end_time:
                logger.warning(f"Missing start_time/end_time for period {period_name} in category {category}")
                continue
            try:
                start_time_obj = datetime.strptime(start_time, "%H:%M")
            except ValueError as e:
                logger.warning(f"Error parsing start time for period {period_name} in category {category}: {e}")
                continue
            # Always use canonical keys in returned dict
            sorted_periods[period_name] = {
                'start_time': start_time,
                'end_time': end_time,
                'active': period_data.get('active', True),
                'days': period_data.get('days', ['ALL'])
            }
            sorted_periods[period_name]['start_time_obj'] = start_time_obj
        # Sort by start_time, but put "ALL" period at the end
        # ERROR_HANDLING_EXCLUDE: Simple nested helper function for sorting
        def sort_key(item):
            period_name, period_data = item
            if period_name.upper() == "ALL":
                # Put ALL period at the end by giving it a very high sort value
                return (999999, period_data['start_time_obj'])
            else:
                return (0, period_data['start_time_obj'])
        
        sorted_periods = dict(sorted(sorted_periods.items(), key=sort_key))
        for period in sorted_periods:
            del sorted_periods[period]['start_time_obj']
        _schedule_periods_cache[cache_key] = (sorted_periods, current_time)
        logger.debug(f"Retrieved and sorted schedule time periods for user {user_id}, category {category}")
        return sorted_periods
    else:
        # Only add "ALL" period if user has no periods at all, and only for non-task/checkin categories
        if category not in ("tasks", "checkin"):
            all_period = {
                "ALL": {
                    "start_time": "00:00",
                    "end_time": "23:59",
                    "active": True,
                    "days": ["ALL"],
                    "description": "Messages sent regardless of time of day"
                }
            }
            _schedule_periods_cache[cache_key] = (all_period, current_time)
            logger.debug(f"No schedule periods found for user {user_id}, category {category}, returning ALL period")
            return all_period
        else:
            _schedule_periods_cache[cache_key] = ({}, current_time)
            logger.debug(f"No schedule periods found for user {user_id}, category {category}, returning empty period")
            return {}

@handle_errors("setting schedule period active", default_return=False)
def set_schedule_period_active(user_id, category, period_name, active=True):
    """
    Set whether a schedule period is active or inactive.
    
    Args:
        user_id: The user ID
        category: The schedule category
        period_name: The name of the period to modify
        active: Whether the period should be active (default: True)
        
    Returns:
        bool: True if the period was found and updated, False otherwise
    """
    # Clear cache to avoid stale reads in randomized/parallel test order
    try:
        clear_schedule_periods_cache(user_id, category)
    except Exception:
        pass
    # Get current periods for this category
    current_periods = get_schedule_time_periods(user_id, category)
    
    if period_name in current_periods:
        # Update the period's active status
        current_periods[period_name]['active'] = active
        
        # Save using the consistent set_schedule_periods function
        set_schedule_periods(user_id, category, current_periods)
        
        status = "enabled" if active else "disabled"
        logger.info(f"Period {period_name} in category {category} for user {user_id} has been {status}.")
        return True
    else:
        logger.error(f"Period {period_name} not found in category {category} for user {user_id}.")
        return False

@handle_errors("checking if schedule period active", default_return=False)
def is_schedule_period_active(user_id, category, period_name):
    """
    Check if a schedule period is currently active.
    
    Args:
        user_id: The user ID
        category: The schedule category
        period_name: The name of the period to check
        
    Returns:
        bool: True if the period is active, False otherwise (defaults to True if field is missing)
    """
    # Clear cache to ensure we read latest state
    try:
        clear_schedule_periods_cache(user_id, category)
    except Exception:
        pass
    # Get user schedules
    schedules_result = get_user_data(user_id, 'schedules', normalize_on_read=True)
    schedules_data = (
        schedules_result.get('schedules', {})
        if isinstance(schedules_result, dict) and 'schedules' in schedules_result
        else (schedules_result if isinstance(schedules_result, dict) else {})
    )
    user_info = {'schedules': schedules_data}
    if not user_info:
        return False
    schedules = user_info.get('schedules', {})
    category_data = schedules.get(category, {})
    periods = category_data.get('periods', {}) if isinstance(category_data, dict) else {}
    period = periods.get(period_name, {})
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
            start_time, end_time = times['start_time'], times['end_time']
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
    # Clear cache to avoid stale reads under randomized/parallel tests
    try:
        clear_schedule_periods_cache(UserContext().get_user_id(), category)
    except Exception:
        pass
    user_id = UserContext().get_user_id()
    internal_username = UserContext().get_internal_username()
    logger.debug(f"Retrieved user_id: {user_id}, internal_username: {internal_username}")
    
    if not user_id:
        logger.error("User ID is not set in UserContext (add_schedule_period).")
        return
    
    # Get current periods for this category
    current_periods = get_schedule_time_periods(user_id, category)
    
    # Validate that period name doesn't already exist
    if period_name in current_periods:
        logger.warning(f"Period '{period_name}' already exists in category '{category}' for user {user_id}")
        raise ValidationError(f"A period named '{period_name}' already exists in this category. Please choose a different name.", details={'period_name': period_name, 'category': category, 'user_id': user_id})
    
    # Add the new period
    current_periods[period_name] = {
        'start_time': start_time,
        'end_time': end_time,
        'active': True,
        'days': ['ALL']
    }
    
    # Save using the consistent set_schedule_periods function
    set_schedule_periods(user_id, category, current_periods)
    logger.info(f"Added period {period_name} in category {category} for user {user_id}.")
    
    # Only reset scheduler if available
    if scheduler_manager:
        scheduler_manager.reset_and_reschedule_daily_messages(category)
    else:
        logger.debug("No scheduler manager available for rescheduling")
        # Create a reschedule request for the service to pick up
        created = create_reschedule_request(user_id, category)
        if created is False:
            logger.debug("Skipped creating reschedule request because service is not running")

@handle_errors("editing schedule period")
def edit_schedule_period(category, period_name, new_start_time, new_end_time, scheduler_manager=None):
    user_id = UserContext().get_user_id()
    if not user_id:
        logger.error("User ID is not set in UserContext (edit_schedule_period).")
        return
    
    # Get current periods for this category
    current_periods = get_schedule_time_periods(user_id, category)
    
    if period_name in current_periods:
        # Update the period
        current_periods[period_name]['start_time'] = new_start_time
        current_periods[period_name]['end_time'] = new_end_time
        
        # Save using the consistent set_schedule_periods function
        success = set_schedule_periods(user_id, category, current_periods)
        if success:
            logger.info(f"Edited period {period_name} in category {category} for user {user_id}.")
        else:
            logger.error(f"Failed to save edited period {period_name} in category {category} for user {user_id}.")
    else:
        logger.warning(f"Period {period_name} not found in category {category} for user {user_id}.")

@handle_errors("deleting schedule period")
def delete_schedule_period(category, period_name, scheduler_manager=None):
    """
    Delete a schedule period from a category.
    
    Args:
        category: The schedule category
        period_name: The name of the period to delete
        scheduler_manager: Optional scheduler manager for rescheduling (default: None)
    """
    user_id = UserContext().get_user_id()
    if not user_id:
        logger.error("User ID is not set in UserContext (delete_schedule_period).")
        return
    
    # Get current periods for this category
    current_periods = get_schedule_time_periods(user_id, category)
    
    if period_name in current_periods:
        # Delete the period
        del current_periods[period_name]
        
        # Save using the consistent set_schedule_periods function
        set_schedule_periods(user_id, category, current_periods)
        logger.info(f"Deleted period {period_name} from category {category} for user {user_id}.")
        
        # Only reset scheduler if available
        if scheduler_manager:
            scheduler_manager.reset_and_reschedule_daily_messages(category)
        else:
            logger.debug("No scheduler manager available for rescheduling")
            # Create a reschedule request for the service to pick up
            created = create_reschedule_request(user_id, category)
            if created is False:
                logger.debug("Skipped creating reschedule request because service is not running")
    else:
        logger.warning(f"Period {period_name} not found in category {category} for user {user_id}.")

@handle_errors("clearing schedule periods cache", default_return=None)
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
def get_period_data__validate_and_format_time(time_str):
    """
    Validate and format a time string to HH:MM format.
    
    Args:
        time_str: Time string to validate and format
        
    Returns:
        str: Formatted time string in HH:MM format
        
    Raises:
        ValueError: If the time format is invalid
    """
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

    raise ValidationError(f"Invalid time format: {time_str}", details={'time_str': time_str})


@handle_errors("converting 24-hour time to 12-hour display format")
def get_period_data__time_24h_to_12h_display(time_24h):
    """
    Convert 24-hour time string (HH:MM) to 12-hour display format.
    
    Args:
        time_24h (str): Time in 24-hour format (e.g., "14:30")
        
    Returns:
        tuple: (hour_12, minute, is_pm) where:
            - hour_12 (int): Hour in 12-hour format (1-12)
            - minute (int): Minute (0-59)
            - is_pm (bool): True if PM, False if AM
    """
    try:
        hour_24, minute = map(int, time_24h.split(':'))
        
        if hour_24 == 0:
            return 12, minute, False  # 12 AM
        elif hour_24 == 12:
            return 12, minute, True   # 12 PM
        elif hour_24 > 12:
            return hour_24 - 12, minute, True  # PM
        else:
            return hour_24, minute, False  # AM
            
    except (ValueError, AttributeError) as e:
        logger.error(f"Error converting 24-hour time '{time_24h}' to 12-hour: {e}")
        raise ValidationError(f"Invalid 24-hour time format: {time_24h}", details={'time_24h': time_24h})


@handle_errors("converting 12-hour display format to 24-hour time")
def get_period_data__time_12h_display_to_24h(hour_12, minute, is_pm):
    """
    Convert 12-hour display format to 24-hour time string.
    
    Args:
        hour_12 (int): Hour in 12-hour format (1-12)
        minute (int): Minute (0-59)
        is_pm (bool): True if PM, False if AM
        
    Returns:
        str: Time in 24-hour format (HH:MM)
    """
    try:
        if hour_12 == 12:
            hour_24 = 0 if not is_pm else 12
        else:
            hour_24 = hour_12 + (12 if is_pm else 0)
            
        return f"{hour_24:02d}:{minute:02d}"
        
    except (ValueError, TypeError) as e:
        logger.error(f"Error converting 12-hour time to 24-hour: hour={hour_12}, minute={minute}, is_pm={is_pm}, error={e}")
        raise ValidationError(f"Invalid 12-hour time parameters: hour={hour_12}, minute={minute}, is_pm={is_pm}", details={'hour_12': hour_12, 'minute': minute, 'is_pm': is_pm})

@handle_errors("getting current day names", default_return=[])
def get_current_day_names():
    """Returns the name of the current day plus 'ALL' for universal day messages."""
    day_index = datetime.today().weekday()
    current_day = list(calendar.day_name)[day_index]
    return [current_day, 'ALL']



@handle_errors("setting schedule periods", default_return=False)
def set_schedule_periods(user_id, category, periods_dict):
    """Replace all schedule periods for a category with the given dict (period_name: {active, days, start_time, end_time})."""
    # Get user schedules
    schedules_result = get_user_data(user_id, 'schedules', normalize_on_read=True)
    schedules_data = (
        schedules_result.get('schedules', {})
        if isinstance(schedules_result, dict) and 'schedules' in schedules_result
        else (schedules_result if isinstance(schedules_result, dict) else {})
    )
    
    logger.info(f"set_schedule_periods: Setting periods for user {user_id}, category {category}")
    logger.info(f"set_schedule_periods: Current schedules data: {schedules_data}")
    logger.info(f"set_schedule_periods: New periods dict: {periods_dict}")

    # Ensure category exists
    if category not in schedules_data:
        schedules_data[category] = {}
    
    # All data now uses periods wrapper format - no legacy migration needed
    category_data = schedules_data[category]
    
    # Ensure periods sub-dict exists
    if 'periods' not in schedules_data[category]:
        schedules_data[category]['periods'] = {}
    
    # Defensive: ensure all keys are strings and only allowed fields are present in each period
    cleaned_periods = {}
    for period_name, period_data in periods_dict.items():
        if not isinstance(period_name, str):
            logger.warning(f"set_schedule_periods: period_name is not a string: {period_name} (type: {type(period_name)}) - converting to string.")
            period_name = str(period_name)
        cleaned_periods[period_name] = {
            'active': period_data.get('active', True),
            'days': period_data.get('days', ['ALL']),
            'start_time': period_data.get('start_time'),
            'end_time': period_data.get('end_time')
        }
    
    # Replace the periods for this category (all categories use periods wrapper)
    schedules_data[category]['periods'] = cleaned_periods
    
    logger.info(f"set_schedule_periods: Final schedules data: {schedules_data}")
    
    # Save the updated schedules
    from core.user_data_handlers import update_user_schedules
    update_user_schedules(user_id, schedules_data)
    clear_schedule_periods_cache(user_id, category)
    return True

@handle_errors("getting schedule days", default_return=["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
def get_schedule_days(user_id, category):
    """
    Get the schedule days for a user and category.
    
    Args:
        user_id: The user ID
        category: The schedule category
        
    Returns:
        list: List of days for the schedule, defaults to all days of the week
    """
    # Get user schedules
    schedules_result = get_user_data(user_id, 'schedules', normalize_on_read=True)
    user_info = {'schedules': schedules_result.get('schedules', {})}
    return user_info.get('schedules', {}).get(category, {}).get('days', ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])

@handle_errors("setting schedule days", default_return=False)
def set_schedule_days(user_id, category, days):
    """
    Set the schedule days for a user and category.
    
    Args:
        user_id: The user ID
        category: The schedule category
        days: List of days to set for the schedule
    """
    # Get user schedules
    schedules_result = get_user_data(user_id, 'schedules', normalize_on_read=True)
    user_info = {'schedules': schedules_result.get('schedules', {})}
    if 'schedules' not in user_info:
        user_info['schedules'] = {}
    if category not in user_info['schedules']:
        user_info['schedules'][category] = {}
    user_info['schedules'][category]['days'] = days
    # Update schedules using new structure
    from core.user_data_handlers import update_user_schedules
    update_user_schedules(user_id, user_info.get('schedules', {}))

@handle_errors("getting user info for schedule management", default_return=None)
def get_user_info_for_schedule_management(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user info for schedule management operations."""
    try:
        from core.user_data_handlers import get_user_data
        schedules_result = get_user_data(user_id, 'schedules')
        schedules_data = schedules_result.get('schedules', {})
        return {'schedules': schedules_data}
    except Exception as e:
        logger.error(f"Error loading user schedules for schedule management: {e}")
        return None 

 