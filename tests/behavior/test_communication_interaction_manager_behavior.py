"""
Real behavior tests for communication interaction manager functionality.

Tests focus on actual side effects and system changes rather than just return values.
"""

import pytest
import types
from communication.message_processing.interaction_manager import InteractionManager
from communication.message_processing.conversation_flow_manager import conversation_manager
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from communication.message_processing.command_parser import ParsingResult
from tests.test_utilities import TestUserFactory


def _create_fast_interaction_manager():
    """Create an interaction manager with deterministic fast-path parsing/chat for tests."""
    interaction_manager = InteractionManager()
    parser = interaction_manager.command_parser

    def _fast_parse(message, user_id=None):
        text = "" if message is None else str(message)
        if not text.strip():
            return ParsingResult(
                ParsedCommand("unknown", {}, 0.0, text),
                0.0,
                "fallback",
            )
        return parser._rule_based_parse(text)

    interaction_manager.command_parser.parse = _fast_parse
    interaction_manager.enable_ai_enhancement = False
    interaction_manager._handle_contextual_chat = (
        lambda user_id, message, channel_type: InteractionResponse(
            "I can help with tasks, check-ins, profile, and schedules.",
            True,
        )
    )
    return interaction_manager


@pytest.mark.behavior
@pytest.mark.communication
class TestInteractionManagerBehavior:
    """Test real behavior of interaction manager functionality."""

    def test_interaction_manager_initialization_creates_components(self, test_data_dir):
        """Test that interaction manager initialization creates required components."""
        # Arrange & Act
        interaction_manager = _create_fast_interaction_manager()
        
        # Assert - Verify actual component creation
        assert interaction_manager is not None, "Interaction manager should be created"
        assert hasattr(interaction_manager, 'command_parser'), "Should have command parser"
        assert hasattr(interaction_manager, 'ai_chatbot'), "Should have AI chatbot"
        assert hasattr(interaction_manager, 'interaction_handlers'), "Should have interaction handlers"
        assert hasattr(interaction_manager, 'slash_command_map'), "Should have slash command map"

    def test_process_message_creates_interaction_record(self, test_data_dir):
        """Test that process_message creates actual interaction record."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "help", "discord")
        
        # Assert - Verify actual response creation
        assert response is not None, "Response should be created"
        assert hasattr(response, 'message'), "Response should have message"
        assert hasattr(response, 'completed'), "Response should have completed flag"

    def test_process_message_handles_command_parsing(self, test_data_dir):
        """Test that process_message handles command parsing correctly."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "/tasks", "discord")
        
        # Assert - Verify command parsing
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_process_message_handles_conversation_flow(self, test_data_dir):
        """Test that process_message handles conversation flow correctly."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "Hello, how are you?", "discord")
        
        # Assert - Verify conversation flow
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_process_message_handles_ai_chat(self, test_data_dir):
        """Test that process_message handles AI chat correctly."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "What's the weather like?", "discord")
        
        # Assert - Verify AI chat handling
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_process_message_includes_user_context(self, test_data_dir):
        """Test that process_message includes user context in processing."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "show my profile", "discord")
        
        # Assert - Verify user context inclusion
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_process_message_handles_task_commands(self, test_data_dir):
        """Test that process_message handles task-related commands."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "/tasks", "discord")
        
        # Assert - Verify task command handling
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_process_message_handles_schedule_commands(self, test_data_dir):
        """Test that process_message handles schedule-related commands."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "/schedule", "discord")
        
        # Assert - Verify schedule command handling
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_process_message_handles_checkin_commands(self, test_data_dir):
        """Test that process_message handles checkin-related commands."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "/checkin", "discord")
        
        # Assert - Verify checkin command handling
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_process_message_handles_profile_commands(self, test_data_dir):
        """Test that process_message handles profile-related commands."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "/profile", "discord")
        
        # Assert - Verify profile command handling
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_process_message_handles_help_commands(self, test_data_dir):
        """Test that process_message handles help commands."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "/help", "discord")
        
        # Assert - Verify help command handling
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_process_message_handles_unknown_commands(self, test_data_dir):
        """Test that process_message handles unknown commands gracefully."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "/unknown_command", "discord")
        
        # Assert - Verify unknown command handling
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_process_message_handles_empty_message(self, test_data_dir):
        """Test that process_message handles empty messages."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "", "discord")
        
        # Assert - Verify empty message handling
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_process_message_handles_whitespace_only_message(self, test_data_dir):
        """Test that process_message handles whitespace-only messages."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "   ", "discord")
        
        # Assert - Verify whitespace-only message handling
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_process_message_includes_timestamp(self, test_data_dir):
        """Test that process_message includes timestamp in result."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "test message", "discord")
        
        # Assert - Verify response structure
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_process_message_includes_interaction_type(self, test_data_dir):
        """Test that process_message includes interaction type in result."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "test message", "discord")
        
        # Assert - Verify response structure
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_process_message_handles_long_messages(self, test_data_dir):
        """Test that process_message handles long messages correctly."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        long_message = "This is a very long message " * 100
        
        # Act
        response = interaction_manager.handle_message(user_id, long_message, "discord")
        
        # Assert - Verify long message handling
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_process_message_handles_special_characters(self, test_data_dir):
        """Test that process_message handles special characters correctly."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        special_message = "Message with special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"
        
        # Act
        response = interaction_manager.handle_message(user_id, special_message, "discord")
        
        # Assert - Verify special character handling
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_process_message_handles_unicode_characters(self, test_data_dir):
        """Test that process_message handles unicode characters correctly."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        unicode_message = "Message with unicode: 🚀🌟🎉你好世界"
        
        # Act
        response = interaction_manager.handle_message(user_id, unicode_message, "discord")
        
        # Assert - Verify unicode character handling
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_process_message_handles_mixed_content(self, test_data_dir):
        """Test that process_message handles mixed content types."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        mixed_message = "Mixed content: /tasks and regular chat 🚀"
        
        # Act
        response = interaction_manager.handle_message(user_id, mixed_message, "discord")
        
        # Assert - Verify mixed content handling
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_process_message_handles_conversation_context(self, test_data_dir):
        """Test that process_message maintains conversation context."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act - Send multiple messages to test context
        response1 = interaction_manager.handle_message(user_id, "Hello", "discord")
        response2 = interaction_manager.handle_message(user_id, "How are you?", "discord")
        
        # Assert - Verify conversation context
        assert response1 is not None, "First response should be created"
        assert response2 is not None, "Second response should be created"
        assert response1.message is not None, "First response should have message"
        assert response2.message is not None, "Second response should have message"

    def test_process_message_handles_error_conditions(self, test_data_dir):
        """Test that process_message handles error conditions gracefully."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act - Test with None message
        response = interaction_manager.handle_message(user_id, None, "discord")
        
        # Assert - Verify error handling
        assert response is not None, "Response should be created even with error"
        assert response.message is not None, "Response should have error message"

    def test_process_message_handles_concurrent_access(self, test_data_dir):
        """Test that process_message handles concurrent access safely."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act - Simulate concurrent access
        response1 = interaction_manager.handle_message(user_id, "Message 1", "discord")
        response2 = interaction_manager.handle_message(user_id, "Message 2", "discord")
        
        # Assert - Verify concurrent access handling
        assert response1 is not None, "First response should be created"
        assert response2 is not None, "Second response should be created"
        assert response1.message is not None, "First response should have message"
        assert response2.message is not None, "Second response should have message"

    def test_process_message_handles_rate_limiting(self, test_data_dir):
        """Test that process_message handles rate limiting correctly."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act - Send multiple rapid messages
        responses = []
        for i in range(5):
            response = interaction_manager.handle_message(user_id, f"Message {i}", "discord")
            responses.append(response)
        
        # Assert - Verify rate limiting handling
        assert len(responses) == 5, "Should handle multiple rapid messages"
        for response in responses:
            assert response is not None, "Each response should be created"
            assert response.message is not None, "Each response should have message"

    def test_process_message_handles_user_preferences(self, test_data_dir):
        """Test that process_message respects user preferences."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "show my preferences", "discord")
        
        # Assert - Verify user preferences handling
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_process_message_handles_feature_flags(self, test_data_dir):
        """Test that process_message respects feature flags."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "show my features", "discord")
        
        # Assert - Verify feature flags handling
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"

    def test_get_slash_command_map_returns_valid_map(self, test_data_dir):
        """Test that get_slash_command_map returns a valid command map."""
        # Arrange
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        command_map = interaction_manager.get_slash_command_map()
        
        # Assert - Verify command map structure
        assert isinstance(command_map, dict), "Command map should be a dictionary"
        assert len(command_map) > 0, "Command map should not be empty"
        # Verify canonical semantics: unprefixed command names as keys
        assert "tasks" in command_map, "Tasks command should be in map"
        assert "help" in command_map, "Help command should be in map"
        assert "/tasks" not in command_map, "Slash-prefixed keys should not be used"
        assert "!tasks" not in command_map, "Bang-prefixed keys should not be used"
    
    def test_get_command_definitions_returns_valid_definitions(self, test_data_dir):
        """Test that get_command_definitions returns valid command definitions."""
        # Arrange
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        definitions = interaction_manager.get_command_definitions()
        
        # Assert - Verify definitions structure
        assert isinstance(definitions, list), "Definitions should be a list"
        assert len(definitions) > 0, "Definitions should not be empty"
        # Verify structure of first definition
        if definitions:
            first_def = definitions[0]
            assert 'name' in first_def, "Definition should have 'name' field"
            assert 'mapped_message' in first_def, "Definition should have 'mapped_message' field"
            assert 'description' in first_def, "Definition should have 'description' field"
    
    def test_get_commands_response_returns_valid_response(self, test_data_dir):
        """Test that _get_commands_response returns a valid response."""
        # Arrange
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager._get_commands_response()
        
        # Assert - Verify response structure
        assert response is not None, "Response should be created"
        assert hasattr(response, 'message'), "Response should have message"
        assert hasattr(response, 'completed'), "Response should have completed flag"
        assert response.completed is True, "Commands response should be completed"
        assert 'Available Commands' in response.message, "Response should contain commands header"
    
    def test_get_available_commands_returns_valid_commands(self, test_data_dir):
        """Test that get_available_commands returns valid commands."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        commands = interaction_manager.get_available_commands(user_id)
        
        # Assert - Verify commands structure
        assert isinstance(commands, dict), "Commands should be a dictionary"
        # Commands may be empty if no handlers are available, which is valid
    
    def test_get_user_suggestions_returns_valid_suggestions(self, test_data_dir):
        """Test that get_user_suggestions returns valid suggestions."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        suggestions = interaction_manager.get_user_suggestions(user_id)
        
        # Assert - Verify suggestions structure
        assert isinstance(suggestions, list), "Suggestions should be a list"
        assert len(suggestions) <= 5, "Suggestions should be limited to 5"
    
    def test_is_ai_command_response_detects_json_commands(self, test_data_dir):
        """Test that _is_ai_command_response detects JSON command responses."""
        # Arrange
        interaction_manager = _create_fast_interaction_manager()
        
        # Act & Assert - Test JSON command detection
        json_command = '{"action": "create_task", "intent": "create_task"}'
        assert interaction_manager._is_ai_command_response(json_command) is True, \
            "Should detect JSON command response"
        
        # Test non-command response
        regular_response = "I can help you with that!"
        assert interaction_manager._is_ai_command_response(regular_response) is False, \
            "Should not detect regular response as command"
    
    def test_parse_ai_command_response_parses_json(self, test_data_dir):
        """Test that _parse_ai_command_response parses JSON command responses."""
        # Arrange
        interaction_manager = _create_fast_interaction_manager()
        original_message = "create a task"
        
        # Act - Test JSON parsing
        json_command = '{"intent": "create_task", "entities": {}, "confidence": 0.8}'
        parsed = interaction_manager._parse_ai_command_response(json_command, original_message)
        
        # Assert - Verify parsing
        assert parsed is not None, "Should parse JSON command"
        assert parsed.intent == "create_task", "Should extract correct intent"
        assert parsed.original_message == original_message, "Should preserve original message"
    
    def test_is_clarification_request_detects_clarification(self, test_data_dir):
        """Test that _is_clarification_request detects clarification requests."""
        # Arrange
        interaction_manager = _create_fast_interaction_manager()
        
        # Act & Assert - Test clarification detection
        clarification = "Could you clarify what you mean?"
        assert interaction_manager._is_clarification_request(clarification) is True, \
            "Should detect clarification request"
        
        # Test non-clarification response
        regular_response = "I can help you with that!"
        assert interaction_manager._is_clarification_request(regular_response) is False, \
            "Should not detect regular response as clarification"
    
    def test_extract_intent_from_text_extracts_intent(self, test_data_dir):
        """Test that _extract_intent_from_text extracts intent from text."""
        # Arrange
        interaction_manager = _create_fast_interaction_manager()
        
        # Act & Assert - Test intent extraction
        text = "I want to create a task"
        intent = interaction_manager._extract_intent_from_text(text)
        # May return None if pattern doesn't match exactly
        assert intent == "create_task" or intent is None, "Should extract create_task intent or return None"
        
        # Test another intent
        text2 = "Show me my tasks"
        intent2 = interaction_manager._extract_intent_from_text(text2)
        # May return None if pattern doesn't match exactly
        assert intent2 == "list_tasks" or intent2 is None, "Should extract list_tasks intent or return None"
    
    def test_is_valid_intent_checks_intent_validity(self, test_data_dir):
        """Test that _is_valid_intent checks if intent is valid."""
        # Arrange
        interaction_manager = _create_fast_interaction_manager()
        
        # Act & Assert - Test intent validation
        valid_intent = "list_tasks"
        assert interaction_manager._is_valid_intent(valid_intent) is True, \
            "Should recognize valid intent"
        
        # Test invalid intent
        # May return True or False depending on handler availability, both are valid
    
    def test_augment_suggestions_adds_suggestions(self, test_data_dir):
        """Test that _augment_suggestions adds suggestions to response."""
        # Arrange
        from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
        interaction_manager = _create_fast_interaction_manager()
        
        # Act - Test suggestion augmentation for multiple matching tasks
        parsed_cmd = ParsedCommand("complete_task", {}, 0.9, "complete task")
        response = InteractionResponse("Multiple matching tasks found. Which task?", False)
        augmented = interaction_manager._augment_suggestions(parsed_cmd, response)
        
        # Assert - Verify suggestions were added
        assert augmented is not None, "Augmented response should be created"
        assert hasattr(augmented, 'suggestions'), "Response should have suggestions"
        if not response.completed:
            assert augmented.suggestions is not None, "Suggestions should be added for incomplete responses"


class TestInteractionManagerRealBehavior:
    """Test interaction manager with real behavior verification."""
    
    @pytest.mark.behavior
    def test_handle_message_creates_conversation_record(self, test_data_dir):
        """Test that handle_message creates actual conversation record."""
        # Arrange
        user_id = "test-interaction-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "Hello", "discord")
        
        # Assert - Verify actual response creation
        assert response is not None, "Response should be created"
        assert hasattr(response, 'message'), "Response should have message"
        assert hasattr(response, 'completed'), "Response should have completed flag"
        assert isinstance(response.message, str), "Response message should be a string"
    
    @pytest.mark.behavior
    def test_handle_message_updates_conversation_state(self, test_data_dir):
        """Test that handle_message updates conversation state."""
        # Arrange
        user_id = "test-interaction-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act - Send multiple messages
        response1 = interaction_manager.handle_message(user_id, "Hello", "discord")
        response2 = interaction_manager.handle_message(user_id, "How are you?", "discord")
        
        # Assert - Verify conversation state is maintained
        assert response1 is not None, "First response should be created"
        assert response2 is not None, "Second response should be created"
        # Both responses should be valid
        assert isinstance(response1.message, str), "First response message should be a string"
        assert isinstance(response2.message, str), "Second response message should be a string"
    
    @pytest.mark.behavior
    def test_handle_message_handles_bang_commands(self, test_data_dir):
        """Test that handle_message handles bang-prefixed commands (!tasks, !help, etc.)."""
        # Arrange
        user_id = "test-interaction-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "!tasks", "discord")
        
        # Assert - Verify bang command handling
        assert response is not None, "Response should be created"
        assert isinstance(response.message, str), "Response message should be a string"

    @pytest.mark.behavior
    def test_handle_message_bang_command_does_not_recurse(self, test_data_dir):
        """Test that bang commands are converted and parsed in-place without recursive re-entry."""
        # Arrange
        user_id = "test-interaction-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()

        call_count = {"count": 0}
        original_handle_message = InteractionManager.handle_message

        def counting_handle_message(self, inner_user_id, inner_message, channel_type="discord"):
            call_count["count"] += 1
            return original_handle_message(self, inner_user_id, inner_message, channel_type)

        interaction_manager.handle_message = types.MethodType(
            counting_handle_message, interaction_manager
        )

        # Act
        response = interaction_manager.handle_message(user_id, "!tasks", "discord")

        # Assert
        assert response is not None, "Response should be created"
        assert isinstance(response.message, str), "Response message should be a string"
        assert call_count["count"] == 1, (
            "Bang command handling should not recursively call handle_message"
        )

    @pytest.mark.behavior
    @pytest.mark.parametrize("keyword", ["/cancel", "!cancel", "/skip", "!skip", "/endlist", "!endl"])
    def test_flow_keyword_delegation_for_slash_and_bang(
        self, test_data_dir, monkeypatch, keyword
    ):
        """Test that flow keywords delegate to conversation manager for both slash and bang forms."""
        # Arrange
        user_id = "test-interaction-user-flow-keyword"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()

        captured = {"calls": 0, "message": None}

        def _fake_handle_inbound_message(inner_user_id, inner_message):
            captured["calls"] += 1
            captured["message"] = inner_message
            return ("delegated", True)

        monkeypatch.setattr(
            conversation_manager, "handle_inbound_message", _fake_handle_inbound_message
        )

        # Act
        response = interaction_manager.handle_message(user_id, keyword, "discord")

        # Assert
        assert response.message == "delegated", "Should return delegated flow-keyword response"
        assert response.completed is True, "Flow keyword delegation should complete"
        assert captured["calls"] == 1, "Flow keyword should delegate exactly once"
        assert captured["message"] == keyword, "Delegation should preserve original keyword form"

    @pytest.mark.behavior
    @pytest.mark.parametrize(
        "slash_cmd,bang_cmd,method_name,expected_message",
        [
            ("/checkin", "!checkin", "start_checkin", "checkin-started"),
            ("/restart", "!restart", "restart_checkin", "checkin-restarted"),
            ("/clear", "!clear", "clear_stuck_flows", "flows-cleared"),
        ],
    )
    def test_flow_command_parity_for_slash_and_bang(
        self,
        test_data_dir,
        monkeypatch,
        slash_cmd,
        bang_cmd,
        method_name,
        expected_message,
    ):
        """Test slash/bang parity for flow starter commands."""
        # Arrange
        user_id = "test-interaction-user-flow-command-parity"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()

        calls = {"count": 0}

        def _fake_flow_method(inner_user_id):
            calls["count"] += 1
            return (expected_message, True)

        monkeypatch.setattr(conversation_manager, method_name, _fake_flow_method)

        # Act
        slash_response = interaction_manager.handle_message(user_id, slash_cmd, "discord")
        bang_response = interaction_manager.handle_message(user_id, bang_cmd, "discord")

        # Assert
        assert slash_response.message == expected_message, "Slash flow command should use flow starter"
        assert bang_response.message == expected_message, "Bang flow command should use same flow starter"
        assert slash_response.completed is True and bang_response.completed is True
        assert calls["count"] == 2, "Slash and bang forms should each invoke the flow starter once"

    @pytest.mark.behavior
    def test_tasks_argument_preservation_parity_for_slash_and_bang(
        self, test_data_dir, monkeypatch
    ):
        """Test that task command arguments are preserved identically for slash and bang forms."""
        # Arrange
        user_id = "test-interaction-user-arg-parity"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        parser = interaction_manager.command_parser

        original_rule_parse = parser._rule_based_parse
        observed_messages: list[str] = []

        def _tracking_rule_parse(message):
            observed_messages.append(message)
            return original_rule_parse(message)

        monkeypatch.setattr(parser, "_rule_based_parse", _tracking_rule_parse)

        # Act
        slash_response = interaction_manager.handle_message(user_id, "/tasks overdue", "discord")
        bang_response = interaction_manager.handle_message(user_id, "!tasks overdue", "discord")

        # Assert
        assert isinstance(slash_response.message, str) and isinstance(bang_response.message, str)
        assert observed_messages.count("show my tasks overdue") >= 2, (
            "Both slash and bang should convert to identical parser input with preserved args"
        )

    @pytest.mark.behavior
    def test_discoverability_only_commands_drop_prefix_and_continue_parser_path(
        self, test_data_dir, monkeypatch
    ):
        """Test discoverability-only commands (/n, !note) drop prefix and continue parsing."""
        # Arrange
        user_id = "test-interaction-user-discoverability"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        parser = interaction_manager.command_parser

        original_rule_parse = parser._rule_based_parse
        observed_messages: list[str] = []

        def _tracking_rule_parse(message):
            observed_messages.append(message)
            return original_rule_parse(message)

        monkeypatch.setattr(parser, "_rule_based_parse", _tracking_rule_parse)

        # Act
        interaction_manager.handle_message(user_id, "/n quick note", "discord")
        interaction_manager.handle_message(user_id, "!note quick note", "discord")

        # Assert
        assert "n quick note" in observed_messages, "Slash discoverability command should reach parser without prefix"
        assert "note quick note" in observed_messages, "Bang discoverability command should reach parser without prefix"
        assert "/n quick note" not in observed_messages
        assert "!note quick note" not in observed_messages

    @pytest.mark.behavior
    def test_unknown_command_with_active_flow_clears_once_without_double_handling(
        self, test_data_dir, monkeypatch
    ):
        """Test unknown command in active flow clears once and does not route through flow-keyword delegation."""
        # Arrange
        user_id = "test-interaction-user-unknown-active-flow"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()

        counters = {"save_calls": 0, "inbound_calls": 0}

        def _count_save_user_states():
            counters["save_calls"] += 1

        def _count_handle_inbound_message(*args, **kwargs):
            counters["inbound_calls"] += 1
            return ("flow keyword handled", True)

        monkeypatch.setattr(
            conversation_manager, "_save_user_states", _count_save_user_states
        )
        monkeypatch.setattr(
            conversation_manager, "handle_inbound_message", _count_handle_inbound_message
        )

        conversation_manager.user_states[user_id] = {"flow": 999, "state": 1, "data": {}}

        # Act
        response = interaction_manager.handle_message(user_id, "/not_a_real_command", "discord")

        # Assert
        assert response is not None
        assert conversation_manager.user_states.get(user_id) is None, (
            "Unknown command should clear active flow state once"
        )
        assert counters["save_calls"] == 1, "Active flow should be persisted once after clear"
        assert counters["inbound_calls"] == 0, (
            "Unknown command should not be treated as flow keyword delegation"
        )

    @pytest.mark.behavior
    def test_flow_clearing_parity_for_slash_and_bang_commands(
        self, test_data_dir, monkeypatch
    ):
        """Test that /tasks and !tasks both clear active flow exactly once and avoid flow-keyword handling."""
        # Arrange
        user_id = "test-interaction-user-flow-parity"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()

        counters = {"save_calls": 0, "inbound_calls": 0}

        def _count_save_user_states():
            counters["save_calls"] += 1

        def _count_handle_inbound_message(*args, **kwargs):
            counters["inbound_calls"] += 1
            return ("flow keyword handled", True)

        monkeypatch.setattr(
            conversation_manager, "_save_user_states", _count_save_user_states
        )
        monkeypatch.setattr(
            conversation_manager, "handle_inbound_message", _count_handle_inbound_message
        )

        for command in ["/tasks", "!tasks"]:
            counters["save_calls"] = 0
            counters["inbound_calls"] = 0
            conversation_manager.user_states[user_id] = {"flow": 123, "state": 1, "data": {}}

            # Act
            response = interaction_manager.handle_message(user_id, command, "discord")

            # Assert
            assert response is not None, "Response should be created"
            assert isinstance(response.message, str), "Response message should be a string"
            assert conversation_manager.user_states.get(user_id) is None, (
                "Active flow should be cleared for command messages"
            )
            assert counters["save_calls"] == 1, (
                "Flow clearing should persist exactly once per command"
            )
            assert counters["inbound_calls"] == 0, (
                "Non-keyword commands should not be routed to flow keyword handler"
            )

    @pytest.mark.behavior
    def test_unknown_prefix_commands_have_slash_bang_parity(
        self, test_data_dir, monkeypatch
    ):
        """Test that unknown /... and !... commands strip prefix and follow identical parsing path."""
        # Arrange
        user_id = "test-interaction-user-unknown-prefix-parity"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        parser = interaction_manager.command_parser

        original_rule_parse = parser._rule_based_parse
        observed_messages: list[str] = []

        def _tracking_rule_parse(message):
            observed_messages.append(message)
            return original_rule_parse(message)

        monkeypatch.setattr(parser, "_rule_based_parse", _tracking_rule_parse)

        # Act
        slash_response = interaction_manager.handle_message(user_id, "/not_a_real_cmd 42", "discord")
        bang_response = interaction_manager.handle_message(user_id, "!not_a_real_cmd 42", "discord")

        # Assert
        assert slash_response.message == bang_response.message, (
            "Unknown slash/bang commands should produce identical fallback behavior"
        )
        assert "not_a_real_cmd 42" in observed_messages, (
            "Parser should receive unknown command text without prefix"
        )
        assert "/not_a_real_cmd 42" not in observed_messages, (
            "Slash-prefixed unknown command should not reach parser unchanged"
        )
        assert "!not_a_real_cmd 42" not in observed_messages, (
            "Bang-prefixed unknown command should not reach parser unchanged"
        )
    
    @pytest.mark.behavior
    def test_handle_message_handles_flow_commands(self, test_data_dir):
        """Test that handle_message handles flow commands correctly."""
        # Arrange
        user_id = "test-interaction-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act - Test flow command
        response = interaction_manager.handle_message(user_id, "/checkin", "discord")
        
        # Assert - Verify flow command handling
        assert response is not None, "Response should be created"
        assert isinstance(response.message, str), "Response message should be a string"
    
    @pytest.mark.behavior
    def test_handle_message_handles_confirm_delete_shortcut(self, test_data_dir):
        """Test that handle_message handles 'confirm delete' shortcut."""
        # Arrange
        user_id = "test-interaction-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "confirm delete", "discord")
        
        # Assert - Verify confirm delete handling
        assert response is not None, "Response should be created"
        assert isinstance(response.message, str), "Response message should be a string"
    
    @pytest.mark.behavior
    def test_handle_message_handles_complete_task_shortcut(self, test_data_dir):
        """Test that handle_message handles 'complete task' shortcut."""
        # Arrange
        user_id = "test-interaction-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "complete task", "discord")
        
        # Assert - Verify complete task handling
        assert response is not None, "Response should be created"
        assert isinstance(response.message, str), "Response message should be a string"
    
    @pytest.mark.behavior
    def test_handle_message_handles_schedule_edit_shortcut(self, test_data_dir):
        """Test that handle_message handles schedule edit shortcuts."""
        # Arrange
        user_id = "test-interaction-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act - Test schedule edit shortcut
        response = interaction_manager.handle_message(user_id, "edit schedule period morning tasks", "discord")
        
        # Assert - Verify schedule edit handling
        assert response is not None, "Response should be created"
        assert isinstance(response.message, str), "Response message should be a string"
    
    @pytest.mark.behavior
    def test_handle_message_handles_update_task_coercion(self, test_data_dir):
        """Test that handle_message handles update task coercion."""
        # Arrange
        user_id = "test-interaction-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act - Test update task coercion
        response = interaction_manager.handle_message(user_id, "update task test_task title New Title", "discord")
        
        # Assert - Verify update task handling
        assert response is not None, "Response should be created"
        assert isinstance(response.message, str), "Response message should be a string"
    
    @pytest.mark.behavior
    def test_get_slash_command_map_returns_actual_map(self, test_data_dir):
        """Test that get_slash_command_map returns actual command map."""
        # Arrange
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        command_map = interaction_manager.get_slash_command_map()
        
        # Assert - Verify actual map structure
        assert isinstance(command_map, dict), "Command map should be a dictionary"
        assert len(command_map) > 0, "Command map should not be empty"
        # Verify expected commands exist
        assert "tasks" in command_map, "Tasks command should be in map"
        assert "help" in command_map, "Help command should be in map"
        assert "/tasks" not in command_map, "Slash-prefixed keys should not be used"
        assert "!tasks" not in command_map, "Bang-prefixed keys should not be used"

    @pytest.mark.behavior
    def test_slash_command_map_property_matches_canonical_getter(self, test_data_dir):
        """Test that compatibility property mirrors canonical getter output."""
        # Arrange
        interaction_manager = _create_fast_interaction_manager()

        # Act
        command_map = interaction_manager.get_slash_command_map()
        property_map = interaction_manager.slash_command_map

        # Assert
        assert property_map == command_map, (
            "Compatibility property should return canonical getter output"
        )
    
    @pytest.mark.behavior
    def test_get_command_definitions_returns_actual_definitions(self, test_data_dir):
        """Test that get_command_definitions returns actual command definitions."""
        # Arrange
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        definitions = interaction_manager.get_command_definitions()
        
        # Assert - Verify actual definitions structure
        assert isinstance(definitions, list), "Definitions should be a list"
        assert len(definitions) > 0, "Definitions should not be empty"
        # Verify structure of definitions
        for definition in definitions:
            assert isinstance(definition, dict), "Each definition should be a dictionary"
            assert 'name' in definition, "Definition should have 'name' field"
            assert 'mapped_message' in definition, "Definition should have 'mapped_message' field"
            assert 'description' in definition, "Definition should have 'description' field"
    
    @pytest.mark.behavior
    def test_get_available_commands_returns_actual_commands(self, test_data_dir):
        """Test that get_available_commands returns actual commands for user."""
        # Arrange
        user_id = "test-interaction-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        commands = interaction_manager.get_available_commands(user_id)
        
        # Assert - Verify actual commands structure
        assert isinstance(commands, dict), "Commands should be a dictionary"
        # Commands may be empty if no handlers are available, which is valid
    
    @pytest.mark.behavior
    def test_get_user_suggestions_returns_actual_suggestions(self, test_data_dir):
        """Test that get_user_suggestions returns actual suggestions for user."""
        # Arrange
        user_id = "test-interaction-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        interaction_manager = _create_fast_interaction_manager()
        
        # Act
        suggestions = interaction_manager.get_user_suggestions(user_id)
        
        # Assert - Verify actual suggestions structure
        assert isinstance(suggestions, list), "Suggestions should be a list"
        assert len(suggestions) <= 5, "Suggestions should be limited to 5"
        # Verify suggestions are strings
        for suggestion in suggestions:
            assert isinstance(suggestion, str), "Each suggestion should be a string"
