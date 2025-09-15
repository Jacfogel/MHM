# schedule_utilities.py
"""
Shared utilities for schedule-related operations.

This module provides common schedule functions that are used across multiple modules
to eliminate code duplication and provide a single source of truth.
"""

from typing import Dict, List, Optional
from datetime import datetime, time
from core.logger import get_component_logger

logger = get_component_logger('schedule_utilities')


def get_active_schedules(schedules: Dict) -> List[str]:
    """
    Get list of currently active schedule periods.
    
    Args:
        schedules: Dictionary containing schedule periods
        
    Returns:
        list: List of active schedule period names
    """
    if not schedules:
        logger.debug("No schedules provided - returning empty list")
        return []
    
    active_periods = []
    total_periods = len(schedules)
    
    for period_name, period_data in schedules.items():
        if isinstance(period_data, dict) and period_data.get('active', True):
            active_periods.append(period_name)
        elif not isinstance(period_data, dict):
            logger.warning(f"Invalid schedule data for period '{period_name}': expected dict, got {type(period_data).__name__}")
    
    logger.debug(f"Processed {total_periods} schedule periods, found {len(active_periods)} active: {active_periods}")
    return active_periods


def is_schedule_active(schedule_data: Dict, current_time: Optional[datetime] = None) -> bool:
    """
    Check if a schedule period is currently active based on time and day.
    
    Args:
        schedule_data: Dictionary containing schedule period data
        current_time: Current time to check against (defaults to now)
        
    Returns:
        bool: True if the schedule is active, False otherwise
    """
    if not current_time:
        current_time = datetime.now()
    
    if not schedule_data or not isinstance(schedule_data, dict):
        logger.warning(f"Invalid schedule data provided: {schedule_data}")
        return False
    
    # Check if schedule is marked as inactive
    if not schedule_data.get('active', True):
        logger.debug("Schedule is marked as inactive")
        return False
    
    # Check days
    days = schedule_data.get('days', ['ALL'])
    if 'ALL' not in days:
        current_day = current_time.strftime('%A')
        if current_day not in days:
            logger.debug(f"Current day '{current_day}' not in schedule days: {days}")
            return False
    
    # Check time range
    start_time_str = schedule_data.get('start_time', '00:00')
    end_time_str = schedule_data.get('end_time', '23:59')
    
    try:
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        current_time_only = current_time.time()
        
        is_active = start_time <= current_time_only <= end_time
        logger.debug(f"Time check: {start_time} <= {current_time_only} <= {end_time} = {is_active}")
        return is_active
        
    except ValueError as e:
        logger.warning(f"Invalid time format in schedule data: start_time='{start_time_str}', end_time='{end_time_str}' - {e}")
        return False


def get_current_active_schedules(schedules: Dict, current_time: Optional[datetime] = None) -> List[str]:
    """
    Get list of schedule periods that are currently active based on time and day.
    
    Args:
        schedules: Dictionary containing all schedule periods
        current_time: Current time to check against (defaults to now)
        
    Returns:
        list: List of currently active schedule period names
    """
    if not schedules:
        logger.debug("No schedules provided - returning empty list")
        return []
    
    if not current_time:
        current_time = datetime.now()
    
    active_periods = []
    total_periods = len(schedules)
    
    for period_name, period_data in schedules.items():
        if is_schedule_active(period_data, current_time):
            active_periods.append(period_name)
    
    logger.debug(f"Checked {total_periods} schedules at {current_time.strftime('%H:%M:%S')}, found {len(active_periods)} currently active: {active_periods}")
    return active_periods
