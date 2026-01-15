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

logger = get_component_logger("user_activity")


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
            resources_dir = (
                Path(__file__).parent.parent / "resources" / "default_checkin"
            )

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
    def get_question_definition(
        self, question_key: str, user_id: str | None = None
    ) -> dict[str, Any] | None:
        """Get the definition for a specific question.

        Checks custom questions first (if user_id provided), then predefined questions.
        """
        # Check custom questions first if user_id provided
        if user_id:
            custom_questions = self.get_custom_questions(user_id)
            if question_key in custom_questions:
                return custom_questions[question_key]

        # Fall back to predefined questions
        if not self.questions_data:
            return None

        return self.questions_data.get("questions", {}).get(question_key)

    @handle_errors("getting all questions", default_return={})
    def get_all_questions(
        self, user_id: str | None = None
    ) -> dict[str, dict[str, Any]]:
        """Get all question definitions, merging predefined and custom questions.

        Custom questions take precedence over predefined questions with the same key.
        """
        questions = {}

        # Start with predefined questions
        if self.questions_data:
            questions.update(self.questions_data.get("questions", {}))

        # Add/override with custom questions if user_id provided
        if user_id:
            custom_questions = self.get_custom_questions(user_id)
            questions.update(custom_questions)

        return questions

    @handle_errors("getting question text", default_return="")
    def get_question_text(
        self, question_key: str, user_id: str | None = None
    ) -> str:
        """Get the question text for a specific question."""
        question_def = self.get_question_definition(question_key, user_id)
        if question_def:
            return question_def.get(
                "question_text", f"Please answer this question: {question_key}"
            )
        return f"Please answer this question: {question_key}"

    @handle_errors("getting question type", default_return="text")
    def get_question_type(self, question_key: str) -> str:
        """Get the type of a specific question."""
        question_def = self.get_question_definition(question_key)
        if question_def:
            return question_def.get("type", "unknown")
        return "unknown"

    @handle_errors("getting question validation", default_return={})
    def get_question_validation(self, question_key: str) -> dict[str, Any]:
        """Get validation rules for a specific question."""
        question_def = self.get_question_definition(question_key)
        if question_def:
            return question_def.get("validation", {})
        return {}

    @handle_errors("getting response statement", default_return=None)
    def get_response_statement(
        self, question_key: str, answer_value: Any
    ) -> str | None:
        """Get a random response statement for a question answer."""
        if not self.responses_data:
            return None

        responses = self.responses_data.get("responses", {})
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

        transition_phrases = self.responses_data.get(
            "transition_phrases", ["Next question:"]
        )
        return random.choice(transition_phrases)

    @handle_errors(
        "building next question with response",
        default_return="Please answer this question:",
    )
    def build_next_question_with_response(
        self, question_key: str, previous_question_key: str, previous_answer: Any
    ) -> str:
        """Build the next question text with a response statement from the previous answer."""
        # Get response statement for the previous answer
        response_statement = self.get_response_statement(
            previous_question_key, previous_answer
        )

        # Get the next question text
        question_text = self.get_question_text(question_key)

        # Build the complete message
        if response_statement:
            transition = self.get_transition_phrase()
            return f"{response_statement}\n\n{transition} {question_text}"
        else:
            return question_text

    @handle_errors(
        "validating answer", default_return=(False, None, "Validation failed")
    )
    def validate_answer(
        self, question_key: str, answer: str, user_id: str | None = None
    ) -> tuple[bool, Any, str | None]:
        """Validate an answer for a specific question."""
        question_def = self.get_question_definition(question_key, user_id)
        if not question_def:
            return False, None, "Question not found"

        question_type = question_def.get("type", "unknown")
        validation = question_def.get("validation", {})
        error_message = validation.get("error_message", "Invalid answer")

        answer = answer.strip()

        # Handle skip functionality for all question types
        if answer.lower() == "skip":
            return True, "SKIPPED", None

        if question_type == "yes_no":
            # Enhanced yes/no parsing with more synonyms
            yes_responses = [
                "yes",
                "y",
                "yeah",
                "yep",
                "true",
                "1",
                "absolutely",
                "definitely",
                "sure",
                "of course",
                "i did",
                "i have",
                "100",
                "100%",
                "correct",
                "affirmative",
                "indeed",
                "certainly",
                "positively",
            ]
            no_responses = [
                "no",
                "n",
                "nope",
                "false",
                "0",
                "not",
                "never",
                "i didn't",
                "i did not",
                "i haven't",
                "i have not",
                "no way",
                "absolutely not",
                "definitely not",
                "negative",
                "incorrect",
                "wrong",
                "0%",
            ]

            answer_lower = answer.lower()
            if answer_lower in yes_responses:
                return True, True, None
            elif answer_lower in no_responses:
                return True, False, None
            else:
                return False, None, error_message

        elif question_type == "scale_1_5":
            # Enhanced numerical parsing for scale questions
            parsed_value = self._parse_numerical_response(answer)
            if parsed_value is not None:
                min_val = validation.get("min", 1)
                max_val = validation.get("max", 5)
                if min_val <= parsed_value <= max_val:
                    return True, int(parsed_value), None
                else:
                    return False, None, error_message
            else:
                return False, None, error_message

        elif question_type == "number":
            # Enhanced numerical parsing for number questions
            parsed_value = self._parse_numerical_response(answer)
            if parsed_value is not None:
                min_val = validation.get("min", 0)
                max_val = validation.get("max", 24)
                if min_val <= parsed_value <= max_val:
                    return True, float(parsed_value), None
                else:
                    return False, None, error_message
            else:
                return False, None, error_message

        elif question_type == "optional_text":
            # For optional text, any answer (including empty) is valid
            return True, answer, None

        elif question_type == "time_pair":
            # Parse sleep time and wake time from answer
            parsed_times = self._parse_time_pair_response(answer)
            if parsed_times:
                sleep_time, wake_time = parsed_times
                return True, {"sleep_time": sleep_time, "wake_time": wake_time}, None
            else:
                return False, None, error_message

        else:
            return False, None, f"Unknown question type: {question_type}"

    @handle_errors("parsing numerical response", default_return=None)
    def _parse_numerical_response(self, answer: str) -> float | None:
        """Parse numerical responses including written numbers, decimals, and mixed formats."""
        answer = answer.strip().lower()

        # Handle direct numeric values (including decimals)
        try:
            return float(answer)
        except ValueError:
            pass

        # Handle written numbers
        written_numbers = {
            "zero": 0,
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10,
            "eleven": 11,
            "twelve": 12,
            "thirteen": 13,
            "fourteen": 14,
            "fifteen": 15,
            "sixteen": 16,
            "seventeen": 17,
            "eighteen": 18,
            "nineteen": 19,
            "twenty": 20,
        }

        # Handle simple written numbers
        if answer in written_numbers:
            return float(written_numbers[answer])

        # Handle "and a half" patterns (e.g., "three and a half", "2 and a half")
        if " and a half" in answer:
            base_part = answer.replace(" and a half", "").strip()
            try:
                base_value = float(base_part)
                return base_value + 0.5
            except ValueError:
                if base_part in written_numbers:
                    return written_numbers[base_part] + 0.5

        # Handle "and half" patterns (e.g., "three and half")
        if " and half" in answer:
            base_part = answer.replace(" and half", "").strip()
            try:
                base_value = float(base_part)
                return base_value + 0.5
            except ValueError:
                if base_part in written_numbers:
                    return written_numbers[base_part] + 0.5

        # Handle decimal written numbers (e.g., "three point five", "2 point 75")
        if " point " in answer:
            parts = answer.split(" point ")
            if len(parts) == 2:
                try:
                    whole_part = (
                        float(parts[0])
                        if parts[0].isdigit()
                        else written_numbers.get(parts[0])
                    )
                    decimal_part = parts[1]

                    # Handle multi-word decimal parts (e.g., "two five" -> "25")
                    if " " in decimal_part:
                        decimal_words = decimal_part.split()
                        decimal_str = ""
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

                    if whole_part is not None and (
                        decimal_part.isdigit() or decimal_part in written_numbers
                    ):
                        if decimal_part in written_numbers:
                            decimal_part = str(written_numbers[decimal_part])
                        # Convert whole_part to int to avoid "2.0.5" issue
                        whole_part_int = (
                            int(whole_part)
                            if whole_part == int(whole_part)
                            else whole_part
                        )
                        return float(f"{whole_part_int}.{decimal_part}")
                except (ValueError, TypeError):
                    pass

        # Handle percentage values (e.g., "100%", "50%")
        if answer.endswith("%"):
            try:
                return float(answer[:-1])
            except ValueError:
                pass

        return None

    @handle_errors("parsing time pair response", default_return=None)
    def _parse_time_pair_response(self, answer: str) -> tuple[str, str] | None:
        """Parse sleep time and wake time from user response.

        Supports formats like:
        - "11:30 PM and 7:00 AM"
        - "23:30 and 07:00"
        - "11:30pm, 7:00am"
        - "11:30 PM, 7:00 AM"
        """
        answer = answer.strip()

        # Try to split on common separators
        separators = [" and ", " & ", ", ", "; ", " to ", " then "]
        parts = None
        for sep in separators:
            if sep in answer.lower():
                parts = [p.strip() for p in answer.split(sep, 1)]
                if len(parts) == 2:
                    break

        # If no separator found, try to find two time patterns
        if not parts or len(parts) != 2:
            # Try to find two time patterns in the text
            import re

            time_pattern = r"\b(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)?\b"
            matches = re.findall(time_pattern, answer)
            if len(matches) >= 2:
                # Use first two matches
                sleep_match = matches[0]
                wake_match = matches[1]
                parts = [
                    f"{sleep_match[0]}:{sleep_match[1]}{sleep_match[2] if sleep_match[2] else ''}",
                    f"{wake_match[0]}:{wake_match[1]}{wake_match[2] if wake_match[2] else ''}",
                ]
            else:
                return None

        if len(parts) != 2:
            return None

        sleep_time_str = parts[0].strip()
        wake_time_str = parts[1].strip()

        # Parse and normalize times
        sleep_time = self._normalize_time(sleep_time_str)
        wake_time = self._normalize_time(wake_time_str)

        if sleep_time and wake_time:
            return (sleep_time, wake_time)

        return None

    @handle_errors("normalizing time format", default_return=None)
    def _normalize_time(self, time_str: str) -> str | None:
        """Normalize time string to HH:MM format (24-hour).

        Supports formats like:
        - "11:30 PM" -> "23:30"
        - "7:00 AM" -> "07:00"
        - "23:30" -> "23:30"
        - "7:00" -> "07:00" (assumes AM if no AM/PM)
        """
        import re

        time_str = time_str.strip().upper()

        # Pattern to match time with optional AM/PM
        pattern = r"(\d{1,2}):(\d{2})\s*(AM|PM)?"
        match = re.match(pattern, time_str)

        if not match:
            return None

        hour = int(match.group(1))
        minute = int(match.group(2))
        am_pm = match.group(3)

        # Validate hour and minute
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            return None

        # Handle AM/PM conversion
        if am_pm:
            if am_pm == "PM" and hour != 12:
                hour += 12
            elif am_pm == "AM" and hour == 12:
                hour = 0
        # If no AM/PM and hour > 12, assume 24-hour format
        # If hour <= 12 and no AM/PM, assume AM (could be ambiguous, but common case)

        # Format as HH:MM
        return f"{hour:02d}:{minute:02d}"

    @handle_errors("getting enabled questions for UI", default_return={})
    def get_enabled_questions_for_ui(
        self, user_id: str | None = None
    ) -> dict[str, dict[str, Any]]:
        """Get questions formatted for UI display with enabled_by_default status.

        Includes both predefined and custom questions if user_id is provided.
        """
        questions = self.get_all_questions(user_id)
        ui_questions = {}

        for key, question in questions.items():
            # For custom questions, check the 'enabled' field directly
            # For predefined questions, use 'enabled_by_default'
            if user_id and key.startswith("custom_"):
                # Custom question - enabled state is stored in the question itself
                enabled = question.get("enabled", False)
            else:
                # Predefined question - use enabled_by_default
                enabled = question.get("enabled_by_default", False)

            ui_questions[key] = {
                "enabled": enabled,
                "ui_display_name": question.get("ui_display_name", key),
                "category": question.get("category", "general"),
                "type": question.get("type", "unknown"),
            }

        return ui_questions

    @handle_errors("getting categories", default_return={})
    def get_categories(self) -> dict[str, dict[str, str]]:
        """Get all question categories."""
        if not self.questions_data:
            return {}

        return self.questions_data.get("categories", {})

    @handle_errors("getting custom questions", default_return={})
    def get_custom_questions(self, user_id: str) -> dict[str, dict[str, Any]]:
        """Get custom questions for a specific user from preferences."""
        try:
            from core.user_data_handlers import get_user_data

            prefs_result = get_user_data(user_id, "preferences")
            prefs = prefs_result.get("preferences") or {}
            checkin_settings = prefs.get("checkin_settings", {})
            custom_questions = checkin_settings.get("custom_questions", {})
            return custom_questions if isinstance(custom_questions, dict) else {}
        except Exception as e:
            logger.error(f"Error loading custom questions for user {user_id}: {e}")
            return {}

    @handle_errors("saving custom question", default_return=False)
    def save_custom_question(
        self, user_id: str, question_key: str, question_def: dict[str, Any]
    ) -> bool:
        """Save a custom question to user preferences."""
        try:
            from core.user_data_handlers import get_user_data, update_user_preferences

            # Get current preferences
            prefs_result = get_user_data(user_id, "preferences")
            prefs = prefs_result.get("preferences") or {}

            # Ensure checkin_settings structure exists
            if "checkin_settings" not in prefs:
                prefs["checkin_settings"] = {}
            if "custom_questions" not in prefs["checkin_settings"]:
                prefs["checkin_settings"]["custom_questions"] = {}

            # Add/update the custom question
            prefs["checkin_settings"]["custom_questions"][question_key] = question_def

            # Save updated preferences
            update_user_preferences(user_id, prefs)
            logger.info(f"Saved custom question '{question_key}' for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving custom question for user {user_id}: {e}")
            return False

    @handle_errors("deleting custom question", default_return=False)
    def delete_custom_question(self, user_id: str, question_key: str) -> bool:
        """Delete a custom question from user preferences."""
        try:
            from core.user_data_handlers import get_user_data, update_user_preferences

            # Get current preferences
            prefs_result = get_user_data(user_id, "preferences")
            prefs = prefs_result.get("preferences") or {}

            # Ensure checkin_settings structure exists
            if "checkin_settings" not in prefs:
                prefs["checkin_settings"] = {}
            if "custom_questions" not in prefs["checkin_settings"]:
                prefs["checkin_settings"]["custom_questions"] = {}

            # Remove the custom question if it exists
            if question_key in prefs["checkin_settings"]["custom_questions"]:
                del prefs["checkin_settings"]["custom_questions"][question_key]

                # Save updated preferences
                update_user_preferences(user_id, prefs)
                logger.info(
                    f"Deleted custom question '{question_key}' for user {user_id}"
                )
                return True
            else:
                logger.warning(
                    f"Custom question '{question_key}' not found for user {user_id}"
                )
                return False
        except Exception as e:
            logger.error(f"Error deleting custom question for user {user_id}: {e}")
            return False

    @handle_errors("getting question templates", default_return={})
    def get_question_templates(self) -> dict[str, dict[str, Any]]:
        """Get available question templates for creating custom questions."""
        try:
            templates_file = (
                Path(__file__).parent.parent
                / "resources"
                / "default_checkin"
                / "question_templates.json"
            )
            if templates_file.exists():
                templates_data = load_json_data(str(templates_file))
                return templates_data.get("templates", {})
            return {}
        except Exception as e:
            logger.error(f"Error loading question templates: {e}")
            return {}


# Create a global instance for convenience
dynamic_checkin_manager = DynamicCheckinManager()
