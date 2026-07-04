"""Focused tests for development_tools.shared.logging."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

import pytest

from tests.development_tools.conftest import load_development_tools_module

lock_state_module = load_development_tools_module("shared.lock_state")


@pytest.fixture
def logging_mod():
    mod = load_development_tools_module("shared.logging")
    _reset_devtools_logger(mod)
    yield mod
    _reset_devtools_logger(mod)


def _reset_devtools_logger(mod) -> None:
    parent = logging.getLogger("devtools")
    for handler in parent.handlers[:]:
        handler.close()
        parent.removeHandler(handler)
    parent.handlers.clear()
    mod._parent_initialized = False


@pytest.mark.unit
def test_default_log_path_uses_development_tools_reports_logs(
    logging_mod, monkeypatch
):
    monkeypatch.delenv("LOG_AI_DEV_TOOLS_FILE", raising=False)
    monkeypatch.delenv("DEV_TOOLS_LOGS_DIR", raising=False)

    path = logging_mod._resolve_log_file_path()
    normalized = str(path).replace("\\", "/")

    assert normalized.endswith("development_tools/reports/logs/ai_dev_tools.log")
    assert not normalized.endswith("logs/ai_dev_tools.log") or "/reports/logs/" in normalized


@pytest.mark.unit
def test_dev_tools_logger_rotates_to_backups_dir(logging_mod, monkeypatch, tmp_path):
    monkeypatch.delenv("DISABLE_LOG_ROTATION", raising=False)
    logs_dir = tmp_path / "development_tools" / "reports" / "logs"
    monkeypatch.setenv("MHM_TESTING", "0")
    monkeypatch.setenv("DEV_TOOLS_LOGS_DIR", str(logs_dir))
    monkeypatch.delenv("LOG_AI_DEV_TOOLS_FILE", raising=False)
    monkeypatch.setenv("DEV_TOOLS_LOG_MAX_BYTES", "120")
    monkeypatch.setenv("DEV_TOOLS_LOG_BACKUP_COUNT", "2")

    _reset_devtools_logger(logging_mod)
    logger = logging_mod.get_dev_tools_logger("rotation_test")
    for _ in range(8):
        logger.info("rotation payload " + ("x" * 80))

    for handler in logging.getLogger("devtools").handlers:
        handler.flush()

    _reset_devtools_logger(logging_mod)

    assert (logs_dir / "ai_dev_tools.log").exists()
    backups = sorted((logs_dir / "backups").glob("ai_dev_tools.log.*"))
    assert backups
    assert len(backups) <= 2


@pytest.mark.unit
def test_dev_tools_logger_defaults_to_one_mb_rotation_threshold(
    logging_mod, monkeypatch, tmp_path
):
    logs_dir = tmp_path / "development_tools" / "reports" / "logs"
    monkeypatch.setenv("MHM_TESTING", "0")
    monkeypatch.setenv("DEV_TOOLS_LOGS_DIR", str(logs_dir))
    monkeypatch.delenv("LOG_AI_DEV_TOOLS_FILE", raising=False)
    monkeypatch.delenv("DEV_TOOLS_LOG_MAX_BYTES", raising=False)
    monkeypatch.delenv("LOG_MAX_BYTES", raising=False)

    logging_mod.get_dev_tools_logger("threshold_test")
    parent = logging.getLogger("devtools")
    handlers = [
        h
        for h in parent.handlers
        if isinstance(h, (RotatingFileHandler, logging_mod.AuditDeferredRotatingFileHandler))
    ]

    assert len(handlers) == 1
    assert isinstance(handlers[0], RotatingFileHandler)
    assert isinstance(handlers[0], logging_mod.AuditDeferredRotatingFileHandler)
    assert handlers[0].maxBytes == 1024 * 1024


@pytest.mark.unit
def test_log_rollover_deferred_while_audit_lock_active(
    logging_mod, monkeypatch, tmp_path, capsys
):
    monkeypatch.delenv("DISABLE_LOG_ROTATION", raising=False)
    project_root = tmp_path / "proj"
    logs_dir = project_root / "development_tools" / "reports" / "logs"
    logs_dir.mkdir(parents=True)
    monkeypatch.setenv("MHM_TESTING", "0")
    monkeypatch.setenv("DEV_TOOLS_LOGS_DIR", str(logs_dir))
    monkeypatch.delenv("LOG_AI_DEV_TOOLS_FILE", raising=False)
    monkeypatch.setenv("DEV_TOOLS_LOG_MAX_BYTES", "120")
    monkeypatch.setenv("DEV_TOOLS_LOG_ROLLOVER_DEFER_SECONDS", "60")

    lock_state_module.write_lock_metadata(
        project_root / ".audit_in_progress.lock",
        lock_type="audit",
    )
    monkeypatch.setattr(
        lock_state_module,
        "active_audit_coverage_locks_present",
        lambda _root: True,
    )

    _reset_devtools_logger(logging_mod)
    logger = logging_mod.get_dev_tools_logger("defer_rotation_test")
    for _ in range(12):
        logger.info("rotation payload " + ("x" * 80))

    _reset_devtools_logger(logging_mod)

    backups = list((logs_dir / "backups").glob("ai_dev_tools.log.*"))
    assert not backups
    captured = capsys.readouterr()
    assert "Log rollover deferred" in captured.err
    assert "audit/coverage lock" in captured.err


@pytest.mark.unit
def test_log_rollover_runs_when_no_audit_lock(
    logging_mod, monkeypatch, tmp_path
):
    monkeypatch.delenv("DISABLE_LOG_ROTATION", raising=False)
    logs_dir = tmp_path / "development_tools" / "reports" / "logs"
    monkeypatch.setenv("MHM_TESTING", "0")
    monkeypatch.setenv("DEV_TOOLS_LOGS_DIR", str(logs_dir))
    monkeypatch.delenv("LOG_AI_DEV_TOOLS_FILE", raising=False)
    monkeypatch.setenv("DEV_TOOLS_LOG_MAX_BYTES", "120")
    monkeypatch.setenv("DEV_TOOLS_LOG_BACKUP_COUNT", "2")

    logger = logging_mod.get_dev_tools_logger("rotation_without_lock")
    for _ in range(8):
        logger.info("rotation payload " + ("x" * 80))

    _reset_devtools_logger(logging_mod)

    backups = sorted((logs_dir / "backups").glob("ai_dev_tools.log.*"))
    assert backups
