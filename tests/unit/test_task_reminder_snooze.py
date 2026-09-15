"""Unit tests for reminder-only task snooze timing and persistence."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from core.natural_language_defaults import NaturalLanguageDefaults
from tasks.task_data_handlers import runtime_task_due_date
from tasks.task_reminder_snooze import (
    parse_custom_snooze_when,
    resolve_snooze_until,
    snooze_task_reminder,
    task_reminder_is_snoozed,
    tonight_snooze_label,
)
from tests.test_helpers.test_utilities import TestUserFactory


def _defaults() -> NaturalLanguageDefaults:
    return NaturalLanguageDefaults.builtin()


@pytest.mark.unit
@pytest.mark.tasks
class TestResolveSnoozeUntil:
    def test_one_hour_keeps_the_same_clock_plus_hour(self):
        now = datetime(2026, 9, 14, 10, 15, 0)
        until = resolve_snooze_until("1_hour", now_dt=now, nl_defaults=_defaults())
        assert until == datetime(2026, 9, 14, 11, 15, 0)

    def test_tonight_before_evening_uses_tonight_start(self):
        now = datetime(2026, 9, 14, 10, 0, 0)
        until = resolve_snooze_until("tonight", now_dt=now, nl_defaults=_defaults())
        assert until is not None
        assert until.date() == now.date()
        assert (until.hour, until.minute) == (18, 0)

    def test_tonight_during_evening_uses_tomorrow_morning(self):
        now = datetime(2026, 9, 14, 20, 0, 0)
        until = resolve_snooze_until("tonight", now_dt=now, nl_defaults=_defaults())
        assert until is not None
        assert until.date().isoformat() == "2026-09-15"
        assert (until.hour, until.minute) == (9, 0)

    def test_tonight_button_label_switches_after_evening(self):
        defaults = _defaults()
        assert (
            tonight_snooze_label(
                None, datetime(2026, 9, 14, 10, 0, 0), nl_defaults=defaults
            )
            == "Tonight"
        )
        assert (
            tonight_snooze_label(
                None, datetime(2026, 9, 14, 20, 0, 0), nl_defaults=defaults
            )
            == "Tomorrow morning"
        )

    def test_next_week_uses_morning_in_seven_days(self):
        now = datetime(2026, 9, 14, 15, 30, 0)
        until = resolve_snooze_until("next_week", now_dt=now, nl_defaults=_defaults())
        assert until == datetime(2026, 9, 21, 9, 0, 0)

    def test_custom_tomorrow_morning(self):
        now = datetime(2026, 9, 14, 10, 0, 0)
        until = parse_custom_snooze_when(
            "tomorrow morning", now_dt=now, nl_defaults=_defaults()
        )
        assert until == datetime(2026, 9, 15, 9, 0, 0)

    def test_custom_friday_afternoon(self):
        now = datetime(2026, 9, 14, 10, 0, 0)
        until = parse_custom_snooze_when(
            "Friday 3pm", now_dt=now, nl_defaults=_defaults()
        )
        assert until == datetime(2026, 9, 18, 15, 0, 0)

    def test_custom_in_twenty_minutes(self):
        now = datetime(2026, 9, 14, 10, 0, 0)
        until = parse_custom_snooze_when(
            "in 20 minutes", now_dt=now, nl_defaults=_defaults()
        )
        assert until == datetime(2026, 9, 14, 10, 20, 0)


@pytest.mark.unit
@pytest.mark.tasks
class TestSnoozeTaskReminder:
    def test_snooze_does_not_change_due_date(self, test_data_dir):
        user_id = "snooze_due_stays"
        assert TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        from tasks import create_task, get_task_by_id

        task_id = create_task(
            user_id, title="Call dentist", due_date="2026-09-20", due_time="14:00"
        )
        scheduler = MagicMock()
        scheduler.schedule_task_reminder_at_datetime.return_value = True
        with patch(
            "scheduler.runtime_access.get_scheduler_manager", return_value=scheduler
        ):
            result = snooze_task_reminder(
                user_id,
                task_id,
                "1_hour",
                now_dt=datetime(2026, 9, 14, 10, 0, 0),
            )
        assert result.success is True
        task = get_task_by_id(user_id, task_id)
        assert runtime_task_due_date(task) == "2026-09-20"
        assert task.get("due", {}).get("time") == "14:00"
        assert task.get("reminder_sent") is True
        assert task.get("reminder_snooze_until")
        scheduler.schedule_task_reminder_at_datetime.assert_called_once()

    def test_future_snooze_is_detected(self):
        task = {"reminder_snooze_until": "2026-09-14 12:00:00"}
        assert task_reminder_is_snoozed(task, now_dt=datetime(2026, 9, 14, 11, 0, 0))
        assert not task_reminder_is_snoozed(task, now_dt=datetime(2026, 9, 14, 12, 0, 0))
