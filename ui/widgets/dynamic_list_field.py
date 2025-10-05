from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal
from ui.generated.dynamic_list_field_template_pyqt import Ui_Form_dynamic_list_field_template
from PySide6.QtWidgets import QSizePolicy
from core.logger import get_component_logger
from core.error_handling import handle_errors, DataError

# Route widget logs to UI component
widget_logger = get_component_logger('ui_widgets')
logger = widget_logger

class DynamicListField(QWidget):
    """Single row consisting of checkbox + editable text + delete button."""

    value_changed = Signal()
    delete_requested = Signal(QWidget)

    @handle_errors("initializing dynamic list field")
    def __init__(self, parent=None, preset_label: str = "", editable: bool = True, checked: bool = False):
        """Initialize the object."""
        try:
            super().__init__(parent)
            self.ui = Ui_Form_dynamic_list_field_template()
            self.ui.setupUi(self)
            self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

            # Keep a public flag so containers can query row type
            self.editable: bool = editable
            logger.debug(f"Dynamic list field initialized: editable={editable}, checked={checked}")
        except Exception as e:
            logger.error(f"Error initializing dynamic list field: {e}")
            raise

        # --- Tighten layout spacing ---
        # Remove extra top/bottom gap between rows
        if hasattr(self.ui, 'verticalLayout'):
            self.ui.verticalLayout.setContentsMargins(0, 0, 0, 0)
            self.ui.verticalLayout.setSpacing(0)

        # Reduce side padding inside row
        if hasattr(self.ui, 'horizontalLayout_4'):
            self.ui.horizontalLayout_4.setContentsMargins(0, 0, 4, 0)

        # Configure initial state
        self.ui.checkBox__dynamic_list_field.setChecked(checked)

        if editable:
            # Editable (custom) row – use line edit for text entry, checkbox has no label
            self.ui.lineEdit_dynamic_list_field.setText(preset_label)
            self.ui.lineEdit_dynamic_list_field.setEnabled(True)
            self.ui.checkBox__dynamic_list_field.setText("")
            # Show delete button for custom rows
            self.ui.pushButton_delete_DynamicListField.show()
            # Optional placeholder to cue user
            if not preset_label:
                self.ui.lineEdit_dynamic_list_field.setPlaceholderText("Add custom item…")
        else:
            # Preset (non-editable) row – show label on checkbox, hide the line edit
            self.ui.checkBox__dynamic_list_field.setText(preset_label)
            self.ui.lineEdit_dynamic_list_field.hide()
            self.ui.lineEdit_dynamic_list_field.setEnabled(False)
            # Remove the delete button for preset rows
            self.ui.pushButton_delete_DynamicListField.hide()
            # Make the checkbox occupy remaining space so the label is fully visible
            self.ui.checkBox__dynamic_list_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            # Stretch checkbox across the row
            if hasattr(self.ui, 'horizontalLayout_4'):
                self.ui.horizontalLayout_4.setStretch(0, 1)

        # connections
        self.ui.lineEdit_dynamic_list_field.textEdited.connect(self.on_text_changed)
        self.ui.checkBox__dynamic_list_field.toggled.connect(self.on_checkbox_toggled)
        self.ui.pushButton_delete_DynamicListField.clicked.connect(self._on_delete)

        # When finished editing text, notify container for duplicate validation
        self.ui.lineEdit_dynamic_list_field.editingFinished.connect(self.on_editing_finished)
        


    # ------------------------------------------------------------------
    @handle_errors("handling text change in dynamic list field")
    def on_text_changed(self):
        """Called when user types in the text field."""
        try:
            # Toggle delete button visibility for editable rows
            if self.editable:
                is_blank = self.get_text() == ""
                self.ui.pushButton_delete_DynamicListField.setVisible(not is_blank)

                # Auto-check when user types non-blank text (but not during programmatic changes)
                from ui.widgets.dynamic_list_container import DynamicListContainer
                if not is_blank and not self.is_checked() and not DynamicListContainer._programmatic_change:
                    self.set_checked(True)
            
            # Emit value changed signal
            from ui.widgets.dynamic_list_container import DynamicListContainer
            if not DynamicListContainer._handling_duplicate:
                self.value_changed.emit()
        except Exception as e:
            logger.error(f"Error handling text change in dynamic list field: {e}")
            # Don't re-raise to avoid breaking UI interaction

    @handle_errors("handling checkbox toggle in dynamic list field")
    def on_checkbox_toggled(self):
        """Called when user clicks the checkbox."""
        try:
            # Only emit if we're not in the middle of duplicate handling
            from ui.widgets.dynamic_list_container import DynamicListContainer
            if not DynamicListContainer._handling_duplicate:
                self.value_changed.emit()
        except Exception as e:
            logger.error(f"Error handling checkbox toggle in dynamic list field: {e}")
            # Don't re-raise to avoid breaking UI interaction

    @handle_errors("handling editing finished in dynamic list field")
    def on_editing_finished(self):
        """Notify parent container that text editing has finished (for duplicate validation)."""
        try:
            self.value_changed.emit()
        except Exception as e:
            logger.error(f"Error handling editing finished in dynamic list field: {e}")
            # Don't re-raise to avoid breaking UI interaction

    @handle_errors("handling delete request in dynamic list field")
    def _on_delete(self):
        try:
            self.delete_requested.emit(self)
        except Exception as e:
            logger.error(f"Error handling delete request in dynamic list field: {e}")
            # Don't re-raise to avoid breaking UI interaction

    # Public helpers ----------------------------------------------------
    @handle_errors("checking if dynamic list field is checked", default_return=False)
    def is_checked(self) -> bool:
        try:
            return self.ui.checkBox__dynamic_list_field.isChecked()
        except Exception as e:
            logger.error(f"Error checking if dynamic list field is checked: {e}")
            return False

    @handle_errors("getting text from dynamic list field", default_return="")
    def get_text(self) -> str:
        try:
            if self.ui.lineEdit_dynamic_list_field.isEnabled():
                return self.ui.lineEdit_dynamic_list_field.text().strip()
            # Preset row – use checkbox label text
            return self.ui.checkBox__dynamic_list_field.text().strip()
        except Exception as e:
            logger.error(f"Error getting text from dynamic list field: {e}")
            return ""

    # Helper to identify blank editable row
    @handle_errors("checking if dynamic list field is blank", default_return=True)
    def is_blank(self) -> bool:
        try:
            return self.editable and self.get_text() == ""
        except Exception as e:
            logger.error(f"Error checking if dynamic list field is blank: {e}")
            return True

    @handle_errors("setting checked state of dynamic list field")
    def set_checked(self, state: bool):
        try:
            self.ui.checkBox__dynamic_list_field.setChecked(state)
        except Exception as e:
            logger.error(f"Error setting checked state of dynamic list field: {e}")
            # Don't re-raise to avoid breaking UI interaction

    @handle_errors("setting text in dynamic list field")
    def set_text(self, text: str):
        try:
            if not isinstance(text, str):
                logger.warning(f"Text must be string, got {type(text)}")
                text = str(text) if text is not None else ""
            
            self.ui.lineEdit_dynamic_list_field.setText(text)
            self.value_changed.emit()
        except Exception as e:
            logger.error(f"Error setting text in dynamic list field: {e}")
            # Don't re-raise to avoid breaking UI interaction 