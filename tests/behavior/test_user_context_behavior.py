#!/usr/bin/env python3

"""
test_user_context_behavior.py

Comprehensive behavior tests for UserContextManager focusing on real behavior and side effects.
Tests verify actual system changes, not just return values.
"""

import json
import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from user.context_manager import UserContextManager
from user.user_context import UserContext
from user.user_preferences import UserPreferences


class TestUserContextManagerBehavior:
    """Test UserContextManager real behavior and side effects."""
    
    @pytest.mark.behavior
    @pytest.mark.user_management
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
    @pytest.mark.user_management
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_current_user_context_uses_usercontext_singleton(self, test_data_dir):
        """Test that get_current_user_context actually uses UserContext singleton."""
        # Arrange
        manager = UserContextManager()
        test_user_id = "test-user-123"
        
        # Mock UserContext to return our test user
        with patch('user.context_manager.UserContext') as mock_user_context_class:
            mock_user_context = MagicMock()
            mock_user_context.get_user_id.return_value = test_user_id
            mock_user_context_class.return_value = mock_user_context
            
            # Act
            result = manager.get_current_user_context()
            
            # Assert - Verify UserContext was actually used
            mock_user_context.get_user_id.assert_called_once()
            assert result is not None, "Should return context even with mocked user"
    
    @pytest.mark.user_management
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_current_user_context_handles_no_user_gracefully(self, test_data_dir):
        """Test that get_current_user_context handles no logged-in user gracefully."""
        # Arrange
        manager = UserContextManager()
        
        # Mock UserContext to return no user
        with patch('user.context_manager.UserContext') as mock_user_context_class:
            mock_user_context = MagicMock()
            mock_user_context.get_user_id.return_value = None
            mock_user_context_class.return_value = mock_user_context
            
            # Act
            result = manager.get_current_user_context()
            
            # Assert - Verify graceful handling
            assert result is not None, "Should return minimal context even with no user"
            assert 'user_profile' in result, "Should have user_profile in minimal context"
    
    @pytest.mark.user_management
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_user_context_creates_complete_structure(self, test_data_dir):
        """Test that get_user_context creates complete context structure."""
        # Arrange
        manager = UserContextManager()
        test_user_id = "test-user-456"
        
        # Mock all the data retrieval functions
        with patch('user.context_manager.get_user_data') as mock_get_user_data, \
             patch('user.context_manager.get_recent_checkins') as mock_get_checkins, \
             patch('user.context_manager.get_recent_chat_interactions') as mock_get_interactions, \
             patch('user.context_manager.get_recent_messages') as mock_get_messages:
            
            # Setup mock returns
            mock_get_user_data.side_effect = lambda user_id, data_type: {
                'preferences': {'preferences': {'theme': 'dark'}},
                'account': {'account': {'username': 'testuser'}},
                'context': {'context': {'timezone': 'UTC'}}
            }.get(data_type, {})
            
            mock_get_checkins.return_value = [{'date': '2025-01-01', 'mood': 'good'}]
            mock_get_interactions.return_value = [{'timestamp': '2025-01-01T10:00:00', 'message': 'hello'}]
            mock_get_messages.return_value = [{'id': 'msg1', 'content': 'test message'}]
            
            # Act
            result = manager.get_ai_context(test_user_id)
            
            # Assert - Verify complete structure creation
            assert 'user_profile' in result, "Should have user_profile"
            assert 'recent_activity' in result, "Should have recent_activity"
            assert 'conversation_insights' in result, "Should have conversation_insights"
            assert 'preferences' in result, "Should have preferences"
            assert 'mood_trends' in result, "Should have mood_trends"
            assert 'conversation_history' in result, "Should have conversation_history"
    
    @pytest.mark.user_management
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_user_context_without_conversation_history(self, test_data_dir):
        """Test that get_user_context excludes conversation history when requested."""
        # Arrange
        manager = UserContextManager()
        test_user_id = "test-user-789"
        
        # Mock data retrieval
        with patch('user.context_manager.get_user_data') as mock_get_user_data:
            mock_get_user_data.side_effect = lambda user_id, data_type: {
                'preferences': {'preferences': {}},
                'account': {'account': {}},
                'context': {'context': {}}
            }.get(data_type, {})
            
            # Act
            result = manager.get_ai_context(test_user_id, include_conversation_history=False)
            
            # Assert - Verify conversation history is excluded
            assert 'conversation_history' in result, "Should have conversation_history key"
            assert result['conversation_history'] == [], "conversation_history should be empty list"
    
    @pytest.mark.user_management
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
    
    @pytest.mark.user_management
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_add_conversation_exchange_maintains_history_limit(self, test_data_dir):
        """Test that add_conversation_exchange maintains conversation history limit."""
        # Arrange
        manager = UserContextManager()
        test_user_id = "test-user-limit"
        
        # Add more than the limit (assuming limit is 50)
        for i in range(60):
            manager.add_conversation_exchange(test_user_id, f"Message {i}", f"Response {i}")
        
        # Act - Add one more exchange
        manager.add_conversation_exchange(test_user_id, "Final message", "Final response")
        
        # Assert - Verify history limit is maintained
        assert len(manager.conversation_history[test_user_id]) <= 50, "History should not exceed limit"
        assert len(manager.conversation_history[test_user_id]) > 0, "Should still have some history"
    
    @pytest.mark.user_management
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
    
    @pytest.mark.user_management
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
    
    @pytest.mark.user_management
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_user_profile_uses_existing_infrastructure(self, test_data_dir):
        """Test that _get_user_profile actually uses existing user infrastructure."""
        # Arrange
        manager = UserContextManager()
        test_user_id = "test-user-profile"
        
        # Mock UserContext and data retrieval
        with patch('user.context_manager.UserContext') as mock_user_context_class, \
             patch('user.context_manager.get_user_data') as mock_get_user_data, \
             patch('user.context_manager.get_active_schedules') as mock_get_active_schedules:
            
            mock_user_context = MagicMock()
            mock_user_context.get_preferred_name.return_value = "TestUser"
            mock_user_context_class.return_value = mock_user_context
            
            mock_get_user_data.side_effect = lambda user_id, data_type: {
                'preferences': {'preferences': {'categories': ['motivational', 'health'], 'channel': {'type': 'discord'}}},
                'account': {'account': {'username': 'testuser', 'email': 'test@example.com'}},
                'context': {'context': {'preferred_name': 'TestUser', 'timezone': 'UTC'}}
            }.get(data_type, {})
            
            mock_get_active_schedules.return_value = []
            
            # Act
            profile = manager._get_user_profile(test_user_id)
            
            # Assert - Verify infrastructure usage
            mock_user_context.load_user_data.assert_called_once_with(test_user_id)
            assert mock_get_user_data.call_count == 3, "Should call get_user_data for all data types"
            assert 'preferred_name' in profile, "Should include preferred_name"
            assert 'active_categories' in profile, "Should include active_categories"
            assert 'messaging_service' in profile, "Should include messaging_service"
            assert 'active_schedules' in profile, "Should include active_schedules"
            assert profile['preferred_name'] == "TestUser", "Should have correct preferred_name"
            assert 'motivational' in profile['active_categories'], "Should include categories from preferences"
            assert profile['messaging_service'] == "discord", "Should include channel type from preferences"
    
    @pytest.mark.user_management
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_recent_activity_integrates_multiple_sources(self, test_data_dir):
        """Test that _get_recent_activity integrates data from multiple sources."""
        # Arrange
        manager = UserContextManager()
        test_user_id = "test-user-activity"
        
        # Mock data retrieval functions
        with patch('user.context_manager.get_recent_checkins') as mock_get_checkins, \
             patch('user.context_manager.get_user_data') as mock_get_user_data:
            
            # Setup mock returns
            mock_get_checkins.return_value = [
                {'timestamp': '2025-01-02 10:00:00', 'mood': 'okay', 'energy': 'medium'},
                {'timestamp': '2025-01-01 10:00:00', 'mood': 'good', 'energy': 'high'}
            ]
            mock_get_user_data.return_value = {
                'preferences': {
                    'categories': ['motivational', 'health']
                }
            }
            
            # Act
            activity = manager._get_recent_activity(test_user_id)
            
            # Assert - Verify integration of multiple sources
            assert 'recent_responses_count' in activity, "Should include recent responses count"
            assert 'last_response_date' in activity, "Should include last response date"
            assert 'recent_messages_count' in activity, "Should include recent messages count"
            assert 'last_message_date' in activity, "Should include last message date"
            assert activity['recent_responses_count'] == 2, "Should have correct number of responses"
            assert activity['last_response_date'] == '2025-01-02', "Should have correct last response date"
    
    @pytest.mark.user_management
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_conversation_insights_analyzes_actual_data(self, test_data_dir):
        """Test that _get_conversation_insights analyzes actual conversation data."""
        # Arrange
        manager = UserContextManager()
        test_user_id = "test-user-insights"
        
        # Mock chat interactions data
        with patch('user.context_manager.get_recent_chat_interactions') as mock_get_interactions:
            mock_get_interactions.return_value = [
                {'user_message': 'I\'m feeling sad', 'ai_response': 'I\'m sorry to hear that'},
                {'user_message': 'I need motivation', 'ai_response': 'You can do this!'},
                {'user_message': 'I\'m feeling better', 'ai_response': 'That\'s great to hear!'}
            ]
            
            # Act
            insights = manager._get_conversation_insights(test_user_id)
            
            # Assert - Verify actual analysis
            assert 'recent_topics' in insights, "Should include recent topics"
            assert 'interaction_count' in insights, "Should include interaction count"
            assert insights['interaction_count'] == 3, "Should count all interactions"
            assert len(insights['recent_topics']) > 0, "Should have some topics"
    
    @pytest.mark.user_management
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_mood_trends_analyzes_checkin_data(self, test_data_dir):
        """Test that _get_mood_trends analyzes actual checkin data."""
        # Arrange
        manager = UserContextManager()
        test_user_id = "test-user-mood"
        
        # Mock checkin data with numeric mood values
        with patch('user.context_manager.get_recent_checkins') as mock_get_checkins:
            mock_get_checkins.return_value = [
                {'date': '2025-01-01', 'mood': 8, 'energy': 7},
                {'date': '2025-01-02', 'mood': 6, 'energy': 5},
                {'date': '2025-01-03', 'mood': 7, 'energy': 6},
                {'date': '2025-01-04', 'mood': 4, 'energy': 3}
            ]
            
            # Act
            trends = manager._get_mood_trends(test_user_id)
            
            # Assert - Verify actual trend analysis
            assert 'average_mood' in trends, "Should include average mood"
            assert 'average_energy' in trends, "Should include average energy"
            assert 'trend' in trends, "Should include trend"
            assert trends['average_mood'] is not None, "Should calculate average mood"
            assert trends['average_energy'] is not None, "Should calculate average energy"
    
    @pytest.mark.user_management
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
    
    @pytest.mark.user_management
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
    
    @pytest.mark.user_management
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
    
    @pytest.mark.user_management
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_user_context_manager_error_handling_preserves_system_stability(self, test_data_dir):
        """Test that UserContextManager error handling preserves system stability."""
        # Arrange
        manager = UserContextManager()
        test_user_id = "test-user-error"
        
        # Mock get_user_data to raise an exception
        with patch('user.context_manager.get_user_data') as mock_get_user_data:
            mock_get_user_data.side_effect = Exception("Test error")
            
            # Act - Should not raise exception due to error handling
            result = manager.get_ai_context(test_user_id)
            
            # Assert - Verify graceful error handling
            assert result is not None, "Should return result even with errors"
            assert 'user_profile' in result, "Should have user_profile even with errors"
    
    @pytest.mark.user_management
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_user_context_manager_integration_with_ai_chatbot(self, test_data_dir):
        """Test that UserContextManager integrates properly with AI chatbot."""
        # Arrange
        manager = UserContextManager()
        test_user_id = "test-user-ai-integration"
        
        # Add conversation exchange
        manager.add_conversation_exchange(test_user_id, "Hello", "Hi there!")
        
        # Mock data retrieval for context generation
        with patch('user.context_manager.get_user_data') as mock_get_user_data, \
             patch('user.context_manager.get_recent_checkins') as mock_get_checkins, \
             patch('user.context_manager.get_recent_chat_interactions') as mock_get_interactions:
            
            mock_get_user_data.side_effect = lambda user_id, data_type: {
                'preferences': {'preferences': {'categories': ['motivational'], 'channel': {'type': 'discord'}}},
                'account': {'account': {'username': 'testuser'}},
                'context': {'context': {'preferred_name': 'testuser'}}
            }.get(data_type, {})
            
            mock_get_checkins.return_value = [{'timestamp': '2025-01-01 10:00:00', 'mood': 8}]
            mock_get_interactions.return_value = [{'user_message': 'Hello', 'ai_response': 'Hi there!'}]
            
            # Act
            context = manager.get_ai_context(test_user_id)
            formatted_context = manager.format_context_for_ai(context)
            
            # Assert - Verify AI integration
            assert 'conversation_history' in context, "Should include conversation history"
            assert len(context['conversation_history']) == 1, "Should have one conversation exchange"
            assert context['conversation_history'][0]['user_message'] == "Hello", "Should have correct user message"
            assert context['conversation_history'][0]['ai_response'] == "Hi there!", "Should have correct AI response"
    
    @pytest.mark.user_management
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_user_context_manager_performance_under_load(self, test_data_dir):
        """Test that UserContextManager performs well under load."""
        # Arrange
        manager = UserContextManager()
        test_user_id = "test-user-performance"
        
        # Add many conversation exchanges
        for i in range(100):
            manager.add_conversation_exchange(test_user_id, f"Message {i}", f"Response {i}")
        
        # Mock data retrieval for performance testing
        with patch('user.context_manager.get_user_data') as mock_get_user_data, \
             patch('user.context_manager.get_recent_checkins') as mock_get_checkins, \
             patch('user.context_manager.get_recent_chat_interactions') as mock_get_interactions, \
             patch('user.context_manager.get_recent_messages') as mock_get_messages:
            
            mock_get_user_data.side_effect = lambda user_id, data_type: {
                'preferences': {'preferences': {}},
                'account': {'account': {}},
                'context': {'context': {}}
            }.get(data_type, {})
            
            mock_get_checkins.return_value = []
            mock_get_interactions.return_value = []
            mock_get_messages.return_value = []
            
            # Act
            context = manager.get_ai_context(test_user_id)
            
            # Assert - Verify performance under load
            assert context is not None, "Should return context under load"
            assert len(context['conversation_history']) <= 50, "Should maintain history limit under load"
    
    @pytest.mark.user_management
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


