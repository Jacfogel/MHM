# schedule_utilities.py
"""
Shared utilities for schedule-related operations.

This module provides common schedule functions that are used across multiple modules
to eliminate code duplication and provide a single source of truth.
"""

from typing import Dict, List
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
        return []
    
    active_periods = []
    for period_name, period_data in schedules.items():
        if isinstance(period_data, dict) and period_data.get('active', True):
            active_periods.append(period_name)
    
    return active_periods
