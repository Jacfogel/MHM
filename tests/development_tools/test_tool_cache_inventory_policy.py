"""V5 §3.19: tool cache inventory JSON matches builder."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from development_tools.shared.tool_cache_inventory import build_tool_cache_inventory

_ROOT = Path(__file__).resolve().parents[2]
_PATH = _ROOT / "development_tools" / "config" / "tool_cache_inventory.json"


@pytest.mark.unit
def test_tool_cache_inventory_json_matches_builder() -> None:
    assert _PATH.is_file()
    assert json.loads(_PATH.read_text(encoding="utf-8")) == build_tool_cache_inventory()


@pytest.mark.unit
def test_tool_cache_inventory_lists_pip_audit_and_static_checks() -> None:
    data = build_tool_cache_inventory()
    names = {e["tool"] for e in data["entries"]}
    assert "analyze_pip_audit" in names
    assert "analyze_pyright" in names
    assert "analyze_bandit" in names
