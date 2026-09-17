# ai/fallback_responses/personalized.py

"""Personalized fallback messages when the AI model is unavailable."""

import ai.fallback.data_access as data_access

from ai.fallback.categories import FallbackCategory
from ai.fallback.profile_helpers import name_prefix_from_context
from core.error_handling import ValidationError, handle_errors


@handle_errors(
    "building personalized fallback message",
    default_return=(
        "Hope you're having a good day! Remember to take care of yourself "
        "and celebrate the small wins along the way.",
        FallbackCategory.PERSONALIZED_MESSAGE,
    ),
)
def build_personalized_message(
    user_id: str, *, source: str
) -> tuple[str, FallbackCategory]:
    """Provide fallback personalized messages when AI model is not available."""
    if source not in {"checkin", "google_health", "profile"}:
        raise ValidationError(
            f"Unsupported personalized message source: {source}",
            details={"source": source},
        )
    context_result = data_access.get_user_data(user_id, "context")
    user_context = context_result.get("context") if context_result else {}
    name_prefix = name_prefix_from_context(user_context or {})

    if source == "profile":
        interests = user_context.get("interests") or []
        goals = user_context.get("goals") or []
        if interests:
            return (
                f"{name_prefix}I hope you can make a little room for {interests[0]} today. "
                "A small moment spent on something you enjoy still counts.",
                FallbackCategory.PERSONALIZED_MESSAGE,
            )
        if goals:
            return (
                f"{name_prefix}A small step toward {goals[0]} is enough for today. "
                "Steady progress matters more than perfection.",
                FallbackCategory.PERSONALIZED_MESSAGE,
            )
        return (
            f"{name_prefix}Hope you're having a good day. Make a little room for something "
            "that feels meaningful to you.",
            FallbackCategory.PERSONALIZED_MESSAGE,
        )

    if source == "google_health":
        from core.health_context_builder import build_user_facing_signal_wellness_snippet

        health_note = build_user_facing_signal_wellness_snippet(user_id)
        if health_note:
            return (
                f"{name_prefix}{health_note} Be gentle with yourself and choose what feels manageable.",
                FallbackCategory.PERSONALIZED_MESSAGE,
            )
        return (
            f"{name_prefix}Hope you're having a good day. Listen to what your body needs "
            "and choose a manageable pace.",
            FallbackCategory.PERSONALIZED_MESSAGE,
        )

    recent_data = data_access.get_recent_responses(user_id, limit=5)

    if recent_data:
        latest_entry = recent_data[0]
        mood = latest_entry.get("mood", None)
        energy = latest_entry.get("energy", None)

        if mood and energy:
            if mood >= 4 and energy >= 4:
                return (
                    f"{name_prefix}You're doing great! Your recent check-ins show positive energy and mood. "
                    f"Keep up those healthy habits and celebrate your progress!",
                    FallbackCategory.PERSONALIZED_MESSAGE,
                )
            if mood <= 2 or energy <= 2:
                return (
                    f"{name_prefix}I noticed things might be challenging for you lately. "
                    f"Remember that tough days are temporary, and it's okay to take things one step at a time. "
                    f"Consider reaching out for support if you need it.",
                    FallbackCategory.PERSONALIZED_MESSAGE,
                )
            return (
                f"{name_prefix}You're making steady progress! Focus on the small things that "
                f"make you feel good and energized. Every positive step counts.",
                FallbackCategory.PERSONALIZED_MESSAGE,
            )

    return (
        f"{name_prefix}Hope you're having a good day! Remember to take care of yourself "
        f"and celebrate the small wins along the way.",
        FallbackCategory.PERSONALIZED_MESSAGE,
    )
