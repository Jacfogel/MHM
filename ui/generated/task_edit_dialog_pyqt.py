# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'task_edit_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDateEdit, QDialog, QDialogButtonBox, QFormLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton,
    QScrollArea, QSizePolicy, QTextEdit, QTimeEdit,
    QVBoxLayout, QWidget)

class Ui_Dialog_task_edit(object):
    def setupUi(self, Dialog_task_edit):
        if not Dialog_task_edit.objectName():
            Dialog_task_edit.setObjectName(u"Dialog_task_edit")
        Dialog_task_edit.resize(600, 500)
        self.verticalLayout_Dialog_task_edit = QVBoxLayout(Dialog_task_edit)
        self.verticalLayout_Dialog_task_edit.setObjectName(u"verticalLayout_Dialog_task_edit")
        self.label_task_edit_header = QLabel(Dialog_task_edit)
        self.label_task_edit_header.setObjectName(u"label_task_edit_header")
        self.label_task_edit_header.setMinimumSize(QSize(0, 0))

        self.verticalLayout_Dialog_task_edit.addWidget(self.label_task_edit_header)

        self.widget_task_details = QWidget(Dialog_task_edit)
        self.widget_task_details.setObjectName(u"widget_task_details")
        self.formLayout_task_details = QFormLayout(self.widget_task_details)
        self.formLayout_task_details.setObjectName(u"formLayout_task_details")
        self.label_task_title = QLabel(self.widget_task_details)
        self.label_task_title.setObjectName(u"label_task_title")

        self.formLayout_task_details.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_task_title)

        self.lineEdit_task_title = QLineEdit(self.widget_task_details)
        self.lineEdit_task_title.setObjectName(u"lineEdit_task_title")

        self.formLayout_task_details.setWidget(0, QFormLayout.ItemRole.FieldRole, self.lineEdit_task_title)

        self.label_task_description = QLabel(self.widget_task_details)
        self.label_task_description.setObjectName(u"label_task_description")

        self.formLayout_task_details.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_task_description)

        self.textEdit_task_description = QTextEdit(self.widget_task_details)
        self.textEdit_task_description.setObjectName(u"textEdit_task_description")
        self.textEdit_task_description.setMaximumSize(QSize(16777215, 100))

        self.formLayout_task_details.setWidget(1, QFormLayout.ItemRole.FieldRole, self.textEdit_task_description)

        self.label_task_category = QLabel(self.widget_task_details)
        self.label_task_category.setObjectName(u"label_task_category")

        self.formLayout_task_details.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_task_category)

        self.lineEdit_task_category = QLineEdit(self.widget_task_details)
        self.lineEdit_task_category.setObjectName(u"lineEdit_task_category")

        self.formLayout_task_details.setWidget(2, QFormLayout.ItemRole.FieldRole, self.lineEdit_task_category)

        self.label_task_priority = QLabel(self.widget_task_details)
        self.label_task_priority.setObjectName(u"label_task_priority")

        self.formLayout_task_details.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_task_priority)

        self.comboBox_task_priority = QComboBox(self.widget_task_details)
        self.comboBox_task_priority.addItem("")
        self.comboBox_task_priority.addItem("")
        self.comboBox_task_priority.addItem("")
        self.comboBox_task_priority.setObjectName(u"comboBox_task_priority")

        self.formLayout_task_details.setWidget(3, QFormLayout.ItemRole.FieldRole, self.comboBox_task_priority)

        self.label_task_due_date = QLabel(self.widget_task_details)
        self.label_task_due_date.setObjectName(u"label_task_due_date")

        self.formLayout_task_details.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_task_due_date)

        self.dateEdit_task_due_date = QDateEdit(self.widget_task_details)
        self.dateEdit_task_due_date.setObjectName(u"dateEdit_task_due_date")
        self.dateEdit_task_due_date.setCalendarPopup(True)

        self.formLayout_task_details.setWidget(4, QFormLayout.ItemRole.FieldRole, self.dateEdit_task_due_date)

        self.label_task_due_time = QLabel(self.widget_task_details)
        self.label_task_due_time.setObjectName(u"label_task_due_time")

        self.formLayout_task_details.setWidget(5, QFormLayout.ItemRole.LabelRole, self.label_task_due_time)

        self.timeEdit_task_due_time = QTimeEdit(self.widget_task_details)
        self.timeEdit_task_due_time.setObjectName(u"timeEdit_task_due_time")

        self.formLayout_task_details.setWidget(5, QFormLayout.ItemRole.FieldRole, self.timeEdit_task_due_time)


        self.verticalLayout_Dialog_task_edit.addWidget(self.widget_task_details)

        self.groupBox_task_reminders = QGroupBox(Dialog_task_edit)
        self.groupBox_task_reminders.setObjectName(u"groupBox_task_reminders")
        self.verticalLayout_groupBox_task_reminders = QVBoxLayout(self.groupBox_task_reminders)
        self.verticalLayout_groupBox_task_reminders.setObjectName(u"verticalLayout_groupBox_task_reminders")
        self.checkBox_enable_reminders = QCheckBox(self.groupBox_task_reminders)
        self.checkBox_enable_reminders.setObjectName(u"checkBox_enable_reminders")

        self.verticalLayout_groupBox_task_reminders.addWidget(self.checkBox_enable_reminders)

        self.widget_reminder_periods = QWidget(self.groupBox_task_reminders)
        self.widget_reminder_periods.setObjectName(u"widget_reminder_periods")
        self.verticalLayout_widget_reminder_periods = QVBoxLayout(self.widget_reminder_periods)
        self.verticalLayout_widget_reminder_periods.setObjectName(u"verticalLayout_widget_reminder_periods")
        self.label_reminder_periods = QLabel(self.widget_reminder_periods)
        self.label_reminder_periods.setObjectName(u"label_reminder_periods")

        self.verticalLayout_widget_reminder_periods.addWidget(self.label_reminder_periods)

        self.scrollArea_reminder_periods = QScrollArea(self.widget_reminder_periods)
        self.scrollArea_reminder_periods.setObjectName(u"scrollArea_reminder_periods")
        self.scrollArea_reminder_periods.setWidgetResizable(True)
        self.scrollAreaWidgetContents_reminder_periods = QWidget()
        self.scrollAreaWidgetContents_reminder_periods.setObjectName(u"scrollAreaWidgetContents_reminder_periods")
        self.verticalLayout_scrollAreaWidgetContents_reminder_periods = QVBoxLayout(self.scrollAreaWidgetContents_reminder_periods)
        self.verticalLayout_scrollAreaWidgetContents_reminder_periods.setSpacing(4)
        self.verticalLayout_scrollAreaWidgetContents_reminder_periods.setObjectName(u"verticalLayout_scrollAreaWidgetContents_reminder_periods")
        self.verticalLayout_scrollAreaWidgetContents_reminder_periods.setContentsMargins(4, 4, 4, 4)
        self.scrollArea_reminder_periods.setWidget(self.scrollAreaWidgetContents_reminder_periods)

        self.verticalLayout_widget_reminder_periods.addWidget(self.scrollArea_reminder_periods)

        self.pushButton_add_reminder_period = QPushButton(self.widget_reminder_periods)
        self.pushButton_add_reminder_period.setObjectName(u"pushButton_add_reminder_period")

        self.verticalLayout_widget_reminder_periods.addWidget(self.pushButton_add_reminder_period)


        self.verticalLayout_groupBox_task_reminders.addWidget(self.widget_reminder_periods)


        self.verticalLayout_Dialog_task_edit.addWidget(self.groupBox_task_reminders)

        self.buttonBox_task_edit = QDialogButtonBox(Dialog_task_edit)
        self.buttonBox_task_edit.setObjectName(u"buttonBox_task_edit")
        self.buttonBox_task_edit.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox_task_edit.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save)

        self.verticalLayout_Dialog_task_edit.addWidget(self.buttonBox_task_edit)


        self.retranslateUi(Dialog_task_edit)

        QMetaObject.connectSlotsByName(Dialog_task_edit)
    # setupUi

    def retranslateUi(self, Dialog_task_edit):
        Dialog_task_edit.setWindowTitle(QCoreApplication.translate("Dialog_task_edit", u"Edit Task", None))
        self.label_task_edit_header.setText(QCoreApplication.translate("Dialog_task_edit", u"Task Details", None))
        self.label_task_edit_header.setProperty(u"role", QCoreApplication.translate("Dialog_task_edit", u"header", None))
        self.label_task_title.setText(QCoreApplication.translate("Dialog_task_edit", u"Title:", None))
        self.lineEdit_task_title.setPlaceholderText(QCoreApplication.translate("Dialog_task_edit", u"Enter task title", None))
        self.label_task_description.setText(QCoreApplication.translate("Dialog_task_edit", u"Description:", None))
        self.textEdit_task_description.setPlaceholderText(QCoreApplication.translate("Dialog_task_edit", u"Enter task description (optional)", None))
        self.label_task_category.setText(QCoreApplication.translate("Dialog_task_edit", u"Category:", None))
        self.lineEdit_task_category.setPlaceholderText(QCoreApplication.translate("Dialog_task_edit", u"Enter category (optional)", None))
        self.label_task_priority.setText(QCoreApplication.translate("Dialog_task_edit", u"Priority:", None))
        self.comboBox_task_priority.setItemText(0, QCoreApplication.translate("Dialog_task_edit", u"Low", None))
        self.comboBox_task_priority.setItemText(1, QCoreApplication.translate("Dialog_task_edit", u"Medium", None))
        self.comboBox_task_priority.setItemText(2, QCoreApplication.translate("Dialog_task_edit", u"High", None))

        self.label_task_due_date.setText(QCoreApplication.translate("Dialog_task_edit", u"Due Date:", None))
        self.label_task_due_time.setText(QCoreApplication.translate("Dialog_task_edit", u"Due Time:", None))
        self.timeEdit_task_due_time.setDisplayFormat(QCoreApplication.translate("Dialog_task_edit", u"h:mm AP", None))
        self.groupBox_task_reminders.setTitle(QCoreApplication.translate("Dialog_task_edit", u"Reminder Settings", None))
        self.checkBox_enable_reminders.setText(QCoreApplication.translate("Dialog_task_edit", u"Enable reminders for this task", None))
        self.label_reminder_periods.setText(QCoreApplication.translate("Dialog_task_edit", u"Reminder Time Periods:", None))
        self.pushButton_add_reminder_period.setText(QCoreApplication.translate("Dialog_task_edit", u"Add Reminder Period", None))
    # retranslateUi

