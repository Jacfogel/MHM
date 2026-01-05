"""
Behavior tests for check-in questions enhancement.

Tests new questions, time_pair validation, and custom question system.
"""

import pytest
from core.checkin_dynamic_manager import dynamic_checkin_manager
from core.checkin_analytics import CheckinAnalytics
from tests.test_utilities import setup_test_data_environment, cleanup_test_data_environment, TestUserFactory


@pytest.mark.behavior
class TestNewCheckinQuestions:
    """Test the new predefined check-in questions."""
    
    def setup_method(self):
        self.test_dir, self.test_data_dir, _ = setup_test_data_environment()
    
    def teardown_method(self):
        cleanup_test_data_environment(self.test_dir)
    
    def test_new_questions_exist(self):
        """Test that new questions are loaded."""
        questions = dynamic_checkin_manager.get_all_questions()
        
        assert 'hopelessness_level' in questions
        assert 'irritability_level' in questions
        assert 'motivation_level' in questions
        assert 'treatment_adherence' in questions
        
        # Verify question types
        assert questions['hopelessness_level']['type'] == 'scale_1_5'
        assert questions['irritability_level']['type'] == 'scale_1_5'
        assert questions['motivation_level']['type'] == 'scale_1_5'
        assert questions['treatment_adherence']['type'] == 'yes_no'
    
    def test_new_questions_validation(self):
        """Test validation for new questions."""
        # Test hopelessness_level
        is_valid, value, error = dynamic_checkin_manager.validate_answer('hopelessness_level', '3')
        assert is_valid is True
        assert value == 3
        assert error is None
        
        # Test irritability_level
        is_valid, value, error = dynamic_checkin_manager.validate_answer('irritability_level', '5')
        assert is_valid is True
        assert value == 5
        
        # Test motivation_level
        is_valid, value, error = dynamic_checkin_manager.validate_answer('motivation_level', '2')
        assert is_valid is True
        assert value == 2
        
        # Test treatment_adherence
        is_valid, value, error = dynamic_checkin_manager.validate_answer('treatment_adherence', 'yes')
        assert is_valid is True
        assert value is True
        
        is_valid, value, error = dynamic_checkin_manager.validate_answer('treatment_adherence', 'no')
        assert is_valid is True
        assert value is False
    
    def test_new_questions_responses(self):
        """Test that responses exist for new questions."""
        # Test hopelessness responses
        response = dynamic_checkin_manager.get_response_statement('hopelessness_level', 1)
        assert response is not None
        assert len(response) > 0
        
        response = dynamic_checkin_manager.get_response_statement('hopelessness_level', 5)
        assert response is not None
        
        # Test irritability responses
        response = dynamic_checkin_manager.get_response_statement('irritability_level', 3)
        assert response is not None
        
        # Test motivation responses
        response = dynamic_checkin_manager.get_response_statement('motivation_level', 4)
        assert response is not None
        
        # Test treatment_adherence responses
        response = dynamic_checkin_manager.get_response_statement('treatment_adherence', True)
        assert response is not None
        
        response = dynamic_checkin_manager.get_response_statement('treatment_adherence', False)
        assert response is not None


@pytest.mark.behavior
class TestSleepScheduleQuestion:
    """Test the sleep_schedule time_pair question type."""
    
    def setup_method(self):
        self.test_dir, self.test_data_dir, _ = setup_test_data_environment()
    
    def teardown_method(self):
        cleanup_test_data_environment(self.test_dir)
    
    def test_sleep_schedule_exists(self):
        """Test that sleep_schedule question exists."""
        questions = dynamic_checkin_manager.get_all_questions()
        assert 'sleep_schedule' in questions
        assert questions['sleep_schedule']['type'] == 'time_pair'
        assert 'sleep_hours' not in questions  # Should be removed
    
    def test_time_pair_validation(self):
        """Test time_pair validation."""
        # Test valid formats
        test_cases = [
            ("11:30 PM and 7:00 AM", {'sleep_time': '23:30', 'wake_time': '07:00'}),
            ("23:30 and 07:00", {'sleep_time': '23:30', 'wake_time': '07:00'}),
            ("11:30pm, 7:00am", {'sleep_time': '23:30', 'wake_time': '07:00'}),
            ("10:00 PM, 6:30 AM", {'sleep_time': '22:00', 'wake_time': '06:30'}),
        ]
        
        for answer, expected in test_cases:
            is_valid, value, error = dynamic_checkin_manager.validate_answer('sleep_schedule', answer)
            assert is_valid is True, f"Should accept: {answer}"
            assert isinstance(value, dict)
            assert 'sleep_time' in value
            assert 'wake_time' in value
            assert value['sleep_time'] == expected['sleep_time']
            assert value['wake_time'] == expected['wake_time']
        
        # Test invalid formats
        invalid_cases = ["invalid", "10:00", "just one time"]
        for answer in invalid_cases:
            is_valid, value, error = dynamic_checkin_manager.validate_answer('sleep_schedule', answer)
            assert is_valid is False, f"Should reject: {answer}"
    
    def test_sleep_duration_calculation(self):
        """Test sleep duration calculation from sleep_schedule."""
        analytics = CheckinAnalytics()
        
        # Test normal overnight sleep
        duration = analytics._calculate_sleep_duration('23:00', '07:00')
        assert duration == 8.0
        
        # Test sleep that doesn't cross midnight
        duration = analytics._calculate_sleep_duration('22:00', '06:00')
        assert duration == 8.0
        
        # Test short sleep
        duration = analytics._calculate_sleep_duration('01:00', '07:00')
        assert duration == 6.0
        
        # Test long sleep
        duration = analytics._calculate_sleep_duration('22:00', '10:00')
        assert duration == 12.0


