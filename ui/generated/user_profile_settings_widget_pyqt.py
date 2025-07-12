# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'user_profile_settings_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QCalendarWidget, QCheckBox, QGridLayout,
    QGroupBox, QHBoxLayout, QLineEdit, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

def qtTrId(id): return id

class Ui_Form_user_profile_settings(object):
    def setupUi(self, Form_user_profile_settings):
        if not Form_user_profile_settings.objectName():
            Form_user_profile_settings.setObjectName(u"Form_user_profile_settings")
        Form_user_profile_settings.resize(500, 686)
        self.verticalLayout_3 = QVBoxLayout(Form_user_profile_settings)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.groupBox_gender_identity = QGroupBox(Form_user_profile_settings)
        self.groupBox_gender_identity.setObjectName(u"groupBox_gender_identity")
        self.gridLayout = QGridLayout(self.groupBox_gender_identity)
        self.gridLayout.setObjectName(u"gridLayout")
        self.checkBox_none = QCheckBox(self.groupBox_gender_identity)
        self.checkBox_none.setObjectName(u"checkBox_none")

        self.gridLayout.addWidget(self.checkBox_none, 0, 1, 1, 1)

        self.checkBox_woman = QCheckBox(self.groupBox_gender_identity)
        self.checkBox_woman.setObjectName(u"checkBox_woman")

        self.gridLayout.addWidget(self.checkBox_woman, 0, 0, 1, 1)

        self.checkBox_prefer_not_to_say = QCheckBox(self.groupBox_gender_identity)
        self.checkBox_prefer_not_to_say.setObjectName(u"checkBox_prefer_not_to_say")

        self.gridLayout.addWidget(self.checkBox_prefer_not_to_say, 1, 1, 1, 1)

        self.checkBox_nonbinary = QCheckBox(self.groupBox_gender_identity)
        self.checkBox_nonbinary.setObjectName(u"checkBox_nonbinary")

        self.gridLayout.addWidget(self.checkBox_nonbinary, 2, 0, 1, 1)

        self.widget_checkBox_with_lineEdit_gender_identity = QWidget(self.groupBox_gender_identity)
        self.widget_checkBox_with_lineEdit_gender_identity.setObjectName(u"widget_checkBox_with_lineEdit_gender_identity")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_checkBox_with_lineEdit_gender_identity.sizePolicy().hasHeightForWidth())
        self.widget_checkBox_with_lineEdit_gender_identity.setSizePolicy(sizePolicy)
        self.horizontalLayout_6 = QHBoxLayout(self.widget_checkBox_with_lineEdit_gender_identity)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 10, 0)
        self.checkBox_custom_entry_gender_identity = QCheckBox(self.widget_checkBox_with_lineEdit_gender_identity)
        self.checkBox_custom_entry_gender_identity.setObjectName(u"checkBox_custom_entry_gender_identity")

        self.horizontalLayout_6.addWidget(self.checkBox_custom_entry_gender_identity)

        self.lineEdit_custom_entry_gender_identity = QLineEdit(self.widget_checkBox_with_lineEdit_gender_identity)
        self.lineEdit_custom_entry_gender_identity.setObjectName(u"lineEdit_custom_entry_gender_identity")
        sizePolicy.setHeightForWidth(self.lineEdit_custom_entry_gender_identity.sizePolicy().hasHeightForWidth())
        self.lineEdit_custom_entry_gender_identity.setSizePolicy(sizePolicy)

        self.horizontalLayout_6.addWidget(self.lineEdit_custom_entry_gender_identity)

        self.horizontalLayout_6.setStretch(1, 1)

        self.gridLayout.addWidget(self.widget_checkBox_with_lineEdit_gender_identity, 2, 1, 1, 1)

        self.checkBox_man = QCheckBox(self.groupBox_gender_identity)
        self.checkBox_man.setObjectName(u"checkBox_man")

        self.gridLayout.addWidget(self.checkBox_man, 1, 0, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 0, 2, 3, 1)

        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 1)
        self.gridLayout.setColumnStretch(2, 1)

        self.verticalLayout_3.addWidget(self.groupBox_gender_identity)

        self.groupBox_date_of_birth = QGroupBox(Form_user_profile_settings)
        self.groupBox_date_of_birth.setObjectName(u"groupBox_date_of_birth")
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_date_of_birth)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.calendarWidget_date_of_birth = QCalendarWidget(self.groupBox_date_of_birth)
        self.calendarWidget_date_of_birth.setObjectName(u"calendarWidget_date_of_birth")

        self.verticalLayout_4.addWidget(self.calendarWidget_date_of_birth)


        self.verticalLayout_3.addWidget(self.groupBox_date_of_birth)

        self.groupBox_medical = QGroupBox(Form_user_profile_settings)
        self.groupBox_medical.setObjectName(u"groupBox_medical")
        self.gridLayout_2 = QGridLayout(self.groupBox_medical)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.widget_checkBox_with_lineEdit_medical = QWidget(self.groupBox_medical)
        self.widget_checkBox_with_lineEdit_medical.setObjectName(u"widget_checkBox_with_lineEdit_medical")
        self.horizontalLayout_4 = QHBoxLayout(self.widget_checkBox_with_lineEdit_medical)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 10, 0)
        self.checkBox_custom_entry_medical = QCheckBox(self.widget_checkBox_with_lineEdit_medical)
        self.checkBox_custom_entry_medical.setObjectName(u"checkBox_custom_entry_medical")

        self.horizontalLayout_4.addWidget(self.checkBox_custom_entry_medical)

        self.lineEdit_custom_entry_medical = QLineEdit(self.widget_checkBox_with_lineEdit_medical)
        self.lineEdit_custom_entry_medical.setObjectName(u"lineEdit_custom_entry_medical")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lineEdit_custom_entry_medical.sizePolicy().hasHeightForWidth())
        self.lineEdit_custom_entry_medical.setSizePolicy(sizePolicy1)

        self.horizontalLayout_4.addWidget(self.lineEdit_custom_entry_medical)

        self.horizontalLayout_4.setStretch(1, 1)

        self.gridLayout_2.addWidget(self.widget_checkBox_with_lineEdit_medical, 3, 1, 1, 1)

        self.checkBox_7 = QCheckBox(self.groupBox_medical)
        self.checkBox_7.setObjectName(u"checkBox_7")

        self.gridLayout_2.addWidget(self.checkBox_7, 2, 1, 1, 1)

        self.checkBox = QCheckBox(self.groupBox_medical)
        self.checkBox.setObjectName(u"checkBox")

        self.gridLayout_2.addWidget(self.checkBox, 0, 0, 1, 1)

        self.checkBox_8 = QCheckBox(self.groupBox_medical)
        self.checkBox_8.setObjectName(u"checkBox_8")

        self.gridLayout_2.addWidget(self.checkBox_8, 2, 0, 1, 1)

        self.checkBox_3 = QCheckBox(self.groupBox_medical)
        self.checkBox_3.setObjectName(u"checkBox_3")

        self.gridLayout_2.addWidget(self.checkBox_3, 1, 1, 1, 1)

        self.checkBox_5 = QCheckBox(self.groupBox_medical)
        self.checkBox_5.setObjectName(u"checkBox_5")

        self.gridLayout_2.addWidget(self.checkBox_5, 3, 0, 1, 1)

        self.checkBox_2 = QCheckBox(self.groupBox_medical)
        self.checkBox_2.setObjectName(u"checkBox_2")

        self.gridLayout_2.addWidget(self.checkBox_2, 0, 1, 1, 1)

        self.checkBox_4 = QCheckBox(self.groupBox_medical)
        self.checkBox_4.setObjectName(u"checkBox_4")

        self.gridLayout_2.addWidget(self.checkBox_4, 1, 0, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer_2, 0, 2, 4, 1)

        self.gridLayout_2.setColumnStretch(0, 1)
        self.gridLayout_2.setColumnStretch(1, 1)
        self.gridLayout_2.setColumnStretch(2, 1)

        self.verticalLayout_3.addWidget(self.groupBox_medical)

        self.groupBox = QGroupBox(Form_user_profile_settings)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout_3 = QGridLayout(self.groupBox)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.checkBox_10 = QCheckBox(self.groupBox)
        self.checkBox_10.setObjectName(u"checkBox_10")

        self.gridLayout_3.addWidget(self.checkBox_10, 0, 1, 1, 1)

        self.checkBox_15 = QCheckBox(self.groupBox)
        self.checkBox_15.setObjectName(u"checkBox_15")

        self.gridLayout_3.addWidget(self.checkBox_15, 2, 1, 1, 1)

        self.checkBox_11 = QCheckBox(self.groupBox)
        self.checkBox_11.setObjectName(u"checkBox_11")

        self.gridLayout_3.addWidget(self.checkBox_11, 1, 0, 1, 1)

        self.checkBox_13 = QCheckBox(self.groupBox)
        self.checkBox_13.setObjectName(u"checkBox_13")

        self.gridLayout_3.addWidget(self.checkBox_13, 3, 0, 1, 1)

        self.checkBox_9 = QCheckBox(self.groupBox)
        self.checkBox_9.setObjectName(u"checkBox_9")

        self.gridLayout_3.addWidget(self.checkBox_9, 0, 0, 1, 1)

        self.checkBox_16 = QCheckBox(self.groupBox)
        self.checkBox_16.setObjectName(u"checkBox_16")

        self.gridLayout_3.addWidget(self.checkBox_16, 2, 0, 1, 1)

        self.checkBox_12 = QCheckBox(self.groupBox)
        self.checkBox_12.setObjectName(u"checkBox_12")

        self.gridLayout_3.addWidget(self.checkBox_12, 1, 1, 1, 1)

        self.widget_checkBox_with_lineEdit = QWidget(self.groupBox)
        self.widget_checkBox_with_lineEdit.setObjectName(u"widget_checkBox_with_lineEdit")
        self.horizontalLayout_5 = QHBoxLayout(self.widget_checkBox_with_lineEdit)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 10, 0)
        self.checkBox_custom_entry = QCheckBox(self.widget_checkBox_with_lineEdit)
        self.checkBox_custom_entry.setObjectName(u"checkBox_custom_entry")

        self.horizontalLayout_5.addWidget(self.checkBox_custom_entry)

        self.lineEdit_custom_entry = QLineEdit(self.widget_checkBox_with_lineEdit)
        self.lineEdit_custom_entry.setObjectName(u"lineEdit_custom_entry")
        sizePolicy1.setHeightForWidth(self.lineEdit_custom_entry.sizePolicy().hasHeightForWidth())
        self.lineEdit_custom_entry.setSizePolicy(sizePolicy1)

        self.horizontalLayout_5.addWidget(self.lineEdit_custom_entry)

        self.horizontalLayout_5.setStretch(1, 1)

        self.gridLayout_3.addWidget(self.widget_checkBox_with_lineEdit, 3, 1, 1, 1)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_3.addItem(self.horizontalSpacer_3, 0, 2, 4, 1)

        self.gridLayout_3.setColumnStretch(0, 1)
        self.gridLayout_3.setColumnStretch(1, 1)
        self.gridLayout_3.setColumnStretch(2, 1)

        self.verticalLayout_3.addWidget(self.groupBox)


        self.retranslateUi(Form_user_profile_settings)

        QMetaObject.connectSlotsByName(Form_user_profile_settings)
    # setupUi

    def retranslateUi(self, Form_user_profile_settings):
        Form_user_profile_settings.setWindowTitle(QCoreApplication.translate("Form_user_profile_settings", u"User Profile Settings", None))
        self.groupBox_gender_identity.setTitle(QCoreApplication.translate("Form_user_profile_settings", u"Gender Identity", None))
        self.checkBox_none.setText(QCoreApplication.translate("Form_user_profile_settings", u"None", None))
        self.checkBox_woman.setText(QCoreApplication.translate("Form_user_profile_settings", u"Woman", None))
        self.checkBox_prefer_not_to_say.setText(QCoreApplication.translate("Form_user_profile_settings", u"Prefer not to say", None))
        self.checkBox_nonbinary.setText(QCoreApplication.translate("Form_user_profile_settings", u"Non-binary", None))
        self.checkBox_custom_entry_gender_identity.setText("")
