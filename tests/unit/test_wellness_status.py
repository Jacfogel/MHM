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


@pytest.mark.unit
@pytest.mark.ai
def test_reinforce_wellness_honesty_replaces_template_reply_with_real_data():
    reply = reinforce_wellness_honesty_if_needed(
        "How am I doing?",
        "You are at [current_date]. Your name is [preferred_name].",
        {"mood_trends": {"average_mood": 4.0, "trend": "stable"}},
    )
    assert "4.0" in reply
    assert "[current_date]" not in reply


@pytest.mark.unit
@pytest.mark.ai
def test_grounded_model_summary_keeps_energy_routines_and_follow_up():
    response = (
        "You’re doing fairly steady based on the recent check-ins.\n\n"
        "- Mood has averaged 4.0/5 over the last 3 check-ins and is staying stable.\n"
        "- Energy has averaged 3.0/5, which looks moderate.\n"
        "- Breakfast and brushing teeth were both done 3/3 times, so those routines are holding well.\n\n"
        "If you want, I can help you look for patterns around energy or make a small plan to support the lower-energy days."
    )
    context = {"recent_activity": {"recent_responses_count": 3},
               "mood_trends": {"average_mood": 4.0, "average_energy": 3.0, "trend": "stable"}}
    assert reinforce_wellness_honesty_if_needed("How am I doing?", response, context) == response


@pytest.mark.unit
@pytest.mark.ai
@pytest.mark.parametrize("response,context", [
    ("Your average mood is 5.0.", {"mood_trends": {"average_mood": 4.0}}),
    ("Energy has averaged 5.0/5.", {"mood_trends": {"average_mood": 4.0, "average_energy": 3.0}}),
    ("Your average mood is 4.0.", {"mood_trends": {"average_energy": 3.0}}),
])
def test_explicit_unverified_average_is_still_repaired(response, context):
    assert reinforce_wellness_honesty_if_needed("How am I doing?", response, context) == build_honest_wellness_status_reply(context)


@pytest.mark.unit
@pytest.mark.ai
def test_no_data_guard_still_rejects_fabricated_model_summary():
    response = "Your average mood is 4.0 and your sleep has improved."
    assert reinforce_wellness_honesty_if_needed("How am I doing?", response, {}) == build_honest_wellness_status_reply({})


@pytest.mark.unit
@pytest.mark.ai
def test_rounded_average_does_not_trigger_rewrite():
    reply = "Your average mood is around 3, with some variation between check-ins."
    assert reinforce_wellness_honesty_if_needed(
        "How am I doing?", reply, {"mood_trends": {"average_mood": 3.2}}
    ) == reply


@pytest.mark.unit
@pytest.mark.ai
def test_curly_apostrophe_generic_deflection_is_still_repaired():
    context = {"mood_trends": {"average_mood": 4.0}}
    assert reinforce_wellness_honesty_if_needed(
        "How am I doing?", "I’m doing well! How are you?", context
    ) == build_honest_wellness_status_reply(context)


@pytest.mark.unit
@pytest.mark.ai
def test_percentage_is_not_compared_directly_to_raw_score():
    reply = "Your average mood is 80% of the maximum score."
    assert reinforce_wellness_honesty_if_needed(
        "How am I doing?", reply, {"mood_trends": {"average_mood": 4.0}}
    ) == reply
