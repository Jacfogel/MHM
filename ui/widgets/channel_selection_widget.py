# channel_selection_widget.py
# pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]

"""Channel Selection Widget"""

from PySide6.QtWidgets import QWidget
from ui.generated.channel_selection_widget_pyqt import Ui_Form_channel_selection

from core import get_timezone_options

# Set up logging
from core.logger import get_component_logger
from core.error_handling import handle_errors

logger = get_component_logger("ui")


class ChannelSelectionWidget(QWidget):
    # ERROR_HANDLING_EXCLUDE: Simple constructor that only sets up UI
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
        self.sms_owner = ""
        self.sms_token = ""
        self.ui.button_sms_connect.clicked.connect(self._begin_sms)
        self.ui.button_sms_verify.clicked.connect(self._verify_sms)
        self.ui.button_sms_disconnect.clicked.connect(self._disconnect_sms)
        self.ui.button_sms_disconnect.setEnabled(False)
        self.whatsapp_owner = ""
        self.whatsapp_token = ""
        self.ui.radioButton_WhatsApp.setEnabled(False)
        self.ui.button_whatsapp_connect.clicked.connect(self._begin_whatsapp)
        self.ui.button_whatsapp_verify.clicked.connect(self._verify_whatsapp)
        self.ui.button_whatsapp_disconnect.clicked.connect(self._disconnect_whatsapp)
        self.ui.button_whatsapp_disconnect.setEnabled(False)


        # Populate timezone options
        self.populate_timezones()

    @handle_errors("populating timezone options")
    def populate_timezones(self):
        """Populate the timezone combo box with options."""
        if hasattr(self.ui, "comboBox_timezone"):
            self.ui.comboBox_timezone.clear()
            timezone_options = get_timezone_options()
            self.ui.comboBox_timezone.addItems(timezone_options)
            logger.debug(
                f"Populated timezone combo box with {len(timezone_options)} options"
            )

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
                    logger.warning(
                        "Could not find America/Regina or UTC in timezone options"
                    )
        else:
            logger.warning("Timezone combo box not found in UI")

    @handle_errors("getting selected channel")
    def get_selected_channel(self):
        if self.ui.radioButton_WhatsApp.isChecked():
            return "WhatsApp", self.ui.lineEdit_whatsapp_phone.text().strip()
        if self.ui.radioButton_SMS.isChecked():
            return "SMS", self.ui.lineEdit_phone.text().strip()
        if self.ui.radioButton_Discord.isChecked():
            discord_id = self.ui.lineEdit_discordID.text()
            logger.debug(f"Selected Discord channel with ID: {discord_id}")
            return "Discord", discord_id
        elif self.ui.radioButton_Email.isChecked():
            email = self.ui.lineEdit_email.text()
            logger.debug(f"Selected Email channel with address: {email}")
            return "Email", email
        else:
            logger.warning("No channel selected")
            return None, None

    @handle_errors("getting all contact info")
    def get_all_contact_info(self):
        """Get all contact info fields from the widget."""
        return {
            "email": self.ui.lineEdit_email.text().strip(),
            "discord_id": self.ui.lineEdit_discordID.text().strip(),
            "phone": self.ui.lineEdit_phone.text().strip(),
            "whatsapp_phone": self.ui.lineEdit_whatsapp_phone.text().strip(),
        }

    @handle_errors("getting timezone")
    def get_timezone(self):
        """Get the selected timezone."""
        if hasattr(self.ui, "comboBox_timezone"):
            return self.ui.comboBox_timezone.currentText()
        return "America/Regina"

    @handle_errors("setting selected channel")
    def set_selected_channel(self, channel, value):
        if channel.lower() == "whatsapp":
            self.ui.radioButton_WhatsApp.setChecked(True)
            self.ui.lineEdit_whatsapp_phone.setText(value)
        if channel.lower() == "sms":
            self.ui.radioButton_SMS.setChecked(True)
            self.ui.lineEdit_phone.setText(value)
        if channel == "Discord":
            self.ui.radioButton_Discord.setChecked(True)
            self.ui.lineEdit_discordID.setText(value)
        elif channel == "Email":
            self.ui.radioButton_Email.setChecked(True)
            self.ui.lineEdit_email.setText(value)

    @handle_errors("setting timezone")
    def set_timezone(self, timezone):
        """Set the timezone."""
        if hasattr(self.ui, "comboBox_timezone") and timezone:
            # First try exact match
            idx = self.ui.comboBox_timezone.findText(timezone)
            if idx >= 0:
                self.ui.comboBox_timezone.setCurrentIndex(idx)
                return

            # Try to find a similar timezone
            for i in range(self.ui.comboBox_timezone.count()):
                item_text = self.ui.comboBox_timezone.itemText(i)
                if (
                    timezone.lower() in item_text.lower()
                    or item_text.lower() in timezone.lower()
                ):
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

    # ERROR_HANDLING_EXCLUDE: Simple setter method that only updates UI elements
    def set_contact_info(self, email=None, discord_id=None, timezone=None, phone=None):
        if phone is not None:
            self.ui.lineEdit_phone.setText(phone)
        if email is not None:
            self.ui.lineEdit_email.setText(email)
        if discord_id is not None:
            self.ui.lineEdit_discordID.setText(discord_id)
        if timezone is not None:
            self.set_timezone(timezone)

    @handle_errors("preparing SMS connection", user_friendly=False, default_return=None)
    def _begin_sms(self):
        """Show a phone ownership challenge without sending a paid text."""
        from core import config
        from core.sms_enrollment import begin_sms_enrollment
        from core.error_handling import ValidationError

        try:
            self.sms_token = begin_sms_enrollment(
                self.ui.lineEdit_phone.text(), self.ui.checkBox_sms_consent.isChecked(), self.sms_owner
            )
            self.ui.label_sms_status.setText(
                f"From this phone, text LINK {self.sms_token} to {config.TWILIO_PHONE_NUMBER}. "
                "Then press verify. The code expires in 15 minutes."
            )
        except ValidationError as exc:
            self.ui.label_sms_status.setText(str(exc))

    @handle_errors("checking SMS phone proof", user_friendly=False, default_return=False)
    def sms_selection_valid(self):
        """Require an existing enrollment or a new phone-bound proof and explicit consent."""
        from core.sms_enrollment import sms_available, sms_user_for_phone
        from communication.communication_channels.sms.phone import normalize_phone
        from storage.sms_state import SmsState

        phone = normalize_phone(self.ui.lineEdit_phone.text())
        if not sms_available() or not phone or not self.ui.checkBox_sms_consent.isChecked():
            return False
        if self.sms_owner and sms_user_for_phone(phone) == self.sms_owner:
            return True
        return self.ui.checkBox_sms_consent.isChecked() and SmsState().enrollment_verified(
            phone, self.sms_token, self.sms_owner
        )

    @handle_errors("showing SMS verification result", user_friendly=False, default_return=None)
    def _verify_sms(self):
        """Show whether the signed incoming text proved ownership."""
        self.ui.label_sms_status.setText(
            "Phone verified. Save the account/channel settings to finish connecting SMS."
            if self.sms_selection_valid() else "Not verified yet. Check the phone and connection code, send it, then verify again."
        )

    @handle_errors("disconnecting desktop SMS", user_friendly=True, default_return=None)
    def _disconnect_sms(self):
        """Revoke SMS consent without deleting opt-out or delivery history."""
        from storage.sms_state import SmsState

        if not self.sms_owner:
            return
        SmsState().disconnect_enrollment(self.sms_owner)
        self.sms_token = ""
        self.ui.checkBox_sms_consent.setChecked(False)
        self.ui.label_sms_status.setText("SMS disconnected. Choose another delivery channel explicitly to resume reminders.")
        self.ui.button_sms_disconnect.setEnabled(False)

    @handle_errors("preparing WhatsApp connection", user_friendly=False, default_return=None)
    def _begin_whatsapp(self):
        """Show a phone ownership challenge without sending a paid text."""
        from core import config
        from core.whatsapp_enrollment import begin_whatsapp_enrollment
        from core.error_handling import ValidationError

        try:
            self.whatsapp_token = begin_whatsapp_enrollment(
                self.ui.lineEdit_whatsapp_phone.text(), self.ui.checkBox_whatsapp_consent.isChecked(), self.whatsapp_owner
            )
            self.ui.label_whatsapp_status.setText(
                f"From this phone, send in WhatsApp: LINK {self.whatsapp_token} to {config.WHATSAPP_PHONE_NUMBER}. "
                "Then press verify. The code expires in 15 minutes."
            )
        except ValidationError as exc:
            self.ui.label_whatsapp_status.setText(str(exc))

    @handle_errors("checking WhatsApp phone proof", user_friendly=False, default_return=False)
    def whatsapp_selection_valid(self):
        """Require an existing enrollment or a new phone-bound proof and explicit consent."""
        from core.whatsapp_enrollment import whatsapp_available, whatsapp_user_for_phone
        from communication.communication_channels.sms.phone import normalize_phone
        from storage.whatsapp_state import WhatsAppState

        phone = normalize_phone(self.ui.lineEdit_whatsapp_phone.text())
        if not whatsapp_available() or not phone or not self.ui.checkBox_whatsapp_consent.isChecked():
            return False
        if self.whatsapp_owner and whatsapp_user_for_phone(phone) == self.whatsapp_owner:
            return True
        return self.ui.checkBox_whatsapp_consent.isChecked() and WhatsAppState().enrollment_verified(
            phone, self.whatsapp_token, self.whatsapp_owner
        )

    @handle_errors("showing WhatsApp verification result", user_friendly=False, default_return=None)
    def _verify_whatsapp(self):
        """Show whether the signed incoming text proved ownership."""
        self.ui.label_whatsapp_status.setText(
            "Phone verified. Save the account/channel settings to finish connecting WhatsApp."
            if self.whatsapp_selection_valid() else "Not verified yet. Check the phone and connection code, send it, then verify again."
        )

    @handle_errors("disconnecting desktop WhatsApp", user_friendly=True, default_return=None)
    def _disconnect_whatsapp(self):
        """Revoke WhatsApp consent and preserve other channel choices."""
        from core import get_user_data
        from core.whatsapp_enrollment import disconnect_whatsapp

        if not self.whatsapp_owner:
            return
        account = get_user_data(self.whatsapp_owner, "account").get("account") or {}
        selected = disconnect_whatsapp(self.whatsapp_owner)
        self.whatsapp_token = ""
        self.ui.checkBox_whatsapp_consent.setChecked(False)
        contact_key = {"sms": "phone", "whatsapp": "whatsapp_phone", "email": "email", "discord": "discord_user_id"}.get(selected, "email")
        label = "SMS" if selected == "sms" else selected.capitalize()
        self.set_selected_channel(label, account.get(contact_key, ""))
        self.ui.label_whatsapp_status.setText("WhatsApp disconnected. Choose another delivery channel explicitly to resume its reminders.")
        self.ui.button_whatsapp_disconnect.setEnabled(False)
