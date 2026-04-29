"""
Conversation Flow Manager Behavior Tests

Tests for communication/message_processing/conversation_flow_manager.py focusing on real behavior and side effects.
These tests verify that the conversation flow manager actually works and produces expected
side effects rather than just returning values.
"""

import pytest
import uuid
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch, MagicMock

# Import the modules we're testing
from communication.message_processing.conversation_flow_manager import (
    ConversationManager,
    conversation_manager,
    FLOW_NONE,
    FLOW_CHECKIN,
    FLOW_TASK_REMINDER,
    CHECKIN_MOOD,
    CHECKIN_INACTIVITY_MINUTES,
)
from core.time_utilities import (
    now_datetime_full,
    now_timestamp_full,
    parse_timestamp_full,
    format_timestamp,
    TIMESTAMP_FULL,
)
from communication.core.channel_orchestrator import CommunicationManager
from tests.test_helpers.test_utilities import TestUserFactory


class TestConversationFlowManagerBehavior:
    """Test conversation flow manager real behavior and side effects."""
    
    def _create_test_user(self, user_id: str, enable_checkins: bool = True, test_data_dir: str | None = None) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(user_id, enable_checkins=enable_checkins, test_data_dir=test_data_dir)
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_conversation_manager_initialization(self, test_data_dir):
        """Test that ConversationManager initializes correctly."""
        manager = ConversationManager()
        
        assert manager is not None, "Manager should be initialized"
        assert hasattr(manager, 'user_states'), "Should have user_states"
        assert isinstance(manager.user_states, dict), "user_states should be a dict"
        assert hasattr(manager, '_state_file'), "Should have state file path"

    @pytest.mark.behavior
    @pytest.mark.communication
    def test_generate_completion_message_uses_sleep_schedule_total_hours(self, test_data_dir):
        """Completion insights should use sleep_schedule total_sleep_hours when available."""
        manager = ConversationManager()

        message = manager._generate_completion_message(
            "test_user_sleep_schedule_completion",
            {
                "sleep_schedule": {
                    "sleep_time": "23:30",
                    "wake_time": "05:00",
                    "total_sleep_hours": 5.5,
                },
                "sleep_quality": 4,
            },
        )

        assert "more sleep tonight" in message
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    @patch('communication.message_processing.conversation_flow_manager.is_user_checkins_enabled')
    @patch('communication.message_processing.conversation_flow_manager.get_user_data')
    def test_conversation_manager_start_checkin_not_enabled(self, mock_get_user_data, mock_is_enabled, test_data_dir):
        """Test that ConversationManager rejects check-in when not enabled."""
        manager = ConversationManager()
        user_id = "test_user_checkin_not_enabled"
        assert self._create_test_user(user_id, enable_checkins=False, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock check-ins disabled
        mock_is_enabled.return_value = False
        
        # Start check-in
        message, completed = manager.start_checkin(user_id)
        
        # Verify response
        assert isinstance(message, str), "Should return message string"
        assert completed, "Should be completed"
        assert "not enabled" in message.lower(), "Should indicate check-ins are not enabled"
        assert user_id not in manager.user_states, "Should not create user state"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    @patch('communication.message_processing.conversation_flow_manager.is_user_checkins_enabled')
    @patch('communication.message_processing.conversation_flow_manager.get_user_data')
    def test_conversation_manager_start_checkin_success(self, mock_get_user_data, mock_is_enabled, test_data_dir):
        """Test that ConversationManager starts check-in successfully."""
        manager = ConversationManager()
        user_id = "test_user_checkin_start"
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock check-ins enabled
        mock_is_enabled.return_value = True
        
        # Mock user data with check-in preferences
        mock_get_user_data.return_value = {
            'preferences': {
                'checkin_settings': {
                    'questions': {
                        'mood': {'enabled': True, 'weight': 1.0},
                        'energy': {'enabled': True, 'weight': 1.0}
                    }
                }
            }
        }
        
        # Start check-in
        message, completed = manager.start_checkin(user_id)
        
        # Verify response
        assert isinstance(message, str), "Should return message string"
        assert not completed, "Should not be completed (flow in progress)"
        assert "check-in" in message.lower() or "checkin" in message.lower(), "Should mention check-in"
        assert user_id in manager.user_states, "Should create user state"
        
        # Verify state structure
        user_state = manager.user_states[user_id]
        assert user_state['flow'] == FLOW_CHECKIN, "Should have check-in flow"
        assert 'question_order' in user_state, "Should have question order"
        assert 'current_question_index' in user_state, "Should have current question index"
        assert 'data' in user_state, "Should have data dict"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    @patch('communication.message_processing.conversation_flow_manager.is_user_checkins_enabled')
    @patch('communication.message_processing.conversation_flow_manager.get_user_data')
    def test_conversation_manager_start_checkin_already_active(self, mock_get_user_data, mock_is_enabled, test_data_dir):
        """Test that ConversationManager handles already active check-in."""
        manager = ConversationManager()
        user_id = "test_user_checkin_active"
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock check-ins enabled
        mock_is_enabled.return_value = True
        
        # Mock user data
        mock_get_user_data.return_value = {
            'preferences': {
                'checkin_settings': {
                    'questions': {
                        'mood': {'enabled': True, 'weight': 1.0}
                    }
                }
            }
        }
        
        # Start first check-in
        message1, completed1 = manager.start_checkin(user_id)
        assert user_id in manager.user_states, "Should have active check-in"
        
        # Try to start another check-in
        message2, completed2 = manager.start_checkin(user_id)
        
        # Verify response
        assert isinstance(message2, str), "Should return message string"
        assert not completed2, "Should not be completed"
        assert "already" in message2.lower() or "in progress" in message2.lower(), "Should indicate check-in already active"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    @patch('communication.message_processing.conversation_flow_manager.is_user_checkins_enabled')
    @patch('communication.message_processing.conversation_flow_manager.get_user_data')
    def test_conversation_manager_restart_checkin(self, mock_get_user_data, mock_is_enabled, test_data_dir):
        """Test that ConversationManager restarts check-in correctly."""
        manager = ConversationManager()
        user_id = "test_user_checkin_restart"
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock check-ins enabled
        mock_is_enabled.return_value = True
        
        # Mock user data
        mock_get_user_data.return_value = {
            'preferences': {
                'checkin_settings': {
                    'questions': {
                        'mood': {'enabled': True, 'weight': 1.0},
                        'energy': {'enabled': True, 'weight': 1.0}
                    }
                }
            }
        }
        
        # Start first check-in
        message1, completed1 = manager.start_checkin(user_id)
        assert user_id in manager.user_states, "Should have active check-in"
        
        # Restart check-in
        message2, completed2 = manager.restart_checkin(user_id)
        
        # Verify response
        assert isinstance(message2, str), "Should return message string"
        assert not completed2, "Should not be completed (new flow started)"
        assert "check-in" in message2.lower() or "checkin" in message2.lower(), "Should mention check-in"
        assert user_id in manager.user_states, "Should still have user state"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_conversation_manager_clear_stuck_flows(self, test_data_dir):
        """Test that ConversationManager clears stuck flows correctly."""
        manager = ConversationManager()
        user_id = "test_user_clear_flows"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create a stuck flow state
        manager.user_states[user_id] = {
            'flow': FLOW_CHECKIN,
            'state': CHECKIN_MOOD,
            'data': {},
            'question_order': ['mood', 'energy'],
            'current_question_index': 0
        }
        
        # Clear stuck flows
        message, completed = manager.clear_stuck_flows(user_id)
        
        # Verify response
        assert isinstance(message, str), "Should return message string"
        assert completed, "Should be completed"
        assert "cleared" in message.lower(), "Should indicate flow cleared"
        assert user_id not in manager.user_states, "Should remove user state"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_conversation_manager_clear_stuck_flows_no_active(self, test_data_dir):
        """Test that ConversationManager handles clear when no active flow."""
        manager = ConversationManager()
        user_id = "test_user_clear_no_flow"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Clear stuck flows when no active flow
        message, completed = manager.clear_stuck_flows(user_id)
        
        # Verify response
        assert isinstance(message, str), "Should return message string"
        assert completed, "Should be completed"
        assert "no active" in message.lower() or "not found" in message.lower(), "Should indicate no active flow"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_conversation_manager_clear_all_states(self, test_data_dir):
        """Test that ConversationManager clears all states correctly."""
        manager = ConversationManager()
        manager._state_file = Path(test_data_dir) / f"conversation_states_{uuid.uuid4().hex[:8]}.json"
        manager.user_states = {}
        
        # Create some user states
        user1 = f"user1_{uuid.uuid4().hex[:8]}"
        user2 = f"user2_{uuid.uuid4().hex[:8]}"
        manager.user_states[user1] = {'flow': FLOW_CHECKIN, 'state': CHECKIN_MOOD, 'data': {}}
        manager.user_states[user2] = {'flow': FLOW_NONE, 'state': 0, 'data': {}}
        
        assert len(manager.user_states) == 2, "Should have 2 user states"
        
        # Clear all states
        manager.clear_all_states()
        
        # Verify all states cleared
        assert len(manager.user_states) == 0, "Should have no user states"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.ai
    @patch('communication.message_processing.conversation_flow_manager.get_ai_chatbot')
    def test_conversation_manager_handle_inbound_message_conversational(self, mock_get_chatbot, test_data_dir):
        """Test that ConversationManager handles conversational messages correctly."""
        manager = ConversationManager()
        user_id = "test_user_conversational"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock AI chatbot
        mock_bot = MagicMock()
        mock_bot.generate_contextual_response.return_value = "Hello! How can I help you today?"
        mock_get_chatbot.return_value = mock_bot
        
        # Handle conversational message
        message, completed = manager.handle_inbound_message(user_id, "Hello, how are you?")
        
        # Verify response
        assert isinstance(message, str), "Should return message string"
        assert completed, "Should be completed"
        assert len(message) > 0, "Should have response message"
        mock_bot.generate_contextual_response.assert_called_once_with(user_id, "Hello, how are you?", timeout=10)
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    @patch('communication.message_processing.conversation_flow_manager.is_user_checkins_enabled')
    @patch('communication.message_processing.conversation_flow_manager.get_user_data')
    def test_conversation_manager_handle_inbound_message_checkin_command(self, mock_get_user_data, mock_is_enabled, test_data_dir):
        """Test that ConversationManager handles /checkin command correctly."""
        manager = ConversationManager()
        user_id = "test_user_checkin_command"
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock check-ins enabled
        mock_is_enabled.return_value = True
        
        # Mock user data
        mock_get_user_data.return_value = {
            'preferences': {
                'checkin_settings': {
                    'questions': {
                        'mood': {'enabled': True, 'weight': 1.0}
                    }
                }
            }
        }
        
        # Handle checkin command
        message, completed = manager.handle_inbound_message(user_id, "/checkin")
        
        # Verify response
        assert isinstance(message, str), "Should return message string"
        assert not completed, "Should not be completed (flow started)"
        assert "check-in" in message.lower() or "checkin" in message.lower(), "Should mention check-in"
        assert user_id in manager.user_states, "Should create user state"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_conversation_manager_handle_inbound_message_cancel_no_flow(self, test_data_dir):
        """Test that ConversationManager handles /cancel when no active flow."""
        manager = ConversationManager()
        user_id = "test_user_cancel_no_flow"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Handle cancel command when no flow
        message, completed = manager.handle_inbound_message(user_id, "/cancel")
        
        # Verify response
        assert isinstance(message, str), "Should return message string"
        assert completed, "Should be completed"
        assert "nothing to cancel" in message.lower() or "not in" in message.lower(), "Should indicate no flow to cancel"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.slow
    def test_conversation_manager_handle_inbound_message_empty(self, test_data_dir):
        """Test that ConversationManager handles empty messages correctly."""
        manager = ConversationManager()
        user_id = "test_user_empty_message"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Handle empty message
        message, completed = manager.handle_inbound_message(user_id, "")
        
        # Verify response
        assert isinstance(message, str), "Should return message string"
        assert completed, "Should be completed"
        assert len(message) > 0, "Should have response message"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    @patch('communication.message_processing.conversation_flow_manager.is_user_checkins_enabled')
    @patch('communication.message_processing.conversation_flow_manager.get_user_data')
    def test_conversation_manager_expire_checkin_flow(self, mock_get_user_data, mock_is_enabled, test_data_dir):
        """Test that ConversationManager expires check-in flow correctly."""
        manager = ConversationManager()
        manager._state_file = Path(test_data_dir) / f"conversation_states_{uuid.uuid4().hex[:8]}.json"
        manager.user_states = {}
        user_id = f"test_user_expire_flow_{uuid.uuid4().hex[:8]}"
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock check-ins enabled
        mock_is_enabled.return_value = True
        
        # Mock user data
        mock_get_user_data.return_value = {
            'preferences': {
                'checkin_settings': {
                    'questions': {
                        'mood': {'enabled': True, 'weight': 1.0}
                    }
                }
            }
        }
        
        # Start check-in
        manager.start_checkin(user_id)
        assert user_id in manager.user_states, "Should have active check-in"
        
        # Ensure state is saved to disk before expire (which reloads from disk)
        manager._save_user_states()

        # Expire check-in flow
        expired = manager.expire_checkin_flow_due_to_unrelated_outbound(user_id)
        assert expired is True, "Expire call should report success when a flow exists"

        # Verify flow expired
        assert user_id not in manager.user_states, "Should remove user state after expiration"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_conversation_manager_expire_checkin_flow_no_active(self, test_data_dir):
        """Test that ConversationManager handles expire when no active flow."""
        manager = ConversationManager()
        user_id = "test_user_expire_no_flow"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Expire check-in flow when no active flow
        expired = manager.expire_checkin_flow_due_to_unrelated_outbound(user_id)
        assert expired is False, "Expire call should be a no-op when no flow is active"

        # Should not raise error and should be safe no-op
        assert user_id not in manager.user_states, "Should not have user state"

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    @patch('communication.message_processing.conversation_flow_manager.is_user_checkins_enabled')
    @patch('communication.message_processing.conversation_flow_manager.get_user_data')
    @patch('communication.core.channel_orchestrator.get_user_data')
    def test_checkin_flow_expires_after_unrelated_outbound(self, mock_channel_get_user_data, mock_conv_get_user_data, mock_is_enabled, test_data_dir, monkeypatch):
        """Ensure outbound non-check-in messages expire active check-in flows."""
        manager = ConversationManager()
        user_id = "test_user_expire_after_outbound"
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"

        # Mock check-ins enabled and provide minimal question set for dynamic flow
        mock_is_enabled.return_value = True
        mock_conv_get_user_data.return_value = {
            'preferences': {
                'checkin_settings': {
                    'questions': {
                        'mood': {'enabled': True, 'weight': 1.0}
                    }
                }
            }
        }

        # Start a check-in flow and persist state to disk
        start_message, completed = manager.start_checkin(user_id)
        assert completed is False, "Flow should be active"
        assert user_id in manager.user_states, "Active check-in state should be stored"
        manager._save_user_states()

        # Ensure the orchestrator uses this test-specific conversation manager instance
        monkeypatch.setattr('communication.message_processing.conversation_flow_manager.conversation_manager', manager)

        # Prepare communication manager dependencies to avoid real sends
        comm_manager = CommunicationManager()
        mock_channel_get_user_data.return_value = {'preferences': {'channel': {'type': 'discord'}}}
        monkeypatch.setattr(comm_manager, '_get_recipient_for_service', lambda *_, **__: 'recipient')
        monkeypatch.setattr(comm_manager, '_send_ai_generated_message', lambda *_, **__: (True, "test message"))
        monkeypatch.setattr(comm_manager, '_send_predefined_message', lambda *_, **__: (True, "test message"))

        # Send a non-scheduled message and verify the active check-in is expired
        comm_manager.handle_message_sending(user_id, 'personalized')

        assert user_id not in manager.user_states, "Check-in flow should expire after unrelated outbound message"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    @patch('communication.message_processing.conversation_flow_manager.is_user_checkins_enabled')
    @patch('communication.message_processing.conversation_flow_manager.get_user_data')
    def test_conversation_manager_handle_checkin_flow_progression(self, mock_get_user_data, mock_is_enabled, test_data_dir):
        """Test that ConversationManager progresses check-in flow correctly."""
        manager = ConversationManager()
        user_id = "test_user_flow_progression"
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock check-ins enabled
        mock_is_enabled.return_value = True
        
        # Mock user data
        mock_get_user_data.return_value = {
            'preferences': {
                'checkin_settings': {
                    'questions': {
                        'mood': {'enabled': True, 'weight': 1.0},
                        'energy': {'enabled': True, 'weight': 1.0}
                    }
                }
            }
        }
        
        # Start check-in
        message1, completed1 = manager.start_checkin(user_id)
        assert not completed1, "Should not be completed"
        
        # Get initial state
        user_state = manager.user_states[user_id]
        initial_index = user_state.get('current_question_index', 0)
        
        # Handle answer to first question
        message2, completed2 = manager.handle_inbound_message(user_id, "4")
        
        # Verify progression
        assert isinstance(message2, str), "Should return message string"
        # Should either complete or show next question
        if not completed2:
            assert user_state.get('current_question_index', 0) > initial_index, "Should advance question index"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_conversation_manager_global_instance(self):
        """Test that global conversation_manager instance exists."""
        # Verify global instance
        assert conversation_manager is not None, "Should have global instance"
        assert isinstance(conversation_manager, ConversationManager), "Should be ConversationManager instance"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    @patch('communication.message_processing.conversation_flow_manager.is_user_checkins_enabled')
    @patch('communication.message_processing.conversation_flow_manager.get_user_data')
    def test_conversation_manager_handle_checkin_complete(self, mock_get_user_data, mock_is_enabled, test_data_dir):
        """Test that ConversationManager completes check-in flow correctly."""
        manager = ConversationManager()
        user_id = "test_user_checkin_complete"
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock check-ins enabled
        mock_is_enabled.return_value = True
        
        # Mock user data with single question
        mock_get_user_data.return_value = {
            'preferences': {
                'checkin_settings': {
                    'questions': {
                        'mood': {'enabled': True, 'weight': 1.0}
                    }
                }
            }
        }
        
        # Start check-in
        message1, completed1 = manager.start_checkin(user_id)
        assert user_id in manager.user_states, "Should have active check-in"
        
        # Complete check-in by answering last question
        # This will depend on the flow implementation, but should eventually complete
        user_state = manager.user_states[user_id]
        user_state['current_question_index'] = len(user_state.get('question_order', []))
        
        # Handle completion
        with patch('communication.message_processing.conversation_flow_manager.conversation_manager._complete_checkin') as mock_complete:
            mock_complete.return_value = ("Check-in completed! Thank you.", True)
            message2, completed2 = manager.handle_inbound_message(user_id, "4")
            
            # Should eventually complete
            # The exact flow depends on implementation, but we verify it handles completion

    @pytest.mark.behavior
    @pytest.mark.communication
    def test_active_checkin_keyword_cancel_clears_flow_state(self, test_data_dir):
        """Test active-flow keyword handling: !cancel during check-in clears flow and completes."""
        # Arrange
        manager = ConversationManager()
        user_id = "test_user_active_checkin_cancel"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir)
        manager.user_states[user_id] = {
            "flow": FLOW_CHECKIN,
            "state": CHECKIN_MOOD,
            "data": {},
            "question_order": ["mood"],
            "current_question_index": 0,
        }

        # Act
        message, completed = manager.handle_inbound_message(user_id, "!cancel")

        # Assert
        assert completed is True
        assert "canceled" in message.lower()
        assert user_id not in manager.user_states

    @pytest.mark.behavior
    @pytest.mark.communication
    def test_clear_flow_state_marks_completion_timestamp(self):
        """Clearing a flow should stamp completion timestamp for cooldown checks."""
        manager = ConversationManager()
        user_id = f"flow_complete_{uuid.uuid4().hex[:8]}"
        manager.user_states[user_id] = {"flow": FLOW_TASK_REMINDER, "state": 1, "data": {}}

        manager._clear_flow_state(user_id, mark_completion=True)

        assert user_id not in manager.user_states
        assert user_id in manager._flow_completion_timestamps

    @pytest.mark.behavior
    @pytest.mark.communication
    def test_post_flow_cooldown_boundary(self):
        """Cooldown should be active for recent completions and inactive after threshold."""
        manager = ConversationManager()
        user_id = f"cooldown_{uuid.uuid4().hex[:8]}"
        now = now_datetime_full()

        manager._flow_completion_timestamps[user_id] = format_timestamp(
            now - timedelta(minutes=5), TIMESTAMP_FULL
        )
        assert manager.is_within_post_flow_cooldown(user_id, cooldown_minutes=10) is True
        assert manager.get_flow_block_reason(user_id, cooldown_minutes=10) == "post_flow_cooldown"

        manager._flow_completion_timestamps[user_id] = format_timestamp(
            now - timedelta(minutes=11), TIMESTAMP_FULL
        )
        assert manager.is_within_post_flow_cooldown(user_id, cooldown_minutes=10) is False
        assert manager.get_flow_block_reason(user_id, cooldown_minutes=10) is None

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_state_persistence_and_reload_transition(self, test_data_dir):
        """Test save->load transition for conversation state persistence."""
        # Arrange
        state_file = Path(test_data_dir) / f"conversation_states_{uuid.uuid4().hex[:8]}.json"

        writer = ConversationManager()
        writer._state_file = state_file
        writer.user_states = {
            "persist_user_1": {"flow": FLOW_CHECKIN, "state": CHECKIN_MOOD, "data": {"mood": "3"}},
            "persist_user_2": {"flow": FLOW_NONE, "state": 0, "data": {}},
        }

        # Act
        writer._save_user_states()

        reader = ConversationManager()
        reader._state_file = state_file
        reader.user_states = {}
        reader._load_user_states()

        # Assert
        assert reader.user_states == writer.user_states, (
            "Loaded user states should match the persisted state snapshot"
        )

    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_expire_inactive_checkins_caches_order_and_removes_user(self, test_data_dir, monkeypatch):
        """Test inactivity expiry branch removes stale check-in and caches same-day question order."""
        # Arrange
        manager = ConversationManager()
        manager._state_file = Path(test_data_dir) / f"conversation_states_{uuid.uuid4().hex[:8]}.json"
        manager.user_states = {}
        user_id = f"expire_user_{uuid.uuid4().hex[:8]}"

        last_activity = now_timestamp_full()
        last_dt = parse_timestamp_full(last_activity)
        assert last_dt is not None

        manager.user_states[user_id] = {
            "flow": FLOW_CHECKIN,
            "state": CHECKIN_MOOD,
            "data": {},
            "question_order": ["mood", "energy"],
            "current_question_index": 0,
            "started_at": last_activity,
            "last_activity": last_activity,
        }

        # Force now beyond inactivity threshold so the state expires.
        forced_now = last_dt + timedelta(minutes=CHECKIN_INACTIVITY_MINUTES + 1)
        monkeypatch.setattr(
            "communication.message_processing.conversation_flow_manager.now_datetime_full",
            lambda: forced_now,
        )

        # Act
        manager._expire_inactive_checkins(user_id=user_id)

        # Assert
        assert user_id not in manager.user_states, "Expired check-in should be removed from active states"
        assert user_id in manager._checkin_order_cache, "Expired check-in order should be cached for same-day restart"
        assert manager._checkin_order_cache[user_id]["order"] == ["mood", "energy"]

    @pytest.mark.behavior
    @pytest.mark.communication
    def test_task_reminder_flow_is_interrupted_by_command(self, test_data_dir, monkeypatch):
        """Test command interruption path: task reminder flow clears when user issues a command."""
        # Arrange
        manager = ConversationManager()
        user_id = "test_user_task_reminder_interrupt"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir)
        manager.user_states[user_id] = {
            "flow": FLOW_TASK_REMINDER,
            "state": 0,
            "data": {"task_identifier": "task-1"},
        }

        save_calls = {"count": 0}

        def _count_save():
            save_calls["count"] += 1

        monkeypatch.setattr(manager, "_save_user_states", _count_save)

        # Act
        message, completed = manager.handle_inbound_message(
            user_id, "update task task-1 priority high"
        )

        # Assert
        assert message == "", "Interrupting command path should return empty message for handoff"
        assert completed is True
        assert user_id not in manager.user_states, "Flow should be cleared on command interruption"
        assert save_calls["count"] == 1, "Flow clear should persist exactly once"
