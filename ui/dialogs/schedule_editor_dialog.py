# schedule_editor_dialog.py - Schedule editor dialog implementation using generated UI class (no QUiLoader)

import sys
import os
from typing import Dict, Any, List, Optional, Callable

# Add parent directory to path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PySide6 imports
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QCheckBox, QComboBox, QGroupBox, QGridLayout, QWidget, QMessageBox,
    QScrollArea, QFrame, QDialogButtonBox, QTimeEdit, QSpinBox,
    QButtonGroup, QRadioButton, QSizePolicy
)
from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QFont

# Set up logging
from core.logger import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)

# Import core functionality
from core.schedule_management import (
    get_schedule_time_periods, set_schedule_periods, clear_schedule_periods_cache,
    validate_and_format_time, time_24h_to_12h_display, time_12h_display_to_24h
)
from core.ui_management import (
    load_period_widgets_for_category, collect_period_data_from_widgets
)
from core.error_handling import handle_errors
from core.user_data_validation import title_case

# Import our new period row widget
from ui.widgets.period_row_widget import PeriodRowWidget
from ui.generated.schedule_editor_dialog_pyqt import Ui_Dialog_edit_schedule


class ScheduleEditorDialog(QDialog):
    """Dialog for editing schedules."""
    
    def __init__(self, parent=None, user_id=None, category=None, on_save: Optional[Callable] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.category = category
        self.on_save = on_save
        
        # Initialize data structures
        self.period_widgets = []  # Keep list of widgets like other dialogs
        self.deleted_periods = []  # For undo functionality
        
        # Setup window
        self.setWindowTitle(f"Edit Schedule - {category.title()}")
        self.setMinimumHeight(400)
        self.adjustSize()
        self.setModal(True)

        # Set up UI using generated class
        self.ui = Ui_Dialog_edit_schedule()
        self.ui.setupUi(self)
        
        # Get the layout for period rows inside the scroll area
        self.periods_layout = self.ui.verticalLayout_3
        
        # Setup functionality
        self.setup_functionality()
        
        # Load existing data
        self.load_existing_data()
        
        # Center the dialog
        self.center_dialog()
    
    def center_dialog(self):
        """Center the dialog on the parent window."""
        if self.parent():
            parent_geometry = self.parent().geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)
    
    def setup_functionality(self):
        """Setup the functionality and connect signals."""
        # Connect buttons
        self.ui.pushButton_add_new_period.clicked.connect(lambda: self.add_new_period())
        self.ui.pushButton_undo_last__time_period_delete.clicked.connect(self.undo_last_delete)
        
        # Connect dialog buttons
        self.ui.buttonBox_save_cancel.accepted.connect(self.save_schedule)
        self.ui.buttonBox_save_cancel.rejected.connect(self.cancel)
        
        # Update title
        self.ui.label_EditSchedule.setText(f"Edit Schedule - {title_case(self.category)}")
        
        # Update group box title
        self.ui.groupBox_time_periods.setTitle("Time Periods")
    
    def load_existing_data(self):
        """Load existing schedule data using the new reusable function."""
        try:
            # Use the new reusable function to load period widgets
            self.period_widgets = load_period_widgets_for_category(
                layout=self.periods_layout,
                user_id=self.user_id,
                category=self.category,
                parent_widget=self,
                widget_list=self.period_widgets,
                delete_callback=self.remove_period_row
            )
        except Exception as e:
            logger.error(f"Error loading schedule data for user {self.user_id}, category {self.category}: {e}")
    
    def add_new_period(self, period_name=None, period_data=None):
        """Add a new period row using the PeriodRowWidget."""
        if period_name is None:
            period_name = f"Period {len(self.period_widgets) + 1}"
        if period_data is None:
            period_data = {'start_time': '18:00', 'end_time': '20:00', 'active': True, 'days': ['ALL']}
        
        # Create the period row widget
        period_widget = PeriodRowWidget(self, period_name, period_data)
        
        # Connect the delete signal
        period_widget.delete_requested.connect(self.remove_period_row)
        
        # Add to layout
        self.periods_layout.addWidget(period_widget)
        
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
                'start_time': period_data['start'],
                'end_time': period_data['end'],
                'active': period_data['active'],
                'days': period_data['days']
            }
            self.deleted_periods.append(deleted_data)
        
        self.periods_layout.removeWidget(row_widget)
        row_widget.setParent(None)
        row_widget.deleteLater()
        
        if row_widget in self.period_widgets:
            self.period_widgets.remove(row_widget)
    
    def undo_last_delete(self):
        """Undo the last deletion."""
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
        
        # Add it back to the grid
        self.add_new_period(deleted_data['period_name'], period_data)
    
    def collect_period_data(self) -> Dict[str, Any]:
        """Collect period data using the new reusable function."""
        return collect_period_data_from_widgets(self.period_widgets, self.category)
    
    @handle_errors("saving schedule")
    def save_schedule(self):
        """Save the schedule data."""
        try:
            # Collect data from UI
            periods = self.collect_period_data()
            
            # Validate times
            for period_name, period_data in periods.items():
                try:
                    validate_and_format_time(period_data['start'])
                    validate_and_format_time(period_data['end'])
                except Exception as e:
                    QMessageBox.warning(self, "Invalid Time", 
                                       f"Invalid time format in {period_name}: {str(e)}")
                    return
            
            # Save the schedule
            set_schedule_periods(self.user_id, self.category, periods)
            
            # Clear cache
            clear_schedule_periods_cache(self.user_id, self.category)
            
            # Call on_save callback if provided
            if self.on_save:
                self.on_save()
            
            logger.info(f"Schedule saved for user {self.user_id}, category {self.category}")
            self.accept()
            
        except Exception as e:
            logger.error(f"Error saving schedule: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save schedule: {str(e)}")
    
    def cancel(self):
        """Cancel the dialog."""
        self.reject()
    
    def get_schedule_data(self):
        """Get the current schedule data."""
        return self.collect_period_data()
    
    def set_schedule_data(self, data):
        """Set the schedule data."""
        if not data:
            return
        
        # Clear existing period widgets
        for widget in self.period_widgets:
            self.periods_layout.removeWidget(widget)
            widget.setParent(None)
            widget.deleteLater()
        self.period_widgets.clear()
        
        # Add periods
        for period_name, period_data in data.items():
            self.add_new_period(period_name, period_data)


def open_schedule_editor(parent, user_id: str, category: str, on_save: Optional[Callable] = None):
    """Open the schedule editor dialog."""
    dialog = ScheduleEditorDialog(parent, user_id, category, on_save)
    return dialog.exec() 