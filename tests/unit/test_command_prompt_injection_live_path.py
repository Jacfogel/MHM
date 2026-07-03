"""Verify command intent list injection on production-style initialization paths."""

import pytest

from ai.prompts.command_interpreter import get_command_interpreter
from ai.prompts.command_registry import get_command_intent_names
from ai.prompts.manager import get_prompt_manager
import communication.message_processing.command_parser as command_parser_module
from communication.message_processing.command_parser import get_enhanced_command_parser
from communication.message_processing.interaction_manager import InteractionManager


@pytest.mark.unit
@pytest.mark.ai
class TestCommandPromptInjectionLivePath:
    def test_parser_singleton_populates_rule_based_intent_patterns(self):
        get_enhanced_command_parser()
        patterns = command_parser_module.RULE_BASED_INTENT_PATTERNS
        assert patterns is not None
        assert "create_task" in patterns

    def test_prompt_manager_injects_live_intents_after_parser_init(self):
        get_enhanced_command_parser()
        prompt = get_prompt_manager().get_prompt("command")
        assert "injected at runtime" not in prompt
        assert "create_task" in prompt
        assert "list_tasks" in prompt

    def test_command_interpreter_prompt_uses_injected_intents(self):
        get_enhanced_command_parser()
        messages = get_command_interpreter().create_command_parsing_prompt("list tasks")
        system_content = messages[0]["content"]
        assert "Product AI flow: action_interpretation" in system_content
        assert "create_task" in system_content
        for intent in get_command_intent_names()[:5]:
            assert intent in system_content

    def test_interaction_manager_init_enables_command_prompt_injection(self):
        manager = InteractionManager()
        assert manager.command_parser is not None
        assert command_parser_module.RULE_BASED_INTENT_PATTERNS is not None
        prompt = get_prompt_manager().get_prompt("command")
        assert "create_task" in prompt
