"""Unit tests for honest wellness-status replies."""

import pytest

from ai.chat.wellness_status import (
    build_honest_wellness_status_reply,
    context_has_wellness_data,
    is_wellness_status_question,
    reinforce_wellness_honesty_if_needed,
)


@pytest.mark.unit
@pytest.mark.ai
def test_is_wellness_status_question_matches_common_phrases():
    assert is_wellness_status_question("How am I doing?")
    assert is_wellness_status_question("How have I been doing lately?")
    assert not is_wellness_status_question("What can you do?")


@pytest.mark.unit
@pytest.mark.ai
def test_context_has_wellness_data_requires_checkins_or_mood():
    assert not context_has_wellness_data({})
    assert not context_has_wellness_data({"recent_activity": {"recent_responses_count": 0}})
    assert context_has_wellness_data(
        {"recent_activity": {"recent_responses_count": 2}}
    )
    assert context_has_wellness_data({"mood_trends": {"average_mood": 3.5}})


@pytest.mark.unit
@pytest.mark.ai
def test_context_has_wellness_data_includes_health_guidance():
    assert context_has_wellness_data(
        {
            "health_guidance_summary": (
                "Health personalization (wellness-oriented, not medical): "
                "Recent rest and recovery patterns suggest a gentler day; "
                "keep expectations smaller. "
                "Never diagnose, cite wearables, or suggest medical treatment."
            )
        }
    )


@pytest.mark.unit
@pytest.mark.ai
def test_build_honest_wellness_status_reply_without_data():
    reply = build_honest_wellness_status_reply({})
    assert "don't have" in reply.lower()
    assert "check-in" in reply.lower() or "check-ins" in reply.lower()


@pytest.mark.unit
@pytest.mark.ai
def test_build_honest_wellness_status_reply_with_health_only():
    reply = build_honest_wellness_status_reply(
        {
            "user_profile": {"preferred_name": "Julie"},
            "health_guidance_summary": (
                "Health personalization (wellness-oriented, not medical): "
                "Recent rest and recovery patterns suggest a gentler day; "
                "keep expectations smaller. "
                "Never diagnose, cite wearables, or suggest medical treatment."
            ),
        }
    )
    assert "Julie" in reply
    assert "gentler day" in reply.lower()
    assert "room for improvement" not in reply.lower()


@pytest.mark.unit
@pytest.mark.ai
def test_build_honest_wellness_status_reply_combines_mood_and_health():
    reply = build_honest_wellness_status_reply(
        {
            "mood_trends": {"average_mood": 3.2, "trend": "stable"},
            "health_guidance_summary": (
                "Health personalization (wellness-oriented, not medical): "
                "Small resets (water, food, breathing, brief rest) are more "
                "appropriate than big pushes. "
                "Never diagnose, cite wearables, or suggest medical treatment."
            ),
        }
    )
    assert "3.2" in reply
    assert "small resets" in reply.lower()


@pytest.mark.unit
@pytest.mark.ai
def test_build_honest_wellness_status_reply_with_mood_data():
    reply = build_honest_wellness_status_reply(
        {"mood_trends": {"average_mood": 4.0, "trend": "improving"}}
    )
    assert "4.0" in reply
    assert "improving" in reply.lower()


@pytest.mark.unit
@pytest.mark.ai
def test_reinforce_wellness_honesty_replaces_generic_deflection():
    generic = "I'm doing well! How are you?"
    reply = reinforce_wellness_honesty_if_needed(
        "How am I doing?",
        generic,
        {},
    )
    assert "don't have" in reply.lower()
    assert "doing well" not in reply.lower()
