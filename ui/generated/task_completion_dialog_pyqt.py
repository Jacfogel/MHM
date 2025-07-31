# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'task_completion_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDateEdit,
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QLabel, QRadioButton, QSizePolicy, QTextEdit,
    QVBoxLayout, QWidget)

class Ui_Dialog_task_completion(object):
    def setupUi(self, Dialog_task_completion):
        if not Dialog_task_completion.objectName():
            Dialog_task_completion.setObjectName(u"Dialog_task_completion")
        Dialog_task_completion.resize(400, 300)
        self.verticalLayout_Dialog_task_completion = QVBoxLayout(Dialog_task_completion)
        self.verticalLayout_Dialog_task_completion.setObjectName(u"verticalLayout_Dialog_task_completion")
        self.label_task_completion_header = QLabel(Dialog_task_completion)
        self.label_task_completion_header.setObjectName(u"label_task_completion_header")

        self.verticalLayout_Dialog_task_completion.addWidget(self.label_task_completion_header)

        self.widget_completion_details = QWidget(Dialog_task_completion)
        self.widget_completion_details.setObjectName(u"widget_completion_details")
        self.formLayout_completion_details = QFormLayout(self.widget_completion_details)
        self.formLayout_completion_details.setObjectName(u"formLayout_completion_details")
        self.label_completion_date = QLabel(self.widget_completion_details)
        self.label_completion_date.setObjectName(u"label_completion_date")

        self.formLayout_completion_details.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_completion_date)

        self.dateEdit_completion_date = QDateEdit(self.widget_completion_details)
        self.dateEdit_completion_date.setObjectName(u"dateEdit_completion_date")
        self.dateEdit_completion_date.setCalendarPopup(True)

        self.formLayout_completion_details.setWidget(0, QFormLayout.ItemRole.FieldRole, self.dateEdit_completion_date)

        self.label_completion_time = QLabel(self.widget_completion_details)
        self.label_completion_time.setObjectName(u"label_completion_time")

        self.formLayout_completion_details.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_completion_time)

        self.widget_completion_time = QWidget(self.widget_completion_details)
        self.widget_completion_time.setObjectName(u"widget_completion_time")
        self.horizontalLayout_completion_time = QHBoxLayout(self.widget_completion_time)
        self.horizontalLayout_completion_time.setObjectName(u"horizontalLayout_completion_time")
        self.comboBox_completion_hour = QComboBox(self.widget_completion_time)
        self.comboBox_completion_hour.setObjectName(u"comboBox_completion_hour")

        self.horizontalLayout_completion_time.addWidget(self.comboBox_completion_hour)

        self.label_completion_colon = QLabel(self.widget_completion_time)
        self.label_completion_colon.setObjectName(u"label_completion_colon")

        self.horizontalLayout_completion_time.addWidget(self.label_completion_colon)

        self.comboBox_completion_minute = QComboBox(self.widget_completion_time)
        self.comboBox_completion_minute.setObjectName(u"comboBox_completion_minute")

        self.horizontalLayout_completion_time.addWidget(self.comboBox_completion_minute)

        self.widget_completion_am_pm = QWidget(self.widget_completion_time)
        self.widget_completion_am_pm.setObjectName(u"widget_completion_am_pm")
        self.verticalLayout_completion_am_pm = QVBoxLayout(self.widget_completion_am_pm)
        self.verticalLayout_completion_am_pm.setSpacing(2)
        self.verticalLayout_completion_am_pm.setObjectName(u"verticalLayout_completion_am_pm")
        self.verticalLayout_completion_am_pm.setContentsMargins(2, 2, 2, 2)
        self.radioButton_completion_am = QRadioButton(self.widget_completion_am_pm)
        self.radioButton_completion_am.setObjectName(u"radioButton_completion_am")

        self.verticalLayout_completion_am_pm.addWidget(self.radioButton_completion_am)

        self.radioButton_completion_pm = QRadioButton(self.widget_completion_am_pm)
        self.radioButton_completion_pm.setObjectName(u"radioButton_completion_pm")

        self.verticalLayout_completion_am_pm.addWidget(self.radioButton_completion_pm)


        self.horizontalLayout_completion_time.addWidget(self.widget_completion_am_pm)


        self.formLayout_completion_details.setWidget(1, QFormLayout.ItemRole.FieldRole, self.widget_completion_time)

        self.label_completion_notes = QLabel(self.widget_completion_details)
        self.label_completion_notes.setObjectName(u"label_completion_notes")

        self.formLayout_completion_details.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_completion_notes)

        self.textEdit_completion_notes = QTextEdit(self.widget_completion_details)
        self.textEdit_completion_notes.setObjectName(u"textEdit_completion_notes")
        self.textEdit_completion_notes.setMaximumSize(QSize(16777215, 80))

        self.formLayout_completion_details.setWidget(2, QFormLayout.ItemRole.FieldRole, self.textEdit_completion_notes)


        self.verticalLayout_Dialog_task_completion.addWidget(self.widget_completion_details)

        self.buttonBox_task_completion = QDialogButtonBox(Dialog_task_completion)
        self.buttonBox_task_completion.setObjectName(u"buttonBox_task_completion")
        self.buttonBox_task_completion.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox_task_completion.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout_Dialog_task_completion.addWidget(self.buttonBox_task_completion)


        self.retranslateUi(Dialog_task_completion)

        QMetaObject.connectSlotsByName(Dialog_task_completion)
    # setupUi

    def retranslateUi(self, Dialog_task_completion):
        Dialog_task_completion.setWindowTitle(QCoreApplication.translate("Dialog_task_completion", u"Complete Task", None))
        self.label_task_completion_header.setText(QCoreApplication.translate("Dialog_task_completion", u"When did you complete this task?", None))
        self.label_task_completion_header.setProperty(u"role", QCoreApplication.translate("Dialog_task_completion", u"header", None))
        self.label_completion_date.setText(QCoreApplication.translate("Dialog_task_completion", u"Completion Date:", None))
        self.label_completion_time.setText(QCoreApplication.translate("Dialog_task_completion", u"Completion Time:", None))
        self.label_completion_colon.setText(QCoreApplication.translate("Dialog_task_completion", u":", None))
        self.radioButton_completion_am.setText(QCoreApplication.translate("Dialog_task_completion", u"AM", None))
        self.radioButton_completion_pm.setText(QCoreApplication.translate("Dialog_task_completion", u"PM", None))
        self.label_completion_notes.setText(QCoreApplication.translate("Dialog_task_completion", u"Notes (Optional):", None))
        self.textEdit_completion_notes.setPlaceholderText(QCoreApplication.translate("Dialog_task_completion", u"Add any notes about task completion...", None))
    # retranslateUi

