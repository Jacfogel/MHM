"""Targeted UI coverage for check-in question count validation behavior."""

from tests.conftest import ensure_qt_runtime
from tests.test_support.conftest_env import skip_qt_ui_on_windows

ensure_qt_runtime()

import pytest

# Qt widget tests run in serial only. On Windows they run (QT_OPENGL=software); set MHM_QT_UI_SKIP=1 to skip if needed.
pytestmark = [pytest.mark.no_parallel, skip_qt_ui_on_windows]


from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QCheckBox, QWidget

from ui.widgets.checkin_settings_widget import CheckinSettingsWidget


def _checkbox(checked: bool) -> QCheckBox:
    box = QCheckBox()
    box.setChecked(checked)
    return box


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def widget(qapp):
    with patch.object(CheckinSettingsWidget, "load_existing_data", return_value=None):
        control = CheckinSettingsWidget(user_id=None, parent=None)
    yield control
    control.close()
    control.deleteLater()


def _set_dynamic_questions(widget: CheckinSettingsWidget, always: int, sometimes: int):
    state: dict[str, dict[str, QCheckBox]] = {}

    for idx in range(always):
        state[f"always_{idx}"] = {
            "always_checkbox": _checkbox(True),
            "sometimes_checkbox": _checkbox(False),
        }
    for idx in range(sometimes):
        state[f"sometimes_{idx}"] = {
            "always_checkbox": _checkbox(False),
            "sometimes_checkbox": _checkbox(True),
        }
    widget.dynamic_question_checkboxes = state


