# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'checkin_settings_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QGridLayout, QGroupBox,
    QHBoxLayout, QPushButton, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget)

def qtTrId(id): return id

class Ui_Form_checkin_settings(object):
    def setupUi(self, Form_checkin_settings):
        if not Form_checkin_settings.objectName():
            Form_checkin_settings.setObjectName(u"Form_checkin_settings")
        Form_checkin_settings.resize(950, 814)
        self.verticalLayout = QVBoxLayout(Form_checkin_settings)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBox_checkin_time_periods = QGroupBox(Form_checkin_settings)
        self.groupBox_checkin_time_periods.setObjectName(u"groupBox_checkin_time_periods")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_checkin_time_periods.sizePolicy().hasHeightForWidth())
        self.groupBox_checkin_time_periods.setSizePolicy(sizePolicy)
        self.gridLayout = QGridLayout(self.groupBox_checkin_time_periods)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(9, 9, 9, 9)
        self.scrollArea_time_periods = QScrollArea(self.groupBox_checkin_time_periods)
        self.scrollArea_time_periods.setObjectName(u"scrollArea_time_periods")
        sizePolicy.setHeightForWidth(self.scrollArea_time_periods.sizePolicy().hasHeightForWidth())
        self.scrollArea_time_periods.setSizePolicy(sizePolicy)
        self.scrollArea_time_periods.setWidgetResizable(True)
        self.scrollAreaWidgetContents_time_periods = QWidget()
        self.scrollAreaWidgetContents_time_periods.setObjectName(u"scrollAreaWidgetContents_time_periods")
        self.scrollAreaWidgetContents_time_periods.setGeometry(QRect(0, 0, 906, 459))
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetContents_time_periods.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents_time_periods.setSizePolicy(sizePolicy)
        self.verticalLayout_3 = QVBoxLayout(self.scrollAreaWidgetContents_time_periods)
        self.verticalLayout_3.setSpacing(4)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(4, 4, 4, 4)
        self.scrollArea_time_periods.setWidget(self.scrollAreaWidgetContents_time_periods)

        self.gridLayout.addWidget(self.scrollArea_time_periods, 0, 0, 1, 1)

        self.widget_time_period_buttons = QWidget(self.groupBox_checkin_time_periods)
        self.widget_time_period_buttons.setObjectName(u"widget_time_period_buttons")
        self.horizontalLayout_2 = QHBoxLayout(self.widget_time_period_buttons)
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(4, 4, 4, 4)
        self.pushButton_add_new_time_period = QPushButton(self.widget_time_period_buttons)
        self.pushButton_add_new_time_period.setObjectName(u"pushButton_add_new_time_period")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.pushButton_add_new_time_period.sizePolicy().hasHeightForWidth())
        self.pushButton_add_new_time_period.setSizePolicy(sizePolicy1)

        self.horizontalLayout_2.addWidget(self.pushButton_add_new_time_period)

        self.pushButton_undo_last__time_period_delete = QPushButton(self.widget_time_period_buttons)
        self.pushButton_undo_last__time_period_delete.setObjectName(u"pushButton_undo_last__time_period_delete")
        sizePolicy1.setHeightForWidth(self.pushButton_undo_last__time_period_delete.sizePolicy().hasHeightForWidth())
        self.pushButton_undo_last__time_period_delete.setSizePolicy(sizePolicy1)

        self.horizontalLayout_2.addWidget(self.pushButton_undo_last__time_period_delete)


        self.gridLayout.addWidget(self.widget_time_period_buttons, 1, 0, 1, 1, Qt.AlignmentFlag.AlignLeft)

        self.gridLayout.setRowStretch(0, 1)

        self.verticalLayout.addWidget(self.groupBox_checkin_time_periods)

        self.groupBox_checkin_questions = QGroupBox(Form_checkin_settings)
        self.groupBox_checkin_questions.setObjectName(u"groupBox_checkin_questions")
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_checkin_questions)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.scrollArea_checkin_questions = QScrollArea(self.groupBox_checkin_questions)
        self.scrollArea_checkin_questions.setObjectName(u"scrollArea_checkin_questions")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.scrollArea_checkin_questions.sizePolicy().hasHeightForWidth())
        self.scrollArea_checkin_questions.setSizePolicy(sizePolicy2)
        self.scrollArea_checkin_questions.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 906, 165))
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.widget_checkin_questions_container = QWidget(self.scrollAreaWidgetContents)
        self.widget_checkin_questions_container.setObjectName(u"widget_checkin_questions_container")
        sizePolicy2.setHeightForWidth(self.widget_checkin_questions_container.sizePolicy().hasHeightForWidth())
        self.widget_checkin_questions_container.setSizePolicy(sizePolicy2)
        self.gridLayout_2 = QGridLayout(self.widget_checkin_questions_container)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.checkBox_energy_level = QCheckBox(self.widget_checkin_questions_container)
        self.checkBox_energy_level.setObjectName(u"checkBox_energy_level")

        self.gridLayout_2.addWidget(self.checkBox_energy_level, 2, 0, 1, 1)

        self.checkBox_sleep_hours = QCheckBox(self.widget_checkin_questions_container)
        self.checkBox_sleep_hours.setObjectName(u"checkBox_sleep_hours")

        self.gridLayout_2.addWidget(self.checkBox_sleep_hours, 1, 1, 1, 1)

        self.checkBox_anxiety_level = QCheckBox(self.widget_checkin_questions_container)
        self.checkBox_anxiety_level.setObjectName(u"checkBox_anxiety_level")

        self.gridLayout_2.addWidget(self.checkBox_anxiety_level, 5, 0, 1, 1)

        self.checkBox_medication = QCheckBox(self.widget_checkin_questions_container)
        self.checkBox_medication.setObjectName(u"checkBox_medication")

        self.gridLayout_2.addWidget(self.checkBox_medication, 2, 1, 1, 1)

        self.checkBox_brushed_teeth = QCheckBox(self.widget_checkin_questions_container)
        self.checkBox_brushed_teeth.setObjectName(u"checkBox_brushed_teeth")

        self.gridLayout_2.addWidget(self.checkBox_brushed_teeth, 0, 1, 1, 1)

        self.checkBox_breakfast = QCheckBox(self.widget_checkin_questions_container)
        self.checkBox_breakfast.setObjectName(u"checkBox_breakfast")

        self.gridLayout_2.addWidget(self.checkBox_breakfast, 3, 1, 1, 1)

        self.checkBox_stress_level = QCheckBox(self.widget_checkin_questions_container)
        self.checkBox_stress_level.setObjectName(u"checkBox_stress_level")

        self.gridLayout_2.addWidget(self.checkBox_stress_level, 1, 0, 1, 1)

        self.checkBox_mood = QCheckBox(self.widget_checkin_questions_container)
        self.checkBox_mood.setObjectName(u"checkBox_mood")

        self.gridLayout_2.addWidget(self.checkBox_mood, 0, 0, 1, 1)

        self.checkBox_sleep_quality = QCheckBox(self.widget_checkin_questions_container)
        self.checkBox_sleep_quality.setObjectName(u"checkBox_sleep_quality")

        self.gridLayout_2.addWidget(self.checkBox_sleep_quality, 3, 0, 1, 1)

        self.checkBox_hydrated = QCheckBox(self.widget_checkin_questions_container)
        self.checkBox_hydrated.setObjectName(u"checkBox_hydrated")

        self.gridLayout_2.addWidget(self.checkBox_hydrated, 5, 1, 1, 1)

        self.checkBox_exercise = QCheckBox(self.widget_checkin_questions_container)
        self.checkBox_exercise.setObjectName(u"checkBox_exercise")

        self.gridLayout_2.addWidget(self.checkBox_exercise, 0, 2, 1, 1)

        self.checkBox_social_interaction = QCheckBox(self.widget_checkin_questions_container)
        self.checkBox_social_interaction.setObjectName(u"checkBox_social_interaction")

        self.gridLayout_2.addWidget(self.checkBox_social_interaction, 1, 2, 1, 1)

        self.checkBox_reflection_notes = QCheckBox(self.widget_checkin_questions_container)
        self.checkBox_reflection_notes.setObjectName(u"checkBox_reflection_notes")

        self.gridLayout_2.addWidget(self.checkBox_reflection_notes, 2, 2, 1, 1)

        self.widget_checkin_element_placeholder = QWidget(self.widget_checkin_questions_container)
        self.widget_checkin_element_placeholder.setObjectName(u"widget_checkin_element_placeholder")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.widget_checkin_element_placeholder.sizePolicy().hasHeightForWidth())
        self.widget_checkin_element_placeholder.setSizePolicy(sizePolicy3)
        self.horizontalLayout_4 = QHBoxLayout(self.widget_checkin_element_placeholder)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 10, 0)

        self.gridLayout_2.addWidget(self.widget_checkin_element_placeholder, 3, 2, 1, 1)

        self.gridLayout_2.setColumnStretch(0, 1)
        self.gridLayout_2.setColumnStretch(1, 1)
        self.gridLayout_2.setColumnStretch(2, 1)

        self.verticalLayout_2.addWidget(self.widget_checkin_questions_container)

        self.scrollArea_checkin_questions.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_4.addWidget(self.scrollArea_checkin_questions)

        self.widget_checkin_questions_buttons = QWidget(self.groupBox_checkin_questions)
        self.widget_checkin_questions_buttons.setObjectName(u"widget_checkin_questions_buttons")
        self.horizontalLayout_3 = QHBoxLayout(self.widget_checkin_questions_buttons)
        self.horizontalLayout_3.setSpacing(4)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(4, 4, 4, 4)
        self.pushButton_add_new_question = QPushButton(self.widget_checkin_questions_buttons)
        self.pushButton_add_new_question.setObjectName(u"pushButton_add_new_question")
        sizePolicy1.setHeightForWidth(self.pushButton_add_new_question.sizePolicy().hasHeightForWidth())
        self.pushButton_add_new_question.setSizePolicy(sizePolicy1)

        self.horizontalLayout_3.addWidget(self.pushButton_add_new_question)

        self.pushButton_undo_last_question_delete = QPushButton(self.widget_checkin_questions_buttons)
        self.pushButton_undo_last_question_delete.setObjectName(u"pushButton_undo_last_question_delete")
        sizePolicy1.setHeightForWidth(self.pushButton_undo_last_question_delete.sizePolicy().hasHeightForWidth())
        self.pushButton_undo_last_question_delete.setSizePolicy(sizePolicy1)

        self.horizontalLayout_3.addWidget(self.pushButton_undo_last_question_delete)


        self.verticalLayout_4.addWidget(self.widget_checkin_questions_buttons, 0, Qt.AlignmentFlag.AlignLeft)


        self.verticalLayout.addWidget(self.groupBox_checkin_questions)


        self.retranslateUi(Form_checkin_settings)

        QMetaObject.connectSlotsByName(Form_checkin_settings)
    # setupUi

    def retranslateUi(self, Form_checkin_settings):
        Form_checkin_settings.setWindowTitle(QCoreApplication.translate("Form_checkin_settings", u"Form", None))
        self.groupBox_checkin_time_periods.setTitle(QCoreApplication.translate("Form_checkin_settings", u"Check-in Time Periods", None))
        self.pushButton_add_new_time_period.setText(QCoreApplication.translate("Form_checkin_settings", u"Add New Period", None))
        self.pushButton_undo_last__time_period_delete.setText(QCoreApplication.translate("Form_checkin_settings", u"Undo Last Delete", None))
        self.groupBox_checkin_questions.setTitle(QCoreApplication.translate("Form_checkin_settings", u"Check-in Questions", None))
        self.checkBox_energy_level.setText(QCoreApplication.translate("Form_checkin_settings", u"Energy level (1-5 scale) (default)", None))
        self.checkBox_sleep_hours.setText(QCoreApplication.translate("Form_checkin_settings", u"Hours of sleep (number)", None))
        self.checkBox_anxiety_level.setText(QCoreApplication.translate("Form_checkin_settings", u"Anxiety level (1-5 scale)", None))
        self.checkBox_medication.setText(QCoreApplication.translate("Form_checkin_settings", u"Took medication (yes/no)", None))
        self.checkBox_brushed_teeth.setText(QCoreApplication.translate("Form_checkin_settings", u"Brushed teeth (yes/no)", None))
        self.checkBox_breakfast.setText(QCoreApplication.translate("Form_checkin_settings", u"Had breakfast (yes/no)", None))
        self.checkBox_stress_level.setText(QCoreApplication.translate("Form_checkin_settings", u"Stress level (1-5 scale) (default)", None))
        self.checkBox_mood.setText(QCoreApplication.translate("Form_checkin_settings", u"Mood (1-5 scale) (default)", None))
        self.checkBox_sleep_quality.setText(QCoreApplication.translate("Form_checkin_settings", u"Sleep quality (1-5 scale) (default)", None))
        self.checkBox_hydrated.setText(QCoreApplication.translate("Form_checkin_settings", u"Staying hydrated (yes/no)", None))
        self.checkBox_exercise.setText(QCoreApplication.translate("Form_checkin_settings", u"Did exercise (yes/no)", None))
        self.checkBox_social_interaction.setText(QCoreApplication.translate("Form_checkin_settings", u"Had social interaction (yes/no)", None))
        self.checkBox_reflection_notes.setText(QCoreApplication.translate("Form_checkin_settings", u"Brief reflection/notes (text)", None))
        self.pushButton_add_new_question.setText(QCoreApplication.translate("Form_checkin_settings", u"Add New Element", None))
        self.pushButton_undo_last_question_delete.setText(QCoreApplication.translate("Form_checkin_settings", u"Undo Last Delete", None))
    # retranslateUi