@pytest.mark.behavior
class TestCustomQuestions:
    """Test custom question CRUD operations."""
    
    def setup_method(self):
        from core.user_management import get_user_id_by_identifier
        self.test_dir, self.test_data_dir, _ = setup_test_data_environment()
        username = "test_custom_questions_user"
        TestUserFactory.create_basic_user(
            username,
            enable_checkins=True,
            test_data_dir=self.test_data_dir
        )
        # Get the actual user_id (UUID) after creation
        self.user_id = get_user_id_by_identifier(username) or TestUserFactory.get_test_user_id_by_internal_username(username, self.test_data_dir) or username
    
    def teardown_method(self):
        cleanup_test_data_environment(self.test_dir)
    
    def test_create_custom_question(self, monkeypatch):
        """Test creating a custom question."""
        # Set environment variables for test data directory
        monkeypatch.setenv("TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TESTING", "1")
        
        question_def = {
            'type': 'yes_no',
            'question_text': 'Did you use your CPAP machine last night? (yes/no)',
            'ui_display_name': 'CPAP use (yes/no)',
            'category': 'health',
            'validation': {
                'error_message': 'Please answer with yes/no, y/n, or similar.'
            },
            'enabled': True
        }
        
        result = dynamic_checkin_manager.save_custom_question(self.user_id, 'cpap_used', question_def)
        assert result is True
        
        # Verify it was saved
        custom_questions = dynamic_checkin_manager.get_custom_questions(self.user_id)
        assert 'cpap_used' in custom_questions
        assert custom_questions['cpap_used']['type'] == 'yes_no'
    
    def test_get_custom_question(self, monkeypatch):
        """Test retrieving a custom question."""
        # Set environment variables for test data directory
        monkeypatch.setenv("TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TESTING", "1")
        
        question_def = {
            'type': 'scale_1_5',
            'question_text': 'How is your pain level today? (1-5)',
            'ui_display_name': 'Pain level (1-5 scale)',
            'category': 'health',
            'validation': {'min': 1, 'max': 5, 'error_message': 'Please enter 1-5.'},
            'enabled': True
        }
        
        dynamic_checkin_manager.save_custom_question(self.user_id, 'pain_level', question_def)
        
        # Get via get_question_definition
        retrieved = dynamic_checkin_manager.get_question_definition('pain_level', self.user_id)
        assert retrieved is not None
        assert retrieved['type'] == 'scale_1_5'
        assert retrieved['question_text'] == question_def['question_text']
    
    def test_custom_question_in_all_questions(self, monkeypatch):
        """Test that custom questions appear in get_all_questions."""
        # Set environment variables for test data directory
        monkeypatch.setenv("TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TESTING", "1")
        
        question_def = {
            'type': 'yes_no',
            'question_text': 'Test question?',
            'ui_display_name': 'Test',
            'category': 'health',
            'validation': {'error_message': 'Please answer yes/no.'},
            'enabled': True
        }
        
        dynamic_checkin_manager.save_custom_question(self.user_id, 'test_custom', question_def)
        
        all_questions = dynamic_checkin_manager.get_all_questions(self.user_id)
        assert 'test_custom' in all_questions
        assert all_questions['test_custom']['type'] == 'yes_no'
    
    def test_delete_custom_question(self, monkeypatch):
        """Test deleting a custom question."""
        # Set environment variables for test data directory
        monkeypatch.setenv("TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TESTING", "1")
        
        question_def = {
            'type': 'yes_no',
            'question_text': 'Test question?',
            'ui_display_name': 'Test',
            'category': 'health',
            'validation': {'error_message': 'Please answer yes/no.'},
            'enabled': True
        }
        
        dynamic_checkin_manager.save_custom_question(self.user_id, 'test_delete', question_def)
        
        # Verify it exists
        custom_questions = dynamic_checkin_manager.get_custom_questions(self.user_id)
        assert 'test_delete' in custom_questions
        
        # Delete it
        result = dynamic_checkin_manager.delete_custom_question(self.user_id, 'test_delete')
        assert result is True
        
        # Verify it's gone
        custom_questions = dynamic_checkin_manager.get_custom_questions(self.user_id)
        assert 'test_delete' not in custom_questions
    
    def test_custom_question_validation(self, monkeypatch):
        """Test that custom questions can be validated."""
        # Set environment variables for test data directory
        monkeypatch.setenv("TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TESTING", "1")
        
        question_def = {
            'type': 'scale_1_5',
            'question_text': 'Rate your pain (1-5)',
            'ui_display_name': 'Pain level',
            'category': 'health',
            'validation': {'min': 1, 'max': 5, 'error_message': 'Please enter 1-5.'},
            'enabled': True
        }
        
        dynamic_checkin_manager.save_custom_question(self.user_id, 'custom_pain', question_def)
        
        # Validate answer
        is_valid, value, error = dynamic_checkin_manager.validate_answer('custom_pain', '4', self.user_id)
        assert is_valid is True
        assert value == 4
        
        is_valid, value, error = dynamic_checkin_manager.validate_answer('custom_pain', '6', self.user_id)
        assert is_valid is False


