#!/usr/bin/env python3
"""
Test Coverage Expansion for Core Message Management
Tests for core/message_management.py to improve coverage from 68% to 75%
"""

import json
import os
import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from core.message_management import (
    get_message_categories,
    load_default_messages,
    _normalize_message_timestamps,
    _parse_message_timestamp,
    get_timestamp_for_sorting,
)


class TestCoreMessageManagementCoverageExpansion:
    """Test class for Core Message Management coverage expansion."""

    @pytest.mark.behavior
    def test_get_message_categories_from_env_real_behavior(self):
        """Test getting message categories from environment variable."""
        with patch.dict(os.environ, {"CATEGORIES": "motivational,health,sleep"}):
            # [OK] VERIFY REAL BEHAVIOR: Categories retrieved from environment
            result = get_message_categories()

            assert isinstance(result, list)
            assert "motivational" in result
            assert "health" in result
            assert "sleep" in result

    @pytest.mark.behavior
    def test_get_message_categories_from_json_real_behavior(self):
        """Test getting message categories from JSON format."""
        with patch.dict(
            os.environ, {"CATEGORIES": '["motivational", "health", "sleep"]'}
        ):
            # [OK] VERIFY REAL BEHAVIOR: Categories retrieved from JSON
            result = get_message_categories()

            assert isinstance(result, list)
            assert "motivational" in result
            assert "health" in result
            assert "sleep" in result

    @pytest.mark.behavior
    def test_get_message_categories_no_env_real_behavior(self):
        """Test getting message categories when no environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            # [OK] VERIFY REAL BEHAVIOR: Returns empty list when no categories
            result = get_message_categories()

            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.behavior
    def test_load_default_messages_real_behavior(self):
        """Test loading default messages for a category."""
        # [OK] VERIFY REAL BEHAVIOR: Default messages loaded successfully
        result = load_default_messages("motivational")

        assert isinstance(result, list)
        # The actual function loads real data, so we just verify it's a list
        assert len(result) > 0

    @pytest.mark.behavior
    def test_load_default_messages_file_not_found_real_behavior(self):
        """Test loading default messages when file doesn't exist."""
        # [OK] VERIFY REAL BEHAVIOR: Returns empty list when file not found
        result = load_default_messages("nonexistent_category")

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.behavior
    def test_parse_timestamp_strict_format(self):
        """Ensure only canonical TIMESTAMP_FULL values are accepted."""
        timestamp_str = "2023-01-01 10:00:00"
        result = _parse_message_timestamp(timestamp_str)

        assert isinstance(result, datetime)
        assert result.tzinfo == timezone.utc
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 1

        sentinel = _parse_message_timestamp("2023-01-01T10:00:00Z")
        assert sentinel == datetime.min.replace(tzinfo=timezone.utc)

    @pytest.mark.behavior
    def test_normalize_message_timestamps_rewrites_compatibility_values(self, tmp_path):
        """Normalize compatibility timestamp shapes before other processing runs."""
        file_path = tmp_path / "sent_messages.json"
        data = {
            "messages": [
                {"message_id": "a", "timestamp": "2023-02-03T04:05:06Z"},
                {"message_id": "b", "timestamp": "2023-02-03 04:05:06"},
            ]
        }
        file_path.write_text(json.dumps(data))

        normalized = _normalize_message_timestamps(data, file_path)
        assert normalized is True

        saved = json.loads(file_path.read_text())
        assert saved["messages"][0]["timestamp"] == "2023-02-03 04:05:06"
        assert saved["messages"][1]["timestamp"] == "2023-02-03 04:05:06"

    @pytest.mark.behavior
    def test_get_timestamp_for_sorting_real_behavior(self):
        """Test getting timestamp for sorting."""
        # Test with timestamp string
        result = get_timestamp_for_sorting({"timestamp": "2023-01-01 10:00:00"})

        assert isinstance(result, float)
        assert result > 0  # Should be a valid timestamp

    @pytest.mark.behavior
    def test_get_timestamp_for_sorting_string_real_behavior(self):
        """Test getting timestamp for sorting with string timestamp."""
        # Test with string timestamp
        result = get_timestamp_for_sorting({"timestamp": "2023-01-01 10:00:00"})

        assert isinstance(result, float)
        assert result > 0  # Should be a valid timestamp

    @pytest.mark.behavior
    def test_get_timestamp_for_sorting_invalid_item_real_behavior(self):
        """Test getting timestamp for sorting with invalid item type."""
        # Test with string item (not dict)
        result = get_timestamp_for_sorting("invalid")

        # Should return 0.0 for invalid items
        assert isinstance(result, float)
        assert result == 0.0
