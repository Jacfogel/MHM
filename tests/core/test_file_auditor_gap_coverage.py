"""Gap-coverage tests for core.file_auditor."""

from __future__ import annotations

import builtins
import importlib.util

import pytest

import core.file_auditor as file_auditor


pytestmark = [pytest.mark.core]

@pytest.mark.unit
@pytest.mark.core
class TestFileAuditorGapCoverage:
    def test_get_audit_directories_exception_fallback(self, monkeypatch):
        auditor = file_auditor.FileAuditor()
        real_getenv = file_auditor.os.getenv

        def _getenv_maybe_fail(key, default=None):
            if key == "FILE_AUDIT_DIRS":
                raise RuntimeError("env failed")
            return real_getenv(key, default)

        monkeypatch.setattr(file_auditor.os, "getenv", _getenv_maybe_fail)
        assert auditor._get_audit_directories() == ["logs", "data"]

    def test_record_created_getsize_exception_path(self, monkeypatch):
        monkeypatch.setattr(file_auditor.os.path, "exists", lambda p: True)
        monkeypatch.setattr(
            file_auditor.os.path,
            "getsize",
            lambda p: (_ for _ in ()).throw(OSError("size failed")),
        )
        file_auditor.record_created("tests/data/whatever.txt", reason="unit-gap")

    def test_file_auditor_init_exception_branch(self, monkeypatch):
        original = file_auditor.FileAuditor._get_audit_directories
        monkeypatch.setattr(
            file_auditor.FileAuditor,
            "_get_audit_directories",
            lambda self: (_ for _ in ()).throw(RuntimeError("dirs failed")),
        )
        # __init__ is handle_errors-decorated; branch should execute without crashing construction.
        instance = file_auditor.FileAuditor()
        assert instance is not None
        monkeypatch.setattr(file_auditor.FileAuditor, "_get_audit_directories", original)

    def test_reload_with_import_failure_uses_dummy_logger(self, monkeypatch):
        real_import = builtins.__import__

        def _failing_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "core.logger":
                raise ImportError("forced import failure")
            return real_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", _failing_import)
        spec = importlib.util.spec_from_file_location(
            "test_file_auditor_fallback_module",
            file_auditor.__file__,
        )
        assert spec is not None and spec.loader is not None
        fallback_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fallback_mod)

        # Exercise no-op logger methods from fallback class.
        fallback_mod._logger.info("x")
        fallback_mod._logger.warning("x")
        fallback_mod._logger.debug("x")
        fallback_mod._logger.error("x")
        fallback_mod._logger.critical("x")

        monkeypatch.setattr(builtins, "__import__", real_import)