#if QT_CONFIG(tooltip)
        self.lineEdit_custom_entry_gender_identity.setToolTip(QCoreApplication.translate("Form_user_profile_settings", u"<html><head/><body><p><br/></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(whatsthis)
        self.lineEdit_custom_entry_gender_identity.setWhatsThis(QCoreApplication.translate("Form_user_profile_settings", u"<html><head/><body><p><br/></p></body></html>", None))
#endif // QT_CONFIG(whatsthis)
        self.lineEdit_custom_entry_gender_identity.setText("")
        self.checkBox_man.setText(QCoreApplication.translate("Form_user_profile_settings", u"Man", None))
        self.groupBox_date_of_birth.setTitle(QCoreApplication.translate("Form_user_profile_settings", u"Date of Birth", None))
        self.groupBox_medical.setTitle(QCoreApplication.translate("Form_user_profile_settings", u"Health and Medical ", None))
        self.checkBox_custom_entry_medical.setText("")
#if QT_CONFIG(tooltip)
        self.lineEdit_custom_entry_medical.setToolTip(QCoreApplication.translate("Form_user_profile_settings", u"<html><head/><body><p><br/></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(whatsthis)
        self.lineEdit_custom_entry_medical.setWhatsThis(QCoreApplication.translate("Form_user_profile_settings", u"<html><head/><body><p><br/></p></body></html>", None))
#endif // QT_CONFIG(whatsthis)
        self.lineEdit_custom_entry_medical.setText("")
        self.checkBox_7.setText(QCoreApplication.translate("Form_user_profile_settings", u"CheckBox", None))
        self.checkBox.setText(QCoreApplication.translate("Form_user_profile_settings", u"CheckBox", None))
        self.checkBox_8.setText(QCoreApplication.translate("Form_user_profile_settings", u"CheckBox", None))
        self.checkBox_3.setText(QCoreApplication.translate("Form_user_profile_settings", u"CheckBox", None))
        self.checkBox_5.setText(QCoreApplication.translate("Form_user_profile_settings", u"CheckBox", None))
        self.checkBox_2.setText(QCoreApplication.translate("Form_user_profile_settings", u"CheckBox", None))
        self.checkBox_4.setText(QCoreApplication.translate("Form_user_profile_settings", u"CheckBox", None))
        self.groupBox.setTitle(QCoreApplication.translate("Form_user_profile_settings", u"Interests", None))
        self.checkBox_10.setText(QCoreApplication.translate("Form_user_profile_settings", u"CheckBox", None))
        self.checkBox_15.setText(QCoreApplication.translate("Form_user_profile_settings", u"CheckBox", None))
        self.checkBox_11.setText(QCoreApplication.translate("Form_user_profile_settings", u"CheckBox", None))
        self.checkBox_13.setText(QCoreApplication.translate("Form_user_profile_settings", u"CheckBox", None))
        self.checkBox_9.setText(QCoreApplication.translate("Form_user_profile_settings", u"CheckBox", None))
        self.checkBox_16.setText(QCoreApplication.translate("Form_user_profile_settings", u"CheckBox", None))
        self.checkBox_12.setText(QCoreApplication.translate("Form_user_profile_settings", u"CheckBox", None))
        self.checkBox_custom_entry.setText("")
#if QT_CONFIG(tooltip)
        self.lineEdit_custom_entry.setToolTip(QCoreApplication.translate("Form_user_profile_settings", u"<html><head/><body><p><br/></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(whatsthis)
        self.lineEdit_custom_entry.setWhatsThis(QCoreApplication.translate("Form_user_profile_settings", u"<html><head/><body><p><br/></p></body></html>", None))
#endif // QT_CONFIG(whatsthis)
        self.lineEdit_custom_entry.setText("")
    # retranslateUi

