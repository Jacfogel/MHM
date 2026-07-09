"""
Coverage tests for check-in analytics in ai.context.analytics.

Replaces legacy ContextBuilder private-method coverage.
"""

import pytest

from ai.context.analytics import (
    ContextAnalysis,
    _calculate_wellness_score,
    _determine_trend,
    _generate_insights,
    analyze_checkin_entries,
)
from tests.test_helpers.test_utilities import TestUserFactory


@pytest.mark.behavior
@pytest.mark.ai
class TestContextAnalyticsCoverageExpansion:
    """Test coverage for check-in analytics helpers."""

    def test_analyze_checkin_entries_with_empty_checkins(self, test_data_dir):
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

        analysis = analyze_checkin_entries([])

        assert isinstance(analysis, ContextAnalysis)
        assert analysis.breakfast_rate == 0
        assert analysis.avg_mood is None
        assert analysis.avg_energy is None
        assert analysis.teeth_brushing_rate == 0
        assert analysis.overall_wellness_score == 0.0

    def test_analyze_checkin_entries_with_checkin_data(self, test_data_dir):
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        rows = [
            {"ate_breakfast": True, "mood": 4, "energy": 3, "brushed_teeth": True},
            {"ate_breakfast": False, "mood": 3, "energy": 4, "brushed_teeth": True},
            {"ate_breakfast": True, "mood": 5, "energy": 5, "brushed_teeth": False},
        ]

        analysis = analyze_checkin_entries(rows)

        assert abs(analysis.breakfast_rate - 66.67) < 0.1
        assert analysis.avg_mood == 4.0
        assert analysis.avg_energy == 4.0
        assert abs(analysis.teeth_brushing_rate - 66.67) < 0.1
        assert analysis.overall_wellness_score > 0

    def test_analyze_checkin_entries_with_missing_data(self, test_data_dir):
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        rows = [
            {"ate_breakfast": True},
            {"mood": 3},
            {"energy": 4},
        ]

        analysis = analyze_checkin_entries(rows)

        assert abs(analysis.breakfast_rate - 33.33) < 0.1
        assert analysis.avg_mood == 3.0
        assert analysis.avg_energy == 4.0
        assert analysis.teeth_brushing_rate == 0

    def test_determine_trend_improving(self, test_data_dir):
        TestUserFactory.create_basic_user("test-user", test_data_dir=test_data_dir)
        assert _determine_trend([1.0, 2.0, 3.0, 4.0, 5.0]) == "improving"

    def test_determine_trend_declining(self, test_data_dir):
        TestUserFactory.create_basic_user("test-user", test_data_dir=test_data_dir)
        assert _determine_trend([5.0, 4.0, 3.0, 2.0, 1.0]) == "declining"

    def test_determine_trend_stable(self, test_data_dir):
        TestUserFactory.create_basic_user("test-user", test_data_dir=test_data_dir)
        assert _determine_trend([3.0, 3.0, 3.0, 3.0, 3.0]) == "stable"

    def test_determine_trend_insufficient_data(self, test_data_dir):
        TestUserFactory.create_basic_user("test-user", test_data_dir=test_data_dir)
        assert _determine_trend([1.0, 2.0]) == "stable"

    def test_calculate_wellness_score_all_factors(self, test_data_dir):
        TestUserFactory.create_basic_user("test-user", test_data_dir=test_data_dir)
        score = _calculate_wellness_score(80.0, 4.0, 4.0, 90.0)
        assert 0 < score <= 100

    def test_calculate_wellness_score_no_factors(self, test_data_dir):
        TestUserFactory.create_basic_user("test-user", test_data_dir=test_data_dir)
        assert _calculate_wellness_score(0.0, None, None, 0.0) == 0.0

    def test_generate_insights_excellent_breakfast(self, test_data_dir):
        TestUserFactory.create_basic_user("test-user", test_data_dir=test_data_dir)
        insights = _generate_insights(85.0, 4.0, 4.0, 90.0, "stable", "stable")
        assert "excellent breakfast habits" in insights

    def test_generate_insights_poor_breakfast(self, test_data_dir):
        TestUserFactory.create_basic_user("test-user", test_data_dir=test_data_dir)
        insights = _generate_insights(25.0, 4.0, 4.0, 90.0, "stable", "stable")
        assert "room for improvement in breakfast habits" in insights

    def test_generate_insights_positive_mood(self, test_data_dir):
        TestUserFactory.create_basic_user("test-user", test_data_dir=test_data_dir)
        insights = _generate_insights(80.0, 4.5, 4.0, 90.0, "improving", "stable")
        assert "generally positive mood" in insights
        assert "mood is trending upward" in insights

    def test_generate_insights_low_mood(self, test_data_dir):
        TestUserFactory.create_basic_user("test-user", test_data_dir=test_data_dir)
        insights = _generate_insights(80.0, 1.5, 4.0, 90.0, "declining", "stable")
        assert "challenging mood patterns" in insights
        assert "mood is trending downward" in insights

    def test_generate_insights_energy_patterns(self, test_data_dir):
        TestUserFactory.create_basic_user("test-user", test_data_dir=test_data_dir)
        insights_high = _generate_insights(80.0, 4.0, 4.5, 90.0, "stable", "improving")
        insights_low = _generate_insights(80.0, 4.0, 1.5, 90.0, "stable", "declining")
        assert "good energy levels" in insights_high
        assert "energy is trending upward" in insights_high
        assert "low energy patterns" in insights_low
        assert "energy is trending downward" in insights_low

    def test_generate_insights_dental_hygiene(self, test_data_dir):
        TestUserFactory.create_basic_user("test-user", test_data_dir=test_data_dir)
        insights_excellent = _generate_insights(80.0, 4.0, 4.0, 95.0, "stable", "stable")
        insights_poor = _generate_insights(80.0, 4.0, 4.0, 30.0, "stable", "stable")
        assert "excellent dental hygiene" in insights_excellent
        assert "room for improvement in dental hygiene" in insights_poor

    def test_analyze_checkin_entries_error_handling(self, test_data_dir):
        TestUserFactory.create_basic_user("test-user", test_data_dir=test_data_dir)
        analysis = analyze_checkin_entries([{"invalid": "data"}])
        assert isinstance(analysis, ContextAnalysis)
