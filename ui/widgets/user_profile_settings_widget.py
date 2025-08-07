# user_profile_settings_widget.py - User profile settings widget implementation

import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox, QScrollArea
from PySide6.QtCore import Qt, QDate, QEvent
from PySide6.QtGui import QFont

# Import generated UI class
from ui.generated.user_profile_settings_widget_pyqt import Ui_Form_user_profile_settings

# Import core functionality
from core.user_management import get_timezone_options
from core.logger import setup_logging, get_logger, get_component_logger

setup_logging()
logger = get_logger(__name__)
widget_logger = get_component_logger('main')





class UserProfileSettingsWidget(QWidget):
    """Widget for user profile settings configuration."""
    
    def __init__(self, parent=None, user_id: Optional[str] = None, existing_data: Optional[Dict[str, Any]] = None):
        """Initialize the object."""
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
        
        # ----------------------------------------------------------
        # Setup dynamic list containers using Designer-created scroll areas
        # ----------------------------------------------------------
        try:
            from ui.widgets.dynamic_list_container import DynamicListContainer
            
            # Interests tab - replace content in existing scroll area
            self.interests_container = DynamicListContainer(
                parent=self.ui.scrollAreaWidgetContents_interests,
                field_key='interests'
            )
            # Clear existing layout and add dynamic container
            layout = self.ui.scrollAreaWidgetContents_interests.layout()
            if layout:
                # Remove all existing widgets
                while layout.count():
                    child = layout.takeAt(0)
                    if child.widget():
                        child.widget().setParent(None)
            else:
                layout = QVBoxLayout()
                self.ui.scrollAreaWidgetContents_interests.setLayout(layout)
            
            layout.addWidget(self.interests_container)
            
            # Health & Medical tab - replace content in existing scroll areas
            self.health_conditions_container = DynamicListContainer(
                parent=self.ui.scrollAreaWidgetContents_medical,
                field_key='health_conditions'
            )
            layout = self.ui.scrollAreaWidgetContents_medical.layout()
            if layout:
                while layout.count():
                    child = layout.takeAt(0)
                    if child.widget():
                        child.widget().setParent(None)
            else:
                layout = QVBoxLayout()
                self.ui.scrollAreaWidgetContents_medical.setLayout(layout)
            layout.addWidget(self.health_conditions_container)
            
            self.allergies_container = DynamicListContainer(
                parent=self.ui.scrollAreaWidgetContents_allergies,
                field_key='allergies_sensitivities'
            )
            layout = self.ui.scrollAreaWidgetContents_allergies.layout()
            if layout:
                while layout.count():
                    child = layout.takeAt(0)
                    if child.widget():
                        child.widget().setParent(None)
            else:
                layout = QVBoxLayout()
                self.ui.scrollAreaWidgetContents_allergies.setLayout(layout)
            layout.addWidget(self.allergies_container)
            
            # Medications & Reminders tab - replace content in existing scroll areas
            self.medications_container = DynamicListContainer(
                parent=self.ui.scrollAreaWidgetContents_medications,
                field_key='medications'
            )
            layout = self.ui.scrollAreaWidgetContents_medications.layout()
            if layout:
                while layout.count():
                    child = layout.takeAt(0)
                    if child.widget():
                        child.widget().setParent(None)
            else:
                layout = QVBoxLayout()
                self.ui.scrollAreaWidgetContents_medications.setLayout(layout)
            layout.addWidget(self.medications_container)
            
            # Goals tab - replace content in existing scroll areas
            self.goals_container = DynamicListContainer(
                parent=self.ui.scrollAreaWidgetContents_goals,
                field_key='goals'
            )
            layout = self.ui.scrollAreaWidgetContents_goals.layout()
            if layout:
                while layout.count():
                    child = layout.takeAt(0)
                    if child.widget():
                        child.widget().setParent(None)
            else:
                layout = QVBoxLayout()
                self.ui.scrollAreaWidgetContents_goals.setLayout(layout)
            layout.addWidget(self.goals_container)
            

            
        except Exception as e:
            logger.error(f"Failed to set up DynamicListContainer: {e}")
        
        # Set default tab to Basic Info (index 0)
        if hasattr(self.ui, 'tabWidget'):
            self.ui.tabWidget.setCurrentIndex(0)
        
        # Load existing data
        self.load_existing_data()
    
    def populate_timezones(self):
        """Populate the timezone combo box with options and enable selection."""
        # Timezone functionality moved to channel selection widget
        pass
    

    
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

            # Health conditions - use dynamic list container
            custom_fields = self.existing_data.get('custom_fields', {})
            health_conditions = custom_fields.get('health_conditions', [])
            if hasattr(self, 'health_conditions_container'):
                self.health_conditions_container.set_values(health_conditions)

            # Medications - use dynamic list container
            medications = custom_fields.get('medications_treatments', [])
            if hasattr(self, 'medications_container'):
                self.medications_container.set_values(medications)

            # Allergies/Sensitivities - use dynamic list container
            allergies = custom_fields.get('allergies_sensitivities', [])
            if hasattr(self, 'allergies_container'):
                self.allergies_container.set_values(allergies)

            # Goals - use dynamic list container
            goals = self.existing_data.get('goals', [])
            if hasattr(self, 'goals_container'):
                self.goals_container.set_values(goals)

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

            # Interests prepopulation via container
            if hasattr(self, 'interests_container'):
                existing_interests = self.existing_data.get('interests', [])
                self.interests_container.set_values(existing_interests)
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

            # Date of Birth (if present in UI)
            if hasattr(self.ui, 'calendarWidget_date_of_birth'):
                selected_date = self.ui.calendarWidget_date_of_birth.selectedDate()
                if selected_date.isValid():
                    # Only save the date if it's different from the default (current date)
                    # or if there was an existing date of birth
                    current_date = QDate.currentDate()
                    existing_dob = self.existing_data.get('date_of_birth', '')
                    
                    # Convert QDate to ISO format string
                    dob_str = selected_date.toString(Qt.DateFormat.ISODate)
                    
                    # Only save if user actually selected a date (not default current date)
                    # or if there was an existing date of birth that we should preserve
                    if selected_date != current_date or existing_dob:
                        data['date_of_birth'] = dob_str
                    else:
                        # Clear date if user didn't actually select one
                        data['date_of_birth'] = ''
                else:
                    # Clear date if invalid
                    data['date_of_birth'] = ''

            # Timezone functionality moved to channel selection widget
            # Timezone is now handled by the channel selection widget

            # Health conditions - use dynamic list container
            if 'custom_fields' not in data:
                data['custom_fields'] = {}
            if hasattr(self, 'health_conditions_container'):
                data['custom_fields']['health_conditions'] = self.health_conditions_container.get_values()
            else:
                # LEGACY COMPATIBILITY FALLBACK - REMOVE AFTER VERIFYING NO USAGE
                # TODO: Remove after confirming all UI uses dynamic list containers
                # REMOVAL PLAN:
                # 1. Add usage logging to track legacy fallback usage
                # 2. Monitor app.log for legacy usage warnings for 1 week
                # 3. If no usage detected, remove entire fallback block
                # 4. Update any remaining UI to use dynamic list containers
                logger.warning("LEGACY health_conditions fallback used - switch to dynamic list container")
                data['custom_fields']['health_conditions'] = self.get_checkbox_group('health_conditions')

            # Medications - use dynamic list container
            if hasattr(self, 'medications_container'):
                data['custom_fields']['medications_treatments'] = self.medications_container.get_values()
            else:
                # LEGACY COMPATIBILITY FALLBACK - REMOVE AFTER VERIFYING NO USAGE
                # TODO: Remove after confirming all UI uses dynamic list containers
                # REMOVAL PLAN:
                # 1. Add usage logging to track legacy fallback usage
                # 2. Monitor app.log for legacy usage warnings for 1 week
                # 3. If no usage detected, remove entire fallback block
                # 4. Update any remaining UI to use dynamic list containers
                logger.warning("LEGACY medications fallback used - switch to dynamic list container")
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

            # Allergies/Sensitivities - use dynamic list container
            if hasattr(self, 'allergies_container'):
                data['custom_fields']['allergies_sensitivities'] = self.allergies_container.get_values()
            else:
                # LEGACY COMPATIBILITY FALLBACK - REMOVE AFTER VERIFYING NO USAGE
                # TODO: Remove after confirming all UI uses dynamic list containers
                # REMOVAL PLAN:
                # 1. Add usage logging to track legacy fallback usage
                # 2. Monitor app.log for legacy usage warnings for 1 week
                # 3. If no usage detected, remove entire fallback block
                # 4. Update any remaining UI to use dynamic list containers
                logger.warning("LEGACY allergies fallback used - switch to dynamic list container")
                allergies = []
                if hasattr(self.ui, 'checkBox_food_allergies') and self.ui.checkBox_food_allergies.isChecked():
                    allergies.append('Food Allergies')
                if hasattr(self.ui, 'checkBox_medication_allergies') and self.ui.checkBox_medication_allergies.isChecked():
                    allergies.append('Medication Allergies')
                if hasattr(self.ui, 'checkBox_environmental_allergies') and self.ui.checkBox_environmental_allergies.isChecked():
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

                        # Interests via dynamic container (if present)
            if hasattr(self, 'interests_container'):
                data['interests'] = self.interests_container.get_values()
            else:
                # LEGACY COMPATIBILITY FALLBACK - REMOVE AFTER VERIFYING NO USAGE
                # TODO: Remove after confirming all UI uses dynamic list containers
                # REMOVAL PLAN:
                # 1. Add usage logging to track legacy fallback usage
                # 2. Monitor app.log for legacy usage warnings for 1 week
                # 3. If no usage detected, remove entire fallback block
                # 4. Update any remaining UI to use dynamic list containers
                logger.warning("LEGACY interests fallback used - switch to dynamic list container")
                interests = self.get_checkbox_group('interests')
                if hasattr(self.ui, 'lineEdit_custom_interest'):
                    custom_interests = self.ui.lineEdit_custom_interest.text().strip()
                    if custom_interests:
                        interests.extend([i.strip() for i in custom_interests.split(',') if i.strip()])
                data['interests'] = interests

            # Goals - use dynamic list container
            if hasattr(self, 'goals_container'):
                data['goals'] = self.goals_container.get_values()
            else:
                # LEGACY COMPATIBILITY FALLBACK - REMOVE AFTER VERIFYING NO USAGE
                # TODO: Remove after confirming all UI uses dynamic list containers
                # REMOVAL PLAN:
                # 1. Add usage logging to track legacy fallback usage
                # 2. Monitor app.log for legacy usage warnings for 1 week
                # 3. If no usage detected, remove entire fallback block
                # 4. Update any remaining UI to use dynamic list containers
                logger.warning("LEGACY goals fallback used - switch to dynamic list container")
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