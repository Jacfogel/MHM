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

# Import generated UI classes
from ui.generated.user_profile_management_dialog_pyqt import Ui_Dialog_user_profile
from ui.generated.user_profile_settings_widget_pyqt import Ui_Form_user_profile_settings

# Set up logging
from core.logger import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)

# Import core functionality
from core.user_management import (
    get_predefined_options, get_timezone_options
)
from core.user_data_validation import validate_personalization_data
from core.error_handling import handle_errors


class UserProfileDialog(QDialog):
    """PySide6-based personalization dialog for user account creation and management."""
    user_changed = Signal()

    def __init__(self, parent, user_id: str, on_save: Optional[Callable] = None, existing_data: Optional[Dict[str, Any]] = None):
        """Initialize the object."""
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
        # Use generated UI class
        self.ui = Ui_Dialog_user_profile()
        self.ui.setupUi(self)
        
        # Add the user profile settings widget to the placeholder
        from ui.widgets.user_profile_settings_widget import UserProfileSettingsWidget
        self.profile_widget = UserProfileSettingsWidget(self, self.user_id, self.personalization_data)
        layout = self.ui.widget__user_profile.layout()
        layout.addWidget(self.profile_widget)
        
        # Connect buttons
        self.ui.buttonBox_save_cancel.accepted.connect(self.save_personalization)
        self.ui.buttonBox_save_cancel.rejected.connect(self.cancel)
        
        # Override key events for large dialog
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
    def keyPressEvent(self, event):
        """Handle key press events for the dialog."""
        if event.key() == Qt.Key.Key_Escape:
            # Show confirmation dialog before canceling
            reply = QMessageBox.question(
                self, 
                "Cancel Personalization", 
                "Are you sure you want to cancel? All unsaved changes will be lost.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.cancel()
            event.accept()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Ignore Enter key to prevent accidental saving
            event.ignore()
        else:
            super().keyPressEvent(event)
    
    def create_custom_field_list(self, parent_layout, predefined_values, existing_values, label_text):
        """Creates a multi-column list with preset items (checkbox + label) and custom fields (checkbox + entry + delete)."""
        def title_case(s):
            """
            Convert snake_case or lowercase to Title Case.
            
            Args:
                s: String to convert to title case
                
            Returns:
                str: String converted to title case
            """
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
        """
        Create the health section of the personalization dialog.
        
        Returns:
            QGroupBox: Health section group box
        """
        health_group = QGroupBox("Health & Wellness")
        health_layout = QVBoxLayout(health_group)
        
        # Get predefined health options
        health_options = get_predefined_options('health_conditions')
        existing_health = self.personalization_data.get('health_conditions', [])
        
        # Create health conditions list
        self.health_group_box = self.create_custom_field_list(
            health_layout, health_options, existing_health, "health_conditions"
        )
        
        return health_group
    
    def create_loved_ones_section(self):
        """
        Create the loved ones section of the personalization dialog.
        
        Returns:
            QGroupBox: Loved ones section group box
        """
        loved_ones_group = QGroupBox("Loved Ones & Relationships")
        loved_ones_layout = QVBoxLayout(loved_ones_group)
        
        # Add loved one button
        add_button = QPushButton("Add Loved One")
        add_button.clicked.connect(lambda: self.add_loved_one_widget(loved_ones_layout))
        loved_ones_layout.addWidget(add_button)
        
        # Add existing loved ones
        existing_loved_ones = self.personalization_data.get('loved_ones', [])
        for loved_one in existing_loved_ones:
            self.add_loved_one_widget(loved_ones_layout, loved_one)
        
        # Store reference for data collection
        loved_ones_group.loved_ones_layout = loved_ones_layout
        
        return loved_ones_group
    
    def add_loved_one_widget(self, parent_layout, loved_one_data=None):
        """
        Add a loved one widget to the layout.
        
        Args:
            parent_layout: Parent layout to add the widget to
            loved_one_data: Optional existing loved one data
        """
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(frame)
        
        # Header with name and remove button
        header_layout = QHBoxLayout()
        
        name_label = QLabel("Name:")
        header_layout.addWidget(name_label)
        
        name_entry = QLineEdit()
        if loved_one_data:
            name_entry.setText(loved_one_data.get('name', ''))
        header_layout.addWidget(name_entry)
        
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(lambda: self.remove_loved_one_widget(frame))
        header_layout.addWidget(remove_button)
        
        layout.addLayout(header_layout)
        
        # Relationship type
        relationship_layout = QHBoxLayout()
        relationship_label = QLabel("Relationship:")
        relationship_layout.addWidget(relationship_label)
        
        relationship_combo = QComboBox()
        relationship_options = ['Spouse', 'Partner', 'Child', 'Parent', 'Sibling', 'Friend', 'Other']
        relationship_combo.addItems(relationship_options)
        if loved_one_data:
            relationship = loved_one_data.get('relationship', '')
            index = relationship_combo.findText(relationship)
            if index >= 0:
                relationship_combo.setCurrentIndex(index)
        relationship_layout.addWidget(relationship_combo)
        
        layout.addLayout(relationship_layout)
        
        # Notes
        notes_label = QLabel("Notes:")
        layout.addWidget(notes_label)
        
        notes_text = QTextEdit()
        notes_text.setMaximumHeight(60)
        if loved_one_data:
            notes_text.setText(loved_one_data.get('notes', ''))
        layout.addWidget(notes_text)
        
        # Store references
        frame.name_entry = name_entry
        frame.relationship_combo = relationship_combo
        frame.notes_text = notes_text
        
        parent_layout.addWidget(frame)
    
    def remove_loved_one_widget(self, frame):
        """
        Remove a loved one widget from the layout.
        
        Args:
            frame: Frame widget to remove
        """
        frame.setParent(None)
        frame.deleteLater()
    
    def create_interests_section(self):
        """
        Create the interests section of the personalization dialog.
        
        Returns:
            QGroupBox: Interests section group box
        """
        interests_group = QGroupBox("Interests & Hobbies")
        interests_layout = QVBoxLayout(interests_group)
        
        from ui.widgets.dynamic_list_container import DynamicListContainer

        existing_interests = self.personalization_data.get('interests', [])
        
        # Dynamic list container handles presets + custom entries
        self.interests_container = DynamicListContainer(self, field_key='interests')
        self.interests_container.set_values(existing_interests)
        interests_layout.addWidget(self.interests_container)
        
        return interests_group
    
    def create_notes_section(self):
        """
        Create the notes section of the personalization dialog.
        
        Returns:
            QGroupBox: Notes section group box
        """
        notes_group = QGroupBox("Additional Notes")
        notes_layout = QVBoxLayout(notes_group)
        
        notes_text = QTextEdit()
        notes_text.setPlaceholderText("Any additional notes or information...")
        notes_text.setText(self.personalization_data.get('notes', ''))
        notes_layout.addWidget(notes_text)
        
        # Store reference
        notes_group.notes_text = notes_text
        
        return notes_group
    
    def create_goals_section(self):
        """
        Create the goals section of the personalization dialog.
        
        Returns:
            QGroupBox: Goals section group box
        """
        goals_group = QGroupBox("Goals & Aspirations")
        goals_layout = QVBoxLayout(goals_group)
        
        # Get predefined goal options
        goal_options = get_predefined_options('goals')
        existing_goals = self.personalization_data.get('goals', [])
        
        # Create goals list
        self.goals_group_box = self.create_custom_field_list(
            goals_layout, goal_options, existing_goals, "goals"
        )
        
        return goals_group
    
    def collect_custom_field_data(self, group_box):
        """
        Collect data from custom field checkboxes and entries.
        
        Args:
            group_box: Group box containing custom fields
            
        Returns:
            list: List of selected values from checkboxes and custom entries
        """
        selected_values = []
        
        # Collect preset values
        for checkbox, value in group_box.preset_vars:
            if checkbox.isChecked():
                selected_values.append(value)
        
        # Collect custom values
        for i in range(group_box.custom_layout.count()):
            widget = group_box.custom_layout.itemAt(i).widget()
            if isinstance(widget, QFrame) and hasattr(widget, 'checkbox') and hasattr(widget, 'entry'):
                if widget.checkbox.isChecked():
                    custom_value = widget.entry.text().strip()
                    if custom_value:
                        selected_values.append(custom_value)
        
        return selected_values
    
    def collect_loved_ones_data(self):
        """
        Collect data from loved ones widgets.
        
        Returns:
            list: List of loved ones data dictionaries
        """
        loved_ones = []
        
        # Find the loved ones section
        for child in self.children():
            if isinstance(child, QGroupBox) and child.title() == "Loved Ones & Relationships":
                if hasattr(child, 'loved_ones_layout'):
                    layout = child.loved_ones_layout
                    for i in range(layout.count()):
                        widget = layout.itemAt(i).widget()
                        if isinstance(widget, QFrame) and hasattr(widget, 'name_entry'):
                            name = widget.name_entry.text().strip()
                            if name:  # Only include if name is provided
                                loved_one = {
                                    'name': name,
                                    'relationship': widget.relationship_combo.currentText(),
                                    'notes': widget.notes_text.toPlainText().strip()
                                }
                                loved_ones.append(loved_one)
                break
        
        return loved_ones
    
    @handle_errors("saving personalization data")
    def save_personalization(self):
        """Save the personalization data."""
        try:
            # Get data from the profile widget
            data = self.profile_widget.get_personalization_data()
            
            # Add metadata
            data['last_updated'] = datetime.now().isoformat()
            data['user_id'] = self.user_id
            
            # Validate data
            is_valid, errors = validate_personalization_data(data)
            if not is_valid:
                QMessageBox.warning(self, "Validation Error", 
                                   f"Please fix the following issues:\n\n" + 
                                   "\n".join(errors))
                return
            
            # Save data: use callback if provided, else save directly
            if self.on_save:
                self.on_save(data)
            else:
                from core.user_data_handlers import update_user_context
                update_user_context(self.user_id, data)
            
            self.user_changed.emit()
            self.accept()
                
        except Exception as e:
            logger.error(f"Error saving personalization data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save personalization data: {str(e)}")
    
    def cancel(self):
        """
        Cancel the personalization dialog.
        """
        self.reject()


def open_personalization_dialog(parent, user_id: str, on_save: Optional[Callable] = None, existing_data: Optional[Dict[str, Any]] = None):
    """
    Open the personalization dialog.
    
    Args:
        parent: Parent widget
        user_id: User ID for the personalization data
        on_save: Optional callback function to call when saving
        existing_data: Optional existing personalization data
        
    Returns:
        QDialog.DialogCode: Dialog result code
    """
    dialog = UserProfileDialog(parent, user_id, on_save, existing_data)
    return dialog.exec() 