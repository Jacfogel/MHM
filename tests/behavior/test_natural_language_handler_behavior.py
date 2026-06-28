"""Behavior tests for natural-language phrase settings handler."""

import pytest

from communication.command_handlers.natural_language_handler import NaturalLanguageHandler
from communication.command_handlers.shared_types import ParsedCommand
from tests.test_helpers.test_utilities import TestUserFactory


class TestNaturalLanguageHandlerBehavior:
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user
    def test_handler_can_handle_intents(self):
        handler = NaturalLanguageHandler()
        for intent in (
            "show_natural_language_defaults",
            "update_natural_language_defaults",
        ):
            assert handler.can_handle(intent)
        assert not handler.can_handle("create_task")

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user
    def test_show_phrase_settings(self, test_data_dir):
        user_id = "user-nl-show"
        TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        handler = NaturalLanguageHandler()
        response = handler.handle(
            user_id,
            ParsedCommand(
                intent="show_natural_language_defaults",
                entities={},
                confidence=1.0,
                original_message="show phrase settings",
            ),
        )
        assert response.completed
        assert "tonight" in response.message.lower()
        assert "18:00" in response.message

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user
    def test_update_phrase_settings_persists(self, test_data_dir):
        user_id = "user-nl-update"
        TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        handler = NaturalLanguageHandler()
        update_response = handler.handle(
            user_id,
            ParsedCommand(
                intent="update_natural_language_defaults",
                entities={"nl_field": "tonight", "nl_value": "9pm"},
                confidence=1.0,
                original_message="set tonight to 9pm",
            ),
        )
        assert update_response.completed
        assert "21:00" in update_response.message

        show_response = handler.handle(
            user_id,
            ParsedCommand(
                intent="show_natural_language_defaults",
                entities={},
                confidence=1.0,
                original_message="show phrase settings",
            ),
        )
        assert "21:00" in show_response.message
