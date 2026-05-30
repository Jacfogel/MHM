"""Unit coverage for checkin_analytics helper and analysis paths."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from checkins.checkin_analytics import CheckinAnalytics
from core.time_utilities import format_timestamp, TIMESTAMP_FULL


TEST_ANCHOR_DT = datetime(2026, 1, 15, 12, 0, 0)


def _row(timestamp: str, **fields) -> dict:
    data = {k: v for k, v in fields.items()}
    return {
        "submitted_at": timestamp,
        **data,
        "responses": dict(data),
        "questions_asked": list(data.keys()),
    }


@pytest.fixture
def analytics() -> CheckinAnalytics:
    return CheckinAnalytics()


@pytest.mark.unit
@pytest.mark.checkins
@pytest.mark.analytics
class TestCheckinAnalyticsHelpers:
    def test_coerce_yes_no_variants(self, analytics: CheckinAnalytics):
        assert analytics._coerce_yes_no(True) is True
        assert analytics._coerce_yes_no(False) is False
        assert analytics._coerce_yes_no(1) is True
        assert analytics._coerce_yes_no(0) is False
        assert analytics._coerce_yes_no("yes") is True
        assert analytics._coerce_yes_no("nope") is False
        assert analytics._coerce_yes_no("maybe") is None
        assert analytics._coerce_yes_no(None) is None
        assert analytics._coerce_yes_no("SKIPPED") is None

    def test_coerce_sleep_hours_formats(self, analytics: CheckinAnalytics):
        assert analytics._coerce_sleep_hours({"total_sleep_hours": 7.5}) == 7.5
        assert analytics._coerce_sleep_hours(
            {
                "sleep_chunks": [
                    {"duration_hours": 6.0},
                    {"sleep_time": "23:00", "wake_time": "07:00"},
                ]
            }
        ) == 14.0
        assert analytics._coerce_sleep_hours("22:00-06:30") == 8.5
        assert analytics._coerce_sleep_hours({"sleep_time": "bad", "wake_time": "07:00"}) is None

    def test_coerce_numeric_and_bucket_scale(self):
        assert CheckinAnalytics._coerce_numeric(4) == 4.0
        assert CheckinAnalytics._coerce_numeric("3.5") == 3.5
        assert CheckinAnalytics._coerce_numeric("bad") is None
        assert CheckinAnalytics._coerce_numeric(True) is None
        assert CheckinAnalytics._bucket_scale_value(2.4) == 2
        assert CheckinAnalytics._bucket_scale_value(2.6) == 3
        assert CheckinAnalytics._bucket_scale_value(6) is None

    def test_question_and_answer_helpers(self, analytics: CheckinAnalytics):
        checkin = {
            "responses": {"mood": 4, "notes": " okay "},
            "questions_asked": ["mood"],
        }
        assert analytics._get_questions_asked(checkin) == ["mood"]
        assert analytics._is_question_asked(checkin, "mood") is True
        assert analytics._response_value(checkin, "mood") == 4
        assert analytics._is_answered_value("SKIPPED") is True
        assert analytics._is_answered_value("  ") is False
        assert analytics._is_answered_value(["a"]) is True

    def test_calculate_sleep_duration_overnight(self, analytics: CheckinAnalytics):
        assert analytics._calculate_sleep_duration("23:00", "07:00") == 8.0
        assert analytics._calculate_sleep_duration("07:00", "06:00") == 23.0

    def test_status_and_recommendation_helpers(self, analytics: CheckinAnalytics):
        assert analytics._get_habit_status(95) == "Excellent"
        assert analytics._get_habit_status(80) == "Good"
        assert analytics._get_habit_status(60) == "Fair"
        assert analytics._get_habit_status(30) == "Needs Improvement"
        assert analytics._get_score_level(85) == "Excellent"
        assert analytics._get_score_level(55) == "Fair"
        assert analytics._get_score_level(40) == "Needs Attention"

        short_sleep = analytics._get_sleep_recommendations(6.0, 2.0, 5)
        assert any("7-8 hours" in item for item in short_sleep)
        assert any("sleep specialist" in item for item in short_sleep)

        good_sleep = analytics._get_sleep_recommendations(8.0, 4.0, 0)
        assert good_sleep == ["Your sleep patterns look good! Keep it up!"]

        wellness_recs = analytics._get_wellness_recommendations(70, 70, 70, 70)
        assert wellness_recs == ["Your wellness is looking good! Keep up the great work!"]

        low_wellness = analytics._get_wellness_recommendations(40, 40, 40, 40)
        assert len(low_wellness) == 4


@pytest.mark.unit
@pytest.mark.checkins
@pytest.mark.analytics
class TestCheckinAnalyticsAnalysisPaths:
    def test_get_energy_trends_with_data(self, analytics: CheckinAnalytics):
        checkins = []
        for i in range(10):
            ts = format_timestamp(
                TEST_ANCHOR_DT - timedelta(days=i), TIMESTAMP_FULL
            )
            checkins.append(_row(ts, energy=3 + (i % 2)))

        with patch("checkins.checkin_analytics.get_checkins_by_days", return_value=checkins):
            result = analytics.get_energy_trends("user-1", days=30)

        assert "error" not in result
        assert result["total_checkins"] == 10
        assert "energy_distribution" in result

    def test_get_energy_trends_no_valid_data(self, analytics: CheckinAnalytics):
        checkins = [_row("2026-01-01 10:00:00", notes="no energy field")]
        with patch("checkins.checkin_analytics.get_checkins_by_days", return_value=checkins):
            result = analytics.get_energy_trends("user-1", days=7)

        assert result["error"] == "No valid energy data found"

    def test_get_mood_trends_improving_and_declining(self, analytics: CheckinAnalytics):
        improving = []
        for i in range(14):
            ts = format_timestamp(
                TEST_ANCHOR_DT - timedelta(days=13 - i), TIMESTAMP_FULL
            )
            mood = 5 if i < 7 else 2
            improving.append(_row(ts, mood=mood))

        with patch("checkins.checkin_analytics.get_checkins_by_days", return_value=improving):
            result = analytics.get_mood_trends("user-1", days=30)

        assert result["trend"] == "improving"

        declining = []
        for i in range(14):
            ts = format_timestamp(
                TEST_ANCHOR_DT - timedelta(days=13 - i), TIMESTAMP_FULL
            )
            mood = 2 if i < 7 else 5
            declining.append(_row(ts, mood=mood))

        with patch("checkins.checkin_analytics.get_checkins_by_days", return_value=declining):
            result = analytics.get_mood_trends("user-1", days=30)

        assert result["trend"] == "declining"

    def test_get_wellness_score_insufficient_data(self, analytics: CheckinAnalytics):
        checkins = [
            _row("2026-01-01 10:00:00", mood=4),
            _row("2026-01-02 10:00:00", mood=4),
        ]
        with patch("checkins.checkin_analytics.get_checkins_by_days", return_value=checkins):
            result = analytics.get_wellness_score("user-1", days=7)

        assert result["error"] == "Insufficient data for analysis"
        assert result["total_checkins"] == 2

    def test_get_available_data_types(self, analytics: CheckinAnalytics):
        checkins = [
            _row("2026-01-01 10:00:00", mood=4, energy=3),
            _row(
                "2026-01-02 10:00:00",
                sleep_quality=4,
                sleep_schedule={"sleep_time": "23:00", "wake_time": "07:00"},
                ate_breakfast=True,
            ),
        ]
        with patch("checkins.checkin_analytics.get_checkins_by_days", return_value=checkins):
            result = analytics.get_available_data_types("user-1", days=30)

        assert result["data_types"]["mood"] is True
        assert result["data_types"]["sleep"] is True
        assert result["data_types"]["habits"] is True
        assert result["data_types"]["quantitative"] is True

    def test_get_basic_analytics_groups_by_category(self, analytics: CheckinAnalytics):
        checkins = [
            _row("2026-01-01 10:00:00", mood=4),
            _row("2026-01-02 10:00:00", mood=5, ate_breakfast=True),
        ]
        question_defs = {
            "mood": {
                "type": "scale_1_5",
                "category": "wellness",
                "ui_display_name": "Mood",
                "validation": {"max": 5},
            },
            "ate_breakfast": {
                "type": "yes_no",
                "category": "habits",
                "ui_display_name": "Breakfast",
            },
        }
        categories = {
            "wellness": {"name": "Wellness"},
            "habits": {"name": "Habits"},
        }

        with (
            patch("checkins.checkin_analytics.get_checkins_by_days", return_value=checkins),
            patch(
                "checkins.checkin_dynamic_manager.dynamic_checkin_manager.get_all_questions",
                return_value=question_defs,
            ),
            patch(
                "checkins.checkin_dynamic_manager.dynamic_checkin_manager.get_categories",
                return_value=categories,
            ),
        ):
            result = analytics.get_basic_analytics("user-1", days=30)

        assert "error" not in result
        assert result["total_checkins"] == 2
        assert "wellness" in result["categories"]
        assert "habits" in result["categories"]
        mood_question = result["categories"]["wellness"]["questions"][0]
        assert mood_question["average"] == 4.5

    def test_get_completion_rate_counts_incomplete_days(self, analytics: CheckinAnalytics):
        complete = _row("2026-01-01 10:00:00", mood=4)
        incomplete = {
            "submitted_at": "2026-01-02 10:00:00",
            "responses": {"mood": None},
            "questions_asked": ["mood"],
        }
        with (
            patch(
                "checkins.checkin_analytics.get_checkins_by_days",
                return_value=[complete, incomplete],
            ),
            patch(
                "checkins.checkin_dynamic_manager.dynamic_checkin_manager.get_all_questions",
                return_value={"mood": {"type": "scale_1_5"}},
            ),
        ):
            result = analytics.get_completion_rate("user-1", days=30)

        assert result["days_completed"] == 1
        assert result["days_missed"] == 1
        assert result["rate"] == 50.0

    def test_calculate_streak_and_sleep_consistency(self, analytics: CheckinAnalytics):
        checkins = [
            {"responses": {"exercise": True}, "questions_asked": ["exercise"]},
            {"responses": {"exercise": True}, "questions_asked": ["exercise"]},
            {"responses": {"exercise": False}, "questions_asked": ["exercise"]},
            {"responses": {"exercise": True}, "questions_asked": ["exercise"]},
        ]
        streak = analytics._calculate_streak(checkins, "exercise")
        assert streak["best"] >= 2

        assert analytics._calculate_sleep_consistency([7.0]) == 100
        consistency = analytics._calculate_sleep_consistency([7.0, 8.0, 7.5])
        assert 0 <= consistency <= 100

    def test_get_sleep_analysis_quality_only_and_hours_only(self, analytics: CheckinAnalytics):
        quality_only = [
            _row("2026-01-01 10:00:00", sleep_quality=2),
            _row("2026-01-02 10:00:00", sleep_quality=5),
        ]
        with patch("checkins.checkin_analytics.get_checkins_by_days", return_value=quality_only):
            result = analytics.get_sleep_analysis("user-1", days=7)

        assert "error" not in result
        assert result["average_quality"] == 3.5
        assert result["average_hours"] is None

        hours_only = [
            _row(
                "2026-01-01 10:00:00",
                sleep_schedule={"sleep_time": "23:00", "wake_time": "07:00"},
            )
        ]
        with patch("checkins.checkin_analytics.get_checkins_by_days", return_value=hours_only):
            result = analytics.get_sleep_analysis("user-1", days=7)

        assert result["average_hours"] == 8.0
        assert result["average_quality"] is None

    def test_get_quantitative_summaries_with_explicit_fields(self, analytics: CheckinAnalytics):
        checkins = [
            _row("2026-01-01 10:00:00", mood=4, exercise=True),
            _row("2026-01-02 10:00:00", mood=5, exercise=False),
        ]
        with patch("checkins.checkin_analytics.get_checkins_by_days", return_value=checkins):
            result = analytics.get_quantitative_summaries(
                "user-1", days=7, enabled_fields=["mood", "exercise"]
            )

        assert result["mood"]["average"] == 4.5
        assert result["exercise"]["average"] == 0.5
