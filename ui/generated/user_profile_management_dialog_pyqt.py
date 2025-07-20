# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'user_profile_management_dialog.ui'
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
    QLabel, QSizePolicy, QVBoxLayout, QWidget)

def qtTrId(id): return id

class Ui_Dialog_user_profile(object):
    def setupUi(self, Dialog_user_profile):
        if not Dialog_user_profile.objectName():
            Dialog_user_profile.setObjectName(u"Dialog_user_profile")
        Dialog_user_profile.resize(577, 867)
        self.verticalLayout = QVBoxLayout(Dialog_user_profile)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_profile = QLabel(Dialog_user_profile)
        self.label_profile.setObjectName(u"label_profile")

        self.verticalLayout.addWidget(self.label_profile)

        self.widget__user_profile = QWidget(Dialog_user_profile)
        self.widget__user_profile.setObjectName(u"widget__user_profile")
        self.verticalLayout_2 = QVBoxLayout(self.widget__user_profile)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")

        self.verticalLayout.addWidget(self.widget__user_profile)

        self.buttonBox_save_cancel = QDialogButtonBox(Dialog_user_profile)
        self.buttonBox_save_cancel.setObjectName(u"buttonBox_save_cancel")
        self.buttonBox_save_cancel.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox_save_cancel.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save)

        self.verticalLayout.addWidget(self.buttonBox_save_cancel)

        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(Dialog_user_profile)
        self.buttonBox_save_cancel.accepted.connect(Dialog_user_profile.accept)
        self.buttonBox_save_cancel.rejected.connect(Dialog_user_profile.reject)

        QMetaObject.connectSlotsByName(Dialog_user_profile)
    # setupUi

    def retranslateUi(self, Dialog_user_profile):
        Dialog_user_profile.setWindowTitle(QCoreApplication.translate("Dialog_user_profile", u"Dialog", None))
        self.label_profile.setText(QCoreApplication.translate("Dialog_user_profile", u"Profile", None))
        self.label_profile.setProperty(u"role", QCoreApplication.translate("Dialog_user_profile", u"header", None))
    # retranslateUi

