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


def test_build_planning_messages_are_compact_and_omit_chat_categories():
    planner = ActionPlanner()
    messages = planner.build_planning_messages("user-1", "add task laundry")

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1] == {"role": "user", "content": "add task laundry"}
    system = messages[0]["content"]
    assert "ACTION: create_task" in system
    assert "ACTION: unknown" in system
    assert "pack hiking bag" in system
    assert "Product AI flow:" not in system
    assert "[data_honesty]" not in system
    assert "[action_boundaries]" not in system
    assert "You are a command parser" not in system
    assert len(system) < 2200


def test_plan_from_message_uses_ai_when_available(monkeypatch):
    planner = ActionPlanner()
    ai_chatbot = MagicMock()
    ai_chatbot.is_ai_available.return_value = True
    mock_call = MagicMock(
        return_value="INTENT: answer_only\n",
    )
    monkeypatch.setattr(
        "ai.chat.action_planner.call_lm_studio_api",
        mock_call,
    )

    plan = planner.plan_from_message(
        "how are you?",
        user_id="user-1",
        ai_chatbot=ai_chatbot,
    )

    assert isinstance(plan, AIActionPlan)
    assert plan.response_intent == "answer_only"
    mock_call.assert_called_once()
    kwargs = mock_call.call_args.kwargs
    assert kwargs["messages"][0]["role"] == "system"
    assert kwargs["messages"][1]["content"] == "how are you?"
    assert "ACTION: create_task" in kwargs["messages"][0]["content"]
    assert kwargs.get("stop")


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


def test_parse_keeps_first_valid_action_when_trailing_block_is_junk():
    catalog = build_action_catalog()
    output = (
        "ACTION: create_task\n"
        "TITLE: buy milk\n"
        "CONFIDENCE: 0.9\n"
        "\nStart with INTENT:\n"
        "ACTION: add_list_item\n"
        "TITLE: entry_ref\n"
        "ITEM_TEXT: item_text\n"
    )
    from ai.chat.action_planner import _trim_planner_output

    plan = parse_action_plan_from_text(
        _trim_planner_output(output),
        source_message="add task buy milk",
        catalog=catalog,
        planning_method="test",
    )

    assert plan is not None
    assert plan.response_intent == "execute_action"
    assert len(plan.actions) == 1
    assert plan.actions[0].action_name == "create_task"
    assert plan.actions[0].entities["title"] == "buy milk"


def test_parse_rejects_ungrounded_example_title_and_clarifies():
    catalog = build_action_catalog()
    plan = parse_action_plan_from_text(
        "ACTION: create_task\nTITLE: pack hiking bag\nCONFIDENCE: 0.9\n",
        source_message="add a task",
        catalog=catalog,
        planning_method="test",
    )

    assert plan is not None
    assert plan.response_intent == "clarify"
    assert "title" in (plan.clarification_question or "").lower()


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
