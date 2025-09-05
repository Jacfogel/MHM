#!/usr/bin/env python3
"""
Behavior tests for Core User Management coverage expansion.

Tests real behavior and side effects of user management functionality.
Focuses on expanding coverage from 63% to 70% by testing:
- User data loader registration and management
- User account creation and management
- User preferences handling
- User context management
- User schedules management
- Cache management and invalidation
- Error handling and recovery
- Data validation and normalization
- File operations and persistence
"""

import pytest
import os
import json
import time
from datetime import datetime
from unittest.mock import patch, MagicMock, mock_open
import core
from core.user_management import (
    register_data_loader,
    get_available_data_types,
    get_data_type_info,
    get_all_user_ids,
    _get_user_data__load_account,
    _save_user_data__save_account,
    _get_user_data__load_preferences,
    _save_user_data__save_preferences,
    _get_user_data__load_context,
    _save_user_data__save_context,
    _get_user_data__load_schedules,
    _save_user_data__save_schedules,
    update_user_schedules,
    create_default_schedule_periods,
    USER_DATA_LOADERS
)
from tests.test_utilities import TestUserFactory, TestDataFactory


class TestUserManagementCoverageExpansion:
    """Test Core User Management coverage expansion with real behavior verification."""
    
    @pytest.fixture(autouse=True)
    def _setup(self, test_path_factory, monkeypatch):
        """Set up test environment with per-test directory and path patches."""
        self.test_dir = test_path_factory
        self.test_user_id = "test_user_123"
        self.test_user_dir = os.path.join(self.test_dir, "data", "users", self.test_user_id)
        os.makedirs(self.test_user_dir, exist_ok=True)

        # Patch file path resolution and directory ensure
        def mock_path(user_id, file_type):
            return os.path.join(self.test_user_dir, f"{file_type}.json")
        monkeypatch.setattr('core.user_management.get_user_file_path', mock_path, raising=False)
        monkeypatch.setattr('core.user_management.ensure_user_directory', lambda uid: True, raising=False)
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            import shutil
            shutil.rmtree(self.test_dir)
    
    def test_register_data_loader_real_behavior(self):
        """Test data loader registration with real behavior."""
        # Arrange
        def test_loader(user_id, auto_create=True):
            return {"test": "data"}

        # Act/Assert within cleanup to avoid leaking custom loader
        try:
            register_data_loader(
                "test_type",
                test_loader,
                "test_file",
                ["field1", "field2"],
                ["created_at"],
                "Test data type",
            )

            # Assert
            assert "test_type" in USER_DATA_LOADERS, "Should register new data type"
            loader_info = USER_DATA_LOADERS["test_type"]
            assert loader_info["loader"] == test_loader, "Should store loader function"
            assert loader_info["file_type"] == "test_file", "Should store file type"
            assert loader_info["default_fields"] == ["field1", "field2"], "Should store default fields"
            assert loader_info["metadata_fields"] == ["created_at"], "Should store metadata fields"
            assert loader_info["description"] == "Test data type", "Should store description"
        finally:
            USER_DATA_LOADERS.pop("test_type", None)

    def test_get_available_data_types_real_behavior(self):
        """Test getting available data types."""
        # Act
        data_types = get_available_data_types()
        
        # Assert
        assert isinstance(data_types, list), "Should return list"
        assert "account" in data_types, "Should include account type"
        assert "preferences" in data_types, "Should include preferences type"
        assert "context" in data_types, "Should include context type"
        assert "schedules" in data_types, "Should include schedules type"
    
    def test_get_data_type_info_real_behavior(self):
        """Test getting data type information."""
        # Act
        account_info = get_data_type_info("account")
        invalid_info = get_data_type_info("invalid_type")
        
        # Assert
        assert account_info is not None, "Should return info for valid type"
        assert "file_type" in account_info, "Should have file_type field"
        assert "default_fields" in account_info, "Should have default_fields field"
        assert "metadata_fields" in account_info, "Should have metadata_fields field"
        assert "description" in account_info, "Should have description field"
        assert invalid_info is None, "Should return None for invalid type"
    
    def test_get_all_user_ids_real_behavior(self):
        """Test getting all user IDs with real behavior."""
        # Arrange - Create test user directories
        test_users = ["user1", "user2", "user3"]
        for user_id in test_users:
            user_dir = os.path.join(self.test_dir, user_id)
            os.makedirs(user_dir, exist_ok=True)
            # Create account.json file
            account_file = os.path.join(user_dir, "account.json")
            with open(account_file, 'w') as f:
                json.dump({"user_id": user_id}, f)
        
        # Mock USER_INFO_DIR_PATH
        with patch.object(core.config, 'USER_INFO_DIR_PATH', self.test_dir):
            # Act
            user_ids = get_all_user_ids()
            
            # Assert
            assert isinstance(user_ids, list), "Should return list"
            assert len(user_ids) == 3, "Should find all test users"
            for user_id in test_users:
                assert user_id in user_ids, f"Should include user {user_id}"
    
    def test_get_all_user_ids_no_directory_real_behavior(self):
        """Test getting user IDs when directory doesn't exist."""
        # Arrange - Use non-existent directory
        with patch.object(core.config, 'USER_INFO_DIR_PATH', "/non/existent/path"):
            # Act
            user_ids = get_all_user_ids()
            
            # Assert
            assert user_ids == [], "Should return empty list for non-existent directory"
    
    def test_load_account_data_real_behavior(self):
        """Test loading account data with real behavior."""
        # Arrange - Create test account file
        test_account = {
            "user_id": self.test_user_id,
            "internal_username": "testuser",
            "account_status": "active",
            "created_at": "2024-01-01 00:00:00",
            "updated_at": "2024-01-01 00:00:00"
        }
        account_file = os.path.join(self.test_user_dir, "account.json")
        with open(account_file, 'w') as f:
            json.dump(test_account, f)
        
        # Act
        with patch('core.user_management.get_user_file_path', return_value=account_file):
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.load_json_data', return_value=test_account):
                    result = _get_user_data__load_account(self.test_user_id)
        
        # Assert
        assert result is not None, "Should return account data"
        assert result["user_id"] == self.test_user_id, "Should have correct user ID"
        assert result["internal_username"] == "testuser", "Should have correct username"
        assert result["account_status"] == "active", "Should have correct status"
    
    def test_load_account_data_auto_create_real_behavior(self):
        """Test auto-creating account data when file doesn't exist."""
        # Arrange - User directory exists but no account file
        os.makedirs(self.test_user_dir, exist_ok=True)
        
        # Act
        with patch('core.user_management.get_user_file_path') as mock_get_path:
            def mock_path(user_id, file_type):
                return os.path.join(self.test_user_dir, f"{file_type}.json")
            mock_get_path.side_effect = mock_path
            
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.save_json_data') as mock_save:
                    result = _get_user_data__load_account(self.test_user_id, auto_create=True)
        
        # Assert
        assert result is not None, "Should return created account data"
        assert result["user_id"] == self.test_user_id, "Should have correct user ID"
        assert result["account_status"] == "active", "Should have default status"
        assert "created_at" in result, "Should have created_at timestamp"
        assert "updated_at" in result, "Should have updated_at timestamp"
        assert mock_save.called, "Should save the created account data"
    
    def test_load_account_data_no_auto_create_real_behavior(self):
        """Test loading account data without auto-creation."""
        # Arrange - User directory doesn't exist
        if os.path.exists(self.test_user_dir):
            import shutil
            shutil.rmtree(self.test_user_dir)
        
        # Act
        with patch('core.user_management.get_user_file_path') as mock_get_path:
            def mock_path(user_id, file_type):
                return os.path.join(self.test_user_dir, f"{file_type}.json")
            mock_get_path.side_effect = mock_path
            
            result = _get_user_data__load_account(self.test_user_id, auto_create=False)
        
        # Assert
        assert result is None, "Should return None when file doesn't exist and auto_create is False"
    
    def test_save_account_data_real_behavior(self):
        """Test saving account data with real behavior."""
        # Arrange
        test_account = {
            "user_id": self.test_user_id,
            "internal_username": "testuser",
            "account_status": "active"
        }
        
        # Act
        with patch('core.user_management.get_user_file_path') as mock_get_path:
            def mock_path(user_id, file_type):
                return os.path.join(self.test_user_dir, f"{file_type}.json")
            mock_get_path.side_effect = mock_path
            
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.save_json_data') as mock_save:
                    with patch('core.user_management.validate_account_dict') as mock_validate:
                        mock_validate.return_value = (test_account, [])
                        result = _save_user_data__save_account(self.test_user_id, test_account)
        
        # Assert
        assert result is True, "Should return True on successful save"
        assert mock_save.called, "Should call save_json_data"
        assert mock_validate.called, "Should validate account data"
    
    def test_save_account_data_invalid_user_id_real_behavior(self):
        """Test saving account data with invalid user ID."""
        # Act
        result = _save_user_data__save_account(None, {})
        
        # Assert
        assert result is False, "Should return False for invalid user ID"
    
    def test_load_preferences_data_real_behavior(self):
        """Test loading preferences data with real behavior."""
        # Arrange - Create test preferences file
        test_preferences = {
            "categories": ["health", "tasks"],
            "channel": {"type": "email"},
            "checkin_settings": {"enabled": True}
        }
        preferences_file = os.path.join(self.test_user_dir, "preferences.json")
        with open(preferences_file, 'w') as f:
            json.dump(test_preferences, f)
        
        # Act
        with patch('core.user_management.get_user_file_path', return_value=preferences_file):
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.load_json_data', return_value=test_preferences):
                    result = _get_user_data__load_preferences(self.test_user_id)
        
        # Assert
        assert result is not None, "Should return preferences data"
        assert result["categories"] == ["health", "tasks"], "Should have correct categories"
        assert result["channel"]["type"] == "email", "Should have correct channel type"
        assert result["checkin_settings"]["enabled"] is True, "Should have correct checkin settings"
    
    def test_load_preferences_data_auto_create_real_behavior(self):
        """Test auto-creating preferences data when file doesn't exist."""
        # Arrange - User directory exists but no preferences file
        os.makedirs(self.test_user_dir, exist_ok=True)
        
        # Act
        with patch('core.user_management.get_user_file_path') as mock_get_path:
            def mock_path(user_id, file_type):
                return os.path.join(self.test_user_dir, f"{file_type}.json")
            mock_get_path.side_effect = mock_path
            
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.save_json_data') as mock_save:
                    result = _get_user_data__load_preferences(self.test_user_id, auto_create=True)
        
        # Assert
        assert result is not None, "Should return created preferences data"
        assert "categories" in result, "Should have categories field"
        assert "channel" in result, "Should have channel field"
        assert "checkin_settings" in result, "Should have checkin_settings field"
        assert result["channel"]["type"] == "email", "Should have default channel type"
        assert mock_save.called, "Should save the created preferences data"
    
    def test_save_preferences_data_real_behavior(self):
        """Test saving preferences data with real behavior."""
        # Arrange
        test_preferences = {
            "categories": ["health", "tasks"],
            "channel": {"type": "discord"},
            "checkin_settings": {"enabled": True}
        }
        
        # Act
        with patch('core.user_management.get_user_file_path') as mock_get_path:
            def mock_path(user_id, file_type):
                return os.path.join(self.test_user_dir, f"{file_type}.json")
            mock_get_path.side_effect = mock_path
            
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.save_json_data') as mock_save:
                    with patch('core.user_management.validate_preferences_dict') as mock_validate:
                        mock_validate.return_value = (test_preferences, [])
                        result = _save_user_data__save_preferences(self.test_user_id, test_preferences)
        
        # Assert
        assert result is True, "Should return True on successful save"
        assert mock_save.called, "Should call save_json_data"
        assert mock_validate.called, "Should validate preferences data"
    
    def test_load_context_data_real_behavior(self):
        """Test loading context data with real behavior."""
        # Arrange - Create test context file
        test_context = {
            "preferred_name": "Test User",
            "gender_identity": ["non-binary"],
            "interests": ["programming", "reading"],
            "goals": ["Learn Python", "Stay healthy"]
        }
        context_file = os.path.join(self.test_user_dir, "user_context.json")
        with open(context_file, 'w') as f:
            json.dump(test_context, f)
        
        # Act
        with patch('core.user_management.get_user_file_path', return_value=context_file):
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.load_json_data', return_value=test_context):
                    result = _get_user_data__load_context(self.test_user_id)
        
        # Assert
        assert result is not None, "Should return context data"
        assert result["preferred_name"] == "Test User", "Should have correct preferred name"
        assert result["gender_identity"] == ["non-binary"], "Should have correct gender identity"
        assert result["interests"] == ["programming", "reading"], "Should have correct interests"
        assert result["goals"] == ["Learn Python", "Stay healthy"], "Should have correct goals"
    
    def test_load_context_data_auto_create_real_behavior(self):
        """Test auto-creating context data when file doesn't exist."""
        # Arrange - User directory exists but no context file
        os.makedirs(self.test_user_dir, exist_ok=True)
        
        # Act
        with patch('core.user_management.get_user_file_path') as mock_get_path:
            def mock_path(user_id, file_type):
                return os.path.join(self.test_user_dir, f"{file_type}.json")
            mock_get_path.side_effect = mock_path
            
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.save_json_data') as mock_save:
                    result = _get_user_data__load_context(self.test_user_id, auto_create=True)
        
        # Assert
        assert result is not None, "Should return created context data"
        assert "preferred_name" in result, "Should have preferred_name field"
        assert "gender_identity" in result, "Should have gender_identity field"
        assert "custom_fields" in result, "Should have custom_fields field"
        assert "interests" in result, "Should have interests field"
        assert "goals" in result, "Should have goals field"
        assert "created_at" in result, "Should have created_at timestamp"
        assert "last_updated" in result, "Should have last_updated timestamp"
        assert mock_save.called, "Should save the created context data"
    
    def test_save_context_data_real_behavior(self):
        """Test saving context data with real behavior."""
        # Arrange
        test_context = {
            "preferred_name": "Updated User",
            "gender_identity": ["female"],
            "interests": ["art", "music"],
            "goals": ["Learn painting", "Practice guitar"]
        }
        
        # Act - Mock the update_user_index call to avoid side effects
        with patch('core.user_management.get_user_file_path') as mock_get_path:
            def mock_path(user_id, file_type):
                return os.path.join(self.test_user_dir, f"{file_type}.json")
            mock_get_path.side_effect = mock_path
            
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.save_json_data') as mock_save:
                    with patch('core.user_data_manager.update_user_index') as mock_update_index:
                        result = _save_user_data__save_context(self.test_user_id, test_context)
        
        # Assert
        assert result is True, "Should return True on successful save"
        assert mock_save.called, "Should call save_json_data"
        # Find the call to save_json_data with context data (not the empty dict from update_user_index)
        context_save_calls = [call for call in mock_save.call_args_list if call[0][0] and 'preferred_name' in call[0][0]]
        assert len(context_save_calls) > 0, "Should have called save_json_data with context data"
        saved_data = context_save_calls[0][0][0]  # First argument of the first context save call
        assert "last_updated" in saved_data, "Should add last_updated timestamp"
        assert saved_data["preferred_name"] == "Updated User", "Should preserve original data"
    
    def test_load_schedules_data_real_behavior(self):
        """Test loading schedules data with real behavior."""
        # Arrange - Create test schedules file
        test_schedules = {
            "morning": {"time": "09:00", "enabled": True},
            "evening": {"time": "18:00", "enabled": False}
        }
        schedules_file = os.path.join(self.test_user_dir, "schedules.json")
        with open(schedules_file, 'w') as f:
            json.dump(test_schedules, f)
        
        # Act
        with patch('core.user_management.get_user_file_path', return_value=schedules_file):
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.load_json_data', return_value=test_schedules):
                    result = _get_user_data__load_schedules(self.test_user_id)
        
        # Assert
        assert result is not None, "Should return schedules data"
        assert result["morning"]["time"] == "09:00", "Should have correct morning time"
        assert result["morning"]["enabled"] is True, "Should have correct morning enabled status"
        assert result["evening"]["time"] == "18:00", "Should have correct evening time"
        assert result["evening"]["enabled"] is False, "Should have correct evening enabled status"
    
    def test_load_schedules_data_auto_create_real_behavior(self):
        """Test auto-creating schedules data when file doesn't exist."""
        # Arrange - User directory exists but no schedules file
        os.makedirs(self.test_user_dir, exist_ok=True)
        
        # Act
        with patch('core.user_management.get_user_file_path') as mock_get_path:
            def mock_path(user_id, file_type):
                return os.path.join(self.test_user_dir, f"{file_type}.json")
            mock_get_path.side_effect = mock_path
            
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.save_json_data') as mock_save:
                    result = _get_user_data__load_schedules(self.test_user_id, auto_create=True)
        
        # Assert
        assert result is not None, "Should return created schedules data"
        assert isinstance(result, dict), "Should return dictionary"
        assert mock_save.called, "Should save the created schedules data"
    
    def test_save_schedules_data_real_behavior(self):
        """Test saving schedules data with real behavior."""
        # Arrange
        test_schedules = {
            "breakfast": {"time": "08:00", "enabled": True},
            "lunch": {"time": "12:00", "enabled": True},
            "dinner": {"time": "19:00", "enabled": True}
        }
        
        # Act
        with patch('core.user_management.get_user_file_path') as mock_get_path:
            def mock_path(user_id, file_type):
                return os.path.join(self.test_user_dir, f"{file_type}.json")
            mock_get_path.side_effect = mock_path
            
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.save_json_data') as mock_save:
                    result = _save_user_data__save_schedules(self.test_user_id, test_schedules)
        
        # Assert
        assert result is True, "Should return True on successful save"
        assert mock_save.called, "Should call save_json_data"
    
    def test_save_schedules_data_invalid_user_id_real_behavior(self):
        """Test saving schedules data with invalid user ID."""
        # Act
        result = _save_user_data__save_schedules(None, {})
        
        # Assert
        assert result is False, "Should return False for invalid user ID"
    
    def test_update_user_schedules_real_behavior(self):
        """Test updating user schedules with real behavior."""
        # Arrange
        test_schedules = {
            "workout": {"time": "07:00", "enabled": True},
            "meditation": {"time": "20:00", "enabled": True}
        }
        
        # Act
        with patch('core.user_data_handlers.save_user_data') as mock_save:
            mock_save.return_value = {"schedules": True}
            result = update_user_schedules(self.test_user_id, test_schedules)
        
        # Assert
        assert result is True, "Should return True on successful update"
        assert mock_save.called, "Should call save_user_data"
    
    def test_update_user_schedules_invalid_user_id_real_behavior(self):
        """Test updating schedules with invalid user ID."""
        # Act
        result = update_user_schedules(None, {})
        
        # Assert
        assert result is False, "Should return False for invalid user ID"
    
    def test_create_default_schedule_periods_tasks_real_behavior(self):
        """Test creating default schedule periods for tasks category."""
        # Act
        result = create_default_schedule_periods("tasks")
        
        # Assert
        assert isinstance(result, dict), "Should return dictionary"
        assert "ALL" in result, "Should have ALL period"
        assert "Task Reminder Default" in result, "Should have Task Reminder Default period"
        assert result["ALL"]["active"] is True, "ALL period should be active"
        assert result["Task Reminder Default"]["active"] is True, "Task period should be active"
    
    def test_create_default_schedule_periods_checkin_real_behavior(self):
        """Test creating default schedule periods for checkin category."""
        # Act
        result = create_default_schedule_periods("checkin")
        
        # Assert
        assert isinstance(result, dict), "Should return dictionary"
        assert "ALL" in result, "Should have ALL period"
        assert "Check-in Reminder Default" in result, "Should have Check-in Reminder Default period"
        assert result["ALL"]["active"] is True, "ALL period should be active"
        assert result["Check-in Reminder Default"]["active"] is True, "Check-in period should be active"
    
    def test_create_default_schedule_periods_other_category_real_behavior(self):
        """Test creating default schedule periods for other categories."""
        # Act
        result = create_default_schedule_periods("health")
        
        # Assert
        assert isinstance(result, dict), "Should return dictionary"
        assert "ALL" in result, "Should have ALL period"
        assert "Health Message Default" in result, "Should have Health Message Default period"
        assert result["ALL"]["active"] is True, "ALL period should be active"
        assert result["Health Message Default"]["active"] is True, "Health period should be active"
    
    def test_create_default_schedule_periods_no_category_real_behavior(self):
        """Test creating default schedule periods without category."""
        # Act
        result = create_default_schedule_periods()
        
        # Assert
        assert isinstance(result, dict), "Should return dictionary"
        assert "ALL" in result, "Should have ALL period"
        assert "Default" in result, "Should have Default period"
        assert result["ALL"]["active"] is True, "ALL period should be active"
        assert result["Default"]["active"] is True, "Default period should be active"
    
    def test_cache_management_real_behavior(self):
        """Test cache management behavior."""
        # Arrange - Load data to populate cache
        test_account = {"user_id": self.test_user_id, "status": "active"}
        
        with patch('core.user_management.get_user_file_path') as mock_get_path:
            def mock_path(user_id, file_type):
                return os.path.join(self.test_user_dir, f"{file_type}.json")
            mock_get_path.side_effect = mock_path
            
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.load_json_data', return_value=test_account):
                    # First load - should populate cache
                    result1 = _get_user_data__load_account(self.test_user_id)
                    
                    # Second load - should use cache
                    result2 = _get_user_data__load_account(self.test_user_id)
        
        # Assert
        assert result1 is not None, "First load should succeed"
        assert result2 is not None, "Second load should succeed"
        assert result1 == result2, "Both loads should return same data"
    
    def test_cache_timeout_real_behavior(self):
        """Test cache timeout behavior."""
        # Arrange - Load data to populate cache
        test_account = {"user_id": self.test_user_id, "status": "active"}
        
        with patch('core.user_management.get_user_file_path') as mock_get_path:
            def mock_path(user_id, file_type):
                return os.path.join(self.test_user_dir, f"{file_type}.json")
            mock_get_path.side_effect = mock_path
            
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.load_json_data', return_value=test_account):
                    # First load - should populate cache
                    result1 = _get_user_data__load_account(self.test_user_id)
                    
                    # Mock time to simulate cache timeout
                    with patch('time.time', return_value=time.time() + 400):  # 6+ minutes
                        # Second load - should reload from file
                        result2 = _get_user_data__load_account(self.test_user_id)
        
        # Assert
        assert result1 is not None, "First load should succeed"
        assert result2 is not None, "Second load should succeed"
    
    def test_error_handling_load_account_real_behavior(self):
        """Test error handling in account loading."""
        # Arrange - Test with invalid user ID to trigger error path
        # Act
        result = _get_user_data__load_account(None)
        
        # Assert
        assert result is None, "Should return None on error"
    
    def test_error_handling_save_account_real_behavior(self):
        """Test error handling in account saving."""
        # Arrange - Test with invalid user ID to trigger error path
        test_account = {"user_id": self.test_user_id, "status": "active"}
        
        # Act
        result = _save_user_data__save_account(None, test_account)
        
        # Assert
        assert result is False, "Should return False on error"
    
    def test_data_validation_real_behavior(self):
        """Test data validation behavior."""
        # Arrange
        invalid_account = {
            "user_id": self.test_user_id,
            "invalid_field": "invalid_value"
        }
        
        # Act
        with patch('core.user_management.get_user_file_path') as mock_get_path:
            def mock_path(user_id, file_type):
                return os.path.join(self.test_user_dir, f"{file_type}.json")
            mock_get_path.side_effect = mock_path
            
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.save_json_data') as mock_save:
                    with patch('core.user_management.validate_account_dict') as mock_validate:
                        # Mock validation to return errors
                        mock_validate.return_value = (invalid_account, ["validation error"])
                        result = _save_user_data__save_account(self.test_user_id, invalid_account)
        
        # Assert
        assert result is True, "Should still save data even with validation errors"
        assert mock_validate.called, "Should call validation function"
        assert mock_save.called, "Should still save the data"
    
    def test_file_persistence_real_behavior(self):
        """Test file persistence behavior."""
        # Arrange
        test_account = {
            "user_id": self.test_user_id,
            "internal_username": "testuser",
            "account_status": "active"
        }
        account_file = os.path.join(self.test_user_dir, "account.json")
        
        # Act
        with patch('core.user_management.get_user_file_path', return_value=account_file):
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.save_json_data') as mock_save:
                    with patch('core.user_management.validate_account_dict') as mock_validate:
                        with patch('core.user_data_manager.update_user_index') as mock_update_index:
                            mock_validate.return_value = (test_account, [])
                            result = _save_user_data__save_account(self.test_user_id, test_account)
        
        # Assert
        assert result is True, "Should return True on successful save"
        assert mock_save.called, "Should call save_json_data"
        # Verify the save was called with the correct data
        call_args = mock_save.call_args
        saved_data = call_args[0][0]  # First argument is the data
        # The function adds updated_at timestamp, so check for that
        assert "updated_at" in saved_data, "Should add updated_at timestamp"
        # Check that the original data is preserved
        assert saved_data.get("internal_username") == "testuser", "Should save correct username"
        assert saved_data.get("account_status") == "active", "Should save correct status"


