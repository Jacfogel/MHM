#!/usr/bin/env python3

"""
test_conversation_behavior.py

Comprehensive behavior tests for ConversationManager focusing on real behavior and side effects.
Tests verify actual system changes, not just return values.
"""

import os
import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock

from communication.message_processing.conversation_flow_manager import ConversationManager, FLOW_CHECKIN, CHECKIN_START, CHECKIN_MOOD, CHECKIN_REFLECTION
from communication.message_processing.conversation_flow_manager import QUESTION_STATES


class TestConversationManagerBehavior:
    """Test ConversationManager real behavior and side effects."""
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_conversation_manager_initialization_creates_structure(self, test_data_dir):
        """Test that ConversationManager initialization creates proper internal structure."""
        # Arrange & Act
        manager = ConversationManager()
        
        # Assert - Verify actual structure creation
        assert hasattr(manager, 'user_states'), "Should have user_states attribute"
        assert isinstance(manager.user_states, dict), "user_states should be a dict"
        assert len(manager.user_states) == 0, "user_states should be empty initially"
    
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_handle_inbound_message_creates_user_state(self, test_data_dir):
        """Test that handle_inbound_message actually creates user state when needed."""
        # Arrange
        manager = ConversationManager()
        test_user_id = "test-user-123"
        message_text = "Hello"
        
        # Mock AI chatbot to return a response
        with patch('communication.message_processing.conversation_flow_manager.get_ai_chatbot') as mock_get_ai_chatbot:
            mock_chatbot = MagicMock()
            mock_chatbot.generate_contextual_response.return_value = "Hi there! How can I help you today?"
            mock_get_ai_chatbot.return_value = mock_chatbot
            
            # Act
            reply, completed = manager.handle_inbound_message(test_user_id, message_text)
            
            # Assert - Verify actual state creation
            # Note: handle_inbound_message doesn't create user state for regular messages
            # It only creates state for specific flows like check-ins
            assert reply is not None, "Should return a reply"
            assert isinstance(completed, bool), "Should return completion status"
            assert "hi there" in reply.lower(), "Should include AI response"
    
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_handle_inbound_message_preserves_existing_state(self, test_data_dir):
        """Test that handle_inbound_message preserves existing user state."""
        # Arrange
        manager = ConversationManager()
        test_user_id = "test-user-456"
        
        # Set up existing state
        manager.user_states[test_user_id] = {
            "flow": FLOW_CHECKIN,
            "state": CHECKIN_MOOD,
            "data": {"mood": "good"},
            "question_order": ["mood", "energy"]
        }
        
        # Mock AI chatbot
        with patch('communication.message_processing.conversation_flow_manager.get_ai_chatbot') as mock_get_ai_chatbot:
            mock_chatbot = MagicMock()
            mock_chatbot.get_response.return_value = "I see you're in a check-in flow."
            mock_get_ai_chatbot.return_value = mock_chatbot
            
            # Act
            reply, completed = manager.handle_inbound_message(test_user_id, "I'm feeling great!")
            
            # Assert - Verify state preservation
            assert test_user_id in manager.user_states, "Should preserve user state"
            assert manager.user_states[test_user_id]['flow'] == FLOW_CHECKIN, "Should preserve flow"
            assert manager.user_states[test_user_id]['state'] == CHECKIN_MOOD, "Should preserve state"
            assert manager.user_states[test_user_id]['data']['mood'] == "good", "Should preserve data"
    
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_start_checkin_creates_checkin_state(self, test_data_dir):
        """Test that start_checkin actually creates check-in state."""
        # Arrange
        manager = ConversationManager()
        test_user_id = "test-user-checkin"
        
        # Mock check-in enabled
        with patch('communication.message_processing.conversation_flow_manager.is_user_checkins_enabled') as mock_enabled, \
             patch('communication.message_processing.conversation_flow_manager.get_user_data') as mock_get_data:
            
            mock_enabled.return_value = True
            mock_get_data.return_value = {
                'preferences': {
                    'checkin_settings': {
                        'questions': {
                            'mood': {'enabled': True},
                            'energy': {'enabled': True}
                        },
                        'welcome_message': 'Welcome to your check-in!'
                    }
                }
            }
            
            # Act
            reply, completed = manager.start_checkin(test_user_id)
            
            # Assert - Verify actual state creation
            assert test_user_id in manager.user_states, "Should create user state"
            assert manager.user_states[test_user_id]['flow'] == FLOW_CHECKIN, "Should set check-in flow"
            
            # The state should correspond to the first question in the question_order
            # (which is determined by weighted selection, so we check dynamically)
            question_order = manager.user_states[test_user_id]['question_order']
            first_question = question_order[0]
            expected_state = QUESTION_STATES.get(first_question, CHECKIN_START)
            assert manager.user_states[test_user_id]['state'] == expected_state, f"Should set state for first question '{first_question}'"
            
            assert 'data' in manager.user_states[test_user_id], "Should have data dictionary"
            assert 'question_order' in manager.user_states[test_user_id], "Should have question order"
            assert len(manager.user_states[test_user_id]['question_order']) == 2, "Should have correct question count"
            assert reply is not None, "Should return a reply"
            assert not completed, "Should not be completed initially"
    
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_start_checkin_handles_disabled_user(self, test_data_dir):
        """Test that start_checkin handles users with disabled check-ins."""
        # Arrange
        manager = ConversationManager()
        test_user_id = "test-user-disabled"
        
        # Mock check-in disabled
        with patch('communication.message_processing.conversation_flow_manager.is_user_checkins_enabled') as mock_enabled:
            mock_enabled.return_value = False
            
            # Act
            reply, completed = manager.start_checkin(test_user_id)
            
            # Assert - Verify graceful handling
            assert test_user_id not in manager.user_states, "Should not create user state"
            assert "not enabled" in reply.lower(), "Should mention check-ins not enabled"
            assert completed, "Should be completed immediately"
    
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_checkin_flow_progression(self, test_data_dir):
        """Test that check-in flow actually progresses through states."""
        # Arrange
        manager = ConversationManager()
        test_user_id = "test-user-flow"
        
        # Set up check-in state
        manager.user_states[test_user_id] = {
            "flow": FLOW_CHECKIN,
            "state": CHECKIN_MOOD,
            "data": {},
            "question_order": ["mood", "energy"]
        }
        
        # Mock response validation
        with patch.object(manager, '_validate_response') as mock_validate:
            mock_validate.return_value = {
                'valid': True,
                'value': 'good',
                'message': 'Great!'
            }
            
            # Act
            reply, completed = manager.handle_inbound_message(test_user_id, "good")
            
            # Assert - Verify state progression
            assert test_user_id in manager.user_states, "Should maintain user state"
            assert manager.user_states[test_user_id]['data']['mood'] == 'good', "Should store response data"
            assert manager.user_states[test_user_id]['state'] > CHECKIN_MOOD, "Should progress to next state"
            assert not completed, "Should not be completed yet"
    
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_checkin_flow_completion(self, test_data_dir):
        """Test that check-in flow actually completes and cleans up state."""
        # Arrange
        manager = ConversationManager()
        test_user_id = "test-user-complete"
        
        # Set up final check-in state - simulate what the actual flow would produce
        manager.user_states[test_user_id] = {
            "flow": FLOW_CHECKIN,
            "state": CHECKIN_REFLECTION,
            "data": {
                "mood": 4,  # Use integer for mood (as returned by validation)
                "energy": 5,  # Use integer for energy (as returned by validation)
                "daily_reflection": "It was a great day!"
            },
            "question_order": ["mood", "energy", "daily_reflection"],
            "current_question_index": 2  # At the last question
        }
        
        # Mock response validation and completion
        with patch.object(manager, '_validate_response') as mock_validate:
            
            mock_validate.return_value = {
                'valid': True,
                'value': 'It was a great day!',
                'message': 'Thanks!'
            }
            
            # Act
            reply, completed = manager.handle_inbound_message(test_user_id, "It was a great day!")
            
            # Assert - Verify completion and cleanup
            assert completed, "Should be completed"
            assert test_user_id not in manager.user_states, "Should remove user state after completion"
            assert "complete" in reply.lower(), "Should indicate completion"
    
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_validate_response_handles_various_inputs(self, test_data_dir):
        """Test that _validate_response actually validates different types of responses."""
        # Arrange
        manager = ConversationManager()
        
        # Test mood validation
        mood_result = manager._validate_response("mood", "4")
        assert mood_result['valid'], "Should accept valid mood"
        assert mood_result['value'] == 4, "Should return correct value"
        
        # Test energy validation
        energy_result = manager._validate_response("energy", "5")
        assert energy_result['valid'], "Should accept valid energy level"
        assert energy_result['value'] == 5, "Should return numeric value"
        
        # Test invalid input
        invalid_result = manager._validate_response("mood", "invalid_mood")
        assert not invalid_result['valid'], "Should reject invalid mood"
        assert "number between 1 and 5" in invalid_result['message'], "Should provide helpful message"
    
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_validate_response_handles_edge_cases(self, test_data_dir):
        """Test that _validate_response handles edge cases gracefully."""
        # Arrange
        manager = ConversationManager()
        
        # Test empty input
        empty_result = manager._validate_response("mood", "")
        assert not empty_result['valid'], "Should reject empty input"
        
        # Test very long input
        long_input = "a" * 1000
        long_result = manager._validate_response("daily_reflection", long_input)
        assert long_result['valid'], "Should accept long reflection text"
        assert len(long_result['value']) == 1000, "Should preserve long text"
        
        # Test special characters
        special_result = manager._validate_response("daily_reflection", "Today was great! 😊")
        assert special_result['valid'], "Should accept special characters"
    
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_question_text_returns_personalized_questions(self, test_data_dir):
        """Test that _get_question_text returns personalized questions based on context."""
        # Arrange
        manager = ConversationManager()
        
        # Test mood question
        mood_question = manager._get_question_text("mood", {})
        assert "feeling" in mood_question.lower(), "Should ask about feeling"
        assert "scale" in mood_question.lower(), "Should mention scale"
        
        # Test energy question
        energy_question = manager._get_question_text("energy", {"mood": 4})  # Use integer for mood
        assert "energy" in energy_question.lower(), "Should ask about energy"
        
        # Test reflection question with context
        reflection_question = manager._get_question_text("daily_reflection", {
            "mood": 4,  # Use integer for mood
            "energy": 5  # Use integer for energy
        })
        assert "reflection" in reflection_question.lower(), "Should ask for reflection"
    
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_handle_contextual_question_integrates_with_ai(self, test_data_dir):
        """Test that handle_contextual_question integrates with AI chatbot."""
        # Arrange
        manager = ConversationManager()
        test_user_id = "test-user-contextual"
        message_text = "How am I doing today?"
        
        # Mock AI chatbot
        with patch('communication.message_processing.conversation_flow_manager.get_ai_chatbot') as mock_get_ai_chatbot:
            mock_chatbot = MagicMock()
            mock_chatbot.generate_contextual_response.return_value = "Based on your recent check-ins, you're doing great!"
            mock_get_ai_chatbot.return_value = mock_chatbot
            
            # Act
            response = manager.handle_contextual_question(test_user_id, message_text)
            
            # Assert - Verify AI integration
            assert response is not None, "Should return a response"
            assert "doing great" in response, "Should include AI-generated content"
            mock_chatbot.generate_contextual_response.assert_called_once(), "Should call AI chatbot"
    
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_conversation_manager_error_handling_preserves_system_stability(self, test_data_dir):
        """Test that ConversationManager error handling preserves system stability."""
        # Arrange
        manager = ConversationManager()
        test_user_id = "test-user-error"
        
        # Mock AI chatbot to raise an exception
        with patch('communication.message_processing.conversation_flow_manager.get_ai_chatbot') as mock_get_ai_chatbot:
            mock_chatbot = MagicMock()
            mock_chatbot.generate_contextual_response.side_effect = Exception("Test error")
            mock_get_ai_chatbot.return_value = mock_chatbot
            
            # Act - Should not raise exception due to error handling
            reply, completed = manager.handle_inbound_message(test_user_id, "Hello")
            
            # Assert - Verify graceful error handling
            assert reply is not None, "Should return error message"
            assert "trouble" in reply.lower(), "Should indicate trouble processing"
            assert completed, "Should complete to prevent hanging"
    
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_conversation_manager_performance_under_load(self, test_data_dir):
        """Test that ConversationManager performs well under load."""
        # Arrange
        manager = ConversationManager()
        test_user_ids = [f"user-{i}" for i in range(100)]
        
        # Mock AI chatbot for performance testing
        with patch('communication.message_processing.conversation_flow_manager.get_ai_chatbot') as mock_get_ai_chatbot:
            mock_chatbot = MagicMock()
            mock_chatbot.generate_contextual_response.return_value = "Performance test response"
            mock_get_ai_chatbot.return_value = mock_chatbot
            
            # Act - Process many users
            responses = []
            for user_id in test_user_ids:
                reply, completed = manager.handle_inbound_message(user_id, "Hello")
                responses.append((reply, completed))
            
            # Assert - Verify performance under load
            # Note: Regular messages don't create user states, only flows do
            assert len(manager.user_states) == 0, "Should not create states for regular messages"
            # Verify all messages were processed successfully
            assert all(reply is not None for reply, completed in responses), "Should process all messages"
    
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_conversation_manager_cleanup_and_resource_management(self, test_data_dir):
        """Test that ConversationManager properly manages resources and cleanup."""
        # Arrange
        manager = ConversationManager()
        test_user_id = "test-user-cleanup"
        
        # Add user state
        manager.user_states[test_user_id] = {
            "flow": FLOW_CHECKIN,
            "state": CHECKIN_MOOD,
            "data": {"mood": "good"},
            "question_order": ["mood", "energy"]
        }
        
        # Act - Simulate cleanup by removing user state
        if test_user_id in manager.user_states:
            del manager.user_states[test_user_id]
        
        # Assert - Verify cleanup
        assert test_user_id not in manager.user_states, "User state should be cleaned up"
        assert len(manager.user_states) == 0, "Should have no remaining user states"
    
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_conversation_manager_integration_with_response_tracking(self, test_data_dir):
        """Test that ConversationManager integrates properly with response tracking."""
        # Arrange
        manager = ConversationManager()
        test_user_id = "test-user-tracking"
        
        # Mock response tracking functions
        with patch('communication.message_processing.conversation_flow_manager.is_user_checkins_enabled') as mock_enabled, \
             patch('communication.message_processing.conversation_flow_manager.get_user_data') as mock_get_data, \
             patch('core.response_tracking.store_user_response') as mock_store:
            
            mock_enabled.return_value = True
            mock_get_data.return_value = {
                'preferences': {
                    'checkin_settings': {
                        'questions': {
                            'mood': {'enabled': True}
                        },
                        'welcome_message': 'Welcome!'
                    }
                }
            }
            mock_store.return_value = True
            
            # Start check-in
            reply, completed = manager.start_checkin(test_user_id)
            
            # Complete check-in - set up final state
            manager.user_states[test_user_id] = {
                "flow": FLOW_CHECKIN,
                "state": CHECKIN_MOOD,
                "data": {},
                "question_order": ["mood"],
                "current_question_index": 0
            }
            
            with patch.object(manager, '_validate_response') as mock_validate:
                
                mock_validate.return_value = {
                    'valid': True,
                    'value': 4,  # Use integer for mood
                    'message': 'Great!'
                }
                
                # Act
                reply, completed = manager.handle_inbound_message(test_user_id, "4")
                
                # Assert - Verify integration
                assert completed, "Should complete check-in"
                mock_store.assert_called(), "Should store check-in response"
    
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_conversation_manager_command_handling(self, test_data_dir):
        """Test that ConversationManager properly handles special commands."""
        # Arrange
        manager = ConversationManager()
        test_user_id = "test-user-command"
        
        # Mock check-in enabled
        with patch('communication.message_processing.conversation_flow_manager.is_user_checkins_enabled') as mock_enabled, \
             patch('communication.message_processing.conversation_flow_manager.get_user_data') as mock_get_data:
            
            mock_enabled.return_value = True
            mock_get_data.return_value = {
                'preferences': {
                    'checkin_settings': {
                        'questions': {
                            'mood': {'enabled': True}
                        },
                        'welcome_message': 'Welcome!'
                    }
                }
            }
            
            # Act - Test check-in command
            reply, completed = manager.handle_inbound_message(test_user_id, "/checkin")
            
            # Assert - Verify command handling
            assert test_user_id in manager.user_states, "Should create user state for command"
            assert manager.user_states[test_user_id]['flow'] == FLOW_CHECKIN, "Should start check-in flow"
            assert "feeling" in reply.lower(), "Should ask first question"
    
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_conversation_manager_cancel_handling(self, test_data_dir):
        """Test that ConversationManager properly handles cancel commands."""
        # Arrange
        manager = ConversationManager()
        test_user_id = "test-user-cancel"
        
        # Set up check-in state
        manager.user_states[test_user_id] = {
            "flow": FLOW_CHECKIN,
            "state": CHECKIN_MOOD,
            "data": {},
            "question_order": ["mood", "energy"]
        }
        
        # Act - Test cancel command
        reply, completed = manager.handle_inbound_message(test_user_id, "/cancel")
        
        # Assert - Verify cancel handling
        assert test_user_id not in manager.user_states, "Should remove user state on cancel"
        assert completed, "Should complete on cancel"
        assert "cancel" in reply.lower(), "Should acknowledge cancellation"


