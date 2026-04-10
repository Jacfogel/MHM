"""Policy reminders for V5 §7.7 directory taxonomy Phase 2 gate (documentation lock-in)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.mark.unit
def test_v5_records_phase2_gate_before_config_moves() -> None:
    """Any Phase 2 move must cite quick audit + import-boundary tooling (V5 §7.7)."""
    v5 = (project_root / "development_tools" / "AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md").read_text(
        encoding="utf-8"
    )
    assert "audit --quick" in v5
    assert "analyze_dev_tools_import_boundaries" in v5
    assert "import-boundary" in v5.lower() or "import boundary" in v5.lower()
