"""
Build derived wellness signals from daily summaries.

Rule-based baselines and confidence — no medical inference.
"""

from __future__ import annotations

import statistics
from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.time_utilities import now_timestamp_full
from integrations.google_health.personalization_rules import apply_personalization_rules
from integrations.google_health.schemas import (
    DailySummaryModel,
    HealthSignalModel,
)

logger = get_component_logger("google_health")

BASELINE_WINDOW_DAYS = 14
MIN_BASELINE_DAYS_MEDIUM = 7
MIN_BASELINE_DAYS_HIGH = 14

SLEEP_LOW_HOURS = 6.0
SLEEP_HIGH_HOURS = 8.0
SLEEP_BELOW_BASELINE_RATIO = 0.85
SLEEP_ABOVE_BASELINE_RATIO = 1.15
STEPS_LOW_RATIO = 0.6
STEPS_HIGH_RATIO = 1.4
HR_ELEVATED_DELTA_BPM = 5.0
HRV_LOW_RATIO = 0.85


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    return float(statistics.median(values))


@handle_errors("computing baseline stats", default_return={})
def compute_baseline_stats(
    summaries: list[dict[str, Any]],
    *,
    exclude_date: str | None = None,
) -> dict[str, Any]:
    """Rolling median baselines from prior daily summaries."""
    sleep_minutes: list[float] = []
    steps: list[float] = []
    resting_hr: list[float] = []
    hrv: list[float] = []

    for item in summaries:
        day = item.get("date")
        if exclude_date and day == exclude_date:
            continue
        try:
            model = DailySummaryModel.model_validate(item)
        except Exception:
            continue
        if model.sleep_duration_minutes is not None:
            sleep_minutes.append(float(model.sleep_duration_minutes))
        if model.steps is not None:
            steps.append(float(model.steps))
        if model.resting_hr_bpm is not None:
            resting_hr.append(float(model.resting_hr_bpm))
        if model.hrv_rmssd_ms is not None:
            hrv.append(float(model.hrv_rmssd_ms))

    days_used = len({s.get("date") for s in summaries if s.get("date") != exclude_date})
    return {
        "days_used": days_used,
        "sleep_minutes_median": _median(sleep_minutes),
        "steps_median": _median(steps),
        "resting_hr_median": _median(resting_hr),
        "hrv_median": _median(hrv),
    }


def _confidence_from_baseline_days(days_used: int) -> str:
    if days_used >= MIN_BASELINE_DAYS_HIGH:
        return "high"
    if days_used >= MIN_BASELINE_DAYS_MEDIUM:
        return "medium"
    return "low"


@handle_errors("building signal for date", default_return=None)
def build_signal_for_date(
    target_date: str,
    summaries: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Build derived health signal for one calendar date."""
    today_summary: dict[str, Any] | None = None
    for item in summaries:
        if item.get("date") == target_date:
            today_summary = item
            break

    if not today_summary:
        return None

    try:
        today = DailySummaryModel.model_validate(today_summary)
    except Exception:
        return None

    baselines = compute_baseline_stats(summaries, exclude_date=target_date)
    days_used = baselines.get("days_used") or 0
    confidence = _confidence_from_baseline_days(days_used)

    sleep_hours = (
        round(today.sleep_duration_minutes / 60.0, 2)
        if today.sleep_duration_minutes is not None
        else None
    )

    sleep_recovery = "unknown"
    if sleep_hours is not None:
        if sleep_hours < SLEEP_LOW_HOURS:
            sleep_recovery = "low"
        elif sleep_hours >= SLEEP_HIGH_HOURS:
            sleep_recovery = "high"
        else:
            sleep_recovery = "normal"

    sleep_vs_baseline = "unknown"
    sleep_median = baselines.get("sleep_minutes_median")
    if (
        sleep_median
        and today.sleep_duration_minutes is not None
        and days_used >= MIN_BASELINE_DAYS_MEDIUM
    ):
        ratio = today.sleep_duration_minutes / sleep_median
        if ratio < SLEEP_BELOW_BASELINE_RATIO:
            sleep_vs_baseline = "below"
        elif ratio > SLEEP_ABOVE_BASELINE_RATIO:
            sleep_vs_baseline = "above"
        else:
            sleep_vs_baseline = "normal"

    activity_level = "unknown"
    steps_median = baselines.get("steps_median")
    if today.steps is not None:
        if steps_median and days_used >= MIN_BASELINE_DAYS_MEDIUM:
            ratio = today.steps / steps_median
            if ratio < STEPS_LOW_RATIO:
                activity_level = "low"
            elif ratio > STEPS_HIGH_RATIO:
                activity_level = "high"
            else:
                activity_level = "normal"
        elif today.steps < 3000:
            activity_level = "low"
        elif today.steps > 10000:
            activity_level = "high"
        else:
            activity_level = "normal"

    resting_hr_signal = "unknown"
    hr_median = baselines.get("resting_hr_median")
    if today.resting_hr_bpm is not None and hr_median and days_used >= MIN_BASELINE_DAYS_MEDIUM:
        if today.resting_hr_bpm > hr_median + HR_ELEVATED_DELTA_BPM:
            resting_hr_signal = "elevated"
        else:
            resting_hr_signal = "normal"

    hrv_signal = "unknown"
    hrv_median = baselines.get("hrv_median")
    if today.hrv_rmssd_ms is not None and hrv_median and days_used >= MIN_BASELINE_DAYS_MEDIUM:
        if today.hrv_rmssd_ms < hrv_median * HRV_LOW_RATIO:
            hrv_signal = "low"
        else:
            hrv_signal = "normal"

    partial = {
        "date": target_date,
        "sleep_recovery": sleep_recovery,
        "sleep_hours": sleep_hours,
        "sleep_vs_baseline": sleep_vs_baseline,
        "activity_level": activity_level,
        "resting_hr_signal": resting_hr_signal,
        "hrv_signal": hrv_signal,
        "confidence": confidence,
        "baseline_days_used": days_used,
        "computed_at": now_timestamp_full(),
    }
    partial["message_guidance"] = apply_personalization_rules(partial)

    if not partial["message_guidance"]:
        partial["confidence"] = "low"

    model = HealthSignalModel.model_validate(partial)
    return model.model_dump()


@handle_errors("rebuilding health signals", default_return=[])
def rebuild_signals_for_summaries(
    summaries: list[dict[str, Any]],
    *,
    dates: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Rebuild signals for given dates (or all summary dates)."""
    target_dates = dates or sorted({s.get("date") for s in summaries if s.get("date")})
    signals: list[dict[str, Any]] = []
    for day in target_dates:
        if not day:
            continue
        signal = build_signal_for_date(day, summaries)
        if signal:
            signals.append(signal)
    return signals
