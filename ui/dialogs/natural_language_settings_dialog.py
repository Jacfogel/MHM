# ui/dialogs/natural_language_settings_dialog.py
# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false

"""Dialog for per-user natural-language phrase settings."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QVBoxLayout

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.natural_language_defaults import (
    get_natural_language_defaults,
    save_natural_language_defaults_preferences,
)
from ui.widgets.natural_language_settings_widget import NaturalLanguageSettingsWidget

logger = get_component_logger("ui")


class NaturalLanguageSettingsDialog(QDialog):
    """Edit preferences.natural_language_defaults for one user."""

    user_changed = Signal()

    @handle_errors("initializing natural language settings dialog", default_return=None)
    def __init__(self, parent=None, user_id: str | None = None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Phrase Settings")
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        self.settings_widget = NaturalLanguageSettingsWidget(self, user_id=user_id)
        layout.addWidget(self.settings_widget)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.save_settings)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.load_settings()

    @handle_errors("loading phrase settings", default_return=None)
    def load_settings(self) -> None:
        if not self.user_id:
            self.settings_widget.set_defaults(get_natural_language_defaults(None))
            return
        defaults = get_natural_language_defaults(self.user_id)
        self.settings_widget.set_defaults(defaults)

    @handle_errors("saving phrase settings", default_return=None)
    def save_settings(self) -> None:
        if not self.user_id:
            QMessageBox.warning(self, "No User", "Select a user before saving phrase settings.")
            return

        error = self.settings_widget.validate_fields()
        if error:
            QMessageBox.warning(self, "Invalid Input", error)
            return

        payload = self.settings_widget.get_preferences_dict()
        if not save_natural_language_defaults_preferences(self.user_id, payload):
            QMessageBox.critical(
                self,
                "Save Failed",
                "Could not save phrase settings. Please try again.",
            )
            return

        self.user_changed.emit()
        self.accept()
