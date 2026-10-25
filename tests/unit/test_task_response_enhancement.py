"""Task reminder actions must preserve their deterministic handler responses."""

from unittest.mock import Mock, patch

import pytest

from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from communication.message_processing.response_enhancer import enhance_response_with_ai


@pytest.mark.unit
@pytest.mark.parametrize(
    "intent", ["snooze_task_reminder", "skip_task_occurrence", "simplify_task", "continue_checkin"]
)
@pytest.mark.parametrize("completed", [False, True])
def test_task_reminder_responses_are_preserved_when_ai_is_offline(intent, completed):
    response = InteractionResponse(
        "When should I remind you about **Call dentist**?",
        completed,
        rich_data={"interaction_view": "task_snooze"},
    )
    command = ParsedCommand(intent=intent, entities={}, confidence=1.0, original_message="snooze task 1")
    chatbot = Mock()
    chatbot.generate_response.return_value = "I'm offline for AI chat right now. Actions: ..."

    with patch(
        "communication.message_processing.response_enhancer.is_ai_usage_allowed",
        return_value=True,
    ):
        result = enhance_response_with_ai(
            "user-1", response, command, ai_chatbot=chatbot, enable_ai_enhancement=True
        )

    assert result is response
    assert result.message == "When should I remind you about **Call dentist**?"
    assert result.rich_data == {"interaction_view": "task_snooze"}
    chatbot.generate_response.assert_not_called()


@pytest.mark.unit
def test_unavailable_enhancement_does_not_generate_chat_fallback():
    from ai.chat.chatbot import _text_when_model_is_unavailable

    with patch("ai.chat.chatbot.get_fallback_responses") as fallback:
        assert _text_when_model_is_unavailable(
            "response_enhancement", "Internal context and action catalog", "user-1"
        ) == ""
    fallback.assert_not_called()
