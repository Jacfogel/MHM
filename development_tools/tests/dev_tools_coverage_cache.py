#!/usr/bin/env python3
"""
Dev Tools Coverage Cache

Caches coverage JSON for development_tools to avoid re-running tests when
development_tools source files have not changed.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

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
        self._load_cache()
    
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
                'cache_version': '1.0',
                'source_files_mtime': {},
                'coverage_json': None,
                'last_updated': None
            }
    
    def _save_cache(self) -> None:
        """Save cache to disk with file locking and atomic write for thread safety."""
        try:
            timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            timestamp_iso = datetime.now().isoformat()
            self.cache_data['last_updated'] = timestamp_iso
            self.cache_data['last_updated_readable'] = timestamp_str
            self.cache_data['generated_by'] = 'DevToolsCoverageCache - Development Tools'
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
        coverage_json = self.cache_data.get('coverage_json')
        return coverage_json if isinstance(coverage_json, dict) else None
    
    def get_cached_mtimes(self) -> Dict[str, float]:
        """Return cached source file mtimes."""
        return self.cache_data.get('source_files_mtime', {}) or {}
    
    def update_cache(self, coverage_json: Dict[str, Any], source_mtimes: Dict[str, float]) -> None:
        """Update cache with new coverage data and source mtimes."""
        self.cache_data['coverage_json'] = coverage_json
        self.cache_data['source_files_mtime'] = source_mtimes
        self._save_cache()
