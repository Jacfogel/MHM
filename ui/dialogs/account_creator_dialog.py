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
    QSpinBox, QTextEdit, QFrame
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
        self.resize(800, 900)
        self.setMinimumSize(700, 700)
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
        
        # Setup collapsible group boxes
        self.setup_collapsible_groups()
    
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
        
        # Set default selection
        self.channel_widget.set_selected_channel("Email", "")
    
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
        
        # Add the task widget
        layout.addWidget(self.task_widget)
    
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
        
        # Add the check-in widget
        layout.addWidget(self.checkin_widget)
        # No frequency selection needed anymore
    
    def setup_collapsible_groups(self):
        """Setup collapsible group boxes for task management and check-ins."""
        # Task management group
        task_group = self.ui.groupBox_checkBox_enable_task_management
        if task_group:
            task_group.setCheckable(True)
            task_group.setChecked(False)
            task_group.toggled.connect(self.on_task_group_toggled)
        
        # Check-in group
        checkin_group = self.ui.groupBox_checkBox_enable_checkins
        if checkin_group:
            checkin_group.setCheckable(True)
            checkin_group.setChecked(False)
            checkin_group.toggled.connect(self.on_checkin_group_toggled)
    
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
        
        # Connect category widget
        if hasattr(self, 'category_widget'):
            self.category_widget.categories_changed.connect(self.on_category_changed)
        
        # Connect channel widget
        if hasattr(self, 'channel_widget'):
            self.channel_widget.channel_changed.connect(self.on_service_changed)
            self.channel_widget.contact_info_changed.connect(self.on_contact_info_changed)
        
        # Connect dialog buttons
        button_box = self.ui.buttonBox_save_cancel
        if button_box:
            button_box.accepted.connect(self.validate_and_accept)
            button_box.rejected.connect(self.reject)
    
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
        """Handle category selection change."""
        self.selected_categories = set(categories)
    
    def on_service_changed(self, service, value):
        """Handle service selection change."""
        self.selected_service = service.lower()
        self.contact_info[service.lower()] = value
    
    def on_contact_info_changed(self, service, value):
        """Handle contact information change."""
        self.contact_info[service.lower()] = value
    
    def on_task_group_toggled(self, checked):
        """Handle task management group toggle."""
        task_widget = self.ui.widget_task_settings
        if task_widget:
            task_widget.setVisible(checked)
    
    def on_checkin_group_toggled(self, checked):
        """Handle check-in group toggle."""
        checkin_widget = self.ui.widget_checkin_settings
        if checkin_widget:
            checkin_widget.setVisible(checked)
    
    def open_personalization_dialog(self):
        """Open the personalization dialog."""
        # Generate a temporary user ID for the dialog
        temp_user_id = f"temp_{uuid.uuid4().hex[:8]}"
        
        def on_personalization_save(data):
            self.personalization_data = data
        
        open_personalization_dialog(self, temp_user_id, on_personalization_save, self.personalization_data)
    
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
        
        # Check categories
        if not self.selected_categories:
            return False, "At least one category must be selected."
        
        # Check message service
        if not self.selected_service:
            return False, "Please select a message service."
        
        # Check contact information for selected service
        if not self.contact_info.get(self.selected_service):
            service_name = self.selected_service.title()
            return False, f"Please provide contact information for {service_name}."
        
        return True, ""
    
    @handle_errors("creating account")
    def validate_and_accept(self):
        """Validate input and accept the dialog."""
        is_valid, error_message = self.validate_input()
        if not is_valid:
            QMessageBox.critical(self, "Validation Error", error_message)
            return
        
        # Get selected timezone
        timezone = self.ui.comboBox_time_zone.currentText()
        
        # Collect all data
        account_data = {
            'username': self.username,
            'preferred_name': self.preferred_name,
            'categories': list(self.selected_categories),
            'message_service': self.selected_service,
            'contact_info': self.contact_info,
            'task_settings': self.task_settings,
            'checkin_settings': self.checkin_settings,
            'personalization_data': self.personalization_data,
            'timezone': timezone
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
            # Create user data in the new format
            user_data = {
                'internal_username': account_data['username'],
                'preferred_name': account_data['preferred_name'],
                'messaging_service': account_data['message_service'],
                'chat_id': account_data['contact_info'].get(account_data['message_service'], ''),
                'phone': account_data['contact_info'].get('telegram', ''),
                'email': account_data['contact_info'].get('email', ''),
                'discord_user_id': account_data['contact_info'].get('discord', ''),
                'categories': account_data['categories'],
                'checkin_settings': account_data['checkin_settings'],
                'task_settings': account_data['task_settings'],
                'personalization_data': account_data['personalization_data'],
                'timezone': account_data['timezone']
            }
            
            # Create the user using the new function
            user_id = create_new_user(user_data)
            
            # Create user files
            create_user_files(user_id, account_data['categories'], account_data)
            
            logger.info(f"Created new user account: {account_data['username']} (ID: {user_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error creating account: {e}")
            return False
    
    def get_account_data(self):
        """Get the account data from the form."""
        data = {
            'username': self.username,
            'preferred_name': self.preferred_name,
            'categories': list(self.selected_categories),
            'message_service': self.selected_service,
            'contact_info': self.contact_info,
            'task_settings': self.task_settings,
            'checkin_settings': self.checkin_settings,
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