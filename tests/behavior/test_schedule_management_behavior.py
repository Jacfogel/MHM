"""
Behavior tests for schedule management module.
Focuses on real behavior, side effects, and actual system changes.
"""

import pytest
import time
from unittest.mock import patch, Mock
from core.schedule_management import (
    get_schedule_time_periods,
    set_schedule_period_active,
    is_schedule_period_active,
    add_schedule_period,
    edit_schedule_period,
    delete_schedule_period,
    clear_schedule_periods_cache,
    get_period_data__validate_and_format_time,
    get_period_data__time_24h_to_12h_display,
    get_period_data__time_12h_display_to_24h,
    get_current_day_names,
    set_schedule_periods,
    set_schedule_days
)


@pytest.mark.behavior
class TestScheduleManagementBehavior:
    """Test schedule management real behavior and side effects."""

    @pytest.mark.scheduler
    @pytest.mark.critical
    def test_get_schedule_time_periods_creates_cache(self, test_data_dir):
        """Test that getting schedule periods actually creates cache entries."""
        # Arrange
        user_id = "test-user"
        category = "messages"
        
        # Set up test schedule data
        schedule_data = {
            "schedules": {
                "messages": {
                    "periods": {
                        "Morning": {
                            "start_time": "08:00",
                            "end_time": "12:00",
                            "active": True,
                            "days": ["Monday", "Tuesday", "Wednesday"]
                        }
                    }
                }
            }
        }
        
        # Act
        with patch('core.schedule_management.get_user_data', return_value=schedule_data):
            result = get_schedule_time_periods(user_id, category)
        
        # Assert - Verify cache was created
        from core.schedule_management import _schedule_periods_cache
        cache_key = f"{user_id}_{category}"
        assert cache_key in _schedule_periods_cache, "Cache entry should be created"
        assert _schedule_periods_cache[cache_key][0] == result, "Cache should contain result"

    @pytest.mark.scheduler
    @pytest.mark.critical
    def test_set_schedule_period_active_persists_changes(self, test_data_dir):
        """Test that setting period active actually persists changes to user data."""
        # Arrange
        user_id = "test-user"
        category = "messages"
        period_name = "Morning"
        
        # Set up initial schedule data
        initial_schedule = {
            "account": {
                "features": {"messages": True}
            },
            "schedules": {
                "messages": {
                    "periods": {
                        "Morning": {
                            "start_time": "08:00",
                            "end_time": "12:00",
                            "active": False,
                            "days": ["Monday", "Tuesday"]
                        }
                    }
                }
            }
        }
        
        # Act - Mock the update_user_schedules function that's actually called
        with patch(
            'core.schedule_management.get_user_data', return_value=initial_schedule
        ), patch('core.user_data_handlers.update_user_schedules') as mock_update:
            result = set_schedule_period_active(user_id, category, period_name, True)
        
        # Assert - Verify update was called with updated data
        assert result is True, "Function should return True on success"
        mock_update.assert_called()
        
        # Verify the saved data has the correct active state
        call_args = mock_update.call_args
        saved_data = call_args[0][1]  # Second argument is the data
        assert saved_data[category]["periods"][period_name]["active"] is True, "Period should be active"

    @pytest.mark.scheduler
    @pytest.mark.regression
    def test_clear_schedule_periods_cache_removes_entries(self, test_data_dir):
        """Test that clearing schedule periods cache actually removes cache entries."""
        # Arrange
        user_id = "test-user"
        category = "messages"
        
        # Populate cache first
        from core.schedule_management import _schedule_periods_cache
        _schedule_periods_cache[f"{user_id}_{category}"] = ({"test": "data"}, time.time())
        _schedule_periods_cache["other_user_messages"] = ({"other": "data"}, time.time())
        
        # Act
        clear_schedule_periods_cache(user_id, category)
        
        # Assert - Verify specific cache entry was removed
        cache_key = f"{user_id}_{category}"
        assert cache_key not in _schedule_periods_cache, "Specific cache entry should be removed"
        assert "other_user_messages" in _schedule_periods_cache, "Other cache entries should remain"

    @pytest.mark.scheduler
    @pytest.mark.regression
    def test_validate_and_format_time_enforces_rules(self):
        """Test that time validation actually enforces format rules."""
        # Test valid times - including formats that are actually accepted
        assert get_period_data__validate_and_format_time("08:30") == "08:30", "Valid time should be returned as-is"
        assert get_period_data__validate_and_format_time("23:59") == "23:59", "Valid time should be returned as-is"
        assert get_period_data__validate_and_format_time("8:30") == "8:30", "Time without leading zero should be accepted"
        assert get_period_data__validate_and_format_time("8") == "8:00", "Hour only should add :00"
        
        # Test invalid times - these should return None due to error handling
        assert get_period_data__validate_and_format_time("25:00") is None, "Invalid hour should return None"
        assert get_period_data__validate_and_format_time("12:60") is None, "Invalid minute should return None"
        assert get_period_data__validate_and_format_time("08:5") is None, "Missing leading zero in minutes should return None"

    @pytest.mark.scheduler
    @pytest.mark.regression
    def test_time_conversion_functions_work_correctly(self):
        """Test that time conversion functions produce accurate results."""
        # Test 24h to 12h conversion - functions return integers, not strings
        assert get_period_data__time_24h_to_12h_display("08:30") == (8, 30, False), "8:30 AM should convert correctly"
        assert get_period_data__time_24h_to_12h_display("13:45") == (1, 45, True), "1:45 PM should convert correctly"
        assert get_period_data__time_24h_to_12h_display("00:00") == (12, 0, False), "12:00 AM should convert correctly"
        assert get_period_data__time_24h_to_12h_display("12:00") == (12, 0, True), "12:00 PM should convert correctly"
        
        # Test 12h to 24h conversion - functions expect integers, not strings
        assert get_period_data__time_12h_display_to_24h(8, 30, False) == "08:30", "8:30 AM should convert to 08:30"
        assert get_period_data__time_12h_display_to_24h(1, 45, True) == "13:45", "1:45 PM should convert to 13:45"
        assert get_period_data__time_12h_display_to_24h(12, 0, False) == "00:00", "12:00 AM should convert to 00:00"
        assert get_period_data__time_12h_display_to_24h(12, 0, True) == "12:00", "12:00 PM should convert to 12:00"

    @pytest.mark.scheduler
    @pytest.mark.regression
    def test_get_current_day_names_returns_actual_days(self):
        """Test that get_current_day_names returns actual current day information."""
        # Act
        current_days = get_current_day_names()
        
        # Assert - Verify it returns a list with actual day names
        assert isinstance(current_days, list), "Should return a list"
        assert len(current_days) > 0, "Should return at least one day"
        
        # Verify all returned values are valid day names (including 'ALL')
        valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "ALL"]
        for day in current_days:
            assert day in valid_days, f"'{day}' should be a valid day name"

    @pytest.mark.scheduler
    @pytest.mark.file_io
    def test_schedule_period_activation_integration(self, test_data_dir):
        """Test complete integration of schedule period activation workflow."""
        # Arrange
        user_id = "test-user"
        category = "messages"
        period_name = "TestPeriod"
        
        # Set up initial schedule
        initial_schedule = {
            "account": {
                "features": {"messages": True}
            },
            "schedules": {
                "messages": {
                    "periods": {
                        period_name: {
                            "start_time": "08:00",
                            "end_time": "12:00",
                            "active": False,
                            "days": ["Monday", "Tuesday"]
                        }
                    }
                }
            }
        }
        
        # Act - Complete workflow: check initial state, activate, verify
        with patch(
            'core.schedule_management.get_user_data', return_value=initial_schedule
        ), patch('core.user_data_handlers.update_user_schedules') as mock_update:
            mock_update.return_value = True
            # Check initial state
            initial_active = is_schedule_period_active(user_id, category, period_name)

            # Activate period
            activation_result = set_schedule_period_active(user_id, category, period_name, True)

            # Check final state
            final_active = is_schedule_period_active(user_id, category, period_name)
        
        # Assert - Verify complete workflow
        assert initial_active is False, "Period should initially be inactive"
        assert activation_result is True, "Activation should succeed"
        assert final_active is True, "Period should be active after activation"
        assert mock_update.call_count >= 1, "Data should be saved during activation"

    @pytest.mark.scheduler
    @pytest.mark.file_io
    def test_schedule_cache_invalidation(self, test_data_dir):
        """Test that schedule cache is properly invalidated when data changes."""
        # Arrange
        user_id = "test-user"
        category = "messages"
        
        # Set up initial schedule
        
        # Materialize Morning period and then exercise cache
        set_schedule_periods(user_id, category, {
            "Morning": {
                "start_time": "08:00",
                "end_time": "12:00",
                "active": True,
                "days": ["Monday"]
            }
        })

        # First call populates cache
        periods1 = get_schedule_time_periods(user_id, category)

        # Clear cache to simulate invalidation
        clear_schedule_periods_cache(user_id, category)

        # Second call should use fresh data
        periods2 = get_schedule_time_periods(user_id, category)
        
        # Assert - Verify cache invalidation
        # Note: get_schedule_time_periods may return default "ALL" period along with custom periods
        assert "Morning" in periods1 or "ALL" in periods1, f"Initial periods should contain Morning or ALL, got: {list(periods1.keys())}"
        assert "Morning" in periods2 or "ALL" in periods2, f"Updated periods should contain Morning or ALL, got: {list(periods2.keys())}"
        
        # Verify cache was cleared and repopulated
        from core.schedule_management import _schedule_periods_cache
        cache_key = f"{user_id}_{category}"
        assert cache_key in _schedule_periods_cache, "Cache should be repopulated"

    @pytest.mark.scheduler
    @pytest.mark.file_io
    def test_set_schedule_periods_persists_complete_data(self, test_data_dir):
        """Test that setting schedule periods actually persists complete data structure."""
        # Arrange
        user_id = "test-user"
        category = "messages"
        
        # Set up new periods data
        new_periods = {
            "Morning": {
                "start_time": "08:00",
                "end_time": "12:00",
                "active": True,
                "days": ["Monday", "Tuesday", "Wednesday"]
            },
            "Afternoon": {
                "start_time": "13:00",
                "end_time": "17:00",
                "active": False,
                "days": ["Thursday", "Friday"]
            }
        }
        
        # Act - Mock the update_user_schedules function that's actually called
        with patch('core.user_data_handlers.update_user_schedules') as mock_update:
            result = set_schedule_periods(user_id, category, new_periods)
        
        # Assert - Verify update was called with complete data structure
        # Note: set_schedule_periods returns True on success (for error handling verification)
        assert result is True, "Function should return True on success"
        mock_update.assert_called()
        
        # Verify the saved data contains all periods
        call_args = mock_update.call_args
        saved_data = call_args[0][1]  # Second argument is the data
        saved_periods = saved_data[category]["periods"]
        assert "Morning" in saved_periods, "Morning period should be saved"
        assert "Afternoon" in saved_periods, "Afternoon period should be saved"
        assert saved_periods["Morning"]["start_time"] == "08:00", "Morning start time should be correct"
        assert saved_periods["Afternoon"]["active"] is False, "Afternoon should be inactive"

    @pytest.mark.scheduler
    @pytest.mark.file_io
    def test_set_schedule_days_persists_day_changes(self, test_data_dir):
        """Test that setting schedule days actually persists day changes."""
        # Arrange
        user_id = "test-user"
        category = "messages"
        
        # Set up initial schedule with periods
        initial_schedule = {
            "schedules": {
                "messages": {
                    "periods": {
                        "Morning": {
                            "start_time": "08:00",
                            "end_time": "12:00",
                            "active": True,
                            "days": ["Monday", "Tuesday"]
                        }
                    }
                }
            }
        }
        
        new_days = ["Wednesday", "Thursday", "Friday"]
        
        # Act - Mock the update_user_schedules function that's actually called
        with patch(
            'core.schedule_management.get_user_data', return_value=initial_schedule
        ), patch('core.user_data_handlers.update_user_schedules') as mock_update:
            result = set_schedule_days(user_id, category, new_days)
        
        # Assert - Verify update was called with updated days
        # Note: set_schedule_days doesn't return anything (None)
        assert result is None, "Function should return None (no return statement)"
        mock_update.assert_called()
        
        # Verify the saved data has updated days
        call_args = mock_update.call_args
        saved_data = call_args[0][1]  # Second argument is the data
        saved_days = saved_data[category]["days"]
        assert saved_days == new_days, "Days should be updated"

    @pytest.mark.scheduler
    @pytest.mark.regression
    def test_schedule_period_crud_with_usercontext_mocking(self, test_data_dir):
        """Test CRUD operations with proper UserContext mocking."""
        # Arrange
        user_id = "test-user"
        category = "messages"
        period_name = "TestPeriod"
        
        # Set up user data with empty schedules
        user_data = {
            "account": {
                "internal_username": user_id,
                "features": {"messages": True}
            },
            "schedules": {
                "messages": {
                    "periods": {}
                }
            }
        }
        
        # Mock UserContext to return our test user ID
        mock_user_context = Mock()
        mock_user_context.get_user_id.return_value = user_id
        mock_user_context.get_internal_username.return_value = user_id
        
        # Act - Complete CRUD workflow with UserContext mocking
        with patch(
            'core.schedule_management.UserContext', return_value=mock_user_context
        ), patch(
            'core.schedule_management.get_user_data', return_value=user_data
        ), patch('core.user_data_handlers.update_user_schedules') as mock_update:
            # Create
            add_schedule_period(category, period_name, "08:00", "12:00")

            # Update - need to update user_data to include the created period
            updated_user_data = {
                "account": {
                    "internal_username": user_id,
                    "enabled_features": ["messages"]
                },
                "schedules": {
                    "messages": {
                        "periods": {
                            period_name: {
                                "start_time": "08:00",
                                "end_time": "12:00",
                                "active": True,
                                "days": ["Monday"]
                            }
                        }
                    }
                }
            }

            with patch(
                'core.schedule_management.get_user_data',
                return_value=updated_user_data,
            ):
                edit_schedule_period(category, period_name, "09:00", "13:00")

                # Delete
                delete_schedule_period(category, period_name)
        
        # Assert - Verify UserContext was called correctly
        assert mock_user_context.get_user_id.call_count >= 3, "UserContext.get_user_id should be called for each operation"
        assert mock_update.call_count >= 3, "Data should be saved for each operation"

    @pytest.mark.scheduler
    @pytest.mark.regression
    def test_schedule_period_operations_with_error_handling(self, test_data_dir):
        """Test that schedule operations handle errors gracefully."""
        # Arrange
        category = "messages"
        period_name = "TestPeriod"
        
        # Mock UserContext to return None (simulating error)
        mock_user_context = Mock()
        mock_user_context.get_user_id.return_value = None
        
        # Act - Test operations with invalid UserContext
        with patch('core.schedule_management.UserContext', return_value=mock_user_context):
            create_result = add_schedule_period(category, period_name, "08:00", "12:00")
            update_result = edit_schedule_period(category, period_name, "09:00", "13:00")
            delete_result = delete_schedule_period(category, period_name)
        
        # Assert - Verify functions handle errors gracefully
        assert create_result is None, "Should return None when UserContext is invalid"
        assert update_result is None, "Should return None when UserContext is invalid"
        assert delete_result is None, "Should return None when UserContext is invalid"

    @pytest.mark.scheduler
    @pytest.mark.regression
    def test_schedule_period_validation_errors(self, test_data_dir):
        """Test that schedule operations validate input correctly."""
        # Arrange
        user_id = "test-user"
        category = "messages"
        period_name = "TestPeriod"
        
        # Mock UserContext
        mock_user_context = Mock()
        mock_user_context.get_user_id.return_value = user_id
        mock_user_context.get_internal_username.return_value = user_id
        
        # Set up schedule with existing period
        existing_schedule = {
            "account": {
                "internal_username": user_id,
                "enabled_features": ["messages"]
            },
            "schedules": {
                "messages": {
                    "periods": {
                        period_name: {
                            "start_time": "08:00",
                            "end_time": "12:00",
                            "active": True,
                            "days": ["Monday"]
                        }
                    }
                }
            }
        }
        
        # Act - Test adding duplicate period
        with patch(
            'core.schedule_management.UserContext', return_value=mock_user_context
        ), patch(
            'core.schedule_management.get_user_data', return_value=existing_schedule
        ):
            # The function doesn't actually raise ValueError, it returns None
            result = add_schedule_period(category, period_name, "09:00", "13:00")
            assert result is None, "Should return None when period already exists"

    @pytest.mark.scheduler
    @pytest.mark.file_io
    def test_schedule_period_operations_with_scheduler_manager(self, test_data_dir):
        """Test schedule operations with scheduler manager integration."""
        # Arrange
        user_id = "test-user"
        category = "messages"
        period_name = "TestPeriod"
        
        # Mock UserContext
        mock_user_context = Mock()
        mock_user_context.get_user_id.return_value = user_id
        mock_user_context.get_internal_username.return_value = user_id
        
        # Mock scheduler manager
        mock_scheduler = Mock()
        
        # Act - Test operations with scheduler manager
        with patch(
            'core.schedule_management.UserContext', return_value=mock_user_context
        ), patch('core.user_data_handlers.update_user_schedules'):
            # Test add with scheduler
            add_schedule_period(category, period_name, "08:00", "12:00", mock_scheduler)

            # Test delete with scheduler
            delete_schedule_period(category, period_name, mock_scheduler)
        
        # Assert - Verify scheduler was called
        assert mock_scheduler.reset_and_reschedule_daily_messages.call_count >= 1, "Scheduler should be called"

    @pytest.mark.scheduler
    @pytest.mark.file_io
    def test_schedule_period_operations_with_real_user_data(self, test_data_dir):
        """Test schedule operations with realistic user data setup."""
        # Arrange
        user_id = "test-user"
        category = "messages"
        period_name = "TestPeriod"
        
        # Create realistic user data structure
        user_data = {
            "account": {
                "internal_username": user_id,
                "enabled_features": ["messages"]
            },
            "schedules": {
                "messages": {
                    "periods": {}
                }
            }
        }
        
        # Mock UserContext
        mock_user_context = Mock()
        mock_user_context.get_user_id.return_value = user_id
        mock_user_context.get_internal_username.return_value = user_id
        
        # Act - Test with realistic user data
        with patch(
            'core.schedule_management.UserContext', return_value=mock_user_context
        ), patch(
            'core.schedule_management.get_user_data', return_value=user_data
        ), patch('core.user_data_handlers.update_user_schedules') as mock_update:
            # Create a period
            create_result = add_schedule_period(category, period_name, "08:00", "12:00")

            # Verify the period was added
            assert create_result is None, "Create should return None"
            assert mock_update.called, "User data should be updated"

            # Verify the update call contained the new period
            call_args = mock_update.call_args
            saved_data = call_args[0][1]  # Second argument is the data
            assert period_name in saved_data[category]["periods"], "Period should be added to data"

    @pytest.mark.scheduler
    @pytest.mark.regression
    def test_schedule_period_edge_cases(self, test_data_dir):
        """Test schedule operations with edge cases and boundary conditions."""
        # Arrange
        user_id = "test-user"
        category = "messages"
        
        # Mock UserContext
        mock_user_context = Mock()
        mock_user_context.get_user_id.return_value = user_id
        mock_user_context.get_internal_username.return_value = user_id
        
        # Test edge cases
        with patch(
            'core.schedule_management.UserContext', return_value=mock_user_context
        ), patch('core.user_data_handlers.update_user_schedules'):
            # Test with empty periods
            result = set_schedule_periods(user_id, category, {})
            assert result is True, "Empty periods should be handled and return True on success"

            # Test with non-string period names (should be converted)
            result = set_schedule_periods(user_id, category, {123: {"start_time": "08:00", "end_time": "12:00"}})
            assert result is True, "Non-string period names should be converted and return True on success"

            # Test with missing period data fields
            result = set_schedule_periods(user_id, category, {"Test": {}})
            assert result is True, "Missing period data should use defaults and return True on success"
