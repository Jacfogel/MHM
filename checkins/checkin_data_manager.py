"""Check-in persistence and feature-state helpers."""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

from core import get_user_data
from core.error_handling import handle_errors
from core.file_operations import get_user_file_path, load_json_data, save_json_data
from core.logger import get_component_logger
from core.time_utilities import now_datetime_full, now_timestamp_full, parse_timestamp_full
from storage.user_data_v2_base import SCHEMA_VERSION

logger = get_component_logger("user_activity")
tracking_logger = get_component_logger("user_activity")


@handle_errors("converting v2 checkin to runtime response", default_return={})
def _checkin_to_runtime_response(checkin: dict[str, Any]) -> dict[str, Any]:
    """Return the flat response shape expected by existing analytics callers."""
    raw_responses = checkin.get("responses")
    responses: dict[str, Any] = raw_responses if isinstance(raw_responses, dict) else {}
    runtime: dict[str, Any] = dict(responses)
    submitted_at = str(checkin.get("submitted_at", "") or "").strip()
    runtime["submitted_at"] = submitted_at
    runtime["questions_asked"] = checkin.get("questions_asked", list(responses.keys()))
    runtime["responses"] = responses
    return runtime


@handle_errors("resolving check-in runtime timestamp", default_return="")
def checkin_runtime_timestamp(checkin: Any) -> str:
    """Wall-clock timestamp string for a check-in row."""
    if not isinstance(checkin, dict):
        return ""
    raw = checkin.get("submitted_at")
    if raw is None:
        return ""
    return str(raw).strip()


@handle_errors("building v2 checkin from payload", default_return={})
def _build_v2_checkin_from_response_payload(response_data: dict[str, Any]) -> dict[str, Any]:
    """Build a canonical v2 check-in dict from a runtime payload."""
    candidates: list[Any] = [
        response_data.get("submitted_at"),
        response_data.get("sent_at"),
    ]
    submitted_at = next((c for c in candidates if c), None) or now_timestamp_full()
    responses = response_data.get("responses")
    if not isinstance(responses, dict):
        skipped = {
            "timestamp",
            "submitted_at",
            "sent_at",
            "questions_asked",
            "source",
            "linked_item_ids",
            "created_at",
            "updated_at",
            "archived_at",
            "deleted_at",
            "metadata",
        }
        responses = {key: value for key, value in response_data.items() if key not in skipped}
    return {
        "id": response_data.get("id") or str(uuid.uuid4()),
        "submitted_at": submitted_at,
        "source": response_data.get("source")
        or {"system": "mhm", "channel": "", "actor": ""},
        "responses": responses,
        "questions_asked": response_data.get("questions_asked") or list(responses.keys()),
        "linked_item_ids": response_data.get("linked_item_ids") or [],
        "created_at": response_data.get("created_at") or submitted_at,
        "updated_at": response_data.get("updated_at") or submitted_at,
        "archived_at": response_data.get("archived_at"),
        "deleted_at": response_data.get("deleted_at"),
        "metadata": response_data.get("metadata") or {},
    }


@handle_errors("loading v2 checkins envelope for append", re_raise=True)
def _coerce_v2_checkins_envelope_for_store(existing_data: Any) -> dict[str, Any] | None:
    """Return a mutable v2 envelope for appending a new check-in."""
    if existing_data is None or existing_data == {}:
        return {
            "schema_version": SCHEMA_VERSION,
            "updated_at": now_timestamp_full(),
            "checkins": [],
        }
    if not isinstance(existing_data, dict):
        logger.error(
            f"checkins.json must be a v2 object (found {type(existing_data).__name__})."
        )
        return None
    if existing_data.get("schema_version") != SCHEMA_VERSION:
        logger.error(
            f"checkins.json must have schema_version {SCHEMA_VERSION} "
            f"(found {existing_data.get('schema_version')!r})."
        )
        return None
    raw_checkins = existing_data.get("checkins")
    if not isinstance(raw_checkins, list):
        logger.error("checkins.json v2 envelope requires a list at key 'checkins'.")
        return None
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": existing_data.get("updated_at") or now_timestamp_full(),
        "checkins": list(raw_checkins),
    }


@handle_errors("storing check-in response")
def store_checkin_response(user_id: str, response_data: dict[str, Any]) -> None:
    """Store one check-in response in the user's check-in log."""
    log_file = get_user_file_path(user_id, "checkins")
    existing_data = load_json_data(log_file)
    envelope = _coerce_v2_checkins_envelope_for_store(existing_data)
    if envelope is None:
        return
    envelope["checkins"].append(_build_v2_checkin_from_response_payload(response_data))
    envelope["updated_at"] = now_timestamp_full()
    save_json_data(envelope, log_file)
    logger.debug(f"Stored v2 checkin response for user {user_id}")


@handle_errors("getting recent checkins", default_return=[])
def get_recent_checkins(user_id: str, limit: int = 7) -> list[dict[str, Any]]:
    """Get recent check-in responses for a user."""
    log_file = get_user_file_path(user_id, "checkins")
    data = load_json_data(log_file)
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        return []
    rows = [
        _checkin_to_runtime_response(item)
        for item in data.get("checkins", [])
        if isinstance(item, dict)
    ]
    return sorted(rows, key=_get_checkin_timestamp_for_sorting, reverse=True)[:limit]


@handle_errors("getting checkins by days", default_return=[])
def get_checkins_by_days(user_id: str, days: int = 7) -> list[dict[str, Any]]:
    """Get check-ins from the last N calendar days."""
    all_checkins = get_recent_checkins(user_id, limit=1000)
    if not all_checkins:
        return []

    cutoff_date = now_datetime_full() - timedelta(days=days)
    recent_checkins = []
    for checkin in all_checkins:
        if not checkin.get("submitted_at"):
            continue
        checkin_date = parse_timestamp_full(str(checkin.get("submitted_at", "")))
        if checkin_date is not None and checkin_date >= cutoff_date:
            recent_checkins.append(checkin)
    return recent_checkins


@handle_errors("checking if user checkins enabled", default_return=False)
def is_user_checkins_enabled(user_id: str) -> bool:
    """Check if check-ins are enabled for a user."""
    user_data_result = get_user_data(user_id, "account")
    user_account = user_data_result.get("account")
    if not user_account:
        return False
    return user_account.get("features", {}).get("checkins") == "enabled"


@handle_errors("getting check-in timestamp for sorting", default_return=0.0)
def _get_checkin_timestamp_for_sorting(item: Any) -> float:
    if isinstance(item, str) or not isinstance(item, dict):
        return 0.0
    timestamp = item.get("submitted_at") or "1970-01-01 00:00:00"
    dt = parse_timestamp_full(str(timestamp))
    if dt is None:
        return 0.0
    return dt.timestamp()
