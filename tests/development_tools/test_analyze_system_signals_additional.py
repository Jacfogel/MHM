"""Additional tests for development_tools/reports/analyze_system_signals.py."""

from types import SimpleNamespace
import argparse
import json
import builtins

import pytest

from tests.development_tools.conftest import load_development_tools_module


signals_module = load_development_tools_module("analyze_system_signals")


@pytest.mark.unit
def test_meaningful_change_and_significance_scoring():
    """Classifier helpers should separate non-meaningful paths and prioritize key files."""
    analyzer = signals_module.SystemSignalsAnalyzer()

    assert analyzer._is_meaningful_change("core/service.py") is True
    assert analyzer._is_meaningful_change("development_tools/logs/main.log") is False
    assert analyzer._is_meaningful_change("tests/data/users/u/account.json") is False
    assert analyzer._is_meaningful_change("docs/guide.md") is True

    assert analyzer._get_change_significance_score("core/service.py") == 100
    assert analyzer._get_change_significance_score("development_docs/guide.md") == 80
    assert analyzer._get_change_significance_score("config/settings.yaml") == 60
    assert analyzer._get_change_significance_score("logs/errors.log") == 0


@pytest.mark.unit
def test_standard_result_counts_missing_and_severity_issues():
    """Standard-format wrapper should aggregate missing artifacts and severity counts."""
    signals = {
        "critical_alerts": ["A"],
        "system_health": {
            "overall_status": "ISSUES",
            "core_files": {"a.py": "MISSING", "b.py": "OK"},
            "key_directories": {"core": "OK", "logs": "MISSING"},
            "severity_levels": {"CRITICAL": ["c1"], "WARNING": ["w1", "w2"]},
        },
    }

    wrapped = signals_module._build_standard_result(signals)

    assert wrapped["summary"]["total_issues"] == 4
    assert wrapped["summary"]["files_affected"] == 2
    assert wrapped["summary"]["status"] == "ISSUES"


@pytest.mark.unit
def test_format_human_readable_includes_recommendations_and_alerts():
    """Human formatter should include key sections when data is present."""
    formatted = signals_module._format_human_readable(
        {
            "timestamp": "2026-02-25T00:00:00",
            "system_health": {
                "overall_status": "CRITICAL",
                "health_indicators": ["Indicator A"],
                "severity_levels": {
                    "CRITICAL": ["Critical item"],
                    "WARNING": ["Warning item"],
                    "INFO": ["Info item"],
                },
                "recommendations": ["Do thing 1"],
                "warnings": [],
                "errors": [],
                "audit_freshness": "<24 hours",
                "last_audit": "2026-02-25T00:00:00",
                "test_coverage_status": "Good",
            },
            "recent_activity": {
                "git_status": "Modified",
                "recent_changes": ["core/a.py"],
            },
            "critical_alerts": ["CRITICAL: missing file"],
            "performance_indicators": {"log_file_sizes": {"errors.log": "1.0MB"}},
        }
    )

    assert "SYSTEM SIGNALS ANALYSIS" in formatted
    assert "RECOMMENDATIONS:" in formatted
    assert "CRITICAL ALERTS:" in formatted
    assert "Git Status: Modified" in formatted
    assert "Documentation Sync Status" not in formatted


@pytest.mark.unit
def test_identify_critical_alerts_projects_severity_only():
    """Critical alerts come from health severity, not a second file/log scan."""
    analyzer = signals_module.SystemSignalsAnalyzer()
    health = {
        "severity_levels": {
            "CRITICAL": [
                "Missing core file: requirements.txt",
                "CRITICAL: Recent errors detected in logs/errors.log (last hour)",
            ],
            "WARNING": ["Audit data is 5 days old"],
        }
    }
    alerts = analyzer._identify_critical_alerts(health)
    assert alerts == [
        "CRITICAL: Missing core file: requirements.txt",
        "CRITICAL: Recent errors detected in logs/errors.log (last hour)",
    ]
    assert analyzer._identify_critical_alerts(None) == []
    assert analyzer._identify_critical_alerts({}) == []


@pytest.mark.unit
def test_check_system_health_omits_documentation_sync_status(tmp_path, monkeypatch):
    """Doc-sync is owned by Documentation Signals; system health must not re-derive it."""
    analyzer = signals_module.SystemSignalsAnalyzer(project_root=tmp_path)
    monkeypatch.setattr(
        analyzer, "_resolve_analysis_detailed_results_path", lambda: None
    )
    health = analyzer._check_system_health()
    assert "documentation_sync_status" not in health
    assert health.get("test_coverage_status") == "Unknown"


@pytest.mark.unit
def test_main_json_mode_prints_standard_result(monkeypatch):
    """CLI main should print standard-format JSON when --json is selected."""
    expected_signals = {
        "critical_alerts": [],
        "system_health": {
            "overall_status": "OK",
            "core_files": {},
            "key_directories": {},
            "severity_levels": {"CRITICAL": [], "WARNING": []},
        },
    }
    printed = {"value": None}

    monkeypatch.setattr(
        argparse.ArgumentParser,
        "parse_args",
        lambda self: SimpleNamespace(json=True, output=None),
    )
    monkeypatch.setattr(
        signals_module.SystemSignalsAnalyzer,
        "analyze_system_signals",
        lambda self: expected_signals,
        raising=True,
    )
    monkeypatch.setattr(
        builtins, "print", lambda text: printed.__setitem__("value", text), raising=True
    )

    signals_module.main()

    value = printed["value"]
    assert value is not None, "print mock should have been called with JSON output"
    payload = json.loads(value)
    assert payload["summary"]["status"] == "OK"
    assert payload["details"]["system_health"]["overall_status"] == "OK"
