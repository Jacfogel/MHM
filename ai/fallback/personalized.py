# ai/fallback_responses/personalized.py

"""Personalized fallback messages when the AI model is unavailable."""

import ai.fallback.data_access as data_access

from ai.fallback.categories import FallbackCategory
from ai.fallback.profile_helpers import name_prefix_from_context
from core.error_handling import handle_errors


@handle_errors(
    "building personalized fallback message",
    default_return=(
        "Hope you're having a good day! Remember to take care of yourself "
        "and celebrate the small wins along the way.",
        FallbackCategory.PERSONALIZED_MESSAGE,
    ),
)
def build_personalized_message(user_id: str) -> tuple[str, FallbackCategory]:
    """Provide fallback personalized messages when AI model is not available."""
    recent_data = data_access.get_recent_responses(user_id, limit=5)
    context_result = data_access.get_user_data(user_id, "context")
    user_context = context_result.get("context") if context_result else {}
    name_prefix = name_prefix_from_context(user_context or {})

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
