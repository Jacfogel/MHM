"""Tests for canonical AI context envelope construction."""

from __future__ import annotations

import pytest

from ai.context.service import AIContextEnvelope, AIContextSection, build_ai_context_envelope
from tests.test_helpers.test_utilities import TestUserFactory


pytestmark = [pytest.mark.unit, pytest.mark.ai]


def _section(name: str, data):
    return AIContextSection(name=name, data=data)


def test_envelope_structured_sections_expose_context_fields():
    envelope = AIContextEnvelope(
        metadata={"user_id": "user-1", "current_timestamp": "2026-07-01 09:30:00"},
        sections={
            "account": _section("account", {"preferred_name": "Julie"}),
            "preferences": _section(
                "preferences",
                {"categories": ["motivational"], "channel": {"type": "discord"}},
            ),
            "personal_context": _section(
                "personal_context",
                {"notes_for_ai": ["Keep it direct"], "goals": ["Finish project"]},
            ),
            "schedules": _section(
                "schedules",
                {"active_schedules": ["Morning Check-in"]},
            ),
            "checkins": _section("checkins", {"recent": [{"mood": 4}]}),
            "conversation": _section(
                "conversation",
                {"recent_chat_interactions": [{"user_message": "hello"}]},
            ),
        },
    )
    structured = envelope.structured

    assert structured["account"]["preferred_name"] == "Julie"
    assert structured["preferences"]["categories"] == ["motivational"]
    assert structured["personal_context"]["goals"] == ["Finish project"]
    assert structured["schedules"]["active_schedules"] == ["Morning Check-in"]
    assert structured["checkins"]["recent"] == [{"mood": 4}]
    assert structured["conversation"]["recent_chat_interactions"] == [
        {"user_message": "hello"}
    ]


def test_build_ai_context_envelope_records_requested_intent(test_data_dir):
    user_id = "envelope-intent-user"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

    envelope = build_ai_context_envelope(
        user_id,
        include_conversation_history=False,
        requested_intent="unit_test_intent",
    )

    assert envelope is not None
    assert envelope.metadata["requested_intent"] == "unit_test_intent"
    assert envelope.metadata["user_id"] == user_id
