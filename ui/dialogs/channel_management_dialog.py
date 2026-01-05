from PySide6.QtWidgets import QDialog, QMessageBox
from ui.generated.channel_management_dialog_pyqt import Ui_Dialog
from ui.widgets.channel_selection_widget import ChannelSelectionWidget
from core.logger import get_component_logger
from PySide6.QtCore import Signal
from core.user_data_validation import is_valid_email
from core.user_data_handlers import (
    get_user_data,
    update_channel_preferences,
    update_user_account,
)
from core.error_handling import handle_errors

class ChannelManagementDialog(QDialog):
    user_changed = Signal()
    def __init__(self, parent=None, user_id=None):
        """Initialize the object."""
        super().__init__(parent)
        try:
            self.setWindowTitle("Channel Settings")
            self.user_id = user_id
            self.ui = Ui_Dialog()
            self.ui.setupUi(self)
            # Add the channel widget to the group box layout
            self.channel_widget = ChannelSelectionWidget(self)
            layout = self.ui.groupBox_primary_channel.layout()
            # Remove any existing widgets
            for i in reversed(range(layout.count())):
                item = layout.itemAt(i)
                w = item.widget()
                if w:
                    w.setParent(None)
            layout.addWidget(self.channel_widget)
            channel_enabled = False
            if self.user_id:
                @handle_errors("loading user channel data", user_friendly=False, default_return=None)
                def load_user_channel_data():
                    user_data_result = get_user_data(self.user_id, 'account')
                    account = user_data_result.get('account') or {}
                    features = account.get('features', {})
                    channel_enabled = features.get('automated_messages') == 'enabled'
                    prefs_result = get_user_data(self.user_id, 'preferences')
                    prefs = prefs_result.get('preferences') or {}
                    channel = prefs.get('channel', {}).get('type', 'email')
                    channel_lc = channel.lower()
                    channel_cap = channel_lc.capitalize()
                    # Always prepopulate all contact fields
                    email = account.get('email', '')
                    discord_id = account.get('discord_user_id', '')
                    timezone = account.get('timezone', 'America/Regina')
                    
                    self.channel_widget.set_contact_info(email=email, discord_id=discord_id, timezone=timezone)
                    # Set the selected channel radio button
                    value = ''
                    if channel_lc == 'email':
                        value = email
                    elif channel_lc == 'discord':
                        value = discord_id
                    self.channel_widget.set_selected_channel(channel_cap, value)
                
                load_user_channel_data()
            
            # Connect Save/Cancel
            self.ui.buttonBox_save_cancel.accepted.connect(self._on_save_clicked)
            self.ui.buttonBox_save_cancel.rejected.connect(self.reject)
        except Exception as e:
            # Error handling for __init__ - log and re-raise since __init__ can't return None
            logger = get_component_logger('ui')
            logger.error(f"Failed to initialize ChannelManagementDialog: {e}", exc_info=True)
            raise

    @handle_errors("handling save button click", default_return=None, user_friendly=True)
    def _on_save_clicked(self):
        """Wrapper to handle save button click and show error dialog if needed."""
        result = self.save_channel_settings()
        if result is False:
            # Error occurred (handled by decorator on save_channel_settings, but show user-friendly dialog)
            QMessageBox.critical(self, "Error", "Failed to save channel settings. Please try again.")
            self.reject()
    
    @handle_errors("saving channel settings", default_return=False, user_friendly=True)
    def save_channel_settings(self):
        if not self.user_id:
            self.accept()
            return True
        
        prefs_result = get_user_data(self.user_id, 'preferences')
        prefs = prefs_result.get('preferences') or {}
        user_data_result = get_user_data(self.user_id, 'account')
        account = user_data_result.get('account') or {}
        channel, value = self.channel_widget.get_selected_channel()
        # Get timezone from channel widget
        timezone = self.channel_widget.get_timezone()
        # Get all contact info from widget
        contact_info = self.channel_widget.get_all_contact_info()
        
        # Collect validation errors
        validation_errors = []
        
        # Validate that the selected channel has valid contact info
        if channel == 'Email' and not contact_info['email']:
            validation_errors.append("Email address is required for Email service.")
        elif channel == 'Discord' and not contact_info['discord_id']:
            validation_errors.append("Discord ID is required for Discord service.")
        
        # Validate email if provided
        if contact_info['email'] and not is_valid_email(contact_info['email']):
            validation_errors.append(f"Invalid email format: {contact_info['email']}")
        
        # Show validation errors if any
        if validation_errors:
            error_message = "Please correct the following validation errors:\n\n" + "\n".join(validation_errors)
            QMessageBox.warning(self, "Validation Errors", error_message)
            return False  # Don't save, let user fix errors
        
        # Save channel type to preferences (lowercase for consistency)
        channel_type = channel.lower()
        # Ensure channel structure exists in preferences
        if 'channel' not in prefs or not isinstance(prefs['channel'], dict):
            prefs['channel'] = {}
        prefs['channel']['type'] = channel_type
        
        # Save the selected channel's contact info as chat_id
        chat_id = ''
        if channel == 'Email':
            chat_id = contact_info['email']
        elif channel == 'Discord':
            chat_id = contact_info['discord_id']
        
        account['chat_id'] = chat_id
        
        if 'settings' in prefs.get('channel', {}):
            del prefs['channel']['settings']
        # Remove any direct contact info from preferences
        for key in ['email', 'phone', 'discord_user_id']:
            if key in prefs:
                del prefs[key]
        
        account['email'] = contact_info['email'] if contact_info['email'] else ''
        account['discord_user_id'] = contact_info['discord_id'] if contact_info['discord_id'] else ''
        
        account['timezone'] = timezone
        # Save both using the channel-specific function to avoid overwriting schedules
        update_channel_preferences(self.user_id, prefs)
        update_user_account(self.user_id, account)
        QMessageBox.information(self, "Success", "Channel settings saved successfully.")
        self.user_changed.emit()
        self.accept()
        return True

    @handle_errors("getting selected channel", default_return=(None, None))
    def get_selected_channel(self):
        return self.channel_widget.get_selected_channel()

    @handle_errors("setting selected channel", default_return=None)
    def set_selected_channel(self, channel, value):
        self.channel_widget.set_selected_channel(channel, value) 