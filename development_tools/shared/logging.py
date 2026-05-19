#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""Self-contained logging for development_tools (no core.* imports)."""

from __future__ import annotations

import contextlib
import json
import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

# Default defer window when audit/coverage lock files are active (15 minutes).
_DEFAULT_ROLLOVER_DEFER_SECONDS = 15 * 60

_RESERVED_LOG_KWARGS = frozenset({"exc_info", "stack_info", "stacklevel", "extra"})

_PARENT_NAME = "devtools"
_parent_initialized = False


def _normalize_component_name(component_name: str) -> str:
    if not isinstance(component_name, str):
        try:
            component_name = str(component_name)
        except Exception:
            component_name = "main"
    name = component_name.strip().lower() if component_name else "main"
    return name or "main"


def _is_testing() -> bool:
    return os.getenv("MHM_TESTING") == "1"


def _test_verbose_logs() -> bool:
    return os.getenv("TEST_VERBOSE_LOGS", "0") in ("1", "2")


def _resolve_log_file_path() -> Path:
    """Resolve dev-tools log file; avoids core.config and .env."""
    explicit = os.getenv("LOG_AI_DEV_TOOLS_FILE", "").strip()
    if explicit:
        return Path(explicit).resolve()
    default_base = Path(__file__).resolve().parents[2] / "development_tools" / "reports" / "logs"
    base = Path(os.getenv("DEV_TOOLS_LOGS_DIR", str(default_base))).resolve()
    return (base / "ai_dev_tools.log").resolve()


def _resolve_int_env(name: str, fallback: int) -> int:
    try:
        value = int(os.getenv(name, "").strip())
    except (TypeError, ValueError):
        return fallback
    return value if value >= 0 else fallback


def _resolve_project_root_from_log_path(log_path: Path) -> Path | None:
    """Walk parents from the log file to find the repository root."""
    try:
        current = log_path.resolve().parent
    except OSError:
        current = log_path.parent
    for _ in range(15):
        if (current / "development_tools").is_dir() or (current / ".git").exists():
            return current
        if current.parent == current:
            break
        current = current.parent
    return None


