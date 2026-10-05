"""Desktop controls for editing account-owned task templates."""

from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

from PySide6.QtCore import Qt, QTime
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from core.error_handling import ValidationError, handle_errors
from tasks.task_templates import (
    MAX_CUSTOM_TASK_TEMPLATES,
    normalize_custom_task_templates,
)


class TaskTemplateEditDialog(QDialog):
    """Collect and validate one custom task-template definition."""

    # ERROR_HANDLING_EXCLUDE: Qt constructor wires fields only; public reads are decorated.
    def __init__(
        self,
        parent: QWidget | None,
        template_id: str,
        record: dict | None = None,
    ) -> None:
        """Build the template editor for a new or existing record."""
        super().__init__(parent)
        self.template_id = template_id
        record = record or {}
        self.setWindowTitle("Edit Task Template" if record else "Add Task Template")

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_edit = QLineEdit(str(record.get("display_name") or ""))
        self.title_edit = QLineEdit(str(record.get("title") or ""))
        self.description_edit = QTextEdit()
        self.description_edit.setPlainText(str(record.get("description") or ""))
        self.description_edit.setMaximumHeight(90)
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High", "Urgent", "Critical"])
        self.priority_combo.setCurrentText(
            str(record.get("priority") or "medium").capitalize()
        )
        self.tags_edit = QLineEdit(", ".join(record.get("tags") or []))
        self.tags_edit.setPlaceholderText("routine, home")

        self.no_time_check = QCheckBox("No default time")
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        due_time = record.get("default_due_time")
        if isinstance(due_time, str) and due_time:
            parsed_time = QTime.fromString(due_time, "HH:mm")
            if parsed_time.isValid():
                self.time_edit.setTime(parsed_time)
        else:
            self.no_time_check.setChecked(True)
        self.time_edit.setEnabled(not self.no_time_check.isChecked())
        self.no_time_check.toggled.connect(
            lambda checked: self.time_edit.setEnabled(not checked)
        )
        time_row = QWidget()
        time_layout = QHBoxLayout(time_row)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.addWidget(self.time_edit)
        time_layout.addWidget(self.no_time_check)

        self.recurrence_combo = QComboBox()
        self.recurrence_combo.addItem("None", None)
        for value in ("daily", "weekly", "monthly", "yearly"):
            self.recurrence_combo.addItem(value.capitalize(), value)
        recurrence = record.get("recurrence_pattern")
        recurrence_index = self.recurrence_combo.findData(recurrence)
        self.recurrence_combo.setCurrentIndex(max(0, recurrence_index))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 365)
        self.interval_spin.setValue(int(record.get("recurrence_interval") or 1))

        form.addRow("Template name:", self.name_edit)
        form.addRow("Task title:", self.title_edit)
        form.addRow("Details:", self.description_edit)
        form.addRow("Priority:", self.priority_combo)
        form.addRow("Tags:", self.tags_edit)
        form.addRow("Default time:", time_row)
        form.addRow("Repeats:", self.recurrence_combo)
        form.addRow("Repeat interval:", self.interval_spin)
        layout.addLayout(form)

        hint = QLabel(
            "The template will also appear on the website and in task template commands."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @handle_errors("reading desktop task template record", re_raise=True)
    def template_record(self) -> dict:
        """Return the normalized template record represented by the form."""
        tags = [tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip()]
        candidate = {
            self.template_id: {
                "display_name": self.name_edit.text().strip(),
                "title": self.title_edit.text().strip(),
                "description": self.description_edit.toPlainText().strip(),
                "priority": self.priority_combo.currentText().casefold(),
                "tags": tags,
                "default_due_time": (
                    None
                    if self.no_time_check.isChecked()
                    else self.time_edit.time().toString("HH:mm")
                ),
                "recurrence_pattern": self.recurrence_combo.currentData(),
                "recurrence_interval": self.interval_spin.value(),
            }
        }
        return normalize_custom_task_templates(candidate, strict=True)[
            self.template_id
        ]

    @handle_errors("validating desktop task template", default_return=None)
    def _validate_and_accept(self) -> None:
        """Accept the dialog only when its template definition is valid."""
        try:
            self.template_record()
        except ValidationError as exc:
            QMessageBox.warning(self, "Check Template", str(exc))
            return
        self.accept()


class TaskTemplateManagerWidget(QGroupBox):
    """Manage the account-owned task templates stored in task settings."""

    # ERROR_HANDLING_EXCLUDE: Qt constructor wires child controls only.
    def __init__(self, parent: QWidget | None = None) -> None:
        """Build the compact task-template manager."""
        super().__init__("Saved Task Templates", parent)
        self._templates: dict[str, dict] = {}
        layout = QVBoxLayout(self)
        hint = QLabel(
            "Templates saved here are shared with the website and task template commands."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Name", "Task title", "Priority"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setMaximumHeight(170)
        self.table.doubleClicked.connect(self.edit_selected_template)
        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        self.add_button = QPushButton("Add Template")
        self.edit_button = QPushButton("Edit Selected")
        self.delete_button = QPushButton("Delete Selected")
        self.add_button.clicked.connect(self.add_template)
        self.edit_button.clicked.connect(self.edit_selected_template)
        self.delete_button.clicked.connect(self.delete_selected_template)
        buttons.addWidget(self.add_button)
        buttons.addWidget(self.edit_button)
        buttons.addWidget(self.delete_button)
        buttons.addStretch()
        layout.addLayout(buttons)

    @handle_errors("setting desktop custom task templates", default_return=None)
    def set_templates(self, value: object) -> None:
        """Replace the editor contents with normalized saved templates."""
        self._templates = normalize_custom_task_templates(value)
        self._refresh_table()

    @handle_errors("reading desktop custom task templates", re_raise=True)
    def templates(self) -> dict[str, dict]:
        """Return a validated copy of the templates currently in the editor."""
        return deepcopy(normalize_custom_task_templates(self._templates, strict=True))

    @handle_errors("refreshing desktop task template table", default_return=None)
    def _refresh_table(self) -> None:
        """Render the current template definitions in the summary table."""
        self.table.setRowCount(0)
        for template_id, record in self._templates.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            name_item = QTableWidgetItem(record["display_name"])
            name_item.setData(Qt.ItemDataRole.UserRole, template_id)
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, QTableWidgetItem(record["title"]))
            self.table.setItem(row, 2, QTableWidgetItem(record["priority"].capitalize()))
        self.table.resizeColumnsToContents()

    @handle_errors("reading selected desktop task template id", default_return=None)
    def _selected_template_id(self) -> str | None:
        """Return the selected custom template ID, if any."""
        row = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
        value = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        return value if isinstance(value, str) else None

    @handle_errors("adding desktop task template", default_return=None)
    def add_template(self) -> None:
        """Open the editor and append one valid custom template."""
        if len(self._templates) >= MAX_CUSTOM_TASK_TEMPLATES:
            QMessageBox.warning(
                self,
                "Template Limit",
                f"You can save up to {MAX_CUSTOM_TASK_TEMPLATES} task templates.",
            )
            return
        template_id = f"custom_{uuid4().hex[:12]}"
        dialog = TaskTemplateEditDialog(self, template_id)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        candidate = deepcopy(self._templates)
        candidate[template_id] = dialog.template_record()
        try:
            self._templates = normalize_custom_task_templates(candidate, strict=True)
        except ValidationError as exc:
            QMessageBox.warning(self, "Check Template", str(exc))
            return
        self._refresh_table()

    @handle_errors("editing desktop task template", default_return=None)
    def edit_selected_template(self, *_args) -> None:
        """Edit the selected custom template without changing its ID."""
        template_id = self._selected_template_id()
        if not template_id:
            QMessageBox.information(self, "Select Template", "Select a template to edit.")
            return
        dialog = TaskTemplateEditDialog(
            self, template_id, deepcopy(self._templates[template_id])
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        candidate = deepcopy(self._templates)
        candidate[template_id] = dialog.template_record()
        try:
            self._templates = normalize_custom_task_templates(candidate, strict=True)
        except ValidationError as exc:
            QMessageBox.warning(self, "Check Template", str(exc))
            return
        self._refresh_table()

    @handle_errors("deleting desktop task template", default_return=None)
    def delete_selected_template(self) -> None:
        """Remove the selected custom template after confirmation."""
        template_id = self._selected_template_id()
        if not template_id:
            QMessageBox.information(
                self, "Select Template", "Select a template to delete."
            )
            return
        name = self._templates[template_id]["display_name"]
        result = QMessageBox.question(
            self,
            "Delete Template",
            f"Delete the task template '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if result != QMessageBox.StandardButton.Yes:
            return
        del self._templates[template_id]
        self._refresh_table()
