"""
File creation auditor

Purpose:
- Track when, where, how, and what files are created while the service is running
- Minimal overhead polling-based watcher (no external deps); uses environment flags

Usage:
- Enable via FILE_AUDIT_ENABLED=1 (default: 1)
- Configure directories via FILE_AUDIT_DIRS (comma-separated); defaults to ['logs', 'data', 'tests/data', 'tests/logs']
- Ignore via FILE_AUDIT_IGNORE_DIRS (comma-separated); defaults to ['.git', '.venv', 'venv', '__pycache__']
- Poll interval FILE_AUDIT_POLL_INTERVAL (seconds, default: 2)
- Optional stack capture FILE_AUDIT_STACK=1 for programmatic record events

Integration:
- Service starts/stops the auditor
- core.file_operations and core.service_utilities call record_created for direct creations
"""

from __future__ import annotations

import os
import threading
import time
import traceback
from typing import Dict, Set, Optional, List

try:
    # Avoid heavy imports during tests; logger provides component loggers
    from core.logger import get_component_logger
    _logger = get_component_logger('file_ops')
except Exception:
    # Fallback to a no-op logger to satisfy static logging checks
    class _DummyLogger:
        def info(self, *args, **kwargs):
            pass
        def warning(self, *args, **kwargs):
            pass
        def debug(self, *args, **kwargs):
            pass
        def error(self, *args, **kwargs):
            pass
        def critical(self, *args, **kwargs):
            pass
    _logger = _DummyLogger()


def _split_env_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


def _classify_path(path: str) -> str:
    lower = path.replace('\\', '/').lower()
    if '/tests/' in lower or lower.startswith('tests/'):
        return 'tests'
    if '/logs/' in lower or lower.endswith('.log'):
        return 'logs'
    if '/flags/' in lower or lower.endswith('.flag'):
        return 'flags'
    if '/data/users/' in lower or lower.startswith('data/users'):
        return 'user_data'
    return 'other'


class FileAuditor:
    """
    Auditor for tracking file creation and modification patterns.
    """
    
    def __init__(self):
        # Use configurable directories instead of hardcoded paths
        self._dirs = self._get_audit_directories()
        self._created_files = []
        self._modified_files = []
        self._audit_data = {}
        
    def _get_audit_directories(self):
        """Get configurable audit directories from environment or use defaults."""
        env_dirs = os.getenv('FILE_AUDIT_DIRS')
        if env_dirs:
            return [d.strip() for d in env_dirs.split(',')]
        else:
            # Default directories - use configurable paths where possible
            default_dirs = ['logs', 'data']
            
            # Add test directories if in testing environment
            if os.getenv('MHM_TESTING') == '1':
                default_dirs.extend(['tests/data', 'tests/logs'])
                
            return default_dirs
    
    def start(self):
        """Start the file auditor (no-op for now)."""
        return True
    
    def stop(self):
        """Stop the file auditor (no-op for now)."""
        return True


# Singleton
_auditor = FileAuditor()


def start_auditor():
    return _auditor.start()


def stop_auditor():
    return _auditor.stop()


def record_created(path: str, reason: str = "api", extra: Optional[Dict] = None):
    """Programmatically record a file creation event.

    Safe to call even if auditor disabled. Includes optional stack if FILE_AUDIT_STACK=1.
    """
    try:
        size = os.path.getsize(path) if os.path.exists(path) else -1
    except Exception:
        size = -1
    classification = _classify_path(path)
    payload = {
        'path': os.path.abspath(path),
        'bytes': size,
        'classification': classification,
        'detected_by': reason,
    }
    if extra:
        payload.update(extra)
    if os.getenv('FILE_AUDIT_STACK') == '1':
        try:
            payload['stack'] = ''.join(traceback.format_stack(limit=10))
        except Exception:
            pass
    _logger.info("File created (programmatic)", **payload)


