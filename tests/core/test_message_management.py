"""
Tests for core/message_management.py
"""

import pytest
import os
import json
from unittest.mock import patch, Mock
from datetime import datetime
from core.message_management import (
    get_message_categories,
    load_default_messages,
    store_sent_message
)


class TestGetMessageCategories:
    """Test get_message_categories function."""
    
    def test_get_message_categories_from_json(self):
        """Test getting categories from JSON format."""
        with patch.dict(os.environ, {'CATEGORIES': '["motivational", "reminder", "checkin"]'}):
            result = get_message_categories()
            assert result == ["motivational", "reminder", "checkin"]
    
    def test_get_message_categories_from_comma_separated(self):
        """Test getting categories from comma-separated format."""
        with patch.dict(os.environ, {'CATEGORIES': 'motivational,reminder,checkin'}):
            result = get_message_categories()
            assert result == ["motivational", "reminder", "checkin"]
    
    def test_get_message_categories_empty(self):
        """Test getting categories when CATEGORIES is empty."""
        with patch.dict(os.environ, {'CATEGORIES': ''}, clear=True):
            result = get_message_categories()
            assert result == []
    
    def test_get_message_categories_none(self):
        """Test getting categories when CATEGORIES is not set."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_message_categories()
            assert result == []


class TestStoreSentMessage:
    """Test store_sent_message function."""
    
    def test_store_sent_message_success(self):
        """Test storing a sent message successfully."""
        with patch('core.message_management.load_json_data', return_value={"sent_messages": []}):
            with patch('core.message_management.save_json_data', return_value=True):
                result = store_sent_message("test_user", "motivational", "msg1", "Test message")
                assert result is True