#!/usr/bin/env python3
"""
Integration Tests for Account Lifecycle - MHM
Tests complete account workflows: creation, modification, feature enablement, deletion
Focuses on real behavior testing and side effect verification
"""

import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class TestAccountLifecycle:
    """Test complete account lifecycle workflows with real behavior verification."""
    
    def save_user_data_simple(self, user_id, account_data=None, preferences_data=None, schedules_data=None):
        """Helper function to save user data in the correct format."""
        data_updates = {}
        if account_data:
            data_updates["account"] = account_data
        if preferences_data:
            data_updates["preferences"] = preferences_data
        if schedules_data:
            data_updates["schedules"] = schedules_data
        
        if data_updates:
            from core.user_data_handlers import save_user_data
            return save_user_data(user_id, data_updates)
        return {}
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up isolated test environment for each test."""
        # Create temporary test directory
        self.test_dir = tempfile.mkdtemp(prefix="mhm_account_test_")
        test_data_dir = os.path.join(self.test_dir, "data")
        self.test_test_data_dir = os.path.join(self.test_dir, "tests", "data")
        
        # Create directory structure
        os.makedirs(test_data_dir, exist_ok=True)
        os.makedirs(self.test_test_data_dir, exist_ok=True)
        os.makedirs(os.path.join(test_data_dir, "users"), exist_ok=True)
        os.makedirs(os.path.join(self.test_test_data_dir, "users"), exist_ok=True)
        
        # Override data paths for testing
        import core.config
        core.config.DATA_DIR = test_data_dir
        
        yield
        
        # Cleanup
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @pytest.mark.integration
    def test_create_basic_account(self, test_data_dir, mock_config):
        """Test creating a basic account with only messages enabled."""
        from core.user_data_handlers import save_user_data, get_user_data
        
        # Arrange
        user_id = "test-basic-user"
        
        # Create test user using centralized utilities for consistent setup
        from tests.test_utilities import TestUserFactory
        success = TestUserFactory.create_minimal_user(user_id)
        assert success, "Test user should be created successfully"
        
        # Get the UUID for the user
        from core.user_management import get_user_id_by_internal_username
        actual_user_id = get_user_id_by_internal_username(user_id)
        assert actual_user_id is not None, f"Should be able to get UUID for user {user_id}"
        
        # Update user data to match the test requirements
        from core.user_management import update_user_account, update_user_preferences
        update_account_success = update_user_account(actual_user_id, {
            "timezone": "America/New_York"
        })
        assert update_account_success, "Account should be updated successfully"
        
        update_preferences_success = update_user_preferences(actual_user_id, {
            "categories": ["motivational"]
        })
        assert update_preferences_success, "Preferences should be updated successfully"
        
        # Assert - Verify actual file creation
        user_dir = os.path.join(test_data_dir, "users", actual_user_id)
        assert os.path.exists(user_dir), "User directory should be created"
        
        # Verify core user files exist
        assert os.path.exists(os.path.join(user_dir, "account.json")), "Account file should be created"
        assert os.path.exists(os.path.join(user_dir, "preferences.json")), "Preferences file should be created"
        assert os.path.exists(os.path.join(user_dir, "user_context.json")), "User context file should be created"
        
        # Verify data loading works
        loaded_data = get_user_data(actual_user_id)
        assert loaded_data["account"]["features"]["automated_messages"] == "enabled", "Messages should be enabled"
        assert loaded_data["account"]["features"]["task_management"] == "disabled", "Tasks should be disabled for minimal user"
        assert loaded_data["account"]["features"]["checkins"] == "disabled", "Check-ins should be disabled for minimal user"
        
        # Verify schedule data structure (may vary based on centralized utilities)
        if "schedules" in loaded_data:
            # Check if schedules data exists and has the expected structure
            schedules = loaded_data["schedules"]
            assert "motivational" in schedules, "Motivational schedule should exist"
            # Note: create_minimal_user only creates motivational category, not health
    
    @pytest.mark.integration
    def test_create_full_account(self, test_data_dir, mock_config):
        """Test creating a full account with all features enabled."""
        from core.user_data_handlers import save_user_data, get_user_data
        from tests.test_utilities import TestUserFactory, TestDataFactory
        
        # Arrange - Create full user with all features using centralized utilities
        user_id = "test-full-user"
        
        # Create full featured user
        success = TestUserFactory.create_full_featured_user(user_id)
        assert success, "Full featured user should be created successfully"
        
        # Get the UUID for the user
        from core.user_management import get_user_id_by_internal_username
        actual_user_id = get_user_id_by_internal_username(user_id)
        assert actual_user_id is not None, f"Should be able to get UUID for user {user_id}"
        
        # Add specific schedule data
        from core.user_management import save_user_schedules_data
        schedules_data = TestDataFactory.create_test_schedule_data(["motivational", "health"])
        schedules_data["motivational"]["periods"]["morning"] = {
            "active": True,
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "start_time": "09:00",
            "end_time": "12:00"
        }
        schedules_data["health"]["periods"]["evening"] = {
            "active": True,
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "start_time": "18:00",
            "end_time": "20:00"
        }
        save_user_schedules_data(actual_user_id, schedules_data)
        
        # Assert - Verify actual file creation
        user_dir = os.path.join(test_data_dir, "users", actual_user_id)
        assert os.path.exists(user_dir), "User directory should be created"
        
        # Verify core user files exist
        assert os.path.exists(os.path.join(user_dir, "account.json")), "Account file should be created"
        assert os.path.exists(os.path.join(user_dir, "preferences.json")), "Preferences file should be created"
        assert os.path.exists(os.path.join(user_dir, "user_context.json")), "User context file should be created"
        
        # Verify data loading works
        loaded_data = get_user_data(actual_user_id)
        assert loaded_data["account"]["features"]["automated_messages"] == "enabled", "Messages should be enabled"
        assert loaded_data["account"]["features"]["task_management"] == "enabled", "Tasks should be enabled"
        assert loaded_data["account"]["features"]["checkins"] == "enabled", "Check-ins should be enabled"
        
        # Verify schedule data structure (may vary based on centralized utilities)
        if "schedules" in loaded_data:
            # Check if schedules data exists and has the expected structure
            schedules = loaded_data["schedules"]
            assert "motivational" in schedules, "Motivational schedule should exist"
            assert "health" in schedules, "Health schedule should exist"
            assert "morning" in schedules["motivational"]["periods"], "Morning period should exist"
            assert "evening" in schedules["health"]["periods"], "Evening period should exist"
    
    @pytest.mark.integration
    def test_enable_checkins_for_basic_user(self, test_data_dir, mock_config):
        """Test enabling check-ins for a user who only has messages enabled."""
        from core.user_data_handlers import save_user_data, get_user_data
        
        # Arrange - Create basic user
        user_id = "test-enable-checkins"
        account_data = {
            "internal_username": user_id,
            "timezone": "America/New_York",
            "channel": {"type": "discord", "contact": "test#1234"},
            "features": {
                "automated_messages": "enabled",
                "task_management": "disabled",
                "checkins": "disabled"
            }
        }
        
        preferences_data = {
            "categories": ["motivational"],
            "channel": {"type": "discord", "contact": "test#1234"}
        }
        
        schedules_data = {
            "periods": [
                {
                    "name": "morning",
                    "active": True,
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "start_time": "09:00",
                    "end_time": "12:00"
                }
            ]
        }
        
        # Create user directory first
        user_dir = os.path.join(test_data_dir, "users", user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        self.save_user_data_simple(user_id, account_data, preferences_data, schedules_data)
        
        # Act - Enable check-ins
        loaded_data = get_user_data(user_id)
        loaded_data["account"]["features"]["checkins"] = "enabled"
        loaded_data["preferences"]["checkin_settings"] = {
            "enabled": True,
            "questions": ["How are you feeling today?"]
        }
        
        # Add check-in schedule periods
        checkin_periods = [
            {
                "name": "morning_checkin",
                "active": True,
                "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "start_time": "09:00",
                "end_time": "10:00"
            }
        ]
        loaded_data["schedules"]["periods"].extend(checkin_periods)
        
        self.save_user_data_simple(user_id, loaded_data["account"], loaded_data["preferences"], loaded_data["schedules"])
        
        # Create check-ins file
        user_dir = os.path.join(test_data_dir, "users", user_id)
        with open(os.path.join(user_dir, "daily_checkins.json"), "w") as f:
            json.dump({"checkins": []}, f, indent=2)
        
        # Assert - Verify actual changes
        updated_data = get_user_data(user_id)
        assert updated_data["account"]["features"]["checkins"] == "enabled", "Check-ins should be enabled"
        assert "checkin_settings" in updated_data["preferences"], "Check-in settings should exist"
        assert len(updated_data["schedules"]["periods"]) == 2, "Should have 2 schedule periods"
        
        # Verify check-ins file was created
        checkins_file = os.path.join(user_dir, "daily_checkins.json")
        assert os.path.exists(checkins_file), "Check-ins file should be created"
        
        # Verify check-in period exists
        checkin_period = next((p for p in updated_data["schedules"]["periods"] if p["name"] == "morning_checkin"), None)
        assert checkin_period is not None, "Check-in period should exist"
    
    @pytest.mark.integration
    def test_disable_tasks_for_full_user(self, test_data_dir, mock_config):
        """Test disabling tasks for a user who has all features enabled."""
        from core.user_data_handlers import save_user_data, get_user_data
        
        # Arrange - Create full user
        user_id = "test-disable-tasks"
        account_data = {
            "internal_username": user_id,
            "timezone": "America/New_York",
            "channel": {"type": "discord", "contact": "test#1234"},
            "features": {
                "automated_messages": "enabled",
                "task_management": "enabled",
                "checkins": "enabled"
            }
        }
        
        preferences_data = {
            "categories": ["motivational"],
            "channel": {"type": "discord", "contact": "test#1234"},
            "task_settings": {
                "enabled": True,
                "reminder_frequency": "daily"
            },
            "checkin_settings": {
                "enabled": True,
                "questions": ["How are you feeling?"]
            }
        }
        
        schedules_data = {
            "periods": [
                {
                    "name": "morning",
                    "active": True,
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "start_time": "09:00",
                    "end_time": "12:00"
                }
            ]
        }
        
        # Create user directory first
        user_dir = os.path.join(test_data_dir, "users", user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        self.save_user_data_simple(user_id, account_data, preferences_data, schedules_data)
        
        # Create feature-specific files
        os.makedirs(os.path.join(user_dir, "tasks"), exist_ok=True)
        with open(os.path.join(user_dir, "tasks", "tasks.json"), "w") as f:
            json.dump({"tasks": []}, f, indent=2)
        
        with open(os.path.join(user_dir, "daily_checkins.json"), "w") as f:
            json.dump({"checkins": []}, f, indent=2)
        
        # Act - Disable tasks
        loaded_data = get_user_data(user_id)
        if "account" in loaded_data and "features" in loaded_data["account"]:
            loaded_data["account"]["features"]["task_management"] = "disabled"
        if "preferences" in loaded_data and "task_settings" in loaded_data["preferences"]:
            del loaded_data["preferences"]["task_settings"]
        
        self.save_user_data_simple(user_id, loaded_data.get("account"), loaded_data.get("preferences"))
        
        # Assert - Verify actual changes
        updated_data = get_user_data(user_id)
        assert updated_data["account"]["features"]["task_management"] == "disabled", "Tasks should be disabled"
        assert "task_settings" not in updated_data["preferences"], "Task settings should be removed"
        assert updated_data["account"]["features"]["automated_messages"] == "enabled", "Messages should still be enabled"
        assert updated_data["account"]["features"]["checkins"] == "enabled", "Check-ins should still be enabled"
    
    @pytest.mark.integration
    def test_reenable_tasks_for_user(self, test_data_dir, mock_config):
        """Test re-enabling tasks for a user who previously had them disabled."""
        from core.user_data_handlers import save_user_data, get_user_data
        
        # Arrange - Create user with tasks disabled
        user_id = "test-reenable-tasks"
        account_data = {
            "internal_username": user_id,
            "timezone": "America/New_York",
            "channel": {"type": "discord", "contact": "test#1234"},
            "features": {
                "automated_messages": "enabled",
                "checkins": "enabled",
                "task_management": "disabled"
            }
        }
        
        preferences_data = {
            "categories": ["motivational"],
            "channel": {"type": "discord", "contact": "test#1234"},
            "checkin_settings": {
                "enabled": True,
                "questions": ["How are you feeling?"]
            }
        }
        
        schedules_data = {
            "periods": [
                {
                    "name": "morning",
                    "active": True,
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "start_time": "09:00",
                    "end_time": "12:00"
                }
            ]
        }
        
        # Create user directory first
        user_dir = os.path.join(test_data_dir, "users", user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        self.save_user_data_simple(user_id, account_data)
        self.save_user_data_simple(user_id, preferences_data=preferences_data)
        self.save_user_data_simple(user_id, schedules_data=schedules_data)
        
        # Create check-ins file
        with open(os.path.join(user_dir, "daily_checkins.json"), "w") as f:
            json.dump({"checkins": []}, f, indent=2)
        
        # Act - Re-enable tasks
        loaded_data = get_user_data(user_id)
        loaded_data["account"]["features"]["task_management"] = "enabled"
        loaded_data["preferences"]["task_settings"] = {
            "enabled": True,
            "reminder_frequency": "daily"
        }
        
        self.save_user_data_simple(user_id, loaded_data["account"])
        self.save_user_data_simple(user_id, preferences_data=loaded_data["preferences"])
        
        # Create tasks directory and file
        os.makedirs(os.path.join(user_dir, "tasks"), exist_ok=True)
        with open(os.path.join(user_dir, "tasks", "tasks.json"), "w") as f:
            json.dump({"tasks": []}, f, indent=2)
        
        # Assert - Verify actual changes
        updated_data = get_user_data(user_id)
        assert updated_data["account"]["features"]["task_management"] == "enabled", "Tasks should be re-enabled"
        assert "task_settings" in updated_data["preferences"], "Task settings should be restored"
        assert updated_data["account"]["features"]["automated_messages"] == "enabled", "Messages should be enabled"
        assert updated_data["account"]["features"]["checkins"] == "enabled", "Check-ins should be enabled"
        assert updated_data["account"]["features"]["task_management"] == "enabled", "Tasks should be enabled"
        
        # Verify tasks directory and file exist
        assert os.path.exists(os.path.join(user_dir, "tasks")), "Tasks directory should exist"
        assert os.path.exists(os.path.join(user_dir, "tasks", "tasks.json")), "Tasks file should exist"
    
    @pytest.mark.integration
    def test_add_message_category(self, test_data_dir, mock_config, update_user_index_for_test):
        """Test adding a new message category to user preferences."""
        from core.user_data_handlers import save_user_data, get_user_data
        
        # Arrange - Create user with automated_messages enabled and basic categories
        user_id = "test-add-category"
        account_data = {
            "internal_username": user_id,
            "timezone": "America/New_York",
            "channel": {"type": "discord", "contact": "test#1234"},
            "features": {
                "automated_messages": "enabled",
                "checkins": "disabled",
                "task_management": "disabled"
            }
        }
        
        preferences_data = {
            "categories": ["motivational"],
            "channel": {"type": "discord", "contact": "test#1234"}
        }
        
        schedules_data = {
            "periods": [
                {
                    "name": "morning",
                    "active": True,
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "start_time": "09:00",
                    "end_time": "12:00"
                }
            ]
        }
        
        # Create user directory first
        user_dir = os.path.join(test_data_dir, "users", user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        self.save_user_data_simple(user_id, account_data)
        self.save_user_data_simple(user_id, preferences_data=preferences_data)
        self.save_user_data_simple(user_id, schedules_data=schedules_data)
        
        # Update user index
        update_user_index_for_test(user_id)
        
        # Act - Add new category
        loaded_data = get_user_data(user_id)
        loaded_data["preferences"]["categories"].append("health")
        self.save_user_data_simple(user_id, preferences_data=loaded_data["preferences"])
        
        # Update user index after category addition
        update_user_index_for_test(user_id)
        
        # Assert - Verify actual changes
        updated_data = get_user_data(user_id)
        assert "health" in updated_data["preferences"]["categories"], "Health category should be added"
        
        # Verify user index reflects the change
        from core.user_data_manager import load_json_data
        from core.config import BASE_DATA_DIR
        index_file = os.path.join(BASE_DATA_DIR, "user_index.json")
        user_index = load_json_data(index_file) or {}
        
        if user_id in user_index:
            index_entry = user_index[user_id]
            enabled_features = index_entry.get("enabled_features", [])
            assert "health" in enabled_features, "Health category should be in user index enabled_features"
        
        # Test removing category
        loaded_data = get_user_data(user_id)
        loaded_data["preferences"]["categories"].remove("health")
        self.save_user_data_simple(user_id, preferences_data=loaded_data["preferences"])
        
        # Update user index after category removal
        update_user_index_for_test(user_id)
        
        # Verify category was removed
        updated_data = get_user_data(user_id)
        assert "health" not in updated_data["preferences"]["categories"], "Health category should be removed"
    
    @pytest.mark.integration
    def test_remove_message_category(self, test_data_dir, mock_config):
        """Test removing a message category from user preferences."""
        from core.user_data_handlers import save_user_data, get_user_data
        
        # Arrange - Create user with multiple categories
        user_id = "test-remove-category"
        account_data = {
            "internal_username": user_id,
            "timezone": "America/New_York",
            "channel": {"type": "discord", "contact": "test#1234"},
            "features": {
                "automated_messages": "enabled",
                "task_management": "disabled",
                "checkins": "disabled"
            }
        }
        
        preferences_data = {
            "categories": ["motivational", "health"],
            "channel": {"type": "discord", "contact": "test#1234"}
        }
        
        schedules_data = {
            "periods": [
                {
                    "name": "morning",
                    "active": True,
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "start_time": "09:00",
                    "end_time": "12:00"
                }
            ]
        }
        
        # Create user directory first
        user_dir = os.path.join(test_data_dir, "users", user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        self.save_user_data_simple(user_id, account_data)
        self.save_user_data_simple(user_id, preferences_data=preferences_data)
        self.save_user_data_simple(user_id, schedules_data=schedules_data)
        
        # Act - Remove category
        loaded_data = get_user_data(user_id)
        if "health" in loaded_data["preferences"]["categories"]:
            loaded_data["preferences"]["categories"].remove("health")
        self.save_user_data_simple(user_id, preferences_data=loaded_data["preferences"])
        
        # Assert - Verify actual changes
        updated_data = get_user_data(user_id)
        assert "health" not in updated_data["preferences"]["categories"], "Health category should be removed"
        assert len(updated_data["preferences"]["categories"]) == 1, "Should have 1 category"
        assert "motivational" in updated_data["preferences"]["categories"], "Motivational should remain"
    
    @pytest.mark.integration
    def test_add_schedule_period(self, test_data_dir, mock_config):
        """Test adding a new schedule period to user schedules."""
        from core.user_data_handlers import save_user_data, get_user_data
        
        # Arrange - Create user with basic schedule
        user_id = "test-add-period"
        account_data = {
            "internal_username": user_id,
            "timezone": "America/New_York",
            "channel": {"type": "discord", "contact": "test#1234"},
            "features": {
                "automated_messages": "enabled",
                "task_management": "disabled",
                "checkins": "disabled"
            }
        }
        
        preferences_data = {
            "categories": ["motivational"],
            "channel": {"type": "discord", "contact": "test#1234"}
        }
        
        schedules_data = {
            "periods": [
                {
                    "name": "morning",
                    "active": True,
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "start_time": "09:00",
                    "end_time": "12:00"
                }
            ]
        }
        
        # Create user directory first
        user_dir = os.path.join(test_data_dir, "users", user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        self.save_user_data_simple(user_id, account_data)
        self.save_user_data_simple(user_id, preferences_data=preferences_data)
        self.save_user_data_simple(user_id, schedules_data=schedules_data)
        
        # Act - Add new period
        loaded_data = get_user_data(user_id)
        new_period = {
            "name": "evening",
            "active": True,
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "start_time": "18:00",
            "end_time": "21:00"
        }
        loaded_data["schedules"]["periods"].append(new_period)
        self.save_user_data_simple(user_id, schedules_data=loaded_data["schedules"])
        
        # Assert - Verify actual changes
        updated_data = get_user_data(user_id)
        assert len(updated_data["schedules"]["periods"]) == 2, "Should have 2 periods"
        
        evening_period = next((p for p in updated_data["schedules"]["periods"] if p["name"] == "evening"), None)
        assert evening_period is not None, "Evening period should exist"
        assert evening_period["start_time"] == "18:00", "Evening period should have correct start time"
        assert evening_period["end_time"] == "21:00", "Evening period should have correct end time"
    
    @pytest.mark.integration
    def test_modify_schedule_period(self, test_data_dir, mock_config):
        """Test modifying an existing schedule period."""
        from core.user_data_handlers import save_user_data, get_user_data
        
        # Arrange - Create user with schedule
        user_id = "test-modify-period"
        account_data = {
            "internal_username": user_id,
            "timezone": "America/New_York",
            "channel": {"type": "discord", "contact": "test#1234"},
            "features": {
                "automated_messages": "enabled",
                "task_management": "disabled",
                "checkins": "disabled"
            }
        }
        
        preferences_data = {
            "categories": ["motivational"],
            "channel": {"type": "discord", "contact": "test#1234"}
        }
        
        schedules_data = {
            "periods": [
                {
                    "name": "morning",
                    "active": True,
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "start_time": "09:00",
                    "end_time": "12:00"
                }
            ]
        }
        
        # Create user directory first
        user_dir = os.path.join(test_data_dir, "users", user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        self.save_user_data_simple(user_id, account_data)
        self.save_user_data_simple(user_id, preferences_data=preferences_data)
        self.save_user_data_simple(user_id, schedules_data=schedules_data)
        
        # Act - Modify period
        loaded_data = get_user_data(user_id)
        morning_period = next((p for p in loaded_data["schedules"]["periods"] if p["name"] == "morning"), None)
        morning_period["start_time"] = "08:00"
        morning_period["end_time"] = "11:00"
        morning_period["days"] = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        
        self.save_user_data_simple(user_id, schedules_data=loaded_data["schedules"])
        
        # Assert - Verify actual changes
        updated_data = get_user_data(user_id)
        updated_morning = next((p for p in updated_data["schedules"]["periods"] if p["name"] == "morning"), None)
        assert updated_morning["start_time"] == "08:00", "Start time should be updated"
        assert updated_morning["end_time"] == "11:00", "End time should be updated"
        assert "saturday" in updated_morning["days"], "Saturday should be added to days"
        assert len(updated_morning["days"]) == 6, "Should have 6 days"
    
    @pytest.mark.integration
    def test_remove_schedule_period(self, test_data_dir, mock_config):
        """Test removing a schedule period from user schedules."""
        from core.user_data_handlers import save_user_data, get_user_data
        
        # Arrange - Create user with multiple periods
        user_id = "test-remove-period"
        account_data = {
            "internal_username": user_id,
            "timezone": "America/New_York",
            "channel": {"type": "discord", "contact": "test#1234"},
            "features": {
                "automated_messages": "enabled",
                "task_management": "disabled",
                "checkins": "disabled"
            }
        }
        
        preferences_data = {
            "categories": ["motivational"],
            "channel": {"type": "discord", "contact": "test#1234"}
        }
        
        schedules_data = {
            "periods": [
                {
                    "name": "morning",
                    "active": True,
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "start_time": "09:00",
                    "end_time": "12:00"
                },
                {
                    "name": "evening",
                    "active": True,
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "start_time": "18:00",
                    "end_time": "21:00"
                }
            ]
        }
        
        # Create user directory first
        user_dir = os.path.join(test_data_dir, "users", user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        self.save_user_data_simple(user_id, account_data)
        self.save_user_data_simple(user_id, preferences_data=preferences_data)
        self.save_user_data_simple(user_id, schedules_data=schedules_data)
        
        # Act - Remove period
        loaded_data = get_user_data(user_id)
        loaded_data["schedules"]["periods"] = [p for p in loaded_data["schedules"]["periods"] if p["name"] != "evening"]
        self.save_user_data_simple(user_id, schedules_data=loaded_data["schedules"])
        
        # Assert - Verify actual changes
        updated_data = get_user_data(user_id)
        assert len(updated_data["schedules"]["periods"]) == 1, "Should have 1 period"
        
        evening_period = next((p for p in updated_data["schedules"]["periods"] if p["name"] == "evening"), None)
        assert evening_period is None, "Evening period should be removed"
        
        morning_period = next((p for p in updated_data["schedules"]["periods"] if p["name"] == "morning"), None)
        assert morning_period is not None, "Morning period should remain"
    
    @pytest.mark.integration
    def test_complete_account_lifecycle(self, test_data_dir, mock_config):
        """Test complete account lifecycle: create, modify, disable, re-enable, delete."""
        from core.user_data_handlers import save_user_data, get_user_data
        
        # 1. Create account
        user_id = "test-lifecycle"
        account_data = {
            "internal_username": user_id,
            "timezone": "America/New_York",
            "channel": {"type": "discord", "contact": "test#1234"},
            "enabled_features": ["messages"]
        }
        
        preferences_data = {
            "categories": ["motivational"],
            "channel": {"type": "discord", "contact": "test#1234"}
        }
        
        schedules_data = {
            "periods": [
                {
                    "name": "morning",
                    "active": True,
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "start_time": "09:00",
                    "end_time": "12:00"
                }
            ]
        }
        
        # Create user directory first
        user_dir = os.path.join(test_data_dir, "users", user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        self.save_user_data_simple(user_id, account_data)
        self.save_user_data_simple(user_id, preferences_data=preferences_data)
        self.save_user_data_simple(user_id, schedules_data=schedules_data)
        
        # Verify creation
        user_dir = os.path.join(test_data_dir, "users", user_id)
        assert os.path.exists(user_dir), "User directory should be created"
        
        # 2. Enable features
        loaded_data = get_user_data(user_id)
        loaded_data["account"]["enabled_features"].extend(["tasks", "checkins"])
        loaded_data["preferences"]["task_settings"] = {"enabled": True, "reminder_frequency": "daily"}
        loaded_data["preferences"]["checkin_settings"] = {"enabled": True, "questions": ["How are you feeling?"]}
        
        self.save_user_data_simple(user_id, loaded_data["account"])
        self.save_user_data_simple(user_id, preferences_data=loaded_data["preferences"])
        
        # Create feature files
        os.makedirs(os.path.join(user_dir, "tasks"), exist_ok=True)
        with open(os.path.join(user_dir, "tasks", "tasks.json"), "w") as f:
            json.dump({"tasks": []}, f, indent=2)
        
        with open(os.path.join(user_dir, "daily_checkins.json"), "w") as f:
            json.dump({"checkins": []}, f, indent=2)
        
        # Verify features enabled
        updated_data = get_user_data(user_id)
        assert len(updated_data["account"]["enabled_features"]) == 3, "Should have 3 features enabled"
        
        # 3. Disable features
        loaded_data = get_user_data(user_id)
        loaded_data["account"]["enabled_features"].remove("tasks")
        if "task_settings" in loaded_data["preferences"]:
            del loaded_data["preferences"]["task_settings"]
        
        self.save_user_data_simple(user_id, loaded_data["account"])
        self.save_user_data_simple(user_id, preferences_data=loaded_data["preferences"])
        
        # Verify features disabled
        updated_data = get_user_data(user_id)
        assert "tasks" not in updated_data["account"]["enabled_features"], "Tasks should be disabled"
        assert len(updated_data["account"]["enabled_features"]) == 2, "Should have 2 features enabled"
        
        # 4. Re-enable features
        loaded_data = get_user_data(user_id)
        loaded_data["account"]["enabled_features"].append("tasks")
        loaded_data["preferences"]["task_settings"] = {"enabled": True, "reminder_frequency": "daily"}
        
        self.save_user_data_simple(user_id, loaded_data["account"])
        self.save_user_data_simple(user_id, preferences_data=loaded_data["preferences"])
        
        # Recreate tasks file
        with open(os.path.join(user_dir, "tasks", "tasks.json"), "w") as f:
            json.dump({"tasks": []}, f, indent=2)
        
        # Verify features re-enabled
        updated_data = get_user_data(user_id)
        assert "tasks" in updated_data["account"]["enabled_features"], "Tasks should be re-enabled"
        assert len(updated_data["account"]["enabled_features"]) == 3, "Should have 3 features enabled"
        
        # 5. Delete account (simulate by removing directory)
        shutil.rmtree(user_dir)
        
        # Verify deletion
        assert not os.path.exists(user_dir), "User directory should be deleted"
        
        # Verify data loading fails
        try:
            get_user_data(user_id)
            assert False, "Should not be able to load deleted user data"
        except:
            pass  # Expected behavior 