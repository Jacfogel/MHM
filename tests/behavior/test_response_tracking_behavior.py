"""
Behavior tests for response tracking module.
Focuses on real behavior, side effects, and actual system changes.
"""

import pytest
import os
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from core.response_tracking import (
    store_user_response,
    store_daily_checkin_response,
    store_chat_interaction,
    get_recent_responses,
    get_recent_daily_checkins,
    get_recent_chat_interactions,
    get_user_checkin_preferences,
    is_user_checkins_enabled,
    get_user_checkin_questions,
    get_user_info_for_tracking,
    track_user_response
)


class TestResponseTrackingBehavior:
    """Test response tracking real behavior and side effects."""

    def test_store_user_response_creates_files(self, test_data_dir):
        """Test that storing user response actually creates data files."""
        # Arrange
        user_id = "test-user"
        response_data = {
            "mood": "happy",
            "energy": 8,
            "notes": "Feeling great today!"
        }
        response_type = "daily_checkin"
        
        # Mock get_user_file_path to point to test directory
        expected_file = os.path.join(test_data_dir, "users", user_id, "daily_checkins.json")
        
        # Act
        with patch('core.response_tracking.get_user_file_path', return_value=expected_file):
            store_user_response(user_id, response_data, response_type)
        
        # Assert - Verify file was created
        assert os.path.exists(expected_file), "Response log file should be created"
        
        # Verify data was saved correctly
        with open(expected_file, 'r') as f:
            saved_data = json.load(f)
        
        assert isinstance(saved_data, list), "Data should be stored as a list"
        assert len(saved_data) == 1, "Should have one response entry"
        assert saved_data[0]["mood"] == "happy", "Response data should be saved correctly"
        assert "timestamp" in saved_data[0], "Timestamp should be added automatically"

    def test_store_daily_checkin_response_persists_data(self, test_data_dir):
        """Test that daily check-in responses are properly persisted."""
        # Arrange
        user_id = "test-user-2"  # Use unique user ID for isolation
        checkin_data = {
            "mood": "calm",
            "sleep_hours": 7,
            "medication_taken": True,
            "goals_met": 3
        }
        
        # Mock get_user_file_path to point to test directory
        expected_file = os.path.join(test_data_dir, "users", user_id, "daily_checkins.json")
        
        # Act
        with patch('core.response_tracking.get_user_file_path', return_value=expected_file):
            store_daily_checkin_response(user_id, checkin_data)
        
        # Assert - Verify data was saved to correct location
        assert os.path.exists(expected_file), "Daily check-in file should be created"
        
        # Verify data structure
        with open(expected_file, 'r') as f:
            saved_data = json.load(f)
        
        assert len(saved_data) == 1, "Should have one check-in entry"
        saved_checkin = saved_data[0]
        assert saved_checkin["mood"] == "calm", "Mood should be saved"
        assert saved_checkin["sleep_hours"] == 7, "Sleep hours should be saved"
        assert saved_checkin["medication_taken"] is True, "Medication status should be saved"
        assert saved_checkin["goals_met"] == 3, "Goals met should be saved"

    def test_store_chat_interaction_creates_interaction_log(self, test_data_dir):
        """Test that chat interactions are stored with proper metadata."""
        # Arrange
        user_id = "test-user-3"  # Use unique user ID for isolation
        user_message = "How are you today?"
        ai_response = "I'm doing well, thank you for asking! How are you feeling?"
        context_used = True
        
        # Mock get_user_file_path to point to test directory
        expected_file = os.path.join(test_data_dir, "users", user_id, "chat_interactions.json")
        
        # Act
        with patch('core.response_tracking.get_user_file_path', return_value=expected_file):
            store_chat_interaction(user_id, user_message, ai_response, context_used)
        
        # Assert - Verify interaction log was created
        assert os.path.exists(expected_file), "Chat interaction file should be created"
        
        # Verify interaction data
        with open(expected_file, 'r') as f:
            saved_data = json.load(f)
        
        assert len(saved_data) == 1, "Should have one interaction entry"
        interaction = saved_data[0]
        assert interaction["user_message"] == user_message, "User message should be saved"
        assert interaction["ai_response"] == ai_response, "AI response should be saved"
        assert interaction["context_used"] is True, "Context flag should be saved"
        assert interaction["message_length"] == len(user_message), "Message length should be calculated"
        assert interaction["response_length"] == len(ai_response), "Response length should be calculated"
        assert "timestamp" in interaction, "Timestamp should be added"

    def test_get_recent_responses_returns_ordered_data(self, test_data_dir):
        """Test that getting recent responses returns properly ordered data."""
        # Arrange
        user_id = "test-user-4"  # Use unique user ID for isolation
        response_type = "daily_checkin"
        
        # Create test data with timestamps
        test_responses = [
            {"mood": "happy", "timestamp": "2025-07-30 10:00:00"},
            {"mood": "sad", "timestamp": "2025-07-30 14:00:00"},
            {"mood": "calm", "timestamp": "2025-07-30 18:00:00"}
        ]
        
        # Save test data
        log_file = os.path.join(test_data_dir, "users", user_id, "daily_checkins.json")
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'w') as f:
            json.dump(test_responses, f)
        
        # Act
        with patch('core.response_tracking.get_user_file_path', return_value=log_file):
            recent_responses = get_recent_responses(user_id, response_type, limit=2)
        
        # Assert - Verify data is returned in correct order (most recent first)
        assert len(recent_responses) == 2, "Should return 2 responses"
        assert recent_responses[0]["mood"] == "calm", "Most recent should be first"
        assert recent_responses[1]["mood"] == "sad", "Second most recent should be second"

    def test_get_recent_daily_checkins_returns_checkin_data(self, test_data_dir):
        """Test that getting recent daily check-ins returns correct data."""
        # Arrange
        user_id = "test-user-5"  # Use unique user ID for isolation
        
        # Create test check-in data
        test_checkins = [
            {"mood": "happy", "sleep_hours": 8, "timestamp": "2025-07-30 09:00:00"},
            {"mood": "tired", "sleep_hours": 6, "timestamp": "2025-07-29 09:00:00"},
            {"mood": "energetic", "sleep_hours": 7, "timestamp": "2025-07-28 09:00:00"}
        ]
        
        # Save test data
        log_file = os.path.join(test_data_dir, "users", user_id, "daily_checkins.json")
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'w') as f:
            json.dump(test_checkins, f)
        
        # Act
        with patch('core.response_tracking.get_user_file_path', return_value=log_file):
            recent_checkins = get_recent_daily_checkins(user_id, limit=2)
        
        # Assert
        assert len(recent_checkins) == 2, "Should return 2 check-ins"
        assert recent_checkins[0]["mood"] == "happy", "Most recent check-in should be first"
        assert recent_checkins[0]["sleep_hours"] == 8, "Sleep hours should be included"

    def test_get_recent_chat_interactions_returns_interaction_data(self, test_data_dir):
        """Test that getting recent chat interactions returns correct data."""
        # Arrange
        user_id = "test-user-6"  # Use unique user ID for isolation
        
        # Create test interaction data
        test_interactions = [
            {
                "user_message": "Hello",
                "ai_response": "Hi there!",
                "context_used": False,
                "timestamp": "2025-07-30 15:00:00"
            },
            {
                "user_message": "How are you?",
                "ai_response": "I'm doing well!",
                "context_used": True,
                "timestamp": "2025-07-30 14:00:00"
            }
        ]
        
        # Save test data
        log_file = os.path.join(test_data_dir, "users", user_id, "chat_interactions.json")
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'w') as f:
            json.dump(test_interactions, f)
        
        # Act
        with patch('core.response_tracking.get_user_file_path', return_value=log_file):
            recent_interactions = get_recent_chat_interactions(user_id, limit=2)
        
        # Assert
        assert len(recent_interactions) == 2, "Should return 2 interactions"
        assert recent_interactions[0]["user_message"] == "Hello", "Most recent interaction should be first"
        assert recent_interactions[1]["context_used"] is True, "Context flag should be preserved"

    def test_get_user_checkin_preferences_returns_user_data(self, test_data_dir):
        """Test that getting user check-in preferences returns correct data."""
        # Arrange
        user_id = "test-user-7"  # Use unique user ID for isolation
        
        # Create test user data with check-in preferences
        user_data = {
            "preferences": {
                "checkin_settings": {
                    "enabled": True,
                    "frequency": "daily",
                    "questions": ["mood", "sleep", "medication"]
                }
            }
        }
        
        # Act
        with patch('core.response_tracking.get_user_data', return_value=user_data):
            preferences = get_user_checkin_preferences(user_id)
        
        # Assert
        assert preferences["enabled"] is True, "Check-ins should be enabled"
        assert preferences["frequency"] == "daily", "Frequency should be daily"
        assert "mood" in preferences["questions"], "Questions should include mood"

    def test_is_user_checkins_enabled_returns_correct_status(self, test_data_dir):
        """Test that checking if user check-ins are enabled returns correct status."""
        # Arrange
        user_id = "test-user-8"  # Use unique user ID for isolation
        
        # Test case 1: Check-ins enabled
        user_data_enabled = {
            "account": {
                "features": {
                    "checkins": "enabled"
                }
            }
        }
        
        # Test case 2: Check-ins disabled
        user_data_disabled = {
            "account": {
                "features": {
                    "messages": "enabled"
                }
            }
        }
        
        # Act & Assert - Test enabled case
        with patch('core.response_tracking.get_user_data', return_value=user_data_enabled):
            enabled_status = is_user_checkins_enabled(user_id)
            assert enabled_status is True, "Check-ins should be enabled"
        
        # Act & Assert - Test disabled case
        with patch('core.response_tracking.get_user_data', return_value=user_data_disabled):
            disabled_status = is_user_checkins_enabled(user_id)
            assert disabled_status is False, "Check-ins should be disabled"

    def test_get_user_checkin_questions_returns_questions(self, test_data_dir):
        """Test that getting user check-in questions returns correct data."""
        # Arrange
        user_id = "test-user-9"  # Use unique user ID for isolation
        
        # Create test user data with check-in questions
        user_data = {
            "preferences": {
                "checkin_settings": {
                    "questions": {
                        "mood": {"type": "scale", "range": "1-10"},
                        "sleep": {"type": "number", "unit": "hours"},
                        "medication": {"type": "boolean"}
                    }
                }
            }
        }
        
        # Act
        with patch('core.response_tracking.get_user_data', return_value=user_data):
            questions = get_user_checkin_questions(user_id)
        
        # Assert
        assert "mood" in questions, "Questions should include mood"
        assert questions["mood"]["type"] == "scale", "Mood should be scale type"
        assert "sleep" in questions, "Questions should include sleep"
        assert questions["sleep"]["unit"] == "hours", "Sleep should have hours unit"

    def test_get_user_info_for_tracking_returns_complete_data(self, test_data_dir):
        """Test that getting user info for tracking returns complete user data."""
        # Arrange
        user_id = "test-user-10"  # Use unique user ID for isolation
        
        # Create comprehensive test user data
        user_data_account = {
            "account": {
                "internal_username": user_id,
                "created_at": "2025-01-01",
                "last_updated": "2025-07-30"
            }
        }
        
        user_data_prefs = {
            "preferences": {
                "categories": ["health", "work"],
                "channel": {
                    "type": "discord"
                }
            }
        }
        
        user_data_context = {
            "context": {
                "preferred_name": "Test User"
            }
        }
        
        # Act
        with patch('core.response_tracking.get_user_data') as mock_get:
            mock_get.side_effect = [user_data_account, user_data_prefs, user_data_context]
            tracking_info = get_user_info_for_tracking(user_id)
        
        # Assert
        assert tracking_info["user_id"] == user_id, "User ID should be included"
        assert tracking_info["internal_username"] == user_id, "Internal username should be included"
        assert tracking_info["preferred_name"] == "Test User", "Preferred name should be included"
        assert "health" in tracking_info["categories"], "Categories should be included"
        assert tracking_info["messaging_service"] == "discord", "Messaging service should be included"

    def test_track_user_response_integrates_with_storage(self, test_data_dir):
        """Test that track_user_response properly integrates with storage functions."""
        # Arrange
        user_id = "test-user-11"  # Use unique user ID for isolation
        category = "daily_checkin"
        response_data = {"mood": "excited", "energy": 9}
        
        # Mock get_user_file_path to point to test directory
        expected_file = os.path.join(test_data_dir, "users", user_id, "daily_checkins.json")
        
        # Act
        with patch('core.response_tracking.get_user_file_path', return_value=expected_file):
            with patch('core.response_tracking.get_user_data', return_value={"account": {"internal_username": user_id}}):
                track_user_response(user_id, category, response_data)
        
        # Assert - Verify data was stored (file should exist after storage)
        assert os.path.exists(expected_file), "Response should be stored"
        
        # Verify stored data
        with open(expected_file, 'r') as f:
            saved_data = json.load(f)
        
        assert len(saved_data) == 1, "Should have one response entry"
        assert saved_data[0]["mood"] == "excited", "Response data should be stored correctly"

    def test_response_tracking_with_multiple_entries(self, test_data_dir):
        """Test that multiple responses are properly tracked and ordered."""
        # Arrange
        user_id = "test-user-12"  # Use unique user ID for isolation
        response_type = "daily_checkin"
        
        # Mock get_user_file_path to point to test directory
        expected_file = os.path.join(test_data_dir, "users", user_id, "daily_checkins.json")
        
        # Store multiple responses with explicit timestamps to control order
        responses = [
            {"mood": "happy", "energy": 8, "timestamp": "2025-07-30 10:00:00"},
            {"mood": "calm", "energy": 6, "timestamp": "2025-07-30 11:00:00"},
            {"mood": "excited", "energy": 9, "timestamp": "2025-07-30 12:00:00"}
        ]
        
        # Act - Store responses
        with patch('core.response_tracking.get_user_file_path', return_value=expected_file):
            for response in responses:
                store_user_response(user_id, response, response_type)
            
            # Get recent responses
            recent_responses = get_recent_responses(user_id, response_type, limit=3)
        
        # Assert
        assert len(recent_responses) == 3, "Should return all 3 responses"
        # Most recent should be first (excited - 12:00:00)
        assert recent_responses[0]["mood"] == "excited", "Most recent should be first"
        assert recent_responses[2]["mood"] == "happy", "Oldest should be last"

    def test_response_tracking_error_handling(self, test_data_dir):
        """Test that response tracking handles errors gracefully."""
        # Arrange
        user_id = "test-user-13"  # Use unique user ID for isolation
        response_data = {"mood": "happy"}
        
        # Act - Test with invalid file path (should handle gracefully)
        with patch('core.response_tracking.get_user_file_path', side_effect=Exception("File error")):
            # Should not raise exception due to error handling
            result = store_user_response(user_id, response_data, "daily_checkin")
        
        # Assert - Function should handle error gracefully
        assert result is None, "Should return None on error"

    def test_chat_interaction_metadata_calculation(self, test_data_dir):
        """Test that chat interaction metadata is calculated correctly."""
        # Arrange
        user_id = "test-user-14"  # Use unique user ID for isolation
        user_message = "This is a test message with some content"
        ai_response = "This is a longer AI response that should be tracked properly"
        context_used = False
        
        # Mock get_user_file_path to point to test directory
        expected_file = os.path.join(test_data_dir, "users", user_id, "chat_interactions.json")
        
        # Act
        with patch('core.response_tracking.get_user_file_path', return_value=expected_file):
            store_chat_interaction(user_id, user_message, ai_response, context_used)
        
        # Assert - Verify metadata calculations
        with open(expected_file, 'r') as f:
            saved_data = json.load(f)
        
        interaction = saved_data[0]
        assert interaction["message_length"] == len(user_message), "Message length should be calculated"
        assert interaction["response_length"] == len(ai_response), "Response length should be calculated"
        assert interaction["context_used"] is False, "Context flag should be preserved"

    def test_response_tracking_file_structure(self, test_data_dir):
        """Test that response tracking creates proper file structure."""
        # Arrange
        user_id = "test-user-15"  # Use unique user ID for isolation
        
        # Mock get_user_file_path to point to test directory
        checkin_file = os.path.join(test_data_dir, "users", user_id, "daily_checkins.json")
        interaction_file = os.path.join(test_data_dir, "users", user_id, "chat_interactions.json")
        
        # Act - Store different types of responses
        with patch('core.response_tracking.get_user_file_path') as mock_path:
            mock_path.side_effect = [checkin_file, interaction_file]
            store_daily_checkin_response(user_id, {"mood": "happy"})
            store_chat_interaction(user_id, "Hello", "Hi there!", False)
        
        # Assert - Verify file structure
        user_dir = os.path.join(test_data_dir, "users", user_id)
        assert os.path.exists(user_dir), "User directory should be created"
        
        assert os.path.exists(checkin_file), "Daily check-ins file should exist"
        assert os.path.exists(interaction_file), "Chat interactions file should exist"

    def test_response_tracking_data_integrity(self, test_data_dir):
        """Test that response tracking maintains data integrity."""
        # Arrange
        user_id = "test-user-16"  # Use unique user ID for isolation
        original_data = {"mood": "happy", "energy": 8, "notes": "Original entry", "timestamp": "2025-07-30 10:00:00"}
        additional_data = {"mood": "calm", "energy": 6, "notes": "Additional entry", "timestamp": "2025-07-30 11:00:00"}
        
        # Mock get_user_file_path to point to test directory
        expected_file = os.path.join(test_data_dir, "users", user_id, "daily_checkins.json")
        
        # Act - Store initial data
        with patch('core.response_tracking.get_user_file_path', return_value=expected_file):
            store_user_response(user_id, original_data, "daily_checkin")
            
            # Store additional data
            store_user_response(user_id, additional_data, "daily_checkin")
            
            # Get recent responses
            recent_responses = get_recent_responses(user_id, "daily_checkin", limit=10)
        
        # Assert - Verify both entries are preserved
        assert len(recent_responses) == 2, "Both entries should be preserved"
        
        # Verify additional data integrity (newer entry should be first)
        additional_entry = recent_responses[0]  # Newer entry
        assert additional_entry["mood"] == "calm", "Additional mood should be preserved"
        assert additional_entry["energy"] == 6, "Additional energy should be preserved"
        assert additional_entry["notes"] == "Additional entry", "Additional notes should be preserved"
        
        # Verify original data integrity (older entry should be last)
        original_entry = recent_responses[1]  # Older entry
        assert original_entry["mood"] == "happy", "Original mood should be preserved"
        assert original_entry["energy"] == 8, "Original energy should be preserved"
        assert original_entry["notes"] == "Original entry", "Original notes should be preserved" 