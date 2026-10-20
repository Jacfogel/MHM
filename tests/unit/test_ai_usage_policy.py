"""Unit tests for centralized optional-AI execution controls."""

from unittest.mock import patch

import pytest

from ai.client.lm_studio_client import complete_lm_studio_chat
from ai.usage_policy import (
    AIUsageFeature,
    AIUsageMode,
    get_ai_usage_mode,
    get_disabled_ai_features,
    is_ai_usage_allowed,
    usage_feature_for_response_mode,
    _normalized_token,
)
from core import config


@pytest.mark.unit
@pytest.mark.ai
class TestAIUsagePolicy:
    """AI calls obey global and feature-level configuration."""

    def test_automatic_mode_allows_features_by_default(self):
        with (
            patch.object(config, "AI_USAGE_MODE", "automatic"),
            patch.object(config, "AI_DISABLED_FEATURES", ""),
        ):
            assert get_ai_usage_mode() is AIUsageMode.AUTOMATIC
            assert is_ai_usage_allowed(AIUsageFeature.CONVERSATION) is True

    def test_off_mode_blocks_every_feature(self):
        with (
            patch.object(config, "AI_USAGE_MODE", "off"),
            patch.object(config, "AI_DISABLED_FEATURES", ""),
        ):
            assert is_ai_usage_allowed(AIUsageFeature.CONVERSATION) is False
            assert is_ai_usage_allowed(AIUsageFeature.TASK_BREAKDOWN) is False

    def test_disabled_features_are_normalized_and_blocked(self):
        with (
            patch.object(config, "AI_USAGE_MODE", "automatic"),
            patch.object(
                config,
                "AI_DISABLED_FEATURES",
                "Conversation, task-breakdown",
            ),
        ):
            assert get_disabled_ai_features() == {
                "conversation",
                "task_breakdown",
            }
            assert is_ai_usage_allowed(AIUsageFeature.CONVERSATION) is False
            assert is_ai_usage_allowed(AIUsageFeature.TASK_BREAKDOWN) is False
            assert is_ai_usage_allowed(AIUsageFeature.TASK_EFFORT) is True

    def test_response_modes_map_to_separate_feature_controls(self):
        assert (
            usage_feature_for_response_mode("chat")
            is AIUsageFeature.CONVERSATION
        )
        assert (
            usage_feature_for_response_mode("command_with_clarification")
            is AIUsageFeature.COMMAND_INTERPRETATION
        )
        assert (
            usage_feature_for_response_mode("personalized")
            is AIUsageFeature.PERSONALIZED_MESSAGES
        )
        assert (
            usage_feature_for_response_mode("response_enhancement")
            is AIUsageFeature.RESPONSE_ENHANCEMENT
        )

    def test_low_level_client_skips_http_when_feature_is_disabled(self):
        with (
            patch.object(config, "AI_USAGE_MODE", "automatic"),
            patch.object(config, "AI_DISABLED_FEATURES", "conversation"),
            patch("ai.client.lm_studio_client.requests.post") as request,
        ):
            result = complete_lm_studio_chat(
                [{"role": "user", "content": "Hello"}],
                usage_feature=AIUsageFeature.CONVERSATION,
            )

        assert result.text is None
        assert result.failure == "AI usage disabled for feature: conversation"
        request.assert_not_called()

    def test_invalid_mode_fails_closed(self):
        with patch.object(config, "AI_USAGE_MODE", "unexpected"):
            assert get_ai_usage_mode() is AIUsageMode.OFF
            assert is_ai_usage_allowed() is False

    def test_token_normalization_fails_closed_on_unexpected_objects(self):
        class BrokenToken:
            def __str__(self):
                raise RuntimeError("broken token")

        assert _normalized_token(BrokenToken()) == ""


@pytest.mark.unit
@pytest.mark.core
class TestAIUsageConfigurationValidation:
    """Configuration validation catches unusable policy values."""

    def test_invalid_usage_mode_is_an_error(self):
        with patch.object(config, "AI_USAGE_MODE", "sometimes"):
            valid, errors, _warnings = config.validate_ai_configuration()

        assert valid is False
        assert "AI_USAGE_MODE must be one of: automatic, off" in errors

    def test_unknown_disabled_feature_is_a_warning(self):
        with patch.object(config, "AI_DISABLED_FEATURES", "conversation, mystery"):
            _valid, _errors, warnings = config.validate_ai_configuration()

        assert any("mystery" in warning for warning in warnings)

    def test_off_mode_does_not_require_model_connection_settings(self):
        with (
            patch.object(config, "AI_USAGE_MODE", "off"),
            patch.object(config, "LM_STUDIO_BASE_URL", ""),
            patch.object(config, "LM_STUDIO_API_KEY", ""),
            patch.object(config, "LM_STUDIO_MODEL", ""),
        ):
            valid, errors, warnings = config.validate_ai_configuration()

        assert valid is True
        assert not any("LM_STUDIO" in error for error in errors)
        assert not any("LM_STUDIO" in warning for warning in warnings)

