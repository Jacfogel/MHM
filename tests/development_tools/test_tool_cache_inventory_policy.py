"""V5 §3.19: tool cache inventory JSON matches builder."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from development_tools.shared.audit_tiers import get_expected_tools_for_tier
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


@pytest.mark.unit
def test_tool_cache_inventory_covers_tier2_and_tier3_tools() -> None:
    """V5 §3.19: every Tier 2 / Tier 3 audit tool has an inventory row."""
    tier1_no_quick = {
        t for t in get_expected_tools_for_tier(1) if t != "quick_status"
    }
    expected = set(get_expected_tools_for_tier(3, dev_tools_only=False)) - tier1_no_quick
    names = {e["tool"] for e in build_tool_cache_inventory()["entries"]}
    assert expected <= names, f"missing: {sorted(expected - names)}"


@pytest.mark.unit
def test_static_analysis_tools_use_shard_fragment_cache() -> None:
    """Ruff, Pyright, Bandit use per-shard fragment caches in analyze_* scripts."""
    by_tool = {e["tool"]: e for e in build_tool_cache_inventory()["entries"]}
    for name in ("analyze_pyright", "analyze_ruff", "analyze_bandit"):
        assert by_tool[name]["strategy"] == "shard_fragment_json_cache"
