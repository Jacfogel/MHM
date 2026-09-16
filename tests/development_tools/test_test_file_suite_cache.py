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
    cache._store_tool_hashes()
    cache._save_cache()
    cache.coverage_cache._save_cache()

    changed = cache.get_changed_domains()

    assert changed == {"development_tools"}
    assert not cache.can_reuse_full_suite_cache()


@pytest.mark.unit
def test_runner_helper_tool_change_only_reruns_tools_domain(tmp_path: Path):
    """Editing run_test_suite / suite cache helpers must not bust every product domain."""
    cache = _make_cache(tmp_path)
    cache.cache_data["last_run_ok"] = True
    cache.cache_data["last_parallel_ok"] = True
    cache.cache_data["last_suite_profile"] = "quick"
    cache.cache_full_suite(
        {"parallel": {"counts": {"passed": 1}, "failed_node_ids": []}}
    )
    cache._store_tool_hashes()
    cache.cache_data["runner_helper_hash"] = "stale_helper"
    cache.cache_data["tool_hash"] = "stale_combined"
    cache._save_cache()
    cache.coverage_cache.get_changed_domains = lambda: set()

    changed = cache.get_changed_domains("quick")

    assert changed == {"development_tools"}
    assert cache.last_invalidation_reason == "suite_runner_helper_change"
    assert cache.get_full_suite_cache() is None
    assert not cache.can_reuse_full_suite_cache("quick")


@pytest.mark.unit
def test_structural_suite_tool_change_invalidates_all_domains(tmp_path: Path):
    """domain_mapper / config tool changes still force a full suite domain bust."""
    cache = _make_cache(tmp_path)
    cache.cache_data["last_run_ok"] = True
    cache.cache_data["last_parallel_ok"] = True
    cache.cache_data["last_suite_profile"] = "quick"
    cache.cache_full_suite(
        {"parallel": {"counts": {"passed": 1}, "failed_node_ids": []}}
    )
    cache._store_tool_hashes()
    cache.cache_data["structural_tool_hash"] = "stale_structural"
    cache.cache_data["tool_hash"] = "stale_combined"
    cache._save_cache()

    changed = cache.get_changed_domains("quick")

    assert changed == cache._all_domains()
    assert cache.last_invalidation_reason == "suite_tool_change"
    assert cache.get_full_suite_cache() is None


@pytest.mark.unit
def test_clear_full_suite_cache_removes_snapshot(tmp_path: Path):
    cache = _make_cache(tmp_path)
    cache.cache_full_suite({"parallel": {"counts": {}, "failed_node_ids": []}})
    assert cache.get_full_suite_cache() is not None

    cache.clear_full_suite_cache()

    assert cache.get_full_suite_cache() is None
    assert not cache.can_reuse_full_suite_cache()


@pytest.mark.unit
def test_suite_profile_change_invalidates_full_cache(tmp_path: Path):
    cache = _make_cache(tmp_path)
    cache.cache_data["last_run_ok"] = True
    cache.cache_data["last_parallel_ok"] = True
    cache.cache_data["last_suite_profile"] = "quick"
    cache.cache_full_suite({"parallel": {"counts": {}, "failed_node_ids": []}})

    assert cache.can_reuse_full_suite_cache("quick")
    assert not cache.can_reuse_full_suite_cache("full")

    changed = cache.get_changed_domains("full")
    assert changed == cache._all_domains()
    assert "suite_profile_change" in str(cache.last_invalidation_reason)
