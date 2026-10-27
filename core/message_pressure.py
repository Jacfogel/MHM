"""One deterministic pressure policy for task, motivational, and health messages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.error_handling import handle_errors
from core.time_utilities import now_datetime_full, parse_date_only, parse_timestamp_full

DEFAULT_LOW_ENERGY_THRESHOLD = 2
MIN_LOW_ENERGY_THRESHOLD = 1
MAX_LOW_ENERGY_THRESHOLD = 4

_GENTLE_GUIDANCE = {
    "avoid_high_pressure_productivity_prompt",
    "avoid_nagging_movement_prompts",
    "keep_expectations_small",
    "use_gentle_tone",
}


@dataclass(frozen=True)
class MessagePressureSettings:
    """Saved user controls for deterministic message-pressure decisions."""

    automatic_energy_rules: bool = True
    low_energy_threshold: int = DEFAULT_LOW_ENERGY_THRESHOLD
    quiet_mode_until: str | None = None


@dataclass(frozen=True)
class MessagePressurePolicy:
    """Reliable user signals reduced to channel-agnostic pressure guidance."""

    energy: int | None
    guidance: tuple[str, ...]
    gentle: bool
    avoid_nagging: bool
    low_energy: bool = False
    low_energy_threshold: int = DEFAULT_LOW_ENERGY_THRESHOLD
    quiet_mode: bool = False
    quiet_mode_until: str | None = None
    energy_cooldown: bool = False

    @property
    @handle_errors("explaining message pressure", default_return="")
    def explanation(self) -> str:
        """Explain only rules that actually softened this decision."""
        reasons = []
        if self.quiet_mode:
            reasons.append(
                f"Quiet mode is on until {self.quiet_mode_until}. Scheduled check-ins "
                "and encouragement are paused; due, overdue, urgent, and critical "
                "task reminders can still arrive with gentler wording."
            )
        if self.energy_cooldown:
            reasons.append(
                "A recent low-energy check-in is keeping support gentle for 30 minutes "
                "after that answer, so pressure does not rise immediately."
            )
        elif self.low_energy:
            reasons.append(
                f"Your check-in energy ({self.energy}/5) meets your low-energy rule "
                f"(1–{self.low_energy_threshold}); smaller steps and gentler wording "
                "are favored while urgent tasks stay visible."
            )
        return " ".join(reasons)


@handle_errors(
    "normalizing message pressure settings",
    default_return=MessagePressureSettings(),
)
def message_pressure_settings_from_preferences(
    preferences: dict[str, Any] | None,
) -> MessagePressureSettings:
    """Normalize saved controls without guessing from free-form user text."""
    raw = (preferences or {}).get("message_pressure_settings") or {}
    if not isinstance(raw, dict):
        raw = {}

    automatic = raw.get("automatic_energy_rules", True)
    if type(automatic) is not bool:
        automatic = True

    threshold = raw.get("low_energy_threshold", DEFAULT_LOW_ENERGY_THRESHOLD)
    if (
        type(threshold) is not int
        or not MIN_LOW_ENERGY_THRESHOLD <= threshold <= MAX_LOW_ENERGY_THRESHOLD
    ):
        threshold = DEFAULT_LOW_ENERGY_THRESHOLD

    quiet_until = raw.get("quiet_mode_until")
    if not isinstance(quiet_until, str) or parse_timestamp_full(quiet_until) is None:
        quiet_until = None

    return MessagePressureSettings(
        automatic_energy_rules=automatic,
        low_energy_threshold=threshold,
        quiet_mode_until=quiet_until,
    )


@handle_errors(
    "loading message pressure settings",
    default_return=MessagePressureSettings(),
)
def load_message_pressure_settings(user_id: str) -> MessagePressureSettings:
    """Read one user's saved deterministic pressure controls."""
    from core import get_user_data

    result = get_user_data(user_id, "preferences", normalize_on_read=True)
    return message_pressure_settings_from_preferences(result.get("preferences"))


