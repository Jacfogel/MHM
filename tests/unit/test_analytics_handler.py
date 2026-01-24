"""Unit tests for analytics_command handler helpers."""

import pytest

from communication.command_handlers.analytics_handler import (
    AnalyticsHandler,
    InteractionResponse,
    ParsedCommand,
)


class _FakeCheckinAnalytics:
    def __init__(self, mood_data):
        self._mood_data = mood_data

    def get_mood_trends(self, *args, **kwargs):
        return self._mood_data


@pytest.mark.unit
def test_can_handle_known_intent():
    handler = AnalyticsHandler()

    assert handler.can_handle("mood_trends")
    assert handler.can_handle("show_analytics")
    assert not handler.can_handle("unknown_intent")


@pytest.mark.unit
def test_handle_returns_default_for_unknown_intent(monkeypatch):
    handler = AnalyticsHandler()
    parsed = ParsedCommand(
        intent="unknown_intent", entities={}, confidence=0.1, original_message="unknown"
    )
    monkeypatch.setattr(
        handler,
        "get_examples",
        lambda: ["example intent"],
    )

    response = handler.handle("user_x", parsed)

    assert isinstance(response, InteractionResponse)
    assert "I don't understand" in response.message
    assert "example intent" in response.message


@pytest.mark.unit
def test_handle_mood_trends_includes_trend_and_distribution(monkeypatch):
    handler = AnalyticsHandler()
    mood_payload = {
        "average_mood": 4,
        "min_mood": 2,
        "max_mood": 5,
        "trend": "improving",
        "mood_distribution": {"Happy": 3, "Okay": 2},
        "insights": ["insight one", "insight two"],
    }
    monkeypatch.setenv("MHM_TESTING", "1")
    monkeypatch.setattr(
        "core.checkin_analytics.CheckinAnalytics",
        lambda *args, **kwargs: _FakeCheckinAnalytics(mood_payload),
    )

    response = handler._handle_mood_trends("user_x", {"days": 7})

    assert isinstance(response, InteractionResponse)
    assert "Mood Trends" in response.message
    assert "Average Mood" in response.message
    assert "Mood Distribution" in response.message
    assert "insight one" in response.message


@pytest.mark.unit
def test_get_field_scale_and_truncate_response():
    handler = AnalyticsHandler()

    assert handler._get_field_scale("mood") == 5
    assert handler._get_field_scale("sleep_hours") is None

    response = "line1\n" + ("x" * 2000) + "\nline2"
    truncated = handler._truncate_response(response, max_length=100)

    assert truncated.endswith("...")
    assert len(truncated) <= 100
