"""Policy tests for development_tools import boundary compliance."""

import pytest

from tests.development_tools.conftest import load_development_tools_module


@pytest.mark.unit
def test_development_tools_has_no_import_boundary_violations():
    """
    Policy: development_tools/** must not import non-approved core modules.

    Approved: core.logger only.
    Run: python development_tools/imports/analyze_dev_tools_import_boundaries.py
    See: development_tools/DEVELOPMENT_TOOLS_GUIDE.md §8.5
    """
    boundary_module = load_development_tools_module(
        "imports.analyze_dev_tools_import_boundaries"
    )
    DevToolsImportBoundaryChecker = boundary_module.DevToolsImportBoundaryChecker
    # Use real project root so we scan actual development_tools code
    from pathlib import Path

    project_root = Path(__file__).resolve().parent.parent.parent
    checker = DevToolsImportBoundaryChecker(project_root_path=str(project_root))
    result = checker.analyze()
    violations = result["summary"]["total_issues"]
    if violations > 0:
        details = result["details"].get("violations", [])
        lines = [f"  - {v.get('file')}: {v.get('module')}" for v in details[:10]]
        msg = (
            f"Import boundary policy violated: {violations} violation(s). "
            f"Refactor to use only core.logger. See DEVELOPMENT_TOOLS_GUIDE.md §8.5.\n"
            + "\n".join(lines)
        )
        pytest.fail(msg)
    assert violations == 0, "Expected zero import boundary violations"
