#!/usr/bin/env python3
"""
Mtime-based File Cache Utility

Provides a reusable caching mechanism for file-based analyzers that checks
file modification times (mtime) to determine if cached results are still valid.

Usage:
    from development_tools.shared.mtime_cache import MtimeFileCache

    cache = MtimeFileCache(
        project_root=project_root,
        use_cache=True,
        tool_name='my_tool',
        domain='docs'
    )

    # Check if file is cached
    cached_results = cache.get_cached(file_path)
    if cached_results is not None:
        # Use cached results
        return cached_results

    # Process file and cache results
    results = process_file(file_path)
    cache.cache_results(file_path, results)
    cache.save_cache()
"""

from pathlib import Path
from typing import Dict, Optional, Any, TypeVar, Iterable, Tuple
import hashlib

T = TypeVar("T")  # Generic type for cached results

try:
    from core.logger import get_component_logger

    logger = get_component_logger("development_tools")
except ImportError:
    logger = None

# Cache metadata key for config file mtime
_CONFIG_MTIME_KEY = "__config_mtime__"
_TOOL_HASH_KEY = "__tool_hash__"


class MtimeFileCache:
    """
    Mtime-based file cache for analyzer results.

    Caches results keyed by file path, with validation based on file modification time.
    Only re-processes files that have been modified since the last cache entry.
    """

    def __init__(
        self,
        project_root: Path,
        use_cache: bool = True,
        tool_name: Optional[str] = None,
        domain: Optional[str] = None,
        tool_paths: Optional[Iterable[Path]] = None,
    ):
        """
        Initialize the cache.

        Args:
            project_root: Root directory of the project (for relative path generation)
            use_cache: Whether to use caching (if False, all operations are no-ops)
            tool_name: Name of the tool (e.g., 'analyze_ascii_compliance') - required for standardized storage
            domain: Domain directory (e.g., 'docs') - required for standardized storage
        """
        if tool_name is None or domain is None:
            raise ValueError("tool_name and domain are required for MtimeFileCache")

        self.project_root = project_root.resolve()
        self.use_cache = use_cache
        self.cache_data: Dict[str, Dict[str, Any]] = {}
        self.tool_name = tool_name
        self.domain = domain
        self.use_standardized_storage = True
        self.tool_paths = self._normalize_tool_paths(tool_paths)

        # Get config file path for cache invalidation
        self.config_file_path = self._get_config_file_path()

        if self.use_cache:
            self._load_cache()
            # Check if config file changed and invalidate cache if needed
            self._check_config_staleness()
            # Check if tool code changed and invalidate cache if needed
            self._check_tool_staleness()

    def _normalize_tool_paths(
        self, tool_paths: Optional[Iterable[Path]]
    ) -> Tuple[Path, ...]:
        """Normalize tool paths to a tuple of resolved Path objects."""
        if not tool_paths:
            return ()
        normalized = []
        for item in tool_paths:
            try:
                path = Path(item).resolve()
                normalized.append(path)
            except Exception:
                continue
        return tuple(normalized)

    def _get_config_file_path(self) -> Optional[Path]:
        """
        Get the path to the development_tools_config.json file.

        Returns:
            Path to config file if found, None otherwise
        """
        try:
            # Try to get the config file path that was actually loaded
            import development_tools.config.config as config_module

            if (
                hasattr(config_module, "_config_file_path")
                and config_module._config_file_path
            ):
                return config_module._config_file_path
        except Exception:
            pass

        # Fallback: try to find it using the same logic as config loading
        try:
            config_file = (
                self.project_root
                / "development_tools"
                / "config"
                / "development_tools_config.json"
            )
            if not config_file.exists():
                config_file = self.project_root / "development_tools_config.json"
            if config_file.exists():
                return config_file
        except Exception:
            pass

        return None

    def _check_config_staleness(self) -> None:
        """
        Check if config file has changed since cache was created.
        If so, clear the cache to force regeneration with new config.
        """
        if not self.config_file_path or not self.config_file_path.exists():
            return

        try:
            # Get current config file mtime
            current_config_mtime = self.config_file_path.stat().st_mtime

            # Check cached config mtime
            cached_config_mtime = None
            if _CONFIG_MTIME_KEY in self.cache_data:
                cached_config_mtime = self.cache_data[_CONFIG_MTIME_KEY].get("mtime")

            # If config file is newer than cached mtime, clear cache
            if (
                cached_config_mtime is not None
                and current_config_mtime > cached_config_mtime
            ):
                if logger:
                    logger.info(
                        f"Config file changed (mtime: {current_config_mtime} > {cached_config_mtime}), "
                        f"invalidating cache for {self.tool_name or 'tool'}"
                    )
                self.clear_cache()
                # Update config mtime in cache immediately
                self._update_config_mtime_in_cache()
            elif cached_config_mtime is None:
                # No cached config mtime (first run or cache was cleared), store current mtime
                self._update_config_mtime_in_cache()
        except Exception as e:
            if logger:
                logger.debug(f"Error checking config file staleness: {e}")

    def _update_config_mtime_in_cache(self) -> None:
        """Store current config file mtime in cache metadata."""
        if not self.config_file_path or not self.config_file_path.exists():
            return

        try:
            config_mtime = self.config_file_path.stat().st_mtime
            self.cache_data[_CONFIG_MTIME_KEY] = {
                "mtime": config_mtime,
                "results": {},  # Empty results, just storing mtime
            }
        except Exception:
            pass

    def _compute_tool_hash(self) -> Optional[str]:
        """Compute a hash for tool source files to detect code changes."""
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

    def _check_tool_staleness(self) -> None:
        """Check if tool code has changed since cache was created."""
        if not self.tool_paths:
            return
        try:
            current_hash = self._compute_tool_hash()
            if not current_hash:
                return

            cached_hash = None
            if _TOOL_HASH_KEY in self.cache_data:
                cached_hash = self.cache_data[_TOOL_HASH_KEY].get("hash")

            if cached_hash is not None and cached_hash != current_hash:
                if logger:
                    logger.info(
                        f"Tool code changed (hash mismatch), invalidating cache for {self.tool_name or 'tool'}"
                    )
                self.clear_cache()
                self._update_tool_hash_in_cache(current_hash)
            elif cached_hash is None:
                self._update_tool_hash_in_cache(current_hash)
        except Exception as e:
            if logger:
                logger.debug(f"Error checking tool code staleness: {e}")

    def _update_tool_hash_in_cache(self, tool_hash: Optional[str] = None) -> None:
        """Store current tool code hash in cache metadata."""
        if not tool_hash:
            tool_hash = self._compute_tool_hash()
        if not tool_hash:
            return
        self.cache_data[_TOOL_HASH_KEY] = {
            "hash": tool_hash,
            "results": {},
        }

    def _load_cache(self) -> None:
        """Load cache from disk if it exists."""
        if self.use_standardized_storage:
            # Use standardized storage
            try:
                from .output_storage import load_tool_cache

                loaded_data = load_tool_cache(
                    self.tool_name, self.domain, project_root=self.project_root
                )
                if loaded_data:
                    # load_tool_cache already extracts data from metadata wrapper, so loaded_data is the cache content
                    migrated_data = {}
                    for key, value in loaded_data.items():
                        if isinstance(value, dict) and "results" in value:
                            migrated_data[key] = value
                    self.cache_data = migrated_data
                    if logger:
                        logger.debug(
                            f"Loaded cache from standardized storage ({self.tool_name}) with {len(self.cache_data)} entries"
                        )
                    return
            except Exception as e:
                if logger:
                    logger.warning(
                        f"Failed to load cache from standardized storage: {e}"
                    )
                # If standardized storage fails, start with empty cache
                # Tools will regenerate cache on next run
                self.cache_data = {}

    def save_cache(self) -> None:
        """Save cache to disk."""
        if not self.use_cache:
            return

        # Update config mtime in cache before saving
        self._update_config_mtime_in_cache()
        # Update tool hash in cache before saving
        self._update_tool_hash_in_cache()

        if self.use_standardized_storage:
            # Use standardized storage
            try:
                from .output_storage import save_tool_cache

                save_tool_cache(
                    self.tool_name,
                    self.domain,
                    self._sanitize_for_json(self.cache_data),
                    project_root=self.project_root,
                )
                if logger:
                    logger.debug(
                        f"Saved cache to standardized storage ({self.tool_name}) with {len(self.cache_data)} entries"
                    )
                return
            except Exception as e:
                if logger:
                    logger.warning(f"Failed to save cache to standardized storage: {e}")
                # If standardized storage fails, log warning but don't fall back to legacy
                # This ensures we fix standardized storage issues rather than silently using legacy paths

    def _get_file_cache_key(self, file_path: Path) -> str:
        """Generate cache key for a file (relative path from project root)."""
        try:
            rel_path = file_path.resolve().relative_to(self.project_root)
            return str(rel_path).replace("\\", "/")
        except ValueError:
            # File is outside project root, use absolute path
            return str(file_path.resolve())

    def _is_file_cached(self, file_path: Path) -> bool:
        """Check if file results are cached and still valid (mtime matches)."""
        if not self.use_cache:
            return False

        cache_key = self._get_file_cache_key(file_path)
        if cache_key not in self.cache_data:
            return False

        cached_mtime = self.cache_data[cache_key].get("mtime")
        if cached_mtime is None:
            return False

        try:
            current_mtime = file_path.stat().st_mtime
            return current_mtime == cached_mtime
        except OSError:
            return False

    def get_cached(self, file_path: Path) -> Optional[T]:
        """
        Get cached results for a file if available and still valid.

        Args:
            file_path: Path to the file to check

        Returns:
            Cached results if available and valid, None otherwise
        """
        if not self._is_file_cached(file_path):
            return None

        cache_key = self._get_file_cache_key(file_path)
        cached_data = self.cache_data[cache_key].get("results")
        return cached_data

    def cache_results(self, file_path: Path, results: T) -> None:
        """
        Cache results for a file.

        Args:
            file_path: Path to the file being cached
            results: Results to cache (must be JSON-serializable)
        """
        if not self.use_cache:
            return

        try:
            cache_key = self._get_file_cache_key(file_path)
            mtime = file_path.stat().st_mtime
            self.cache_data[cache_key] = {"mtime": mtime, "results": results}
        except OSError:
            # File doesn't exist or can't be accessed, skip caching
            if logger:
                logger.warning(
                    f"Failed to cache results for {file_path} (file missing or inaccessible)"
                )
        except Exception as exc:
            if logger:
                logger.warning(f"Failed to cache results for {file_path}: {exc}")

    def clear_cache(self) -> None:
        """Clear all cached data (in memory only, call save_cache() to persist)."""
        self.cache_data = {}

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.

        Returns:
            Dictionary with cache statistics (total_entries, tool_name, domain)
        """
        return {
            "total_entries": len(self.cache_data),
            "tool_name": self.tool_name,
            "domain": self.domain,
        }

    def _sanitize_for_json(self, value: Any) -> Any:
        """Convert non-serializable cache values into JSON-safe structures."""
        if isinstance(value, dict):
            return {k: self._sanitize_for_json(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._sanitize_for_json(v) for v in value]
        if isinstance(value, set):
            return [self._sanitize_for_json(v) for v in sorted(value)]
        if isinstance(value, Path):
            return value.as_posix()
        return value
