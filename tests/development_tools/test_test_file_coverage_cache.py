"""Tests for test-file coverage cache invalidation behavior."""

from __future__ import annotations

import os
import shutil
import stat
import time
import uuid
import json
from pathlib import Path

import pytest

from development_tools.tests.domain_mapper import DomainMapper
from development_tools.tests.test_file_coverage_cache import TestFileCoverageCache


def _make_local_scratch_dir() -> Path:
    """Create a writable local scratch directory for cache tests under tests/data/tmp."""
    scratch_root = (
        Path("tests") / "data" / "tmp" / "test_file_coverage_cache_scratch"
    )
    scratch_root.mkdir(parents=True, exist_ok=True)
    scratch_dir = scratch_root / f"cache_{uuid.uuid4().hex[:10]}"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    return scratch_dir.resolve()


def _cleanup_local_scratch_dir(path: Path) -> None:
    """Best-effort cleanup for scratch dirs with basic Windows retry/permission handling."""
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
def test_domain_mapper_expands_cross_domain_dependencies() -> None:
    """Changed domains should include configured dependent domains."""
    temp_dir = _make_local_scratch_dir()
    try:
        mapper = DomainMapper(temp_dir)
        expanded = mapper.expand_domains_with_dependencies({"core"})

        assert "core" in expanded
        assert "communication" in expanded
        assert "ui" in expanded
        assert "tasks" in expanded
        assert "ai" in expanded
        assert "user" in expanded
        assert "notebook" in expanded
    finally:
        _cleanup_local_scratch_dir(temp_dir)


@pytest.mark.unit
def test_cache_invalidates_domains_when_test_file_changes() -> None:
    """Changing a test file should invalidate affected (and dependent) domains."""
    temp_path = _make_local_scratch_dir()
    try:
        (temp_path / "tests" / "unit").mkdir(parents=True, exist_ok=True)
        (temp_path / "core").mkdir(parents=True, exist_ok=True)

        source_file = temp_path / "core" / "demo_module.py"
        source_file.write_text("def f():\n    return 1\n", encoding="utf-8")

        test_file = temp_path / "tests" / "unit" / "test_demo_module.py"
        test_file.write_text(
            "import pytest\n\n@pytest.mark.unit\ndef test_demo():\n    assert True\n",
            encoding="utf-8",
        )

        cache = TestFileCoverageCache(temp_path)

        # Build initial mapping and a stable baseline cache snapshot.
        cache.update_test_file_mapping(test_file)
        for domain in cache.domain_mapper.SOURCE_TO_TEST_MAPPING.keys():
            cache.cache_data.setdefault("source_files_mtime", {})[
                domain
            ] = cache.get_source_file_mtimes(domain)
        cache._save_cache()

        # First pass should use the saved baseline.
        cache._cached_changed_domains = None
        baseline_changes = cache.get_changed_domains()
        assert baseline_changes == set()

        # Modify the test file and bump mtime explicitly for deterministic detection.
        test_file.write_text(
            "import pytest\n\n@pytest.mark.unit\ndef test_demo():\n    assert 1 == 1\n",
            encoding="utf-8",
        )
        current_stat = test_file.stat()
        os.utime(test_file, (current_stat.st_atime + 2, current_stat.st_mtime + 2))

        cache._cached_changed_domains = None
        changed_domains = cache.get_changed_domains()

        assert "core" in changed_domains
        # Dependency expansion should pull in communication from core changes.
        assert "communication" in changed_domains
        assert cache.last_invalidation_reason == "test_file_content_or_mapping_changed"
    finally:
        _cleanup_local_scratch_dir(temp_path)


@pytest.mark.unit
def test_cache_persists_tool_hash_and_mtimes() -> None:
    """Cache save should persist tool hash + tool mtimes metadata."""
    temp_path = _make_local_scratch_dir()
    try:
        project_root = Path.cwd().resolve()
        cache = TestFileCoverageCache(project_root, cache_dir=temp_path)

        cache._save_cache()

        cache_file = temp_path / "test_file_coverage_cache.json"
        assert cache_file.exists()
        cache_json = json.loads(cache_file.read_text(encoding="utf-8"))
        assert cache_json.get("tool_hash")
        tool_mtimes = cache_json.get("tool_mtimes")
        assert isinstance(tool_mtimes, dict)
        normalized_keys = {k.replace("\\", "/") for k in tool_mtimes.keys()}
        assert "development_tools/tests/run_test_coverage.py" in normalized_keys
        assert "development_tools/tests/test_file_coverage_cache.py" in normalized_keys
    finally:
        _cleanup_local_scratch_dir(temp_path)


@pytest.mark.unit
def test_tool_hash_mismatch_invalidates_all_domains() -> None:
    """Tool hash mismatch should invalidate all domains with explicit reason."""
    temp_path = _make_local_scratch_dir()
    try:
        project_root = Path.cwd().resolve()
        cache = TestFileCoverageCache(project_root, cache_dir=temp_path)
        cache._save_cache()

        # Force mismatch without touching tool files.
        cache.cache_data["tool_hash"] = "stale_hash_value"
        cache._cached_changed_domains = None
        changed_domains = cache.get_changed_domains()

        expected_domains = set(cache.domain_mapper.SOURCE_TO_TEST_MAPPING.keys())
        assert changed_domains == expected_domains
        assert cache.last_invalidation_reason is not None
        assert cache.last_invalidation_reason.startswith("tool_change:")
    finally:
        _cleanup_local_scratch_dir(temp_path)
