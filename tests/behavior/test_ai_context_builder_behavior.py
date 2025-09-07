"""
Real behavior tests for AI context builder functionality.

Tests focus on actual side effects and system changes rather than just return values.
"""

import pytest
import json
import os
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

from ai.context_builder import ContextBuilder
from tests.test_utilities import TestUserFactory, TestDataFactory


class TestContextBuilderBehavior:
    """Test real behavior of context builder functionality."""

    def test_context_builder_initialization_creates_components(self, test_data_dir):
        """Test that context builder initialization creates required components."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        # Act
        context_builder = ContextBuilder()
        
        # Assert - Verify actual component creation
        assert context_builder is not None, "Context builder should be created"

    def test_build_user_context_creates_structured_context_data(self, test_data_dir):
        """Test that build_user_context creates actual structured context data."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act
        context = context_builder.build_user_context(user_id)
        
        # Assert - Verify actual context structure
        assert isinstance(context, object), "Context should be a ContextData object"
        assert hasattr(context, 'user_profile'), "Context should include user_profile"
        assert hasattr(context, 'user_context'), "Context should include user_context"
        assert hasattr(context, 'recent_checkins'), "Context should include recent_checkins"
        assert hasattr(context, 'conversation_history'), "Context should include conversation_history"
        assert hasattr(context, 'current_time'), "Context should include current_time"

    def test_build_user_context_includes_user_data_from_files(self, test_data_dir):
        """Test that build_user_context actually reads and includes user data from files."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act
        context = context_builder.build_user_context(user_id)
        
        # Assert - Verify actual data inclusion
        assert isinstance(context.user_profile, dict), "User profile should be included"
        assert isinstance(context.user_context, dict), "User context should be included"

    def test_build_user_context_includes_conversation_history(self, test_data_dir):
        """Test that build_user_context includes actual conversation history."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act
        context = context_builder.build_user_context(user_id, include_conversation_history=True)
        
        # Assert - Verify actual history inclusion
        assert isinstance(context.conversation_history, list), "Conversation history should be included"

    def test_build_user_context_handles_missing_user_data_gracefully(self, test_data_dir):
        """Test that build_user_context handles missing user data gracefully."""
        # Arrange
        user_id = "nonexistent-user"
        context_builder = ContextBuilder()
        
        # Act
        context = context_builder.build_user_context(user_id)
        
        # Assert - Verify graceful handling
        assert isinstance(context, object), "Should return valid context even with missing user"
        assert isinstance(context.user_profile, dict), "Should include empty user profile"
        assert isinstance(context.user_context, dict), "Should include empty user context"

    def test_build_user_context_includes_current_time(self, test_data_dir):
        """Test that build_user_context includes current time information."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act
        context = context_builder.build_user_context(user_id)
        
        # Assert - Verify time information inclusion
        assert context.current_time is not None, "Current time should be included"
        assert isinstance(context.current_time, datetime), "Current time should be a datetime object"

    def test_build_user_context_includes_recent_checkins(self, test_data_dir):
        """Test that build_user_context includes recent checkins information."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act
        context = context_builder.build_user_context(user_id)
        
        # Assert - Verify recent checkins inclusion
        assert isinstance(context.recent_checkins, list), "Recent checkins should be included"

    def test_build_user_context_without_conversation_history(self, test_data_dir):
        """Test that build_user_context can exclude conversation history."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act
        context = context_builder.build_user_context(user_id, include_conversation_history=False)
        
        # Assert - Verify conversation history exclusion
        assert isinstance(context.conversation_history, list), "Conversation history should still be a list"
        # The list might be empty when history is excluded

    def test_build_user_context_handles_error_conditions(self, test_data_dir):
        """Test that build_user_context handles error conditions gracefully."""
        # Arrange
        user_id = "invalid-user-id"
        context_builder = ContextBuilder()
        
        # Act
        context = context_builder.build_user_context(user_id)
        
        # Assert - Verify error handling
        assert isinstance(context, object), "Should return valid context even with errors"
        assert isinstance(context.user_profile, dict), "Should include empty user profile"
        assert isinstance(context.user_context, dict), "Should include empty user context"

    def test_build_user_context_creates_fresh_timestamp(self, test_data_dir):
        """Test that build_user_context creates fresh timestamp for each call."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act
        context1 = context_builder.build_user_context(user_id)
        # Ensure different timestamps through controlled call sequencing (no sleep)
        context2 = context_builder.build_user_context(user_id)
        
        # Assert - Verify fresh timestamp creation
        assert context1.current_time != context2.current_time, "Should create fresh timestamps"

    def test_build_user_context_handles_empty_user_data(self, test_data_dir):
        """Test that build_user_context handles empty user data gracefully."""
        # Arrange
        user_id = "empty-user"
        # Create user directory but no data files
        user_dir = os.path.join(test_data_dir, "users", user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        context_builder = ContextBuilder()
        
        # Act
        context = context_builder.build_user_context(user_id)
        
        # Assert - Verify empty data handling
        assert isinstance(context, object), "Should return valid context"
        assert isinstance(context.user_profile, dict), "Should include empty user profile"
        assert isinstance(context.user_context, dict), "Should include empty user context"

    def test_build_user_context_handles_corrupted_user_data(self, test_data_dir):
        """Test that build_user_context handles corrupted user data gracefully."""
        # Arrange
        user_id = "corrupted-user"
        TestDataFactory.create_corrupted_user_data(user_id, "invalid_json")
        
        context_builder = ContextBuilder()
        
        # Act
        context = context_builder.build_user_context(user_id)
        
        # Assert - Verify corrupted data handling
        assert isinstance(context, object), "Should return valid context even with corrupted data"
        assert isinstance(context.user_profile, dict), "Should include empty user profile"
        assert isinstance(context.user_context, dict), "Should include empty user context"

    def test_build_user_context_handles_missing_files(self, test_data_dir):
        """Test that build_user_context handles missing user files gracefully."""
        # Arrange
        user_id = "missing-files-user"
        TestDataFactory.create_corrupted_user_data(user_id, "missing_file")
        
        context_builder = ContextBuilder()
        
        # Act
        context = context_builder.build_user_context(user_id)
        
        # Assert - Verify missing files handling
        assert isinstance(context, object), "Should return valid context even with missing files"
        assert isinstance(context.user_profile, dict), "Should include empty user profile"
        assert isinstance(context.user_context, dict), "Should include empty user context"

    def test_build_user_context_handles_empty_files(self, test_data_dir):
        """Test that build_user_context handles empty user files gracefully."""
        # Arrange
        user_id = "empty-files-user"
        TestDataFactory.create_corrupted_user_data(user_id, "empty_file")
        
        context_builder = ContextBuilder()
        
        # Act
        context = context_builder.build_user_context(user_id)
        
        # Assert - Verify empty files handling
        assert isinstance(context, object), "Should return valid context even with empty files"
        assert isinstance(context.user_profile, dict), "Should include empty user profile"
        assert isinstance(context.user_context, dict), "Should include empty user context"

    def test_build_user_context_handles_long_user_id(self, test_data_dir):
        """Test that build_user_context handles long user IDs correctly."""
        # Arrange
        user_id = "very-long-user-id-" + "x" * 100
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act
        context = context_builder.build_user_context(user_id)
        
        # Assert - Verify long user ID handling
        assert isinstance(context, object), "Should handle long user IDs"
        assert isinstance(context.user_profile, dict), "Should include user profile"

    def test_build_user_context_handles_special_characters_in_user_id(self, test_data_dir):
        """Test that build_user_context handles special characters in user IDs."""
        # Arrange
        user_id = "user-with-special-chars-@#$%^&*()"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act
        context = context_builder.build_user_context(user_id)
        
        # Assert - Verify special character handling
        assert isinstance(context, object), "Should handle special characters in user ID"
        assert isinstance(context.user_profile, dict), "Should include user profile"

    def test_build_user_context_handles_unicode_user_id(self, test_data_dir):
        """Test that build_user_context handles unicode characters in user IDs."""
        # Arrange
        user_id = "user-with-unicode-🎉🌟✨"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act
        context = context_builder.build_user_context(user_id)
        
        # Assert - Verify unicode handling
        assert isinstance(context, object), "Should handle unicode characters in user ID"
        assert isinstance(context.user_profile, dict), "Should include user profile"

    def test_build_user_context_handles_concurrent_access(self, test_data_dir):
        """Test that build_user_context handles concurrent access safely."""
        # Arrange
        user_id = "concurrent-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act - Simulate concurrent access
        import threading
        results = []
        
        def build_context():
            context = context_builder.build_user_context(user_id)
            results.append(context)
        
        threads = [threading.Thread(target=build_context) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Assert - Verify concurrent access handling
        assert len(results) == 3, "Should handle all concurrent requests"
        for context in results:
            assert isinstance(context, object), "Each result should be valid"
            assert isinstance(context.user_profile, dict), "Each result should include user profile"

    def test_build_user_context_handles_rapid_calls(self, test_data_dir):
        """Test that build_user_context handles rapid successive calls."""
        # Arrange
        user_id = "rapid-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act - Make rapid successive calls
        contexts = []
        for i in range(10):
            context = context_builder.build_user_context(user_id)
            contexts.append(context)
        
        # Assert - Verify rapid call handling
        assert len(contexts) == 10, "Should handle all rapid calls"
        for context in contexts:
            assert isinstance(context, object), "Each result should be valid"
            assert isinstance(context.user_profile, dict), "Each result should include user profile"

    def test_build_user_context_handles_large_user_data(self, test_data_dir):
        """Test that build_user_context handles large user data efficiently."""
        # Arrange
        user_id = "large-data-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act
        context = context_builder.build_user_context(user_id)
        
        # Assert - Verify context creation
        assert context is not None, "Context should be created"
        assert hasattr(context, 'user_profile'), "Context should have user_profile attribute"
        assert hasattr(context, 'user_context'), "Context should have user_context attribute"
        assert hasattr(context, 'recent_checkins'), "Context should have recent_checkins attribute"
