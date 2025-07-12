from PySide6.QtWidgets import QDialog, QMessageBox
from ui.generated.channel_management_dialog_pyqt import Ui_Dialog
from ui.widgets.channel_selection_widget import ChannelSelectionWidget
import logging
from PySide6.QtCore import Signal

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
        # Load user data and prepopulate fields
        self.load_user_channel_data()
        # Connect Save/Cancel
        self.ui.buttonBox_save_cancel.accepted.connect(self.save_channel_settings)
        self.ui.buttonBox_save_cancel.rejected.connect(self.reject)

    def load_user_channel_data(self):
        if not self.user_id:
            return
        try:
            from core.user_management import get_user_preferences, get_user_account
            prefs = get_user_preferences(self.user_id) or {}
            account = get_user_account(self.user_id) or {}
            channel = prefs.get('messaging_service', 'email')
            channel_lc = channel.lower()
            channel_cap = channel_lc.capitalize()
            # Always prepopulate all contact fields
            email = account.get('email', '')
            phone = account.get('phone', '')
            discord_id = account.get('discord_user_id', '')
            self.channel_widget.set_contact_info(email=email, phone=phone, discord_id=discord_id)
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

    def save_channel_settings(self):
        if not self.user_id:
            self.accept()
            return
        try:
            from core.user_management import get_user_preferences, update_user_preferences, get_user_account, update_user_account
            prefs = get_user_preferences(self.user_id) or {}
            account = get_user_account(self.user_id) or {}
            channel, value = self.channel_widget.get_selected_channel()
            # Save channel type to preferences (lowercase for consistency)
            channel_type = channel.lower()
            prefs['messaging_service'] = channel_type
            # If using a nested channel structure, update it too
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
            # Save contact info to account/profile only
            if channel_type == 'email':
                account['email'] = value
            elif channel_type == 'telegram':
                account['phone'] = value
            elif channel_type == 'discord':
                account['discord_user_id'] = value
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