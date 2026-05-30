"""Tests for domain-scoped pytest suite result caching."""

from __future__ import annotations

from pathlib import Path

import pytest

from development_tools.tests.test_file_suite_cache import TestFileSuiteCache


def _make_cache(tmp_path: Path) -> TestFileSuiteCache:
    cache_dir = tmp_path / "suite_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return TestFileSuiteCache(Path.cwd(), cache_dir=cache_dir)


@pytest.mark.unit
def test_failed_suite_run_invalidates_even_when_coverage_cache_is_ok(tmp_path: Path):
    """Suite failure must not be masked by a later coverage-only cache success."""
    cache = _make_cache(tmp_path)
    cache.cache_data["last_run_ok"] = False
    cache.cache_data["last_failed_domains"] = ["development_tools"]
    cache.cache_data["_full_suite_snapshot"] = {
        "parallel": {"counts": {"passed": 5000}, "failed_node_ids": []},
        "no_parallel": {"counts": {"passed": 100}, "failed_node_ids": []},
    }
    cache.coverage_cache.cache_data["last_run_ok"] = True
    cache.coverage_cache.cache_data["last_failed_domains"] = []
    current_hash = cache._compute_tool_hash()
    if current_hash:
        cache.cache_data["tool_hash"] = current_hash
    cache._save_cache()
    cache.coverage_cache._save_cache()

    changed = cache.get_changed_domains()

    assert changed == {"development_tools"}
    assert not cache.can_reuse_full_suite_cache()


@pytest.mark.unit
def test_clear_full_suite_cache_removes_snapshot(tmp_path: Path):
    cache = _make_cache(tmp_path)
    cache.cache_full_suite({"parallel": {"counts": {}, "failed_node_ids": []}})
    assert cache.get_full_suite_cache() is not None

    cache.clear_full_suite_cache()

    assert cache.get_full_suite_cache() is None
    assert not cache.can_reuse_full_suite_cache()
