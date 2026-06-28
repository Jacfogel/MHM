"""
Safe AI-facing health guidance (no raw wearable metrics).
"""

from __future__ import annotations

from core.error_handling import handle_errors
from core.health_signals import get_google_health_feature_state, get_today_signal
from integrations.google_health.personalization_rules import (
    GUIDANCE_AVOID_NAG,
    GUIDANCE_AVOID_PRESSURE,
    GUIDANCE_GENTLE,
    GUIDANCE_LIGHT_MOVEMENT,
    GUIDANCE_LOW_EFFORT,
    GUIDANCE_REINFORCE,
    GUIDANCE_SHORT_WALK,
    GUIDANCE_SMALL_EXPECTATIONS,
)


@handle_errors("building safe health guidance summary", default_return="")
def build_safe_health_guidance_summary(user_id: str) -> str:
    """
    Return coarse wellness guidance for AI context.

    Never includes exact steps, HR, HRV, or device names.
    """
    state = get_google_health_feature_state(user_id)
    if state == "disabled":
        return ""
    if state == "paused":
        return "Health personalization is paused; use normal supportive messaging."

    signal = get_today_signal(user_id)
    if not signal:
        return ""

    confidence = signal.get("confidence") or "low"
    if confidence == "low":
        return ""

    guidance = signal.get("message_guidance") or []
    if not guidance:
        return ""

    phrases: list[str] = []

    if GUIDANCE_GENTLE in guidance or GUIDANCE_SMALL_EXPECTATIONS in guidance:
        phrases.append(
            "Recent rest and recovery patterns suggest a gentler day; keep expectations smaller."
        )
    if GUIDANCE_AVOID_PRESSURE in guidance:
        phrases.append("Avoid productivity pressure or high-effort asks today.")
    if GUIDANCE_LOW_EFFORT in guidance:
        phrases.append(
            "Small resets (water, food, breathing, brief rest) are more appropriate than big pushes."
        )
    if GUIDANCE_LIGHT_MOVEMENT in guidance or GUIDANCE_SHORT_WALK in guidance:
        phrases.append("Light movement like a short walk or stretch may feel good if they choose.")
    if GUIDANCE_REINFORCE in guidance:
        phrases.append("Acknowledge recent activity positively without nagging about more movement.")
    if GUIDANCE_AVOID_NAG in guidance:
        phrases.append("Do not nag about exercise or steps.")

    if not phrases:
        return ""

    return (
        "Health personalization (wellness-oriented, not medical): "
        + " ".join(phrases)
        + " Never diagnose, cite wearables, or suggest medical treatment."
    )
