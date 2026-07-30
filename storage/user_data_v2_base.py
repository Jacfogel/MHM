"""
Dependency leaf for v2 user-data item shapes shared across core and domain packages.

Must not import ``tasks`` or ``notebook`` to avoid circular imports with
``user_data_v2_envelopes`` orchestration and domain schema modules.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError

from core.error_handling import handle_errors
from core.ids import generate_short_id
from core.time_utilities import parse_timestamp_full

SCHEMA_VERSION = 2

ItemKind = Literal["task", "note", "list", "journal_entry"]

# Explicit public surface so generate_short_id remains a documented re-export from core.ids.
__all__ = [
    "SCHEMA_VERSION",
    "ItemKind",
    "SourceModel",
    "BaseItemModel",
    "validate_optional_v2_timestamp",
    "v2_schema_validation_error",
    "generate_short_id",
]


class SourceModel(BaseModel):
    """Best-known origin of a persisted record."""

    model_config = ConfigDict(extra="forbid")

    system: str = "mhm"
    channel: str = ""
    actor: str = ""
    migration: str | None = None


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
            raise v2_schema_validation_error("timestamp must use canonical full timestamp format")
        return value

    @field_validator("archived_at", "deleted_at")
    @classmethod
    def validate_optional_timestamp_fields(cls, value: str | None) -> str | None:
        validate_optional_v2_timestamp(value, "optional timestamp")
        return value

    @field_validator("tags", "linked_item_ids", mode="before")
    @classmethod
    def normalize_string_list(cls, value: Any) -> list[str]:
        """Coerce tags or linked_item_ids to a list of stripped, non-empty strings."""
        if value is None:
            return []
        if not isinstance(value, list):
            raise v2_schema_validation_error("value must be a list")
        return [str(item).strip() for item in value if str(item).strip()]


@handle_errors("validating optional v2 timestamp field", re_raise=True)
def validate_optional_v2_timestamp(value: str | None, field_name: str) -> None:
    if value and parse_timestamp_full(value) is None:
        raise v2_schema_validation_error(
            f"{field_name} must use canonical full timestamp format"
        )


@handle_errors("building v2 schema validation error", re_raise=True)
def v2_schema_validation_error(message: str) -> PydanticCustomError:
    """Build a Pydantic-native validation error without generic exception raises."""
    return PydanticCustomError("user_data_v2_validation", "{message}", {"message": message})
