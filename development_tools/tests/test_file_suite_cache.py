#!/usr/bin/env python3
"""
Test-file-based suite result cache for run_test_suite.

Reuses domain invalidation from TestFileCoverageCache (source mtimes, test-file
set drift, config/tool hashes, failure-aware bust) and stores per-test-file pytest
outcomes so Tier 3 audits can skip unchanged domains.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from development_tools.shared.logging import get_dev_tools_logger

    logger = get_dev_tools_logger("development_tools")
except ImportError:
    logger = None

from development_tools.shared.cache_dependency_paths import (
    coverage_config_paths,
    static_check_config_paths,
)
from development_tools.shared.time_helpers import now_timestamp_full
from development_tools.tests.test_file_coverage_cache import TestFileCoverageCache


class TestFileSuiteCache:
    """Domain-scoped cache for pytest suite outcomes (no coverage data)."""

    FULL_SUITE_KEY = "_full_suite_snapshot"
    # Runner/cache helpers: editing these must not force every product domain to rerun.
    RUNNER_HELPER_NAMES = frozenset(
        {
            "run_test_suite.py",
            "test_file_suite_cache.py",
            "pytest_isolation.py",
        }
    )

    def __init__(
        self,
        project_root: Path,
        cache_dir: Path | None = None,
        mapper_config: dict[str, Any] | None = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.coverage_cache = TestFileCoverageCache(
            self.project_root,
            cache_dir,
            mapper_config=mapper_config,
        )
        self.cache_dir = self.coverage_cache.cache_dir
        self.cache_file = self.cache_dir / "test_file_suite_cache.json"
        self.tool_paths = self._get_default_tool_paths()
        self.cache_data: dict[str, Any] = {}
        self.last_invalidation_reason: str | None = None
        self._load_cache()

    def _get_default_tool_paths(self) -> tuple[Path, ...]:
        tests_dir = Path(__file__).resolve().parent
        scripts = (
            tests_dir / "run_test_suite.py",
            tests_dir / "test_file_suite_cache.py",
            tests_dir / "pytest_isolation.py",
            tests_dir / "domain_mapper.py",
        )
        combined = (
            *scripts,
            *static_check_config_paths(self.project_root),
            *coverage_config_paths(self.project_root),
        )
        return tuple(path for path in combined if path.exists())

    def _default_cache_data(self) -> dict[str, Any]:
        return {
            "cache_version": "1.0",
            "test_files": {},
            "tool_hash": None,
            "runner_helper_hash": None,
            "structural_tool_hash": None,
            "tool_mtimes": {},
            "last_run_ok": None,
            "last_parallel_ok": None,
            "last_no_parallel_ok": None,
            "last_failed_domains": [],
            "last_run_domains": [],
            "last_run_at": None,
            "last_updated": None,
            "last_suite_profile": None,
        }

    def _load_cache(self) -> None:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, encoding="utf-8") as handle:
                    loaded = json.load(handle)
                if isinstance(loaded, dict):
                    self.cache_data = loaded
            except Exception as exc:
                if logger:
                    logger.warning(f"Failed to load test suite cache: {exc}")
        defaults = self._default_cache_data()
        for key, value in defaults.items():
            if key not in self.cache_data:
                self.cache_data[key] = deepcopy(value)
        if not isinstance(self.cache_data.get("test_files"), dict):
            self.cache_data["test_files"] = {}

    def _save_cache(self) -> None:
        self.cache_data["last_updated"] = now_timestamp_full()
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as handle:
                json.dump(self.cache_data, handle, indent=2)
        except Exception as exc:
            if logger:
                logger.warning(f"Failed to save test suite cache: {exc}")

    def _hash_paths(self, paths: tuple[Path, ...] | list[Path]) -> str | None:
        if not paths:
            return None
        hasher = hashlib.sha256()
        has_data = False
        for path in paths:
            try:
                if not path.exists() or not path.is_file():
                    continue
                hasher.update(path.read_bytes())
                has_data = True
            except Exception:
                return None
        return hasher.hexdigest() if has_data else None

    def _compute_tool_hash(self) -> str | None:
        return self._hash_paths(self.tool_paths)

    def _partition_tool_paths(self) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
        helpers: list[Path] = []
        structural: list[Path] = []
        for path in self.tool_paths:
            if path.name in self.RUNNER_HELPER_NAMES:
                helpers.append(path)
            else:
                structural.append(path)
        return tuple(helpers), tuple(structural)

    def _store_tool_hashes(self) -> None:
        helpers, structural = self._partition_tool_paths()
        helper_hash = self._hash_paths(helpers)
        structural_hash = self._hash_paths(structural)
        combined = self._compute_tool_hash()
        if helper_hash:
            self.cache_data["runner_helper_hash"] = helper_hash
        if structural_hash:
            self.cache_data["structural_tool_hash"] = structural_hash
        if combined:
            self.cache_data["tool_hash"] = combined

    @staticmethod
    def _hash_changed(current: str | None, cached: str | None) -> bool:
        if current and cached and current != cached:
            return True
        if current and not cached:
            return True
        return bool(cached and not current)

    def _tool_change_kind(self) -> str | None:
        """Classify suite tool drift: None, ``runner_helper``, or ``structural``."""
        helpers, structural = self._partition_tool_paths()
        helper_hash = self._hash_paths(helpers)
        structural_hash = self._hash_paths(structural)
        combined = self._compute_tool_hash()
        cached_helper = self.cache_data.get("runner_helper_hash")
        cached_structural = self.cache_data.get("structural_tool_hash")
        cached_combined = self.cache_data.get("tool_hash")

        # Migrate older caches that only stored the combined tool_hash.
        if cached_helper is None and cached_structural is None:
            if combined and cached_combined == combined:
                self._store_tool_hashes()
                return None
            if self._hash_changed(combined, cached_combined):
                # Prefer soft invalidation: runner/helper edits are the common case.
                return "runner_helper"
            return None

        if self._hash_changed(structural_hash, cached_structural):
            return "structural"
        if self._hash_changed(helper_hash, cached_helper):
            return "runner_helper"
        return None

    def _suite_tool_changed(self) -> bool:
        return self._tool_change_kind() is not None

    def _drop_full_suite_snapshot(self) -> None:
        """Drop aggregate snapshot without saving (caller persists hashes/snapshot)."""
        if self.FULL_SUITE_KEY in self.cache_data:
            self.cache_data.pop(self.FULL_SUITE_KEY, None)

    def _domains_for_runner_helper_change(self) -> set[str]:
        """Re-run tools tests plus any domains the coverage cache already flagged.

        Always include ``development_tools``. Helper edits belong to that suite even
        when a polluted or empty domain map omits the key (xdist config reloads).
        """
        domains = set(self.coverage_cache.get_changed_domains())
        domains.add("development_tools")
        self.last_invalidation_reason = getattr(
            self.coverage_cache, "last_invalidation_reason", None
        )
        if self.last_invalidation_reason:
            self.last_invalidation_reason = (
                f"suite_runner_helper_change+{self.last_invalidation_reason}"
            )
        else:
            self.last_invalidation_reason = "suite_runner_helper_change"
        return domains

    def _all_domains(self) -> set[str]:
        return set(self.coverage_cache.domain_mapper.SOURCE_TO_TEST_MAPPING.keys())

    def get_changed_domains(self, suite_profile: str = "quick") -> set[str]:
        """Return domains that require re-running tests (suite + shared invalidation)."""
        cached_profile = self.cache_data.get("last_suite_profile")
        if cached_profile and str(cached_profile) != str(suite_profile):
            self.last_invalidation_reason = (
                f"suite_profile_change:{cached_profile}->{suite_profile}"
            )
            return self._all_domains()
        change_kind = self._tool_change_kind()
        if change_kind == "structural":
            self.last_invalidation_reason = "suite_tool_change"
            self._drop_full_suite_snapshot()
            self._store_tool_hashes()
            self._save_cache()
            return self._all_domains()
        if change_kind == "runner_helper":
            self._drop_full_suite_snapshot()
            self._store_tool_hashes()
            self._save_cache()
            return self._domains_for_runner_helper_change()
        if (
            self.cache_data.get("last_run_ok") is False
            or self.cache_data.get("last_parallel_ok") is False
        ):
            return self._domains_for_previous_suite_failure()
        self.last_invalidation_reason = getattr(
            self.coverage_cache, "last_invalidation_reason", None
        )
        return self.coverage_cache.get_changed_domains()

    def get_test_files_to_run(self, changed_domains: set[str]) -> list[Path]:
        return self.coverage_cache.get_test_files_to_run(changed_domains)

    def get_full_suite_cache(self) -> dict[str, Any] | None:
        snapshot = self.cache_data.get(self.FULL_SUITE_KEY)
        return snapshot if isinstance(snapshot, dict) else None

    def clear_full_suite_cache(self) -> None:
        """Drop the cached full-suite snapshot after a non-clean pytest run."""
        if self.FULL_SUITE_KEY in self.cache_data:
            self.cache_data.pop(self.FULL_SUITE_KEY, None)
            self._save_cache()

    def can_reuse_full_suite_cache(self, suite_profile: str = "quick") -> bool:
        """Return True only when the last suite run succeeded and a snapshot exists."""
        if self.cache_data.get("last_suite_profile") != suite_profile:
            return False
        if self.cache_data.get("last_run_ok") is False:
            return False
        if self.cache_data.get("last_parallel_ok") is False:
            return False
        return self.get_full_suite_cache() is not None

    def _domains_for_previous_suite_failure(self) -> set[str]:
        failed_domains = {
            d
            for d in (self.cache_data.get("last_failed_domains") or [])
            if isinstance(d, str) and d
        }
        if failed_domains:
            self.last_invalidation_reason = (
                "previous_suite_run_failed: failed domains from previous suite run"
            )
            return failed_domains
        run_domains = {
            d
            for d in (self.cache_data.get("last_run_domains") or [])
            if isinstance(d, str) and d
        }
        if run_domains:
            self.last_invalidation_reason = (
                "previous_suite_run_failed: run domains from previous suite run"
            )
            return run_domains
        self.last_invalidation_reason = (
            "previous_suite_run_failed: no failed-domain mapping available"
        )
        return self._all_domains()

    def cache_full_suite(self, snapshot: dict[str, Any]) -> None:
        self.cache_data[self.FULL_SUITE_KEY] = snapshot
        self._save_cache()

    def cache_test_file_suite(
        self,
        test_file: Path,
        *,
        parallel: dict[str, Any] | None = None,
        no_parallel: dict[str, Any] | None = None,
    ) -> None:
        rel = TestFileCoverageCache._normalize_test_file_rel(
            str(test_file.relative_to(self.project_root))
        )
        existing = self.cache_data.setdefault("test_files", {}).get(rel)
        existing_entry = existing if isinstance(existing, dict) else {}
        domains = sorted(self.coverage_cache.get_test_files_domains(test_file))
        entry: dict[str, Any] = {
            "domains": domains,
            "last_run": datetime.now().isoformat(),
        }
        if parallel is not None:
            entry["parallel"] = parallel
        elif existing_entry.get("parallel"):
            entry["parallel"] = existing_entry["parallel"]
        if no_parallel is not None:
            entry["no_parallel"] = no_parallel
        elif existing_entry.get("no_parallel"):
            entry["no_parallel"] = existing_entry["no_parallel"]
        self.cache_data["test_files"][rel] = entry
        self.coverage_cache.update_test_file_mapping(test_file, save_cache=True)
        self._save_cache()

    def get_all_cached_suite_results(
        self, exclude_domains: set[str] | None = None
    ) -> dict[str, dict[str, Any]]:
        if exclude_domains is None:
            exclude_domains = set()
        changed_domains = self.get_changed_domains()
        cached: dict[str, dict[str, Any]] = {}
        for rel, data in (self.cache_data.get("test_files") or {}).items():
            if not isinstance(data, dict):
                continue
            file_domains = set(data.get("domains") or [])
            if file_domains & exclude_domains or file_domains & changed_domains:
                continue
            if data.get("parallel") or data.get("no_parallel"):
                cached[rel] = data
        return cached

    def update_run_status(
        self,
        *,
        parallel_ok: bool | None = None,
        no_parallel_ok: bool | None = None,
        no_parallel_coverage_present: bool | None = None,
        failed_domains: set[str] | None = None,
        run_domains: set[str] | None = None,
        suite_profile: str | None = None,
    ) -> None:
        if parallel_ok is not None:
            self.cache_data["last_parallel_ok"] = bool(parallel_ok)
        if no_parallel_ok is not None:
            self.cache_data["last_no_parallel_ok"] = bool(no_parallel_ok)
        if failed_domains is not None:
            self.cache_data["last_failed_domains"] = sorted(failed_domains)
        if run_domains is not None:
            self.cache_data["last_run_domains"] = sorted(run_domains)
        if suite_profile is not None:
            self.cache_data["last_suite_profile"] = str(suite_profile)
        if parallel_ok is not None or no_parallel_ok is not None:
            self.cache_data["last_run_ok"] = bool(
                (parallel_ok is True)
                and (no_parallel_ok is None or no_parallel_ok is True)
            )
            self.cache_data["last_run_at"] = datetime.now().isoformat()
        self._store_tool_hashes()
        self._save_cache()
        self.coverage_cache.update_run_status(
            parallel_ok=parallel_ok,
            no_parallel_ok=no_parallel_ok,
            no_parallel_coverage_present=no_parallel_coverage_present,
            failed_domains=failed_domains,
            run_domains=run_domains,
        )

    def get_cache_stats(self) -> dict[str, Any]:
        coverage_stats = self.coverage_cache.get_cache_stats()
        changed_domains = self.get_changed_domains()
        test_files_to_run = len(self.get_test_files_to_run(changed_domains))
        cached_entries = sum(
            1
            for data in (self.cache_data.get("test_files") or {}).values()
            if isinstance(data, dict) and (data.get("parallel") or data.get("no_parallel"))
        )
        has_full = self.get_full_suite_cache() is not None
        total = coverage_stats.get("total_test_files", 0)
        cached_count = total if has_full and not changed_domains else cached_entries
        return {
            **coverage_stats,
            "test_files_cached": cached_count,
            "test_files_to_run": test_files_to_run,
            "has_full_suite_cache": has_full,
            "changed_domains": len(changed_domains),
        }
