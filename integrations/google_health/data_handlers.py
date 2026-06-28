"""
Health data load/save helpers via storage.user_item_storage.

No business logic — paths and I/O only.
"""

from __future__ import annotations

import shutil
from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.time_utilities import now_timestamp_full
from storage.user_data_validation import is_valid_user_id
from storage.user_item_storage import (
    ensure_user_subdir,
    get_user_subdir_path,
    load_user_json_file,
    save_user_json_file,
)

from integrations.google_health.schemas import (
    AUTH_FILENAME,
    DAILY_SUMMARIES_FILENAME,
    HEALTH_SIGNALS_FILENAME,
    SYNC_STATE_FILENAME,
    DailySummariesCollectionModel,
    GoogleHealthAuthModel,
    HealthSignalsCollectionModel,
    SyncStateModel,
    empty_auth_document,
    empty_daily_summaries_document,
    empty_health_signals_document,
    empty_sync_state_document,
)

logger = get_component_logger("google_health")

HEALTH_SUBDIR = "health"

_INIT_FILES = {
    AUTH_FILENAME: {},  # filled with defaults on first ensure
    DAILY_SUMMARIES_FILENAME: {},
    HEALTH_SIGNALS_FILENAME: {},
    SYNC_STATE_FILENAME: {},
}


def _now() -> str:
    return now_timestamp_full()


@handle_errors("ensuring health directory", default_return=False)
def ensure_health_directory(user_id: str) -> bool:
    if not is_valid_user_id(user_id):
        logger.error(f"Invalid user_id for ensure_health_directory: {user_id}")
        return False
    ts = _now()
    init = {
        AUTH_FILENAME: empty_auth_document(ts),
        DAILY_SUMMARIES_FILENAME: empty_daily_summaries_document(ts),
        HEALTH_SIGNALS_FILENAME: empty_health_signals_document(ts),
        SYNC_STATE_FILENAME: empty_sync_state_document(ts),
    }
    path = ensure_user_subdir(user_id, HEALTH_SUBDIR, init_files=init)
    return path is not None


def _load_or_default(
    user_id: str,
    filename: str,
    default_factory,
    model_cls,
) -> dict[str, Any]:
    ensure_health_directory(user_id)
    raw = load_user_json_file(user_id, HEALTH_SUBDIR, filename, default_factory(_now()))
    if not isinstance(raw, dict):
        return default_factory(_now())
    try:
        return model_cls.model_validate(raw).model_dump()
    except Exception:
        logger.warning(
            f"Invalid {filename} for user {user_id} — returning empty document"
        )
        return default_factory(_now())


@handle_errors("loading google health auth", default_return=None)
def load_auth(user_id: str) -> dict[str, Any] | None:
    if not is_valid_user_id(user_id):
        return None
    return _load_or_default(user_id, AUTH_FILENAME, empty_auth_document, GoogleHealthAuthModel)


@handle_errors("saving google health auth", default_return=False)
def save_auth(user_id: str, data: dict[str, Any]) -> bool:
    if not is_valid_user_id(user_id):
        return False
    ensure_health_directory(user_id)
    payload = GoogleHealthAuthModel.model_validate(
        {**data, "updated_at": _now()}
    ).model_dump()
    return bool(save_user_json_file(user_id, HEALTH_SUBDIR, AUTH_FILENAME, payload))


@handle_errors("loading daily summaries", default_return=None)
def load_daily_summaries(user_id: str) -> dict[str, Any] | None:
    if not is_valid_user_id(user_id):
        return None
    try:
        return _load_or_default(
            user_id,
            DAILY_SUMMARIES_FILENAME,
            empty_daily_summaries_document,
            DailySummariesCollectionModel,
        )
    except Exception:
        return empty_daily_summaries_document(_now())


@handle_errors("saving daily summaries", default_return=False)
def save_daily_summaries(user_id: str, data: dict[str, Any]) -> bool:
    if not is_valid_user_id(user_id):
        return False
    ensure_health_directory(user_id)
    payload = DailySummariesCollectionModel.model_validate(
        {**data, "updated_at": _now()}
    ).model_dump()
    return bool(
        save_user_json_file(user_id, HEALTH_SUBDIR, DAILY_SUMMARIES_FILENAME, payload)
    )


@handle_errors("loading health signals", default_return=None)
def load_health_signals(user_id: str) -> dict[str, Any] | None:
    if not is_valid_user_id(user_id):
        return None
    return _load_or_default(
        user_id,
        HEALTH_SIGNALS_FILENAME,
        empty_health_signals_document,
        HealthSignalsCollectionModel,
    )


@handle_errors("saving health signals", default_return=False)
def save_health_signals(user_id: str, data: dict[str, Any]) -> bool:
    if not is_valid_user_id(user_id):
        return False
    ensure_health_directory(user_id)
    payload = HealthSignalsCollectionModel.model_validate(
        {**data, "updated_at": _now()}
    ).model_dump()
    return bool(
        save_user_json_file(user_id, HEALTH_SUBDIR, HEALTH_SIGNALS_FILENAME, payload)
    )


@handle_errors("loading sync state", default_return=None)
def load_sync_state(user_id: str) -> dict[str, Any] | None:
    if not is_valid_user_id(user_id):
        return None
    return _load_or_default(
        user_id,
        SYNC_STATE_FILENAME,
        empty_sync_state_document,
        SyncStateModel,
    )


@handle_errors("saving sync state", default_return=False)
def save_sync_state(user_id: str, data: dict[str, Any]) -> bool:
    if not is_valid_user_id(user_id):
        return False
    ensure_health_directory(user_id)
    payload = SyncStateModel.model_validate({**data, "updated_at": _now()}).model_dump()
    return bool(save_user_json_file(user_id, HEALTH_SUBDIR, SYNC_STATE_FILENAME, payload))


@handle_errors("deleting user health data", default_return=False)
def delete_user_health_data(user_id: str) -> bool:
    """Remove entire health/ subdir for a user."""
    if not is_valid_user_id(user_id):
        return False
    path = get_user_subdir_path(user_id, HEALTH_SUBDIR)
    if path is None or not path.exists():
        return True
    try:
        shutil.rmtree(path, ignore_errors=True)
        logger.info(f"Deleted health data directory for user {user_id}")
        return True
    except OSError as exc:
        logger.error(f"Failed to delete health data for user {user_id}: {exc}")
        return False


@handle_errors("checking health auth present", default_return=False)
def has_valid_auth(user_id: str) -> bool:
    auth = load_auth(user_id)
    if not auth:
        return False
    return bool(auth.get("refresh_token") or auth.get("access_token"))
