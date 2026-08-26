# ai/command_registry.py

"""
Bridge from AI command prompts to rule-based intent names.

Dependency direction (intentional):
  ``ai.prompts.command_registry`` -> ``communication.message_processing.command_parser``

The communication layer owns ``RULE_BASED_INTENT_PATTERNS`` and intent detection.
The AI layer must not duplicate that list in prompt text. This module injects the
live intent names into the command system prompt at runtime.

Reverse coupling (separate concern):
  ``communication`` modules call ``ai.chat.chatbot.get_ai_chatbot`` for generation.
  That does not import ``command_registry``.

If ``RULE_BASED_INTENT_PATTERNS`` is unset, injection initializes the parser
singleton so every run mode gets the live list. The template in
``resources/prompts/command.txt`` stays a placeholder, not a second inventory.

Imports from ``command_parser`` are lazy (inside ``get_command_intent_names``) to avoid
a circular import when ``command_parser`` loads ``ai.chat.chatbot`` during package init.
"""

import re
from collections.abc import Iterable

from core.error_handling import handle_errors


_AVAILABLE_ACTIONS_LINE = re.compile(r"^(Available actions: ).+$", re.MULTILINE)


@handle_errors("getting command intent names", default_return=[])
# not_duplicate: command_registry_raw_vs_initialized_intents
def get_command_intent_names() -> list[str]:
    """Return sorted intent names from the rule-based command parser patterns."""
    # Lazy import avoids circular load: command_parser imports ai.chat.chatbot, which
    # loads ai.__init__ -> command_registry before command_parser finishes init.
    from communication.message_processing.command_parser import get_rule_based_intent_names

    return get_rule_based_intent_names()


@handle_errors("getting initialized command intent names", default_return=[])
# not_duplicate: command_registry_raw_vs_initialized_intents
def get_initialized_command_intent_names() -> list[str]:
    """Return live parser intent names, initializing the parser registry if needed."""
    names = get_command_intent_names()
    if names:
        return names

    from communication.message_processing.command_parser import get_enhanced_command_parser

    get_enhanced_command_parser()
    return get_command_intent_names()


@handle_errors("canonicalizing command intent name", default_return="")
# not_duplicate: command_registry_intent_canonicalize_bridge
def canonicalize_intent_name(
    raw: str, known_intents: Iterable[str] | None = None
) -> str:
    """Normalize spaced or hyphenated ACTION names to live parser intent names.

    AI modules must call this registry helper instead of importing
    ``communication.message_processing.intent_validation`` directly.
    """
    from communication.message_processing.intent_validation import (
        canonicalize_intent_name as canonicalize_communication_intent_name,
    )

    return canonicalize_communication_intent_name(raw, known_intents)


@handle_errors("formatting command actions for prompt", default_return="unknown")
def format_command_actions_for_prompt() -> str:
    """Format intent names for inclusion in the command system prompt."""
    names = get_initialized_command_intent_names()
    if not names:
        return "unknown"
    return ", ".join(names)


@handle_errors("injecting command actions into prompt", default_return="")
def inject_command_actions_into_prompt(prompt_content: str) -> str:
    """Replace the 'Available actions:' line with the live registry."""
    if not prompt_content:
        return prompt_content
    actions = format_command_actions_for_prompt()
    if not actions or actions == "unknown":
        return prompt_content
    if not _AVAILABLE_ACTIONS_LINE.search(prompt_content):
        return prompt_content
    return _AVAILABLE_ACTIONS_LINE.sub(
        lambda match: f"{match.group(1)}{actions}.",
        prompt_content,
        count=1,
    )
