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
    QGroupBox, QLabel, QLineEdit, QSizePolicy,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget)

class Ui_Form_user_profile_settings(object):
    def setupUi(self, Form_user_profile_settings):
        if not Form_user_profile_settings.objectName():
            Form_user_profile_settings.setObjectName(u"Form_user_profile_settings")
        Form_user_profile_settings.resize(600, 700)
        self.mainVerticalLayout = QVBoxLayout(Form_user_profile_settings)
        self.mainVerticalLayout.setObjectName(u"mainVerticalLayout")
        self.tabWidget = QTabWidget(Form_user_profile_settings)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_basic_info = QWidget()
        self.tab_basic_info.setObjectName(u"tab_basic_info")
        self.verticalLayout_basic_info = QVBoxLayout(self.tab_basic_info)
        self.verticalLayout_basic_info.setObjectName(u"verticalLayout_basic_info")
        self.groupBox_gender_identity = QGroupBox(self.tab_basic_info)
        self.groupBox_gender_identity.setObjectName(u"groupBox_gender_identity")
        self.gridLayout_gender = QGridLayout(self.groupBox_gender_identity)
        self.gridLayout_gender.setObjectName(u"gridLayout_gender")
        self.checkBox_woman = QCheckBox(self.groupBox_gender_identity)
        self.checkBox_woman.setObjectName(u"checkBox_woman")

        self.gridLayout_gender.addWidget(self.checkBox_woman, 0, 0, 1, 1)

        self.checkBox_man = QCheckBox(self.groupBox_gender_identity)
        self.checkBox_man.setObjectName(u"checkBox_man")

        self.gridLayout_gender.addWidget(self.checkBox_man, 0, 1, 1, 1)

        self.checkBox_nonbinary = QCheckBox(self.groupBox_gender_identity)
        self.checkBox_nonbinary.setObjectName(u"checkBox_nonbinary")

        self.gridLayout_gender.addWidget(self.checkBox_nonbinary, 0, 2, 1, 1)

        self.checkBox_none = QCheckBox(self.groupBox_gender_identity)
        self.checkBox_none.setObjectName(u"checkBox_none")

        self.gridLayout_gender.addWidget(self.checkBox_none, 1, 0, 1, 1)

        self.checkBox_prefer_not_to_say = QCheckBox(self.groupBox_gender_identity)
        self.checkBox_prefer_not_to_say.setObjectName(u"checkBox_prefer_not_to_say")

        self.gridLayout_gender.addWidget(self.checkBox_prefer_not_to_say, 1, 1, 1, 1)

        self.lineEdit_custom_gender = QLineEdit(self.groupBox_gender_identity)
        self.lineEdit_custom_gender.setObjectName(u"lineEdit_custom_gender")

        self.gridLayout_gender.addWidget(self.lineEdit_custom_gender, 1, 2, 1, 1)


        self.verticalLayout_basic_info.addWidget(self.groupBox_gender_identity)

        self.groupBox_date_of_birth = QGroupBox(self.tab_basic_info)
        self.groupBox_date_of_birth.setObjectName(u"groupBox_date_of_birth")
        self.verticalLayout_dob = QVBoxLayout(self.groupBox_date_of_birth)
        self.verticalLayout_dob.setObjectName(u"verticalLayout_dob")
        self.calendarWidget_date_of_birth = QCalendarWidget(self.groupBox_date_of_birth)
        self.calendarWidget_date_of_birth.setObjectName(u"calendarWidget_date_of_birth")

        self.verticalLayout_dob.addWidget(self.calendarWidget_date_of_birth)


        self.verticalLayout_basic_info.addWidget(self.groupBox_date_of_birth)

        self.tabWidget.addTab(self.tab_basic_info, "")
        self.tab_health = QWidget()
        self.tab_health.setObjectName(u"tab_health")
        self.verticalLayout_health = QVBoxLayout(self.tab_health)
        self.verticalLayout_health.setObjectName(u"verticalLayout_health")
        self.groupBox_medical = QGroupBox(self.tab_health)
        self.groupBox_medical.setObjectName(u"groupBox_medical")
        self.gridLayout_medical = QGridLayout(self.groupBox_medical)
        self.gridLayout_medical.setObjectName(u"gridLayout_medical")
        self.checkBox_depression = QCheckBox(self.groupBox_medical)
        self.checkBox_depression.setObjectName(u"checkBox_depression")

        self.gridLayout_medical.addWidget(self.checkBox_depression, 0, 0, 1, 1)

        self.checkBox_anxiety = QCheckBox(self.groupBox_medical)
        self.checkBox_anxiety.setObjectName(u"checkBox_anxiety")

        self.gridLayout_medical.addWidget(self.checkBox_anxiety, 0, 1, 1, 1)

        self.checkBox_adhd = QCheckBox(self.groupBox_medical)
        self.checkBox_adhd.setObjectName(u"checkBox_adhd")

        self.gridLayout_medical.addWidget(self.checkBox_adhd, 0, 2, 1, 1)

        self.checkBox_bipolar = QCheckBox(self.groupBox_medical)
        self.checkBox_bipolar.setObjectName(u"checkBox_bipolar")

        self.gridLayout_medical.addWidget(self.checkBox_bipolar, 1, 0, 1, 1)

        self.checkBox_ptsd = QCheckBox(self.groupBox_medical)
        self.checkBox_ptsd.setObjectName(u"checkBox_ptsd")

        self.gridLayout_medical.addWidget(self.checkBox_ptsd, 1, 1, 1, 1)

        self.checkBox_ocd = QCheckBox(self.groupBox_medical)
        self.checkBox_ocd.setObjectName(u"checkBox_ocd")

        self.gridLayout_medical.addWidget(self.checkBox_ocd, 1, 2, 1, 1)

        self.checkBox_eating_disorder = QCheckBox(self.groupBox_medical)
        self.checkBox_eating_disorder.setObjectName(u"checkBox_eating_disorder")

        self.gridLayout_medical.addWidget(self.checkBox_eating_disorder, 2, 0, 1, 1)

        self.checkBox_substance_abuse = QCheckBox(self.groupBox_medical)
        self.checkBox_substance_abuse.setObjectName(u"checkBox_substance_abuse")

        self.gridLayout_medical.addWidget(self.checkBox_substance_abuse, 2, 1, 1, 1)

        self.checkBox_sleep_disorder = QCheckBox(self.groupBox_medical)
        self.checkBox_sleep_disorder.setObjectName(u"checkBox_sleep_disorder")

        self.gridLayout_medical.addWidget(self.checkBox_sleep_disorder, 2, 2, 1, 1)

        self.checkBox_chronic_pain = QCheckBox(self.groupBox_medical)
        self.checkBox_chronic_pain.setObjectName(u"checkBox_chronic_pain")

        self.gridLayout_medical.addWidget(self.checkBox_chronic_pain, 3, 0, 1, 1)

        self.checkBox_autism = QCheckBox(self.groupBox_medical)
        self.checkBox_autism.setObjectName(u"checkBox_autism")

        self.gridLayout_medical.addWidget(self.checkBox_autism, 3, 1, 1, 1)

        self.checkBox_other_mental_health = QCheckBox(self.groupBox_medical)
        self.checkBox_other_mental_health.setObjectName(u"checkBox_other_mental_health")

        self.gridLayout_medical.addWidget(self.checkBox_other_mental_health, 3, 2, 1, 1)


        self.verticalLayout_health.addWidget(self.groupBox_medical)

        self.groupBox_medications = QGroupBox(self.tab_health)
        self.groupBox_medications.setObjectName(u"groupBox_medications")
        self.gridLayout_medications = QGridLayout(self.groupBox_medications)
        self.gridLayout_medications.setObjectName(u"gridLayout_medications")
        self.checkBox_antidepressants = QCheckBox(self.groupBox_medications)
        self.checkBox_antidepressants.setObjectName(u"checkBox_antidepressants")

        self.gridLayout_medications.addWidget(self.checkBox_antidepressants, 0, 0, 1, 1)

        self.checkBox_anxiety_meds = QCheckBox(self.groupBox_medications)
        self.checkBox_anxiety_meds.setObjectName(u"checkBox_anxiety_meds")

        self.gridLayout_medications.addWidget(self.checkBox_anxiety_meds, 0, 1, 1, 1)

        self.checkBox_adhd_meds = QCheckBox(self.groupBox_medications)
        self.checkBox_adhd_meds.setObjectName(u"checkBox_adhd_meds")

        self.gridLayout_medications.addWidget(self.checkBox_adhd_meds, 0, 2, 1, 1)

        self.checkBox_mood_stabilizers = QCheckBox(self.groupBox_medications)
        self.checkBox_mood_stabilizers.setObjectName(u"checkBox_mood_stabilizers")

        self.gridLayout_medications.addWidget(self.checkBox_mood_stabilizers, 1, 0, 1, 1)

        self.checkBox_sleep_meds = QCheckBox(self.groupBox_medications)
        self.checkBox_sleep_meds.setObjectName(u"checkBox_sleep_meds")

        self.gridLayout_medications.addWidget(self.checkBox_sleep_meds, 1, 1, 1, 1)

        self.checkBox_pain_meds = QCheckBox(self.groupBox_medications)
        self.checkBox_pain_meds.setObjectName(u"checkBox_pain_meds")

        self.gridLayout_medications.addWidget(self.checkBox_pain_meds, 1, 2, 1, 1)

        self.lineEdit_custom_medications = QLineEdit(self.groupBox_medications)
        self.lineEdit_custom_medications.setObjectName(u"lineEdit_custom_medications")

        self.gridLayout_medications.addWidget(self.lineEdit_custom_medications, 2, 0, 1, 3)


        self.verticalLayout_health.addWidget(self.groupBox_medications)

        self.groupBox_reminders_needed = QGroupBox(self.tab_health)
        self.groupBox_reminders_needed.setObjectName(u"groupBox_reminders_needed")
        self.verticalLayout_reminders_needed = QVBoxLayout(self.groupBox_reminders_needed)
        self.verticalLayout_reminders_needed.setObjectName(u"verticalLayout_reminders_needed")
        self.label_reminders_placeholder = QLabel(self.groupBox_reminders_needed)
        self.label_reminders_placeholder.setObjectName(u"label_reminders_placeholder")

        self.verticalLayout_reminders_needed.addWidget(self.label_reminders_placeholder)


        self.verticalLayout_health.addWidget(self.groupBox_reminders_needed)

        self.groupBox_allergies = QGroupBox(self.tab_health)
        self.groupBox_allergies.setObjectName(u"groupBox_allergies")
        self.gridLayout_allergies = QGridLayout(self.groupBox_allergies)
        self.gridLayout_allergies.setObjectName(u"gridLayout_allergies")
        self.checkBox_food_allergies = QCheckBox(self.groupBox_allergies)
        self.checkBox_food_allergies.setObjectName(u"checkBox_food_allergies")

        self.gridLayout_allergies.addWidget(self.checkBox_food_allergies, 0, 0, 1, 1)

        self.checkBox_medication_allergies = QCheckBox(self.groupBox_allergies)
        self.checkBox_medication_allergies.setObjectName(u"checkBox_medication_allergies")

        self.gridLayout_allergies.addWidget(self.checkBox_medication_allergies, 0, 1, 1, 1)

        self.checkBox_environmental_allergies = QCheckBox(self.groupBox_allergies)
        self.checkBox_environmental_allergies.setObjectName(u"checkBox_environmental_allergies")

        self.gridLayout_allergies.addWidget(self.checkBox_environmental_allergies, 0, 2, 1, 1)

        self.checkBox_latex_allergy = QCheckBox(self.groupBox_allergies)
        self.checkBox_latex_allergy.setObjectName(u"checkBox_latex_allergy")

        self.gridLayout_allergies.addWidget(self.checkBox_latex_allergy, 1, 0, 1, 1)

        self.checkBox_gluten_sensitivity = QCheckBox(self.groupBox_allergies)
        self.checkBox_gluten_sensitivity.setObjectName(u"checkBox_gluten_sensitivity")

        self.gridLayout_allergies.addWidget(self.checkBox_gluten_sensitivity, 1, 1, 1, 1)

        self.checkBox_lactose_intolerance = QCheckBox(self.groupBox_allergies)
        self.checkBox_lactose_intolerance.setObjectName(u"checkBox_lactose_intolerance")

        self.gridLayout_allergies.addWidget(self.checkBox_lactose_intolerance, 1, 2, 1, 1)

        self.lineEdit_custom_allergies = QLineEdit(self.groupBox_allergies)
        self.lineEdit_custom_allergies.setObjectName(u"lineEdit_custom_allergies")

        self.gridLayout_allergies.addWidget(self.lineEdit_custom_allergies, 2, 0, 1, 3)


        self.verticalLayout_health.addWidget(self.groupBox_allergies)

        self.tabWidget.addTab(self.tab_health, "")
        self.tab_interests = QWidget()
        self.tab_interests.setObjectName(u"tab_interests")
        self.verticalLayout_interests = QVBoxLayout(self.tab_interests)
        self.verticalLayout_interests.setObjectName(u"verticalLayout_interests")
        self.groupBox_interests = QGroupBox(self.tab_interests)
        self.groupBox_interests.setObjectName(u"groupBox_interests")
        self.gridLayout_interests = QGridLayout(self.groupBox_interests)
        self.gridLayout_interests.setObjectName(u"gridLayout_interests")
        self.checkBox_reading = QCheckBox(self.groupBox_interests)
        self.checkBox_reading.setObjectName(u"checkBox_reading")

        self.gridLayout_interests.addWidget(self.checkBox_reading, 0, 0, 1, 1)

        self.checkBox_writing = QCheckBox(self.groupBox_interests)
        self.checkBox_writing.setObjectName(u"checkBox_writing")

        self.gridLayout_interests.addWidget(self.checkBox_writing, 0, 1, 1, 1)

        self.checkBox_music = QCheckBox(self.groupBox_interests)
        self.checkBox_music.setObjectName(u"checkBox_music")

        self.gridLayout_interests.addWidget(self.checkBox_music, 0, 2, 1, 1)

        self.checkBox_art = QCheckBox(self.groupBox_interests)
        self.checkBox_art.setObjectName(u"checkBox_art")

        self.gridLayout_interests.addWidget(self.checkBox_art, 1, 0, 1, 1)

        self.checkBox_gaming = QCheckBox(self.groupBox_interests)
        self.checkBox_gaming.setObjectName(u"checkBox_gaming")

        self.gridLayout_interests.addWidget(self.checkBox_gaming, 1, 1, 1, 1)

        self.checkBox_cooking = QCheckBox(self.groupBox_interests)
        self.checkBox_cooking.setObjectName(u"checkBox_cooking")

        self.gridLayout_interests.addWidget(self.checkBox_cooking, 1, 2, 1, 1)

        self.checkBox_exercise = QCheckBox(self.groupBox_interests)
        self.checkBox_exercise.setObjectName(u"checkBox_exercise")

        self.gridLayout_interests.addWidget(self.checkBox_exercise, 2, 0, 1, 1)

        self.checkBox_nature = QCheckBox(self.groupBox_interests)
        self.checkBox_nature.setObjectName(u"checkBox_nature")

        self.gridLayout_interests.addWidget(self.checkBox_nature, 2, 1, 1, 1)

        self.checkBox_technology = QCheckBox(self.groupBox_interests)
        self.checkBox_technology.setObjectName(u"checkBox_technology")

        self.gridLayout_interests.addWidget(self.checkBox_technology, 2, 2, 1, 1)

        self.checkBox_photography = QCheckBox(self.groupBox_interests)
        self.checkBox_photography.setObjectName(u"checkBox_photography")

        self.gridLayout_interests.addWidget(self.checkBox_photography, 3, 0, 1, 1)

        self.checkBox_travel = QCheckBox(self.groupBox_interests)
        self.checkBox_travel.setObjectName(u"checkBox_travel")

        self.gridLayout_interests.addWidget(self.checkBox_travel, 3, 1, 1, 1)

        self.checkBox_volunteering = QCheckBox(self.groupBox_interests)
        self.checkBox_volunteering.setObjectName(u"checkBox_volunteering")

        self.gridLayout_interests.addWidget(self.checkBox_volunteering, 3, 2, 1, 1)

        self.lineEdit_custom_interest = QLineEdit(self.groupBox_interests)
        self.lineEdit_custom_interest.setObjectName(u"lineEdit_custom_interest")

        self.gridLayout_interests.addWidget(self.lineEdit_custom_interest, 4, 0, 1, 3)


        self.verticalLayout_interests.addWidget(self.groupBox_interests)

        self.groupBox_activities_for_encouragement = QGroupBox(self.tab_interests)
        self.groupBox_activities_for_encouragement.setObjectName(u"groupBox_activities_for_encouragement")
        self.verticalLayout_activities_for_encouragement = QVBoxLayout(self.groupBox_activities_for_encouragement)
        self.verticalLayout_activities_for_encouragement.setObjectName(u"verticalLayout_activities_for_encouragement")
        self.label_activities_placeholder = QLabel(self.groupBox_activities_for_encouragement)
        self.label_activities_placeholder.setObjectName(u"label_activities_placeholder")

        self.verticalLayout_activities_for_encouragement.addWidget(self.label_activities_placeholder)


        self.verticalLayout_interests.addWidget(self.groupBox_activities_for_encouragement)

        self.tabWidget.addTab(self.tab_interests, "")
        self.tab_goals = QWidget()
        self.tab_goals.setObjectName(u"tab_goals")
        self.verticalLayout_goals = QVBoxLayout(self.tab_goals)
        self.verticalLayout_goals.setObjectName(u"verticalLayout_goals")
        self.groupBox_goals = QGroupBox(self.tab_goals)
        self.groupBox_goals.setObjectName(u"groupBox_goals")
        self.gridLayout_goals = QGridLayout(self.groupBox_goals)
        self.gridLayout_goals.setObjectName(u"gridLayout_goals")
        self.checkBox_mental_health_goals = QCheckBox(self.groupBox_goals)
        self.checkBox_mental_health_goals.setObjectName(u"checkBox_mental_health_goals")

        self.gridLayout_goals.addWidget(self.checkBox_mental_health_goals, 0, 0, 1, 1)

        self.checkBox_physical_health_goals = QCheckBox(self.groupBox_goals)
        self.checkBox_physical_health_goals.setObjectName(u"checkBox_physical_health_goals")

        self.gridLayout_goals.addWidget(self.checkBox_physical_health_goals, 0, 1, 1, 1)

        self.checkBox_career_goals = QCheckBox(self.groupBox_goals)
        self.checkBox_career_goals.setObjectName(u"checkBox_career_goals")

        self.gridLayout_goals.addWidget(self.checkBox_career_goals, 0, 2, 1, 1)

        self.checkBox_education_goals = QCheckBox(self.groupBox_goals)
        self.checkBox_education_goals.setObjectName(u"checkBox_education_goals")

        self.gridLayout_goals.addWidget(self.checkBox_education_goals, 1, 0, 1, 1)

        self.checkBox_relationship_goals = QCheckBox(self.groupBox_goals)
        self.checkBox_relationship_goals.setObjectName(u"checkBox_relationship_goals")

        self.gridLayout_goals.addWidget(self.checkBox_relationship_goals, 1, 1, 1, 1)

        self.checkBox_financial_goals = QCheckBox(self.groupBox_goals)
        self.checkBox_financial_goals.setObjectName(u"checkBox_financial_goals")

        self.gridLayout_goals.addWidget(self.checkBox_financial_goals, 1, 2, 1, 1)

        self.checkBox_creative_goals = QCheckBox(self.groupBox_goals)
        self.checkBox_creative_goals.setObjectName(u"checkBox_creative_goals")

        self.gridLayout_goals.addWidget(self.checkBox_creative_goals, 2, 0, 1, 1)

        self.checkBox_social_goals = QCheckBox(self.groupBox_goals)
        self.checkBox_social_goals.setObjectName(u"checkBox_social_goals")

        self.gridLayout_goals.addWidget(self.checkBox_social_goals, 2, 1, 1, 1)

        self.checkBox_spiritual_goals = QCheckBox(self.groupBox_goals)
        self.checkBox_spiritual_goals.setObjectName(u"checkBox_spiritual_goals")

        self.gridLayout_goals.addWidget(self.checkBox_spiritual_goals, 2, 2, 1, 1)

        self.lineEdit_custom_goal = QLineEdit(self.groupBox_goals)
        self.lineEdit_custom_goal.setObjectName(u"lineEdit_custom_goal")

        self.gridLayout_goals.addWidget(self.lineEdit_custom_goal, 3, 0, 1, 3)


        self.verticalLayout_goals.addWidget(self.groupBox_goals)

        self.groupBox_goals_placeholder = QGroupBox(self.tab_goals)
        self.groupBox_goals_placeholder.setObjectName(u"groupBox_goals_placeholder")
        self.verticalLayout_goals_placeholder = QVBoxLayout(self.groupBox_goals_placeholder)
        self.verticalLayout_goals_placeholder.setObjectName(u"verticalLayout_goals_placeholder")
        self.label_goals_placeholder = QLabel(self.groupBox_goals_placeholder)
        self.label_goals_placeholder.setObjectName(u"label_goals_placeholder")

        self.verticalLayout_goals_placeholder.addWidget(self.label_goals_placeholder)


        self.verticalLayout_goals.addWidget(self.groupBox_goals_placeholder)

        self.tabWidget.addTab(self.tab_goals, "")
        self.tab_support_notes = QWidget()
        self.tab_support_notes.setObjectName(u"tab_support_notes")
        self.verticalLayout_support_notes = QVBoxLayout(self.tab_support_notes)
        self.verticalLayout_support_notes.setObjectName(u"verticalLayout_support_notes")
        self.groupBox_loved_ones = QGroupBox(self.tab_support_notes)
        self.groupBox_loved_ones.setObjectName(u"groupBox_loved_ones")
        self.verticalLayout_loved_ones = QVBoxLayout(self.groupBox_loved_ones)
        self.verticalLayout_loved_ones.setObjectName(u"verticalLayout_loved_ones")
        self.textEdit_loved_ones = QTextEdit(self.groupBox_loved_ones)
        self.textEdit_loved_ones.setObjectName(u"textEdit_loved_ones")

        self.verticalLayout_loved_ones.addWidget(self.textEdit_loved_ones)


        self.verticalLayout_support_notes.addWidget(self.groupBox_loved_ones)

        self.groupBox_notes = QGroupBox(self.tab_support_notes)
        self.groupBox_notes.setObjectName(u"groupBox_notes")
        self.verticalLayout_notes = QVBoxLayout(self.groupBox_notes)
        self.verticalLayout_notes.setObjectName(u"verticalLayout_notes")
        self.textEdit_notes = QTextEdit(self.groupBox_notes)
        self.textEdit_notes.setObjectName(u"textEdit_notes")

        self.verticalLayout_notes.addWidget(self.textEdit_notes)


        self.verticalLayout_support_notes.addWidget(self.groupBox_notes)

        self.tabWidget.addTab(self.tab_support_notes, "")

        self.mainVerticalLayout.addWidget(self.tabWidget)


        self.retranslateUi(Form_user_profile_settings)

        self.tabWidget.setCurrentIndex(4)


        QMetaObject.connectSlotsByName(Form_user_profile_settings)
    # setupUi

    def retranslateUi(self, Form_user_profile_settings):
        Form_user_profile_settings.setWindowTitle(QCoreApplication.translate("Form_user_profile_settings", u"User Profile Settings", None))
        self.groupBox_gender_identity.setTitle(QCoreApplication.translate("Form_user_profile_settings", u"Gender Identity", None))
        self.checkBox_woman.setText(QCoreApplication.translate("Form_user_profile_settings", u"Woman", None))
        self.checkBox_man.setText(QCoreApplication.translate("Form_user_profile_settings", u"Man", None))
        self.checkBox_nonbinary.setText(QCoreApplication.translate("Form_user_profile_settings", u"Non-binary", None))
        self.checkBox_none.setText(QCoreApplication.translate("Form_user_profile_settings", u"None", None))
        self.checkBox_prefer_not_to_say.setText(QCoreApplication.translate("Form_user_profile_settings", u"Prefer not to say", None))
        self.lineEdit_custom_gender.setPlaceholderText(QCoreApplication.translate("Form_user_profile_settings", u"Custom...", None))
        self.groupBox_date_of_birth.setTitle(QCoreApplication.translate("Form_user_profile_settings", u"Date of Birth", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_basic_info), QCoreApplication.translate("Form_user_profile_settings", u"Basic Info", None))
        self.groupBox_medical.setTitle(QCoreApplication.translate("Form_user_profile_settings", u"Health and Medical", None))
        self.checkBox_depression.setText(QCoreApplication.translate("Form_user_profile_settings", u"Depression", None))
        self.checkBox_anxiety.setText(QCoreApplication.translate("Form_user_profile_settings", u"Anxiety", None))
        self.checkBox_adhd.setText(QCoreApplication.translate("Form_user_profile_settings", u"ADHD", None))
        self.checkBox_bipolar.setText(QCoreApplication.translate("Form_user_profile_settings", u"Bipolar Disorder", None))
        self.checkBox_ptsd.setText(QCoreApplication.translate("Form_user_profile_settings", u"PTSD", None))
        self.checkBox_ocd.setText(QCoreApplication.translate("Form_user_profile_settings", u"OCD", None))
        self.checkBox_eating_disorder.setText(QCoreApplication.translate("Form_user_profile_settings", u"Eating Disorder", None))
        self.checkBox_substance_abuse.setText(QCoreApplication.translate("Form_user_profile_settings", u"Substance Abuse", None))
        self.checkBox_sleep_disorder.setText(QCoreApplication.translate("Form_user_profile_settings", u"Sleep Disorder", None))
        self.checkBox_chronic_pain.setText(QCoreApplication.translate("Form_user_profile_settings", u"Chronic Pain", None))
        self.checkBox_autism.setText(QCoreApplication.translate("Form_user_profile_settings", u"Autism Spectrum", None))
        self.checkBox_other_mental_health.setText(QCoreApplication.translate("Form_user_profile_settings", u"Other Mental Health", None))
        self.groupBox_medications.setTitle(QCoreApplication.translate("Form_user_profile_settings", u"Medications", None))
        self.checkBox_antidepressants.setText(QCoreApplication.translate("Form_user_profile_settings", u"Antidepressants", None))
        self.checkBox_anxiety_meds.setText(QCoreApplication.translate("Form_user_profile_settings", u"Anti-Anxiety", None))
        self.checkBox_adhd_meds.setText(QCoreApplication.translate("Form_user_profile_settings", u"ADHD Medication", None))
        self.checkBox_mood_stabilizers.setText(QCoreApplication.translate("Form_user_profile_settings", u"Mood Stabilizers", None))
        self.checkBox_sleep_meds.setText(QCoreApplication.translate("Form_user_profile_settings", u"Sleep Medication", None))
        self.checkBox_pain_meds.setText(QCoreApplication.translate("Form_user_profile_settings", u"Pain Medication", None))
        self.lineEdit_custom_medications.setPlaceholderText(QCoreApplication.translate("Form_user_profile_settings", u"Add custom medication", None))
        self.groupBox_reminders_needed.setTitle(QCoreApplication.translate("Form_user_profile_settings", u"Reminders Needed", None))
        self.label_reminders_placeholder.setText(QCoreApplication.translate("Form_user_profile_settings", u"Reminders feature coming soon...", None))
        self.groupBox_allergies.setTitle(QCoreApplication.translate("Form_user_profile_settings", u"Allergies & Sensitivities", None))
        self.checkBox_food_allergies.setText(QCoreApplication.translate("Form_user_profile_settings", u"Food Allergies", None))
        self.checkBox_medication_allergies.setText(QCoreApplication.translate("Form_user_profile_settings", u"Medication Allergies", None))
        self.checkBox_environmental_allergies.setText(QCoreApplication.translate("Form_user_profile_settings", u"Environmental", None))
        self.checkBox_latex_allergy.setText(QCoreApplication.translate("Form_user_profile_settings", u"Latex Allergy", None))
        self.checkBox_gluten_sensitivity.setText(QCoreApplication.translate("Form_user_profile_settings", u"Gluten Sensitivity", None))
        self.checkBox_lactose_intolerance.setText(QCoreApplication.translate("Form_user_profile_settings", u"Lactose Intolerance", None))
        self.lineEdit_custom_allergies.setPlaceholderText(QCoreApplication.translate("Form_user_profile_settings", u"Add custom allergy/sensitivity", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_health), QCoreApplication.translate("Form_user_profile_settings", u"Health", None))
        self.groupBox_interests.setTitle(QCoreApplication.translate("Form_user_profile_settings", u"Interests", None))
        self.checkBox_reading.setText(QCoreApplication.translate("Form_user_profile_settings", u"Reading", None))
        self.checkBox_writing.setText(QCoreApplication.translate("Form_user_profile_settings", u"Writing", None))
        self.checkBox_music.setText(QCoreApplication.translate("Form_user_profile_settings", u"Music", None))
        self.checkBox_art.setText(QCoreApplication.translate("Form_user_profile_settings", u"Art & Drawing", None))
        self.checkBox_gaming.setText(QCoreApplication.translate("Form_user_profile_settings", u"Gaming", None))
        self.checkBox_cooking.setText(QCoreApplication.translate("Form_user_profile_settings", u"Cooking", None))
        self.checkBox_exercise.setText(QCoreApplication.translate("Form_user_profile_settings", u"Exercise", None))
        self.checkBox_nature.setText(QCoreApplication.translate("Form_user_profile_settings", u"Nature & Outdoors", None))
        self.checkBox_technology.setText(QCoreApplication.translate("Form_user_profile_settings", u"Technology", None))
        self.checkBox_photography.setText(QCoreApplication.translate("Form_user_profile_settings", u"Photography", None))
        self.checkBox_travel.setText(QCoreApplication.translate("Form_user_profile_settings", u"Travel", None))
        self.checkBox_volunteering.setText(QCoreApplication.translate("Form_user_profile_settings", u"Volunteering", None))
        self.lineEdit_custom_interest.setPlaceholderText(QCoreApplication.translate("Form_user_profile_settings", u"Add custom interest", None))
        self.groupBox_activities_for_encouragement.setTitle(QCoreApplication.translate("Form_user_profile_settings", u"Activities for Encouragement", None))
        self.label_activities_placeholder.setText(QCoreApplication.translate("Form_user_profile_settings", u"Activities for encouragement coming soon...", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_interests), QCoreApplication.translate("Form_user_profile_settings", u"Interests", None))
        self.groupBox_goals.setTitle(QCoreApplication.translate("Form_user_profile_settings", u"Goals & Aspirations", None))
        self.checkBox_mental_health_goals.setText(QCoreApplication.translate("Form_user_profile_settings", u"Mental Health", None))
        self.checkBox_physical_health_goals.setText(QCoreApplication.translate("Form_user_profile_settings", u"Physical Health", None))
        self.checkBox_career_goals.setText(QCoreApplication.translate("Form_user_profile_settings", u"Career", None))
        self.checkBox_education_goals.setText(QCoreApplication.translate("Form_user_profile_settings", u"Education", None))
        self.checkBox_relationship_goals.setText(QCoreApplication.translate("Form_user_profile_settings", u"Relationships", None))
        self.checkBox_financial_goals.setText(QCoreApplication.translate("Form_user_profile_settings", u"Financial", None))
        self.checkBox_creative_goals.setText(QCoreApplication.translate("Form_user_profile_settings", u"Creative", None))
        self.checkBox_social_goals.setText(QCoreApplication.translate("Form_user_profile_settings", u"Social", None))
        self.checkBox_spiritual_goals.setText(QCoreApplication.translate("Form_user_profile_settings", u"Spiritual", None))
        self.lineEdit_custom_goal.setPlaceholderText(QCoreApplication.translate("Form_user_profile_settings", u"Add custom goal", None))
        self.groupBox_goals_placeholder.setTitle(QCoreApplication.translate("Form_user_profile_settings", u"Goals (detailed entry coming soon)", None))
        self.label_goals_placeholder.setText(QCoreApplication.translate("Form_user_profile_settings", u"Detailed goals entry coming soon...", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_goals), QCoreApplication.translate("Form_user_profile_settings", u"Goals", None))
        self.groupBox_loved_ones.setTitle(QCoreApplication.translate("Form_user_profile_settings", u"Loved Ones & Support Network", None))
        self.textEdit_loved_ones.setPlaceholderText(QCoreApplication.translate("Form_user_profile_settings", u"List important people in your life (family, friends, therapists, etc.) and their relationships to you...", None))
        self.groupBox_notes.setTitle(QCoreApplication.translate("Form_user_profile_settings", u"Additional Notes", None))
        self.textEdit_notes.setPlaceholderText(QCoreApplication.translate("Form_user_profile_settings", u"Any additional information you'd like to share about yourself, your preferences, or anything else that might help personalize your experience...", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_support_notes), QCoreApplication.translate("Form_user_profile_settings", u"Support & Notes", None))
    # retranslateUi

