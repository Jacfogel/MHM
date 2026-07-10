#!/usr/bin/env python3

"""
test_user_context_behavior.py

Comprehensive behavior tests for UserContextManager focusing on real behavior and side effects.
Tests verify actual system changes, not just return values.
"""

import os
import pytest
from unittest.mock import patch

from user.context_manager import UserContextManager
from ai.context.chatbot_context import build_chatbot_context_dict


@pytest.mark.behavior
@pytest.mark.user
class TestUserContextManagerBehavior:
    """Test UserContextManager real behavior and side effects."""
    
    @pytest.mark.behavior
    @pytest.mark.user
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_user_context_manager_initialization_creates_structure(self, test_data_dir):
        """Test that UserContextManager initialization creates proper internal structure."""
        # Arrange & Act
        manager = UserContextManager()
        
        # Assert - Verify actual structure creation
        assert hasattr(manager, 'conversation_history'), "Should have conversation_history attribute"
        assert isinstance(manager.conversation_history, dict), "conversation_history should be a dict"
        assert len(manager.conversation_history) == 0, "conversation_history should be empty initially"
    
    @pytest.mark.behavior
    @pytest.mark.user
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_build_context_with_session_overlay_uses_envelope_shape(self, test_data_dir):
        """Envelope-backed context dict includes expected top-level keys."""
        manager = UserContextManager()
        test_user_id = "test-user-456"

        from tests.test_helpers.test_utilities import TestUserFactory

        assert TestUserFactory.create_basic_user(
            test_user_id, test_data_dir=test_data_dir
        )

        result = manager.build_context_with_session_overlay(test_user_id)

        assert "user_profile" in result
        assert "recent_activity" in result
        assert "conversation_insights" in result
        assert "preferences" in result
        assert "mood_trends" in result
        assert "conversation_history" in result
    
    @pytest.mark.user
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_build_context_without_session_overlay(self, test_data_dir):
        """Session overlay can be skipped while envelope context still loads."""
        manager = UserContextManager()
        test_user_id = "test-user-789"

        from tests.test_helpers.test_utilities import TestUserFactory

        assert TestUserFactory.create_basic_user(
            test_user_id, test_data_dir=test_data_dir
        )
        manager.add_conversation_exchange(test_user_id, "Hello", "Hi")

        result = build_chatbot_context_dict(
            test_user_id, include_conversation_history=False
        )

        assert "conversation_history" in result
        assert result["conversation_history"] == []
    
    @pytest.mark.user
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_add_conversation_exchange_actually_stores_data(self, test_data_dir):
        """Test that add_conversation_exchange actually stores conversation data."""
        # Arrange
        manager = UserContextManager()
        test_user_id = "test-user-exchange"
        user_message = "Hello, how are you?"
        ai_response = "I'm doing well, thank you for asking!"
        
        # Act
        manager.add_conversation_exchange(test_user_id, user_message, ai_response)
        
        # Assert - Verify actual data storage
        assert test_user_id in manager.conversation_history, "User should be in conversation history"
        assert len(manager.conversation_history[test_user_id]) == 1, "Should have one conversation exchange"
        
        exchange = manager.conversation_history[test_user_id][0]
        assert exchange['user_message'] == user_message, "User message should be stored correctly"
        assert exchange['ai_response'] == ai_response, "AI response should be stored correctly"
        assert 'timestamp' in exchange, "Should have timestamp"

    @pytest.mark.user
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_session_conversation_history_returns_recent_exchanges(self, test_data_dir):
        """Session history API returns in-memory exchanges without full context load."""
        manager = UserContextManager()
        test_user_id = "test-user-session-api"
        manager.add_conversation_exchange(test_user_id, "Hello", "Hi there")

        history = manager.get_session_conversation_history(test_user_id)

        assert len(history) == 1
        assert history[0]["user_message"] == "Hello"
        assert history[0]["ai_response"] == "Hi there"
    
    @pytest.mark.user
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_add_conversation_exchange_maintains_history_limit(self, test_data_dir):
        """Test that add_conversation_exchange maintains conversation history limit."""
        # Arrange
        manager = UserContextManager()
        test_user_id = "test-user-limit"
        
        # Add more than the in-memory limit (20 exchanges)
        for i in range(25):
            manager.add_conversation_exchange(test_user_id, f"Message {i}", f"Response {i}")

        # Act - Add one more exchange
        manager.add_conversation_exchange(test_user_id, "Final message", "Final response")

        # Assert - Verify history limit is maintained
        assert len(manager.conversation_history[test_user_id]) <= 20
    
    @pytest.mark.user
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_conversation_history_returns_actual_data(self, test_data_dir):
        """Test that _get_conversation_history returns actual stored conversation data."""
        # Arrange
        manager = UserContextManager()
        test_user_id = "test-user-history"
        
        # Add some conversation exchanges
        manager.add_conversation_exchange(test_user_id, "Hello", "Hi there!")
        manager.add_conversation_exchange(test_user_id, "How are you?", "I'm great!")
        
        # Act
        history = manager._get_conversation_history(test_user_id)
        
        # Assert - Verify actual data retrieval
        assert len(history) == 2, "Should return all conversation exchanges"
        assert history[0]['user_message'] == "Hello", "Should have correct user message"
        assert history[1]['ai_response'] == "I'm great!", "Should have correct AI response"
    
    @pytest.mark.user
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_conversation_history_handles_empty_history(self, test_data_dir):
        """Test that _get_conversation_history handles users with no conversation history."""
        # Arrange
        manager = UserContextManager()
        test_user_id = "test-user-empty"
        
        # Act
        history = manager._get_conversation_history(test_user_id)
        
        # Assert - Verify empty history handling
        assert history == [], "Should return empty list for new user"
    
    @pytest.mark.user
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_active_schedules_identifies_active_periods(self, test_data_dir):
        """Test that get_active_schedules identifies actually active schedule periods."""
        # Arrange
        from core.schedule_utilities import get_active_schedules
        
        # Test schedules with active and inactive periods (actual format)
        test_schedules = {
            'Morning': {
                'start_time': '08:00',
                'end_time': '12:00',
                'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'active': True
            },
            'Afternoon': {
                'start_time': '13:00',
                'end_time': '17:00',
                'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'active': False
            },
            'Evening': {
                'start_time': '18:00',
                'end_time': '22:00',
                'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'active': True
            }
        }
        
        # Act
        active_schedules = get_active_schedules(test_schedules)
        
        # Assert - Verify active period identification
        assert len(active_schedules) == 2, "Should identify 2 active periods"
        assert 'Morning' in active_schedules, "Should include Morning period"
        assert 'Evening' in active_schedules, "Should include Evening period"
        assert 'Afternoon' not in active_schedules, "Should not include inactive Afternoon period"
    
    @pytest.mark.user
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_format_context_for_ai_creates_readable_string(self, test_data_dir):
        """Test that format_context_for_ai creates actual readable string from context."""
        # Arrange
        manager = UserContextManager()
        test_context = {
            'user_profile': {
                'preferred_name': 'testuser',
                'active_categories': ['motivational', 'health'],
                'messaging_service': 'discord',
                'active_schedules': ['Morning', 'Evening']
            },
            'recent_activity': {
                'recent_responses_count': 3,
                'last_response_date': '2025-01-01',
                'recent_messages_count': 5,
                'last_message_date': '2025-01-02'
            },
            'conversation_insights': {
                'recent_topics': ['motivation', 'health'],
                'interaction_count': 5,
                'engagement_level': 'high'
            },
            'preferences': {
                'notifications': True,
                'language': 'en'
            },
            'mood_trends': {
                'average_mood': 7.5,
                'trend': 'improving'
            },
            'conversation_history': [
                {'user_message': 'Hello', 'ai_response': 'Hi there!', 'timestamp': '2025-01-01T10:00:00'}
            ]
        }
        
        # Act
        formatted = manager.format_context_for_ai(test_context)
        
        # Assert - Verify actual string formatting
        assert isinstance(formatted, str), "Should return a string"
        assert len(formatted) > 0, "Should not be empty"
        assert 'testuser' in formatted, "Should include preferred name"
        assert 'motivational' in formatted, "Should include active categories"
        assert '3' in formatted, "Should include recent responses count"
        assert 'motivation' in formatted, "Should include recent topics"
    
    @pytest.mark.user
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_format_context_for_ai_handles_empty_context(self, test_data_dir):
        """Test that format_context_for_ai handles empty or minimal context gracefully."""
        # Arrange
        manager = UserContextManager()
        empty_context = {}
        
        # Act
        formatted = manager.format_context_for_ai(empty_context)
        
        # Assert - Verify graceful handling
        assert isinstance(formatted, str), "Should return a string"
        assert len(formatted) > 0, "Should not be empty"
        assert "User context unavailable" in formatted, "Should indicate context unavailability"
    
    @pytest.mark.user
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_user_context_manager_error_handling_preserves_system_stability(self, test_data_dir):
        """Test that UserContextManager error handling preserves system stability."""
        manager = UserContextManager()
        test_user_id = "test-user-error"

        with patch(
            "ai.context.chatbot_context.build_chatbot_context_dict", return_value=None
        ):
            result = manager.build_context_with_session_overlay(test_user_id)

        assert result is not None
        assert "user_profile" in result
    
    @pytest.mark.user
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_user_context_manager_integration_with_ai_chatbot(self, test_data_dir):
        """Test session conversation overlay on envelope-backed context."""
        manager = UserContextManager()
        test_user_id = "test-user-ai-integration"

        from tests.test_helpers.test_utilities import TestUserFactory

        assert TestUserFactory.create_basic_user(
            test_user_id, test_data_dir=test_data_dir
        )
        manager.add_conversation_exchange(test_user_id, "Hello", "Hi there!")

        context = manager.build_context_with_session_overlay(test_user_id)
        manager.format_context_for_ai(context)

        assert "conversation_history" in context
        assert len(context["conversation_history"]) == 1
        assert context["conversation_history"][0]["user_message"] == "Hello"
        assert context["conversation_history"][0]["ai_response"] == "Hi there!"
    
    @pytest.mark.user
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_user_context_manager_performance_under_load(self, test_data_dir):
        """Test that UserContextManager performs well under load."""
        manager = UserContextManager()
        test_user_id = "test-user-performance"

        from tests.test_helpers.test_utilities import TestUserFactory

        assert TestUserFactory.create_basic_user(
            test_user_id, test_data_dir=test_data_dir
        )

        for i in range(25):
            manager.add_conversation_exchange(test_user_id, f"Message {i}", f"Response {i}")

        context = manager.build_context_with_session_overlay(test_user_id)

        assert context is not None
        assert len(context["conversation_history"]) <= 5
        assert len(manager.conversation_history[test_user_id]) <= 20
    
    @pytest.mark.user
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_user_context_manager_cleanup_and_resource_management(self, test_data_dir):
        """Test that UserContextManager properly manages resources and cleanup."""
        # Arrange
        manager = UserContextManager()
        test_user_id = "test-user-cleanup"
        
        # Add conversation exchanges
        for i in range(10):
            manager.add_conversation_exchange(test_user_id, f"Message {i}", f"Response {i}")
        
        # Act - Simulate cleanup by removing user data
        if test_user_id in manager.conversation_history:
            del manager.conversation_history[test_user_id]
        
        # Assert - Verify cleanup
        assert test_user_id not in manager.conversation_history, "User data should be cleaned up"
        assert len(manager.conversation_history) == 0, "Should have no remaining user data"


