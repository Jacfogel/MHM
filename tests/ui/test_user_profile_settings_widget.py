# pyright: reportAttributeAccessIssue=false
"""Behavior tests for UserProfileSettingsWidget load/save helpers.

lineEdit_preferred_name is created in UserProfileSettingsWidget.__init__, not
in the generated Ui_Form_user_profile_settings class, so attribute-access
checks need the same suppression the widget file already uses.
"""

from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()

from unittest.mock import patch

import pytest
from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QApplication

from ui.widgets.user_profile_settings_widget import UserProfileSettingsWidget

pytestmark = [pytest.mark.ui]


@pytest.fixture(scope="module")
def qapp():
    """Provide a process-wide QApplication for widget tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _small_options(_field_key=""):
    return ["reading", "music"]


def _make_widget(existing_data=None):
    with patch(
        "ui.widgets.dynamic_list_container.get_predefined_options",
        side_effect=_small_options,
    ):
        return UserProfileSettingsWidget(existing_data=existing_data or {})


def test_load_existing_data_fills_profile_fields(qapp):
    existing = {
        "preferred_name": "Ada",
        "gender_identity": ["Woman", "Agender"],
        "date_of_birth": "1990-05-01",
        "notes_for_ai": ["Keep reminders short."],
        "loved_ones": [
            {"name": "Sam", "type": "friend", "relationships": ["support"]},
            "plain name",
        ],
        "interests": ["reading"],
        "goals": ["sleep more"],
        "custom_fields": {
            "health_conditions": ["anxiety"],
            "medications_treatments": ["meds"],
            "allergies_sensitivities": ["pollen"],
        },
    }
    widget = _make_widget(existing)
    assert widget.ui.lineEdit_preferred_name.text() == "Ada"
    assert widget.ui.checkBox_woman.isChecked()
    assert "Agender" in widget.ui.lineEdit_custom_gender.text()
    assert widget.ui.textEdit_notes.toPlainText() == "Keep reminders short."
    loved = widget.ui.textEdit_loved_ones.toPlainText()
    assert "Sam" in loved
    assert "plain name" in loved
    widget.deleteLater()


def test_get_personalization_data_round_trip(qapp):
    widget = _make_widget({"preferred_name": "Old"})
    widget.ui.lineEdit_preferred_name.setText("Julie")
    widget.ui.checkBox_nonbinary.setChecked(True)
    widget.ui.lineEdit_custom_gender.setText("Agender,  ")
    widget.ui.textEdit_notes.setPlainText("Be gentle.")
    widget.ui.textEdit_loved_ones.setPlainText("Alex - family - sibling, friend")
    widget.ui.calendarWidget_date_of_birth.setSelectedDate(QDate(1991, 2, 3))

    data = widget.get_personalization_data()
    assert data["preferred_name"] == "Julie"
    assert "Non-binary" in data["gender_identity"]
    assert "Agender" in data["gender_identity"]
    assert data["notes_for_ai"] == ["Be gentle."]
    assert data["loved_ones"][0]["name"] == "Alex"
    assert data["loved_ones"][0]["type"] == "family"
    assert "sibling" in data["loved_ones"][0]["relationships"]
    assert data["date_of_birth"] == QDate(1991, 2, 3).toString(Qt.DateFormat.ISODate)
    assert "timezone" in data
    widget.deleteLater()


def test_set_settings_reloads_existing_data(qapp):
    widget = _make_widget()
    widget.set_settings({"preferred_name": "Reloaded", "notes_for_ai": []})
    assert widget.ui.lineEdit_preferred_name.text() == "Reloaded"
    assert widget.ui.textEdit_notes.toPlainText() == ""
    widget.deleteLater()


def test_set_checkbox_group_checks_matching_values(qapp):
    widget = _make_widget()
    widget.set_checkbox_group("health_conditions", ["anxiety", "adhd"])
    assert widget.ui.checkBox_anxiety.isChecked()
    assert widget.ui.checkBox_adhd.isChecked()
    assert widget.ui.checkBox_depression.isChecked() is False
    widget.set_checkbox_group("unknown_group", ["x"])
    widget.deleteLater()


def test_date_of_birth_clears_when_left_at_today(qapp):
    widget = _make_widget()
    widget.ui.calendarWidget_date_of_birth.setSelectedDate(QDate.currentDate())
    data = widget.get_personalization_data()
    assert data.get("date_of_birth", "") == ""
    widget.deleteLater()
