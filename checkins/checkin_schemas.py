"""Check-in domain schemas for stored check-in records."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.time_utilities import parse_timestamp_full
from storage.user_data_v2_base import (
    SCHEMA_VERSION,
    SourceModel,
    v2_schema_validation_error,
)


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


class CheckinCollectionV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    checkins: list[CheckinV2Model] = Field(default_factory=list)


# error_handling_exclude: This validation API returns Pydantic errors as data.
def validate_checkins_v2_document(data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validate a v2 check-in envelope."""
    try:
        model = CheckinCollectionV2Model.model_validate(data)
        return model.model_dump(mode="json"), []
    except Exception as exc:
        return data, [str(exc)]
