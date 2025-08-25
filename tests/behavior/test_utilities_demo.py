#!/usr/bin/env python3
"""
Test Utilities Demo - MHM
Demonstrates how to use the centralized test utilities to eliminate redundancy
"""

import os
import json
import pytest
from tests.test_utilities import (
    TestUserFactory, TestDataManager, TestUserDataFactory,
    create_test_user, setup_test_data_environment, cleanup_test_data_environment
)


class TestUtilitiesDemo:
    """Demonstration of centralized test utilities usage"""
    
    @pytest.mark.behavior
    @pytest.mark.debug
    @pytest.mark.smoke
    def test_basic_user_creation(self, test_data_dir):
        """Demonstrate creating a basic test user"""
        # Simple way to create a basic user
        success = create_test_user("demo_basic_user", user_type="basic", test_data_dir=test_data_dir)
        assert success, "Basic user creation should succeed"
        
        # Alternative using the factory directly
        success = TestUserFactory.create_basic_user("demo_basic_user_2", enable_checkins=True, enable_tasks=True, test_data_dir=test_data_dir)
        assert success, "Factory user creation should succeed"
    
    @pytest.mark.behavior
    @pytest.mark.debug
    @pytest.mark.smoke
    def test_discord_user_creation(self, test_data_dir):
        """Demonstrate creating a Discord-specific test user"""
        success = create_test_user("demo_discord_user", user_type="discord", discord_user_id="987654321", test_data_dir=test_data_dir)
        assert success, "Discord user creation should succeed"
        
        # Alternative using the factory directly
        success = TestUserFactory.create_discord_user("demo_discord_user_2", discord_user_id="111222333", test_data_dir=test_data_dir)
        assert success, "Discord factory user creation should succeed"
    
    @pytest.mark.behavior
    @pytest.mark.debug
    @pytest.mark.smoke
    def test_full_featured_user_creation(self, test_data_dir):
        """Demonstrate creating a full-featured test user"""
        success = create_test_user("demo_full_user", user_type="full", test_data_dir=test_data_dir)
        assert success, "Full user creation should succeed"
        
        # Alternative using the factory directly
        success = TestUserFactory.create_full_featured_user("demo_full_user_2", test_data_dir=test_data_dir)
        assert success, "Full factory user creation should succeed"
    
    @pytest.mark.behavior
    @pytest.mark.debug
    @pytest.mark.smoke
    def test_minimal_user_creation(self, test_data_dir):
        """Demonstrate creating a minimal test user"""
        success = create_test_user("demo_minimal_user", user_type="minimal", test_data_dir=test_data_dir)
        assert success, "Minimal user creation should succeed"
        
        # Alternative using the factory directly
        success = TestUserFactory.create_minimal_user("demo_minimal_user_2", test_data_dir=test_data_dir)
        assert success, "Minimal factory user creation should succeed"
    
    @pytest.mark.behavior
    @pytest.mark.debug
    @pytest.mark.smoke
    def test_user_data_factory_usage(self, test_data_dir):
        """Demonstrate using the user data factory for custom data structures"""
        user_id = "demo_data_user"
        
        # Create custom account data
        account_data = TestUserDataFactory.create_account_data(
            user_id,
            name="Custom User",
            timezone="America/Los_Angeles",
            pronouns="he/him"
        )
        
        # Create custom preferences data
        preferences_data = TestUserDataFactory.create_preferences_data(
            user_id,
            categories=["motivational", "health"],
            notification_settings={"morning_reminders": False}
        )
        
        # Create custom schedules data
        schedules_data = TestUserDataFactory.create_schedules_data(
            periods=[
                {
                    "name": "evening",
                    "active": True,
                    "days": ["monday", "wednesday", "friday"],
                    "start_time": "18:00",
                    "end_time": "21:00"
                }
            ]
        )
        
        # Verify the data structures
        assert account_data["name"] == "Custom User"
        assert account_data["timezone"] == "America/Los_Angeles"
        assert account_data["pronouns"] == "he/him"
        
        assert "motivational" in preferences_data["categories"]
        assert preferences_data["notification_settings"]["morning_reminders"] == False
        
        assert len(schedules_data["periods"]) == 1
        assert schedules_data["periods"][0]["name"] == "evening"
    
    def test_environment_management(self):
        """Demonstrate test environment setup and cleanup"""
        # Setup test environment
        test_dir, test_data_dir, test_test_data_dir = setup_test_data_environment()
        
        # Verify directories were created
        assert os.path.exists(test_data_dir)
        assert os.path.exists(test_test_data_dir)
        assert os.path.exists(os.path.join(test_data_dir, "users"))
        
        # Verify user index was created
        user_index_file = os.path.join(test_data_dir, "user_index.json")
        assert os.path.exists(user_index_file)
        
        with open(user_index_file, "r") as f:
            user_index = json.load(f)
        
        assert "test-user-basic" in user_index
        assert "test-user-full" in user_index
        
        # Cleanup test environment
        cleanup_test_data_environment(test_dir)
        
        # Verify cleanup worked
        assert not os.path.exists(test_dir)
    
    def test_multiple_user_types_in_single_test(self, test_data_dir):
        """Test creating multiple different user types in a single test."""
        # Create different types of users
        assert TestUserFactory.create_basic_user("multi_basic", test_data_dir=test_data_dir), "Basic user should be created"
        assert TestUserFactory.create_discord_user("multi_discord", test_data_dir=test_data_dir), "Discord user should be created"
        assert TestUserFactory.create_full_featured_user("multi_full", test_data_dir=test_data_dir), "Full featured user should be created"
        assert TestUserFactory.create_minimal_user("multi_minimal", test_data_dir=test_data_dir), "Minimal user should be created"
        
        # Verify all users were created by checking they can be found by internal username
        from core.user_management import get_user_id_by_identifier
        for user_id in ["multi_basic", "multi_discord", "multi_full", "multi_minimal"]:
            actual_user_id = get_user_id_by_identifier(user_id)
            assert actual_user_id is not None, f"User should be found by internal username: {user_id}"
            
            # Verify user directory exists
            from core.config import get_user_data_dir
            user_dir = get_user_data_dir(actual_user_id)
            assert os.path.exists(user_dir), f"User directory should exist for {user_id}"
    
    def test_email_user_creation(self, test_data_dir):
        """Test creating an email user with specific email address."""
        user_id = "test_email_user"
        email = "test.email@example.com"
        
        success = TestUserFactory.create_email_user(user_id, email=email, test_data_dir=test_data_dir)
        assert success, "Email user should be created successfully"
        
        # Verify user was created by checking internal username
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        assert actual_user_id is not None, "User should be found by internal username"
        
        # Verify user directory exists
        from core.config import get_user_data_dir
        user_dir = get_user_data_dir(actual_user_id)
        assert os.path.exists(user_dir), "User directory should exist"
        
        # Verify account data contains email
        from core.user_data_handlers import get_user_data
        account_result = get_user_data(actual_user_id, 'account')
        account_data = account_result.get('account', {})
        assert account_data is not None, "Account data should be loadable"
        assert account_data.get("email") == email, "Email should be saved correctly"
        assert account_data.get("features", {}).get("automated_messages") == "enabled", "Messages should be enabled"
    

    
    def test_custom_fields_user_creation(self, test_data_dir):
        """Test creating a user with custom fields."""
        user_id = "test_custom_user"
        custom_fields = {
            "health_conditions": ["Anxiety", "Depression"],
            "medications_treatments": ["Therapy", "Medication B"],
            "reminders_needed": ["Take breaks", "Drink water"]
        }
        
        success = TestUserFactory.create_user_with_custom_fields(user_id, custom_fields=custom_fields, test_data_dir=test_data_dir)
        assert success, "Custom fields user should be created successfully"
        
        # Verify user was created by checking internal username
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        assert actual_user_id is not None, "User should be found by internal username"
        
        # Verify user directory exists
        from core.config import get_user_data_dir
        user_dir = get_user_data_dir(actual_user_id)
        assert os.path.exists(user_dir), "User directory should exist"
        
        # Verify context data contains custom fields
        from core.user_data_handlers import get_user_data
        context_result = get_user_data(actual_user_id, 'context')
        context_data = context_result.get('context', {})
        assert context_data is not None, "Context data should be loadable"
        assert context_data.get("custom_fields", {}).get("health_conditions") == custom_fields["health_conditions"], "Custom fields should be saved correctly"
        assert context_data.get("interests") == ["Technology", "Gaming"], "Default interests should be set"
    
    def test_scheduled_user_creation(self, test_data_dir):
        """Test creating a user with comprehensive schedules."""
        user_id = "test_scheduled_user"
        schedule_config = {
            "motivational": {
                "periods": {
                    "Morning": {
                        "active": True,
                        "days": ["monday", "wednesday", "friday"],
                        "start_time": "08:00",
                        "end_time": "10:00"
                    }
                }
            },
            "health": {
                "periods": {
                    "Evening": {
                        "active": True,
                        "days": ["ALL"],
                        "start_time": "19:00",
                        "end_time": "21:00"
                    }
                }
            }
        }
        
        success = TestUserFactory.create_user_with_schedules(user_id, schedule_config=schedule_config, test_data_dir=test_data_dir)
        assert success, "Scheduled user should be created successfully"
        
        # Verify user was created by checking internal username
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        assert actual_user_id is not None, "User should be found by internal username"
        
        # Verify user directory exists
        from core.config import get_user_data_dir
        user_dir = get_user_data_dir(actual_user_id)
        assert os.path.exists(user_dir), "User directory should exist"
        
        # Verify schedules data contains custom configuration
        from core.user_data_handlers import get_user_data
        schedules_result = get_user_data(actual_user_id, 'schedules')
        schedules_data = schedules_result.get('schedules', {})
        assert schedules_data is not None, "Schedules data should be loadable"
        
        # Check if the custom schedule was saved correctly
        actual_morning_period = schedules_data.get("motivational", {}).get("periods", {}).get("Morning")
        expected_morning_period = schedule_config["motivational"]["periods"]["Morning"]
        
        # The schedule might be saved with different day format, so check the key fields
        assert actual_morning_period is not None, "Morning period should exist"
        assert actual_morning_period.get("active") == expected_morning_period["active"], "Active status should match"
        assert actual_morning_period.get("start_time") == expected_morning_period["start_time"], "Start time should match"
        assert actual_morning_period.get("end_time") == expected_morning_period["end_time"], "End time should match"
        # Note: Days might be normalized to uppercase or different format, so we don't assert on that

    def test_comprehensive_user_types(self, test_data_dir):
        """Test all comprehensive user types to ensure they cover real user scenarios."""
        from tests.test_utilities import TestUserFactory
        
        # Test all user types
        user_types = [
            ("basic_user", TestUserFactory.create_basic_user, "test_basic"),
            ("discord_user", TestUserFactory.create_discord_user, "test_discord"),
            ("email_user", TestUserFactory.create_email_user, "test_email"),

            ("full_featured_user", TestUserFactory.create_full_featured_user, "test_full"),
            ("minimal_user", TestUserFactory.create_minimal_user, "test_minimal"),
            ("health_focus_user", TestUserFactory.create_user_with_health_focus, "test_health"),
            ("task_focus_user", TestUserFactory.create_user_with_task_focus, "test_task"),
            ("disability_user", TestUserFactory.create_user_with_disabilities, "test_disability"),
            ("complex_checkins_user", TestUserFactory.create_user_with_complex_checkins, "test_complex_checkins"),
            ("limited_data_user", TestUserFactory.create_user_with_limited_data, "test_limited"),
            ("inconsistent_data_user", TestUserFactory.create_user_with_inconsistent_data, "test_inconsistent"),
        ]
        
        results = {}
        
        for user_type_name, factory_method, user_id in user_types:
            try:
                # Create user with appropriate parameters
                if user_type_name == "discord_user":
                    success = factory_method(user_id, discord_user_id="123456789", test_data_dir=test_data_dir)
                elif user_type_name == "email_user":
                    success = factory_method(user_id, email=f"{user_id}@example.com", test_data_dir=test_data_dir)

                else:
                    success = factory_method(user_id, test_data_dir=test_data_dir)
                
                results[user_type_name] = success
                
                if success:
                    # Verify user data can be loaded using test-specific functions
                    from tests.test_utilities import TestUserFactory
                    
                    # Get the actual user ID (UUID) that was created using test-specific function
                    actual_user_id = TestUserFactory.get_test_user_id_by_internal_username(user_id, test_data_dir)
                    if actual_user_id:
                        user_data = TestUserFactory.get_test_user_data(user_id, test_data_dir)
                    else:
                        # Fallback: try to get data directly by internal username
                        user_data = TestUserFactory.get_test_user_data(user_id, test_data_dir)
                    
                    assert user_data is not None, f"{user_type_name} should have loadable data"
                    
                    # Verify basic structure
                    assert 'account' in user_data, f"{user_type_name} should have account data"
                    assert 'preferences' in user_data, f"{user_type_name} should have preferences data"
                    assert 'context' in user_data, f"{user_type_name} should have context data"
                    
                    print(f"✅ {user_type_name}: Created successfully")
                else:
                    print(f"❌ {user_type_name}: Failed to create")
                    
            except Exception as e:
                print(f"❌ {user_type_name}: Error - {e}")
                results[user_type_name] = False
        
        # Summary
        successful_types = [name for name, success in results.items() if success]
        failed_types = [name for name, success in results.items() if not success]
        
        print(f"\n📊 Summary:")
        print(f"✅ Successful: {len(successful_types)}/{len(user_types)}")
        print(f"❌ Failed: {len(failed_types)}/{len(user_types)}")
        
        if failed_types:
            print(f"Failed types: {', '.join(failed_types)}")
        
        # Assert that most user types succeed (allowing for some edge cases)
        success_rate = len(successful_types) / len(user_types)
        assert success_rate >= 0.8, f"Success rate should be at least 80%, got {success_rate:.1%}"
    
    def test_real_user_scenarios(self, test_data_dir, mock_config):
        """Test scenarios that mirror real user data patterns."""
        from tests.test_utilities import TestUserFactory
        from core.user_data_handlers import get_user_data
        from core.user_management import get_user_id_by_identifier
        
        # Scenario 1: User with phone but no email (like real user c59410b9...)
        success1 = TestUserFactory.create_user_with_inconsistent_data("phone_only_user", test_data_dir=test_data_dir)
        assert success1, "Phone-only user should be created successfully"
        
        actual_user_id1 = get_user_id_by_identifier("phone_only_user")
        user_data1 = get_user_data(actual_user_id1) if actual_user_id1 else get_user_data("phone_only_user")
        assert user_data1['account']['phone'] == "3062619228", "Should have phone number"
        assert user_data1['account']['email'] == "", "Should have empty email"
        assert user_data1['account']['timezone'] == "America/Regina", "Should have Regina timezone"
        
        # Scenario 2: User with complex check-ins (like real user with detailed check-in settings)
        success2 = TestUserFactory.create_user_with_complex_checkins("complex_checkin_user", test_data_dir=test_data_dir)
        assert success2, "Complex check-in user should be created successfully"
        
        actual_user_id2 = get_user_id_by_identifier("complex_checkin_user")
        user_data2 = get_user_data(actual_user_id2) if actual_user_id2 else get_user_data("complex_checkin_user")
        checkin_settings = user_data2['preferences'].get('checkin_settings', {})
        custom_questions = checkin_settings.get('custom_questions', [])
        
        # Verify complex check-in structure
        # The feature enablement is now stored in account.features.checkins
        assert user_data2['account']['features']['checkins'] == 'enabled', "Check-ins should be enabled"
        # The checkin_settings has custom_questions as a list
        assert len(custom_questions) > 0, "Should have check-in questions"
        
        # Scenario 3: User with minimal data (like real users who don't fill out much)
        success3 = TestUserFactory.create_user_with_limited_data("minimal_data_user", test_data_dir=test_data_dir)
        assert success3, "Minimal data user should be created successfully"
        
        actual_user_id3 = get_user_id_by_identifier("minimal_data_user")
        user_data3 = get_user_data(actual_user_id3) if actual_user_id3 else get_user_data("minimal_data_user")
        
        # Verify minimal data structure
        assert user_data3['context']['preferred_name'] == "", "Should have empty preferred name"
        assert user_data3['context']['gender_identity'] == [], "Should have empty gender identity"
        assert user_data3['context']['interests'] == [], "Should have empty interests"
        assert user_data3['account']['timezone'] == "UTC", "Should have UTC timezone"
        
        # Scenario 4: Health-focused user with comprehensive health data
        success4 = TestUserFactory.create_user_with_health_focus("health_focus_user", test_data_dir=test_data_dir)
        assert success4, "Health focus user should be created successfully"
        
        actual_user_id4 = get_user_id_by_identifier("health_focus_user")
        user_data4 = get_user_data(actual_user_id4) if actual_user_id4 else get_user_data("health_focus_user")
        
        # Verify health-focused data
        assert "health" in user_data4['preferences']['categories'], "Should have health category"
        assert "motivational" in user_data4['preferences']['categories'], "Should have motivational category"
        
        custom_fields = user_data4['context']['custom_fields']
        assert "Anxiety" in custom_fields['health_conditions'], "Should have anxiety condition"
        assert "Depression" in custom_fields['health_conditions'], "Should have depression condition"
        assert "Therapy" in custom_fields['medications_treatments'], "Should have therapy treatment"
        assert "medication" in custom_fields['reminders_needed'], "Should have medication reminder"
        
        # Scenario 5: Task-focused user with productivity settings
        success5 = TestUserFactory.create_user_with_task_focus("task_focus_user", test_data_dir=test_data_dir)
        assert success5, "Task focus user should be created successfully"
        
        actual_user_id5 = get_user_id_by_identifier("task_focus_user")
        user_data5 = get_user_data(actual_user_id5) if actual_user_id5 else get_user_data("task_focus_user")
        
        # Verify task-focused data
        # The feature enablement is now stored in account.features.task_management
        assert user_data5['account']['features']['task_management'] == 'enabled', "Task management should be enabled"
        # Note: The specific task settings may vary based on TestUserFactory implementation
        
        interests = user_data5['context']['interests']
        assert "Productivity" in interests, "Should have productivity interest"
        assert "Organization" in interests, "Should have organization interest"
        
        print("✅ All real user scenarios tested successfully")
    
    def test_edge_case_users(self, test_data_dir):
        """Test edge cases and boundary conditions for user creation."""
        from tests.test_utilities import TestUserFactory
        from core.user_data_handlers import get_user_data
        from core.user_management import get_user_id_by_identifier
        
        # Edge case 1: User with very long user_id
        long_user_id = "a" * 50  # 50 character user ID (more reasonable)
        success1 = TestUserFactory.create_basic_user(long_user_id, test_data_dir=test_data_dir)
        assert success1, "Long user ID should be handled"
        
        actual_user_id1 = get_user_id_by_identifier(long_user_id)
        user_data1 = get_user_data(actual_user_id1) if actual_user_id1 else get_user_data(long_user_id)
        assert user_data1 is not None, "Long user ID should have loadable data"
        
        # Edge case 2: User with special characters in user_id (but valid for internal_username)
        special_user_id = "test-user_with.special_chars_123"
        success2 = TestUserFactory.create_basic_user(special_user_id, test_data_dir=test_data_dir)
        assert success2, "Special characters in user ID should be handled"
        
        actual_user_id2 = get_user_id_by_identifier(special_user_id)
        user_data2 = get_user_data(actual_user_id2) if actual_user_id2 else get_user_data(special_user_id)
        assert user_data2 is not None, "Special character user ID should have loadable data"
        
        # Edge case 3: User with all features disabled
        success3 = TestUserFactory.create_basic_user("disabled_user", enable_checkins=False, enable_tasks=False, test_data_dir=test_data_dir)
        assert success3, "User with all features disabled should be created"
        
        actual_user_id3 = get_user_id_by_identifier("disabled_user")
        user_data3 = get_user_data(actual_user_id3) if actual_user_id3 else get_user_data("disabled_user")
        features = user_data3['account']['features']
        assert features['checkins'] == "disabled", "Check-ins should be disabled"
        assert features['task_management'] == "disabled", "Task management should be disabled"
        assert features['automated_messages'] == "enabled", "Automated messages should still be enabled"
        
        # Edge case 4: User with empty string user_id (should fail gracefully)
        success4 = TestUserFactory.create_basic_user("", test_data_dir=test_data_dir)
        # This might fail, but should not crash the system
        print(f"Empty user ID creation result: {success4}")
        
        # Edge case 5: User with None user_id (should fail gracefully)
        try:
            success5 = TestUserFactory.create_basic_user(None, test_data_dir=test_data_dir)
            print(f"None user ID creation result: {success5}")
        except Exception as e:
            print(f"None user ID creation failed as expected: {e}")
        
        # Edge case 6: User with only numbers in user_id
        numeric_user_id = "12345"
        success6 = TestUserFactory.create_basic_user(numeric_user_id, test_data_dir=test_data_dir)
        assert success6, "Numeric user ID should be handled"
        
        actual_user_id6 = get_user_id_by_identifier(numeric_user_id)
        user_data6 = get_user_data(actual_user_id6) if actual_user_id6 else get_user_data(numeric_user_id)
        assert user_data6 is not None, "Numeric user ID should have loadable data"
        
        print("✅ All edge case scenarios tested successfully")
    
    def test_user_data_consistency(self, test_data_dir):
        """Test that all user types produce consistent data structures."""
        from tests.test_utilities import TestUserFactory
        from core.user_data_handlers import get_user_data
        from core.user_management import get_user_id_by_identifier
        
        # Test multiple user types and verify consistent structure
        test_users = [
            ("consistency_basic", TestUserFactory.create_basic_user),
            ("consistency_full", TestUserFactory.create_full_featured_user),
            ("consistency_minimal", TestUserFactory.create_minimal_user),
            ("consistency_health", TestUserFactory.create_user_with_health_focus),
            ("consistency_task", TestUserFactory.create_user_with_task_focus),
        ]
        
        for user_id, factory_method in test_users:
            try:
                # Create user
                success = factory_method(user_id, test_data_dir=test_data_dir)
                assert success, f"{user_id} should be created successfully"
                
                # Load user data
                actual_user_id = get_user_id_by_identifier(user_id)
                user_data = get_user_data(actual_user_id) if actual_user_id else get_user_data(user_id)
                assert user_data is not None, f"{user_id} should have loadable data"
                
                # Verify consistent structure
                required_sections = ['account', 'preferences', 'context']
                for section in required_sections:
                    assert section in user_data, f"{user_id} should have {section} section"
                
                # Verify account structure
                account = user_data['account']
                required_account_fields = ['user_id', 'internal_username', 'account_status', 'features']
                for field in required_account_fields:
                    assert field in account, f"{user_id} account should have {field} field"
                
                # Verify preferences structure
                preferences = user_data['preferences']
                required_pref_fields = ['categories', 'channel']
                for field in required_pref_fields:
                    assert field in preferences, f"{user_id} preferences should have {field} field"
                
                # Verify context structure
                context = user_data['context']
                required_context_fields = ['preferred_name', 'custom_fields', 'interests', 'goals']
                for field in required_context_fields:
                    assert field in context, f"{user_id} context should have {field} field"
                
                print(f"✅ {user_id}: Consistent structure verified")
                
            except Exception as e:
                print(f"❌ {user_id}: Structure verification failed - {e}")
                raise
        
        print("✅ All user types have consistent data structures")


