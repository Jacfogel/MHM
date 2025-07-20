# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'channel_selection_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QLabel,
    QLayout, QLineEdit, QRadioButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

def qtTrId(id): return id

class Ui_Form_channel_selection(object):
    def setupUi(self, Form_channel_selection):
        if not Form_channel_selection.objectName():
            Form_channel_selection.setObjectName(u"Form_channel_selection")
        Form_channel_selection.resize(400, 180)
        self.verticalLayout = QVBoxLayout(Form_channel_selection)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.radioButton_telegram = QRadioButton(Form_channel_selection)
        self.radioButton_telegram.setObjectName(u"radioButton_telegram")

        self.gridLayout_4.addWidget(self.radioButton_telegram, 3, 0, 1, 1)

        self.lineEdit_discordID = QLineEdit(Form_channel_selection)
        self.lineEdit_discordID.setObjectName(u"lineEdit_discordID")

        self.gridLayout_4.addWidget(self.lineEdit_discordID, 1, 3, 1, 1)

        self.lineEdit_email = QLineEdit(Form_channel_selection)
        self.lineEdit_email.setObjectName(u"lineEdit_email")

        self.gridLayout_4.addWidget(self.lineEdit_email, 2, 3, 1, 1)

        self.lineEdit_phone = QLineEdit(Form_channel_selection)
        self.lineEdit_phone.setObjectName(u"lineEdit_phone")

        self.gridLayout_4.addWidget(self.lineEdit_phone, 3, 3, 1, 1)

        self.comboBox_timezone = QComboBox(Form_channel_selection)
        self.comboBox_timezone.setObjectName(u"comboBox_timezone")

        self.gridLayout_4.addWidget(self.comboBox_timezone, 4, 3, 1, 1)

        self.label_select_service = QLabel(Form_channel_selection)
        self.label_select_service.setObjectName(u"label_select_service")

        self.gridLayout_4.addWidget(self.label_select_service, 0, 0, 1, 1)

        self.radioButton_Discord = QRadioButton(Form_channel_selection)
        self.radioButton_Discord.setObjectName(u"radioButton_Discord")

        self.gridLayout_4.addWidget(self.radioButton_Discord, 1, 0, 1, 1)

        self.radioButton_Email = QRadioButton(Form_channel_selection)
        self.radioButton_Email.setObjectName(u"radioButton_Email")

        self.gridLayout_4.addWidget(self.radioButton_Email, 2, 0, 1, 1)

        self.label_timezone = QLabel(Form_channel_selection)
        self.label_timezone.setObjectName(u"label_timezone")

        self.gridLayout_4.addWidget(self.label_timezone, 4, 0, 1, 1)

        self.label_email = QLabel(Form_channel_selection)
        self.label_email.setObjectName(u"label_email")

        self.gridLayout_4.addWidget(self.label_email, 2, 2, 1, 1)

        self.label_phone = QLabel(Form_channel_selection)
        self.label_phone.setObjectName(u"label_phone")

        self.gridLayout_4.addWidget(self.label_phone, 3, 2, 1, 1)

        self.label_discordID = QLabel(Form_channel_selection)
        self.label_discordID.setObjectName(u"label_discordID")

        self.gridLayout_4.addWidget(self.label_discordID, 1, 2, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_4.addItem(self.verticalSpacer, 0, 1, 5, 1)

        self.label_contact_information = QLabel(Form_channel_selection)
        self.label_contact_information.setObjectName(u"label_contact_information")

        self.gridLayout_4.addWidget(self.label_contact_information, 0, 2, 1, 2)


        self.verticalLayout.addLayout(self.gridLayout_4)


        self.retranslateUi(Form_channel_selection)

        QMetaObject.connectSlotsByName(Form_channel_selection)
    # setupUi

    def retranslateUi(self, Form_channel_selection):
        Form_channel_selection.setWindowTitle(QCoreApplication.translate("Form_channel_selection", u"Form", None))
        self.radioButton_telegram.setText(QCoreApplication.translate("Form_channel_selection", u"Telegram", None))
        self.label_select_service.setText(QCoreApplication.translate("Form_channel_selection", u"Select Service", None))
        self.label_select_service.setProperty(u"role", QCoreApplication.translate("Form_channel_selection", u"header3", None))
        self.radioButton_Discord.setText(QCoreApplication.translate("Form_channel_selection", u"Discord", None))
        self.radioButton_Email.setText(QCoreApplication.translate("Form_channel_selection", u"Email", None))
        self.label_timezone.setText(QCoreApplication.translate("Form_channel_selection", u"Timezone:", None))
        self.label_email.setText(QCoreApplication.translate("Form_channel_selection", u"Email:", None))
        self.label_phone.setText(QCoreApplication.translate("Form_channel_selection", u"Phone:", None))
        self.label_discordID.setText(QCoreApplication.translate("Form_channel_selection", u"Discord ID:", None))
        self.label_contact_information.setText(QCoreApplication.translate("Form_channel_selection", u"Contact Information", None))
        self.label_contact_information.setProperty(u"role", QCoreApplication.translate("Form_channel_selection", u"header3", None))
    # retranslateUi

