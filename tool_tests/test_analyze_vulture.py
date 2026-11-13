"""Unit tests for analyze_vulture (V6 B-012)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from development_tools.static_checks import analyze_vulture as av_mod


@pytest.mark.unit
def test_parse_vulture_output_extracts_findings() -> None:
    text = (
        "core/foo.py:10: unused function 'bar' (80% confidence)\n"
        "ui/baz.py:2: unused variable 'x' (90% confidence)\n"
        "not a finding line\n"
    )
    findings = av_mod._parse_vulture_output(text)
    assert len(findings) == 2
    assert findings[0]["file"] == "core/foo.py"
    assert findings[0]["line"] == 10
    assert findings[0]["confidence"] == 80
    assert findings[1]["file"] == "ui/baz.py"


@pytest.mark.unit
def test_build_result_warns_when_findings() -> None:
    out = av_mod._build_result_from_findings(
        [{"file": "a.py", "line": 1, "message": "unused", "confidence": 80}],
        returncode=3,
        min_confidence=80,
    )
    assert out["summary"]["status"] == "WARN"
    assert out["summary"]["total_issues"] == 1
    assert out["details"]["tool_available"] is True


@pytest.mark.unit
def test_build_result_pass_when_clean() -> None:
    out = av_mod._build_result_from_findings([], returncode=0, min_confidence=80)
    assert out["summary"]["status"] == "PASS"
    assert out["summary"]["total_issues"] == 0


@pytest.mark.unit
def test_normalize_pattern_for_vulture_expands_bare_names() -> None:
    assert "*/.venv" in av_mod._normalize_pattern_for_vulture(".venv")
    assert "*/.venv/*" in av_mod._normalize_pattern_for_vulture(".venv")
    assert av_mod._normalize_pattern_for_vulture("*/generated/*") == ["*/generated/*"]
    assert av_mod._normalize_pattern_for_vulture("tests/data/") == [
        "tests/data",
        "tests/data/*",
        "*/tests/data",
        "*/tests/data/*",
    ]
    assert av_mod._normalize_pattern_for_vulture("x/{domain}/y") == []


@pytest.mark.unit
def test_run_vulture_unavailable_on_missing_command(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        av_mod.config,
        "get_static_analysis_config",
        lambda: {
            "vulture_command": ["python", "-m", "vulture"],
            "vulture_min_confidence": 80,
            "vulture_timeout_seconds": 30,
            "vulture_args": [],
            "vulture_scan_paths": ["core"],
        },
    )
    (tmp_path / "core").mkdir()
    with patch.object(av_mod.subprocess, "run", side_effect=FileNotFoundError):
        result = av_mod.run_vulture(tmp_path)
    assert result["details"]["tool_available"] is False
    assert result["summary"]["status"] == "WARN"


@pytest.mark.unit
def test_run_vulture_parses_subprocess_stdout(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        av_mod.config,
        "get_static_analysis_config",
        lambda: {
            "vulture_command": ["python", "-m", "vulture"],
            "vulture_min_confidence": 80,
            "vulture_timeout_seconds": 30,
            "vulture_args": [],
            "vulture_scan_paths": ["core"],
        },
    )
    monkeypatch.setattr(
        av_mod,
        "_collect_vulture_exclude_patterns",
        lambda: ["*/generated/*", "*/.venv/*"],
    )
    monkeypatch.setattr(av_mod, "_filter_excluded_findings", lambda findings: findings)
    (tmp_path / "core").mkdir()
    proc = MagicMock()
    proc.returncode = 3
    proc.stdout = "core/mod.py:5: unused function 'helper' (85% confidence)\n"
    proc.stderr = ""
    with patch.object(av_mod.subprocess, "run", return_value=proc) as run_mock:
        result = av_mod.run_vulture(tmp_path)
    assert result["summary"]["total_issues"] == 1
    assert result["summary"]["status"] == "WARN"
    assert result["details"]["tool_available"] is True
    assert "--min-confidence=80" in run_mock.call_args[0][0]
    cmd = run_mock.call_args[0][0]
    assert "--exclude" in cmd
    exclude_val = cmd[cmd.index("--exclude") + 1]
    assert "*/generated/*" in exclude_val
    assert "*/.venv/*" in exclude_val


@pytest.mark.unit
def test_merge_vulture_exclude_args_appends_shared_patterns() -> None:
    merged = av_mod._merge_vulture_exclude_args(
        ["--exclude", "*/vendor/*"],
        exclude_patterns=["*/generated/*", "*/tests/data/*"],
    )
    assert merged[0] == "--exclude"
    assert "*/vendor/*" in merged[1]
    assert "*/generated/*" in merged[1]
    assert "*/tests/data/*" in merged[1]


@pytest.mark.unit
def test_resolve_scan_paths_skips_excluded_roots(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "communication").mkdir()
    (tmp_path / "tests").mkdir()
    monkeypatch.setattr(
        av_mod.config,
        "get_scan_directories",
        lambda: ["communication", "tests"],
    )
    monkeypatch.setattr(
        av_mod,
        "should_exclude_file",
        lambda path, tool_type=None, context="development": str(path).startswith(
            "tests/"
        ),
    )
    paths = av_mod._resolve_scan_paths(tmp_path, {"vulture_scan_paths": []})
    assert paths == ["communication"]


@pytest.mark.unit
def test_resolve_scan_paths_uses_get_scan_directories(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "communication").mkdir()
    monkeypatch.setattr(
        av_mod.config,
        "get_scan_directories",
        lambda: ["communication"],
    )
    monkeypatch.setattr(av_mod, "_is_excluded_scan_root", lambda _name: False)
    paths = av_mod._resolve_scan_paths(tmp_path, {"vulture_scan_paths": []})
    assert paths == ["communication"]


@pytest.mark.unit
def test_filter_excluded_findings_uses_shared_exclusions(monkeypatch) -> None:
    monkeypatch.setattr(
        av_mod,
        "should_exclude_file",
        lambda path, tool_type=None, context="development": "generated" in str(path),
    )
    findings = [
        {"file": "ui/generated/foo.py", "line": 1, "message": "unused import", "confidence": 90},
        {"file": "core/bar.py", "line": 2, "message": "unused import", "confidence": 90},
    ]
    kept = av_mod._filter_excluded_findings(findings)
    assert len(kept) == 1
    assert kept[0]["file"] == "core/bar.py"
