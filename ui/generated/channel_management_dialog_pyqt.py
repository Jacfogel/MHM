# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'channel_management_dialog.ui'
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
    QGroupBox, QLabel, QSizePolicy, QVBoxLayout,
    QWidget)

def qtTrId(id): return id

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(496, 300)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_channel_settings = QLabel(Dialog)
        self.label_channel_settings.setObjectName(u"label_channel_settings")
        self.label_channel_settings.setMinimumSize(QSize(0, 0))

        self.verticalLayout.addWidget(self.label_channel_settings)

        self.groupBox_primary_channel = QGroupBox(Dialog)
        self.groupBox_primary_channel.setObjectName(u"groupBox_primary_channel")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_primary_channel)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.widget_placeholder_channel_selection = QWidget(self.groupBox_primary_channel)
        self.widget_placeholder_channel_selection.setObjectName(u"widget_placeholder_channel_selection")
        self.verticalLayout_3 = QVBoxLayout(self.widget_placeholder_channel_selection)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")

        self.verticalLayout_2.addWidget(self.widget_placeholder_channel_selection)


        self.verticalLayout.addWidget(self.groupBox_primary_channel)

        self.buttonBox_save_cancel = QDialogButtonBox(Dialog)
        self.buttonBox_save_cancel.setObjectName(u"buttonBox_save_cancel")
        self.buttonBox_save_cancel.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox_save_cancel.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save)

        self.verticalLayout.addWidget(self.buttonBox_save_cancel)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.label_channel_settings.setText(QCoreApplication.translate("Dialog", u"Channel Settings", None))
        self.label_channel_settings.setProperty(u"role", QCoreApplication.translate("Dialog", u"header", None))
        self.groupBox_primary_channel.setTitle(QCoreApplication.translate("Dialog", u"Prmiary Message Service", None))
    # retranslateUi

