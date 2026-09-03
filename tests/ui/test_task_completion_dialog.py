"""Behavior tests for TaskCompletionDialog date/time/notes helpers."""

from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()

from unittest.mock import patch

import pytest
from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import QApplication

from ui.dialogs.task_completion_dialog import TaskCompletionDialog

pytestmark = [pytest.mark.ui]


@pytest.fixture(scope="module")
def qapp():
    """Provide a process-wide QApplication for dialog tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_header_includes_task_title(qapp):
    dialog = TaskCompletionDialog(task_title="Water the plants")
    assert "Water the plants" in dialog.ui.label_task_completion_header.text()
    dialog.deleteLater()


def test_empty_title_still_initializes(qapp):
    dialog = TaskCompletionDialog(task_title="")
    assert dialog.task_title == ""
    assert dialog.get_completion_date()
    dialog.deleteLater()


def test_get_completion_notes(qapp):
    dialog = TaskCompletionDialog(task_title="Task")
    dialog.ui.textEdit_completion_notes.setPlainText("  done for today  ")
    assert dialog.get_completion_notes() == "done for today"
    dialog.deleteLater()


def test_get_completion_time_converts_am_pm(qapp):
    dialog = TaskCompletionDialog(task_title="Task")
    dialog.ui.comboBox_completion_hour.setCurrentText("03")
    dialog.ui.comboBox_completion_minute.setCurrentText("15")
    dialog.ui.radioButton_completion_pm.setChecked(True)
    assert dialog.get_completion_time() == "15:15"

    dialog.ui.comboBox_completion_hour.setCurrentText("12")
    dialog.ui.radioButton_completion_am.setChecked(True)
    assert dialog.get_completion_time() == "00:15"

    dialog.ui.comboBox_completion_hour.setCurrentText("12")
    dialog.ui.radioButton_completion_pm.setChecked(True)
    assert dialog.get_completion_time() == "12:15"
    dialog.deleteLater()


def test_get_completion_time_defaults_when_empty(qapp):
    dialog = TaskCompletionDialog(task_title="Task")
    dialog.ui.comboBox_completion_hour.clear()
    dialog.ui.comboBox_completion_minute.clear()
    assert dialog.get_completion_time() == "00:00"
    dialog.deleteLater()


def test_get_completion_date_empty_when_invalid(qapp):
    dialog = TaskCompletionDialog(task_title="Task")
    invalid = QDate()
    with patch.object(dialog.ui.dateEdit_completion_date, "date", return_value=invalid):
        assert dialog.get_completion_date() == ""
    dialog.deleteLater()


def test_setup_uses_current_afternoon_time(qapp):
    afternoon = QTime(15, 22)
    with patch("ui.dialogs.task_completion_dialog.QTime.currentTime", return_value=afternoon):
        dialog = TaskCompletionDialog(task_title="Task")
    assert dialog.ui.radioButton_completion_pm.isChecked()
    assert dialog.ui.comboBox_completion_hour.currentText() == "03"
    assert dialog.ui.comboBox_completion_minute.currentText() in {"15", "30"}
    dialog.deleteLater()


def test_get_completion_data_combines_fields(qapp):
    dialog = TaskCompletionDialog(task_title="Task")
    dialog.ui.dateEdit_completion_date.setDate(QDate(2026, 9, 2))
    dialog.ui.comboBox_completion_hour.setCurrentText("09")
    dialog.ui.comboBox_completion_minute.setCurrentText("00")
    dialog.ui.radioButton_completion_am.setChecked(True)
    dialog.ui.textEdit_completion_notes.setPlainText("all done")
    data = dialog.get_completion_data()
    assert data["completion_date"] == "2026-09-02"
    assert data["completion_time"] == "09:00"
    assert data["completion_notes"] == "all done"
    dialog.deleteLater()
