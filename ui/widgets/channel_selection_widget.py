from PySide6.QtWidgets import QWidget
from ui.generated.channel_selection_widget_pyqt import Ui_Form_channel_selection

# Import core functionality for timezone handling
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.user_management import get_timezone_options
import pytz

class ChannelSelectionWidget(QWidget):
    def __init__(self, parent=None):
        """
        Initialize the ChannelSelectionWidget.
        
        Sets up the UI for channel selection with Discord and Email options,
        along with timezone selection. Populates timezone options and sets default
        timezone to America/Regina.
        
        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.ui = Ui_Form_channel_selection()
        self.ui.setupUi(self)
        
        # Populate timezone options
        self.populate_timezones()

    def populate_timezones(self):
        """Populate the timezone combo box with options."""
        if hasattr(self.ui, 'comboBox_timezone'):
            self.ui.comboBox_timezone.clear()
            timezone_options = get_timezone_options()
            self.ui.comboBox_timezone.addItems(timezone_options)
            
            # Set default to America/Regina
            regina_idx = self.ui.comboBox_timezone.findText("America/Regina")
            if regina_idx >= 0:
                self.ui.comboBox_timezone.setCurrentIndex(regina_idx)
            else:
                # Fallback to UTC if Regina not found
                utc_idx = self.ui.comboBox_timezone.findText("UTC")
                if utc_idx >= 0:
                    self.ui.comboBox_timezone.setCurrentIndex(utc_idx)

    def get_selected_channel(self):
        if self.ui.radioButton_Discord.isChecked():
            return 'Discord', self.ui.lineEdit_discordID.text()
        elif self.ui.radioButton_Email.isChecked():
            return 'Email', self.ui.lineEdit_email.text()
        # Telegram removed
        else:
            return None, None

    def get_all_contact_info(self):
        """Get all contact info fields from the widget."""
        return {
            'email': self.ui.lineEdit_email.text().strip(),
            'phone': self.ui.lineEdit_phone.text().strip(),
            'discord_id': self.ui.lineEdit_discordID.text().strip()
        }

    def get_timezone(self):
        """Get the selected timezone."""
        if hasattr(self.ui, 'comboBox_timezone'):
            return self.ui.comboBox_timezone.currentText()
        return "America/Regina"

    def set_selected_channel(self, channel, value):
        if channel == 'Discord':
            self.ui.radioButton_Discord.setChecked(True)
            self.ui.lineEdit_discordID.setText(value)
        elif channel == 'Email':
            self.ui.radioButton_Email.setChecked(True)
            self.ui.lineEdit_email.setText(value)
        # Telegram removed

    def set_timezone(self, timezone):
        """Set the timezone."""
        if hasattr(self.ui, 'comboBox_timezone') and timezone:
            # First try exact match
            idx = self.ui.comboBox_timezone.findText(timezone)
            if idx >= 0:
                self.ui.comboBox_timezone.setCurrentIndex(idx)
                return
            
            # Try to find a similar timezone
            for i in range(self.ui.comboBox_timezone.count()):
                item_text = self.ui.comboBox_timezone.itemText(i)
                if timezone.lower() in item_text.lower() or item_text.lower() in timezone.lower():
                    self.ui.comboBox_timezone.setCurrentIndex(i)
                    return
            
            # Fallback to America/Regina
            regina_idx = self.ui.comboBox_timezone.findText("America/Regina")
            if regina_idx >= 0:
                self.ui.comboBox_timezone.setCurrentIndex(regina_idx)
            else:
                # Final fallback to UTC
                utc_idx = self.ui.comboBox_timezone.findText("UTC")
                if utc_idx >= 0:
                    self.ui.comboBox_timezone.setCurrentIndex(utc_idx)

    def set_contact_info(self, email=None, phone=None, discord_id=None, timezone=None):
        if email is not None:
            self.ui.lineEdit_email.setText(email)
        if phone is not None:
            self.ui.lineEdit_phone.setText(phone)
        if discord_id is not None:
            self.ui.lineEdit_discordID.setText(discord_id)
        if timezone is not None:
            self.set_timezone(timezone) 