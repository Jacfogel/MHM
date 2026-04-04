"""
Lightweight replacement for the prior commented-out audit status suite.

Asserts markdown status outputs are produced via create_output_file in a single
end-of-audit batch (one write per logical report), without running real tools.
"""

from __future__ import annotations

import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import pytest

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import development_tools.shared.service.audit_orchestration as audit_orch
from development_tools.shared.service import AIToolsService


@pytest.mark.unit
def test_quick_audit_writes_each_core_status_file_once(tmp_path, monkeypatch):
    """AI_STATUS, AI_PRIORITIES, and CONSOLIDATED each receive exactly one create_output_file call."""
    # Patch the same module object `run_audit` uses (avoids duplicate importlib copies in full suites).
    monkeypatch.setattr(
        audit_orch,
        "evaluate_lock_set",
        lambda _paths: {"stale": [], "malformed": [], "active": []},
    )
    monkeypatch.setenv("DISABLE_LOG_ROTATION", "1")

    proj = tmp_path / "audit_status_proj"
    proj.mkdir()
    (proj / "development_tools").mkdir(parents=True)

    service = AIToolsService(project_root=str(proj))
    patches = [
        patch.object(service, "_generate_ai_status_document", return_value="# AI Status\n"),
        patch.object(
            service, "_generate_ai_priorities_document", return_value="# AI Priorities\n"
        ),
        patch.object(service, "_generate_consolidated_report", return_value="# Consolidated\n"),
        patch.object(service, "_run_quick_audit_tools", return_value=True),
        patch.object(service, "_save_audit_results_aggregated", return_value=None),
        patch.object(service, "_reload_all_cache_data", return_value=None),
        patch.object(service, "_sync_todo_with_changelog", return_value=None),
        patch.object(service, "_validate_referenced_paths", return_value=None),
        patch.object(service, "_check_and_trim_changelog_entries", return_value=None),
        patch.object(service, "_check_documentation_quality", return_value=None),
        patch.object(service, "_check_ascii_compliance", return_value=None),
        patch.object(
            service,
            "run_script",
            return_value={"success": True, "output": "{}", "data": {}},
        ),
    ]
    with ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        assert service.run_audit(quick=True) is True

    # Black-box check: end-of-audit writes each report under project_root/development_tools/.
    # (Do not wrap create_output_file — coverage/subprocess runs can bind a different module copy.)
    out = proj / "development_tools"
    for name, prefix in (
        ("AI_STATUS.md", "# AI Status"),
        ("AI_PRIORITIES.md", "# AI Priorities"),
        ("CONSOLIDATED_REPORT.md", "# Consolidated"),
    ):
        path = out / name
        assert path.is_file(), f"expected {name} at {path}"
        assert path.read_text(encoding="utf-8").startswith(prefix)
