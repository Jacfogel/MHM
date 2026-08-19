"""Unit tests for reminder-period HH:MM combo helpers."""

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="QtWidgets unavailable due to missing GUI system libraries",
)

from PySide6.QtWidgets import QApplication, QComboBox, QHBoxLayout, QWidget

from ui.dialogs.task_edit_dialog import (
    _add_time_combos_to_layout,
    _hhmm_from_combos,
    _time_combos_from_hhmm,
)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _empty_time_combos():
    hour = QComboBox()
    minute = QComboBox()
    ampm = QComboBox()
    hour.addItems([""] + [f"{h:02d}" for h in range(1, 13)])
    minute.addItems([""] + [f"{m:02d}" for m in range(0, 60, 5)])
    ampm.addItems(["", "AM", "PM"])
    return hour, minute, ampm


@pytest.mark.unit
@pytest.mark.ui
class TestTaskEditDialogTimeCombos:
    def test_time_combos_from_hhmm_midnight_and_afternoon(self, qapp):
        hour, minute, ampm = _empty_time_combos()
        _time_combos_from_hhmm(hour, minute, ampm, "00:00")
        assert hour.currentText() == "12"
        assert minute.currentText() == "00"
        assert ampm.currentText() == "AM"

        _time_combos_from_hhmm(hour, minute, ampm, "13:45")
        assert hour.currentText() == "01"
        assert minute.currentText() == "45"
        assert ampm.currentText() == "PM"

    def test_hhmm_from_combos_round_trips(self, qapp):
        hour, minute, ampm = _empty_time_combos()
        _time_combos_from_hhmm(hour, minute, ampm, "09:05")
        assert _hhmm_from_combos(hour, minute, ampm) == "09:05"

        _time_combos_from_hhmm(hour, minute, ampm, "12:00")
        assert _hhmm_from_combos(hour, minute, ampm) == "12:00"

        _time_combos_from_hhmm(hour, minute, ampm, "00:30")
        assert _hhmm_from_combos(hour, minute, ampm) == "00:30"

    def test_hhmm_from_combos_empty_when_incomplete_or_missing(self, qapp):
        hour, minute, ampm = _empty_time_combos()
        assert _hhmm_from_combos(hour, minute, ampm) == ""
        assert _hhmm_from_combos(None, minute, ampm) == ""

    def test_add_time_combos_to_layout_sets_start_and_end(self, qapp):
        host = QWidget()
        layout = QHBoxLayout(host)
        start_hour, start_minute, start_ampm = _add_time_combos_to_layout(
            layout, "08:15"
        )
        end_hour, end_minute, end_ampm = _add_time_combos_to_layout(layout, "17:00")

        assert _hhmm_from_combos(start_hour, start_minute, start_ampm) == "08:15"
        assert _hhmm_from_combos(end_hour, end_minute, end_ampm) == "17:00"
