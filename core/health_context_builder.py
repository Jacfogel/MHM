"""
Safe AI-facing health guidance (no raw wearable metrics).
"""

from __future__ import annotations

from typing import Any

from core.error_handling import handle_errors
from core.health_signals import (
    get_google_health_feature_state,
    is_personalization_active,
    resolve_active_health_signal,
)
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

    signal = resolve_active_health_signal(user_id)
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


_HEALTH_GUIDANCE_PREFIX = "Health personalization (wellness-oriented, not medical): "
_HEALTH_GUIDANCE_SUFFIX = (
    " Never diagnose, cite wearables, or suggest medical treatment."
)
_PAUSED_HEALTH_GUIDANCE = (
    "Health personalization is paused; use normal supportive messaging."
)


@handle_errors("formatting health guidance for user reply", default_return="")
def format_health_guidance_for_user_reply(guidance_summary: str) -> str:
    """Strip AI-prompt framing and return user-facing wellness text."""
    text = (guidance_summary or "").strip()
    if not text or text == _PAUSED_HEALTH_GUIDANCE:
        return ""
    if text.startswith(_HEALTH_GUIDANCE_PREFIX):
        text = text[len(_HEALTH_GUIDANCE_PREFIX) :]
    if text.endswith(_HEALTH_GUIDANCE_SUFFIX):
        text = text[: -len(_HEALTH_GUIDANCE_SUFFIX)]
    return text.strip()


@handle_errors("reading health wellness snippet from context", default_return="")
def health_wellness_snippet_from_context(
    context: dict[str, Any] | None = None,
    *,
    user_id: str | None = None,
    guidance_summary: str | None = None,
) -> str:
    """Return user-facing wellness text from envelope context or live health signals."""
    summary = (guidance_summary or "").strip()
    if not summary and context:
        summary = str(context.get("health_guidance_summary") or "").strip()
        if not summary:
            summary = str(context.get("health_wellness_snippet") or "").strip()
    formatted = format_health_guidance_for_user_reply(summary)
    if formatted:
        return formatted
    if user_id:
        return build_user_facing_signal_wellness_snippet(user_id)
    return ""


@handle_errors("building user-facing wellness snippet from health signal", default_return="")
def build_user_facing_signal_wellness_snippet(user_id: str) -> str:
    """
    Return a coarse, user-facing wellness read from the active health signal.

    Used when message_guidance is empty or confidence is low but recent wearable
    data still supports an honest wellness reply.
    """
    if not is_personalization_active(user_id):
        return ""

    signal = resolve_active_health_signal(user_id)
    if not signal:
        return ""

    phrases: list[str] = []
    sleep_recovery = str(signal.get("sleep_recovery") or "unknown").strip().lower()
    if sleep_recovery == "high":
        phrases.append("your recent rest and recovery look stronger than usual")
    elif sleep_recovery == "low":
        phrases.append("your recent rest and recovery look lower than usual")

    sleep_vs = str(signal.get("sleep_vs_baseline") or "unknown").strip().lower()
    if sleep_vs == "below":
        phrases.append("sleep has been below your usual baseline")
    elif sleep_vs == "above":
        phrases.append("sleep has been above your usual baseline")
    elif sleep_vs == "normal":
        phrases.append("sleep has been close to your usual baseline")

    activity = str(signal.get("activity_level") or "unknown").strip().lower()
    if activity == "low":
        phrases.append("activity has been on the lighter side")
    elif activity == "high":
        phrases.append("you have been more active than usual")
    elif activity == "normal":
        phrases.append("activity has been around your usual level")

    resting_hr = str(signal.get("resting_hr_signal") or "unknown").strip().lower()
    if resting_hr == "elevated":
        phrases.append("resting heart rate looks a bit elevated versus your baseline")
    elif resting_hr == "low":
        phrases.append("resting heart rate looks lower than your baseline")

    hrv = str(signal.get("hrv_signal") or "unknown").strip().lower()
    if hrv == "low":
        phrases.append("recovery signals look lower than your baseline")
    elif hrv == "high":
        phrases.append("recovery signals look stronger than your baseline")

    if not phrases:
        return ""

    if len(phrases) == 1:
        return f"{phrases[0].capitalize()}."
    return f"{phrases[0].capitalize()}, and {phrases[1]}."


