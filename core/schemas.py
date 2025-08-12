"""
Pydantic models and helpers for user data: account, preferences, schedules, and messages.

Design goals:
- Be tolerant of existing on-disk shapes (no breaking changes).
- Normalize when safe; log validation issues but do not raise by default.
- Keep string-based timestamps and enumerations used by current JSON files.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator, RootModel
import re


# ----------------------------- Common Validators -----------------------------

_TIME_PATTERN = re.compile(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
_VALID_DAYS = {
    "ALL", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
}


# --------------------------------- Account ----------------------------------

class FeaturesModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    automated_messages: Literal["enabled", "disabled"] = "disabled"
    checkins: Literal["enabled", "disabled"] = "disabled"
    task_management: Literal["enabled", "disabled"] = "disabled"

    @classmethod
    def _coerce_bool(cls, v: Any) -> Literal["enabled", "disabled"]:
        if isinstance(v, bool):
            return "enabled" if v else "disabled"
        if isinstance(v, str):
            vv = v.strip().lower()
            if vv in ("enabled", "enable", "true", "yes", "1"):
                return "enabled"
            if vv in ("disabled", "disable", "false", "no", "0"):
                return "disabled"
        return "disabled"

    @field_validator("automated_messages", "checkins", "task_management", mode="before")
    @classmethod
    def _normalize_flags(cls, v: Any) -> Literal["enabled", "disabled"]:
        return cls._coerce_bool(v)


class AccountModel(BaseModel):
    # Allow unknown fields (e.g., legacy/pass-through like 'channel', 'enabled_features')
    model_config = ConfigDict(extra="allow")

    user_id: str
    internal_username: str = ""
    account_status: Literal["active", "inactive", "suspended"] = "active"

    chat_id: str = ""
    phone: str = ""
    email: str = ""
    discord_user_id: str = ""
    timezone: str = ""

    created_at: str = ""
    updated_at: str = ""

    features: FeaturesModel = Field(default_factory=FeaturesModel)

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: str) -> str:
        if not v:
            return v
        pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        return v if pattern.match(v) else ""


# -------------------------------- Preferences --------------------------------

class ChannelModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["email", "discord"]
    contact: Optional[str] = None


class PreferencesModel(BaseModel):
    # Allow unknown top-level fields so tests expecting passthrough extras succeed
    model_config = ConfigDict(extra="allow")

    categories: List[str] = Field(default_factory=list)
    channel: ChannelModel = Field(default_factory=lambda: ChannelModel(type="email", contact=None))
    checkin_settings: Dict[str, Any] | None = None
    task_settings: Dict[str, Any] | None = None


# --------------------------------- Schedules ---------------------------------

class PeriodModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    active: bool = True
    days: List[str] = Field(default_factory=lambda: ["ALL"])
    start_time: str = "00:00"
    end_time: str = "23:59"

    @field_validator("start_time", "end_time")
    @classmethod
    def _valid_time(cls, v: str) -> str:
        return v if _TIME_PATTERN.match(v or "") else "00:00"

    @field_validator("days")
    @classmethod
    def _valid_days(cls, v: List[str]) -> List[str]:
        if not v:
            return ["ALL"]
        filtered = [d for d in v if d in _VALID_DAYS]
        return filtered or ["ALL"]


class CategoryScheduleModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    periods: Dict[str, PeriodModel]

    @model_validator(mode="before")
    @classmethod
    def _accept_legacy_shape(cls, data: Any):
        # Accept legacy shape where periods are at top-level without 'periods' key
        if isinstance(data, dict) and "periods" not in data:
            return {"periods": data}
        return data


class SchedulesModel(RootModel[Dict[str, CategoryScheduleModel]]):
    # RootModel does not support extra config; rely on inner models' tolerance
    pass

    def to_dict(self) -> Dict[str, Any]:
        return {k: v.model_dump() for k, v in self.root.items()}


# --------------------------------- Messages ----------------------------------

class MessageModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message_id: str
    message: str
    days: List[str] = Field(default_factory=lambda: ["ALL"])
    time_periods: List[str] = Field(default_factory=lambda: ["ALL"])
    timestamp: Optional[str] = None

    @field_validator("days")
    @classmethod
    def _normalize_days(cls, v: List[str]) -> List[str]:
        if not v:
            return ["ALL"]
        return v

    @field_validator("time_periods")
    @classmethod
    def _normalize_periods(cls, v: List[str]) -> List[str]:
        if not v:
            return ["ALL"]
        return v


class MessagesFileModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    messages: List[MessageModel] = Field(default_factory=list)


# ------------------------------ Helper functions -----------------------------

def validate_account_dict(data: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    errors: List[str] = []
    try:
        model = AccountModel.model_validate(data)
        return model.model_dump(), errors
    except Exception as e:
        errors.append(str(e))
        # Best effort normalization: coerce features
        fixed = data.copy()
        feats = fixed.get("features") or {}
        for k in ("automated_messages", "checkins", "task_management"):
            v = feats.get(k)
            feats[k] = FeaturesModel._coerce_bool(v)
        fixed["features"] = feats
        return fixed, errors


def validate_preferences_dict(data: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    errors: List[str] = []
    try:
        model = PreferencesModel.model_validate(data)
        # Exclude None so optional blocks like task_settings/checkin_settings vanish when absent
        return model.model_dump(exclude_none=True), errors
    except Exception as e:
        errors.append(str(e))
        # Return original data to avoid disruption
        return data, errors


def validate_schedules_dict(data: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    errors: List[str] = []
    try:
        model = SchedulesModel.model_validate(data)
        return model.to_dict(), errors
    except Exception as e:
        errors.append(str(e))
        return data, errors


def validate_messages_file_dict(data: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    errors: List[str] = []
    try:
        model = MessagesFileModel.model_validate(data)
        return model.model_dump(), errors
    except Exception as e:
        errors.append(str(e))
        # Try to coerce to messages list
        msgs = data.get("messages")
        if isinstance(msgs, list):
            normalized: List[Dict[str, Any]] = []
            for item in msgs:
                try:
                    mi = MessageModel.model_validate(item)
                    normalized.append(mi.model_dump())
                except Exception:
                    # skip bad rows
                    continue
            return {"messages": normalized}, errors
        return {"messages": []}, errors


