# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'category_selection_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QGridLayout, QSizePolicy,
    QVBoxLayout, QWidget)

def qtTrId(id): return id

class Ui_Form_category_selection_widget(object):
    def setupUi(self, Form_category_selection_widget):
        if not Form_category_selection_widget.objectName():
            Form_category_selection_widget.setObjectName(u"Form_category_selection_widget")
        Form_category_selection_widget.resize(400, 300)
        self.verticalLayout = QVBoxLayout(Form_category_selection_widget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.checkBox_word_of_the_day = QCheckBox(Form_category_selection_widget)
        self.checkBox_word_of_the_day.setObjectName(u"checkBox_word_of_the_day")

        self.gridLayout_2.addWidget(self.checkBox_word_of_the_day, 4, 0, 1, 1)

        self.checkBox_quotes_to_ponder = QCheckBox(Form_category_selection_widget)
        self.checkBox_quotes_to_ponder.setObjectName(u"checkBox_quotes_to_ponder")

        self.gridLayout_2.addWidget(self.checkBox_quotes_to_ponder, 3, 0, 1, 1)

        self.checkBox_motivational = QCheckBox(Form_category_selection_widget)
        self.checkBox_motivational.setObjectName(u"checkBox_motivational")

        self.gridLayout_2.addWidget(self.checkBox_motivational, 2, 0, 1, 1)

        self.checkBox_fun_facts = QCheckBox(Form_category_selection_widget)
        self.checkBox_fun_facts.setObjectName(u"checkBox_fun_facts")

        self.gridLayout_2.addWidget(self.checkBox_fun_facts, 0, 0, 1, 1)

        self.checkBox_health = QCheckBox(Form_category_selection_widget)
        self.checkBox_health.setObjectName(u"checkBox_health")

        self.gridLayout_2.addWidget(self.checkBox_health, 1, 0, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout_2)


        self.retranslateUi(Form_category_selection_widget)

        QMetaObject.connectSlotsByName(Form_category_selection_widget)
    # setupUi

    def retranslateUi(self, Form_category_selection_widget):
        Form_category_selection_widget.setWindowTitle(QCoreApplication.translate("Form_category_selection_widget", u"Form", None))
        self.checkBox_word_of_the_day.setText(QCoreApplication.translate("Form_category_selection_widget", u"Word of the Day", None))
        self.checkBox_quotes_to_ponder.setText(QCoreApplication.translate("Form_category_selection_widget", u"Quotes to Ponder", None))
        self.checkBox_motivational.setText(QCoreApplication.translate("Form_category_selection_widget", u"Motivational", None))
        self.checkBox_fun_facts.setText(QCoreApplication.translate("Form_category_selection_widget", u"Fun Facts", None))
        self.checkBox_health.setText(QCoreApplication.translate("Form_category_selection_widget", u"Health", None))
    # retranslateUi

