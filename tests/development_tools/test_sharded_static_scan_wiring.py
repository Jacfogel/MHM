"""§3.19.1 Phase 2: optional sharded Ruff/Bandit subprocess wiring (config-gated)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from development_tools import config as dt_config
from development_tools.static_checks import analyze_bandit as ab_mod
from development_tools.static_checks import analyze_ruff as ar_mod


@pytest.mark.unit
def test_static_analysis_defaults_enable_sharding() -> None:
    assert dt_config.STATIC_ANALYSIS["ruff_shard_scan"] is True
    assert dt_config.STATIC_ANALYSIS["bandit_shard_scan"] is True
    assert len(dt_config.STATIC_ANALYSIS["ruff_path_shards"]) >= 1


@pytest.mark.unit
def test_run_ruff_single_subprocess_when_sharding_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def _capture(
        project_root: Path,
        command: list[str],
        args: list[str],
        timeout_seconds: int,
    ):
        calls.append(args)
        return (
            0,
            [{"filename": "a.py", "code": "E1", "location": {"row": 1, "column": 0}}],
            "",
        )

    monkeypatch.setattr(ar_mod, "_run_ruff_subprocess_for_json_list", _capture)
    base = dict(dt_config.STATIC_ANALYSIS)
    base["ruff_shard_scan"] = False
    monkeypatch.setattr(ar_mod.config, "get_static_analysis_config", lambda: base.copy())

    out = ar_mod.run_ruff(tmp_path)
    assert len(calls) == 1
    assert "check" in calls[0] and "." in calls[0]
    assert out["summary"]["total_issues"] == 1


@pytest.mark.unit
def test_run_ruff_merges_shard_subprocesses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def _capture(
        project_root: Path,
        command: list[str],
        args: list[str],
        timeout_seconds: int,
    ):
        calls.append(args)
        n = len(calls)
        if n == 1:
            pl = [{"filename": "a.py", "code": "F401", "location": {"row": 1, "column": 0}}]
        else:
            pl = [{"filename": "b.py", "code": "E501", "location": {"row": 2, "column": 0}}]
        return 1, pl, ""

    monkeypatch.setattr(ar_mod, "_run_ruff_subprocess_for_json_list", _capture)
    (tmp_path / "core").mkdir()
    (tmp_path / "ui").mkdir()
    base = dict(dt_config.STATIC_ANALYSIS)
    base["ruff_shard_scan"] = True
    base["ruff_path_shards"] = [["core"], ["ui"]]
    monkeypatch.setattr(ar_mod.config, "get_static_analysis_config", lambda: base.copy())

    out = ar_mod.run_ruff(tmp_path)
    assert len(calls) == 2
    assert out["summary"]["total_issues"] == 2
    assert out["summary"]["files_affected"] == 2


@pytest.mark.unit
def test_run_bandit_merges_when_shard_scan_enabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def _capture(
        project_root: Path,
        command: list[str],
        args: list[str],
        timeout_seconds: int,
    ):
        calls.append(args)
        n = len(calls)
        issue = {
            "filename": f"{n}.py",
            "line_number": n,
            "issue_severity": "HIGH",
            "test_id": "B101",
        }
        return 1, {"results": [issue]}, ""

    monkeypatch.setattr(ab_mod, "_run_bandit_subprocess_for_json", _capture)
    (tmp_path / "core").mkdir()
    (tmp_path / "ui").mkdir()
    base = dict(dt_config.STATIC_ANALYSIS)
    base["bandit_shard_scan"] = True
    base["bandit_scan_roots"] = ["core", "ui"]
    base["bandit_root_python"] = []
    monkeypatch.setattr(ab_mod.config, "get_static_analysis_config", lambda: base.copy())

    out = ab_mod.run_bandit(tmp_path)
    assert len(calls) == 2
    assert "-r" in calls[0] and "core" in calls[0]
    assert out["summary"]["total_issues"] == 2


@pytest.mark.unit
def test_run_bandit_single_call_when_shard_disabled_or_one_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock = MagicMock(
        return_value=(
            0,
            {"results": []},
            "",
        )
    )
    monkeypatch.setattr(ab_mod, "_run_bandit_subprocess_for_json", mock)
    (tmp_path / "only").mkdir()
    base = dict(dt_config.STATIC_ANALYSIS)
    base["bandit_shard_scan"] = True
    base["bandit_scan_roots"] = ["only"]
    base["bandit_root_python"] = []
    monkeypatch.setattr(ab_mod.config, "get_static_analysis_config", lambda: base.copy())

    ab_mod.run_bandit(tmp_path)
    assert mock.call_count == 1

    mock.reset_mock()
    base["bandit_shard_scan"] = False
    base["bandit_scan_roots"] = ["only", "missing_dir_xyz"]
    monkeypatch.setattr(ab_mod.config, "get_static_analysis_config", lambda: base.copy())
    # only one existing dir → path_args length 1 → single subprocess
    ab_mod.run_bandit(tmp_path)
    assert mock.call_count == 1
