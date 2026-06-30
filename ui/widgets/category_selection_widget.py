# category_selection_widget.py
# pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]

"""Category Selection Widget"""

from PySide6.QtWidgets import QCheckBox, QWidget
from ui.generated.category_selection_widget_pyqt import (
    Ui_Form_category_selection_widget,
)
from storage.user_data_validation import _shared__title_case
from core.error_handling import handle_errors
from messages.message_data_manager import (
    get_message_categories,
    is_ai_generated_message_category,
)

# Set up logging
from core.logger import get_component_logger

logger = get_component_logger("ui")


@handle_errors("building category display label", default_return="")
def _category_display_label(category_key: str) -> str:
    label = _shared__title_case(category_key.replace("_", " "))
    if is_ai_generated_message_category(category_key):
        return f"{label} (AI-generated)"
    return label


class CategorySelectionWidget(QWidget):
    # ERROR_HANDLING_EXCLUDE: Simple constructor that only sets up UI
    def __init__(self, parent=None):
        """Initialize the object."""
        super().__init__(parent)
        self.ui = Ui_Form_category_selection_widget()
        self.ui.setupUi(self)
        self._category_checkboxes: dict[str, QCheckBox] = {}
        self._build_category_checkboxes()

    @handle_errors("building category checkboxes", default_return=None)
    def _build_category_checkboxes(self) -> None:
        """Build checkboxes from CATEGORIES env (via get_message_categories)."""
        while self.ui.gridLayout_2.count():
            item = self.ui.gridLayout_2.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        self._category_checkboxes.clear()
        categories = sorted(get_message_categories())
        for row, key in enumerate(categories):
            cb = QCheckBox(_category_display_label(key), self)
            cb.setObjectName(f"checkBox_{key}")
            self.ui.gridLayout_2.addWidget(cb, row, 0)
            self._category_checkboxes[key] = cb

        if not categories:
            logger.warning(
                "No message categories configured (check CATEGORIES in .env)"
            )

    @handle_errors("getting selected categories", default_return=[])
    def get_selected_categories(self):
        selected = []
        for key, cb in self._category_checkboxes.items():
            if cb.isChecked():
                selected.append(key)
        logger.debug(f"Selected categories: {selected}")
        return selected

    @handle_errors("setting selected categories", default_return=None)
    def set_selected_categories(self, categories):
        normalized = set()
        for cat in categories:
            norm = cat.lower().replace(" ", "_")
            if norm in self._category_checkboxes:
                normalized.add(norm)
            else:
                logger.debug(f"Ignoring unknown category not in CATEGORIES: {cat}")
        logger.debug(f"Setting categories to: {normalized}")
        for key, cb in self._category_checkboxes.items():
            cb.setChecked(key in normalized)
