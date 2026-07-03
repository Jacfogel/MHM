"""AI package for the MHM application.

Subpackages:
- client: LM Studio API and response cache
- context: user data envelope and prompt context assembly
- prompts: prompt categories, flows, and command interpretation helpers
- chat: conversational reply orchestration and post-processing
- fallback: deterministic responses when the model is unavailable
"""

from ai.chat.chatbot import AIChatBotSingleton, get_ai_chatbot
from ai.client.cache_manager import (
    CacheEntry,
    ContextCache,
    ResponseCache,
    get_context_cache,
    get_response_cache,
)
from ai.prompts.action_catalog import (
    AIActionCatalog,
    AIActionDefinition,
    AIActionField,
    AIActionPlan,
    AIActionRequest,
    build_action_catalog,
    get_action_catalog,
)
from ai.chat.action_planner import (
    ActionPlanner,
    get_action_planner,
    parse_action_plan_from_text,
)
from ai.prompts.command_interpreter import CommandInterpreter, get_command_interpreter
from ai.prompts.command_registry import (
    format_command_actions_for_prompt,
    get_command_intent_names,
    inject_command_actions_into_prompt,
)
from ai.context.builder import (
    ContextAnalysis,
    ContextBuilder,
    ContextData,
    get_context_builder,
)
from ai.context.service import (
    AIContextEnvelope,
    AIContextSection,
    build_ai_context_envelope,
)
from ai.context.history import (
    ConversationHistory,
    ConversationMessage,
    ConversationSession,
    get_conversation_history,
)
from ai.context.assembly import (
    assemble_action_result_messages,
    assemble_comprehensive_messages,
    build_context_parts,
)
from ai.fallback import (
    FallbackCategory,
    FallbackResponses,
    build_contextual_fallback,
    get_fallback_responses,
)
from ai.chat.interaction_types import AIInteractionType, interaction_type_for_mode
from ai.client.lm_studio_manager import (
    LMStudioManager,
    ensure_lm_studio_ready,
    get_lm_studio_manager,
    is_lm_studio_ready,
)
from ai.prompts.manager import PromptManager, PromptTemplate, get_prompt_manager
from ai.prompts.flows import (
    PRODUCT_AI_PROMPT_FLOWS,
    ProductAIPromptFlow,
    get_product_ai_prompt_flow,
)
from ai.chat.response_generator import ResponseGenerator, get_response_generator

__all__ = [
    "AIChatBotSingleton",
    "get_ai_chatbot",
    "ResponseCache",
    "get_response_cache",
    "get_context_cache",
    "CacheEntry",
    "ContextCache",
    "AIActionCatalog",
    "AIActionDefinition",
    "AIActionField",
    "AIActionRequest",
    "AIActionPlan",
    "build_action_catalog",
    "get_action_catalog",
    "ActionPlanner",
    "get_action_planner",
    "parse_action_plan_from_text",
    "CommandInterpreter",
    "get_command_interpreter",
    "get_command_intent_names",
    "format_command_actions_for_prompt",
    "inject_command_actions_into_prompt",
    "ContextBuilder",
    "get_context_builder",
    "ContextData",
    "ContextAnalysis",
    "AIContextEnvelope",
    "AIContextSection",
    "build_ai_context_envelope",
    "assemble_comprehensive_messages",
    "assemble_action_result_messages",
    "build_context_parts",
    "ConversationHistory",
    "get_conversation_history",
    "ConversationMessage",
    "ConversationSession",
    "FallbackResponses",
    "get_fallback_responses",
    "FallbackCategory",
    "build_contextual_fallback",
    "AIInteractionType",
    "interaction_type_for_mode",
    "PromptManager",
    "get_prompt_manager",
    "PromptTemplate",
    "PRODUCT_AI_PROMPT_FLOWS",
    "ProductAIPromptFlow",
    "get_product_ai_prompt_flow",
    "ResponseGenerator",
    "get_response_generator",
    "LMStudioManager",
    "get_lm_studio_manager",
    "is_lm_studio_ready",
    "ensure_lm_studio_ready",
]
