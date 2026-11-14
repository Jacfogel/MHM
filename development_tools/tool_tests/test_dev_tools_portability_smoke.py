"""Smoke tests for development_tools portability (no core.* under fake project roots)."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from development_tools.tool_tests.conftest import load_development_tools_module

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _minimal_external_config(*, with_host_package: bool = False) -> dict:
    """Project config with no MHM package roots / allowlists (portable)."""
    local_prefixes = ["extapp"] if with_host_package else []
    return {
        "project": {
            "name": "ExternalProject",
            "key_files": ["README.md", "requirements.txt"],
        },
        "paths": {
            "project_root": ".",
            "scan_directories": [],
            "docs_dir": "docs",
            "logs_dir": "logs",
            "data_dir": "data",
            "tests_dir": "tests",
        },
        "constants": {
            "default_docs": ["README.md"],
            "local_module_prefixes": local_prefixes,
            "project_directories": ["."],
            "core_modules": [],
            "derived_prefix_excludes": {
                "scan": [],
                "core": [],
                "project": [],
            },
        },
        "quick_status": {
            "core_files": ["README.md", "requirements.txt"],
            "key_directories": [],
        },
        "audit_tiers": {
            "quick": {"tools": ["quick_status"]},
            "standard": {"tools": ["quick_status"]},
            "full": {"tools": ["quick_status"]},
        },
        # Empty static roots: tools must fall back to full-project scan, not MHM trees.
        "static_analysis": {
            "ruff_shard_scan": True,
            "ruff_path_shards": [],
            "pyright_shard_scan": True,
            "pyright_path_shards": [],
            "bandit_shard_scan": False,
            "bandit_scan_roots": [],
            "bandit_root_python": [],
        },
        "static_checks": {
            "channel_loggers": {
                "excluded_dirs": ["tests", "scripts", "development_tools"],
                "allowed_logging_import_paths": [],
            }
        },
    }


def _copy_development_tools_tree(target_root: Path, *, with_host_package: bool = False) -> Path:
    """Copy the dev-tools package into a minimal external project."""
    source = _REPO_ROOT / "development_tools"
    destination = target_root / "development_tools"
    ignored = shutil.ignore_patterns(
        "__pycache__",
        ".pytest_cache",
        "jsons",
        "*.pyc",
    )
    shutil.copytree(source, destination, ignore=ignored)
    config_path = destination / "config" / "development_tools_config.json"
    config_path.write_text(
        json.dumps(_minimal_external_config(with_host_package=with_host_package), indent=2),
        encoding="utf-8",
    )
    (target_root / "README.md").write_text("# External Project\n", encoding="utf-8")
    (target_root / "requirements.txt").write_text("", encoding="utf-8")
    if with_host_package:
        host = target_root / "extapp"
        host.mkdir()
        (host / "__init__.py").write_text(
            '"""Minimal host package for external-repo validation."""\n\ndef ok() -> int:\n    return 1\n',
            encoding="utf-8",
        )
    return destination


@pytest.mark.unit
def test_import_boundary_checker_runs_on_minimal_project_without_core_package(tmp_path):
    """Host repo has no ``core/`` package: checker still analyzes ``development_tools/**``."""
    boundary_module = load_development_tools_module("imports.analyze_dev_tools_import_boundaries")
    DevToolsImportBoundaryChecker = boundary_module.DevToolsImportBoundaryChecker

    dt = tmp_path / "development_tools"
    dt.mkdir()
    (dt / "clean.py").write_text(
        "from pathlib import Path\n"
        "from development_tools.shared.logging import get_dev_tools_logger\n"
        "log = get_dev_tools_logger('x')\n",
        encoding="utf-8",
    )

    checker = DevToolsImportBoundaryChecker(project_root_path=str(tmp_path))
    result = checker.analyze()
    assert result["summary"]["total_issues"] == 0


@pytest.mark.unit
def test_import_boundary_detects_core_in_minimal_tree(tmp_path):
    boundary_module = load_development_tools_module("imports.analyze_dev_tools_import_boundaries")
    DevToolsImportBoundaryChecker = boundary_module.DevToolsImportBoundaryChecker

    dt = tmp_path / "development_tools"
    dt.mkdir()
    (dt / "bad.py").write_text("from core.service import x\n", encoding="utf-8")

    checker = DevToolsImportBoundaryChecker(project_root_path=str(tmp_path))
    result = checker.analyze()
    assert result["summary"]["total_issues"] >= 1
    assert any(v.get("module") == "core.service" for v in result["details"]["violations"])


@pytest.mark.unit
def test_shared_logging_import_does_not_load_core_modules():
    """Subprocess: importing ``development_tools.shared.logging`` must not load ``core.*``."""
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(_REPO_ROOT)!r})\n"
        "import development_tools.shared.logging\n"
        "assert 'core' not in sys.modules\n"
        "assert not any(k.startswith('core.') for k in sys.modules)\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.unit
def test_service_uses_minimal_project_config_without_core_package(tmp_path):
    """AIToolsService should honor supplied project_root config without MHM packages."""
    _copy_development_tools_tree(tmp_path)
    service_module = load_development_tools_module("shared.service")
    AIToolsService = service_module.AIToolsService

    service = AIToolsService(project_root=str(tmp_path))

    assert service.project_root == tmp_path.resolve()
    assert service.project_name == "ExternalProject"
    assert service.key_files == ["README.md", "requirements.txt"]
    assert not (tmp_path / "core").exists()

    backup_result = service.run_backup_health_check(run_drill=False)
    assert backup_result["success"] is True
    assert backup_result.get("skipped") is True
    assert backup_result["data"]["summary"]["status"] == "SKIP"


@pytest.mark.unit
def test_minimal_project_runs_read_only_config_status_and_report_paths(tmp_path):
    """Copied dev tools can execute read-only tools against an external project root."""
    _copy_development_tools_tree(tmp_path)
    service_module = load_development_tools_module("shared.service")
    AIToolsService = service_module.AIToolsService
    service = AIToolsService(project_root=str(tmp_path))

    config_result = service.run_script("analyze_config")
    assert config_result["success"] is True, config_result.get("error", "")
    config_payload = json.loads(config_result["output"])
    assert config_payload["summary"]["total_issues"] == 0
    assert str(_REPO_ROOT) not in config_result["output"]

    quick_result = service.run_script("quick_status", "json")
    assert quick_result["success"] is True, quick_result.get("error", "")
    quick_payload = json.loads(quick_result["output"])
    assert quick_payload["summary"]["status"] == "OK"
    assert quick_payload["details"]["system_health"]["core_files"]["README.md"] == "OK"

    status_doc = service._generate_ai_status_document()
    priorities_doc = service._generate_ai_priorities_document()
    assert "run_mhm.py" not in status_doc
    assert "run_mhm.py" not in priorities_doc


@pytest.mark.unit
def test_bandit_empty_roots_fallback_scans_external_project_root(tmp_path, monkeypatch):
    """B-004: empty bandit roots must scan ``.``, not hardcoded MHM package names."""
    _copy_development_tools_tree(tmp_path, with_host_package=True)
    cfg_path = tmp_path / "development_tools" / "config" / "development_tools_config.json"
    on_disk = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert on_disk["static_analysis"]["bandit_scan_roots"] == []
    assert on_disk["static_analysis"]["bandit_root_python"] == []

    bandit_module = load_development_tools_module("static_checks.analyze_bandit")
    config_module = load_development_tools_module("config.config")
    base = dict(config_module.STATIC_ANALYSIS)
    base["bandit_scan_roots"] = []
    base["bandit_root_python"] = []
    base["bandit_shard_scan"] = False
    monkeypatch.setattr(
        bandit_module.config, "get_static_analysis_config", lambda: base.copy()
    )

    captured: list[list[str]] = []

    def _capture(project_root, command, args, timeout_seconds):
        captured.append(list(args))
        return 0, {"results": []}, ""

    monkeypatch.setattr(bandit_module, "_run_bandit_subprocess_for_json", _capture)
    out = bandit_module.run_bandit(tmp_path)
    assert out["summary"]["status"] in {"PASS", "WARN"}
    assert captured, "expected bandit subprocess invocation"
    # Fallback path when no roots resolve is a single ``.`` scan.
    assert "." in captured[0]
    assert "core" not in captured[0]
    assert "run_mhm.py" not in captured[0]


@pytest.mark.unit
def test_ruff_empty_shards_uses_monolithic_scan_on_external_project(tmp_path, monkeypatch):
    """B-004: empty ruff shards must take monolithic fallback (full project), not MHM trees."""
    _copy_development_tools_tree(tmp_path, with_host_package=True)
    cfg_path = tmp_path / "development_tools" / "config" / "development_tools_config.json"
    on_disk = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert on_disk["static_analysis"]["ruff_path_shards"] == []

    ruff_module = load_development_tools_module("static_checks.analyze_ruff")
    config_module = load_development_tools_module("config.config")
    base = dict(config_module.STATIC_ANALYSIS)
    base["ruff_path_shards"] = []
    base["ruff_shard_scan"] = True
    monkeypatch.setattr(
        ruff_module.config, "get_static_analysis_config", lambda: base.copy()
    )

    def _capture(project_root, command, args, timeout_seconds):
        return 0, [], ""

    monkeypatch.setattr(ruff_module, "_run_ruff_subprocess_for_json_list", _capture)
    out = ruff_module.run_ruff(tmp_path)
    details = out.get("details") or {}
    shard_run = details.get("shard_run") or {}
    assert shard_run.get("mode") in {"single", "single_fallback"}
    assert "core" not in json.dumps(out)


@pytest.mark.unit
@pytest.mark.slow
def test_copied_devtools_cli_audit_quick_succeeds_on_external_project(tmp_path):
    """B-004: subprocess ``audit --quick`` against a copied tree with a host package."""
    _copy_development_tools_tree(tmp_path, with_host_package=True)
    runner = tmp_path / "development_tools" / "run_development_tools.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(runner),
            "--project-root",
            str(tmp_path),
            "audit",
            "--quick",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "run_mhm.py" not in (proc.stdout + proc.stderr)

@pytest.mark.unit
def test_custom_audit_writes_status_under_host_configured_directory(tmp_path, monkeypatch):
    # Exercise production logging while keeping the subprocess confined to tmp_path.
    monkeypatch.setenv("MHM_TESTING", "0")
    monkeypatch.delenv("DEV_TOOLS_LOGS_DIR", raising=False)
    monkeypatch.delenv("LOG_AI_DEV_TOOLS_FILE", raising=False)
    destination = _copy_development_tools_tree(tmp_path, with_host_package=True)
    config_path = destination / "config" / "development_tools_config.json"
    host_config = json.loads(config_path.read_text(encoding="utf-8"))
    host_config["status"] = {"scoped_report_dir": "artifacts/scoped audits"}
    host_config["paths"]["report_logs_dir"] = "artifacts/logs"
    config_path.write_text(json.dumps(host_config), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            str(destination / "run_development_tools.py"),
            "--project-root",
            str(tmp_path),
            "audit",
            "--audit-scope",
            "extapp",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    report_path = "artifacts/scoped audits/scope_extapp/SCOPED_AUDIT_STATUS.md"
    report = (tmp_path / report_path).read_text(encoding="utf-8")
    assert f"> **File**: `{report_path}`" in report
    assert (tmp_path / "artifacts/logs/ai_dev_tools.log").is_file()


@pytest.mark.unit
def test_coverage_report_uses_host_paths(tmp_path):
    """The wrapper and report subprocess use the same host configuration."""
    config_path = tmp_path / "host-config.json"
    host_config = _minimal_external_config()
    host_config["coverage"] = {
        "json_dir": "artifacts/snapshots",
        "detail_report_path": "reports/quality/coverage.md",
    }
    config_path.write_text(json.dumps(host_config), encoding="utf-8")
    snapshot = tmp_path / "artifacts" / "snapshots" / "coverage.json"
    snapshot.parent.mkdir(parents=True)
    summary = {"num_statements": 4, "covered_lines": 3, "missing_lines": 1}
    snapshot.write_text(
        json.dumps({"files": {"example.py": {"summary": summary}}, "totals": summary}),
        encoding="utf-8",
    )

    service_module = load_development_tools_module("shared.service")
    service = service_module.AIToolsService(
        project_root=str(tmp_path), config_path=str(config_path)
    )
    result = service.run_generate_test_coverage_report()

    assert result["success"], result
    report = tmp_path / "reports" / "quality" / "coverage.md"
    assert "reports/quality/coverage.md" in report.read_text(encoding="utf-8")
    assert service._load_coverage_summary()["overall"]["coverage"] == 75.0


@pytest.mark.unit
def test_legacy_report_and_scanner_share_host_paths(tmp_path, monkeypatch):
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    config_path = tmp_path / "host-config.json"
    host_config = _minimal_external_config()
    report_path = "reports/maintenance/legacy.md"
    inventory_path = "policy/retired.json"
    host_config["legacy_cleanup"] = {
        "detail_report_path": report_path,
        "deprecation_inventory_file": inventory_path,
    }
    config_path.write_text(json.dumps(host_config), encoding="utf-8")
    inventory = tmp_path / inventory_path
    inventory.parent.mkdir()
    inventory.write_text(
        json.dumps({"active_or_candidate_inventory": [{"search_terms": ["retired_api"]}]}),
        encoding="utf-8",
    )

    service_module = load_development_tools_module("shared.service")
    service = service_module.AIToolsService(
        project_root=str(tmp_path), config_path=str(config_path)
    )
    scan = service.run_analyze_legacy_references()
    assert scan["success"], scan
    details = scan["data"]["details"]
    assert details["report_path"] == report_path
    assert details["deprecation_inventory"]["inventory_path"] == inventory_path
    assert details["deprecation_inventory"]["loaded"]

    result = service.run_generate_legacy_reference_report()
    assert result["success"], result
    report = (tmp_path / report_path).read_text(encoding="utf-8")
    assert f"> **File**: `{report_path}`" in report
    assert f"Inventory file: `{inventory_path}`" in report


@pytest.mark.unit
def test_status_reports_use_host_paths_and_link_across_scopes(tmp_path):
    config_path = tmp_path / "host-config.json"
    host_config = _minimal_external_config()
    host_config["status"] = {
        "status_files": {
            "ai_status": "reports/full/overview.md",
            "ai_priorities": "reports/full/actions.md",
            "consolidated_report": "reports/full/details/summary.md",
        },
        "dev_tools_status_files": {
            "ai_status": "reports/tools/overview.md",
            "ai_priorities": "reports/tools/actions.md",
            "consolidated_report": "reports/tools/details/summary.md",
        },
    }
    config_path.write_text(json.dumps(host_config), encoding="utf-8")

    service_module = load_development_tools_module("shared.service")
    service = service_module.AIToolsService(
        project_root=str(tmp_path), config_path=str(config_path)
    )
    service.run_status()
    service.dev_tools_only_mode = True
    service.run_status()

    for paths in host_config["status"].values():
        for path in paths.values():
            assert f"> **File**: `{path}`" in (tmp_path / path).read_text(encoding="utf-8")
    full = (tmp_path / "reports/full/details/summary.md").read_text(encoding="utf-8")
    scoped = (tmp_path / "reports/tools/details/summary.md").read_text(encoding="utf-8")
    assert "[overview.md](../overview.md)" in full
    assert "[actions.md](../actions.md)" in scoped
    assert "[overview.md](../../full/overview.md)" in scoped
    assert "[actions.md](../../full/actions.md)" in scoped


@pytest.mark.unit
def test_quick_status_and_freshness_read_configured_audit_outputs(tmp_path):
    from development_tools.shared.service import data_freshness_audit

    # The host itself can live under a directory named reports.
    host = tmp_path / "reports" / "external"
    host.mkdir(parents=True)
    config_path = host / "host-config.json"
    host_config = _minimal_external_config()
    host_config["quick_audit"] = {"results_file": "artifacts/audit.json"}
    host_config["status"] = {"status_files": {"ai_status": "artifacts/overview.md"}}
    config_path.write_text(json.dumps(host_config), encoding="utf-8")
    for name in ("README.md", "requirements.txt"):
        (host / name).touch()

    service_module = load_development_tools_module("shared.service")
    service = service_module.AIToolsService(
        project_root=str(host), config_path=str(config_path)
    )
    aggregate = service._get_results_file_path()
    assert aggregate == host / "artifacts" / "audit.json"
    service.dev_tools_only_mode = True
    scoped_aggregate = service._get_results_file_path()
    assert scoped_aggregate == host / "artifacts" / "scopes" / "dev_tools" / "audit.json"

    aggregate.parent.mkdir(parents=True)
    aggregate.write_text(
        json.dumps({
            "timestamp": "2026-11-12T01:02:03",
            "results": {"analyze_function_registry": {"success": True, "output": "Coverage: 96%"}},
        }),
        encoding="utf-8",
    )
    scoped_aggregate.parent.mkdir(parents=True)
    scoped_aggregate.write_text(
        json.dumps({"timestamp": "2026-11-12T04:05:06", "path": "old/deleted.py"}),
        encoding="utf-8",
    )
    (aggregate.parent / "overview.md").write_text("old/deleted.py", encoding="utf-8")

    result = service.run_script("quick_status", "json")
    assert result["success"], result
    details = json.loads(result["output"])["details"]
    assert details["documentation_status"]["coverage"] == "96%"
    assert details["recent_activity"]["last_audit"] == "2026-11-12T01:02:03"
    assert details["system_health"]["core_files"]["README.md"] == "OK"

    assert data_freshness_audit.find_all_json_cache_files(host) == [aggregate, scoped_aggregate]
    cache_issues = data_freshness_audit.check_tool_results_for_deleted_files(host, {"old/deleted.py"})
    assert len(cache_issues) == 1
    assert data_freshness_audit.check_generated_reports_for_deleted_files(
        host, {"old/deleted.py"}
    ) == [("old/deleted.py", "Found in overview.md")]
