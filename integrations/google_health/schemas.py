"""
Pydantic schemas for Google Health on-disk documents and normalized summaries.

Strict v2 envelopes for health/ JSON files under data/users/{user_id}/health/.
"""

from __future__ import annotations

from typing import Any, Literal

from core.error_handling import handle_errors
from pydantic import BaseModel, ConfigDict, Field

from storage.user_data_v2_base import SCHEMA_VERSION

# Filenames under health/
AUTH_FILENAME = "google_health_auth.json"
DAILY_SUMMARIES_FILENAME = "daily_summaries.json"
HEALTH_SIGNALS_FILENAME = "health_signals.json"
SYNC_STATE_FILENAME = "sync_state.json"

GoogleHealthFeatureState = Literal["enabled", "disabled", "paused"]
SleepRecovery = Literal["low", "normal", "high", "unknown"]
SleepQuality = Literal["low", "normal", "high", "unknown"]
BaselineComparison = Literal["below", "normal", "above", "unknown"]
ActivityLevel = Literal["low", "normal", "high", "unknown"]
ActiveIntensity = Literal["low", "normal", "high", "unknown"]
RestingHrSignal = Literal["elevated", "normal", "unknown"]
HrvSignal = Literal["low", "normal", "unknown"]
SignalConfidence = Literal["low", "medium", "high"]


class SleepStagesSummaryModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    light_minutes: int | None = None
    deep_minutes: int | None = None
    rem_minutes: int | None = None
    awake_minutes: int | None = None


class DailySummaryModel(BaseModel):
    """Normalized raw metrics for one calendar day (not for AI prompts)."""

    model_config = ConfigDict(extra="forbid")

    date: str
    sleep_duration_minutes: int | None = None
    sleep_efficiency_pct: float | None = None
    sleep_stages: SleepStagesSummaryModel | None = None
    steps: int | None = None
    active_minutes: int | None = None
    calories_out: float | None = None
    resting_hr_bpm: float | None = None
    hrv_rmssd_ms: float | None = None
    source_synced_at: str = ""
    api_record_ids: list[str] = Field(default_factory=list)
    completeness: list[str] = Field(default_factory=list)


class DailySummariesCollectionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    summaries: list[DailySummaryModel] = Field(default_factory=list)


class HealthSignalModel(BaseModel):
    """Derived wellness signals for one day."""

    model_config = ConfigDict(extra="forbid")

    date: str
    sleep_recovery: SleepRecovery = "unknown"
    sleep_hours: float | None = None
    sleep_vs_baseline: BaselineComparison = "unknown"
    sleep_quality: SleepQuality = "unknown"
    activity_level: ActivityLevel = "unknown"
    active_intensity: ActiveIntensity = "unknown"
    resting_hr_signal: RestingHrSignal = "unknown"
    hrv_signal: HrvSignal = "unknown"
    confidence: SignalConfidence = "low"
    message_guidance: list[str] = Field(default_factory=list)
    baseline_days_used: int = 0
    computed_at: str = ""


class HealthSignalsCollectionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    signals: list[HealthSignalModel] = Field(default_factory=list)


class GoogleHealthAuthModel(BaseModel):
    """Per-user OAuth token document (sensitive — never log token values)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    access_token: str = ""
    refresh_token: str = ""
    token_type: str = "Bearer"
    expires_at: str = ""
    scopes: list[str] = Field(default_factory=list)
    connected_at: str = ""
    last_refresh_at: str = ""
    google_user_id: str = ""
    tokens_encrypted: bool = False


class SyncStateModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    last_sync_at: str = ""
    last_success_at: str = ""
    last_error: str = ""
    consecutive_failures: int = 0
    reconnect_notice_sent: bool = False
    last_scheduled_slot: str = ""
    baseline_metadata: dict[str, Any] = Field(default_factory=dict)


@handle_errors("creating empty auth document", default_return={})
def empty_auth_document(updated_at: str) -> dict[str, Any]:
    """Return an empty google_health_auth.json document."""
    return GoogleHealthAuthModel(updated_at=updated_at).model_dump()


@handle_errors("creating empty daily summaries document", default_return={})
def empty_daily_summaries_document(updated_at: str) -> dict[str, Any]:
    """Return an empty daily_summaries.json document."""
    return DailySummariesCollectionModel(updated_at=updated_at).model_dump()


@handle_errors("creating empty health signals document", default_return={})
def empty_health_signals_document(updated_at: str) -> dict[str, Any]:
    """Return an empty health_signals.json document."""
    return HealthSignalsCollectionModel(updated_at=updated_at).model_dump()


@handle_errors("creating empty sync state document", default_return={})
def empty_sync_state_document(updated_at: str) -> dict[str, Any]:
    """Return an empty sync_state.json document."""
    return SyncStateModel(updated_at=updated_at).model_dump()
