from PySide6.QtWidgets import QWidget
from ui.generated.channel_selection_widget_pyqt import Ui_Form_channel_selection

class ChannelSelectionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Form_channel_selection()
        self.ui.setupUi(self)

    def get_selected_channel(self):
        if self.ui.radioButton_Discord.isChecked():
            return 'Discord', self.ui.lineEdit_discordID.text()
        elif self.ui.radioButton_Email.isChecked():
            return 'Email', self.ui.lineEdit_email.text()
        elif self.ui.radioButton_telegram.isChecked():
            return 'Telegram', self.ui.lineEdit_phone.text()
        else:
            return None, None

    def set_selected_channel(self, channel, value):
        if channel == 'Discord':
            self.ui.radioButton_Discord.setChecked(True)
            self.ui.lineEdit_discordID.setText(value)
        elif channel == 'Email':
            self.ui.radioButton_Email.setChecked(True)
            self.ui.lineEdit_email.setText(value)
        elif channel == 'Telegram':
            self.ui.radioButton_telegram.setChecked(True)
            self.ui.lineEdit_phone.setText(value)

    def set_contact_info(self, email=None, phone=None, discord_id=None):
        if email is not None:
            self.ui.lineEdit_email.setText(email)
        if phone is not None:
            self.ui.lineEdit_phone.setText(phone)
        if discord_id is not None:
            self.ui.lineEdit_discordID.setText(discord_id) 