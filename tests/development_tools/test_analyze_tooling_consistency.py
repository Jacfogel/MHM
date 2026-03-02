"""Tests for development_tools/config/analyze_tooling_consistency.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module


tooling_module = load_development_tools_module("config.analyze_tooling_consistency")


@pytest.mark.unit
def test_detects_missing_required_alias_pair(monkeypatch):
    monkeypatch.setattr(
        tooling_module,
        "_build_command_flag_inventory",
        lambda: {
            "audit": ["--full"],
            "cleanup": ["--full", "--all"],
            "doc-fix": ["--all", "--full"],
        },
        raising=True,
    )
    monkeypatch.setattr(
        tooling_module,
        "_build_global_flag_inventory",
        lambda _root: ["--clear-cache", "--cache-clear"],
        raising=True,
    )
    monkeypatch.setattr(
        tooling_module,
        "_build_standalone_argparse_inventory",
        lambda _root: {},
        raising=True,
    )
    monkeypatch.setattr(
        tooling_module,
        "_check_exclusion_consistency",
        lambda _root: (
            {
                "scanner_candidates": 0,
                "compliant_scanners": 0,
                "non_compliant_scanners": 0,
                "non_compliant_files": [],
            },
            [],
        ),
        raising=True,
    )

    result = tooling_module.analyze_tooling_consistency(Path("."))
    issue_ids = {issue["id"] for issue in result["details"]["issues"]}

    assert "audit_full_alias_command" in issue_ids


@pytest.mark.unit
def test_detects_scanner_missing_exclusion_filtering(tmp_path):
    project_root = tmp_path
    tools_root = project_root / "development_tools"
    (tools_root / "shared").mkdir(parents=True, exist_ok=True)

    (tools_root / "run_development_tools.py").write_text(
        "def main():\n    pass\n",
        encoding="utf-8",
    )
    (tools_root / "shared" / "cli_interface.py").write_text(
        'def _full_audit_command(argv):\n    return _audit_command(["--full", *argv])\n',
        encoding="utf-8",
    )
    (tools_root / "scanner_without_exclusion.py").write_text(
        "from pathlib import Path\n"
        "def scan(root):\n"
        "    for path in Path(root).rglob('*.py'):\n"
        "        collected = path\n",
        encoding="utf-8",
    )

    summary, issues = tooling_module._check_exclusion_consistency(project_root)

    assert summary["non_compliant_scanners"] >= 1
    assert any(
        issue["file"].endswith("scanner_without_exclusion.py") for issue in issues
    )


@pytest.mark.unit
def test_passes_when_alias_and_exclusions_are_compliant(monkeypatch):
    monkeypatch.setattr(
        tooling_module,
        "_build_command_flag_inventory",
        lambda: {
            "audit": ["--full"],
            "full-audit": [],
            "cleanup": ["--full", "--all"],
            "doc-fix": ["--all", "--full"],
        },
        raising=True,
    )
    monkeypatch.setattr(
        tooling_module,
        "_build_global_flag_inventory",
        lambda _root: ["--clear-cache", "--cache-clear"],
        raising=True,
    )
    monkeypatch.setattr(
        tooling_module,
        "_build_standalone_argparse_inventory",
        lambda _root: {"development_tools/config/analyze_config.py": ["--json"]},
        raising=True,
    )
    monkeypatch.setattr(
        tooling_module,
        "_check_alias_rules",
        lambda *_args, **_kwargs: (
            [
                {
                    "id": "dummy",
                    "description": "dummy",
                    "passed": True,
                    "target": "development_tools/shared/cli_interface.py",
                }
            ],
            [],
        ),
        raising=True,
    )
    monkeypatch.setattr(
        tooling_module,
        "_check_exclusion_consistency",
        lambda _root: (
            {
                "scanner_candidates": 1,
                "compliant_scanners": 1,
                "non_compliant_scanners": 0,
                "non_compliant_files": [],
            },
            [],
        ),
        raising=True,
    )

    result = tooling_module.analyze_tooling_consistency(Path("."))

    assert result["summary"]["status"] == "PASS"
    assert result["summary"]["total_issues"] == 0


@pytest.mark.unit
def test_main_json_output_emits_standard_format(monkeypatch, capsys):
    monkeypatch.setattr(
        tooling_module,
        "analyze_tooling_consistency",
        lambda _root: {
            "summary": {"total_issues": 0, "files_affected": 0, "status": "PASS"},
            "details": {"issues": []},
        },
        raising=True,
    )

    exit_code = tooling_module.main(["--json", "--project-root", "."])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"summary"' in output
    assert '"status": "PASS"' in output


@pytest.mark.unit
def test_main_strict_returns_nonzero_on_findings(monkeypatch):
    monkeypatch.setattr(
        tooling_module,
        "analyze_tooling_consistency",
        lambda _root: {
            "summary": {"total_issues": 2, "files_affected": 1, "status": "FAIL"},
            "details": {"issues": [{"id": "x"}]},
        },
        raising=True,
    )

    assert tooling_module.main(["--strict", "--project-root", "."]) == 1
