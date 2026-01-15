"""Dialog windows package.

Contains dialog windows used throughout the MHM UI for user account management,
task management, schedule editing, check-in configuration, and system administration.
"""

# Main public API - package-level exports for easier refactoring
# Note: Also exported from parent ui package for convenience
from .account_creator_dialog import AccountCreatorDialog
from .user_profile_dialog import UserProfileDialog
from .task_management_dialog import TaskManagementDialog
from .checkin_management_dialog import CheckinManagementDialog
from .schedule_editor_dialog import ScheduleEditorDialog
from .message_editor_dialog import MessageEditorDialog, MessageEditDialog
from .user_analytics_dialog import UserAnalyticsDialog

__all__ = [
    # Account management
    "AccountCreatorDialog",
    # User profile
    "UserProfileDialog",
    # Task management
    "TaskManagementDialog",
    # Check-in management
    "CheckinManagementDialog",
    # Schedule editing
    "ScheduleEditorDialog",
    # Message editing
    "MessageEditorDialog",
    "MessageEditDialog",
    # Analytics
    "UserAnalyticsDialog",
]
