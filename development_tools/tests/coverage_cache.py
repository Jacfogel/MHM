#!/usr/bin/env python3
"""
Domain-Aware Coverage Cache

Provides domain-aware caching for test coverage data, enabling granular cache invalidation.
When source files in a domain change, only that domain's cache is invalidated, not the entire
test suite.

This is a proof-of-concept implementation demonstrating the domain-aware caching approach.
Full integration with run_test_coverage.py would require additional changes to support
partial test execution and coverage data merging.

Usage:
    from development_tools.tests.coverage_cache import DomainAwareCoverageCache
    
    cache = DomainAwareCoverageCache(project_root)
    changed_domains = cache.get_changed_domains()
    if changed_domains:
        # Only re-run tests for changed domains
        # Merge cached data from unchanged domains with fresh data
"""

import json
from pathlib import Path
from typing import Dict, Optional, Set, Any
from datetime import datetime

try:
    from core.logger import get_component_logger
    logger = get_component_logger("development_tools")
except ImportError:
    logger = None

from .domain_mapper import DomainMapper


class DomainAwareCoverageCache:
    """
    Domain-aware cache for test coverage data.
    
    Tracks source file modification times per domain and only invalidates cache
    for domains with changed source files.
    """
    
    def __init__(self, project_root: Path, cache_dir: Optional[Path] = None):
        """
        Initialize domain-aware coverage cache.
        
        Args:
            project_root: Root directory of the project
            cache_dir: Optional cache directory (default: development_tools/tests/.coverage_cache/)
        """
        self.project_root = Path(project_root).resolve()
        self.domain_mapper = DomainMapper(self.project_root)
        
        if cache_dir is None:
            cache_dir = self.project_root / 'development_tools' / 'tests' / '.coverage_cache'
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_file = self.cache_dir / 'domain_coverage_cache.json'
        self.cache_data: Dict[str, Any] = {}
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache_data = json.load(f)
                if logger:
                    logger.debug(f"Loaded domain coverage cache with {len(self.cache_data.get('domains', {}))} domains")
            except Exception as e:
                if logger:
                    logger.warning(f"Failed to load domain coverage cache: {e}")
                self.cache_data = {}
        else:
            self.cache_data = {
                'cache_version': '1.0',
                'domains': {},
                'last_updated': None
            }
    
    def _save_cache(self) -> None:
        """Save cache to disk."""
        try:
            self.cache_data['last_updated'] = datetime.now().isoformat()
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2)
            if logger:
                logger.debug(f"Saved domain coverage cache")
        except Exception as e:
            if logger:
                logger.warning(f"Failed to save domain coverage cache: {e}")
    
    def get_source_file_mtimes(self, domain: str) -> Dict[str, float]:
        """
        Get current modification times for all source files in a domain.
        
        Args:
            domain: Domain name (e.g., 'core')
            
        Returns:
            Dictionary mapping file paths to modification times
        """
        mtimes = {}
        source_dir = self.project_root / domain
        if not source_dir.exists():
            return mtimes
        
        # Get all Python files in the domain
        for py_file in source_dir.rglob('*.py'):
            try:
                rel_path = str(py_file.relative_to(self.project_root))
                mtime = py_file.stat().st_mtime
                mtimes[rel_path] = mtime
            except OSError:
                continue
        
        return mtimes
    
    def get_changed_domains(self) -> Set[str]:
        """
        Get set of domains that have changed source files.
        
        Returns:
            Set of domain names with changes
        """
        changed_domains = set()
        domains = self.cache_data.get('domains', {})
        
        for domain_name, domain_data in domains.items():
            cached_mtimes = domain_data.get('source_files_mtime', {})
            current_mtimes = self.get_source_file_mtimes(domain_name)
            
            # Check if any files changed
            for file_path, current_mtime in current_mtimes.items():
                cached_mtime = cached_mtimes.get(file_path)
                if cached_mtime is None or current_mtime != cached_mtime:
                    changed_domains.add(domain_name)
                    break
        
        return changed_domains
    
    def get_unchanged_domains(self) -> Set[str]:
        """
        Get set of domains that have no changed source files.
        
        Returns:
            Set of domain names without changes
        """
        all_domains = set(self.cache_data.get('domains', {}).keys())
        changed = self.get_changed_domains()
        return all_domains - changed
    
    def get_cached_coverage_for_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Get cached coverage data for a domain.
        
        Args:
            domain: Domain name
            
        Returns:
            Cached coverage data or None if not cached or invalid
        """
        domains = self.cache_data.get('domains', {})
        if domain not in domains:
            return None
        
        # Check if domain has changed
        if domain in self.get_changed_domains():
            return None
        
        return domains[domain].get('coverage_data')
    
    def cache_coverage_for_domain(self, domain: str, coverage_data: Dict[str, Any]) -> None:
        """
        Cache coverage data for a domain.
        
        Args:
            domain: Domain name
            coverage_data: Coverage data to cache
        """
        if 'domains' not in self.cache_data:
            self.cache_data['domains'] = {}
        
        # Get current source file mtimes
        source_mtimes = self.get_source_file_mtimes(domain)
        
        # Get test domains and markers for this source domain
        test_dirs = self.domain_mapper.get_test_domains_for_source(f"{domain}/dummy.py")
        markers = self.domain_mapper.get_markers_for_source(f"{domain}/dummy.py")
        
        self.cache_data['domains'][domain] = {
            'source_files_mtime': source_mtimes,
            'coverage_data': coverage_data,
            'test_domains': test_dirs,
            'test_markers': list(markers),
            'last_coverage_run': datetime.now().isoformat()
        }
        
        self._save_cache()
    
    def clear_domain_cache(self, domain: str) -> None:
        """
        Clear cache for a specific domain.
        
        Args:
            domain: Domain name
        """
        domains = self.cache_data.get('domains', {})
        if domain in domains:
            del domains[domain]
            self._save_cache()
    
    def clear_all_cache(self) -> None:
        """Clear all cached data."""
        self.cache_data = {
            'cache_version': '1.0',
            'domains': {},
            'last_updated': None
        }
        self._save_cache()
        if logger:
            logger.info("Cleared all domain coverage cache")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        domains = self.cache_data.get('domains', {})
        changed = self.get_changed_domains()
        unchanged = self.get_unchanged_domains()
        
        total_files = sum(
            len(domain_data.get('source_files_mtime', {}))
            for domain_data in domains.values()
        )
        
        return {
            'total_domains': len(domains),
            'changed_domains': len(changed),
            'unchanged_domains': len(unchanged),
            'total_tracked_files': total_files,
            'cache_version': self.cache_data.get('cache_version', 'unknown'),
            'last_updated': self.cache_data.get('last_updated')
        }
