"""Smoke tests for development_tools portability (no core.* under fake project roots)."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _copy_development_tools_tree(target_root: Path) -> Path:
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
        json.dumps(
            {
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
                    "local_module_prefixes": [],
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
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (target_root / "README.md").write_text("# External Project\n", encoding="utf-8")
    (target_root / "requirements.txt").write_text("", encoding="utf-8")
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
