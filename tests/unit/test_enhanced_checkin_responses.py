"""
Test enhanced checkin response parsing capabilities.

Tests the new response parsing features:
- Enhanced numerical parsing (decimals, written numbers, mixed formats)
- Enhanced yes/no parsing (synonyms and variations)
- Skip functionality
- Analytics handling of skipped questions
"""

import pytest
from unittest.mock import patch, MagicMock
from core.checkin_dynamic_manager import DynamicCheckinManager
from core.checkin_analytics import CheckinAnalytics


@pytest.mark.unit
class TestEnhancedNumericalParsing:
    """Test enhanced numerical response parsing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = DynamicCheckinManager()
    
    def test_direct_numeric_values(self):
        """Test direct numeric values including decimals."""
        test_cases = [
            ("3", 3.0),
            ("3.5", 3.5),
            ("2.75", 2.75),
            ("0", 0.0),
            ("5", 5.0)
        ]
        
        for input_val, expected in test_cases:
            result = self.manager._parse_numerical_response(input_val)
            assert result == expected, f"Failed for input: {input_val}"
    
    def test_written_numbers(self):
        """Test written number parsing."""
        test_cases = [
            ("one", 1.0),
            ("two", 2.0),
            ("three", 3.0),
            ("four", 4.0),
            ("five", 5.0),
            ("zero", 0.0),
            ("ten", 10.0),
            ("fifteen", 15.0),
            ("twenty", 20.0)
        ]
        
        for input_val, expected in test_cases:
            result = self.manager._parse_numerical_response(input_val)
            assert result == expected, f"Failed for input: {input_val}"
    
    def test_and_a_half_patterns(self):
        """Test 'and a half' patterns."""
        test_cases = [
            ("three and a half", 3.5),
            ("2 and a half", 2.5),
            ("one and a half", 1.5),
            ("four and a half", 4.5)
        ]
        
        for input_val, expected in test_cases:
            result = self.manager._parse_numerical_response(input_val)
            assert result == expected, f"Failed for input: {input_val}"
    
    def test_and_half_patterns(self):
        """Test 'and half' patterns (without 'a')."""
        test_cases = [
            ("three and half", 3.5),
            ("2 and half", 2.5),
            ("one and half", 1.5)
        ]
        
        for input_val, expected in test_cases:
            result = self.manager._parse_numerical_response(input_val)
            assert result == expected, f"Failed for input: {input_val}"
    
    def test_decimal_written_numbers(self):
        """Test decimal written numbers."""
        test_cases = [
            ("three point five", 3.5),
            ("2 point 5", 2.5),
            ("one point zero", 1.0),
            ("four point two", 4.2)
        ]
        
        for input_val, expected in test_cases:
            result = self.manager._parse_numerical_response(input_val)
            assert result == expected, f"Failed for input: {input_val}"
    
    def test_percentage_values(self):
        """Test percentage value parsing."""
        test_cases = [
            ("100%", 100.0),
            ("50%", 50.0),
            ("3.5%", 3.5),
            ("0%", 0.0)
        ]
        
        for input_val, expected in test_cases:
            result = self.manager._parse_numerical_response(input_val)
            assert result == expected, f"Failed for input: {input_val}"
    
    def test_invalid_numerical_responses(self):
        """Test that invalid responses return None."""
        invalid_cases = [
            "not a number",
            "maybe",
            "I don't know",
            "three and a quarter",  # Not supported yet
            "some text",
            ""
        ]
        
        for input_val in invalid_cases:
            result = self.manager._parse_numerical_response(input_val)
            assert result is None, f"Should return None for: {input_val}"


@pytest.mark.unit
class TestEnhancedYesNoParsing:
    """Test enhanced yes/no response parsing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = DynamicCheckinManager()
        
        # Mock question definition for yes_no type
        self.mock_question_def = {
            'type': 'yes_no',
            'validation': {'error_message': 'Please answer with yes/no'}
        }
    
    @patch.object(DynamicCheckinManager, 'get_question_definition')
    def test_yes_responses(self, mock_get_question):
        """Test various yes response formats."""
        mock_get_question.return_value = self.mock_question_def
        
        yes_responses = [
            "yes", "y", "yeah", "yep", "true", "1",
            "absolutely", "definitely", "sure", "of course",
            "i did", "i have", "100", "100%", "correct",
            "affirmative", "indeed", "certainly", "positively"
        ]
        
        for response in yes_responses:
            is_valid, value, error = self.manager.validate_answer("test_question", response)
            assert is_valid, f"Should be valid: {response}"
            assert value is True, f"Should be True: {response}"
            assert error is None, f"Should have no error: {response}"
    
    @patch.object(DynamicCheckinManager, 'get_question_definition')
    def test_no_responses(self, mock_get_question):
        """Test various no response formats."""
        mock_get_question.return_value = self.mock_question_def
        
        no_responses = [
            "no", "n", "nope", "false", "0",
            "not", "never", "i didn't", "i did not",
            "i haven't", "i have not", "no way",
            "absolutely not", "definitely not", "negative",
            "incorrect", "wrong", "0%"
        ]
        
        for response in no_responses:
            is_valid, value, error = self.manager.validate_answer("test_question", response)
            assert is_valid, f"Should be valid: {response}"
            assert value is False, f"Should be False: {response}"
            assert error is None, f"Should have no error: {response}"
    
    @patch.object(DynamicCheckinManager, 'get_question_definition')
    def test_invalid_yes_no_responses(self, mock_get_question):
        """Test that invalid yes/no responses are rejected."""
        mock_get_question.return_value = self.mock_question_def
        
        invalid_responses = [
            "maybe", "I don't know", "sometimes",
            "not sure", "could be", "perhaps"
        ]
        
        for response in invalid_responses:
            is_valid, value, error = self.manager.validate_answer("test_question", response)
            assert not is_valid, f"Should be invalid: {response}"
            assert value is None, f"Should have no value: {response}"
            assert error is not None, f"Should have error: {response}"


