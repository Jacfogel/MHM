"""Unit tests for ai/command_registry.py."""

import pytest

from ai.prompts.command_registry import (
    canonicalize_intent_name,
    format_command_actions_for_prompt,
    get_command_intent_names,
    get_initialized_command_intent_names,
    inject_command_actions_into_prompt,
)
from communication.message_processing.command_parser import (
    get_rule_based_intent_names,
)


def _actions_from_available_line(text: str) -> set[str]:
    for line in text.splitlines():
        if line.startswith("Available actions:"):
            payload = line.split(":", 1)[1].strip().rstrip(".")
            return {part.strip() for part in payload.split(",") if part.strip()}
    return set()


@pytest.mark.unit
@pytest.mark.ai
class TestCommandRegistry:
    def test_get_command_intent_names_matches_parser_when_loaded(self):
        names = get_initialized_command_intent_names()
        assert names
        assert get_command_intent_names() == get_rule_based_intent_names()
        assert names == get_rule_based_intent_names()

    def test_format_command_actions_non_empty_when_patterns_loaded(self):
        formatted = format_command_actions_for_prompt()
        assert "create_task" in formatted
        assert "create_note" in formatted
        assert "injected at runtime" not in formatted

    def test_inject_command_actions_replaces_static_list_when_patterns_loaded(self):
        base = "Available actions: create_task, old_action.\nFor help: ACTION: unknown"
        result = inject_command_actions_into_prompt(base)
        assert "old_action" not in result
        assert "create_task" in result
        assert "For help: ACTION: unknown" in result
        assert result.startswith("Available actions:")
        assert _actions_from_available_line(result) == set(
            get_initialized_command_intent_names()
        )

    def test_inject_command_actions_replaces_runtime_placeholder_when_patterns_loaded(
        self,
    ):
        base = (
            "Available actions: injected at runtime from the rule-based command parser "
            "when loaded."
        )
        result = inject_command_actions_into_prompt(base)
        assert "injected at runtime" not in result
        assert "create_task" in result
        assert _actions_from_available_line(result) == set(
            get_initialized_command_intent_names()
        )

    def test_inject_command_actions_replaces_line_without_trailing_period(self):
        base = "Available actions: placeholder list\nNext line stays."
        result = inject_command_actions_into_prompt(base)
        assert "placeholder list" not in result
        assert result.endswith("Next line stays.")
        assert "create_task" in result

    def test_canonicalize_intent_name_maps_spaced_and_hyphenated_actions(self):
        names = get_initialized_command_intent_names()
        assert canonicalize_intent_name("create note", names) == "create_note"
        assert canonicalize_intent_name("start check-in", names) == "start_checkin"
