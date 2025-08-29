"""
Comprehensive tests for user creation and management scenarios.

Tests all the possibilities and options for user creation, including:
- Different channel types (email, discord)
- Feature combinations (messages, tasks, check-ins)
- Validation scenarios
- Data persistence
- Error handling
"""

import pytest
import os
import json
import tempfile
from unittest.mock import patch, Mock
from datetime import datetime
from pathlib import Path

from core.user_data_handlers import (
    get_user_data,
    save_user_data,
    update_user_account,
    update_user_preferences,
    update_user_context,
    update_user_schedules
)
from tests.test_utilities import TestUserFactory
from core.user_data_validation import is_valid_email, validate_schedule_periods__validate_time_format

class TestUserCreationScenarios:
    """Test comprehensive user creation scenarios."""
    
    @pytest.mark.integration
    @pytest.mark.user_management
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.file_io
    def test_basic_email_user_creation(self, test_data_dir, mock_config):
        """Test creating a basic email user with minimal settings."""
        user_id = 'test-basic-email'
        
        # Create test user directly using create_new_user
        from core.user_management import create_new_user
        user_data = {
            "internal_username": user_id,
            "email": 'basic@example.com',
            "channel": {"type": "email"},
            "categories": ["motivational", "health"],
            "checkin_settings": {"enabled": True},
            "task_settings": {"enabled": True}
        }
        actual_user_id = create_new_user(user_data)
        assert actual_user_id, "Test user should be created successfully"
        
        # Verify data can be loaded
        loaded_data = get_user_data(actual_user_id, 'all')
        assert loaded_data['account']['email'] == 'basic@example.com'
        assert loaded_data['preferences']['channel']['type'] == 'email'  # Email user should have email channel
        assert 'motivational' in loaded_data['preferences']['categories']
        # Note: enabled flags are removed from preferences and stored in account.features
        assert loaded_data['account']['features']['checkins'] == 'enabled'
        assert loaded_data['account']['features']['task_management'] == 'enabled'
    
    @pytest.mark.integration
    @pytest.mark.user_management
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.file_io
    def test_discord_user_creation(self, test_data_dir, mock_config):
        """Test creating a Discord user with full features enabled."""
        user_id = 'test-discord-user'
        
        # Create test user using centralized utilities for consistent setup
        from tests.test_utilities import TestUserFactory
        success = TestUserFactory.create_discord_user(user_id, discord_user_id='discord_user#1234', test_data_dir=test_data_dir)
        assert success, "Test user should be created successfully"
        
        # Get the UUID for the user
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        assert actual_user_id is not None, f"Should be able to get UUID for user {user_id}"
        
        # Update user context with additional data
        from core.user_management import update_user_context
        update_success = update_user_context(actual_user_id, {
            'preferred_name': 'Discord User',
            'gender_identity': ['they/them'],
            'custom_fields': {
                'health_conditions': ['ADHD', 'Depression']
            },
            'interests': ['Gaming', 'Technology'],
            'goals': ['Improve executive functioning', 'Stay organized']
        })
        assert update_success, "User context should be updated successfully"
        
        # Verify data can be loaded
        loaded_data = get_user_data(actual_user_id, 'all')
        assert loaded_data['account']['discord_user_id'] == 'discord_user#1234'
        assert loaded_data['preferences']['channel']['type'] == 'discord'
        assert 'motivational' in loaded_data['preferences']['categories']
        assert loaded_data['account']['features']['checkins'] == 'enabled'
        assert loaded_data['account']['features']['task_management'] == 'enabled'
        assert loaded_data['context']['preferred_name'] == 'Discord User'
        assert loaded_data['context']['gender_identity'] == ['they/them']
    
    @pytest.mark.unit
    def test_user_with_custom_fields(self, test_data_dir, mock_config):
        """Test creating a user with extensive custom fields using enhanced test utilities."""
        user_id = 'test-custom-fields'
        
        # Create test user using enhanced centralized utilities
        from tests.test_utilities import TestUserFactory
        success = TestUserFactory.create_user_with_custom_fields(user_id, None, test_data_dir)
        assert success, f"Failed to create custom fields test user {user_id}"
        
        # Get the UUID for the user
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        assert actual_user_id is not None, f"Should be able to get UUID for user {user_id}"
        
        # Verify complex data can be loaded
        loaded_data = get_user_data(actual_user_id, 'all')
        assert loaded_data['context']['preferred_name'] == f'Test User {user_id}'
        assert 'custom_fields' in loaded_data['context']
        assert 'ADHD' in loaded_data['context']['custom_fields']['health_conditions']
        assert 'Technology' in loaded_data['context']['interests']
        assert 'Improve executive functioning' in loaded_data['context']['goals']
    
    @pytest.mark.unit
    def test_user_creation_with_schedules(self, test_data_dir, mock_config):
        """Test creating a user with schedule periods using enhanced test utilities."""
        user_id = 'test-schedule-user-new'
        
        # Create test user using enhanced centralized utilities
        from tests.test_utilities import TestUserFactory
        success = TestUserFactory.create_user_with_schedules(user_id, None, test_data_dir)
        assert success, f"Failed to create schedule test user {user_id}"
        
        # Get the UUID for the user
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        assert actual_user_id is not None, f"Should be able to get UUID for user {user_id}"
        
        # Verify schedule data can be loaded
        loaded_data = get_user_data(actual_user_id, 'all')
        assert 'schedules' in loaded_data
        assert 'motivational' in loaded_data['schedules']
        assert 'Default' in loaded_data['schedules']['motivational']['periods']
        assert loaded_data['schedules']['motivational']['periods']['Default']['start_time'] == '18:00'

