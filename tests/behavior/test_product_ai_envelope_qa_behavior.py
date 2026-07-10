"""
Behavior tests: product AI answers from envelope-backed user data.

Asserts domain facts appear in responses (tasks, profile, schedules) without
checking exact prompt wording. Uses deterministic fallback routing so tests do
not require LM Studio.
"""

from __future__ import annotations

import pytest

from ai.context.chatbot_context import build_chatbot_context_dict
from ai.context.service import build_ai_context_envelope
from ai.fallback import FallbackCategory, build_contextual_fallback
from core import get_user_id_by_identifier
from tasks import are_tasks_enabled, create_task, load_active_tasks
from tests.test_helpers.test_utilities import TestUserFactory


pytestmark = [pytest.mark.behavior, pytest.mark.ai]


def _create_user_with_task(test_data_dir, user_id: str, task_title: str) -> str:
    assert TestUserFactory.create_basic_user(
        user_id,
        enable_tasks=True,
        enable_checkins=True,
        test_data_dir=test_data_dir,
    )
    resolved_id = get_user_id_by_identifier(user_id) or user_id
    create_task(resolved_id, task_title, due_date="2026-07-15")
    assert are_tasks_enabled(resolved_id)
    assert any(
        task.get("title") == task_title for task in load_active_tasks(resolved_id)
    )
    return resolved_id


@pytest.mark.tasks
def test_fallback_lists_created_task_from_envelope(test_data_dir):
    user_id = "envelope-qa-task-user"
    task_title = "Pick up prescription"
    resolved_id = _create_user_with_task(test_data_dir, user_id, task_title)

    text, category = build_contextual_fallback("what are my tasks", resolved_id)

    assert category == FallbackCategory.ENVELOPE_SUMMARY
    assert task_title in text
    assert "active task" in text.lower()


def test_fallback_answers_preferred_name_from_envelope(test_data_dir):
    user_id = "envelope-qa-name-user"
    assert TestUserFactory.create_basic_user(
        user_id,
        enable_tasks=False,
        enable_checkins=False,
        test_data_dir=test_data_dir,
    )
    resolved_id = get_user_id_by_identifier(user_id) or user_id

    context = build_chatbot_context_dict(resolved_id, include_conversation_history=False)
    preferred = (context.get("user_profile") or {}).get("preferred_name")
    assert preferred

    text, category = build_contextual_fallback("what is my name", resolved_id)

    assert category in (
        FallbackCategory.ENVELOPE_SUMMARY,
        FallbackCategory.DATA_UNAVAILABLE,
    )
    assert preferred in text


def test_fallback_mentions_active_schedules_from_envelope(test_data_dir):
    user_id = "envelope-qa-schedule-user"
    assert TestUserFactory.create_basic_user(
        user_id,
        enable_tasks=False,
        enable_checkins=False,
        test_data_dir=test_data_dir,
    )
    resolved_id = get_user_id_by_identifier(user_id) or user_id

    text, category = build_contextual_fallback("what is my schedule", resolved_id)

    assert category == FallbackCategory.ENVELOPE_SUMMARY
    envelope = build_ai_context_envelope(
        resolved_id,
        requested_intent="envelope_qa_schedule",
        prompt_request="what is my schedule",
    )
    assert envelope is not None
    schedules = envelope.structured.get("schedules") or {}
    active = schedules.get("active_schedules") or []
    assert active, "Basic user should have active schedule periods"
    assert "schedule" in text.lower()


def test_envelope_structured_tasks_include_created_title(test_data_dir):
    user_id = "envelope-qa-prompt-view-user"
    task_title = "Water the plants"
    resolved_id = _create_user_with_task(test_data_dir, user_id, task_title)

    envelope = build_ai_context_envelope(
        resolved_id,
        requested_intent="envelope_qa_prompt_view",
        prompt_request="show my tasks and reminders",
    )
    assert envelope is not None
    assert "tasks" in envelope.included_sections

    active = (envelope.structured.get("tasks") or {}).get("active") or []
    titles = [task.get("title") for task in active if isinstance(task, dict)]
    assert task_title in titles


def test_chatbot_context_dict_reflects_envelope_task_data(test_data_dir):
    user_id = "envelope-qa-chatbot-dict-user"
    task_title = "Call dentist"
    resolved_id = _create_user_with_task(test_data_dir, user_id, task_title)

    context = build_chatbot_context_dict(resolved_id, include_conversation_history=False)
    envelope = build_ai_context_envelope(resolved_id, requested_intent="envelope_qa_dict")

    assert envelope is not None
    envelope_tasks = envelope.structured.get("tasks") or {}
    active_titles = [
        task.get("title")
        for task in (envelope_tasks.get("active") or [])
        if isinstance(task, dict)
    ]
    assert task_title in active_titles
    assert context.get("user_profile") is not None
    assert context.get("preferences") is not None
