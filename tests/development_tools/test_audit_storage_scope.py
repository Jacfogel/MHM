"""Tests for audit-scoped tool result / cache storage paths."""

from __future__ import annotations

import json

import pytest

from tests.development_tools.conftest import load_development_tools_module

output_storage = load_development_tools_module("shared.output_storage")
scope_mod = load_development_tools_module("shared.audit_storage_scope")


@pytest.mark.unit
def test_jsons_dir_for_scope_full_vs_dev_tools(tmp_path):
    root = tmp_path
    full_d = scope_mod.jsons_dir_for_scope(root, "docs", audit_scope=scope_mod.STORAGE_SCOPE_FULL)
    assert full_d == root / "development_tools" / "docs" / "jsons" / "scopes" / "full"
    scoped = scope_mod.jsons_dir_for_scope(
        root, "docs", audit_scope=scope_mod.STORAGE_SCOPE_DEV_TOOLS
    )
    assert scoped == root / "development_tools" / "docs" / "jsons" / "scopes" / "dev_tools"


@pytest.mark.unit
def test_scoped_analysis_and_timings_paths(tmp_path):
    root = tmp_path
    cfg = "development_tools/reports/analysis_detailed_results.json"
    full_p = scope_mod.scoped_analysis_detailed_path(
        root, configured_relative=cfg, audit_scope=scope_mod.STORAGE_SCOPE_FULL
    )
    assert "scopes" in full_p.parts and "full" in full_p.parts
    dev_p = scope_mod.scoped_analysis_detailed_path(
        root, configured_relative=cfg, audit_scope=scope_mod.STORAGE_SCOPE_DEV_TOOLS
    )
    assert "scopes" in dev_p.parts and "dev_tools" in dev_p.parts

    t_full = scope_mod.scoped_tool_timings_path(root, audit_scope=scope_mod.STORAGE_SCOPE_FULL)
    assert "scopes" in t_full.parts and t_full.name == "tool_timings.json"
    t_dev = scope_mod.scoped_tool_timings_path(
        root, audit_scope=scope_mod.STORAGE_SCOPE_DEV_TOOLS
    )
    assert "scopes" in t_dev.parts and "dev_tools" in t_dev.parts


@pytest.mark.unit
def test_save_and_get_tool_results_under_dev_tools_scope(tmp_path):
    out = output_storage.save_tool_result(
        "scoped_tool",
        domain="docs",
        data={"k": 1},
        project_root=tmp_path,
        audit_scope=scope_mod.STORAGE_SCOPE_DEV_TOOLS,
    )
    rel = str(out.relative_to(tmp_path)).replace("\\", "/")
    assert "/jsons/scopes/dev_tools/scoped_tool_results.json" in rel

    loaded = output_storage.load_tool_result(
        "scoped_tool",
        domain="docs",
        project_root=tmp_path,
        audit_scope=scope_mod.STORAGE_SCOPE_DEV_TOOLS,
        normalize=False,
    )
    assert loaded is not None
    assert loaded.get("k") == 1

    agg = output_storage.get_all_tool_results(
        project_root=tmp_path, audit_scope=scope_mod.STORAGE_SCOPE_DEV_TOOLS
    )
    assert "scoped_tool" in agg


@pytest.mark.unit
def test_get_all_tool_results_full_reads_scoped_only(tmp_path):
    """Full scope loads only ``jsons/scopes/full`` (flat jsons/ no longer scanned)."""
    docs_flat = tmp_path / "development_tools" / "docs" / "jsons"
    docs_scoped = docs_flat / "scopes" / "full"
    docs_scoped.mkdir(parents=True, exist_ok=True)
    docs_flat.mkdir(parents=True, exist_ok=True)

    (docs_scoped / "from_scoped_results.json").write_text(
        json.dumps({"timestamp": "2026-03-31T12:00:00", "data": {"which": "scoped"}}),
        encoding="utf-8",
    )
    (docs_flat / "from_legacy_only_results.json").write_text(
        json.dumps({"timestamp": "2026-03-31T11:00:00", "data": {"which": "legacy"}}),
        encoding="utf-8",
    )

    full = output_storage.get_all_tool_results(
        project_root=tmp_path, audit_scope=scope_mod.STORAGE_SCOPE_FULL
    )
    assert full["from_scoped"]["data"]["which"] == "scoped"
    assert "from_legacy_only" not in full

    only_scoped = output_storage.get_all_tool_results(
        project_root=tmp_path, audit_scope=scope_mod.STORAGE_SCOPE_DEV_TOOLS
    )
    assert "from_scoped" not in only_scoped


@pytest.mark.unit
def test_get_all_tool_results_uses_scoped_file_for_tool(tmp_path):
    docs_flat = tmp_path / "development_tools" / "docs" / "jsons"
    scoped = docs_flat / "scopes" / "full"
    scoped.mkdir(parents=True, exist_ok=True)
    docs_flat.mkdir(parents=True, exist_ok=True)
    (scoped / "same_tool_results.json").write_text(
        json.dumps({"timestamp": "2026-02-26T10:00:00", "data": {"source": "scoped"}}),
        encoding="utf-8",
    )
    (docs_flat / "same_tool_results.json").write_text(
        json.dumps({"timestamp": "2026-02-25T10:00:00", "data": {"source": "flat_only"}}),
        encoding="utf-8",
    )
    results = output_storage.get_all_tool_results(
        project_root=tmp_path, audit_scope=scope_mod.STORAGE_SCOPE_FULL
    )
    assert results["same_tool"]["data"]["source"] == "scoped"
