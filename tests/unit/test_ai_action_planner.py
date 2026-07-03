"""Tests for AI action planning and plan parsing."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.chat.action_planner import (
    ActionPlanner,
    answer_only_plan,
    parse_action_plan_from_text,
)
from ai.prompts.action_catalog import AIActionPlan, build_action_catalog


pytestmark = [pytest.mark.unit, pytest.mark.ai]


def test_parse_execute_action_plan_maps_entities():
    catalog = build_action_catalog()
    output = (
        "INTENT: execute_action\n"
        "ACTION: create_task\n"
        "TITLE: Buy groceries\n"
        "PRIORITY: high\n"
        "CONFIDENCE: 0.92\n"
    )

    plan = parse_action_plan_from_text(
        output,
        source_message="remind me to buy groceries",
        catalog=catalog,
        planning_method="test",
    )

    assert plan is not None
    assert plan.response_intent == "execute_action"
    assert len(plan.actions) == 1
    action = plan.actions[0]
    assert action.action_name == "create_task"
    assert action.entities["title"] == "Buy groceries"
    assert action.entities["priority"] == "high"
    assert action.confidence == 0.92


def test_parse_clarify_plan_returns_question():
    plan = parse_action_plan_from_text(
        "INTENT: clarify\nQUESTION: What should the task be called?",
        source_message="add a task",
        planning_method="test",
    )

    assert plan is not None
    assert plan.response_intent == "clarify"
    assert plan.clarification_question == "What should the task be called?"


def test_parse_answer_only_plan_from_intent_line():
    plan = parse_action_plan_from_text(
        "INTENT: answer_only",
        source_message="I'm feeling overwhelmed today",
        planning_method="test",
    )

    assert plan is not None
    assert plan.response_intent == "answer_only"
    assert plan.actions == ()


def test_parse_malformed_output_defaults_to_answer_only():
    plan = parse_action_plan_from_text(
        "I think the user wants help with tasks.",
        source_message="help me",
        planning_method="test",
    )

    assert plan is not None
    assert plan.response_intent == "answer_only"
    assert plan.planning_method.endswith("_malformed")


def test_parse_missing_required_fields_downgrades_to_clarify():
    catalog = build_action_catalog()
    plan = parse_action_plan_from_text(
        "INTENT: execute_action\nACTION: create_task\nCONFIDENCE: 0.95",
        source_message="create a task",
        catalog=catalog,
        planning_method="test",
    )

    assert plan is not None
    assert plan.response_intent == "clarify"
    assert "title" in (plan.clarification_question or "").lower()


def test_parse_invalid_action_downgrades_to_clarify():
    catalog = build_action_catalog()
    plan = parse_action_plan_from_text(
        "INTENT: execute_action\nACTION: fly_to_moon\nCONFIDENCE: 0.99",
        source_message="fly to the moon",
        catalog=catalog,
        planning_method="test",
    )

    assert plan is not None
    assert plan.response_intent == "clarify"


def test_parse_low_confidence_downgrades_to_clarify():
    catalog = build_action_catalog()
    plan = parse_action_plan_from_text(
        "INTENT: execute_action\n"
        "ACTION: create_task\n"
        "TITLE: Maybe groceries\n"
        "CONFIDENCE: 0.1",
        source_message="groceries?",
        catalog=catalog,
        planning_method="test",
    )

    assert plan is not None
    assert plan.response_intent == "clarify"


def test_plan_from_message_uses_ai_when_available():
    planner = ActionPlanner()
    ai_chatbot = MagicMock()
    ai_chatbot.is_ai_available.return_value = True
    ai_chatbot.generate_response.return_value = (
        "INTENT: answer_only\n"
    )

    plan = planner.plan_from_message(
        "how are you?",
        user_id="user-1",
        ai_chatbot=ai_chatbot,
    )

    assert isinstance(plan, AIActionPlan)
    assert plan.response_intent == "answer_only"
    ai_chatbot.generate_response.assert_called_once()


def test_plan_from_message_defaults_when_ai_unavailable():
    planner = ActionPlanner()
    ai_chatbot = MagicMock()
    ai_chatbot.is_ai_available.return_value = False

    plan = planner.plan_from_message(
        "list my tasks",
        user_id="user-1",
        ai_chatbot=ai_chatbot,
    )

    assert plan == answer_only_plan(
        "list my tasks", planning_method="ai_unavailable"
    )
