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

# Dialogs (low usage)
from .dialogs.category_management_dialog import CategoryManagementDialog
from .dialogs.channel_management_dialog import ChannelManagementDialog
from .dialogs.process_watcher_dialog import ProcessWatcherDialog
from .dialogs.task_completion_dialog import TaskCompletionDialog
from .dialogs.task_crud_dialog import TaskCrudDialog
from .dialogs.admin_panel import AdminPanelDialog
from .dialogs.message_editor_dialog import MessageEditDialog, MessageEditorDialog, open_message_editor_dialog
from .dialogs.schedule_editor_dialog import ScheduleEditorDialog, open_schedule_editor
from .dialogs.user_analytics_dialog import UserAnalyticsDialog, open_user_analytics_dialog
from .dialogs.user_profile_dialog import open_personalization_dialog
from .dialogs.account_creator_dialog import create_account_dialog

# Widgets (high usage)
from .widgets.dynamic_list_container import DynamicListContainer
from .widgets.period_row_widget import PeriodRowWidget

# Widgets (medium usage)
from .widgets.category_selection_widget import CategorySelectionWidget
from .widgets.channel_selection_widget import ChannelSelectionWidget
from .widgets.task_settings_widget import TaskSettingsWidget
from .widgets.checkin_settings_widget import CheckinSettingsWidget
from .widgets.tag_widget import TagWidget

# Widgets (low usage)
from .widgets.dynamic_list_field import DynamicListField
from .widgets.user_profile_settings_widget import UserProfileSettingsWidget

# Dialogs (medium usage)
from .dialogs.task_edit_dialog import TaskEditDialog

# UI utility functions (low usage)
# Note: generate_ui_files.py contains utility functions for generating UI files
# These are typically used as scripts, but exported for consistency
from .generate_ui_files import generate_ui_file, generate_all_ui_files
from .ui_app_qt import main

__all__ = [
    # Main UI application
    'MHMManagerUI',
    'ServiceManager',
    # Dialogs (commonly used)
    'AccountCreatorDialog',
    'UserProfileDialog',
    'TaskManagementDialog',
    'CheckinManagementDialog',
    # Dialogs (medium usage)
    'TaskEditDialog',
    # Dialogs (low usage)
    'CategoryManagementDialog',
    'ChannelManagementDialog',
    'ProcessWatcherDialog',
    'TaskCompletionDialog',
    'TaskCrudDialog',
    'AdminPanelDialog',
    'MessageEditDialog',
    'MessageEditorDialog',
    'ScheduleEditorDialog',
    'UserAnalyticsDialog',
    # Widgets (high usage)
    'DynamicListContainer',
    'PeriodRowWidget',
    # Widgets (medium usage)
    'CategorySelectionWidget',
    'ChannelSelectionWidget',
    'TaskSettingsWidget',
    'CheckinSettingsWidget',
    'TagWidget',
    # Widgets (low usage)
    'DynamicListField',
    'UserProfileSettingsWidget',
    # Dialog helper functions (low usage)
    'open_message_editor_dialog',
    'open_schedule_editor',
    'open_user_analytics_dialog',
    'open_personalization_dialog',
    'create_account_dialog',
    # UI utility functions (low usage)
    'generate_ui_file',
    'generate_all_ui_files',
    'main',
]
