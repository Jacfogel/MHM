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
from typing import Generic, Any, Literal, NamedTuple, TypeVar
from collections.abc import Iterable
import hashlib

T = TypeVar("T")  # Generic type for cached results
ConfigIdentityVerdict = Literal["missing", "first_seen", "unchanged", "content_changed"]


class ConfigIdentity(NamedTuple):
    """Result of hybrid config mtime + content-hash comparison."""

    mtime: float | None
    content_hash: str | None
    verdict: ConfigIdentityVerdict


def hash_file_sha256(path: Path) -> str | None:
    """Return the SHA-256 hex digest of ``path``, or None if it cannot be read."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        return None


def resolve_config_identity(
    config_path: Path | None,
    *,
    cached_mtime: float | None,
    cached_hash: str | None,
) -> ConfigIdentity:
    """Decide whether config *content* changed.

    ``mtime`` is a cheap first check. Bytes are hashed only when mtime differs
    or when the cache has no hash yet (backfill). A rewrite that only updates
    the timestamp does not count as a change.
    """
    if config_path is None:
        return ConfigIdentity(None, None, "missing")
    try:
        if not config_path.exists():
            return ConfigIdentity(None, None, "missing")
        current_mtime = config_path.stat().st_mtime
    except OSError:
        return ConfigIdentity(None, None, "missing")

    cached_hash_value = cached_hash if isinstance(cached_hash, str) and cached_hash else None
    has_cached_mtime = isinstance(cached_mtime, (int, float))
    mtime_matches = has_cached_mtime and current_mtime == cached_mtime

    if not has_cached_mtime and cached_hash_value is None:
        return ConfigIdentity(current_mtime, hash_file_sha256(config_path), "first_seen")

    if mtime_matches:
        if cached_hash_value is not None:
            return ConfigIdentity(current_mtime, cached_hash_value, "unchanged")
        return ConfigIdentity(current_mtime, hash_file_sha256(config_path), "unchanged")

    current_hash = hash_file_sha256(config_path)
    if cached_hash_value is not None and current_hash is not None and cached_hash_value == current_hash:
        return ConfigIdentity(current_mtime, current_hash, "unchanged")
    return ConfigIdentity(current_mtime, current_hash, "content_changed")

try:
    from development_tools.shared.logging import get_dev_tools_logger

    logger = get_dev_tools_logger("development_tools")
except ImportError:
    logger = None

# Cache metadata key for config file mtime
_CONFIG_MTIME_KEY = "__config_mtime__"
_TOOL_HASH_KEY = "__tool_hash__"
_TOOL_MTIMES_KEY = "__tool_mtimes__"
_RUN_STATUS_KEY = "__run_status__"


class MtimeFileCache(Generic[T]):
    """
    Mtime-based file cache for analyzer results.

    Caches results keyed by file path, with validation based on file modification time.
    Only re-processes files that have been modified since the last cache entry.
    """

    def __init__(
        self,
        project_root: Path,
        use_cache: bool = True,
        tool_name: str | None = None,
        domain: str | None = None,
        tool_paths: Iterable[Path] | None = None,
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
        self.cache_data: dict[str, dict[str, Any]] = {}
        self.tool_name = tool_name
        self.domain = domain
        self.use_standardized_storage = True
        self.tool_paths = self._normalize_tool_paths(tool_paths)

        # Get config file path for cache invalidation
        self.config_file_path = self._get_config_file_path()
        self._cache_namespace = self._build_cache_namespace()

        if self.use_cache:
            self._load_cache()
            # Check if config file changed and invalidate cache if needed
            self._check_config_staleness()
            # Check if tool code changed and invalidate cache if needed
            self._check_tool_staleness()
            # Check if previous run failed and invalidate cache
            self._check_previous_failure_staleness()

    def _normalize_tool_paths(
        self, tool_paths: Iterable[Path] | None
    ) -> tuple[Path, ...]:
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

    def _get_config_file_path(self) -> Path | None:
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

    def _cached_config_identity(self) -> tuple[float | None, str | None]:
        """Return (mtime, hash) stored in cache metadata."""
        meta = self.cache_data.get(_CONFIG_MTIME_KEY)
        if not isinstance(meta, dict):
            return None, None
        mtime = meta.get("mtime")
        content_hash = meta.get("hash")
        return (
            mtime if isinstance(mtime, (int, float)) else None,
            content_hash if isinstance(content_hash, str) else None,
        )

    def _check_config_staleness(self) -> None:
        """
        Clear the cache when config *content* changes.

        A newer mtime with the same bytes (save/format/copy) is not a change.
        """
        if not self.config_file_path or not self.config_file_path.exists():
            return

        try:
            cached_mtime, cached_hash = self._cached_config_identity()
            identity = resolve_config_identity(
                self.config_file_path,
                cached_mtime=cached_mtime,
                cached_hash=cached_hash,
            )
            if identity.verdict == "content_changed":
                if logger:
                    logger.info(
                        "Config file content changed, invalidating cache for "
                        f"{self.tool_name or 'tool'}"
                    )
                self.clear_cache()
            self._store_config_identity(identity)
        except Exception as e:
            if logger:
                logger.debug(f"Error checking config file staleness: {e}")

    def _compute_config_signature(self) -> str:
        """
        Compute a stable signature for config file content.

        Falls back to file mtime when content hashing fails.
        """
        if not self.config_file_path or not self.config_file_path.exists():
            return "no_config"

        config_hash = hash_file_sha256(self.config_file_path)
        if config_hash:
            return config_hash[:16]
        try:
            return f"mtime:{self.config_file_path.stat().st_mtime}"
        except Exception:
            return "config_unavailable"

    def _build_cache_namespace(self) -> str:
        """Build namespace that scopes cache keys to tool/domain/config/tool-code inputs."""
        config_sig = self._compute_config_signature()
        tool_hash = self._compute_tool_hash() or "no_tool_hash"
        return f"{self.tool_name}|{self.domain}|cfg:{config_sig}|tool:{tool_hash[:16]}"

    def _store_config_identity(self, identity: ConfigIdentity) -> None:
        """Store current config mtime and content hash in cache metadata."""
        if identity.verdict == "missing":
            return
        self.cache_data[_CONFIG_MTIME_KEY] = {
            "mtime": identity.mtime,
            "hash": identity.content_hash,
            "results": {},
        }

    def _update_config_mtime_in_cache(self) -> None:
        """Store current config file mtime and content hash in cache metadata."""
        if not self.config_file_path or not self.config_file_path.exists():
            return
        cached_mtime, cached_hash = self._cached_config_identity()
        self._store_config_identity(
            resolve_config_identity(
                self.config_file_path,
                cached_mtime=cached_mtime,
                cached_hash=cached_hash,
            )
        )

    def _compute_tool_hash(self) -> str | None:
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

    def _get_tool_mtimes(self) -> dict[str, float]:
        """Return mtimes for tool source files for debug/traceability."""
        mtimes: dict[str, float] = {}
        for path in self.tool_paths:
            try:
                if not path.exists():
                    continue
                key = str(path.relative_to(self.project_root)).replace("\\", "/")
                mtimes[key] = path.stat().st_mtime
            except Exception:
                continue
        return mtimes

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
                self._update_tool_metadata_in_cache(current_hash)
            elif cached_hash is None:
                self._update_tool_metadata_in_cache(current_hash)
        except Exception as e:
            if logger:
                logger.debug(f"Error checking tool code staleness: {e}")

    def _update_tool_metadata_in_cache(self, tool_hash: str | None = None) -> None:
        """Store current tool code hash and mtimes in cache metadata."""
        if not tool_hash:
            tool_hash = self._compute_tool_hash()
        if tool_hash:
            self.cache_data[_TOOL_HASH_KEY] = {
                "hash": tool_hash,
                "results": {},
            }
        self.cache_data[_TOOL_MTIMES_KEY] = {
            "mtimes": self._get_tool_mtimes(),
            "results": {},
        }

    def _check_previous_failure_staleness(self) -> None:
        """Invalidate cache when previous run status indicates failure."""
        run_status = self.cache_data.get(_RUN_STATUS_KEY, {})
        if not isinstance(run_status, dict):
            return
        status = run_status.get("status")
        if status != "failed":
            return

        reason = run_status.get("error") or "previous run failed"
        if logger:
            logger.info(
                f"Previous cached run failed for {self.tool_name}; invalidating cache ({reason})"
            )
        self.clear_cache()
        self.mark_run_result(success=True)

    def mark_run_result(self, success: bool, error: str | None = None) -> None:
        """Persist last run status for failure-aware invalidation."""
        self.cache_data[_RUN_STATUS_KEY] = {
            "status": "success" if success else "failed",
            "error": (error or "")[:500] if not success else "",
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
                        if isinstance(value, dict) and (
                            "results" in value or key.startswith("__")
                        ):
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
        self._update_tool_metadata_in_cache()
        # If run status has not been set explicitly, default to success on save.
        if _RUN_STATUS_KEY not in self.cache_data:
            self.mark_run_result(success=True)

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
                # If standardized storage fails, log warning but do not silently use alternate paths.
                # This keeps storage issues visible and forces explicit remediation.

    def _get_file_cache_key(self, file_path: Path) -> str:
        """Generate cache key for a file (relative path from project root)."""
        try:
            rel_path = file_path.resolve().relative_to(self.project_root)
            rel_path_str = str(rel_path).replace("\\", "/")
        except ValueError:
            # File is outside project root, use absolute path
            rel_path_str = str(file_path.resolve())
        return f"{self._cache_namespace}|{rel_path_str}"

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

    def get_cached(self, file_path: Path) -> T | None:
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

    def get_cache_stats(self) -> dict[str, Any]:
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
