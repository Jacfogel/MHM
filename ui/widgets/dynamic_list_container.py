from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout
from PySide6.QtCore import Signal
from ui.widgets.dynamic_list_field import DynamicListField
from core.user_management import get_predefined_options

class DynamicListContainer(QWidget):
    """Manages a vertical list of DynamicListField rows."""

    values_changed = Signal()

    # Guard to prevent recursion while duplicate warning dialog is showing
    _showing_dup_alert = False
    # Flag to skip validation during programmatic changes
    _programmatic_change = False
    # Flag to prevent duplicate handling recursion
    _handling_duplicate = False

    def __init__(self, parent=None, field_key: str = ""):
        super().__init__(parent)
        self.field_key = field_key
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(2)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.rows: list[DynamicListField] = []

        # Allow wheel scrolling even when children have focus
        self.installEventFilter(self)

        # -----------------------------------------------------------------
        # Create two-part layout: grid for presets, vertical list for customs
        # -----------------------------------------------------------------
        self.grid_widget = QWidget(self)
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setHorizontalSpacing(20)
        self.grid_layout.setVerticalSpacing(4)

        self.custom_widget = QWidget(self)
        self.custom_layout = QVBoxLayout(self.custom_widget)
        self.custom_layout.setContentsMargins(0, 0, 0, 0)
        self.custom_layout.setSpacing(2)

        # Outer layout: grid then customs
        self.layout.addWidget(self.grid_widget)
        self.layout.addWidget(self.custom_widget)

        # Add preset checkboxes into grid (non-editable DynamicListField rows)
        presets = get_predefined_options(field_key)
        cols = 2  # default columns
        row_idx = 0
        col_idx = 0
        for option in presets:
            row = DynamicListField(self, preset_label=option, editable=False, checked=False)
            row.value_changed.connect(lambda r=row: self._on_preset_toggled(r))
            self.grid_layout.addWidget(row, row_idx, col_idx)
            self.rows.append(row)

            col_idx += 1
            if col_idx >= cols:
                col_idx = 0
                row_idx += 1

        # Add one blank custom row
        self._add_blank_row()
        


    # ------------------------------------------------------------------
    def _add_blank_row(self):
        blank = DynamicListField(self, preset_label="", editable=True, checked=False)
        blank.value_changed.connect(lambda: self._on_row_edited(blank))
        blank.delete_requested.connect(self._on_row_deleted)
        self.custom_layout.addWidget(blank)
        self.rows.append(blank)

        # Hide its delete button until text entered
        blank.ui.pushButton_delete_DynamicListField.hide()

    def _on_row_edited(self, row: DynamicListField):
        # If this was the last row and now has text, append another blank
        if row is self.rows[-1] and row.get_text():
            self._add_blank_row()

        # Skip warning during programmatic changes
        self._deduplicate_values(trigger_row=row, skip_warning=DynamicListContainer._programmatic_change)
        self._ensure_single_blank_row(current_blank=row if row.is_blank() else None)
        self.values_changed.emit()

    def _on_row_deleted(self, row: DynamicListField):
        if row in self.rows:
            self.rows.remove(row)
            row.setParent(None)
            row.deleteLater()
            # Always ensure at least one blank custom row exists
            self._ensure_single_blank_row()
            self.values_changed.emit()

    # ------------------------------------------------------------------
    def _ensure_single_blank_row(self, current_blank: DynamicListField | None = None):
        blanks = [r for r in self.rows if r.is_blank()]
        if not blanks:
            self._add_blank_row()
            return
        # keep only one blank row (prefer current_blank if provided)
        keep = current_blank or blanks[0]
        for b in blanks:
            if b is not keep:
                self.rows.remove(b)
                b.setParent(None)
                b.deleteLater()

    def _deduplicate_values(self, trigger_row: DynamicListField | None = None, skip_warning: bool = False):
        # Skip if we're already handling duplicates or if this is a programmatic change
        if DynamicListContainer._handling_duplicate or skip_warning:
            return
            
        DynamicListContainer._handling_duplicate = True
        DynamicListContainer._programmatic_change = True
        
        try:
            # Skip if no trigger row provided
            if not trigger_row:
                return
                
            # Find all currently checked rows (excluding the trigger row)
            existing_checked: dict[str, DynamicListField] = {}
            for r in self.rows:
                if r is trigger_row or not r.is_checked():
                    continue
                val = r.get_text().strip().lower()
                if val:
                    existing_checked[val] = r

            # Check if the trigger row's text matches any existing checked item
            # Only do this if the trigger row is actually checked
            if not trigger_row.is_checked():
                return
                
            trigger_text = trigger_row.get_text().strip().lower()
            if trigger_text and trigger_text in existing_checked:
                # Temporarily disconnect the trigger row's signal to prevent recursion
                trigger_row.value_changed.disconnect()
                
                # Uncheck the trigger row (the duplicate that was just checked)
                trigger_row.set_checked(False)
                
                # Show warning once, only when user finishes editing/ toggling duplicate row
                if (
                    not (trigger_row.editable and trigger_row.ui.lineEdit_dynamic_list_field.hasFocus()) and
                    not DynamicListContainer._showing_dup_alert
                ):
                    from PySide6.QtWidgets import QMessageBox
                    DynamicListContainer._showing_dup_alert = True
                    QMessageBox.warning(self, "Duplicate Interest", f"'{trigger_row.get_text()}' is already selected.")
                    DynamicListContainer._showing_dup_alert = False

                # Reconnect the signal
                if trigger_row.editable:
                    trigger_row.value_changed.connect(lambda: self._on_row_edited(trigger_row))
                else:
                    trigger_row.value_changed.connect(lambda: self._on_preset_toggled(trigger_row))
        finally:
            DynamicListContainer._handling_duplicate = False
            DynamicListContainer._programmatic_change = False

    # ------------------------------------------------------------------
    def get_values(self) -> list[str]:
        predefined_options = get_predefined_options(self.field_key)
        preset_vals: list[str] = []
        custom_vals: list[str] = []
        
        # Collect all checked items
        for r in self.rows:
            if not r.is_checked():
                continue
            text = r.get_text()
            if text:
                # If this is a preset item, normalize to titlecase
                # If it's a custom item, keep original case
                if text.lower() in [opt.lower() for opt in predefined_options]:
                    # Find the original preset text to preserve exact titlecase
                    for preset in predefined_options:
                        if preset.lower() == text.lower():
                            preset_vals.append(preset)
                            break
                else:
                    # Custom item - keep original case
                    custom_vals.append(text)
        
        # Return presets in predefined order, followed by custom items
        return preset_vals + custom_vals

    def set_values(self, selected: list[str]):
        # Clear custom rows first (leave presets)
        for r in list(self.rows):
            if r.ui.lineEdit_dynamic_list_field.isEnabled():
                self.rows.remove(r)
                r.setParent(None)
                r.deleteLater()
        # Check presets (case-insensitive matching)
        selected_lower = [s.lower() for s in selected]
        for r in self.rows:
            r.set_checked(r.get_text().lower() in selected_lower)
        # Add custom rows for remaining (case-insensitive matching)
        predefined_options = [opt.lower() for opt in get_predefined_options(self.field_key)]
        remaining = [t for t in selected if t.lower() not in predefined_options]
        for item in remaining:
            row = DynamicListField(self, preset_label=item, editable=True, checked=True)
            row.value_changed.connect(lambda: self._on_row_edited(row))
            row.delete_requested.connect(self._on_row_deleted)
            # Insert before current blank row (last widget)
            insert_pos = max(0, self.custom_layout.count() - 1)
            self.custom_layout.insertWidget(insert_pos, row)
            self.rows.append(row)
        # Ensure trailing blank
        if not self.rows or self.rows[-1].get_text():
            self._add_blank_row()

    def _first_blank_index(self):
        for idx, r in enumerate(self.rows):
            if r.editable and r.get_text() == "":
                return idx
        return len(self.rows)



    # Handle preset toggle to include duplicate validation
    def _on_preset_toggled(self, row: DynamicListField):
        # Skip warning during programmatic changes
        self._deduplicate_values(trigger_row=row, skip_warning=DynamicListContainer._programmatic_change)
        self.values_changed.emit()

    def __post_init__(self):
        self.installEventFilter(self)