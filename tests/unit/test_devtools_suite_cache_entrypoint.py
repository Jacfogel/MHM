"""Regression coverage for standalone suite cache setup and reporting."""

import os
from pathlib import Path
import subprocess
import sys

import pytest


pytestmark = [pytest.mark.unit, pytest.mark.core]


def test_suite_script_imports_cache_without_pythonpath(tmp_path):
    project_root = Path(__file__).resolve().parents[2]
    script = project_root / "development_tools/tests/run_test_suite.py"
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["DEVTOOLS_TESTING"] = "1"
    env["DEV_TOOLS_LOGS_DIR"] = str(tmp_path / "logs")
    # Match direct-file launch search paths, without executing the real suite.
    probe = """
import runpy, sys
from pathlib import Path
script = Path(sys.argv[1])
sys.path[:] = [str(script.parent)] + [p for p in sys.path if p and Path(p).resolve() != Path.cwd()]
runner = runpy.run_path(str(script), run_name='cache_import_probe')
assert runner['_suite_logger'] is not None
assert runner['partition_test_paths'] is not None
from development_tools.tests.test_file_suite_cache import TestFileSuiteCache
cache = TestFileSuiteCache(Path.cwd(), cache_dir=Path.cwd() / 'cache')
assert isinstance(cache.get_changed_domains('quick'), set)
"""
    result = subprocess.run(
        [sys.executable, "-c", probe, str(script)], cwd=tmp_path, env=env,
        capture_output=True, text=True, timeout=30, check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("enabled", [True, False])
def test_cache_setup_failure_is_distinct_from_explicit_disable(monkeypatch, tmp_path, enabled):
    from development_tools.tests import run_test_suite as runner
    from development_tools.tests import test_file_suite_cache as cache_module

    def fail_cache(*args, **kwargs):
        raise RuntimeError("cache setup probe")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cache_module, "TestFileSuiteCache", fail_cache)
    monkeypatch.setattr(runner, "_has_xdist", lambda: False)
    monkeypatch.setattr(runner, "_STOP_REQUESTED", False)
    monkeypatch.setattr(runner, "_run_phase", lambda name, *a, **kw: runner.PhaseResult(
        name=name, command=[], return_code=0, duration_seconds=0,
        counts={"passed": 1}, failed_node_ids=[], output_tail="", junit_xml="",
    ))
    warnings = []
    class Logger:
        def warning(self, message, **kwargs):
            warnings.append(message)
    monkeypatch.setattr(runner, "_suite_logger", Logger())
    result = runner.run_suite({"junit_dir": str(tmp_path / "junit")}, use_domain_cache=enabled)
    metadata = result["details"]["domain_cache"]
    assert metadata["cache_mode"] == "disabled"
    if enabled:
        assert metadata["invalidation_reason"] == "domain_cache_initialization_failed"
        assert metadata["initialization_error"] == "RuntimeError: cache setup probe"
        assert "cache setup probe" in warnings[0]
    else:
        assert metadata["invalidation_reason"] == "domain_cache_disabled"
        assert not warnings


@pytest.mark.parametrize("mode,expected", [
    ("disabled", "disabled"), ("selective_run", "partially_utilized"),
    ("full_run", "invalidated"), ("cache_hit", "utilized"),
])
def test_suite_cache_modes_are_visible_in_audit_logs(mode, expected):
    from development_tools.shared.service.audit_orchestration import AuditOrchestrationMixin

    audit = AuditOrchestrationMixin()
    audit._tool_cache_metadata = {"run_test_suite": {"cache_mode": mode}}
    assert audit._tool_cache_state_for_log("run_test_suite", True) == expected
