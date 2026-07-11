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


def test_parse_multi_action_plan_builds_ordered_requests():
    catalog = build_action_catalog()
    output = (
        "INTENT: execute_action\n"
        "ACTION: update_task\n"
        "TASK_IDENTIFIER: 1\n"
        "PRIORITY: high\n"
        "CONFIDENCE: 0.95\n"
        "ACTION: list_tasks\n"
        "CONFIDENCE: 0.92\n"
    )

    plan = parse_action_plan_from_text(
        output,
        source_message="update task 1 priority high and show tasks",
        catalog=catalog,
        planning_method="test",
    )

    assert plan is not None
    assert plan.response_intent == "execute_action"
    assert len(plan.actions) == 2
    assert plan.actions[0].action_name == "update_task"
    assert plan.actions[0].entities["priority"] == "high"
    assert plan.actions[1].action_name == "list_tasks"


def test_parse_multi_action_plan_uses_shared_default_confidence():
    catalog = build_action_catalog()
    output = (
        "INTENT: execute_action\n"
        "CONFIDENCE: 0.93\n"
        "ACTION: update_task\n"
        "TASK_IDENTIFIER: 1\n"
        "PRIORITY: high\n"
        "ACTION: list_tasks\n"
    )

    plan = parse_action_plan_from_text(
        output,
        source_message="update and list",
        catalog=catalog,
        planning_method="test",
    )

    assert plan is not None
    assert len(plan.actions) == 2
    assert plan.actions[0].confidence == 0.93
    assert plan.actions[1].confidence == 0.93


def test_parse_multi_action_missing_fields_downgrades_to_clarify():
    catalog = build_action_catalog()
    output = (
        "INTENT: execute_action\n"
        "ACTION: update_task\n"
        "TASK_IDENTIFIER: 1\n"
        "PRIORITY: high\n"
        "CONFIDENCE: 0.95\n"
        "ACTION: create_task\n"
        "CONFIDENCE: 0.95\n"
    )

    plan = parse_action_plan_from_text(
        output,
        source_message="update then create",
        catalog=catalog,
        planning_method="test",
    )

    assert plan is not None
    assert plan.response_intent == "clarify"
    assert plan.planning_method.endswith("_missing_fields")


@pytest.mark.tasks
def test_multi_action_plan_text_routes_through_executor(test_data_dir):
    """Parsed multi-action planner output executes through the executor."""
    from communication.message_processing.action_plan_executor import (
        get_action_plan_executor,
    )
    from tasks import create_task, load_active_tasks
    from tests.test_helpers.test_utilities import TestUserFactory

    user_id = "planner-parse-multi-user"
    task_title = "Fold laundry"
    TestUserFactory.create_basic_user(
        user_id,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )
    create_task(user_id, task_title, due_date="2026-07-15", priority="low")

    output = (
        "INTENT: execute_action\n"
        "ACTION: update_task\n"
        "TASK_IDENTIFIER: 1\n"
        "PRIORITY: high\n"
        "CONFIDENCE: 0.95\n"
        "ACTION: list_tasks\n"
        "CONFIDENCE: 0.95\n"
    )
    plan = parse_action_plan_from_text(
        output,
        source_message="raise priority and list tasks",
        planning_method="test",
    )
    assert plan is not None
    assert len(plan.actions) == 2

    command_parser = MagicMock()
    command_parser.get_suggestions.return_value = []
    ai_chatbot = MagicMock()
    ai_chatbot.is_ai_available.return_value = False

    result = get_action_plan_executor().execute_plan(
        plan,
        user_id,
        "discord",
        command_parser=command_parser,
        ai_chatbot=ai_chatbot,
        enable_ai_enhancement=False,
        command_definitions={},
    )

    assert result is not None
    assert task_title in result.response.message
    task = next(
        (item for item in load_active_tasks(user_id) if item.get("title") == task_title),
        None,
    )
    assert task is not None
    assert task.get("priority") == "high"
