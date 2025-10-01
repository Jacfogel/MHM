"""
Behavior tests for Comprehensive Quantitative Analytics.
Tests that ALL quantitative questions from questions.json are included in analytics.
"""

import pytest
import json
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from core.checkin_analytics import CheckinAnalytics
from core.user_data_handlers import get_user_data, save_user_data
from tests.test_utilities import TestUserFactory


class TestComprehensiveQuantitativeAnalytics:
    """Test that analytics include ALL quantitative questions from questions.json."""
    
    @pytest.mark.behavior
    @pytest.mark.analytics
    @pytest.mark.file_io
    @pytest.mark.critical
    def test_all_quantitative_questions_included(self, test_data_dir, fix_user_data_loaders):
        """Test that analytics include all quantitative questions from questions.json."""
        user_id = "test-user-comprehensive"
        
        # Arrange - Create user with all quantitative questions enabled
        test_user = TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        # Enable ALL quantitative questions from questions.json
        checkin_settings = {
            "questions": {
                # Scale 1-5 questions
                "mood": {"enabled": True, "type": "scale_1_5"},
                "energy": {"enabled": True, "type": "scale_1_5"},
                "stress_level": {"enabled": True, "type": "scale_1_5"},
                "sleep_quality": {"enabled": True, "type": "scale_1_5"},
                "anxiety_level": {"enabled": True, "type": "scale_1_5"},
                "focus_level": {"enabled": True, "type": "scale_1_5"},
                # Number questions
                "sleep_hours": {"enabled": True, "type": "number"},
                # Yes/No questions (should be converted to 0/1)
                "ate_breakfast": {"enabled": True, "type": "yes_no"},
                "brushed_teeth": {"enabled": True, "type": "yes_no"},
                "medication_taken": {"enabled": True, "type": "yes_no"},
                "exercise": {"enabled": True, "type": "yes_no"},
                "hydration": {"enabled": True, "type": "yes_no"},
                "social_interaction": {"enabled": True, "type": "yes_no"},
                # Non-quantitative (should be ignored)
                "daily_reflection": {"enabled": True, "type": "optional_text"}
            }
        }
        
        # Save user preferences
        user_data = get_user_data(user_id, 'preferences') or {}
        user_data['preferences'] = {'checkin_settings': checkin_settings}
        save_user_data(user_id, 'preferences', user_data)
        
        # Create sample check-in data with all quantitative fields
        sample_checkins = [
            {
                "timestamp": "2025-10-01 08:00:00",
                # Scale 1-5 questions
                "mood": 4,
                "energy": 3,
                "stress_level": 2,
                "sleep_quality": 4,
                "anxiety_level": 1,
                "focus_level": 4,
                # Number questions
                "sleep_hours": 7.5,
                # Yes/No questions
                "ate_breakfast": "yes",
                "brushed_teeth": "yes",
                "medication_taken": "no",
                "exercise": "no",
                "hydration": "yes",
                "social_interaction": "yes",
                # Non-quantitative
                "daily_reflection": "Feeling good today"
            },
            {
                "timestamp": "2025-10-02 08:00:00",
                # Scale 1-5 questions
                "mood": 3,
                "energy": 4,
                "stress_level": 3,
                "sleep_quality": 3,
                "anxiety_level": 2,
                "focus_level": 3,
                # Number questions
                "sleep_hours": 6.0,
                # Yes/No questions
                "ate_breakfast": "no",
                "brushed_teeth": "yes",
                "medication_taken": "yes",
                "exercise": "yes",
                "hydration": "no",
                "social_interaction": "no",
                # Non-quantitative
                "daily_reflection": "Had a rough day"
            }
        ]
        
        # Store check-in data
        checkin_file = os.path.join(test_data_dir, "users", user_id, "checkins.json")
        os.makedirs(os.path.dirname(checkin_file), exist_ok=True)
        with open(checkin_file, 'w', encoding='utf-8') as f:
            json.dump(sample_checkins, f, indent=2)
        
        # Act - Get quantitative summaries with explicit enabled fields
        analytics = CheckinAnalytics()
        enabled_fields = [
            'mood', 'energy', 'stress_level', 'sleep_quality', 'anxiety_level', 
            'focus_level', 'sleep_hours', 'ate_breakfast', 'brushed_teeth', 
            'medication_taken', 'exercise', 'hydration', 'social_interaction'
        ]
        summaries = analytics.get_quantitative_summaries(user_id, days=30, enabled_fields=enabled_fields)
        
        # Assert - Verify all quantitative fields are included
        assert "error" not in summaries, f"Should not have error: {summaries}"
        
        # Check that all quantitative fields are present
        expected_fields = [
            # Scale 1-5 questions
            'mood', 'energy', 'stress_level', 'sleep_quality', 'anxiety_level', 'focus_level',
            # Number questions
            'sleep_hours',
            # Yes/No questions (converted to 0/1)
            'ate_breakfast', 'brushed_teeth', 'medication_taken', 'exercise', 'hydration', 'social_interaction'
        ]
        
        for field in expected_fields:
            assert field in summaries, f"Should include {field} in analytics"
            
            # Verify field has proper structure
            field_stats = summaries[field]
            assert 'average' in field_stats, f"{field} should have average"
            assert 'min' in field_stats, f"{field} should have min"
            assert 'max' in field_stats, f"{field} should have max"
            assert 'count' in field_stats, f"{field} should have count"
            assert field_stats['count'] == 2, f"{field} should have count of 2"
        
        # Verify non-quantitative fields are not included
        assert 'daily_reflection' not in summaries, "Non-quantitative fields should not be included"
        
        # Verify specific calculations for scale 1-5 questions
        assert summaries['mood']['average'] == 3.5, "Mood average should be 3.5"
        assert summaries['mood']['min'] == 3, "Mood min should be 3"
        assert summaries['mood']['max'] == 4, "Mood max should be 4"
        
        # Verify specific calculations for number questions
        assert summaries['sleep_hours']['average'] == 6.75, "Sleep hours average should be 6.75"
        assert summaries['sleep_hours']['min'] == 6.0, "Sleep hours min should be 6.0"
        assert summaries['sleep_hours']['max'] == 7.5, "Sleep hours max should be 7.5"
        
        # Verify specific calculations for yes/no questions (converted to 0/1)
        assert summaries['ate_breakfast']['average'] == 0.5, "Breakfast average should be 0.5 (1 yes, 1 no)"
        assert summaries['ate_breakfast']['min'] == 0.0, "Breakfast min should be 0.0"
        assert summaries['ate_breakfast']['max'] == 1.0, "Breakfast max should be 1.0"
        
        assert summaries['exercise']['average'] == 0.5, "Exercise average should be 0.5 (1 yes, 1 no)"
        assert summaries['exercise']['min'] == 0.0, "Exercise min should be 0.0"
        assert summaries['exercise']['max'] == 1.0, "Exercise max should be 1.0"
    
    @pytest.mark.behavior
    @pytest.mark.analytics
    @pytest.mark.file_io
    def test_yes_no_questions_converted_correctly(self, test_data_dir, fix_user_data_loaders):
        """Test that yes/no questions are correctly converted to 0/1 values."""
        user_id = "test-user-yes-no"
        
        # Arrange - Create user with yes/no questions
        test_user = TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        # Create check-in data with various yes/no formats
        sample_checkins = [
            {
                "timestamp": "2025-10-01 08:00:00",
                "ate_breakfast": "yes",
                "exercise": "no",
                "medication_taken": "y",
                "hydration": "n"
            },
            {
                "timestamp": "2025-10-02 08:00:00",
                "ate_breakfast": "YES",
                "exercise": "NO",
                "medication_taken": "true",
                "hydration": "false"
            },
            {
                "timestamp": "2025-10-03 08:00:00",
                "ate_breakfast": "1",
                "exercise": "0",
                "medication_taken": "Yes",
                "hydration": "No"
            }
        ]
        
        # Store check-in data
        checkin_file = os.path.join(test_data_dir, "users", user_id, "checkins.json")
        os.makedirs(os.path.dirname(checkin_file), exist_ok=True)
        with open(checkin_file, 'w', encoding='utf-8') as f:
            json.dump(sample_checkins, f, indent=2)
        
        # Act - Get quantitative summaries
        analytics = CheckinAnalytics()
        enabled_fields = ['ate_breakfast', 'exercise', 'medication_taken', 'hydration']
        summaries = analytics.get_quantitative_summaries(user_id, days=30, enabled_fields=enabled_fields)
        
        # Assert - Verify yes/no questions are converted correctly
        assert "error" not in summaries, f"Should not have error: {summaries}"
        
        # Verify all yes/no fields are present
        for field in enabled_fields:
            assert field in summaries, f"Should include {field} in analytics"
            assert summaries[field]['count'] == 3, f"{field} should have count of 3"
        
        # Verify specific conversions
        # ate_breakfast: yes, YES, 1 -> 1, 1, 1 -> average 1.0
        assert summaries['ate_breakfast']['average'] == 1.0, "Breakfast should average 1.0 (all yes)"
        assert summaries['ate_breakfast']['min'] == 1.0, "Breakfast min should be 1.0"
        assert summaries['ate_breakfast']['max'] == 1.0, "Breakfast max should be 1.0"
        
        # exercise: no, NO, 0 -> 0, 0, 0 -> average 0.0
        assert summaries['exercise']['average'] == 0.0, "Exercise should average 0.0 (all no)"
        assert summaries['exercise']['min'] == 0.0, "Exercise min should be 0.0"
        assert summaries['exercise']['max'] == 0.0, "Exercise max should be 0.0"
        
        # medication_taken: y, true, Yes -> 1, 1, 1 -> average 1.0
        assert summaries['medication_taken']['average'] == 1.0, "Medication should average 1.0 (all yes)"
        
        # hydration: n, false, No -> 0, 0, 0 -> average 0.0
        assert summaries['hydration']['average'] == 0.0, "Hydration should average 0.0 (all no)"
    
    @pytest.mark.behavior
    @pytest.mark.analytics
    @pytest.mark.file_io
    def test_responses_dict_format_with_yes_no(self, test_data_dir, fix_user_data_loaders):
        """Test that yes/no questions work correctly in responses dict format."""
        user_id = "test-user-responses-yes-no"
        
        # Arrange - Create user with responses dict format
        test_user = TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        # Create check-in data with responses dict format
        sample_checkins = [
            {
                "timestamp": "2025-10-01 08:00:00",
                "responses": {
                    "mood": "4",
                    "energy": "3",
                    "ate_breakfast": "yes",
                    "exercise": "no"
                }
            },
            {
                "timestamp": "2025-10-02 08:00:00",
                "responses": {
                    "mood": "3",
                    "energy": "4",
                    "ate_breakfast": "no",
                    "exercise": "yes"
                }
            }
        ]
        
        # Store check-in data
        checkin_file = os.path.join(test_data_dir, "users", user_id, "checkins.json")
        os.makedirs(os.path.dirname(checkin_file), exist_ok=True)
        with open(checkin_file, 'w', encoding='utf-8') as f:
            json.dump(sample_checkins, f, indent=2)
        
        # Act - Get quantitative summaries
        analytics = CheckinAnalytics()
        enabled_fields = ['mood', 'energy', 'ate_breakfast', 'exercise']
        summaries = analytics.get_quantitative_summaries(user_id, days=30, enabled_fields=enabled_fields)
        
        # Assert - Verify fields are processed correctly
        assert "error" not in summaries, f"Should not have error: {summaries}"
        
        # Check all fields are present
        for field in enabled_fields:
            assert field in summaries, f"Should include {field} from responses dict"
            assert summaries[field]['count'] == 2, f"{field} should have count of 2"
        
        # Verify calculations are correct
        assert summaries['mood']['average'] == 3.5, "Mood average should be 3.5"
        assert summaries['energy']['average'] == 3.5, "Energy average should be 3.5"
        
        # Verify yes/no conversions in responses dict
        assert summaries['ate_breakfast']['average'] == 0.5, "Breakfast average should be 0.5 (1 yes, 1 no)"
        assert summaries['exercise']['average'] == 0.5, "Exercise average should be 0.5 (1 yes, 1 no)"
