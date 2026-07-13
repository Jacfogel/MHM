"""
Confirm conversational phrasing uses the same check-in analytics as ai.context.analytics.
"""

import pytest

from ai.context.analytics import ContextAnalysis, analyze_checkin_entries
from ai.context.phraser import phrase_checkin_summary
from ai.fallback.checkin_summary import try_checkin_summary_response


@pytest.mark.unit
@pytest.mark.ai
class TestContextAnalyticsSharedSource:
    """analytics calculates; context_phraser phrases from ContextAnalysis."""

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
        analysis = analyze_checkin_entries(sample_checkins)

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
        analysis = analyze_checkin_entries([])
        assert analysis.total_entries == 0
        assert phrase_checkin_summary(analysis, []) == (
            "They have not completed any check-ins yet."
        )

    def test_analyze_checkin_entries_is_canonical_entry_point(self, sample_checkins):
        direct = analyze_checkin_entries(sample_checkins)
        assert direct.total_entries == 3
        assert direct.breakfast_count == 2

    def test_try_checkin_summary_uses_canonical_breakfast_rate(self, sample_checkins):
        analysis = analyze_checkin_entries(sample_checkins)
        text, _category = try_checkin_summary_response("did i eat breakfast", analysis, "")
        assert "66" in text or "67" in text
        assert analysis.breakfast_count == 2
        assert analysis.total_entries == 3

    def test_try_checkin_summary_does_not_match_breakfast_inside_other_words(self):
        analysis = ContextAnalysis(total_entries=3, breakfast_rate=80.0)
        result = try_checkin_summary_response("tell me lately", analysis, "")
        assert result is None

    def test_try_checkin_summary_mood_branches(self):
        from ai.fallback.categories import FallbackCategory

        positive = ContextAnalysis(
            total_entries=5,
            avg_mood=4.5,
            avg_energy=4.2,
        )
        text, category = try_checkin_summary_response("how is my mood lately", positive, "Hi. ")
        assert category == FallbackCategory.CHECKIN_SUMMARY
        assert "4.5" in text

        low = ContextAnalysis(total_entries=5, avg_mood=1.5, avg_energy=2.0)
        text, category = try_checkin_summary_response("how have i been feeling", low, "")
        assert "challenging" in text.lower() or "1.5" in text

    def test_try_checkin_summary_progress_and_frequency(self):
        from ai.fallback.categories import FallbackCategory

        analysis = ContextAnalysis(
            total_entries=10,
            breakfast_count=8,
            breakfast_rate=80.0,
            avg_mood=4.0,
            avg_energy=3.5,
        )
        text, category = try_checkin_summary_response("how am i doing recently", analysis, "")
        assert category == FallbackCategory.CHECKIN_SUMMARY
        assert "good work" in text.lower() or "well" in text.lower()

        text, category = try_checkin_summary_response(
            "how many times was my mood recorded", analysis, ""
        )
        assert "4.0/5" in text or "average mood" in text.lower()

        missing_mood = ContextAnalysis(total_entries=3, avg_mood=None)
        text, category = try_checkin_summary_response("how many times mood", missing_mood, "")
        assert category == FallbackCategory.DATA_UNAVAILABLE

    def test_try_checkin_summary_weak_progress_uses_health_guidance(self):
        from ai.fallback.categories import FallbackCategory

        analysis = ContextAnalysis(
            total_entries=5,
            breakfast_rate=40.0,
            avg_mood=2.5,
            avg_energy=2.0,
        )
        health_summary = (
            "Health personalization (wellness-oriented, not medical): "
            "Recent rest and recovery patterns suggest a gentler day; "
            "keep expectations smaller. "
            "Never diagnose, cite wearables, or suggest medical treatment."
        )
        text, category = try_checkin_summary_response(
            "how am i doing",
            analysis,
            "Julie, ",
            health_guidance_summary=health_summary,
        )
        assert category == FallbackCategory.CHECKIN_SUMMARY
        assert "gentler day" in text.lower()
        assert "2.5/5" in text
        assert "room for improvement" not in text.lower()

    def test_try_health_guidance_wellness_response_without_checkins(self):
        from ai.fallback.categories import FallbackCategory
        from ai.fallback.checkin_summary import try_health_guidance_wellness_response

        health_summary = (
            "Health personalization (wellness-oriented, not medical): "
            "Light movement like a short walk or stretch may feel good if they choose. "
            "Never diagnose, cite wearables, or suggest medical treatment."
        )
        text, category = try_health_guidance_wellness_response(
            "how am i doing",
            "Julie, ",
            health_summary,
        )
        assert category == FallbackCategory.CHECKIN_SUMMARY
        assert "short walk" in text.lower()

    def test_try_checkin_summary_weak_progress_uses_partial_checkin_metrics(self):
        from ai.fallback.categories import FallbackCategory

        analysis = ContextAnalysis(
            total_entries=5,
            breakfast_rate=30.0,
            avg_mood=None,
            avg_energy=2.5,
        )
        text, category = try_checkin_summary_response("how am i doing", analysis, "Julie, ")
        assert category == FallbackCategory.CHECKIN_SUMMARY
        assert "2.5/5" in text
        assert "room for improvement" not in text.lower()
