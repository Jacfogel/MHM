"""
Canonical v2 user-data schemas and validation helpers.
"""

from __future__ import annotations

from typing import Any, Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.time_utilities import parse_date_only, parse_time_only_minute, parse_timestamp_full

logger = get_component_logger(__name__)

SCHEMA_VERSION = 2

ItemKind = Literal["task", "note", "list", "journal_entry"]
TaskStatus = Literal["active", "completed", "cancelled", "archived", "deleted"]
NotebookStatus = Literal["active", "archived", "deleted"]
MessageTemplateStatus = Literal["active", "archived", "deleted"]
DeliveryStatus = Literal["sent", "failed", "skipped"]

OLD_FIELD_NAMES_BY_DOCUMENT: dict[str, set[str]] = {
    "task": {
        "task_id",
        "completed",
        "completed_at",
        "completion_notes",
        "due_date",
        "due_time",
        "reminder_periods",
        "quick_reminders",
        "recurrence_pattern",
        "recurrence_interval",
        "repeat_after_completion",
        "next_due_date",
        "last_updated",
    },
    "notebook": {"body", "archived"},
    "checkin": {"timestamp"},
    "message": {"message_id", "message", "days", "time_periods", "timestamp"},
    "delivery": {"message_id", "message", "delivery_status", "timestamp"},
}

class SourceModel(BaseModel):
    """Best-known origin of a migrated or newly written record."""

    model_config = ConfigDict(extra="forbid")

    system: str = "mhm"
    channel: str = ""
    actor: str = ""
    migration: str | None = None


class DueModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str | None = None
    time: str | None = None

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str | None) -> str | None:
        if value and parse_date_only(value) is None:
            raise _schema_validation_error("due.date must use YYYY-MM-DD")
        return value

    @field_validator("time")
    @classmethod
    def validate_time(cls, value: str | None) -> str | None:
        if value and parse_time_only_minute(value) is None:
            raise _schema_validation_error("due.time must use HH:MM")
        return value


class ScheduleModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    days: list[str] = Field(default_factory=lambda: ["ALL"])
    periods: list[str] = Field(default_factory=lambda: ["ALL"])


class CompletionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    completed: bool = False
    completed_at: str | None = None
    notes: str = ""

    @field_validator("completed_at")
    @classmethod
    def validate_completed_at(cls, value: str | None) -> str | None:
        _validate_optional_timestamp(value, "completion.completed_at")
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
            raise _schema_validation_error("recurrence.next_due_date must use YYYY-MM-DD")
        return value


class BaseItemModel(BaseModel):
    """Shared item fields for v2 task, notebook, list, and journal records."""

    model_config = ConfigDict(extra="forbid")

    id: str
    short_id: str
    kind: ItemKind
    title: str = ""
    description: str = ""
    category: str = ""
    group: str = ""
    tags: list[str] = Field(default_factory=list)
    status: str = "active"
    source: SourceModel = Field(default_factory=SourceModel)
    linked_item_ids: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    archived_at: str | None = None
    deleted_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("created_at", "updated_at")
    @classmethod
    def validate_required_timestamp(cls, value: str) -> str:
        if parse_timestamp_full(value) is None:
            raise _schema_validation_error("timestamp must use canonical full timestamp format")
        return value

    @field_validator("archived_at", "deleted_at")
    @classmethod
    def validate_optional_timestamp(cls, value: str | None) -> str | None:
        _validate_optional_timestamp(value, "optional timestamp")
        return value

    @field_validator("tags", "linked_item_ids", mode="before")
    @classmethod
    def normalize_string_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise _schema_validation_error("value must be a list")
        return [str(item).strip() for item in value if str(item).strip()]


class TaskV2Model(BaseItemModel):
    kind: Literal["task"] = "task"
    status: TaskStatus = "active"
    priority: Literal["low", "medium", "high", "urgent", "critical"] = "medium"
    due: DueModel = Field(default_factory=DueModel)
    reminders: list[dict[str, Any]] = Field(default_factory=list)
    recurrence: RecurrenceModel = Field(default_factory=RecurrenceModel)
    completion: CompletionModel = Field(default_factory=CompletionModel)

    @model_validator(mode="after")
    def validate_completion_status(self) -> TaskV2Model:
        if self.status == "completed" and not self.completion.completed:
            raise _schema_validation_error("completed tasks must set completion.completed")
        return self


class NotebookV2Model(BaseItemModel):
    kind: Literal["note", "list", "journal_entry"]
    status: NotebookStatus = "active"
    pinned: bool = False
    submitted_at: str | None = None
    items: list[dict[str, Any]] | None = None

    @field_validator("submitted_at")
    @classmethod
    def validate_submitted_at(cls, value: str | None) -> str | None:
        _validate_optional_timestamp(value, "submitted_at")
        return value

    @model_validator(mode="after")
    def validate_kind_details(self) -> NotebookV2Model:
        if self.kind == "journal_entry" and not self.submitted_at:
            raise _schema_validation_error("journal_entry records require submitted_at")
        if self.kind == "list" and not self.items:
            raise _schema_validation_error("list records require items")
        if self.kind != "list" and self.items is not None:
            raise _schema_validation_error("only list records may include items")
        return self


