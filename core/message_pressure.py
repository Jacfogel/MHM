"""One pressure policy for task, motivational, and health messages."""

from __future__ import annotations

from dataclasses import dataclass

from core.error_handling import handle_errors

_GENTLE_GUIDANCE = {
    "avoid_high_pressure_productivity_prompt",
    "avoid_nagging_movement_prompts",
    "keep_expectations_small",
    "use_gentle_tone",
}


@dataclass(frozen=True)
class MessagePressurePolicy:
    """Reliable user signals reduced to channel-agnostic pressure guidance."""

    energy: int | None
    guidance: tuple[str, ...]
    gentle: bool
    avoid_nagging: bool


@handle_errors(
    "resolving coordinated message pressure",
    default_return=MessagePressurePolicy(None, (), False, False),
)
def resolve_message_pressure(user_id: str) -> MessagePressurePolicy:
    """Resolve today's reliable signals without exposing raw health measurements."""
    from checkins.checkin_service import today_checkin_energy
    from core.health_signals import get_message_guidance

    energy = today_checkin_energy(user_id)
    guidance = tuple(
        dict.fromkeys(
            str(item).strip().lower()
            for item in get_message_guidance(user_id)
            if str(item).strip()
        )
    )
    guidance_set = set(guidance)
    return MessagePressurePolicy(
        energy=energy,
        guidance=guidance,
        gentle=energy in {1, 2} or bool(guidance_set & _GENTLE_GUIDANCE),
        avoid_nagging="avoid_nagging_movement_prompts" in guidance_set,
    )


@handle_errors("building coordinated message pressure prompt", default_return="")
def scheduled_message_pressure_prefix(user_id: str) -> str:
    """Return private prompt guidance shared by all scheduled message categories."""
    from integrations.google_health.personalization_rules import (
        build_scheduled_message_context_prefix,
    )

    policy = resolve_message_pressure(user_id)
    hints = build_scheduled_message_context_prefix(list(policy.guidance))
    if policy.energy in {1, 2}:
        guidance = set(policy.guidance)
        energy_hints = []
        if "use_gentle_tone" not in guidance:
            energy_hints.append("Use a gentler, supportive tone.")
        if "keep_expectations_small" not in guidance:
            energy_hints.append("Keep expectations smaller today.")
        if "avoid_high_pressure_productivity_prompt" not in guidance:
            energy_hints.append("Avoid productivity pressure or high-effort asks.")
        hints = f"{hints} {' '.join(energy_hints)}".strip()
    if policy.avoid_nagging:
        hints = (
            f"{hints} Keep this message optional and avoid repeated prompting."
        ).strip()
    return hints
