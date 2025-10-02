from PySide6.QtWidgets import QDialog, QMessageBox
from ui.generated.category_management_dialog_pyqt import Ui_Dialog_category_management
from ui.widgets.category_selection_widget import CategorySelectionWidget
from PySide6.QtCore import Signal
from core.logger import get_logger, get_component_logger
from core.user_data_handlers import update_user_preferences, update_user_account
from core.user_data_handlers import get_user_data
from core.error_handling import handle_errors
from core.schedule_management import clear_schedule_periods_cache

logger = get_component_logger('ui')
dialog_logger = logger

class CategoryManagementDialog(QDialog):
    user_changed = Signal()
    def __init__(self, parent=None, user_id=None):
        """Initialize the object."""
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Category Settings")
        self.ui = Ui_Dialog_category_management()
        self.ui.setupUi(self)
        # Add the category widget to the group box layout
        self.category_widget = CategorySelectionWidget(self)
        layout = self.ui.groupBox_select_categories.layout()
        # Remove any existing widgets
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        layout.addWidget(self.category_widget)
        
        # Connect checkbox to enable/disable category selection
        self.ui.groupBox_enable_automated_messages.toggled.connect(self.on_enable_messages_toggled)
        
        # Connect Save/Cancel
        self.ui.buttonBox_save_cancel.accepted.connect(self.save_category_settings)
        self.ui.buttonBox_save_cancel.rejected.connect(self.reject)
        # Load user's current categories
        self.load_user_category_data()

    @handle_errors("loading user category data", default_return=None)
    def load_user_category_data(self):
        """Load user's current category settings"""
        try:
            # Load user account to check if automated messages are enabled
            user_data_result = get_user_data(self.user_id, 'account')
            account = user_data_result.get('account') or {}
            features = account.get('features', {})
            messages_enabled = features.get('automated_messages') == 'enabled'
            
            # Set groupbox checkbox state
            self.ui.groupBox_enable_automated_messages.setChecked(messages_enabled)
            
            # Load user preferences
            prefs_result = get_user_data(self.user_id, 'preferences')
            prefs = prefs_result.get('preferences') or {}
            current_categories = prefs.get('categories', [])
            self.category_widget.set_selected_categories(current_categories)
            
            # Enable/disable category selection based on checkbox
            self.on_enable_messages_toggled(messages_enabled)
        except Exception as e:
            logger.error(f"Error loading user category data: {e}")
            # Set default categories if loading fails
            self.category_widget.set_selected_categories([])
            self.ui.groupBox_enable_automated_messages.setChecked(True)
            self.on_enable_messages_toggled(True)

    def on_enable_messages_toggled(self, checked):
        """Handle enable automated messages checkbox toggle."""
        # Enable/disable the category selection group box
        self.ui.groupBox_select_categories.setEnabled(checked)

    @handle_errors("saving category settings", default_return=False)
    def save_category_settings(self):
        """Save the selected categories back to user preferences"""
        if not self.user_id:
            self.accept()
            return
        try:
            messages_enabled = self.ui.groupBox_enable_automated_messages.isChecked()
            
            # Get selected categories from widget (should work regardless of groupbox state)
            selected_categories = self.category_widget.get_selected_categories()
            logger.debug(f"Category dialog: Got categories from widget: {selected_categories}")
            
            # Validate that at least one category is selected if messages are enabled
            if messages_enabled and not selected_categories:
                QMessageBox.warning(self, "No Categories Selected", 
                                   "Please select at least one category when automated messages are enabled.")
                return
            
            # Validate that user has at least one feature enabled
            if not messages_enabled:
                # Check if user has other features enabled
                account_result = get_user_data(self.user_id, 'account')
                account = account_result.get('account') or {}
                features = account.get('features', {})
                other_features = [k for k, v in features.items() if k != 'automated_messages' and v == 'enabled']
                
                if not other_features:
                    QMessageBox.warning(self, "No Features Enabled", 
                                       "You must have at least one feature enabled. Please enable tasks, check-ins, or automated messages.")
                    return
            
            # Get current preferences and update categories
            prefs_result = get_user_data(self.user_id, 'preferences')
            prefs = prefs_result.get('preferences') or {}
            # Always save the selected categories, regardless of whether messages are enabled
            prefs['categories'] = selected_categories
            
            # Save updated preferences
            update_user_preferences(self.user_id, prefs)
            
            # Update account features (preserve existing account data)
            user_data_result = get_user_data(self.user_id, 'account')
            account = user_data_result.get('account') or {}
            features = account.get('features', {})
            features['automated_messages'] = 'enabled' if messages_enabled else 'disabled'
            account['features'] = features
            update_user_account(self.user_id, account)
            logger.debug(f"Category dialog: Updated account features - automated_messages: {features['automated_messages']}")
            
            # Clear schedule cache for categories if messages are disabled
            if not messages_enabled:
                # Clear cache for all categories to ensure schedules are updated
                clear_schedule_periods_cache(self.user_id)
                logger.info(f"Cleared schedule cache for user {self.user_id} after disabling automated messages")
            
            status_text = "enabled" if messages_enabled else "disabled"
            category_text = f" with {len(selected_categories)} categories" if selected_categories else ""
            QMessageBox.information(self, "Settings Saved", 
                                   f"Automated messages {status_text}{category_text}.")
            self.user_changed.emit()
            self.accept()
            
        except Exception as e:
            logger.error(f"Error saving category settings for user {self.user_id}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save categories: {str(e)}")

    def get_selected_categories(self):
        return self.category_widget.get_selected_categories()

    def set_selected_categories(self, categories):
        self.category_widget.set_selected_categories(categories) 