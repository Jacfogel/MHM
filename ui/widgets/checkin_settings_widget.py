# checkin_settings_widget.py - Check-in settings widget implementation

import sys
import os
from typing import Dict, Any, List, Optional

# Add parent directory to path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QRadioButton, QSpinBox, QPushButton, QMessageBox
from PySide6.QtCore import Qt, Signal
from ui.generated.checkin_settings_widget_pyqt import Ui_Form_checkin_settings

# Import core functionality
from core.schedule_management import (
    get_schedule_time_periods, set_schedule_periods, clear_schedule_periods_cache
)
from core.ui_management import (
    load_period_widgets_for_category, collect_period_data_from_widgets
)
from core.user_management import update_user_preferences
from core.error_handling import handle_errors
from core.logger import setup_logging, get_logger
from core.user_management import get_user_data

# Import our period row widget
from ui.widgets.period_row_widget import PeriodRowWidget

setup_logging()
logger = get_logger(__name__)

class CheckinSettingsWidget(QWidget):
    """Widget for check-in settings configuration."""
    
    def __init__(self, parent=None, user_id=None):
        super().__init__(parent)
        self.user_id = user_id
        self.ui = Ui_Form_checkin_settings()
        self.ui.setupUi(self)
        # Initialize data structures
        # Initialize data structures
        self.period_widgets = []
        self.deleted_periods = []  # For undo functionality
        self.deleted_questions = []  # For undo functionality
        
        self.setup_connections()
        self.load_existing_data()
        self.ui.scrollAreaWidgetContents_checkin_time_periods.setVisible(True)
    
    def showEvent(self, event):
        super().showEvent(event)
    
    def setup_connections(self):
        """Setup signal connections."""
        # Connect time period buttons
        self.ui.pushButton_add_new_checkin_time_period.clicked.connect(lambda: self.add_new_time_period())
        self.ui.pushButton_undo_last__checkin_time_period_delete.clicked.connect(self.undo_last_time_period_delete)
        # Connect question buttons
        self.ui.pushButton_add_new_checkin_question.clicked.connect(self.add_new_question)
        self.ui.pushButton_undo_last_checkin_question_delete.clicked.connect(self.undo_last_question_delete)
        
        # Connect question checkboxes
        self.connect_question_checkboxes()
    
    def connect_question_checkboxes(self):
        """Connect all question checkboxes to track changes."""
        question_checkboxes = [
            self.ui.checkBox_mood,
            self.ui.checkBox_energy_level,
            self.ui.checkBox_hydrated,
            self.ui.checkBox_brushed_teeth,
            self.ui.checkBox_sleep_quality,
            self.ui.checkBox_stress_level,
            self.ui.checkBox_anxiety_level,
            self.ui.checkBox_sleep_hours,
            self.ui.checkBox_medication,
            self.ui.checkBox_breakfast,
            self.ui.checkBox_exercise,
            self.ui.checkBox_social_interaction,
            self.ui.checkBox_reflection_notes
        ]
        
        for checkbox in question_checkboxes:
            checkbox.toggled.connect(self.on_question_toggled)
    
    def on_question_toggled(self, checked):
        """Handle question checkbox toggle."""
        # This can be used for real-time validation or UI updates
        pass
    
    def load_existing_data(self):
        """Load existing check-in data."""
        if not self.user_id:
            logger.info("CheckinSettingsWidget: No user_id provided - creating new user mode")
            # For new user creation, add a default period and set default questions
            self.add_new_time_period()
            self.set_question_checkboxes({})  # Use defaults
            return
            
        logger.info(f"CheckinSettingsWidget: Loading periods for user_id={self.user_id}")
        # Use the new reusable function to load period widgets
        self.period_widgets = load_period_widgets_for_category(
            layout=self.ui.verticalLayout_scrollAreaWidgetContents_checkin_time_periods,
            user_id=self.user_id,
            category="checkin",
            parent_widget=self,
            widget_list=self.period_widgets,
            delete_callback=self.remove_period_row
        )
        # Get user preferences
        prefs_result = get_user_data(self.user_id, 'preferences')
        prefs = prefs_result.get('preferences') or {}
        checkin_settings = prefs.get('checkin_settings', {})
        questions = checkin_settings.get('questions', {})
        # Set question checkboxes based on saved preferences
        self.set_question_checkboxes(questions)
    
    def set_question_checkboxes(self, questions):
        """Set question checkboxes based on saved preferences."""
        question_mapping = {
            'mood': self.ui.checkBox_mood,
            'energy_level': self.ui.checkBox_energy_level,
            'hydrated': self.ui.checkBox_hydrated,
            'brushed_teeth': self.ui.checkBox_brushed_teeth,
            'sleep_quality': self.ui.checkBox_sleep_quality,
            'stress_level': self.ui.checkBox_stress_level,
            'anxiety_level': self.ui.checkBox_anxiety_level,
            'sleep_hours': self.ui.checkBox_sleep_hours,
            'medication': self.ui.checkBox_medication,
            'breakfast': self.ui.checkBox_breakfast,
            'exercise': self.ui.checkBox_exercise,
            'social_interaction': self.ui.checkBox_social_interaction,
            'reflection_notes': self.ui.checkBox_reflection_notes
        }
        
        for question_key, checkbox in question_mapping.items():
            question_data = questions.get(question_key, {})
            enabled = question_data.get('enabled', self.get_default_question_state(question_key))
            checkbox.setChecked(enabled)
    
    def get_default_question_state(self, question_key):
        """Get default enabled state for a question."""
        # Default questions that are enabled by default
        default_enabled = ['mood', 'energy_level', 'stress_level', 'sleep_quality']
        return question_key in default_enabled
    
    def add_new_time_period(self, checked=None, period_name=None, period_data=None):
        """Add a new time period using the PeriodRowWidget."""
        logger.info(f"CheckinSettingsWidget: add_new_time_period called with period_name={period_name}, period_data={period_data}")
        if period_name is None:
            period_name = f"Period {len(self.period_widgets) + 1}"
        if not isinstance(period_name, str):
            logger.warning(f"CheckinSettingsWidget: period_name is not a string: {period_name} (type: {type(period_name)})")
            period_name = str(period_name)
        if period_data is None:
            period_data = {'start_time': '18:00', 'end_time': '20:00', 'active': True, 'days': ['ALL']}
        # Defensive: ensure period_data is a dict
        if not isinstance(period_data, dict):
            logger.warning(f"CheckinSettingsWidget: period_data is not a dict: {period_data} (type: {type(period_data)})")
            period_data = {'start_time': '18:00', 'end_time': '20:00', 'active': True, 'days': ['ALL']}
        # Create the period row widget
        period_widget = PeriodRowWidget(self, period_name, period_data)
        # Connect the delete signal
        period_widget.delete_requested.connect(self.remove_period_row)
        # Add to the scroll area layout
        layout = self.ui.verticalLayout_scrollAreaWidgetContents_checkin_time_periods
        layout.addWidget(period_widget)
        # Store reference
        self.period_widgets.append(period_widget)
        return period_widget
    
    def remove_period_row(self, row_widget):
        """Remove a period row and store it for undo."""
        # Store the deleted period data for undo
        if isinstance(row_widget, PeriodRowWidget):
            period_data = row_widget.get_period_data()
            deleted_data = {
                'period_name': period_data['name'],
                'start_time': period_data['start_time'],
                'end_time': period_data['end_time'],
                'active': period_data['active'],
                'days': period_data['days']
            }
            self.deleted_periods.append(deleted_data)
        
        # Remove from layout and widget list
        layout = self.ui.verticalLayout_scrollAreaWidgetContents_checkin_time_periods
        layout.removeWidget(row_widget)
        row_widget.setParent(None)
        row_widget.deleteLater()
        
        if row_widget in self.period_widgets:
            self.period_widgets.remove(row_widget)
    
    def undo_last_time_period_delete(self):
        """Undo the last time period deletion."""
        if not self.deleted_periods:
            QMessageBox.information(self, "No Deletions", "No deletions to undo.")
            return
        
        # Get the last deleted period
        deleted_data = self.deleted_periods.pop()
        
        # Recreate the period
        period_data = {
            'start_time': deleted_data['start_time'],
            'end_time': deleted_data['end_time'],
            'active': deleted_data['active'],
            'days': deleted_data.get('days', ['ALL'])
        }
        
        # Add it back
        self.add_new_time_period(period_name=deleted_data['period_name'], period_data=period_data)
    
    def add_new_question(self):
        """Add a new check-in question."""
        # For now, this is a placeholder since we have a fixed set of questions
        QMessageBox.information(self, "Add Question", 
                               "Question addition is not yet implemented. The current set of questions is fixed.")
    
    def undo_last_question_delete(self):
        """Undo the last question deletion."""
        if not self.deleted_questions:
            QMessageBox.information(self, "No Deletions", "No question deletions to undo.")
            return
        
        # Get the last deleted question
        deleted_question = self.deleted_questions.pop()
        
        # Recreate the question (placeholder for future implementation)
        QMessageBox.information(self, "Undo Question", 
                               f"Would restore question: {deleted_question}")
    
    def get_checkin_settings(self):
        """Get the current check-in settings."""
        # Use the new reusable function to collect period data
        time_periods = collect_period_data_from_widgets(self.period_widgets, "checkin")
        
        # Get questions from checkboxes
        questions = {}
        question_mapping = {
            'mood': self.ui.checkBox_mood,
            'energy_level': self.ui.checkBox_energy_level,
            'hydrated': self.ui.checkBox_hydrated,
            'brushed_teeth': self.ui.checkBox_brushed_teeth,
            'sleep_quality': self.ui.checkBox_sleep_quality,
            'stress_level': self.ui.checkBox_stress_level,
            'anxiety_level': self.ui.checkBox_anxiety_level,
            'sleep_hours': self.ui.checkBox_sleep_hours,
            'medication': self.ui.checkBox_medication,
            'breakfast': self.ui.checkBox_breakfast,
            'exercise': self.ui.checkBox_exercise,
            'social_interaction': self.ui.checkBox_social_interaction,
            'reflection_notes': self.ui.checkBox_reflection_notes
        }
        question_labels = {
            'mood': 'Mood (1-5 scale)',
            'energy_level': 'Energy level (1-5 scale)',
            'hydrated': 'Staying hydrated (yes/no)',
            'brushed_teeth': 'Brushed teeth (yes/no)',
            'sleep_quality': 'Sleep quality (1-5 scale)',
            'stress_level': 'Stress level (1-5 scale)',
            'anxiety_level': 'Anxiety level (1-5 scale)',
            'sleep_hours': 'Hours of sleep (number)',
            'medication': 'Took medication (yes/no)',
            'breakfast': 'Had breakfast (yes/no)',
            'exercise': 'Did exercise (yes/no)',
            'social_interaction': 'Had social interaction (yes/no)',
            'reflection_notes': 'Brief reflection/notes (text)'
        }
        for question_key, checkbox in question_mapping.items():
            questions[question_key] = {
                'enabled': checkbox.isChecked(),
                'label': question_labels.get(question_key, question_key)
            }
        
        return {
            'time_periods': time_periods,
            'questions': questions
        }
    
    def set_checkin_settings(self, settings):
        """Set the check-in settings."""
        if not settings:
            return
        
        # Clear existing period widgets
        for widget in self.period_widgets:
            layout = self.ui.verticalLayout_scrollAreaWidgetContents_checkin_time_periods
            layout.removeWidget(widget)
            widget.setParent(None)
            widget.deleteLater()
        self.period_widgets.clear()
        
        # Add time periods
        time_periods = settings.get('time_periods', {})
        for period_name, period_data in time_periods.items():
            self.add_new_time_period(period_name, period_data)
        
        # Set questions
        questions = settings.get('questions', {})
        self.set_question_checkboxes(questions) 