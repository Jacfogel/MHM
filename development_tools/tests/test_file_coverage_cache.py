#!/usr/bin/env python3
"""
Test-File-Based Coverage Cache

Provides test-file-based caching for test coverage data, enabling granular cache invalidation.
Each test file is associated with one or more domains. When source files in a domain change,
only test files that cover that domain need to be re-run.

This approach is more granular than domain-based caching and provides real time savings:
- When a domain changes, only test files covering that domain are invalidated
- Only those test files need to be re-run
- Cached coverage from unchanged test files is merged with fresh coverage from re-run test files

Usage:
    from development_tools.tests.test_file_coverage_cache import TestFileCoverageCache
    
    cache = TestFileCoverageCache(project_root)
    changed_domains = cache.get_changed_domains()
    test_files_to_run = cache.get_test_files_to_run(changed_domains)
    # Run only test_files_to_run
    # Merge cached coverage from other test files with fresh coverage
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Optional, Set, Any, List
from datetime import datetime

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

from .domain_mapper import DomainMapper


class TestFileCoverageCache:
    """
    Test-file-based cache for test coverage data.
    
    Tracks:
    - Source file modification times per domain (to detect changes)
    - Test file -> domains mapping (which domains each test file covers)
    - Test file -> coverage data (coverage data from each test file)
    
    When a domain changes, invalidates cache for all test files that cover that domain.
    """
    
    def __init__(self, project_root: Path, cache_dir: Optional[Path] = None):
        """
        Initialize test-file-based coverage cache.
        
        Args:
            project_root: Root directory of the project
            cache_dir: Optional cache directory (default: development_tools/tests/jsons/)
        """
        self.project_root = Path(project_root).resolve()
        self.domain_mapper = DomainMapper(self.project_root)
        self.test_root = self.project_root / 'tests'
        
        if cache_dir is None:
            # Store cache file in jsons/ directory like other JSON files
            cache_dir = self.project_root / 'development_tools' / 'tests' / 'jsons'
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_file = self.cache_dir / 'test_file_coverage_cache.json'
        self.cache_data: Dict[str, Any] = {}
        self._load_cache()
        
        # Full coverage JSON cache (for when no domains change)
        self.full_coverage_cache_key = '_full_coverage_json'
        
        # Directories to exclude when discovering test files (test data, temp files, etc.)
        self.excluded_test_dirs = [
            'tests/data',  # Test data directory - contains temporary test data files
        ]
    
    def is_valid_test_file(self, test_file: Path) -> bool:
        """
        Check if a file is a valid test file (not test data or temporary file).
        
        Args:
            test_file: Path to potential test file
            
        Returns:
            True if file should be included, False if it should be excluded
        """
        test_file_rel = str(test_file.relative_to(self.project_root))
        
        # Exclude files in test data directories
        for excluded_dir in self.excluded_test_dirs:
            excluded_path = Path(excluded_dir)
            if test_file.is_relative_to(self.project_root / excluded_path):
                return False
        
        return True
    
    def _load_cache(self) -> None:
        """Load cache from disk with file locking for thread safety."""
        if self.cache_file.exists():
            try:
                max_retries = 5
                retry_delay = 0.1
                for attempt in range(max_retries):
                    try:
                        with open(self.cache_file, 'r', encoding='utf-8') as f:
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
                            
                            if logger:
                                test_files_count = len(self.cache_data.get('test_files', {}))
                                logger.debug(f"Loaded test-file coverage cache with {test_files_count} test files")
                            break
                    except (IOError, OSError) as e:
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            raise
            except Exception as e:
                if logger:
                    logger.warning(f"Failed to load test-file coverage cache: {e}")
                self.cache_data = {}
        else:
            self.cache_data = {
                'cache_version': '2.0',
                'source_files_mtime': {},  # domain -> {file_path: mtime}
                'test_files': {},  # test_file_path -> {domains: [], coverage_data: {}, last_run: timestamp}
                'last_updated': None
            }
    
    def _save_cache(self) -> None:
        """Save cache to disk with file locking and atomic write for thread safety."""
        try:
            timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            timestamp_iso = datetime.now().isoformat()
            self.cache_data['last_updated'] = timestamp_iso
            self.cache_data['last_updated_readable'] = timestamp_str
            self.cache_data['generated_by'] = 'TestFileCoverageCache - Development Tools'
            self.cache_data['note'] = 'This file is auto-generated. Do not edit manually.'
            
            temp_file = self.cache_file.with_suffix('.tmp')
            max_retries = 5
            retry_delay = 0.1
            
            for attempt in range(max_retries):
                try:
                    with open(temp_file, 'w', encoding='utf-8') as f:
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
                    
                    if logger:
                        logger.debug(f"Saved test-file coverage cache")
                    break
                except (IOError, OSError) as e:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise
        except Exception as e:
            if logger:
                logger.warning(f"Failed to save test-file coverage cache: {e}")
    
    def get_source_file_mtimes(self, domain: str) -> Dict[str, float]:
        """
        Get current modification times for all source files in a domain.
        
        Only tracks .py files (Python source files), ignoring documentation,
        configuration, and log files.
        
        Args:
            domain: Domain name (e.g., 'core')
            
        Returns:
            Dictionary mapping file paths to modification times
        """
        mtimes = {}
        source_dir = self.project_root / domain
        if not source_dir.exists():
            return mtimes
        
        for py_file in source_dir.rglob('*.py'):
            # Skip actual test files (files with test_ prefix) and cache directories
            if py_file.name.startswith('test_') or '.coverage_cache' in py_file.parts:
                continue
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
        source_files_mtime = self.cache_data.get('source_files_mtime', {})
        
        # Check all known domains in cache
        for domain_name, domain_mtimes in source_files_mtime.items():
            current_mtimes = self.get_source_file_mtimes(domain_name)
            
            # Check if any files changed
            for file_path, current_mtime in current_mtimes.items():
                cached_mtime = domain_mtimes.get(file_path)
                if cached_mtime is None or current_mtime != cached_mtime:
                    changed_domains.add(domain_name)
                    break
        
        # Also check domains that might not be in cache yet (new domains or after cache clear)
        # Get all domains from domain mapper and check if they're in cache
        all_domains = set(self.domain_mapper.SOURCE_TO_TEST_MAPPING.keys())
        for domain_name in all_domains:
            if domain_name not in source_files_mtime:
                # Domain not in cache - treat as changed (needs initial caching)
                changed_domains.add(domain_name)
            else:
                # Domain is in cache - already checked above
                pass
        
        return changed_domains
    
    def get_test_files_to_run(self, changed_domains: Set[str]) -> List[Path]:
        """
        Get list of test files that need to be re-run based on changed domains.
        
        If all domains have changed (or cache is empty), includes ALL test files,
        even those not mapped to any domain, to ensure complete coverage.
        
        Args:
            changed_domains: Set of domain names that have changed
            
        Returns:
            List of test file paths that need to be re-run
        """
        if not changed_domains:
            return []  # No changes, no tests to run
        
        test_files_to_run = set()
        test_files = self.cache_data.get('test_files', {})
        
        # Check if this is a "full run" scenario (all domains changed or cache is empty)
        all_domains = set(self.domain_mapper.SOURCE_TO_TEST_MAPPING.keys())
        is_full_run = (changed_domains == all_domains) or (len(test_files) == 0)
        
        if is_full_run:
            # Full run: include ALL test files, even unmapped ones, to ensure complete coverage
            # But exclude test data directories
            all_test_files = [tf for tf in self.test_root.rglob('test_*.py') if self.is_valid_test_file(tf)]
            
            return sorted(all_test_files)
        
        # Selective run: only include test files that cover changed domains
        # Find all test files that cover any of the changed domains
        for test_file_path, test_file_data in test_files.items():
            test_file_domains = set(test_file_data.get('domains', []))
            if test_file_domains & changed_domains:
                # This test file covers at least one changed domain
                test_file_path_obj = self.project_root / test_file_path
                if test_file_path_obj.exists():
                    test_files_to_run.add(test_file_path_obj)
        
        # Also discover test files that aren't in cache yet (new test files)
        # These should be run if they cover changed domains
        for test_file in self.test_root.rglob('test_*.py'):
            # Skip test data files
            if not self.is_valid_test_file(test_file):
                continue
                
            test_file_rel = str(test_file.relative_to(self.project_root))
            if test_file_rel not in test_files:
                # New test file - check if it covers changed domains
                test_file_markers = self.domain_mapper.parse_markers_from_test_file(test_file)
                # Check if test file is in a directory that maps to changed domains
                for domain in changed_domains:
                    test_dirs = self.domain_mapper.get_test_domains_for_source(f"{domain}/dummy.py")
                    for test_dir in test_dirs:
                        if test_file.is_relative_to(self.project_root / test_dir):
                            test_files_to_run.add(test_file)
                            break
                    # Also check markers
                    domain_markers = self.domain_mapper.get_markers_for_source(f"{domain}/dummy.py")
                    if test_file_markers & domain_markers:
                        test_files_to_run.add(test_file)
        
        return sorted(test_files_to_run)
    
    def get_test_files_domains(self, test_file: Path) -> Set[str]:
        """
        Get set of domains that a test file covers.
        
        Args:
            test_file: Path to test file
            
        Returns:
            Set of domain names that this test file covers
        """
        domains = set()
        test_file_rel = str(test_file.relative_to(self.project_root))
        
        # Check cache first
        test_files = self.cache_data.get('test_files', {})
        if test_file_rel in test_files:
            cached_domains = test_files[test_file_rel].get('domains', [])
            domains.update(cached_domains)
            return domains
        
        # Discover domains from test file location and markers
        # Check test directory
        for domain, (test_dirs, _) in self.domain_mapper.SOURCE_TO_TEST_MAPPING.items():
            for test_dir in test_dirs:
                test_dir_path = self.project_root / test_dir
                if test_file.is_relative_to(test_dir_path):
                    domains.add(domain)
        
        # Check markers
        test_file_markers = self.domain_mapper.parse_markers_from_test_file(test_file)
        for domain, (_, domain_markers) in self.domain_mapper.SOURCE_TO_TEST_MAPPING.items():
            if test_file_markers & set(domain_markers):
                domains.add(domain)
        
        return domains
    
    def update_test_file_mapping(self, test_file: Path) -> None:
        """
        Update domain mapping for a test file without caching coverage data.
        Used on first runs to build the mapping without the expensive coverage caching.
        
        Args:
            test_file: Path to test file
        """
        # Reload cache first to merge with any concurrent updates
        self._load_cache()
        
        test_file_rel = str(test_file.relative_to(self.project_root))
        test_file_domains = self.get_test_files_domains(test_file)
        
        if 'test_files' not in self.cache_data:
            self.cache_data['test_files'] = {}
        
        # Update or create entry with just domain mapping (no coverage data)
        if test_file_rel not in self.cache_data['test_files']:
            self.cache_data['test_files'][test_file_rel] = {
                'domains': sorted(test_file_domains),
                'last_run': None  # No coverage data cached yet
            }
        else:
            # Update domains if they changed
            self.cache_data['test_files'][test_file_rel]['domains'] = sorted(test_file_domains)
        
        # Update source file mtimes for all domains this test file covers
        if 'source_files_mtime' not in self.cache_data:
            self.cache_data['source_files_mtime'] = {}
        
        for domain in test_file_domains:
            if domain not in self.cache_data['source_files_mtime']:
                self.cache_data['source_files_mtime'][domain] = {}
            # Update mtimes for this domain
            current_mtimes = self.get_source_file_mtimes(domain)
            self.cache_data['source_files_mtime'][domain].update(current_mtimes)
    
    def cache_test_file_coverage(self, test_file: Path, coverage_data: Dict[str, Any]) -> None:
        """
        Cache coverage data for a test file.
        
        Args:
            test_file: Path to test file
            coverage_data: Coverage data from this test file (subset of full coverage JSON)
        """
        # Reload cache first to merge with any concurrent updates
        self._load_cache()
        
        test_file_rel = str(test_file.relative_to(self.project_root))
        test_file_domains = self.get_test_files_domains(test_file)
        
        if 'test_files' not in self.cache_data:
            self.cache_data['test_files'] = {}
        
        self.cache_data['test_files'][test_file_rel] = {
            'domains': sorted(test_file_domains),
            'coverage_data': coverage_data,
            'last_run': datetime.now().isoformat()
        }
        
        # Update source file mtimes for all domains this test file covers
        if 'source_files_mtime' not in self.cache_data:
            self.cache_data['source_files_mtime'] = {}
        
        for domain in test_file_domains:
            if domain not in self.cache_data['source_files_mtime']:
                self.cache_data['source_files_mtime'][domain] = {}
            # Update mtimes for this domain
            current_mtimes = self.get_source_file_mtimes(domain)
            self.cache_data['source_files_mtime'][domain].update(current_mtimes)
        
        self._save_cache()
    
    def get_cached_test_file_coverage(self, test_file: Path) -> Optional[Dict[str, Any]]:
        """
        Get cached coverage data for a test file.
        
        Args:
            test_file: Path to test file
            
        Returns:
            Cached coverage data or None if not cached or invalid
        """
        test_file_rel = str(test_file.relative_to(self.project_root))
        test_files = self.cache_data.get('test_files', {})
        
        if test_file_rel not in test_files:
            return None
        
        # Check if any domains this test file covers have changed
        test_file_data = test_files[test_file_rel]
        test_file_domains = set(test_file_data.get('domains', []))
        changed_domains = self.get_changed_domains()
        
        if test_file_domains & changed_domains:
            # At least one domain this test file covers has changed
            return None
        
        return test_file_data.get('coverage_data')
    
    def get_full_coverage_cache(self) -> Optional[Dict[str, Any]]:
        """
        Get the cached full coverage JSON (from a previous full test run).
        
        Returns:
            Full coverage JSON or None if not cached
        """
        return self.cache_data.get(self.full_coverage_cache_key)
    
    def cache_full_coverage(self, coverage_json: Dict[str, Any]) -> None:
        """
        Cache the full coverage JSON from a complete test run.
        
        Args:
            coverage_json: Full coverage JSON from pytest-cov
        """
        self._load_cache()
        self.cache_data[self.full_coverage_cache_key] = coverage_json
        self._save_cache()
        if logger:
            logger.debug("Cached full coverage JSON")
    
    def get_all_cached_coverage(self, exclude_domains: Optional[Set[str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get all cached coverage data, excluding test files that cover specified domains.
        
        Args:
            exclude_domains: Set of domains to exclude (test files covering these domains won't be included)
            
        Returns:
            Dictionary mapping test file paths to their coverage data
        """
        if exclude_domains is None:
            exclude_domains = set()
        
        cached_coverage = {}
        test_files = self.cache_data.get('test_files', {})
        changed_domains = self.get_changed_domains()
        
        for test_file_path, test_file_data in test_files.items():
            test_file_domains = set(test_file_data.get('domains', []))
            
            # Skip if test file covers any excluded or changed domains
            if test_file_domains & exclude_domains or test_file_domains & changed_domains:
                continue
            
            coverage_data = test_file_data.get('coverage_data')
            if coverage_data:
                cached_coverage[test_file_path] = coverage_data
        
        return cached_coverage
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.cache_data = {
            'cache_version': '2.0',
            'generated_by': 'TestFileCoverageCache - Development Tools',
            'note': 'This file is auto-generated. Do not edit manually.',
            'source_files_mtime': {},
            'test_files': {},
            'last_updated': None,
            'last_updated_readable': None
        }
        self._save_cache()
        if logger:
            logger.info("Cleared all test-file coverage cache")
    
    def get_unmapped_test_files(self) -> List[Path]:
        """
        Get list of test files that are not mapped to any domain.
        
        Returns:
            List of test file paths that don't have domain mappings
        """
        unmapped = []
        all_test_files = [tf for tf in self.test_root.rglob('test_*.py') if self.is_valid_test_file(tf)]
        
        for test_file in all_test_files:
            test_file_domains = self.get_test_files_domains(test_file)
            if not test_file_domains:
                unmapped.append(test_file)
        
        return sorted(unmapped)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        test_files = self.cache_data.get('test_files', {})
        changed_domains = self.get_changed_domains()
        has_full_coverage = self.get_full_coverage_cache() is not None
        
        # Always discover actual test files from filesystem to get accurate count
        # Don't rely on cached count which may be incomplete
        actual_test_files = []
        unmapped_test_files = []
        for test_file in self.test_root.rglob('test_*.py'):
            # Skip test data files
            if not self.is_valid_test_file(test_file):
                continue
                
            # Check if this test file is associated with any domain
            test_file_domains = self.get_test_files_domains(test_file)
            if test_file_domains:  # Only count if it has at least one domain
                actual_test_files.append(test_file)
            else:
                unmapped_test_files.append(test_file)
        total_test_files = len(actual_test_files)
        unmapped_count = len(unmapped_test_files)
        
        test_files_to_run = len(self.get_test_files_to_run(changed_domains))
        # Count test files that have coverage_data cached (for selective runs)
        test_files_with_coverage = sum(1 for tf_data in test_files.values() if tf_data.get('coverage_data'))
        # If we have full coverage cache and no domains changed, all test files can use cache
        if has_full_coverage and not changed_domains:
            test_files_cached = total_test_files
        else:
            test_files_cached = test_files_with_coverage
        
        return {
            'total_test_files': total_test_files,
            'test_files_to_run': test_files_to_run,
            'test_files_cached': test_files_cached,
            'test_files_with_coverage': test_files_with_coverage,
            'unmapped_test_files': unmapped_count,
            'has_full_coverage_cache': has_full_coverage,
            'changed_domains': len(changed_domains),
            'cache_version': self.cache_data.get('cache_version', 'unknown'),
            'last_updated': self.cache_data.get('last_updated')
        }
