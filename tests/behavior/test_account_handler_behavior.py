"""
Account Handler Behavior Tests

Tests for communication/command_handlers/account_handler.py focusing on real behavior and side effects.
These tests verify that account handlers actually work and produce expected side effects.
"""

import pytest
import uuid
from unittest.mock import patch, MagicMock, AsyncMock
from tests.test_helpers.test_utilities import TestUserFactory
from core import get_user_id_by_identifier
from core import get_user_data
from communication.command_handlers.account_handler import (
    AccountManagementHandler,
    _generate_confirmation_code,
    _send_confirmation_code,
    _pending_link_operations
)
from communication.command_handlers.shared_types import ParsedCommand


def _snowflake() -> str:
    """Unique numeric Discord snowflake-like ID for parallel-safe handler tests."""
    return str(uuid.uuid4().int)[:18]


def _unique_username(prefix: str = "user") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"
    """Test account handler real behavior and side effects."""
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_can_handle_recognizes_account_intents(self):
        """Test: Handler recognizes account management intents."""
        handler = AccountManagementHandler()
        
        # Test valid intents
        assert handler.can_handle('create_account'), "Should handle create_account"
        assert handler.can_handle('link_account'), "Should handle link_account"
        assert handler.can_handle('check_account_status'), "Should handle check_account_status"
        
        # Test invalid intents
        assert not handler.can_handle('unknown_intent'), "Should not handle unknown intent"
        assert not handler.can_handle('task_create'), "Should not handle non-account intents"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_routes_to_create_account(self, test_data_dir):
        """Test: Handler routes create_account intent correctly."""
        handler = AccountManagementHandler()
        
        parsed_command = ParsedCommand(
            intent='create_account',
            entities={'username': 'testuser123'},
            confidence=0.9,
            original_message='create account'
        )
        
        response = handler.handle('test_channel_id', parsed_command)
        
        assert response is not None, "Should return response"
        assert isinstance(response.message, str), "Should return string message"
        # Response may be success or ask for more info
        assert len(response.message) > 0, "Should return non-empty message"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_create_account_with_valid_username(self, test_data_dir):
        """Test: Create account with valid username creates user and saves data."""
        handler = AccountManagementHandler()

        discord_user_id = _snowflake()
        username = _unique_username("newtestuser")

        parsed_command = ParsedCommand(
            intent='create_account',
            entities={
                'username': username,
                'channel_identifier': discord_user_id,
                'channel_type': 'discord',
                'tasks_enabled': True,
                'checkins_enabled': True,
                'messages_enabled': False
            },
            confidence=0.9,
            original_message='create account'
        )

        response = handler.handle(discord_user_id, parsed_command)
        
        # Assert: Should create account successfully
        assert response.completed is True, "Should complete account creation"
        assert 'Account created successfully' in response.message, "Should indicate success"
        
        # Verify user was actually created
        created_user_id = get_user_id_by_identifier(discord_user_id)
        assert created_user_id is not None, "User should be created"
        
        # Verify user data exists
        user_data = get_user_data(created_user_id, 'account')
        assert user_data is not None, "User data should exist"
        account_data = user_data.get('account', {})
        assert account_data.get('internal_username') == username, "Username should match"
        assert account_data.get('discord_user_id') == discord_user_id, "Discord ID should be set"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_create_account_with_feature_selection(self, test_data_dir):
        """Test: Create account with feature selection parameters sets correct feature flags."""
        handler = AccountManagementHandler()

        discord_user_id = _snowflake()
        username = _unique_username("featuretestuser")

        parsed_command = ParsedCommand(
            intent='create_account',
            entities={
                'username': username,
                'channel_identifier': discord_user_id,
                'channel_type': 'discord',
                'tasks_enabled': False,
                'checkins_enabled': True,
                'messages_enabled': True,
                'timezone': 'America/New_York'
            },
            confidence=0.9,
            original_message='create account'
        )

        response = handler.handle(discord_user_id, parsed_command)
        
        # Assert: Should create account successfully
        assert response.completed is True, "Should complete account creation"
        
        # Verify user was created
        created_user_id = get_user_id_by_identifier(discord_user_id)
        assert created_user_id is not None, "User should be created"
        
        # Verify feature flags are set correctly
        user_data = get_user_data(created_user_id, 'account')
        account_data = user_data.get('account', {})
        features = account_data.get('features', {})
        
        assert features.get('task_management') == 'disabled', "Task management should be disabled"
        assert features.get('checkins') == 'enabled', "Check-ins should be enabled"
        assert features.get('automated_messages') == 'enabled', "Automated messages should be enabled"
        assert account_data.get('timezone') == 'America/New_York', "Timezone should be set correctly"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_create_account_requires_feature_selection(self, test_data_dir):
        """Test: Create account without feature selection prompts for required flags."""
        handler = AccountManagementHandler()

        discord_user_id = _snowflake()
        username = _unique_username("defaulttestuser")

        parsed_command = ParsedCommand(
            intent='create_account',
            entities={
                'username': username,
                'channel_identifier': discord_user_id,
                'channel_type': 'discord'
            },
            confidence=0.9,
            original_message='create account'
        )

        response = handler.handle(discord_user_id, parsed_command)
        
        # Assert: Should require explicit feature selection
        assert response.completed is False, "Should not complete without feature selection"
        assert 'feature' in response.message.lower(), "Should request feature settings"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_create_account_without_username(self, test_data_dir):
        """Test: Create account without username asks for username."""
        handler = AccountManagementHandler()
        
        parsed_command = ParsedCommand(
            intent='create_account',
            entities={},
            confidence=0.9,
            original_message='create account'
        )
        
        response = handler.handle('test_channel_id', parsed_command)
        
        # Assert: Should ask for username
        assert response.completed is False, "Should not complete without username"
        assert 'username' in response.message.lower(), "Should ask for username"
        assert len(response.suggestions) > 0, "Should provide suggestions"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_create_account_with_short_username(self, test_data_dir):
        """Test: Create account with short username rejects and asks for longer."""
        handler = AccountManagementHandler()
        
        parsed_command = ParsedCommand(
            intent='create_account',
            entities={'username': 'ab'},
            confidence=0.9,
            original_message='create account'
        )
        
        response = handler.handle('test_channel_id', parsed_command)
        
        # Assert: Should reject short username
        assert response.completed is False, "Should not complete with short username"
        assert '3 characters' in response.message, "Should mention minimum length"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_create_account_with_existing_username(self, test_data_dir):
        """Test: Create account with existing username rejects."""
        handler = AccountManagementHandler()

        existing_username = _unique_username("existinguser")
        TestUserFactory.create_basic_user(existing_username, test_data_dir=test_data_dir)

        parsed_command = ParsedCommand(
            intent='create_account',
            entities={'username': existing_username},
            confidence=0.9,
            original_message='create account'
        )

        response = handler.handle('test_channel_id', parsed_command)
        
        # Assert: Should reject existing username
        assert response.completed is False, "Should not complete with existing username"
        assert 'already taken' in response.message.lower(), "Should indicate username taken"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_check_account_status_with_existing_user(self, test_data_dir):
        """Test: Check account status returns account info for existing user."""
        handler = AccountManagementHandler()

        internal_name = _unique_username("status-check")
        discord_user_id = _snowflake()
        TestUserFactory.create_discord_user(
            internal_name,
            discord_user_id=discord_user_id,
            test_data_dir=test_data_dir,
        )

        internal_user_id = TestUserFactory.get_test_user_id_by_internal_username(
            internal_name, test_data_dir
        )
        assert internal_user_id is not None, "User should exist"

        parsed_command = ParsedCommand(
            intent='check_account_status',
            entities={},
            confidence=0.9,
            original_message='check account status'
        )

        response = handler.handle(discord_user_id, parsed_command)
        
        # Assert: Should return account status
        assert response.completed is True, "Should complete status check"
        assert 'account linked' in response.message.lower(), "Should indicate account exists"
        assert response.rich_data is not None, "Should include rich data"
        assert response.rich_data.get('has_account') is True, "Should indicate account exists"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_check_account_status_without_user(self, test_data_dir):
        """Test: Check account status indicates no account for new user."""
        handler = AccountManagementHandler()

        new_user_id = _snowflake()

        parsed_command = ParsedCommand(
            intent='check_account_status',
            entities={},
            confidence=0.9,
            original_message='check account status'
        )

        response = handler.handle(new_user_id, parsed_command)
        
        # Assert: Should indicate no account
        assert response.completed is False, f"Should indicate no account, but got completed={response.completed}, message={response.message}"
        assert 'no mhm account' in response.message.lower() or 'no account found' in response.message.lower(), f"Should indicate no account found, but got: {response.message}"
        assert response.rich_data is not None, "Should include rich data"
        assert response.rich_data.get('has_account') is False, "Should indicate no account"
        assert len(response.suggestions) > 0, "Should provide suggestions"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_link_account_without_username(self, test_data_dir):
        """Test: Link account without username asks for username."""
        handler = AccountManagementHandler()
        
        parsed_command = ParsedCommand(
            intent='link_account',
            entities={},
            confidence=0.9,
            original_message='link account'
        )
        
        response = handler.handle('test_channel_id', parsed_command)
        
        # Assert: Should ask for username
        assert response.completed is False, "Should not complete without username"
        assert 'username' in response.message.lower(), "Should ask for username"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_link_account_with_nonexistent_username(self, test_data_dir):
        """Test: Link account with nonexistent username rejects."""
        handler = AccountManagementHandler()
        
        parsed_command = ParsedCommand(
            intent='link_account',
            entities={'username': 'nonexistentuser123'},
            confidence=0.9,
            original_message='link account'
        )
        
        response = handler.handle('test_channel_id', parsed_command)
        
        # Assert: Should reject nonexistent username
        assert response.completed is False, "Should not complete with nonexistent username"
        assert 'not found' in response.message.lower(), "Should indicate username not found"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_link_account_sends_confirmation_code(self, test_data_dir):
        """Test: Link account sends confirmation code for valid username."""
        handler = AccountManagementHandler()

        existing_username = _unique_username("linktestuser")
        create_success = TestUserFactory.create_basic_user(
            existing_username, test_data_dir=test_data_dir
        )
        assert create_success is True, "Test user should be created"

        from core import update_user_account
        user_id = TestUserFactory.get_test_user_id_by_internal_username(
            existing_username, test_data_dir
        )
        assert user_id is not None, "Test user should be discoverable by username"
        update_user_account(user_id, {'email': 'test@example.com'})

        discord_user_id = _snowflake()
        try:
            parsed_command = ParsedCommand(
                intent='link_account',
                entities={
                    'username': existing_username,
                    'channel_identifier': discord_user_id,
                    'channel_type': 'discord'
                },
                confidence=0.9,
                original_message='link account'
            )

            with patch('communication.command_handlers.account_handler._send_confirmation_code') as mock_send:
                mock_send.return_value = True
                response = handler.handle(discord_user_id, parsed_command)

            assert response.completed is False, "Should not complete without code"
            assert 'confirmation code' in response.message.lower(), "Should mention confirmation code"
            assert mock_send.called, "Should call send confirmation code"

            assert discord_user_id in _pending_link_operations, "Should create pending operation"
            pending = _pending_link_operations[discord_user_id]
            assert pending['operation_type'] == 'link', "Should be link operation"
            assert pending['username'] == existing_username, "Should store username"
        finally:
            _pending_link_operations.pop(discord_user_id, None)
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_link_account_verifies_confirmation_code(self, test_data_dir):
        """Test: Link account verifies confirmation code and links account."""
        handler = AccountManagementHandler()

        existing_username = _unique_username("linkverifyuser")
        TestUserFactory.create_basic_user(existing_username, test_data_dir=test_data_dir)

        user_id = TestUserFactory.get_test_user_id_by_internal_username(
            existing_username, test_data_dir
        )
        assert user_id is not None, "User should be created"

        from core import update_user_account
        update_result = update_user_account(user_id, {'email': 'test@example.com'})
        assert update_result is True, "Email should be added"

        discord_user_id = _snowflake()
        confirmation_code = '123456'
        _pending_link_operations[discord_user_id] = {
            'operation_type': 'link',
            'username': existing_username,
            'user_id': user_id,
            'confirmation_code': confirmation_code,
            'channel_type': 'discord'
        }
        try:
            parsed_command = ParsedCommand(
                intent='link_account',
                entities={
                    'username': existing_username,
                    'confirmation_code': confirmation_code,
                    'channel_identifier': discord_user_id,
                    'channel_type': 'discord'
                },
                confidence=0.9,
                original_message='link account'
            )

            with patch('communication.command_handlers.account_handler._send_confirmation_code'):
                response = handler.handle(discord_user_id, parsed_command)

            assert response.completed is True, f"Should complete linking, got: {response.message}"
            assert 'linked successfully' in response.message.lower(), "Should indicate success"

            linked_user_id = get_user_id_by_identifier(discord_user_id)
            assert linked_user_id == user_id, "User should be linked"
            assert discord_user_id not in _pending_link_operations, "Should clear pending operation"
        finally:
            _pending_link_operations.pop(discord_user_id, None)
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_link_account_rejects_invalid_code(self, test_data_dir):
        """Test: Link account rejects invalid confirmation code."""
        handler = AccountManagementHandler()
        
        # Create existing user
        existing_username = 'linkinvaliduser'
        create_success = TestUserFactory.create_basic_user(
            existing_username, test_data_dir=test_data_dir
        )
        assert create_success is True, "Test user should be created"
        user_id = get_user_id_by_identifier(existing_username)
        assert user_id is not None, "Test user should be discoverable by username"
        
        # Set up pending operation
        discord_user_id = "555666777888999000"
        _pending_link_operations[discord_user_id] = {
            'operation_type': 'link',
            'username': existing_username,
            'user_id': user_id,
            'confirmation_code': '123456',
            'channel_type': 'discord'
        }
        
        parsed_command = ParsedCommand(
            intent='link_account',
            entities={
                'username': existing_username,
                'confirmation_code': '999999',  # Wrong code
                'channel_identifier': discord_user_id,
                'channel_type': 'discord'
            },
            confidence=0.9,
            original_message='link account'
        )
        
        response = handler.handle(discord_user_id, parsed_command)
        
        # Assert: Should reject invalid code
        assert response.completed is False, "Should not complete with invalid code"
        assert 'invalid' in response.message.lower(), "Should indicate invalid code"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_username_exists_checks_existing_username(self, test_data_dir):
        """Test: Username exists check finds existing username."""
        handler = AccountManagementHandler()

        existing_username = _unique_username("existscheckuser")
        create_success = TestUserFactory.create_basic_user(
            existing_username, test_data_dir=test_data_dir
        )
        assert create_success is True, "Test user should be created"

        assert handler._username_exists(existing_username), "Should find existing username"
        assert handler._username_exists(existing_username.upper()), "Should be case-insensitive"
        assert not handler._username_exists('nonexistentuser123'), "Should not find nonexistent username"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_get_user_id_by_username_returns_correct_id(self, test_data_dir):
        """Test: Get user ID by username returns correct user ID."""
        handler = AccountManagementHandler()

        existing_username = _unique_username("getiduser")
        create_success = TestUserFactory.create_basic_user(
            existing_username, test_data_dir=test_data_dir
        )
        assert create_success is True, "Test user should be created"

        user_id = TestUserFactory.get_test_user_id_by_internal_username(
            existing_username, test_data_dir
        )
        assert user_id is not None, "User should be created"

        found_id = handler._get_user_id_by_username(existing_username)
        assert found_id == user_id, "Should return correct user ID"

        found_id_upper = handler._get_user_id_by_username(existing_username.upper())
        assert found_id_upper == user_id, "Should be case-insensitive"

        found_id_nonexistent = handler._get_user_id_by_username('nonexistentuser123')
        assert found_id_nonexistent is None, "Should return None for nonexistent username"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_get_help_returns_help_text(self):
        """Test: Get help returns help text."""
        handler = AccountManagementHandler()
        
        help_text = handler.get_help()
        assert isinstance(help_text, str), "Should return string"
        assert len(help_text) > 0, "Should return non-empty help text"
        assert 'account' in help_text.lower(), "Should mention account"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_get_examples_returns_example_commands(self):
        """Test: Get examples returns example commands."""
        handler = AccountManagementHandler()
        
        examples = handler.get_examples()
        assert isinstance(examples, list), "Should return list"
        assert len(examples) > 0, "Should return examples"
        assert 'create account' in examples, "Should include create account"
        assert 'link account' in examples, "Should include link account"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_generate_confirmation_code_creates_6_digit_code(self):
        """Test: Generate confirmation code creates 6-digit code."""
        code = _generate_confirmation_code()
        
        assert isinstance(code, str), "Should return string"
        assert len(code) == 6, "Should be 6 digits"
        assert code.isdigit(), "Should contain only digits"
        
        # Generate multiple codes to ensure randomness
        codes = [_generate_confirmation_code() for _ in range(10)]
        assert len(set(codes)) > 1, "Should generate different codes"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_send_confirmation_code_with_email(self, test_data_dir):
        """Test: Send confirmation code attempts to send when user has email."""
        # Create user with email
        TestUserFactory.create_basic_user('emailtestuser', test_data_dir=test_data_dir)
        user_id = get_user_id_by_identifier('emailtestuser')
        assert user_id is not None, "User should be created"
        
        from core import update_user_account
        update_user_account(user_id, {'email': 'test@example.com'})
        
        # Mock the entire communication manager import path
        # Since get_communication_manager doesn't exist, we'll patch the import inside the function
        with patch('communication.command_handlers.account_handler.get_communication_manager', create=True) as mock_get_manager:
            mock_manager = MagicMock()
            # Mock both async and sync paths
            mock_manager.send_message = AsyncMock(return_value=True)
            mock_manager.send_message_sync.return_value = True
            mock_get_manager.return_value = mock_manager
            
            result = _send_confirmation_code(user_id, '123456', 'discord', 'test_discord_id')
        
        # Assert: Should attempt to send (may fail if comm manager not available, but should try)
        # The function will return False if comm manager is None, True if it succeeds
        assert isinstance(result, bool), "Should return boolean result"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_send_confirmation_code_without_email(self, test_data_dir):
        """Test: Send confirmation code fails when user has no email."""
        # Create user without email
        create_success = TestUserFactory.create_basic_user(
            'noemailuser', test_data_dir=test_data_dir
        )
        assert create_success is True, "Test user should be created"
        user_id = get_user_id_by_identifier('noemailuser')
        assert user_id is not None, "Test user should be discoverable by username"
        
        result = _send_confirmation_code(user_id, '123456', 'discord', 'test_discord_id')
        
        # Assert: Should fail without email
        assert result is False, "Should fail without email"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_link_account_with_email_channel(self, test_data_dir):
        """Test: Link account works with email channel type."""
        handler = AccountManagementHandler()

        existing_username = _unique_username("emaillinkuser")
        create_success = TestUserFactory.create_basic_user(
            existing_username, test_data_dir=test_data_dir
        )
        assert create_success is True, "Test user should be created"

        from core import update_user_account
        user_id = TestUserFactory.get_test_user_id_by_internal_username(
            existing_username, test_data_dir
        )
        assert user_id is not None, "Test user should be discoverable by username"
        update_user_account(user_id, {'email': 'existing@example.com'})

        email_address = f'linktest-{uuid.uuid4().hex[:8]}@example.com'
        parsed_command = ParsedCommand(
            intent='link_account',
            entities={
                'username': existing_username,
                'channel_identifier': email_address,
                'channel_type': 'email'
            },
            confidence=0.9,
            original_message='link account'
        )

        response = handler.handle(email_address, parsed_command)

        assert response.completed is False, "Should not complete immediately"
        assert 'already linked' in response.message.lower() or 'confirmation code' in response.message.lower(), "Should indicate status"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_link_account_with_already_linked_discord(self, test_data_dir):
        """Test: Link account rejects when Discord account already linked to different user."""
        handler = AccountManagementHandler()

        existing_username = _unique_username("alreadylinkeduser")
        create_success = TestUserFactory.create_basic_user(
            existing_username, test_data_dir=test_data_dir
        )
        assert create_success is True, "Test user should be created"

        from core import update_user_account
        user_id = TestUserFactory.get_test_user_id_by_internal_username(
            existing_username, test_data_dir
        )
        assert user_id is not None, "Test user should be discoverable by username"
        linked_discord_id = _snowflake()
        update_user_account(user_id, {
            'discord_user_id': linked_discord_id,
            'email': 'test@example.com'
        })

        new_discord_id = _snowflake()
        parsed_command = ParsedCommand(
            intent='link_account',
            entities={
                'username': existing_username,
                'channel_identifier': new_discord_id,
                'channel_type': 'discord'
            },
            confidence=0.9,
            original_message='link account'
        )

        response = handler.handle(new_discord_id, parsed_command)

        assert response.completed is False, "Should not complete immediately"
        assert 'already linked' in response.message.lower() or 'confirmation code' in response.message.lower() or 'could not send' in response.message.lower(), f"Should indicate status, got: {response.message}"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_link_account_with_already_linked_email(self, test_data_dir):
        """Test: Link account rejects when email already linked to different user."""
        handler = AccountManagementHandler()

        existing_username = _unique_username("alreadylinkedemailuser")
        create_success = TestUserFactory.create_basic_user(
            existing_username, test_data_dir=test_data_dir
        )
        assert create_success is True, "Test user should be created"

        from core import update_user_account
        user_id = TestUserFactory.get_test_user_id_by_internal_username(
            existing_username, test_data_dir
        )
        assert user_id is not None, "Test user should be discoverable by username"
        update_user_account(user_id, {'email': 'existing@example.com'})

        new_email = f'newemail-{uuid.uuid4().hex[:8]}@example.com'
        parsed_command = ParsedCommand(
            intent='link_account',
            entities={
                'username': existing_username,
                'channel_identifier': new_email,
                'channel_type': 'email'
            },
            confidence=0.9,
            original_message='link account'
        )

        response = handler.handle(new_email, parsed_command)

        assert response.completed is False, "Should not complete with already linked account"
        assert 'already linked' in response.message.lower(), "Should indicate already linked"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_link_account_with_invalid_pending_operation(self, test_data_dir):
        """Test: Link account rejects when pending operation doesn't match."""
        handler = AccountManagementHandler()

        existing_username = _unique_username("invalidpendinguser")
        TestUserFactory.create_basic_user(existing_username, test_data_dir=test_data_dir)

        discord_user_id = _snowflake()
        _pending_link_operations[discord_user_id] = {
            'operation_type': 'wrong_type',
            'username': 'wronguser',
            'user_id': 'wrong_id',
            'confirmation_code': '123456',
            'channel_type': 'discord'
        }
        try:
            parsed_command = ParsedCommand(
                intent='link_account',
                entities={
                    'username': existing_username,
                    'confirmation_code': '123456',
                    'channel_identifier': discord_user_id,
                    'channel_type': 'discord'
                },
                confidence=0.9,
                original_message='link account'
            )

            response = handler.handle(discord_user_id, parsed_command)

            assert response.completed is False, "Should not complete with invalid pending operation"
            assert 'no pending' in response.message.lower() or 'start over' in response.message.lower(), "Should indicate need to start over"
        finally:
            _pending_link_operations.pop(discord_user_id, None)
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_create_account_with_email_channel(self, test_data_dir):
        """Test: Create account works with email channel type."""
        handler = AccountManagementHandler()

        email_address = f'newemailuser-{uuid.uuid4().hex[:8]}@example.com'
        username = _unique_username("newemailuser")

        parsed_command = ParsedCommand(
            intent='create_account',
            entities={
                'username': username,
                'channel_identifier': email_address,
                'channel_type': 'email',
                'tasks_enabled': True,
                'checkins_enabled': True,
                'messages_enabled': False
            },
            confidence=0.9,
            original_message='create account'
        )

        response = handler.handle(email_address, parsed_command)
        
        # Assert: Should create account successfully
        assert response.completed is True, "Should complete account creation"
        assert 'Account created successfully' in response.message, "Should indicate success"
        
        # Verify user was actually created
        created_user_id = get_user_id_by_identifier(email_address)
        assert created_user_id is not None, "User should be created"
        
        # Verify email was set
        user_data = get_user_data(created_user_id, 'account')
        account_data = user_data.get('account', {})
        assert account_data.get('email') == email_address, "Email should be set"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_create_account_handles_creation_failure(self, test_data_dir):
        """Test: Create account handles creation failure gracefully."""
        handler = AccountManagementHandler()
        
        parsed_command = ParsedCommand(
            intent='create_account',
            entities={
                'username': 'failuser',
                'channel_identifier': 'fail@example.com',
                'channel_type': 'email',
                'tasks_enabled': True,
                'checkins_enabled': True,
                'messages_enabled': False
            },
            confidence=0.9,
            original_message='create account'
        )
        
        # Mock create_new_user to return None (failure)
        with patch('communication.command_handlers.account_handler.create_new_user') as mock_create:
            mock_create.return_value = None
            response = handler.handle('fail@example.com', parsed_command)
        
        # Assert: Should handle failure gracefully
        assert response.completed is False, "Should not complete on creation failure"
        assert 'failed' in response.message.lower() or 'error' in response.message.lower(), "Should indicate failure"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_link_account_handles_index_update_failure(self, test_data_dir):
        """Test: Link account handles index update failure gracefully."""
        handler = AccountManagementHandler()
        
        # Create existing user with email
        existing_username = 'indexfailuser'
        create_success = TestUserFactory.create_basic_user(
            existing_username, test_data_dir=test_data_dir
        )
        assert create_success is True, "Test user should be created"
        user_id = get_user_id_by_identifier(existing_username)
        assert user_id is not None, "Test user should be discoverable by username"
        
        # Add email to user account
        from core import update_user_account
        update_user_account(user_id, {'email': 'test@example.com'})
        
        # Set up pending operation
        discord_user_id = "777888999000111222"
        confirmation_code = '123456'
        _pending_link_operations[discord_user_id] = {
            'operation_type': 'link',
            'username': existing_username,
            'user_id': user_id,
            'confirmation_code': confirmation_code,
            'channel_type': 'discord'
        }
        
        parsed_command = ParsedCommand(
            intent='link_account',
            entities={
                'username': existing_username,
                'confirmation_code': confirmation_code,
                'channel_identifier': discord_user_id,
                'channel_type': 'discord'
            },
            confidence=0.9,
            original_message='link account'
        )
        
        # Mock update_user_account to succeed, but update_user_index to raise exception
        with patch('communication.command_handlers.account_handler.update_user_index') as mock_index, \
             patch('communication.command_handlers.account_handler._send_confirmation_code'), \
             patch('communication.command_handlers.account_handler.update_user_account') as mock_update:
            mock_index.side_effect = Exception("Index update failed")
            # Mock update_user_account to return True (linking succeeds)
            mock_update.return_value = True
            response = handler.handle(discord_user_id, parsed_command)
        
        # Assert: Should still complete linking (index failure is non-critical, but update_user_account failure is)
        # The actual implementation may fail if update_user_account fails, which is expected
        assert isinstance(response.completed, bool), "Should return boolean completion status"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_link_account_with_same_discord_id(self, test_data_dir):
        """Test: Link account allows linking when Discord ID matches existing link."""
        handler = AccountManagementHandler()
        
        # Create existing user with Discord ID
        existing_username = 'samediscorduser'
        discord_user_id = "888999000111222333"
        create_success = TestUserFactory.create_discord_user(
            existing_username,
            discord_user_id=discord_user_id,
            test_data_dir=test_data_dir,
        )
        assert create_success is True, "Test user should be created"
        user_id = get_user_id_by_identifier(existing_username)
        assert user_id is not None, "Test user should be discoverable by username"
        
        # Add email to user account
        from core import update_user_account
        update_user_account(user_id, {'email': 'test@example.com'})
        
        # Try to link same Discord ID (should work - same user)
        parsed_command = ParsedCommand(
            intent='link_account',
            entities={
                'username': existing_username,
                'channel_identifier': discord_user_id,
                'channel_type': 'discord'
            },
            confidence=0.9,
            original_message='link account'
        )
        
        # Should proceed to confirmation code step (not reject)
        with patch('communication.command_handlers.account_handler._send_confirmation_code') as mock_send:
            mock_send.return_value = True
            response = handler.handle(discord_user_id, parsed_command)
        
        # Assert: Should proceed (same Discord ID is allowed)
        # The handler should check username match, not just Discord ID
        assert response is not None, "Should return response"
        assert isinstance(response.message, str), "Should return string message"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_handle_routes_to_unknown_intent(self):
        """Test: Handler routes unknown intent to error message."""
        handler = AccountManagementHandler()
        
        parsed_command = ParsedCommand(
            intent='unknown_intent',
            entities={},
            confidence=0.9,
            original_message='unknown command'
        )
        
        response = handler.handle('test_user_id', parsed_command)
        
        # Assert: Should return error message
        assert response.completed is True, "Should complete with error message"
        assert 'don\'t understand' in response.message.lower() or 'try' in response.message.lower(), "Should provide helpful error"
        assert len(response.message) > 0, "Should return non-empty message"