@handle_errors("checking usable health wellness context", default_return=False)
def context_has_usable_health_wellness(
    context: dict[str, Any] | None = None,
    *,
    user_id: str | None = None,
    guidance_summary: str | None = None,
) -> bool:
    """True when recent Google Health guidance can ground a wellness reply."""
    return bool(
        health_wellness_snippet_from_context(
            context,
            user_id=user_id,
            guidance_summary=guidance_summary,
        )
    )


_SKIP_CHECKIN_KEYS = frozenset(
    {
        "timestamp",
        "submitted_at",
        "questions_asked",
        "responses",
        "metadata",
        "source",
        "linked_item_ids",
        "created_at",
        "updated_at",
        "archived_at",
        "deleted_at",
        "id",
    }
)


@handle_errors("formatting check-in entry for personalized prompt", default_return="")
def _format_checkin_entry_for_prompt(entry: dict) -> str:
    if not isinstance(entry, dict):
        return ""
    parts: list[str] = []
    submitted = entry.get("submitted_at") or entry.get("timestamp")
    if submitted:
        parts.append(f"date={str(submitted)[:10]}")

    for key, value in entry.items():
        if key in _SKIP_CHECKIN_KEYS:
            continue
        if key == "sleep_schedule" and isinstance(value, dict):
            hours = value.get("total_sleep_hours")
            if isinstance(hours, (int, float)):
                parts.append(f"checkin_sleep_hours={hours}")
            continue
        if isinstance(value, dict):
            continue
        parts.append(f"{key}={value}")

    return ", ".join(parts)


@handle_errors("formatting coarse health signal for prompt", default_return="")
def _format_health_signal_coarse(signal: dict) -> str:
    if not signal:
        return ""
    parts: list[str] = []
    if signal.get("date"):
        parts.append(f"signal_date={signal['date']}")
    for field in (
        "sleep_recovery",
        "sleep_vs_baseline",
        "activity_level",
        "resting_hr_signal",
        "hrv_signal",
    ):
        value = signal.get(field) or "unknown"
        if value != "unknown":
            parts.append(f"{field}={value}")
    return ", ".join(parts)


PERSONALIZED_CHECKIN_LOOKBACK_DAYS = 7


@handle_errors("building personalized wellness context", default_return="")
def build_personalized_wellness_context(user_id: str) -> str:
    """
    Compact wellness context for scheduled personalized messages.

    Google Health signals take priority; stale check-ins are excluded.
    """
    from checkins.checkin_data_manager import get_checkins_by_days

    sections: list[str] = []
    health_signal = None
    if is_personalization_active(user_id):
        health_signal = resolve_active_health_signal(user_id)
        coarse = _format_health_signal_coarse(health_signal or {})
        if coarse:
            sections.append(f"Primary source — wearable wellness (coarse): {coarse}")

    health_summary = build_safe_health_guidance_summary(user_id)
    if health_summary:
        sections.append(health_summary)

    health_is_primary = bool(
        health_signal and health_signal.get("confidence") in ("medium", "high")
    )
    if not health_is_primary:
        recent_checkins = get_checkins_by_days(
            user_id, days=PERSONALIZED_CHECKIN_LOOKBACK_DAYS
        )
        if recent_checkins:
            formatted = [
                line
                for line in (
                    _format_checkin_entry_for_prompt(entry) for entry in recent_checkins
                )
                if line
            ]
            if formatted:
                sections.append("Recent check-ins: " + " | ".join(formatted))

    if not sections:
        return "No recent wellness data available."

    return " ".join(sections)
