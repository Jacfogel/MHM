"""Central policy for deciding whether optional AI work may run."""

from enum import StrEnum

from core.ai_usage_settings import read_ai_usage_settings
from core.error_handling import handle_errors


class AIUsageMode(StrEnum):
    """Supported global AI execution modes."""

    AUTOMATIC = "automatic"
    MANUAL = "manual"
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
    """Read the current shared mode; invalid or unreadable policy returns OFF."""
    return AIUsageMode(_normalized_token(read_ai_usage_settings()["mode"]))


@handle_errors("reading disabled AI features", default_return=set())
def get_disabled_ai_features() -> set[str]:
    """Read disabled feature names without mutating saved settings.

    Errors return an empty set for diagnostics. This helper is not an execution
    authorization check; callers must use is_ai_usage_allowed, which fails closed.
    """
    return set(read_ai_usage_settings()["disabled_features"])


@handle_errors("checking the AI usage policy", default_return=False)
def is_ai_usage_allowed(
    feature: AIUsageFeature | str = AIUsageFeature.GENERIC,
    *,
    explicit_request: bool = False,
) -> bool:
    """Allow manual task breakdown only when its caller marks an explicit request.

    Authorization belongs to this invocation, never to conversation text or saved
    state. Global off and feature disables also apply to explicit requests.
    """
    settings = read_ai_usage_settings()
    mode = _normalized_token(settings["mode"])
    feature_name = _normalized_token(feature)
    if mode != AIUsageMode.AUTOMATIC.value and not (
        mode == AIUsageMode.MANUAL.value
        and explicit_request is True
        and feature_name == AIUsageFeature.TASK_BREAKDOWN.value
    ):
        return False
    return feature_name not in settings["disabled_features"]


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
    settings = read_ai_usage_settings()
    token = _normalized_token(settings["mode"])
    mode = next((item for item in AIUsageMode if item.value == token), AIUsageMode.OFF)
    disabled = sorted(settings["disabled_features"])
    return {
        "mode": mode.value,
        "automatic_calls_allowed": mode is AIUsageMode.AUTOMATIC,
        "disabled_features": disabled,
        "source": settings["source"],
    }

