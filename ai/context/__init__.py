"""User context gathering and conversational prompt assembly."""

from ai.context.assembly import assemble_comprehensive_messages, build_context_parts
from ai.context.analytics import (
    ContextAnalysis,
    analyze_checkin_entries,
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
    "analyze_checkin_entries",
    "ConversationHistory",
    "ConversationMessage",
    "ConversationSession",
    "get_conversation_history",
    "AIContextEnvelope",
    "AIContextSection",
    "build_ai_context_envelope",
]
