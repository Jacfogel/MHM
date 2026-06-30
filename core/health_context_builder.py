"""
Safe AI-facing health guidance (no raw wearable metrics).
"""

from __future__ import annotations

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
