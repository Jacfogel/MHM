from PySide6.QtWidgets import QDialog, QMessageBox
from ui.generated.category_management_dialog_pyqt import Ui_Dialog_category_management as Ui_Dialog
from ui.widgets.category_selection_widget import CategorySelectionWidget
from PySide6.QtCore import Signal
from core.logger import get_logger
from core.user_management import update_user_preferences, get_user_data
from core.error_handling import handle_errors

logger = get_logger(__name__)

class CategoryManagementDialog(QDialog):
    user_changed = Signal()
    def __init__(self, parent=None, user_id=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Category Settings")
        self.ui = Ui_Dialog()
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
        # Connect Save/Cancel
        self.ui.buttonBox_save_cancel.accepted.connect(self.save_category_settings)
        self.ui.buttonBox_save_cancel.rejected.connect(self.reject)
        # Load user's current categories
        self.load_user_category_data()

    def load_user_category_data(self):
        """Load user's current category settings"""
        try:
            # Load user preferences
            prefs_result = get_user_data(self.user_id, 'preferences')
            prefs = prefs_result.get('preferences') or {}
            current_categories = prefs.get('categories', [])
            self.category_widget.set_selected_categories(current_categories)
        except Exception as e:
            logger.error(f"Error loading user category data: {e}")
            # Set default categories if loading fails
            self.category_widget.set_selected_categories([])

    def save_category_settings(self):
        """Save the selected categories back to user preferences"""
        if not self.user_id:
            self.accept()
            return
        try:
            selected_categories = self.category_widget.get_selected_categories()
            
            # Validate that at least one category is selected
            if not selected_categories:
                QMessageBox.warning(self, "No Categories Selected", 
                                   "Please select at least one category.")
                return
            
            # Get current preferences and update categories
            prefs_result = get_user_data(self.user_id, 'preferences')
            prefs = prefs_result.get('preferences') or {}
            prefs['categories'] = selected_categories
            
            # Save updated preferences
            update_user_preferences(self.user_id, prefs)
            
            QMessageBox.information(self, "Categories Saved", 
                                   f"Successfully saved {len(selected_categories)} categories.")
            self.user_changed.emit()
            self.accept()
            
        except Exception as e:
            logger.error(f"Error saving category settings for user {self.user_id}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save categories: {str(e)}")

    def get_selected_categories(self):
        return self.category_widget.get_selected_categories()

    def set_selected_categories(self, categories):
        self.category_widget.set_selected_categories(categories) 