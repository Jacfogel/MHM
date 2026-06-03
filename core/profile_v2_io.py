"""
Load/save bridging for profile v2 envelopes vs in-memory application shapes.

On-disk JSON is always schema_version 2. Unwrapped dicts/lists match existing
application expectations (for example flat schedule categories in memory).
"""

from __future__ import annotations

from typing import Any, Literal

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.profile_v2_schemas import (
    validate_account_v2_document,
    validate_chat_interactions_v2_document,
    validate_context_v2_document,
    validate_preferences_v2_document,
    validate_schedules_v2_document,
    validate_tags_v2_document,
)
from core.schemas import (
    validate_account_dict,
    validate_preferences_dict,
    validate_schedules_dict,
)
from core.time_format_constants import TIMESTAMP_FULL
from core.time_utilities import format_timestamp, now_timestamp_full, parse_timestamp
from storage.user_data_v2_base import SCHEMA_VERSION

logger = get_component_logger("main")

ProfileDocumentType = Literal[
    "account",
    "preferences",
    "schedules",
    "context",
    "tags",
    "chat_interactions",
]

_V2_ENVELOPE_KEYS = frozenset({"schema_version", "updated_at"})
_SCHEDULE_V2_RESERVED_KEYS = frozenset({"schema_version", "updated_at", "categories"})
_CONTEXT_ACCOUNT_LEAK_KEYS = frozenset(
    {
        "user_id",
        "internal_username",
        "account_status",
        "chat_id",
        "phone",
        "email",
        "discord_user_id",
        "discord_username",
        "timezone",
        "features",
    }
)
_CUSTOM_FIELDS_LIST_KEYS = (
    "health_conditions",
    "medications_treatments",
    "reminders_needed",
    "allergies_sensitivities",
)

_VALIDATORS = {
    "account": validate_account_v2_document,
    "preferences": validate_preferences_v2_document,
    "schedules": validate_schedules_v2_document,
    "context": validate_context_v2_document,
    "tags": validate_tags_v2_document,
    "chat_interactions": validate_chat_interactions_v2_document,
}


@handle_errors("checking profile v2 envelope", default_return=False)
def is_profile_v2_envelope(data: Any) -> bool:
    """Return True when ``data`` is a dict with ``schema_version`` equal to v2."""
    return isinstance(data, dict) and data.get("schema_version") == SCHEMA_VERSION


@handle_errors("normalizing in-memory profile payload", default_return={})
def _normalize_in_memory_profile(
    document_type: ProfileDocumentType, inner: dict[str, Any]
) -> dict[str, Any]:
    """Apply tolerant in-memory validators after unwrapping a v2 on-disk envelope."""
    if document_type == "account":
        normalized, _ = validate_account_dict(inner)
        return normalized if isinstance(normalized, dict) else inner
    if document_type == "preferences":
        normalized, _ = validate_preferences_dict(inner)
        return normalized if isinstance(normalized, dict) else inner
    if document_type == "schedules":
        normalized, _ = validate_schedules_dict(inner)
        return normalized if isinstance(normalized, dict) else inner
    return inner


@handle_errors("normalizing context timestamp", default_return="")
def _normalize_context_timestamp(value: Any) -> str:
    """Coerce non-canonical ISO/microsecond timestamps to canonical TIMESTAMP_FULL."""
    if not isinstance(value, str) or not value.strip():
        return ""
    parsed = parse_timestamp(
        value.strip(),
        allowed=("full", "minute", "microseconds", "external"),
    )
    if parsed is None:
        return value.strip()
    return format_timestamp(parsed, TIMESTAMP_FULL)


