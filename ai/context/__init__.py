"""User context gathering and conversational prompt assembly."""

from ai.context.assembly import assemble_comprehensive_messages, build_context_parts
from ai.context.builder import (
    ContextAnalysis,
    ContextBuilder,
    ContextData,
    analyze_recent_checkin_rows,
    get_context_builder,
)
from ai.context.history import (
    ConversationHistory,
    ConversationMessage,
    ConversationSession,
    get_conversation_history,
)
from ai.context.service import (
    AIContextEnvelope,
    AIContextSection,
    build_ai_context_envelope,
)

__all__ = [
    "assemble_comprehensive_messages",
    "build_context_parts",
    "ContextAnalysis",
    "ContextBuilder",
    "ContextData",
    "analyze_recent_checkin_rows",
    "get_context_builder",
    "ConversationHistory",
    "ConversationMessage",
    "ConversationSession",
    "get_conversation_history",
    "AIContextEnvelope",
    "AIContextSection",
    "build_ai_context_envelope",
]
