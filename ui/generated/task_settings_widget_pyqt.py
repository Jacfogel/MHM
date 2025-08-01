# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'task_settings_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QPushButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

class Ui_Form_task_settings(object):
    def setupUi(self, Form_task_settings):
        if not Form_task_settings.objectName():
            Form_task_settings.setObjectName(u"Form_task_settings")
        Form_task_settings.resize(950, 524)
        self.verticalLayout_Form_task_settings = QVBoxLayout(Form_task_settings)
        self.verticalLayout_Form_task_settings.setObjectName(u"verticalLayout_Form_task_settings")
        self.groupBox_task_reminder_time_periods = QGroupBox(Form_task_settings)
        self.groupBox_task_reminder_time_periods.setObjectName(u"groupBox_task_reminder_time_periods")
        self.verticalLayout_groupBox_task_reminder_time_periods = QVBoxLayout(self.groupBox_task_reminder_time_periods)
        self.verticalLayout_groupBox_task_reminder_time_periods.setSpacing(2)
        self.verticalLayout_groupBox_task_reminder_time_periods.setObjectName(u"verticalLayout_groupBox_task_reminder_time_periods")
        self.verticalLayout_groupBox_task_reminder_time_periods.setContentsMargins(2, 2, 2, 2)
        self.scrollArea_task_reminder_time_periods = QScrollArea(self.groupBox_task_reminder_time_periods)
        self.scrollArea_task_reminder_time_periods.setObjectName(u"scrollArea_task_reminder_time_periods")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea_task_reminder_time_periods.sizePolicy().hasHeightForWidth())
        self.scrollArea_task_reminder_time_periods.setSizePolicy(sizePolicy)
        self.scrollArea_task_reminder_time_periods.setWidgetResizable(True)
        self.scrollAreaWidgetContents_task_reminder_time_periods = QWidget()
        self.scrollAreaWidgetContents_task_reminder_time_periods.setObjectName(u"scrollAreaWidgetContents_task_reminder_time_periods")
        self.scrollAreaWidgetContents_task_reminder_time_periods.setGeometry(QRect(0, 0, 920, 441))
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetContents_task_reminder_time_periods.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents_task_reminder_time_periods.setSizePolicy(sizePolicy)
        self.verticalLayout_scrollAreaWidgetContents_task_reminder_time_periods = QVBoxLayout(self.scrollAreaWidgetContents_task_reminder_time_periods)
        self.verticalLayout_scrollAreaWidgetContents_task_reminder_time_periods.setSpacing(4)
        self.verticalLayout_scrollAreaWidgetContents_task_reminder_time_periods.setObjectName(u"verticalLayout_scrollAreaWidgetContents_task_reminder_time_periods")
        self.verticalLayout_scrollAreaWidgetContents_task_reminder_time_periods.setContentsMargins(4, 4, 4, 4)
        self.scrollArea_task_reminder_time_periods.setWidget(self.scrollAreaWidgetContents_task_reminder_time_periods)

        self.verticalLayout_groupBox_task_reminder_time_periods.addWidget(self.scrollArea_task_reminder_time_periods)

        self.widget_task_reminder_time_period_buttons = QWidget(self.groupBox_task_reminder_time_periods)
        self.widget_task_reminder_time_period_buttons.setObjectName(u"widget_task_reminder_time_period_buttons")
        self.horizontalLayout_widget_task_reminder_time_period_buttons = QHBoxLayout(self.widget_task_reminder_time_period_buttons)
        self.horizontalLayout_widget_task_reminder_time_period_buttons.setSpacing(4)
        self.horizontalLayout_widget_task_reminder_time_period_buttons.setObjectName(u"horizontalLayout_widget_task_reminder_time_period_buttons")
        self.horizontalLayout_widget_task_reminder_time_period_buttons.setContentsMargins(4, 4, 4, 4)
        self.pushButton_task_reminder_add_new_period = QPushButton(self.widget_task_reminder_time_period_buttons)
        self.pushButton_task_reminder_add_new_period.setObjectName(u"pushButton_task_reminder_add_new_period")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.pushButton_task_reminder_add_new_period.sizePolicy().hasHeightForWidth())
        self.pushButton_task_reminder_add_new_period.setSizePolicy(sizePolicy1)

        self.horizontalLayout_widget_task_reminder_time_period_buttons.addWidget(self.pushButton_task_reminder_add_new_period)

        self.pushButton_undo_last__task_reminder_time_period_delete = QPushButton(self.widget_task_reminder_time_period_buttons)
        self.pushButton_undo_last__task_reminder_time_period_delete.setObjectName(u"pushButton_undo_last__task_reminder_time_period_delete")
        sizePolicy1.setHeightForWidth(self.pushButton_undo_last__task_reminder_time_period_delete.sizePolicy().hasHeightForWidth())
        self.pushButton_undo_last__task_reminder_time_period_delete.setSizePolicy(sizePolicy1)

        self.horizontalLayout_widget_task_reminder_time_period_buttons.addWidget(self.pushButton_undo_last__task_reminder_time_period_delete)


        self.verticalLayout_groupBox_task_reminder_time_periods.addWidget(self.widget_task_reminder_time_period_buttons, 0, Qt.AlignmentFlag.AlignLeft)

        self.verticalLayout_groupBox_task_reminder_time_periods.setStretch(0, 1)

        self.verticalLayout_Form_task_settings.addWidget(self.groupBox_task_reminder_time_periods)

        self.widget_tag_management_placeholder = QWidget(Form_task_settings)
        self.widget_tag_management_placeholder.setObjectName(u"widget_tag_management_placeholder")
        sizePolicy.setHeightForWidth(self.widget_tag_management_placeholder.sizePolicy().hasHeightForWidth())
        self.widget_tag_management_placeholder.setSizePolicy(sizePolicy)
        self.verticalLayout_widget_tag_management_placeholder = QVBoxLayout(self.widget_tag_management_placeholder)
        self.verticalLayout_widget_tag_management_placeholder.setSpacing(4)
        self.verticalLayout_widget_tag_management_placeholder.setObjectName(u"verticalLayout_widget_tag_management_placeholder")
        self.verticalLayout_widget_tag_management_placeholder.setContentsMargins(4, 4, 4, 4)

        self.verticalLayout_Form_task_settings.addWidget(self.widget_tag_management_placeholder)


        self.retranslateUi(Form_task_settings)

        QMetaObject.connectSlotsByName(Form_task_settings)
    # setupUi

    def retranslateUi(self, Form_task_settings):
        Form_task_settings.setWindowTitle(QCoreApplication.translate("Form_task_settings", u"Form", None))
        self.groupBox_task_reminder_time_periods.setTitle(QCoreApplication.translate("Form_task_settings", u"Reminder Time Periods", None))
        self.pushButton_task_reminder_add_new_period.setText(QCoreApplication.translate("Form_task_settings", u"Add New Period", None))
        self.pushButton_undo_last__task_reminder_time_period_delete.setText(QCoreApplication.translate("Form_task_settings", u"Undo Last Delete", None))
    # retranslateUi

