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


class FileCreationAuditor:
    def __init__(self):
        self._enabled = os.getenv('FILE_AUDIT_ENABLED', '1') == '1'
        self._poll_interval = float(os.getenv('FILE_AUDIT_POLL_INTERVAL', '2'))
        self._dirs: List[str] = _split_env_list(os.getenv('FILE_AUDIT_DIRS'))
        if not self._dirs:
            self._dirs = ['logs', 'data', os.path.join('tests', 'data'), os.path.join('tests', 'logs')]
        self._ignore_dirs: Set[str] = set(_split_env_list(os.getenv('FILE_AUDIT_IGNORE_DIRS')) or ['.git', '.venv', 'venv', '__pycache__'])
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._seen: Set[str] = set()
        self._initialized = False

    def start(self):
        if not self._enabled:
            return False
        if self._thread and self._thread.is_alive():
            return True
        try:
            # Prime seen set
            self._snapshot_existing()
            self._thread = threading.Thread(target=self._run, name='FileCreationAuditor', daemon=True)
            self._thread.start()
            _logger.info("FileCreationAuditor started", dirs=','.join(self._dirs))
            return True
        except Exception as e:
            _logger.warning(f"FileCreationAuditor failed to start: {e}")
            return False

    def stop(self):
        try:
            self._stop_event.set()
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=2.0)
            _logger.info("FileCreationAuditor stopped")
        except Exception:
            pass

    def _snapshot_existing(self):
        self._seen.clear()
        for base in self._dirs:
            if not os.path.exists(base):
                continue
            for root, dirs, files in os.walk(base):
                # filter ignored dirs
                dirs[:] = [d for d in dirs if d not in self._ignore_dirs]
                for f in files:
                    try:
                        full = os.path.join(root, f)
                        self._seen.add(os.path.abspath(full))
                    except Exception:
                        continue
        self._initialized = True

    def _run(self):
        while not self._stop_event.is_set():
            try:
                self._poll_once()
            except Exception as e:
                _logger.warning(f"FileCreationAuditor poll error: {e}")
            self._stop_event.wait(self._poll_interval)

    def _poll_once(self):
        for base in self._dirs:
            if not os.path.exists(base):
                continue
            for root, dirs, files in os.walk(base):
                dirs[:] = [d for d in dirs if d not in self._ignore_dirs]
                for f in files:
                    full = os.path.abspath(os.path.join(root, f))
                    if full not in self._seen:
                        self._seen.add(full)
                        try:
                            size = os.path.getsize(full)
                        except Exception:
                            size = -1
                        classification = _classify_path(full)
                        _logger.info(
                            "File created",
                            path=full,
                            bytes=size,
                            classification=classification,
                            detected_by='poll',
                        )


# Singleton
_auditor = FileCreationAuditor()


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


