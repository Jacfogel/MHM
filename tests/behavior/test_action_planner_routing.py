"""
Behavior tests for InteractionManager routing when AI_ACTION_PLANNER_ENABLED is on.

Uses mocked planner output so tests do not require LM Studio or Discord.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import core.config as app_config
from ai.chat.action_planner import answer_only_plan, clarify_plan
from ai.prompts.action_catalog import AIActionPlan, AIActionRequest
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from communication.message_processing.command_parser import ParsingResult
from communication.message_processing.interaction_manager import InteractionManager
from tasks import load_active_tasks
from tests.test_helpers.test_utilities import TestUserFactory


pytestmark = [pytest.mark.behavior, pytest.mark.ai, pytest.mark.communication]


def _force_low_confidence_parse(interaction_manager: InteractionManager) -> None:
    """Force messages onto the contextual-chat / planner path."""

    def _parse(message, user_id=None):
        text = "" if message is None else str(message)
        return ParsingResult(
            ParsedCommand("unknown", {}, 0.05, text),
            0.05,
            "ai_fallback",
        )

    interaction_manager.command_parser.parse = _parse


def _force_high_confidence_create_task(interaction_manager: InteractionManager) -> None:
    """Force structured-command path with a confident create_task parse."""

    def _parse(message, user_id=None):
        text = "" if message is None else str(message)
        return ParsingResult(
            ParsedCommand("create_task", {"title": "Buy milk"}, 0.95, text),
            0.95,
            "rule_based",
        )

    interaction_manager.command_parser.parse = _parse


def _mock_planner_plan(plan):
    """Patch get_action_planner in the executor module used by InteractionManager."""
    mock_planner = MagicMock()
    mock_planner.plan_from_message.return_value = plan
    return patch(
        "communication.message_processing.action_plan_executor.get_action_planner",
        return_value=mock_planner,
    )


@pytest.fixture
def planner_enabled(monkeypatch):
    """Enable the action planner flag for one test."""
    monkeypatch.setattr(app_config, "AI_ACTION_PLANNER_ENABLED", True)


@pytest.mark.tasks
def test_planner_execute_action_creates_task(test_data_dir, planner_enabled):
    """Low-confidence message + execute_action plan routes through dispatcher."""
    user_id = "planner-routing-create-task"
    TestUserFactory.create_basic_user(
        user_id,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )
    message = "could you remind me tomorrow about the dentist"
    plan = AIActionPlan(
        response_intent="execute_action",
        actions=(
            AIActionRequest(
                action_name="create_task",
                entities={"title": "Dentist appointment"},
                confidence=0.92,
                source_message=message,
            ),
        ),
        source_message=message,
        planning_method="test",
    )

    interaction_manager = InteractionManager()
    interaction_manager.enable_ai_enhancement = False
    _force_low_confidence_parse(interaction_manager)

    with _mock_planner_plan(plan):
        response = interaction_manager.handle_message(user_id, message, "discord")

    assert response is not None
    assert "Dentist appointment" in response.message
    titles = [task.get("title") for task in load_active_tasks(user_id)]
    assert "Dentist appointment" in titles


def test_planner_clarify_returns_question(test_data_dir, planner_enabled):
    """Clarify plans return the planner question without side effects."""
    user_id = "planner-routing-clarify"
    TestUserFactory.create_basic_user(
        user_id,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )
    message = "add a task"
    plan = clarify_plan(message, "What should the task be called?")

    interaction_manager = InteractionManager()
    interaction_manager.enable_ai_enhancement = False
    _force_low_confidence_parse(interaction_manager)

    with _mock_planner_plan(plan):
        response = interaction_manager.handle_message(user_id, message, "discord")

    assert response is not None
    assert response.message == "What should the task be called?"
    assert response.completed is True
    assert load_active_tasks(user_id) == []


def test_planner_answer_only_uses_chat_generation(test_data_dir, planner_enabled):
    """Answer-only plans delegate to chat response generation."""
    user_id = "planner-routing-answer"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    message = "I'm feeling overwhelmed today"
    plan = answer_only_plan(message, planning_method="test")

    interaction_manager = InteractionManager()
    interaction_manager.enable_ai_enhancement = False
    _force_low_confidence_parse(interaction_manager)
    interaction_manager.ai_chatbot = MagicMock()
    interaction_manager.ai_chatbot.generate_response.return_value = (
        "That sounds hard. Want to talk through what's on your plate?"
    )

    with _mock_planner_plan(plan):
        response = interaction_manager.handle_message(user_id, message, "discord")

    assert response is not None
    assert "overwhelmed" in response.message.lower() or "plate" in response.message.lower()
    interaction_manager.ai_chatbot.generate_response.assert_called_once_with(
        message,
        user_id=user_id,
        mode="chat",
    )


def test_planner_none_falls_back_to_contextual_chat(test_data_dir, planner_enabled):
    """When planning returns None, InteractionManager uses contextual chat."""
    user_id = "planner-routing-fallback"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    message = "what should I focus on this week?"

    interaction_manager = InteractionManager()
    interaction_manager.enable_ai_enhancement = False
    _force_low_confidence_parse(interaction_manager)
    interaction_manager._handle_contextual_chat = MagicMock(
        return_value=InteractionResponse("Contextual chat fallback reply.", True)
    )

    with _mock_planner_plan(None):
        response = interaction_manager.handle_message(user_id, message, "discord")

    assert response is not None
    assert response.message == "Contextual chat fallback reply."
    interaction_manager._handle_contextual_chat.assert_called_once_with(
        user_id, message, "discord"
    )


@pytest.mark.tasks
def test_high_confidence_parse_skips_planner(test_data_dir, planner_enabled):
    """Confident structured commands bypass the planner even when it is enabled."""
    user_id = "planner-routing-skip"
    TestUserFactory.create_basic_user(
        user_id,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )
    message = "add task buy milk"

    interaction_manager = InteractionManager()
    interaction_manager.enable_ai_enhancement = False
    _force_high_confidence_create_task(interaction_manager)

    mock_planner = MagicMock()

    with patch(
        "communication.message_processing.action_plan_executor.get_action_planner",
        return_value=mock_planner,
    ):
        response = interaction_manager.handle_message(user_id, message, "discord")

    assert response is not None
    mock_planner.plan_from_message.assert_not_called()
    titles = [task.get("title") for task in load_active_tasks(user_id)]
    assert "Buy milk" in titles


def test_planner_disabled_uses_contextual_chat(test_data_dir, monkeypatch):
    """With planner off, low-confidence messages go straight to contextual chat."""
    monkeypatch.setattr(app_config, "AI_ACTION_PLANNER_ENABLED", False)
    user_id = "planner-routing-disabled"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    message = "I'm having a rough day"

    interaction_manager = InteractionManager()
    interaction_manager.enable_ai_enhancement = False
    _force_low_confidence_parse(interaction_manager)
    interaction_manager._handle_contextual_chat = MagicMock(
        return_value=InteractionResponse("Chat path without planner.", True)
    )

    mock_planner = MagicMock()
    with patch(
        "communication.message_processing.action_plan_executor.get_action_planner",
        return_value=mock_planner,
    ):
        response = interaction_manager.handle_message(user_id, message, "discord")

    assert response is not None
    assert response.message == "Chat path without planner."
    mock_planner.plan_from_message.assert_not_called()
    interaction_manager._handle_contextual_chat.assert_called_once()
