"""Envelope-backed summary dict for contextual chat personalization."""

from __future__ import annotations

from typing import Any

from ai.context.analytics import analyze_checkin_entries
from ai.context.service import build_ai_context_envelope
from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("ai_context")


@handle_errors("building chatbot context dict", default_return={})
def build_chatbot_context_dict(
    user_id: str,
    *,
    include_conversation_history: bool = True,
) -> dict[str, Any]:
    """
    Build the chatbot summary dict used by ``generate_contextual_response``.

    New product-AI code should use ``AIContextEnvelope`` directly.
    """
    envelope = build_ai_context_envelope(
        user_id,
        include_conversation_history=include_conversation_history,
        requested_intent="chatbot_context_summary",
    )
    if envelope is None:
        return {
            "user_profile": {},
            "recent_activity": {},
            "conversation_insights": {},
            "preferences": {},
            "mood_trends": {"trend": "no_data"},
            "health_guidance_summary": "",
            "conversation_history": [] if include_conversation_history else [],
        }

    structured = envelope.structured
    account = structured.get("account") or {}
    preferences = structured.get("preferences") or {}
    personal_context = structured.get("personal_context") or {}
    schedules = structured.get("schedules") or {}
    checkins = structured.get("checkins") or {}
    messages = structured.get("messages") or {}
    health = structured.get("health") or {}
    conversation = structured.get("conversation") or {}

    recent_checkins = list(checkins.get("recent") or [])
    analysis = analyze_checkin_entries(recent_checkins)

    user_profile = {
        "preferred_name": (
            account.get("preferred_name")
            or personal_context.get("preferred_name")
            or ""
        ),
        "active_categories": preferences.get("categories") or [],
        "messaging_service": (preferences.get("channel") or {}).get("type", ""),
        "active_schedules": schedules.get("active_schedules") or [],
    }

    recent_sent = list(messages.get("recent_sent") or [])
    last_response_date = None
    if recent_checkins:
        ts = str(recent_checkins[0].get("submitted_at") or "").strip()
        if ts:
            last_response_date = ts.split(" ")[0]

    last_message_date = None
    if recent_sent:
        sent_at = str(recent_sent[0].get("sent_at") or "").strip()
        if sent_at:
            last_message_date = sent_at[:10]

    recent_activity = {
        "recent_responses_count": len(recent_checkins),
        "last_response_date": last_response_date,
        "recent_messages_count": min(len(recent_sent), 10),
        "last_message_date": last_message_date,
    }

    mood_trends = (
        {
            "average_mood": analysis.avg_mood,
            "average_energy": analysis.avg_energy,
            "trend": analysis.mood_trend,
        }
        if recent_checkins
        else {"trend": "no_data"}
    )

    recent_chats = list(conversation.get("recent_chat_interactions") or [])
    conversation_insights = _conversation_insights_from_chats(recent_chats)

    context = {
        "user_profile": user_profile,
        "recent_activity": recent_activity,
        "conversation_insights": conversation_insights,
        "preferences": preferences,
        "mood_trends": mood_trends,
        "health_guidance_summary": health.get("guidance_summary") or "",
        "conversation_history": (
            list(conversation.get("recent_chat_interactions") or [])
            if include_conversation_history
            else []
        ),
    }

    logger.debug(f"Built envelope-backed chatbot context for user {user_id}")
    return context


@handle_errors("building conversation insights", default_return={})
def _conversation_insights_from_chats(
    recent_chats: list[dict[str, Any]],
) -> dict[str, Any]:
    """Derive lightweight topic tags from recent chat interaction rows."""
    if not recent_chats:
        return {"recent_topics": [], "interaction_count": 0}

    topics: list[str] = []
    total_user_messages = 0

    for chat in recent_chats:
        user_msg = str(chat.get("user_message") or "")
        if len(user_msg) > 10:
            lowered = user_msg.lower()
            if any(word in lowered for word in ["mood", "feeling", "sad", "happy", "stress"]):
                topics.append("emotional_wellbeing")
            elif any(word in lowered for word in ["book", "books", "reading", "read", "novel"]):
                topics.append("reading")
            elif any(word in lowered for word in ["help", "advice", "how to", "what should"]):
                topics.append("seeking_guidance")
            elif any(word in lowered for word in ["energy", "tired", "sleep", "rest"]):
                topics.append("energy_health")
            else:
                topics.append("general_conversation")

        total_user_messages += int(chat.get("message_length") or len(user_msg))

    unique_topics = list(set(topics))
    return {
        "recent_topics": unique_topics,
        "interaction_count": len(recent_chats),
        "avg_message_length": total_user_messages // max(len(recent_chats), 1),
        "engagement_level": (
            "high"
            if len(recent_chats) > 3
            else "moderate" if len(recent_chats) > 1 else "low"
        ),
    }
