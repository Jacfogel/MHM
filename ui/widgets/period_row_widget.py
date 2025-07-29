# period_row_widget.py - Reusable period row widget for schedules, check-ins, and tasks

import sys
import os
from typing import Dict, Any, List, Optional

# Add parent directory to path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PySide6 imports
from PySide6.QtWidgets import (
    QWidget, QButtonGroup, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

# Set up logging
from core.logger import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)

# Import core functionality
from core.schedule_management import (
    time_24h_to_12h_display, time_12h_display_to_24h
)
from core.error_handling import handle_errors

# Import generated UI
from ui.generated.period_row_template_pyqt import Ui_Form_period_row_template


class PeriodRowWidget(QWidget):
    """Reusable widget for editing time periods with days selection."""
    
    # Signals
    delete_requested = Signal(object)  # Emits the widget instance
    
    def __init__(self, parent=None, period_name: str = "", period_data: Optional[Dict[str, Any]] = None):
        """Initialize the object."""
        super().__init__(parent)
        
        # Initialize with default data if none provided
        if period_data is None:
            period_data = {
                'start_time': '18:00',
                'end_time': '20:00',
                'active': True,
                'days': ['ALL']
            }
        
        self.period_name = period_name
        self.period_data = period_data
        
        # Setup UI
        self.ui = Ui_Form_period_row_template()
        self.ui.setupUi(self)
        # Ensure dynamic property for QSS is set and style is refreshed
        self.ui.checkBox_select_all_days.setProperty("role", "header3")
        self.ui.checkBox_select_all_days.style().unpolish(self.ui.checkBox_select_all_days)
        self.ui.checkBox_select_all_days.style().polish(self.ui.checkBox_select_all_days)
        
        # Setup functionality
        self.setup_functionality()
        
        # Load data
        self.load_period_data()
        
        # Connect delete button
        self.ui.pushButton_delete.clicked.connect(self.request_delete)
    
    def setup_functionality(self):
        """Setup the widget functionality and connect signals."""
        
        # Populate hour dropdowns (1-12)
        for h in range(1, 13):
            self.ui.comboBox_start_time_hours.addItem(f"{h}")
            self.ui.comboBox_end_time_hours.addItem(f"{h}")
        
        # Populate minute dropdowns (0, 15, 30, 45)
        for m in [0, 15, 30, 45]:
            self.ui.comboBox_start_time_minutes.addItem(f"{m:02d}")
            self.ui.comboBox_end_time_minutes.addItem(f"{m:02d}")
        
        # Setup AM/PM button groups
        self.start_am_pm_group = QButtonGroup(self)
        self.start_am_pm_group.addButton(self.ui.radioButton_start_time_am)
        self.start_am_pm_group.addButton(self.ui.radioButton_start_time_pm)
        
        self.end_am_pm_group = QButtonGroup(self)
        self.end_am_pm_group.addButton(self.ui.radioButton_end_time_am)
        self.end_am_pm_group.addButton(self.ui.radioButton_end_time_pm)
        
        # Connect day selection signals
        self.ui.checkBox_select_all_days.toggled.connect(self.on_select_all_days_toggled)
        
        # Connect individual day checkboxes
        day_checkboxes = [
            self.ui.checkBox_sunday,
            self.ui.checkBox_monday,
            self.ui.checkBox_tuesday,
            self.ui.checkBox_wednesday,
            self.ui.checkBox_thursday,
            self.ui.checkBox_friday,
            self.ui.checkBox_saturday
        ]
        
        for checkbox in day_checkboxes:
            checkbox.toggled.connect(self.on_individual_day_toggled)
    
    def load_period_data(self):
        """Load period data into the widget."""
        # Set period name - preserve user's original case for custom entries
        name = self.period_name
        if not name or not name.strip():
            # If no name provided, use a default name
            name = "Task Reminder"
        
        if name.upper() == 'ALL':
            display_name = 'ALL'
        else:
            # Preserve user's original case - don't convert to title case
            display_name = name
        self.ui.lineEdit_time_period_name.setText(display_name)
        
        # Set start time
        start_time = self.period_data.get('start_time', '18:00')
        start_hour_12, start_min_val, start_is_pm = time_24h_to_12h_display(start_time)
        self.ui.comboBox_start_time_hours.setCurrentText(f"{start_hour_12}")
        self.ui.comboBox_start_time_minutes.setCurrentText(f"{start_min_val:02d}")
        self.ui.radioButton_start_time_am.setChecked(not start_is_pm)
        self.ui.radioButton_start_time_pm.setChecked(start_is_pm)
        
        # Set end time
        end_time = self.period_data.get('end_time', '20:00')
        end_hour_12, end_min_val, end_is_pm = time_24h_to_12h_display(end_time)
        self.ui.comboBox_end_time_hours.setCurrentText(f"{end_hour_12}")
        self.ui.comboBox_end_time_minutes.setCurrentText(f"{end_min_val:02d}")
        self.ui.radioButton_end_time_am.setChecked(not end_is_pm)
        self.ui.radioButton_end_time_pm.setChecked(end_is_pm)
        
        # Set active status
        self.ui.checkBox_active.setChecked(self.period_data.get('active', True))
        
        # Set days
        days = self.period_data.get('days', ['ALL'])
        self.load_days(days)
    
    def load_days(self, days: List[str]):
        """Load day selections."""
        # Clear all checkboxes first
        self.ui.checkBox_select_all_days.setChecked(False)
        self.ui.checkBox_sunday.setChecked(False)
        self.ui.checkBox_monday.setChecked(False)
        self.ui.checkBox_tuesday.setChecked(False)
        self.ui.checkBox_wednesday.setChecked(False)
        self.ui.checkBox_thursday.setChecked(False)
        self.ui.checkBox_friday.setChecked(False)
        self.ui.checkBox_saturday.setChecked(False)
        
        # Set based on days list
        if 'ALL' in days:
            self.ui.checkBox_select_all_days.setChecked(True)
        else:
            day_mapping = {
                'Sunday': self.ui.checkBox_sunday,
                'Monday': self.ui.checkBox_monday,
                'Tuesday': self.ui.checkBox_tuesday,
                'Wednesday': self.ui.checkBox_wednesday,
                'Thursday': self.ui.checkBox_thursday,
                'Friday': self.ui.checkBox_friday,
                'Saturday': self.ui.checkBox_saturday
            }
            
            for day in days:
                if day in day_mapping:
                    day_mapping[day].setChecked(True)
    
    def on_select_all_days_toggled(self, checked: bool):
        """Handle 'Select All Days' checkbox toggle."""
        day_checkboxes = [
            self.ui.checkBox_sunday,
            self.ui.checkBox_monday,
            self.ui.checkBox_tuesday,
            self.ui.checkBox_wednesday,
            self.ui.checkBox_thursday,
            self.ui.checkBox_friday,
            self.ui.checkBox_saturday
        ]
        for cb in day_checkboxes:
            cb.blockSignals(True)
            cb.setChecked(checked)
            cb.blockSignals(False)
    
    def on_individual_day_toggled(self, checked: bool):
        """Handle individual day checkbox toggle."""
        day_checkboxes = [
            self.ui.checkBox_sunday,
            self.ui.checkBox_monday,
            self.ui.checkBox_tuesday,
            self.ui.checkBox_wednesday,
            self.ui.checkBox_thursday,
            self.ui.checkBox_friday,
            self.ui.checkBox_saturday
        ]
        # If all days are checked, check 'Select All Days'
        if all(cb.isChecked() for cb in day_checkboxes):
            self.ui.checkBox_select_all_days.blockSignals(True)
            self.ui.checkBox_select_all_days.setChecked(True)
            self.ui.checkBox_select_all_days.blockSignals(False)
        else:
            self.ui.checkBox_select_all_days.blockSignals(True)
            self.ui.checkBox_select_all_days.setChecked(False)
            self.ui.checkBox_select_all_days.blockSignals(False)
    
    def get_period_data(self) -> Dict[str, Any]:
        """Get the current period data from the widget."""
        
        # Get period name
        period_name = self.ui.lineEdit_time_period_name.text().strip()
        if not period_name:
            # Use a proper default name instead of "Period"
            period_name = "Task Reminder"
        
        # Get start time
        start_hour = int(self.ui.comboBox_start_time_hours.currentText())
        start_min = int(self.ui.comboBox_start_time_minutes.currentText())
        start_is_pm = self.ui.radioButton_start_time_pm.isChecked()
        start_time = time_12h_display_to_24h(start_hour, start_min, start_is_pm)
        
        # Get end time
        end_hour = int(self.ui.comboBox_end_time_hours.currentText())
        end_min = int(self.ui.comboBox_end_time_minutes.currentText())
        end_is_pm = self.ui.radioButton_end_time_pm.isChecked()
        end_time = time_12h_display_to_24h(end_hour, end_min, end_is_pm)
        
        # Get active status
        active = self.ui.checkBox_active.isChecked()
        
        # Get days
        days = self.get_selected_days()
        
        return {
            'name': period_name,
            'start_time': start_time,
            'end_time': end_time,
            'active': active,
            'days': days
        }
    
    def get_selected_days(self) -> List[str]:
        """Get the currently selected days."""
        if self.ui.checkBox_select_all_days.isChecked():
            return ['ALL']
        
        days = []
        day_mapping = [
            ('Sunday', self.ui.checkBox_sunday),
            ('Monday', self.ui.checkBox_monday),
            ('Tuesday', self.ui.checkBox_tuesday),
            ('Wednesday', self.ui.checkBox_wednesday),
            ('Thursday', self.ui.checkBox_thursday),
            ('Friday', self.ui.checkBox_friday),
            ('Saturday', self.ui.checkBox_saturday)
        ]
        
        for day_name, checkbox in day_mapping:
            if checkbox.isChecked():
                days.append(day_name)
        
        # Return empty list if no days selected - let validation handle this
        return days
    
    def request_delete(self):
        """Request deletion of this period row."""
        self.delete_requested.emit(self)
    
    def set_period_name(self, name: str):
        """Set the period name."""
        self.ui.lineEdit_time_period_name.setText(name)
        self.period_name = name
    
    def get_period_name(self) -> str:
        """Get the current period name."""
        return self.ui.lineEdit_time_period_name.text().strip()
    
    def is_valid(self) -> bool:
        """Check if the period data is valid."""
        try:
            data = self.get_period_data()
            
            # Basic validation
            if not data['name']:
                return False
                
            # Time validation
            if not data['start_time'] or not data['end_time']:
                return False
                
            # Day validation - active periods must have at least one day selected
            if data['active'] and not data['days']:
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error validating period data: {e}")
            return False 