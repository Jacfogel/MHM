# ai/fallback_responses/personalized.py

"""Personalized fallback messages when the AI model is unavailable."""

import ai.fallback.data_access as data_access
import random

from ai.fallback.categories import FallbackCategory
from ai.fallback.profile_helpers import name_prefix_from_context
from core.error_handling import ValidationError, handle_errors


@handle_errors(
    "building varied profile fallback message",
    default_return=(
        "You can leave a little space in your day for something you enjoy.",
        FallbackCategory.PERSONALIZED_MESSAGE,
    ),
)
def _profile_fallback(
    user_id: str, context: dict, name_prefix: str
) -> tuple[str, FallbackCategory]:
    """Choose across profile details and avoid recently delivered fallback wording."""
    from messages.message_data_manager import get_recent_messages

    candidates = []
    for field, templates in (
        (
            "interests",
            (
                "Enjoying {detail} doesn't have to be productive to be worthwhile.",
                "If you're in the mood for {detail}, you could try a different approach just for fun.",
                "What first drew you to {detail}? That spark can be worth revisiting.",
            ),
        ),
        (
            "goals",
            (
                "For your goal of {detail}, you can choose a pace that fits your life.",
                "There's more than one way to approach {detail}. You can adjust the plan as you learn.",
            ),
        ),
        (
            "activities_for_encouragement",
            (
                "If it appeals to you today, {detail} could be something to look forward to.",
                "You don't need a special occasion to enjoy {detail}.",
            ),
        ),
    ):
        values = context.get(field) or []
        if isinstance(values, str):
            values = [values]
        for value in values:
            detail = str(value).strip()
            if detail:
                candidates.extend(
                    name_prefix + template.format(detail=detail)
                    for template in templates
                )
    if not candidates:
        candidates = [
            name_prefix + text
            for text in (
                "You can leave a little space in your day for something you enjoy.",
                "Your time and attention matter. It's okay to choose what feels meaningful today.",
                "A quiet moment can be worthwhile too. You don't have to fill every pause.",
            )
        ]
    recent = get_recent_messages(user_id, category="personalized_profile", limit=5)
    sent = {str(message.get("sent_text") or "").strip() for message in recent}
    return (
        random.choice([text for text in candidates if text not in sent] or candidates),
        FallbackCategory.PERSONALIZED_MESSAGE,
    )


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
        return _profile_fallback(user_id, user_context or {}, name_prefix)

    if source == "google_health":
        from core.health_context_builder import (
            build_user_facing_signal_wellness_snippet,
        )

        from core.health_signals import health_personalization_allowed

        health_note = (
            build_user_facing_signal_wellness_snippet(user_id)
            if health_personalization_allowed(user_id, surface="messages")
            else ""
        )
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
