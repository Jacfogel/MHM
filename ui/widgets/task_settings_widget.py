# task_settings_widget.py - Task settings widget implementation

from PySide6.QtWidgets import QWidget, QMessageBox
from ui.generated.task_settings_widget_pyqt import Ui_Form_task_settings
from tasks.task_management import get_user_task_stats

# Import core functionality
from core.ui_management import (
    load_period_widgets_for_category, collect_period_data_from_widgets
)
from core.user_data_handlers import get_user_data, update_user_preferences
from core.error_handling import handle_errors
from core.logger import setup_logging, get_component_logger

# Import our period row widget and tag widget
from ui.widgets.period_row_widget import PeriodRowWidget
from ui.widgets.tag_widget import TagWidget

setup_logging()
logger = get_component_logger('ui')
widget_logger = logger

class TaskSettingsWidget(QWidget):
    @handle_errors("initializing task settings widget")
    def __init__(self, parent=None, user_id=None):
        """Initialize the object."""
        super().__init__(parent)
        self.user_id = user_id
        self.ui = Ui_Form_task_settings()
        self.ui.setupUi(self)
        
        # Initialize data structures
        self.period_widgets = []
        self.deleted_periods = []  # For undo functionality
        
        # Add tag management widget to placeholder
        self.tag_widget = TagWidget(self, user_id, mode="management", title="Task Tags")
        layout = self.ui.verticalLayout_widget_tag_management_placeholder.layout()
        layout.addWidget(self.tag_widget)
        
        self.setup_connections()
        self.load_existing_data()

    @handle_errors("setting up connections")
    def setup_connections(self):
        """Setup signal connections."""
        # Connect time period buttons
        self.ui.pushButton_task_reminder_add_new_period.clicked.connect(lambda: self.add_new_period())
        self.ui.pushButton_undo_last__task_reminder_time_period_delete.clicked.connect(self.undo_last_period_delete)
    
    @handle_errors("loading existing data")
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
            
            # Load recurring task settings
            self.load_recurring_task_settings()
        except Exception as e:
            logger.error(f"Error loading task data for user {self.user_id}: {e}")
    
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
    
    @handle_errors("finding lowest available period number")
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
    
    @handle_errors("adding new period")
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
    
    @handle_errors("removing period row")
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
    
    @handle_errors("undoing last period delete")
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
    
    @handle_errors("getting task settings")
    def get_task_settings(self):
        """Get the current task settings."""
        # Use the new reusable function to collect period data
        time_periods = collect_period_data_from_widgets(self.period_widgets, "tasks")
        
        # Get tags from the tag widget
        tags = self.tag_widget.get_available_tags() if hasattr(self, 'tag_widget') else []
        
        # Get recurring task settings
        recurring_settings = self.get_recurring_task_settings()
        
        return {
            'time_periods': time_periods,
            'tags': tags,
            'recurring_settings': recurring_settings
        }
    
    @handle_errors("setting task settings")
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
        
        # Set recurring task settings
        recurring_settings = settings.get('recurring_settings', {})
        self.set_recurring_task_settings(recurring_settings)

    @handle_errors("getting statistics")
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

    @handle_errors("getting available tags")
    def get_available_tags(self):
        """Get the current list of available tags from the tag widget."""
        return self.tag_widget.get_available_tags()

    @handle_errors("refreshing tags")
    def refresh_tags(self):
        """Refresh the tags in the tag widget."""
        self.tag_widget.refresh_tags()
    
    @handle_errors("undoing last tag delete")
    def undo_last_tag_delete(self):
        """Undo the last tag deletion (account creation mode only)."""
        return self.tag_widget.undo_last_tag_delete()

    @handle_errors("getting recurring task settings")
    def get_recurring_task_settings(self):
        """Get the current recurring task settings."""
        pattern_index = self.ui.comboBox_recurring_pattern.currentIndex()
        pattern_map = {
            0: None,  # None (One-time tasks)
            1: 'daily',
            2: 'weekly', 
            3: 'monthly',
            4: 'yearly'
        }
        
        return {
            'default_recurrence_pattern': pattern_map.get(pattern_index),
            'default_recurrence_interval': self.ui.spinBox_recurring_interval.value(),
            'default_repeat_after_completion': self.ui.checkBox_repeat_after_completion.isChecked()
        }
    
    @handle_errors("setting recurring task settings")
    def set_recurring_task_settings(self, settings):
        """Set the recurring task settings."""
        if not settings:
            return
        
        # Set pattern
        pattern = settings.get('default_recurrence_pattern')
        pattern_map = {
            None: 0,  # None (One-time tasks)
            'daily': 1,
            'weekly': 2,
            'monthly': 3,
            'yearly': 4
        }
        pattern_index = pattern_map.get(pattern, 0)
        self.ui.comboBox_recurring_pattern.setCurrentIndex(pattern_index)
        
        # Set interval
        interval = settings.get('default_recurrence_interval', 1)
        self.ui.spinBox_recurring_interval.setValue(interval)
        
        # Set repeat after completion
        repeat_after = settings.get('default_repeat_after_completion', True)
        self.ui.checkBox_repeat_after_completion.setChecked(repeat_after)
    
    @handle_errors("loading recurring task settings")
    def load_recurring_task_settings(self):
        """Load recurring task settings from user preferences."""
        if not self.user_id:
            return
        
        try:
            user_data = get_user_data(self.user_id, 'preferences')
            preferences = user_data.get('preferences', {})
            task_settings = preferences.get('task_settings', {})
            recurring_settings = task_settings.get('recurring_settings', {})
            
            self.set_recurring_task_settings(recurring_settings)
        except Exception as e:
            logger.error(f"Error loading recurring task settings for user {self.user_id}: {e}")
    
    @handle_errors("saving recurring task settings")
    def save_recurring_task_settings(self):
        """Save recurring task settings to user preferences."""
        if not self.user_id:
            return
        
        try:
            recurring_settings = self.get_recurring_task_settings()
            
            # Get current preferences
            user_data = get_user_data(self.user_id, 'preferences')
            preferences = user_data.get('preferences', {})
            task_settings = preferences.get('task_settings', {})
            
            # Update recurring settings
            task_settings['recurring_settings'] = recurring_settings
            preferences['task_settings'] = task_settings
            
            # Save back to user data
            update_user_preferences(self.user_id, preferences)
            
        except Exception as e:
            logger.error(f"Error saving recurring task settings for user {self.user_id}: {e}")

 