"""Unit tests for ui.dialogs.dialog_helpers (no full dialog fixtures)."""

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from ui.dialogs.dialog_helpers import handle_dialog_escape_enter_keys


@pytest.mark.unit
@pytest.mark.ui
class TestHandleDialogEscapeEnterKeys:
    def test_escape_confirmed_calls_callback_and_accepts(self, monkeypatch):
        confirmed: list[bool] = []

        def on_escape():
            confirmed.append(True)

        monkeypatch.setattr(
            "ui.dialogs.dialog_helpers.QMessageBox.question",
            lambda *a, **k: QMessageBox.StandardButton.Yes,
        )

        event = MagicMock()
        event.key.return_value = Qt.Key.Key_Escape

        assert (
            handle_dialog_escape_enter_keys(
                MagicMock(),
                event,
                cancel_title="Test",
                on_escape_confirm=on_escape,
            )
            is True
        )
        assert confirmed == [True]
        event.accept.assert_called_once()

    def test_escape_declined_does_not_call_callback(self, monkeypatch):
        confirmed: list[bool] = []

        monkeypatch.setattr(
            "ui.dialogs.dialog_helpers.QMessageBox.question",
            lambda *a, **k: QMessageBox.StandardButton.No,
        )

        event = MagicMock()
        event.key.return_value = Qt.Key.Key_Escape

        assert (
            handle_dialog_escape_enter_keys(
                MagicMock(),
                event,
                cancel_title="Test",
                on_escape_confirm=lambda: confirmed.append(True),
            )
            is True
        )
        assert confirmed == []
        event.accept.assert_called_once()

    def test_return_key_ignores_event(self):
        event = MagicMock()
        event.key.return_value = Qt.Key.Key_Return

        assert (
            handle_dialog_escape_enter_keys(
                MagicMock(),
                event,
                cancel_title="Test",
                on_escape_confirm=lambda: None,
            )
            is True
        )
        event.ignore.assert_called_once()
        event.accept.assert_not_called()

    def test_other_key_not_handled(self):
        event = MagicMock()
        event.key.return_value = Qt.Key.Key_Space

        assert (
            handle_dialog_escape_enter_keys(
                MagicMock(),
                event,
                cancel_title="Test",
                on_escape_confirm=lambda: None,
            )
            is False
        )
        event.ignore.assert_not_called()
        event.accept.assert_not_called()