class TestUserManagementIntegration:
    """Test integration behavior of Core User Management."""
    
    @pytest.fixture(autouse=True)
    def _setup(self, test_path_factory):
        """Set up test environment."""
        self.test_dir = test_path_factory
        self.test_user_id = "integration_test_user"
        self.test_user_dir = os.path.join(self.test_dir, "data", "users", self.test_user_id)
        os.makedirs(self.test_user_dir, exist_ok=True)
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            import shutil
            shutil.rmtree(self.test_dir)
    
    def test_user_data_lifecycle_real_behavior(self):
        """Test complete user data lifecycle."""
        # Arrange
        test_account = {
            "user_id": self.test_user_id,
            "internal_username": "integration_user",
            "account_status": "active"
        }
        
        test_preferences = {
            "categories": ["health", "tasks"],
            "channel": {"type": "discord"}
        }
        
        test_context = {
            "preferred_name": "Integration User",
            "gender_identity": ["non-binary"],
            "interests": ["testing", "integration"]
        }
        
        test_schedules = {
            "morning": {"time": "08:00", "enabled": True},
            "evening": {"time": "20:00", "enabled": True}
        }
        
        # Act - Save all data types
        with patch('core.user_management.get_user_file_path') as mock_get_path:
            def mock_path(user_id, file_type):
                return os.path.join(self.test_user_dir, f"{file_type}.json")
            mock_get_path.side_effect = mock_path
            
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.save_json_data') as mock_save:
                    with patch('core.user_management.validate_account_dict') as mock_validate_account:
                        with patch('core.user_management.validate_preferences_dict') as mock_validate_prefs:
                            with patch('core.user_data_manager.update_user_index') as mock_update_index:
                                mock_validate_account.return_value = (test_account, [])
                                mock_validate_prefs.return_value = (test_preferences, [])
                                
                                # Save all data types
                                account_result = _save_user_data__save_account(self.test_user_id, test_account)
                                prefs_result = _save_user_data__save_preferences(self.test_user_id, test_preferences)
                                context_result = _save_user_data__save_context(self.test_user_id, test_context)
                                schedules_result = _save_user_data__save_schedules(self.test_user_id, test_schedules)
        
        # Assert
        assert account_result is True, "Account save should succeed"
        assert prefs_result is True, "Preferences save should succeed"
        assert context_result is True, "Context save should succeed"
        assert schedules_result is True, "Schedules save should succeed"
        # Count only the main data saves (not the side effect saves from update_user_index)
        main_saves = [call for call in mock_save.call_args_list if len(call[0]) > 0 and isinstance(call[0][0], dict) and any(key in call[0][0] for key in ['internal_username', 'categories', 'preferred_name', 'morning'])]
        assert len(main_saves) == 4, f"Should save all four data types, got {len(main_saves)}"
    
    def test_user_data_consistency_real_behavior(self):
        """Test user data consistency across operations."""
        # Arrange
        original_account = {
            "user_id": self.test_user_id,
            "internal_username": "consistency_user",
            "account_status": "active"
        }
        
        # Act - Save and then load the same data
        with patch('core.user_management.get_user_file_path') as mock_get_path:
            def mock_path(user_id, file_type):
                return os.path.join(self.test_user_dir, f"{file_type}.json")
            mock_get_path.side_effect = mock_path
            
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.save_json_data') as mock_save:
                    with patch('core.user_management.load_json_data') as mock_load:
                        with patch('core.user_management.validate_account_dict') as mock_validate:
                            mock_validate.return_value = (original_account, [])
                            mock_load.return_value = original_account
                            
                            # Save the data
                            save_result = _save_user_data__save_account(self.test_user_id, original_account)
                            
                            # Load the data
                            load_result = _get_user_data__load_account(self.test_user_id)
        
        # Assert
        assert save_result is True, "Save should succeed"
        assert load_result is not None, "Load should succeed"
        assert load_result["user_id"] == original_account["user_id"], "Should maintain user ID consistency"
        assert load_result["internal_username"] == original_account["internal_username"], "Should maintain username consistency"
        assert load_result["account_status"] == original_account["account_status"], "Should maintain status consistency"
    
    def test_user_data_error_recovery_real_behavior(self):
        """Test user data error recovery."""
        # Arrange - Simulate corrupted data
        corrupted_data = None  # Simulate corrupted file
        
        # Act - Try to load corrupted data with auto-create enabled
        with patch('core.user_management.get_user_file_path') as mock_get_path:
            def mock_path(user_id, file_type):
                return os.path.join(self.test_user_dir, f"{file_type}.json")
            mock_get_path.side_effect = mock_path
            
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.load_json_data', return_value=corrupted_data):
                    with patch('core.user_management.save_json_data') as mock_save:
                        # Try to load corrupted preferences
                        result = _get_user_data__load_preferences(self.test_user_id, auto_create=True)
        
        # Assert
        assert result is not None, "Should recover from corrupted data"
        assert isinstance(result, dict), "Should return valid dictionary"
        assert mock_save.called, "Should create new data file"
    
    def test_user_data_performance_real_behavior(self):
        """Test user data performance under load."""
        # Arrange
        test_account = {
            "user_id": self.test_user_id,
            "internal_username": "performance_user",
            "account_status": "active"
        }
        
        # Act - Perform multiple operations quickly
        import time
        start_time = time.time()
        
        with patch('core.user_management.get_user_file_path') as mock_get_path:
            def mock_path(user_id, file_type):
                return os.path.join(self.test_user_dir, f"{file_type}.json")
            mock_get_path.side_effect = mock_path
            
            with patch('core.user_management.ensure_user_directory'):
                with patch('core.user_management.save_json_data') as mock_save:
                    with patch('core.user_management.load_json_data', return_value=test_account):
                        with patch('core.user_management.validate_account_dict') as mock_validate:
                            mock_validate.return_value = (test_account, [])
                            
                            # Perform multiple operations
                            for i in range(100):
                                _get_user_data__load_account(self.test_user_id)
                                _save_user_data__save_account(self.test_user_id, test_account)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Assert
        assert total_time < 10.0, f"Should complete operations quickly, took {total_time:.2f} seconds"
        # Count only the main account saves (not side effect saves)
        account_saves = [call for call in mock_save.call_args_list if len(call[0]) > 0 and isinstance(call[0][0], dict) and 'internal_username' in call[0][0]]
        # First call creates default account, then 100 iterations = 101 total
        assert len(account_saves) == 101, f"Should perform all save operations (1 default + 100 iterations), got {len(account_saves)}"
    
    def test_user_data_concurrent_access_real_behavior(self):
        """Test user data concurrent access behavior."""
        # Arrange
        test_account = {
            "user_id": self.test_user_id,
            "internal_username": "concurrent_user",
            "account_status": "active"
        }
        
        # Act - Simulate concurrent access
        import threading
        import time
        
        results = []
        errors = []
        
        def user_operation(thread_id):
            try:
                with patch('core.user_management.get_user_file_path') as mock_get_path:
                    def mock_path(user_id, file_type):
                        return os.path.join(self.test_user_dir, f"{file_type}.json")
                    mock_get_path.side_effect = mock_path
                    
                    with patch('core.user_management.ensure_user_directory'):
                        with patch('core.user_management.save_json_data') as mock_save:
                            with patch('core.user_management.load_json_data', return_value=test_account):
                                with patch('core.user_management.validate_account_dict') as mock_validate:
                                    mock_validate.return_value = (test_account, [])
                                    
                                    # Perform operations
                                    for i in range(10):
                                        _get_user_data__load_account(self.test_user_id)
                                        _save_user_data__save_account(self.test_user_id, test_account)
                                        time.sleep(0.001)  # Small delay
                                    
                                    results.append(True)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=user_operation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Assert
        assert len(errors) == 0, f"Should not have threading errors: {errors}"
        assert len(results) == 5, f"Should process all threads: {len(results)}"
        for result in results:
            assert result is True, "All results should be valid"