@handle_errors("normalizing context profile payload", default_return={})
def _normalize_context_inner(inner: dict[str, Any]) -> dict[str, Any]:
    """Normalize context fields for in-memory use and v2 envelope build."""
    payload = dict(inner)
    stripped = [key for key in _CONTEXT_ACCOUNT_LEAK_KEYS if key in payload]
    for key in stripped:
        payload.pop(key, None)
    if stripped:
        logger.debug(f"Removed account fields from context payload: {stripped}")

    raw_custom = payload.get("custom_fields")
    custom: dict[str, Any] = dict(raw_custom) if isinstance(raw_custom, dict) else {}
    for key in _CUSTOM_FIELDS_LIST_KEYS:
        value = custom.get(key)
        custom[key] = value if isinstance(value, list) else []

    top_level_reminders = payload.pop("reminders_needed", None)
    if isinstance(top_level_reminders, list):
        merged = list(custom.get("reminders_needed") or [])
        for item in top_level_reminders:
            if item not in merged:
                merged.append(item)
        custom["reminders_needed"] = merged

    payload["custom_fields"] = custom

    pronouns = payload.get("pronouns")
    payload["pronouns"] = pronouns if isinstance(pronouns, list) else []

    for ts_key in ("created_at", "last_updated"):
        if ts_key in payload:
            payload[ts_key] = _normalize_context_timestamp(payload[ts_key])

    return payload


@handle_errors("building empty profile payload", default_return={})
def _empty_profile_payload(
    document_type: ProfileDocumentType,
) -> dict[str, Any] | list[dict[str, Any]]:
    """Return the in-memory empty shape for a profile document type after a failed v2 load."""
    if document_type == "chat_interactions":
        return []
    if document_type == "tags":
        return {"tags": [], "metadata": {}}
    return {}


@handle_errors("logging non-v2 profile on disk", default_return=None)
def _warn_non_v2_on_disk(document_type: ProfileDocumentType, raw: Any) -> None:
    """Log when on-disk JSON is not a v2 envelope (load path returns empty in-memory data)."""
    if raw is None:
        return
    kind = type(raw).__name__
    version = raw.get("schema_version") if isinstance(raw, dict) else None
    logger.warning(
        f"Expected v2 envelope for {document_type} on load (got {kind}"
        + (f", schema_version={version!r}" if version is not None else "")
        + "); returning empty in-memory payload"
    )


@handle_errors("unwrapping profile document", default_return={})
def unwrap_profile_document_on_load(
    document_type: ProfileDocumentType, raw: Any
) -> dict[str, Any] | list[dict[str, Any]]:
    """Unwrap a v2 on-disk envelope to in-memory application shapes."""
    if document_type == "chat_interactions":
        if not isinstance(raw, dict) or not is_profile_v2_envelope(raw):
            _warn_non_v2_on_disk(document_type, raw)
            return []
        interactions = raw.get("interactions")
        return interactions if isinstance(interactions, list) else []

    if not isinstance(raw, dict) or not is_profile_v2_envelope(raw):
        _warn_non_v2_on_disk(document_type, raw)
        return _empty_profile_payload(document_type)  # type: ignore[return-value]

    if document_type == "account":
        inner = {k: v for k, v in raw.items() if k not in _V2_ENVELOPE_KEYS}
        metadata = inner.pop("metadata", None)
        if isinstance(metadata, dict):
            for key, value in metadata.items():
                if key not in inner:
                    inner[key] = value
        return _normalize_in_memory_profile("account", inner)

    if document_type == "preferences":
        inner = {k: v for k, v in raw.items() if k not in _V2_ENVELOPE_KEYS}
        return _normalize_in_memory_profile("preferences", inner)

    if document_type == "schedules":
        from core.schedule_document_defaults import migrate_legacy_schedules_structure

        categories = raw.get("categories")
        if isinstance(categories, dict):
            migrated = migrate_legacy_schedules_structure(categories)
            return _normalize_in_memory_profile("schedules", migrated)
        return {}

    if document_type == "context":
        inner = {k: v for k, v in raw.items() if k not in _V2_ENVELOPE_KEYS}
        if "last_updated" not in inner and raw.get("updated_at"):
            inner["last_updated"] = raw["updated_at"]
        return _normalize_context_inner(inner)

    if document_type == "tags":
        return {
            "tags": raw.get("tags", []) if isinstance(raw.get("tags"), list) else [],
            "metadata": raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {},
        }

    return {}


