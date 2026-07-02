"""AI package for the MHM application.

Contains AI chatbot functionality, conversation management, context building,
prompt management, and LM Studio integration for conversational AI support.
"""

# Main public API - package-level exports for easier refactoring
from .chatbot import AIChatBotSingleton, get_ai_chatbot
from .cache_manager import (
    CacheEntry,
    ContextCache,
    ResponseCache,
    get_context_cache,
    get_response_cache,
)
from .action_catalog import (
    AIActionCatalog,
    AIActionDefinition,
    AIActionField,
    AIActionRequest,
    build_action_catalog,
    get_action_catalog,
)
from .command_interpreter import CommandInterpreter, get_command_interpreter
from .command_registry import (
    format_command_actions_for_prompt,
    get_command_intent_names,
    inject_command_actions_into_prompt,
)
from .context_builder import (
    ContextAnalysis,
    ContextBuilder,
    ContextData,
    get_context_builder,
)
from .context_service import (
    AIContextEnvelope,
    AIContextSection,
    build_ai_context_envelope,
)
from .conversation_history import (
    ConversationHistory,
    ConversationMessage,
    ConversationSession,
    get_conversation_history,
)
from .conversational_context import assemble_comprehensive_messages, build_context_parts
from .fallback_responses import (
    FallbackCategory,
    FallbackResponses,
    build_contextual_fallback,
    get_fallback_responses,
)
from .interaction_types import AIInteractionType, interaction_type_for_mode
from .lm_studio_manager import (
    LMStudioManager,
    ensure_lm_studio_ready,
    get_lm_studio_manager,
    is_lm_studio_ready,
)
from .prompt_manager import PromptManager, PromptTemplate, get_prompt_manager
from .prompt_flows import (
    PRODUCT_AI_PROMPT_FLOWS,
    ProductAIPromptFlow,
    get_product_ai_prompt_flow,
)
from .response_generator import ResponseGenerator, get_response_generator

__all__ = [
    # Chatbot
    "AIChatBotSingleton",
    "get_ai_chatbot",
    # Cache management
    "ResponseCache",
    "get_response_cache",
    "get_context_cache",
    "CacheEntry",
    "ContextCache",
    # Action catalog
    "AIActionCatalog",
    "AIActionDefinition",
    "AIActionField",
    "AIActionRequest",
    "build_action_catalog",
    "get_action_catalog",
    # Command interpretation
    "CommandInterpreter",
    "get_command_interpreter",
    "get_command_intent_names",
    "format_command_actions_for_prompt",
    "inject_command_actions_into_prompt",
    # Context building
    "ContextBuilder",
    "get_context_builder",
    "ContextData",
    "ContextAnalysis",
    "AIContextEnvelope",
    "AIContextSection",
    "build_ai_context_envelope",
    # Conversational context assembly
    "assemble_comprehensive_messages",
    "build_context_parts",
    # Conversation history
    "ConversationHistory",
    "get_conversation_history",
    "ConversationMessage",
    "ConversationSession",
    # Fallback responses
    "FallbackResponses",
    "get_fallback_responses",
    "FallbackCategory",
    "build_contextual_fallback",
    # Interaction types
    "AIInteractionType",
    "interaction_type_for_mode",
    # Prompt management
    "PromptManager",
    "get_prompt_manager",
    "PromptTemplate",
    "PRODUCT_AI_PROMPT_FLOWS",
    "ProductAIPromptFlow",
    "get_product_ai_prompt_flow",
    # Response generation
    "ResponseGenerator",
    "get_response_generator",
    # LM Studio management
    "LMStudioManager",
    "get_lm_studio_manager",
    "is_lm_studio_ready",
    "ensure_lm_studio_ready",
]