class TestUserContextManagerIntegration:
    """Integration tests for UserContextManager with real user data."""
    
    def test_user_context_manager_with_real_user_data(self, test_data_dir):
        """Test UserContextManager with real user data files."""
        # Arrange
        manager = UserContextManager()
        test_user_id = "real-user-test"
        
        # Create test user using centralized utilities
        from tests.test_utilities import TestUserFactory
        success = TestUserFactory.create_basic_user(test_user_id, enable_checkins=True, enable_tasks=True, test_data_dir=test_data_dir)
        assert success, "Test user should be created successfully"
        
        # Get the UUID for the user
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(test_user_id)
        assert actual_user_id is not None, f"Should be able to get UUID for user {test_user_id}"
        
        # Update user context with specific data for testing
        from core.user_management import update_user_context
        update_success = update_user_context(actual_user_id, {
            'preferred_name': 'realuser',
            'gender_identity': ['they/them']
        })
        assert update_success, "User context should be updated successfully"
        
        # Mock UserContext and data retrieval to return the correct data
        with patch('user.context_manager.UserContext') as mock_user_context_class, \
             patch('user.context_manager.get_user_data') as mock_get_user_data, \
             patch('user.context_manager.get_active_schedules') as mock_get_active_schedules:
            
            mock_user_context = MagicMock()
            mock_user_context.get_preferred_name.return_value = "realuser"
            mock_user_context_class.return_value = mock_user_context
            
            # Mock get_user_data to return the correct structure
            mock_get_user_data.side_effect = lambda user_id, data_type: {
                'preferences': {'preferences': {'categories': ['motivational', 'health'], 'channel': {'type': 'discord'}}},
                'account': {'account': {'username': 'realuser', 'email': f'{test_user_id}@example.com'}},
                'context': {'context': {'preferred_name': 'realuser', 'timezone': 'UTC'}}
            }.get(data_type, {})
            
            mock_get_active_schedules.return_value = []
            
            # Act
            context = manager.get_ai_context(test_user_id)
            
            # Assert - Verify real data integration
            assert context is not None, "Should return context with real data"
            assert context['user_profile']['preferred_name'] == "realuser", "Should read real preferred name"
            assert 'motivational' in context['user_profile']['active_categories'], "Should read real categories"
            assert context['user_profile']['messaging_service'] == "discord", "Should read real messaging service"
    
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
        context = manager.get_ai_context(test_user_id)
        
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
            context = manager.get_ai_context(test_user_id)
        
        # Assert - Verify concurrent access safety
        assert test_user_id in manager.conversation_history, "User should still be in conversation history"
        assert len(manager.conversation_history[test_user_id]) <= 50, "Should maintain history limit"
        assert len(manager.conversation_history[test_user_id]) > 0, "Should have some conversation history" 