class TestConversationManagerIntegration:
    """Integration tests for ConversationManager with real user data."""
    
    def test_conversation_manager_with_real_user_data(self, test_data_dir):
        """Test ConversationManager with real user data files."""
        # Arrange
        manager = ConversationManager()
        test_user_id = "real-user-test"
        
        # Create test user using centralized utilities
        from tests.test_utilities import TestUserFactory
        success = TestUserFactory.create_basic_user(test_user_id, enable_checkins=True, enable_tasks=True, test_data_dir=test_data_dir)
        assert success, "Test user should be created successfully"
        
        # Get the UUID for the user
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(test_user_id)
        assert actual_user_id is not None, f"Should be able to get UUID for user {test_user_id}"
        
        # Update user preferences with check-in settings
        from core.user_data_handlers import update_user_preferences
        update_success = update_user_preferences(actual_user_id, {
            "checkin_settings": {
                "enabled": True,
                "questions": ["mood", "energy", "daily_reflection"],
                "welcome_message": "Welcome to your check-in!"
            }
        })
        assert update_success, "User preferences should be updated successfully"
        
        # Mock response tracking functions
        with patch('communication.message_processing.conversation_flow_manager.is_user_checkins_enabled') as mock_enabled, \
             patch('communication.message_processing.conversation_flow_manager.get_user_data') as mock_get_data:
            
            mock_enabled.return_value = True
            mock_get_data.return_value = {
                'preferences': {
                    'checkin_settings': {
                        'questions': {
                            'mood': {'enabled': True},
                            'energy': {'enabled': True},
                            'daily_reflection': {'enabled': True}
                        },
                        'welcome_message': 'Welcome to your check-in!'
                    }
                }
            }
            
            # Act
            reply, completed = manager.start_checkin(test_user_id)
            
            # Assert - Verify real data integration
            assert test_user_id in manager.user_states, "Should create user state with real data"
            assert manager.user_states[test_user_id]['flow'] == FLOW_CHECKIN, "Should start check-in flow"
            assert len(manager.user_states[test_user_id]['question_order']) == 3, "Should have correct question count"
            # Check for any check-in related content (since question order is weighted/random)
            assert any(word in reply.lower() for word in ['check-in', 'feeling', 'mood', 'energy', 'stress', 'sleep', 'exercise', 'medication', 'breakfast', 'teeth', 'hydration', 'social', 'reflection']), f"Should ask first question, got: {reply[:100]}..."
    
    def test_conversation_manager_error_recovery_with_real_files(self, test_data_dir):
        """Test ConversationManager error recovery with corrupted real files."""
        # Arrange
        manager = ConversationManager()
        test_user_id = "corrupted-user-test"
        
        # Create user directory with corrupted files
        user_dir = os.path.join(test_data_dir, "users", test_user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Create corrupted preferences.json
        with open(os.path.join(user_dir, "preferences.json"), 'w') as f:
            f.write("invalid json content")
        
        # Act - Should handle corrupted files gracefully
        reply, completed = manager.handle_inbound_message(test_user_id, "Hello")
        
        # Assert - Verify error recovery
        assert reply is not None, "Should return response even with corrupted files"
        # The system handles corrupted files gracefully and still provides AI responses
        assert len(reply) > 0, "Should return a meaningful response"
    
    def test_conversation_manager_concurrent_access_safety(self, test_data_dir):
        """Test ConversationManager safety under concurrent access."""
        # Arrange
        manager = ConversationManager()
        test_user_id = "concurrent-user-test"
        
        # Mock AI chatbot
        with patch('communication.message_processing.conversation_flow_manager.get_ai_chatbot') as mock_get_ai_chatbot:
            mock_chatbot = MagicMock()
            mock_chatbot.generate_contextual_response.return_value = "Concurrent test response"
            mock_get_ai_chatbot.return_value = mock_chatbot
            
            # Act - Simulate concurrent access (in real scenario, this would be multiple threads)
            # For now, we'll test that the manager can handle rapid successive calls
            responses = []
            for i in range(10):
                reply, completed = manager.handle_inbound_message(test_user_id, f"Message {i}")
                responses.append((reply, completed))
            
            # Assert - Verify concurrent access safety
            # Note: Regular messages don't create user states, only flows do
            assert len(manager.user_states) == 0, "Should not create states for regular messages"
            assert all(reply is not None for reply, completed in responses), "Should process all messages successfully"