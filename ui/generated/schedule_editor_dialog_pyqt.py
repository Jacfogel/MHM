# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'schedule_editor_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

def qtTrId(id): return id

class Ui_Dialog_edit_schedule(object):
    def setupUi(self, Dialog_edit_schedule):
        if not Dialog_edit_schedule.objectName():
            Dialog_edit_schedule.setObjectName(u"Dialog_edit_schedule")
        Dialog_edit_schedule.resize(950, 330)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog_edit_schedule.sizePolicy().hasHeightForWidth())
        Dialog_edit_schedule.setSizePolicy(sizePolicy)
        Dialog_edit_schedule.setMinimumSize(QSize(0, 100))
        self.verticalLayout = QVBoxLayout(Dialog_edit_schedule)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_EditSchedule = QLabel(Dialog_edit_schedule)
        self.label_EditSchedule.setObjectName(u"label_EditSchedule")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_EditSchedule.sizePolicy().hasHeightForWidth())
        self.label_EditSchedule.setSizePolicy(sizePolicy1)
        self.label_EditSchedule.setMinimumSize(QSize(0, 0))

        self.verticalLayout.addWidget(self.label_EditSchedule)

        self.groupBox_time_periods = QGroupBox(Dialog_edit_schedule)
        self.groupBox_time_periods.setObjectName(u"groupBox_time_periods")
        sizePolicy.setHeightForWidth(self.groupBox_time_periods.sizePolicy().hasHeightForWidth())
        self.groupBox_time_periods.setSizePolicy(sizePolicy)
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_time_periods)
        self.verticalLayout_2.setSpacing(4)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(4, 4, 4, 4)
        self.scrollArea_time_periods = QScrollArea(self.groupBox_time_periods)
        self.scrollArea_time_periods.setObjectName(u"scrollArea_time_periods")
        sizePolicy.setHeightForWidth(self.scrollArea_time_periods.sizePolicy().hasHeightForWidth())
        self.scrollArea_time_periods.setSizePolicy(sizePolicy)
        self.scrollArea_time_periods.setWidgetResizable(True)
        self.scrollAreaWidgetContents_periods = QWidget()
        self.scrollAreaWidgetContents_periods.setObjectName(u"scrollAreaWidgetContents_periods")
        self.scrollAreaWidgetContents_periods.setGeometry(QRect(0, 0, 916, 103))
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetContents_periods.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents_periods.setSizePolicy(sizePolicy)
        self.verticalLayout_3 = QVBoxLayout(self.scrollAreaWidgetContents_periods)
        self.verticalLayout_3.setSpacing(4)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(4, 4, 4, 4)
        self.scrollArea_time_periods.setWidget(self.scrollAreaWidgetContents_periods)

        self.verticalLayout_2.addWidget(self.scrollArea_time_periods)


        self.verticalLayout.addWidget(self.groupBox_time_periods)

        self.widget_buttons = QWidget(Dialog_edit_schedule)
        self.widget_buttons.setObjectName(u"widget_buttons")
        self.horizontalLayout = QHBoxLayout(self.widget_buttons)
        self.horizontalLayout.setSpacing(4)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(4, 4, 4, 4)
        self.pushButton_add_new_period = QPushButton(self.widget_buttons)
        self.pushButton_add_new_period.setObjectName(u"pushButton_add_new_period")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.pushButton_add_new_period.sizePolicy().hasHeightForWidth())
        self.pushButton_add_new_period.setSizePolicy(sizePolicy2)

        self.horizontalLayout.addWidget(self.pushButton_add_new_period)

        self.pushButton_undo_last__time_period_delete = QPushButton(self.widget_buttons)
        self.pushButton_undo_last__time_period_delete.setObjectName(u"pushButton_undo_last__time_period_delete")
        sizePolicy2.setHeightForWidth(self.pushButton_undo_last__time_period_delete.sizePolicy().hasHeightForWidth())
        self.pushButton_undo_last__time_period_delete.setSizePolicy(sizePolicy2)

        self.horizontalLayout.addWidget(self.pushButton_undo_last__time_period_delete)


        self.verticalLayout.addWidget(self.widget_buttons, 0, Qt.AlignmentFlag.AlignLeft)

        self.buttonBox_save_cancel = QDialogButtonBox(Dialog_edit_schedule)
        self.buttonBox_save_cancel.setObjectName(u"buttonBox_save_cancel")
        self.buttonBox_save_cancel.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox_save_cancel.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save)

        self.verticalLayout.addWidget(self.buttonBox_save_cancel)

        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(Dialog_edit_schedule)
        self.buttonBox_save_cancel.accepted.connect(Dialog_edit_schedule.accept)
        self.buttonBox_save_cancel.rejected.connect(Dialog_edit_schedule.reject)

        QMetaObject.connectSlotsByName(Dialog_edit_schedule)
    # setupUi

    def retranslateUi(self, Dialog_edit_schedule):
        Dialog_edit_schedule.setWindowTitle(QCoreApplication.translate("Dialog_edit_schedule", u"Dialog", None))
        self.label_EditSchedule.setText(QCoreApplication.translate("Dialog_edit_schedule", u"Edit Schedule", None))
        self.label_EditSchedule.setProperty(u"role", QCoreApplication.translate("Dialog_edit_schedule", u"header", None))
        self.groupBox_time_periods.setTitle(QCoreApplication.translate("Dialog_edit_schedule", u"Time Periods", None))
        self.pushButton_add_new_period.setText(QCoreApplication.translate("Dialog_edit_schedule", u"Add New Period", None))
        self.pushButton_undo_last__time_period_delete.setText(QCoreApplication.translate("Dialog_edit_schedule", u"Undo Last Delete", None))
    # retranslateUi

