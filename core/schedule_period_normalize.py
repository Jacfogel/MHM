"""
Schedule period field normalization used by envelopes and document defaults.

Kept as a leaf module so ``profile_v2_io`` can migrate period maps without
importing ``schedule_document_defaults`` (which loads user data).
"""

from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("main")

_PERIOD_V2_KEYS = frozenset({"active", "days", "start_time", "end_time"})


@handle_errors("creating default schedule periods", default_return={})
def create_default_schedule_periods(category: str | None = None) -> dict[str, Any]:
    """Create default schedule periods for a new category."""
    if category:
        if category in ("tasks", "checkin"):
            if category == "tasks":
                default_period_name = "Task Reminder Default"
            else:
                default_period_name = "Check-in Reminder Default"
        else:
            category_display = category.replace("_", " ").title()
            default_period_name = f"{category_display} Message Default"
    else:
        default_period_name = "Default"

    return {
        "ALL": {
            "active": True,
            "days": ["ALL"],
            "start_time": "00:00",
            "end_time": "23:59",
        },
        default_period_name: {
            "active": True,
            "days": ["ALL"],
            "start_time": "18:00",
            "end_time": "20:00",
        },
    }


@handle_errors("normalizing schedule period fields", default_return={})
def _normalize_period_fields(period_data: dict[str, Any]) -> dict[str, Any]:
    """Rename start/end keys to start_time/end_time and drop extra period fields."""
    if not isinstance(period_data, dict):
        return {}
    normalized = dict(period_data)
    if "start_time" not in normalized and "start" in normalized:
        normalized["start_time"] = normalized["start"]
    if "end_time" not in normalized and "end" in normalized:
        normalized["end_time"] = normalized["end"]
    return {key: value for key, value in normalized.items() if key in _PERIOD_V2_KEYS}


# devtools: ignore[facade-shims]: current period-map migration, not a compatibility bridge
@handle_errors("migrating legacy schedules structure", default_return={})
def migrate_legacy_schedules_structure(
    schedules_data: dict[str, Any],
) -> dict[str, Any]:
    """Normalize category maps to ``{category: {periods: ...}}`` with v2 period fields."""
    migrated_data = {}
    for category, category_data in schedules_data.items():
        if isinstance(category_data, dict):
            if "periods" in category_data:
                raw_periods = category_data.get("periods")
                periods = raw_periods if isinstance(raw_periods, dict) else {}
                migrated_data[category] = {
                    "periods": {
                        name: _normalize_period_fields(period)
                        for name, period in periods.items()
                        if isinstance(period, dict)
                    }
                }
            else:
                unwrapped_periods = {}
                for period_name, period_data in category_data.items():
                    if isinstance(period_data, dict) and (
                        "start_time" in period_data or "start" in period_data
                    ):
                        unwrapped_periods[period_name] = _normalize_period_fields(
                            period_data
                        )
                if not unwrapped_periods:
                    unwrapped_periods = create_default_schedule_periods(category)
                for _period_name, period_data in unwrapped_periods.items():
                    if "days" not in period_data:
                        period_data["days"] = ["ALL"]
                migrated_data[category] = {"periods": unwrapped_periods}
        else:
            migrated_data[category] = {
                "periods": create_default_schedule_periods(category)
            }
    return migrated_data
