# schedule_editor_dialog.py - Schedule editor dialog implementation using generated UI class (no QUiLoader)

import sys
import os
from typing import Dict, Any, Optional, Callable

# Add parent directory to path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PySide6 imports
from PySide6.QtWidgets import (
    QDialog, QMessageBox
)

# Set up logging
from core.logger import setup_logging, get_component_logger
setup_logging()
logger = get_component_logger('ui')
dialog_logger = logger

# Import core functionality
from core.schedule_management import (
    clear_schedule_periods_cache,
    set_schedule_periods,
    set_schedule_days
)
from core.ui_management import (
    load_period_widgets_for_category, collect_period_data_from_widgets
)
from core.error_handling import handle_errors
from core.user_data_validation import _shared__title_case, validate_schedule_periods

# Import our new period row widget
from ui.widgets.period_row_widget import PeriodRowWidget
from ui.generated.schedule_editor_dialog_pyqt import Ui_Dialog_edit_schedule


class ScheduleEditorDialog(QDialog):
    """Dialog for editing schedules."""
    
    @handle_errors("initializing schedule editor dialog")
    def __init__(self, parent=None, user_id=None, category=None, on_save: Optional[Callable] = None):
        """Initialize the object."""
        try:
            super().__init__(parent)
            self.user_id = user_id
            self.category = category
            self.on_save = on_save
            
            # Initialize data structures
            self.period_widgets = []  # Keep list of widgets like other dialogs
            self.deleted_periods = []  # For undo functionality
            self.creation_counter = 0  # Track creation order for sorting
            
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
        except Exception as e:
            logger.error(f"Error initializing schedule editor dialog: {e}")
            raise
    
    @handle_errors("centering dialog", default_return=None)
    def center_dialog(self):
        """Center the dialog on the parent window."""
        if self.parent():
            parent_geometry = self.parent().geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)
    
    @handle_errors("setting up functionality", default_return=None)
    def setup_functionality(self):
        """Setup the functionality and connect signals."""
        # Connect buttons
        self.ui.pushButton_add_new_period.clicked.connect(lambda: self.add_new_period())
        self.ui.pushButton_undo_last__time_period_delete.clicked.connect(self.undo_last_delete)
        
        # Connect dialog buttons
        self.ui.buttonBox_save_cancel.accepted.connect(self.handle_save)
        self.ui.buttonBox_save_cancel.rejected.connect(self.cancel)
        
        # Update title
        self.ui.label_EditSchedule.setText(f"Edit Schedule - {_shared__title_case(self.category)}")
        
        # Update group box title
        self.ui.groupBox_time_periods.setTitle("Time Periods")
    
    @handle_errors("loading existing data", default_return=None)
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
            
            # Assign creation order to existing widgets (older first)
            for i, widget in enumerate(self.period_widgets):
                widget.creation_order = i
            self.creation_counter = len(self.period_widgets)
            
        except Exception as e:
            logger.error(f"Error loading schedule data for user {self.user_id}, category {self.category}: {e}")
    
    @handle_errors("adding new period", default_return=None)
    def add_new_period(self, period_name=None, period_data=None):
        """Add a new period row using the PeriodRowWidget."""
        if period_name is None:
            # Use descriptive name for default periods (title case for consistency)
            # Replace underscores with spaces before applying title case
            category_display = self.category.replace('_', ' ').title()
            if len(self.period_widgets) == 0:
                period_name = f"{category_display} Message Default"
            else:
                # Find the lowest available number for new periods
                next_number = self.find_lowest_available_period_number()
                period_name = f"{category_display} Message {next_number}"
        if period_data is None:
            period_data = {'start_time': '18:00', 'end_time': '20:00', 'active': True, 'days': ['ALL']}
        
        # Create the period row widget
        period_widget = PeriodRowWidget(self, period_name, period_data)
        
        # Connect the delete signal
        period_widget.delete_requested.connect(self.remove_period_row)
        
        # Assign creation order for sorting
        period_widget.creation_order = self.creation_counter
        self.creation_counter += 1
        
        # Store reference first
        self.period_widgets.append(period_widget)
        
        # Re-sort the layout to maintain proper order (ALL at bottom)
        self.resort_period_widgets()
        
        return period_widget

    @handle_errors("resorting period widgets", default_return=None)
    def resort_period_widgets(self):
        """Re-sort the period widgets to maintain proper order (ALL at bottom)."""
        # Remove all widgets from layout
        while self.periods_layout.count():
            item = self.periods_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Sort widgets: ALL periods at bottom, others by creation order (newest at end, before ALL)
        def sort_key(widget):
            period_name = widget.get_period_name()
            if period_name.upper() == "ALL":
                return (999999, period_name)  # Put ALL at the end
            else:
                # For non-ALL periods, use creation order (newer periods at end, before ALL)
                creation_order = getattr(widget, 'creation_order', 0)
                return (0, creation_order)  # Positive so newer (higher numbers) come last
        
        sorted_widgets = sorted(self.period_widgets, key=sort_key)
        
        # Add widgets back to layout in sorted order
        for widget in sorted_widgets:
            self.periods_layout.addWidget(widget)

    @handle_errors("finding lowest available period number", default_return=2)
    def find_lowest_available_period_number(self):
        """Find the lowest available number for new period names."""
        try:
            used_numbers = set()
            for widget in self.period_widgets:
                period_name = widget.get_period_name()
                # Extract number from period name (e.g., "Category Message 2" -> 2)
                import re
                match = re.search(r'Message\s+(\d+)$', period_name)
                if match:
                    used_numbers.add(int(match.group(1)))
            
            # Find the lowest available number starting from 2
            number = 2
            while number in used_numbers:
                number += 1
            return number
        except Exception as e:
            logger.error(f"Error finding lowest available period number: {e}")
            return 2

    @handle_errors("removing period row")
    def remove_period_row(self, row_widget):
        """Remove a period row and store it for undo."""
        try:
            # Prevent deletion of "ALL" periods for category messages
            if isinstance(row_widget, PeriodRowWidget):
                period_name = row_widget.get_period_name()
                if period_name.upper() == "ALL" and self.category not in ("tasks", "checkin"):
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.information(
                        self,
                        "Cannot Delete ALL Period",
                        "The 'ALL' period cannot be deleted as it is a system-managed period that ensures messages can always be sent."
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
            
            self.periods_layout.removeWidget(row_widget)
            row_widget.setParent(None)
            row_widget.deleteLater()
            
            if row_widget in self.period_widgets:
                self.period_widgets.remove(row_widget)
        except Exception as e:
            logger.error(f"Error removing period row: {e}")
            raise
    
    @handle_errors("undoing last delete")
    def undo_last_delete(self):
        """Undo the last deletion."""
        try:
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
        except Exception as e:
            logger.error(f"Error undoing last delete: {e}")
            raise
    
    @handle_errors("collecting period data", default_return={})
    def collect_period_data(self) -> Dict[str, Any]:
        """Collect period data using the new reusable function."""
        try:
            return collect_period_data_from_widgets(self.period_widgets, self.category)
        except Exception as e:
            logger.error(f"Error collecting period data: {e}")
            return {}
    
    @handle_errors("handling save")
    def handle_save(self):
        """Handle save button click - prevents dialog closure on validation errors."""
        try:
            if self.save_schedule():
                # Only close dialog if save was successful
                self.accept()
        except Exception as e:
            logger.error(f"Error handling save: {e}")
            raise
    
    @handle_errors("saving schedule", default_return=False)
    def save_schedule(self):
        """Save the schedule data."""
        try:
            # Collect data from UI
            periods = self.collect_period_data()
            
            # Validate periods using centralized validation
            is_valid, errors = validate_schedule_periods(periods, self.category)
            if not is_valid:
                # Use information instead of warning to avoid modal issues
                QMessageBox.information(
                    self,
                    "Validation Error",
                    f"Schedule validation failed:\n\n{errors[0]}",
                )
                # Ensure dialog stays active
                self.raise_()
                self.activateWindow()
                return False
            
            # Save the schedule
            set_schedule_periods(self.user_id, self.category, periods)
            
            # Clear cache
            clear_schedule_periods_cache(self.user_id, self.category)
            
            # Trigger rescheduling for this user and category
            self._trigger_rescheduling()
            
            # Call on_save callback if provided
            if self.on_save:
                self.on_save()
            
            logger.info(f"Schedule saved for user {self.user_id}, category {self.category}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving schedule: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save schedule: {str(e)}")
            return False
    
    @handle_errors("triggering rescheduling")
    def _trigger_rescheduling(self):
        """Trigger rescheduling for this user and category when schedule changes."""
        try:
            import json
            import os
            from datetime import datetime
            
            # Create a reschedule request file that the service will pick up
            request_data = {
                'user_id': self.user_id,
                'category': self.category,
                'timestamp': datetime.now().isoformat(),
                'source': 'schedule_editor'
            }
            
            # Create the requests directory if it doesn't exist
            # Use test data directory if in test environment, otherwise use production directory
            import core.config
            if hasattr(core.config, 'BASE_DATA_DIR') and core.config.BASE_DATA_DIR != 'data':
                # We're in a test environment (BASE_DATA_DIR is patched to tests/data), use test data directory
                requests_dir = os.path.join(core.config.BASE_DATA_DIR, 'requests')
            else:
                # Production environment, use standard data directory
                requests_dir = 'data/requests'
            os.makedirs(requests_dir, exist_ok=True)
            
            # Create a unique filename
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            filename = f"reschedule_{self.user_id}_{self.category}_{timestamp_str}.json"
            request_file = os.path.join(requests_dir, filename)
            
            # Write the request file
            with open(request_file, 'w') as f:
                json.dump(request_data, f, indent=2)
            
            logger.info(f"Created reschedule request for user {self.user_id}, category {self.category}")
            
        except Exception as e:
            logger.error(f"Error creating reschedule request: {e}")
            # Don't fail the save operation if rescheduling fails
    
    @handle_errors("canceling dialog")
    def cancel(self):
        """Cancel the dialog."""
        try:
            self.reject()
        except Exception as e:
            logger.error(f"Error canceling dialog: {e}")
            raise
    
    @handle_errors("getting schedule data", default_return={})
    def get_schedule_data(self):
        """Get the current schedule data."""
        try:
            return self.collect_period_data()
        except Exception as e:
            logger.error(f"Error getting schedule data: {e}")
            return {}
    
    @handle_errors("setting schedule data")
    def set_schedule_data(self, data):
        """Set the schedule data."""
        try:
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
        except Exception as e:
            logger.error(f"Error setting schedule data: {e}")
            raise


def open_schedule_editor(parent, user_id: str, category: str, on_save: Optional[Callable] = None):
    """Open the schedule editor dialog."""
    dialog = ScheduleEditorDialog(parent, user_id, category, on_save)
    return dialog.exec() 