"""
Unit tests for ai/fallback_responses.py boundary behavior.
"""

import pytest
from unittest.mock import patch

from ai.fallback_responses import FallbackResponses, get_fallback_responses
from ai.interaction_types import AIInteractionType, interaction_type_for_mode


FALSE_SUCCESS_PHRASES = (
    "i created",
    "i've created",
    "task has been added",
    "has been created",
    "successfully created",
    "i deleted",
    "i updated",
    "based on your recent data",
    "i noticed a pattern",
)


@pytest.mark.unit
@pytest.mark.ai
class TestInteractionTypes:
    """Test mode to interaction type mapping."""

    def test_interaction_type_for_chat_mode(self):
        assert interaction_type_for_mode("chat") == AIInteractionType.CONVERSATIONAL

    def test_interaction_type_for_command_mode(self):
        assert interaction_type_for_mode("command") == AIInteractionType.COMMAND_INTERPRETATION

    def test_interaction_type_for_clarification_mode(self):
        assert interaction_type_for_mode("command_with_clarification") == AIInteractionType.CLARIFICATION

    def test_interaction_type_for_none_defaults_to_conversational(self):
        assert interaction_type_for_mode(None) == AIInteractionType.CONVERSATIONAL


@pytest.mark.unit
@pytest.mark.ai
class TestFallbackResponses:
    """Test fallback response generation boundaries."""

    @pytest.fixture
    def fallback(self):
        return FallbackResponses()

    @patch("ai.fallback_responses.get_user_data", return_value={})
    @patch("ai.fallback_responses.get_recent_responses", return_value=[])
    def test_contextual_returns_non_empty_for_chat_like_prompt(
        self, _mock_recent, _mock_user_data, fallback
    ):
        response = fallback.contextual("I'm feeling overwhelmed today", user_id="user-test")
        assert response
        assert isinstance(response, str)
        assert len(response.strip()) > 0

    @patch("ai.fallback_responses.get_user_data", return_value={})
    @patch("ai.fallback_responses.get_recent_responses", return_value=[])
    def test_contextual_returns_non_empty_for_command_like_prompt(
        self, _mock_recent, _mock_user_data, fallback
    ):
        response = fallback.contextual("create task buy milk", user_id="user-test")
        assert response
        assert isinstance(response, str)

    @patch("ai.fallback_responses.get_user_data", return_value={})
    @patch("ai.fallback_responses.get_recent_responses", return_value=[])
    def test_contextual_does_not_claim_action_success(
        self, _mock_recent, _mock_user_data, fallback
    ):
        prompts = [
            "hello",
            "I'm stressed",
            "create task buy milk",
            "how am I doing",
            "remind me tomorrow",
        ]
        for prompt in prompts:
            response = fallback.contextual(prompt, user_id="user-test").lower()
            for phrase in FALSE_SUCCESS_PHRASES:
                assert phrase not in response, (
                    f"Fallback for '{prompt}' must not claim success: found '{phrase}'"
                )

    @patch("ai.fallback_responses.get_user_data", return_value={"context": {}})
    @patch("ai.fallback_responses.get_recent_responses", return_value=[])
    def test_personalized_returns_non_empty(self, _mock_recent, _mock_user_data, fallback):
        response = fallback.personalized("user-test")
        assert response
        assert len(response.strip()) > 0

    def test_get_fallback_responses_returns_singleton(self):
        assert get_fallback_responses() is get_fallback_responses()

    def test_personalize_with_profile_name_injects_name(self, fallback):
        result = fallback.personalize_with_profile_name(
            "Hello! How are you?",
            ["Active user"],
            {"preferred_name": "Alex"},
        )
        assert "Alex" in result
