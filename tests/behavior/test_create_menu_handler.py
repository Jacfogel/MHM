"""Behavior tests for the unified create menu handler."""

import pytest

from communication.command_handlers.create_menu_handler import CreateMenuHandler
from communication.command_handlers.shared_types import ParsedCommand


@pytest.mark.behavior
@pytest.mark.communication
def test_create_menu_handler_returns_hub_rich_data():
    handler = CreateMenuHandler()
    response = handler.handle(
        "user-create-menu",
        ParsedCommand(
            intent="show_create_hub",
            entities={},
            confidence=1.0,
            original_message="create",
        ),
    )
    assert response.completed
    assert response.rich_data
    assert response.rich_data.get("interaction_view") == "create_hub"
    assert response.rich_data.get("user_id") == "user-create-menu"
    assert "template" in response.message.lower()


@pytest.mark.unit
@pytest.mark.communication
def test_command_parser_create_opens_hub():
    from communication.message_processing.command_parser import parse_command

    result = parse_command("create")
    assert result is not None
    assert result.parsed_command.intent == "show_create_hub"
