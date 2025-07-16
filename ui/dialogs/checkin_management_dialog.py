# checkin_management_dialog.py - Check-in management dialog implementation

import sys
import os
from typing import Dict, Any, Optional

# Add parent directory to path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PySide6 imports
from PySide6.QtWidgets import QDialog, QMessageBox, QWidget
from PySide6.QtCore import Signal

# Set up logging
from core.logger import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)

# Import core functionality
from core.schedule_management import set_schedule_periods, clear_schedule_periods_cache
from core.user_management import update_user_preferences, get_user_data, update_user_account
from core.error_handling import handle_errors

# Import widget
from ui.widgets.checkin_settings_widget import CheckinSettingsWidget
from ui.generated.checkin_management_dialog_pyqt import Ui_Dialog_checkin_management


class CheckinManagementDialog(QDialog):
    """Dialog for managing check-in settings."""
    user_changed = Signal()
    
    def __init__(self, parent=None, user_id=None):
        super().__init__(parent)
        self.user_id = user_id
        self.ui = Ui_Dialog_checkin_management()
        self.ui.setupUi(self)
        # Load user account to set groupbox checked state
        checkins_enabled = False
        if self.user_id:
            user_data_result = get_user_data(self.user_id, 'account')
            account = user_data_result.get('account') or {}
            features = account.get('features', {})
            checkins_enabled = features.get('checkins') == 'enabled'
        self.ui.groupBox_checkBox_enable_checkins.setChecked(checkins_enabled)
        # Add the check-in settings widget to the placeholder
        self.checkin_widget = CheckinSettingsWidget(self, self.user_id)
        layout = self.ui.widget_placeholder_checkin_settings.layout()
        # Remove any existing widgets
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        layout.addWidget(self.checkin_widget)
        # Connect Save/Cancel
        self.ui.buttonBox_save_cancel.accepted.connect(self.save_checkin_settings)
        self.ui.buttonBox_save_cancel.rejected.connect(self.reject)
        # Wire up groupbox checkbox logic
        self.ui.groupBox_checkBox_enable_checkins.toggled.connect(self.on_enable_checkins_toggled)
        self.on_enable_checkins_toggled(self.ui.groupBox_checkBox_enable_checkins.isChecked())
    
    def on_enable_checkins_toggled(self, checked):
        # Enable/disable all children except the groupbox itself
        for child in self.ui.groupBox_checkBox_enable_checkins.findChildren(QWidget):
            if child is not self.ui.groupBox_checkBox_enable_checkins:
                child.setEnabled(checked)
    
    def load_user_checkin_data(self):
        """Load the user's current check-in settings"""
        if not self.user_id:
            return
        try:
            # Load user preferences
            prefs_result = get_user_data(self.user_id, 'preferences')
            prefs = prefs_result.get('preferences') or {}
            checkin_settings = prefs.get('checkin_settings', {})
            self.checkin_widget.set_checkin_settings(checkin_settings)
        except Exception as e:
            logger.error(f"Error loading check-in data for user {self.user_id}: {e}")
    
    @handle_errors("saving check-in settings")
    def save_checkin_settings(self):
        """Save the check-in settings back to user preferences"""
        if not self.user_id:
            self.accept()
            return
        try:
            checkin_settings = self.checkin_widget.get_checkin_settings()
            
            # Save time periods to schedule management
            time_periods = checkin_settings.get('time_periods', {})
            logger.info(f"Saving check-in time periods for user {self.user_id}: {time_periods}")
            set_schedule_periods(self.user_id, "checkin", time_periods)
            clear_schedule_periods_cache(self.user_id, "checkin")
            
            # Get current preferences and update check-in settings
            prefs_result = get_user_data(self.user_id, 'preferences')
            prefs = prefs_result.get('preferences') or {}
            prefs['checkin_settings'] = {
                'questions': checkin_settings.get('questions', {})
            }
            
            # Save updated preferences
            update_user_preferences(self.user_id, prefs)
            
            # Update user account features
            user_data_result = get_user_data(self.user_id, 'account')
            account = user_data_result.get('account') or {}
            if 'features' not in account:
                account['features'] = {}
            account['features']['checkins'] = 'enabled' if self.ui.groupBox_checkBox_enable_checkins.isChecked() else 'disabled'
            update_user_account(self.user_id, account)
            
            QMessageBox.information(self, "Check-in Settings Saved", 
                                   "Check-in settings saved successfully.")
            self.user_changed.emit()
            self.accept()
            
        except Exception as e:
            logger.error(f"Error saving check-in settings for user {self.user_id}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save check-in settings: {str(e)}")
    
    def get_checkin_settings(self):
        """Get the current check-in settings."""
        return self.checkin_widget.get_checkin_settings()
    
    def set_checkin_settings(self, settings):
        """Set the check-in settings."""
        self.checkin_widget.set_checkin_settings(settings) 