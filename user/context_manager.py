#!/usr/bin/env python3

"""
user_context_manager.py

Manages in-memory session conversation history for AI chat.
Context reads use ``build_chatbot_context_dict`` with optional session overlay.
"""

from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.time_utilities import now_timestamp_full

context_logger = get_component_logger("user_activity")
logger = context_logger


class UserContextManager:
    """Tracks per-session chat exchanges and overlays them on envelope-backed context."""

    # ERROR_HANDLING_EXCLUDE: Simple constructor that only sets attributes
    def __init__(self):
        """Initialize conversation history storage for in-memory session exchanges."""
        self.conversation_history: dict[str, list[dict]] = {}

    @handle_errors("building context with session overlay", default_return=None)
    def build_context_with_session_overlay(
        self, user_id: str, *, include_session_history: bool = True
    ) -> dict[str, Any]:
        """
        Build envelope-backed chatbot context with in-memory session exchanges overlaid.

        Prefer ``build_chatbot_context_dict`` when session overlay is not needed.
        """
        from ai.context.chatbot_context import build_chatbot_context_dict

        context = build_chatbot_context_dict(
            user_id, include_conversation_history=include_session_history
        )
        if not context:
            return self._get_minimal_context(user_id)

        if include_session_history:
            session_history = self._get_conversation_history(user_id)
            if session_history:
                context["conversation_history"] = session_history

        logger.debug(f"Built session-overlay context for user {user_id}")
        return context

    @handle_errors("getting session conversation history", default_return=[])
    def get_session_conversation_history(self, user_id: str) -> list[dict[str, str]]:
        """Return recent in-memory session exchanges for this user."""
        return self._get_conversation_history(user_id)

    @handle_errors("getting conversation history", default_return=[])
    def _get_conversation_history(self, user_id: str) -> list[dict[str, str]]:
        """Return recent in-memory session exchanges for this user."""
        return self.conversation_history.get(user_id, [])[-5:]

    @handle_errors("adding conversation exchange")
    def add_conversation_exchange(
        self, user_id: str, user_message: str, ai_response: str
    ):
        """Add a conversation exchange to in-memory session history."""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []

        exchange = {
            "timestamp": now_timestamp_full(),
            "user_message": user_message,
            "ai_response": ai_response,
            "message_length": len(user_message),
            "response_length": len(ai_response),
        }

        self.conversation_history[user_id].append(exchange)

        if len(self.conversation_history[user_id]) > 20:
            self.conversation_history[user_id] = self.conversation_history[user_id][
                -20:
            ]

        logger.debug(f"Added conversation exchange for user {user_id}")

    @handle_errors("getting minimal context", default_return={})
    def _get_minimal_context(self, user_id: str | None) -> dict[str, Any]:
        """Fallback minimal context if envelope-backed context generation fails."""
        return {
            "user_profile": {
                "preferred_name": "User" if user_id else "Anonymous",
                "active_categories": [],
                "messaging_service": "",
                "active_schedules": [],
            },
            "recent_activity": {
                "recent_responses_count": 0,
                "last_response_date": None,
                "recent_messages_count": 0,
                "last_message_date": None,
            },
            "conversation_insights": {
                "recent_topics": [],
                "interaction_count": 0,
                "avg_message_length": 0,
                "engagement_level": "low",
            },
            "preferences": {},
            "mood_trends": {},
            "conversation_history": [],
        }

    @handle_errors(
        "formatting context for AI", default_return="User context unavailable"
    )
    def format_context_for_ai(self, context: dict[str, Any]) -> str:
        """Format user context into a concise string for AI prompt."""
        if not context:
            return "User context unavailable"

        profile = context.get("user_profile", {})
        activity = context.get("recent_activity", {})
        insights = context.get("conversation_insights", {})

        context_parts = []

        if profile.get("preferred_name"):
            context_parts.append(f"User: {profile['preferred_name']}")

        if profile.get("active_categories"):
            context_parts.append(
                f"Active categories: {', '.join(profile['active_categories'])}"
            )

        if activity.get("recent_responses_count", 0) > 0:
            context_parts.append(
                f"Recent check-ins: {activity['recent_responses_count']}"
            )

        if activity.get("last_response_date"):
            context_parts.append(f"Last response: {activity['last_response_date']}")

        if insights.get("recent_topics"):
            context_parts.append(
                f"Recent topics: {', '.join(insights['recent_topics'])}"
            )

        if insights.get("engagement_level"):
            context_parts.append(f"Engagement: {insights['engagement_level']}")

        return " | ".join(context_parts) if context_parts else "No recent activity"


# Global instance
user_context_manager = UserContextManager()
