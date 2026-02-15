#!/usr/bin/env python3
"""
Dev Tools Coverage Cache

Caches coverage JSON for development_tools to avoid re-running tests when
development_tools source files have not changed.
"""

import json
import os
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from core.time_utilities import now_timestamp_full, now_timestamp_filename

# Try to import file locking (Unix/Linux)
try:
    import fcntl

    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

# Try to import Windows file locking
try:
    import msvcrt

    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False

try:
    from core.logger import get_component_logger

    logger = get_component_logger("development_tools")
except ImportError:
    logger = None


class DevToolsCoverageCache:
    """
    Cache for development_tools coverage data.

    Stores:
    - source_files_mtime: map of dev_tools files to mtimes
    - coverage_json: coverage report JSON payload
    """

    def __init__(self, project_root: Path, cache_dir: Optional[Path] = None):
        self.project_root = Path(project_root).resolve()
        if cache_dir is None:
            cache_dir = self.project_root / "development_tools" / "tests" / "jsons"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache_file = self.cache_dir / "dev_tools_coverage_cache.json"
        self.cache_data: Dict[str, Any] = {}
        self.tool_paths = self._get_default_tool_paths()
        self._load_cache()

    def _get_default_tool_paths(self) -> Tuple[Path, ...]:
        """Return tool paths used to compute cache invalidation hash."""
        tool_files = [
            self.project_root / "development_tools" / "tests" / "run_test_coverage.py",
            self.project_root
            / "development_tools"
            / "tests"
            / "dev_tools_coverage_cache.py",
        ]
        return tuple(path for path in tool_files if path.exists())

    def _compute_tool_hash(self) -> Optional[str]:
        """Compute a hash for coverage tool source files."""
        if not self.tool_paths:
            return None
        hasher = hashlib.sha256()
        has_data = False
        for path in self.tool_paths:
            try:
                if not path.exists() or not path.is_file():
                    continue
                hasher.update(path.read_bytes())
                has_data = True
            except Exception:
                return None
        return hasher.hexdigest() if has_data else None

    def _get_tool_mtimes(self) -> Dict[str, float]:
        """Return mtimes for tool source files."""
        mtimes: Dict[str, float] = {}
        for path in self.tool_paths:
            try:
                if not path.exists():
                    continue
                mtimes[str(path.relative_to(self.project_root))] = path.stat().st_mtime
            except Exception:
                continue
        return mtimes

    def _load_cache(self) -> None:
        """Load cache from disk with file locking for thread safety."""
        if self.cache_file.exists():
            try:
                max_retries = 5
                retry_delay = 0.1
                for attempt in range(max_retries):
                    try:
                        with open(self.cache_file, "r", encoding="utf-8") as f:
                            if HAS_FCNTL:
                                try:
                                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                                except (OSError, AttributeError):
                                    pass
                            elif HAS_MSVCRT:
                                try:
                                    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                                except (OSError, AttributeError):
                                    pass

                            self.cache_data = json.load(f)

                            if HAS_FCNTL:
                                try:
                                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                                except (OSError, AttributeError):
                                    pass
                            elif HAS_MSVCRT:
                                try:
                                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                                except (OSError, AttributeError):
                                    pass
                            break
                    except (IOError, OSError):
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            raise
            except Exception as e:
                if logger:
                    logger.warning(f"Failed to load dev tools coverage cache: {e}")
                self.cache_data = {}
        else:
            self.cache_data = {
                "cache_version": "1.0",
                "source_files_mtime": {},
                "test_files_mtime": {},
                "config_mtime": None,
                "tool_hash": None,
                "tool_mtimes": {},
                "coverage_json": None,
                "last_run_ok": None,
                "last_exit_code": None,
                "last_run_at": None,
                "last_updated": None,
            }

    def _save_cache(self) -> None:
        """Save cache to disk with file locking and atomic write for thread safety."""
        try:
            timestamp_str = now_timestamp_full()
            timestamp_iso = now_timestamp_filename()
            self.cache_data["last_updated"] = timestamp_iso
            self.cache_data["last_updated_readable"] = timestamp_str
            self.cache_data["generated_by"] = (
                "DevToolsCoverageCache - Development Tools"
            )
            self.cache_data["note"] = (
                "This file is auto-generated. Do not edit manually."
            )
            self.cache_data["tool_hash"] = self._compute_tool_hash()
            self.cache_data["tool_mtimes"] = self._get_tool_mtimes()

            temp_file = self.cache_file.with_suffix(".tmp")
            max_retries = 5
            retry_delay = 0.1

            for attempt in range(max_retries):
                try:
                    with open(temp_file, "w", encoding="utf-8") as f:
                        if HAS_FCNTL:
                            try:
                                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                            except (OSError, AttributeError):
                                pass
                        elif HAS_MSVCRT:
                            try:
                                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                            except (OSError, AttributeError):
                                pass

                        json.dump(self.cache_data, f, indent=2)
                        f.flush()
                        os.fsync(f.fileno())

                        if HAS_FCNTL:
                            try:
                                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                            except (OSError, AttributeError):
                                pass
                        elif HAS_MSVCRT:
                            try:
                                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                            except (OSError, AttributeError):
                                pass

                    temp_file.replace(self.cache_file)
                    break
                except (IOError, OSError):
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise
        except Exception as e:
            if logger:
                logger.warning(f"Failed to save dev tools coverage cache: {e}")

    def get_cached_coverage(self) -> Optional[Dict[str, Any]]:
        """Return cached coverage JSON if available."""
        coverage_json = self.cache_data.get("coverage_json")
        return coverage_json if isinstance(coverage_json, dict) else None

    def get_cached_mtimes(self) -> Dict[str, float]:
        """Return cached source file mtimes."""
        return self.cache_data.get("source_files_mtime", {}) or {}

    def get_cached_test_mtimes(self) -> Dict[str, float]:
        """Return cached test file mtimes."""
        return self.cache_data.get("test_files_mtime", {}) or {}

    def get_cached_config_mtime(self) -> Optional[float]:
        """Return cached config file mtime."""
        config_mtime = self.cache_data.get("config_mtime")
        return config_mtime if isinstance(config_mtime, (int, float)) else None

    def get_last_run_ok(self) -> Optional[bool]:
        """Return whether the last dev tools coverage run succeeded."""
        last_run_ok = self.cache_data.get("last_run_ok")
        return last_run_ok if isinstance(last_run_ok, bool) else None

    def get_tool_change_reason(self) -> Optional[str]:
        """Return explicit tool-change reason when cached tool metadata is stale."""
        current_hash = self._compute_tool_hash()
        if not current_hash:
            return None
        cached_hash = self.cache_data.get("tool_hash")
        if cached_hash is None:
            return "tool hash missing from dev tools cache metadata"
        if not isinstance(cached_hash, str):
            return "tool hash in dev tools cache metadata has invalid type"
        if current_hash != cached_hash:
            return (
                "tool hash mismatch "
                f"(cached={cached_hash[:12]}, current={current_hash[:12]})"
            )
        return None

    def update_run_status(self, last_run_ok: bool, last_exit_code: Optional[int]) -> None:
        """Record dev tools coverage run status without modifying coverage data."""
        self.cache_data["last_run_ok"] = bool(last_run_ok)
        self.cache_data["last_exit_code"] = (
            int(last_exit_code) if last_exit_code is not None else None
        )
        self.cache_data["last_run_at"] = now_timestamp_filename()
        self._save_cache()

    def update_cache(
        self,
        coverage_json: Dict[str, Any],
        source_mtimes: Dict[str, float],
        test_mtimes: Optional[Dict[str, float]] = None,
        config_mtime: Optional[float] = None,
        last_run_ok: Optional[bool] = None,
        last_exit_code: Optional[int] = None,
    ) -> None:
        """Update cache with new coverage data and source mtimes."""
        self.cache_data["coverage_json"] = coverage_json
        self.cache_data["source_files_mtime"] = source_mtimes
        if test_mtimes is not None:
            self.cache_data["test_files_mtime"] = test_mtimes
        if config_mtime is not None:
            self.cache_data["config_mtime"] = config_mtime
        if last_run_ok is not None:
            self.cache_data["last_run_ok"] = bool(last_run_ok)
        if last_exit_code is not None:
            self.cache_data["last_exit_code"] = int(last_exit_code)
        if last_run_ok is not None or last_exit_code is not None:
            self.cache_data["last_run_at"] = now_timestamp_filename()
        self._save_cache()
