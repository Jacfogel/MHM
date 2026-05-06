"""Headless helper coverage for ScheduleEditorDialog methods."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from ui.dialogs import schedule_editor_dialog
from ui.dialogs.schedule_editor_dialog import ScheduleEditorDialog


pytestmark = [pytest.mark.unit, pytest.mark.ui]


class _FakeItem:
    def __init__(self, widget):
        self._widget = widget

    def widget(self):
        return self._widget


class _FakeLayout:
    def __init__(self):
        self.widgets = []

    def count(self):
        return len(self.widgets)

    def takeAt(self, index):
        return _FakeItem(self.widgets.pop(index))

    def addWidget(self, widget):
        self.widgets.append(widget)

    def removeWidget(self, widget):
        if widget in self.widgets:
            self.widgets.remove(widget)


class _FakePeriodWidget:
    def __init__(self, name, order=0):
        self._name = name
        self.creation_order = order
        self.parent_value = object()
        self.deleted = False

    def get_period_name(self):
        return self._name

    def setParent(self, value):
        self.parent_value = value

    def deleteLater(self):
        self.deleted = True


def _dialog() -> Any:
    dialog: Any = ScheduleEditorDialog.__new__(ScheduleEditorDialog)
    dialog.user_id = "user-1"
    dialog.category = "motivational"
    dialog.on_save = None
    dialog.periods_layout = _FakeLayout()
    dialog.period_widgets = []
    dialog.deleted_periods = []
    dialog.creation_counter = 0
    return dialog


@pytest.mark.unit
@pytest.mark.ui
def test_resort_period_widgets_places_all_last_and_preserves_creation_order():
    dialog = _dialog()
    old = _FakePeriodWidget("Motivational Message 1", order=0)
    all_period = _FakePeriodWidget("ALL", order=1)
    newer = _FakePeriodWidget("Motivational Message 2", order=2)
    dialog.period_widgets = [all_period, newer, old]
    dialog.periods_layout.widgets = list(dialog.period_widgets)

    dialog.resort_period_widgets()

    assert dialog.periods_layout.widgets == [old, newer, all_period]
    assert all(widget.parent_value is None for widget in [old, newer, all_period])


@pytest.mark.unit
@pytest.mark.ui
def test_find_lowest_available_period_number_uses_message_suffixes():
    dialog = _dialog()
    dialog.period_widgets = [
        _FakePeriodWidget("Motivational Message 1"),
        _FakePeriodWidget("Motivational Message 3"),
        _FakePeriodWidget("ALL"),
    ]

    assert dialog.find_lowest_available_period_number() == 2


@pytest.mark.unit
@pytest.mark.ui
def test_after_add_period_assigns_creation_order_and_resorts(monkeypatch: pytest.MonkeyPatch):
    dialog = _dialog()
    widget = _FakePeriodWidget("Later")
    called = MagicMock()
    monkeypatch.setattr(dialog, "resort_period_widgets", called)

    dialog._after_add_period(widget)

    assert widget.creation_order == 0
    assert dialog.creation_counter == 1
    called.assert_called_once()


@pytest.mark.unit
@pytest.mark.ui
def test_undo_last_delete_recreates_deleted_period(monkeypatch: pytest.MonkeyPatch):
    dialog = _dialog()
    dialog.deleted_periods = [
        {
            "period_name": "Evening",
            "start_time": "18:00",
            "end_time": "20:00",
            "active": True,
            "days": ["Monday"],
        }
    ]
    added: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        dialog,
        "add_new_period",
        lambda name, data: added.append((name, data)),
    )

    dialog.undo_last_delete()

    assert dialog.deleted_periods == []
    assert added == [
        (
            "Evening",
            {
                "start_time": "18:00",
                "end_time": "20:00",
                "active": True,
                "days": ["Monday"],
            },
        )
    ]


@pytest.mark.unit
@pytest.mark.ui
def test_set_schedule_data_clears_existing_widgets_and_adds_new_periods(
    monkeypatch: pytest.MonkeyPatch,
):
    dialog = _dialog()
    first = _FakePeriodWidget("Old")
    dialog.period_widgets = [first]
    dialog.periods_layout.widgets = [first]
    added: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        dialog,
        "add_new_period",
        lambda name, data: added.append((name, data)),
    )

    dialog.set_schedule_data({"Morning": {"start_time": "08:00"}})

    assert dialog.period_widgets == []
    assert first.deleted is True
    assert added == [("Morning", {"start_time": "08:00"})]


@pytest.mark.unit
@pytest.mark.ui
def test_save_schedule_success_persists_clears_cache_triggers_and_calls_callback(
    monkeypatch: pytest.MonkeyPatch,
):
    dialog = _dialog()
    periods = {"Morning": {"start_time": "08:00", "end_time": "09:00"}}
    callback = MagicMock()
    dialog.on_save = callback
    monkeypatch.setattr(dialog, "collect_period_data", lambda: periods)
    monkeypatch.setattr(
        schedule_editor_dialog,
        "validate_schedule_periods",
        lambda _periods, _category: (True, []),
    )
    set_schedule = MagicMock()
    clear_cache = MagicMock()
    trigger = MagicMock()
    monkeypatch.setattr(schedule_editor_dialog, "set_schedule_periods", set_schedule)
    monkeypatch.setattr(
        schedule_editor_dialog, "clear_schedule_periods_cache", clear_cache
    )
    monkeypatch.setattr(dialog, "_trigger_rescheduling", trigger)

    assert dialog.save_schedule() is True
    set_schedule.assert_called_once_with("user-1", "motivational", periods)
    clear_cache.assert_called_once_with("user-1", "motivational")
    trigger.assert_called_once()
    callback.assert_called_once()
