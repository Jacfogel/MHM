"""Message domain schemas for templates and sent deliveries."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.time_utilities import parse_timestamp_full
from storage.user_data_v2_base import (
    SCHEMA_VERSION,
    SourceModel,
    v2_schema_validation_error,
)

DeliveryStatus = Literal["sent", "failed", "skipped"]


class ScheduleModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    days: list[str] = Field(default_factory=lambda: ["ALL"])
    periods: list[str] = Field(default_factory=lambda: ["ALL"])


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
    metadata: dict = Field(default_factory=dict)

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
    metadata: dict = Field(default_factory=dict)

    @field_validator("sent_at")
    @classmethod
    def validate_sent_at(cls, value: str) -> str:
        if parse_timestamp_full(value) is None:
            raise v2_schema_validation_error("sent_at must use canonical full timestamp format")
        return value


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


def validate_messages_v2_document(data: dict) -> tuple[dict, list[str]]:
    """Validate a v2 message-template envelope."""
    try:
        model = MessageTemplateCollectionV2Model.model_validate(data)
        return model.model_dump(mode="json"), []
    except Exception as exc:
        return data, [str(exc)]


def validate_deliveries_v2_document(data: dict) -> tuple[dict, list[str]]:
    """Validate a v2 message-delivery envelope."""
    try:
        model = MessageDeliveryCollectionV2Model.model_validate(data)
        return model.model_dump(mode="json"), []
    except Exception as exc:
        return data, [str(exc)]
