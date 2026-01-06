# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'checkin_management_dialog.ui'
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
    QGroupBox, QLabel, QSizePolicy, QTabWidget,
    QVBoxLayout, QWidget)

class Ui_Dialog_checkin_management(object):
    def setupUi(self, Dialog_checkin_management):
        if not Dialog_checkin_management.objectName():
            Dialog_checkin_management.setObjectName(u"Dialog_checkin_management")
        Dialog_checkin_management.resize(1000, 800)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog_checkin_management.sizePolicy().hasHeightForWidth())
        Dialog_checkin_management.setSizePolicy(sizePolicy)
        self.verticalLayout_Dialog_checkin_management = QVBoxLayout(Dialog_checkin_management)
        self.verticalLayout_Dialog_checkin_management.setObjectName(u"verticalLayout_Dialog_checkin_management")
        self.label_checkin_management = QLabel(Dialog_checkin_management)
        self.label_checkin_management.setObjectName(u"label_checkin_management")
        self.label_checkin_management.setMinimumSize(QSize(0, 0))

        self.verticalLayout_Dialog_checkin_management.addWidget(self.label_checkin_management)

        self.groupBox_checkBox_enable_checkins = QGroupBox(Dialog_checkin_management)
        self.groupBox_checkBox_enable_checkins.setObjectName(u"groupBox_checkBox_enable_checkins")
        self.groupBox_checkBox_enable_checkins.setCheckable(True)
        self.groupBox_checkBox_enable_checkins.setChecked(False)
        self.verticalLayout_groupBox_checkBox_enable_checkins = QVBoxLayout(self.groupBox_checkBox_enable_checkins)
        self.verticalLayout_groupBox_checkBox_enable_checkins.setObjectName(u"verticalLayout_groupBox_checkBox_enable_checkins")
        self.tabWidget_checkin_settings = QTabWidget(self.groupBox_checkBox_enable_checkins)
        self.tabWidget_checkin_settings.setObjectName(u"tabWidget_checkin_settings")
        self.tab_checkin_questions = QWidget()
        self.tab_checkin_questions.setObjectName(u"tab_checkin_questions")
        self.verticalLayout_tab_checkin_questions = QVBoxLayout(self.tab_checkin_questions)
        self.verticalLayout_tab_checkin_questions.setObjectName(u"verticalLayout_tab_checkin_questions")
        self.widget_placeholder_checkin_settings = QWidget(self.tab_checkin_questions)
        self.widget_placeholder_checkin_settings.setObjectName(u"widget_placeholder_checkin_settings")
        self.widget_placeholder_checkin_settings.setEnabled(True)
        sizePolicy.setHeightForWidth(self.widget_placeholder_checkin_settings.sizePolicy().hasHeightForWidth())
        self.widget_placeholder_checkin_settings.setSizePolicy(sizePolicy)
        self.verticalLayout_widget_placeholder_checkin_settings = QVBoxLayout(self.widget_placeholder_checkin_settings)
        self.verticalLayout_widget_placeholder_checkin_settings.setObjectName(u"verticalLayout_widget_placeholder_checkin_settings")

        self.verticalLayout_tab_checkin_questions.addWidget(self.widget_placeholder_checkin_settings)

        self.tabWidget_checkin_settings.addTab(self.tab_checkin_questions, "")
        self.tab_checkin_frequency = QWidget()
        self.tab_checkin_frequency.setObjectName(u"tab_checkin_frequency")
        self.verticalLayout_tab_checkin_frequency = QVBoxLayout(self.tab_checkin_frequency)
        self.verticalLayout_tab_checkin_frequency.setObjectName(u"verticalLayout_tab_checkin_frequency")
        self.widget_placeholder_frequency_settings = QWidget(self.tab_checkin_frequency)
        self.widget_placeholder_frequency_settings.setObjectName(u"widget_placeholder_frequency_settings")
        sizePolicy.setHeightForWidth(self.widget_placeholder_frequency_settings.sizePolicy().hasHeightForWidth())
        self.widget_placeholder_frequency_settings.setSizePolicy(sizePolicy)
        self.verticalLayout_widget_placeholder_frequency_settings = QVBoxLayout(self.widget_placeholder_frequency_settings)
        self.verticalLayout_widget_placeholder_frequency_settings.setObjectName(u"verticalLayout_widget_placeholder_frequency_settings")

        self.verticalLayout_tab_checkin_frequency.addWidget(self.widget_placeholder_frequency_settings)

        self.tabWidget_checkin_settings.addTab(self.tab_checkin_frequency, "")

        self.verticalLayout_groupBox_checkBox_enable_checkins.addWidget(self.tabWidget_checkin_settings)


        self.verticalLayout_Dialog_checkin_management.addWidget(self.groupBox_checkBox_enable_checkins)

        self.buttonBox_save_cancel = QDialogButtonBox(Dialog_checkin_management)
        self.buttonBox_save_cancel.setObjectName(u"buttonBox_save_cancel")
        self.buttonBox_save_cancel.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox_save_cancel.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save)

        self.verticalLayout_Dialog_checkin_management.addWidget(self.buttonBox_save_cancel)

        self.verticalLayout_Dialog_checkin_management.setStretch(1, 1)

        self.retranslateUi(Dialog_checkin_management)

        self.tabWidget_checkin_settings.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Dialog_checkin_management)
    # setupUi

    def retranslateUi(self, Dialog_checkin_management):
        Dialog_checkin_management.setWindowTitle(QCoreApplication.translate("Dialog_checkin_management", u"Check-in Management", None))
        self.label_checkin_management.setText(QCoreApplication.translate("Dialog_checkin_management", u"Check-in Management", None))
        self.label_checkin_management.setProperty(u"role", QCoreApplication.translate("Dialog_checkin_management", u"header", None))
        self.groupBox_checkBox_enable_checkins.setTitle(QCoreApplication.translate("Dialog_checkin_management", u"Enable Check-ins", None))
        self.tabWidget_checkin_settings.setTabText(self.tabWidget_checkin_settings.indexOf(self.tab_checkin_questions), QCoreApplication.translate("Dialog_checkin_management", u"Check-in Questions", None))
        self.tabWidget_checkin_settings.setTabText(self.tabWidget_checkin_settings.indexOf(self.tab_checkin_frequency), QCoreApplication.translate("Dialog_checkin_management", u"Check-in Frequency / Schedule", None))
    # retranslateUi

