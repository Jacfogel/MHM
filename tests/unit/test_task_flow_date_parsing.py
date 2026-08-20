"""Due-date flow parsing uses parse_relative_date, then time separately."""

from datetime import datetime
from unittest.mock import patch

import pytest

from communication.message_processing.conversation_flow_manager import ConversationManager
from communication.message_processing.flows.task_flow import (
    _strip_time_tokens_from_date_phrase,
)


@pytest.fixture
def manager(monkeypatch):
    monkeypatch.setattr(ConversationManager, "_load_user_states", lambda self: None)
    monkeypatch.setattr(
        ConversationManager, "_expire_inactive_checkins", lambda self, user_id=None: None
    )
    return ConversationManager()


@pytest.mark.unit
@pytest.mark.communication
class TestTaskFlowDateParsing:
    def test_strip_time_tokens_leaves_date_phrase(self):
        assert _strip_time_tokens_from_date_phrase("tomorrow at 10am") == "tomorrow"
        assert _strip_time_tokens_from_date_phrase("monday at 2pm") == "monday"
        assert _strip_time_tokens_from_date_phrase("2026-01-15 10:00") == "2026-01-15"

    def test_tomorrow_at_time(self, manager):
        fixed_now = datetime(2026, 5, 11, 9, 0)
        with patch(
            "communication.message_processing.flows.task_flow.now_datetime_full",
            return_value=fixed_now,
        ), patch(
            "tasks.task_service.now_datetime_full",
            return_value=fixed_now,
        ):
            date_str, time_str = manager._parse_date_time_from_text("tomorrow at 10am")
        assert date_str == "2026-05-12"
        assert time_str == "10:00"

    def test_tonight_matches_create_task_policy(self, manager):
        fixed_now = datetime(2026, 5, 11, 9, 0)
        with patch(
            "communication.message_processing.flows.task_flow.now_datetime_full",
            return_value=fixed_now,
        ), patch(
            "tasks.task_service.now_datetime_full",
            return_value=fixed_now,
        ):
            date_str, time_str = manager._parse_date_time_from_text("tonight")
        assert date_str == "2026-05-11"
        assert time_str is None

    def test_next_month_on_jan_31_does_not_throw(self, manager):
        fixed_now = datetime(2026, 1, 31, 9, 0)
        with patch(
            "communication.message_processing.flows.task_flow.now_datetime_full",
            return_value=fixed_now,
        ), patch(
            "tasks.task_service.now_datetime_full",
            return_value=fixed_now,
        ):
            date_str, time_str = manager._parse_date_time_from_text("next month")
        assert date_str == "2026-02-28"
        assert time_str is None

    def test_flexible_iso_date_with_time(self, manager):
        date_str, time_str = manager._parse_date_time_from_text("2026-07-01 14:30")
        assert date_str == "2026-07-01"
        assert time_str == "14:30"