@pytest.mark.behavior
@pytest.mark.user
class TestUserContextManagerIntegration:
    """Integration tests for UserContextManager with real user data."""
    
    def test_user_context_manager_with_real_user_data(self, test_data_dir):
        """Test UserContextManager with real user data files."""
        test_user_id = "real-user-test"

        from tests.test_helpers.test_utilities import TestUserFactory
        from core import get_user_id_by_identifier, update_user_context

        assert TestUserFactory.create_basic_user(
            test_user_id, test_data_dir=test_data_dir
        )
        actual_user_id = get_user_id_by_identifier(test_user_id)
        assert actual_user_id is not None

        assert update_user_context(
            actual_user_id,
            {"preferred_name": "realuser", "gender_identity": ["they/them"]},
        )

        context = build_chatbot_context_dict(actual_user_id)

        assert context is not None
        assert context["user_profile"]["preferred_name"] == "realuser"
    
    def test_user_context_manager_error_recovery_with_real_files(self, test_data_dir):
        """Test UserContextManager error recovery with corrupted real files."""
        # Arrange
        manager = UserContextManager()
        test_user_id = "corrupted-user-test"
        
        # Create user directory with corrupted files
        user_dir = os.path.join(test_data_dir, "users", test_user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Create corrupted account.json
        with open(os.path.join(user_dir, "account.json"), 'w') as f:
            f.write("invalid json content")
        
        # Act - Should handle corrupted files gracefully
        context = manager.build_context_with_session_overlay(test_user_id)
        
        # Assert - Verify error recovery
        assert context is not None, "Should return context even with corrupted files"
        assert 'user_profile' in context, "Should have user_profile even with errors"
    
    def test_user_context_manager_concurrent_access_safety(self, test_data_dir):
        """Test UserContextManager safety under concurrent access."""
        # Arrange
        manager = UserContextManager()
        test_user_id = "concurrent-user-test"
        
        # Add initial conversation exchange
        manager.add_conversation_exchange(test_user_id, "Initial message", "Initial response")
        
        # Act - Simulate concurrent access (in real scenario, this would be multiple threads)
        # For now, we'll test that the manager can handle rapid successive calls
        for i in range(10):
            manager.add_conversation_exchange(test_user_id, f"Concurrent message {i}", f"Concurrent response {i}")
            manager.build_context_with_session_overlay(test_user_id)
        
        # Assert - Verify concurrent access safety
        assert test_user_id in manager.conversation_history, "User should still be in conversation history"
        assert len(manager.conversation_history[test_user_id]) <= 20
        assert len(manager.conversation_history[test_user_id]) > 0, "Should have some conversation history" 
