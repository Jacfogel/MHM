"""
Dynamic Check-in Manager for MHM.
Handles loading and managing dynamic check-in questions and responses from JSON files.
"""

import random
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.file_operations import load_json_data

logger = get_component_logger('user_activity')

class DynamicCheckinManager:
    """Manages dynamic check-in questions and responses loaded from JSON files."""
    
    @handle_errors("initializing checkin dynamic manager", default_return=None)
    def __init__(self):
        """Initialize the dynamic check-in manager."""
        self.questions_data = None
        self.responses_data = None
        self._load_data()
    
    @handle_errors("loading checkin data", default_return=False)
    def _load_data(self) -> bool:
        """Load questions and responses data from JSON files."""
        try:
            # Get the path to the default_checkin directory
            resources_dir = Path(__file__).parent.parent / "resources" / "default_checkin"
            
            questions_file = resources_dir / "questions.json"
            if questions_file.exists():
                self.questions_data = load_json_data(str(questions_file))
                logger.debug(f"Loaded questions data from {questions_file}")
            else:
                logger.error(f"Questions file not found: {questions_file}")
                return False
            
            responses_file = resources_dir / "responses.json"
            if responses_file.exists():
                self.responses_data = load_json_data(str(responses_file))
                logger.debug(f"Loaded responses data from {responses_file}")
            else:
                logger.error(f"Responses file not found: {responses_file}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading checkin data: {e}")
            return False
    
    @handle_errors("getting question definition", default_return=None)
    def get_question_definition(self, question_key: str) -> Optional[Dict[str, Any]]:
        """Get the definition for a specific question."""
        if not self.questions_data:
            return None
        
        return self.questions_data.get('questions', {}).get(question_key)
    
    @handle_errors("getting all questions", default_return={})
    def get_all_questions(self) -> Dict[str, Dict[str, Any]]:
        """Get all question definitions."""
        if not self.questions_data:
            return {}
        
        return self.questions_data.get('questions', {})
    
    @handle_errors("getting question text", default_return="")
    def get_question_text(self, question_key: str) -> str:
        """Get the question text for a specific question."""
        question_def = self.get_question_definition(question_key)
        if question_def:
            return question_def.get('question_text', f"Please answer this question: {question_key}")
        return f"Please answer this question: {question_key}"
    
    @handle_errors("getting question type", default_return="text")
    def get_question_type(self, question_key: str) -> str:
        """Get the type of a specific question."""
        question_def = self.get_question_definition(question_key)
        if question_def:
            return question_def.get('type', 'unknown')
        return 'unknown'
    
    @handle_errors("getting question validation", default_return={})
    def get_question_validation(self, question_key: str) -> Dict[str, Any]:
        """Get validation rules for a specific question."""
        question_def = self.get_question_definition(question_key)
        if question_def:
            return question_def.get('validation', {})
        return {}
    
    @handle_errors("getting response statement", default_return=None)
    def get_response_statement(self, question_key: str, answer_value: Any) -> Optional[str]:
        """Get a random response statement for a question answer."""
        if not self.responses_data:
            return None
        
        responses = self.responses_data.get('responses', {})
        question_responses = responses.get(question_key, {})
        
        # Convert answer value to string key for lookup
        if isinstance(answer_value, bool):
            answer_key = str(answer_value).lower()
        else:
            answer_key = str(answer_value)
        
        response_list = question_responses.get(answer_key, [])
        
        if response_list:
            return random.choice(response_list)
        
        return None
    
    @handle_errors("getting transition phrase", default_return="Great! Let's continue.")
    def get_transition_phrase(self) -> str:
        """Get a random transition phrase."""
        if not self.responses_data:
            return "Next question:"
        
        transition_phrases = self.responses_data.get('transition_phrases', ["Next question:"])
        return random.choice(transition_phrases)
    
    @handle_errors("building next question with response", default_return="Please answer this question:")
    def build_next_question_with_response(self, question_key: str, previous_question_key: str, 
                                        previous_answer: Any) -> str:
        """Build the next question text with a response statement from the previous answer."""
        # Get response statement for the previous answer
        response_statement = self.get_response_statement(previous_question_key, previous_answer)
        
        # Get the next question text
        question_text = self.get_question_text(question_key)
        
        # Build the complete message
        if response_statement:
            transition = self.get_transition_phrase()
            return f"{response_statement}\n\n{transition} {question_text}"
        else:
            return question_text
    
    @handle_errors("validating answer", default_return=(False, None, "Validation failed"))
    def validate_answer(self, question_key: str, answer: str) -> Tuple[bool, Any, Optional[str]]:
        """Validate an answer for a specific question."""
        question_def = self.get_question_definition(question_key)
        if not question_def:
            return False, None, "Question not found"
        
        question_type = question_def.get('type', 'unknown')
        validation = question_def.get('validation', {})
        error_message = validation.get('error_message', "Invalid answer")
        
        answer = answer.strip()
        
        # Handle skip functionality for all question types
        if answer.lower() == 'skip':
            return True, 'SKIPPED', None
        
        if question_type == 'yes_no':
            # Enhanced yes/no parsing with more synonyms
            yes_responses = [
                "yes", "y", "yeah", "yep", "true", "1", "absolutely", "definitely", 
                "sure", "of course", "i did", "i have", "100", "100%", "correct", 
                "affirmative", "indeed", "certainly", "positively"
            ]
            no_responses = [
                "no", "n", "nope", "false", "0", "not", "never", "i didn't", 
                "i did not", "i haven't", "i have not", "no way", "absolutely not", 
                "definitely not", "negative", "incorrect", "wrong", "0%"
            ]
            
            answer_lower = answer.lower()
            if answer_lower in yes_responses:
                return True, True, None
            elif answer_lower in no_responses:
                return True, False, None
            else:
                return False, None, error_message
        
        elif question_type == 'scale_1_5':
            # Enhanced numerical parsing for scale questions
            parsed_value = self._parse_numerical_response(answer)
            if parsed_value is not None:
                min_val = validation.get('min', 1)
                max_val = validation.get('max', 5)
                if min_val <= parsed_value <= max_val:
                    return True, int(parsed_value), None
                else:
                    return False, None, error_message
            else:
                return False, None, error_message
        
        elif question_type == 'number':
            # Enhanced numerical parsing for number questions
            parsed_value = self._parse_numerical_response(answer)
            if parsed_value is not None:
                min_val = validation.get('min', 0)
                max_val = validation.get('max', 24)
                if min_val <= parsed_value <= max_val:
                    return True, float(parsed_value), None
                else:
                    return False, None, error_message
            else:
                return False, None, error_message
        
        elif question_type == 'optional_text':
            # For optional text, any answer (including empty) is valid
            return True, answer, None
        
        else:
            return False, None, f"Unknown question type: {question_type}"
    
    @handle_errors("parsing numerical response", default_return=None)
    def _parse_numerical_response(self, answer: str) -> Optional[float]:
        """Parse numerical responses including written numbers, decimals, and mixed formats."""
        answer = answer.strip().lower()
        
        # Handle direct numeric values (including decimals)
        try:
            return float(answer)
        except ValueError:
            pass
        
        # Handle written numbers
        written_numbers = {
            'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
            'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20
        }
        
        # Handle simple written numbers
        if answer in written_numbers:
            return float(written_numbers[answer])
        
        # Handle "and a half" patterns (e.g., "three and a half", "2 and a half")
        if ' and a half' in answer:
            base_part = answer.replace(' and a half', '').strip()
            try:
                base_value = float(base_part)
                return base_value + 0.5
            except ValueError:
                if base_part in written_numbers:
                    return written_numbers[base_part] + 0.5
        
        # Handle "and half" patterns (e.g., "three and half")
        if ' and half' in answer:
            base_part = answer.replace(' and half', '').strip()
            try:
                base_value = float(base_part)
                return base_value + 0.5
            except ValueError:
                if base_part in written_numbers:
                    return written_numbers[base_part] + 0.5
        
        # Handle decimal written numbers (e.g., "three point five", "2 point 75")
        if ' point ' in answer:
            parts = answer.split(' point ')
            if len(parts) == 2:
                try:
                    whole_part = float(parts[0]) if parts[0].isdigit() else written_numbers.get(parts[0])
                    decimal_part = parts[1]
                    
                    # Handle multi-word decimal parts (e.g., "two five" -> "25")
                    if ' ' in decimal_part:
                        decimal_words = decimal_part.split()
                        decimal_str = ''
                        for word in decimal_words:
                            if word in written_numbers:
                                decimal_str += str(written_numbers[word])
                            elif word.isdigit():
                                decimal_str += word
                        if decimal_str:
                            decimal_part = decimal_str
                    else:
                        # Handle single word decimal parts
                        if decimal_part in written_numbers:
                            decimal_part = str(written_numbers[decimal_part])
                    
                    if whole_part is not None and (decimal_part.isdigit() or decimal_part in written_numbers):
                        if decimal_part in written_numbers:
                            decimal_part = str(written_numbers[decimal_part])
                        # Convert whole_part to int to avoid "2.0.5" issue
                        whole_part_int = int(whole_part) if whole_part == int(whole_part) else whole_part
                        return float(f"{whole_part_int}.{decimal_part}")
                except (ValueError, TypeError):
                    pass
        
        # Handle percentage values (e.g., "100%", "50%")
        if answer.endswith('%'):
            try:
                return float(answer[:-1])
            except ValueError:
                pass
        
        return None
    
    @handle_errors("getting enabled questions for UI", default_return={})
    def get_enabled_questions_for_ui(self) -> Dict[str, Dict[str, Any]]:
        """Get questions formatted for UI display with enabled_by_default status."""
        questions = self.get_all_questions()
        ui_questions = {}
        
        for key, question in questions.items():
            ui_questions[key] = {
                'enabled': question.get('enabled_by_default', False),
                'ui_display_name': question.get('ui_display_name', key),
                'category': question.get('category', 'general'),
                'type': question.get('type', 'unknown')
            }
        
        return ui_questions
    
    @handle_errors("getting categories", default_return={})
    def get_categories(self) -> Dict[str, Dict[str, str]]:
        """Get all question categories."""
        if not self.questions_data:
            return {}
        
        return self.questions_data.get('categories', {})

# Create a global instance for convenience
dynamic_checkin_manager = DynamicCheckinManager()
