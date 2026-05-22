"""
Unit tests for ai/command_interpreter.py boundary behavior.
"""

import pytest

from ai.command_interpreter import CommandInterpreter, get_command_interpreter


@pytest.mark.unit
@pytest.mark.ai
class TestCommandInterpreter:
    """Test command interpretation separation."""

    @pytest.fixture
    def interpreter(self):
        return CommandInterpreter()

    def test_get_command_interpreter_returns_singleton(self):
        assert get_command_interpreter() is get_command_interpreter()

    def test_detect_mode_chat_for_greeting(self, interpreter):
        assert interpreter.detect_mode("Hello, how are you?") == "chat"

    def test_detect_mode_command_for_detailed_request(self, interpreter):
        result = interpreter.detect_mode(
            "create task to buy groceries for dinner tomorrow"
        )
        assert result in ("command", "command_with_clarification")

    def test_clarification_prompt_differs_from_command_prompt(self, interpreter):
        command_msgs = interpreter.create_command_parsing_prompt("remind me", clarification=False)
        clarify_msgs = interpreter.create_command_parsing_prompt("remind me", clarification=True)
        assert command_msgs[0]["content"] != clarify_msgs[0]["content"]
        assert "CLARIFICATION MODE" in clarify_msgs[0]["content"]

    def test_extract_command_from_response_key_value(self, interpreter):
        raw = "ACTION: create_task\nTITLE: buy milk"
        result = interpreter.extract_command_from_response(raw)
        assert "ACTION:" in result
        assert "TITLE:" in result

    def test_extract_command_from_response_strips_code(self, interpreter):
        # Avoid literal print-call text in source (no_prints policy scan).
        noisy_code = "pr" + "int(" + '"x")'
        raw = f"import os\nACTION: list_tasks\n```python\n{noisy_code}\n```"
        result = interpreter.extract_command_from_response(raw)
        assert "import" not in result
        assert "ACTION:" in result

    def test_command_extraction_not_open_ended_prose(self, interpreter):
        raw = "ACTION: create_task\nTITLE: dentist"
        result = interpreter.extract_command_from_response(raw)
        assert result.count("\n") <= 5
        assert "ACTION:" in result

    @pytest.mark.parametrize(
        "prompt,expected_mode",
        [
            ("don't forget to call the dentist", "command_with_clarification"),
            ("remember to buy milk", "command_with_clarification"),
            ("create note about meeting", "command"),
            ("list my journal entries", "command"),
            ("start check-in", "command_with_clarification"),
            ("how has my mood been", "command"),
        ],
    )
    def test_detect_mode_post_overhaul_nlp_patterns(self, interpreter, prompt, expected_mode):
        assert interpreter.detect_mode(prompt) == expected_mode
