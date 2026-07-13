"""Honest wellness-status replies when check-in, mood, or health data is missing."""

from __future__ import annotations

import re
from typing import Any

from core.error_handling import handle_errors
from core.health_context_builder import (
    context_has_usable_health_wellness,
    health_wellness_snippet_from_context,
)

_WELLNESS_STATUS_PATTERN = re.compile(
    r"(?i)\b(?:"
    r"how am i doing|how have i been(?: doing)?|how am i feeling|"
    r"how(?:'s| is) my (?:mood|energy|wellness)|"
    r"am i doing (?:okay|ok|well|alright)"
    r")\b"
)

_GENERIC_DEFLECTION_PATTERN = re.compile(
    r"(?i)^(?:i'm doing well|i am doing well|i'm fine|i am fine)"
    r"(?:\.|!)?\s*(?:how are you|what would you like|how can i help)?"
)


@handle_errors("checking wellness status question", default_return=False)
def is_wellness_status_question(prompt: str) -> bool:
    """True when the user asks for a personal wellness or progress read."""
    if not prompt or not isinstance(prompt, str):
        return False
    return bool(_WELLNESS_STATUS_PATTERN.search(prompt.strip()))


@handle_errors("checking wellness data in context", default_return=False)
def context_has_wellness_data(context: dict[str, Any]) -> bool:
    """True when context includes check-in, mood trend, or recent health guidance."""
    if not context:
        return False

    if context_has_usable_health_wellness(context):
        return True

    recent_activity = context.get("recent_activity") or {}
    if int(recent_activity.get("recent_responses_count") or 0) > 0:
        return True

    mood_trends = context.get("mood_trends") or {}
    if mood_trends.get("average_mood") is not None:
        return True
    if mood_trends.get("average_energy") is not None:
        return True
    trend = str(mood_trends.get("trend") or "").strip().lower()
    return bool(trend and trend not in {"no_data", "unknown", "none"})


@handle_errors("building preferred name prefix", default_return="")
def _preferred_name_prefix(context: dict[str, Any]) -> str:
    """Return a preferred-name salutation prefix when profile data includes one."""
    profile = context.get("user_profile") or {}
    name = str(profile.get("preferred_name") or "").strip()
    return f"{name}, " if name else ""


@handle_errors("building health-only wellness status reply", default_return="")
def _reply_from_health_only(prefix: str, health_text: str, *, has_checkins: bool) -> str:
    """Build a wellness reply grounded in health data when check-ins are weak or absent."""
    if has_checkins:
        return (
            f"{prefix}Your recent check-ins don't give me a clear mood picture yet, "
            f"but from your wellness data: {health_text}"
        )
    return (
        f"{prefix}I don't have check-in data yet, but from your recent wellness data: "
        f"{health_text} How are you feeling right now?"
    )


@handle_errors("building honest wellness status reply", default_return="")
def build_honest_wellness_status_reply(context: dict[str, Any]) -> str:
    """Return a supportive reply that does not invent wellness metrics."""
    prefix = _preferred_name_prefix(context)
    health_text = health_wellness_snippet_from_context(context)
    recent_count = int(
        (context.get("recent_activity") or {}).get("recent_responses_count") or 0
    )
    has_checkins = recent_count > 0

    mood_trends = context.get("mood_trends") or {}
    avg_mood = mood_trends.get("average_mood")
    trend = mood_trends.get("trend")
    if avg_mood is not None:
        trend_text = f" and your recent trend looks {trend}" if trend else ""
        base = (
            f"{prefix}From your recent check-ins, your average mood is around "
            f"{float(avg_mood):.1f}{trend_text}."
        )
        if health_text:
            return (
                f"{base} From your wellness data: {health_text} "
                f"I'm here if you want to talk through what's behind that."
            )
        return f"{base} I'm here if you want to talk through what's behind that."

    if health_text:
        return _reply_from_health_only(prefix, health_text, has_checkins=has_checkins)

    return (
        f"{prefix}I don't have check-in or recent wellness data for you yet, so I can't "
        f"give a grounded read on how you're doing. I'm here to support you though - "
        f"how are you feeling right now? Once you start check-ins or connect wellness "
        f"data, I can reflect patterns back to you."
    )


@handle_errors("reinforcing wellness honesty in reply", default_return="")
def reinforce_wellness_honesty_if_needed(
    user_prompt: str,
    response: str,
    context: dict[str, Any],
) -> str:
    """Replace generic deflections when a wellness question lacks supporting data."""
    if not is_wellness_status_question(user_prompt):
        return response
    if context_has_wellness_data(context):
        return response

    text = (response or "").strip()
    if not text or not _GENERIC_DEFLECTION_PATTERN.search(text):
        if any(
            phrase in text.lower()
            for phrase in ("don't have", "no check-in", "not enough", "yet")
        ):
            return response
        if "support" in text.lower() or "here to help" in text.lower():
            return response
        return build_honest_wellness_status_reply(context)

    return build_honest_wellness_status_reply(context)
