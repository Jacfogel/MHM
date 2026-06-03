"""
Load/save bridging for profile v2 envelopes vs legacy on-disk shapes.

Unwrapped dicts/lists match existing application expectations; wrapping applies on
save when PROFILE_V2_WRITE is enabled.
"""

from __future__ import annotations

from typing import Any, Literal

from core.config import is_profile_v2_enforce_enabled, is_profile_v2_write_enabled
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
from core.time_utilities import now_timestamp_full
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
_LEGACY_SCHEDULE_RESERVED = frozenset({"schema_version", "updated_at", "categories"})

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


# devtools: ignore[facade-shims]: tolerant legacy normalizer during profile v2 dual-read
@handle_errors("validating legacy profile document", default_return={})
def _legacy_validate(document_type: ProfileDocumentType, inner: dict[str, Any]) -> dict[str, Any]:
    """Apply ``core/schemas.py`` validators to unwrapped in-memory profile payloads."""
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


# devtools: ignore[facade-shims]: dual-read bridge from on-disk v2 or legacy JSON to in-memory shapes
@handle_errors("unwrapping profile document", default_return={})
def unwrap_profile_document_on_load(
    document_type: ProfileDocumentType, raw: Any
) -> dict[str, Any] | list[dict[str, Any]]:
    """Normalize on-disk JSON (v2 envelope or legacy) to legacy in-memory shapes."""
    if document_type == "chat_interactions":
        if isinstance(raw, list):
            return raw
        if is_profile_v2_envelope(raw):
            interactions = raw.get("interactions")
            return interactions if isinstance(interactions, list) else []
        return []

    if not isinstance(raw, dict):
        return {} if document_type != "tags" else {"tags": [], "metadata": {}}

    if not is_profile_v2_envelope(raw):
        if document_type == "schedules":
            from core.schedule_document_defaults import migrate_legacy_schedules_structure

            migrated = migrate_legacy_schedules_structure(raw)
            return _legacy_validate("schedules", migrated)
        return _legacy_validate(document_type, raw)

    if document_type == "account":
        inner = {k: v for k, v in raw.items() if k not in _V2_ENVELOPE_KEYS}
        metadata = inner.pop("metadata", None)
        if isinstance(metadata, dict):
            for key, value in metadata.items():
                if key not in inner:
                    inner[key] = value
        return _legacy_validate("account", inner)

    if document_type == "preferences":
        inner = {k: v for k, v in raw.items() if k not in _V2_ENVELOPE_KEYS}
        return _legacy_validate("preferences", inner)

    if document_type == "schedules":
        from core.schedule_document_defaults import migrate_legacy_schedules_structure

        categories = raw.get("categories")
        if isinstance(categories, dict):
            migrated = migrate_legacy_schedules_structure(categories)
            return _legacy_validate("schedules", migrated)
        return {}

    if document_type == "context":
        inner = {k: v for k, v in raw.items() if k not in _V2_ENVELOPE_KEYS}
        if "last_updated" not in inner and raw.get("updated_at"):
            inner["last_updated"] = raw["updated_at"]
        return inner

    if document_type == "tags":
        return {
            "tags": raw.get("tags", []) if isinstance(raw.get("tags"), list) else [],
            "metadata": raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {},
        }

    return raw


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
            if key not in _LEGACY_SCHEDULE_RESERVED
        }
        categories = migrate_legacy_schedules_structure(categories_raw)
        return {
            "schema_version": SCHEMA_VERSION,
            "updated_at": timestamp,
            "categories": categories,
        }

    if document_type == "context":
        payload = dict(inner)
        payload["schema_version"] = SCHEMA_VERSION
        payload["updated_at"] = payload.get("last_updated") or timestamp
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


@handle_errors("wrapping chat interactions for save", default_return=[])
def wrap_chat_interactions_for_save(interactions: list[dict[str, Any]]) -> dict[str, Any] | list[dict[str, Any]]:
    """Wrap interaction rows in a v2 envelope when ``PROFILE_V2_WRITE`` is enabled."""
    if not is_profile_v2_write_enabled():
        return interactions
    payload = {
        "schema_version": SCHEMA_VERSION,
        "updated_at": now_timestamp_full(),
        "interactions": interactions,
    }
    normalized, errors = validate_chat_interactions_v2_document(payload)
    if errors and is_profile_v2_enforce_enabled():
        logger.warning(f"chat_interactions v2 enforce failed: {errors[0]}")
        return interactions
    return normalized if not errors else payload


@handle_errors("wrapping profile document for save", default_return={})
def wrap_profile_document_for_save(
    document_type: ProfileDocumentType, inner: dict[str, Any]
) -> dict[str, Any]:
    """Build and optionally validate a v2 on-disk envelope from in-memory profile data."""
    if not is_profile_v2_write_enabled():
        return inner
    payload = _build_v2_envelope(document_type, inner)
    validator = _VALIDATORS.get(document_type)
    if validator is None:
        return inner
    normalized, errors = validator(payload)
    if errors:
        if is_profile_v2_enforce_enabled():
            logger.warning(
                f"profile v2 enforce failed for {document_type}: {errors[0]}; "
                "saving legacy shape"
            )
            return inner
        return payload
    return normalized


# devtools: ignore[facade-shims]: compatibility alias for loader call sites
@handle_errors("preparing profile raw document", default_return={})
def prepare_profile_raw_on_load(
    document_type: ProfileDocumentType, raw: Any
) -> dict[str, Any] | list[dict[str, Any]]:
    """Alias for :func:`unwrap_profile_document_on_load` used by the registry loaders."""
    return unwrap_profile_document_on_load(document_type, raw)

