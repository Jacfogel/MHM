"""Unit tests for development_tools/tests/verify_process_cleanup.py (V5 §3.18)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from development_tools.tests import verify_process_cleanup as vpc


@pytest.mark.unit
def test_parse_cim_json_array() -> None:
    raw = json.dumps(
        [
            {"ProcessId": 42, "CommandLine": "python.exe -m pytest -q"},
            {"ProcessId": 99, "CommandLine": ""},
        ]
    )
    rows = vpc._parse_cim_json_payload(raw)
    assert len(rows) == 2
    assert rows[0]["ProcessId"] == 42


@pytest.mark.unit
def test_parse_cim_json_single_object() -> None:
    raw = json.dumps({"ProcessId": 1, "CommandLine": "pytest"})
    rows = vpc._parse_cim_json_payload(raw)
    assert len(rows) == 1
    assert rows[0]["ProcessId"] == 1


@pytest.mark.unit
def test_parse_cim_json_invalid_returns_empty() -> None:
    assert vpc._parse_cim_json_payload("not-json") == []


@pytest.mark.unit
def test_get_python_processes_non_windows_empty() -> None:
    with mock.patch.object(vpc.sys, "platform", "linux"):
        assert vpc.get_python_processes() == []


@pytest.mark.unit
def test_check_for_orphaned_detects_pytest_in_cmdline() -> None:
    procs = [
        {"pid": 1, "cmdline": r"C:\Python\python.exe -m pytest tests/", "is_pytest": False},
        {"pid": 2, "cmdline": r"C:\Python\python.exe script.py", "is_pytest": False},
    ]
    with mock.patch.object(vpc, "get_python_processes", return_value=procs):
        found, offenders = vpc.check_for_orphaned_processes()
    assert found is True
    assert len(offenders) == 1
    assert offenders[0]["pid"] == 1


@pytest.mark.unit
def test_cim_fallback_to_tasklist_when_cim_returns_none() -> None:
    csv_out = (
        '"Image Name","PID","Session Name","Session#","Mem Usage"\r\n'
        '"python.exe","12345","Console","1","1 K"\r\n'
    )
    with mock.patch.object(vpc.sys, "platform", "win32"):
        with mock.patch.object(vpc, "_get_python_processes_win32_cim", return_value=None):
            with mock.patch.object(
                vpc.subprocess,
                "run",
                return_value=mock.Mock(returncode=0, stdout=csv_out, stderr=""),
            ) as run_mock:
                procs = vpc.get_python_processes()
    assert len(procs) == 1
    assert procs[0]["pid"] == 12345
    assert procs[0]["cmdline"] == ""
    run_mock.assert_called()


@pytest.mark.unit
def test_cim_used_when_available() -> None:
    cim_rows = [{"pid": 7, "cmdline": "python -m pytest", "is_pytest": False}]
    with mock.patch.object(vpc.sys, "platform", "win32"):
        with mock.patch.object(vpc, "_get_python_processes_win32_cim", return_value=cim_rows):
            assert vpc.get_python_processes() == cim_rows
