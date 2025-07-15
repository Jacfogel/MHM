# account_creator_dialog.py - Account creator dialog implementation

import sys
import os
import uuid
import logging
from typing import Dict, Any, Optional

# Add parent directory to path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PySide6 imports
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QRadioButton, QCheckBox, QComboBox, QGroupBox, QGridLayout, QWidget,
    QMessageBox, QButtonGroup, QDialogButtonBox, QScrollArea, QTimeEdit,
    QSpinBox, QTextEdit, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTime
from PySide6.QtGui import QFont

# Set up logging
from core.logger import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)

# Import core functionality
from user.user_context import UserContext
from core.message_management import get_message_categories
from core.validation import title_case
from core.user_management import get_user_id_by_internal_username, create_new_user
from core.file_operations import create_user_files
from core.error_handling import handle_errors

# Import widgets
from ui.widgets.category_selection_widget import CategorySelectionWidget
from ui.widgets.channel_selection_widget import ChannelSelectionWidget
from ui.widgets.task_settings_widget import TaskSettingsWidget
from ui.widgets.checkin_settings_widget import CheckinSettingsWidget
from ui.generated.account_creator_dialog_pyqt import Ui_Dialog_create_account

# Import personalization dialog
from ui.dialogs.user_profile_dialog import open_personalization_dialog


