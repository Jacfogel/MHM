"""
Schedule defaults and migration: create_default_schedule_periods,
migrate_legacy_schedules_structure, ensure_category_has_default_schedule,
ensure_all_categories_have_schedules.
"""

from typing import Any

from core.logger import get_component_logger
from core.error_handling import handle_errors

from core.user_data_registry import (
    _get_user_data__load_schedules,
    _save_user_data__save_schedules,
)
from core.user_data_read import get_user_data

logger = get_component_logger("main")


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


@handle_errors("migrating legacy schedules structure", default_return={})
def migrate_legacy_schedules_structure(
    schedules_data: dict[str, Any],
) -> dict[str, Any]:
    """Migrate legacy schedules structure to new format."""
    migrated_data = {}
    for category, category_data in schedules_data.items():
        if isinstance(category_data, dict):
            if "periods" in category_data:
                migrated_data[category] = category_data
            else:
                legacy_periods = {}
                for period_name, period_data in category_data.items():
                    if isinstance(period_data, dict) and (
                        "start_time" in period_data or "start" in period_data
                    ):
                        legacy_periods[period_name] = period_data
                if not legacy_periods:
                    legacy_periods = create_default_schedule_periods(category)
                for _period_name, period_data in legacy_periods.items():
                    if "days" not in period_data:
                        period_data["days"] = ["ALL"]
                migrated_data[category] = {"periods": legacy_periods}
        else:
            migrated_data[category] = {
                "periods": create_default_schedule_periods(category)
            }
    return migrated_data


@handle_errors("ensuring category has default schedule", default_return=False)
def ensure_category_has_default_schedule(user_id: str, category: str) -> bool:
    """Ensure a category has default schedule periods if it doesn't exist."""
    if not user_id or not category:
        logger.warning(f"Invalid user_id or category: {user_id}, {category}")
        return False
    try:
        schedules_data = _get_user_data__load_schedules(user_id) or {}
        logger.debug(f"Current schedules data for user {user_id}: {schedules_data}")

        if schedules_data and any(
            isinstance(v, dict) and "periods" not in v for v in schedules_data.values()
        ):
            logger.info(f"Migrating legacy schedules structure for user {user_id}")
            schedules_data = migrate_legacy_schedules_structure(schedules_data)
            _save_user_data__save_schedules(user_id, schedules_data)

        category_exists = category in schedules_data
        has_periods = (
            schedules_data.get(category, {}).get("periods")
            if category_exists
            else False
        )
        logger.debug(
            f"Category '{category}' exists: {category_exists}, has periods: {has_periods}"
        )

        if not category_exists or not has_periods:
            default_periods = create_default_schedule_periods(category)
            logger.debug(
                f"Creating default periods for category '{category}': {default_periods}"
            )
            if not category_exists:
                schedules_data[category] = {"periods": default_periods}
            else:
                schedules_data[category]["periods"] = default_periods
            _save_user_data__save_schedules(user_id, schedules_data)
            logger.info(
                f"Created default schedule periods for category '{category}' for user {user_id}"
            )
            return True
        logger.debug(
            f"Category '{category}' already has periods, skipping default creation"
        )
        return True
    except Exception as e:
        logger.error(
            f"Error ensuring default schedule for category '{category}' for user {user_id}: {e}"
        )
        return False


@handle_errors("ensuring all categories have schedules", default_return=False)
def ensure_all_categories_have_schedules(
    user_id: str, suppress_logging: bool = False
) -> bool:
    """Ensure all categories in user preferences have corresponding schedules."""
    if not user_id:
        logger.warning(f"Invalid user_id: {user_id}")
        return False
    try:
        user_data = get_user_data(user_id, "preferences")
        if not user_data or "preferences" not in user_data:
            logger.warning(f"User preferences not found for user_id: {user_id}")
            return False
        preferences_data = user_data["preferences"]
        categories = preferences_data.get("categories", [])
        if not categories:
            logger.debug(f"No categories found for user {user_id}")
            return True
        created_schedules = []
        for category in categories:
            if ensure_category_has_default_schedule(user_id, category):
                created_schedules.append(category)
        if created_schedules and not suppress_logging:
            logger.info(f"Created schedules for user {user_id}: {created_schedules}")
        elif not suppress_logging:
            logger.debug(f"Verified schedules exist for user {user_id}: {categories}")
        return True
    except Exception as e:
        logger.error(
            f"Error ensuring all categories have schedules for user {user_id}: {e}"
        )
        return False