_ACCOUNT_V2_KEYS = frozenset(
    {
        "user_id",
        "internal_username",
        "account_status",
        "chat_id",
        "phone",
        "email",
        "discord_user_id",
        "discord_username",
        "timezone",
        "created_at",
        "features",
        "metadata",
    }
)


@handle_errors("building profile v2 envelope", default_return={})
def _build_v2_envelope(document_type: ProfileDocumentType, inner: dict[str, Any]) -> dict[str, Any]:
    timestamp = now_timestamp_full()
    if document_type == "account":
        payload: dict[str, Any] = {}
        overflow: dict[str, Any] = {}
        for key, value in inner.items():
            if key in _V2_ENVELOPE_KEYS:
                continue
            if key in _ACCOUNT_V2_KEYS:
                payload[key] = value
            else:
                overflow[key] = value
        if overflow:
            metadata = dict(payload.get("metadata") or {})
            metadata.update(overflow)
            payload["metadata"] = metadata
        payload.setdefault("user_id", "")
        payload["schema_version"] = SCHEMA_VERSION
        payload["updated_at"] = inner.get("updated_at") or timestamp
        return payload

    if document_type == "preferences":
        return {
            "schema_version": SCHEMA_VERSION,
            "updated_at": timestamp,
            "categories": inner.get("categories", []),
            "channel": inner.get("channel", {"type": "email"}),
            "checkin_settings": inner.get("checkin_settings"),
            "task_settings": inner.get("task_settings"),
        }

    if document_type == "schedules":
        from core.schedule_document_defaults import migrate_legacy_schedules_structure

        categories_raw = {
            key: value
            for key, value in inner.items()
            if key not in _SCHEDULE_V2_RESERVED_KEYS
        }
        categories = migrate_legacy_schedules_structure(categories_raw)
        return {
            "schema_version": SCHEMA_VERSION,
            "updated_at": timestamp,
            "categories": categories,
        }

    if document_type == "context":
        normalized = _normalize_context_inner(inner)
        updated_at = _normalize_context_timestamp(
            normalized.get("last_updated") or timestamp
        ) or timestamp
        payload = dict(normalized)
        payload["schema_version"] = SCHEMA_VERSION
        payload["updated_at"] = updated_at
        return payload

    if document_type == "tags":
        raw_metadata = inner.get("metadata")
        metadata: dict[str, Any] = (
            dict(raw_metadata) if isinstance(raw_metadata, dict) else {}
        )
        metadata.setdefault("updated_at", timestamp)
        return {
            "schema_version": SCHEMA_VERSION,
            "updated_at": timestamp,
            "tags": inner.get("tags", []),
            "metadata": metadata,
        }

    return inner


@handle_errors("wrapping chat interactions for save", default_return={})
def wrap_chat_interactions_for_save(interactions: list[dict[str, Any]]) -> dict[str, Any]:
    """Wrap interaction rows in a validated v2 on-disk envelope."""
    payload = {
        "schema_version": SCHEMA_VERSION,
        "updated_at": now_timestamp_full(),
        "interactions": interactions,
    }
    normalized, errors = validate_chat_interactions_v2_document(payload)
    if errors:
        logger.warning(f"chat_interactions v2 validation failed: {errors[0]}")
        return payload
    return normalized


@handle_errors("wrapping profile document for save", default_return={})
def wrap_profile_document_for_save(
    document_type: ProfileDocumentType, inner: dict[str, Any]
) -> dict[str, Any]:
    """Build and validate a v2 on-disk envelope from in-memory profile data."""
    payload = _build_v2_envelope(document_type, inner)
    validator = _VALIDATORS.get(document_type)
    if validator is None:
        return payload
    normalized, errors = validator(payload)
    if errors:
        logger.warning(
            f"profile v2 validation failed for {document_type}: {errors[0]}"
        )
        return payload
    return normalized


@handle_errors("preparing profile raw document", default_return={})
def prepare_profile_raw_on_load(
    document_type: ProfileDocumentType, raw: Any
) -> dict[str, Any] | list[dict[str, Any]]:
    """Unwrap a v2 on-disk profile document for registry loaders and tooling."""
    return unwrap_profile_document_on_load(document_type, raw)
