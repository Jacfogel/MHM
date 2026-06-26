"""Per-user defaults for natural-language task due-date and time phrases."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core import get_user_data
from core.error_handling import handle_errors
from core.logger import get_component_logger
from tasks.task_time_parsing import parse_time_string

logger = get_component_logger("tasks")

_BUILTIN_TIME_OF_DAY_DEFAULTS: dict[str, str] = {
    "morning": "9:00",
    "afternoon": "14:00",
    "evening": "18:00",
    "night": "21:00",
}


@dataclass(frozen=True)
class TaskNaturalLanguageDefaults:
    """Resolved natural-language parsing defaults for one user."""

    tonight_start_time: str = "18:00"
    after_work_school_time: str = "17:00"
    time_of_day_defaults: dict[str, str] = field(
        default_factory=lambda: dict(_BUILTIN_TIME_OF_DAY_DEFAULTS)
    )
    weekend_this_week_means_coming_week: bool = True

    # error_handling_exclude: delegates to build_builtin_task_natural_language_defaults (@handle_errors)
    @classmethod
    def builtin(cls) -> TaskNaturalLanguageDefaults:
        """Return built-in defaults when user preferences are unset or invalid."""
        return build_builtin_task_natural_language_defaults()

    # error_handling_exclude: delegates to merge_task_natural_language_preferences (@handle_errors)
    @classmethod
    def from_preferences(cls, data: dict[str, Any] | None) -> TaskNaturalLanguageDefaults:
        """Merge stored preference payload onto built-in defaults."""
        if not data or not isinstance(data, dict):
            return cls.builtin()
        return merge_task_natural_language_preferences(data)


@handle_errors("building builtin task natural-language defaults")
def build_builtin_task_natural_language_defaults() -> TaskNaturalLanguageDefaults:
    """Construct built-in defaults (no user preferences applied)."""
    return TaskNaturalLanguageDefaults()


_FALLBACK_NL_DEFAULTS = build_builtin_task_natural_language_defaults()


@handle_errors(
    "merging task natural-language defaults from preferences",
    default_return=_FALLBACK_NL_DEFAULTS,
)
def merge_task_natural_language_preferences(
    data: dict[str, Any],
) -> TaskNaturalLanguageDefaults:
    """Apply user preference overrides onto built-in natural-language defaults."""
    base = _FALLBACK_NL_DEFAULTS
    tonight = _coerce_time_setting(data.get("tonight_start_time"), base.tonight_start_time)
    after_work = _coerce_time_setting(
        data.get("after_work_school_time"), base.after_work_school_time
    )

    merged_tod = dict(base.time_of_day_defaults)
    raw_tod = data.get("time_of_day_defaults")
    if isinstance(raw_tod, dict):
        for key, value in raw_tod.items():
            if isinstance(key, str) and isinstance(value, str):
                coerced = _coerce_time_setting(value, merged_tod.get(key, value))
                if coerced:
                    merged_tod[key.lower()] = coerced

    weekend_flag = data.get("weekend_this_week_means_coming_week")
    if not isinstance(weekend_flag, bool):
        weekend_flag = base.weekend_this_week_means_coming_week

    return TaskNaturalLanguageDefaults(
        tonight_start_time=tonight,
        after_work_school_time=after_work,
        time_of_day_defaults=merged_tod,
        weekend_this_week_means_coming_week=weekend_flag,
    )


@handle_errors("parsing task natural-language preference time", default_return=None)
def _parse_preference_time(value: Any) -> str | None:
    """Parse a single preference time string when present and valid."""
    if not isinstance(value, str) or not value.strip():
        return None
    return parse_time_string(value.strip())


@handle_errors("coercing task natural-language time setting")
def _coerce_time_setting(value: Any, fallback: str) -> str:
    """Parse a preference time string, falling back when empty or invalid."""
    return _parse_preference_time(value) or fallback


@handle_errors(
    "loading task natural-language defaults",
    default_return=_FALLBACK_NL_DEFAULTS,
)
def get_task_natural_language_defaults(
    user_id: str | None,
) -> TaskNaturalLanguageDefaults:
    """Load task natural-language defaults for a user (built-ins when unset)."""
    if not user_id:
        return TaskNaturalLanguageDefaults.builtin()

    user_data = get_user_data(user_id, "preferences")
    preferences = user_data.get("preferences", {}) if user_data else {}
    task_settings = preferences.get("task_settings", {})
    if not isinstance(task_settings, dict):
        return TaskNaturalLanguageDefaults.builtin()

    stored = task_settings.get("natural_language_defaults", {})
    return TaskNaturalLanguageDefaults.from_preferences(
        stored if isinstance(stored, dict) else None
    )


@handle_errors("building time-of-day cutoff datetime", default_return=None)
def _time_of_day_cutoff(now_dt: datetime, parsed_time: str) -> datetime | None:
    """Build a datetime cutoff from HH:MM on the same calendar day as *now_dt*."""
    hour_text, minute_text = parsed_time.split(":", 1)
    return now_dt.replace(
        hour=int(hour_text),
        minute=int(minute_text),
        second=0,
        microsecond=0,
    )


@handle_errors("checking past time-of-day cutoff", default_return=False)
def is_past_time_of_day(now_dt: datetime, time_setting: str, *, fallback_hour: int = 17) -> bool:
    """Return True when *now_dt* is at or after the configured time-of-day."""
    parsed = parse_time_string(time_setting)
    if not parsed:
        return now_dt.hour >= fallback_hour
    cutoff = _time_of_day_cutoff(now_dt, parsed)
    if cutoff is None:
        return now_dt.hour >= fallback_hour
    return now_dt >= cutoff
