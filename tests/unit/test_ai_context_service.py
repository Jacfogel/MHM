"""Tests for canonical product-AI context envelopes."""

from __future__ import annotations

import pytest

from ai.context_service import build_ai_context_envelope
from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory


pytestmark = [pytest.mark.unit, pytest.mark.ai]


def test_ai_context_envelope_includes_populated_product_data(test_data_dir):
    user_id = "ai-context-envelope-user"
    assert TestUserFactory.create_full_featured_user(user_id, test_data_dir=test_data_dir)

    from core import get_user_id_by_identifier
    from checkins.checkin_data_manager import store_checkin_response
    from messages.message_data_manager import add_message, store_sent_message
    from notebook import notebook_service
    from tasks import task_service

    actual_user_id = get_user_id_by_identifier(user_id) or user_id
    task_id = task_service.create_task(
        user_id=actual_user_id,
        title="Review refill request",
        due_date="2026-07-02",
        priority="high",
    )
    assert task_id
    store_checkin_response(
        actual_user_id,
        {
            "mood": 4,
            "energy": 3,
            "ate_breakfast": True,
            "brushed_teeth": True,
            "submitted_at": "2026-07-01 08:00:00",
        },
    )
    add_message(
        actual_user_id,
        "motivational",
        {"text": "Keep going.", "schedule": {"days": ["ALL"], "periods": ["morning"]}},
    )
    assert store_sent_message(
        actual_user_id,
        "motivational",
        "message-1",
        "Keep going.",
        delivery_status="sent",
        time_period="morning",
    )
    note_result = notebook_service.create_note_from_command(
        actual_user_id,
        {"title": "Refill notes", "description": "Call pharmacy before Friday."},
    )
    assert note_result and note_result.success

    envelope = build_ai_context_envelope(
        actual_user_id,
        active_channel="discord",
        requested_intent="answer_only",
        prompt_request="What tasks and notes do I have?",
    )

    assert envelope is not None
    structured = envelope.structured
    assert envelope.metadata["user_id"] == actual_user_id
    assert envelope.metadata["active_channel"] == "discord"
    assert envelope.metadata["context_version"] == 1
    assert "features" in structured["account"]
    assert "motivational" in structured["preferences"]["categories"]
    assert "Prefers gentle encouragement" in structured["personal_context"]["notes_for_ai"]
    assert "raw" in structured["schedules"]
    assert any(task["title"] == "Review refill request" for task in structured["tasks"]["active"])
    assert structured["checkins"]["recent"][0]["mood"] == 4
    assert structured["messages"]["recent_sent"][0]["sent_text"] == "Keep going."
    assert structured["messages"]["templates_by_category"]["motivational"][0]["text"] == "Keep going."
    assert structured["notebooks"]["recent"][0]["title"] == "Refill notes"
    assert "guidance_summary" in structured["health"]
    assert structured["analytics"]["recent_checkin_count"] == 1
    assert "recent_chat_interactions" in structured["conversation"]
    assert "create_task" in structured["action_catalog"]["available"]
    assert structured["action_catalog"]["actions"]["create_task"]["domain"] == "tasks"


def test_ai_context_prompt_selection_records_included_sections(test_data_dir):
    user_id = "ai-context-selection-user"
    assert TestUserFactory.create_full_featured_user(user_id, test_data_dir=test_data_dir)

    from core import get_user_id_by_identifier

    actual_user_id = get_user_id_by_identifier(user_id) or user_id
    envelope = build_ai_context_envelope(
        actual_user_id,
        prompt_request="Summarize my recent check-in mood and health recovery.",
    )

    assert envelope is not None
    assert "account" in envelope.included_sections
    assert "preferences" in envelope.included_sections
    assert "personal_context" in envelope.included_sections
    assert "tasks" in envelope.included_sections
    assert "conversation" in envelope.included_sections
    assert "checkins" in envelope.included_sections
    assert "health" in envelope.included_sections
    assert "messages" not in envelope.included_sections
    assert envelope.metadata["included_sections"] == [
        name for name, section in envelope.sections.items() if section.included
    ]
    assert "Check-ins:" in envelope.to_prompt_text()
