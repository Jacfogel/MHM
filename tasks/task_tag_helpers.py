"""Task tag normalization helpers (shared by schemas, validation, and service)."""

from __future__ import annotations

import re

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.tags import normalize_tag, normalize_tags

logger = get_component_logger("tasks")

_TASK_TAG_PATTERN = re.compile(r"^[a-z0-9\-_:]+$")


@handle_errors("checking normalized task tag", default_return=False)
def is_valid_normalized_task_tag(tag: str) -> bool:
    """Return True when tag matches core.tags validation rules."""
    return bool(tag) and len(tag) <= 50 and _TASK_TAG_PATTERN.fullmatch(tag) is not None


@handle_errors("sanitizing task tags", default_return=[])
def sanitize_task_tags(tags: list[str] | None) -> list[str]:
    """Normalize and validate task tags using the shared core.tags helpers."""
    if not tags or not isinstance(tags, list):
        return []
    normalized = normalize_tags(tags)
    valid: list[str] = []
    for tag in normalized:
        if is_valid_normalized_task_tag(tag):
            valid.append(tag)
        else:
            logger.warning(f"Invalid task tag '{tag}' removed during sanitization")
    return valid


@handle_errors("normalizing task tag filter", default_return="")
def normalize_task_tag_filter(tag_filter: str | None) -> str:
    """Normalize a tag filter value for list/search comparisons."""
    if not tag_filter or not isinstance(tag_filter, str):
        return ""
    return normalize_tag(tag_filter)
