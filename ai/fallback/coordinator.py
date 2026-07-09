# ai/fallback/coordinator.py

"""Orchestrates fallback routing: envelope summaries, check-ins, then keyword support."""

from __future__ import annotations

import ai.fallback.data_access as data_access

from ai.context.analytics import analyze_checkin_entries
from ai.context.service import AIContextEnvelope
from ai.fallback.action_hints import try_action_unavailable_response
from ai.fallback.categories import FallbackCategory
from ai.fallback.checkin_summary import try_checkin_summary_response
from ai.fallback.context import FallbackContext, build_fallback_context
from ai.fallback.conversational import (
    default_contextual_response,
    try_conversational_support,
    try_new_user_no_context,
    try_technical_unavailable,
)
from ai.fallback.envelope_summaries import try_envelope_summary_response
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
    user_prompt: str,
    user_id: str | None = None,
    *,
    envelope: AIContextEnvelope | None = None,
    fallback_context: FallbackContext | None = None,
) -> tuple[str, FallbackCategory]:
    """
    Provide contextually aware fallback responses based on envelope data and prompt analysis.
    Check-in analytics and envelope summaries are handled before generic keyword support.
    """
    prompt_lower = user_prompt.lower()
    context = fallback_context or build_fallback_context(
        user_id, user_prompt, envelope=envelope
    )

    if context is not None:
        envelope_result = try_envelope_summary_response(prompt_lower, context)
        if envelope_result:
            return envelope_result

        action_hint = try_action_unavailable_response(prompt_lower, context)
        if action_hint:
            return action_hint

        user_context = context.structured.get("personal_context") or {}
        user_name = context.preferred_name
        name_prefix = context.name_prefix
        recent_data = context.recent_checkin_rows or None
    else:
        user_context = load_user_context(user_id)
        user_name = preferred_name_from_context(user_context)
        name_prefix = name_prefix_from_context(user_context)
        recent_data = None

    if not recent_data and user_id:
        recent_data = data_access.get_recent_responses(user_id, limit=10)

    is_new_user = bool(not user_context or (user_id and not recent_data))

    if recent_data:
        analysis = analyze_checkin_entries(recent_data)
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
