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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QDialog,
    QDialogButtonBox, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QTabWidget, QVBoxLayout,
    QWidget)

class Ui_Dialog_create_account(object):
    def setupUi(self, Dialog_create_account):
        if not Dialog_create_account.objectName():
            Dialog_create_account.setObjectName(u"Dialog_create_account")
        Dialog_create_account.resize(900, 700)
        Dialog_create_account.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.verticalLayout = QVBoxLayout(Dialog_create_account)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        self.label_create_a_new_account = QLabel(Dialog_create_account)
        self.label_create_a_new_account.setObjectName(u"label_create_a_new_account")
        self.label_create_a_new_account.setMinimumSize(QSize(0, 30))
        self.label_create_a_new_account.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.label_create_a_new_account.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.label_create_a_new_account.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.label_create_a_new_account.setFrameShape(QFrame.Shape.NoFrame)
        self.label_create_a_new_account.setMargin(-1)

        self.verticalLayout.addWidget(self.label_create_a_new_account)

        self.tabWidget = QTabWidget(Dialog_create_account)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab_basic_info = QWidget()
        self.tab_basic_info.setObjectName(u"tab_basic_info")
        self.verticalLayout_basic = QVBoxLayout(self.tab_basic_info)
        self.verticalLayout_basic.setObjectName(u"verticalLayout_basic")
        self.verticalLayout_basic.setContentsMargins(10, 10, 10, 10)
        self.groupBox_basic_information = QGroupBox(self.tab_basic_info)
        self.groupBox_basic_information.setObjectName(u"groupBox_basic_information")
        self.gridLayout_basic = QGridLayout(self.groupBox_basic_information)
        self.gridLayout_basic.setObjectName(u"gridLayout_basic")
        self.gridLayout_basic.setContentsMargins(10, 10, 10, 10)
        self.label_username = QLabel(self.groupBox_basic_information)
        self.label_username.setObjectName(u"label_username")

        self.gridLayout_basic.addWidget(self.label_username, 0, 0, 1, 1)

        self.lineEdit_username = QLineEdit(self.groupBox_basic_information)
        self.lineEdit_username.setObjectName(u"lineEdit_username")

        self.gridLayout_basic.addWidget(self.lineEdit_username, 0, 1, 1, 1)

        self.label_prefered_name = QLabel(self.groupBox_basic_information)
        self.label_prefered_name.setObjectName(u"label_prefered_name")

        self.gridLayout_basic.addWidget(self.label_prefered_name, 1, 0, 1, 1)

        self.lineEdit_prefered_name = QLineEdit(self.groupBox_basic_information)
        self.lineEdit_prefered_name.setObjectName(u"lineEdit_prefered_name")

        self.gridLayout_basic.addWidget(self.lineEdit_prefered_name, 1, 1, 1, 1)


        self.verticalLayout_basic.addWidget(self.groupBox_basic_information)

        self.groupBox_features = QGroupBox(self.tab_basic_info)
        self.groupBox_features.setObjectName(u"groupBox_features")
        self.verticalLayout_features = QVBoxLayout(self.groupBox_features)
        self.verticalLayout_features.setObjectName(u"verticalLayout_features")
        self.verticalLayout_features.setContentsMargins(10, 10, 10, 10)
        self.checkBox_enable_messages = QCheckBox(self.groupBox_features)
        self.checkBox_enable_messages.setObjectName(u"checkBox_enable_messages")
        self.checkBox_enable_messages.setChecked(True)

        self.verticalLayout_features.addWidget(self.checkBox_enable_messages)

        self.checkBox_enable_task_management = QCheckBox(self.groupBox_features)
        self.checkBox_enable_task_management.setObjectName(u"checkBox_enable_task_management")
        self.checkBox_enable_task_management.setChecked(False)

        self.verticalLayout_features.addWidget(self.checkBox_enable_task_management)

        self.checkBox_enable_checkins = QCheckBox(self.groupBox_features)
        self.checkBox_enable_checkins.setObjectName(u"checkBox_enable_checkins")
        self.checkBox_enable_checkins.setChecked(False)

        self.verticalLayout_features.addWidget(self.checkBox_enable_checkins)


        self.verticalLayout_basic.addWidget(self.groupBox_features)

        self.verticalSpacer_basic = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_basic.addItem(self.verticalSpacer_basic)

        self.tabWidget.addTab(self.tab_basic_info, "")
        self.tab_communication = QWidget()
        self.tab_communication.setObjectName(u"tab_communication")
        self.verticalLayout_comm = QVBoxLayout(self.tab_communication)
        self.verticalLayout_comm.setObjectName(u"verticalLayout_comm")
        self.verticalLayout_comm.setContentsMargins(10, 10, 10, 10)
        self.groupBox_primary_channel = QGroupBox(self.tab_communication)
        self.groupBox_primary_channel.setObjectName(u"groupBox_primary_channel")
        self.verticalLayout_11 = QVBoxLayout(self.groupBox_primary_channel)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.widget_placeholder_channel_selection = QWidget(self.groupBox_primary_channel)
        self.widget_placeholder_channel_selection.setObjectName(u"widget_placeholder_channel_selection")
        self.verticalLayout_7 = QVBoxLayout(self.widget_placeholder_channel_selection)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")

        self.verticalLayout_11.addWidget(self.widget_placeholder_channel_selection)


        self.verticalLayout_comm.addWidget(self.groupBox_primary_channel)

        self.verticalSpacer_comm = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_comm.addItem(self.verticalSpacer_comm)

        self.tabWidget.addTab(self.tab_communication, "")
        self.tab_categories = QWidget()
        self.tab_categories.setObjectName(u"tab_categories")
        self.verticalLayout_cat = QVBoxLayout(self.tab_categories)
        self.verticalLayout_cat.setObjectName(u"verticalLayout_cat")
        self.verticalLayout_cat.setContentsMargins(10, 10, 10, 10)
        self.groupBox_select_categories = QGroupBox(self.tab_categories)
        self.groupBox_select_categories.setObjectName(u"groupBox_select_categories")
        self.verticalLayout_3 = QVBoxLayout(self.groupBox_select_categories)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.widget_placeholder_select_categories = QWidget(self.groupBox_select_categories)
        self.widget_placeholder_select_categories.setObjectName(u"widget_placeholder_select_categories")
        self.verticalLayout_10 = QVBoxLayout(self.widget_placeholder_select_categories)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")

        self.verticalLayout_3.addWidget(self.widget_placeholder_select_categories)


        self.verticalLayout_cat.addWidget(self.groupBox_select_categories)

        self.verticalSpacer_cat = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_cat.addItem(self.verticalSpacer_cat)

        self.tabWidget.addTab(self.tab_categories, "")
        self.tab_tasks = QWidget()
        self.tab_tasks.setObjectName(u"tab_tasks")
        self.verticalLayout_tasks = QVBoxLayout(self.tab_tasks)
        self.verticalLayout_tasks.setObjectName(u"verticalLayout_tasks")
        self.verticalLayout_tasks.setContentsMargins(10, 10, 10, 10)
        self.groupBox_task_settings = QGroupBox(self.tab_tasks)
        self.groupBox_task_settings.setObjectName(u"groupBox_task_settings")
        self.verticalLayout_9 = QVBoxLayout(self.groupBox_task_settings)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.widget_placeholder_task_settings = QWidget(self.groupBox_task_settings)
        self.widget_placeholder_task_settings.setObjectName(u"widget_placeholder_task_settings")
        self.verticalLayout_4 = QVBoxLayout(self.widget_placeholder_task_settings)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")

        self.verticalLayout_9.addWidget(self.widget_placeholder_task_settings)


        self.verticalLayout_tasks.addWidget(self.groupBox_task_settings)

        self.tabWidget.addTab(self.tab_tasks, "")
        self.tab_checkins = QWidget()
        self.tab_checkins.setObjectName(u"tab_checkins")
        self.verticalLayout_checkins = QVBoxLayout(self.tab_checkins)
        self.verticalLayout_checkins.setObjectName(u"verticalLayout_checkins")
        self.verticalLayout_checkins.setContentsMargins(10, 10, 10, 10)
        self.groupBox_checkin_settings = QGroupBox(self.tab_checkins)
        self.groupBox_checkin_settings.setObjectName(u"groupBox_checkin_settings")
        self.verticalLayout_8 = QVBoxLayout(self.groupBox_checkin_settings)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.widget_placeholder_checkin_settings = QWidget(self.groupBox_checkin_settings)
        self.widget_placeholder_checkin_settings.setObjectName(u"widget_placeholder_checkin_settings")
        self.verticalLayout_5 = QVBoxLayout(self.widget_placeholder_checkin_settings)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")

        self.verticalLayout_8.addWidget(self.widget_placeholder_checkin_settings)


        self.verticalLayout_checkins.addWidget(self.groupBox_checkin_settings)

        self.tabWidget.addTab(self.tab_checkins, "")

        self.verticalLayout.addWidget(self.tabWidget)

        self.horizontalLayout_buttons = QHBoxLayout()
        self.horizontalLayout_buttons.setObjectName(u"horizontalLayout_buttons")
        self.pushButton_profile = QPushButton(Dialog_create_account)
        self.pushButton_profile.setObjectName(u"pushButton_profile")

        self.horizontalLayout_buttons.addWidget(self.pushButton_profile)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_buttons.addItem(self.horizontalSpacer)

        self.buttonBox_save_cancel = QDialogButtonBox(Dialog_create_account)
        self.buttonBox_save_cancel.setObjectName(u"buttonBox_save_cancel")
        self.buttonBox_save_cancel.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox_save_cancel.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save)

        self.horizontalLayout_buttons.addWidget(self.buttonBox_save_cancel)


        self.verticalLayout.addLayout(self.horizontalLayout_buttons)

        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(Dialog_create_account)
        self.buttonBox_save_cancel.accepted.connect(Dialog_create_account.accept)
        self.buttonBox_save_cancel.rejected.connect(Dialog_create_account.reject)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Dialog_create_account)
    # setupUi

    def retranslateUi(self, Dialog_create_account):
        Dialog_create_account.setWindowTitle(QCoreApplication.translate("Dialog_create_account", u"Create a New Account", None))
        Dialog_create_account.setProperty(u"role", QCoreApplication.translate("Dialog_create_account", u"header", None))
        self.label_create_a_new_account.setText(QCoreApplication.translate("Dialog_create_account", u"Create a New Account", None))
        self.label_create_a_new_account.setProperty(u"role", QCoreApplication.translate("Dialog_create_account", u"header", None))
        self.groupBox_basic_information.setTitle(QCoreApplication.translate("Dialog_create_account", u"Account Details", None))
        self.label_username.setText(QCoreApplication.translate("Dialog_create_account", u"Username:", None))
        self.label_prefered_name.setText(QCoreApplication.translate("Dialog_create_account", u"Preferred Name:", None))
        self.groupBox_features.setTitle(QCoreApplication.translate("Dialog_create_account", u"Features", None))
        self.checkBox_enable_messages.setText(QCoreApplication.translate("Dialog_create_account", u"Enable Automated Messages", None))
        self.checkBox_enable_task_management.setText(QCoreApplication.translate("Dialog_create_account", u"Enable Task Management", None))
        self.checkBox_enable_checkins.setText(QCoreApplication.translate("Dialog_create_account", u"Enable Check-ins", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_basic_info), QCoreApplication.translate("Dialog_create_account", u"Basic Information", None))
        self.groupBox_primary_channel.setTitle(QCoreApplication.translate("Dialog_create_account", u"Primary Communication Channel", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_communication), QCoreApplication.translate("Dialog_create_account", u"Communication", None))
        self.groupBox_select_categories.setTitle(QCoreApplication.translate("Dialog_create_account", u"Select Message Categories (at least one required)", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_categories), QCoreApplication.translate("Dialog_create_account", u"Messages", None))
        self.groupBox_task_settings.setTitle(QCoreApplication.translate("Dialog_create_account", u"Task Management Settings", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_tasks), QCoreApplication.translate("Dialog_create_account", u"Tasks", None))
        self.groupBox_checkin_settings.setTitle(QCoreApplication.translate("Dialog_create_account", u"Check-in Settings", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_checkins), QCoreApplication.translate("Dialog_create_account", u"Check-ins", None))
        self.pushButton_profile.setText(QCoreApplication.translate("Dialog_create_account", u"Setup Profile (Optional)", None))
    # retranslateUi

