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

# Add logging support for schema validation
from core.logger import get_component_logger
from core.error_handling import handle_errors
logger = get_component_logger('main')


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
    @handle_errors("coercing boolean value", default_return="disabled")
    def _coerce_bool(cls, v: Any) -> Literal["enabled", "disabled"]:
        try:
            if isinstance(v, bool):
                return "enabled" if v else "disabled"
            if isinstance(v, str):
                vv = v.strip().lower()
                if vv in ("enabled", "enable", "true", "yes", "1"):
                    return "enabled"
                if vv in ("disabled", "disable", "false", "no", "0"):
                    return "disabled"
            return "disabled"
        except Exception as e:
            logger.error(f"Error coercing boolean value '{v}': {e}")
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
        if pattern.match(v):
            logger.debug(f"Email validation passed: {v}")
            return v
        else:
            logger.warning(f"Invalid email format provided: '{v}' - normalized to empty string")
            return ""

    @field_validator("discord_user_id")
    @classmethod
    def _validate_discord_id(cls, v: str) -> str:
        # Accept any non-empty string; tests and legacy data may use username#discriminator format
        if not v:
            return ""
        if isinstance(v, str):
            normalized = v.strip()
            if normalized != v:
                logger.debug(f"Discord ID normalized (whitespace trimmed): '{v}' -> '{normalized}'")
            return normalized
        else:
            logger.warning(f"Discord ID validation failed: expected string, got {type(v).__name__}: {v}")
            return ""

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
                logger.debug(f"Timezone validation passed: {vv}")
                return vv
        except Exception as e:
            logger.warning(f"Timezone validation error for '{vv}': {e}")
            pass
        # Unknown timezone → return empty to avoid misleading data
        logger.warning(f"Unknown timezone provided: '{vv}' - normalized to empty string")
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
                logger.error(f"Invalid categories provided: {invalid_categories}. Allowed categories: {allowed_categories}")
                raise ValueError(f"Invalid categories: {invalid_categories}. Allowed categories: {allowed_categories}")
            
            logger.debug(f"Categories validation passed: {v}")
            return v
        except ImportError:
            # If message_management is not available, allow all categories
            logger.warning("Message management module not available - allowing all categories without validation")
            return v
        except ValueError:
            # Re-raise ValueError (invalid categories) - don't catch this
            raise
        except Exception as e:
            # If there's any other error (like missing env vars), use default categories
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
        if not v:
            return "00:00"
        if _TIME_PATTERN.match(v):
            logger.debug(f"Time validation passed: {v}")
            return v
        else:
            logger.warning(f"Invalid time format provided: '{v}' - normalized to '00:00'")
            return "00:00"

    @field_validator("days")
    @classmethod
    def _valid_days(cls, v: List[str]) -> List[str]:
        if not v:
            return ["ALL"]
        filtered = [d for d in v if d in _VALID_DAYS]
        invalid_days = [d for d in v if d not in _VALID_DAYS]
        if invalid_days:
            logger.warning(f"Invalid days provided: {invalid_days} - filtered out. Valid days: {_VALID_DAYS}")
        if not filtered:
            logger.warning(f"No valid days provided, defaulting to ['ALL']")
            return ["ALL"]
        logger.debug(f"Days validation passed: {filtered}")
        return filtered


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

    @handle_errors("converting to dictionary")
    def to_dict(self) -> Dict[str, Any]:
        try:
            return {k: v.model_dump() for k, v in self.root.items()}
        except Exception as e:
            logger.error(f"Error converting to dictionary: {e}")
            return {}


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

@handle_errors("validating account dictionary")
def validate_account_dict(data: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    try:
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
    except Exception as e:
        logger.error(f"Error validating account dictionary: {e}")
        return data, [str(e)]


@handle_errors("validating preferences dictionary")
def validate_preferences_dict(data: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    try:
        errors: List[str] = []
        try:
            model = PreferencesModel.model_validate(data)
            # Exclude None so optional blocks like task_settings/checkin_settings vanish when absent
            return model.model_dump(exclude_none=True), errors
        except Exception as e:
            errors.append(str(e))
            # Return original data to avoid disruption
            return data, errors
    except Exception as e:
        logger.error(f"Error validating preferences dictionary: {e}")
        return data, [str(e)]


@handle_errors("validating schedules dictionary")
def validate_schedules_dict(data: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    try:
        errors: List[str] = []
        try:
            model = SchedulesModel.model_validate(data)
            return model.to_dict(), errors
        except Exception as e:
            errors.append(str(e))
            return data, errors
    except Exception as e:
        logger.error(f"Error validating schedules dictionary: {e}")
        return data, [str(e)]


@handle_errors("validating messages file dictionary")
def validate_messages_file_dict(data: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    try:
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
    except Exception as e:
        logger.error(f"Error validating messages file dictionary: {e}")
        return {"messages": []}, [str(e)]


