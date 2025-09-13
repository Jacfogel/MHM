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
try:
    import pytz  # Best-effort timezone validation
except Exception:
    pytz = None


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

    @field_validator("discord_user_id")
    @classmethod
    def _validate_discord_id(cls, v: str) -> str:
        # Accept any non-empty string; tests and legacy data may use username#discriminator format
        if not v:
            return ""
        return v.strip() if isinstance(v, str) else ""

    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, v: str) -> str:
        # Best-effort: keep empty if invalid; tolerate unknowns
        if not v or not isinstance(v, str):
            return ""
        vv = v.strip()
        if not vv:
            return ""
        try:
            if pytz and vv in pytz.all_timezones:
                return vv
        except Exception:
            pass
        # Unknown timezone → return empty to avoid misleading data
        return ""


# -------------------------------- Preferences --------------------------------

class ChannelModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["email", "discord"]
    contact: Optional[str] = None

    @model_validator(mode="after")
    def _normalize_contact(self):
        # If contact is missing, leave as None. If present, lightly normalize.
        if self.contact is None:
            return self
        try:
            if isinstance(self.contact, str):
                self.contact = self.contact.strip()
            if self.type == "email":
                pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
                # If invalid, keep as-is for backward compatibility (tests may set placeholders)
                # Future: optionally warn rather than drop
            elif self.type == "discord":
                # Accept any non-empty string, including username#discriminator or IDs
                if not (isinstance(self.contact, str) and self.contact):
                    self.contact = None
        except Exception:
            # On any failure, keep original contact to avoid data loss
            pass
        return self


class PreferencesModel(BaseModel):
    # Allow unknown top-level fields so tests expecting passthrough extras succeed
    model_config = ConfigDict(extra="allow")

    categories: List[str] = Field(default_factory=list)
    channel: ChannelModel = Field(default_factory=lambda: ChannelModel(type="email", contact=None))
    checkin_settings: Dict[str, Any] | None = None
    task_settings: Dict[str, Any] | None = None

    @field_validator("categories")
    @classmethod
    def _validate_categories(cls, v: List[str]) -> List[str]:
        """Validate that all categories are in the allowed list."""
        if not v:
            return v
        
        try:
            from core.message_management import get_message_categories
            allowed_categories = get_message_categories()
            invalid_categories = [c for c in v if c not in allowed_categories]
            
            if invalid_categories:
                raise ValueError(f"Invalid categories: {invalid_categories}. Allowed categories: {allowed_categories}")
            
            return v
        except ImportError:
            # If message_management is not available, allow all categories
            return v
        except ValueError:
            # Re-raise ValueError (invalid categories) - don't catch this
            raise
        except Exception as e:
            # If there's any other error (like missing env vars), use default categories
            from core.logger import get_component_logger
            logger = get_component_logger('main')
            logger.warning(f"Category validation error: {e}, using default categories")
            
            # Default categories that should always be valid
            default_categories = ['motivational', 'health', 'fun_facts', 'quotes_to_ponder', 'word_of_the_day']
            invalid_categories = [c for c in v if c not in default_categories]
            
            if invalid_categories:
                raise ValueError(f"Invalid categories: {invalid_categories}. Allowed categories: {default_categories}")
            
            return v


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


