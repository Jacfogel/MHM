# ai/command_registry.py

"""Single source for command intent names used in AI command prompts."""

import re

from communication.message_processing.command_parser import get_rule_based_intent_names
from core.error_handling import handle_errors


@handle_errors("getting command intent names", default_return=[])
def get_command_intent_names() -> list[str]:
    """Return sorted intent names from the rule-based command parser patterns."""
    return get_rule_based_intent_names()


@handle_errors("formatting command actions for prompt", default_return="unknown")
def format_command_actions_for_prompt() -> str:
    """Format intent names for inclusion in the command system prompt."""
    names = get_command_intent_names()
    if not names:
        return "unknown"
    return ", ".join(names)


@handle_errors("injecting command actions into prompt", default_return="")
def inject_command_actions_into_prompt(prompt_content: str) -> str:
    """Replace the static 'Available actions:' list with the live registry."""
    if not prompt_content:
        return prompt_content
    actions = format_command_actions_for_prompt()
    if not actions or actions == "unknown":
        return prompt_content
    return re.sub(
        r"(Available actions: )[^.]+\.",
        rf"\1{actions}.",
        prompt_content,
        count=1,
    )
