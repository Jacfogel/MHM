#!/usr/bin/env python3
"""
Mtime-based File Cache Utility

Provides a reusable caching mechanism for file-based analyzers that checks
file modification times (mtime) to determine if cached results are still valid.

Usage:
    from development_tools.shared.mtime_cache import MtimeFileCache
    
    cache = MtimeFileCache(
        cache_file=project_root / "development_tools" / "docs" / ".my_cache.json",
        project_root=project_root,
        use_cache=True
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

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, TypeVar

T = TypeVar('T')  # Generic type for cached results

try:
    from core.logger import get_component_logger
    logger = get_component_logger("development_tools")
except ImportError:
    logger = None


class MtimeFileCache:
    """
    Mtime-based file cache for analyzer results.
    
    Caches results keyed by file path, with validation based on file modification time.
    Only re-processes files that have been modified since the last cache entry.
    """
    
    def __init__(
        self,
        cache_file: Path,
        project_root: Path,
        use_cache: bool = True,
        tool_name: Optional[str] = None,
        domain: Optional[str] = None
    ):
        """
        Initialize the cache.
        
        Args:
            cache_file: Path to the JSON cache file (legacy - used if tool_name/domain not provided)
            project_root: Root directory of the project (for relative path generation)
            use_cache: Whether to use caching (if False, all operations are no-ops)
            tool_name: Name of the tool (e.g., 'analyze_ascii_compliance') - if provided, uses standardized storage
            domain: Domain directory (e.g., 'docs') - if provided with tool_name, uses standardized storage
        """
        self.cache_file = cache_file
        self.project_root = project_root.resolve()
        self.use_cache = use_cache
        self.cache_data: Dict[str, Dict[str, Any]] = {}
        self.tool_name = tool_name
        self.domain = domain
        self.use_standardized_storage = tool_name is not None and domain is not None
        
        if self.use_cache:
            self._load_cache()
    
    def _load_cache(self) -> None:
        """Load cache from disk if it exists."""
        if self.use_standardized_storage:
            # Use standardized storage
            try:
                from .output_storage import load_tool_cache
                loaded_data = load_tool_cache(self.tool_name, self.domain, project_root=self.project_root)
                if loaded_data:
                    # load_tool_cache already extracts data from metadata wrapper, so loaded_data is the cache content
                    # Migrate old cache format (with 'issues' key) to new format (with 'results' key)
                    migrated_data = {}
                    for key, value in loaded_data.items():
                        if isinstance(value, dict):
                            # Check if it's old format with 'issues' key
                            if 'issues' in value and 'results' not in value:
                                migrated_data[key] = {
                                    'mtime': value.get('mtime'),
                                    'results': value.get('issues', [])
                                }
                            else:
                                # Already in new format or has 'results' key
                                migrated_data[key] = value
                        else:
                            # Invalid format, skip
                            continue
                    self.cache_data = migrated_data
                    if logger:
                        logger.debug(f"Loaded cache from standardized storage ({self.tool_name}) with {len(self.cache_data)} entries")
                    return
            except Exception as e:
                if logger:
                    logger.warning(f"Failed to load cache from standardized storage: {e}")
                # If standardized storage fails, start with empty cache
                # Tools will regenerate cache on next run
                self.cache_data = {}
    
    def save_cache(self) -> None:
        """Save cache to disk."""
        if not self.use_cache:
            return
        
        if self.use_standardized_storage:
            # Use standardized storage
            try:
                from .output_storage import save_tool_cache
                save_tool_cache(self.tool_name, self.domain, self.cache_data, project_root=self.project_root)
                if logger:
                    logger.debug(f"Saved cache to standardized storage ({self.tool_name}) with {len(self.cache_data)} entries")
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
            return str(rel_path).replace('\\', '/')
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
        
        cached_mtime = self.cache_data[cache_key].get('mtime')
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
        cached_data = self.cache_data[cache_key].get('results')
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
            self.cache_data[cache_key] = {
                'mtime': mtime,
                'results': results
            }
        except OSError:
            # File doesn't exist or can't be accessed, skip caching
            pass
    
    def clear_cache(self) -> None:
        """Clear all cached data (in memory only, call save_cache() to persist)."""
        self.cache_data = {}
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics (total_entries, etc.)
        """
        return {
            'total_entries': len(self.cache_data),
            'cache_file': str(self.cache_file)
        }

