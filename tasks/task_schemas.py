"""
Task domain types, constants, v2 persistence schemas, and exception.

Used by task_validation and task_data_manager. No business logic.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from core.logger import get_component_logger
from core.time_utilities import parse_date_only, parse_time_only_minute
from storage.user_data_v2_base import (
    SCHEMA_VERSION,
    BaseItemModel,
    v2_schema_validation_error,
    validate_optional_v2_timestamp,
)


# Domain exception for task operations
class TaskManagementError(Exception):
    """Custom exception for task management errors."""

    pass


# Valid priority values for tasks
VALID_PRIORITIES: tuple[str, ...] = ("low", "medium", "high", "urgent", "critical")

# Fields that may be updated via update_task
ALLOWED_UPDATE_FIELDS: tuple[str, ...] = (
    "title",
    "description",
    "category",
    "group",
    "status",
    "due_date",
    "due_time",
    "due",
    "reminder_periods",
    "reminders",
    "priority",
    "tags",
    "quick_reminders",
    "recurrence_pattern",
    "recurrence_interval",
    "repeat_after_completion",
    "next_due_date",
    "recurrence",
)

TASKS_V2_FILENAME = "tasks.json"

logger = get_component_logger("tasks")

TaskStatus = Literal["active", "completed", "cancelled", "archived", "deleted"]


class DueModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str | None = None
    time: str | None = None

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str | None) -> str | None:
        if value and parse_date_only(value) is None:
            raise v2_schema_validation_error("due.date must use YYYY-MM-DD")
        return value

    @field_validator("time")
    @classmethod
    def validate_time(cls, value: str | None) -> str | None:
        if value and parse_time_only_minute(value) is None:
            raise v2_schema_validation_error("due.time must use HH:MM")
        return value


class CompletionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    completed: bool = False
    completed_at: str | None = None
    notes: str = ""

    @field_validator("completed_at")
    @classmethod
    def validate_completed_at(cls, value: str | None) -> str | None:
        validate_optional_v2_timestamp(value, "completion.completed_at")
        return value


class RecurrenceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern: str | None = None
    interval: int = 1
    repeat_after_completion: bool = True
    next_due_date: str | None = None

    @field_validator("next_due_date")
    @classmethod
    def validate_next_due_date(cls, value: str | None) -> str | None:
        if value and parse_date_only(value) is None:
            raise v2_schema_validation_error("recurrence.next_due_date must use YYYY-MM-DD")
        return value


class TaskV2Model(BaseItemModel):
    kind: Literal["task"] = "task"
    status: TaskStatus = "active"
    priority: Literal["low", "medium", "high", "urgent", "critical"] = "medium"
    due: DueModel = Field(default_factory=DueModel)
    reminders: list[dict[str, Any]] = Field(default_factory=list)
    recurrence: RecurrenceModel = Field(default_factory=RecurrenceModel)
    completion: CompletionModel = Field(default_factory=CompletionModel)

    @field_validator("tags", mode="before")
    @classmethod
    def sanitize_tags(cls, value: Any) -> list[str]:
        """Normalize and validate task tags before model construction."""
        from tasks.task_tag_helpers import sanitize_task_tags

        if value is None:
            return []
        if not isinstance(value, list):
            return sanitize_task_tags([str(value)] if value else [])
        return sanitize_task_tags(value)

    # devtools: ignore[unused-functions]: pydantic model_validator invoked at model construction
    @model_validator(mode="after")
    def validate_completion_status(self) -> TaskV2Model:
        if self.status == "completed" and not self.completion.completed:
            raise v2_schema_validation_error("completed tasks must set completion.completed")
        return self


class TaskCollectionV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    tasks: list[TaskV2Model] = Field(default_factory=list)
