"""Unit tests for development_tools/config/analyze_config.py (ConfigValidator)."""

from __future__ import annotations

from pathlib import Path

import pytest

from development_tools.config import analyze_config


@pytest.mark.unit
def test_config_validator_relative_project_root_uses_package_anchor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fallback project root matches `_PACKAGE_ROOT` when config returns a relative path (V5 §3.17)."""
    monkeypatch.setattr(analyze_config.config, "get_project_root", lambda: ".")
    v = analyze_config.ConfigValidator()
    assert v.project_root == analyze_config._PACKAGE_ROOT


@pytest.mark.unit
def test_config_validator_absolute_project_root_is_used(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(analyze_config.config, "get_project_root", lambda: str(tmp_path))
    v = analyze_config.ConfigValidator()
    assert v.project_root == tmp_path.resolve()


@pytest.mark.unit
def test_analyze_tool_config_usage_detects_entry_point(tmp_path: Path) -> None:
    """AIToolsService() marks entry-point scripts exempt from config-import rules."""
    p = tmp_path / "entry.py"
    p.write_text(
        "from development_tools.shared.service.service import AIToolsService\n"
        "def main():\n"
        "    svc = AIToolsService()\n",
        encoding="utf-8",
    )
    v = analyze_config.ConfigValidator()
    result = v._analyze_tool_config_usage(p)
    assert result.get("is_entry_point_script") is True
    assert result.get("imports_config") is True


@pytest.mark.unit
def test_analyze_tool_config_usage_detects_wrapper(tmp_path: Path) -> None:
    """Wrapper scripts that delegate main() are exempt."""
    p = tmp_path / "wrap.py"
    p.write_text(
        "from some.module import main\nimport sys\nsys.exit(main())\n",
        encoding="utf-8",
    )
    v = analyze_config.ConfigValidator()
    result = v._analyze_tool_config_usage(p)
    assert result.get("is_wrapper_script") is True
    assert result.get("imports_config") is True


@pytest.mark.unit
def test_analyze_tool_config_usage_imports_config_keyword(tmp_path: Path) -> None:
    p = tmp_path / "tool.py"
    p.write_text("import config\nconfig.validate_all_configuration()\n", encoding="utf-8")
    v = analyze_config.ConfigValidator()
    result = v._analyze_tool_config_usage(p)
    assert result.get("imports_config") is True


@pytest.mark.unit
def test_generate_recommendations_skips_wrapper_and_entry_point() -> None:
    v = analyze_config.ConfigValidator()
    tools = {
        "bad.py": {"imports_config": False, "hardcoded_values": [], "issues": [], "is_wrapper_script": True},
        "run.py": {"imports_config": False, "hardcoded_values": [], "issues": [], "is_entry_point_script": True},
        "fixme.py": {
            "imports_config": False,
            "hardcoded_values": [],
            "issues": [],
            "is_wrapper_script": False,
            "is_entry_point_script": False,
            "config_functions_used": [],
        },
    }
    recs = v.generate_recommendations(
        tools,
        {"missing_directories": [], "issues": [], "config_structure_valid": True},
        {"sections_complete": True, "missing_fields": []},
    )
    assert any("fixme.py" in r for r in recs)
    assert not any("bad.py" in r for r in recs)
    assert not any("run.py" in r for r in recs)


@pytest.mark.unit
def test_print_validation_report_invalid_results_raises() -> None:
    v = analyze_config.ConfigValidator()
    with pytest.raises(ValueError, match="standard format"):
        v.print_validation_report({})


@pytest.mark.unit
def test_run_validation_structure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run validation returns standard-format summary and details."""
    v = analyze_config.ConfigValidator()
    monkeypatch.setattr(
        v,
        "scan_tools_for_config_usage",
        lambda: {
            "t.py": {
                "imports_config": True,
                "issues": [],
                "hardcoded_values": [],
                "is_wrapper_script": False,
                "is_entry_point_script": False,
            }
        },
    )
    monkeypatch.setattr(
        v,
        "validate_configuration_consistency",
        lambda: {"scan_directories_exist": [], "missing_directories": [], "config_structure_valid": True, "issues": []},
    )
    monkeypatch.setattr(
        v,
        "check_configuration_completeness",
        lambda: {"sections_complete": True, "missing_fields": [], "recommendations": []},
    )
    monkeypatch.setattr(v, "generate_recommendations", lambda *a, **k: [])
    out = v.run_validation()
    assert "summary" in out and "details" in out
    assert "tools_analysis" in out["details"]


@pytest.mark.unit
def test_main_smoke_json_prints(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """main() exits after printing JSON; avoid full project scan."""
    minimal = {
        "summary": {"total_issues": 0, "files_affected": 0},
        "details": {
            "tools_analysis": {},
            "validation": {"issues": [], "missing_directories": [], "config_structure_valid": True},
            "completeness": {"sections_complete": True, "missing_fields": []},
            "recommendations": [],
            "summary": {
                "tools_using_config": 0,
                "total_tools": 0,
                "config_valid": True,
                "config_complete": True,
                "total_recommendations": 0,
            },
        },
    }
    monkeypatch.setattr(analyze_config.ConfigValidator, "run_validation", lambda self: minimal)
    monkeypatch.setattr(analyze_config.ConfigValidator, "print_validation_report", lambda self, r: None)
    analyze_config.main()
    captured = capsys.readouterr()
    assert '"summary"' in captured.out
