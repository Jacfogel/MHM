from PySide6.QtWidgets import QWidget
from ui.generated.channel_selection_widget_pyqt import Ui_Form_channel_selection

# Import core functionality for timezone handling
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.user_management import get_timezone_options

# Set up logging
from core.logger import get_component_logger
from core.error_handling import handle_errors
logger = get_component_logger('ui')

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

    @handle_errors("populating timezone options")
    def populate_timezones(self):
        """Populate the timezone combo box with options."""
        if hasattr(self.ui, 'comboBox_timezone'):
            self.ui.comboBox_timezone.clear()
            timezone_options = get_timezone_options()
            self.ui.comboBox_timezone.addItems(timezone_options)
            logger.debug(f"Populated timezone combo box with {len(timezone_options)} options")
            
            # Set default to America/Regina
            regina_idx = self.ui.comboBox_timezone.findText("America/Regina")
            if regina_idx >= 0:
                self.ui.comboBox_timezone.setCurrentIndex(regina_idx)
                logger.debug("Set default timezone to America/Regina")
            else:
                # Fallback to UTC if Regina not found
                utc_idx = self.ui.comboBox_timezone.findText("UTC")
                if utc_idx >= 0:
                    self.ui.comboBox_timezone.setCurrentIndex(utc_idx)
                    logger.debug("Set default timezone to UTC (fallback)")
                else:
                    logger.warning("Could not find America/Regina or UTC in timezone options")
        else:
            logger.warning("Timezone combo box not found in UI")

    @handle_errors("getting selected channel")
    def get_selected_channel(self):
        if self.ui.radioButton_Discord.isChecked():
            discord_id = self.ui.lineEdit_discordID.text()
            logger.debug(f"Selected Discord channel with ID: {discord_id}")
            return 'Discord', discord_id
        elif self.ui.radioButton_Email.isChecked():
            email = self.ui.lineEdit_email.text()
            logger.debug(f"Selected Email channel with address: {email}")
            return 'Email', email
        else:
            logger.warning("No channel selected")
            return None, None

    @handle_errors("getting all contact info")
    def get_all_contact_info(self):
        """Get all contact info fields from the widget."""
        return {
            'email': self.ui.lineEdit_email.text().strip(),
            'discord_id': self.ui.lineEdit_discordID.text().strip()
        }

    @handle_errors("getting timezone")
    def get_timezone(self):
        """Get the selected timezone."""
        if hasattr(self.ui, 'comboBox_timezone'):
            return self.ui.comboBox_timezone.currentText()
        return "America/Regina"

    @handle_errors("setting selected channel")
    def set_selected_channel(self, channel, value):
        if channel == 'Discord':
            self.ui.radioButton_Discord.setChecked(True)
            self.ui.lineEdit_discordID.setText(value)
        elif channel == 'Email':
            self.ui.radioButton_Email.setChecked(True)
            self.ui.lineEdit_email.setText(value)


    @handle_errors("setting timezone")
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

    def set_contact_info(self, email=None, discord_id=None, timezone=None):
        if email is not None:
            self.ui.lineEdit_email.setText(email)
        if discord_id is not None:
            self.ui.lineEdit_discordID.setText(discord_id)
        if timezone is not None:
            self.set_timezone(timezone) 