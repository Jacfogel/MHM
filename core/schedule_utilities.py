# schedule_utilities.py
"""
Shared utilities for schedule-related operations.

This module provides common schedule functions that are used across multiple modules
to eliminate code duplication and provide a single source of truth.
"""

from datetime import datetime
from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.time_utilities import (
    now_datetime_full,
    TIME_ONLY_MINUTE,
    DATE_DISPLAY_WEEKDAY,
    format_timestamp,
    parse_time_only_minute,
)


logger = get_component_logger("scheduler")


@handle_errors("getting active schedules", default_return=[])
def get_active_schedules(schedules: dict) -> list[str]:
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
        if isinstance(period_data, dict) and period_data.get("active", True):
            active_periods.append(period_name)
        elif not isinstance(period_data, dict):
            logger.warning(
                f"Invalid schedule data for period '{period_name}': expected dict, got {type(period_data).__name__}"
            )

    logger.debug(
        f"Processed {total_periods} schedule periods, found {len(active_periods)} active: {active_periods}"
    )
    return active_periods


@handle_errors("checking if schedule is active", default_return=False)
def is_schedule_active(
    schedule_data: dict, current_time: datetime | None = None
) -> bool:
    """
    Check if a schedule period is currently active based on time and day.

    Args:
        schedule_data: Dictionary containing schedule period data
        current_time: Current time to check against (defaults to now)

    Returns:
        bool: True if the schedule is active, False otherwise
    """

    # Be explicit: only default when caller provided nothing.
    if current_time is None:
        current_time = now_datetime_full()

    if not schedule_data or not isinstance(schedule_data, dict):
        logger.warning(f"Invalid schedule data provided: {schedule_data}")
        return False

    # Check if schedule is marked as inactive
    if not schedule_data.get("active", True):
        logger.debug("Schedule is marked as inactive")
        return False

    # Check days
    days = schedule_data.get("days", ["ALL"])
    if "ALL" not in days:
        # Display-only weekday name for day matching (never persisted).
        current_day = format_timestamp(current_time, DATE_DISPLAY_WEEKDAY)
        if current_day not in days:
            logger.debug(f"Current day '{current_day}' not in schedule days: {days}")
            return False

    # Check time range
    start_time_str = schedule_data.get("start_time", "00:00")
    end_time_str = schedule_data.get("end_time", "23:59")

    # Canonical time parsing via core.time_utilities
    start_dt = parse_time_only_minute(start_time_str)
    end_dt = parse_time_only_minute(end_time_str)
    if start_dt is None or end_dt is None:
        logger.warning(
            f"Invalid time format in schedule data: start_time='{start_time_str}', end_time='{end_time_str}'"
        )
        return False

    start_time = start_dt.time()
    end_time = end_dt.time()
    current_time_only = current_time.time()

    is_active = start_time <= current_time_only <= end_time
    logger.debug(
        f"Time check: {start_time} <= {current_time_only} <= {end_time} = {is_active}"
    )
    return is_active


@handle_errors("getting current active schedules", default_return=[])
def get_current_active_schedules(
    schedules: dict, current_time: datetime | None = None
) -> list[str]:
    """
    Get list of schedule periods that are currently active based on time and day.
    """
    # local import to keep deps minimal

    if not schedules:
        logger.debug("No schedules provided - returning empty list")
        return []

    # Be explicit: only default when caller provided nothing.
    if current_time is None:
        current_time = now_datetime_full()

    active_periods = []
    total_periods = len(schedules)

    for period_name, period_data in schedules.items():
        if is_schedule_active(period_data, current_time):
            active_periods.append(period_name)

    # No canonical seconds format exists; log minute precision consistently.
    logger.debug(
        f"Checked {total_periods} schedules at {format_timestamp(current_time, TIME_ONLY_MINUTE)}, "
        f"found {len(active_periods)} currently active: {active_periods}"
    )
    return active_periods
