"""AI package for the MHM application.

Contains AI chatbot functionality, conversation management, context building,
prompt management, and LM Studio integration for conversational AI support.
"""

# Main public API - package-level exports for easier refactoring
from .chatbot import AIChatBotSingleton, get_ai_chatbot
from .cache_manager import ResponseCache, get_response_cache, get_context_cache, CacheEntry, ContextCache
from .context_builder import ContextBuilder, get_context_builder, ContextData, ContextAnalysis
from .prompt_manager import PromptManager, get_prompt_manager, PromptTemplate
from .conversation_history import ConversationHistory, get_conversation_history, ConversationMessage, ConversationSession
from .lm_studio_manager import LMStudioManager, get_lm_studio_manager, is_lm_studio_ready, ensure_lm_studio_ready

__all__ = [
    # Chatbot
    'AIChatBotSingleton',
    'get_ai_chatbot',
    # Cache management
    'ResponseCache',
    'get_response_cache',
    'get_context_cache',
    'CacheEntry',
    'ContextCache',
    # Context building
    'ContextBuilder',
    'get_context_builder',
    'ContextData',
    'ContextAnalysis',
    # Prompt management
    'PromptManager',
    'get_prompt_manager',
    'PromptTemplate',
    # Conversation history
    'ConversationHistory',
    'get_conversation_history',
    'ConversationMessage',
    'ConversationSession',
    # LM Studio management
    'LMStudioManager',
    'get_lm_studio_manager',
    'is_lm_studio_ready',
    'ensure_lm_studio_ready',
]

