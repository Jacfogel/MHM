"""
Deterministic message personalization rules from derived health signals.

No diagnosis or medical claims - guidance tokens only.
"""

from __future__ import annotations

from typing import Any

from core.error_handling import handle_errors

GUIDANCE_GENTLE = "use_gentle_tone"
GUIDANCE_AVOID_PRESSURE = "avoid_high_pressure_productivity_prompt"
GUIDANCE_LOW_EFFORT = "suggest_low_effort_health_action"
GUIDANCE_LIGHT_MOVEMENT = "allow_light_movement_prompt"
GUIDANCE_SHORT_WALK = "suggest_short_walk_or_stretch"
GUIDANCE_REINFORCE = "send_reinforcement"
GUIDANCE_AVOID_NAG = "avoid_nagging_movement_prompts"
GUIDANCE_SMALL_EXPECTATIONS = "keep_expectations_small"


@handle_errors("appending guidance token", default_return=None)
def _add_guidance(tokens: list[str], *items: str) -> None:
    """Append unique message_guidance tokens without duplicates."""
    for item in items:
        if item not in tokens:
            tokens.append(item)


@handle_errors("applying health personalization rules", default_return=[])
def apply_personalization_rules(signal: dict[str, Any]) -> list[str]:
    """
    Map derived signal fields to message_guidance tokens.

    Returns empty list when confidence is low or data insufficient.
    """
    confidence = signal.get("confidence") or "low"
    if confidence == "low":
        return []

    guidance: list[str] = []

    sleep_recovery = signal.get("sleep_recovery") or "unknown"
    sleep_vs_baseline = signal.get("sleep_vs_baseline") or "unknown"
    activity_level = signal.get("activity_level") or "unknown"
    resting_hr = signal.get("resting_hr_signal") or "unknown"
    hrv_signal = signal.get("hrv_signal") or "unknown"

    poor_sleep = sleep_recovery == "low" or sleep_vs_baseline == "below"
    good_sleep = sleep_recovery in ("normal", "high") and sleep_vs_baseline != "below"
    low_activity = activity_level == "low"
    high_activity = activity_level == "high"

    if poor_sleep and low_activity:
        _add_guidance(
            guidance,
            GUIDANCE_GENTLE,
            GUIDANCE_AVOID_PRESSURE,
            GUIDANCE_LOW_EFFORT,
        )
    elif good_sleep and low_activity:
        _add_guidance(
            guidance,
            GUIDANCE_LIGHT_MOVEMENT,
            GUIDANCE_SHORT_WALK,
        )
    elif high_activity:
        _add_guidance(
            guidance,
            GUIDANCE_REINFORCE,
            GUIDANCE_AVOID_NAG,
        )

    if confidence in ("medium", "high") and (
        resting_hr == "elevated" or hrv_signal == "low"
    ):
        _add_guidance(
            guidance,
            GUIDANCE_GENTLE,
            GUIDANCE_SMALL_EXPECTATIONS,
        )

    if poor_sleep and not low_activity:
        _add_guidance(guidance, GUIDANCE_GENTLE, GUIDANCE_SMALL_EXPECTATIONS)

    return guidance


@handle_errors("building contextual prompt prefix from guidance", default_return="")
def build_scheduled_message_context_prefix(guidance: list[str]) -> str:
    """Optional prefix hints for scheduled AI messages (no raw metrics)."""
    if not guidance:
        return ""

    hints: list[str] = []
    if GUIDANCE_GENTLE in guidance:
        hints.append("Use a gentler, supportive tone.")
    if GUIDANCE_AVOID_PRESSURE in guidance:
        hints.append("Avoid productivity pressure or high-effort asks.")
    if GUIDANCE_LOW_EFFORT in guidance:
        hints.append("Suggest very small resets like water, food, breathing, or rest.")
    if GUIDANCE_LIGHT_MOVEMENT in guidance:
        hints.append("Light movement suggestions are okay if gentle.")
    if GUIDANCE_SHORT_WALK in guidance:
        hints.append("A short walk or stretch may be appropriate.")
    if GUIDANCE_REINFORCE in guidance:
        hints.append("Acknowledge recent activity positively.")
    if GUIDANCE_AVOID_NAG in guidance:
        hints.append("Do not nag about movement.")
    if GUIDANCE_SMALL_EXPECTATIONS in guidance:
        hints.append("Keep expectations smaller today.")

    return " ".join(hints)
