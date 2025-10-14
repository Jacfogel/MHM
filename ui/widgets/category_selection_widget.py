from PySide6.QtWidgets import QWidget
from ui.generated.category_selection_widget_pyqt import Ui_Form_category_selection_widget
from core.user_data_validation import _shared__title_case

# Set up logging
from core.logger import get_component_logger
logger = get_component_logger('ui')

CATEGORY_KEYS = [
    'fun_facts',
    'health',
    'motivational',
    'quotes_to_ponder',
    'word_of_the_day',
]

class CategorySelectionWidget(QWidget):
    def __init__(self, parent=None):
        """Initialize the object."""
        super().__init__(parent)
        self.ui = Ui_Form_category_selection_widget()
        self.ui.setupUi(self)
        # Set checkbox labels using title_case
        for key in CATEGORY_KEYS:
            cb = getattr(self.ui, f'checkBox_{key}', None)
            if cb:
                cb.setText(_shared__title_case(key.replace('_', ' ')))

    def get_selected_categories(self):
        try:
            selected = []
            for key in CATEGORY_KEYS:
                cb = getattr(self.ui, f'checkBox_{key}', None)
                if cb and cb.isChecked():
                    selected.append(key)
            logger.debug(f"Selected categories: {selected}")
            return selected
        except Exception as e:
            logger.error(f"Error getting selected categories: {e}")
            return []

    def set_selected_categories(self, categories):
        try:
            # Normalize input to internal keys
            normalized = set()
            for cat in categories:
                norm = cat.lower().replace(' ', '_')
                if norm in CATEGORY_KEYS:
                    normalized.add(norm)
            logger.debug(f"Setting categories to: {normalized}")
            for key in CATEGORY_KEYS:
                cb = getattr(self.ui, f'checkBox_{key}', None)
                if cb:
                    cb.setChecked(key in normalized)
        except Exception as e:
            logger.error(f"Error setting selected categories: {e}") 