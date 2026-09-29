"""The local model is loaded with a 2048-token window."""

import pytest

from ai.client.lm_studio_client import fit_messages_to_context


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
    context = "[selected_user_context]\nThe user's preferred name is Julie.\n" + ("detail\n" * 800)
    messages = [
        {"role": "system", "content": ("rule\n" * 800) + context},
        {"role": "user", "content": "hi"},
    ]
    fitted = fit_messages_to_context(messages, 300)
    system = fitted[0]["content"]
    assert fitted[1]["content"] == "hi"
    assert len(system) + 2 < 4000
    assert "preferred name is Julie" in system
