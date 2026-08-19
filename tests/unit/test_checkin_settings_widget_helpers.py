"""Unit tests for check-in settings helpers that do not need the full dialog."""

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="QtWidgets unavailable due to missing GUI system libraries",
)

from PySide6.QtWidgets import QApplication, QComboBox

from ui.widgets.checkin_settings_widget import CheckinSettingsWidget


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.mark.unit
@pytest.mark.checkins
class TestCheckinSettingsWidgetHelpers:
    def test_strip_type_hint_from_display_name(self):
        strip = CheckinSettingsWidget._strip_type_hint_from_display_name
        assert strip("CPAP use (yes/no)") == "CPAP use"
        assert strip("Mood") == "Mood"

    def test_set_combo_current_by_data(self, qapp):
        combo = QComboBox()
        combo.addItem("Yes/No", "yes_no")
        combo.addItem("Number", "number")
        combo.setCurrentIndex(0)

        CheckinSettingsWidget._set_combo_current_by_data(combo, "number")
        assert combo.currentData() == "number"
