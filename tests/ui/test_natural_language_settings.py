"""Behavior tests for phrase-settings widget and dialog."""

from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()

from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from core.natural_language_defaults import NaturalLanguageDefaults
from ui.dialogs.natural_language_settings_dialog import NaturalLanguageSettingsDialog
from ui.widgets.natural_language_settings_widget import NaturalLanguageSettingsWidget

pytestmark = [pytest.mark.ui]


@pytest.fixture(scope="module")
def qapp():
    """Provide a process-wide QApplication for widget tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _fill_valid_times(widget: NaturalLanguageSettingsWidget) -> None:
    """Populate every time field with parseable values."""
    widget.line_tonight.setText("18:00")
    widget.line_after_work.setText("17:00")
    widget.line_morning.setText("9:00")
    widget.line_afternoon.setText("14:00")
    widget.line_evening.setText("18:00")
    widget.line_night.setText("21:00")


class TestNaturalLanguageSettingsWidget:
    """Phrase-mapping widget loads, validates, and serializes fields."""

    def test_set_defaults_fills_fields(self, qapp):
        widget = NaturalLanguageSettingsWidget()
        defaults = NaturalLanguageDefaults(
            tonight_start_time="19:30",
            after_work_school_time="16:15",
            time_of_day_defaults={
                "morning": "08:00",
                "afternoon": "13:00",
                "evening": "17:30",
                "night": "22:00",
            },
            weekend_this_week_means_coming_week=False,
        )

        widget.set_defaults(defaults)

        assert widget.line_tonight.text() == "19:30"
        assert widget.line_after_work.text() == "16:15"
        assert widget.line_morning.text() == "08:00"
        assert widget.line_afternoon.text() == "13:00"
        assert widget.line_evening.text() == "17:30"
        assert widget.line_night.text() == "22:00"
        assert widget.check_weekend_coming_week.isChecked() is False
        widget.deleteLater()

    def test_validate_fields_requires_each_time(self, qapp):
        widget = NaturalLanguageSettingsWidget()
        _fill_valid_times(widget)
        widget.line_tonight.setText("")

        assert widget.validate_fields() == "Tonight time is required."
        widget.deleteLater()

    def test_validate_fields_rejects_unparseable_time(self, qapp):
        widget = NaturalLanguageSettingsWidget()
        _fill_valid_times(widget)
        widget.line_morning.setText("not-a-time")

        assert widget.validate_fields() == "Could not parse Morning time: not-a-time"
        widget.deleteLater()

    def test_validate_fields_accepts_parseable_times(self, qapp):
        widget = NaturalLanguageSettingsWidget()
        _fill_valid_times(widget)
        widget.line_tonight.setText("6:00 PM")

        assert widget.validate_fields() == ""
        widget.deleteLater()

    def test_get_preferences_dict_includes_weekend_flag(self, qapp):
        widget = NaturalLanguageSettingsWidget()
        _fill_valid_times(widget)
        widget.check_weekend_coming_week.setChecked(True)

        payload = widget.get_preferences_dict()

        assert payload["tonight_start_time"]
        assert payload["after_work_school_time"]
        assert "morning" in payload["time_of_day_defaults"]
        assert payload["weekend_this_week_means_coming_week"] is True
        widget.deleteLater()


class TestNaturalLanguageSettingsDialog:
    """Phrase-settings dialog load/save paths."""

    def test_load_without_user_uses_builtin_defaults(self, qapp):
        dialog = NaturalLanguageSettingsDialog(user_id=None)

        assert dialog.settings_widget.line_tonight.text()
        assert dialog.settings_widget.line_after_work.text()
        dialog.deleteLater()

    def test_save_without_user_warns(self, qapp):
        dialog = NaturalLanguageSettingsDialog(user_id=None)

        with patch(
            "ui.dialogs.natural_language_settings_dialog.QMessageBox.warning"
        ) as mock_warning:
            dialog.save_settings()

        mock_warning.assert_called_once()
        assert mock_warning.call_args.args[1] == "No User"
        dialog.deleteLater()

    def test_save_with_invalid_time_warns(self, qapp):
        dialog = NaturalLanguageSettingsDialog(user_id="user-1")
        dialog.settings_widget.line_tonight.setText("nope")

        with patch(
            "ui.dialogs.natural_language_settings_dialog.QMessageBox.warning"
        ) as mock_warning:
            dialog.save_settings()

        mock_warning.assert_called_once()
        assert mock_warning.call_args.args[1] == "Invalid Input"
        dialog.deleteLater()

    def test_save_failure_shows_critical(self, qapp):
        dialog = NaturalLanguageSettingsDialog(user_id="user-1")
        _fill_valid_times(dialog.settings_widget)

        with (
            patch(
                "ui.dialogs.natural_language_settings_dialog.save_natural_language_defaults_preferences",
                return_value=False,
            ),
            patch(
                "ui.dialogs.natural_language_settings_dialog.QMessageBox.critical"
            ) as mock_critical,
        ):
            dialog.save_settings()

        mock_critical.assert_called_once()
        dialog.deleteLater()

    def test_save_success_emits_and_accepts(self, qapp):
        dialog = NaturalLanguageSettingsDialog(user_id="user-1")
        _fill_valid_times(dialog.settings_widget)
        emitted = []
        dialog.user_changed.connect(lambda: emitted.append(True))

        with (
            patch(
                "ui.dialogs.natural_language_settings_dialog.save_natural_language_defaults_preferences",
                return_value=True,
            ) as mock_save,
            patch.object(dialog, "accept") as mock_accept,
        ):
            dialog.save_settings()

        mock_save.assert_called_once()
        assert mock_save.call_args.args[0] == "user-1"
        assert emitted == [True]
        mock_accept.assert_called_once()
        dialog.deleteLater()

    def test_load_settings_uses_user_defaults(self, qapp):
        defaults = NaturalLanguageDefaults(tonight_start_time="20:00")
        with patch(
            "ui.dialogs.natural_language_settings_dialog.get_natural_language_defaults",
            return_value=defaults,
        ):
            dialog = NaturalLanguageSettingsDialog(user_id="user-1")

        assert dialog.settings_widget.line_tonight.text() == "20:00"
        dialog.deleteLater()
