# ai/fallback_responses/coordinator.py

"""Orchestrates fallback routing: check-in data first, then keyword support."""

import ai.fallback.data_access as data_access

from ai.context.builder import analyze_recent_checkin_rows
from ai.fallback.categories import FallbackCategory
from ai.fallback.checkin_summary import try_checkin_summary_response
from ai.fallback.conversational import (
    default_contextual_response,
    try_conversational_support,
    try_new_user_no_context,
    try_technical_unavailable,
)
from ai.fallback.profile_helpers import (
    load_user_context,
    name_prefix_from_context,
    preferred_name_from_context,
)
from core.error_handling import handle_errors


@handle_errors(
    "building contextual fallback",
    default_return=(
        "I'd like to help with that! How can I assist you today?",
        FallbackCategory.GENERAL_SUPPORT,
    ),
)
def build_contextual_fallback(
    user_prompt: str, user_id: str | None = None
) -> tuple[str, FallbackCategory]:
    """
    Provide contextually aware fallback responses based on user data and prompt analysis.
    Check-in analytics are handled separately from generic keyword support.
    """
    prompt_lower = user_prompt.lower()
    user_context = load_user_context(user_id)
    user_name = preferred_name_from_context(user_context)
    name_prefix = name_prefix_from_context(user_context)

    recent_data = data_access.get_recent_responses(user_id, limit=10) if user_id else None
    is_new_user = bool(not user_context or (user_id and not recent_data))

    if recent_data:
        analysis = analyze_recent_checkin_rows(recent_data)
        checkin_result = try_checkin_summary_response(
            prompt_lower, analysis, name_prefix
        )
        if checkin_result:
            return checkin_result

    technical = try_technical_unavailable(prompt_lower, name_prefix)
    if technical:
        return technical

    new_user = try_new_user_no_context(prompt_lower, name_prefix, is_new_user)
    if new_user:
        return new_user

    conversational = try_conversational_support(
        prompt_lower, name_prefix, user_name
    )
    if conversational:
        return conversational

    return default_contextual_response(name_prefix, is_new_user)
