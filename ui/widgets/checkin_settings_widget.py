# checkin_settings_widget.py - Check-in settings widget implementation

from PySide6.QtWidgets import QWidget, QMessageBox
from ui.generated.checkin_settings_widget_pyqt import Ui_Form_checkin_settings

# Import core functionality
from core.ui_management import (
    load_period_widgets_for_category, collect_period_data_from_widgets
)
from core.user_data_handlers import get_user_data
from core.error_handling import handle_errors
from core.logger import setup_logging, get_component_logger

# Import our period row widget
from ui.widgets.period_row_widget import PeriodRowWidget

setup_logging()
logger = get_component_logger('ui')
widget_logger = logger

class CheckinSettingsWidget(QWidget):
    """Widget for check-in settings configuration."""
    
    @handle_errors("initializing checkin settings widget")
    def __init__(self, parent=None, user_id=None):
        """Initialize the object."""
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
    
    @handle_errors("handling show event")
    def showEvent(self, event):
        """
        Handle widget show event.
        
        Called when the widget becomes visible. Currently just calls the parent
        implementation but can be extended for initialization that needs to happen
        when the widget is shown.
        
        Args:
            event: The show event object
        """
        super().showEvent(event)
    
    @handle_errors("setting up connections")
    def setup_connections(self):
        """Setup signal connections."""
        # Connect time period buttons
        self.ui.pushButton_add_new_checkin_time_period.clicked.connect(lambda: self.add_new_period())
        self.ui.pushButton_undo_last__checkin_time_period_delete.clicked.connect(self.undo_last_time_period_delete)
        # Connect question buttons
        self.ui.pushButton_add_new_checkin_question.clicked.connect(self.add_new_question)
        self.ui.pushButton_undo_last_checkin_question_delete.clicked.connect(self.undo_last_question_delete)
        
        # Connect question checkboxes
        self.connect_question_checkboxes()
    
    @handle_errors("connecting question checkboxes")
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
            self.ui.checkBox_sleep_schedule,
            self.ui.checkBox_medication,
            self.ui.checkBox_breakfast,
            self.ui.checkBox_exercise,
            self.ui.checkBox_social_interaction,
            self.ui.checkBox_reflection_notes
        ]
        
        for checkbox in question_checkboxes:
            checkbox.toggled.connect(self.on_question_toggled)
    
    @handle_errors("handling question toggle")
    def on_question_toggled(self, checked):
        """Handle question checkbox toggle."""
        # This can be used for real-time validation or UI updates
        pass
    
    @handle_errors("loading existing check-in data")
    def load_existing_data(self):
        """Load existing check-in data."""
        if not self.user_id:
            logger.info("CheckinSettingsWidget: No user_id provided - creating new user mode")
            # For new user creation, add a default period and set default questions
            self.add_new_period()
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
    
    @handle_errors("setting question checkboxes")
    def set_question_checkboxes(self, questions):
        """Set question checkboxes based on saved preferences."""
        # Import the dynamic checkin manager
        from core.checkin_dynamic_manager import dynamic_checkin_manager
        
        # Get all available questions from the dynamic manager (include custom questions)
        available_questions = dynamic_checkin_manager.get_enabled_questions_for_ui(self.user_id)
        
        # Map question keys to checkboxes
        question_mapping = {
            'mood': self.ui.checkBox_mood,
            'energy': self.ui.checkBox_energy_level,
            'hydration': self.ui.checkBox_hydrated,
            'brushed_teeth': self.ui.checkBox_brushed_teeth,
            'sleep_quality': self.ui.checkBox_sleep_quality,
            'stress_level': self.ui.checkBox_stress_level,
            'anxiety_level': self.ui.checkBox_anxiety_level,
            'sleep_schedule': self.ui.checkBox_sleep_schedule,
            'medication_taken': self.ui.checkBox_medication,
            'ate_breakfast': self.ui.checkBox_breakfast,
            'exercise': self.ui.checkBox_exercise,
            'social_interaction': self.ui.checkBox_social_interaction,
            'daily_reflection': self.ui.checkBox_reflection_notes
        }
        
        for question_key, checkbox in question_mapping.items():
            if question_key in available_questions:
                question_data = questions.get(question_key, {})
                # Use the default enabled state from the dynamic manager if not set
                default_enabled = available_questions[question_key].get('enabled', False)
                enabled = question_data.get('enabled', default_enabled)
                checkbox.setChecked(enabled)
    
    @handle_errors("getting default question state")
    def get_default_question_state(self, question_key):
        """Get default enabled state for a question."""
        # Import the dynamic checkin manager
        from core.checkin_dynamic_manager import dynamic_checkin_manager
        
        # Get the default enabled state from the dynamic manager (include custom questions)
        available_questions = dynamic_checkin_manager.get_enabled_questions_for_ui(self.user_id)
        question_data = available_questions.get(question_key, {})
        return question_data.get('enabled', False)
    
    @handle_errors("finding lowest available period number")
    def find_lowest_available_period_number(self):
        """Find the lowest available integer (2+) that's not currently used in period names."""
        used_numbers = set()
        
        # Check existing period widgets
        for widget in self.period_widgets:
            period_name = widget.get_period_data().get('name', '')
            # Extract number from names like "Check-in Reminder 2", "Check-in Reminder 3", etc.
            if 'Check-in Reminder ' in period_name:
                try:
                    number = int(period_name.split('Check-in Reminder ')[1])
                    used_numbers.add(number)
                except (ValueError, IndexError):
                    pass
        
        # Find the lowest available number starting from 2
        number = 2
        while number in used_numbers:
            number += 1
        
        return number
    
    @handle_errors("adding new check-in period")
    def add_new_period(self, checked=None, period_name=None, period_data=None):
        """Add a new time period using the PeriodRowWidget."""
        logger.info(f"CheckinSettingsWidget: add_new_period called with period_name={period_name}, period_data={period_data}")
        if period_name is None:
            # Use descriptive name for default periods (title case for consistency with task widget)
            if len(self.period_widgets) == 0:
                period_name = "Check-in Reminder Default"
            else:
                # Find the lowest available number for new periods
                next_number = self.find_lowest_available_period_number()
                period_name = f"Check-in Reminder {next_number}"
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
    
    @handle_errors("removing period row")
    def remove_period_row(self, row_widget):
        """Remove a period row and store it for undo."""
        # Prevent deletion of the last period
        if len(self.period_widgets) <= 1:
            QMessageBox.warning(
                self, 
                "Cannot Delete Last Period", 
                "You must have at least one time period. Please add another period before deleting this one."
            )
            return
        
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
    
    @handle_errors("undoing last time period delete")
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
        self.add_new_period(period_name=deleted_data['period_name'], period_data=period_data)
    
    @handle_errors("adding new question")
    def add_new_question(self):
        """Add a new check-in question."""
        if not self.user_id:
            QMessageBox.warning(self, "No User", "Cannot add custom questions without a user ID.")
            return
        
        from PySide6.QtWidgets import QInputDialog, QMessageBox, QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QDialogButtonBox
        from core.checkin_dynamic_manager import dynamic_checkin_manager
        
        # Create a simple dialog for question creation
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Custom Check-in Question")
        layout = QVBoxLayout(dialog)
        
        # Question text input
        layout.addWidget(QLabel("Question Text:"))
        question_text_edit = QLineEdit()
        question_text_edit.setPlaceholderText("Enter your question...")
        layout.addWidget(question_text_edit)
        
        # Question type selection
        layout.addWidget(QLabel("Question Type:"))
        type_combo = QComboBox()
        type_combo.addItems(["scale_1_5", "yes_no", "number", "optional_text", "time_pair"])
        layout.addWidget(type_combo)
        
        # Category selection
        layout.addWidget(QLabel("Category:"))
        category_combo = QComboBox()
        categories = dynamic_checkin_manager.get_categories()
        category_combo.addItems(list(categories.keys()) if categories else ["mood", "health", "sleep", "social", "reflection"])
        layout.addWidget(category_combo)
        
        # Display name input
        layout.addWidget(QLabel("Display Name (for UI):"))
        display_name_edit = QLineEdit()
        display_name_edit.setPlaceholderText("Leave empty to use question text")
        layout.addWidget(display_name_edit)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            question_text = question_text_edit.text().strip()
            if not question_text:
                QMessageBox.warning(self, "Empty Question", "Please enter a question text.")
                return
            
            question_type = type_combo.currentText()
            category = category_combo.currentText()
            display_name = display_name_edit.text().strip() or question_text
            
            # Generate a unique question key
            import re
            question_key = re.sub(r'[^a-z0-9_]', '_', question_text.lower()[:50])
            question_key = f"custom_{question_key}"
            
            # Check if key already exists
            existing_custom = dynamic_checkin_manager.get_custom_questions(self.user_id)
            counter = 1
            original_key = question_key
            while question_key in existing_custom:
                question_key = f"{original_key}_{counter}"
                counter += 1
            
            # Build validation rules based on type
            validation = {}
            if question_type == 'scale_1_5':
                validation = {
                    "min": 1,
                    "max": 5,
                    "error_message": f"Please enter a number between 1 and 5 for {display_name}."
                }
            elif question_type == 'number':
                validation = {
                    "min": 0,
                    "max": 100,
                    "error_message": f"Please enter a number for {display_name}."
                }
            elif question_type == 'yes_no':
                validation = {
                    "error_message": f"Please answer with yes/no, y/n, or similar for {display_name}."
                }
            elif question_type == 'optional_text':
                validation = {
                    "error_message": f"This is optional - you can just press enter to skip {display_name}."
                }
            elif question_type == 'time_pair':
                validation = {
                    "error_message": f"Please provide both times in HH:MM format (e.g., '23:30' and '07:00') for {display_name}."
                }
            
            # Create question definition
            question_def = {
                'type': question_type,
                'question_text': question_text,
                'ui_display_name': display_name,
                'category': category,
                'validation': validation,
                'enabled': True  # Enable by default when created
            }
            
            # Save the custom question
            if dynamic_checkin_manager.save_custom_question(self.user_id, question_key, question_def):
                QMessageBox.information(
                    self,
                    "Question Added",
                    f"Custom question '{display_name}' has been added successfully.\n\n"
                    "You can enable/disable it in the check-in questions list."
                )
                # Reload the question checkboxes to show the new question
                self.load_existing_data()
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to save the custom question. Please try again."
                )
    
    @handle_errors("undoing last question delete")
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
    
    @handle_errors("getting check-in settings")
    def get_checkin_settings(self):
        """Get the current check-in settings."""
        # Use the new reusable function to collect period data
        time_periods = collect_period_data_from_widgets(self.period_widgets, "checkin")
        
        # Import the dynamic checkin manager
        from core.checkin_dynamic_manager import dynamic_checkin_manager
        
        # Get questions from checkboxes using the correct question keys
        questions = {}
        question_mapping = {
            'mood': self.ui.checkBox_mood,
            'energy': self.ui.checkBox_energy_level,
            'hydration': self.ui.checkBox_hydrated,
            'brushed_teeth': self.ui.checkBox_brushed_teeth,
            'sleep_quality': self.ui.checkBox_sleep_quality,
            'stress_level': self.ui.checkBox_stress_level,
            'anxiety_level': self.ui.checkBox_anxiety_level,
            'sleep_schedule': self.ui.checkBox_sleep_schedule,
            'medication_taken': self.ui.checkBox_medication,
            'ate_breakfast': self.ui.checkBox_breakfast,
            'exercise': self.ui.checkBox_exercise,
            'social_interaction': self.ui.checkBox_social_interaction,
            'daily_reflection': self.ui.checkBox_reflection_notes
        }
        
        # Get available questions from dynamic manager for labels (include custom questions)
        available_questions = dynamic_checkin_manager.get_enabled_questions_for_ui(self.user_id)
        
        for question_key, checkbox in question_mapping.items():
            if question_key in available_questions:
                questions[question_key] = {
                    'enabled': checkbox.isChecked(),
                    'label': available_questions[question_key].get('ui_display_name', question_key)
                }
        
        # Custom questions are stored separately in checkin_settings.custom_questions
        # They're handled by DynamicCheckinManager and included in enabled_questions automatically
        
        return {
            'time_periods': time_periods,
            'questions': questions
        }
    
    @handle_errors("setting checkin settings")
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
            self.add_new_period(period_name, period_data)
        
        # Set questions
        questions = settings.get('questions', {})
        self.set_question_checkboxes(questions) 

 