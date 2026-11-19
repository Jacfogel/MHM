"""Freshness and failure coverage for message-time health pulls."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from integrations.google_health import sync_manager as sync

pytestmark = [pytest.mark.unit, pytest.mark.integrations]


@pytest.mark.parametrize(
    "state,expected_calls,expected_result",
    [
        ({}, 1, True),
        ({"last_success_at": "2026-11-18 12:56:00"}, 0, True),
        ({"last_success_at": "2026-11-18 12:55:00"}, 1, True),
        ({"last_sync_at": "2026-11-18 12:59:00", "last_error": "offline"}, 0, False),
        ({"last_success_at": "invalid"}, 1, True),
        ({"last_success_at": "2026-11-18 14:00:00"}, 1, True),
    ],
)
def test_message_refresh_freshness(state, expected_calls, expected_result):
    with (
        patch.object(sync, "GOOGLE_HEALTH_ENABLED", True),
        patch.object(sync, "is_google_health_testing_mode", return_value=False),
        patch("core.health_signals.health_personalization_allowed", return_value=True),
        patch.object(sync, "load_sync_state", return_value=state),
        patch.object(sync, "now_datetime_full", return_value=datetime(2026, 11, 18, 13)),
        patch.object(sync, "sync_user_health_data", return_value=True) as pull,
    ):
        assert sync.refresh_health_for_message("user") is expected_result
        assert pull.call_count == expected_calls


@pytest.mark.parametrize("enabled,testing,allowed", [(False, False, True), (True, True, True), (True, False, False)])
def test_message_refresh_respects_guards(enabled, testing, allowed):
    with (
        patch.object(sync, "GOOGLE_HEALTH_ENABLED", enabled),
        patch.object(sync, "is_google_health_testing_mode", return_value=testing),
        patch("core.health_signals.health_personalization_allowed", return_value=allowed),
        patch.object(sync, "sync_user_health_data") as pull,
    ):
        assert sync.refresh_health_for_message("user") is False
        pull.assert_not_called()


@pytest.mark.parametrize("failed", [False, True])
def test_ai_message_refreshes_before_reading_context(failed):
    from ai.chat.chatbot import AIChatBotSingleton

    bot = object.__new__(AIChatBotSingleton)
    bot.openai_available = True
    bot.response_cache = MagicMock()
    bot.response_cache.get.return_value = "generated message"
    events = []
    with (
        patch("ai.chat.chatbot.is_ai_usage_allowed", return_value=True),
        patch.object(sync, "refresh_health_for_message", side_effect=lambda _: events.append("pull") or not failed),
        patch("core.health_context_builder.build_personalized_google_health_context", side_effect=lambda _: events.append("context") or "recent sleep"),
    ):
        assert bot.generate_personalized_message("user", source="google_health") == "generated message"
    assert events == ["pull", "context"]


def test_fallback_reads_health_after_failed_refresh():
    from ai.fallback.personalized import build_personalized_message

    events = []
    with (
        patch("ai.fallback.data_access.get_user_data", return_value={}),
        patch.object(sync, "refresh_health_for_message", side_effect=lambda _: events.append("pull") or False),
        patch("core.health_signals.health_personalization_allowed", return_value=True),
        patch("core.health_context_builder.build_user_facing_signal_wellness_snippet", side_effect=lambda _: events.append("context") or "You slept about 7 hours."),
    ):
        message, _ = build_personalized_message("user", source="google_health")
    assert events == ["pull", "context"]
    assert "7 hours" in message
