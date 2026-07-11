"""Unit tests for honest wellness-status replies."""

from ai.chat.wellness_status import (
    build_honest_wellness_status_reply,
    context_has_wellness_data,
    is_wellness_status_question,
    reinforce_wellness_honesty_if_needed,
)


def test_is_wellness_status_question_matches_common_phrases():
    assert is_wellness_status_question("How am I doing?")
    assert is_wellness_status_question("How have I been doing lately?")
    assert not is_wellness_status_question("What can you do?")


def test_context_has_wellness_data_requires_checkins_or_mood():
    assert not context_has_wellness_data({})
    assert not context_has_wellness_data({"recent_activity": {"recent_responses_count": 0}})
    assert context_has_wellness_data(
        {"recent_activity": {"recent_responses_count": 2}}
    )
    assert context_has_wellness_data({"mood_trends": {"average_mood": 3.5}})


def test_build_honest_wellness_status_reply_without_data():
    reply = build_honest_wellness_status_reply({})
    assert "don't have" in reply.lower()
    assert "check-in" in reply.lower() or "check-ins" in reply.lower()


def test_build_honest_wellness_status_reply_with_mood_data():
    reply = build_honest_wellness_status_reply(
        {"mood_trends": {"average_mood": 4.0, "trend": "improving"}}
    )
    assert "4.0" in reply
    assert "improving" in reply.lower()


def test_reinforce_wellness_honesty_replaces_generic_deflection():
    generic = "I'm doing well! How are you?"
    reply = reinforce_wellness_honesty_if_needed(
        "How am I doing?",
        generic,
        {},
    )
    assert "don't have" in reply.lower()
    assert "doing well" not in reply.lower()
