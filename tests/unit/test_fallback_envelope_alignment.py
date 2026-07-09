"""Unit tests for envelope-backed fallback alignment (Phase 7)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from ai.fallback import FallbackCategory, build_contextual_fallback
from ai.fallback.action_hints import try_action_unavailable_response
from ai.fallback.context import FallbackContext, build_fallback_context
from ai.fallback.envelope_summaries import try_envelope_summary_response


pytestmark = [pytest.mark.unit, pytest.mark.ai]


def _fallback_context(**overrides) -> FallbackContext:
    structured = {
        "personal_context": {"preferred_name": "Alex"},
        "tasks": {
            "enabled": True,
            "active": [{"title": "Buy milk"}, {"title": "Call pharmacy"}],
            "due_soon": [{"title": "Dentist"}],
            "stats": {"completion_rate": 72.0},
        },
        "checkins": {"enabled": True, "recent": []},
        "messages": {"enabled": True, "categories": ["motivation"], "recent_sent": [{}]},
        "schedules": {"active_schedules": ["morning", "evening"]},
        "action_catalog": {"summary": "Actions: create_task (tasks; required: title)"},
        **overrides.get("structured", {}),
    }
    return FallbackContext(
        user_id=overrides.get("user_id", "user-test"),
        envelope=None,
        preferred_name="Alex",
        name_prefix="Alex, ",
        action_catalog_summary=structured["action_catalog"]["summary"],
        is_new_user=overrides.get("is_new_user", False),
        structured=structured,
    )


def test_envelope_task_summary_lists_active_tasks():
    context = _fallback_context()
    result = try_envelope_summary_response("what are my tasks", context)
    assert result is not None
    text, category = result
    assert category == FallbackCategory.ENVELOPE_SUMMARY
    assert "2 active task" in text
    assert "Buy milk" in text


def test_envelope_capability_summary_uses_catalog():
    context = _fallback_context()
    result = try_envelope_summary_response("what can you do", context)
    assert result is not None
    text, category = result
    assert category == FallbackCategory.ENVELOPE_SUMMARY
    assert "create_task" in text
    assert "offline for AI chat" in text


def test_action_unavailable_suggests_command_without_claiming_success():
    context = _fallback_context()
    result = try_action_unavailable_response("please create task buy eggs", context)
    assert result is not None
    text, category = result
    assert category == FallbackCategory.ACTION_UNAVAILABLE
    assert "add task" in text.lower()
    assert "can't run that automatically" in text.lower()
    assert "done" not in text.lower()


@patch("ai.fallback.context.build_ai_context_envelope")
def test_build_fallback_context_requests_fallback_flow(mock_build):
    mock_build.return_value = None
    context = build_fallback_context("user-1", "list my tasks")
    assert context is not None
    assert context.user_id == "user-1"
    mock_build.assert_called_once()
    kwargs = mock_build.call_args.kwargs
    assert kwargs["requested_intent"] == "fallback_response"
    assert kwargs["prompt_request"] == "list my tasks"


@patch("ai.fallback.coordinator.build_fallback_context")
def test_coordinator_prefers_envelope_summary_before_keywords(mock_context):
    context = _fallback_context()
    mock_context.return_value = context
    text, category = build_contextual_fallback("what are my tasks", "user-test")
    assert category == FallbackCategory.ENVELOPE_SUMMARY
    assert "active task" in text