@pytest.mark.unit
class TestSkipFunctionality:
    """Test skip functionality for all question types."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = DynamicCheckinManager()
    
    @patch.object(DynamicCheckinManager, 'get_question_definition')
    def test_skip_scale_1_5(self, mock_get_question):
        """Test skip functionality for scale_1_5 questions."""
        mock_get_question.return_value = {
            'type': 'scale_1_5',
            'validation': {'min': 1, 'max': 5, 'error_message': 'Invalid'}
        }
        
        is_valid, value, error = self.manager.validate_answer("test_question", "skip")
        assert is_valid, "Skip should be valid"
        assert value == 'SKIPPED', "Skip should return 'SKIPPED'"
        assert error is None, "Skip should have no error"
    
    @patch.object(DynamicCheckinManager, 'get_question_definition')
    def test_skip_yes_no(self, mock_get_question):
        """Test skip functionality for yes_no questions."""
        mock_get_question.return_value = {
            'type': 'yes_no',
            'validation': {'error_message': 'Invalid'}
        }
        
        is_valid, value, error = self.manager.validate_answer("test_question", "skip")
        assert is_valid, "Skip should be valid"
        assert value == 'SKIPPED', "Skip should return 'SKIPPED'"
        assert error is None, "Skip should have no error"
    
    @patch.object(DynamicCheckinManager, 'get_question_definition')
    def test_skip_number(self, mock_get_question):
        """Test skip functionality for number questions."""
        mock_get_question.return_value = {
            'type': 'number',
            'validation': {'min': 0, 'max': 24, 'error_message': 'Invalid'}
        }
        
        is_valid, value, error = self.manager.validate_answer("test_question", "skip")
        assert is_valid, "Skip should be valid"
        assert value == 'SKIPPED', "Skip should return 'SKIPPED'"
        assert error is None, "Skip should have no error"
    
    @patch.object(DynamicCheckinManager, 'get_question_definition')
    def test_skip_optional_text(self, mock_get_question):
        """Test skip functionality for optional_text questions."""
        mock_get_question.return_value = {
            'type': 'optional_text',
            'validation': {'error_message': 'Invalid'}
        }
        
        is_valid, value, error = self.manager.validate_answer("test_question", "skip")
        assert is_valid, "Skip should be valid"
        assert value == 'SKIPPED', "Skip should return 'SKIPPED'"
        assert error is None, "Skip should have no error"


@pytest.mark.unit
class TestAnalyticsSkippedQuestions:
    """Test that skipped questions are handled properly in analytics."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analytics = CheckinAnalytics()
    
    def test_skipped_questions_excluded_from_analytics(self):
        """Test that 'SKIPPED' responses are excluded from analytics calculations."""
        # Mock checkin data with some skipped responses
        mock_checkins = [
            {'mood': 3, 'energy': 4, 'sleep_quality': 'SKIPPED'},
            {'mood': 4, 'energy': 'SKIPPED', 'sleep_quality': 5},
            {'mood': 'SKIPPED', 'energy': 3, 'sleep_quality': 4},
            {'mood': 2, 'energy': 2, 'sleep_quality': 3}
        ]
        
        # Mock the get_checkins_by_days method
        with patch('core.checkin_analytics.get_checkins_by_days', return_value=mock_checkins):
            summaries = self.analytics.get_quantitative_summaries("test_user", 30, ['mood', 'energy', 'sleep_quality'])
        
        # Check that skipped values are excluded from calculations
        assert 'mood' in summaries
        assert 'energy' in summaries
        assert 'sleep_quality' in summaries
        
        # Mood should only include [3, 4, 2] (excluding 'SKIPPED')
        mood_values = [3, 4, 2]
        expected_mood_avg = sum(mood_values) / len(mood_values)
        assert summaries['mood']['average'] == expected_mood_avg
        
        # Energy should only include [4, 3, 2] (excluding 'SKIPPED')
        energy_values = [4, 3, 2]
        expected_energy_avg = sum(energy_values) / len(energy_values)
        assert summaries['energy']['average'] == expected_energy_avg
        
        # Sleep quality should only include [5, 4, 3] (excluding 'SKIPPED')
        sleep_values = [5, 4, 3]
        expected_sleep_avg = sum(sleep_values) / len(sleep_values)
        assert summaries['sleep_quality']['average'] == expected_sleep_avg
    
    def test_enhanced_yes_no_analytics(self):
        """Test that enhanced yes/no responses are properly converted for analytics."""
        # Mock checkin data with enhanced yes/no responses
        mock_checkins = [
            {'exercise': 'absolutely', 'medication_taken': 'I did'},
            {'exercise': 'no way', 'medication_taken': '100%'},
            {'exercise': 'definitely not', 'medication_taken': 'never'}
        ]
        
        # Mock the get_checkins_by_days method
        with patch('core.checkin_analytics.get_checkins_by_days', return_value=mock_checkins):
            summaries = self.analytics.get_quantitative_summaries("test_user", 30, ['exercise', 'medication_taken'])
        
        # Check that enhanced responses are properly converted
        assert 'exercise' in summaries
        assert 'medication_taken' in summaries
        
        # Exercise: 'absolutely'=1, 'no way'=0, 'definitely not'=0
        # Average should be (1 + 0 + 0) / 3 = 0.33
        assert summaries['exercise']['average'] == 0.33
        
        # Medication: 'I did'=1, '100%'=1, 'never'=0
        # Average should be (1 + 1 + 0) / 3 = 0.67
        assert summaries['medication_taken']['average'] == 0.67


