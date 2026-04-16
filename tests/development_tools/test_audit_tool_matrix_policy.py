"""V5 §7.21: audit tier matrix JSON stays aligned with audit_tiers + script registry."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from development_tools.shared.audit_tool_matrix import build_audit_tool_matrix

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_MATRIX_PATH = _PROJECT_ROOT / "development_tools" / "config" / "audit_tool_matrix.json"


@pytest.mark.unit
def test_audit_tool_matrix_json_matches_builder() -> None:
    """Checked-in matrix must match build_audit_tool_matrix() (regenerate via audit_tool_matrix builder)."""
    assert _MATRIX_PATH.is_file(), f"Missing {_MATRIX_PATH}"
    on_disk = json.loads(_MATRIX_PATH.read_text(encoding="utf-8"))
    built = build_audit_tool_matrix()
    assert on_disk == built


@pytest.mark.unit
def test_audit_tool_matrix_covers_tier3_static_group() -> None:
    """Tier 3 static analysis tools must appear in matrix with tier flags."""
    data = build_audit_tool_matrix()
    tools = data["audit_tools"]
    for name in ("analyze_ruff", "analyze_pyright", "analyze_bandit", "analyze_pip_audit"):
        assert name in tools
        assert tools[name]["in_tier3_full_repo_audit"] is True
        assert tools[name]["in_tier3_dev_tools_only_audit"] is True