class AuditDeferredRotatingFileHandler(RotatingFileHandler):
    """
    RotatingFileHandler that defers rollover while audit/coverage locks are active.

    When active lock files are present (same set as ``active_audit_coverage_locks_present``),
    rollover is skipped and retried after ``DEV_TOOLS_LOG_ROLLOVER_DEFER_SECONDS`` (default 15
    minutes). This avoids Windows rename failures while ``ai_dev_tools.log`` is heavily written
    or held open during Tier 3 audits.
    """

    def __init__(
        self,
        filename: str | os.PathLike[str],
        defer_seconds: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(filename, **kwargs)
        self.defer_seconds = (
            defer_seconds
            if defer_seconds is not None
            else _resolve_int_env(
                "DEV_TOOLS_LOG_ROLLOVER_DEFER_SECONDS",
                _DEFAULT_ROLLOVER_DEFER_SECONDS,
            )
        )
        if self.defer_seconds <= 0:
            self.defer_seconds = _DEFAULT_ROLLOVER_DEFER_SECONDS
        self._defer_rollover_until = 0.0
        self._project_root: Path | None = None

    def _get_project_root(self) -> Path | None:
        if self._project_root is None:
            self._project_root = _resolve_project_root_from_log_path(Path(self.baseFilename))
        return self._project_root

    def _rollover_deferred_now(self) -> bool:
        return time.time() < self._defer_rollover_until

    def _audit_locks_block_rollover(self) -> bool:
        if os.environ.get("DISABLE_LOG_ROTATION") == "1":
            return False
        project_root = self._get_project_root()
        if project_root is None:
            return False
        from development_tools.shared.lock_state import active_audit_coverage_locks_present

        return active_audit_coverage_locks_present(project_root)

    def _schedule_rollover_retry(self, reason: str) -> None:
        now = time.time()
        if now < self._defer_rollover_until:
            return
        self._defer_rollover_until = now + float(self.defer_seconds)
        minutes = max(1, int(self.defer_seconds // 60))
        with contextlib.suppress(Exception):
            sys.stderr.write(
                f"[devtools] Log rollover deferred for {minutes} minute(s): {reason}\n"
            )

    def shouldRollover(self, record: logging.LogRecord) -> bool:  # noqa: N802
        if os.environ.get("DISABLE_LOG_ROTATION") == "1":
            return False
        if self._rollover_deferred_now():
            return False
        if not super().shouldRollover(record):
            return False
        if self._audit_locks_block_rollover():
            self._schedule_rollover_retry("active audit/coverage lock file(s) present")
            return False
        return True

    def doRollover(self) -> None:  # noqa: N802
        if os.environ.get("DISABLE_LOG_ROTATION") == "1":
            return
        if self._rollover_deferred_now():
            return
        if self._audit_locks_block_rollover():
            self._schedule_rollover_retry("active audit/coverage lock file(s) present")
            return
        try:
            super().doRollover()
        except PermissionError:
            if self._audit_locks_block_rollover():
                self._schedule_rollover_retry(
                    "log file locked during audit/coverage (rollover rename failed)"
                )
            else:
                raise


def _setup_devtools_parent_logger() -> None:
    global _parent_initialized
    if _parent_initialized:
        return
    parent = logging.getLogger(_PARENT_NAME)
    if parent.handlers:
        _parent_initialized = True
        return
    parent.setLevel(logging.DEBUG)
    parent.propagate = False
    log_path = _resolve_log_file_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    backup_dir = log_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    max_bytes = _resolve_int_env(
        "DEV_TOOLS_LOG_MAX_BYTES",
        1 * 1024 * 1024,
    )
    backup_count = _resolve_int_env(
        "DEV_TOOLS_LOG_BACKUP_COUNT",
        _resolve_int_env("LOG_BACKUP_COUNT", 7),
    )
    handler = AuditDeferredRotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.namer = lambda default_name: str(backup_dir / Path(default_name).name)
    # INFO default: keeps routine audit/tool chatter out of ai_dev_tools.log; override
    # with DEV_TOOLS_LOG_LEVEL=DEBUG (or WARNING, etc.) when diagnosing.
    _lvl = os.getenv("DEV_TOOLS_LOG_LEVEL", "INFO").upper()
    try:
        file_level = int(getattr(logging, _lvl))
    except (AttributeError, TypeError, ValueError):
        file_level = logging.INFO
    handler.setLevel(file_level)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    parent.addHandler(handler)
    _parent_initialized = True


class _DummyDevToolsLogger:
    """No-op logger for tests when verbose file logging is disabled."""

    def __init__(self, name: str) -> None:
        self.name = name

    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        pass

    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        pass

    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        pass

    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        pass

    def critical(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        pass


class DevToolsLogger:
    """Compatible with get_component_logger and stdlib Logger printf-style calls."""

    def __init__(self, component_name: str, logger: logging.Logger) -> None:
        self.component_name = component_name
        self._logger = logger

    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, msg, *args, **kwargs)

    def _log(self, level: int, msg: Any, *args: Any, **kwargs: Any) -> None:
        reserved = {k: kwargs[k] for k in _RESERVED_LOG_KWARGS if k in kwargs}
        structured = {k: v for k, v in kwargs.items() if k not in _RESERVED_LOG_KWARGS}
        if args:
            self._logger.log(level, msg, *args, **reserved)
            return
        if structured:
            full_message = f"{msg} | {json.dumps(structured, default=str)}"
        else:
            full_message = str(msg)
        self._logger.log(level, full_message, **reserved)


def get_dev_tools_logger(component_name: str) -> DevToolsLogger | _DummyDevToolsLogger:
    """
    Return a logger for development_tools code.

    When MHM_TESTING=1 and TEST_VERBOSE_LOGS is not 1 or 2, returns a no-op
    logger (matching prior get_component_logger test behavior).

    Otherwise attaches a shared file handler under the ``devtools`` hierarchy
    (default directory: ``development_tools/reports/logs`` under the repository
    root; override with ``LOG_AI_DEV_TOOLS_FILE`` or ``DEV_TOOLS_LOGS_DIR``).
    The rotating file handler's threshold defaults to **INFO**; set
    ``DEV_TOOLS_LOG_LEVEL=DEBUG`` (or ``WARNING``, etc.) for a different cutoff.
    Rotation defaults to 1 MB and can be overridden with
    ``DEV_TOOLS_LOG_MAX_BYTES``. Retention defaults to ``LOG_BACKUP_COUNT``
    compatible values and can be overridden with ``DEV_TOOLS_LOG_BACKUP_COUNT``.
    While audit/coverage lock files are active, log rollover is deferred for
    ``DEV_TOOLS_LOG_ROLLOVER_DEFER_SECONDS`` (default 900 / 15 minutes).
    """
    name = _normalize_component_name(component_name)
    if _is_testing() and not _test_verbose_logs():
        return _DummyDevToolsLogger(name)

    if _is_testing() and _test_verbose_logs():
        base = Path(
            os.getenv("LOGS_DIR") or os.getenv("TEST_LOGS_DIR", str(Path("tests") / "logs"))
        )
        os.environ.setdefault("DEV_TOOLS_LOGS_DIR", str(base))
        os.environ.setdefault("LOG_AI_DEV_TOOLS_FILE", str(base / "ai_dev_tools.log"))

    _setup_devtools_parent_logger()
    underlying = logging.getLogger(f"{_PARENT_NAME}.{name}")
    underlying.setLevel(logging.DEBUG)
    underlying.propagate = True
    return DevToolsLogger(name, underlying)
