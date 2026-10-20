"""Central policy for deciding whether optional AI work may run."""

from enum import StrEnum

from core import config
from core.error_handling import handle_errors


class AIUsageMode(StrEnum):
    """Supported global AI execution modes."""

    AUTOMATIC = "automatic"
    OFF = "off"


class AIUsageFeature(StrEnum):
    """Product features that may make a model request."""

    GENERIC = "generic"
    CONVERSATION = "conversation"
    COMMAND_INTERPRETATION = "command_interpretation"
    PERSONALIZED_MESSAGES = "personalized_messages"
    ACTION_PLANNING = "action_planning"
    RESPONSE_ENHANCEMENT = "response_enhancement"
    TASK_BREAKDOWN = "task_breakdown"
    TASK_EFFORT = "task_effort"


@handle_errors("normalizing an AI usage policy token", default_return="")
def _normalized_token(value: object) -> str:
    """Return a configuration token in its canonical comparison form."""
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


@handle_errors("reading the configured AI usage mode", default_return=AIUsageMode.OFF)
def get_ai_usage_mode() -> AIUsageMode:
    """Return the configured mode, failing closed for an invalid value."""
    return AIUsageMode(_normalized_token(config.AI_USAGE_MODE))


@handle_errors("reading disabled AI features", default_return=set())
def get_disabled_ai_features() -> set[str]:
    """Return normalized feature names disabled by configuration."""
    raw = str(config.AI_DISABLED_FEATURES or "")
    return {_normalized_token(part) for part in raw.split(",") if part.strip()}


@handle_errors("checking the AI usage policy", default_return=False)
def is_ai_usage_allowed(
    feature: AIUsageFeature | str = AIUsageFeature.GENERIC,
) -> bool:
    """Return whether an automatic model call is allowed for ``feature``."""
    if get_ai_usage_mode() is not AIUsageMode.AUTOMATIC:
        return False
    feature_name = _normalized_token(feature)
    return feature_name not in get_disabled_ai_features()


@handle_errors(
    "mapping an AI response mode to a usage feature",
    default_return=AIUsageFeature.CONVERSATION,
)
def usage_feature_for_response_mode(mode: str | None) -> AIUsageFeature:
    """Map chatbot response modes to cost-control feature names."""
    normalized = _normalized_token(mode)
    if normalized.startswith("command"):
        return AIUsageFeature.COMMAND_INTERPRETATION
    if normalized == "personalized":
        return AIUsageFeature.PERSONALIZED_MESSAGES
    if normalized == "response_enhancement":
        return AIUsageFeature.RESPONSE_ENHANCEMENT
    return AIUsageFeature.CONVERSATION


@handle_errors("building AI usage policy status", default_return={})
def get_ai_usage_policy_status() -> dict[str, object]:
    """Return non-secret policy state for status and diagnostics."""
    mode = get_ai_usage_mode()
    disabled = sorted(get_disabled_ai_features())
    return {
        "mode": mode.value,
        "automatic_calls_allowed": mode is AIUsageMode.AUTOMATIC,
        "disabled_features": disabled,
    }

