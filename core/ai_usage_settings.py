"""Installation-wide AI controls shared by the desktop admin and service."""

from core.ai_usage_configuration import (
    AI_SETTINGS_FILE,
    AI_FEATURE_LABELS,
    UNREADABLE_AI_SETTINGS,
    read_ai_usage_override,
)
from core.error_handling import ValidationError, handle_errors
from storage.runtime_state_storage import save_runtime_state_json


@handle_errors("reading environment AI controls", default_return=UNREADABLE_AI_SETTINGS)
def environment_ai_usage_settings() -> dict:
    """Return the operational environment defaults without changing them."""
    from core import config

    return {
        "mode": str(config.AI_USAGE_MODE).strip().lower(),
        "disabled_features": sorted(
            {
                part.strip().lower().replace("-", "_").replace(" ", "_")
                for part in str(config.AI_DISABLED_FEATURES or "").split(",")
                if part.strip()
            }
        ),
        "source": "environment",
    }


@handle_errors("reading desktop AI controls", default_return=UNREADABLE_AI_SETTINGS)
def read_ai_usage_settings() -> dict:
    """Read one fresh policy snapshot; unreadable saved controls disable AI.

    Atomic shared storage makes subsequent calls in separate desktop/service
    processes observe saved changes without restarting or mutating environment.
    """
    from core import config

    override = read_ai_usage_override(config.BASE_DATA_DIR)
    return override if override is not None else environment_ai_usage_settings()


@handle_errors("saving desktop AI controls", default_return=False)
def save_ai_usage_settings(
    mode: str, disabled_features: list[str], *, use_environment: bool = False
) -> bool:
    """Validate and atomically persist installation-wide administrator choices."""
    if type(use_environment) is not bool:
        raise ValidationError("Choose whether to use environment defaults")
    if use_environment:
        return save_runtime_state_json(
            AI_SETTINGS_FILE, {"schema_version": 1, "use_environment": True}
        )
    if (
        mode not in ("automatic", "off")
        or not isinstance(disabled_features, list)
        or any(
            not isinstance(item, str) or item not in AI_FEATURE_LABELS
            for item in disabled_features
        )
    ):
        raise ValidationError("Choose a valid AI mode and supported features")
    return save_runtime_state_json(
        AI_SETTINGS_FILE,
        {
            "schema_version": 1,
            "use_environment": False,
            "mode": mode,
            "disabled_features": sorted(set(disabled_features)),
        },
    )
