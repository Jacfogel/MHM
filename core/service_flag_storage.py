"""JSON read/write helpers for service request and response ``.flag`` files."""

from pathlib import Path
from typing import Any

import contextlib
import json

from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("main")

try:
    from core.file_auditor import record_created as _record_created
except Exception:
    _record_created = None


@handle_errors("reading service flag JSON", default_return={})
def read_service_flag_json(
    flag_file: str | Path, default_data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Read a JSON service flag file and return a dict payload."""
    try:
        with open(flag_file, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Could not read service flag JSON {flag_file}: {e}")
        return dict(default_data or {})
    return data if isinstance(data, dict) else dict(default_data or {})


@handle_errors("writing service flag JSON", default_return=False)
def write_service_flag_json(
    flag_file: str | Path,
    data: dict[str, Any],
    *,
    indent: int | None = 2,
    audit_reason: str | None = None,
    audit_extra: dict[str, Any] | None = None,
) -> bool:
    """Write a JSON service flag file and optionally record file-auditor metadata."""
    flag_path = Path(flag_file)
    flag_path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(flag_path), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)

    if audit_reason and _record_created:
        with contextlib.suppress(Exception):
            _record_created(str(flag_path), reason=audit_reason, extra=audit_extra)
    return True
