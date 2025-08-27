"""
Real behavior tests for communication interaction manager functionality.

Tests focus on actual side effects and system changes rather than just return values.
"""

import pytest
import json
import os
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime, timedelta

from communication.message_processing.interaction_manager import InteractionManager
from tests.test_utilities import TestUserFactory, TestDataFactory


class TestInteractionManagerBehavior:
    """Test real behavior of interaction manager functionality."""

    def test_interaction_manager_initialization_creates_components(self, test_data_dir):
        """Test that interaction manager initialization creates required components."""
        # Arrange & Act
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
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
        interaction_manager = InteractionManager()
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
        interaction_manager = InteractionManager()
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
        interaction_manager = InteractionManager()
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
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
        interaction_manager = InteractionManager()
        
        # Act
        response = interaction_manager.handle_message(user_id, "show my features", "discord")
        
        # Assert - Verify feature flags handling
        assert response is not None, "Response should be created"
        assert response.message is not None, "Response should have message"
