# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'checkin_element_template.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QHBoxLayout,
    QLineEdit, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

def qtTrId(id): return id

class Ui_Form_checkin_element_template(object):
    def setupUi(self, Form_checkin_element_template):
        if not Form_checkin_element_template.objectName():
            Form_checkin_element_template.setObjectName(u"Form_checkin_element_template")
        Form_checkin_element_template.resize(341, 42)
        self.verticalLayout = QVBoxLayout(Form_checkin_element_template)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget_checkBox_with_lineEdit_element = QWidget(Form_checkin_element_template)
        self.widget_checkBox_with_lineEdit_element.setObjectName(u"widget_checkBox_with_lineEdit_element")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_checkBox_with_lineEdit_element.sizePolicy().hasHeightForWidth())
        self.widget_checkBox_with_lineEdit_element.setSizePolicy(sizePolicy)
        self.horizontalLayout_4 = QHBoxLayout(self.widget_checkBox_with_lineEdit_element)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 10, 0)
        self.checkBox_custom_entry_element = QCheckBox(self.widget_checkBox_with_lineEdit_element)
        self.checkBox_custom_entry_element.setObjectName(u"checkBox_custom_entry_element")

        self.horizontalLayout_4.addWidget(self.checkBox_custom_entry_element)

        self.lineEdit_custom_entry_element_name = QLineEdit(self.widget_checkBox_with_lineEdit_element)
        self.lineEdit_custom_entry_element_name.setObjectName(u"lineEdit_custom_entry_element_name")
        sizePolicy.setHeightForWidth(self.lineEdit_custom_entry_element_name.sizePolicy().hasHeightForWidth())
        self.lineEdit_custom_entry_element_name.setSizePolicy(sizePolicy)

        self.horizontalLayout_4.addWidget(self.lineEdit_custom_entry_element_name)

        self.comboBox_custom_entry_element_input_type = QComboBox(self.widget_checkBox_with_lineEdit_element)
        self.comboBox_custom_entry_element_input_type.setObjectName(u"comboBox_custom_entry_element_input_type")

        self.horizontalLayout_4.addWidget(self.comboBox_custom_entry_element_input_type)

        self.pushButton_delete_element = QPushButton(self.widget_checkBox_with_lineEdit_element)
        self.pushButton_delete_element.setObjectName(u"pushButton_delete_element")

        self.horizontalLayout_4.addWidget(self.pushButton_delete_element)

        self.horizontalLayout_4.setStretch(1, 1)

        self.verticalLayout.addWidget(self.widget_checkBox_with_lineEdit_element)


        self.retranslateUi(Form_checkin_element_template)

        QMetaObject.connectSlotsByName(Form_checkin_element_template)
    # setupUi

    def retranslateUi(self, Form_checkin_element_template):
        Form_checkin_element_template.setWindowTitle(QCoreApplication.translate("Form_checkin_element_template", u"Form", None))
        self.checkBox_custom_entry_element.setText("")
#if QT_CONFIG(tooltip)
        self.lineEdit_custom_entry_element_name.setToolTip(QCoreApplication.translate("Form_checkin_element_template", u"<html><head/><body><p><br/></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(whatsthis)
        self.lineEdit_custom_entry_element_name.setWhatsThis(QCoreApplication.translate("Form_checkin_element_template", u"<html><head/><body><p><br/></p></body></html>", None))
#endif // QT_CONFIG(whatsthis)
        self.lineEdit_custom_entry_element_name.setText("")
        self.pushButton_delete_element.setText(QCoreApplication.translate("Form_checkin_element_template", u"Delete", None))
    # retranslateUi

