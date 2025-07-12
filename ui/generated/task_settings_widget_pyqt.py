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

def qtTrId(id): return id

class Ui_Form_task_settings(object):
    def setupUi(self, Form_task_settings):
        if not Form_task_settings.objectName():
            Form_task_settings.setObjectName(u"Form_task_settings")
        Form_task_settings.resize(950, 524)
        self.verticalLayout = QVBoxLayout(Form_task_settings)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBox_reminder_time_periods = QGroupBox(Form_task_settings)
        self.groupBox_reminder_time_periods.setObjectName(u"groupBox_reminder_time_periods")
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_reminder_time_periods)
        self.verticalLayout_4.setSpacing(2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(2, 2, 2, 2)
        self.scrollArea_time_periods = QScrollArea(self.groupBox_reminder_time_periods)
        self.scrollArea_time_periods.setObjectName(u"scrollArea_time_periods")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea_time_periods.sizePolicy().hasHeightForWidth())
        self.scrollArea_time_periods.setSizePolicy(sizePolicy)
        self.scrollArea_time_periods.setWidgetResizable(True)
        self.scrollAreaWidgetContents_periods = QWidget()
        self.scrollAreaWidgetContents_periods.setObjectName(u"scrollAreaWidgetContents_periods")
        self.scrollAreaWidgetContents_periods.setGeometry(QRect(0, 0, 920, 441))
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetContents_periods.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents_periods.setSizePolicy(sizePolicy)
        self.verticalLayout_3 = QVBoxLayout(self.scrollAreaWidgetContents_periods)
        self.verticalLayout_3.setSpacing(4)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(4, 4, 4, 4)
        self.scrollArea_time_periods.setWidget(self.scrollAreaWidgetContents_periods)

        self.verticalLayout_4.addWidget(self.scrollArea_time_periods)

        self.widget_time_period_buttons = QWidget(self.groupBox_reminder_time_periods)
        self.widget_time_period_buttons.setObjectName(u"widget_time_period_buttons")
        self.horizontalLayout = QHBoxLayout(self.widget_time_period_buttons)
        self.horizontalLayout.setSpacing(4)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(4, 4, 4, 4)
        self.pushButton_add_new_period = QPushButton(self.widget_time_period_buttons)
        self.pushButton_add_new_period.setObjectName(u"pushButton_add_new_period")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.pushButton_add_new_period.sizePolicy().hasHeightForWidth())
        self.pushButton_add_new_period.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.pushButton_add_new_period)

        self.pushButton_undo_last__time_period_delete = QPushButton(self.widget_time_period_buttons)
        self.pushButton_undo_last__time_period_delete.setObjectName(u"pushButton_undo_last__time_period_delete")
        sizePolicy1.setHeightForWidth(self.pushButton_undo_last__time_period_delete.sizePolicy().hasHeightForWidth())
        self.pushButton_undo_last__time_period_delete.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.pushButton_undo_last__time_period_delete)


        self.verticalLayout_4.addWidget(self.widget_time_period_buttons, 0, Qt.AlignmentFlag.AlignLeft)

        self.verticalLayout_4.setStretch(0, 1)

        self.verticalLayout.addWidget(self.groupBox_reminder_time_periods)


        self.retranslateUi(Form_task_settings)

        QMetaObject.connectSlotsByName(Form_task_settings)
    # setupUi

    def retranslateUi(self, Form_task_settings):
        Form_task_settings.setWindowTitle(QCoreApplication.translate("Form_task_settings", u"Form", None))
        self.groupBox_reminder_time_periods.setTitle(QCoreApplication.translate("Form_task_settings", u"Reminder Time Periods", None))
        self.pushButton_add_new_period.setText(QCoreApplication.translate("Form_task_settings", u"Add New Period", None))
        self.pushButton_undo_last__time_period_delete.setText(QCoreApplication.translate("Form_task_settings", u"Undo Last Delete", None))
    # retranslateUi

