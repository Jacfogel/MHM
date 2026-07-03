"""Tests for AIActionRequest conversion and structured command dispatch routing."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.prompts.action_catalog import AIActionRequest
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from communication.message_processing.action_request_adapter import (
    AIActionExecutionMetadata,
    build_action_execution_metadata,
    build_parsing_result_from_action_request,
    convert_action_request_to_parsed_command,
)
from communication.message_processing.structured_command_dispatcher import (
    dispatch_structured_command,
)
from tasks import load_active_tasks
from tests.test_helpers.test_utilities import TestUserFactory


pytestmark = [pytest.mark.unit, pytest.mark.ai, pytest.mark.communication]


def test_convert_action_request_to_parsed_command_maps_fields():
    request = AIActionRequest(
        action_name="create_task",
        entities={"title": "Buy groceries", "priority": "high"},
        confidence=0.91,
        source_message="Remind me to buy groceries.",
    )

    parsed = convert_action_request_to_parsed_command(request)

    assert isinstance(parsed, ParsedCommand)
    assert parsed.intent == "create_task"
    assert parsed.entities["title"] == "Buy groceries"
    assert parsed.confidence == 0.91
    assert parsed.original_message == "Remind me to buy groceries."


def test_build_parsing_result_from_action_request_sets_method():
    request = AIActionRequest(
        action_name="list_tasks",
        entities={},
        confidence=0.8,
        source_message="show my tasks",
    )

    parsing = build_parsing_result_from_action_request(request)

    assert parsing is not None
    assert parsing.method == "ai_action_request"
    assert parsing.parsed_command.intent == "list_tasks"


def test_build_action_execution_metadata_captures_handler_output():
    request = AIActionRequest(
        action_name="create_task",
        entities={"title": "Call pharmacy"},
        confidence=0.95,
        source_message="remind me to call the pharmacy",
    )
    response = InteractionResponse(
        message="Task created: Call pharmacy",
        completed=True,
        rich_data={"task_id": "task-123"},
    )

    metadata = build_action_execution_metadata(request, response)

    assert isinstance(metadata, AIActionExecutionMetadata)
    assert metadata.action_name == "create_task"
    assert metadata.completed is True
    assert metadata.handler_message == "Task created: Call pharmacy"
    assert metadata.rich_data == {"task_id": "task-123"}
    assert metadata.to_dict()["action_name"] == "create_task"


@pytest.mark.tasks
def test_action_request_routes_create_task_through_dispatcher(test_data_dir):
    user_id = "action-routing-user"
    TestUserFactory.create_basic_user(
        user_id,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )

    request = AIActionRequest(
        action_name="create_task",
        entities={"title": "Water plants"},
        confidence=0.93,
        source_message="remind me to water the plants",
    )
    parsing = build_parsing_result_from_action_request(request)
    assert parsing is not None

    command_parser = MagicMock()
    command_parser.get_suggestions.return_value = []
    ai_chatbot = MagicMock()
    ai_chatbot.is_ai_available.return_value = False

    response = dispatch_structured_command(
        user_id,
        parsing,
        "discord",
        command_parser=command_parser,
        ai_chatbot=ai_chatbot,
        enable_ai_enhancement=False,
        command_definitions={},
    )

    assert "Water plants" in response.message

    active_tasks = load_active_tasks(user_id)
    titles = [task.get("title") for task in active_tasks]
    assert "Water plants" in titles
