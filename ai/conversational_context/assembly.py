# ai/conversational_context/assembly.py

"""Orchestrate natural-language context sections into LM Studio message arrays."""

from typing import Any

from ai.conversational_context.instructions import CONVERSATIONAL_CONTEXT_INSTRUCTIONS
from ai.conversational_context.sections import (
    append_activity_and_mood_trends,
    append_checkin_summary,
    append_conversation_history,
    append_feature_enablement,
    append_profile_sections,
    append_recent_sent_messages,
    append_schedule_details,
    append_task_data,
    append_task_reminder,
    append_today_checkin_status,
)
from core.error_handling import handle_errors
from user.context_manager import user_context_manager


@handle_errors("building conversational context parts", default_return=[])
def build_context_parts(user_id: str) -> list[str]:
    """Assemble natural-language context lines for the system prompt."""
    context = user_context_manager.get_ai_context(
        user_id, include_conversation_history=True
    )
    parts: list[str] = []

    append_profile_sections(parts, context)
    append_feature_enablement(parts, user_id)
    append_checkin_summary(parts, user_id)
    append_activity_and_mood_trends(parts, user_id, context)
    append_conversation_history(parts, context)
    append_today_checkin_status(parts, user_id)

    recent_sent_all = append_recent_sent_messages(parts, user_id)
    append_task_reminder(parts, recent_sent_all)
    append_task_data(parts, user_id)
    append_schedule_details(parts, user_id, context)

    return parts


@handle_errors(
    "assembling comprehensive conversational messages",
    default_return=[
        {
            "role": "system",
            "content": "You are a supportive wellness assistant. Keep responses helpful, encouraging, and conversational.",
        },
        {"role": "user", "content": "Hello"},
    ],
)
def assemble_comprehensive_messages(
    user_id: str, user_prompt: str, wellness_base_prompt: str
) -> list[dict[str, Any]]:
    """Build system + user messages for comprehensive conversational generation."""
    context_parts = build_context_parts(user_id)
    context_str = (
        "\n".join(context_parts) if context_parts else "New user with no data"
    )

    instructions = CONVERSATIONAL_CONTEXT_INSTRUCTIONS.format(context_str=context_str)
    system_message = {
        "role": "system",
        "content": f"{wellness_base_prompt}\n{instructions}",
    }
    user_message = {"role": "user", "content": user_prompt}
    return [system_message, user_message]
