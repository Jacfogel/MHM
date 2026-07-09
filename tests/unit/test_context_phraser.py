"""
Unit tests for ai/conversational_context/context_phraser.py.

Phrasing helpers use analyze_checkin_entries for check-in metrics.
"""

from unittest.mock import patch

import pytest

from ai.context.analytics import ContextAnalysis, analyze_checkin_entries
from ai.context.phraser import (
    append_checkin_summary,
    append_profile_sections,
    append_task_data,
    phrase_checkin_summary,
)
from tests.test_helpers.test_utilities import TestUserFactory


@pytest.mark.unit
@pytest.mark.ai
class TestContextPhraser:
    """Natural-language context sections built from computed facts."""

    def test_append_profile_sections_with_profile(self):
        parts: list[str] = []
        append_profile_sections(
            parts,
            {
                "user_profile": {
                    "preferred_name": "Test User",
                    "active_categories": ["health", "productivity"],
                },
                "user_context": {},
            },
        )
        text = "\n".join(parts)
        assert "Test User" in text
        assert "health, productivity" in text

    def test_append_profile_sections_with_user_context(self):
        parts: list[str] = []
        append_profile_sections(
            parts,
            {
                "user_profile": {},
                "user_context": {
                    "custom_fields": {"health_conditions": ["ADHD", "Depression"]},
                    "notes_for_ai": ["I prefer gentle reminders"],
                    "activities_for_encouragement": ["exercise", "meditation"],
                    "goals": ["Improve sleep", "Exercise regularly"],
                },
            },
        )
        text = "\n".join(parts)
        assert "ADHD, Depression" in text
        assert "I prefer gentle reminders" in text
        assert "exercise, meditation" in text
        assert "Improve sleep, Exercise regularly" in text

    def test_phrase_checkin_summary_with_precomputed_analysis(self):
        checkins = [{"ate_breakfast": True, "mood": 4, "energy": 3, "brushed_teeth": True}]
        analysis = ContextAnalysis(
            total_entries=1,
            breakfast_count=1,
            teeth_brushed_count=1,
            breakfast_rate=100.0,
            avg_mood=4.0,
            avg_energy=3.0,
            teeth_brushing_rate=100.0,
            mood_trend="stable",
            energy_trend="stable",
            overall_wellness_score=85.0,
            insights=["excellent breakfast habits", "generally positive mood"],
        )
        text = phrase_checkin_summary(analysis, checkins)
        assert "1 check-in" in text or "1 check-ins" in text
        assert "4.0" in text
        assert "3.0" in text
        assert "100%" in text

    @patch("ai.context.phraser.is_user_checkins_enabled", return_value=True)
    @patch("ai.context.phraser.get_recent_checkins")
    def test_append_checkin_summary_for_user(self, mock_recent, _mock_enabled, test_data_dir):
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        mock_recent.return_value = [
            {"ate_breakfast": True, "mood": 4, "energy": 3, "brushed_teeth": True}
        ]
        parts: list[str] = []
        append_checkin_summary(parts, user_id)
        text = "\n".join(parts)
        assert "Over the last" in text
        assert "average mood" in text

    @patch("ai.context.phraser.are_tasks_enabled", return_value=True)
    @patch("ai.context.phraser.get_user_task_stats")
    @patch("ai.context.phraser.load_active_tasks", return_value=[])
    @patch("ai.context.phraser.get_tasks_due_soon", return_value=[])
    def test_append_task_data_for_user(
        self, _mock_due, _mock_active, mock_stats, _mock_enabled, test_data_dir
    ):
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        mock_stats.return_value = {"total_count": 2, "active_count": 1, "completed_count": 1}
        parts: list[str] = []
        append_task_data(parts, user_id)
        text = "\n".join(parts)
        assert "task information" in text
        assert "active task" in text

    def test_append_profile_sections_empty_context(self):
        parts: list[str] = []
        append_profile_sections(parts, {})
        assert parts == []

    @patch("ai.context.phraser.resolve_user_timezone_str", return_value="America/Regina")
    @patch("ai.context.phraser.localized_now_for_user")
    def test_phrase_current_datetime_context(self, mock_now, _mock_tz):
        from datetime import datetime

        import pytz

        mock_now.return_value = pytz.timezone("America/Regina").localize(
            datetime(2026, 7, 7, 22, 54, 0)
        )
        from ai.context.phraser import phrase_current_datetime_context

        text = phrase_current_datetime_context("user-1")
        assert "Tuesday, 2026-07-07 at 22:54" in text
        assert "America/Regina" in text
        assert "authoritative 'now'" in text

    @patch("ai.context.phraser.user_local_date")
    @patch("ai.context.phraser.parse_timestamp_full")
    def test_checkin_completed_today_uses_user_local_date(
        self, mock_parse, mock_user_local_date
    ):
        from datetime import date, datetime

        from ai.context.phraser import _checkin_completed_today

        mock_user_local_date.return_value = date(2026, 7, 7)
        mock_parse.return_value = datetime(2026, 7, 7, 9, 15, 0)

        completed, completed_at = _checkin_completed_today(
            "2026-07-07 09:15:00", "user-1"
        )

        assert completed is True
        assert completed_at == "09:15"
        mock_user_local_date.assert_called_once_with("user-1")

    def test_phrase_checkin_summary_empty_checkins(self):
        analysis = analyze_checkin_entries([])
        assert phrase_checkin_summary(analysis, []) == (
            "They have not completed any check-ins yet."
        )