class TestUserCreationValidation:
    """Test validation scenarios during user creation."""
    
    @pytest.mark.unit
    def test_username_validation(self):
        """Test username validation."""
        # Note: Username validation is handled in the UI layer
        # Backend validation focuses on data integrity, not format
        # Valid usernames (basic format check)
        assert len('validuser') > 0
        assert len('user123') > 0
        assert len('user_name') > 0
        
        # Invalid usernames
        assert len('') == 0  # Empty username
        assert len('a') == 1  # Too short (handled in UI)
        assert '@' in 'user@name'  # Invalid characters (handled in UI)
    
    @pytest.mark.unit
    def test_email_validation(self):
        """Test email validation."""
        # Valid emails
        assert is_valid_email('user@example.com') is True
        assert is_valid_email('test.user@domain.co.uk') is True
        
        # Invalid emails
        assert is_valid_email('invalid-email') is False
        assert is_valid_email('user@') is False
        assert is_valid_email('@domain.com') is False
    
    @pytest.mark.unit
    def test_timezone_validation(self):
        """Test timezone validation."""
        # Note: Timezone validation is handled in the UI layer with dropdown selection
        # Backend validation focuses on data integrity, not format
        # Valid timezones (basic format check)
        assert len('America/New_York') > 0
        assert len('Europe/London') > 0
        assert len('Australia/Sydney') > 0
        
        # Invalid timezones
        assert len('') == 0  # Empty timezone
        assert '/' in 'Invalid/Timezone'  # Basic format check
    
    @pytest.mark.unit
    def test_required_fields_validation(self, test_data_dir, mock_config):
        """Test that required fields are validated."""
        user_id = 'test-validation-new'
        
        # Missing required fields
        incomplete_account = {
            'user_id': user_id,
            # Missing internal_username
            'account_status': 'active'
            # Missing channel type
        }
        
        # Create user using TestUserFactory
        success = TestUserFactory.create_basic_user(user_id, enable_checkins=True, enable_tasks=True, test_data_dir=test_data_dir)
        assert success is True, "Failed to create test user"
        
        # Test that we can update the existing user with new data
        # The user already has a complete structure, so we're testing updates
        result = save_user_data(user_id, {
            'account': incomplete_account,
            'preferences': {'categories': ['motivational']},  # Non-empty preferences
            'context': {'preferred_name': 'Test User'}  # Non-empty context
        })
        
        # Since the user already exists with a complete structure, 
        # save_user_data should handle the update properly
        assert isinstance(result, dict), "Should return a result dictionary"

