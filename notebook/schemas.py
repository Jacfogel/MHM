"""
Pydantic models for notebook entries.

Defines Entry and ListItem models with validation, following MHM patterns.
"""

from __future__ import annotations
from typing import Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from core.tags import normalize_tags, validate_tag
from core.logger import get_component_logger
from core.time_utilities import now_timestamp_full

logger = get_component_logger("notebook_schemas")


EntryKind = Literal["note", "list", "journal"]


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
    kind: EntryKind
    title: str | None = None
    body: str | None = None
    items: list[ListItem] | None = None
    tags: list[str] = Field(default_factory=list)
    group: str | None = None
    pinned: bool = False
    archived: bool = False
    created_at: str = Field(default_factory=now_timestamp_full)
    updated_at: str = Field(default_factory=now_timestamp_full)

    @field_validator("title", "body", "group", mode="before")
    @classmethod
    def strip_optional_strings(cls, v: str | None) -> str | None:
        if v is not None:
            stripped_v = v.strip()
            return stripped_v if stripped_v else None
        return v

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

    @field_validator("body", mode="after")
    @classmethod
    def validate_body_for_list(cls, v: str | None, info) -> str | None:
        """For lists, body is optional and can be empty."""
        if info.data.get("kind") == "list" and v is not None:
            stripped_v = v.strip()
            return stripped_v if stripped_v else None
        return v

    @model_validator(mode="after")
    def validate_kind_specific_fields(self) -> "Entry":
        """Validate that kind-specific fields are correct."""
        if self.kind != "list" and self.items is not None:
            raise ValueError(f"Entry kind '{self.kind}' cannot have 'items'.")
        if self.kind == "list" and (self.items is None or len(self.items) == 0):
            raise ValueError("Entry kind 'list' must have 'items'.")
        return self
