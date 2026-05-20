"""Unit tests for ai/command_registry.py."""

import pytest

from ai.command_registry import (
    format_command_actions_for_prompt,
    get_command_intent_names,
    inject_command_actions_into_prompt,
)
from communication.message_processing.command_parser import (
    RULE_BASED_INTENT_PATTERNS,
    get_rule_based_intent_names,
)


@pytest.mark.unit
@pytest.mark.ai
class TestCommandRegistry:
    def test_get_command_intent_names_matches_parser_when_loaded(self):
        if RULE_BASED_INTENT_PATTERNS is None:
            pytest.skip("EnhancedCommandParser not constructed in this test process")
        assert get_command_intent_names() == get_rule_based_intent_names()

    def test_format_command_actions_non_empty_when_patterns_loaded(self):
        if RULE_BASED_INTENT_PATTERNS is None:
            pytest.skip("EnhancedCommandParser not constructed in this test process")
        formatted = format_command_actions_for_prompt()
        assert "create_task" in formatted

    def test_inject_command_actions_replaces_static_list_when_patterns_loaded(self):
        if RULE_BASED_INTENT_PATTERNS is None:
            pytest.skip("EnhancedCommandParser not constructed in this test process")
        base = "Available actions: create_task, old_action. For help: ACTION: unknown"
        result = inject_command_actions_into_prompt(base)
        assert "old_action" not in result
        assert "create_task" in result
        assert result.startswith("Available actions:")
