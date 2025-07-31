#!/usr/bin/env python3
"""
Real Behavior Testing for Account Management - MHM
Tests actual system changes, side effects, and integration scenarios
Focuses on real file operations, data persistence, and cross-module interactions
"""

import sys
import os
import time
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
import pytest

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_test_environment(test_data_dir):
    """Create isolated test environment with temporary directories"""
    print("🔧 Setting up test environment...")
    
    # Create temporary test directory
    test_dir = tempfile.mkdtemp(prefix="mhm_test_")
    test_data_dir = os.path.join(test_dir, "data")
    test_test_data_dir = os.path.join(test_dir, "tests", "data")
    
    # Create directory structure
    os.makedirs(test_data_dir, exist_ok=True)
    os.makedirs(test_test_data_dir, exist_ok=True)
    os.makedirs(os.path.join(test_data_dir, "users"), exist_ok=True)
    os.makedirs(os.path.join(test_test_data_dir, "users"), exist_ok=True)
    
    # Create test user index
    user_index = {
        "test-user-basic": {
            "internal_username": "test-user-basic",
            "active": True,
            "channel_type": "discord",
            "enabled_features": ["messages"],
            "last_interaction": "2025-01-01T00:00:00",
            "last_updated": "2025-01-01T00:00:00"
        },
        "test-user-full": {
            "internal_username": "test-user-full", 
            "active": True,
            "channel_type": "discord",
            "enabled_features": ["messages", "tasks", "checkins"],
            "last_interaction": "2025-01-01T00:00:00",
            "last_updated": "2025-01-01T00:00:00"
        }
    }
    
    with open(os.path.join(test_data_dir, "user_index.json"), "w") as f:
        json.dump(user_index, f, indent=2)
    
    return test_dir, test_data_dir, test_test_data_dir

def create_test_user_data(user_id, test_data_dir, base_state="basic"):
    """Create test user data with specific base state"""
    user_dir = os.path.join(test_data_dir, "users", user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    if base_state == "basic":
        # Basic user with only messages enabled
        account_data = {
            "user_id": user_id,
            "internal_username": user_id,
            "account_status": "active",
            "timezone": "America/New_York",
            "channel": {"type": "discord", "contact": "test#1234"},
            "created_at": "2025-01-01 00:00:00",
            "updated_at": "2025-01-01 00:00:00",
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
        
    elif base_state == "full":
        # Full user with all features enabled
        account_data = {
            "user_id": user_id,
            "internal_username": user_id,
            "account_status": "active",
            "timezone": "America/New_York", 
            "channel": {"type": "discord", "contact": "test#1234"},
            "created_at": "2025-01-01 00:00:00",
            "updated_at": "2025-01-01 00:00:00",
            "features": {
                "automated_messages": "enabled",
                "checkins": "enabled",
                "task_management": "enabled"
            }
        }
        
        preferences_data = {
            "categories": ["motivational", "health"],
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
                },
                {
                    "name": "afternoon",
                    "active": True,
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "start_time": "14:00",
                    "end_time": "17:00"
                }
            ]
        }
    
    # Write user data files
    with open(os.path.join(user_dir, "account.json"), "w") as f:
        json.dump(account_data, f, indent=2)
    
    with open(os.path.join(user_dir, "preferences.json"), "w") as f:
        json.dump(preferences_data, f, indent=2)
    
    with open(os.path.join(user_dir, "schedules.json"), "w") as f:
        json.dump(schedules_data, f, indent=2)
    
    # Create feature-specific files for full user
    if base_state == "full":
        os.makedirs(os.path.join(user_dir, "tasks"), exist_ok=True)
        with open(os.path.join(user_dir, "tasks", "tasks.json"), "w") as f:
            json.dump({"tasks": []}, f, indent=2)
        
        with open(os.path.join(user_dir, "daily_checkins.json"), "w") as f:
            json.dump({"checkins": []}, f, indent=2)

