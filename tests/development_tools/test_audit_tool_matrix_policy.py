"""V5 §7.21: audit tier matrix JSON stays aligned with audit_tiers + script registry."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from development_tools.shared.audit_tiers import get_tier2_groups
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


@pytest.mark.unit
def test_facade_shims_runs_in_tier2_groups_and_reports() -> None:
    """Facade/shims must be scheduled by Tier 2 and surfaced in status reports."""

    class _Service:
        dev_tools_only_mode = False

        def __getattr__(self, name: str):
            if name.startswith("run_"):
                return lambda: {"success": True}
            raise AttributeError(name)

    independent, dependent = get_tier2_groups(_Service())
    scheduled = [name for name, _runner in independent]
    scheduled.extend(name for group in dependent for name, _runner in group)

    assert "analyze_facade_shims" in scheduled

    hints = build_audit_tool_matrix()["audit_tools"]["analyze_facade_shims"][
        "report_surface_hints"
    ]
    assert "AI_PRIORITIES" in hints
    assert "AI_STATUS" in hints
    assert "CONSOLIDATED_REPORT" in hints