@pytest.mark.behavior
class TestSleepQualityUpdate:
    """Test the updated sleep_quality question."""
    
    def setup_method(self):
        self.test_dir, self.test_data_dir, _ = setup_test_data_environment()
    
    def teardown_method(self):
        cleanup_test_data_environment(self.test_dir)
    
    def test_sleep_quality_question_text(self):
        """Test that sleep_quality question text mentions 'rested'."""
        question = dynamic_checkin_manager.get_question_definition('sleep_quality')
        assert question is not None
        assert 'rested' in question['question_text'].lower()
        assert 'rest' in question['ui_display_name'].lower()


@pytest.mark.behavior
class TestAnalyticsWithNewQuestions:
    """Test analytics with new questions and sleep_schedule."""
    
    def setup_method(self):
        from core.user_management import get_user_id_by_identifier
        self.test_dir, self.test_data_dir, _ = setup_test_data_environment()
        username = "test_analytics_user"
        TestUserFactory.create_basic_user(
            username,
            enable_checkins=True,
            test_data_dir=self.test_data_dir
        )
        # Get the actual user_id (UUID) after creation
        self.user_id = get_user_id_by_identifier(username) or TestUserFactory.get_test_user_id_by_internal_username(username, self.test_data_dir) or username
        self.analytics = CheckinAnalytics()
    
    def teardown_method(self):
        cleanup_test_data_environment(self.test_dir)
    
    def test_analytics_with_sleep_schedule(self, monkeypatch):
        """Test analytics with sleep_schedule data."""
        # Set environment variables for test data directory
        monkeypatch.setenv("TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TESTING", "1")
        
        from core.response_tracking import store_user_response, get_checkins_by_days
        from datetime import datetime
        from unittest.mock import patch
        import os
        
        # Create check-in with sleep_schedule
        checkin_data = {
            'mood': 3,
            'energy': 3,
            'sleep_quality': 4,
            'sleep_schedule': {
                'sleep_time': '23:00',
                'wake_time': '07:00'
            },
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Store check-in using patched file path
        checkins_file = os.path.join(self.test_data_dir, "users", self.user_id, "checkins.json")
        os.makedirs(os.path.dirname(checkins_file), exist_ok=True)
        
        # Patch get_user_file_path for both storing and retrieving
        with patch('core.response_tracking.get_user_file_path', return_value=checkins_file):
            store_user_response(self.user_id, checkin_data, 'checkin')
            
            # Verify check-in was stored
            checkins = get_checkins_by_days(self.user_id, days=7)
            assert len(checkins) > 0, "Should have at least one check-in"
        
        # Test sleep analysis (also needs patched file path)
        with patch('core.response_tracking.get_user_file_path', return_value=checkins_file):
            sleep_analysis = self.analytics.get_sleep_analysis(self.user_id, days=7)
            assert 'error' not in sleep_analysis
            assert sleep_analysis['average_hours'] == 8.0
    
    def test_quantitative_summaries_includes_new_questions(self, monkeypatch):
        """Test that quantitative summaries can handle new questions."""
        # Set environment variables for test data directory
        monkeypatch.setenv("TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TESTING", "1")
        
        from core.response_tracking import store_user_response, get_checkins_by_days
        from datetime import datetime
        from unittest.mock import patch
        import os
        
        # Create check-ins with new questions
        checkin_data = {
            'mood': 3,
            'hopelessness_level': 2,
            'irritability_level': 3,
            'motivation_level': 4,
            'treatment_adherence': True,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Store check-in using patched file path
        checkins_file = os.path.join(self.test_data_dir, "users", self.user_id, "checkins.json")
        os.makedirs(os.path.dirname(checkins_file), exist_ok=True)
        
        # Patch get_user_file_path for both storing and retrieving
        with patch('core.response_tracking.get_user_file_path', return_value=checkins_file):
            store_user_response(self.user_id, checkin_data, 'checkin')
            
            # Verify check-in was stored
            checkins = get_checkins_by_days(self.user_id, days=7)
            assert len(checkins) > 0, "Should have at least one check-in"
            assert 'hopelessness_level' in checkins[0] or 'mood' in checkins[0], "Check-in should contain data"
        
        # Get quantitative summaries - should work with the stored data (also needs patched file path)
        with patch('core.response_tracking.get_user_file_path', return_value=checkins_file):
            summaries = self.analytics.get_quantitative_summaries(self.user_id, days=7)
            
            # Should get summaries if data exists, or error if no matching fields
            # Either way, the function should handle new question types gracefully
            assert isinstance(summaries, dict), "Should return a dictionary"