def test_user_data_loading_real_behavior(test_data_dir):
    """Test actual user data loading with file verification"""
    print("\n🔍 Testing User Data Loading (Real Behavior)...")
    
    # Setup test environment and create test users
    import core.config
    core.config.BASE_DATA_DIR = test_data_dir
    print(f"  Setting BASE_DATA_DIR to: {test_data_dir}")
    create_test_user_data("test-user-basic", test_data_dir, "basic")
    create_test_user_data("test-user-full", test_data_dir, "full")
    print(f"  Test users created. Checking if files exist...")
    print(f"  Basic user account file: {os.path.join(test_data_dir, 'users', 'test-user-basic', 'account.json')}")
    print(f"  File exists: {os.path.exists(os.path.join(test_data_dir, 'users', 'test-user-basic', 'account.json'))}")
    
    try:
        from core.user_data_handlers import get_user_data
        
        # Test loading basic user
        basic_data = get_user_data("test-user-basic", "all")

        # Verify actual data structure
        assert "account" in basic_data, "Account data should be loaded"
        assert "preferences" in basic_data, "Preferences data should be loaded"
        assert "schedules" in basic_data, "Schedules data should be loaded"
        
        # Verify actual content
        assert basic_data["account"]["features"]["automated_messages"] == "enabled", "Basic user should have messages enabled"
        assert basic_data["account"]["features"]["checkins"] == "disabled", "Basic user should have checkins disabled"
        assert basic_data["account"]["features"]["task_management"] == "disabled", "Basic user should have tasks disabled"
        assert "motivational" in basic_data["preferences"]["categories"], "Basic user should have motivational category"
        
        print("  ✅ Basic user data loading: Success")
        
        # Test loading full user
        full_data = get_user_data("test-user-full", "all")
        
        # Verify actual data structure
        assert "account" in full_data, "Account data should be loaded"
        assert "preferences" in full_data, "Preferences data should be loaded"
        assert "schedules" in full_data, "Schedules data should be loaded"
        
        # Verify actual content
        assert full_data["account"]["features"]["task_management"] == "enabled", "Full user should have tasks enabled"
        assert full_data["account"]["features"]["checkins"] == "enabled", "Full user should have checkins enabled"
        assert len(full_data["schedules"]["periods"]) == 2, "Full user should have 2 schedule periods"
        
        print("  ✅ Full user data loading: Success")
        
    except Exception as e:
        print(f"  ❌ User data loading: Error - {e}")
        raise

def test_feature_enablement_real_behavior(test_data_dir):
    """Test actual feature enablement with file creation/deletion"""
    print("\n🔍 Testing Feature Enablement (Real Behavior)...")
    
    # Setup test environment and create test users
    import core.config
    core.config.BASE_DATA_DIR = test_data_dir
    create_test_user_data("test-user-basic", test_data_dir, "basic")
    create_test_user_data("test-user-full", test_data_dir, "full")
    
    try:
        from core.user_data_handlers import save_user_data, get_user_data
        
        # Test enabling check-ins for basic user
        basic_data = get_user_data("test-user-basic", "all")
        
        # Enable check-ins
        basic_data["account"]["features"]["checkins"] = "enabled"
        basic_data["preferences"]["checkin_settings"] = {
            "enabled": True,
            "questions": ["How are you feeling today?"]
        }
        
        # Save changes
        save_user_data("test-user-basic", {"account": basic_data["account"], "preferences": basic_data["preferences"]})
        
        # Verify actual file changes
        updated_data = get_user_data("test-user-basic", "all")
        assert updated_data["account"]["features"]["checkins"] == "enabled", "Check-ins should be enabled"
        assert "checkin_settings" in updated_data["preferences"], "Check-in settings should exist"
        
        # Verify daily_checkins.json was created
        checkins_file = os.path.join(test_data_dir, "users", "test-user-basic", "daily_checkins.json")
        assert os.path.exists(checkins_file), "daily_checkins.json should be created"
        
        print("  ✅ Enable check-ins: Success")
        
        # Test disabling tasks for full user
        full_data = get_user_data("test-user-full", "all")
        
        # Disable tasks
        full_data["account"]["features"]["task_management"] = "disabled"
        if "task_settings" in full_data["preferences"]:
            del full_data["preferences"]["task_settings"]
        
        # Save changes
        save_user_data("test-user-full", {"account": full_data["account"], "preferences": full_data["preferences"]})
        
        # Verify actual file changes
        updated_data = get_user_data("test-user-full", "all")
        assert updated_data["account"]["features"]["task_management"] == "disabled", "Tasks should be disabled"
        assert "task_settings" not in updated_data["preferences"], "Task settings should be removed"
        
        print("  ✅ Disable tasks: Success")
        
    except Exception as e:
        print(f"  ❌ Feature enablement: Error - {e}")
        raise

