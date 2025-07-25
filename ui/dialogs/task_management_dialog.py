from PySide6.QtWidgets import QDialog, QMessageBox, QWidget
from ui.generated.task_management_dialog_pyqt import Ui_Dialog_task_management
from ui.widgets.task_settings_widget import TaskSettingsWidget
from PySide6.QtCore import Signal

# Import core functionality
from core.schedule_management import set_schedule_periods, clear_schedule_periods_cache
from core.user_management import update_user_preferences, update_user_account, get_user_data
from core.error_handling import handle_errors
from core.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

class TaskManagementDialog(QDialog):
    user_changed = Signal()
    def __init__(self, parent=None, user_id=None):
        super().__init__(parent)
        self.user_id = user_id
        self.ui = Ui_Dialog_task_management()
        self.ui.setupUi(self)

        # Get user account
        user_data_result = get_user_data(self.user_id, 'account')
        account = user_data_result.get('account') or {}
        features = account.get('features', {})
        tasks_enabled = features.get('task_management') == 'enabled'
        self.ui.groupBox_checkBox_enable_task_management.setChecked(tasks_enabled)

        # Add the task management widget to the placeholder
        self.task_widget = TaskSettingsWidget(self, user_id)
        layout = self.ui.widget_placeholder_task_settings.layout()
        # Remove any existing widgets
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        layout.addWidget(self.task_widget)
        
        # Populate statistics box with real values
        stats = self.task_widget.get_statistics()
        self.ui.label_total_tasks.setText(f"Active Tasks: {stats['active']}")
        self.ui.label_completed_tasks.setText(f"Completed Tasks: {stats['completed']}")
        self.ui.label_active_tasks.setText(f"Total Tasks: {stats['total']}")
        
        # Connect Save/Cancel
        self.ui.buttonBox_save_cancel.accepted.connect(self.save_task_settings)
        self.ui.buttonBox_save_cancel.rejected.connect(self.reject)

        # Wire up groupbox checkbox logic
        self.ui.groupBox_checkBox_enable_task_management.toggled.connect(self.on_enable_task_management_toggled)
        self.on_enable_task_management_toggled(self.ui.groupBox_checkBox_enable_task_management.isChecked())

    def on_enable_task_management_toggled(self, checked):
        # Enable/disable all children except the groupbox itself
        for child in self.ui.groupBox_checkBox_enable_task_management.findChildren(QWidget):
            if child is not self.ui.groupBox_checkBox_enable_task_management:
                child.setEnabled(checked)

    @handle_errors("saving task settings")
    def save_task_settings(self):
        """Save the task settings."""
        if not self.user_id:
            self.accept()
            return
        
        try:
            # Get task settings from widget
            task_settings = self.task_widget.get_task_settings()
            time_periods = task_settings.get('time_periods', {})
            
            logger.info(f"Saving task time periods for user {self.user_id}: {time_periods}")
            # When saving periods
            set_schedule_periods(self.user_id, "tasks", time_periods)
            clear_schedule_periods_cache(self.user_id, "tasks")
            
            # Update user account features
            user_data_result = get_user_data(self.user_id, 'account')
            account = user_data_result.get('account') or {}
            if 'features' not in account:
                account['features'] = {}
            account['features']['task_management'] = 'enabled' if self.ui.groupBox_checkBox_enable_task_management.isChecked() else 'disabled'
            update_user_account(self.user_id, account)
            
            QMessageBox.information(self, "Task Settings Saved", 
                                   "Task settings saved successfully.")
            self.user_changed.emit()
            self.accept()
            
        except Exception as e:
            logger.error(f"Error saving task settings for user {self.user_id}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save task settings: {str(e)}")

    def get_statistics(self):
        return self.task_widget.get_statistics() 