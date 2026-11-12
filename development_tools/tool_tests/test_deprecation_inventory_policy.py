"""Structural checks for development_tools/config/jsons/DEPRECATION_INVENTORY.json (V5 §5.6)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.mark.unit
def test_deprecation_inventory_loads_and_root_ruff_bridge_active() -> None:
    path = project_root / "development_tools" / "config" / "jsons" / "DEPRECATION_INVENTORY.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    active = data.get("active_or_candidate_inventory", [])
    assert isinstance(active, list) and len(active) >= 1
    ids = {x.get("id") for x in active if isinstance(x, dict)}
    assert "root_ruff_compat_mirror" in ids
    bridge = next(x for x in active if x.get("id") == "root_ruff_compat_mirror")
    assert bridge.get("status") == "active_bridge"
    assert isinstance(bridge.get("exit_criteria"), str) and bridge["exit_criteria"].strip()
    removed = data.get("removed_inventory", [])
    assert isinstance(removed, list)

