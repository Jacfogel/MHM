# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'category_management_dialog.ui'
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
    QGroupBox, QHBoxLayout, QLabel, QSizePolicy,
    QVBoxLayout, QWidget)

def qtTrId(id): 
    """
    Qt translation function stub.
    
    This is a placeholder function for Qt's translation system. In a real Qt
    application, this would return the translated string for the given ID.
    
    Args:
        id: The translation ID
        
    Returns:
        The translation ID (no translation performed in this stub)
    """
    return id

class Ui_Dialog_category_management(object):
    def setupUi(self, Dialog_category_management):
        if not Dialog_category_management.objectName():
            Dialog_category_management.setObjectName(u"Dialog_category_management")
        Dialog_category_management.resize(400, 300)
        self.verticalLayout = QVBoxLayout(Dialog_category_management)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_categories = QLabel(Dialog_category_management)
        self.label_categories.setObjectName(u"label_categories")
        self.label_categories.setMinimumSize(QSize(0, 0))

        self.verticalLayout.addWidget(self.label_categories)

        self.groupBox_select_categories = QGroupBox(Dialog_category_management)
        self.groupBox_select_categories.setObjectName(u"groupBox_select_categories")
        self.horizontalLayout = QHBoxLayout(self.groupBox_select_categories)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.widget_placeholder_select_categories = QWidget(self.groupBox_select_categories)
        self.widget_placeholder_select_categories.setObjectName(u"widget_placeholder_select_categories")
        self.verticalLayout_10 = QVBoxLayout(self.widget_placeholder_select_categories)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")

        self.horizontalLayout.addWidget(self.widget_placeholder_select_categories)


        self.verticalLayout.addWidget(self.groupBox_select_categories)

        self.buttonBox_save_cancel = QDialogButtonBox(Dialog_category_management)
        self.buttonBox_save_cancel.setObjectName(u"buttonBox_save_cancel")
        self.buttonBox_save_cancel.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox_save_cancel.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save)

        self.verticalLayout.addWidget(self.buttonBox_save_cancel)


        self.retranslateUi(Dialog_category_management)

        QMetaObject.connectSlotsByName(Dialog_category_management)
    # setupUi

    def retranslateUi(self, Dialog_category_management):
        Dialog_category_management.setWindowTitle(QCoreApplication.translate("Dialog_category_management", u"Dialog", None))
        self.label_categories.setText(QCoreApplication.translate("Dialog_category_management", u"Categories", None))
        self.label_categories.setProperty(u"role", QCoreApplication.translate("Dialog_category_management", u"header", None))
        self.groupBox_select_categories.setTitle(QCoreApplication.translate("Dialog_category_management", u"Select Categories (at least one required)", None))
    # retranslateUi

