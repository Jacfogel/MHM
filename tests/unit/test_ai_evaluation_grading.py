"""Regression cases observed during review of the functionality suite."""

import pytest

from tests.ai.ai_response_validator import AIResponseValidator

pytestmark = [pytest.mark.unit, pytest.mark.ai]


@pytest.mark.parametrize(
    "prompt", ["How are you?", "Hello, how are you?", "How are you feeling?"]
)
def test_user_assessment_does_not_answer_question_about_assistant(prompt):
    response = (
        "I don't have enough information about how you're doing today, "
        "but we can figure it out together! How are you feeling right now?"
    )
    assert (
        AIResponseValidator.validate_response(response, prompt, "chat")["status"]
        == "FAIL"
    )


@pytest.mark.parametrize(
    "prompt", ["Tell me about yourself", "Tell me about your capabilities"]
)
def test_intake_does_not_describe_assistant(prompt):
    response = (
        "I'm here to listen and support you! Since we're just getting started, "
        "I'd love to learn more about you. How are you feeling right now?"
    )
    assert (
        AIResponseValidator.validate_response(response, prompt, "chat")["status"]
        == "FAIL"
    )


def test_thanks_does_not_provide_requested_help():
    result = AIResponseValidator.validate_response(
        "You're very welcome! I'm glad I could help. Keep up the great work!",
        "Tell me something helpful",
        "chat",
    )
    assert result["status"] == "FAIL"


@pytest.mark.parametrize(
    "prompt,response",
    [
        ("How are you?", "I'm ready to chat. Thanks for asking!"),
        (
            "Tell me about your capabilities",
            "I'm MHM's assistant. I can help manage tasks and check-ins.",
        ),
        (
            "Tell me something helpful",
            "Write down one small next step so it is easier to start.",
        ),
        (
            "How am I doing?",
            "I don't have enough information about how you're doing today. Tell me about your day.",
        ),
    ],
)
def test_relevant_answers_are_not_rejected(prompt, response):
    assert (
        AIResponseValidator.validate_response(response, prompt, "chat")["status"]
        == "PASS"
    )


@pytest.mark.parametrize(
    "response",
    [
        'Switch to "good enough" mode: choose a reasonable stopping point.',
        "A lantern glowed at the edge of the forest. " * 12,
    ],
)
def test_ordinary_advice_and_narratives_are_not_debug_artifacts(response):
    assert (
        AIResponseValidator.validate_response(
            response, "Tell me a short story", "chat"
        )["status"]
        == "PASS"
    )


def test_actual_mode_header_is_still_a_leak():
    assert (
        AIResponseValidator.validate_response("Mode: chat\nHello!", "Hello", "chat")[
            "status"
        ]
        == "FAIL"
    )