@pytest.mark.ui
@pytest.mark.checkins
class TestCheckinSettingsWidgetQuestionCounts:
    def test_load_existing_data_without_user_id_initializes_defaults(self, widget):
        with (
            patch.object(widget, "add_new_period") as mock_add_period,
            patch.object(widget, "set_question_checkboxes") as mock_set_questions,
        ):
            widget.user_id = None
            widget.load_existing_data()

        mock_add_period.assert_called_once()
        mock_set_questions.assert_called_once_with({})

    def test_on_question_toggled_calls_validation(self, widget):
        with patch.object(widget, "_validate_question_counts") as mock_validate:
            widget.on_question_toggled(True)

        mock_validate.assert_called_once()

    def test_refresh_question_display_rebuilds_from_current_state(self, widget):
        widget.dynamic_question_checkboxes = {
            "q1": {
                "always_checkbox": _checkbox(True),
                "sometimes_checkbox": _checkbox(False),
            },
            "q2": {
                "always_checkbox": _checkbox(False),
                "sometimes_checkbox": _checkbox(True),
            },
        }

        with patch.object(widget, "set_question_checkboxes") as mock_set_questions:
            widget._refresh_question_display()

        mock_set_questions.assert_called_once()
        sent_state = mock_set_questions.call_args.args[0]
        assert sent_state["q1"]["always_include"] is True
        assert sent_state["q2"]["sometimes_include"] is True

    def test_validate_question_counts_defaults_without_dynamic_questions(self, widget):
        widget.dynamic_question_checkboxes = {}
        widget._validate_question_counts()

        assert widget.min_questions_spinbox.minimum() == 1
        assert widget.max_questions_spinbox.maximum() == 50

    def test_validate_question_counts_all_always_questions_locks_ranges(self, widget):
        _set_dynamic_questions(widget, always=2, sometimes=0)
        widget._validate_question_counts()

        assert widget.min_questions_spinbox.minimum() == 2
        assert widget.min_questions_spinbox.maximum() == 2
        assert widget.max_questions_spinbox.minimum() == 2
        assert widget.max_questions_spinbox.maximum() == 2
        assert widget.min_questions_spinbox.value() == 2
        assert widget.max_questions_spinbox.value() == 2

    def test_validate_question_counts_sometimes_questions_require_max_headroom(self, widget):
        _set_dynamic_questions(widget, always=1, sometimes=2)
        widget._validate_question_counts()

        assert widget.min_questions_spinbox.minimum() == 1
        assert widget.min_questions_spinbox.maximum() == 2
        assert widget.max_questions_spinbox.minimum() == 2
        assert widget.max_questions_spinbox.maximum() == 2

    def test_on_max_changed_reduces_min_when_max_drops_below_min(self, widget):
        widget.min_questions_spinbox.setValue(5)
        widget.max_questions_spinbox.setValue(8)

        widget._on_max_changed(3)

        assert widget.min_questions_spinbox.value() == 3
        assert widget.max_questions_spinbox.value() >= widget.min_questions_spinbox.value()
        assert widget._adjusting_from_max is False

    def test_on_min_changed_raises_max_when_needed(self, widget):
        widget.min_questions_spinbox.setValue(1)
        widget.max_questions_spinbox.setValue(2)

        widget._on_min_changed(4)

        assert widget.max_questions_spinbox.value() == 4

    def test_get_checkin_settings_uses_dynamic_checkbox_state(self, widget):
        widget.dynamic_question_checkboxes = {
            "q_always": {
                "always_checkbox": _checkbox(True),
                "sometimes_checkbox": _checkbox(False),
            },
            "q_sometimes": {
                "always_checkbox": _checkbox(False),
                "sometimes_checkbox": _checkbox(True),
            },
        }
        widget.min_questions_spinbox.setValue(2)
        widget.max_questions_spinbox.setValue(4)

        with (
            patch(
                "ui.widgets.checkin_settings_widget.collect_period_data_from_widgets",
                return_value={"morning": {"start_time": "08:00", "end_time": "09:00"}},
            ),
            patch(
                "core.checkin_dynamic_manager.dynamic_checkin_manager.get_enabled_questions_for_ui",
                return_value={
                    "q_always": {"ui_display_name": "Always"},
                    "q_sometimes": {"ui_display_name": "Sometimes"},
                },
            ),
        ):
            settings = widget.get_checkin_settings()

        assert settings["time_periods"]["morning"]["start_time"] == "08:00"
        assert settings["questions"]["q_always"]["enabled"] is True
        assert settings["questions"]["q_always"]["always_include"] is True
        assert settings["questions"]["q_sometimes"]["sometimes_include"] is True
        assert settings["min_questions"] == 2
        assert settings["max_questions"] == 2

    def test_set_checkin_settings_populates_periods_and_question_ranges(self, widget):
        existing = QWidget()
        widget.period_widgets = [existing]
        settings = {
            "time_periods": {"morning": {"start_time": "08:00", "end_time": "09:00"}},
            "questions": {"q1": {"enabled": True, "always_include": True}},
            "min_questions": 2,
            "max_questions": 3,
        }

        with (
            patch.object(widget, "add_new_period") as mock_add_period,
            patch.object(widget, "set_question_checkboxes") as mock_set_questions,
            patch.object(widget, "_validate_question_counts") as mock_validate,
        ):
            widget.set_checkin_settings(settings)

        mock_add_period.assert_called_once()
        mock_set_questions.assert_called_once_with(settings["questions"])
        assert widget.min_questions_spinbox.value() == 2
        assert widget.max_questions_spinbox.value() == 3
        assert mock_validate.call_count >= 1

    def test_undo_last_question_delete_shows_info_when_no_deletions(self, widget):
        widget.deleted_questions = []

        with patch("ui.widgets.checkin_settings_widget.QMessageBox.information") as mock_info:
            widget.undo_last_question_delete()

        mock_info.assert_called_once()

    def test_undo_last_question_delete_shows_error_when_restore_fails(self, widget):
        widget.deleted_questions = [
            {"key": "custom_sleep", "definition": {"ui_display_name": "Sleep quality"}}
        ]

        with (
            patch(
                "core.checkin_dynamic_manager.dynamic_checkin_manager.save_custom_question",
                return_value=False,
            ),
            patch("ui.widgets.checkin_settings_widget.QMessageBox.critical") as mock_critical,
        ):
            widget.undo_last_question_delete()

        mock_critical.assert_called_once()
