"""Tests for AI action plan execution."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ai.chat.action_planner import clarify_plan
from ai.prompts.action_catalog import AIActionPlan, AIActionRequest
from communication.command_handlers.shared_types import InteractionResponse
from communication.message_processing.action_plan_executor import (
    ActionPlanExecutor,
    get_action_plan_executor,
)
from tasks import create_task, load_active_tasks
from tests.test_helpers.test_utilities import TestUserFactory


pytestmark = [pytest.mark.unit, pytest.mark.ai, pytest.mark.communication]


def test_execute_clarify_plan_returns_question():
    executor = ActionPlanExecutor()
    plan = clarify_plan("add task", "What should the task be called?")

    result = executor.execute_plan(
        plan,
        "user-1",
        "discord",
        command_parser=MagicMock(),
        ai_chatbot=MagicMock(),
        enable_ai_enhancement=False,
        command_definitions={},
    )

    assert result is not None
    assert result.response.message == "What should the task be called?"
    assert result.response.completed is True


def test_execute_answer_only_plan_uses_chat_mode():
    executor = ActionPlanExecutor()
    ai_chatbot = MagicMock()
    ai_chatbot.generate_response.return_value = "I'm here to listen."
    plan = AIActionPlan(
        response_intent="answer_only",
        source_message="I'm stressed",
        planning_method="test",
    )

    result = executor.execute_plan(
        plan,
        "user-1",
        "discord",
        command_parser=MagicMock(),
        ai_chatbot=ai_chatbot,
        enable_ai_enhancement=False,
        command_definitions={},
    )

    assert result is not None
    assert result.response.message == "I'm here to listen."
    ai_chatbot.generate_response.assert_called_once_with(
        "I'm stressed",
        user_id="user-1",
        mode="chat",
    )


@pytest.mark.tasks
def test_execute_action_plan_routes_through_dispatcher(test_data_dir):
    user_id = "planner-exec-user"
    TestUserFactory.create_basic_user(
        user_id,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )

    plan = AIActionPlan(
        response_intent="execute_action",
        actions=(
            AIActionRequest(
                action_name="create_task",
                entities={"title": "Feed the cat"},
                confidence=0.95,
                source_message="remind me to feed the cat",
            ),
        ),
        source_message="remind me to feed the cat",
        planning_method="test",
    )

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
    assert "Feed the cat" in result.response.message
    assert result.metadata is not None
    assert result.metadata.action_name == "create_task"

    titles = [task.get("title") for task in load_active_tasks(user_id)]
    assert "Feed the cat" in titles


@pytest.mark.tasks
def test_execute_multi_action_plan_runs_actions_in_order(test_data_dir):
    """A plan with multiple completed actions applies each change and combines replies."""
    user_id = "planner-exec-multi-user"
    task_title = "Weekly laundry"
    TestUserFactory.create_basic_user(
        user_id,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )
    create_task(user_id, task_title, due_date="2026-07-15", priority="low")

    plan = AIActionPlan(
        response_intent="execute_action",
        actions=(
            AIActionRequest(
                action_name="update_task",
                entities={"task_identifier": "1", "priority": "high"},
                confidence=0.95,
                source_message="update task 1 priority high",
            ),
            AIActionRequest(
                action_name="list_tasks",
                entities={},
                confidence=0.95,
                source_message="show my tasks",
            ),
        ),
        source_message="update task 1 priority high and show my tasks",
        planning_method="test",
    )

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
    assert "updated" in result.response.message.lower()
    assert isinstance(result.metadata, list)
    assert len(result.metadata) == 2
    assert result.metadata[0].action_name == "update_task"
    assert result.metadata[1].action_name == "list_tasks"

    task = next(
        (item for item in load_active_tasks(user_id) if item.get("title") == task_title),
        None,
    )
    assert task is not None
    assert task.get("priority") == "high"


def test_execute_multi_action_plan_stops_on_incomplete_follow_up():
    """Multi-action execution stops when an action enters a follow-up flow."""
    executor = ActionPlanExecutor()
    plan = AIActionPlan(
        response_intent="execute_action",
        actions=(
            AIActionRequest(
                action_name="create_task",
                entities={"title": "Needs due date"},
                confidence=0.95,
                source_message="add task needs due date",
            ),
            AIActionRequest(
                action_name="list_tasks",
                entities={},
                confidence=0.95,
                source_message="show tasks",
            ),
        ),
        source_message="add task needs due date and show tasks",
        planning_method="test",
    )

    follow_up = InteractionResponse(
        "Task created. What due date should I use?",
        completed=False,
    )
    list_response = InteractionResponse("Here are your tasks.", True)

    with patch(
        "communication.message_processing.action_plan_executor.dispatch_structured_command",
        side_effect=[follow_up, list_response],
    ) as dispatch:
        result = executor.execute_plan(
            plan,
            "user-1",
            "discord",
            command_parser=MagicMock(),
            ai_chatbot=MagicMock(),
            enable_ai_enhancement=False,
            command_definitions={},
        )

    assert result is not None
    assert result.response is follow_up
    dispatch.assert_called_once()
    assert isinstance(result.metadata, list)
    assert len(result.metadata) == 1
    assert result.metadata[0].action_name == "create_task"


def test_execute_action_plan_applies_result_aware_when_enhancement_disabled():
    """Planner path rewrites handler output even when enable_ai_enhancement is False."""
    executor = ActionPlanExecutor()
    plan = AIActionPlan(
        response_intent="execute_action",
        actions=(
            AIActionRequest(
                action_name="list_tasks",
                entities={},
                confidence=0.95,
                source_message="show my tasks",
            ),
        ),
        source_message="show my tasks",
        planning_method="test",
    )
    handler_response = InteractionResponse("Here are your tasks: Buy milk", True)
    ai_chatbot = MagicMock()
    ai_chatbot.is_ai_available.return_value = True
    ai_chatbot.generate_response.return_value = (
        "You have one task on your list: buy milk."
    )

    with patch(
        "communication.message_processing.action_plan_executor.dispatch_structured_command",
        return_value=handler_response,
    ):
        with patch(
            "communication.message_processing.action_plan_executor.assemble_action_result_messages",
            return_value=[
                {"role": "system", "content": "Product AI flow: action_result_response"},
                {"role": "user", "content": "show my tasks"},
            ],
        ) as assemble:
            result = executor.execute_plan(
                plan,
                "user-1",
                "discord",
                command_parser=MagicMock(),
                ai_chatbot=ai_chatbot,
                enable_ai_enhancement=False,
                command_definitions={},
            )

    assert result is not None
    assert result.response.message == "You have one task on your list: buy milk."
    assemble.assert_called_once()
    ai_chatbot.generate_response.assert_called_once()


def test_execute_multi_action_plan_applies_result_aware_to_each_action():
    """Multi-action plans rewrite every completed handler reply, then combine."""
    executor = ActionPlanExecutor()
    plan = AIActionPlan(
        response_intent="execute_action",
        actions=(
            AIActionRequest(
                action_name="update_task",
                entities={"task_identifier": "1", "priority": "high"},
                confidence=0.95,
                source_message="update task 1 priority high",
            ),
            AIActionRequest(
                action_name="list_tasks",
                entities={},
                confidence=0.95,
                source_message="show my tasks",
            ),
        ),
        source_message="update task 1 priority high and show my tasks",
        planning_method="test",
    )
    update_response = InteractionResponse("Task 1 updated to high priority.", True)
    list_response = InteractionResponse("Tasks: Weekly laundry (high)", True)
    ai_chatbot = MagicMock()
    ai_chatbot.is_ai_available.return_value = True
    ai_chatbot.generate_response.side_effect = [
        "Done — task 1 is now high priority.",
        "Your tasks: Weekly laundry, marked high priority.",
    ]

    with patch(
        "communication.message_processing.action_plan_executor.dispatch_structured_command",
        side_effect=[update_response, list_response],
    ):
        with patch(
            "communication.message_processing.action_plan_executor.assemble_action_result_messages",
            return_value=[
                {"role": "system", "content": "Product AI flow: action_result_response"},
                {"role": "user", "content": "user prompt"},
            ],
        ) as assemble:
            result = executor.execute_plan(
                plan,
                "user-1",
                "discord",
                command_parser=MagicMock(),
                ai_chatbot=ai_chatbot,
                enable_ai_enhancement=False,
                command_definitions={},
            )

    assert result is not None
    assert "Done — task 1 is now high priority." in result.response.message
    assert "Your tasks: Weekly laundry, marked high priority." in result.response.message
    assert assemble.call_count == 2
    assert ai_chatbot.generate_response.call_count == 2


def test_execute_action_plan_skips_result_aware_when_ai_unavailable():
    """Raw handler messages are kept when the model is unavailable."""
    executor = ActionPlanExecutor()
    plan = AIActionPlan(
        response_intent="execute_action",
        actions=(
            AIActionRequest(
                action_name="list_tasks",
                entities={},
                confidence=0.95,
                source_message="show my tasks",
            ),
        ),
        source_message="show my tasks",
        planning_method="test",
    )
    handler_response = InteractionResponse("Here are your tasks.", True)
    ai_chatbot = MagicMock()
    ai_chatbot.is_ai_available.return_value = False

    with patch(
        "communication.message_processing.action_plan_executor.dispatch_structured_command",
        return_value=handler_response,
    ):
        with patch(
            "communication.message_processing.action_plan_executor.assemble_action_result_messages",
        ) as assemble:
            result = executor.execute_plan(
                plan,
                "user-1",
                "discord",
                command_parser=MagicMock(),
                ai_chatbot=ai_chatbot,
                enable_ai_enhancement=True,
                command_definitions={},
            )

    assert result is not None
    assert result.response.message == "Here are your tasks."
    assemble.assert_not_called()
    ai_chatbot.generate_response.assert_not_called()
