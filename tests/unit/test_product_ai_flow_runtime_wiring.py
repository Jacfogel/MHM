"""Tests for action_interpretation and action_result_response prompt wiring."""

from __future__ import annotations

import pytest

from ai.prompts.command_interpreter import get_command_interpreter
from ai.prompts.manager import get_prompt_manager
from ai.context.assembly import assemble_action_result_messages
from communication.message_processing.command_parser import get_enhanced_command_parser


pytestmark = [pytest.mark.unit, pytest.mark.ai]


def test_action_interpretation_prompt_uses_composed_categories():
    get_enhanced_command_parser()
    messages = get_command_interpreter().create_command_parsing_prompt("list tasks")

    system_content = messages[0]["content"]
    assert "Product AI flow: action_interpretation" in system_content
    assert "[data_honesty]" in system_content
    assert "[action_boundaries]" in system_content
    assert "[available_actions]" in system_content
    assert "ACTION:" in system_content
    assert "create_task" in system_content


def test_action_interpretation_prompt_avoids_duplicate_action_lists():
    get_enhanced_command_parser()
    manager = get_prompt_manager()

    messages = get_command_interpreter().create_command_parsing_prompt("create task buy milk")
    system_content = messages[0]["content"]
    format_only = manager.get_command_format_instructions()

    assert format_only in system_content
    assert system_content.count("Available actions:") <= 1


def test_action_result_response_prompt_includes_result_metadata():
    messages = assemble_action_result_messages(
        "user-test",
        "remind me to call the pharmacy",
        {
            "action_name": "create_task",
            "completed": True,
            "handler_message": "Task created: Call pharmacy",
        },
    )

    system_content = messages[0]["content"]
    assert "Product AI flow: action_result_response" in system_content
    assert "[persona]" in system_content
    assert "[reply_rules]" in system_content
    assert "[action_boundaries]" in system_content
    assert "[action_result_metadata]" in system_content
    assert "create_task" in system_content
    assert "Call pharmacy" in system_content
