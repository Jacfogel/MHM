"""
Pydantic models for notebook entries.

Defines Entry and ListItem models with validation, following MHM patterns.
"""

from __future__ import annotations
from typing import Any, Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from core.tags import normalize_tags, validate_tag
from core.logger import get_component_logger
from core.time_utilities import now_timestamp_full
from storage.user_data_v2_base import (
    SCHEMA_VERSION,
    BaseItemModel,
    validate_optional_v2_timestamp,
    v2_schema_validation_error,
)

logger = get_component_logger("notebook_schemas")


# Aligns with the notebook subset of ``ItemKind`` in ``storage.user_data_v2_base``.
EntryKind = Literal["note", "list", "journal_entry"]

NotebookStatus = Literal["active", "archived", "deleted"]


class ListItem(BaseModel):
    """A single item in a list entry."""

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    text: str
    done: bool = False
    order: int
    created_at: str = Field(default_factory=now_timestamp_full)
    updated_at: str = Field(default_factory=now_timestamp_full)

    @field_validator("text", mode="before")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("List item text cannot be empty.")
        return v.strip()


class Entry(BaseModel):
    """A notebook entry (note, list, or journal)."""

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    short_id: str | None = None
    kind: EntryKind
    title: str | None = None
    description: str | None = None
    category: str = ""
    status: Literal["active", "archived", "deleted"] = "active"
    items: list[ListItem] | None = None
    tags: list[str] = Field(default_factory=list)
    group: str | None = None
    pinned: bool = False
    submitted_at: str | None = None
    source: dict | None = None
    linked_item_ids: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_timestamp_full)
    updated_at: str = Field(default_factory=now_timestamp_full)
    archived_at: str | None = None
    deleted_at: str | None = None
    metadata: dict = Field(default_factory=dict)

    @field_validator("title", "description", "group", mode="before")
    @classmethod
    def strip_optional_strings(cls, v: str | None) -> str | None:
        if v is not None:
            stripped_v = v.strip()
            return stripped_v if stripped_v else None
        return v

    @field_validator("category", mode="before")
    @classmethod
    def strip_category(cls, v: str | None) -> str:
        if v is None:
            return ""
        return v.strip()

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_and_validate_tags(cls, v: list[str]) -> list[str]:
        """Normalize and validate tags."""
        normalized = normalize_tags(v)
        for tag in normalized:
            try:
                validate_tag(tag)
            except ValueError as e:
                logger.warning(f"Invalid tag '{tag}' removed during validation: {e}")
        return normalized

    @field_validator("items", mode="after")
    @classmethod
    def validate_list_items(
        cls, v: list[ListItem] | None, info
    ) -> list[ListItem] | None:
        """Validate list items and ensure order consistency."""
        if info.data.get("kind") == "list":
            if not v or len(v) == 0:
                raise ValueError("List entries must have at least one item.")
            # Ensure order is consistent with list index
            for i, item in enumerate(v):
                if item.order != i:
                    item.order = i  # Auto-correct order
                    item.updated_at = now_timestamp_full()
        elif v is not None:
            raise ValueError("Only 'list' kind entries can have 'items'.")
        return v

    @field_validator("description", mode="after")
    @classmethod
    def validate_description_for_list(cls, v: str | None, info) -> str | None:
        """For lists, description is optional and can be empty."""
        if info.data.get("kind") == "list" and v is not None:
            stripped_v = v.strip()
            return stripped_v if stripped_v else None
        return v

    @model_validator(mode="after")
    def validate_kind_specific_fields(self) -> Entry:
        """Validate that kind-specific fields are correct."""
        if self.kind != "list" and self.items is not None:
            raise ValueError(f"Entry kind '{self.kind}' cannot have 'items'.")
        if self.kind == "list" and (self.items is None or len(self.items) == 0):
            raise ValueError("Entry kind 'list' must have 'items'.")
        return self


class NotebookV2Model(BaseItemModel):
    """v2 JSON shape for notebook/entries.json (string ids, list items as dicts)."""

    kind: Literal["note", "list", "journal_entry"]
    status: NotebookStatus = "active"
    pinned: bool = False
    submitted_at: str | None = None
    items: list[dict[str, Any]] | None = None

    @field_validator("submitted_at")
    @classmethod
    def validate_submitted_at(cls, value: str | None) -> str | None:
        validate_optional_v2_timestamp(value, "submitted_at")
        return value

    @model_validator(mode="after")
    def validate_kind_details(self) -> NotebookV2Model:
        if self.kind == "journal_entry" and not self.submitted_at:
            raise v2_schema_validation_error("journal_entry records require submitted_at")
        if self.kind == "list" and not self.items:
            raise v2_schema_validation_error("list records require items")
        if self.kind != "list" and self.items is not None:
            raise v2_schema_validation_error("only list records may include items")
        return self


class NotebookCollectionV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    entries: list[NotebookV2Model] = Field(default_factory=list)