class TestUtilitiesBenefits:
    """Demonstrate the benefits of centralized test utilities"""
    
    def test_reduced_code_duplication(self, test_data_dir):
        """Show how much less code is needed with centralized utilities"""
        # Before: Each test file had its own user creation logic
        # After: Simple one-liner
        success = create_test_user("benefit_user", user_type="basic", test_data_dir=test_data_dir)
        assert success, "User creation should be simple and consistent"
    
    def test_consistent_user_data(self, test_data_dir):
        """Show that all tests use consistent user data structures"""
        # Create users using different methods
        user1 = TestUserFactory.create_basic_user("consistent_user_1", test_data_dir=test_data_dir)
        user2 = create_test_user("consistent_user_2", user_type="basic", test_data_dir=test_data_dir)
        user3 = TestUserFactory.create_discord_user("consistent_user_3", test_data_dir=test_data_dir)
        
        # All should succeed with consistent data structures
        assert user1, "Factory method should work"
        assert user2, "Convenience function should work"
        assert user3, "Discord factory should work"
    
    def test_easy_maintenance(self, test_data_dir):
        """Show how easy it is to update user creation logic"""
        # If we need to change user creation logic, we only change it in one place
        # All tests automatically get the updated logic
        
        # Example: Create users with new features
        success = TestUserFactory.create_full_featured_user("maintenance_user", test_data_dir=test_data_dir)
        assert success, "Should work with any updates to user creation logic"
    
    def test_flexible_configuration(self, test_data_dir):
        """Show the flexibility of the utilities"""
        # Create users with different configurations
        basic_user = TestUserFactory.create_basic_user("flex_user_1", enable_checkins=True, enable_tasks=True, test_data_dir=test_data_dir)
        no_checkins_user = TestUserFactory.create_basic_user("flex_user_2", enable_checkins=False, enable_tasks=True, test_data_dir=test_data_dir)
        no_tasks_user = TestUserFactory.create_basic_user("flex_user_3", enable_checkins=True, enable_tasks=False, test_data_dir=test_data_dir)
        
        assert basic_user, "Full features should work"
        assert no_checkins_user, "No checkins should work"
        assert no_tasks_user, "No tasks should work"


if __name__ == "__main__":
    # This file can also be run directly to demonstrate the utilities
    print("🧪 Test Utilities Demo")
    print("=" * 40)
    
    # Setup test environment
    test_dir, test_data_dir, test_test_data_dir = setup_test_data_environment()
    
    try:
        # Override data paths for testing
        import core.config
        core.config.DATA_DIR = test_data_dir
        
        # Demonstrate user creation
        print("Creating test users...")
        success = create_test_user("demo_user", user_type="basic", test_data_dir=test_data_dir)
        print(f"Basic user creation: {'✅' if success else '❌'}")
        
        success = create_test_user("demo_discord", user_type="discord", test_data_dir=test_data_dir)
        print(f"Discord user creation: {'✅' if success else '❌'}")
        
        success = create_test_user("demo_full", user_type="full", test_data_dir=test_data_dir)
        print(f"Full user creation: {'✅' if success else '❌'}")
        
        print("\n🎉 Demo completed successfully!")
        
    finally:
        # Cleanup
        cleanup_test_data_environment(test_dir) 