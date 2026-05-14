"""
Storage helpers for app-level runtime JSON state under BASE_DATA_DIR.

These files are mutable runtime state shared across communication flows, but they
are not per-user profile documents. Keep path resolution and JSON I/O centralized
here so callers do not open runtime JSON files directly.
"""

from copy import deepcopy
from pathlib import Path
from typing import Any

import core.config
from core.error_handling import handle_errors
from core.file_operations import load_json_data, save_json_data
from core.logger import get_component_logger

logger = get_component_logger("file_ops")


# devtools: ignore[facade-shims]: primary runtime-state path helper, not a compatibility shim
@handle_errors("resolving runtime state path", re_raise=True)
def get_runtime_state_path(
    file_name_or_path: str | Path, base_dir: str | Path | None = None
) -> Path:
    """
    Resolve a runtime-state JSON path.

    Plain filenames are placed under BASE_DATA_DIR. Explicit paths are accepted
    for tests and callers that isolate a specific file.
    """
    path = Path(file_name_or_path)
    if path.is_absolute() or path.parent != Path("."):
        return path

    root = Path(base_dir) if base_dir is not None else Path(core.config.BASE_DATA_DIR)
    return root / path


@handle_errors("copying runtime state default", default_return={})
def _fresh_default(default_data: dict[str, Any] | None) -> dict[str, Any]:
    """Return an independent default dict for callers that mutate loaded state."""
    return deepcopy(default_data) if default_data is not None else {}


@handle_errors("loading runtime state JSON", default_return={})
def load_runtime_state_json(
    file_name_or_path: str | Path,
    *,
    default_data: dict[str, Any] | None = None,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Load a runtime-state JSON dict through the centralized JSON helper."""
    path = get_runtime_state_path(file_name_or_path, base_dir=base_dir)
    if not path.exists():
        return _fresh_default(default_data)

    data = load_json_data(str(path))
    if not isinstance(data, dict):
        logger.warning(
            f"Runtime state file did not contain a JSON object; using defaults: {path}"
        )
        return _fresh_default(default_data)

    if data.get("file_type") == "generic_json" and "data" in data:
        logger.warning(
            f"Runtime state file was recovered with a generic JSON payload; using defaults: {path}"
        )
        return _fresh_default(default_data)

    return data


@handle_errors("saving runtime state JSON", default_return=False)
def save_runtime_state_json(
    file_name_or_path: str | Path,
    data: dict[str, Any],
    *,
    base_dir: str | Path | None = None,
) -> bool:
    """Save a runtime-state JSON dict through the centralized JSON helper."""
    path = get_runtime_state_path(file_name_or_path, base_dir=base_dir)
    return save_json_data(data, str(path))
