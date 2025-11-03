"""AI package for the MHM application.

Contains AI chatbot functionality, conversation management, context building,
prompt management, and LM Studio integration for conversational AI support.
"""

# Main public API - package-level exports for easier refactoring
from .chatbot import AIChatBotSingleton, get_ai_chatbot
from .cache_manager import ResponseCache, get_response_cache, get_context_cache
from .context_builder import ContextBuilder, get_context_builder
from .prompt_manager import PromptManager, get_prompt_manager

__all__ = [
    # Chatbot
    'AIChatBotSingleton',
    'get_ai_chatbot',
    # Cache management
    'ResponseCache',
    'get_response_cache',
    'get_context_cache',
    # Context building
    'ContextBuilder',
    'get_context_builder',
    # Prompt management
    'PromptManager',
    'get_prompt_manager',
]

