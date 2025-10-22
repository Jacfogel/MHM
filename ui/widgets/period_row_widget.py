# period_row_widget.py - Reusable period row widget for schedules, check-ins, and tasks

from typing import Dict, Any, List, Optional

# PySide6 imports
from PySide6.QtWidgets import (
    QWidget, QButtonGroup
)
from PySide6.QtCore import Signal

# Set up logging
from core.logger import setup_logging, get_component_logger
setup_logging()
logger = get_component_logger('ui')
widget_logger = logger

# Import core functionality
from core.schedule_management import (
    get_period_data__time_24h_to_12h_display, get_period_data__time_12h_display_to_24h
)
from core.error_handling import handle_errors

# Import generated UI
from ui.generated.period_row_template_pyqt import Ui_Form_period_row_template


class PeriodRowWidget(QWidget):
    """Reusable widget for editing time periods with days selection."""
    
    # Signals
    delete_requested = Signal(object)  # Emits the widget instance
    
    @handle_errors("initializing period row widget")
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
        
        # For ALL periods, ensure correct data
        if period_name.upper() == "ALL":
            period_data = {
                'start_time': '00:00',
                'end_time': '23:59',
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
        
        # If this is an ALL period, ensure it's properly configured as read-only
        # Do this AFTER loading data to ensure proper state
        if period_name.upper() == "ALL":
            # Force the correct state for ALL periods
            self.ui.checkBox_active.setChecked(True)
            self.ui.checkBox_select_all_days.setChecked(True)
            # Ensure all individual days are checked
            self.ui.checkBox_sunday.setChecked(True)
            self.ui.checkBox_monday.setChecked(True)
            self.ui.checkBox_tuesday.setChecked(True)
            self.ui.checkBox_wednesday.setChecked(True)
            self.ui.checkBox_thursday.setChecked(True)
            self.ui.checkBox_friday.setChecked(True)
            self.ui.checkBox_saturday.setChecked(True)
            # Now set read-only
            self.set_read_only(True)
    
    @handle_errors("setting up period row functionality", default_return=None)
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
    
    @handle_errors("loading period data", default_return=None)
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
        start_hour_12, start_min_val, start_is_pm = get_period_data__time_24h_to_12h_display(start_time)
        self.ui.comboBox_start_time_hours.setCurrentText(f"{start_hour_12}")
        self.ui.comboBox_start_time_minutes.setCurrentText(f"{start_min_val:02d}")
        self.ui.radioButton_start_time_am.setChecked(not start_is_pm)
        self.ui.radioButton_start_time_pm.setChecked(start_is_pm)
        
        # Set end time
        end_time = self.period_data.get('end_time', '20:00')
        end_hour_12, end_min_val, end_is_pm = get_period_data__time_24h_to_12h_display(end_time)
        self.ui.comboBox_end_time_hours.setCurrentText(f"{end_hour_12}")
        self.ui.comboBox_end_time_minutes.setCurrentText(f"{end_min_val:02d}")
        self.ui.radioButton_end_time_am.setChecked(not end_is_pm)
        self.ui.radioButton_end_time_pm.setChecked(end_is_pm)
        
        # Set active status
        self.ui.checkBox_active.setChecked(self.period_data.get('active', True))
        
        # Set days
        days = self.period_data.get('days', ['ALL'])
        self.load_days(days)
    
    @handle_errors("loading days", default_return=None)
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
    
    @handle_errors("handling select all days toggle", default_return=None)
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
    
    @handle_errors("handling individual day toggle", default_return=None)
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
    
    @handle_errors("getting period data from widget")
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
        start_time = get_period_data__time_12h_display_to_24h(start_hour, start_min, start_is_pm)
        
        # Get end time
        end_hour = int(self.ui.comboBox_end_time_hours.currentText())
        end_min = int(self.ui.comboBox_end_time_minutes.currentText())
        end_is_pm = self.ui.radioButton_end_time_pm.isChecked()
        end_time = get_period_data__time_12h_display_to_24h(end_hour, end_min, end_is_pm)
        
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
    
    @handle_errors("getting selected days from widget")
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
    
    @handle_errors("requesting delete")
    def request_delete(self):
        """Request deletion of this period row."""
        self.delete_requested.emit(self)
    
    @handle_errors("setting period name")
    def set_period_name(self, name: str):
        """Set the period name."""
        self.ui.lineEdit_time_period_name.setText(name)
        self.period_name = name
    
    @handle_errors("getting period name")
    def get_period_name(self) -> str:
        """Get the current period name."""
        return self.ui.lineEdit_time_period_name.text().strip()
    
    @handle_errors("validating period data")
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
    
    @handle_errors("setting read only mode")
    def set_read_only(self, read_only: bool = True):
        """Set the widget to read-only mode."""
        self._set_read_only__time_inputs(read_only)
        self._set_read_only__checkbox_states(read_only)
        self._set_read_only__delete_button_visibility(read_only)
        self._set_read_only__visual_styling(read_only)
        self._set_read_only__force_style_updates()
    
    @handle_errors("setting read only time inputs")
    def _set_read_only__time_inputs(self, read_only: bool):
        """Set time input widgets to read-only mode."""
        self.ui.lineEdit_time_period_name.setReadOnly(read_only)
        self.ui.comboBox_start_time_hours.setEnabled(not read_only)
        self.ui.comboBox_start_time_minutes.setEnabled(not read_only)
        self.ui.radioButton_start_time_am.setEnabled(not read_only)
        self.ui.radioButton_start_time_pm.setEnabled(not read_only)
        self.ui.comboBox_end_time_hours.setEnabled(not read_only)
        self.ui.comboBox_end_time_minutes.setEnabled(not read_only)
        self.ui.radioButton_end_time_am.setEnabled(not read_only)
        self.ui.radioButton_end_time_pm.setEnabled(not read_only)
    
    @handle_errors("setting read only checkbox states")
    def _set_read_only__checkbox_states(self, read_only: bool):
        """Set checkbox states based on read-only mode and period type."""
        if read_only and self.get_period_name().upper() == "ALL":
            self._set_read_only__all_period_read_only()
        else:
            self._set_read_only__normal_checkbox_states(read_only)
    
    @handle_errors("setting all period read only")
    def _set_read_only__all_period_read_only(self):
        """Set ALL period to read-only with all days selected."""
        # Ensure ALL period is active and has all days selected
        self.ui.checkBox_active.setChecked(True)
        self.ui.checkBox_active.setEnabled(False)
        self.ui.checkBox_select_all_days.setChecked(True)
        self.ui.checkBox_select_all_days.setEnabled(False)
        
        # Ensure individual days are all checked but disabled
        day_checkboxes = self._get_day_checkboxes()
        for checkbox in day_checkboxes:
            checkbox.setChecked(True)
            checkbox.setEnabled(False)
    
    @handle_errors("setting normal checkbox states")
    def _set_read_only__normal_checkbox_states(self, read_only: bool):
        """Set normal checkbox states for non-ALL periods."""
        self.ui.checkBox_active.setEnabled(not read_only)
        self.ui.checkBox_select_all_days.setEnabled(not read_only)
        
        day_checkboxes = self._get_day_checkboxes()
        for checkbox in day_checkboxes:
            checkbox.setEnabled(not read_only)
    
    @handle_errors("getting day checkboxes")
    def _get_day_checkboxes(self):
        """Get list of day checkboxes."""
        return [
            self.ui.checkBox_sunday, self.ui.checkBox_monday, self.ui.checkBox_tuesday,
            self.ui.checkBox_wednesday, self.ui.checkBox_thursday, self.ui.checkBox_friday,
            self.ui.checkBox_saturday
        ]
    
    @handle_errors("setting delete button visibility")
    def _set_read_only__delete_button_visibility(self, read_only: bool):
        """Set delete button visibility based on read-only state."""
        self.ui.pushButton_delete.setVisible(not read_only)
    
    @handle_errors("setting visual styling")
    def _set_read_only__visual_styling(self, read_only: bool):
        """Apply visual styling for read-only state."""
        if read_only:
            self._set_read_only__apply_read_only_styling()
        else:
            self._set_read_only__clear_read_only_styling()
    
    @handle_errors("applying read only styling")
    def _set_read_only__apply_read_only_styling(self):
        """Apply read-only visual styling."""
        self.setStyleSheet("QWidget { background-color: #f0f0f0; }")
        self.ui.lineEdit_time_period_name.setStyleSheet("QLineEdit { background-color: #e0e0e0; color: #666666; }")
        
        # Set readonly property for QSS styling
        self.ui.checkBox_active.setProperty("readonly", True)
        self.ui.checkBox_select_all_days.setProperty("readonly", True)
        
        day_checkboxes = self._get_day_checkboxes()
        for checkbox in day_checkboxes:
            checkbox.setProperty("readonly", True)
    
    @handle_errors("clearing read only styling")
    def _set_read_only__clear_read_only_styling(self):
        """Clear read-only visual styling."""
        self.setStyleSheet("")
        self.ui.lineEdit_time_period_name.setStyleSheet("")
        
        # Clear readonly property
        self.ui.checkBox_active.setProperty("readonly", False)
        self.ui.checkBox_select_all_days.setProperty("readonly", False)
        
        day_checkboxes = self._get_day_checkboxes()
        for checkbox in day_checkboxes:
            checkbox.setProperty("readonly", False)
    
    @handle_errors("forcing style updates")
    def _set_read_only__force_style_updates(self):
        """Force style updates for all checkboxes."""
        self.ui.checkBox_active.style().unpolish(self.ui.checkBox_active)
        self.ui.checkBox_active.style().polish(self.ui.checkBox_active)
        self.ui.checkBox_select_all_days.style().unpolish(self.ui.checkBox_select_all_days)
        self.ui.checkBox_select_all_days.style().polish(self.ui.checkBox_select_all_days)
        
        day_checkboxes = self._get_day_checkboxes()
        for checkbox in day_checkboxes:
            checkbox.style().unpolish(checkbox)
            checkbox.style().polish(checkbox) 