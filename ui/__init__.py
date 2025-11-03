"""User interface package for the MHM application.

Contains UI components including dialogs, widgets, and generated PyQt modules
for the administrative interface.
"""

# Main public API - package-level exports for easier refactoring
# Note: UI components are typically imported directly from their modules
# (e.g., from ui.dialogs.account_creator_dialog import AccountCreatorDialog)
# but we provide package-level exports for consistency

# Main UI application
from .ui_app_qt import MHMManagerUI, ServiceManager

# Dialogs (commonly used)
from .dialogs.account_creator_dialog import AccountCreatorDialog
from .dialogs.user_profile_dialog import UserProfileDialog
from .dialogs.task_management_dialog import TaskManagementDialog
from .dialogs.checkin_management_dialog import CheckinManagementDialog

# Widgets (high usage)
from .widgets.dynamic_list_container import DynamicListContainer
from .widgets.period_row_widget import PeriodRowWidget

__all__ = [
    # Main UI application
    'MHMManagerUI',
    'ServiceManager',
    # Dialogs
    'AccountCreatorDialog',
    'UserProfileDialog',
    'TaskManagementDialog',
    'CheckinManagementDialog',
    # Widgets (high usage)
    'DynamicListContainer',
    'PeriodRowWidget',
]