def test_category_management_real_behavior(test_data_dir):
    """Test actual category management with file persistence"""
    print("\n🔍 Testing Category Management (Real Behavior)...")
    
    # Setup test environment and create test users
    import core.config
    core.config.BASE_DATA_DIR = test_data_dir
    create_test_user_data("test-user-basic", test_data_dir, "basic")
    create_test_user_data("test-user-full", test_data_dir, "full")
    
    try:
        from core.user_data_handlers import save_user_data, get_user_data
        from core.message_management import create_message_file_from_defaults
        
        # Create test user
        user_id = "test-user-category"
        user_dir = os.path.join(test_data_dir, "users", user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Test data
        account_data = {
            "internal_username": user_id,
            "enabled_features": ["messages"]
        }
        
        preferences_data = {
            "categories": ["motivational", "health"],
            "channel": {"type": "discord", "contact": "test#1234"}
        }
        
        # Save user data
        result = save_user_data(user_id, {
            'account': account_data,
            'preferences': preferences_data
        })
        
        if result.get('account') and result.get('preferences'):
            print("✅ User data saved successfully")
            
            # Test adding a new category
            print("📝 Testing category addition...")
            loaded_data = get_user_data(user_id)
            if 'fun_facts' not in loaded_data['preferences']['categories']:
                loaded_data['preferences']['categories'].append('fun_facts')
                save_result = save_user_data(user_id, {'preferences': loaded_data['preferences']})
                if save_result.get('preferences'):
                    print("✅ Category 'fun_facts' added successfully")
                else:
                    print("❌ Failed to add category")
                    assert False, "Failed to add category"
            else:
                print("⚠️ Category 'fun_facts' already exists")
            
            # Test removing a category
            print("🗑️ Testing category removal...")
            loaded_data = get_user_data(user_id)
            if 'health' in loaded_data['preferences']['categories']:
                loaded_data['preferences']['categories'].remove('health')
                save_result = save_user_data(user_id, {'preferences': loaded_data['preferences']})
                if save_result.get('preferences'):
                    print("✅ Category 'health' removed successfully")
                else:
                    print("❌ Failed to remove category")
                    assert False, "Failed to remove category"
            else:
                print("⚠️ Category 'health' not found to remove")
            
            # Test message file creation for categories
            print("📄 Testing message file creation...")
            try:
                # Create message files for enabled categories
                for category in loaded_data['preferences']['categories']:
                    create_message_file_from_defaults(user_id, category)
                    message_file = os.path.join(user_dir, "messages", f"{category}.json")
                    if os.path.exists(message_file):
                        print(f"✅ Message file created for category: {category}")
                    else:
                        print(f"❌ Failed to create message file for category: {category}")
                        assert False, f"Failed to create message file for category: {category}"
            except Exception as e:
                print(f"❌ Error creating message files: {e}")
                raise
            
            # Verify final state
            final_data = get_user_data(user_id)
            print(f"📊 Final categories: {final_data['preferences']['categories']}")
            
        else:
            print("❌ Failed to save user data")
            assert False, "Failed to save user data"
            
    except Exception as e:
        print(f"❌ Error in category management test: {e}")
        raise

def test_schedule_period_management_real_behavior(test_data_dir):
    """Test actual schedule period management with file persistence"""
    print("\n🔍 Testing Schedule Period Management (Real Behavior)...")
    
    # Setup test environment and create test users
    import core.config
    core.config.BASE_DATA_DIR = test_data_dir
    create_test_user_data("test-user-basic", test_data_dir, "basic")
    create_test_user_data("test-user-full", test_data_dir, "full")
    
    try:
        from core.user_data_handlers import save_user_data, get_user_data
        
        # Test adding new schedule period
        basic_data = get_user_data("test-user-basic", "all")
        original_periods = len(basic_data["schedules"]["periods"])
        
        # Add evening period
        new_period = {
            "name": "evening",
            "active": True,
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "start_time": "18:00",
            "end_time": "21:00"
        }
        
        basic_data["schedules"]["periods"].append(new_period)
        save_user_data("test-user-basic", {"schedules": basic_data["schedules"]})
        
        # Verify actual file changes
        updated_data = get_user_data("test-user-basic", "all")
        assert len(updated_data["schedules"]["periods"]) == original_periods + 1, "Should have one more period"
        
        # Verify period content
        evening_period = next((p for p in updated_data["schedules"]["periods"] if p["name"] == "evening"), None)
        assert evening_period is not None, "Evening period should exist"
        assert evening_period["start_time"] == "18:00", "Evening period should have correct start time"
        
        print("  ✅ Add schedule period: Success")
        
        # Test modifying existing period
        basic_data = get_user_data("test-user-basic", "all")
        morning_period = next((p for p in basic_data["schedules"]["periods"] if p["name"] == "morning"), None)
        morning_period["start_time"] = "08:00"
        morning_period["end_time"] = "11:00"
        
        save_user_data("test-user-basic", {"schedules": basic_data["schedules"]})
        
        # Verify actual file changes
        updated_data = get_user_data("test-user-basic", "all")
        updated_morning = next((p for p in updated_data["schedules"]["periods"] if p["name"] == "morning"), None)
        assert updated_morning["start_time"] == "08:00", "Morning period should have updated start time"
        assert updated_morning["end_time"] == "11:00", "Morning period should have updated end time"
        
        print("  ✅ Modify schedule period: Success")
        
        # Test removing schedule period
        basic_data = get_user_data("test-user-basic", "all")
        basic_data["schedules"]["periods"] = [p for p in basic_data["schedules"]["periods"] if p["name"] != "evening"]
        save_user_data("test-user-basic", {"schedules": basic_data["schedules"]})
        
        # Verify actual file changes
        updated_data = get_user_data("test-user-basic", "all")
        assert len(updated_data["schedules"]["periods"]) == original_periods, "Should be back to original count"
        evening_period = next((p for p in updated_data["schedules"]["periods"] if p["name"] == "evening"), None)
        assert evening_period is None, "Evening period should be removed"
        
        print("  ✅ Remove schedule period: Success")
        
    except Exception as e:
        print(f"  ❌ Schedule period management: Error - {e}")
        raise

def test_integration_scenarios_real_behavior(test_data_dir):
    """Test complex integration scenarios with multiple operations"""
    print("\n🔍 Testing Integration Scenarios (Real Behavior)...")
    
    # Setup test environment and create test users
    import core.config
    core.config.BASE_DATA_DIR = test_data_dir
    create_test_user_data("test-user-basic", test_data_dir, "basic")
    create_test_user_data("test-user-full", test_data_dir, "full")
    
    try:
        from core.user_data_handlers import save_user_data, get_user_data
        
        # Scenario 1: User opts into check-ins for the first time
        print("  Testing: User opts into check-ins for the first time")
        
        basic_data = get_user_data("test-user-basic", "all")
        
        # Enable check-ins
        basic_data["account"]["features"]["checkins"] = "enabled"
        basic_data["preferences"]["checkin_settings"] = {
            "enabled": True,
            "questions": ["How are you feeling?", "What's your energy level?"]
        }
        
        # Add check-in schedule periods
        checkin_periods = [
            {
                "name": "morning_checkin",
                "active": True,
                "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "start_time": "09:00",
                "end_time": "10:00"
            },
            {
                "name": "evening_checkin", 
                "active": True,
                "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "start_time": "18:00",
                "end_time": "19:00"
            }
        ]
        
        basic_data["schedules"]["periods"].extend(checkin_periods)
        
        # Save all changes
        save_user_data("test-user-basic", {
            "account": basic_data["account"],
            "preferences": basic_data["preferences"],
            "schedules": basic_data["schedules"]
        })
        
        # Verify integration
        updated_data = get_user_data("test-user-basic", "all")
        assert updated_data["account"]["features"]["checkins"] == "enabled", "Check-ins should be enabled"
        assert "checkin_settings" in updated_data["preferences"], "Check-in settings should exist"
        assert len(updated_data["schedules"]["periods"]) >= 3, "Should have check-in schedule periods"
        
        # Verify daily_checkins.json was created
        checkins_file = os.path.join(test_data_dir, "users", "test-user-basic", "daily_checkins.json")
        assert os.path.exists(checkins_file), "daily_checkins.json should be created"
        
        print("    ✅ Check-in opt-in scenario: Success")
        
        # Scenario 2: User disables task management and re-enables it
        print("  Testing: User disables task management and re-enables it")
        
        full_data = get_user_data("test-user-full", "all")
        
        # Disable tasks
        full_data["account"]["features"]["task_management"] = "disabled"
        if "task_settings" in full_data["preferences"]:
            del full_data["preferences"]["task_settings"]
        
        save_user_data("test-user-full", {
            "account": full_data["account"],
            "preferences": full_data["preferences"]
        })
        
        # Verify disabled state
        disabled_data = get_user_data("test-user-full", "all")
        assert disabled_data["account"]["features"]["task_management"] == "disabled", "Tasks should be disabled"
        assert "task_settings" not in disabled_data["preferences"], "Task settings should be removed"
        
        # Re-enable tasks
        full_data = get_user_data("test-user-full", "all")
        full_data["account"]["features"]["task_management"] = "enabled"
        full_data["preferences"]["task_settings"] = {
            "enabled": True,
            "reminder_frequency": "daily"
        }
        
        save_user_data("test-user-full", {
            "account": full_data["account"],
            "preferences": full_data["preferences"]
        })
        
        # Verify re-enabled state
        reenabled_data = get_user_data("test-user-full", "all")
        assert reenabled_data["account"]["features"]["task_management"] == "enabled", "Tasks should be re-enabled"
        assert "task_settings" in reenabled_data["preferences"], "Task settings should be restored"
        
        # Verify tasks directory exists
        tasks_dir = os.path.join(test_data_dir, "users", "test-user-full", "tasks")
        assert os.path.exists(tasks_dir), "Tasks directory should exist"
        
        print("    ✅ Task disable/re-enable scenario: Success")
        
        # Scenario 3: User adds new message category and then removes it
        print("  Testing: User adds new message category and then removes it")
        
        basic_data = get_user_data("test-user-basic", "all")
        
        # Add new category
        basic_data["preferences"]["categories"].append("quotes")
        save_user_data("test-user-basic", {"preferences": basic_data["preferences"]})
        
        # Verify category added
        updated_data = get_user_data("test-user-basic", "all")
        assert "quotes" in updated_data["preferences"]["categories"], "Quotes category should be added"
        
        # Remove category
        basic_data = get_user_data("test-user-basic", "all")
        basic_data["preferences"]["categories"].remove("quotes")
        save_user_data("test-user-basic", {"preferences": basic_data["preferences"]})
        
        # Verify category removed
        final_data = get_user_data("test-user-basic", "all")
        assert "quotes" not in final_data["preferences"]["categories"], "Quotes category should be removed"
        
        print("    ✅ Category add/remove scenario: Success")
        
    except Exception as e:
        print(f"  ❌ Integration scenarios: Error - {e}")
        raise

def test_data_consistency_real_behavior(test_data_dir):
    """Test data consistency across multiple operations"""
    print("\n🔍 Testing Data Consistency (Real Behavior)...")
    
    # Setup test environment and create test users
    import core.config
    core.config.BASE_DATA_DIR = test_data_dir
    
    # Create user index
    user_index = {
        "test-user-basic": {
            "internal_username": "test-user-basic",
            "active": True,
            "channel_type": "discord",
            "enabled_features": ["messages"],
            "last_interaction": "2025-01-01T00:00:00",
            "last_updated": "2025-01-01T00:00:00"
        },
        "test-user-full": {
            "internal_username": "test-user-full", 
            "active": True,
            "channel_type": "discord",
            "enabled_features": ["messages", "tasks", "checkins"],
            "last_interaction": "2025-01-01T00:00:00",
            "last_updated": "2025-01-01T00:00:00"
        }
    }
    
    with open(os.path.join(test_data_dir, "user_index.json"), "w") as f:
        json.dump(user_index, f, indent=2)
    
    create_test_user_data("test-user-basic", test_data_dir, "basic")
    create_test_user_data("test-user-full", test_data_dir, "full")
    
    try:
        from core.user_data_handlers import save_user_data, get_user_data
        
        # Test that user index stays consistent
        user_index_file = os.path.join(test_data_dir, "user_index.json")
        
        # Perform multiple operations
        basic_data = get_user_data("test-user-basic", "all")
        basic_data["account"]["timezone"] = "America/Los_Angeles"
        save_user_data("test-user-basic", {"account": basic_data["account"]})
        
        # Verify user index still exists and is valid
        assert os.path.exists(user_index_file), "User index should still exist"
        
        with open(user_index_file, "r") as f:
            user_index = json.load(f)
        
        print(f"  User index content: {user_index}")
        assert "test-user-basic" in user_index, "User should still be in index"
        assert user_index["test-user-basic"]["active"] == True, "User should still be active"
        
        print("  ✅ User index consistency: Success")
        
        # Test that account.json and preferences.json stay in sync
        basic_data = get_user_data("test-user-basic", "all")
        
        # Update channel in both places
        basic_data["account"]["channel"]["contact"] = "newcontact#5678"
        basic_data["preferences"]["channel"]["contact"] = "newcontact#5678"
        
        save_user_data("test-user-basic", {"account": basic_data["account"], "preferences": basic_data["preferences"]})
        
        # Verify both files have the same contact
        updated_data = get_user_data("test-user-basic", "all")
        assert updated_data["account"]["channel"]["contact"] == "newcontact#5678", "Account should have new contact"
        assert updated_data["preferences"]["channel"]["contact"] == "newcontact#5678", "Preferences should have new contact"
        
        print("  ✅ File synchronization: Success")
        
    except Exception as e:
        print(f"  ❌ Data consistency: Error - {e}")
        raise

def cleanup_test_environment(test_dir):
    """Clean up test environment"""
    print("\n🧹 Cleaning up test environment...")
    try:
        shutil.rmtree(test_dir)
        print("  ✅ Test environment cleaned up")
    except Exception as e:
        print(f"  ⚠️ Cleanup warning: {e}")

def main():
    """Run all real behavior tests"""
    print("🚀 Starting Real Behavior Testing for Account Management")
    print("=" * 60)
    
    # Setup test environment
    test_dir, test_data_dir, test_test_data_dir = setup_test_environment(test_data_dir)
    
    # Override data paths for testing
    import core.config
    core.config.DATA_DIR = test_data_dir
    
    # Create test users
    create_test_user_data("test-user-basic", test_data_dir, "basic")
    create_test_user_data("test-user-full", test_data_dir, "full")
    
    all_results = {}
    
    # Run all tests
    all_results.update(test_user_data_loading_real_behavior(test_data_dir))
    all_results.update(test_feature_enablement_real_behavior(test_data_dir))
    all_results.update(test_category_management_real_behavior(test_data_dir))
    all_results.update(test_schedule_period_management_real_behavior(test_data_dir))
    all_results.update(test_integration_scenarios_real_behavior(test_data_dir))
    all_results.update(test_data_consistency_real_behavior(test_data_dir))
    
    # Cleanup
    cleanup_test_environment(test_dir)
    
    # Print results summary
    print("\n" + "=" * 60)
    print("📊 REAL BEHAVIOR TESTING RESULTS")
    print("=" * 60)
    
    success_count = 0
    total_count = 0
    
    for test_name, result in all_results.items():
        total_count += 1
        if "SUCCESS" in result:
            success_count += 1
            print(f"✅ {test_name}: {result}")
        else:
            print(f"❌ {test_name}: {result}")
    
    print(f"\n🎯 SUMMARY: {success_count}/{total_count} tests passed")
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if success_count == total_count:
        print("🎉 ALL REAL BEHAVIOR TESTS PASSED!")
    else:
        print("⚠️ Some tests failed - review results above")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 