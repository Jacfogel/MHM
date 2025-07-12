# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'account_creator_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFrame, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QSizePolicy, QVBoxLayout,
    QWidget)

def qtTrId(id): return id

class Ui_Dialog_create_account(object):
    def setupUi(self, Dialog_create_account):
        if not Dialog_create_account.objectName():
            Dialog_create_account.setObjectName(u"Dialog_create_account")
        Dialog_create_account.resize(798, 1091)
        Dialog_create_account.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.verticalLayout = QVBoxLayout(Dialog_create_account)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(5, 7, -1, -1)
        self.label_create_a_new_account = QLabel(Dialog_create_account)
        self.label_create_a_new_account.setObjectName(u"label_create_a_new_account")
        self.label_create_a_new_account.setMinimumSize(QSize(0, 0))
        self.label_create_a_new_account.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.label_create_a_new_account.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.label_create_a_new_account.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.label_create_a_new_account.setFrameShape(QFrame.Shape.NoFrame)
        self.label_create_a_new_account.setMargin(-1)

        self.verticalLayout.addWidget(self.label_create_a_new_account)

        self.groupBox_basic_information = QGroupBox(Dialog_create_account)
        self.groupBox_basic_information.setObjectName(u"groupBox_basic_information")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_basic_information)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_username = QLabel(self.groupBox_basic_information)
        self.label_username.setObjectName(u"label_username")

        self.gridLayout.addWidget(self.label_username, 0, 0, 1, 1)

        self.label_prefered_name = QLabel(self.groupBox_basic_information)
        self.label_prefered_name.setObjectName(u"label_prefered_name")

        self.gridLayout.addWidget(self.label_prefered_name, 1, 0, 1, 1)

        self.lineEdit_prefered_name = QLineEdit(self.groupBox_basic_information)
        self.lineEdit_prefered_name.setObjectName(u"lineEdit_prefered_name")

        self.gridLayout.addWidget(self.lineEdit_prefered_name, 1, 1, 1, 1, Qt.AlignmentFlag.AlignLeft)

        self.lineEdit_username = QLineEdit(self.groupBox_basic_information)
        self.lineEdit_username.setObjectName(u"lineEdit_username")

        self.gridLayout.addWidget(self.lineEdit_username, 0, 1, 1, 1, Qt.AlignmentFlag.AlignLeft)

        self.gridLayout.setColumnStretch(1, 1)

        self.verticalLayout_2.addLayout(self.gridLayout)


        self.verticalLayout.addWidget(self.groupBox_basic_information)

        self.groupBox_time_zone = QGroupBox(Dialog_create_account)
        self.groupBox_time_zone.setObjectName(u"groupBox_time_zone")
        self.verticalLayout_12 = QVBoxLayout(self.groupBox_time_zone)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.comboBox_time_zone = QComboBox(self.groupBox_time_zone)
        self.comboBox_time_zone.setObjectName(u"comboBox_time_zone")
        self.comboBox_time_zone.setMinimumSize(QSize(200, 0))

        self.verticalLayout_12.addWidget(self.comboBox_time_zone, 0, Qt.AlignmentFlag.AlignLeft)


        self.verticalLayout.addWidget(self.groupBox_time_zone)

        self.groupBox_primary_channel = QGroupBox(Dialog_create_account)
        self.groupBox_primary_channel.setObjectName(u"groupBox_primary_channel")
        self.verticalLayout_11 = QVBoxLayout(self.groupBox_primary_channel)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.widget_placeholder_channel_selection = QWidget(self.groupBox_primary_channel)
        self.widget_placeholder_channel_selection.setObjectName(u"widget_placeholder_channel_selection")
        self.verticalLayout_7 = QVBoxLayout(self.widget_placeholder_channel_selection)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")

        self.verticalLayout_11.addWidget(self.widget_placeholder_channel_selection)


        self.verticalLayout.addWidget(self.groupBox_primary_channel)

        self.groupBox_select_categories = QGroupBox(Dialog_create_account)
        self.groupBox_select_categories.setObjectName(u"groupBox_select_categories")
        self.verticalLayout_3 = QVBoxLayout(self.groupBox_select_categories)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.widget_placeholder_select_categories = QWidget(self.groupBox_select_categories)
        self.widget_placeholder_select_categories.setObjectName(u"widget_placeholder_select_categories")
        self.verticalLayout_10 = QVBoxLayout(self.widget_placeholder_select_categories)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")

        self.verticalLayout_3.addWidget(self.widget_placeholder_select_categories)


        self.verticalLayout.addWidget(self.groupBox_select_categories)

        self.groupBox_checkBox_enable_task_management = QGroupBox(Dialog_create_account)
        self.groupBox_checkBox_enable_task_management.setObjectName(u"groupBox_checkBox_enable_task_management")
        self.groupBox_checkBox_enable_task_management.setCheckable(True)
        self.groupBox_checkBox_enable_task_management.setChecked(False)
        self.verticalLayout_9 = QVBoxLayout(self.groupBox_checkBox_enable_task_management)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.widget_placeholder_task_settings = QWidget(self.groupBox_checkBox_enable_task_management)
        self.widget_placeholder_task_settings.setObjectName(u"widget_placeholder_task_settings")
        self.verticalLayout_4 = QVBoxLayout(self.widget_placeholder_task_settings)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")

        self.verticalLayout_9.addWidget(self.widget_placeholder_task_settings)


        self.verticalLayout.addWidget(self.groupBox_checkBox_enable_task_management)

        self.groupBox_checkBox_enable_checkins = QGroupBox(Dialog_create_account)
        self.groupBox_checkBox_enable_checkins.setObjectName(u"groupBox_checkBox_enable_checkins")
        self.groupBox_checkBox_enable_checkins.setFlat(False)
        self.groupBox_checkBox_enable_checkins.setCheckable(True)
        self.groupBox_checkBox_enable_checkins.setChecked(False)
        self.verticalLayout_8 = QVBoxLayout(self.groupBox_checkBox_enable_checkins)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.widget_placeholder_checkin_settings = QWidget(self.groupBox_checkBox_enable_checkins)
        self.widget_placeholder_checkin_settings.setObjectName(u"widget_placeholder_checkin_settings")
        self.verticalLayout_5 = QVBoxLayout(self.widget_placeholder_checkin_settings)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")

        self.verticalLayout_8.addWidget(self.widget_placeholder_checkin_settings)


        self.verticalLayout.addWidget(self.groupBox_checkBox_enable_checkins)

        self.groupBox_user_profile = QGroupBox(Dialog_create_account)
        self.groupBox_user_profile.setObjectName(u"groupBox_user_profile")
        self.groupBox_user_profile.setFlat(False)
        self.groupBox_user_profile.setCheckable(False)
        self.groupBox_user_profile.setChecked(False)
        self.verticalLayout_6 = QVBoxLayout(self.groupBox_user_profile)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.widget_placeholder_user_profile = QWidget(self.groupBox_user_profile)
        self.widget_placeholder_user_profile.setObjectName(u"widget_placeholder_user_profile")
        self.verticalLayout_13 = QVBoxLayout(self.widget_placeholder_user_profile)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")

        self.verticalLayout_6.addWidget(self.widget_placeholder_user_profile)


        self.verticalLayout.addWidget(self.groupBox_user_profile)

        self.buttonBox_save_cancel = QDialogButtonBox(Dialog_create_account)
        self.buttonBox_save_cancel.setObjectName(u"buttonBox_save_cancel")
        self.buttonBox_save_cancel.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox_save_cancel.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save)

        self.verticalLayout.addWidget(self.buttonBox_save_cancel)

        self.verticalLayout.setStretch(5, 1)
        self.verticalLayout.setStretch(6, 1)
        self.verticalLayout.setStretch(7, 1)

        self.retranslateUi(Dialog_create_account)
        self.buttonBox_save_cancel.accepted.connect(Dialog_create_account.accept)
        self.buttonBox_save_cancel.rejected.connect(Dialog_create_account.reject)

        QMetaObject.connectSlotsByName(Dialog_create_account)
    # setupUi

    def retranslateUi(self, Dialog_create_account):
        Dialog_create_account.setWindowTitle(QCoreApplication.translate("Dialog_create_account", u"Dialog", None))
        Dialog_create_account.setProperty(u"role", QCoreApplication.translate("Dialog_create_account", u"header", None))
        self.label_create_a_new_account.setText(QCoreApplication.translate("Dialog_create_account", u"Create a New Account", None))
        self.label_create_a_new_account.setProperty(u"role", QCoreApplication.translate("Dialog_create_account", u"header", None))
        self.groupBox_basic_information.setTitle(QCoreApplication.translate("Dialog_create_account", u"Basic Information", None))
        self.label_username.setText(QCoreApplication.translate("Dialog_create_account", u"Username:", None))
        self.label_prefered_name.setText(QCoreApplication.translate("Dialog_create_account", u"Prefered Name:", None))
        self.groupBox_time_zone.setTitle(QCoreApplication.translate("Dialog_create_account", u"Time Zone", None))
        self.groupBox_primary_channel.setTitle(QCoreApplication.translate("Dialog_create_account", u"Prmiary Channel", None))
        self.groupBox_select_categories.setTitle(QCoreApplication.translate("Dialog_create_account", u"Select Categories (at least one required)", None))
        self.groupBox_checkBox_enable_task_management.setTitle(QCoreApplication.translate("Dialog_create_account", u"Enable Task Management", None))
        self.groupBox_checkBox_enable_checkins.setTitle(QCoreApplication.translate("Dialog_create_account", u"Enable Check-ins", None))
        self.groupBox_user_profile.setTitle(QCoreApplication.translate("Dialog_create_account", u"Profile", None))
    # retranslateUi

