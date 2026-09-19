"""Tests for domain-scoped pytest suite result caching."""

from __future__ import annotations

from pathlib import Path

import pytest

from development_tools.tests.domain_mapper import _default_domain_mapper_config
from development_tools.tests.test_file_suite_cache import TestFileSuiteCache

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _make_cache(tmp_path: Path) -> TestFileSuiteCache:
    cache_dir = tmp_path / "suite_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return TestFileSuiteCache(
        _PROJECT_ROOT,
        cache_dir=cache_dir,
        mapper_config=_default_domain_mapper_config(),
    )


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
def test_runner_helper_change_reruns_tools_domain_when_mapper_omits_it(tmp_path: Path):
    """Soft invalidation must rerun tools tests even if the domain map is empty."""
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
    cache._all_domains = lambda: set()
    cache.coverage_cache.get_changed_domains = lambda: set()

    changed = cache.get_changed_domains("quick")

    assert changed == {"development_tools"}
    assert cache.last_invalidation_reason == "suite_runner_helper_change"


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


@pytest.mark.unit
def test_cache_test_file_suite_keeps_existing_results_when_phase_missing(tmp_path: Path):
    cache = _make_cache(tmp_path)
    test_file = _PROJECT_ROOT / "tests/development_tools/test_test_file_suite_cache.py"
    cache.cache_test_file_suite(
        test_file,
        parallel={
            "counts": {"passed": 3, "failed": 0, "errors": 0, "skipped": 0, "total": 3},
            "failed_node_ids": [],
        },
        no_parallel={
            "counts": {"passed": 1, "failed": 0, "errors": 0, "skipped": 0, "total": 1},
            "failed_node_ids": [],
        },
    )

    cache.cache_test_file_suite(test_file, parallel=None, no_parallel=None)

    rel = "tests/development_tools/test_test_file_suite_cache.py"
    entry = cache.cache_data["test_files"][rel]
    assert entry["parallel"]["counts"]["passed"] == 3
    assert entry["no_parallel"]["counts"]["passed"] == 1