class AccountCreatorDialog(QDialog):
    """Account creation dialog using existing UI files."""
    user_changed = Signal()
    
    def __init__(self, parent=None, communication_manager=None):
        super().__init__(parent)
        self.parent = parent
        self.communication_manager = communication_manager
        
        # Account data
        self.username = ""
        self.preferred_name = ""
        self.selected_categories = set()
        self.selected_service = "email"
        self.contact_info = {}
        self.task_settings = {}
        self.checkin_settings = {}
        self.personalization_data = {}
        
        # Setup window
        self.setWindowTitle("Create New Account")
        self.resize(900, 700)
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        # Load UI from file
        self.ui = Ui_Dialog_create_account()
        self.ui.setupUi(self)
        # Now self.ui.<widget_name> is available for all widgets
        
        # Load the widget UI files into the placeholder widgets
        self.load_category_widget()
        self.load_message_service_widget()
        self.load_task_management_widget()
        self.load_checkin_settings_widget()
        self.populate_timezones()
        
        # Setup group boxes (no longer collapsible in tab structure)
        self.setup_feature_group_boxes()
        
        # Setup profile button
        self.setup_profile_button()
        
        # Setup signal connections
        self.setup_connections()
        
        # Initialize tab visibility based on default feature settings
        self.update_tab_visibility()
    
    def load_category_widget(self):
        """Load the category selection widget."""
        # Add the category selection widget to the placeholder
        self.category_widget = CategorySelectionWidget(self)
        layout = self.ui.widget_placeholder_select_categories.layout()
        
        # Remove any existing widgets
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        
        # Add the category widget
        layout.addWidget(self.category_widget)
    
    def load_message_service_widget(self):
        """Load the message service selection widget."""
        # Add the channel selection widget to the placeholder
        self.channel_widget = ChannelSelectionWidget(self)
        layout = self.ui.widget_placeholder_channel_selection.layout()
        
        # Remove any existing widgets
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        
        # Add the channel widget
        layout.addWidget(self.channel_widget)
        
        # Don't set default selection - let user choose
    
    def load_task_management_widget(self):
        """Load the task management widget."""
        # Add the task settings widget to the placeholder
        self.task_widget = TaskSettingsWidget(self)
        layout = self.ui.widget_placeholder_task_settings.layout()
        
        # Remove any existing widgets
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        
        # Add the task widget with expansion
        layout.addWidget(self.task_widget)
        
        # Make the widget and placeholder expand to fill available space
        self.task_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.ui.widget_placeholder_task_settings.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    def load_checkin_settings_widget(self):
        """Load the check-in settings widget."""
        # Add the check-in settings widget to the placeholder
        self.checkin_widget = CheckinSettingsWidget(self)
        layout = self.ui.widget_placeholder_checkin_settings.layout()
        
        # Remove any existing widgets
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        
        # Add the check-in widget with expansion
        layout.addWidget(self.checkin_widget)
        
        # Make the widget and placeholder expand to fill available space
        self.checkin_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.ui.widget_placeholder_checkin_settings.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    def setup_feature_group_boxes(self):
        """Setup group boxes for task management and check-ins (no longer collapsible in tab structure)."""
        # Task management group (now in Tasks tab) - always visible
        task_group = self.ui.groupBox_task_settings
        if task_group:
            # Make the group box expand to fill available space
            task_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Check-in group (now in Check-ins tab) - always visible
        checkin_group = self.ui.groupBox_checkin_settings
        if checkin_group:
            # Make the group box expand to fill available space
            checkin_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    def setup_profile_button(self):
        """Setup the profile button."""
        profile_button = self.ui.pushButton_profile
        if profile_button:
            profile_button.setToolTip("Click to setup detailed personalization settings")
            # Style the button to make it stand out
            profile_button.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
                QPushButton:pressed {
                    background-color: #0D47A1;
                }
            """)
    
    def center_dialog(self):
        """Center the dialog on the parent window."""
        if self.parent:
            parent_geometry = self.parent.geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)
    
    def setup_connections(self):
        """Setup signal connections."""
        # Connect basic info fields
        username_edit = self.ui.lineEdit_username
        if username_edit:
            username_edit.textChanged.connect(self.on_username_changed)
        
        preferred_name_edit = self.ui.lineEdit_prefered_name
        if preferred_name_edit:
            preferred_name_edit.textChanged.connect(self.on_preferred_name_changed)
        
        # Note: Widgets don't have signals, so we'll collect data when needed
        # Category and channel widgets will be queried during validation
        
        # Connect dialog buttons
        button_box = self.ui.buttonBox_save_cancel
        if button_box:
            button_box.accepted.connect(self.validate_and_accept)
            button_box.rejected.connect(self.reject)
        
        # Connect profile button
        profile_button = self.ui.pushButton_profile
        if profile_button:
            profile_button.clicked.connect(self.open_personalization_dialog)
        
        # Connect feature enablement checkboxes
        if hasattr(self.ui, 'checkBox_enable_messages'):
            self.ui.checkBox_enable_messages.toggled.connect(self.on_feature_toggled)
        if hasattr(self.ui, 'checkBox_enable_task_management'):
            self.ui.checkBox_enable_task_management.toggled.connect(self.on_feature_toggled)
        if hasattr(self.ui, 'checkBox_enable_checkins'):
            self.ui.checkBox_enable_checkins.toggled.connect(self.on_feature_toggled)
        
        # Override key events for large dialog
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
    def keyPressEvent(self, event):
        """Handle key press events for the dialog."""
        if event.key() == Qt.Key.Key_Escape:
            # Show confirmation dialog before canceling
            reply = QMessageBox.question(
                self, 
                "Cancel Account Creation", 
                "Are you sure you want to cancel? All unsaved changes will be lost.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.reject()
            event.accept()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Ignore Enter key to prevent accidental saving
            event.ignore()
        else:
            super().keyPressEvent(event)
    
    def on_username_changed(self):
        """Handle username change."""
        username_edit = self.ui.lineEdit_username
        if username_edit:
            self.username = username_edit.text().strip().lower()
    
    def on_preferred_name_changed(self):
        """Handle preferred name change."""
        preferred_name_edit = self.ui.lineEdit_prefered_name
        if preferred_name_edit:
            self.preferred_name = preferred_name_edit.text().strip()
    
    def on_category_changed(self, categories):
        """Handle category selection change (no longer used - widgets don't have signals)."""
        # This method is kept for compatibility but no longer needed
        pass
    
    def on_service_changed(self, service, value):
        """Handle service selection change (no longer used - widgets don't have signals)."""
        # This method is kept for compatibility but no longer needed
        pass
    
    def on_contact_info_changed(self, service, value):
        """Handle contact information change (no longer used - widgets don't have signals)."""
        # This method is kept for compatibility but no longer needed
        pass
    
    def on_task_group_toggled(self, checked):
        """Handle task management group toggle (no longer used in tab structure)."""
        # This method is kept for compatibility but no longer needed
        # Task widgets are always visible in the tab structure
        pass
    
    def on_checkin_group_toggled(self, checked):
        """Handle check-in group toggle (no longer used in tab structure)."""
        # This method is kept for compatibility but no longer needed
        # Check-in widgets are always visible in the tab structure
        pass
    
    def on_feature_toggled(self, checked):
        """Handle feature enablement checkbox toggles."""
        # Get the sender checkbox to determine which feature was toggled
        sender = self.sender()
        if not sender:
            return
        
        # Update tab visibility based on feature enablement
        self.update_tab_visibility()
    
    def update_tab_visibility(self):
        """Update tab visibility based on feature enablement."""
        tab_widget = self.ui.tabWidget
        
        # Get feature enablement states
        messages_enabled = self.ui.checkBox_enable_messages.isChecked()
        tasks_enabled = self.ui.checkBox_enable_task_management.isChecked()
        checkins_enabled = self.ui.checkBox_enable_checkins.isChecked()
        
        # Update tab visibility
        # Messages tab (index 2) - only show if messages are enabled
        if hasattr(self.ui, 'tab_categories'):
            tab_widget.setTabEnabled(2, messages_enabled)
            if not messages_enabled:
                # If switching to disabled, switch to Basic Information tab
                if tab_widget.currentIndex() == 2:
                    tab_widget.setCurrentIndex(0)
        
        # Tasks tab (index 3) - only show if tasks are enabled
        if hasattr(self.ui, 'tab_tasks'):
            tab_widget.setTabEnabled(3, tasks_enabled)
            if not tasks_enabled:
                # If switching to disabled, switch to Basic Information tab
                if tab_widget.currentIndex() == 3:
                    tab_widget.setCurrentIndex(0)
        
        # Check-ins tab (index 4) - only show if check-ins are enabled
        if hasattr(self.ui, 'tab_checkins'):
            tab_widget.setTabEnabled(4, checkins_enabled)
            if not checkins_enabled:
                # If switching to disabled, switch to Basic Information tab
                if tab_widget.currentIndex() == 4:
                    tab_widget.setCurrentIndex(0)
    
    def open_personalization_dialog(self):
        """Open the personalization dialog."""
        # Generate a temporary user ID for the dialog
        temp_user_id = f"temp_{uuid.uuid4().hex[:8]}"
        
        # Merge timezone from the dialog's timezone field into the data passed to the widget
        tz = self.ui.comboBox_time_zone.currentText() if hasattr(self.ui, 'comboBox_time_zone') else ''
        if tz:
            self.personalization_data['timezone'] = tz
        
        def on_personalization_save(data):
            # Store the personalization data temporarily, and store timezone separately
            tz = data.pop('timezone', None)
            self.personalization_data = data
            if tz:
                self._pending_timezone = tz
            logger.info("Personalization data saved for account creation")
            # Update the profile button to show it's been configured
            self.update_profile_button_state()
        
        from ui.dialogs.user_profile_dialog import open_personalization_dialog
        open_personalization_dialog(self, temp_user_id, on_personalization_save, self.personalization_data)
    
    def update_profile_button_state(self):
        """Update the profile button to show if profile has been configured."""
        profile_button = self.ui.pushButton_profile
        if profile_button and self.personalization_data:
            profile_button.setText("Profile Configured ✓")
            profile_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
            profile_button.setToolTip("Profile has been configured. Click to edit.")
    
    def populate_timezones(self):
        """Populate the timezone combobox with common timezones."""
        import pytz
        timezones = pytz.all_timezones
        self.ui.comboBox_time_zone.clear()
        self.ui.comboBox_time_zone.addItems(timezones)
        # Optionally, set a default (e.g., system timezone)
        import tzlocal
        try:
            local_tz = tzlocal.get_localzone_name()
            idx = self.ui.comboBox_time_zone.findText(local_tz)
            if idx >= 0:
                self.ui.comboBox_time_zone.setCurrentIndex(idx)
        except Exception:
            pass
    
    def validate_input(self) -> tuple[bool, str]:
        """Validate the input and return (is_valid, error_message)."""
        # Check username
        if not self.username:
            return False, "Username is required."
        
        # Check if username is already taken
        if get_user_id_by_internal_username(self.username):
            return False, "Username is already taken."
        
        # Check timezone
        timezone = self.ui.comboBox_time_zone.currentText()
        if not timezone:
            return False, "Time zone is required."
        
        # Check feature enablement
        messages_enabled = self.ui.checkBox_enable_messages.isChecked()
        tasks_enabled = self.ui.checkBox_enable_task_management.isChecked()
        checkins_enabled = self.ui.checkBox_enable_checkins.isChecked()
        
        # At least one feature must be enabled
        if not (messages_enabled or tasks_enabled or checkins_enabled):
            return False, "At least one feature must be enabled."
        
        # If messages are enabled, validate message-related fields
        if messages_enabled:
            # Check categories from widget
            if hasattr(self, 'category_widget'):
                selected_categories = self.category_widget.get_selected_categories()
                if not selected_categories:
                    return False, "At least one message category must be selected."
            else:
                return False, "Category widget not loaded."
            
            # Check message service from widget
            if hasattr(self, 'channel_widget'):
                selected_service, contact_value = self.channel_widget.get_selected_channel()
                if not selected_service:
                    return False, "Please select a communication service."
                if not contact_value:
                    service_name = selected_service.title()
                    return False, f"Please provide contact information for {service_name}."
            else:
                return False, "Channel widget not loaded."
        
        return True, ""
    
    @handle_errors("creating account")
    def validate_and_accept(self):
        """Validate input and accept the dialog."""
        # Read current values from UI fields
        username_edit = self.ui.lineEdit_username
        if username_edit:
            self.username = username_edit.text().strip().lower()
        
        preferred_name_edit = self.ui.lineEdit_prefered_name
        if preferred_name_edit:
            self.preferred_name = preferred_name_edit.text().strip()
        
        is_valid, error_message = self.validate_input()
        if not is_valid:
            QMessageBox.critical(self, "Validation Error", error_message)
            return
        
        # Get selected timezone
        timezone = self.ui.comboBox_time_zone.currentText()
        
        # Get feature enablement states
        messages_enabled = self.ui.checkBox_enable_messages.isChecked()
        tasks_enabled = self.ui.checkBox_enable_task_management.isChecked()
        checkins_enabled = self.ui.checkBox_enable_checkins.isChecked()
        
        # Collect data from widgets based on feature enablement
        selected_categories = []
        selected_service = None
        contact_value = None
        contact_info = {}
        
        if messages_enabled:
            selected_categories = self.category_widget.get_selected_categories()
            selected_service, contact_value = self.channel_widget.get_selected_channel()
            
            # Build contact info
            if selected_service == 'Email':
                contact_info['email'] = contact_value
            elif selected_service == 'Telegram':
                contact_info['telegram'] = contact_value
            elif selected_service == 'Discord':
                contact_info['discord'] = contact_value
        
        task_settings = {}
        if tasks_enabled and hasattr(self, 'task_widget'):
            task_settings = self.task_widget.get_task_settings()
            task_settings['enabled'] = True
        
        checkin_settings = {}
        if checkins_enabled and hasattr(self, 'checkin_widget'):
            checkin_settings = self.checkin_widget.get_checkin_settings()
            checkin_settings['enabled'] = True
        
        # Collect all data
        account_data = {
            'username': self.username,
            'preferred_name': self.preferred_name,
            'categories': selected_categories,
            'channel': {
                'type': selected_service.lower() if selected_service else 'email'
            },
            'contact_info': contact_info,
            'task_settings': task_settings,
            'checkin_settings': checkin_settings,
            'personalization_data': self.personalization_data,
            'timezone': timezone,
            'features_enabled': {
                'messages': messages_enabled,
                'tasks': tasks_enabled,
                'checkins': checkins_enabled
            }
        }
        
        # Create the account
        success = self.create_account(account_data)
        if success:
            self.user_changed.emit()
            self.accept()
        else:
            QMessageBox.critical(self, "Account Creation Failed", "Failed to create account. Please try again.")
    
    def create_account(self, account_data: Dict[str, Any]) -> bool:
        """Create the user account."""
        try:
            # Map contact info correctly
            contact_info = account_data['contact_info']
            email = contact_info.get('email', '')
            phone = contact_info.get('telegram', '')  # Telegram uses phone number
            discord_user_id = contact_info.get('discord', '')
            
            # Determine chat_id based on service type
            channel_type = account_data['channel']['type']
            chat_id = ''
            if channel_type == 'email':
                chat_id = email
            elif channel_type == 'telegram':
                chat_id = phone
            elif channel_type == 'discord':
                chat_id = discord_user_id
            
            # Create user data in the new format
            user_data = {
                'internal_username': account_data['username'],
                'preferred_name': account_data['preferred_name'],
                'chat_id': chat_id,
                'phone': phone,
                'email': email,
                'discord_user_id': discord_user_id,
                'categories': account_data['categories'],
                'channel': account_data['channel'],
                'checkin_settings': account_data['checkin_settings'],
                'task_settings': account_data['task_settings'],
                'personalization_data': account_data['personalization_data'],
                'timezone': getattr(self, '_pending_timezone', account_data.get('timezone', ''))
            }
            
            # Create the user using the new function
            user_id = create_new_user(user_data)
            
            # Create user files with feature enablement information
            # Pass the feature enablement data in the expected format
            user_preferences = {
                'categories': account_data['categories'],
                'channel': account_data['channel'],
                'features_enabled': account_data['features_enabled'],
                'checkin_settings': account_data['checkin_settings'],
                'task_settings': account_data['task_settings']
            }
            create_user_files(user_id, account_data['categories'], user_preferences)
            
            logger.info(f"Created new user account: {account_data['username']} (ID: {user_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error creating account: {e}")
            return False
    
    def get_account_data(self):
        """Get the account data from the form."""
        # Collect data from widgets
        selected_categories = self.category_widget.get_selected_categories()
        selected_service, contact_value = self.channel_widget.get_selected_channel()
        
        # Build contact info
        contact_info = {}
        if selected_service == 'Email':
            contact_info['email'] = contact_value
        elif selected_service == 'Telegram':
            contact_info['telegram'] = contact_value
        elif selected_service == 'Discord':
            contact_info['discord'] = contact_value
        
        task_settings = {}
        if hasattr(self, 'task_widget'):
            task_settings = self.task_widget.get_task_settings()
        
        checkin_settings = {}
        if hasattr(self, 'checkin_widget'):
            checkin_settings = self.checkin_widget.get_checkin_settings()
        
        data = {
            'username': self.username,
            'preferred_name': self.preferred_name,
            'categories': selected_categories,
            'message_service': selected_service.lower() if selected_service else '',
            'contact_info': contact_info,
            'task_settings': task_settings,
            'checkin_settings': checkin_settings,
            'personalization_data': self.personalization_data,
            'timezone': self.ui.comboBox_time_zone.currentText()
        }
        return data
    
    def validate_account_data(self):
        """Validate the account data."""
        return self.validate_input()


def create_account_dialog(parent=None, communication_manager=None):
    """Create and show the account creation dialog."""
    dialog = AccountCreatorDialog(parent, communication_manager)
    result = dialog.exec()
    return result == QDialog.DialogCode.Accepted 