"""Tests for development_tools.shared.mtime_cache."""

from __future__ import annotations

import json
import os
import shutil
import stat
import time
import uuid
from pathlib import Path

import pytest

from development_tools.shared.mtime_cache import MtimeFileCache


def _make_local_scratch_dir() -> Path:
    """Create a writable local scratch directory under tests/data/tmp."""
    scratch_root = Path("tests") / "data" / "tmp" / "mtime_cache_scratch"
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
def test_mtime_cache_persists_tool_metadata_and_run_status() -> None:
    """Cache payload should include tool hash/mtimes and run status metadata."""
    project_root = _make_local_scratch_dir()
    try:
        source_file = project_root / "docs" / "sample.md"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text("hello", encoding="utf-8")

        tool_file = project_root / "tools" / "demo_tool.py"
        tool_file.parent.mkdir(parents=True, exist_ok=True)
        tool_file.write_text("VALUE = 'demo'\n", encoding="utf-8")

        cache = MtimeFileCache(
            project_root=project_root,
            use_cache=True,
            tool_name="demo_tool",
            domain="docs",
            tool_paths=[tool_file],
        )
        cache.cache_results(source_file, {"issues": 0})
        cache.save_cache()

        cache_path = (
            project_root
            / "development_tools"
            / "docs"
            / "jsons"
            / ".demo_tool_cache.json"
        )
        assert cache_path.exists()

        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        data = payload.get("data", {})
        assert "__tool_hash__" in data
        assert "__tool_mtimes__" in data
        assert "__run_status__" in data
        assert data["__run_status__"]["status"] == "success"
    finally:
        _cleanup_local_scratch_dir(project_root)


@pytest.mark.unit
def test_mtime_cache_invalidates_after_previous_failed_run() -> None:
    """A failed previous run should invalidate cached results on next initialization."""
    project_root = _make_local_scratch_dir()
    try:
        source_file = project_root / "docs" / "sample.md"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text("hello", encoding="utf-8")

        cache = MtimeFileCache(
            project_root=project_root,
            use_cache=True,
            tool_name="demo_failure_tool",
            domain="docs",
        )
        cache.cache_results(source_file, {"cached": True})
        cache.mark_run_result(success=False, error="simulated failure")
        cache.save_cache()

        reloaded = MtimeFileCache(
            project_root=project_root,
            use_cache=True,
            tool_name="demo_failure_tool",
            domain="docs",
        )
        assert reloaded.get_cached(source_file) is None
    finally:
        _cleanup_local_scratch_dir(project_root)


@pytest.mark.unit
def test_mtime_cache_invalidates_when_tool_source_changes() -> None:
    """Tool hash changes should invalidate existing cached entries."""
    project_root = _make_local_scratch_dir()
    try:
        source_file = project_root / "docs" / "sample.md"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text("hello", encoding="utf-8")

        tool_file = project_root / "tools" / "tool.py"
        tool_file.parent.mkdir(parents=True, exist_ok=True)
        tool_file.write_text("VALUE = 1\n", encoding="utf-8")

        cache = MtimeFileCache(
            project_root=project_root,
            use_cache=True,
            tool_name="demo_tool_hash_tool",
            domain="docs",
            tool_paths=[tool_file],
        )
        cache.cache_results(source_file, {"cached": True})
        cache.save_cache()

        tool_file.write_text("VALUE = 2\n", encoding="utf-8")

        reloaded = MtimeFileCache(
            project_root=project_root,
            use_cache=True,
            tool_name="demo_tool_hash_tool",
            domain="docs",
            tool_paths=[tool_file],
        )
        assert reloaded.get_cached(source_file) is None
    finally:
        _cleanup_local_scratch_dir(project_root)
