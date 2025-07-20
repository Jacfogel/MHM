from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal
from ui.generated.dynamic_list_field_template_pyqt import Ui_Form_dynamic_list_field_template
from PySide6.QtWidgets import QSizePolicy

class DynamicListField(QWidget):
    """Single row consisting of checkbox + editable text + delete button."""

    value_changed = Signal()
    delete_requested = Signal(QWidget)

    def __init__(self, parent=None, preset_label: str = "", editable: bool = True, checked: bool = False):
        super().__init__(parent)
        self.ui = Ui_Form_dynamic_list_field_template()
        self.ui.setupUi(self)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        # Keep a public flag so containers can query row type
        self.editable: bool = editable

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
    def on_text_changed(self):
        """Called when user types in the text field."""
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

    def on_checkbox_toggled(self):
        """Called when user clicks the checkbox."""
        # Only emit if we're not in the middle of duplicate handling
        from ui.widgets.dynamic_list_container import DynamicListContainer
        if not DynamicListContainer._handling_duplicate:
            self.value_changed.emit()

    def on_editing_finished(self):
        """Notify parent container that text editing has finished (for duplicate validation)."""
        self.value_changed.emit()

    def _on_delete(self):
        self.delete_requested.emit(self)

    # Public helpers ----------------------------------------------------
    def is_checked(self) -> bool:
        return self.ui.checkBox__dynamic_list_field.isChecked()

    def get_text(self) -> str:
        if self.ui.lineEdit_dynamic_list_field.isEnabled():
            return self.ui.lineEdit_dynamic_list_field.text().strip()
        # Preset row – use checkbox label text
        return self.ui.checkBox__dynamic_list_field.text().strip()

    # Helper to identify blank editable row
    def is_blank(self) -> bool:
        return self.editable and self.get_text() == ""

    def set_checked(self, state: bool):
        self.ui.checkBox__dynamic_list_field.setChecked(state)



    def set_text(self, text: str):
        self.ui.lineEdit_dynamic_list_field.setText(text)
        self.on_value_changed() 