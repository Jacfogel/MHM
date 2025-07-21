# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'task_management_dialog.ui'
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
    QGridLayout, QGroupBox, QLabel, QSizePolicy,
    QVBoxLayout, QWidget)

def qtTrId(id): return id

class Ui_Dialog_task_management(object):
    def setupUi(self, Dialog_task_management):
        """Auto-generated Qt UI setup function for task_management_dialog."""
        if not Dialog_task_management.objectName():
            Dialog_task_management.setObjectName(u"Dialog_task_management")
        Dialog_task_management.resize(950, 601)
        self.verticalLayout_Dialog_task_management = QVBoxLayout(Dialog_task_management)
        self.verticalLayout_Dialog_task_management.setObjectName(u"verticalLayout_Dialog_task_management")
        self.label_task_management = QLabel(Dialog_task_management)
        self.label_task_management.setObjectName(u"label_task_management")
        self.label_task_management.setMinimumSize(QSize(0, 0))

        self.verticalLayout_Dialog_task_management.addWidget(self.label_task_management)

        self.groupBox_checkBox_enable_task_management = QGroupBox(Dialog_task_management)
        self.groupBox_checkBox_enable_task_management.setObjectName(u"groupBox_checkBox_enable_task_management")
        self.groupBox_checkBox_enable_task_management.setCheckable(True)
        self.groupBox_checkBox_enable_task_management.setChecked(False)
        self.verticalLayout_groupBox_checkBox_enable_task_management = QVBoxLayout(self.groupBox_checkBox_enable_task_management)
        self.verticalLayout_groupBox_checkBox_enable_task_management.setObjectName(u"verticalLayout_groupBox_checkBox_enable_task_management")
        self.widget_placeholder_task_settings = QWidget(self.groupBox_checkBox_enable_task_management)
        self.widget_placeholder_task_settings.setObjectName(u"widget_placeholder_task_settings")
        self.verticalLayout_widget_placeholder_task_settings = QVBoxLayout(self.widget_placeholder_task_settings)
        self.verticalLayout_widget_placeholder_task_settings.setSpacing(2)
        self.verticalLayout_widget_placeholder_task_settings.setObjectName(u"verticalLayout_widget_placeholder_task_settings")
        self.verticalLayout_widget_placeholder_task_settings.setContentsMargins(2, 2, 2, 2)

        self.verticalLayout_groupBox_checkBox_enable_task_management.addWidget(self.widget_placeholder_task_settings)


        self.verticalLayout_Dialog_task_management.addWidget(self.groupBox_checkBox_enable_task_management)

        self.groupBox_task_stats = QGroupBox(Dialog_task_management)
        self.groupBox_task_stats.setObjectName(u"groupBox_task_stats")
        self.gridLayout = QGridLayout(self.groupBox_task_stats)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_completed_tasks = QLabel(self.groupBox_task_stats)
        self.label_completed_tasks.setObjectName(u"label_completed_tasks")
        self.label_completed_tasks.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.label_completed_tasks, 1, 0, 1, 1)

        self.label_active_tasks = QLabel(self.groupBox_task_stats)
        self.label_active_tasks.setObjectName(u"label_active_tasks")
        self.label_active_tasks.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.label_active_tasks, 2, 0, 1, 1)

        self.label_total_tasks = QLabel(self.groupBox_task_stats)
        self.label_total_tasks.setObjectName(u"label_total_tasks")
        self.label_total_tasks.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.label_total_tasks, 0, 0, 1, 1)


        self.verticalLayout_Dialog_task_management.addWidget(self.groupBox_task_stats)

        self.buttonBox_save_cancel = QDialogButtonBox(Dialog_task_management)
        self.buttonBox_save_cancel.setObjectName(u"buttonBox_save_cancel")
        self.buttonBox_save_cancel.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox_save_cancel.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save)

        self.verticalLayout_Dialog_task_management.addWidget(self.buttonBox_save_cancel)

        self.verticalLayout_Dialog_task_management.setStretch(1, 1)

        self.retranslateUi(Dialog_task_management)

        QMetaObject.connectSlotsByName(Dialog_task_management)
    # setupUi

    def retranslateUi(self, Dialog_task_management):
        """Auto-generated Qt UI translation function for task_management_dialog."""
        Dialog_task_management.setWindowTitle(QCoreApplication.translate("Dialog_task_management", u"Dialog", None))
        self.label_task_management.setText(QCoreApplication.translate("Dialog_task_management", u"Task Management", None))
        self.label_task_management.setProperty(u"role", QCoreApplication.translate("Dialog_task_management", u"header", None))
        self.groupBox_checkBox_enable_task_management.setTitle(QCoreApplication.translate("Dialog_task_management", u"Enable Task Management", None))
        self.groupBox_task_stats.setTitle(QCoreApplication.translate("Dialog_task_management", u"Task Statistics", None))
        self.label_completed_tasks.setText(QCoreApplication.translate("Dialog_task_management", u"Cimpleted Tasks:", None))
        self.label_active_tasks.setText(QCoreApplication.translate("Dialog_task_management", u"Total Tasks:", None))
        self.label_total_tasks.setText(QCoreApplication.translate("Dialog_task_management", u"Active Tasks:", None))
    # retranslateUi

