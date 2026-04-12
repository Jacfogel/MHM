"""Tests for Bandit and pip-audit static check wrappers."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from development_tools.static_checks.analyze_bandit import run_bandit
from development_tools.static_checks.analyze_pip_audit import (
    requirements_signature,
    run_pip_audit,
)


@pytest.mark.unit
@patch("development_tools.static_checks.analyze_bandit.subprocess.run")
def test_run_bandit_summarizes_medium_high_only(mock_run: MagicMock, tmp_path) -> None:
    payload = {
        "results": [
            {"filename": "app.py", "issue_severity": "HIGH"},
            {"filename": "app.py", "issue_severity": "LOW"},
        ]
    }
    mock_run.return_value = MagicMock(
        returncode=1,
        stdout=json.dumps(payload),
        stderr="",
    )
    out = run_bandit(tmp_path)
    assert out["summary"]["status"] == "FAIL"
    assert out["summary"]["total_issues"] == 1
    assert out["summary"]["files_affected"] == 1
    assert out["details"]["low_severity_count"] == 1


@pytest.mark.unit
def test_run_pip_audit_skip_env_skips_subprocess(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """MHM_PIP_AUDIT_SKIP yields PASS with zero findings and no network (V5 §4.2 CI/offline)."""
    monkeypatch.setenv("MHM_PIP_AUDIT_SKIP", "1")
    with patch("development_tools.static_checks.analyze_pip_audit.subprocess.run") as mock_run:
        out = run_pip_audit(tmp_path)
    mock_run.assert_not_called()
    assert out["summary"]["status"] == "PASS"
    assert out["summary"]["total_issues"] == 0
    assert out["details"].get("pip_audit_skipped") is True
    monkeypatch.delenv("MHM_PIP_AUDIT_SKIP", raising=False)


@pytest.mark.unit
@patch("development_tools.static_checks.analyze_pip_audit.subprocess.run")
def test_run_pip_audit_counts_vulnerabilities(mock_run: MagicMock, tmp_path) -> None:
    payload = {
        "dependencies": [
            {"name": "requests", "version": "1", "vulns": [{"id": "CVE-1"}]},
            {"name": "ok", "version": "2", "vulns": []},
        ]
    }
    mock_run.return_value = MagicMock(
        returncode=1,
        stdout=json.dumps(payload),
        stderr="",
    )
    out = run_pip_audit(tmp_path)
    assert out["summary"]["total_issues"] == 1
    assert out["summary"]["files_affected"] == 1
    assert out["summary"]["status"] == "WARN"


@pytest.mark.unit
def test_requirements_signature_changes_with_requirements_txt(tmp_path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("a==1\n", encoding="utf-8")
    s1 = requirements_signature(tmp_path)
    req.write_text("a==2\n", encoding="utf-8")
    s2 = requirements_signature(tmp_path)
    assert s1 and s2 and s1 != s2
