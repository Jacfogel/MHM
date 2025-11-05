"""
Profile Handler Behavior Tests

Tests for communication/command_handlers/profile_handler.py focusing on real behavior and side effects.
These tests verify that the profile handler actually works and produces expected
side effects rather than just returning values.
"""

import pytest
from unittest.mock import patch, MagicMock

# Import the modules we're testing
from communication.command_handlers.profile_handler import ProfileHandler
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from tests.test_utilities import TestUserFactory


class TestProfileHandlerBehavior:
    """Test profile handler real behavior and side effects."""
    
    def _create_test_user(self, user_id: str, enable_checkins: bool = True, test_data_dir: str = None) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(user_id, enable_checkins=enable_checkins, test_data_dir=test_data_dir)
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    def test_profile_handler_can_handle_intents(self):
        """Test that ProfileHandler can handle all expected intents."""
        handler = ProfileHandler()
        
        expected_intents = ['show_profile', 'update_profile', 'profile_stats']
        for intent in expected_intents:
            assert handler.can_handle(intent), f"ProfileHandler should handle {intent}"
        
        # Test that it doesn't handle other intents
        assert not handler.can_handle('create_task'), "ProfileHandler should not handle create_task"
        assert not handler.can_handle('start_checkin'), "ProfileHandler should not handle start_checkin"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    def test_profile_handler_get_help(self):
        """Test that ProfileHandler returns help text."""
        handler = ProfileHandler()
        help_text = handler.get_help()
        
        assert isinstance(help_text, str), "Should return help text as string"
        assert len(help_text) > 0, "Help text should not be empty"
        assert "profile" in help_text.lower(), "Help text should mention profile"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    def test_profile_handler_get_examples(self):
        """Test that ProfileHandler returns example commands."""
        handler = ProfileHandler()
        examples = handler.get_examples()
        
        assert isinstance(examples, list), "Should return examples as list"
        assert len(examples) > 0, "Should have at least one example"
        assert all(isinstance(ex, str) for ex in examples), "All examples should be strings"
        assert any("profile" in ex.lower() for ex in examples), "Should include profile examples"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    def test_profile_handler_unknown_intent(self):
        """Test that ProfileHandler handles unknown intents gracefully."""
        handler = ProfileHandler()
        parsed_command = ParsedCommand(
            intent="unknown_intent",
            entities={},
            confidence=0.5,
            original_message="unknown command"
        )
        
        response = handler.handle("test_user", parsed_command)
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "don't understand" in response.message.lower() or "try" in response.message.lower(), "Should indicate unknown command"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    @pytest.mark.file_io
    @patch('communication.command_handlers.profile_handler.get_user_data')
    def test_profile_handler_show_profile_success(self, mock_get_user_data, test_data_dir):
        """Test that ProfileHandler shows profile successfully."""
        handler = ProfileHandler()
        user_id = "test_user_profile_show"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        mock_get_user_data.side_effect = [
            {'account': {'email': 'test@example.com', 'account_status': 'active', 'features': {'checkins': 'enabled', 'task_management': 'enabled'}}},
            {'context': {'preferred_name': 'Test User', 'gender_identity': ['Non-binary'], 'interests': ['Reading'], 'goals': ['Learn Python']}},
            {'preferences': {}}
        ]
        
        parsed_command = ParsedCommand(
            intent="show_profile",
            entities={},
            confidence=0.9,
            original_message="show profile"
        )
        
        response = handler.handle(user_id, parsed_command)
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "profile" in response.message.lower(), "Should mention profile"
        assert "Test User" in response.message or "test@example.com" in response.message, "Should include user data"
        assert response.rich_data is not None, "Should include rich data for Discord"
        assert mock_get_user_data.call_count == 3, "Should load account, context, and preferences"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    @pytest.mark.file_io
    @patch('communication.command_handlers.profile_handler.get_user_data')
    def test_profile_handler_show_profile_empty(self, mock_get_user_data, test_data_dir):
        """Test that ProfileHandler handles empty profile gracefully."""
        handler = ProfileHandler()
        user_id = "test_user_profile_empty"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        mock_get_user_data.side_effect = [
            {'account': {}},
            {'context': {}},
            {'preferences': {}}
        ]
        
        parsed_command = ParsedCommand(
            intent="show_profile",
            entities={},
            confidence=0.9,
            original_message="show profile"
        )
        
        response = handler.handle(user_id, parsed_command)
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "profile" in response.message.lower(), "Should mention profile"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    @pytest.mark.file_io
    @patch('communication.command_handlers.profile_handler.save_user_data')
    @patch('communication.command_handlers.profile_handler.get_user_data')
    def test_profile_handler_update_profile_name(self, mock_get_user_data, mock_save_user_data, test_data_dir):
        """Test that ProfileHandler updates name successfully."""
        handler = ProfileHandler()
        user_id = "test_user_profile_update_name"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        mock_get_user_data.return_value = {'context': {'preferred_name': 'Old Name'}}
        mock_save_user_data.return_value = True
        
        parsed_command = ParsedCommand(
            intent="update_profile",
            entities={'name': 'New Name'},
            confidence=0.9,
            original_message="update name 'New Name'"
        )
        
        response = handler.handle(user_id, parsed_command)
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "updated" in response.message.lower(), "Should indicate profile was updated"
        assert "name" in response.message.lower(), "Should mention name update"
        
        # Verify actual system changes: Check that save_user_data was called with correct data
        mock_save_user_data.assert_called_once()
        call_args = mock_save_user_data.call_args
        saved_user_id = call_args[0][0] if call_args[0] else call_args[1].get('user_id')
        saved_data_type = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get('data_type')
        saved_data = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get('data')
        
        assert saved_user_id == user_id, "Should save data for correct user"
        assert saved_data_type == 'context', "Should save context data"
        assert saved_data is not None, "Should have data to save"
        assert saved_data.get('preferred_name') == 'New Name', "Should update preferred_name to 'New Name'"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    @pytest.mark.file_io
    @patch('communication.command_handlers.profile_handler.save_user_data')
    @patch('communication.command_handlers.profile_handler.get_user_data')
    def test_profile_handler_update_profile_gender_identity(self, mock_get_user_data, mock_save_user_data, test_data_dir):
        """Test that ProfileHandler updates gender identity successfully."""
        handler = ProfileHandler()
        user_id = "test_user_profile_update_gender"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        mock_get_user_data.return_value = {'context': {}}
        mock_save_user_data.return_value = True
        
        parsed_command = ParsedCommand(
            intent="update_profile",
            entities={'gender_identity': 'Non-binary, Woman'},
            confidence=0.9,
            original_message="update gender_identity 'Non-binary, Woman'"
        )
        
        response = handler.handle(user_id, parsed_command)
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "updated" in response.message.lower(), "Should indicate profile was updated"
        assert "gender" in response.message.lower() or "identity" in response.message.lower(), "Should mention gender identity update"
        
        # Verify actual system changes: Check that gender_identity is correctly parsed and saved
        mock_save_user_data.assert_called_once()
        call_args = mock_save_user_data.call_args
        saved_data = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get('data')
        assert saved_data is not None, "Should have data to save"
        assert 'gender_identity' in saved_data, "Should include gender_identity in saved data"
        assert isinstance(saved_data['gender_identity'], list), "Should convert gender_identity to list"
        assert 'Non-binary' in saved_data['gender_identity'], "Should include 'Non-binary' in gender_identity"
        assert 'Woman' in saved_data['gender_identity'], "Should include 'Woman' in gender_identity"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    @pytest.mark.file_io
    @patch('communication.command_handlers.profile_handler.save_user_data')
    @patch('communication.command_handlers.profile_handler.get_user_data')
    def test_profile_handler_update_profile_health_conditions(self, mock_get_user_data, mock_save_user_data, test_data_dir):
        """Test that ProfileHandler updates health conditions successfully."""
        handler = ProfileHandler()
        user_id = "test_user_profile_update_health"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        mock_get_user_data.return_value = {'context': {'custom_fields': {}}}
        mock_save_user_data.return_value = True
        
        parsed_command = ParsedCommand(
            intent="update_profile",
            entities={'health_conditions': 'Depression, Anxiety'},
            confidence=0.9,
            original_message="add health_conditions 'Depression, Anxiety'"
        )
        
        response = handler.handle(user_id, parsed_command)
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "updated" in response.message.lower(), "Should indicate profile was updated"
        assert "health" in response.message.lower() or "condition" in response.message.lower(), "Should mention health conditions update"
        
        # Verify actual system changes: Check that health_conditions are correctly parsed and saved
        mock_save_user_data.assert_called_once()
        call_args = mock_save_user_data.call_args
        saved_data = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get('data')
        assert saved_data is not None, "Should have data to save"
        assert 'custom_fields' in saved_data, "Should include custom_fields in saved data"
        assert 'health_conditions' in saved_data['custom_fields'], "Should include health_conditions in custom_fields"
        assert isinstance(saved_data['custom_fields']['health_conditions'], list), "Should convert health_conditions to list"
        assert 'Depression' in saved_data['custom_fields']['health_conditions'], "Should include 'Depression' in health_conditions"
        assert 'Anxiety' in saved_data['custom_fields']['health_conditions'], "Should include 'Anxiety' in health_conditions"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    @pytest.mark.file_io
    @patch('communication.command_handlers.profile_handler.save_user_data')
    @patch('communication.command_handlers.profile_handler.get_user_data')
    def test_profile_handler_update_profile_medications(self, mock_get_user_data, mock_save_user_data, test_data_dir):
        """Test that ProfileHandler updates medications successfully."""
        handler = ProfileHandler()
        user_id = "test_user_profile_update_meds"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        mock_get_user_data.return_value = {'context': {'custom_fields': {}}}
        mock_save_user_data.return_value = True
        
        parsed_command = ParsedCommand(
            intent="update_profile",
            entities={'medications': 'Sertraline, 50mg'},
            confidence=0.9,
            original_message="add medications 'Sertraline, 50mg'"
        )
        
        response = handler.handle(user_id, parsed_command)
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "updated" in response.message.lower(), "Should indicate profile was updated"
        assert "medication" in response.message.lower(), "Should mention medications update"
        
        # Verify actual system changes: Check that medications are correctly parsed and saved
        mock_save_user_data.assert_called_once()
        call_args = mock_save_user_data.call_args
        saved_data = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get('data')
        assert saved_data is not None, "Should have data to save"
        assert 'custom_fields' in saved_data, "Should include custom_fields in saved data"
        assert 'medications_treatments' in saved_data['custom_fields'], "Should include medications_treatments in custom_fields"
        assert isinstance(saved_data['custom_fields']['medications_treatments'], list), "Should convert medications to list"
        assert 'Sertraline' in saved_data['custom_fields']['medications_treatments'], "Should include 'Sertraline' in medications"
        assert '50mg' in saved_data['custom_fields']['medications_treatments'], "Should include '50mg' in medications"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    @pytest.mark.file_io
    @patch('communication.command_handlers.profile_handler.save_user_data')
    @patch('communication.command_handlers.profile_handler.get_user_data')
    def test_profile_handler_update_profile_allergies(self, mock_get_user_data, mock_save_user_data, test_data_dir):
        """Test that ProfileHandler updates allergies successfully."""
        handler = ProfileHandler()
        user_id = "test_user_profile_update_allergies"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        mock_get_user_data.return_value = {'context': {'custom_fields': {}}}
        mock_save_user_data.return_value = True
        
        parsed_command = ParsedCommand(
            intent="update_profile",
            entities={'allergies': 'Peanuts, Shellfish'},
            confidence=0.9,
            original_message="add allergies 'Peanuts, Shellfish'"
        )
        
        response = handler.handle(user_id, parsed_command)
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "updated" in response.message.lower(), "Should indicate profile was updated"
        assert "allerg" in response.message.lower(), "Should mention allergies update"
        
        # Verify actual system changes: Check that allergies are correctly parsed and saved
        mock_save_user_data.assert_called_once()
        call_args = mock_save_user_data.call_args
        saved_data = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get('data')
        assert saved_data is not None, "Should have data to save"
        assert 'custom_fields' in saved_data, "Should include custom_fields in saved data"
        assert 'allergies_sensitivities' in saved_data['custom_fields'], "Should include allergies_sensitivities in custom_fields"
        assert isinstance(saved_data['custom_fields']['allergies_sensitivities'], list), "Should convert allergies to list"
        assert 'Peanuts' in saved_data['custom_fields']['allergies_sensitivities'], "Should include 'Peanuts' in allergies"
        assert 'Shellfish' in saved_data['custom_fields']['allergies_sensitivities'], "Should include 'Shellfish' in allergies"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    @pytest.mark.file_io
    @patch('communication.command_handlers.profile_handler.save_user_data')
    @patch('communication.command_handlers.profile_handler.get_user_data')
    def test_profile_handler_update_profile_interests(self, mock_get_user_data, mock_save_user_data, test_data_dir):
        """Test that ProfileHandler updates interests successfully."""
        handler = ProfileHandler()
        user_id = "test_user_profile_update_interests"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        mock_get_user_data.return_value = {'context': {}}
        mock_save_user_data.return_value = True
        
        parsed_command = ParsedCommand(
            intent="update_profile",
            entities={'interests': 'Reading, Gaming, Hiking'},
            confidence=0.9,
            original_message="update interests 'Reading, Gaming, Hiking'"
        )
        
        response = handler.handle(user_id, parsed_command)
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "updated" in response.message.lower(), "Should indicate profile was updated"
        assert "interest" in response.message.lower(), "Should mention interests update"
        
        # Verify actual system changes: Check that interests are correctly parsed and saved
        mock_save_user_data.assert_called_once()
        call_args = mock_save_user_data.call_args
        saved_data = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get('data')
        assert saved_data is not None, "Should have data to save"
        assert 'interests' in saved_data, "Should include interests in saved data"
        assert isinstance(saved_data['interests'], list), "Should convert interests to list"
        assert 'Reading' in saved_data['interests'], "Should include 'Reading' in interests"
        assert 'Gaming' in saved_data['interests'], "Should include 'Gaming' in interests"
        assert 'Hiking' in saved_data['interests'], "Should include 'Hiking' in interests"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    @pytest.mark.file_io
    @patch('communication.command_handlers.profile_handler.save_user_data')
    @patch('communication.command_handlers.profile_handler.get_user_data')
    def test_profile_handler_update_profile_goals(self, mock_get_user_data, mock_save_user_data, test_data_dir):
        """Test that ProfileHandler updates goals successfully."""
        handler = ProfileHandler()
        user_id = "test_user_profile_update_goals"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        mock_get_user_data.return_value = {'context': {}}
        mock_save_user_data.return_value = True
        
        parsed_command = ParsedCommand(
            intent="update_profile",
            entities={'goals': 'Learn Python, Build projects'},
            confidence=0.9,
            original_message="add goals 'Learn Python, Build projects'"
        )
        
        response = handler.handle(user_id, parsed_command)
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "updated" in response.message.lower(), "Should indicate profile was updated"
        assert "goal" in response.message.lower(), "Should mention goals update"
        
        # Verify actual system changes: Check that goals are correctly parsed and saved
        mock_save_user_data.assert_called_once()
        call_args = mock_save_user_data.call_args
        saved_data = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get('data')
        assert saved_data is not None, "Should have data to save"
        assert 'goals' in saved_data, "Should include goals in saved data"
        assert isinstance(saved_data['goals'], list), "Should convert goals to list"
        assert 'Learn Python' in saved_data['goals'], "Should include 'Learn Python' in goals"
        assert 'Build projects' in saved_data['goals'], "Should include 'Build projects' in goals"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    @pytest.mark.file_io
    @patch('communication.command_handlers.profile_handler.save_user_data')
    @patch('communication.command_handlers.profile_handler.get_user_data')
    def test_profile_handler_update_profile_notes_for_ai(self, mock_get_user_data, mock_save_user_data, test_data_dir):
        """Test that ProfileHandler updates notes for AI successfully."""
        handler = ProfileHandler()
        user_id = "test_user_profile_update_notes"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        mock_get_user_data.return_value = {'context': {}}
        mock_save_user_data.return_value = True
        
        parsed_command = ParsedCommand(
            intent="update_profile",
            entities={'notes_for_ai': 'I prefer gentle reminders'},
            confidence=0.9,
            original_message="update notes_for_ai 'I prefer gentle reminders'"
        )
        
        response = handler.handle(user_id, parsed_command)
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "updated" in response.message.lower(), "Should indicate profile was updated"
        assert "note" in response.message.lower() or "ai" in response.message.lower(), "Should mention notes for AI update"
        
        # Verify actual system changes: Check that notes_for_ai are correctly saved
        mock_save_user_data.assert_called_once()
        call_args = mock_save_user_data.call_args
        saved_data = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get('data')
        assert saved_data is not None, "Should have data to save"
        assert 'notes_for_ai' in saved_data, "Should include notes_for_ai in saved data"
        assert isinstance(saved_data['notes_for_ai'], list), "Should convert notes_for_ai to list"
        assert saved_data['notes_for_ai'][0] == 'I prefer gentle reminders', "Should include the note text"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    def test_profile_handler_update_profile_missing_entities(self):
        """Test that ProfileHandler asks for update fields when missing."""
        handler = ProfileHandler()
        parsed_command = ParsedCommand(
            intent="update_profile",
            entities={},
            confidence=0.9,
            original_message="update profile"
        )
        
        response = handler.handle("test_user", parsed_command)
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert not response.completed, "Should ask for update fields"
        assert "what" in response.message.lower() or "update" in response.message.lower(), "Should ask what to update"
        assert "field" in response.message.lower() or "available" in response.message.lower(), "Should list available fields"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    @pytest.mark.file_io
    @patch('communication.command_handlers.profile_handler.save_user_data')
    @patch('communication.command_handlers.profile_handler.get_user_data')
    def test_profile_handler_update_profile_no_updates(self, mock_get_user_data, mock_save_user_data, test_data_dir):
        """Test that ProfileHandler handles no valid updates."""
        handler = ProfileHandler()
        user_id = "test_user_profile_no_updates"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        mock_get_user_data.return_value = {'context': {}}
        
        parsed_command = ParsedCommand(
            intent="update_profile",
            entities={'invalid_field': 'invalid_value'},
            confidence=0.9,
            original_message="update profile invalid_field"
        )
        
        response = handler.handle(user_id, parsed_command)
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert not response.completed, "Should indicate no valid updates"
        assert "no" in response.message.lower() or "valid" in response.message.lower() or "specify" in response.message.lower(), "Should indicate no valid updates"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    @pytest.mark.file_io
    @patch('communication.command_handlers.profile_handler.get_recent_checkins')
    @patch('communication.command_handlers.profile_handler.get_user_task_stats')
    def test_profile_handler_profile_stats_success(self, mock_get_task_stats, mock_get_checkins, test_data_dir):
        """Test that ProfileHandler shows profile statistics successfully."""
        handler = ProfileHandler()
        user_id = "test_user_profile_stats"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        mock_get_task_stats.return_value = {
            'active_count': 5,
            'completed_count': 10,
            'completion_rate': 66.7
        }
        mock_get_checkins.return_value = [
            {'timestamp': '2024-01-01', 'response': 'Good'},
            {'timestamp': '2024-01-02', 'response': 'Fine'}
        ]
        
        parsed_command = ParsedCommand(
            intent="profile_stats",
            entities={},
            confidence=0.9,
            original_message="profile stats"
        )
        
        response = handler.handle(user_id, parsed_command)
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "statistic" in response.message.lower() or "stats" in response.message.lower(), "Should mention statistics"
        assert "task" in response.message.lower() or "check" in response.message.lower(), "Should include task or check-in stats"
        mock_get_task_stats.assert_called_once_with(user_id)
        mock_get_checkins.assert_called_once_with(user_id, limit=30)
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    @pytest.mark.file_io
    @patch('communication.command_handlers.profile_handler.get_recent_checkins')
    @patch('communication.command_handlers.profile_handler.get_user_task_stats')
    def test_profile_handler_profile_stats_no_data(self, mock_get_task_stats, mock_get_checkins, test_data_dir):
        """Test that ProfileHandler handles profile statistics with no data."""
        handler = ProfileHandler()
        user_id = "test_user_profile_stats_empty"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        mock_get_task_stats.return_value = {
            'active_count': 0,
            'completed_count': 0,
            'completion_rate': 0
        }
        mock_get_checkins.return_value = []
        
        parsed_command = ParsedCommand(
            intent="profile_stats",
            entities={},
            confidence=0.9,
            original_message="profile stats"
        )
        
        response = handler.handle(user_id, parsed_command)
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "statistic" in response.message.lower() or "stats" in response.message.lower(), "Should mention statistics"
        # Should still show stats even if zero
        assert "0" in response.message or "task" in response.message.lower() or "check" in response.message.lower(), "Should include stats"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    @pytest.mark.file_io
    @patch('communication.command_handlers.profile_handler.save_user_data')
    @patch('communication.command_handlers.profile_handler.get_user_data')
    def test_profile_handler_update_profile_save_failure(self, mock_get_user_data, mock_save_user_data, test_data_dir):
        """Test that ProfileHandler handles save failure gracefully."""
        handler = ProfileHandler()
        user_id = "test_user_profile_save_fail"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        mock_get_user_data.return_value = {'context': {}}
        mock_save_user_data.return_value = False
        
        parsed_command = ParsedCommand(
            intent="update_profile",
            entities={'name': 'Test Name'},
            confidence=0.9,
            original_message="update name 'Test Name'"
        )
        
        response = handler.handle(user_id, parsed_command)
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "fail" in response.message.lower() or "error" in response.message.lower(), "Should indicate failure"
        mock_save_user_data.assert_called_once()
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    def test_profile_handler_format_profile_text(self):
        """Test that ProfileHandler formats profile text correctly."""
        handler = ProfileHandler()
        
        account_data = {
            'email': 'test@example.com',
            'account_status': 'active',
            'features': {'checkins': 'enabled', 'task_management': 'enabled'}
        }
        context_data = {
            'preferred_name': 'Test User',
            'gender_identity': ['Non-binary'],
            'interests': ['Reading', 'Gaming'],
            'goals': ['Learn Python'],
            'custom_fields': {
                'health_conditions': ['Depression'],
                'medications_treatments': ['Sertraline'],
                'allergies_sensitivities': ['Peanuts']
            }
        }
        preferences_data = {}
        
        result = handler._format_profile_text(account_data, context_data, preferences_data)
        assert isinstance(result, str), "Should return formatted text as string"
        assert "Test User" in result, "Should include name"
        assert "test@example.com" in result, "Should include email"
        assert "Reading" in result or "Gaming" in result, "Should include interests"
        assert "Learn Python" in result, "Should include goals"
        assert "Depression" in result or "Sertraline" in result or "Peanuts" in result, "Should include health info"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.user_management
    def test_profile_handler_format_profile_text_empty(self):
        """Test that ProfileHandler formats empty profile text gracefully."""
        handler = ProfileHandler()
        
        result = handler._format_profile_text({}, {}, {})
        assert isinstance(result, str), "Should return formatted text as string"
        assert "profile" in result.lower(), "Should mention profile"
        assert len(result) > 0, "Should return some text even for empty profile"

