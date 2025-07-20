# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dynamic_list_field_template.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QLineEdit,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_Form_dynamic_list_field_template(object):
    def setupUi(self, Form_dynamic_list_field_template):
        if not Form_dynamic_list_field_template.objectName():
            Form_dynamic_list_field_template.setObjectName(u"Form_dynamic_list_field_template")
        Form_dynamic_list_field_template.resize(318, 42)
        self.verticalLayout = QVBoxLayout(Form_dynamic_list_field_template)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget_dynamic_list_field = QWidget(Form_dynamic_list_field_template)
        self.widget_dynamic_list_field.setObjectName(u"widget_dynamic_list_field")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_dynamic_list_field.sizePolicy().hasHeightForWidth())
        self.widget_dynamic_list_field.setSizePolicy(sizePolicy)
        self.widget_dynamic_list_field.setMinimumSize(QSize(300, 0))
        self.horizontalLayout_4 = QHBoxLayout(self.widget_dynamic_list_field)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 10, 0)
        self.checkBox__dynamic_list_field = QCheckBox(self.widget_dynamic_list_field)
        self.checkBox__dynamic_list_field.setObjectName(u"checkBox__dynamic_list_field")

        self.horizontalLayout_4.addWidget(self.checkBox__dynamic_list_field)

        self.lineEdit_dynamic_list_field = QLineEdit(self.widget_dynamic_list_field)
        self.lineEdit_dynamic_list_field.setObjectName(u"lineEdit_dynamic_list_field")
        sizePolicy.setHeightForWidth(self.lineEdit_dynamic_list_field.sizePolicy().hasHeightForWidth())
        self.lineEdit_dynamic_list_field.setSizePolicy(sizePolicy)

        self.horizontalLayout_4.addWidget(self.lineEdit_dynamic_list_field)

        self.pushButton_delete_DynamicListField = QPushButton(self.widget_dynamic_list_field)
        self.pushButton_delete_DynamicListField.setObjectName(u"pushButton_delete_DynamicListField")
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.EditClear))
        self.pushButton_delete_DynamicListField.setIcon(icon)

        self.horizontalLayout_4.addWidget(self.pushButton_delete_DynamicListField)

        self.horizontalLayout_4.setStretch(1, 1)

        self.verticalLayout.addWidget(self.widget_dynamic_list_field)


        self.retranslateUi(Form_dynamic_list_field_template)

        QMetaObject.connectSlotsByName(Form_dynamic_list_field_template)
    # setupUi

    def retranslateUi(self, Form_dynamic_list_field_template):
        Form_dynamic_list_field_template.setWindowTitle(QCoreApplication.translate("Form_dynamic_list_field_template", u"Form", None))
        self.checkBox__dynamic_list_field.setText("")
#if QT_CONFIG(tooltip)
        self.lineEdit_dynamic_list_field.setToolTip(QCoreApplication.translate("Form_dynamic_list_field_template", u"<html><head/><body><p><br/></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(whatsthis)
        self.lineEdit_dynamic_list_field.setWhatsThis(QCoreApplication.translate("Form_dynamic_list_field_template", u"<html><head/><body><p><br/></p></body></html>", None))
#endif // QT_CONFIG(whatsthis)
        self.lineEdit_dynamic_list_field.setText("")
        self.pushButton_delete_DynamicListField.setText("")
    # retranslateUi

