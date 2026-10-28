"""Prompts respect the configurable application budget without local-model limits."""

import pytest
from core.config import AI_CONTEXT_TOKENS

from ai.client.openai_client import fit_messages_to_context


pytestmark = [pytest.mark.unit, pytest.mark.ai]


def test_short_messages_are_left_unchanged():
    messages = [
        {"role": "system", "content": "You are MHM."},
        {"role": "user", "content": "hi"},
    ]
    fitted = fit_messages_to_context(messages, 80)
    assert fitted[1]["content"] == "hi"
    assert fitted[0]["content"] == "You are MHM."
    assert messages[0]["content"] == "You are MHM."


def test_long_system_prompt_keeps_the_user_message_and_context_start():
    context = "[selected_user_context]\nThe user's preferred name is Julie.\n" + ("detail\n" * 8000)
    messages = [
        {"role": "system", "content": ("rule\n" * 8000) + context},
        {"role": "user", "content": "hi"},
    ]
    fitted = fit_messages_to_context(messages, 300)
    system = fitted[0]["content"]
    assert fitted[1]["content"] == "hi"
    assert len(system) + 2 <= (AI_CONTEXT_TOKENS - 332) * 2
    assert "preferred name is Julie" in system


def test_long_user_message_stays_inside_the_context_budget():
    user = "please add this task. " * 4000
    system = (
        "rule\n" * 4000
        + "[selected_user_context]\nThe user's preferred name is Julie.\n"
        + ("detail\n" * 200)
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    fitted = fit_messages_to_context(messages, 60)
    budget = max(256, AI_CONTEXT_TOKENS - (60 + 32)) * 2
    total = len(fitted[0]["content"]) + len(fitted[1]["content"])
    assert total <= budget
    assert fitted[0]["content"].startswith("rule")
    assert user.endswith(fitted[1]["content"])
    assert "please add this task." in fitted[1]["content"]
    assert messages[1]["content"] == user
