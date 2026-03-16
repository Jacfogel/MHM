# dialog_helpers.py

"""Shared helpers for dialog behavior (e.g. key handling)."""

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QMessageBox

from core.error_handling import handle_errors


@handle_errors("handling dialog key events", default_return=False)
def handle_dialog_escape_enter_keys(
    dialog: Any,
    event: QKeyEvent,
    *,
    cancel_title: str,
    on_escape_confirm: Callable[[], None],
) -> bool:
    """Handle Escape (confirm then close) and Enter (ignore) for a dialog.

    Use from keyPressEvent: if this returns True, the event was handled;
    otherwise call super().keyPressEvent(event).

    Args:
        dialog: The dialog widget (used as parent for QMessageBox).
        event: The key event.
        cancel_title: Title for the Escape confirmation (e.g. "Cancel Account Creation").
        on_escape_confirm: Callable with no args, invoked when user confirms cancel (e.g. self.reject).

    Returns:
        True if the event was handled; False if the dialog should chain to super().
    """
    if event.key() == Qt.Key.Key_Escape:
        reply = QMessageBox.question(
            dialog,
            cancel_title,
            "Are you sure you want to cancel? All unsaved changes will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            on_escape_confirm()
        event.accept()
        return True
    if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
        event.ignore()
        return True
    return False
