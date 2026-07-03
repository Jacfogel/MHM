"""Tests for AI action plan execution."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.chat.action_planner import clarify_plan
from ai.prompts.action_catalog import AIActionPlan, AIActionRequest
from communication.message_processing.action_plan_executor import (
    ActionPlanExecutor,
    get_action_plan_executor,
)
from tasks import load_active_tasks
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
