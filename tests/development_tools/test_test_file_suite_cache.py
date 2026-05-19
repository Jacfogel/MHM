"""Tests for development_tools.tests.test_file_suite_cache."""

from __future__ import annotations

from pathlib import Path

import pytest

from development_tools.tests.test_file_coverage_cache import TestFileCoverageCache
from development_tools.tests.test_file_suite_cache import TestFileSuiteCache


@pytest.mark.unit
def test_suite_cache_delegates_changed_domains_to_coverage_cache(tmp_path: Path, monkeypatch):
    cache = TestFileSuiteCache(tmp_path)
    cache.cache_data["tool_hash"] = cache._compute_tool_hash()
    expected = {"core", "ai"}
    monkeypatch.setattr(
        cache.coverage_cache, "get_changed_domains", lambda: set(expected)
    )
    assert cache.get_changed_domains() == expected


@pytest.mark.unit
def test_suite_cache_tool_change_invalidates_all_domains(tmp_path: Path):
    cache = TestFileSuiteCache(tmp_path)
    cache.cache_data["tool_hash"] = "stale-hash"
    domains = cache.get_changed_domains()
    assert domains == cache._all_domains()
    assert cache.last_invalidation_reason == "suite_tool_change"


@pytest.mark.unit
def test_cache_and_read_per_file_suite_results(tmp_path: Path, monkeypatch):
    cache = TestFileSuiteCache(tmp_path)
    monkeypatch.setattr(cache, "get_changed_domains", lambda: set())
    tests_dir = tmp_path / "tests" / "unit"
    tests_dir.mkdir(parents=True)
    test_file = tests_dir / "test_sample.py"
    test_file.write_text(
        'import pytest\n\n@pytest.mark.unit\ndef test_ok():\n    assert True\n',
        encoding="utf-8",
    )
    cache.cache_test_file_suite(
        test_file,
        parallel={"counts": {"total": 1, "passed": 1, "failed": 0, "errors": 0, "skipped": 0}, "failed_node_ids": []},
    )
    rel = TestFileCoverageCache._normalize_test_file_rel(
        str(test_file.relative_to(tmp_path))
    )
    stored = cache.cache_data["test_files"][rel]
    assert stored["parallel"]["counts"]["passed"] == 1
    cached = cache.get_all_cached_suite_results()
    assert rel in cached
