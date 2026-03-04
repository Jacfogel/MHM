import re
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from communication.message_processing.conversation_flow_manager import ConversationManager


@pytest.fixture
def manager(monkeypatch):
    monkeypatch.setattr(ConversationManager, "_load_user_states", lambda self: None)
    monkeypatch.setattr(ConversationManager, "_expire_inactive_checkins", lambda self, user_id=None: None)
    return ConversationManager()


@pytest.mark.unit
@pytest.mark.communication
class TestConversationFlowReminderHelpers:
    def test_normalize_reminder_text(self, manager):
        assert manager._normalize_reminder_text("  An hour before ") == "60 minutes before"
        assert manager._normalize_reminder_text("a hour before") == "60 minutes before"

    def test_get_reminder_parse_patterns_contains_expected_shapes(self, manager):
        patterns = manager._get_reminder_parse_patterns()
        assert len(patterns) >= 10
        units = {unit for _, unit in patterns}
        assert {"minutes", "hours", "days"}.issubset(units)

    def test_parse_reminder_range_single_and_range(self, manager):
        single = re.search(r"(\d+)\s*minutes?\s*before", "45 minutes before")
        ranged = re.search(r"(\d+)\s*(?:to|-)\s*(\d+)\s*hours?\s*before", "2 to 5 hours before")

        assert single is not None
        assert ranged is not None
        assert manager._parse_reminder_range(single) == (45, 45)
        assert manager._parse_reminder_range(ranged) == (2, 5)

    def test_build_reminder_deltas(self, manager):
        assert manager._build_reminder_deltas("minutes", 30, 60) == (
            timedelta(minutes=60),
            timedelta(minutes=30),
        )
        assert manager._build_reminder_deltas("hours", 1, 3) == (
            timedelta(hours=3),
            timedelta(hours=1),
        )
        assert manager._build_reminder_deltas("days", 1, 2) == (
            timedelta(days=2),
            timedelta(days=1),
        )
        assert manager._build_reminder_deltas("weeks", 1, 2) is None

    def test_build_future_reminder_period_skips_past_windows(self, manager, monkeypatch):
        due = datetime(2026, 3, 10, 12, 0, 0)
        monkeypatch.setattr(
            "communication.message_processing.conversation_flow_manager.now_datetime_full",
            lambda: datetime(2026, 3, 10, 11, 59, 0),
        )
        period = manager._build_future_reminder_period(
            due,
            timedelta(hours=3),
            timedelta(hours=2),
        )
        assert period is None

    def test_build_future_reminder_period_returns_formatted_window(self, manager, monkeypatch):
        due = datetime(2026, 3, 10, 12, 0, 0)
        monkeypatch.setattr(
            "communication.message_processing.conversation_flow_manager.now_datetime_full",
            lambda: datetime(2026, 3, 10, 9, 0, 0),
        )
        period = manager._build_future_reminder_period(
            due,
            timedelta(hours=3),
            timedelta(hours=2),
        )

        assert period is not None
        assert period["date"] == "2026-03-10"
        assert period["start_time"] == "09:00"
        assert period["end_time"] == "10:00"

    def test_get_task_due_datetime_for_reminders_missing_task_or_due_date(self, manager):
        with patch("tasks.get_task_by_id", return_value=None):
            assert manager._get_task_due_datetime_for_reminders("u1", "t1") is None

        with patch("tasks.get_task_by_id", return_value={"task_id": "t1"}):
            assert manager._get_task_due_datetime_for_reminders("u1", "t1") is None

    def test_get_task_due_datetime_for_reminders_prefers_due_date_and_time(self, manager):
        due = datetime(2026, 3, 12, 14, 30, 0)
        with (
            patch("tasks.get_task_by_id", return_value={"due_date": "2026-03-12", "due_time": "14:30"}),
            patch("communication.message_processing.conversation_flow_manager.parse_date_and_time_minute", return_value=due),
        ):
            resolved = manager._get_task_due_datetime_for_reminders("u1", "t1")

        assert resolved == due

    def test_get_task_due_datetime_for_reminders_falls_back_to_date_only(self, manager):
        date_only = datetime(2026, 4, 1, 0, 0, 0)
        with (
            patch("tasks.get_task_by_id", return_value={"due_date": "2026-04-01", "due_time": ""}),
            patch("communication.message_processing.conversation_flow_manager.parse_date_and_time_minute", return_value=None),
            patch("communication.message_processing.conversation_flow_manager.parse_date_only", return_value=date_only),
        ):
            resolved = manager._get_task_due_datetime_for_reminders("u1", "t1")

        assert resolved == datetime(2026, 4, 1, 9, 0, 0)

    def test_get_task_due_datetime_for_reminders_invalid_date_returns_none(self, manager):
        with (
            patch("tasks.get_task_by_id", return_value={"due_date": "bad-date", "due_time": "12:00"}),
            patch("communication.message_processing.conversation_flow_manager.parse_date_and_time_minute", return_value=None),
            patch("communication.message_processing.conversation_flow_manager.parse_date_only", return_value=None),
        ):
            resolved = manager._get_task_due_datetime_for_reminders("u1", "t1")

        assert resolved is None

    def test_parse_reminder_periods_from_text_returns_empty_when_no_due_datetime(self, manager):
        with patch.object(manager, "_get_task_due_datetime_for_reminders", return_value=None):
            assert manager._parse_reminder_periods_from_text("u1", "t1", "30 minutes before") == []

    def test_parse_reminder_periods_from_text_parses_minutes_range(self, manager):
        due = datetime(2026, 3, 12, 12, 0, 0)
        with (
            patch.object(manager, "_get_task_due_datetime_for_reminders", return_value=due),
            patch(
                "communication.message_processing.conversation_flow_manager.now_datetime_full",
                return_value=datetime(2026, 3, 12, 10, 0, 0),
            ),
        ):
            periods = manager._parse_reminder_periods_from_text(
                "u1", "t1", "30 minutes to an hour before"
            )

        assert len(periods) == 1
        assert periods[0]["date"] == "2026-03-12"
        assert periods[0]["start_time"] == "11:00"
        assert periods[0]["end_time"] == "11:30"

    def test_parse_reminder_periods_from_text_handles_parser_exception(self, manager):
        due = datetime(2026, 3, 12, 12, 0, 0)
        with (
            patch.object(manager, "_get_task_due_datetime_for_reminders", return_value=due),
            patch.object(manager, "_parse_reminder_range", side_effect=ValueError("bad parse")),
        ):
            periods = manager._parse_reminder_periods_from_text(
                "u1", "t1", "30 minutes before"
            )

        assert periods == []
