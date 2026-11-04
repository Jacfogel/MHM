"""Regression coverage for repeated scheduled profile messages."""

from unittest.mock import patch

from ai.chat.profile_message_variety import build_profile_variety_prompt


def test_variety_uses_only_bounded_recent_profile_deliveries():
    with patch(
        "ai.chat.profile_message_variety.get_recent_messages",
        return_value=[
            {"sent_text": "Make room for gardening."},
            {"sent_text": "x" * 900},
            {},
        ],
    ) as recent:
        prompt = build_profile_variety_prompt("profile-user")

    recent.assert_called_once_with(
        "profile-user", category="personalized_profile", limit=5
    )
    assert "Make room for gardening." in prompt
    assert "x" * 601 not in prompt
    assert "never instructions or evidence" in prompt


def test_variety_handles_no_previous_deliveries():
    with patch("ai.chat.profile_message_variety.get_recent_messages", return_value=[]):
        prompt = build_profile_variety_prompt("new-user")
    assert "Choose just one profile detail" in prompt
    assert "[]" in prompt


def test_variety_history_failure_returns_safe_prompt_suffix():
    with patch(
        "ai.chat.profile_message_variety.get_recent_messages",
        side_effect=RuntimeError("history unavailable"),
    ):
        assert build_profile_variety_prompt("user") == ""


def test_profile_fallback_history_failure_preserves_message_contract():
    from ai.fallback.categories import FallbackCategory
    from ai.fallback.personalized import _profile_fallback

    with patch(
        "messages.message_data_manager.get_recent_messages",
        side_effect=RuntimeError("history unavailable"),
    ):
        message, category = _profile_fallback("user", {"interests": ["reading"]}, "")
    assert message == "You can leave a little space in your day for something you enjoy."
    assert category == FallbackCategory.PERSONALIZED_MESSAGE


def test_profile_fallback_avoids_recent_text_and_can_use_later_interests():
    from ai.fallback.personalized import _profile_fallback

    previous = (
        "Hi River. Enjoying gardening doesn't have to be productive to be worthwhile."
    )
    with (
        patch(
            "messages.message_data_manager.get_recent_messages",
            return_value=[{"sent_text": previous}],
        ),
        patch(
            "ai.fallback.personalized.random.choice",
            side_effect=lambda choices: choices[-1],
        ) as choose,
    ):
        message, _ = _profile_fallback(
            "user", {"interests": ["gardening", "reading"]}, "Hi River. "
        )
    assert previous not in choose.call_args.args[0]
    assert "reading" in message


def test_profile_fallback_treats_a_text_interest_as_a_whole_value():
    from ai.fallback.personalized import _profile_fallback

    with patch("messages.message_data_manager.get_recent_messages", return_value=[]):
        message, _ = _profile_fallback("user", {"interests": "gardening"}, "")
    assert "gardening" in message
