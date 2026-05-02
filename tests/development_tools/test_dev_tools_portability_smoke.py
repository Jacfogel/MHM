"""Smoke tests for development_tools portability (no core.* under fake project roots)."""

import subprocess
import sys
from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


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
