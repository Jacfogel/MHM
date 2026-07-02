"""
Strict v2 on-disk envelopes for profile, tags, and chat-interaction JSON.

Leaf module: do not import tasks/ or notebook/. Runtime loaders unwrap to the
legacy in-memory shapes expected by the rest of the codebase.
"""

from __future__ import annotations

import importlib
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.error_handling import ValidationError, handle_errors
from core.time_utilities import parse_timestamp_full
from storage.user_data_v2_base import SCHEMA_VERSION, v2_schema_validation_error

_TIME_PATTERN = re.compile(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
_VALID_DAYS = {
    "ALL",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
}
_TAG_PATTERN = re.compile(r"^[a-z0-9\-_:]+$")

try:
    import pytz
except Exception:
    pytz = None


# error_handling_exclude: validator helper must raise for invalid timestamps.
def _validate_full_timestamp(value: str) -> str:
    """Require canonical full timestamp strings for v2 envelope metadata fields."""
    if parse_timestamp_full(value) is None:
        raise v2_schema_validation_error("timestamp must use canonical full timestamp format")
    return value


class FeaturesV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    automated_messages: Literal["enabled", "disabled"] = "disabled"
    checkins: Literal["enabled", "disabled"] = "disabled"
    task_management: Literal["enabled", "disabled"] = "disabled"
    google_health: Literal["enabled", "disabled", "paused"] = "disabled"

    @field_validator(
        "automated_messages",
        "checkins",
        "task_management",
        mode="before",
    )
    @classmethod
    def _coerce_flag(cls, value: Any) -> str:
        """Normalize feature flag inputs to enabled/disabled literals."""
        if isinstance(value, bool):
            return "enabled" if value else "disabled"
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in ("enabled", "enable", "true", "yes", "1"):
                return "enabled"
            if lowered in ("disabled", "disable", "false", "no", "0"):
                return "disabled"
        return "disabled"

    @field_validator("google_health", mode="before")
    @classmethod
    # devtools: ignore[facade-shims]: pydantic before-validator for google_health (supports paused)
    def _coerce_google_health(cls, value: Any) -> str:
        """Normalize google_health to enabled, disabled, or paused."""
        if isinstance(value, bool):
            return "enabled" if value else "disabled"
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in ("enabled", "enable", "true", "yes", "1"):
                return "enabled"
            if lowered == "paused":
                return "paused"
            if lowered in ("disabled", "disable", "false", "no", "0"):
                return "disabled"
        return "disabled"


class ChannelV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["email", "discord"]
    contact: str | None = None


class PeriodV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    active: bool = True
    days: list[str] = Field(default_factory=lambda: ["ALL"])
    start_time: str = "00:00"
    end_time: str = "23:59"

    @field_validator("start_time", "end_time")
    @classmethod
    def _valid_time(cls, value: str) -> str:
        """Normalize schedule period times to HH:MM or 00:00 when invalid."""
        if not value or not _TIME_PATTERN.match(value):
            return "00:00"
        return value

    @field_validator("days")
    @classmethod
    # not_duplicate: schema_v1_v2_period_validators
    def _valid_days(cls, value: list[str]) -> list[str]:
        """Filter schedule days to the allowed set, defaulting to ALL."""
        if not value:
            return ["ALL"]
        filtered = [day for day in value if day in _VALID_DAYS]
        return filtered or ["ALL"]


class CategoryScheduleV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    periods: dict[str, PeriodV2Model]


class CustomFieldsV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    health_conditions: list[str] = Field(default_factory=list)
    medications_treatments: list[str] = Field(default_factory=list)
    reminders_needed: list[str] = Field(default_factory=list)
    allergies_sensitivities: list[str] = Field(default_factory=list)


class TagsMetadataV2Model(BaseModel):
    model_config = ConfigDict(extra="allow")

    created_at: str = ""
    updated_at: str = ""
    initialized_with_defaults: bool | None = None
    reinitialized: bool | None = None


class ChatInteractionV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_message: str = ""
    ai_response: str = ""
    context_used: bool = False
    message_length: int = 0
    response_length: int = 0
    timestamp: str

    @field_validator("timestamp")
    @classmethod
    def _validate_timestamp(cls, value: str) -> str:
        return _validate_full_timestamp(value)


class AccountV2EnvelopeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    user_id: str
    internal_username: str = ""
    account_status: Literal["active", "inactive", "suspended"] = "active"
    chat_id: str = ""
    phone: str = ""
    email: str = ""
    discord_user_id: str = ""
    discord_username: str = ""
    timezone: str = ""
    created_at: str = ""
    features: FeaturesV2Model = Field(default_factory=FeaturesV2Model)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("created_at")
    @classmethod
    def _validate_created_at(cls, value: str) -> str:
        if not value:
            return value
        return _validate_full_timestamp(value)

    @field_validator("updated_at")
    @classmethod
    def _require_updated_at(cls, value: str) -> str:
        return _validate_full_timestamp(value)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        """Drop invalid email strings to empty for strict account envelopes."""
        if not value:
            return ""
        pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        return value if pattern.match(value) else ""

    @field_validator("discord_user_id")
    @classmethod
    # not_duplicate: schema_v1_v2_discord_validators
    def _normalize_discord_id(cls, value: str) -> str:
        """Validate Discord snowflake IDs; invalid values become empty."""
        if not value:
            return ""
        normalized = value.strip()
        is_valid = importlib.import_module("storage.user_data_validation").is_valid_discord_id
        return normalized if is_valid(normalized) else ""

    @field_validator("timezone")
    @classmethod
    def _normalize_timezone(cls, value: str) -> str:
        """Keep only IANA timezone names known to pytz when available."""
        if not value or not isinstance(value, str):
            return ""
        candidate = value.strip()
        if pytz and candidate in pytz.all_timezones:
            return candidate
        return ""

    @field_validator("discord_username")
    @classmethod
    # not_duplicate: schema_v1_v2_discord_validators
    def _normalize_discord_username(cls, value: str) -> str:
        """Trim and bound Discord username length for on-disk storage."""
        if not value:
            return ""
        normalized = value.strip()
        return normalized[:100] if len(normalized) > 100 else normalized


class PreferencesV2EnvelopeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    categories: list[str] = Field(default_factory=list)
    channel: ChannelV2Model = Field(default_factory=lambda: ChannelV2Model(type="email"))
    checkin_settings: dict[str, Any] | None = None
    task_settings: dict[str, Any] | None = None

    @field_validator("updated_at")
    @classmethod
    def _validate_updated_at(cls, value: str) -> str:
        return _validate_full_timestamp(value)

    @field_validator("categories")
    @classmethod
    def _validate_categories(cls, value: list[str]) -> list[str]:
        if not value:
            return value
        try:
            allowed = importlib.import_module(
                "messages.message_data_manager"
            ).get_message_categories()
        except Exception:
            allowed = [
                "motivational",
                "health",
                "fun_facts",
                "quotes_to_ponder",
                "word_of_the_day",
            ]
        invalid = [category for category in value if category not in allowed]
        if invalid:
            raise ValidationError(
                f"Invalid categories: {invalid}",
                details={"invalid_categories": invalid, "allowed_categories": allowed},
            )
        return value


class SchedulesV2EnvelopeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    categories: dict[str, CategoryScheduleV2Model] = Field(default_factory=dict)

    @field_validator("updated_at")
    @classmethod
    def _validate_updated_at(cls, value: str) -> str:
        return _validate_full_timestamp(value)


class ContextV2EnvelopeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    preferred_name: str = ""
    gender_identity: list[str] = Field(default_factory=list)
    pronouns: list[str] = Field(default_factory=list)
    date_of_birth: str = ""
    custom_fields: CustomFieldsV2Model = Field(default_factory=CustomFieldsV2Model)
    interests: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    loved_ones: list[dict[str, Any]] = Field(default_factory=list)
    activities_for_encouragement: list[str] = Field(default_factory=list)
    notes_for_ai: list[str] = Field(default_factory=list)
    created_at: str = ""
    last_updated: str = ""

    @field_validator("created_at", "last_updated")
    @classmethod
    def _validate_optional_timestamps(cls, value: str) -> str:
        if not value:
            return value
        return _validate_full_timestamp(value)

    @field_validator("updated_at")
    @classmethod
    def _require_updated_at(cls, value: str) -> str:
        return _validate_full_timestamp(value)

    @field_validator("date_of_birth")
    @classmethod
    def _validate_dob(cls, value: str) -> str:
        if not value:
            return ""
        from core.time_utilities import parse_date_only

        if parse_date_only(value) is None:
            raise v2_schema_validation_error("date_of_birth must be YYYY-MM-DD")
        return value


class TagsV2EnvelopeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    tags: list[str] = Field(default_factory=list)
    metadata: TagsMetadataV2Model = Field(default_factory=TagsMetadataV2Model)

    @field_validator("updated_at")
    @classmethod
    def _validate_updated_at(cls, value: str) -> str:
        return _validate_full_timestamp(value)

    @field_validator("tags")
    @classmethod
    def _validate_tags(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for tag in value:
            candidate = str(tag).strip().lower().lstrip("#")
            if not candidate or candidate in seen:
                continue
            if len(candidate) > 50 or not _TAG_PATTERN.fullmatch(candidate):
                raise v2_schema_validation_error(f"invalid tag: {tag}")
            seen.add(candidate)
            normalized.append(candidate)
        return normalized


class ChatInteractionsV2EnvelopeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = SCHEMA_VERSION
    updated_at: str
    interactions: list[ChatInteractionV2Model] = Field(default_factory=list)

    @field_validator("updated_at")
    @classmethod
    def _validate_updated_at(cls, value: str) -> str:
        return _validate_full_timestamp(value)


# error_handling_exclude: validation API returns Pydantic errors as data.
def _validate_envelope(model_cls: type[BaseModel], data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validate ``data`` against a profile v2 envelope model and return JSON-safe output."""
    try:
        model = model_cls.model_validate(data)
        return model.model_dump(mode="json"), []
    except Exception as exc:
        return data, [str(exc)]


# error_handling_exclude: validation API returns errors as data.
def validate_account_v2_document(data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validate a v2 account.json envelope."""
    return _validate_envelope(AccountV2EnvelopeModel, data)


# error_handling_exclude: validation API returns Pydantic errors as data.
def validate_preferences_v2_document(data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validate a v2 preferences file envelope."""
    try:
        model = PreferencesV2EnvelopeModel.model_validate(data)
        return model.model_dump(mode="json", exclude_none=True), []
    except Exception as exc:
        return data, [str(exc)]


@handle_errors("validating schedules v2 document", default_return=({}, ["Validation failed"]))
def validate_schedules_v2_document(data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validate a v2 schedules.json envelope (``categories`` wrapper)."""
    return _validate_envelope(SchedulesV2EnvelopeModel, data)


@handle_errors("validating context v2 document", default_return=({}, ["Validation failed"]))
def validate_context_v2_document(data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validate a v2 user_context.json envelope."""
    return _validate_envelope(ContextV2EnvelopeModel, data)


@handle_errors("validating tags v2 document", default_return=({}, ["Validation failed"]))
def validate_tags_v2_document(data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validate a v2 tags.json envelope."""
    return _validate_envelope(TagsV2EnvelopeModel, data)


@handle_errors("validating chat interactions v2 document", default_return=({}, ["Validation failed"]))
def validate_chat_interactions_v2_document(data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validate a v2 chat_interactions.json envelope."""
    return _validate_envelope(ChatInteractionsV2EnvelopeModel, data)

