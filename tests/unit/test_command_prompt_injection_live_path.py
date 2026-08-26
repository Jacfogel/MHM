"""Verify command intent list injection on production-style initialization paths."""

import pytest

from ai.prompts.action_catalog import build_action_catalog
from ai.prompts.command_interpreter import get_command_interpreter
from ai.prompts.command_registry import get_initialized_command_intent_names
from ai.prompts.manager import get_prompt_manager
import communication.message_processing.command_parser as command_parser_module
from communication.message_processing.command_parser import get_enhanced_command_parser
from communication.message_processing.interaction_manager import InteractionManager


def _actions_from_available_line(text: str) -> set[str]:
    for line in text.splitlines():
        if line.startswith("Available actions:"):
            payload = line.split(":", 1)[1].strip().rstrip(".")
            return {part.strip() for part in payload.split(",") if part.strip()}
    return set()


def _actions_from_planning_summary(summary: str) -> set[str]:
    return {part.strip() for part in summary.split(",") if part.strip()}


@pytest.mark.unit
@pytest.mark.ai
class TestCommandPromptInjectionLivePath:
    def test_parser_singleton_populates_rule_based_intent_patterns(self):
        get_enhanced_command_parser()
        patterns = command_parser_module.RULE_BASED_INTENT_PATTERNS
        assert patterns is not None
        assert "create_task" in patterns

    def test_prompt_manager_injects_live_intents_after_parser_init(self):
        names = set(get_initialized_command_intent_names())
        prompt = get_prompt_manager().get_prompt("command")
        assert "injected at runtime" not in prompt
        assert _actions_from_available_line(prompt) == names

    def test_command_interpreter_prompt_uses_injected_intents(self):
        names = set(get_initialized_command_intent_names())
        messages = get_command_interpreter().create_command_parsing_prompt("list tasks")
        system_content = messages[0]["content"]
        assert "Product AI flow: action_interpretation" in system_content
        for intent in names:
            assert intent in system_content

    def test_interaction_manager_init_enables_command_prompt_injection(self):
        manager = InteractionManager()
        assert manager.command_parser is not None
        assert command_parser_module.RULE_BASED_INTENT_PATTERNS is not None
        prompt = get_prompt_manager().get_prompt("command")
        assert "create_task" in prompt
        assert "injected at runtime" not in prompt

    def test_action_catalog_matches_parser_intent_names(self):
        names = set(get_initialized_command_intent_names())
        catalog = build_action_catalog()
        assert set(catalog.actions) == names

    def test_planning_prompt_summary_matches_parser_intent_names(self):
        names = set(get_initialized_command_intent_names())
        catalog = build_action_catalog()
        listed = _actions_from_planning_summary(catalog.to_planning_prompt_summary())
        assert listed == names
