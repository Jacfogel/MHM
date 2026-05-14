"""
Canonical v2 on-disk **envelope** models (check-ins, message templates, deliveries) and
``validate_v2_document`` orchestration.

Task and notebook persistence models live in ``tasks.task_schemas`` and
``notebook.notebook_schemas``; shared item primitives are in ``user_data_v2_base``.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.time_utilities import parse_timestamp_full
from storage.user_data_v2_base import (
    SCHEMA_VERSION,
    ItemKind,
    SourceModel,
    generate_short_id,
    v2_schema_validation_error,
)
from notebook.notebook_schemas import NotebookCollectionV2Model, NotebookV2Model
from notebook.notebook_validation import validate_notebook_v2_document
from tasks.task_schemas import (
    TaskCollectionV2Model,
    TaskV2Model,
)
from tasks.task_validation import validate_tasks_v2_document

# Re-exports so ``from storage.user_data_v2_envelopes import â€¦`` stays stable; task/notebook models live in domain packages.
__all__ = [
    "SCHEMA_VERSION",
    "ItemKind",
    "SourceModel",
    "ScheduleModel",
    "CheckinV2Model",
    "MessageTemplateV2Model",
    "MessageDeliveryV2Model",
    "CheckinCollectionV2Model",
    "MessageTemplateCollectionV2Model",
    "MessageDeliveryCollectionV2Model",
    "TaskV2Model",
    "TaskCollectionV2Model",
    "NotebookV2Model",
    "NotebookCollectionV2Model",
    "generate_short_id",
    "validate_v2_document",
]

DeliveryStatus = Literal["sent", "failed", "skipped"]


class ScheduleModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    days: list[str] = Field(default_factory=lambda: ["ALL"])
    periods: list[str] = Field(default_factory=lambda: ["ALL"])


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
            raise v2_schema_validation_error("timestamp must use canonical full timestamp format")
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
            raise v2_schema_validation_error("timestamp must use canonical full timestamp format")
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
            raise v2_schema_validation_error("sent_at must use canonical full timestamp format")
        return value


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


# error_handling_exclude: This validation API returns Pydantic errors as data.
def validate_v2_document(document_type: str, data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validate a v2 document and return normalized data plus validation errors."""
    if document_type == "tasks":
        return validate_tasks_v2_document(data)
    if document_type == "notebook":
        return validate_notebook_v2_document(data)

    model_by_type: dict[str, type[BaseModel]] = {
        "checkins": CheckinCollectionV2Model,
        "messages": MessageTemplateCollectionV2Model,
        "deliveries": MessageDeliveryCollectionV2Model,
    }
    model_cls = model_by_type.get(document_type)
    if model_cls is None:
        return data, [f"Unknown v2 document type: {document_type}"]
    try:
        model = model_cls.model_validate(data)
        return model.model_dump(mode="json"), []
    except Exception as exc:
        return data, [str(exc)]
