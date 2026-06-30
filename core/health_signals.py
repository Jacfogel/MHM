"""
Public API for health-derived wellness signals.

Channel-agnostic — used by scheduler, AI context, and message orchestration.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from core import get_user_data
from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.time_utilities import DATE_ONLY, now_datetime_full, parse_timestamp_full
from integrations.google_health.data_handlers import load_health_signals

logger = get_component_logger("google_health")


@handle_errors("parsing health signal date", default_return=None)
def _parse_signal_date(date_value: str | None):
    if not date_value:
        return None
    return parse_timestamp_full(f"{date_value} 00:00:00")


@handle_errors("getting google health feature state", default_return="disabled")
def get_google_health_feature_state(user_id: str) -> str:
    account = get_user_data(user_id, "account").get("account") or {}
    features = account.get("features") or {}
    return features.get("google_health") or "disabled"


@handle_errors("checking health personalization active", default_return=False)
def is_personalization_active(user_id: str) -> bool:
    return get_google_health_feature_state(user_id) == "enabled"


@handle_errors("getting today health signal", default_return=None)
def get_today_signal(user_id: str) -> dict[str, Any] | None:
    if not is_personalization_active(user_id):
        return None
    today = now_datetime_full().strftime(DATE_ONLY)
    doc = load_health_signals(user_id)
    if not doc:
        return None
    for signal in doc.get("signals") or []:
        if signal.get("date") == today:
            return signal
    return None


@handle_errors("getting latest usable health signal", default_return=None)
def get_latest_usable_signal(
    user_id: str, *, max_age_days: int = 2
) -> dict[str, Any] | None:
    """Return the newest non-low-confidence signal within the recent window."""
    if not is_personalization_active(user_id):
        return None
    doc = load_health_signals(user_id)
    if not doc:
        return None

    today = now_datetime_full().date()
    cutoff = today - timedelta(days=max_age_days)
    candidates: list[tuple[Any, dict[str, Any]]] = []

    for signal in doc.get("signals") or []:
        if not isinstance(signal, dict):
            continue
        if signal.get("confidence") == "low":
            continue
        signal_date = _parse_signal_date(str(signal.get("date") or ""))
        if signal_date is None:
            continue
        if signal_date.date() < cutoff:
            continue
        candidates.append((signal_date, signal))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


@handle_errors("resolving active health signal", default_return=None)
def resolve_active_health_signal(user_id: str) -> dict[str, Any] | None:
    """Today's signal when synced; otherwise the latest usable recent signal."""
    return get_today_signal(user_id) or get_latest_usable_signal(user_id)


@handle_errors("getting message guidance for user", default_return=[])
def get_message_guidance(user_id: str) -> list[str]:
    signal = resolve_active_health_signal(user_id)
    if not signal:
        return []
    if signal.get("confidence") == "low":
        return []
    return list(signal.get("message_guidance") or [])


@handle_errors("checking avoid productivity pressure", default_return=False)
def should_avoid_productivity_pressure(user_id: str) -> bool:
    guidance = get_message_guidance(user_id)
    return "avoid_high_pressure_productivity_prompt" in guidance
