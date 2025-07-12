# user_profile_dialog.py
"""
Personalization dialog for user account creation and management (PySide6-based).
Provides a comprehensive interface for collecting and editing user personalization data.
"""

import sys
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable

# Add parent directory to path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PySide6 imports
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QCheckBox, QComboBox, QTextEdit, QGroupBox, QGridLayout, QWidget,
    QMessageBox, QScrollArea, QFrame, QButtonGroup, QDialogButtonBox,
    QSpinBox, QTimeEdit, QDateEdit, QTabWidget, QFormLayout
)
from PySide6.QtCore import Qt, QTime, QDate, Signal
from PySide6.QtGui import QFont, QIcon

# Set up logging
from core.logger import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)

# Import core functionality
from core.personalization_management import (
    get_predefined_options, get_timezone_options, validate_personalization_data
)
from core.error_handling import handle_errors


class UserProfileDialog(QDialog):
    """PySide6-based personalization dialog for user account creation and management."""
    user_changed = Signal()

    def __init__(self, parent, user_id: str, on_save: Optional[Callable] = None, existing_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.parent = parent
        self.user_id = user_id
        self.on_save = on_save
        
        # Use provided data or empty dict - don't load from file to prevent premature creation
        self.personalization_data = existing_data or {}
        
        # Setup window
        self.setWindowTitle("Personalization Settings")
        self.resize(900, 800)
        self.setMinimumSize(700, 600)
        
        # Make dialog modal
        self.setModal(True)
        
        # Setup UI
        self.setup_ui()
        
        # Center the dialog
        self.center_dialog()
    
    def center_dialog(self):
        """Center the dialog on the parent window."""
        if self.parent:
            parent_geometry = self.parent.geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)
    
    def setup_ui(self):
        """Setup the user interface."""
        # Load UI from file
        ui_file_path = os.path.join(os.path.dirname(__file__), '..', 'designs', 'user_profile_dialog.ui')
        if not os.path.exists(ui_file_path):
            raise FileNotFoundError(f"UI file not found: {ui_file_path}")

        # Remove all QUiLoader imports and usage
        # loader = QUiLoader()
        # self.ui = loader.load(ui_file_path, self)
        # self.setLayout(self.ui.layout())
        
        # Store references to UI elements
        self.name_edit = self.ui.lineEdit_name
        self.age_spin = self.ui.spinBox_age
        self.timezone_combo = self.ui.comboBox_timezone
        self.notes_edit = self.ui.textEdit_notes
        
        # Setup placeholder widgets for dynamic content
        self.health_conditions_widget = self.ui.widget_health_conditions
        self.medications_widget = self.ui.widget_medications
        self.allergies_widget = self.ui.widget_allergies
        self.loved_ones_container = self.ui.widget_loved_ones_container
        self.interests_widget = self.ui.widget_interests
        self.goals_widget = self.ui.widget_goals
        
        # Create dynamic sections
        self.create_health_section()
        self.create_loved_ones_section()
        self.create_interests_section()
        self.create_notes_section()
        self.create_goals_section()
        
        # Connect buttons
        self.ui.buttonBox.accepted.connect(self.save_personalization)
        self.ui.buttonBox.rejected.connect(self.cancel)
    
    def create_custom_field_list(self, parent_layout, predefined_values, existing_values, label_text):
        """Creates a multi-column list with preset items (checkbox + label) and custom fields (checkbox + entry + delete)."""
        def title_case(s):
            # Convert snake_case or lowercase to Title Case
            return re.sub(r'(_|-)+', ' ', s).title()

        # Create group box
        group_box = QGroupBox(title_case(label_text))
        group_layout = QGridLayout(group_box)

        # Multi-column logic for preset options
        n = len(predefined_values)
        if n > 12:
            num_cols = 3
        elif n > 6:
            num_cols = 2
        else:
            num_cols = 1

        preset_vars = []
        max_rows = (n + num_cols - 1) // num_cols
        
        # Place preset options in the grid
        for idx, value in enumerate(predefined_values):
            is_checked = value in existing_values
            checkbox = QCheckBox(title_case(value))
            checkbox.setChecked(is_checked)
            
            col = idx // max_rows
            row = idx % max_rows
            
            group_layout.addWidget(checkbox, row, col)
            preset_vars.append((checkbox, value))
        
        # Custom fields section
        custom_frame = QFrame()
        custom_layout = QVBoxLayout(custom_frame)
        
        # Add custom field button
        add_button = QPushButton("Add Custom Field")
        add_button.clicked.connect(lambda: self.add_custom_field(custom_layout, label_text))
        custom_layout.addWidget(add_button)
        
        # Add existing custom values
        custom_values = [v for v in existing_values if v not in predefined_values]
        for value in custom_values:
            self.add_custom_field(custom_layout, label_text, value, True)
        
        # Add custom frame to group layout
        group_layout.addWidget(custom_frame, max_rows, 0, 1, num_cols)
        
        # Store references for data collection
        group_box.preset_vars = preset_vars
        group_box.custom_layout = custom_layout
        
        parent_layout.addWidget(group_box)
        return group_box
    
    def add_custom_field(self, parent_layout, field_type, value="", checked=False):
        """Add a custom field row with checkbox, entry, and delete button."""
        field_frame = QFrame()
        field_layout = QHBoxLayout(field_frame)
        
        checkbox = QCheckBox()
        checkbox.setChecked(checked)
        field_layout.addWidget(checkbox)
        
        entry = QLineEdit()
        entry.setText(value)
        entry.setPlaceholderText(f"Enter custom {field_type}")
        field_layout.addWidget(entry)
        
        delete_button = QPushButton("×")
        delete_button.setMaximumWidth(30)
        delete_button.clicked.connect(lambda: self.remove_custom_field(field_frame))
        field_layout.addWidget(delete_button)
        
        # Store references
        field_frame.checkbox = checkbox
        field_frame.entry = entry
        
        parent_layout.addWidget(field_frame)
    
    def remove_custom_field(self, field_frame):
        """Remove a custom field from the layout."""
        field_frame.setParent(None)
        field_frame.deleteLater()
    
    def create_health_section(self):
        """Create the health information section."""
        # Health conditions
        predefined_conditions = get_predefined_options('health_conditions')
        existing_conditions = self.personalization_data.get('health_conditions', [])
        self.health_conditions_group = self.create_custom_field_list(
            self.health_conditions_widget.layout(), predefined_conditions, existing_conditions, "health_conditions"
        )
        
        # Medications
        predefined_medications = get_predefined_options('medications')
        existing_medications = self.personalization_data.get('medications', [])
        self.medications_group = self.create_custom_field_list(
            self.medications_widget.layout(), predefined_medications, existing_medications, "medications"
        )
        
        # Allergies
        predefined_allergies = get_predefined_options('allergies')
        existing_allergies = self.personalization_data.get('allergies', [])
        self.allergies_group = self.create_custom_field_list(
            self.allergies_widget.layout(), predefined_allergies, existing_allergies, "allergies"
        )
    
    def create_loved_ones_section(self):
        """Create the loved ones section."""
        layout = self.loved_ones_container.layout()
        
        # Add loved one button
        add_button = QPushButton("Add Loved One")
        add_button.clicked.connect(lambda: self.add_loved_one_widget(layout))
        layout.addWidget(add_button)
        
        # Add existing loved ones
        loved_ones = self.personalization_data.get('loved_ones', [])
        for loved_one in loved_ones:
            self.add_loved_one_widget(layout, loved_one)
        
        # Store reference for data collection
        self.loved_ones_container.loved_ones_layout = layout
    
    def add_loved_one_widget(self, parent_layout, loved_one_data=None):
        """Add a loved one widget with name, relationship, and birthday fields."""
        if loved_one_data is None:
            loved_one_data = {}
        
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QFormLayout(frame)
        
        # Name
        name_entry = QLineEdit()
        name_entry.setText(loved_one_data.get('name', ''))
        layout.addRow("Name:", name_entry)
        
        # Relationship
        relationship_entry = QLineEdit()
        relationship_entry.setText(loved_one_data.get('relationship', ''))
        layout.addRow("Relationship:", relationship_entry)
        
        # Birthday
        birthday_edit = QDateEdit()
        birthday_edit.setCalendarPopup(True)
        birthday_str = loved_one_data.get('birthday', '')
        if birthday_str:
            try:
                birthday_date = QDate.fromString(birthday_str, Qt.DateFormat.ISODate)
                birthday_edit.setDate(birthday_date)
            except:
                birthday_edit.setDate(QDate.currentDate())
        else:
            birthday_edit.setDate(QDate.currentDate())
        layout.addRow("Birthday:", birthday_edit)
        
        # Remove button
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(lambda: self.remove_loved_one_widget(frame))
        layout.addRow("", remove_button)
        
        # Store references
        frame.name_entry = name_entry
        frame.relationship_entry = relationship_entry
        frame.birthday_edit = birthday_edit
        
        parent_layout.addWidget(frame)
    
    def remove_loved_one_widget(self, frame):
        """Remove a loved one widget from the layout."""
        frame.setParent(None)
        frame.deleteLater()
    
    def create_interests_section(self):
        """Create the interests section."""
        layout = self.interests_widget.layout()
        
        # Hobbies
        predefined_hobbies = get_predefined_options('hobbies')
        existing_hobbies = self.personalization_data.get('hobbies', [])
        self.hobbies_group = self.create_custom_field_list(
            layout, predefined_hobbies, existing_hobbies, "hobbies"
        )
        
        # Music preferences
        predefined_music = get_predefined_options('music_preferences')
        existing_music = self.personalization_data.get('music_preferences', [])
        self.music_group = self.create_custom_field_list(
            layout, predefined_music, existing_music, "music_preferences"
        )
        
        # Reading preferences
        predefined_reading = get_predefined_options('reading_preferences')
        existing_reading = self.personalization_data.get('reading_preferences', [])
        self.reading_group = self.create_custom_field_list(
            layout, predefined_reading, existing_reading, "reading_preferences"
        )
    
    def create_notes_section(self):
        """Create the notes section."""
        # Notes section is already in the UI file, just load existing data
        self.notes_edit.setPlainText(self.personalization_data.get('notes', ''))
        self.notes_edit.setPlaceholderText("Add any additional notes about yourself...")
    
    def create_goals_section(self):
        """Create the goals section."""
        layout = self.goals_widget.layout()
        
        # Short-term goals
        predefined_short_goals = get_predefined_options('short_term_goals')
        existing_short_goals = self.personalization_data.get('short_term_goals', [])
        self.short_goals_group = self.create_custom_field_list(
            layout, predefined_short_goals, existing_short_goals, "short_term_goals"
        )
        
        # Long-term goals
        predefined_long_goals = get_predefined_options('long_term_goals')
        existing_long_goals = self.personalization_data.get('long_term_goals', [])
        self.long_goals_group = self.create_custom_field_list(
            layout, predefined_long_goals, existing_long_goals, "long_term_goals"
        )
    
    def collect_custom_field_data(self, group_box):
        """Collect data from a custom field group box."""
        data = []
        
        # Collect preset values
        for checkbox, value in group_box.preset_vars:
            if checkbox.isChecked():
                data.append(value)
        
        # Collect custom values
        for i in range(group_box.custom_layout.count()):
            widget = group_box.custom_layout.itemAt(i).widget()
            if isinstance(widget, QFrame) and hasattr(widget, 'checkbox') and hasattr(widget, 'entry'):
                if widget.checkbox.isChecked():
                    value = widget.entry.text().strip()
                if value:
                    data.append(value)
        
        return data
    
    def collect_loved_ones_data(self):
        """Collect data from loved ones section."""
        loved_ones = []
        
        # Use the stored reference to the loved ones layout
        if hasattr(self.loved_ones_container, 'loved_ones_layout'):
            layout = self.loved_ones_container.loved_ones_layout
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if isinstance(widget, QFrame) and hasattr(widget, 'name_entry'):
                    name = widget.name_entry.text().strip()
                    relationship = widget.relationship_entry.text().strip()
                    birthday = widget.birthday_edit.date().toString(Qt.DateFormat.ISODate)
                    
                    if name or relationship:
                        loved_ones.append({
                            'name': name,
                            'relationship': relationship,
                            'birthday': birthday
                        })
        
        return loved_ones
    
    @handle_errors("saving personalization data")
    def save_personalization(self):
        """Save the personalization data."""
        try:
            # Collect basic information
            data = {
                'name': self.name_edit.text().strip(),
                'age': self.age_spin.value(),
                'timezone': self.timezone_combo.currentText(),
                
                # Health information
                'health_conditions': self.collect_custom_field_data(self.health_conditions_group),
                'medications': self.collect_custom_field_data(self.medications_group),
                'allergies': self.collect_custom_field_data(self.allergies_group),
                
                # Loved ones
                'loved_ones': self.collect_loved_ones_data(),
                
                # Interests
                'hobbies': self.collect_custom_field_data(self.hobbies_group),
                'music_preferences': self.collect_custom_field_data(self.music_group),
                'reading_preferences': self.collect_custom_field_data(self.reading_group),
                
                # Notes
                'notes': self.notes_edit.toPlainText().strip(),
                
                # Goals
                'short_term_goals': self.collect_custom_field_data(self.short_goals_group),
                'long_term_goals': self.collect_custom_field_data(self.long_goals_group),
                
                # Metadata
                'last_updated': datetime.now().isoformat(),
                'user_id': self.user_id
            }
            
            # Validate data
            validation_result = validate_personalization_data(data)
            if not validation_result['valid']:
                QMessageBox.warning(self, "Validation Error", 
                                   f"Please fix the following issues:\n\n" + 
                                   "\n".join(validation_result['errors']))
                return
            
            # Call save callback if provided
            if self.on_save:
                self.on_save(data)
            
            self.user_changed.emit()
            self.accept()
                
        except Exception as e:
            logger.error(f"Error saving personalization data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save personalization data: {str(e)}")
    
    def cancel(self):
        """Cancel the dialog."""
        self.reject()


def open_personalization_dialog(parent, user_id: str, on_save: Optional[Callable] = None, existing_data: Optional[Dict[str, Any]] = None):
    """Open the personalization dialog and return the result."""
    dialog = UserProfileDialog(parent, user_id, on_save, existing_data)
    result = dialog.exec()
    
    if result == QDialog.DialogCode.Accepted:
        return True
    else:
        return False 