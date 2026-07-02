"""Tests for ContextBuilder delegation to the canonical AI context envelope."""

from __future__ import annotations

from datetime import datetime

import pytest

from ai.context_builder import ContextBuilder, _context_data_from_ai_envelope
from ai.context_service import AIContextEnvelope, AIContextSection


pytestmark = [pytest.mark.unit, pytest.mark.ai]


def _section(name: str, data):
    return AIContextSection(name=name, data=data)


def test_context_data_adapter_preserves_legacy_shape_from_envelope():
    envelope = AIContextEnvelope(
        metadata={"user_id": "user-1"},
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

    context = _context_data_from_ai_envelope(
        envelope, current_time=datetime(2026, 7, 1, 9, 30, 0)
    )

    assert context.user_profile == {
        "preferred_name": "Julie",
        "active_categories": ["motivational"],
        "messaging_service": "discord",
        "active_schedules": ["Morning Check-in"],
    }
    assert context.user_context == {
        "notes_for_ai": ["Keep it direct"],
        "goals": ["Finish project"],
    }
    assert context.recent_checkins == [{"mood": 4}]
    assert context.conversation_history == [{"user_message": "hello"}]
    assert context.current_time == datetime(2026, 7, 1, 9, 30, 0)


def test_context_builder_build_user_context_uses_canonical_envelope(monkeypatch):
    envelope = AIContextEnvelope(
        metadata={"user_id": "user-1"},
        sections={
            "account": _section("account", {"preferred_name": "Julie"}),
            "preferences": _section("preferences", {}),
            "personal_context": _section("personal_context", {}),
            "schedules": _section("schedules", {}),
            "checkins": _section("checkins", {"recent": []}),
            "conversation": _section("conversation", {"recent_chat_interactions": []}),
        },
    )
    calls = []

    def _fake_build_envelope(user_id, **kwargs):
        calls.append((user_id, kwargs))
        return envelope

    monkeypatch.setattr(
        "ai.context_builder.build_ai_context_envelope", _fake_build_envelope
    )

    context = ContextBuilder().build_user_context(
        "user-1", include_conversation_history=False
    )

    assert context.user_profile["preferred_name"] == "Julie"
    assert calls == [
        (
            "user-1",
            {
                "include_conversation_history": False,
                "requested_intent": "context_builder_compat",
            },
        )
    ]
