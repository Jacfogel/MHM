"""Prompt composition, command interpretation metadata, and action catalog."""

from ai.prompts.action_catalog import (
    AIActionCatalog,
    AIActionDefinition,
    AIActionField,
    AIActionRequest,
    build_action_catalog,
    get_action_catalog,
)
from ai.prompts.command_interpreter import CommandInterpreter, get_command_interpreter
from ai.prompts.command_registry import (
    format_command_actions_for_prompt,
    get_command_intent_names,
    inject_command_actions_into_prompt,
)
from ai.prompts.flows import (
    PRODUCT_AI_PROMPT_FLOWS,
    RUNTIME_PROMPT_CATEGORIES,
    ProductAIPromptFlow,
    get_product_ai_prompt_flow,
)
from ai.prompts.manager import PromptManager, PromptTemplate, get_prompt_manager

__all__ = [
    "AIActionCatalog",
    "AIActionDefinition",
    "AIActionField",
    "AIActionRequest",
    "build_action_catalog",
    "get_action_catalog",
    "CommandInterpreter",
    "get_command_interpreter",
    "format_command_actions_for_prompt",
    "get_command_intent_names",
    "inject_command_actions_into_prompt",
    "PRODUCT_AI_PROMPT_FLOWS",
    "RUNTIME_PROMPT_CATEGORIES",
    "ProductAIPromptFlow",
    "get_product_ai_prompt_flow",
    "PromptManager",
    "PromptTemplate",
    "get_prompt_manager",
]
