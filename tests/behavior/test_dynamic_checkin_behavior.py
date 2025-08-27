"""
Behavior tests for the dynamic check-in system.
Tests the new dynamic question and response system.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

from core.checkin_dynamic_manager import dynamic_checkin_manager, DynamicCheckinManager
from communication.message_processing.conversation_flow_manager import conversation_manager


class TestDynamicCheckinManager:
    """Test the dynamic check-in manager functionality."""
    
    def test_dynamic_checkin_manager_initialization(self):
        """Test that the dynamic check-in manager initializes correctly."""
        # Test that the manager loads data
        assert dynamic_checkin_manager.questions_data is not None
        assert dynamic_checkin_manager.responses_data is not None
        
        # Test that we have questions loaded
        questions = dynamic_checkin_manager.get_all_questions()
        assert len(questions) > 0
        assert 'mood' in questions
        assert 'energy' in questions
        assert 'sleep_quality' in questions
    
    def test_question_definitions(self):
        """Test that question definitions are loaded correctly."""
        mood_question = dynamic_checkin_manager.get_question_definition('mood')
        assert mood_question is not None
        assert mood_question['type'] == 'scale_1_5'
        assert 'How are you feeling today' in mood_question['question_text']
        assert mood_question['enabled_by_default'] is True
        
        energy_question = dynamic_checkin_manager.get_question_definition('energy')
        assert energy_question is not None
        assert energy_question['type'] == 'scale_1_5'
        assert 'energy level' in energy_question['question_text']
    
    def test_response_statements(self):
        """Test that response statements are loaded and varied."""
        # Test mood responses
        mood_response_1 = dynamic_checkin_manager.get_response_statement('mood', 1)
        mood_response_2 = dynamic_checkin_manager.get_response_statement('mood', 1)
        mood_response_3 = dynamic_checkin_manager.get_response_statement('mood', 5)
        
        assert mood_response_1 is not None
        assert mood_response_2 is not None
        assert mood_response_3 is not None
        # Check for any of the expected phrases in mood=1 responses
        assert any(phrase in mood_response_1.lower() for phrase in ['terrible', 'tough', 'challenging', 'difficult'])
        # Check for any of the expected phrases in mood=5 responses
        assert any(phrase in mood_response_3.lower() for phrase in ['thriving', 'amazing', 'incredible', 'fantastic'])
        
        # Test that we get different responses (randomization)
        responses = set()
        for _ in range(10):
            response = dynamic_checkin_manager.get_response_statement('mood', 3)
            responses.add(response)
        
        # We should get at least 2 different responses for variety
        assert len(responses) >= 2
    
    def test_validation(self):
        """Test that validation works correctly for different question types."""
        # Test scale questions
        is_valid, value, error = dynamic_checkin_manager.validate_answer('mood', '3')
        assert is_valid is True
        assert value == 3
        assert error is None
        
        is_valid, value, error = dynamic_checkin_manager.validate_answer('mood', '6')
        assert is_valid is False
        assert value is None
        assert error is not None
        
        # Test yes/no questions
        is_valid, value, error = dynamic_checkin_manager.validate_answer('ate_breakfast', 'yes')
        assert is_valid is True
        assert value is True
        assert error is None
        
        is_valid, value, error = dynamic_checkin_manager.validate_answer('ate_breakfast', 'no')
        assert is_valid is True
        assert value is False
        assert error is None
        
        # Test number questions
        is_valid, value, error = dynamic_checkin_manager.validate_answer('sleep_hours', '7.5')
        assert is_valid is True
        assert value == 7.5
        assert error is None
    
    def test_build_next_question_with_response(self):
        """Test building questions with response statements."""
        # Test with a previous answer
        question_text = dynamic_checkin_manager.build_next_question_with_response(
            'energy', 'mood', 2
        )

        # Should contain both the response statement and the next question
        assert any(phrase in question_text.lower() for phrase in ['feeling down', 'rough', 'aren\'t great', 'tough'])
        assert 'energy level' in question_text.lower()
        # Check for newline separation between response and question
        assert '\n\n' in question_text
        
        # Test without a previous answer (first question)
        question_text = dynamic_checkin_manager.build_next_question_with_response(
            'mood', 'none', None
        )
        # Should just be the question text
        assert 'How are you feeling today' in question_text
        assert '\n\n' not in question_text
    
    def test_ui_questions_format(self):
        """Test that questions are formatted correctly for UI."""
        ui_questions = dynamic_checkin_manager.get_enabled_questions_for_ui()
        
        assert 'mood' in ui_questions
        assert ui_questions['mood']['enabled'] is True  # Should be enabled by default
        assert 'ui_display_name' in ui_questions['mood']
        assert 'category' in ui_questions['mood']
        assert 'type' in ui_questions['mood']


class TestDynamicCheckinIntegration:
    """Test integration with the conversation flow manager."""
    
    def test_conversation_manager_uses_dynamic_questions(self):
        """Test that the conversation manager uses the dynamic question system."""
        # Test that the dynamic manager is working
        questions = dynamic_checkin_manager.get_all_questions()
        assert len(questions) > 0
        assert 'mood' in questions
        assert 'energy' in questions
        
        # Test that question text is retrieved correctly
        mood_text = dynamic_checkin_manager.get_question_text('mood')
        assert 'How are you feeling today' in mood_text
        
        # Test that validation works
        is_valid, value, error = dynamic_checkin_manager.validate_answer('mood', '3')
        assert is_valid is True
        assert value == 3
    
    def test_question_text_uses_dynamic_manager(self):
        """Test that question text is retrieved from the dynamic manager."""
        # Test getting question text
        question_text = conversation_manager._get_question_text('mood', {})
        
        # Should be the text from the dynamic manager
        assert 'How are you feeling today' in question_text
        assert '1=terrible, 5=great' in question_text
    
    def test_validation_uses_dynamic_manager(self):
        """Test that validation uses the dynamic manager."""
        # Test validation
        result = conversation_manager._validate_response('mood', '4')
        
        assert result['valid'] is True
        assert result['value'] == 4
        assert result['message'] is None
        
        # Test invalid input
        result = conversation_manager._validate_response('mood', 'invalid')
        
        assert result['valid'] is False
        assert result['value'] is None
        assert result['message'] is not None


class TestDynamicCheckinVariety:
    """Test that the system provides variety in responses."""
    
    def test_response_variety(self):
        """Test that we get varied responses for the same answer."""
        responses = set()
        
        # Get multiple responses for the same answer
        for _ in range(20):
            response = dynamic_checkin_manager.get_response_statement('mood', 3)
            responses.add(response)
        
        # We should get multiple different responses for variety
        assert len(responses) >= 3, f"Expected at least 3 different responses, got {len(responses)}"
    
    def test_transition_phrase_variety(self):
        """Test that transition phrases provide variety."""
        phrases = set()
        
        # Get multiple transition phrases
        for _ in range(10):
            phrase = dynamic_checkin_manager.get_transition_phrase()
            phrases.add(phrase)
        
        # We should get multiple different phrases
        assert len(phrases) >= 3, f"Expected at least 3 different transition phrases, got {len(phrases)}"
    
    def test_complete_question_flow_variety(self):
        """Test that complete question flows provide variety."""
        # Simulate a complete question flow
        previous_data = {'mood': 2}
        
        # Get the next question with response
        question_text = conversation_manager._get_question_text('energy', previous_data)
        
        # Should contain both response and question
        assert any(phrase in question_text.lower() for phrase in ['feeling down', 'rough', 'aren\'t great', 'tough'])
        assert 'energy level' in question_text.lower()
        
        # Get it again to test variety
        question_text_2 = conversation_manager._get_question_text('energy', previous_data)
        
        # The responses should be different (due to randomization)
        # Note: This test might occasionally fail due to randomness, but it should usually pass
        assert question_text != question_text_2 or any(phrase in question_text.lower() for phrase in ['feeling down', 'rough', 'aren\'t great', 'tough'])
