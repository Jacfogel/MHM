"""Tests for development_tools.tests.dev_tools_coverage_cache."""

from __future__ import annotations

import json
import os
import shutil
import stat
import time
import uuid
from pathlib import Path

import pytest

from development_tools.tests.dev_tools_coverage_cache import DevToolsCoverageCache


def _make_local_scratch_dir() -> Path:
    """Create a writable local scratch directory under tests/data/tmp."""
    scratch_root = Path("tests") / "data" / "tmp" / "dev_tools_cache_scratch"
    scratch_root.mkdir(parents=True, exist_ok=True)
    scratch_dir = scratch_root / f"cache_{uuid.uuid4().hex[:10]}"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    return scratch_dir.resolve()


def _cleanup_local_scratch_dir(path: Path) -> None:
    """Best-effort cleanup for scratch dirs with Windows permission handling."""
    if not path.exists():
        return
    for _ in range(3):
        try:
            for item in path.rglob("*"):
                try:
                    os.chmod(item, stat.S_IWRITE | stat.S_IREAD)
                except OSError:
                    pass
            shutil.rmtree(path, ignore_errors=False)
            return
        except OSError:
            time.sleep(0.1)
    shutil.rmtree(path, ignore_errors=True)


@pytest.mark.unit
def test_dev_tools_cache_persists_tool_hash_and_mtimes() -> None:
    """Dev tools cache payload should include tool hash and tool mtimes."""
    temp_path = _make_local_scratch_dir()
    try:
        project_root = Path.cwd().resolve()
        cache = DevToolsCoverageCache(project_root=project_root, cache_dir=temp_path)
        cache.update_run_status(last_run_ok=True, last_exit_code=0)

        cache_file = temp_path / "dev_tools_coverage_cache.json"
        assert cache_file.exists()

        cache_json = json.loads(cache_file.read_text(encoding="utf-8"))
        assert cache_json.get("tool_hash")
        tool_mtimes = cache_json.get("tool_mtimes")
        assert isinstance(tool_mtimes, dict)
        normalized_keys = {k.replace("\\", "/") for k in tool_mtimes.keys()}
        assert "development_tools/tests/run_test_coverage.py" in normalized_keys
        assert "development_tools/tests/dev_tools_coverage_cache.py" in normalized_keys
    finally:
        _cleanup_local_scratch_dir(temp_path)


@pytest.mark.unit
def test_dev_tools_cache_reports_tool_hash_mismatch_reason() -> None:
    """Tool hash mismatch should produce an explicit invalidation reason."""
    temp_path = _make_local_scratch_dir()
    try:
        project_root = Path.cwd().resolve()
        cache = DevToolsCoverageCache(project_root=project_root, cache_dir=temp_path)
        cache.update_run_status(last_run_ok=True, last_exit_code=0)
        cache.cache_data["tool_hash"] = "stale_hash"

        reason = cache.get_tool_change_reason()
        assert reason is not None
        assert "tool hash mismatch" in reason
    finally:
        _cleanup_local_scratch_dir(temp_path)
