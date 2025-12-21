"""Unit tests for schedule management utilities."""

import pytest
from unittest.mock import patch

from core.schedule_management import (
    add_schedule_period,
    edit_schedule_period,
    delete_schedule_period,
    get_schedule_time_periods,
    set_schedule_period_active,
    clear_schedule_periods_cache,
    get_period_data__validate_and_format_time,
    get_period_data__time_24h_to_12h_display,
    get_period_data__time_12h_display_to_24h
)


class TestPeriodValidation:
    """Tests for time validation and conversion helpers."""

    @pytest.mark.unit
    @pytest.mark.scheduler
    def test_validate_and_format_time(self):
        """Ensure various time formats are normalized to HH:MM."""
        assert get_period_data__validate_and_format_time("9") == "9:00"
        assert get_period_data__validate_and_format_time("09:30") == "09:30"
        assert get_period_data__validate_and_format_time("9pm") == "21:00"
        assert get_period_data__validate_and_format_time("12am") == "00:00"

        assert get_period_data__validate_and_format_time("25:00") is None

    @pytest.mark.unit
    @pytest.mark.scheduler
    def test_time_conversion_helpers(self):
        """Verify 12h/24h conversion helpers."""
        assert get_period_data__time_24h_to_12h_display("00:30") == (12, 30, False)
        assert get_period_data__time_24h_to_12h_display("13:05") == (1, 5, True)
        assert get_period_data__time_12h_display_to_24h(12, 0, False) == "00:00"
        assert get_period_data__time_12h_display_to_24h(1, 5, True) == "13:05"

        assert get_period_data__time_24h_to_12h_display("bad") is None


class TestScheduleManagement:
    """Tests for schedule period lifecycle operations."""

    @pytest.mark.unit
    @pytest.mark.scheduler
    def test_schedule_period_lifecycle(self, mock_user_data, mock_config):
        """Add, edit, deactivate, and delete a schedule period."""
        user_id = mock_user_data["user_id"]
        category = "motivational"
        clear_schedule_periods_cache(user_id, category)

        with patch("core.schedule_management.UserContext") as MockUserContext, \
             patch("core.schedule_management.create_reschedule_request") as mock_reschedule:
            mock_ctx = MockUserContext.return_value
            mock_ctx.get_user_id.return_value = user_id
            mock_ctx.get_internal_username.return_value = "tester"

            add_schedule_period(category, "morning", "08:00", "10:00")
            # Clear cache after add to ensure we read fresh data (parallel test safety)
            clear_schedule_periods_cache(user_id, category)
            periods = get_schedule_time_periods(user_id, category)
            assert periods["morning"]["start_time"] == "08:00"
            assert periods["morning"]["end_time"] == "10:00"

            edit_schedule_period(category, "morning", "09:00", "11:00")
            # Clear cache after edit to ensure we read fresh data
            clear_schedule_periods_cache(user_id, category)
            periods = get_schedule_time_periods(user_id, category)
            assert periods["morning"]["start_time"] == "09:00"
            assert periods["morning"]["end_time"] == "11:00"

            result = set_schedule_period_active(user_id, category, "morning", False)
            assert result is True, "set_schedule_period_active should return True when period exists"
            # Clear cache after setting active to ensure we read fresh data
            clear_schedule_periods_cache(user_id, category)
            periods = get_schedule_time_periods(user_id, category)
            assert periods and "morning" in periods, f"Period 'morning' should exist in periods. Got: {periods}"
            assert periods["morning"]["active"] is False

            delete_schedule_period(category, "morning")
            # Clear cache after delete to ensure we read fresh data
            clear_schedule_periods_cache(user_id, category)
            periods = get_schedule_time_periods(user_id, category)
            assert "morning" not in periods
            assert "ALL" in periods
            assert periods["ALL"]["start_time"] == "00:00"
            assert periods["ALL"]["end_time"] == "23:59"

            assert mock_reschedule.call_count == 2

        clear_schedule_periods_cache(user_id, category)