@pytest.mark.unit
class TestScaleQuestionsWithEnhancedParsing:
    """Test scale questions with enhanced numerical parsing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = DynamicCheckinManager()
    
    @patch.object(DynamicCheckinManager, 'get_question_definition')
    def test_scale_1_5_enhanced_parsing(self, mock_get_question):
        """Test scale_1_5 questions with enhanced numerical parsing."""
        mock_get_question.return_value = {
            'type': 'scale_1_5',
            'validation': {'min': 1, 'max': 5, 'error_message': 'Invalid'}
        }
        
        test_cases = [
            ("3", 3),  # Direct number
            ("3.5", 3),  # Decimal (should be converted to int)
            ("three", 3),  # Written number
            ("two and a half", 2),  # Mixed format (should be converted to int)
            ("four point five", 4),  # Decimal written
        ]
        
        for input_val, expected in test_cases:
            is_valid, value, error = self.manager.validate_answer("test_question", input_val)
            assert is_valid, f"Should be valid: {input_val}"
            assert value == expected, f"Expected {expected}, got {value} for input: {input_val}"
            assert error is None, f"Should have no error: {input_val}"
    
    @patch.object(DynamicCheckinManager, 'get_question_definition')
    def test_number_enhanced_parsing(self, mock_get_question):
        """Test number questions with enhanced numerical parsing."""
        mock_get_question.return_value = {
            'type': 'number',
            'validation': {'min': 0, 'max': 24, 'error_message': 'Invalid'}
        }
        
        test_cases = [
            ("8.5", 8.5),  # Decimal
            ("eight and a half", 8.5),  # Written with half
            ("7.25", 7.25),  # Decimal
            ("seven point five", 7.5),  # Written decimal
            ("12", 12.0),  # Integer
        ]
        
        for input_val, expected in test_cases:
            is_valid, value, error = self.manager.validate_answer("test_question", input_val)
            assert is_valid, f"Should be valid: {input_val}"
            assert value == expected, f"Expected {expected}, got {value} for input: {input_val}"
            assert error is None, f"Should have no error: {input_val}"


if __name__ == "__main__":
    pytest.main([__file__])
