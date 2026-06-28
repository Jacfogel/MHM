"""
Per-user Google Health sync orchestration.

Automated polling path — idempotent daily upsert + signal rebuild.
"""

from __future__ import annotations

import os
from typing import Any

from core import get_user_data, update_user_account
from core.config import (
    GOOGLE_HEALTH_ENABLED,
    GOOGLE_HEALTH_SYNC_FAILURE_PAUSE_THRESHOLD,
    GOOGLE_HEALTH_SYNC_LOOKBACK_DAYS,
)
from core.error_handling import CommunicationError, handle_errors
from core.logger import get_component_logger
from core.time_utilities import now_timestamp_full
from core.user_management import get_all_user_ids
from integrations.google_health.auth import ensure_valid_access_token
from integrations.google_health.client import fetch_daily_summaries
from integrations.google_health.data_handlers import (
    has_valid_auth,
    load_daily_summaries,
    load_health_signals,
    load_sync_state,
    save_daily_summaries,
    save_health_signals,
    save_sync_state,
)
from integrations.google_health.signal_builder import rebuild_signals_for_summaries

logger = get_component_logger("google_health")


def _testing_mode() -> bool:
    return os.getenv("MHM_TESTING") == "1"


def _google_health_feature_enabled(user_id: str) -> bool:
    account = get_user_data(user_id, "account").get("account") or {}
    features = account.get("features") or {}
    return features.get("google_health") == "enabled"


_SCALAR_SUMMARY_FIELDS = (
    "sleep_duration_minutes",
    "sleep_efficiency_pct",
    "steps",
    "active_minutes",
    "calories_out",
    "resting_hr_bpm",
    "hrv_rmssd_ms",
)


def merge_summary_records(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Merge one daily summary, keeping existing values when incoming omits them."""
    merged = dict(existing)
    for key in _SCALAR_SUMMARY_FIELDS:
        incoming_value = incoming.get(key)
        if incoming_value is not None:
            merged[key] = incoming_value
    if incoming.get("sleep_stages"):
        merged["sleep_stages"] = incoming["sleep_stages"]
    record_ids = list(existing.get("api_record_ids") or [])
    for record_id in incoming.get("api_record_ids") or []:
        if record_id not in record_ids:
            record_ids.append(record_id)
    merged["api_record_ids"] = record_ids
    completeness = set(existing.get("completeness") or [])
    completeness.update(incoming.get("completeness") or [])
    merged["completeness"] = sorted(completeness)
    if incoming.get("source_synced_at"):
        merged["source_synced_at"] = incoming["source_synced_at"]
    merged["date"] = existing.get("date") or incoming.get("date")
    return merged


@handle_errors("upserting daily summaries", default_return=[])
def upsert_daily_summaries(
    existing: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_date = {item["date"]: item for item in existing if item.get("date")}
    for item in incoming:
        day = item.get("date")
        if not day:
            continue
        if day in by_date:
            by_date[day] = merge_summary_records(by_date[day], item)
        else:
            by_date[day] = item
    return sorted(by_date.values(), key=lambda x: x.get("date") or "")


@handle_errors("merging health signals", default_return=[])
def merge_health_signals(
    existing: list[dict[str, Any]],
    rebuilt: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_date = {item["date"]: item for item in existing if item.get("date")}
    for item in rebuilt:
        day = item.get("date")
        if day:
            by_date[day] = item
    return sorted(by_date.values(), key=lambda x: x.get("date") or "")


@handle_errors("pausing google health feature", default_return=False)
def pause_google_health_feature(user_id: str, *, reason: str = "") -> bool:
    account = get_user_data(user_id, "account").get("account") or {}
    features = dict(account.get("features") or {})
    features["google_health"] = "paused"
    ok = update_user_account(user_id, {"features": features})
    if ok:
        logger.warning(
            f"Paused Google Health for user {user_id}{f': {reason}' if reason else ''}"
        )
    return ok


@handle_errors("syncing user health data", default_return=False)
def sync_user_health_data(user_id: str, *, force: bool = False) -> bool:
    """
    Sync Google Health data for one user.

    Skips when globally disabled, testing mode, feature not enabled, or no auth.
    """
    if not GOOGLE_HEALTH_ENABLED and not force:
        return False
    if _testing_mode() and not force:
        logger.debug(f"Skipping health sync in testing mode for user {user_id}")
        return False
    if not _google_health_feature_enabled(user_id):
        return False
    if not has_valid_auth(user_id):
        logger.debug(f"No Google Health auth for user {user_id} — skipping sync")
        return False

    sync_state = load_sync_state(user_id) or {}
    now = now_timestamp_full()

    try:
        token = ensure_valid_access_token(user_id)
        if not token:
            raise CommunicationError("Unable to obtain valid access token")

        incoming = fetch_daily_summaries(
            token, lookback_days=GOOGLE_HEALTH_SYNC_LOOKBACK_DAYS
        )
        doc = load_daily_summaries(user_id) or {"summaries": []}
        merged = upsert_daily_summaries(doc.get("summaries") or [], incoming)
        doc["summaries"] = merged
        save_daily_summaries(user_id, doc)

        affected_dates = [item.get("date") for item in incoming if item.get("date")]
        rebuilt = rebuild_signals_for_summaries(merged, dates=affected_dates or None)
        signals_doc = load_health_signals(user_id) or {"signals": []}
        signals_doc["signals"] = merge_health_signals(
            signals_doc.get("signals") or [], rebuilt
        )
        save_health_signals(user_id, signals_doc)

        sync_state.update(
            {
                "last_sync_at": now,
                "last_success_at": now,
                "last_error": "",
                "consecutive_failures": 0,
            }
        )
        save_sync_state(user_id, sync_state)
        logger.info(
            f"Google Health sync completed for user {user_id} ({len(incoming)} summaries)"
        )
        return True

    except Exception as exc:
        failures = int(sync_state.get("consecutive_failures") or 0) + 1
        sync_state.update(
            {
                "last_sync_at": now,
                "last_error": str(exc)[:500],
                "consecutive_failures": failures,
            }
        )
        save_sync_state(user_id, sync_state)
        logger.warning(
            f"Google Health sync failed for user {user_id} (failure {failures}): {exc}"
        )
        if failures >= GOOGLE_HEALTH_SYNC_FAILURE_PAUSE_THRESHOLD:
            pause_google_health_feature(user_id, reason=str(exc)[:200])
        return False


@handle_errors("syncing all enabled users", default_return=0)
def sync_all_enabled_users() -> int:
    """Run sync for every user with google_health enabled."""
    if not GOOGLE_HEALTH_ENABLED:
        return 0
    if _testing_mode():
        return 0

    count = 0
    for user_id in get_all_user_ids():
        if sync_user_health_data(user_id):
            count += 1
    return count


def main() -> None:
    """Dev entry: python -m integrations.google_health.sync_manager --user-id ID"""
    import argparse

    parser = argparse.ArgumentParser(description="Manual Google Health sync (debug)")
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    ok = sync_user_health_data(args.user_id, force=args.force)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
