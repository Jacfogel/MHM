from PySide6.QtWidgets import QWidget, QCheckBox
from ui.generated.category_selection_widget_pyqt import Ui_Form_category_selection_widget
from core.user_data_validation import title_case

CATEGORY_KEYS = [
    'fun_facts',
    'health',
    'motivational',
    'quotes_to_ponder',
    'word_of_the_day',
]

class CategorySelectionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Form_category_selection_widget()
        self.ui.setupUi(self)
        # Set checkbox labels using title_case
        for key in CATEGORY_KEYS:
            cb = getattr(self.ui, f'checkBox_{key}', None)
            if cb:
                cb.setText(title_case(key.replace('_', ' ')))

    def get_selected_categories(self):
        selected = []
        for key in CATEGORY_KEYS:
            cb = getattr(self.ui, f'checkBox_{key}', None)
            if cb and cb.isChecked():
                selected.append(key)
        return selected

    def set_selected_categories(self, categories):
        # Normalize input to internal keys
        normalized = set()
        for cat in categories:
            norm = cat.lower().replace(' ', '_')
            if norm in CATEGORY_KEYS:
                normalized.add(norm)
        for key in CATEGORY_KEYS:
            cb = getattr(self.ui, f'checkBox_{key}', None)
            if cb:
                cb.setChecked(key in normalized) 