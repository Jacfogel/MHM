"""
Behavior tests for Quantitative Check-in Analytics Expansion.
Tests that all opted-in quantitative questions are included in analytics.
"""

import pytest
import json
import os
from core.checkin_analytics import CheckinAnalytics
from core.user_data_handlers import (
    get_user_data,
    get_user_id_by_identifier,
    save_user_data,
)
from core.config import get_user_file_path
from core.time_utilities import TIMESTAMP_FULL, format_timestamp, now_datetime_full
from tests.test_utilities import TestUserFactory


class TestQuantitativeAnalyticsExpansion:
    """Test that quantitative analytics include all opted-in quantitative questions."""

    @pytest.mark.behavior
    @pytest.mark.analytics
    @pytest.mark.file_io
    @pytest.mark.critical
    def test_quantitative_analytics_includes_all_enabled_fields(
        self, test_data_dir, fix_user_data_loaders
    ):
        """Test that analytics include all enabled quantitative fields."""
        user_id = "test-user-analytics"

        # Arrange - Create user with comprehensive check-in settings
        test_user = TestUserFactory.create_basic_user(
            user_id, test_data_dir=test_data_dir
        )

        # Get the actual UUID for the user
        actual_user_id = get_user_id_by_identifier(user_id)
        assert actual_user_id is not None, "User should be created and resolvable"

        # Enable multiple quantitative fields
        checkin_settings = {
            "questions": {
                "mood": {"enabled": True, "type": "scale_1_5"},
                "energy": {"enabled": True, "type": "scale_1_5"},
                "stress_level": {"enabled": True, "type": "scale_1_5"},
                "sleep_quality": {"enabled": True, "type": "scale_1_5"},
                "anxiety_level": {"enabled": True, "type": "scale_1_5"},
                "focus_level": {"enabled": True, "type": "scale_1_5"},
                "sleep_schedule": {"enabled": True, "type": "time_pair"},
                # Non-quantitative fields should be ignored
                "ate_breakfast": {"enabled": True, "type": "yes_no"},
                "exercise": {"enabled": True, "type": "yes_no"},
            }
        }

        # Save user preferences
        user_data = get_user_data(actual_user_id, "preferences") or {}
        user_data["preferences"] = {"checkin_settings": checkin_settings}
        save_user_data(actual_user_id, "preferences", user_data)

        # Create sample check-in data with all quantitative fields (use recent dates)
        from datetime import datetime, timedelta

        now = now_datetime_full()
        sample_checkins = [
            {
                "timestamp": format_timestamp(now - timedelta(days=2), TIMESTAMP_FULL),
                "mood": 4,
                "energy": 3,
                "stress_level": 2,
                "sleep_quality": 4,
                "anxiety_level": 1,
                "focus_level": 4,
                "sleep_schedule": {
                    "sleep_time": "23:30",
                    "wake_time": "07:00",
                },  # 7.5 hours
                "ate_breakfast": "yes",
                "exercise": "no",
            },
            {
                "timestamp": format_timestamp(now - timedelta(days=1), TIMESTAMP_FULL),
                "mood": 3,
                "energy": 4,
                "stress_level": 3,
                "sleep_quality": 3,
                "anxiety_level": 2,
                "focus_level": 3,
                "sleep_schedule": {
                    "sleep_time": "01:00",
                    "wake_time": "07:00",
                },  # 6.0 hours
                "ate_breakfast": "no",
                "exercise": "yes",
            },
            {
                "timestamp": format_timestamp(now, TIMESTAMP_FULL),
                "mood": 5,
                "energy": 5,
                "stress_level": 1,
                "sleep_quality": 5,
                "anxiety_level": 1,
                "focus_level": 5,
                "sleep_schedule": {
                    "sleep_time": "23:00",
                    "wake_time": "07:00",
                },  # 8.0 hours
                "ate_breakfast": "yes",
                "exercise": "yes",
            },
        ]

        # Store check-in data in the correct UUID directory
        checkin_file = get_user_file_path(actual_user_id, "checkins")
        os.makedirs(os.path.dirname(checkin_file), exist_ok=True)
        with open(checkin_file, "w", encoding="utf-8") as f:
            json.dump(sample_checkins, f, indent=2)

        # Act - Get quantitative summaries with explicit enabled fields (use actual_user_id)
        analytics = CheckinAnalytics()
        enabled_fields = [
            "mood",
            "energy",
            "stress_level",
            "sleep_quality",
            "anxiety_level",
            "focus_level",
            "sleep_schedule",
            "ate_breakfast",
            "exercise",
        ]
        summaries = analytics.get_quantitative_summaries(
            actual_user_id, days=30, enabled_fields=enabled_fields
        )

        # Assert - Verify all quantitative fields are included
        assert "error" not in summaries, f"Should not have error: {summaries}"

        # Check that all quantitative fields are present
        expected_fields = [
            "mood",
            "energy",
            "stress_level",
            "sleep_quality",
            "anxiety_level",
            "focus_level",
            "sleep_schedule",
            "ate_breakfast",
            "exercise",
        ]
        for field in expected_fields:
            assert field in summaries, f"Should include {field} in analytics"

            # Verify field has proper structure
            field_stats = summaries[field]
            assert "average" in field_stats, f"{field} should have average"
            assert "min" in field_stats, f"{field} should have min"
            assert "max" in field_stats, f"{field} should have max"
            assert "count" in field_stats, f"{field} should have count"
            assert field_stats["count"] == 3, f"{field} should have count of 3"

        # Verify yes/no questions are converted to 0/1 values
        assert (
            summaries["ate_breakfast"]["average"] == 0.67
        ), "Breakfast average should be 0.67 (2 yes, 1 no)"
        assert (
            summaries["exercise"]["average"] == 0.67
        ), "Exercise average should be 0.67 (2 yes, 1 no)"

        # Verify specific calculations
        assert summaries["mood"]["average"] == 4.0, "Mood average should be 4.0"
        assert summaries["mood"]["min"] == 3, "Mood min should be 3"
        assert summaries["mood"]["max"] == 5, "Mood max should be 5"

        # sleep_schedule is converted to hours for analytics
        assert (
            abs(summaries["sleep_schedule"]["average"] - 7.17) < 0.1
        ), f"Sleep schedule average should be ~7.17, got {summaries['sleep_schedule']['average']}"
        assert (
            abs(summaries["sleep_schedule"]["min"] - 6.0) < 0.1
        ), f"Sleep schedule min should be 6.0, got {summaries['sleep_schedule']['min']}"
        assert (
            abs(summaries["sleep_schedule"]["max"] - 8.0) < 0.1
        ), f"Sleep schedule max should be 8.0, got {summaries['sleep_schedule']['max']}"

    @pytest.mark.behavior
    @pytest.mark.analytics
    @pytest.mark.file_io
    def test_quantitative_analytics_respects_user_enabled_fields(
        self, test_data_dir, fix_user_data_loaders
    ):
        """Test that analytics only include fields the user has enabled."""
        user_id = "test-user-selective"

        # Arrange - Create user with selective check-in settings
        test_user = TestUserFactory.create_basic_user(
            user_id, test_data_dir=test_data_dir
        )

        # Get the actual UUID for the user
        actual_user_id = get_user_id_by_identifier(user_id)
        assert actual_user_id is not None, "User should be created and resolvable"

        # Enable only some quantitative fields
        checkin_settings = {
            "questions": {
                "mood": {"enabled": True, "type": "scale_1_5"},
                "energy": {"enabled": False, "type": "scale_1_5"},  # Disabled
                "stress_level": {"enabled": True, "type": "scale_1_5"},
                "sleep_quality": {"enabled": False, "type": "scale_1_5"},  # Disabled
                "anxiety_level": {"enabled": True, "type": "scale_1_5"},
                "focus_level": {"enabled": False, "type": "scale_1_5"},  # Disabled
                "sleep_hours": {"enabled": True, "type": "number"},
            }
        }

        # Save user preferences
        user_data = get_user_data(actual_user_id, "preferences") or {}
        user_data["preferences"] = {"checkin_settings": checkin_settings}
        save_user_data(actual_user_id, "preferences", user_data)

        # Create sample check-in data (use recent date)
        from datetime import datetime, timedelta

        now = now_datetime_full()
        sample_checkins = [
            {
                "timestamp": format_timestamp(now - timedelta(days=1), TIMESTAMP_FULL),
                "mood": 4,
                "energy": 3,  # Should be ignored
                "stress_level": 2,
                "sleep_quality": 4,  # Should be ignored
                "anxiety_level": 1,
                "focus_level": 4,  # Should be ignored
                "sleep_schedule": {
                    "sleep_time": "23:30",
                    "wake_time": "07:00",
                },  # 7.5 hours
            }
        ]

        # Store check-in data in the correct UUID directory
        checkin_file = get_user_file_path(actual_user_id, "checkins")
        os.makedirs(os.path.dirname(checkin_file), exist_ok=True)
        with open(checkin_file, "w", encoding="utf-8") as f:
            json.dump(sample_checkins, f, indent=2)

        # Act - Get quantitative summaries with explicit enabled fields (use actual_user_id)
        analytics = CheckinAnalytics()
        enabled_fields = ["mood", "stress_level", "anxiety_level", "sleep_schedule"]
        summaries = analytics.get_quantitative_summaries(
            actual_user_id, days=30, enabled_fields=enabled_fields
        )

        # Assert - Verify only enabled fields are included
        assert "error" not in summaries, f"Should not have error: {summaries}"

        # Check enabled fields are present
        enabled_fields = ["mood", "stress_level", "anxiety_level", "sleep_schedule"]
        for field in enabled_fields:
            assert field in summaries, f"Should include enabled field {field}"

        # Check disabled fields are not present
        disabled_fields = ["energy", "sleep_quality", "focus_level"]
        for field in disabled_fields:
            assert field not in summaries, f"Should not include disabled field {field}"

    @pytest.mark.behavior
    @pytest.mark.analytics
    @pytest.mark.file_io
    def test_quantitative_analytics_handles_missing_fields_gracefully(
        self, test_data_dir, fix_user_data_loaders
    ):
        """Test that analytics handle missing fields gracefully."""
        user_id = "test-user-missing-fields"

        # Arrange - Create user with check-in data missing some fields
        test_user = TestUserFactory.create_basic_user(
            user_id, test_data_dir=test_data_dir
        )

        # Get the actual UUID for the user
        actual_user_id = get_user_id_by_identifier(user_id)
        assert actual_user_id is not None, "User should be created and resolvable"

        # Enable all quantitative fields
        checkin_settings = {
            "questions": {
                "mood": {"enabled": True, "type": "scale_1_5"},
                "energy": {"enabled": True, "type": "scale_1_5"},
                "stress_level": {"enabled": True, "type": "scale_1_5"},
                "sleep_quality": {"enabled": True, "type": "scale_1_5"},
                "anxiety_level": {"enabled": True, "type": "scale_1_5"},
                "focus_level": {"enabled": True, "type": "scale_1_5"},
                "sleep_hours": {"enabled": True, "type": "number"},
            }
        }

        # Save user preferences
        user_data = get_user_data(actual_user_id, "preferences") or {}
        user_data["preferences"] = {"checkin_settings": checkin_settings}
        save_user_data(actual_user_id, "preferences", user_data)

        # Create check-in data with missing fields (use recent dates)
        from datetime import datetime, timedelta

        now = now_datetime_full()
        sample_checkins = [
            {
                "timestamp": format_timestamp(now - timedelta(days=1), TIMESTAMP_FULL),
                "mood": 4,
                "energy": 3,
                # Missing: stress_level, sleep_quality, anxiety_level, focus_level, sleep_schedule
            },
            {
                "timestamp": format_timestamp(now, TIMESTAMP_FULL),
                "mood": 3,
                "stress_level": 2,
                "sleep_quality": 4,
                # Missing: energy, anxiety_level, focus_level, sleep_schedule
            },
        ]

        # Store check-in data in the correct UUID directory
        checkin_file = get_user_file_path(actual_user_id, "checkins")
        os.makedirs(os.path.dirname(checkin_file), exist_ok=True)
        with open(checkin_file, "w", encoding="utf-8") as f:
            json.dump(sample_checkins, f, indent=2)

        # Act - Get quantitative summaries with explicit enabled fields (use actual_user_id)
        analytics = CheckinAnalytics()
        enabled_fields = [
            "mood",
            "energy",
            "stress_level",
            "sleep_quality",
            "anxiety_level",
            "focus_level",
            "sleep_schedule",
            "ate_breakfast",
            "exercise",
        ]
        summaries = analytics.get_quantitative_summaries(
            actual_user_id, days=30, enabled_fields=enabled_fields
        )

        # Assert - Verify only fields with data are included
        assert "error" not in summaries, f"Should not have error: {summaries}"

        # Check fields with data are present
        assert "mood" in summaries, "Should include mood (has data in both check-ins)"
        assert (
            "energy" in summaries
        ), "Should include energy (has data in first check-in)"
        assert (
            "stress_level" in summaries
        ), "Should include stress_level (has data in second check-in)"
        assert (
            "sleep_quality" in summaries
        ), "Should include sleep_quality (has data in second check-in)"

        # Check fields without data are not included
        assert (
            "anxiety_level" not in summaries
        ), "Should not include anxiety_level (no data)"
        assert (
            "focus_level" not in summaries
        ), "Should not include focus_level (no data)"
        assert (
            "sleep_schedule" not in summaries
        ), "Should not include sleep_schedule (no data)"

        # Verify counts are correct
        assert summaries["mood"]["count"] == 2, "Mood should have count of 2"
        assert summaries["energy"]["count"] == 1, "Energy should have count of 1"
        assert (
            summaries["stress_level"]["count"] == 1
        ), "Stress level should have count of 1"

    @pytest.mark.behavior
    @pytest.mark.analytics
    @pytest.mark.file_io
    def test_quantitative_analytics_handles_responses_dict_format(
        self, test_data_dir, fix_user_data_loaders
    ):
        """Test that analytics handle check-in data in responses dict format."""
        user_id = "test-user-responses-dict"

        # Arrange - Create user with check-in data in responses dict format
        test_user = TestUserFactory.create_basic_user(
            user_id, test_data_dir=test_data_dir
        )

        # Get the actual UUID for the user
        actual_user_id = get_user_id_by_identifier(user_id)
        assert actual_user_id is not None, "User should be created and resolvable"

        # Enable quantitative fields
        checkin_settings = {
            "questions": {
                "mood": {"enabled": True, "type": "scale_1_5"},
                "energy": {"enabled": True, "type": "scale_1_5"},
                "stress_level": {"enabled": True, "type": "scale_1_5"},
            }
        }

        # Save user preferences
        user_data = get_user_data(actual_user_id, "preferences") or {}
        user_data["preferences"] = {"checkin_settings": checkin_settings}
        save_user_data(actual_user_id, "preferences", user_data)

        # Create check-in data with responses dict format (use recent dates)
        from datetime import datetime, timedelta

        now = now_datetime_full()
        sample_checkins = [
            {
                "timestamp": format_timestamp(now - timedelta(days=2), TIMESTAMP_FULL),
                "responses": {"mood": "4", "energy": "3", "stress_level": "2"},
            },
            {
                "timestamp": format_timestamp(now - timedelta(days=1), TIMESTAMP_FULL),
                "responses": {"mood": "3", "energy": "4", "stress_level": "3"},
            },
        ]

        # Store check-in data in the correct UUID directory
        checkin_file = get_user_file_path(actual_user_id, "checkins")
        os.makedirs(os.path.dirname(checkin_file), exist_ok=True)
        with open(checkin_file, "w", encoding="utf-8") as f:
            json.dump(sample_checkins, f, indent=2)

        # Act - Get quantitative summaries with explicit enabled fields (use actual_user_id)
        analytics = CheckinAnalytics()
        enabled_fields = [
            "mood",
            "energy",
            "stress_level",
            "sleep_quality",
            "anxiety_level",
            "focus_level",
            "sleep_schedule",
            "ate_breakfast",
            "exercise",
        ]
        summaries = analytics.get_quantitative_summaries(
            actual_user_id, days=30, enabled_fields=enabled_fields
        )

        # Assert - Verify fields are processed correctly
        assert "error" not in summaries, f"Should not have error: {summaries}"

        # Check all fields are present
        assert "mood" in summaries, "Should include mood from responses dict"
        assert "energy" in summaries, "Should include energy from responses dict"
        assert (
            "stress_level" in summaries
        ), "Should include stress_level from responses dict"

        # Verify calculations are correct
        assert summaries["mood"]["count"] == 2, "Mood should have count of 2"
        assert summaries["mood"]["average"] == 3.5, "Mood average should be 3.5"
        assert summaries["mood"]["min"] == 3, "Mood min should be 3"
        assert summaries["mood"]["max"] == 4, "Mood max should be 4"

    @pytest.mark.behavior
    @pytest.mark.analytics
    @pytest.mark.file_io
    def test_quantitative_analytics_error_handling(
        self, test_data_dir, fix_user_data_loaders
    ):
        """Test that analytics handle errors gracefully."""
        user_id = "test-user-error-handling"

        # Arrange - Create user with invalid data
        test_user = TestUserFactory.create_basic_user(
            user_id, test_data_dir=test_data_dir
        )

        # Get the actual UUID for the user
        # Retry lookup in case of race conditions with index updates in parallel execution
        import time

        actual_user_id = None
        for attempt in range(5):
            actual_user_id = get_user_id_by_identifier(user_id)
            if actual_user_id is not None:
                break
            if attempt < 4:
                time.sleep(0.1)  # Brief delay before retry
        assert (
            actual_user_id is not None
        ), f"User should be created and resolvable after index update (attempted {user_id})"

        # Enable quantitative fields
        checkin_settings = {
            "questions": {
                "mood": {"enabled": True, "type": "scale_1_5"},
                "energy": {"enabled": True, "type": "scale_1_5"},
            }
        }

        # Save user preferences
        user_data = get_user_data(actual_user_id, "preferences") or {}
        user_data["preferences"] = {"checkin_settings": checkin_settings}
        save_user_data(actual_user_id, "preferences", user_data)

        # Create check-in data with invalid values (use recent dates)
        from datetime import datetime, timedelta

        now = now_datetime_full()
        sample_checkins = [
            {
                "timestamp": format_timestamp(now - timedelta(days=2), TIMESTAMP_FULL),
                "mood": "invalid",  # Invalid value
                "energy": 3,
            },
            {
                "timestamp": format_timestamp(now - timedelta(days=1), TIMESTAMP_FULL),
                "mood": 4,
                "energy": "not_a_number",  # Invalid value
            },
            {
                "timestamp": format_timestamp(now, TIMESTAMP_FULL),
                "mood": 5,
                "energy": 4,
            },
        ]

        # Store check-in data in the correct UUID directory
        checkin_file = get_user_file_path(actual_user_id, "checkins")
        os.makedirs(os.path.dirname(checkin_file), exist_ok=True)
        with open(checkin_file, "w", encoding="utf-8") as f:
            json.dump(sample_checkins, f, indent=2)

        # Act - Get quantitative summaries with explicit enabled fields (use actual_user_id)
        analytics = CheckinAnalytics()
        enabled_fields = [
            "mood",
            "energy",
            "stress_level",
            "sleep_quality",
            "anxiety_level",
            "focus_level",
            "sleep_schedule",
            "ate_breakfast",
            "exercise",
        ]
        summaries = analytics.get_quantitative_summaries(
            actual_user_id, days=30, enabled_fields=enabled_fields
        )

        # Assert - Verify only valid data is processed
        assert "error" not in summaries, f"Should not have error: {summaries}"

        # Check that only valid data is included
        assert "mood" in summaries, "Should include mood with valid data"
        assert "energy" in summaries, "Should include energy with valid data"

        # Verify counts reflect only valid data
        assert (
            summaries["mood"]["count"] == 2
        ), "Mood should have count of 2 (valid entries only)"
        assert (
            summaries["energy"]["count"] == 2
        ), "Energy should have count of 2 (valid entries only)"

        # Verify calculations are correct for valid data
        assert (
            summaries["mood"]["average"] == 4.5
        ), "Mood average should be 4.5 (4 and 5)"
        assert (
            summaries["energy"]["average"] == 3.5
        ), "Energy average should be 3.5 (3 and 4)"
