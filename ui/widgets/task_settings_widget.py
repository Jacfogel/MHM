# task_settings_widget.py - Task settings widget implementation

import sys
import os
from typing import Dict, Any, List, Optional

# Add parent directory to path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QWidget, QMessageBox
from ui.generated.task_settings_widget_pyqt import Ui_Form_task_settings
from tasks.task_management import get_user_task_stats

# Import core functionality
from core.schedule_management import (
    get_schedule_time_periods, set_schedule_periods, clear_schedule_periods_cache
)
from core.ui_management import (
    load_period_widgets_for_category, collect_period_data_from_widgets
)
from core.user_data_handlers import update_user_preferences
from core.error_handling import handle_errors
from core.logger import setup_logging, get_logger

# Import our period row widget
from ui.widgets.period_row_widget import PeriodRowWidget

setup_logging()
logger = get_logger(__name__)

class TaskSettingsWidget(QWidget):
    def __init__(self, parent=None, user_id=None):
        """Initialize the object."""
        super().__init__(parent)
        self.user_id = user_id
        self.ui = Ui_Form_task_settings()
        self.ui.setupUi(self)
        
        # Initialize data structures
        self.period_widgets = []
        self.deleted_periods = []  # For undo functionality
        
        self.setup_connections()
        self.load_existing_data()

    def setup_connections(self):
        """Setup signal connections."""
        # Connect time period buttons
        self.ui.pushButton_task_reminder_add_new_period.clicked.connect(lambda: self.add_new_period())
        self.ui.pushButton_undo_last__task_reminder_time_period_delete.clicked.connect(self.undo_last_period_delete)
    
    def load_existing_data(self):
        if not self.user_id:
            logger.info("TaskSettingsWidget: No user_id provided - creating new user mode")
            # For new user creation, add a default period
            self.add_new_period()
            return
        try:
            # Use the new reusable function to load period widgets
            self.period_widgets = load_period_widgets_for_category(
                layout=self.ui.verticalLayout_scrollAreaWidgetContents_task_reminder_time_periods,
                user_id=self.user_id,
                category="tasks",
                parent_widget=self,
                widget_list=self.period_widgets,
                delete_callback=self.remove_period_row
            )
        except Exception as e:
            logger.error(f"Error loading task data for user {self.user_id}: {e}")
    
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
    
    def find_lowest_available_period_number(self):
        """Find the lowest available integer (2+) that's not currently used in period names."""
        used_numbers = set()
        
        # Check existing period widgets
        for widget in self.period_widgets:
            period_name = widget.get_period_data().get('name', '')
            # Extract number from names like "Task Reminder 2", "Task Reminder 3", etc.
            if 'Task Reminder ' in period_name:
                try:
                    number = int(period_name.split('Task Reminder ')[1])
                    used_numbers.add(number)
                except (ValueError, IndexError):
                    pass
        
        # Find the lowest available number starting from 2
        number = 2
        while number in used_numbers:
            number += 1
        
        return number
    
    def add_new_period(self, checked=None, period_name=None, period_data=None):
        """Add a new time period using the PeriodRowWidget."""
        logger.info(f"TaskSettingsWidget: add_new_period called with period_name={period_name}, period_data={period_data}")
        if period_name is None:
            # Use descriptive name for default periods
            if len(self.period_widgets) == 0:
                period_name = "Task Reminder Default"
            else:
                # Find the lowest available number for new periods
                next_number = self.find_lowest_available_period_number()
                period_name = f"Task Reminder {next_number}"
        if not isinstance(period_name, str):
            logger.warning(f"TaskSettingsWidget: period_name is not a string: {period_name} (type: {type(period_name)})")
            period_name = str(period_name)
        if period_data is None:
            period_data = {'start_time': '18:00', 'end_time': '20:00', 'active': True, 'days': ['ALL']}
        # Defensive: ensure period_data is a dict
        if not isinstance(period_data, dict):
            logger.warning(f"TaskSettingsWidget: period_data is not a dict: {period_data} (type: {type(period_data)})")
            period_data = {'start_time': '18:00', 'end_time': '20:00', 'active': True, 'days': ['ALL']}
        # Create the period row widget
        period_widget = PeriodRowWidget(self, period_name, period_data)
        # Connect the delete signal
        period_widget.delete_requested.connect(self.remove_period_row)
        # Add to the scroll area layout
        layout = self.ui.verticalLayout_scrollAreaWidgetContents_task_reminder_time_periods
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
        layout = self.ui.verticalLayout_scrollAreaWidgetContents_task_reminder_time_periods
        layout.removeWidget(row_widget)
        row_widget.setParent(None)
        row_widget.deleteLater()
        
        if row_widget in self.period_widgets:
            self.period_widgets.remove(row_widget)
    
    def undo_last_period_delete(self):
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
    
    def get_task_settings(self):
        """Get the current task settings."""
        # Use the new reusable function to collect period data
        time_periods = collect_period_data_from_widgets(self.period_widgets, "tasks")
        
        return {
            'time_periods': time_periods
        }
    
    def set_task_settings(self, settings):
        """Set the task settings."""
        if not settings:
            return
        
        # Clear existing period widgets
        for widget in self.period_widgets:
            layout = self.ui.verticalLayout_scrollAreaWidgetContents_task_reminder_time_periods
            layout.removeWidget(widget)
            widget.setParent(None)
            widget.deleteLater()
        self.period_widgets.clear()
        
        # Add time periods
        time_periods = settings.get('time_periods', {})
        for period_name, period_data in time_periods.items():
            self.add_new_period(period_name, period_data)

    # Removed set_statistics method; stats are now set in the dialog, not the widget.

    def get_statistics(self):
        """Get real task statistics for the user."""
        if not self.user_id:
            return {'active': 0, 'completed': 0, 'total': 0}
        
        try:
            stats = get_user_task_stats(self.user_id)
            return {
                'active': stats.get('active_count', 0),
                'completed': stats.get('completed_count', 0),
                'total': stats.get('total_count', 0)
            }
        except Exception as e:
            # Fallback to placeholder if there's an error
            return {'active': 0, 'completed': 0, 'total': 0}

 