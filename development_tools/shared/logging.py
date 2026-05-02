#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""Self-contained logging for development_tools (no core.* imports)."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

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
    base = Path(os.getenv("DEV_TOOLS_LOGS_DIR", "logs")).resolve()
    return (base / "ai_dev_tools.log").resolve()


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
    handler = logging.FileHandler(log_path, encoding="utf-8")
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
    (default directory: ``logs`` under cwd, or ``development_tools/reports/logs``
    when ``run_development_tools.py`` sets ``DEV_TOOLS_LOGS_DIR``; override with
    ``LOG_AI_DEV_TOOLS_FILE`` or ``DEV_TOOLS_LOGS_DIR``). The file handler's
    threshold defaults to **INFO**; set ``DEV_TOOLS_LOG_LEVEL=DEBUG`` (or
    ``WARNING``, etc.) for a different cutoff.
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
