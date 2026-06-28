"""Per-user and shipped defaults for natural-language phrase parsing."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from core import get_user_data
from core.error_handling import handle_errors
from core.logger import get_component_logger
from storage.user_data_write import update_user_preferences
from tasks.task_time_parsing import parse_time_string

logger = get_component_logger("natural_language_defaults")

PREFERENCES_NL_KEY = "natural_language_defaults"
_RESOURCE_FILENAME = "default_natural_language_defaults.json"

# Last-resort fallback if resources/default_natural_language_defaults.json is missing.
_HARDCODED_FALLBACK: dict[str, Any] = {
    "tonight_start_time": "18:00",
    "after_work_school_time": "17:00",
    "time_of_day_defaults": {
        "morning": "9:00",
        "afternoon": "14:00",
        "evening": "18:00",
        "night": "21:00",
    },
    "weekend_this_week_means_coming_week": True,
}

_BUILTIN_DEFAULTS_DICT_CACHE: dict[str, Any] | None = None
_BUILTIN_DEFAULTS_CACHE: NaturalLanguageDefaults | None = None


@handle_errors(
    "loading builtin natural-language defaults JSON",
    default_return=_HARDCODED_FALLBACK,
)
def _load_builtin_defaults_dict() -> dict[str, Any]:
    """Load shipped defaults from resources/default_natural_language_defaults.json."""
    global _BUILTIN_DEFAULTS_DICT_CACHE
    if _BUILTIN_DEFAULTS_DICT_CACHE is not None:
        return _BUILTIN_DEFAULTS_DICT_CACHE

    resource_path = Path(__file__).parent.parent / "resources" / _RESOURCE_FILENAME
    try:
        with open(resource_path, encoding="utf-8") as handle:
            raw = json.load(handle)
    except FileNotFoundError:
        logger.warning(
            f"Default natural-language defaults file not found: {resource_path}"
        )
        _BUILTIN_DEFAULTS_DICT_CACHE = dict(_HARDCODED_FALLBACK)
        return _BUILTIN_DEFAULTS_DICT_CACHE
    except json.JSONDecodeError as exc:
        logger.error(
            f"Invalid JSON in default natural-language defaults file {resource_path}: {exc}"
        )
        _BUILTIN_DEFAULTS_DICT_CACHE = dict(_HARDCODED_FALLBACK)
        return _BUILTIN_DEFAULTS_DICT_CACHE

    if not isinstance(raw, dict):
        logger.warning(
            f"Invalid format in default natural-language defaults file: {resource_path}"
        )
        _BUILTIN_DEFAULTS_DICT_CACHE = dict(_HARDCODED_FALLBACK)
        return _BUILTIN_DEFAULTS_DICT_CACHE

    tod = raw.get("time_of_day_defaults")
    if not isinstance(tod, dict):
        tod = dict(_HARDCODED_FALLBACK["time_of_day_defaults"])

    weekend_flag = raw.get("weekend_this_week_means_coming_week")
    if not isinstance(weekend_flag, bool):
        weekend_flag = bool(_HARDCODED_FALLBACK["weekend_this_week_means_coming_week"])

    _BUILTIN_DEFAULTS_DICT_CACHE = {
        "tonight_start_time": raw.get(
            "tonight_start_time", _HARDCODED_FALLBACK["tonight_start_time"]
        ),
        "after_work_school_time": raw.get(
            "after_work_school_time", _HARDCODED_FALLBACK["after_work_school_time"]
        ),
        "time_of_day_defaults": {
            key: str(value)
            for key, value in tod.items()
            if isinstance(key, str) and isinstance(value, str)
        },
        "weekend_this_week_means_coming_week": weekend_flag,
    }
    return _BUILTIN_DEFAULTS_DICT_CACHE


@handle_errors("building natural-language defaults from dict", default_return=None)
def _defaults_dict_to_dataclass(data: dict[str, Any]) -> NaturalLanguageDefaults | None:
    """Construct NaturalLanguageDefaults from a normalized defaults dict."""
    if not isinstance(data, dict):
        return None
    tod = data.get("time_of_day_defaults")
    if not isinstance(tod, dict):
        tod = dict(_HARDCODED_FALLBACK["time_of_day_defaults"])
    weekend_flag = data.get("weekend_this_week_means_coming_week")
    if not isinstance(weekend_flag, bool):
        weekend_flag = bool(_HARDCODED_FALLBACK["weekend_this_week_means_coming_week"])
    return NaturalLanguageDefaults(
        tonight_start_time=str(
            data.get("tonight_start_time", _HARDCODED_FALLBACK["tonight_start_time"])
        ),
        after_work_school_time=str(
            data.get(
                "after_work_school_time",
                _HARDCODED_FALLBACK["after_work_school_time"],
            )
        ),
        time_of_day_defaults={
            key: str(value)
            for key, value in tod.items()
            if isinstance(key, str) and isinstance(value, str)
        },
        weekend_this_week_means_coming_week=weekend_flag,
    )


@dataclass(frozen=True)
class NaturalLanguageDefaults:
    """Resolved natural-language parsing defaults for one user."""

    tonight_start_time: str = "18:00"
    after_work_school_time: str = "17:00"
    time_of_day_defaults: dict[str, str] = field(
        default_factory=lambda: dict(_HARDCODED_FALLBACK["time_of_day_defaults"])
    )
    weekend_this_week_means_coming_week: bool = True

    # error_handling_exclude: delegates to build_builtin_natural_language_defaults (@handle_errors)
    @classmethod
    def builtin(cls) -> NaturalLanguageDefaults:
        """Return built-in defaults when user preferences are unset or invalid."""
        return build_builtin_natural_language_defaults()

    # error_handling_exclude: delegates to merge_natural_language_preferences (@handle_errors)
    @classmethod
    def from_preferences(cls, data: dict[str, Any] | None) -> NaturalLanguageDefaults:
        """Merge stored preference payload onto built-in defaults."""
        if not data or not isinstance(data, dict):
            return cls.builtin()
        return merge_natural_language_preferences(data)


@handle_errors("building builtin natural-language defaults")
def build_builtin_natural_language_defaults() -> NaturalLanguageDefaults:
    """Construct built-in defaults from resources/default_natural_language_defaults.json."""
    built = _defaults_dict_to_dataclass(_load_builtin_defaults_dict())
    if built is None:
        built = _defaults_dict_to_dataclass(_HARDCODED_FALLBACK)
    assert built is not None
    return built


_HARDCODED_NL_DEFAULTS = _defaults_dict_to_dataclass(_HARDCODED_FALLBACK)
assert _HARDCODED_NL_DEFAULTS is not None


@handle_errors(
    "getting cached builtin natural-language defaults",
    default_return=_HARDCODED_NL_DEFAULTS,
)
def _get_cached_builtin_defaults() -> NaturalLanguageDefaults:
    """Return cached built-in defaults loaded from resources."""
    global _BUILTIN_DEFAULTS_CACHE
    if _BUILTIN_DEFAULTS_CACHE is None:
        _BUILTIN_DEFAULTS_CACHE = build_builtin_natural_language_defaults()
    return _BUILTIN_DEFAULTS_CACHE


_FALLBACK_NL_DEFAULTS = _get_cached_builtin_defaults()


@handle_errors(
    "merging natural-language defaults from preferences",
    default_return=_FALLBACK_NL_DEFAULTS,
)
def merge_natural_language_preferences(
    data: dict[str, Any],
) -> NaturalLanguageDefaults:
    """Apply user preference overrides onto built-in natural-language defaults."""
    base = _get_cached_builtin_defaults()
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

    return NaturalLanguageDefaults(
        tonight_start_time=tonight,
        after_work_school_time=after_work,
        time_of_day_defaults=merged_tod,
        weekend_this_week_means_coming_week=weekend_flag,
    )


@handle_errors("reading stored natural-language preferences", default_return=None)
def _read_stored_nl_dict(preferences: dict[str, Any]) -> dict[str, Any] | None:
    """Read per-user NL defaults from preferences.natural_language_defaults."""
    if not isinstance(preferences, dict):
        return None
    stored = preferences.get(PREFERENCES_NL_KEY)
    if isinstance(stored, dict):
        return stored
    return None


@handle_errors("parsing natural-language preference time", default_return=None)
def _parse_preference_time(value: Any) -> str | None:
    """Parse a single preference time string when present and valid."""
    if not isinstance(value, str) or not value.strip():
        return None
    return parse_time_string(value.strip())


@handle_errors("coercing natural-language time setting")
def _coerce_time_setting(value: Any, fallback: str) -> str:
    """Parse a preference time string, falling back when empty or invalid."""
    return _parse_preference_time(value) or fallback


@handle_errors(
    "loading natural-language defaults",
    default_return=_FALLBACK_NL_DEFAULTS,
)
def get_natural_language_defaults(user_id: str | None) -> NaturalLanguageDefaults:
    """Load natural-language defaults for a user (built-ins when unset)."""
    if not user_id:
        return NaturalLanguageDefaults.builtin()

    user_data = get_user_data(user_id, "preferences")
    preferences = user_data.get("preferences", {}) if user_data else {}
    if not isinstance(preferences, dict):
        return NaturalLanguageDefaults.builtin()

    stored = _read_stored_nl_dict(preferences)
    return NaturalLanguageDefaults.from_preferences(stored)


@handle_errors("building preferences dict from natural-language defaults", default_return={})
def natural_language_defaults_to_preferences_dict(
    defaults: NaturalLanguageDefaults,
) -> dict[str, Any]:
    """Serialize resolved defaults for persistence under preferences.natural_language_defaults."""
    return {
        "tonight_start_time": defaults.tonight_start_time,
        "after_work_school_time": defaults.after_work_school_time,
        "time_of_day_defaults": dict(defaults.time_of_day_defaults),
        "weekend_this_week_means_coming_week": defaults.weekend_this_week_means_coming_week,
    }


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


_TIME_OF_DAY_FIELDS = frozenset(_HARDCODED_FALLBACK["time_of_day_defaults"].keys())

_NL_FIELD_ALIASES: dict[str, str] = {
    "tonight": "tonight_start_time",
    "after_work": "after_work_school_time",
    "after_school": "after_work_school_time",
    "weekend_this_week": "weekend_this_week_means_coming_week",
    "weekend": "weekend_this_week_means_coming_week",
    "this_week": "weekend_this_week_means_coming_week",
}


@dataclass(frozen=True)
class NaturalLanguageDefaultsUpdateResult:
    """Outcome of applying one natural-language defaults change."""

    success: bool
    updated_labels: tuple[str, ...] = ()
    error_message: str | None = None


@handle_errors("normalizing natural-language field key", default_return="")
def normalize_nl_field_key(field: str) -> str:
    """Map user-facing field names to stored preference keys."""
    normalized = field.strip().lower().replace(" ", "_").replace("-", "_")
    return _NL_FIELD_ALIASES.get(normalized, normalized)


@handle_errors("parsing weekend this-week flag", default_return=None)
def parse_weekend_this_week_flag(value: str) -> bool | None:
    """Parse on/off/coming/current style values for weekend `this week` behavior."""
    token = value.strip().lower()
    if token in {"on", "yes", "true", "coming", "next"}:
        return True
    if token in {"off", "no", "false", "current", "this"}:
        return False
    return None


@handle_errors("formatting natural-language defaults message", default_return="")
def format_natural_language_defaults_message(defaults: NaturalLanguageDefaults) -> str:
    """Build channel-neutral help text for current phrase-to-time mappings."""
    tod = defaults.time_of_day_defaults
    weekend = (
        "the coming week (Sat/Sun)"
        if defaults.weekend_this_week_means_coming_week
        else "the current week (Sat/Sun)"
    )
    return (
        "**Phrase settings**\n"
        "These control how phrases like `tonight`, `after work`, and `tomorrow morning` "
        "are interpreted.\n\n"
        f"- **tonight** starts at **{defaults.tonight_start_time}**\n"
        f"- **after work / after school** threshold **{defaults.after_work_school_time}**\n"
        f"- **morning** **{tod.get('morning', '9:00')}** | "
        f"**afternoon** **{tod.get('afternoon', '14:00')}** | "
        f"**evening** **{tod.get('evening', '18:00')}** | "
        f"**night** **{tod.get('night', '21:00')}**\n"
        f"- **this week** on weekends means **{weekend}**\n\n"
        "**Change examples:**\n"
        "- `set tonight to 8pm`\n"
        "- `set after work to 6pm`\n"
        "- `set morning to 8:30am`\n"
        "- `set weekend this week to coming` or `off`"
    )


@handle_errors("merging natural-language defaults patch", default_return={})
def _merge_nl_defaults_patch(
    existing: dict[str, Any], patch: dict[str, Any]
) -> dict[str, Any]:
    """Deep-merge one NL defaults patch onto stored natural_language_defaults."""
    merged = dict(existing)
    for key, value in patch.items():
        if key == "time_of_day_defaults" and isinstance(value, dict):
            tod = dict(merged.get("time_of_day_defaults") or {})
            if not isinstance(tod, dict):
                tod = {}
            tod.update(value)
            merged["time_of_day_defaults"] = tod
        else:
            merged[key] = value
    return merged


@handle_errors("building natural-language defaults patch", default_return=None)
def _build_nl_defaults_patch(field: str, value: str) -> dict[str, Any] | None:
    """Validate one field update and return a patch dict for natural_language_defaults."""
    field_key = normalize_nl_field_key(field)
    if field_key == "weekend_this_week_means_coming_week":
        parsed_flag = parse_weekend_this_week_flag(value)
        if parsed_flag is None:
            return None
        return {field_key: parsed_flag}
    if field_key in {"tonight_start_time", "after_work_school_time"}:
        parsed_time = _parse_preference_time(value)
        if not parsed_time:
            return None
        return {field_key: parsed_time}
    if field_key in _TIME_OF_DAY_FIELDS:
        parsed_time = _parse_preference_time(value)
        if not parsed_time:
            return None
        return {"time_of_day_defaults": {field_key: parsed_time}}
    return None


@handle_errors(
    "applying natural-language defaults update",
    default_return=NaturalLanguageDefaultsUpdateResult(
        success=False, error_message="Could not update phrase settings."
    ),
)
def apply_natural_language_defaults_update(
    user_id: str,
    nl_field: str,
    nl_value: str,
    *,
    save_preferences: Callable[..., bool] = update_user_preferences,
) -> NaturalLanguageDefaultsUpdateResult:
    """Apply one natural-language defaults change and persist under preferences."""
    if not user_id or not nl_field or not nl_value:
        return NaturalLanguageDefaultsUpdateResult(
            success=False,
            error_message="Please specify what to change and the new value.",
        )

    patch = _build_nl_defaults_patch(nl_field, nl_value)
    if not patch:
        return NaturalLanguageDefaultsUpdateResult(
            success=False,
            error_message=(
                "I could not understand that setting. Try `set tonight to 8pm`, "
                "`set after work to 6pm`, `set morning to 8:30am`, or "
                "`set weekend this week to coming`."
            ),
        )

    user_data = get_user_data(user_id, "preferences")
    preferences = user_data.get("preferences", {}) if isinstance(user_data, dict) else {}
    if not isinstance(preferences, dict):
        preferences = {}

    stored_nl = _read_stored_nl_dict(preferences) or {}
    if not isinstance(stored_nl, dict):
        stored_nl = {}

    merged_nl = _merge_nl_defaults_patch(stored_nl, patch)

    if not save_preferences(user_id, {PREFERENCES_NL_KEY: merged_nl}):
        return NaturalLanguageDefaultsUpdateResult(
            success=False,
            error_message="Failed to save phrase settings. Please try again.",
        )

    field_key = normalize_nl_field_key(nl_field)
    if field_key == "weekend_this_week_means_coming_week":
        label = "weekend this week"
    elif field_key in _TIME_OF_DAY_FIELDS:
        label = field_key
    elif field_key == "tonight_start_time":
        label = "tonight"
    elif field_key == "after_work_school_time":
        label = "after work/school"
    else:
        label = field_key

    return NaturalLanguageDefaultsUpdateResult(
        success=True,
        updated_labels=(label,),
    )


@handle_errors(
    "saving natural-language defaults preferences",
    default_return=False,
)
def save_natural_language_defaults_preferences(
    user_id: str,
    payload: dict[str, Any],
    *,
    save_preferences: Callable[..., bool] = update_user_preferences,
) -> bool:
    """Persist a full natural_language_defaults object under preferences."""
    if not user_id or not isinstance(payload, dict):
        return False

    merged = merge_natural_language_preferences(payload)
    prefs_dict = natural_language_defaults_to_preferences_dict(merged)

    user_data = get_user_data(user_id, "preferences")
    preferences = user_data.get("preferences", {}) if isinstance(user_data, dict) else {}
    if not isinstance(preferences, dict):
        preferences = {}

    return bool(save_preferences(user_id, {PREFERENCES_NL_KEY: prefs_dict}))


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
