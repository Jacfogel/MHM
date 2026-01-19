#!/usr/bin/env python3
"""
Test Coverage Expansion for Core Message Management
Tests for core/message_management.py to improve coverage from 68% to 75%
"""

import pytest
import os
from unittest.mock import patch
from datetime import datetime

from core.message_management import (
    get_message_categories,
    load_default_messages,
    _parse_timestamp,
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
    def test_parse_timestamp_real_behavior(self):
        """
        LEGACY COMPATIBILITY:
        Verify backward support for ISO/Z-style timestamps that may exist in historical persisted
        sent_messages data.

        NOTE: This test intentionally calls the private helper to assert legacy parsing behavior.
        """
        # [OK] VERIFY REAL BEHAVIOR: Timestamp parsing works correctly
        # ISO/Z-style timestamp (NOT TIMESTAMP_FULL) - maintained for historical compatibility
        timestamp_str = "2023-01-01T10:00:00Z"
        result = _parse_timestamp(timestamp_str)

        assert isinstance(result, datetime)
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 1

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
