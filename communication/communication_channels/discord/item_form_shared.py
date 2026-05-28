"""
Shared field parsing for Discord task/note creation modals.

Keeps task and note forms aligned on title, body, group, and tags.
"""

from __future__ import annotations

from typing import Any

from core.error_handling import handle_errors
from core.tags import parse_tags_from_text


@handle_errors("parsing modal tags", default_return=[])
def parse_modal_tags(tags_value: str | None) -> list[str]:
    """Parse comma- or space-separated tags from a modal text field."""
    if not tags_value or not str(tags_value).strip():
        return []
    raw = str(tags_value).strip()
    if "," in raw:
        parts = [part.strip() for part in raw.split(",")]
    else:
        parts = [part.strip() for part in raw.split()]
    return [tag.lstrip("#") for tag in parts if tag]


@handle_errors("building entities from shared modal fields", default_return={})
def entities_from_shared_fields(
    *,
    title: str | None = None,
    description: str | None = None,
    group: str | None = None,
    tags_value: str | None = None,
    due_phrase: str | None = None,
    priority: str | None = None,
) -> dict[str, Any]:
    """Build handler entities dict from shared modal fields."""
    entities: dict[str, Any] = {}
    if title and title.strip():
        entities["title"] = title.strip()
    if description and description.strip():
        entities["description"] = description.strip()
    if group and group.strip():
        entities["group"] = group.strip()

    tags = parse_modal_tags(tags_value)
    if tags:
        entities["tags"] = tags

    if title:
        cleaned_title, parsed = parse_tags_from_text(title.strip())
        if parsed:
            entities["title"] = cleaned_title
            existing = entities.get("tags", [])
            entities["tags"] = list(dict.fromkeys([*existing, *parsed]))

    if due_phrase and due_phrase.strip():
        entities["due_date"] = due_phrase.strip()
    if priority and priority.strip():
        entities["priority"] = priority.strip().lower()

    return entities
