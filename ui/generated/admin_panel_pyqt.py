# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'admin_panel.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QGroupBox,
    QLabel, QMainWindow, QMenu, QMenuBar,
    QPushButton, QSizePolicy, QStatusBar, QVBoxLayout,
    QWidget)

class Ui_ui_app_mainwindow(object):
    def setupUi(self, ui_app_mainwindow):
        if not ui_app_mainwindow.objectName():
            ui_app_mainwindow.setObjectName(u"ui_app_mainwindow")
        ui_app_mainwindow.resize(879, 711)
        self.actionToggle_Verbose_Logging = QAction(ui_app_mainwindow)
        self.actionToggle_Verbose_Logging.setObjectName(u"actionToggle_Verbose_Logging")
        self.actionView_Log_File = QAction(ui_app_mainwindow)
        self.actionView_Log_File.setObjectName(u"actionView_Log_File")
        self.actionView_Cache_Status = QAction(ui_app_mainwindow)
        self.actionView_Cache_Status.setObjectName(u"actionView_Cache_Status")
        self.actionForce_Clean_Cache = QAction(ui_app_mainwindow)
        self.actionForce_Clean_Cache.setObjectName(u"actionForce_Clean_Cache")
        self.actionValidate_Configuration = QAction(ui_app_mainwindow)
        self.actionValidate_Configuration.setObjectName(u"actionValidate_Configuration")
        self.actionView_All_Users = QAction(ui_app_mainwindow)
        self.actionView_All_Users.setObjectName(u"actionView_All_Users")
        self.actionSystem_Health_Check = QAction(ui_app_mainwindow)
        self.actionSystem_Health_Check.setObjectName(u"actionSystem_Health_Check")
        self.centralwidget = QWidget(ui_app_mainwindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_mhm_admin_panel = QLabel(self.centralwidget)
        self.label_mhm_admin_panel.setObjectName(u"label_mhm_admin_panel")
        self.label_mhm_admin_panel.setMinimumSize(QSize(0, 0))

        self.verticalLayout.addWidget(self.label_mhm_admin_panel)

        self.groupBox_server_management = QGroupBox(self.centralwidget)
        self.groupBox_server_management.setObjectName(u"groupBox_server_management")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_server_management)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(5, 9, -1, -1)
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.pushButton_start_service = QPushButton(self.groupBox_server_management)
        self.pushButton_start_service.setObjectName(u"pushButton_start_service")

        self.gridLayout.addWidget(self.pushButton_start_service, 1, 0, 1, 1)

        self.pushButton_stop_service = QPushButton(self.groupBox_server_management)
        self.pushButton_stop_service.setObjectName(u"pushButton_stop_service")

        self.gridLayout.addWidget(self.pushButton_stop_service, 1, 1, 1, 1)

        self.pushButton_restart_service = QPushButton(self.groupBox_server_management)
        self.pushButton_restart_service.setObjectName(u"pushButton_restart_service")

        self.gridLayout.addWidget(self.pushButton_restart_service, 1, 2, 1, 1)

        self.pushButton_refresh_server_status = QPushButton(self.groupBox_server_management)
        self.pushButton_refresh_server_status.setObjectName(u"pushButton_refresh_server_status")

        self.gridLayout.addWidget(self.pushButton_refresh_server_status, 1, 3, 1, 1)

        self.pushButton_run_scheduler = QPushButton(self.groupBox_server_management)
        self.pushButton_run_scheduler.setObjectName(u"pushButton_run_scheduler")

        self.gridLayout.addWidget(self.pushButton_run_scheduler, 2, 0, 1, 1)

        self.label_service_status = QLabel(self.groupBox_server_management)
        self.label_service_status.setObjectName(u"label_service_status")

        self.gridLayout.addWidget(self.label_service_status, 0, 0, 1, 4)


        self.verticalLayout_2.addLayout(self.gridLayout)


        self.verticalLayout.addWidget(self.groupBox_server_management)

        self.pushButton_create_new_user = QPushButton(self.centralwidget)
        self.pushButton_create_new_user.setObjectName(u"pushButton_create_new_user")

        self.verticalLayout.addWidget(self.pushButton_create_new_user)

        self.groupBox_user_management = QGroupBox(self.centralwidget)
        self.groupBox_user_management.setObjectName(u"groupBox_user_management")
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_user_management)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.comboBox_users = QComboBox(self.groupBox_user_management)
        self.comboBox_users.setObjectName(u"comboBox_users")

        self.gridLayout_3.addWidget(self.comboBox_users, 0, 2, 1, 2)

        self.label_select_user = QLabel(self.groupBox_user_management)
        self.label_select_user.setObjectName(u"label_select_user")
        self.label_select_user.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.label_select_user.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_3.addWidget(self.label_select_user, 0, 0, 1, 1)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.pushButton_communication_settings = QPushButton(self.groupBox_user_management)
        self.pushButton_communication_settings.setObjectName(u"pushButton_communication_settings")
        self.pushButton_communication_settings.setCursor(QCursor(Qt.CursorShape.SizeBDiagCursor))
        self.pushButton_communication_settings.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.pushButton_communication_settings.setToolTipDuration(-7)
        self.pushButton_communication_settings.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        self.gridLayout_2.addWidget(self.pushButton_communication_settings, 0, 0, 1, 1)

        self.pushButton_personalization = QPushButton(self.groupBox_user_management)
        self.pushButton_personalization.setObjectName(u"pushButton_personalization")

        self.gridLayout_2.addWidget(self.pushButton_personalization, 0, 1, 1, 1)

        self.pushButton_category_management = QPushButton(self.groupBox_user_management)
        self.pushButton_category_management.setObjectName(u"pushButton_category_management")

        self.gridLayout_2.addWidget(self.pushButton_category_management, 0, 2, 1, 1)

        self.pushButton_checkin_settings = QPushButton(self.groupBox_user_management)
        self.pushButton_checkin_settings.setObjectName(u"pushButton_checkin_settings")

        self.gridLayout_2.addWidget(self.pushButton_checkin_settings, 1, 0, 1, 1)

        self.pushButton_task_management = QPushButton(self.groupBox_user_management)
        self.pushButton_task_management.setObjectName(u"pushButton_task_management")

        self.gridLayout_2.addWidget(self.pushButton_task_management, 1, 1, 1, 1)

        self.pushButton_task_crud = QPushButton(self.groupBox_user_management)
        self.pushButton_task_crud.setObjectName(u"pushButton_task_crud")

        self.gridLayout_2.addWidget(self.pushButton_task_crud, 1, 2, 1, 1)

        self.pushButton_run_user_scheduler = QPushButton(self.groupBox_user_management)
        self.pushButton_run_user_scheduler.setObjectName(u"pushButton_run_user_scheduler")

        self.gridLayout_2.addWidget(self.pushButton_run_user_scheduler, 2, 0, 1, 3)


        self.gridLayout_3.addLayout(self.gridLayout_2, 2, 0, 2, 4)


        self.verticalLayout_4.addLayout(self.gridLayout_3)

        self.groupBox_category_actions = QGroupBox(self.groupBox_user_management)
        self.groupBox_category_actions.setObjectName(u"groupBox_category_actions")
        self.verticalLayout_5 = QVBoxLayout(self.groupBox_category_actions)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.pushButton_send_test_message = QPushButton(self.groupBox_category_actions)
        self.pushButton_send_test_message.setObjectName(u"pushButton_send_test_message")

        self.gridLayout_4.addWidget(self.pushButton_send_test_message, 1, 2, 1, 1)

        self.label_select_category = QLabel(self.groupBox_category_actions)
        self.label_select_category.setObjectName(u"label_select_category")
        self.label_select_category.setToolTipDuration(-2)
        self.label_select_category.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.label_select_category.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_4.addWidget(self.label_select_category, 0, 0, 1, 1)

        self.pushButton_edit_messages = QPushButton(self.groupBox_category_actions)
        self.pushButton_edit_messages.setObjectName(u"pushButton_edit_messages")

        self.gridLayout_4.addWidget(self.pushButton_edit_messages, 1, 1, 1, 1)

        self.comboBox_user_categories = QComboBox(self.groupBox_category_actions)
        self.comboBox_user_categories.setObjectName(u"comboBox_user_categories")

        self.gridLayout_4.addWidget(self.comboBox_user_categories, 0, 2, 1, 2)

        self.pushButton_edit_schedules = QPushButton(self.groupBox_category_actions)
        self.pushButton_edit_schedules.setObjectName(u"pushButton_edit_schedules")

        self.gridLayout_4.addWidget(self.pushButton_edit_schedules, 1, 0, 1, 1)

        self.pushButton_run_category_scheduler = QPushButton(self.groupBox_category_actions)
        self.pushButton_run_category_scheduler.setObjectName(u"pushButton_run_category_scheduler")

        self.gridLayout_4.addWidget(self.pushButton_run_category_scheduler, 2, 0, 1, 3)


        self.verticalLayout_5.addLayout(self.gridLayout_4)


        self.verticalLayout_4.addWidget(self.groupBox_category_actions)


        self.verticalLayout.addWidget(self.groupBox_user_management)

        ui_app_mainwindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(ui_app_mainwindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 879, 21))
        self.menuDebug = QMenu(self.menubar)
        self.menuDebug.setObjectName(u"menuDebug")
        self.menuCache_Management = QMenu(self.menuDebug)
        self.menuCache_Management.setObjectName(u"menuCache_Management")
        self.menuAdmin = QMenu(self.menubar)
        self.menuAdmin.setObjectName(u"menuAdmin")
        ui_app_mainwindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(ui_app_mainwindow)
        self.statusbar.setObjectName(u"statusbar")
        ui_app_mainwindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuDebug.menuAction())
        self.menubar.addAction(self.menuAdmin.menuAction())
        self.menuDebug.addAction(self.actionToggle_Verbose_Logging)
        self.menuDebug.addAction(self.actionView_Log_File)
        self.menuDebug.addAction(self.menuCache_Management.menuAction())
        self.menuCache_Management.addAction(self.actionView_Cache_Status)
        self.menuCache_Management.addAction(self.actionForce_Clean_Cache)
        self.menuAdmin.addAction(self.actionValidate_Configuration)
        self.menuAdmin.addAction(self.actionView_All_Users)
        self.menuAdmin.addAction(self.actionSystem_Health_Check)

        self.retranslateUi(ui_app_mainwindow)

        QMetaObject.connectSlotsByName(ui_app_mainwindow)
    # setupUi

    def retranslateUi(self, ui_app_mainwindow):
        ui_app_mainwindow.setWindowTitle(QCoreApplication.translate("ui_app_mainwindow", u"MainWindow", None))
        self.actionToggle_Verbose_Logging.setText(QCoreApplication.translate("ui_app_mainwindow", u"Toggle Verbose Logging", None))
        self.actionView_Log_File.setText(QCoreApplication.translate("ui_app_mainwindow", u"View Log File", None))
        self.actionView_Cache_Status.setText(QCoreApplication.translate("ui_app_mainwindow", u"View Cache Status", None))
        self.actionForce_Clean_Cache.setText(QCoreApplication.translate("ui_app_mainwindow", u"Force Clean Cache", None))
        self.actionValidate_Configuration.setText(QCoreApplication.translate("ui_app_mainwindow", u"Validate Configuration", None))
        self.actionView_All_Users.setText(QCoreApplication.translate("ui_app_mainwindow", u"View All Users", None))
        self.actionSystem_Health_Check.setText(QCoreApplication.translate("ui_app_mainwindow", u"System Health Check", None))
        self.label_mhm_admin_panel.setText(QCoreApplication.translate("ui_app_mainwindow", u"Motivational Health Messages Admin Panel", None))
        self.label_mhm_admin_panel.setProperty(u"role", QCoreApplication.translate("ui_app_mainwindow", u"header", None))
        self.groupBox_server_management.setTitle(QCoreApplication.translate("ui_app_mainwindow", u"Service Management", None))
        self.pushButton_start_service.setText(QCoreApplication.translate("ui_app_mainwindow", u"Start Service", None))
        self.pushButton_stop_service.setText(QCoreApplication.translate("ui_app_mainwindow", u"Stop Service", None))
        self.pushButton_restart_service.setText(QCoreApplication.translate("ui_app_mainwindow", u"Restart", None))
        self.pushButton_refresh_server_status.setText(QCoreApplication.translate("ui_app_mainwindow", u"Refresh", None))
        self.pushButton_run_scheduler.setText(QCoreApplication.translate("ui_app_mainwindow", u"Run Full Scheduler", None))
        self.label_service_status.setText(QCoreApplication.translate("ui_app_mainwindow", u"Service Status:", None))
        self.pushButton_create_new_user.setText(QCoreApplication.translate("ui_app_mainwindow", u"Create New User", None))
        self.groupBox_user_management.setTitle(QCoreApplication.translate("ui_app_mainwindow", u"User Management", None))
        self.label_select_user.setText(QCoreApplication.translate("ui_app_mainwindow", u"Select User:", None))
        self.pushButton_communication_settings.setText(QCoreApplication.translate("ui_app_mainwindow", u"Communication Settings", None))
        self.pushButton_personalization.setText(QCoreApplication.translate("ui_app_mainwindow", u"Personalization", None))
        self.pushButton_category_management.setText(QCoreApplication.translate("ui_app_mainwindow", u"Category Management", None))
        self.pushButton_checkin_settings.setText(QCoreApplication.translate("ui_app_mainwindow", u"Check-in Settings", None))
        self.pushButton_task_management.setText(QCoreApplication.translate("ui_app_mainwindow", u"Task Management", None))
        self.pushButton_task_crud.setText(QCoreApplication.translate("ui_app_mainwindow", u"Task CRUD", None))
        self.pushButton_run_user_scheduler.setText(QCoreApplication.translate("ui_app_mainwindow", u"Run User Scheduler", None))
        self.groupBox_category_actions.setTitle(QCoreApplication.translate("ui_app_mainwindow", u"Category Actions", None))
        self.pushButton_send_test_message.setText(QCoreApplication.translate("ui_app_mainwindow", u"Send Test Message", None))
        self.label_select_category.setText(QCoreApplication.translate("ui_app_mainwindow", u"Select Category:", None))
        self.pushButton_edit_messages.setText(QCoreApplication.translate("ui_app_mainwindow", u"Edit Messages", None))
        self.pushButton_edit_schedules.setText(QCoreApplication.translate("ui_app_mainwindow", u"Edit Schedules", None))
        self.pushButton_run_category_scheduler.setText(QCoreApplication.translate("ui_app_mainwindow", u"Run Category Scheduler", None))
        self.menuDebug.setTitle(QCoreApplication.translate("ui_app_mainwindow", u"Debug", None))
        self.menuCache_Management.setTitle(QCoreApplication.translate("ui_app_mainwindow", u"Cache Management", None))
        self.menuAdmin.setTitle(QCoreApplication.translate("ui_app_mainwindow", u"Admin", None))
    # retranslateUi

