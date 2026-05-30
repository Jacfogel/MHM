"""Unit coverage for scheduler.task_reminders selection and weight helpers."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from scheduler import task_reminders as tr


@pytest.mark.unit
@pytest.mark.scheduler
class TestTaskSelectionEdgeCases:
    def test_empty_list_returns_none(self):
        assert tr.handle_task_selection_edge_cases([]) is None

    def test_single_task_returns_that_task(self):
        task = {"id": "t1", "title": "Only task"}
        assert tr.handle_task_selection_edge_cases([task]) == task

    def test_multiple_tasks_returns_proceed_token(self):
        tasks = [{"id": "t1"}, {"id": "t2"}]
        assert tr.handle_task_selection_edge_cases(tasks) == "PROCEED"


@pytest.mark.unit
@pytest.mark.scheduler
class TestPriorityAndDueDateWeights:
    @pytest.mark.parametrize(
        ("priority", "expected"),
        [
            ("critical", 3.0),
            ("high", 2.0),
            ("medium", 1.5),
            ("low", 1.0),
            ("none", 0.8),
            ("unknown", 1.0),
        ],
    )
    def test_calculate_priority_weight(self, priority, expected):
        assert tr.calculate_priority_weight({"priority": priority}) == expected

    def test_calculate_due_date_weight_no_due_date(self):
        assert tr.calculate_due_date_weight({}, date(2026, 5, 29)) == 0.9

    def test_calculate_due_date_weight_overdue(self):
        task = {"due": {"date": "2026-05-20"}}
        weight = tr.calculate_due_date_weight(task, date(2026, 5, 29))
        assert weight > 2.5

    def test_calculate_due_date_weight_due_today(self):
        task = {"due": {"date": "2026-05-29"}}
        assert tr.calculate_due_date_weight(task, date(2026, 5, 29)) == 2.5

    def test_calculate_due_date_weight_within_week(self):
        task = {"due": {"date": "2026-06-02"}}
        weight = tr.calculate_due_date_weight(task, date(2026, 5, 29))
        assert 1.0 <= weight < 2.5

    def test_calculate_due_date_weight_far_future(self):
        task = {"due": {"date": "2026-08-15"}}
        assert tr.calculate_due_date_weight(task, date(2026, 5, 29)) == 0.8

    def test_calculate_due_date_weight_invalid_date(self):
        task = {"due": {"date": "not-a-date"}}
        assert tr.calculate_due_date_weight(task, date(2026, 5, 29)) == 1.0

    def test_calculate_task_weights_combines_factors(self):
        today = date(2026, 5, 29)
        tasks = [
            {"id": "a", "priority": "high", "due": {"date": "2026-05-29"}},
            {"id": "b", "priority": "low"},
        ]
        weights = tr.calculate_task_weights(tasks, today)
        assert len(weights) == 2
        assert weights[0][1] > weights[1][1]


@pytest.mark.unit
@pytest.mark.scheduler
class TestTaskSelectionKeyAndWeightedPick:
    def test_task_selection_key_prefers_id(self):
        assert tr.task_selection_key({"id": "abc", "title": "T"}, 0) == "abc|0"

    def test_task_selection_key_falls_back_to_index(self):
        assert tr.task_selection_key({}, 3) == "idx-3|3"

    def test_select_task_by_weight_empty_weights_uses_random_choice(self):
        manager = MagicMock(_reminder_selection_state={})
        tasks = [{"id": "t1"}, {"id": "t2"}]
        with patch("scheduler.task_reminders.random.choice", return_value=tasks[1]):
            picked = tr.select_task_by_weight(manager, [], tasks)
        assert picked == tasks[1]

    def test_select_task_by_weight_zero_total_weight(self):
        manager = MagicMock(_reminder_selection_state={})
        tasks = [{"id": "t1"}]
        weights = [(tasks[0], 0.0)]
        with patch("scheduler.task_reminders.random.choice", return_value=tasks[0]):
            picked = tr.select_task_by_weight(manager, weights, tasks)
        assert picked == tasks[0]

    def test_select_task_by_weight_tracks_selection_state(self):
        manager = MagicMock(_reminder_selection_state={})
        task = {"id": "weighted-task", "priority": "high"}
        weights = [(task, 5.0)]
        with patch("scheduler.task_reminders.random.uniform", return_value=1.0):
            picked = tr.select_task_by_weight(manager, weights, [task])
        assert picked == task
        assert manager._reminder_selection_state["weighted-task|0"] == 5.0

    def test_select_task_for_reminder_single_task_short_circuit(self):
        manager = MagicMock(_reminder_selection_state={})
        task = {"id": "solo"}
        assert tr.select_task_for_reminder(manager, [task]) == task


@pytest.mark.unit
@pytest.mark.scheduler
class TestRandomTimeWithinTaskPeriod:
    def test_valid_range_returns_hh_mm(self):
        with patch("scheduler.task_reminders.random.randint", return_value=0):
            result = tr.get_random_time_within_task_period("09:00", "10:00")
        assert result == "09:00"

    def test_invalid_times_return_none(self):
        assert tr.get_random_time_within_task_period("bad", "10:00") is None

    def test_end_before_start_wraps_to_next_day(self):
        with patch("scheduler.task_reminders.random.randint", return_value=3600):
            result = tr.get_random_time_within_task_period("22:00", "01:00")
        assert result is not None


@pytest.mark.unit
@pytest.mark.scheduler
class TestHandleTaskReminderModule:
    def test_no_delivery_logs_and_returns(self):
        tr.handle_task_reminder(MagicMock(delivery=None), "u1", "task-1")

    def test_task_not_found(self):
        manager = MagicMock()
        with patch("tasks.get_task_by_id", return_value=None):
            tr.handle_task_reminder(manager, "u1", "missing")
        manager.delivery.handle_task_reminder.assert_not_called()

    def test_completed_task_skipped(self):
        manager = MagicMock()
        with (
            patch("tasks.get_task_by_id", return_value={"id": "t1", "status": "done"}),
            patch("scheduler.task_reminders.runtime_task_is_completed", return_value=True),
        ):
            tr.handle_task_reminder(manager, "u1", "t1")
        manager.delivery.handle_task_reminder.assert_not_called()

    def test_success_sends_and_updates_task(self):
        manager = MagicMock()
        task = {"id": "t1", "status": "open"}
        with (
            patch("tasks.get_task_by_id", return_value=task),
            patch("scheduler.task_reminders.runtime_task_is_completed", return_value=False),
            patch("tasks.update_task") as update_task,
        ):
            tr.handle_task_reminder(manager, "u1", "t1", retry_attempts=1)
        manager.delivery.handle_task_reminder.assert_called_once_with("u1", "t1")
        update_task.assert_called_once_with("u1", "t1", {"reminder_sent": True})
