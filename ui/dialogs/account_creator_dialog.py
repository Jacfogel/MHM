# account_creator_dialog.py - Account creator dialog implementation

import uuid
from typing import Dict, Any

# PySide6 imports
from PySide6.QtWidgets import (
    QDialog, QMessageBox
)
from PySide6.QtCore import Signal

# Set up logging
from core.logger import setup_logging, get_component_logger
setup_logging()
logger = get_component_logger('ui')
dialog_logger = logger

# Import core functionality
from core.user_data_validation import validate_schedule_periods
from core.user_management import get_user_id_by_identifier
from core.error_handling import handle_errors

# Import widgets
from ui.widgets.category_selection_widget import CategorySelectionWidget
from ui.widgets.channel_selection_widget import ChannelSelectionWidget
from ui.widgets.task_settings_widget import TaskSettingsWidget
from ui.widgets.checkin_settings_widget import CheckinSettingsWidget
from ui.generated.account_creator_dialog_pyqt import Ui_Dialog_create_account


class AccountCreatorDialog(QDialog):
    """Account creation dialog using existing UI files."""
    user_changed = Signal()
    
    @handle_errors("initializing account creator dialog")
    def __init__(self, parent=None, communication_manager=None):
        """Initialize the account creator dialog."""
        super().__init__(parent)
        logger.info("AccountCreatorDialog.__init__() called")
        
        self.parent = parent
        self.communication_manager = communication_manager
        self.username = ""
        self.preferred_name = ""
        self.personalization_data = {}
        
        # Set up the UI
        self.setWindowTitle("Create New Account")
        self.ui = Ui_Dialog_create_account()
        self.ui.setupUi(self)
        logger.info("AccountCreatorDialog UI setup completed")
        
        # Set up the dialog
        self.setup_dialog()
        logger.info("AccountCreatorDialog setup_dialog() completed")
        
        # Set up connections
        self.setup_connections()
        logger.info("AccountCreatorDialog setup_connections() completed")
        
        # Load widgets
        self.load_widgets()
        logger.info("AccountCreatorDialog load_widgets() completed")
        
        # Center the dialog
        self.center_dialog()
        logger.info("AccountCreatorDialog initialization completed")
    
    @handle_errors("setting up dialog")
    def setup_dialog(self):
        """Set up the dialog properties."""
        self.resize(900, 700)
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        # Setup group boxes (no longer collapsible in tab structure)
        self.setup_feature_group_boxes()
        
        # Setup profile button
        self.setup_profile_button()
        
        # Initialize tab visibility based on default feature settings
        self.update_tab_visibility()
    
    @handle_errors("loading widgets")
    def load_widgets(self):
        """Load all the widget UI files into the placeholder widgets."""
        # Load the widget UI files into the placeholder widgets
        self.load_category_widget()
        self.load_message_service_widget()
        self.load_task_management_widget()
        self.load_checkin_settings_widget()
    
    @handle_errors("loading category widget")
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
    
    @handle_errors("loading message service widget")
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
        
        # Set timezone from existing data if available
        if hasattr(self, '_pending_timezone') and self._pending_timezone:
            self.channel_widget.set_timezone(self._pending_timezone)
        
        # Don't set default selection - let user choose
    
    @handle_errors("loading task management widget")
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
    
    @handle_errors("loading checkin settings widget")
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
    
    @handle_errors("setting up feature group boxes")
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
    
    @handle_errors("setting up profile button")
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
    
    @handle_errors("centering dialog")
    def center_dialog(self):
        """Center the dialog on the parent window."""
        if self.parent:
            parent_geometry = self.parent.geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)
    
    @handle_errors("accepting dialog")
    def accept(self):
        """Override accept to prevent automatic dialog closing."""
        # Don't call super().accept() - this prevents the dialog from closing
        # The dialog will only close when we explicitly call self.accept() after successful account creation
        pass
    
    @handle_errors("closing dialog")
    def close_dialog(self):
        """Close the dialog properly."""
        super().accept()
    
    @handle_errors("setting up connections")
    def setup_connections(self):
        """Setup signal connections."""
        logger.info("setup_connections() called")
        
        # Connect basic info fields
        username_edit = self.ui.lineEdit_username
        if username_edit:
            username_edit.textChanged.connect(self.on_username_changed)
        
        preferred_name_edit = self.ui.lineEdit_preferred_name
        if preferred_name_edit:
            preferred_name_edit.textChanged.connect(self.on_preferred_name_changed)
        
        # Note: Widgets don't have signals, so we'll collect data when needed
        # Category and channel widgets will be queried during validation
        
        # Connect dialog buttons - handle manually to prevent automatic dialog closing
        button_box = self.ui.buttonBox_save_cancel
        if button_box:
            # Clear existing connections and connect manually
            try:
                button_box.accepted.disconnect()
            except:
                pass  # Signal wasn't connected
            try:
                button_box.rejected.disconnect()
            except:
                pass  # Signal wasn't connected
            
            # Connect buttons manually
            save_button = button_box.button(QDialogButtonBox.StandardButton.Save)
            if save_button:
                save_button.clicked.connect(self.validate_and_accept)  # Restore proper connection
                logger.info("Save button connected to validate_and_accept")
            else:
                logger.error("Save button not found in button box")
            
            cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
            if cancel_button:
                cancel_button.clicked.connect(self.reject)
                logger.info("Cancel button connected to reject")
            else:
                logger.error("Cancel button not found in button box")
        else:
            logger.error("buttonBox_save_cancel not found in UI")
        
        # Connect profile button
        profile_button = self.ui.pushButton_profile
        if profile_button:
            profile_button.clicked.connect(self.open_personalization_dialog)
        
        # Connect feature enablement checkboxes
        if hasattr(self.ui, 'checkBox_enable_messages'):
            self.ui.checkBox_enable_messages.toggled.connect(self.on_feature_toggled)
        else:
            logger.warning("checkBox_enable_messages not found in UI")
            
        if hasattr(self.ui, 'checkBox_enable_task_management'):
            self.ui.checkBox_enable_task_management.toggled.connect(self.on_feature_toggled)
        else:
            logger.warning("checkBox_enable_task_management not found in UI")
            
        if hasattr(self.ui, 'checkBox_enable_checkins'):
            self.ui.checkBox_enable_checkins.toggled.connect(self.on_feature_toggled)
        else:
            logger.warning("checkBox_enable_checkins not found in UI")
        
        # Override key events for large dialog
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
    @handle_errors("handling key press events")
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
        try:
            username_edit = self.ui.lineEdit_username
            if username_edit:
                self.username = username_edit.text().strip().lower()
        except Exception as e:
            logger.error(f"Error handling username change: {e}")
    
    def on_preferred_name_changed(self):
        """Handle preferred name change."""
        try:
            preferred_name_edit = self.ui.lineEdit_preferred_name
            if preferred_name_edit:
                self.preferred_name = preferred_name_edit.text().strip()
        except Exception as e:
            logger.error(f"Error handling preferred name change: {e}")
    

    
    def on_feature_toggled(self, checked):
        """Handle feature enablement checkbox toggles."""
        try:
            # Get the sender checkbox to determine which feature was toggled
            sender = self.sender()
            if not sender:
                logger.warning("on_feature_toggled called but no sender found")
                return
            
            logger.info(f"Feature toggled: {sender.objectName()} = {checked}")
            
            # Update tab visibility based on feature enablement
            self.update_tab_visibility()
        except Exception as e:
            logger.error(f"Error handling feature toggle: {e}")
    
    @handle_errors("updating tab visibility")
    def update_tab_visibility(self):
        """Update tab visibility based on feature enablement."""
        tab_widget = self.ui.tabWidget
        
        # Get feature enablement states
        messages_enabled = self.ui.checkBox_enable_messages.isChecked()
        tasks_enabled = self.ui.checkBox_enable_task_management.isChecked()
        checkins_enabled = self.ui.checkBox_enable_checkins.isChecked()
        
        logger.info(f"Updating tab visibility - Messages: {messages_enabled}, Tasks: {tasks_enabled}, Check-ins: {checkins_enabled}")
        
        # Update tab visibility
        # Messages tab (index 2) - only show if messages are enabled
        tab_widget.setTabEnabled(2, messages_enabled)
        if not messages_enabled:
            # If switching to disabled, switch to Basic Information tab
            if tab_widget.currentIndex() == 2:
                tab_widget.setCurrentIndex(0)
        
        # Tasks tab (index 3) - only show if tasks are enabled
        tab_widget.setTabEnabled(3, tasks_enabled)
        logger.info(f"Tasks tab enabled: {tab_widget.isTabEnabled(3)}")
        if not tasks_enabled:
            # If switching to disabled, switch to Basic Information tab
            if tab_widget.currentIndex() == 3:
                tab_widget.setCurrentIndex(0)
        
        # Check-ins tab (index 4) - only show if check-ins are enabled
        tab_widget.setTabEnabled(4, checkins_enabled)
        if not checkins_enabled:
            # If switching to disabled, switch to Basic Information tab
            if tab_widget.currentIndex() == 4:
                tab_widget.setCurrentIndex(0)
    
    @handle_errors("opening personalization dialog")
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
    
    @handle_errors("updating profile button state")
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
    
    # Removed populate_timezones as timezone is now handled by channel widget
    
    @handle_errors("validating input", default_return=(False, "Validation failed"))
    def validate_input(self) -> tuple[bool, str]:
        """Validate the input and return (is_valid, error_message)."""
        logger.info("validate_input() called - starting validation")
        
        # Check username
        if not self.username:
            logger.warning("Validation failed: Username is required")
            return False, "Username is required."
        
        # Check if username is already taken
        if get_user_id_by_identifier(self.username):
            logger.warning(f"Validation failed: Username '{self.username}' is already taken")
            return False, "Username is already taken."
        
        # Check timezone from channel widget
        if hasattr(self, 'channel_widget'):
            timezone = self.channel_widget.get_timezone()
            if not timezone:
                logger.warning("Validation failed: Time zone is required")
                return False, "Time zone is required."
        else:
            logger.warning("Validation failed: Channel widget not loaded")
            return False, "Channel widget not loaded."
        
        # Check feature enablement
        messages_enabled = self.ui.checkBox_enable_messages.isChecked()
        tasks_enabled = self.ui.checkBox_enable_task_management.isChecked()
        checkins_enabled = self.ui.checkBox_enable_checkins.isChecked()
        
        logger.info(f"Feature enablement - messages: {messages_enabled}, tasks: {tasks_enabled}, checkins: {checkins_enabled}")
        
        # At least one feature must be enabled
        if not (messages_enabled or tasks_enabled or checkins_enabled):
            logger.warning("Validation failed: At least one feature must be enabled")
            return False, "At least one feature must be enabled."
        
        # If messages are enabled, validate message-related fields
        if messages_enabled:
            # Check categories from widget
            if hasattr(self, 'category_widget'):
                selected_categories = self.category_widget.get_selected_categories()
                if not selected_categories:
                    logger.warning("Validation failed: At least one message category must be selected")
                    return False, "At least one message category must be selected."
            else:
                logger.warning("Validation failed: Category widget not loaded")
                return False, "Category widget not loaded."
            
            # Check message service from widget
            if hasattr(self, 'channel_widget'):
                selected_service, contact_value = self.channel_widget.get_selected_channel()
                if not selected_service:
                    logger.warning("Validation failed: Please select a communication service")
                    return False, "Please select a communication service."
                if not contact_value:
                    service_name = selected_service.title()
                    logger.warning(f"Validation failed: Please provide contact information for {service_name}")
                    return False, f"Please provide contact information for {service_name}."
                
                # Validate contact info format based on service type
                if selected_service == 'Email':
                    from core.user_data_validation import is_valid_email
                    if not is_valid_email(contact_value):
                        logger.warning("Validation failed: Please enter a valid email address")
                        return False, "Please enter a valid email address."
                # Discord doesn't need format validation - any string is acceptable
                
                # Validate ALL contact fields that have values (not just the selected one)
                email = self.channel_widget.ui.lineEdit_email.text().strip()
                # Phone field was removed - use safe access
                phone = getattr(self.channel_widget.ui, 'lineEdit_phone', None)
                phone = phone.text().strip() if phone else ""
                discord_id = self.channel_widget.ui.lineEdit_discordID.text().strip()
                
                from core.user_data_validation import is_valid_email, is_valid_phone
                
                # Validate email if provided
                if email and not is_valid_email(email):
                    logger.warning("Validation failed: Please enter a valid email address")
                    return False, "Please enter a valid email address."
                
                # Validate phone if provided
                if phone and not is_valid_phone(phone):
                    logger.warning("Validation failed: Please enter a valid phone number (digits only, minimum 10 digits)")
                    return False, "Please enter a valid phone number (digits only, minimum 10 digits)."
                
                # Discord ID doesn't need format validation - any string is acceptable
            else:
                logger.warning("Validation failed: Channel widget not loaded")
                return False, "Channel widget not loaded."
        
        # If task management is enabled, validate task-related fields
        if tasks_enabled:
            if hasattr(self, 'task_widget'):
                task_settings = self.task_widget.get_task_settings()
                time_periods = task_settings.get('time_periods', {})
                is_valid, errors = validate_schedule_periods(time_periods, "tasks")
                if not is_valid:
                    logger.warning(f"Validation failed: Task Management: {errors[0]}")
                    return False, f"Task Management: {errors[0]}"
            else:
                logger.warning("Validation failed: Task widget not loaded")
                return False, "Task widget not loaded."
        
        # If check-ins are enabled, validate check-in-related fields
        if checkins_enabled:
            if hasattr(self, 'checkin_widget'):
                checkin_settings = self.checkin_widget.get_checkin_settings()
                time_periods = checkin_settings.get('time_periods', {})
                is_valid, errors = validate_schedule_periods(time_periods, "check-ins")
                if not is_valid:
                    logger.warning(f"Validation failed: Check-ins: {errors[0]}")
                    return False, f"Check-ins: {errors[0]}"
            else:
                logger.warning("Validation failed: Check-in widget not loaded")
                return False, "Check-in widget not loaded."
        
        logger.info("Validation successful.")
        return True, ""
    
    @handle_errors("collecting basic user info")
    def _validate_and_accept__collect_basic_user_info(self) -> tuple[str, str]:
        """Collect basic user information from UI fields."""
        username_edit = self.ui.lineEdit_username
        if username_edit:
            self.username = username_edit.text().strip().lower()
        
        preferred_name_edit = self.ui.lineEdit_preferred_name
        if preferred_name_edit:
            self.preferred_name = preferred_name_edit.text().strip()
        
        logger.info(f"Collected basic info - username: '{self.username}', preferred_name: '{self.preferred_name}'")
        return self.username, self.preferred_name
    
    @handle_errors("collecting feature settings")
    def _validate_and_accept__collect_feature_settings(self) -> tuple[bool, bool, bool]:
        """Collect feature enablement states from UI."""
        messages_enabled = self.ui.checkBox_enable_messages.isChecked()
        tasks_enabled = self.ui.checkBox_enable_task_management.isChecked()
        checkins_enabled = self.ui.checkBox_enable_checkins.isChecked()
        logger.info(f"Feature enablement - messages: {messages_enabled}, tasks: {tasks_enabled}, checkins: {checkins_enabled}")
        return messages_enabled, tasks_enabled, checkins_enabled
    
    @handle_errors("collecting channel data")
    def _validate_and_accept__collect_channel_data(self) -> tuple[str, dict, dict]:
        """Collect channel and contact information from widgets."""
        # Get selected timezone from channel widget
        timezone = self.channel_widget.get_timezone() if hasattr(self, 'channel_widget') else "America/Regina"
        logger.info(f"Timezone: {timezone}")
        
        # Use the correct method names from ChannelSelectionWidget
        selected_service, contact_value = self.channel_widget.get_selected_channel() if hasattr(self, 'channel_widget') else (None, None)
        channel_data = {'type': selected_service.lower() if selected_service else 'discord'}
        logger.info(f"Channel widget data - service: {selected_service}, contact: {contact_value}")
        
        # Collect contact info
        if hasattr(self, 'channel_widget'):
            # Collect ALL contact info fields, not just the selected one
            # Get all contact fields from the channel widget
            email = self.channel_widget.ui.lineEdit_email.text().strip()
            # Phone field was removed - use safe access
            phone = getattr(self.channel_widget.ui, 'lineEdit_phone', None)
            phone = phone.text().strip() if phone else ""
            discord_id = self.channel_widget.ui.lineEdit_discordID.text().strip()
            logger.info(f"Contact fields - email: '{email}', phone: '{phone}', discord: '{discord_id}'")
        else:
            email = phone = discord_id = ""
        
        contact_info = {
            'email': email,
            'phone': phone,
            'discord': discord_id
        }
        
        return timezone, channel_data, contact_info
    
    @handle_errors("collecting widget data")
    def _validate_and_accept__collect_widget_data(self) -> tuple[list, dict, dict]:
        """Collect data from all widgets."""
        logger.info("About to collect category widget data")
        categories = self.category_widget.get_selected_categories() if hasattr(self, 'category_widget') else []
        logger.info(f"Selected categories: {categories}")
        
        logger.info("About to collect task widget data")
        task_settings = self.task_widget.get_task_settings() if hasattr(self, 'task_widget') else {}
        
        logger.info("About to collect checkin widget data")
        checkin_settings = self.checkin_widget.get_checkin_settings() if hasattr(self, 'checkin_widget') else {}
        
        return categories, task_settings, checkin_settings
    
    @handle_errors("building account data")
    def _validate_and_accept__build_account_data(self, username: str, preferred_name: str, timezone: str, 
                           channel_data: dict, contact_info: dict, categories: list,
                           task_settings: dict, checkin_settings: dict,
                           messages_enabled: bool, tasks_enabled: bool, checkins_enabled: bool) -> dict:
        """Build the complete account data structure."""
        logger.info("About to build account_data")
        account_data = {
            'username': username,
            'preferred_name': preferred_name,
            'categories': categories,
            'channel': channel_data,
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
        logger.info(f"Account data built: {account_data}")
        return account_data
    
    @handle_errors("showing error dialog")
    def _validate_and_accept__show_error_dialog(self, title: str, message: str):
        """Show an error dialog with the given title and message."""
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.setWindowTitle(title)
        error_dialog.setText(message)
        error_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        error_dialog.setModal(True)
        error_dialog.exec()
    
    @handle_errors("showing success dialog")
    def _validate_and_accept__show_success_dialog(self, username: str):
        """Show a success dialog for account creation."""
        success_dialog = QMessageBox(self)
        success_dialog.setIcon(QMessageBox.Icon.Information)
        success_dialog.setWindowTitle("Account Created Successfully")
        success_dialog.setText(f"Account '{username}' has been created successfully!")
        success_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        success_dialog.setModal(True)
        success_dialog.exec()
    
    @handle_errors("validating and accepting dialog", default_return=False)
    def validate_and_accept(self):
        """Validate input and accept the dialog."""
        logger.info("validate_and_accept() called - starting account creation process")
        
        # Validate input first
        if not self._validate_and_accept__input_errors():
            return  # Return without closing the dialog
        
        # Collect all data and create account
        try:
            account_data = self._validate_and_accept__collect_data()
            success = self._validate_and_accept__create_account(account_data)
            
            if success:
                self._validate_and_accept__handle_success(account_data['username'])
            else:
                self._validate_and_accept__show_error_dialog("Account Creation Failed", "Failed to create account. Please try again.")
        except Exception as e:
            logger.error(f"Error during account creation: {e}")
            self._validate_and_accept__show_error_dialog("Account Creation Error", f"An error occurred while creating the account: {str(e)}")
    
    @handle_errors("checking input errors")
    def _validate_and_accept__input_errors(self) -> bool:
        """Validate input and show error dialog if validation fails."""
        username, preferred_name = self._validate_and_accept__collect_basic_user_info()
        
        is_valid, error_message = self.validate_input()
        logger.info(f"Validation result: valid={is_valid}, error_message='{error_message}'")
        
        if not is_valid:
            self._validate_and_accept__show_error_dialog("Validation Error", error_message)
            logger.warning(f"Account creation failed validation: {error_message}")
            return False
        
        logger.info("Validation passed, proceeding with account creation")
        return True
    
    @handle_errors("collecting data")
    def _validate_and_accept__collect_data(self) -> dict:
        """Collect all data from UI and build account data structure."""
        messages_enabled, tasks_enabled, checkins_enabled = self._validate_and_accept__collect_feature_settings()
        timezone, channel_data, contact_info = self._validate_and_accept__collect_channel_data()
        categories, task_settings, checkin_settings = self._validate_and_accept__collect_widget_data()
        
        username, preferred_name = self._validate_and_accept__collect_basic_user_info()
        
        return self._validate_and_accept__build_account_data(
            username, preferred_name, timezone, channel_data, contact_info,
            categories, task_settings, checkin_settings,
            messages_enabled, tasks_enabled, checkins_enabled
        )
    
    @handle_errors("creating account")
    def _validate_and_accept__create_account(self, account_data: dict) -> bool:
        """Create the account and set up all necessary components."""
        try:
            logger.info("About to call create_account()")
            success = self.create_account(account_data)
            logger.info(f"create_account() returned: {success}")
            return success
        except Exception as e:
            logger.error(f"Error during account creation: {e}")
            return False
    
    @handle_errors("handling success")
    def _validate_and_accept__handle_success(self, username: str):
        """Handle successful account creation."""
        self.user_changed.emit()
        self._validate_and_accept__show_success_dialog(username)
        self.close_dialog()
    
    @handle_errors("creating account", default_return=False)
    def create_account(self, account_data: Dict[str, Any]) -> bool:
        """Create the user account."""
        try:
            user_id = str(uuid.uuid4())
            user_preferences = self._validate_and_accept__build_user_preferences(account_data)
            
            # Create user files
            from core.file_operations import create_user_files
            create_user_files(user_id, account_data['categories'], user_preferences)
            
            # Set up additional components
            self._validate_and_accept__setup_task_tags(user_id, account_data)
            self._validate_and_accept__update_user_index(user_id)
            self._validate_and_accept__schedule_new_user(user_id)
            
            logger.info(f"Created new user: {user_id} ({account_data['username']})")
            return True
        except Exception as e:
            logger.error(f"Error creating account: {e}")
            return False
    
    @handle_errors("building user preferences")
    def _validate_and_accept__build_user_preferences(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build user preferences data structure."""
        contact_info = account_data['contact_info']
        features_enabled = account_data.get('features_enabled', {})
        
        # Extract contact info
        email = contact_info.get('email', '')
        phone = contact_info.get('phone', '')
        discord_user_id = contact_info.get('discord', '')
        
        # Determine chat_id based on service type
        chat_id = self._determine_chat_id(account_data['channel']['type'], email, phone, discord_user_id)
        
        # Build features dict
        features = self._build_features_dict(features_enabled)
        
        # Build base preferences
        user_preferences = {
            'internal_username': account_data['username'],
            'chat_id': chat_id,
            'phone': phone,
            'email': email,
            'discord_user_id': discord_user_id,
            'timezone': account_data['timezone'],
            'channel': account_data['channel'],
            'categories': account_data['categories'],
            'features': features,
            'personalization_data': account_data.get('personalization_data', {}),
            'features_enabled': features_enabled
        }
        
        # Add feature-specific settings
        self._validate_and_accept__add_feature_settings(user_preferences, account_data, features_enabled)
        
        return user_preferences
    
    @handle_errors("determining chat ID")
    def _determine_chat_id(self, channel_type: str, email: str, phone: str, discord_user_id: str) -> str:
        """Determine chat_id based on channel type."""
        if channel_type == 'email':
            return email

        elif channel_type == 'discord':
            return discord_user_id
        return ''
    
    @handle_errors("building features dictionary")
    def _build_features_dict(self, features_enabled: Dict[str, bool]) -> Dict[str, str]:
        """Build features dictionary in the correct format."""
        return {
            'automated_messages': 'enabled' if features_enabled.get('messages', False) else 'disabled',
            'checkins': 'enabled' if features_enabled.get('checkins', False) else 'disabled',
            'task_management': 'enabled' if features_enabled.get('tasks', False) else 'disabled'
        }
    
    @handle_errors("adding feature settings")
    def _validate_and_accept__add_feature_settings(self, user_preferences: Dict[str, Any], account_data: Dict[str, Any], features_enabled: Dict[str, bool]):
        """Add feature-specific settings to user preferences."""
        # Add task settings if tasks are enabled
        if features_enabled.get('tasks', False):
            task_settings = account_data.get('task_settings', {}).copy()
            if 'enabled' in task_settings:
                del task_settings['enabled']
            user_preferences['task_settings'] = task_settings
        
        # Add check-in settings if check-ins are enabled
        if features_enabled.get('checkins', False):
            checkin_settings = account_data.get('checkin_settings', {}).copy()
            if 'enabled' in checkin_settings:
                del checkin_settings['enabled']
            user_preferences['checkin_settings'] = checkin_settings
    
    @handle_errors("setting up task tags")
    def _validate_and_accept__setup_task_tags(self, user_id: str, account_data: Dict[str, Any]):
        """Set up task tags for the new user."""
        features_enabled = account_data.get('features_enabled', {})
        if not features_enabled.get('tasks', False):
            return
        
        task_settings = account_data.get('task_settings', {})
        custom_tags = task_settings.get('tags', [])
        
        if custom_tags:
            # Save custom tags that were added during account creation
            from tasks.task_management import add_user_task_tag
            for tag in custom_tags:
                add_user_task_tag(user_id, tag)
            logger.info(f"Saved {len(custom_tags)} custom tags for new user {user_id}: {custom_tags}")
        else:
            # Set up default tags only if no custom tags were added
            from tasks.task_management import setup_default_task_tags
            setup_default_task_tags(user_id)
            logger.info(f"Set up default task tags for new user {user_id}")
    
    @handle_errors("updating user index")
    def _validate_and_accept__update_user_index(self, user_id: str):
        """Update user index for the new user."""
        try:
            from core.user_data_manager import update_user_index
            update_user_index(user_id)
        except Exception as e:
            logger.warning(f"Failed to update user index for new user {user_id}: {e}")
    
    @handle_errors("scheduling new user")
    def _validate_and_accept__schedule_new_user(self, user_id: str):
        """Schedule the new user in the scheduler."""
        try:
            from core.service import get_scheduler_manager
            scheduler_manager = get_scheduler_manager()
            if scheduler_manager:
                scheduler_manager.schedule_new_user(user_id)
                logger.info(f"Scheduled new user {user_id} in scheduler")
            else:
                logger.warning(f"Scheduler manager not available, new user {user_id} not scheduled")
        except Exception as e:
            logger.warning(f"Failed to schedule new user {user_id} in scheduler: {e}")
    
    @handle_errors("getting account data")
    def get_account_data(self):
        """Get the account data from the form."""
        # Collect data from widgets
        selected_categories = self.category_widget.get_selected_categories()
        selected_service, contact_value = self.channel_widget.get_selected_channel()
        
        # Build contact info
        contact_info = {}
        if selected_service == 'Email':
            contact_info['email'] = contact_value
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
            'timezone': self.channel_widget.get_timezone() if hasattr(self, 'channel_widget') else "America/Regina"
        }
        return data
    
    @handle_errors("validating account data")
    def validate_account_data(self):
        """Validate the account data."""
        return self.validate_input()
    
    @staticmethod
    @handle_errors("validating username")
    def validate_username_static(username):
        """Static method to validate username without UI dependencies."""
        if not username:
            return False
        
        if len(username) < 1 or len(username) > 50:
            return False
        
        # Check for invalid characters
        invalid_chars = ['@', ' ', '.', '/', '\\', ':', ';', ',', '<', '>', '|', '?', '*']
        for char in invalid_chars:
            if char in username:
                return False
        
        return True
    
    @staticmethod
    @handle_errors("validating preferred name")
    def validate_preferred_name_static(name):
        """Static method to validate preferred name without UI dependencies."""
        if not name:
            return False
        
        if len(name) < 1 or len(name) > 100:
            return False
        
        # Check for invalid characters
        invalid_chars = ['@', '/', '\\', ':', ';', '<', '>', '|', '?', '*']
        for char in invalid_chars:
            if char in name:
                return False
        
        return True
    
    @staticmethod
    @handle_errors("validating all fields")
    def validate_all_fields_static(username, preferred_name):
        """Static method to validate all fields without UI dependencies."""
        return (AccountCreatorDialog.validate_username_static(username) and 
                AccountCreatorDialog.validate_preferred_name_static(preferred_name))


@handle_errors("creating account dialog")
def create_account_dialog(parent=None, communication_manager=None):
    """Create and show the account creation dialog."""
    dialog = AccountCreatorDialog(parent, communication_manager)
    result = dialog.exec()
    return result == QDialog.DialogCode.Accepted 