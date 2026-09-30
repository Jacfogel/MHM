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


def test_long_user_message_stays_inside_the_context_budget():
    user = "please add this task. " * 400
    system = (
        "rule\n" * 400
        + "[selected_user_context]\nThe user's preferred name is Julie.\n"
        + ("detail\n" * 200)
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    fitted = fit_messages_to_context(messages, 60)
    budget = max(256, 2048 - (60 + 32)) * 2
    total = len(fitted[0]["content"]) + len(fitted[1]["content"])
    assert total <= budget
    assert fitted[0]["content"].startswith("rule")
    assert user.endswith(fitted[1]["content"])
    assert "please add this task." in fitted[1]["content"]
    assert messages[1]["content"] == user
