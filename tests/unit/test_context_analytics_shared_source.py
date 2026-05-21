"""
Confirm conversational phrasing uses the same check-in analytics as ContextBuilder.
"""

import pytest

from ai.context_builder import ContextBuilder, ContextData, analyze_recent_checkin_rows
from ai.conversational_context.context_phraser import phrase_checkin_summary
from ai.fallback_responses.checkin_summary import try_checkin_summary_response


@pytest.mark.unit
@pytest.mark.ai
class TestContextAnalyticsSharedSource:
    """context_builder calculates; context_phraser phrases from ContextAnalysis."""

    @pytest.fixture
    def sample_checkins(self):
        return [
            {"ate_breakfast": True, "mood": 4, "energy": 3, "brushed_teeth": True},
            {"ate_breakfast": False, "mood": 3, "energy": 4, "brushed_teeth": True},
            {"ate_breakfast": True, "mood": 5, "energy": 5, "brushed_teeth": False},
        ]

    def test_phrase_checkin_summary_uses_analysis_counts_not_recomputed(
        self, sample_checkins
    ):
        builder = ContextBuilder()
        analysis = builder.analyze_context(
            ContextData(recent_checkins=sample_checkins)
        )

        assert analysis.total_entries == 3
        assert analysis.breakfast_count == 2
        assert analysis.teeth_brushed_count == 2
        assert abs(analysis.breakfast_rate - 66.67) < 0.1

        text = phrase_checkin_summary(analysis, sample_checkins)

        assert "2 out of 3 times" in text
        assert "66%" in text or "67%" in text
        assert "average mood has been 4.0" in text
        assert "Most recent check-ins:" in text

    def test_empty_checkins_phrased_consistently(self):
        builder = ContextBuilder()
        analysis = builder.analyze_context(ContextData(recent_checkins=[]))

        assert analysis.total_entries == 0
        assert phrase_checkin_summary(analysis, []) == (
            "They have not completed any check-ins yet."
        )

    def test_analyze_recent_checkin_rows_matches_analyze_context(self, sample_checkins):
        builder = ContextBuilder()
        via_context_data = builder.analyze_context(
            ContextData(recent_checkins=sample_checkins)
        )
        via_helper = analyze_recent_checkin_rows(sample_checkins)
        assert via_context_data.total_entries == via_helper.total_entries
        assert via_context_data.breakfast_count == via_helper.breakfast_count
        assert via_context_data.breakfast_rate == pytest.approx(via_helper.breakfast_rate)
        assert via_context_data.avg_mood == via_helper.avg_mood
        assert via_context_data.avg_energy == via_helper.avg_energy

    def test_try_checkin_summary_uses_canonical_breakfast_rate(self, sample_checkins):
        analysis = analyze_recent_checkin_rows(sample_checkins)
        text, _category = try_checkin_summary_response("did i eat breakfast", analysis, "")
        assert "66" in text or "67" in text
        assert analysis.breakfast_count == 2
        assert analysis.total_entries == 3
