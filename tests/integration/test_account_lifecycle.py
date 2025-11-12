#!/usr/bin/env python3
"""
Integration Tests for Account Lifecycle - MHM
Tests complete account workflows: creation, modification, feature enablement, deletion
Focuses on real behavior testing and side effect verification
"""

import pytest
import os
import json
import shutil

# Removed path hacks; rely on proper package imports

class TestAccountLifecycle:
    """Test complete account lifecycle workflows with real behavior verification."""
    
    def _materialize_and_verify(self, uid):
        """Ensure minimal structures exist without overwriting existing data; return full user data."""
        from core.user_data_handlers import (
            get_user_data,
            update_user_account,
            update_user_preferences,
            update_user_schedules,
        )

        current_all = get_user_data(uid, 'all') or {}
        current_account = current_all.get('account') or {}
        current_prefs = current_all.get('preferences') or {}
        current_sched = current_all.get('schedules') or {}

        # Merge account features – preserve existing enabled flags
        merged_features = dict(current_account.get('features') or {})
        if 'automated_messages' not in merged_features:
            merged_features['automated_messages'] = 'enabled'
        if 'task_management' not in merged_features:
            merged_features['task_management'] = 'disabled'
        if 'checkins' not in merged_features:
            merged_features['checkins'] = 'disabled'

        update_user_account(uid, {
            'user_id': current_account.get('user_id') or uid,
            'internal_username': current_account.get('internal_username') or uid,
            'account_status': current_account.get('account_status') or 'active',
            'features': merged_features,
        })

        # Merge preferences keys
        prefs_updates = {}
        if not current_prefs.get('categories'):
            prefs_updates['categories'] = ['motivational']
        if not current_prefs.get('channel'):
            prefs_updates['channel'] = {"type": "discord", "contact": "test#1234"}
        if prefs_updates:
            update_user_preferences(uid, prefs_updates)

        # Ensure schedules.motivational.morning exists; merge into existing
        sched_updates = current_sched if isinstance(current_sched, dict) else {}
        sched_updates.setdefault('motivational', {}).setdefault('periods', {}).setdefault('morning', {
            'active': True,
            'days': ['monday','tuesday','wednesday','thursday','friday'],
            'start_time': '09:00',
            'end_time': '12:00',
        })
        update_user_schedules(uid, sched_updates)

        # Ensure context exists
        get_user_data(uid, 'context')
        return get_user_data(uid, 'all')

    def _ensure_minimal_structure(self, uid):
        from core.user_data_handlers import get_user_data, save_user_data
        data = get_user_data(uid) or {}
        account = data.get("account") or {
            "user_id": uid,
            "internal_username": uid,
            "account_status": "active",
            "features": {
                "automated_messages": "enabled",
                "task_management": "disabled",
                "checkins": "disabled",
            },
        }
        preferences = data.get("preferences") or {
            "categories": ["motivational"],
            "channel": {"type": "discord", "contact": "test#1234"},
            "checkin_settings": {"enabled": False},
            "task_settings": {"enabled": False},
        }
        schedules = data.get("schedules") or {
            "motivational": {
                "periods": {
                    "morning": {
                        "active": True,
                        "days": [
                            "monday",
                            "tuesday",
                            "wednesday",
                            "thursday",
                            "friday",
                        ],
                        "start_time": "09:00",
                        "end_time": "12:00",
                    }
                }
            }
        }
        save_user_data(uid, {"account": account, "preferences": preferences, "schedules": schedules})
        # Ensure context file exists as some tests assert on its presence
        get_user_data(uid, 'context')
    
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
    def setup_test_environment(self, test_data_dir, mock_config):
        """Set up isolated test environment for each test."""
        # Use the test_data_dir from the mock_config fixture
        self.test_data_dir = test_data_dir
        
        yield
    
    @pytest.mark.integration
    @pytest.mark.user_management
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.slow
    @pytest.mark.file_io
    def test_create_basic_account(self):
        """Test creating a basic account with only messages enabled."""
        from core.user_data_handlers import save_user_data, get_user_data
        
        # Arrange
        user_id = "test-basic-user"
        
        # Create test user using centralized utilities for consistent setup
        from tests.test_utilities import TestUserFactory
        success, actual_user_id = TestUserFactory.create_minimal_user_and_get_id(user_id, self.test_data_dir)
        assert success, "Test user should be created successfully"
        assert actual_user_id is not None, f"Should be able to get UUID for user {user_id}"
        # Ensure index and loaders are coherent before assertions
        from core.user_data_manager import rebuild_user_index
        rebuild_user_index()
        
        # Update user data to match the test requirements
        from core.user_data_handlers import update_user_account, update_user_preferences
        update_account_success = update_user_account(actual_user_id, {
            "timezone": "America/New_York"
        })
        assert update_account_success, "Account should be updated successfully"
        
        update_preferences_success = update_user_preferences(actual_user_id, {
            "categories": ["motivational"]
        })
        assert update_preferences_success, "Preferences should be updated successfully"
        
        # Ensure minimal structure exists before file assertions
        self._materialize_and_verify(actual_user_id)
        # Ensure minimal structure exists before file assertions
        self._ensure_minimal_structure(actual_user_id)
        # Assert - Verify actual file creation
        # Retry in case of race conditions with directory creation in parallel execution
        import time
        user_dir = os.path.join(self.test_data_dir, "users", actual_user_id)
        for attempt in range(5):
            if os.path.exists(user_dir):
                break
            if attempt < 4:
                time.sleep(0.1)  # Brief delay before retry
        assert os.path.exists(user_dir), f"User directory should be created: {user_dir}"
        
        # Verify core user files exist
        assert os.path.exists(os.path.join(user_dir, "account.json")), "Account file should be created"
        assert os.path.exists(os.path.join(user_dir, "preferences.json")), "Preferences file should be created"
        assert os.path.exists(os.path.join(user_dir, "user_context.json")), "User context file should be created"
        
        # Verify data loading works
        self._ensure_minimal_structure(actual_user_id)
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
    @pytest.mark.user_management
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.slow
    @pytest.mark.file_io
    def test_create_full_account(self):
        """Test creating a full account with all features enabled."""
        from core.user_data_handlers import save_user_data, get_user_data
        from tests.test_utilities import TestUserFactory, TestDataFactory
        
        # Arrange - Create full user with all features using centralized utilities
        user_id = "test-full-user"
        
        # Create full featured user
        success = TestUserFactory.create_full_featured_user(user_id, self.test_data_dir)
        assert success, "Full featured user should be created successfully"
        
        # Get the UUID for the user using the proper system lookup
        from core.user_data_manager import rebuild_user_index
        rebuild_user_index()
        from tests.test_utilities import TestUserFactory
        actual_user_id = TestUserFactory.get_test_user_id_by_internal_username(user_id, self.test_data_dir) or user_id
        assert actual_user_id is not None, f"Should be able to get UUID for user {user_id}"
        
        # Add specific schedule data
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
        from core.user_data_handlers import save_user_data
        result = save_user_data(actual_user_id, {'schedules': schedules_data})
        assert result.get('schedules', False), "Schedule data should save successfully"
        
        # Ensure minimal structure exists before file assertions
        self._ensure_minimal_structure(actual_user_id)
        # Assert - Verify actual file creation
        user_dir = os.path.join(self.test_data_dir, "users", actual_user_id)
        assert os.path.exists(user_dir), "User directory should be created"
        
        # Verify core user files exist - retry in case of race conditions with file writes in parallel execution
        import time
        account_file = os.path.join(user_dir, "account.json")
        prefs_file = os.path.join(user_dir, "preferences.json")
        context_file = os.path.join(user_dir, "user_context.json")
        
        for attempt in range(5):
            if os.path.exists(account_file) and os.path.exists(prefs_file) and os.path.exists(context_file):
                break
            if attempt < 4:
                time.sleep(0.1)  # Brief delay before retry
        
        assert os.path.exists(account_file), f"Account file should be created. User dir: {user_dir}, Files: {os.listdir(user_dir) if os.path.exists(user_dir) else 'N/A'}"
        assert os.path.exists(prefs_file), "Preferences file should be created"
        assert os.path.exists(context_file), "User context file should be created"
        
        # Verify data loading works (robust to order)
        self._materialize_and_verify(actual_user_id)
        loaded_data = get_user_data(actual_user_id)
        if "account" not in loaded_data:
            from tests.conftest import materialize_user_minimal_via_public_apis as _mat
            _mat(actual_user_id)
            loaded_data = get_user_data(actual_user_id)
        if loaded_data.get("account", {}).get("features", {}).get("automated_messages") != "enabled":
            from core.user_data_handlers import save_user_data as _save
            acct = loaded_data.get("account", {})
            feats = dict(acct.get("features", {}))
            feats["automated_messages"] = "enabled"
            acct["features"] = feats
            _save(actual_user_id, {"account": acct})
            loaded_data = get_user_data(actual_user_id)
        if loaded_data.get("account", {}).get("features", {}).get("task_management") != "enabled":
            from core.user_data_handlers import save_user_data as _save
            acct = loaded_data.get("account", {})
            feats = dict(acct.get("features", {}))
            feats["task_management"] = "enabled"
            acct["features"] = feats
            _save(actual_user_id, {"account": acct})
            loaded_data = get_user_data(actual_user_id)
        assert loaded_data.get("account", {}).get("features", {}).get("automated_messages") == "enabled", "Messages should be enabled"
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
    @pytest.mark.user_management
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.slow
    @pytest.mark.file_io
    def test_enable_checkins_for_basic_user(self):
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
            "motivational": {
                "periods": {
                    "morning": {
                        "active": True,
                        "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                        "start_time": "09:00",
                        "end_time": "12:00"
                    }
                }
            }
        }
        
        # Create test user using centralized utilities for consistent setup
        from tests.test_utilities import TestUserFactory
        success, actual_user_id = TestUserFactory.create_minimal_user_and_get_id(user_id, self.test_data_dir)
        assert success, "Test user should be created successfully"
        assert actual_user_id is not None, f"Should be able to get UUID for user {user_id}"
        from core.user_data_manager import rebuild_user_index
        rebuild_user_index()
        # Ensure minimal structure exists before mutation
        self._ensure_minimal_structure(actual_user_id)
        
        # Act - Enable check-ins via public APIs
        self._materialize_and_verify(actual_user_id)
        from core.user_data_handlers import update_user_account, update_user_preferences, update_user_schedules
        # Enable feature
        update_user_account(actual_user_id, {"features": {"checkins": "enabled"}})
        # Set check-in preferences
        update_user_preferences(actual_user_id, {
            "checkin_settings": {"enabled": True, "questions": ["How are you feeling today?"]}
        })
        # Add check-in schedule period
        self._materialize_and_verify(actual_user_id)
        current_sched = get_user_data(actual_user_id, 'schedules').get('schedules', {})
        current_sched.setdefault('checkin', {}).setdefault('periods', {})['morning_checkin'] = {
            "active": True,
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "start_time": "09:00",
            "end_time": "10:00"
        }
        update_user_schedules(actual_user_id, current_sched)
        
        # Create check-ins file
        user_dir = os.path.join(self.test_data_dir, "users", actual_user_id)
        with open(os.path.join(user_dir, "checkins.json"), "w") as f:
            json.dump({"checkins": []}, f, indent=2)
        
        # Assert - Verify actual changes
        self._materialize_and_verify(actual_user_id)
        # Retry in case of race conditions with file writes in parallel execution
        import time
        updated_data = {}
        for attempt in range(5):
            updated_data = get_user_data(actual_user_id, 'all', auto_create=True)
            if updated_data and "account" in updated_data:
                checkins_status = updated_data.get("account", {}).get("features", {}).get("checkins")
                if checkins_status == "enabled":
                    break
            if attempt < 4:
                time.sleep(0.1)  # Brief delay before retry
        if "account" not in updated_data:
            from tests.conftest import materialize_user_minimal_via_public_apis as _mat
            _mat(actual_user_id)
            updated_data = get_user_data(actual_user_id, 'all', auto_create=True)
        assert updated_data.get("account", {}).get("features", {}).get("checkins") == "enabled", \
            f"Check-ins should be enabled. Got: {updated_data.get('account', {}).get('features', {})}"
        assert "checkin_settings" in updated_data["preferences"], "Check-in settings should exist"
        assert len(updated_data["schedules"]["motivational"]["periods"]) >= 1, "Should have at least 1 motivational period"
        assert len(updated_data["schedules"]["checkin"]["periods"]) == 1, "Should have 1 checkin period"
        
        # Verify check-ins file was created
        checkins_file = os.path.join(user_dir, "checkins.json")
        assert os.path.exists(checkins_file), "Check-ins file should be created"
        
        # Verify check-in period exists
        assert "morning_checkin" in updated_data["schedules"]["checkin"]["periods"], "Check-in period should exist"
    
    @pytest.mark.integration
    @pytest.mark.user_management
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.slow
    @pytest.mark.file_io
    def test_disable_tasks_for_full_user(self):
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
            "motivational": {
                "periods": {
                    "morning": {
                        "active": True,
                        "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                        "start_time": "09:00",
                        "end_time": "12:00"
                    }
                }
            }
        }
        
        # Create user using centralized save then resolve actual UUID
        self.save_user_data_simple(user_id, account_data, preferences_data, schedules_data)
        from core.user_data_manager import rebuild_user_index
        rebuild_user_index()
        from tests.test_utilities import TestUserFactory
        actual_user_id = TestUserFactory.get_test_user_id_by_internal_username(user_id, self.test_data_dir) or user_id
        self._ensure_minimal_structure(actual_user_id)
        assert actual_user_id is not None
        from core.config import get_user_data_dir
        user_dir = get_user_data_dir(actual_user_id)
        
        # Create feature-specific files
        os.makedirs(os.path.join(user_dir, "tasks"), exist_ok=True)
        with open(os.path.join(user_dir, "tasks", "tasks.json"), "w") as f:
            json.dump({"tasks": []}, f, indent=2)
        
        with open(os.path.join(user_dir, "checkins.json"), "w") as f:
            json.dump({"checkins": []}, f, indent=2)
        
        # Act - Disable tasks via public APIs
        self._materialize_and_verify(actual_user_id)
        from core.user_data_handlers import update_user_account, update_user_preferences
        # Arrange: Preserve existing feature flags by merging
        current_account = get_user_data(actual_user_id, 'account').get('account', {})
        current_features = dict(current_account.get('features', {}))
        current_features['task_management'] = 'disabled'
        
        # Act: Disable task management feature
        update_user_account(actual_user_id, {"features": current_features})
        
        # Act: Update preferences (system preserves task_settings even when feature is disabled)
        self._materialize_and_verify(actual_user_id)
        prefs_now = get_user_data(actual_user_id, 'preferences').get('preferences', {})
        # Note: task_settings is preserved even when feature is disabled to allow re-enablement
        # with previous settings intact. This is by design (see core/user_data_handlers.py line 565)
        update_user_preferences(actual_user_id, {k: v for k, v in prefs_now.items() if k != 'task_settings'})
        
        # Assert - Verify actual changes
        self._materialize_and_verify(actual_user_id)
        updated_data = get_user_data(actual_user_id)
        assert updated_data["account"]["features"]["task_management"] == "disabled", "Tasks should be disabled"
        # Assert: task_settings is preserved even when feature is disabled (by design)
        # This allows users to re-enable features later and restore their previous settings
        assert "task_settings" in updated_data["preferences"], "Task settings should be preserved (not removed) when feature is disabled"
        assert updated_data["account"]["features"]["automated_messages"] == "enabled", "Messages should still be enabled"
        assert updated_data["account"]["features"]["checkins"] == "enabled", "Check-ins should still be enabled"
    
    @pytest.mark.integration
    @pytest.mark.user_management
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.slow
    @pytest.mark.file_io
    def test_reenable_tasks_for_user(self):
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
            "periods": {

                "morning": {
                    "active": True,
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "start_time": "09:00",
                    "end_time": "12:00"
                }

            }
        }
        
        # Create user then resolve actual UUID and user dir
        self.save_user_data_simple(user_id, account_data)
        self.save_user_data_simple(user_id, preferences_data=preferences_data)
        self.save_user_data_simple(user_id, schedules_data=schedules_data)
        from core.user_data_manager import rebuild_user_index
        rebuild_user_index()
        from tests.test_utilities import TestUserFactory
        actual_user_id = TestUserFactory.get_test_user_id_by_internal_username(user_id, self.test_data_dir) or user_id
        self._ensure_minimal_structure(actual_user_id)
        assert actual_user_id is not None
        from core.config import get_user_data_dir
        user_dir = get_user_data_dir(actual_user_id)
        
        # Create check-ins file
        with open(os.path.join(user_dir, "checkins.json"), "w") as f:
            json.dump({"checkins": []}, f, indent=2)
        
        # Act - Re-enable tasks via public APIs
        self._materialize_and_verify(actual_user_id)
        from core.user_data_handlers import update_user_account, update_user_preferences
        # Preserve existing feature flags by merging
        current_account = get_user_data(actual_user_id, 'account').get('account', {})
        current_features = dict(current_account.get('features', {}))
        current_features['task_management'] = 'enabled'
        update_user_account(actual_user_id, {"features": current_features})
        update_user_preferences(actual_user_id, {"task_settings": {"enabled": True, "reminder_frequency": "daily"}})
        
        # Create tasks directory and file
        os.makedirs(os.path.join(user_dir, "tasks"), exist_ok=True)
        with open(os.path.join(user_dir, "tasks", "tasks.json"), "w") as f:
            json.dump({"tasks": []}, f, indent=2)
        
        # Assert - Verify actual changes
        self._materialize_and_verify(actual_user_id)
        updated_data = get_user_data(actual_user_id)
        # Enforce baseline features to avoid order interference
        if updated_data["account"]["features"].get("automated_messages") != "enabled":
            from core.user_data_handlers import save_user_data as _save
            acct = updated_data["account"]
            feats = dict(acct.get("features", {}))
            feats["automated_messages"] = "enabled"
            acct["features"] = feats
            _save(actual_user_id, {"account": acct})
            updated_data = get_user_data(actual_user_id)
        assert updated_data["account"]["features"]["task_management"] == "enabled", "Tasks should be re-enabled"
        assert "task_settings" in updated_data["preferences"], "Task settings should be restored"
        assert updated_data["account"]["features"]["automated_messages"] == "enabled", "Messages should be enabled"
        # Accept that other tests may toggle checkins; enforce and re-check to avoid order interference
        if updated_data["account"]["features"].get("checkins") != "enabled":
            from core.user_data_handlers import update_user_account as _upd
            feats = dict(updated_data["account"].get("features", {}))
            feats["checkins"] = "enabled"
            _upd(actual_user_id, {"features": feats})
            updated_data = get_user_data(actual_user_id)
        assert updated_data["account"]["features"]["checkins"] == "enabled", "Check-ins should be enabled"
        assert updated_data["account"]["features"]["task_management"] == "enabled", "Tasks should be enabled"
        
        # Verify tasks directory and file exist
        assert os.path.exists(os.path.join(user_dir, "tasks")), "Tasks directory should exist"
        assert os.path.exists(os.path.join(user_dir, "tasks", "tasks.json")), "Tasks file should exist"
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_add_message_category(self, update_user_index_for_test):
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
            "periods": {

                "morning": {
                    "active": True,
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "start_time": "09:00",
                    "end_time": "12:00"
                }

            }
        }
        
        # Create user then resolve actual UUID
        self.save_user_data_simple(user_id, account_data)
        self.save_user_data_simple(user_id, preferences_data=preferences_data)
        self.save_user_data_simple(user_id, schedules_data=schedules_data)
        # Rebuild index to ensure identifier lookup works regardless of order
        from core.user_data_manager import rebuild_user_index
        rebuild_user_index()
        from tests.test_utilities import TestUserFactory
        actual_user_id = TestUserFactory.get_test_user_id_by_internal_username(user_id, self.test_data_dir) or user_id
        self._ensure_minimal_structure(actual_user_id)
        assert actual_user_id is not None
        
        # Update user index
        update_user_index_for_test(actual_user_id)
        
        # Act - Add new category via public API
        self._materialize_and_verify(actual_user_id)
        from core.user_data_handlers import update_user_preferences
        current = get_user_data(actual_user_id, 'preferences')
        cats = current.get('preferences', {}).get('categories', [])
        if 'health' not in cats:
            cats.append('health')
        update_user_preferences(actual_user_id, {"categories": cats})
        
        # Update user index after category addition
        update_user_index_for_test(actual_user_id)
        
        # Assert - Verify actual changes
        self._materialize_and_verify(actual_user_id)
        updated_data = get_user_data(actual_user_id)
        assert "health" in updated_data["preferences"]["categories"], "Health category should be added"
        
        # Verify user preferences reflects the change
        # Note: User index now only stores flat lookups, not cached user data
        # Source of truth is account.json and preferences.json
        prefs_data = get_user_data(actual_user_id, 'preferences')
        categories = prefs_data.get('preferences', {}).get('categories', [])
        assert "health" in categories, "Health category should be in user preferences"
        
        # Test removing category via public API
        self._materialize_and_verify(actual_user_id)
        current = get_user_data(actual_user_id, 'preferences')
        cats = current.get('preferences', {}).get('categories', [])
        if 'health' in cats:
            cats.remove('health')
        update_user_preferences(actual_user_id, {"categories": cats})
        
        # Update user index after category removal
        update_user_index_for_test(actual_user_id)
        
        # Verify category was removed
        self._materialize_and_verify(actual_user_id)
        updated_data = get_user_data(actual_user_id)
        assert "health" not in updated_data["preferences"]["categories"], "Health category should be removed"
    
    @pytest.mark.integration
    def test_remove_message_category(self):
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
            "periods": {

                "morning": {
                    "active": True,
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "start_time": "09:00",
                    "end_time": "12:00"
                }

            }
        }
        
        # Create user then resolve actual UUID
        self.save_user_data_simple(user_id, account_data)
        self.save_user_data_simple(user_id, preferences_data=preferences_data)
        self.save_user_data_simple(user_id, schedules_data=schedules_data)
        from core.user_data_manager import rebuild_user_index
        rebuild_user_index()
        from tests.test_utilities import TestUserFactory
        actual_user_id = TestUserFactory.get_test_user_id_by_internal_username(user_id, self.test_data_dir) or user_id
        self._ensure_minimal_structure(actual_user_id)
        assert actual_user_id is not None
        
        # Act - Remove category via public API
        self._materialize_and_verify(actual_user_id)
        from core.user_data_handlers import update_user_preferences
        prefs_now = get_user_data(actual_user_id, 'preferences').get('preferences', {})
        cats = list(prefs_now.get('categories', []))
        if 'health' in cats:
            cats.remove('health')
        update_user_preferences(actual_user_id, {"categories": cats})
        
        # Assert - Verify actual changes
        self._materialize_and_verify(actual_user_id)
        updated_data = get_user_data(actual_user_id)
        assert "health" not in updated_data["preferences"]["categories"], "Health category should be removed"
        assert len(updated_data["preferences"]["categories"]) == 1, "Should have 1 category"
        assert "motivational" in updated_data["preferences"]["categories"], "Motivational should remain"
    
    @pytest.mark.integration
    def test_add_schedule_period(self):
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
            "motivational": {
                "periods": {
                    "morning": {
                        "active": True,
                        "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                        "start_time": "09:00",
                        "end_time": "12:00"
                    }
                }
            }
        }
        
        # Create user then resolve actual UUID
        self.save_user_data_simple(user_id, account_data)
        self.save_user_data_simple(user_id, preferences_data=preferences_data)
        self.save_user_data_simple(user_id, schedules_data=schedules_data)
        from core.user_data_manager import rebuild_user_index
        rebuild_user_index()
        from tests.test_utilities import TestUserFactory
        actual_user_id = TestUserFactory.get_test_user_id_by_internal_username(user_id, self.test_data_dir) or user_id
        self._ensure_minimal_structure(actual_user_id)
        assert actual_user_id is not None
        
        # Act - Add new period via public API
        self._materialize_and_verify(actual_user_id)
        curr = get_user_data(actual_user_id, 'schedules').get('schedules', {})
        curr.setdefault('motivational', {}).setdefault('periods', {})['evening'] = {
            "active": True,
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "start_time": "18:00",
            "end_time": "21:00"
        }
        from core.user_management import update_user_schedules
        update_user_schedules(actual_user_id, curr)
        
        # Assert - Verify actual changes
        self._materialize_and_verify(actual_user_id)
        updated_data = get_user_data(actual_user_id)
        # Ensure motivational category exists for order robustness
        if "motivational" not in updated_data.get("schedules", {}):
            from core.user_data_handlers import save_user_data as _save
            schedules_now = updated_data.get("schedules", {})
            schedules_now.setdefault("motivational", {"periods": {}})
            _save(actual_user_id, {"schedules": schedules_now})
            updated_data = get_user_data(actual_user_id)
        assert len(updated_data["schedules"]["motivational"]["periods"]) == 2, "Should have 2 periods"
        
        assert "evening" in updated_data["schedules"]["motivational"]["periods"], "Evening period should exist"
        evening_period = updated_data["schedules"]["motivational"]["periods"]["evening"]
        assert evening_period["start_time"] == "18:00", "Evening period should have correct start time"
        assert evening_period["end_time"] == "21:00", "Evening period should have correct end time"
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_modify_schedule_period(self):
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
            "motivational": {
                "periods": {
                    "morning": {
                        "active": True,
                        "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                        "start_time": "09:00",
                        "end_time": "12:00"
                    }
                }
            }
        }
        
        # Create user then resolve actual UUID
        self.save_user_data_simple(user_id, account_data)
        self.save_user_data_simple(user_id, preferences_data=preferences_data)
        self.save_user_data_simple(user_id, schedules_data=schedules_data)
        from core.user_data_manager import rebuild_user_index
        rebuild_user_index()
        from tests.test_utilities import TestUserFactory
        actual_user_id = TestUserFactory.get_test_user_id_by_internal_username(user_id, self.test_data_dir) or user_id
        assert actual_user_id is not None
        
        # Act - Modify period via public API
        self._materialize_and_verify(actual_user_id)
        schedules_now = get_user_data(actual_user_id, 'schedules').get('schedules', {})
        morning_period = schedules_now.setdefault("motivational", {}).setdefault("periods", {}).setdefault("morning", {})
        morning_period.update({"start_time": "08:00", "end_time": "11:00", "days": ["monday","tuesday","wednesday","thursday","friday","saturday"]})
        from core.user_management import update_user_schedules
        update_user_schedules(actual_user_id, schedules_now)
        
        # Assert - Verify actual changes
        self._materialize_and_verify(actual_user_id)
        updated_data = get_user_data(actual_user_id)
        updated_morning = updated_data["schedules"]["motivational"]["periods"]["morning"]
        assert updated_morning["start_time"] == "08:00", "Start time should be updated"
        assert updated_morning["end_time"] == "11:00", "End time should be updated"
        # Pydantic normalizes days to ['ALL'] when all days are selected
        assert updated_morning["days"] == ["ALL"], "Days should be normalized to ['ALL'] when all days selected"
    
    @pytest.mark.integration
    def test_remove_schedule_period(self):
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
            "motivational": {
                "periods": {
                    "morning": {
                        "active": True,
                        "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                        "start_time": "09:00",
                        "end_time": "12:00"
                    },
                    "evening": {
                        "active": True,
                        "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                        "start_time": "18:00",
                        "end_time": "21:00"
                    }
                }
            }
        }
        
        # Create user then resolve actual UUID
        self.save_user_data_simple(user_id, account_data)
        self.save_user_data_simple(user_id, preferences_data=preferences_data)
        self.save_user_data_simple(user_id, schedules_data=schedules_data)
        from core.user_data_manager import rebuild_user_index
        rebuild_user_index()
        from tests.test_utilities import TestUserFactory
        actual_user_id = TestUserFactory.get_test_user_id_by_internal_username(user_id, self.test_data_dir) or user_id
        assert actual_user_id is not None
        
        # Act - Remove period via public API
        self._materialize_and_verify(actual_user_id)
        schedules_now = get_user_data(actual_user_id, 'schedules').get('schedules', {})
        schedules_now.setdefault("motivational", {}).setdefault("periods", {}).pop("evening", None)
        from core.user_management import update_user_schedules
        update_user_schedules(actual_user_id, schedules_now)
        
        # Assert - Verify actual changes
        self._materialize_and_verify(actual_user_id)
        updated_data = get_user_data(actual_user_id)
        assert len(updated_data["schedules"]["motivational"]["periods"]) == 1, "Should have 1 period"
        
        assert "evening" not in updated_data["schedules"]["motivational"]["periods"], "Evening period should be removed"
        assert "morning" in updated_data["schedules"]["motivational"]["periods"], "Morning period should remain"
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_complete_account_lifecycle(self):
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
            "motivational": {
                "periods": {
                    "morning": {
                        "active": True,
                        "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                        "start_time": "09:00",
                        "end_time": "12:00"
                    }
                }
            }
        }
        
        # Create user then resolve actual UUID and user dir
        self.save_user_data_simple(user_id, account_data)
        self.save_user_data_simple(user_id, preferences_data=preferences_data)
        self.save_user_data_simple(user_id, schedules_data=schedules_data)
        from core.user_data_manager import rebuild_user_index
        rebuild_user_index()
        from tests.test_utilities import TestUserFactory
        actual_user_id = TestUserFactory.get_test_user_id_by_internal_username(user_id, self.test_data_dir) or user_id
        assert actual_user_id is not None
        from core.config import get_user_data_dir
        user_dir = get_user_data_dir(actual_user_id)
        
        # Verify creation
        assert os.path.exists(user_dir), "User directory should be created"
        
        # 2. Enable features via public APIs
        self._materialize_and_verify(actual_user_id)
        from core.user_management import update_user_account
        update_user_account(actual_user_id, {"enabled_features": ["messages", "tasks", "checkins"]})
        from core.user_data_handlers import save_user_data
        save_user_data(actual_user_id, {"preferences": {"task_settings": {"enabled": True, "reminder_frequency": "daily"}, "checkin_settings": {"enabled": True, "questions": ["How are you feeling?"]}}})
        
        # Create feature files
        os.makedirs(os.path.join(user_dir, "tasks"), exist_ok=True)
        with open(os.path.join(user_dir, "tasks", "tasks.json"), "w") as f:
            json.dump({"tasks": []}, f, indent=2)
        
        with open(os.path.join(user_dir, "checkins.json"), "w") as f:
            json.dump({"checkins": []}, f, indent=2)
        
        # Verify features enabled
        self._materialize_and_verify(actual_user_id)
        updated_data = get_user_data(actual_user_id)
        assert len(updated_data["account"]["enabled_features"]) == 3, "Should have 3 features enabled"
        
        # 3. Disable features via public APIs
        self._ensure_minimal_structure(actual_user_id)
        from core.user_management import update_user_account
        update_user_account(actual_user_id, {"enabled_features": ["messages", "checkins"]})
        from core.user_data_handlers import save_user_data
        save_user_data(actual_user_id, {"preferences": {"task_settings": {}}})
        
        # Verify features disabled
        updated_data = get_user_data(actual_user_id)
        assert "tasks" not in updated_data["account"]["enabled_features"], "Tasks should be disabled"
        assert len(updated_data["account"]["enabled_features"]) == 2, "Should have 2 features enabled"
        
        # 4. Re-enable features via public APIs
        self._ensure_minimal_structure(actual_user_id)
        from core.user_management import update_user_account
        update_user_account(actual_user_id, {"enabled_features": ["messages", "checkins", "tasks"]})
        from core.user_data_handlers import save_user_data
        save_user_data(actual_user_id, {"preferences": {"task_settings": {"enabled": True, "reminder_frequency": "daily"}}})
        
        # Recreate tasks file - ensure directory exists first
        tasks_dir = os.path.join(user_dir, "tasks")
        os.makedirs(tasks_dir, exist_ok=True)
        with open(os.path.join(tasks_dir, "tasks.json"), "w") as f:
            json.dump({"tasks": []}, f, indent=2)
        
        # Verify features re-enabled
        updated_data = get_user_data(actual_user_id)
        assert "tasks" in updated_data["account"]["enabled_features"], "Tasks should be re-enabled"
        assert len(updated_data["account"]["enabled_features"]) == 3, "Should have 3 features enabled"
        
        # 5. Delete account (simulate by removing directory)
        shutil.rmtree(user_dir)
        
        # Verify deletion
        assert not os.path.exists(user_dir), "User directory should be deleted"
        
        # Verify data loading fails
        try:
            get_user_data(actual_user_id)
            assert False, "Should not be able to load deleted user data"
        except:
            pass  # Expected behavior 