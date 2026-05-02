"""
Validation helpers for task data and inputs.

Used by task_data_manager (and optionally task_data_handlers).
Uses core.user_data_validation.is_valid_user_id and core.time_utilities.
"""

from typing import Any

from core.logger import get_component_logger
from tasks.task_schemas import TaskCollectionV2Model
from core.error_handling import handle_errors
from core.time_utilities import parse_date_only

from tasks.task_schemas import VALID_PRIORITIES, ALLOWED_UPDATE_FIELDS

logger = get_component_logger("tasks")


@handle_errors("validating task title", default_return=False)
def is_valid_task_title(title: Any) -> bool:
    """Return True if title is a non-empty string after strip."""
    if title is None:
        return False
    if not isinstance(title, str):
        return False
    return bool(title.strip())


@handle_errors("validating task priority", default_return=False)
def is_valid_priority(priority: Any) -> bool:
    """Return True if priority is one of VALID_PRIORITIES (case-insensitive)."""
    if priority is None or not isinstance(priority, str):
        return False
    return priority.lower().strip() in VALID_PRIORITIES


@handle_errors("validating due date", default_return=False)
def is_valid_due_date(value: Any) -> bool:
    """Return True if value is None or a parseable date-only string (YYYY-MM-DD)."""
    if value is None:
        return True
    if not isinstance(value, str) or not value.strip():
        return True
    return parse_date_only(value.strip()) is not None


@handle_errors("validating update field", default_return=(False, "Validation error"))
def validate_update_field(field: str, value: Any) -> tuple[bool, str | None]:
    """
    Validate a single update field/value for update_task.

    Returns:
        (True, None) if valid; (False, reason) if invalid.
    """
    if field not in ALLOWED_UPDATE_FIELDS:
        return False, f"Disallowed field: {field}"
    if field == "priority" and value is not None and not is_valid_priority(value):
        return False, f"Invalid priority: {value}"
    if field == "due_date" and value is not None and not is_valid_due_date(value):
        return False, f"Invalid due_date format: {value}"
    if field == "title":
        if value is None:
            return False, "Title cannot be None"
        if not is_valid_task_title(value):
            return False, "Title cannot be empty"
    return True, None


# error_handling_exclude: This validation API returns Pydantic errors as data.
def validate_tasks_v2_document(data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validate a v2 tasks file envelope and return normalized data plus validation errors."""
    try:
        model = TaskCollectionV2Model.model_validate(data)
        return model.model_dump(mode="json"), []
    except Exception as exc:
        return data, [str(exc)]
