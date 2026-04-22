"""Unit tests for development_tools/shared/verify_tool_storage.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from development_tools.shared import verify_tool_storage as vts
from development_tools.shared.verify_tool_storage import (
    check_tool_uses_save_tool_result,
    verify_all_tools,
)


class _MixinWithSave:
    def run_sample_tool(self):
        # Referenced by name so storage check passes
        _ = "save_tool_result"
        return None


class _MixinWithoutSave:
    def run_other_tool(self):
        return 1


@pytest.mark.unit
def test_check_tool_uses_save_tool_result_true():
    ok, msg = check_tool_uses_save_tool_result("sample_tool", _MixinWithSave)
    assert ok is True
    assert "save_tool_result" in msg


@pytest.mark.unit
def test_check_tool_uses_save_tool_result_false():
    ok, msg = check_tool_uses_save_tool_result("other_tool", _MixinWithoutSave)
    assert ok is False
    assert "Does not use" in msg


@pytest.mark.unit
def test_check_tool_uses_save_tool_result_missing_method():
    ok, msg = check_tool_uses_save_tool_result("nope", _MixinWithSave)
    assert ok is False
    assert "not found" in msg


@pytest.mark.unit
def test_verify_all_tools_prints_summary(capsys):
    ok = verify_all_tools()
    out = capsys.readouterr().out
    assert "Tool Storage Standardization Verification" in out
    assert "Checking" in out and "analysis tools" in out
    assert "Summary:" in out
    assert isinstance(ok, bool)


@pytest.mark.unit
def test_verify_all_tools_fails_when_storage_check_false():
    with patch.object(vts, "check_tool_uses_save_tool_result", return_value=(False, "no save")):
        assert verify_all_tools() is False


@pytest.mark.unit
def test_cli_process_exit_code_matches_success_line():
    """Standalone script exit code matches printed success vs warning summary."""
    project_root = Path(__file__).resolve().parent.parent.parent
    script = project_root / "development_tools" / "shared" / "verify_tool_storage.py"
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        timeout=60,
    )
    out = proc.stdout
    success_banner = "[OK] All tools use standardized storage correctly"
    assert (proc.returncode == 0) == (success_banner in out)
