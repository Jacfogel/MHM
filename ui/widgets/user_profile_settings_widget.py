# user_profile_settings_widget.py - User profile settings widget implementation

import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

# Import generated UI class
from ui.generated.user_profile_settings_widget_pyqt import Ui_Form_user_profile_settings

# Import core functionality
from core.user_management import get_timezone_options
from core.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

class UserProfileSettingsWidget(QWidget):
    """Widget for user profile settings configuration."""
    
    def __init__(self, parent=None, user_id: Optional[str] = None, existing_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.existing_data = existing_data or {}
        
        # Setup UI
        self.ui = Ui_Form_user_profile_settings()
        self.ui.setupUi(self)
        
        # Add preferred name field at the top of Basic Info
        if hasattr(self.ui, 'verticalLayout_basic_info') and not hasattr(self.ui, 'lineEdit_preferred_name'):
            from PySide6.QtWidgets import QLineEdit, QLabel
            self.ui.label_preferred_name = QLabel("Preferred Name:")
            self.ui.lineEdit_preferred_name = QLineEdit()
            self.ui.lineEdit_preferred_name.setObjectName('lineEdit_preferred_name')
            self.ui.verticalLayout_basic_info.insertWidget(0, self.ui.label_preferred_name)
            self.ui.verticalLayout_basic_info.insertWidget(1, self.ui.lineEdit_preferred_name)
        
        # Populate timezone options
        self.populate_timezones()
        
        # Set default tab to Basic Info (index 0)
        if hasattr(self.ui, 'tabWidget'):
            self.ui.tabWidget.setCurrentIndex(0)
        
        # Load existing data
        self.load_existing_data()
    
    def populate_timezones(self):
        """Populate the timezone combo box with options and enable selection."""
        if hasattr(self.ui, 'comboBox_timezone'):
            from core.user_management import get_timezone_options
            self.ui.comboBox_timezone.setEnabled(True)
            self.ui.comboBox_timezone.clear()
            self.ui.comboBox_timezone.addItems(get_timezone_options())
    
    def load_existing_data(self):
        """Load existing personalization data into the form."""
        try:
            # Preferred Name
            if hasattr(self.ui, 'lineEdit_preferred_name'):
                self.ui.lineEdit_preferred_name.setText(self.existing_data.get('preferred_name', ''))

            # Gender Identity
            gender_identity = self.existing_data.get('gender_identity', [])
            if hasattr(self.ui, 'checkBox_woman'):
                self.ui.checkBox_woman.setChecked('Woman' in gender_identity)
            if hasattr(self.ui, 'checkBox_man'):
                self.ui.checkBox_man.setChecked('Man' in gender_identity)
            if hasattr(self.ui, 'checkBox_nonbinary'):
                self.ui.checkBox_nonbinary.setChecked('Non-binary' in gender_identity)
            if hasattr(self.ui, 'checkBox_none'):
                self.ui.checkBox_none.setChecked('None' in gender_identity)
            if hasattr(self.ui, 'checkBox_prefer_not_to_say'):
                self.ui.checkBox_prefer_not_to_say.setChecked('Prefer not to say' in gender_identity)
            if hasattr(self.ui, 'lineEdit_custom_gender'):
                custom_genders = [g for g in gender_identity if g not in [
                    'Woman', 'Man', 'Non-binary', 'None', 'Prefer not to say']]
                self.ui.lineEdit_custom_gender.setText(', '.join(custom_genders))

            # Timezone
            if hasattr(self.ui, 'comboBox_timezone'):
                tz = self.existing_data.get('timezone', '')
                if tz:
                    idx = self.ui.comboBox_timezone.findText(tz)
                    if idx >= 0:
                        self.ui.comboBox_timezone.setCurrentIndex(idx)
                    else:
                        # If timezone not found, try to set a reasonable default
                        # Try to find a timezone with similar name
                        for i in range(self.ui.comboBox_timezone.count()):
                            item_text = self.ui.comboBox_timezone.itemText(i)
                            if tz.lower() in item_text.lower() or item_text.lower() in tz.lower():
                                self.ui.comboBox_timezone.setCurrentIndex(i)
                                break
                        else:
                            # If no match found, set to UTC as fallback
                            utc_idx = self.ui.comboBox_timezone.findText("UTC")
                            if utc_idx >= 0:
                                self.ui.comboBox_timezone.setCurrentIndex(utc_idx)
                            else:
                                self.ui.comboBox_timezone.setCurrentIndex(0)

            # Health conditions (available in UI) - handle nested structure
            custom_fields = self.existing_data.get('custom_fields', {})
            health_conditions = custom_fields.get('health_conditions', [])
            self.set_checkbox_group('health_conditions', health_conditions)

            # Medications (if present in UI) - handle nested structure
            medications = custom_fields.get('medications_treatments', [])
            if hasattr(self.ui, 'checkBox_antidepressants'):
                self.ui.checkBox_antidepressants.setChecked('Antidepressants' in medications)
            if hasattr(self.ui, 'checkBox_anxiety_meds'):
                self.ui.checkBox_anxiety_meds.setChecked('Anti-Anxiety' in medications)
            if hasattr(self.ui, 'checkBox_adhd_meds'):
                self.ui.checkBox_adhd_meds.setChecked('ADHD Medication' in medications)
            if hasattr(self.ui, 'checkBox_mood_stabilizers'):
                self.ui.checkBox_mood_stabilizers.setChecked('Mood Stabilizers' in medications)
            if hasattr(self.ui, 'checkBox_sleep_meds'):
                self.ui.checkBox_sleep_meds.setChecked('Sleep Medication' in medications)
            if hasattr(self.ui, 'checkBox_pain_meds'):
                self.ui.checkBox_pain_meds.setChecked('Pain Medication' in medications)
            if hasattr(self.ui, 'lineEdit_custom_medications'):
                custom_meds = [m for m in medications if m not in [
                    'Antidepressants', 'Anti-Anxiety', 'ADHD Medication', 'Mood Stabilizers', 'Sleep Medication', 'Pain Medication']]
                self.ui.lineEdit_custom_medications.setText(', '.join(custom_meds))

            # Allergies/Sensitivities (handle nested structure)
            allergies = custom_fields.get('allergies_sensitivities', [])
            if hasattr(self.ui, 'checkBox_food_allergies'):
                self.ui.checkBox_food_allergies.setChecked('Food Allergies' in allergies)
            if hasattr(self.ui, 'checkBox_medication_allergies'):
                self.ui.checkBox_medication_allergies.setChecked('Medication Allergies' in allergies)
            if hasattr(self.ui, 'checkBox_environmental'):
                self.ui.checkBox_environmental.setChecked('Environmental' in allergies)
            if hasattr(self.ui, 'checkBox_latex_allergy'):
                self.ui.checkBox_latex_allergy.setChecked('Latex Allergy' in allergies)
            if hasattr(self.ui, 'checkBox_gluten_sensitivity'):
                self.ui.checkBox_gluten_sensitivity.setChecked('Gluten Sensitivity' in allergies)
            if hasattr(self.ui, 'checkBox_lactose_intolerance'):
                self.ui.checkBox_lactose_intolerance.setChecked('Lactose Intolerance' in allergies)
            if hasattr(self.ui, 'lineEdit_custom_allergies'):
                custom_allergies = [a for a in allergies if a not in [
                    'Food Allergies', 'Medication Allergies', 'Environmental', 'Latex Allergy', 'Gluten Sensitivity', 'Lactose Intolerance']]
                self.ui.lineEdit_custom_allergies.setText(', '.join(custom_allergies))

            # Interests (available in UI)
            interests = self.existing_data.get('interests', [])
            self.set_checkbox_group('interests', interests)
            # Custom interests
            if hasattr(self.ui, 'lineEdit_custom_interest'):
                custom_interests = [i for i in interests if i not in [
                    'reading', 'writing', 'music', 'art', 'gaming', 'cooking', 'exercise', 'nature', 'technology', 'photography', 'travel', 'volunteering']]
                self.ui.lineEdit_custom_interest.setText(', '.join(custom_interests))

            # Goals (available in UI)
            goals = self.existing_data.get('goals', [])
            if hasattr(self.ui, 'checkBox_mental_health_goals'):
                self.ui.checkBox_mental_health_goals.setChecked('mental_health' in goals)
            if hasattr(self.ui, 'checkBox_physical_health_goals'):
                self.ui.checkBox_physical_health_goals.setChecked('physical_health' in goals)
            if hasattr(self.ui, 'checkBox_career_goals'):
                self.ui.checkBox_career_goals.setChecked('career' in goals)
            if hasattr(self.ui, 'checkBox_education_goals'):
                self.ui.checkBox_education_goals.setChecked('education' in goals)
            if hasattr(self.ui, 'checkBox_relationship_goals'):
                self.ui.checkBox_relationship_goals.setChecked('relationships' in goals)
            if hasattr(self.ui, 'checkBox_financial_goals'):
                self.ui.checkBox_financial_goals.setChecked('financial' in goals)
            if hasattr(self.ui, 'checkBox_creative_goals'):
                self.ui.checkBox_creative_goals.setChecked('creative' in goals)
            if hasattr(self.ui, 'checkBox_social_goals'):
                self.ui.checkBox_social_goals.setChecked('social' in goals)
            if hasattr(self.ui, 'checkBox_spiritual_goals'):
                self.ui.checkBox_spiritual_goals.setChecked('spiritual' in goals)
            if hasattr(self.ui, 'lineEdit_custom_goal'):
                custom_goals = [g for g in goals if g not in [
                    'mental_health', 'physical_health', 'career', 'education', 'relationships', 'financial', 'creative', 'social', 'spiritual']]
                self.ui.lineEdit_custom_goal.setText(', '.join(custom_goals))

            # Loved Ones/Support Network
            loved_ones = self.existing_data.get('loved_ones', [])
            if hasattr(self.ui, 'textEdit_loved_ones'):
                lines = []
                for entry in loved_ones:
                    if isinstance(entry, dict):
                        name = entry.get('name', '')
                        type_val = entry.get('type', '')
                        relationships = entry.get('relationships', [])
                        line = name
                        if type_val:
                            line += f' - {type_val}'
                        if relationships:
                            line += f' - {" ,".join(relationships)}'
                        lines.append(line)
                    elif isinstance(entry, str):
                        lines.append(entry)
                self.ui.textEdit_loved_ones.setPlainText('\n'.join(lines))

            # Date of Birth (if present in UI)
            if hasattr(self.ui, 'calendarWidget_date_of_birth') and 'date_of_birth' in self.existing_data:
                dob_str = self.existing_data['date_of_birth']
                if dob_str:
                    try:
                        dob_date = QDate.fromString(dob_str, Qt.DateFormat.ISODate)
                        self.ui.calendarWidget_date_of_birth.setSelectedDate(dob_date)
                    except:
                        # If parsing fails, use current date
                        self.ui.calendarWidget_date_of_birth.setSelectedDate(QDate.currentDate())

            # Notes (available in UI)
            if hasattr(self.ui, 'textEdit_notes') and 'notes_for_ai' in self.existing_data:
                notes_list = self.existing_data['notes_for_ai']
                if notes_list and len(notes_list) > 0:
                    self.ui.textEdit_notes.setPlainText(notes_list[0])
                else:
                    self.ui.textEdit_notes.setPlainText('')
        except Exception as e:
            logger.error(f"Error loading existing data: {e}")
    
    def set_checkbox_group(self, group_name: str, values: list):
        """Set checkboxes for a specific group based on values."""
        try:
            # Map group names to UI elements (only what's available in the UI)
            group_mappings = {
                'health_conditions': [
                    ('depression', self.ui.checkBox_depression),
                    ('anxiety', self.ui.checkBox_anxiety),
                    ('adhd', self.ui.checkBox_adhd),
                    ('bipolar', self.ui.checkBox_bipolar),
                    ('ptsd', self.ui.checkBox_ptsd),
                    ('ocd', self.ui.checkBox_ocd),
                    ('eating_disorder', self.ui.checkBox_eating_disorder),
                    ('substance_abuse', self.ui.checkBox_substance_abuse),
                    ('sleep_disorder', self.ui.checkBox_sleep_disorder),
                    ('chronic_pain', self.ui.checkBox_chronic_pain),
                    ('autism', self.ui.checkBox_autism),
                    ('other_mental_health', self.ui.checkBox_other_mental_health),
                ],
                'interests': [
                    ('reading', self.ui.checkBox_reading),
                    ('writing', self.ui.checkBox_writing),
                    ('music', self.ui.checkBox_music),
                    ('art', self.ui.checkBox_art),
                    ('gaming', self.ui.checkBox_gaming),
                    ('cooking', self.ui.checkBox_cooking),
                    ('exercise', self.ui.checkBox_exercise),
                    ('nature', self.ui.checkBox_nature),
                    ('technology', self.ui.checkBox_technology),
                    ('photography', self.ui.checkBox_photography),
                    ('travel', self.ui.checkBox_travel),
                    ('volunteering', self.ui.checkBox_volunteering),
                ]
            }
            
            if group_name in group_mappings:
                for value, checkbox in group_mappings[group_name]:
                    checkbox.setChecked(value in values)
                    
        except Exception as e:
            logger.error(f"Error setting checkbox group {group_name}: {e}")
    
    def get_checkbox_group(self, group_name: str) -> list:
        """Get checked values for a specific group."""
        try:
            # Map group names to UI elements (only what's available in the UI)
            group_mappings = {
                'health_conditions': [
                    ('depression', self.ui.checkBox_depression),
                    ('anxiety', self.ui.checkBox_anxiety),
                    ('adhd', self.ui.checkBox_adhd),
                    ('bipolar', self.ui.checkBox_bipolar),
                    ('ptsd', self.ui.checkBox_ptsd),
                    ('ocd', self.ui.checkBox_ocd),
                    ('eating_disorder', self.ui.checkBox_eating_disorder),
                    ('substance_abuse', self.ui.checkBox_substance_abuse),
                    ('sleep_disorder', self.ui.checkBox_sleep_disorder),
                    ('chronic_pain', self.ui.checkBox_chronic_pain),
                    ('autism', self.ui.checkBox_autism),
                    ('other_mental_health', self.ui.checkBox_other_mental_health),
                ],
                'interests': [
                    ('reading', self.ui.checkBox_reading),
                    ('writing', self.ui.checkBox_writing),
                    ('music', self.ui.checkBox_music),
                    ('art', self.ui.checkBox_art),
                    ('gaming', self.ui.checkBox_gaming),
                    ('cooking', self.ui.checkBox_cooking),
                    ('exercise', self.ui.checkBox_exercise),
                    ('nature', self.ui.checkBox_nature),
                    ('technology', self.ui.checkBox_technology),
                    ('photography', self.ui.checkBox_photography),
                    ('travel', self.ui.checkBox_travel),
                    ('volunteering', self.ui.checkBox_volunteering),
                ]
            }
            
            if group_name in group_mappings:
                return [value for value, checkbox in group_mappings[group_name] if checkbox.isChecked()]
            return []
            
        except Exception as e:
            logger.error(f"Error getting checkbox group {group_name}: {e}")
            return []
    
    def get_personalization_data(self) -> Dict[str, Any]:
        """Get all personalization data from the form, preserving existing data structure."""
        try:
            # Start with existing data to preserve fields we don't handle yet
            data = self.existing_data.copy() if self.existing_data else {}
            
            # Preferred Name
            if hasattr(self.ui, 'lineEdit_preferred_name'):
                data['preferred_name'] = self.ui.lineEdit_preferred_name.text().strip()

            # Gender Identity
            gender_identity = []
            if hasattr(self.ui, 'checkBox_woman') and self.ui.checkBox_woman.isChecked():
                gender_identity.append('Woman')
            if hasattr(self.ui, 'checkBox_man') and self.ui.checkBox_man.isChecked():
                gender_identity.append('Man')
            if hasattr(self.ui, 'checkBox_nonbinary') and self.ui.checkBox_nonbinary.isChecked():
                gender_identity.append('Non-binary')
            if hasattr(self.ui, 'checkBox_none') and self.ui.checkBox_none.isChecked():
                gender_identity.append('None')
            if hasattr(self.ui, 'checkBox_prefer_not_to_say') and self.ui.checkBox_prefer_not_to_say.isChecked():
                gender_identity.append('Prefer not to say')
            if hasattr(self.ui, 'lineEdit_custom_gender'):
                custom_genders = self.ui.lineEdit_custom_gender.text().strip()
                if custom_genders:
                    gender_identity.extend([g.strip() for g in custom_genders.split(',') if g.strip()])
            data['gender_identity'] = gender_identity

            # Timezone
            if hasattr(self.ui, 'comboBox_timezone'):
                data['timezone'] = self.ui.comboBox_timezone.currentText().strip()

            # Health conditions (checkbox group)
            health_conditions = self.get_checkbox_group('health_conditions')
            
            # Handle nested custom_fields structure
            if 'custom_fields' not in data:
                data['custom_fields'] = {}
            data['custom_fields']['health_conditions'] = health_conditions

            # Medications (from checkboxes and custom field)
            medications = []
            if hasattr(self.ui, 'checkBox_antidepressants') and self.ui.checkBox_antidepressants.isChecked():
                medications.append('Antidepressants')
            if hasattr(self.ui, 'checkBox_anxiety_meds') and self.ui.checkBox_anxiety_meds.isChecked():
                medications.append('Anti-Anxiety')
            if hasattr(self.ui, 'checkBox_adhd_meds') and self.ui.checkBox_adhd_meds.isChecked():
                medications.append('ADHD Medication')
            if hasattr(self.ui, 'checkBox_mood_stabilizers') and self.ui.checkBox_mood_stabilizers.isChecked():
                medications.append('Mood Stabilizers')
            if hasattr(self.ui, 'checkBox_sleep_meds') and self.ui.checkBox_sleep_meds.isChecked():
                medications.append('Sleep Medication')
            if hasattr(self.ui, 'checkBox_pain_meds') and self.ui.checkBox_pain_meds.isChecked():
                medications.append('Pain Medication')
            if hasattr(self.ui, 'lineEdit_custom_medications'):
                custom_meds = self.ui.lineEdit_custom_medications.text().strip()
                if custom_meds:
                    medications.extend([m.strip() for m in custom_meds.split(',') if m.strip()])
            data['custom_fields']['medications_treatments'] = medications

            # Allergies/Sensitivities (checkbox group)
            allergies = []
            if hasattr(self.ui, 'checkBox_food_allergies') and self.ui.checkBox_food_allergies.isChecked():
                allergies.append('Food Allergies')
            if hasattr(self.ui, 'checkBox_medication_allergies') and self.ui.checkBox_medication_allergies.isChecked():
                allergies.append('Medication Allergies')
            if hasattr(self.ui, 'checkBox_environmental') and self.ui.checkBox_environmental.isChecked():
                allergies.append('Environmental')
            if hasattr(self.ui, 'checkBox_latex_allergy') and self.ui.checkBox_latex_allergy.isChecked():
                allergies.append('Latex Allergy')
            if hasattr(self.ui, 'checkBox_gluten_sensitivity') and self.ui.checkBox_gluten_sensitivity.isChecked():
                allergies.append('Gluten Sensitivity')
            if hasattr(self.ui, 'checkBox_lactose_intolerance') and self.ui.checkBox_lactose_intolerance.isChecked():
                allergies.append('Lactose Intolerance')
            if hasattr(self.ui, 'lineEdit_custom_allergies'):
                custom_allergies = self.ui.lineEdit_custom_allergies.text().strip()
                if custom_allergies:
                    allergies.extend([a.strip() for a in custom_allergies.split(',') if a.strip()])
            data['custom_fields']['allergies_sensitivities'] = allergies

            # Interests (checkbox group + custom)
            interests = self.get_checkbox_group('interests')
            if hasattr(self.ui, 'lineEdit_custom_interest'):
                custom_interests = self.ui.lineEdit_custom_interest.text().strip()
                if custom_interests:
                    interests.extend([i.strip() for i in custom_interests.split(',') if i.strip()])
            data['interests'] = interests

            # Goals (checkbox group + custom)
            goals = []
            if hasattr(self.ui, 'checkBox_mental_health_goals') and self.ui.checkBox_mental_health_goals.isChecked():
                goals.append('mental_health')
            if hasattr(self.ui, 'checkBox_physical_health_goals') and self.ui.checkBox_physical_health_goals.isChecked():
                goals.append('physical_health')
            if hasattr(self.ui, 'checkBox_career_goals') and self.ui.checkBox_career_goals.isChecked():
                goals.append('career')
            if hasattr(self.ui, 'checkBox_education_goals') and self.ui.checkBox_education_goals.isChecked():
                goals.append('education')
            if hasattr(self.ui, 'checkBox_relationship_goals') and self.ui.checkBox_relationship_goals.isChecked():
                goals.append('relationships')
            if hasattr(self.ui, 'checkBox_financial_goals') and self.ui.checkBox_financial_goals.isChecked():
                goals.append('financial')
            if hasattr(self.ui, 'checkBox_creative_goals') and self.ui.checkBox_creative_goals.isChecked():
                goals.append('creative')
            if hasattr(self.ui, 'checkBox_social_goals') and self.ui.checkBox_social_goals.isChecked():
                goals.append('social')
            if hasattr(self.ui, 'checkBox_spiritual_goals') and self.ui.checkBox_spiritual_goals.isChecked():
                goals.append('spiritual')
            if hasattr(self.ui, 'lineEdit_custom_goal'):
                custom_goals = self.ui.lineEdit_custom_goal.text().strip()
                if custom_goals:
                    goals.extend([g.strip() for g in custom_goals.split(',') if g.strip()])
            data['goals'] = goals

            # Loved Ones/Support Network (multi-line text, parse as Name - Type - Relationship1,Relationship2)
            if hasattr(self.ui, 'textEdit_loved_ones'):
                loved_ones_text = self.ui.textEdit_loved_ones.toPlainText().strip()
                loved_ones = []
                if loved_ones_text:
                    for line in loved_ones_text.split('\n'):
                        parts = [p.strip() for p in line.split('-')]
                        name = parts[0] if len(parts) > 0 else ''
                        type_val = parts[1] if len(parts) > 1 else ''
                        relationships = []
                        if len(parts) > 2:
                            relationships = [r.strip() for r in parts[2].split(',') if r.strip()]
                        if name:
                            loved_ones.append({
                                'name': name,
                                'type': type_val,
                                'relationships': relationships
                            })
                data['loved_ones'] = loved_ones

            # Notes for AI (use notes field, wrap as list if not empty)
            notes_text = self.ui.textEdit_notes.toPlainText().strip() if hasattr(self.ui, 'textEdit_notes') else ""
            notes_for_ai = [notes_text] if notes_text else []
            data['notes_for_ai'] = notes_for_ai

            # Preserve other fields that we don't handle yet
            if 'timezone' not in data:
                data['timezone'] = ''
            if 'reminders_needed' not in data:
                data['reminders_needed'] = []
            if 'activities_for_encouragement' not in data:
                data['activities_for_encouragement'] = []
            if 'preferred_name' not in data:
                data['preferred_name'] = ''

            return data
        except Exception as e:
            logger.error(f"Error getting personalization data: {e}")
            return self.existing_data or {}
    
    def get_settings(self):
        """Get the current user profile settings."""
        return self.get_personalization_data()
    
    def set_settings(self, settings):
        """Set the user profile settings."""
        self.existing_data = settings
        self.load_existing_data() 