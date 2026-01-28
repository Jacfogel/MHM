# TOOL_TIER: core

"""
Result format validation for development tools.

All tools are expected to output the standard format. This module validates
that assumption and raises if the format is violated.
"""

from typing import Dict, Any
from core.logger import get_component_logger

logger = get_component_logger("development_tools")


def normalize_to_standard_format(tool_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate tool result data is already in standard format.

    Standard format structure:
    {
        "summary": {
            "total_issues": int,
            "files_affected": int,
            "status": str (optional)
        },
        "details": dict (optional)
    }
    """
    if not isinstance(data, dict):
        raise ValueError(f"{tool_name} result must be a dict (got {type(data).__name__})")

    summary = data.get("summary")
    if not isinstance(summary, dict):
        raise ValueError(f"{tool_name} result missing 'summary' dict")

    if "total_issues" not in summary or "files_affected" not in summary:
        raise ValueError(
            f"{tool_name} result summary must include total_issues and files_affected"
        )

    return data
