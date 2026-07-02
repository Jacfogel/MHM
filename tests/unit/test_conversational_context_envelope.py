"""Tests for envelope-backed conversational prompt assembly."""

from __future__ import annotations

import pytest

from ai.context.service import AIContextEnvelope, AIContextSection
from ai.context.assembly import (
    assemble_comprehensive_messages,
    build_context_parts,
)


pytestmark = [pytest.mark.unit, pytest.mark.ai]


def _section(name: str, data):
    return AIContextSection(name=name, data=data)


def _envelope() -> AIContextEnvelope:
    return AIContextEnvelope(
        metadata={"user_id": "user-1"},
        sections={
            "account": _section("account", {"preferred_name": "Julie"}),
            "preferences": _section(
                "preferences",
                {"categories": ["motivational"], "channel": {"type": "discord"}},
            ),
            "personal_context": _section(
                "personal_context",
                {"notes_for_ai": ["Prefers direct wording"]},
            ),
            "schedules": _section("schedules", {"raw": {}, "active_schedules": []}),
            "tasks": _section(
                "tasks",
                {
                    "enabled": True,
                    "active": [{"title": "Call pharmacy"}],
                    "due_soon": [],
                    "stats": {"total_count": 1, "active_count": 1, "completed_count": 0},
                },
            ),
            "checkins": _section(
                "checkins",
                {"enabled": False, "recent": [], "latest": None, "daily_status": {}},
            ),
            "messages": _section(
                "messages",
                {
                    "enabled": True,
                    "recent_sent": [
                        {
                            "category": "motivational",
                            "sent_text": "Keep going.",
                            "sent_at": "2026-07-01 09:00:00",
                        }
                    ],
                },
            ),
            "health": _section("health", {"guidance_summary": ""}),
            "conversation": _section(
                "conversation",
                {"recent_chat_interactions": [{"user_message": "hello"}]},
            ),
        },
    )


def test_build_context_parts_phrases_from_supplied_envelope():
    parts = build_context_parts("ignored-user", envelope=_envelope())
    joined = "\n".join(parts)

    assert "Julie's" not in joined
    assert "The user's preferred name is Julie" in joined
    assert "task management is enabled" in joined
    assert "check-ins are disabled" in joined
    assert "Recent automated messages sent to them:" in joined
    assert "Keep going." in joined
    assert "Their task information:" in joined


def test_assemble_comprehensive_messages_uses_chat_response_flow(monkeypatch):
    calls = []

    def _fake_build_envelope(user_id, **kwargs):
        calls.append((user_id, kwargs))
        return _envelope()

    monkeypatch.setattr(
        "ai.context.assembly.build_ai_context_envelope",
        _fake_build_envelope,
    )

    messages = assemble_comprehensive_messages(
        "user-1",
        "hello",
    )

    assert messages[0]["role"] == "system"
    assert "MHM's in-app assistant" in messages[0]["content"]
    assert "User Context:" in messages[0]["content"]
    assert messages[1] == {"role": "user", "content": "hello"}
    assert calls == [
        (
            "user-1",
            {
                "requested_intent": "chat_response",
                "prompt_request": "hello",
                "include_conversation_history": True,
            },
        )
    ]