@handle_errors("checking quiet mode", default_return=False)
def quiet_mode_is_active(
    settings: MessagePressureSettings,
    *,
    now_dt: datetime | None = None,
) -> bool:
    """Return whether the saved quiet-mode expiry is still in the future."""
    quiet_until = parse_timestamp_full(settings.quiet_mode_until or "")
    return quiet_until is not None and quiet_until > (now_dt or now_datetime_full())


@handle_errors("checking user quiet mode", default_return=False)
def user_quiet_mode_is_active(user_id: str) -> bool:
    """Check the manual quiet control without loading health or check-in signals."""
    from scheduler.user_timezone import user_local_now_naive

    return quiet_mode_is_active(
        load_message_pressure_settings(user_id),
        now_dt=user_local_now_naive(user_id),
    )


@handle_errors("applying the low-energy rule", default_return=False)
def energy_is_low(energy: int | None, settings: MessagePressureSettings) -> bool:
    """Apply the user's explicit one-to-five energy rule."""
    return bool(
        settings.automatic_energy_rules
        and type(energy) is int
        and 1 <= energy <= settings.low_energy_threshold
    )


@handle_errors("checking quiet-mode task urgency", default_return=False)
def task_reminder_allowed_during_quiet_mode(
    task: dict[str, Any],
    *,
    now_dt: datetime | None = None,
) -> bool:
    """Allow only due, overdue, urgent, or critical task reminders while quiet."""
    priority = str(task.get("priority") or "").strip().lower()
    if priority in {"urgent", "critical"}:
        return True

    from tasks.task_data_handlers import runtime_task_due_date

    due_text = runtime_task_due_date(task)
    due = parse_date_only(due_text) if due_text else None
    return due is not None and due.date() <= (now_dt or now_datetime_full()).date()


@handle_errors(
    "resolving coordinated message pressure",
    default_return=MessagePressurePolicy(None, (), False, False),
)
def resolve_message_pressure(user_id: str) -> MessagePressurePolicy:
    """Resolve saved controls and today's reliable signals without an LLM."""
    from checkins.checkin_service import (
        recent_low_energy_cooldown,
        today_checkin_energy,
    )
    from core.health_signals import get_message_guidance

    settings = load_message_pressure_settings(user_id)
    energy = today_checkin_energy(user_id)
    guidance = tuple(
        dict.fromkeys(
            str(item).strip().lower()
            for item in get_message_guidance(user_id)
            if str(item).strip()
        )
    )
    guidance_set = set(guidance)
    low_energy = energy_is_low(energy, settings)
    from scheduler.user_timezone import user_local_now_naive

    now_dt = user_local_now_naive(user_id)
    cooldown = bool(
        settings.automatic_energy_rules
        and type(energy) is int
        and 1 <= energy <= 5
        and not low_energy
        and recent_low_energy_cooldown(
            user_id, settings.low_energy_threshold, now_dt=now_dt
        )
    )
    low_energy = low_energy or cooldown
    quiet_mode = quiet_mode_is_active(settings, now_dt=now_dt)
    return MessagePressurePolicy(
        energy=energy,
        guidance=guidance,
        gentle=quiet_mode or low_energy or bool(guidance_set & _GENTLE_GUIDANCE),
        avoid_nagging=quiet_mode or "avoid_nagging_movement_prompts" in guidance_set,
        low_energy=low_energy,
        low_energy_threshold=settings.low_energy_threshold,
        quiet_mode=quiet_mode,
        quiet_mode_until=settings.quiet_mode_until if quiet_mode else None,
        energy_cooldown=cooldown,
    )


@handle_errors("building coordinated message pressure prompt", default_return="")
def scheduled_message_pressure_prefix(user_id: str) -> str:
    """Return private prompt guidance shared by all scheduled message categories."""
    from integrations.google_health.personalization_rules import (
        build_scheduled_message_context_prefix,
    )

    policy = resolve_message_pressure(user_id)
    hints = build_scheduled_message_context_prefix(list(policy.guidance))
    if policy.low_energy:
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
