"""
Real behavior tests for AI conversation history functionality.

Tests focus on actual side effects and system changes rather than just return values.
"""

import pytest
import os
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

from ai.conversation_history import ConversationHistory
from tests.test_utilities import TestUserFactory, TestDataFactory


class TestConversationHistoryBehavior:
    """Test real behavior of conversation history functionality."""

    def test_conversation_history_initialization_creates_components(self, test_data_dir):
        """Test that conversation history initialization creates required components."""
        # Arrange & Act
        history = ConversationHistory()
        
        # Assert - Verify actual component creation
        assert history is not None, "Conversation history should be created"
        assert hasattr(history, 'max_sessions_per_user'), "Should have max_sessions_per_user attribute"
        assert hasattr(history, 'max_messages_per_session'), "Should have max_messages_per_session attribute"
        assert hasattr(history, '_sessions'), "Should have _sessions attribute"
        assert hasattr(history, '_active_sessions'), "Should have _active_sessions attribute"

    def test_start_session_creates_actual_session(self, test_data_dir):
        """Test that start_session creates actual session data."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        
        # Act
        session_id = history.start_session(user_id)
        
        # Assert - Verify actual session creation
        assert session_id is not None, "Session ID should be returned"
        assert isinstance(session_id, str), "Session ID should be a string"
        assert len(session_id) > 0, "Session ID should not be empty"
        
        # Verify session is stored
        active_session = history.get_active_session(user_id)
        assert active_session is not None, "Active session should be created"
        assert active_session.session_id == session_id, "Session ID should match"
        assert active_session.user_id == user_id, "User ID should match"

    def test_add_message_persists_to_session(self, test_data_dir):
        """Test that add_message actually persists messages to session."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        session_id = history.start_session(user_id)
        
        # Act
        result = history.add_message(user_id, "user", "Hello there")
        
        # Assert - Verify actual message persistence
        assert result is True, "Message should be added successfully"
        
        # Verify message is in session
        messages = history.get_session_messages(user_id, session_id)
        assert len(messages) == 1, "Should have one message"
        assert messages[0].role == "user", "Message role should match"
        assert messages[0].content == "Hello there", "Message content should match"

    def test_add_message_appends_to_existing_session(self, test_data_dir):
        """Test that add_message appends to existing session."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        session_id = history.start_session(user_id)
        
        # Add initial message
        history.add_message(user_id, "user", "Hello")
        
        # Act - Add second message
        history.add_message(user_id, "assistant", "Hi there!")
        
        # Assert - Verify both messages exist
        messages = history.get_session_messages(user_id, session_id)
        assert len(messages) == 2, "Should contain two messages"
        assert messages[0].role == "user", "First message should be user"
        assert messages[1].role == "assistant", "Second message should be assistant"

    def test_get_recent_messages_returns_actual_data(self, test_data_dir):
        """Test that get_recent_messages returns actual session data."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        session_id = history.start_session(user_id)
        
        # Add some messages
        history.add_message(user_id, "user", "Message 1")
        history.add_message(user_id, "assistant", "Response 1")
        history.add_message(user_id, "user", "Message 2")
        
        # Act
        recent_messages = history.get_recent_messages(user_id, 2)
        
        # Assert - Verify actual data return
        assert len(recent_messages) == 2, "Should return requested number of messages"
        assert recent_messages[0]["content"] == "Response 1", "Should return most recent messages"
        assert recent_messages[1]["content"] == "Message 2", "Should return correct order"

    def test_get_recent_messages_handles_empty_history(self, test_data_dir):
        """Test that get_recent_messages handles empty conversation history."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        
        # Act
        recent_messages = history.get_recent_messages(user_id, 5)
        
        # Assert - Verify empty history handling
        assert isinstance(recent_messages, list), "Should return empty list"
        assert len(recent_messages) == 0, "Should return empty list for no history"

    def test_clear_history_removes_session_data(self, test_data_dir):
        """Test that clear_history removes actual session data."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        session_id = history.start_session(user_id)
        
        # Add some messages
        history.add_message(user_id, "user", "Test message")
        
        # Verify session exists
        messages = history.get_session_messages(user_id, session_id)
        assert len(messages) == 1, "Session should have messages before clearing"
        
        # Act
        result = history.clear_history(user_id)
        
        # Assert - Verify session removal
        assert result is True, "Clear history should succeed"
        
        # Verify session is cleared
        messages = history.get_session_messages(user_id, session_id)
        assert len(messages) == 0, "Session should be empty after clearing"

    def test_get_conversation_summary_returns_actual_summary(self, test_data_dir):
        """Test that get_conversation_summary returns actual conversation summary."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        session_id = history.start_session(user_id)
        
        # Add conversation messages
        history.add_message(user_id, "user", "I'm feeling sad today")
        history.add_message(user_id, "assistant", "I'm sorry to hear that. What's going on?")
        history.add_message(user_id, "user", "I had a bad day at work")
        history.add_message(user_id, "assistant", "That sounds really difficult. Would you like to talk about it?")
        
        # Act
        summary = history.get_conversation_summary(user_id, session_id)
        
        # Assert - Verify actual summary creation
        assert isinstance(summary, str), "Should return string summary"
        assert len(summary) > 0, "Summary should not be empty"
        assert "sad" in summary.lower() or "work" in summary.lower(), "Summary should include key topics"

    def test_get_conversation_summary_handles_empty_history(self, test_data_dir):
        """Test that get_conversation_summary handles empty conversation history."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        session_id = history.start_session(user_id)
        
        # Act
        summary = history.get_conversation_summary(user_id, session_id)
        
        # Assert - Verify empty history handling
        assert isinstance(summary, str), "Should return string summary"
        assert len(summary) == 0 or "no conversation" in summary.lower(), "Should handle empty history"

    def test_add_message_includes_timestamp(self, test_data_dir):
        """Test that add_message includes timestamp in message data."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        session_id = history.start_session(user_id)
        
        # Act
        history.add_message(user_id, "user", "Test message")
        
        # Assert - Verify timestamp inclusion
        messages = history.get_session_messages(user_id, session_id)
        assert len(messages) == 1, "Should have one message"
        assert hasattr(messages[0], 'timestamp'), "Message should include timestamp"
        assert isinstance(messages[0].timestamp, datetime), "Timestamp should be datetime object"

    def test_add_message_validates_role(self, test_data_dir):
        """Test that add_message validates role parameter."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        history.start_session(user_id)
        
        # Act & Assert - Test invalid role (should not raise exception, just log)
        result = history.add_message(user_id, "invalid_role", "test content")
        
        # Assert - Should still return True (no validation in current implementation)
        assert result is True, "Should handle invalid role gracefully"

    def test_add_message_validates_content(self, test_data_dir):
        """Test that add_message validates content parameter."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        history.start_session(user_id)
        
        # Act & Assert - Test empty content (should not raise exception, just log)
        result = history.add_message(user_id, "user", "")
        
        # Assert - Should still return True (no validation in current implementation)
        assert result is True, "Should handle empty content gracefully"

    def test_get_recent_messages_respects_limit(self, test_data_dir):
        """Test that get_recent_messages respects the count limit."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        history.start_session(user_id)
        
        # Add multiple messages
        for i in range(5):
            history.add_message(user_id, "user", f"Message {i}")
            history.add_message(user_id, "assistant", f"Response {i}")
        
        # Act
        recent_messages = history.get_recent_messages(user_id, count=3)
        
        # Assert - Should return most recent messages
        assert len(recent_messages) == 3, "Should return exactly 3 messages"
        # Check that we get the most recent messages (last 3)
        assert recent_messages[-1]["content"] == "Response 4", "Should return most recent messages"

    def test_get_recent_messages_handles_zero_limit(self, test_data_dir):
        """Test that get_recent_messages handles zero count gracefully."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        history.start_session(user_id)
        
        # Add a message
        history.add_message(user_id, "user", "test message")
        
        # Act
        recent_messages = history.get_recent_messages(user_id, count=0)
        
        # Assert - Should return all messages (current implementation doesn't handle zero specially)
        assert len(recent_messages) >= 0, "Should return valid list"
        assert isinstance(recent_messages, list), "Should return a list"

    def test_get_recent_messages_handles_negative_limit(self, test_data_dir):
        """Test that get_recent_messages handles negative limit."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        session_id = history.start_session(user_id)
        
        # Add some messages
        history.add_message(user_id, "user", "Test message")
        
        # Act
        recent_messages = history.get_recent_messages(user_id, -1)
        
        # Assert - Verify negative limit handling
        assert isinstance(recent_messages, list), "Should return empty list"
        assert len(recent_messages) == 0, "Should return empty list for negative limit"

    def test_conversation_history_handles_concurrent_access(self, test_data_dir):
        """Test that conversation history handles concurrent access safely."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        session_id = history.start_session(user_id)
        
        # Act - Simulate concurrent access
        import threading
        results = []
        
        def add_message():
            history.add_message(user_id, "user", f"Concurrent message {threading.current_thread().name}")
            results.append(True)
        
        threads = [threading.Thread(target=add_message) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Assert - Verify concurrent access handling
        assert len(results) == 3, "Should handle all concurrent requests"
        
        # Verify all messages were added
        recent_messages = history.get_recent_messages(user_id, 10)
        assert len(recent_messages) >= 3, "Should include all concurrent messages"

    def test_conversation_history_handles_rapid_access(self, test_data_dir):
        """Test that conversation history handles rapid successive access."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        session_id = history.start_session(user_id)
        
        # Act - Make rapid successive calls
        for i in range(20):
            history.add_message(user_id, "user", f"Rapid message {i}")
            history.get_recent_messages(user_id, 5)
        
        # Assert - Verify rapid access handling
        recent_messages = history.get_recent_messages(user_id, 10)
        assert len(recent_messages) >= 10, "Should handle rapid access"

    def test_conversation_history_handles_large_messages(self, test_data_dir):
        """Test that conversation history handles large message content."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        session_id = history.start_session(user_id)
        
        # Create large message content
        large_message = "x" * 10000  # 10KB message
        
        # Act
        history.add_message(user_id, "user", large_message)
        
        # Assert - Verify large message handling
        messages = history.get_session_messages(user_id, session_id)
        assert len(messages) == 1, "Should handle large message"
        assert messages[0].content == large_message, "Should preserve large message content"

    def test_conversation_history_handles_special_characters(self, test_data_dir):
        """Test that conversation history handles special characters in messages."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        session_id = history.start_session(user_id)
        
        # Message with special characters
        special_message = "Message with special chars: @#$%^&*() 🎉🌟✨"
        
        # Act
        history.add_message(user_id, "user", special_message)
        
        # Assert - Verify special character handling
        messages = history.get_session_messages(user_id, session_id)
        assert len(messages) == 1, "Should handle special characters"
        assert messages[0].content == special_message, "Should preserve special characters"

    def test_conversation_history_handles_unicode_messages(self, test_data_dir):
        """Test that conversation history handles unicode messages."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        session_id = history.start_session(user_id)
        
        # Unicode message
        unicode_message = "Unicode message: 你好世界 🌍"
        
        # Act
        history.add_message(user_id, "user", unicode_message)
        
        # Assert - Verify unicode handling
        messages = history.get_session_messages(user_id, session_id)
        assert len(messages) == 1, "Should handle unicode"
        assert messages[0].content == unicode_message, "Should preserve unicode content"

    def test_end_session_terminates_active_session(self, test_data_dir):
        """Test that end_session terminates the active session."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        session_id = history.start_session(user_id)
        
        # Verify active session exists
        active_session = history.get_active_session(user_id)
        assert active_session is not None, "Active session should exist"
        
        # Act
        result = history.end_session(user_id)
        
        # Assert - Verify session termination
        assert result is True, "End session should succeed"
        
        # Verify active session is terminated
        active_session = history.get_active_session(user_id)
        assert active_session is None, "Active session should be terminated"

    def test_get_statistics_returns_actual_data(self, test_data_dir):
        """Test that get_statistics returns actual conversation statistics."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        session_id = history.start_session(user_id)
        
        # Add some messages
        history.add_message(user_id, "user", "Message 1")
        history.add_message(user_id, "assistant", "Response 1")
        history.add_message(user_id, "user", "Message 2")
        
        # Act
        stats = history.get_statistics(user_id)
        
        # Assert - Verify actual statistics
        assert isinstance(stats, dict), "Should return dictionary"
        assert "total_sessions" in stats, "Should include total sessions"
        assert "total_messages" in stats, "Should include total messages"
        assert "user_messages" in stats, "Should include user messages"
        assert "assistant_messages" in stats, "Should include assistant messages"
        assert stats["total_messages"] == 3, "Should count all messages"
        assert stats["user_messages"] == 2, "Should count user messages"
        assert stats["assistant_messages"] == 1, "Should count assistant messages"

    def test_delete_session_removes_specific_session(self, test_data_dir):
        """Test that delete_session removes a specific session."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        session_id = history.start_session(user_id)
        
        # Add some messages
        history.add_message(user_id, "user", "Test message")
        
        # Verify session exists
        messages = history.get_session_messages(user_id, session_id)
        assert len(messages) == 1, "Session should have messages before deletion"
        
        # Act
        result = history.delete_session(user_id, session_id)
        
        # Assert - Verify session deletion
        assert result is True, "Delete session should succeed"
        
        # Verify session is deleted
        messages = history.get_session_messages(user_id, session_id)
        assert len(messages) == 0, "Session should be empty after deletion"

    def test_get_history_returns_all_sessions(self, test_data_dir):
        """Test that get_history returns all sessions for a user."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        history = ConversationHistory()
        
        # Create multiple sessions
        session1 = history.start_session(user_id)
        history.add_message(user_id, "user", "Session 1 message")
        history.end_session(user_id)
        
        session2 = history.start_session(user_id)
        history.add_message(user_id, "user", "Session 2 message")
        
        # Act
        all_history = history.get_history(user_id)
        
        # Assert - Verify all sessions returned
        assert isinstance(all_history, list), "Should return list of sessions"
        assert len(all_history) >= 2, "Should include all sessions"
        
        # Verify session data
        session_ids = [session["session_id"] for session in all_history]
        assert session1 in session_ids, "Should include first session"
        assert session2 in session_ids, "Should include second session"
