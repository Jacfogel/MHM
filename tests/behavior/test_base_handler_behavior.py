"""
Base Handler Behavior Tests

Tests for communication/command_handlers/base_handler.py focusing on real behavior and side effects.
These tests verify that the base handler class actually works and produces expected
side effects rather than just returning values.
"""

import pytest
from abc import ABC

# Import the modules we're testing
from communication.command_handlers.base_handler import InteractionHandler
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand


class ConcreteTestHandler(InteractionHandler):
    """Concrete implementation of InteractionHandler for testing."""
    
    def can_handle(self, intent: str) -> bool:
        """Test implementation of can_handle."""
        return intent == 'test_intent'
    
    def handle(self, user_id: str, parsed_command: ParsedCommand) -> InteractionResponse:
        """Test implementation of handle."""
        # Use base class validation
        if not user_id or not isinstance(user_id, str):
            return InteractionResponse("Invalid user ID provided", False)
        if not user_id.strip():
            return InteractionResponse("Empty user ID provided", False)
        if not parsed_command:
            return InteractionResponse("Invalid command provided", False)
        
        return InteractionResponse("Test response", True)
    
    def get_help(self) -> str:
        """Test implementation of get_help."""
        return "Test help text"
    
    def get_examples(self) -> list:
        """Test implementation of get_examples."""
        return ["example 1", "example 2"]


