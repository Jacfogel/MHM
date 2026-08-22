"""Contract tests for the shared check-in analysis core."""

from __future__ import annotations

import pytest

from checkins.analysis import (
    CheckinAnalysis,
    analyze_checkin_entries,
    format_wellness_score_report,
)
from checkins.checkin_analytics import CheckinAnalytics


pytestmark = [pytest.mark.unit, pytest.mark.checkins, pytest.mark.analytics]


def _rows() -> list[dict]:
    return [
        {
            "ate_breakfast": True,
            "mood": 4,
            "energy": 3,
            "brushed_teeth": True,
            "responses": {
                "ate_breakfast": True,
                "mood": 4,
                "energy": 3,
                "brushed_teeth": True,
            },
            "questions_asked": ["ate_breakfast", "mood", "energy", "brushed_teeth"],
        },
        {
            "ate_breakfast": False,
            "mood": 3,
            "energy": 4,
            "brushed_teeth": True,
            "responses": {
                "ate_breakfast": False,
                "mood": 3,
                "energy": 4,
                "brushed_teeth": True,
            },
            "questions_asked": ["ate_breakfast", "mood", "energy", "brushed_teeth"],
        },
        {
            "ate_breakfast": True,
            "mood": 5,
            "energy": 5,
            "brushed_teeth": False,
            "responses": {
                "ate_breakfast": True,
                "mood": 5,
                "energy": 5,
                "brushed_teeth": False,
            },
            "questions_asked": ["ate_breakfast", "mood", "energy", "brushed_teeth"],
        },
    ]


def test_analyze_checkin_entries_matches_wellness_report_for_same_rows():
    rows = _rows()
    analysis = analyze_checkin_entries(rows)
    report = format_wellness_score_report(analysis, period_days=7)

    assert isinstance(analysis, CheckinAnalysis)
    assert abs(analysis.breakfast_rate - 66.67) < 0.1
    assert analysis.avg_mood == 4.0
    assert analysis.avg_energy == 4.0
    assert report["score"] == round(analysis.overall_wellness_score, 1)
    assert report["level"] == analysis.wellness_level
    assert report["components"]["mood_score"] == round(analysis.mood_score or 0, 1)


def test_checkin_analytics_wellness_uses_shared_analysis(monkeypatch):
    rows = _rows()
    analytics = CheckinAnalytics()
    monkeypatch.setattr(
        "checkins.checkin_analytics.get_checkins_by_days",
        lambda user_id, days: rows,
    )

    result = analytics.get_wellness_score("user-1", days=7)
    analysis = analyze_checkin_entries(rows)

    assert "error" not in result
    assert result["score"] == round(analysis.overall_wellness_score, 1)
    assert result["level"] == analysis.wellness_level
    assert result["components"]["mood_score"] == round(analysis.mood_score or 0, 1)
    assert result["components"]["habit_score"] == round(analysis.habit_score or 0, 1)
    assert "sleep_score" not in result["components"]