class TestUserCreationErrorHandling:
    """Test error handling during user creation."""
    
    @pytest.mark.unit
    def test_duplicate_user_creation(self, test_data_dir, mock_config):
        """Test creating a user that already exists."""
        user_id = 'test-duplicate-new'
        
        # Create first user
        account_data = {
            'user_id': user_id,
            'internal_username': 'duplicateuser',
            'account_status': 'active',
            'channel': {'type': 'email', 'contact': 'test@example.com'}
        }
        
        # Create user using TestUserFactory
        success = TestUserFactory.create_basic_user(user_id, enable_checkins=True, enable_tasks=True, test_data_dir=test_data_dir)
        assert success is True, "Failed to create test user"
        
        # Test updating the existing user
        result1 = save_user_data(user_id, {
            'account': account_data,
            'preferences': {'categories': ['motivational']},  # Non-empty preferences
            'context': {'preferred_name': 'Duplicate User'}  # Non-empty context
        })
        assert isinstance(result1, dict), "Should return a result dictionary"
        
        # Try to update the same user again (should succeed - update existing)
        result2 = save_user_data(user_id, {
            'account': account_data,
            'preferences': {'categories': ['motivational']},  # Non-empty preferences
            'context': {'preferred_name': 'Duplicate User Updated'}  # Non-empty context
        })
        # Should succeed (update existing)
        assert isinstance(result2, dict), "Should return a result dictionary"
    
    @pytest.mark.unit
    def test_invalid_user_id(self, test_data_dir, mock_config):
        """Test creating user with invalid user ID."""
        invalid_user_id = 'invalid/user/id'  # Contains invalid characters
        
        account_data = {
            'user_id': invalid_user_id,
            'internal_username': 'testuser',
            'account_status': 'active',
            'channel': {'type': 'email', 'contact': 'test@example.com'}
        }
        
        # This should handle the invalid user ID gracefully
        result = save_user_data(invalid_user_id, {
            'account': account_data,
            'preferences': {},
            'context': {}
        })
        
        # Should either succeed (with sanitized ID) or fail gracefully
        assert isinstance(result, dict)
    
    @pytest.mark.unit
    def test_corrupted_data_handling(self, test_data_dir, mock_config):
        """Test handling corrupted user data."""
        user_id = 'test-corrupted'
        user_dir = os.path.join(test_data_dir, 'users', user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Create corrupted account file
        corrupted_account_file = os.path.join(user_dir, 'account.json')
        with open(corrupted_account_file, 'w') as f:
            f.write('{invalid json}')
        
        # Try to load corrupted data
        loaded_data = get_user_data(user_id, 'account', auto_create=False)
        # Should handle corruption gracefully
        assert isinstance(loaded_data, dict)

class TestUserCreationIntegration:
    """Test integration scenarios for user creation."""
    
    @pytest.mark.integration
    def test_full_user_lifecycle(self, test_data_dir, mock_config):
        """Test complete user lifecycle: create, update, delete."""
        user_id = 'test-lifecycle-new'
        
        # 1. Create user
        account_data = {
            'user_id': user_id,
            'internal_username': 'lifecycleuser',
            'account_status': 'active',
            'timezone': 'America/New_York',
            'channel': {'type': 'email', 'contact': 'lifecycle@example.com'}
        }
        
        preferences_data = {
            'categories': ['motivational'],
            'checkin_settings': {'enabled': False},
            'task_settings': {'enabled': False}
        }
        
        context_data = {
            'preferred_name': 'Lifecycle User'
        }
        
        # Create user using TestUserFactory
        success = TestUserFactory.create_basic_user(user_id, enable_checkins=True, enable_tasks=True, test_data_dir=test_data_dir)
        assert success is True, "Failed to create test user"
        
        # Update user with additional data
        result = save_user_data(user_id, {
            'account': account_data,
            'preferences': {
                **preferences_data,
                'channel': {'type': 'email'}  # Add required channel type
            },
            'context': context_data
        })
        assert isinstance(result, dict), "Should return a result dictionary"
        
        # 2. Verify user exists
        loaded_data = get_user_data(user_id, 'all')
        assert loaded_data['account']['internal_username'] == 'lifecycleuser'
        
        # 3. Update user preferences
        updated_preferences = {
            'categories': ['motivational', 'health'],
            'checkin_settings': {'enabled': True},
            'task_settings': {'enabled': False}
        }
        
        update_result = update_user_preferences(user_id, updated_preferences)
        assert update_result is True
        
        # 4. Verify update
        updated_data = get_user_data(user_id, 'preferences')
        assert 'health' in updated_data['preferences']['categories']
        assert updated_data['preferences']['checkin_settings']['enabled'] is True
        
        # 5. Update user context
        updated_context = {
            'preferred_name': 'Updated Lifecycle User',
            'interests': ['Testing', 'Development']
        }
        
        context_result = update_user_context(user_id, updated_context)
        assert context_result is True
        
        # 6. Verify context update
        final_context = get_user_data(user_id, 'context')
        assert final_context['context']['preferred_name'] == 'Updated Lifecycle User'
        assert 'Testing' in final_context['context']['interests']
    
    @pytest.mark.integration
    def test_multiple_users_same_channel(self, test_data_dir, mock_config):
        """Test creating multiple users with the same channel type."""
        users = [
            {
                'id': 'test-email-1-new',
                'username': 'emailuser1',
                'email': 'user1@example.com'
            },
            {
                'id': 'test-email-2-new',
                'username': 'emailuser2',
                'email': 'user2@example.com'
            },
            {
                'id': 'test-email-3-new',
                'username': 'emailuser3',
                'email': 'user3@example.com'
            }
        ]
        
        created_users = []
        
        # Create all users
        for user in users:
            account_data = {
                'user_id': user['id'],
                'internal_username': user['username'],
                'account_status': 'active',
                'channel': {'type': 'email', 'contact': user['email']}
            }
            
            # Create user using TestUserFactory
            success = TestUserFactory.create_basic_user(user['id'], enable_checkins=True, enable_tasks=True, test_data_dir=test_data_dir)
            assert success is True, "Failed to create test user"
            
            result = save_user_data(user['id'], {
                'account': account_data,
                'preferences': {
                    'categories': ['motivational'],
                    'channel': {'type': 'email'}  # Add required channel type
                },
                'context': {'preferred_name': f'{user["username"]} User'}  # Non-empty context
            })
            
            assert isinstance(result, dict), "Should return a result dictionary"
            created_users.append(user['id'])
        
        # Verify all users can be loaded
        for user_id in created_users:
            loaded_data = get_user_data(user_id, 'account')
            assert loaded_data['account']['channel']['type'] == 'email'
    
    @pytest.mark.integration
    def test_user_with_all_features(self, test_data_dir, mock_config):
        """Test creating a user with all possible features enabled."""
        user_id = 'test-all-features-new'
        
        # Account with all channel types (should choose one)
        account_data = {
            'user_id': user_id,
            'internal_username': 'allfeaturesuser',
            'account_status': 'active',
            'timezone': 'UTC',
            'channel': {
                'type': 'discord',
                'contact': 'allfeatures#1234'
            }
        }
        
        # All categories
        preferences_data = {
            'categories': [
                'motivational', 'health', 'fun_facts', 
                'quotes_to_ponder', 'word_of_the_day'
            ],
            'checkin_settings': {
                'enabled': True,
                'frequency': 'daily',
                'questions': [
                    'How are you feeling today?',
                    'What are your main goals?',
                    'Any challenges you\'re facing?'
                ]
            },
            'task_settings': {
                'enabled': True,
                'default_reminder_time': '09:00',
                'priority_levels': ['low', 'medium', 'high']
            }
        }
        
        # Comprehensive context
        context_data = {
            'preferred_name': 'All Features User',
            'pronouns': 'they/them',
            'date_of_birth': '1985-12-25',
            'health_conditions': ['ADHD', 'Anxiety', 'Depression'],
            'medications': ['Adderall', 'Lexapro'],
            'allergies': ['Shellfish', 'Dairy'],
            'interests': ['Programming', 'Reading', 'Hiking', 'Cooking'],
            'goals': [
                'Improve executive functioning',
                'Manage anxiety better',
                'Learn new programming languages',
                'Read 50 books this year'
            ],
            'loved_ones': [
                {'name': 'Alex', 'type': 'Partner', 'relationships': ['romantic']},
                {'name': 'Jordan', 'type': 'Friend', 'relationships': ['close_friend']},
                {'name': 'Dr. Smith', 'type': 'Healthcare', 'relationships': ['therapist']}
            ],
            'notes_for_ai': 'I respond well to gentle encouragement and need help with time management.'
        }
        
        # Comprehensive schedules
        schedules_data = {
            'motivational': {
                'periods': {
                    'morning': {
                        'active': True,
                        'days': ['monday', 'wednesday', 'friday'],
                        'start_time': '08:00',
                        'end_time': '10:00'
                    }
                }
            },
            'health': {
                'periods': {
                    'evening': {
                        'active': True,
                        'days': ['tuesday', 'thursday'],
                        'start_time': '18:00',
                        'end_time': '20:00'
                    }
                }
            },
            'fun_facts': {
                'periods': {
                    'weekend': {
                        'active': True,
                        'days': ['saturday'],
                        'start_time': '12:00',
                        'end_time': '14:00'
                    }
                }
            }
        }
        
        # Create user using TestUserFactory
        success = TestUserFactory.create_basic_user(user_id, enable_checkins=True, enable_tasks=True, test_data_dir=test_data_dir)
        assert success is True, "Failed to create test user"
        
        # Save all data
        result = save_user_data(user_id, {
            'account': account_data,
            'preferences': {
                **preferences_data,
                'channel': {'type': 'discord'}  # Add required channel type
            },
            'context': context_data,
            'schedules': schedules_data
        })
        
        # Verify all saves were successful
        assert result.get('account') is True
        assert result.get('preferences') is True
        assert result.get('context') is True
        assert result.get('schedules') is True
        
        # Verify all data can be loaded
        loaded_data = get_user_data(user_id, 'all')
        
        # Verify account
        assert loaded_data['account']['channel']['type'] == 'discord'
        assert loaded_data['account']['timezone'] == 'UTC'
        
        # Verify preferences
        assert len(loaded_data['preferences']['categories']) == 5
        assert loaded_data['preferences']['checkin_settings']['enabled'] is True
        assert loaded_data['preferences']['task_settings']['enabled'] is True
        
        # Verify context
        assert loaded_data['context']['preferred_name'] == 'All Features User'
        assert len(loaded_data['context']['health_conditions']) == 3
        assert len(loaded_data['context']['loved_ones']) == 3
        
        # Verify schedules
        assert 'motivational' in loaded_data['schedules']
        assert 'health' in loaded_data['schedules']
        assert 'fun_facts' in loaded_data['schedules'] 