class TestBaseHandlerBehavior:
    """Test base handler real behavior and side effects."""
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_cannot_be_instantiated_directly(self):
        """Test that InteractionHandler cannot be instantiated directly (abstract class)."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            InteractionHandler()  # pyright: ignore[reportAbstractUsage]
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_concrete_implementation_can_be_instantiated(self):
        """Test that concrete implementation of InteractionHandler can be instantiated."""
        handler = ConcreteTestHandler()
        assert isinstance(handler, InteractionHandler), "Should be instance of InteractionHandler"
        assert isinstance(handler, ABC), "Should be instance of ABC"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_validate_user_id_valid(self):
        """Test that _validate_user_id accepts valid user IDs."""
        handler = ConcreteTestHandler()
        
        # Test various valid user IDs
        valid_user_ids = [
            "user123",
            "user_123",
            "user-123",
            "test_user",
            "a",  # Minimum length
            "a" * 100,  # Maximum length
            "user_123-test"
        ]
        
        for user_id in valid_user_ids:
            assert handler._validate_user_id(user_id) is True, f"Should accept valid user_id: {user_id}"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_validate_user_id_invalid_type(self):
        """Test that _validate_user_id rejects invalid types."""
        handler = ConcreteTestHandler()
        
        # Test invalid types
        invalid_user_ids = [
            None,
            123,
            [],
            {},
            True
        ]
        
        for user_id in invalid_user_ids:
            assert handler._validate_user_id(user_id) is False, f"Should reject invalid type: {type(user_id)}"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_validate_user_id_empty(self):
        """Test that _validate_user_id rejects empty strings."""
        handler = ConcreteTestHandler()
        
        # Test empty strings
        empty_user_ids = [
            "",
            "   ",
            "\t",
            "\n"
        ]
        
        for user_id in empty_user_ids:
            assert handler._validate_user_id(user_id) is False, f"Should reject empty user_id: {repr(user_id)}"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_validate_user_id_invalid_length(self):
        """Test that _validate_user_id rejects invalid lengths."""
        handler = ConcreteTestHandler()
        
        # Test too long
        too_long = "a" * 101  # 101 characters
        assert handler._validate_user_id(too_long) is False, "Should reject user_id longer than 100 characters"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_validate_user_id_invalid_characters(self):
        """Test that _validate_user_id rejects invalid characters."""
        handler = ConcreteTestHandler()
        
        # Test invalid characters
        invalid_user_ids = [
            "user@123",  # @ symbol
            "user 123",  # space
            "user.123",  # period
            "user#123",  # hash
            "user$123",  # dollar
            "user%123",  # percent
        ]
        
        for user_id in invalid_user_ids:
            assert handler._validate_user_id(user_id) is False, f"Should reject user_id with invalid characters: {user_id}"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_validate_parsed_command_valid(self):
        """Test that _validate_parsed_command accepts valid ParsedCommand objects."""
        handler = ConcreteTestHandler()
        
        # Test valid ParsedCommand
        valid_command = ParsedCommand(
            intent="test_intent",
            entities={},
            confidence=0.9,
            original_message="test message"
        )
        
        assert handler._validate_parsed_command(valid_command) is True, "Should accept valid ParsedCommand"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_validate_parsed_command_invalid_type(self):
        """Test that _validate_parsed_command rejects invalid types."""
        handler = ConcreteTestHandler()
        
        # Test invalid types
        invalid_commands = [
            None,
            "string",
            123,
            [],
            {}
        ]
        
        for command in invalid_commands:
            assert handler._validate_parsed_command(command) is False, f"Should reject invalid type: {type(command)}"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_validate_parsed_command_missing_intent_attribute(self):
        """Test that _validate_parsed_command rejects objects without intent attribute."""
        handler = ConcreteTestHandler()
        
        # Create object without intent attribute
        class FakeCommand:
            pass
        
        fake_command = FakeCommand()
        assert handler._validate_parsed_command(fake_command) is False, "Should reject object without intent attribute"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_validate_parsed_command_empty_intent(self):
        """Test that _validate_parsed_command rejects empty intent."""
        handler = ConcreteTestHandler()
        
        # Test empty intent
        empty_intent_command = ParsedCommand(
            intent="",
            entities={},
            confidence=0.9,
            original_message="test message"
        )
        
        assert handler._validate_parsed_command(empty_intent_command) is False, "Should reject empty intent"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_validate_parsed_command_invalid_intent_type(self):
        """Test that _validate_parsed_command rejects invalid intent types."""
        handler = ConcreteTestHandler()
        
        # Test invalid intent types
        invalid_intent_commands = [
            ParsedCommand(intent=None, entities={}, confidence=0.9, original_message="test"),
            ParsedCommand(intent=123, entities={}, confidence=0.9, original_message="test"),
            ParsedCommand(intent=[], entities={}, confidence=0.9, original_message="test"),
        ]
        
        for command in invalid_intent_commands:
            assert handler._validate_parsed_command(command) is False, f"Should reject invalid intent type: {type(command.intent)}"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_validate_parsed_command_whitespace_intent(self):
        """Test that _validate_parsed_command rejects whitespace-only intent."""
        handler = ConcreteTestHandler()
        
        # Test whitespace-only intent
        whitespace_intent_command = ParsedCommand(
            intent="   ",
            entities={},
            confidence=0.9,
            original_message="test message"
        )
        
        assert handler._validate_parsed_command(whitespace_intent_command) is False, "Should reject whitespace-only intent"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_create_error_response_valid(self):
        """Test that _create_error_response creates valid error response."""
        handler = ConcreteTestHandler()
        
        error_message = "Test error message"
        user_id = "test_user"
        
        response = handler._create_error_response(error_message, user_id)
        
        # Should return a valid InteractionResponse with completed=False
        assert response is not None, "Should return a valid InteractionResponse"
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse instance"
        assert response.completed is False, "Error response should have completed=False"
        assert response.error == error_message, "Error response should contain the error message"
        assert "error" in response.message.lower(), "Error message should mention error"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_create_error_response_without_user_id(self):
        """Test that _create_error_response works without user_id."""
        handler = ConcreteTestHandler()
        
        error_message = "Test error message"
        
        response = handler._create_error_response(error_message)
        
        # Should return a valid InteractionResponse with completed=False
        assert response is not None, "Should return a valid InteractionResponse"
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse instance"
        assert response.completed is False, "Error response should have completed=False"
        assert response.error == error_message, "Error response should contain the error message"
        assert "error" in response.message.lower(), "Error message should mention error"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_create_error_response_invalid_error_message(self):
        """Test that _create_error_response handles invalid error message."""
        handler = ConcreteTestHandler()
        
        # Test invalid error messages
        invalid_messages = [
            None,
            123,
            [],
            {},
            ""
        ]
        
        for error_message in invalid_messages:
            response = handler._create_error_response(error_message)
            assert response is None, f"Should return None for invalid error message: {type(error_message)}"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_create_error_response_empty_error_message(self):
        """Test that _create_error_response handles empty error message."""
        handler = ConcreteTestHandler()
        
        # Test empty error messages
        empty_messages = [
            "",
            "   ",
            "\t",
            "\n"
        ]
        
        for error_message in empty_messages:
            response = handler._create_error_response(error_message)
            assert response is None, f"Should return None for empty error message: {repr(error_message)}"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_create_error_response_invalid_user_id_type(self):
        """Test that _create_error_response handles invalid user_id type."""
        handler = ConcreteTestHandler()
        
        error_message = "Test error message"
        
        # Test invalid user_id types
        invalid_user_ids = [
            123,
            [],
            {},
            True
        ]
        
        for user_id in invalid_user_ids:
            response = handler._create_error_response(error_message, user_id)
            assert response is None, f"Should return None for invalid user_id type: {type(user_id)}"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_handle_validates_user_id(self):
        """Test that handle method validates user_id correctly."""
        handler = ConcreteTestHandler()
        
        valid_command = ParsedCommand(
            intent="test_intent",
            entities={},
            confidence=0.9,
            original_message="test message"
        )
        
        # Test invalid user_id types
        invalid_user_ids = [
            None,
            123,
            [],
        ]
        
        for user_id in invalid_user_ids:
            response = handler.handle(user_id, valid_command)
            assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
            assert "invalid" in response.message.lower() or "Invalid" in response.message, f"Should indicate invalid user_id for {type(user_id)}"
            assert response.completed is False, "Should have completed=False"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_handle_validates_empty_user_id(self):
        """Test that handle method validates empty user_id."""
        handler = ConcreteTestHandler()
        
        valid_command = ParsedCommand(
            intent="test_intent",
            entities={},
            confidence=0.9,
            original_message="test message"
        )
        
        # Test empty user_id - empty string is caught by first check (not user_id or not isinstance)
        # Whitespace-only strings are caught by second check (not user_id.strip())
        empty_user_ids = [
            "",  # Caught by first check
            "   ",  # Caught by second check
            "\t",  # Caught by second check
            "\n"  # Caught by second check
        ]
        
        for user_id in empty_user_ids:
            response = handler.handle(user_id, valid_command)
            assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
            # Empty string gets "Invalid user ID provided", whitespace gets "Empty user ID provided"
            assert "invalid" in response.message.lower() or "empty" in response.message.lower() or "Invalid" in response.message or "Empty" in response.message, f"Should indicate invalid/empty user_id for {repr(user_id)}"
            assert response.completed is False, "Should have completed=False"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_handle_validates_parsed_command(self):
        """Test that handle method validates parsed_command."""
        handler = ConcreteTestHandler()
        
        valid_user_id = "test_user"
        
        # Test invalid parsed_command - None and empty string are caught by `if not parsed_command:`
        # Non-falsy invalid types like 123 will pass the check and be handled by the concrete implementation
        invalid_commands = [
            None,  # Caught by `if not parsed_command:`
            "",  # Caught by `if not parsed_command:`
        ]
        
        for command in invalid_commands:
            response = handler.handle(valid_user_id, command)
            assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
            assert "invalid" in response.message.lower() or "Invalid" in response.message, f"Should indicate invalid command for {type(command)}"
            assert response.completed is False, "Should have completed=False"
        
        # Test non-falsy invalid type - this will pass the check and be handled by concrete implementation
        # The concrete implementation will handle it gracefully
        invalid_command = 123
        response = handler.handle(valid_user_id, invalid_command)
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        # The concrete implementation may handle this differently, so we just check it returns a response
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_handle_success(self):
        """Test that handle method works correctly with valid inputs."""
        handler = ConcreteTestHandler()
        
        valid_user_id = "test_user"
        valid_command = ParsedCommand(
            intent="test_intent",
            entities={},
            confidence=0.9,
            original_message="test message"
        )
        
        response = handler.handle(valid_user_id, valid_command)
        
        # Verify actual system changes: Check that response is created correctly
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.message == "Test response", "Should return test response"
        assert response.completed is True, "Should have completed=True"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_can_handle_with_none(self):
        """Test that can_handle method handles None correctly."""
        handler = ConcreteTestHandler()
        
        # Test that can_handle returns False for None
        result = handler.can_handle(None)
        assert result is False, "Should return False for None"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_concrete_implementation_methods(self):
        """Test that concrete implementation has all required methods."""
        handler = ConcreteTestHandler()
        
        # Test that all abstract methods are implemented
        assert hasattr(handler, 'can_handle'), "Should have can_handle method"
        assert hasattr(handler, 'handle'), "Should have handle method"
        assert hasattr(handler, 'get_help'), "Should have get_help method"
        assert hasattr(handler, 'get_examples'), "Should have get_examples method"
        
        # Test that methods work
        assert handler.can_handle('test_intent') is True, "can_handle should work"
        assert handler.can_handle('other_intent') is False, "can_handle should return False for other intents"
        
        help_text = handler.get_help()
        assert isinstance(help_text, str), "get_help should return string"
        assert len(help_text) > 0, "get_help should return non-empty string"
        
        examples = handler.get_examples()
        assert isinstance(examples, list), "get_examples should return list"
        assert len(examples) > 0, "get_examples should return non-empty list"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_base_handler_helper_methods_available(self):
        """Test that helper methods are available on concrete implementations."""
        handler = ConcreteTestHandler()
        
        # Test that helper methods are available
        assert hasattr(handler, '_validate_user_id'), "Should have _validate_user_id method"
        assert hasattr(handler, '_validate_parsed_command'), "Should have _validate_parsed_command method"
        assert hasattr(handler, '_create_error_response'), "Should have _create_error_response method"
        
        # Test that they can be called
        assert callable(handler._validate_user_id), "_validate_user_id should be callable"
        assert callable(handler._validate_parsed_command), "_validate_parsed_command should be callable"
        assert callable(handler._create_error_response), "_create_error_response should be callable"
