# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'period_row_template.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QRadioButton, QSizePolicy, QVBoxLayout, QWidget)

def qtTrId(id): return id

class Ui_Form_period_row_template(object):
    def setupUi(self, Form_period_row_template):
        if not Form_period_row_template.objectName():
            Form_period_row_template.setObjectName(u"Form_period_row_template")
        Form_period_row_template.resize(732, 97)
        self.verticalLayout_2 = QVBoxLayout(Form_period_row_template)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(4, 4, 4, 4)
        self.frame = QFrame(Form_period_row_template)
        self.frame.setObjectName(u"frame")
        self.frame.setMaximumSize(QSize(16777215, 100))
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.frame)
        self.horizontalLayout_5.setSpacing(2)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(2, 2, 2, 2)
        self.checkBox_active = QCheckBox(self.frame)
        self.checkBox_active.setObjectName(u"checkBox_active")

        self.horizontalLayout_5.addWidget(self.checkBox_active)

        self.frame_2 = QFrame(self.frame)
        self.frame_2.setObjectName(u"frame_2")
        self.verticalLayout = QVBoxLayout(self.frame_2)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.widget_2 = QWidget(self.frame_2)
        self.widget_2.setObjectName(u"widget_2")
        self.horizontalLayout_3 = QHBoxLayout(self.widget_2)
        self.horizontalLayout_3.setSpacing(2)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(2, 2, 2, 2)
        self.lineEdit_time_period_name = QLineEdit(self.widget_2)
        self.lineEdit_time_period_name.setObjectName(u"lineEdit_time_period_name")

        self.horizontalLayout_3.addWidget(self.lineEdit_time_period_name)

        self.label_start = QLabel(self.widget_2)
        self.label_start.setObjectName(u"label_start")
        self.label_start.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.label_start.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_3.addWidget(self.label_start)

        self.comboBox_start_time_hours = QComboBox(self.widget_2)
        self.comboBox_start_time_hours.setObjectName(u"comboBox_start_time_hours")

        self.horizontalLayout_3.addWidget(self.comboBox_start_time_hours)

        self.label_start_start_colon = QLabel(self.widget_2)
        self.label_start_start_colon.setObjectName(u"label_start_start_colon")
        self.label_start_start_colon.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.label_start_start_colon.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_3.addWidget(self.label_start_start_colon)

        self.comboBox_start_time_minutes = QComboBox(self.widget_2)
        self.comboBox_start_time_minutes.setObjectName(u"comboBox_start_time_minutes")

        self.horizontalLayout_3.addWidget(self.comboBox_start_time_minutes)

        self.widget_start_time_am_pm = QWidget(self.widget_2)
        self.widget_start_time_am_pm.setObjectName(u"widget_start_time_am_pm")
        self.verticalLayout_5 = QVBoxLayout(self.widget_start_time_am_pm)
        self.verticalLayout_5.setSpacing(2)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(2, 2, 2, 2)
        self.radioButton_start_time_am = QRadioButton(self.widget_start_time_am_pm)
        self.radioButton_start_time_am.setObjectName(u"radioButton_start_time_am")

        self.verticalLayout_5.addWidget(self.radioButton_start_time_am)

        self.radioButton_start_time_pm = QRadioButton(self.widget_start_time_am_pm)
        self.radioButton_start_time_pm.setObjectName(u"radioButton_start_time_pm")

        self.verticalLayout_5.addWidget(self.radioButton_start_time_pm)


        self.horizontalLayout_3.addWidget(self.widget_start_time_am_pm)

        self.label_end = QLabel(self.widget_2)
        self.label_end.setObjectName(u"label_end")
        self.label_end.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_3.addWidget(self.label_end)

        self.comboBox_end_time_hours = QComboBox(self.widget_2)
        self.comboBox_end_time_hours.setObjectName(u"comboBox_end_time_hours")

        self.horizontalLayout_3.addWidget(self.comboBox_end_time_hours)

        self.label_start_end_colon = QLabel(self.widget_2)
        self.label_start_end_colon.setObjectName(u"label_start_end_colon")
        self.label_start_end_colon.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.label_start_end_colon.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_3.addWidget(self.label_start_end_colon)

        self.comboBox_end_time_minutes = QComboBox(self.widget_2)
        self.comboBox_end_time_minutes.setObjectName(u"comboBox_end_time_minutes")

        self.horizontalLayout_3.addWidget(self.comboBox_end_time_minutes)

        self.widget_end_time_am_pm = QWidget(self.widget_2)
        self.widget_end_time_am_pm.setObjectName(u"widget_end_time_am_pm")
        self.verticalLayout_7 = QVBoxLayout(self.widget_end_time_am_pm)
        self.verticalLayout_7.setSpacing(2)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(2, 2, 2, 2)
        self.radioButton_end_time_am = QRadioButton(self.widget_end_time_am_pm)
        self.radioButton_end_time_am.setObjectName(u"radioButton_end_time_am")

        self.verticalLayout_7.addWidget(self.radioButton_end_time_am)

        self.radioButton_end_time_pm = QRadioButton(self.widget_end_time_am_pm)
        self.radioButton_end_time_pm.setObjectName(u"radioButton_end_time_pm")

        self.verticalLayout_7.addWidget(self.radioButton_end_time_pm)


        self.horizontalLayout_3.addWidget(self.widget_end_time_am_pm)


        self.verticalLayout.addWidget(self.widget_2)

        self.widget = QWidget(self.frame_2)
        self.widget.setObjectName(u"widget")
        self.horizontalLayout_2 = QHBoxLayout(self.widget)
        self.horizontalLayout_2.setSpacing(2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(2, 2, 2, 2)
        self.checkBox_select_all_days = QCheckBox(self.widget)
        self.checkBox_select_all_days.setObjectName(u"checkBox_select_all_days")
        self.checkBox_select_all_days.setProperty(u"role", u"header3")

        self.horizontalLayout_2.addWidget(self.checkBox_select_all_days)

        self.checkBox_sunday = QCheckBox(self.widget)
        self.checkBox_sunday.setObjectName(u"checkBox_sunday")

        self.horizontalLayout_2.addWidget(self.checkBox_sunday)

        self.checkBox_monday = QCheckBox(self.widget)
        self.checkBox_monday.setObjectName(u"checkBox_monday")
        self.checkBox_monday.setChecked(False)

        self.horizontalLayout_2.addWidget(self.checkBox_monday)

        self.checkBox_tuesday = QCheckBox(self.widget)
        self.checkBox_tuesday.setObjectName(u"checkBox_tuesday")
        self.checkBox_tuesday.setChecked(False)

        self.horizontalLayout_2.addWidget(self.checkBox_tuesday)

        self.checkBox_wednesday = QCheckBox(self.widget)
        self.checkBox_wednesday.setObjectName(u"checkBox_wednesday")
        self.checkBox_wednesday.setChecked(False)

        self.horizontalLayout_2.addWidget(self.checkBox_wednesday)

        self.checkBox_thursday = QCheckBox(self.widget)
        self.checkBox_thursday.setObjectName(u"checkBox_thursday")
        self.checkBox_thursday.setChecked(False)

        self.horizontalLayout_2.addWidget(self.checkBox_thursday)

        self.checkBox_friday = QCheckBox(self.widget)
        self.checkBox_friday.setObjectName(u"checkBox_friday")
        self.checkBox_friday.setChecked(False)

        self.horizontalLayout_2.addWidget(self.checkBox_friday)

        self.checkBox_saturday = QCheckBox(self.widget)
        self.checkBox_saturday.setObjectName(u"checkBox_saturday")

        self.horizontalLayout_2.addWidget(self.checkBox_saturday)


        self.verticalLayout.addWidget(self.widget)


        self.horizontalLayout_5.addWidget(self.frame_2)

        self.pushButton_delete = QPushButton(self.frame)
        self.pushButton_delete.setObjectName(u"pushButton_delete")
        self.pushButton_delete.setEnabled(True)

        self.horizontalLayout_5.addWidget(self.pushButton_delete)


        self.verticalLayout_2.addWidget(self.frame)


        self.retranslateUi(Form_period_row_template)

        QMetaObject.connectSlotsByName(Form_period_row_template)
    # setupUi

    def retranslateUi(self, Form_period_row_template):
        Form_period_row_template.setWindowTitle(QCoreApplication.translate("Form_period_row_template", u"Form", None))
        self.checkBox_active.setText(QCoreApplication.translate("Form_period_row_template", u"Active", None))
        self.label_start.setText(QCoreApplication.translate("Form_period_row_template", u"Start:", None))
        self.label_start_start_colon.setText(QCoreApplication.translate("Form_period_row_template", u":", None))
        self.radioButton_start_time_am.setText(QCoreApplication.translate("Form_period_row_template", u"AM", None))
        self.radioButton_start_time_pm.setText(QCoreApplication.translate("Form_period_row_template", u"PM", None))
        self.label_end.setText(QCoreApplication.translate("Form_period_row_template", u"End:", None))
        self.label_start_end_colon.setText(QCoreApplication.translate("Form_period_row_template", u":", None))
        self.radioButton_end_time_am.setText(QCoreApplication.translate("Form_period_row_template", u"AM", None))
        self.radioButton_end_time_pm.setText(QCoreApplication.translate("Form_period_row_template", u"PM", None))
        self.checkBox_select_all_days.setText(QCoreApplication.translate("Form_period_row_template", u"Select All", None))
        self.checkBox_sunday.setText(QCoreApplication.translate("Form_period_row_template", u"Sunday", None))
        self.checkBox_monday.setText(QCoreApplication.translate("Form_period_row_template", u"Monday", None))
        self.checkBox_tuesday.setText(QCoreApplication.translate("Form_period_row_template", u"Tuesday", None))
        self.checkBox_wednesday.setText(QCoreApplication.translate("Form_period_row_template", u"Wednesday", None))
        self.checkBox_thursday.setText(QCoreApplication.translate("Form_period_row_template", u"Thursday", None))
        self.checkBox_friday.setText(QCoreApplication.translate("Form_period_row_template", u"Friday", None))
        self.checkBox_saturday.setText(QCoreApplication.translate("Form_period_row_template", u"Saturday", None))
        self.pushButton_delete.setText(QCoreApplication.translate("Form_period_row_template", u"Delete", None))
    # retranslateUi