class CheckinV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    submitted_at: str
    source: SourceModel = Field(default_factory=SourceModel)
    responses: dict[str, Any] = Field(default_factory=dict)
    questions_asked: list[str] = Field(default_factory=list)
    linked_item_ids: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    archived_at: str | None = None
    deleted_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("submitted_at", "created_at", "updated_at")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        if parse_timestamp_full(value) is None:
            raise _schema_validation_error("timestamp must use canonical full timestamp format")
        return value


class MessageTemplateV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: Literal["message"] = "message"
    text: str
    category: str
    active: bool = True
    schedule: ScheduleModel = Field(default_factory=ScheduleModel)
    created_at: str
    updated_at: str
    archived_at: str | None = None
    deleted_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("created_at", "updated_at")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        if parse_timestamp_full(value) is None:
            raise _schema_validation_error("timestamp must use canonical full timestamp format")
        return value


class MessageDeliveryV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    message_template_id: str
    sent_text: str
    category: str
    channel: str = ""
    status: DeliveryStatus = "sent"
    source: SourceModel = Field(default_factory=SourceModel)
    sent_at: str
    time_period: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("sent_at")
    @classmethod
    def validate_sent_at(cls, value: str) -> str:
        if parse_timestamp_full(value) is None:
            raise _schema_validation_error("sent_at must use canonical full timestamp format")
        return value


class TaskCollectionV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    tasks: list[TaskV2Model] = Field(default_factory=list)


class NotebookCollectionV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    entries: list[NotebookV2Model] = Field(default_factory=list)


class CheckinCollectionV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    checkins: list[CheckinV2Model] = Field(default_factory=list)


class MessageTemplateCollectionV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    category: str
    updated_at: str
    messages: list[MessageTemplateV2Model] = Field(default_factory=list)


class MessageDeliveryCollectionV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    deliveries: list[MessageDeliveryV2Model] = Field(default_factory=list)


@handle_errors("generating v2 short id", re_raise=True)
def generate_short_id(record_id: str, kind: str, length: int = 6) -> str:
    """Generate a mobile-friendly no-dash short ID from a UUID-like value."""
    prefix_map = {
        "task": "t",
        "note": "n",
        "list": "l",
        "journal": "j",
        "journal_entry": "j",
        "message": "m",
        "delivery": "d",
        "checkin": "c",
    }
    prefix = prefix_map.get(kind, kind[:1].lower())
    uuid_value = _stable_uuid(record_id)
    fragment = str(uuid_value).replace("-", "")[:length]
    return f"{prefix}{fragment}"


# error_handling_exclude: This validation API returns Pydantic errors as data.
def validate_v2_document(document_type: str, data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validate a v2 document and return normalized data plus validation errors."""
    model_by_type = {
        "tasks": TaskCollectionV2Model,
        "notebook": NotebookCollectionV2Model,
        "checkins": CheckinCollectionV2Model,
        "messages": MessageTemplateCollectionV2Model,
        "deliveries": MessageDeliveryCollectionV2Model,
    }
    model_cls = model_by_type.get(document_type)
    if model_cls is None:
        return data, [f"Unknown v2 document type: {document_type}"]
    obsolete = _find_obsolete_fields(data, document_type)
    if obsolete:
        return data, [f"Obsolete v1 fields are not allowed in v2 {document_type}: {sorted(obsolete)}"]
    try:
        model = model_cls.model_validate(data)
        return model.model_dump(mode="json"), []
    except Exception as exc:
        return data, [str(exc)]


@handle_errors("finding obsolete v1 fields", re_raise=True)
def _find_obsolete_fields(data: Any, document_type: str) -> set[str]:
    """Find obsolete fields on v2 record objects without scanning nested v2 shapes."""
    obsolete_by_type = {
        "tasks": OLD_FIELD_NAMES_BY_DOCUMENT["task"],
        "notebook": OLD_FIELD_NAMES_BY_DOCUMENT["notebook"],
        "checkins": OLD_FIELD_NAMES_BY_DOCUMENT["checkin"],
        "messages": OLD_FIELD_NAMES_BY_DOCUMENT["message"],
        "deliveries": OLD_FIELD_NAMES_BY_DOCUMENT["delivery"],
    }
    obsolete = obsolete_by_type.get(document_type, set())
    found: set[str] = set()
    collection_key_by_type = {
        "tasks": "tasks",
        "notebook": "entries",
        "checkins": "checkins",
        "messages": "messages",
        "deliveries": "deliveries",
    }
    collection_key = collection_key_by_type.get(document_type)

    if isinstance(data, dict):
        found.update(obsolete.intersection(data.keys()))
        records = data.get(collection_key, []) if collection_key else []
    elif isinstance(data, list):
        records = data
    else:
        records = []

    for record in records:
        if isinstance(record, dict):
            found.update(obsolete.intersection(record.keys()))
    return found


@handle_errors("validating optional migration timestamp", re_raise=True)
def _validate_optional_timestamp(value: str | None, field_name: str) -> None:
    if value and parse_timestamp_full(value) is None:
        raise _schema_validation_error(f"{field_name} must use canonical full timestamp format")


@handle_errors("coercing stable migration uuid", re_raise=True)
def _stable_uuid(value: str) -> UUID:
    """Return value as a UUID, deriving a stable UUID for old non-UUID IDs."""
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return uuid5(NAMESPACE_URL, str(value))


@handle_errors("building v2 schema validation error", re_raise=True)
def _schema_validation_error(message: str) -> PydanticCustomError:
    """Build a Pydantic-native validation error without generic exception raises."""
    return PydanticCustomError("user_data_v2_validation", "{message}", {"message": message})


