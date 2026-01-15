"""Reusable widget components package.

Contains reusable widget components for the MHM UI, including task settings,
check-in settings, user profile settings, channel selection, and tag management.
"""

# Main public API - package-level exports for easier refactoring
from .task_settings_widget import TaskSettingsWidget
from .checkin_settings_widget import CheckinSettingsWidget
from .user_profile_settings_widget import UserProfileSettingsWidget
from .channel_selection_widget import ChannelSelectionWidget
from .category_selection_widget import CategorySelectionWidget
from .tag_widget import TagWidget
from .period_row_widget import PeriodRowWidget

__all__ = [
    # Task settings
    "TaskSettingsWidget",
    # Check-in settings
    "CheckinSettingsWidget",
    # User profile settings
    "UserProfileSettingsWidget",
    # Channel selection
    "ChannelSelectionWidget",
    # Category selection
    "CategorySelectionWidget",
    # Tag management
    "TagWidget",
    # Period row
    "PeriodRowWidget",
]
