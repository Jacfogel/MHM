from PySide6.QtWidgets import QDialog, QMessageBox
from ui.generated.channel_management_dialog_pyqt import Ui_Dialog
from ui.widgets.channel_selection_widget import ChannelSelectionWidget
import logging
from PySide6.QtCore import Signal
from core.validation import is_valid_email, is_valid_phone

class ChannelManagementDialog(QDialog):
    user_changed = Signal()
    def __init__(self, parent=None, user_id=None):
        super().__init__(parent)
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
        # Load user account to set groupbox checked state
        channel_enabled = False
        if self.user_id:
            try:
                from core.user_management import get_user_data
                user_data_result = get_user_data(self.user_id, 'account')
                account = user_data_result.get('account') or {}
                features = account.get('features', {})
                channel_enabled = features.get('automated_messages') == 'enabled'
                # Load user data and prepopulate fields
                prefs_result = get_user_data(self.user_id, 'preferences')
                prefs = prefs_result.get('preferences') or {}
                channel = prefs.get('channel', {}).get('type', 'email')
                channel_lc = channel.lower()
                channel_cap = channel_lc.capitalize()
                # Always prepopulate all contact fields
                email = account.get('email', '')
                phone = account.get('phone', '')
                discord_id = account.get('discord_user_id', '')
                timezone = account.get('timezone', 'America/Regina')
                self.channel_widget.set_contact_info(email=email, phone=phone, discord_id=discord_id, timezone=timezone)
                # Set the selected channel radio button
                value = ''
                if channel_lc == 'email':
                    value = email
                elif channel_lc == 'telegram':
                    value = phone
                elif channel_lc == 'discord':
                    value = discord_id
                self.channel_widget.set_selected_channel(channel_cap, value)
            except Exception as e:
                logging.error(f"Exception in load_user_channel_data: {e}")
        
        # Connect Save/Cancel
        self.ui.buttonBox_save_cancel.accepted.connect(self.save_channel_settings)
        self.ui.buttonBox_save_cancel.rejected.connect(self.reject)

    def save_channel_settings(self):
        if not self.user_id:
            self.accept()
            return
        try:
            from core.user_management import update_user_preferences, get_user_data, update_user_account
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
            
            # Validate email if provided
            if contact_info['email'] and not is_valid_email(contact_info['email']):
                validation_errors.append(f"Invalid email format: {contact_info['email']}")
            
            # Validate phone if provided
            if contact_info['phone'] and not is_valid_phone(contact_info['phone']):
                validation_errors.append(f"Invalid phone format: {contact_info['phone']}")
            
            # Show validation errors if any
            if validation_errors:
                error_message = "Please correct the following validation errors:\n\n" + "\n".join(validation_errors)
                QMessageBox.warning(self, "Validation Errors", error_message)
                return  # Don't save, let user fix errors
            
            # Save channel type to preferences (lowercase for consistency)
            channel_type = channel.lower()
            # Ensure channel structure exists in preferences
            if 'channel' not in prefs or not isinstance(prefs['channel'], dict):
                prefs['channel'] = {}
            prefs['channel']['type'] = channel_type
            # Remove any old 'settings' block from preferences
            if 'settings' in prefs.get('channel', {}):
                del prefs['channel']['settings']
            # Remove any direct contact info from preferences
            for key in ['email', 'phone', 'discord_user_id']:
                if key in prefs:
                    del prefs[key]
            # Save all valid contact info to account/profile
            if contact_info['email'] and is_valid_email(contact_info['email']):
                account['email'] = contact_info['email']
            if contact_info['phone'] and is_valid_phone(contact_info['phone']):
                account['phone'] = contact_info['phone']
            if contact_info['discord_id'] and contact_info['discord_id'].strip():
                account['discord_user_id'] = contact_info['discord_id']
            # Save timezone to account
            account['timezone'] = timezone
            # Save both
            update_user_preferences(self.user_id, prefs)
            update_user_account(self.user_id, account)
            QMessageBox.information(self, "Success", "Channel settings saved successfully.")
            self.user_changed.emit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save channel settings: {e}")
            self.reject()

    def get_selected_channel(self):
        return self.channel_widget.get_selected_channel()

    def set_selected_channel(self, channel, value):
        self.channel_widget.set_selected_channel(channel, value) 