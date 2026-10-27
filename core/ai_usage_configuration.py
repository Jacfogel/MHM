"""Dependency-light schema and reader for administrator AI configuration.

This configuration reader deliberately avoids runtime storage and core.config
imports so startup validation can inspect the saved policy without a cycle.
"""

import json
from pathlib import Path

from core.error_handling import DataError, handle_errors

AI_SETTINGS_FILE = "ai_usage_settings.json"
AI_FEATURE_LABELS = {
    "conversation": "Conversation and reflection",
    "command_interpretation": "Natural-language command interpretation",
    "personalized_messages": "Personalized messages",
    "action_planning": "Action planning",
    "response_enhancement": "Response enhancement",
    "task_breakdown": "Task breakdown (Simplify)",
    "task_effort": "Task effort estimates",
}
UNREADABLE_AI_SETTINGS = {"mode": "off", "disabled_features": [], "source": "invalid"}


@handle_errors(
    "reading desktop AI configuration", default_return=UNREADABLE_AI_SETTINGS
)
def read_ai_usage_override(base_dir: str | Path) -> dict | None:
    """Read an admin override, return None for environment defaults, or fail closed."""
    path = Path(base_dir) / AI_SETTINGS_FILE
    if not path.exists():
        return None
    saved = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(saved, dict)
        or type(saved.get("schema_version")) is not int
        or saved.get("schema_version") != 1
        or type(saved.get("use_environment")) is not bool
    ):
        raise DataError("Desktop AI controls have an invalid schema")
    if saved["use_environment"]:
        return None
    mode = saved.get("mode")
    disabled = saved.get("disabled_features")
    if (
        mode not in ("automatic", "off")
        or not isinstance(disabled, list)
        or any(
            not isinstance(item, str) or item not in AI_FEATURE_LABELS
            for item in disabled
        )
    ):
        raise DataError("Desktop AI controls contain invalid policy values")
    return {
        "mode": mode,
        "disabled_features": sorted(set(disabled)),
        "source": "desktop",
    }
