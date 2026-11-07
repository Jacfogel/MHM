"""Opt-in pytest history recorder, independent of application logging.

Each process writes flushed JSONL events so crashes preserve the active test.
Load with PYTEST_PLUGINS=tests.test_helpers.test_support.nightly_diagnostics.
"""

import json
import os
from pathlib import Path
import platform
import time

_DIRECTORY = Path(__file__).resolve().parents[2] / "logs" / "nightly_diagnostics"
_history_path: Path | None = None


def _record(event: str, **details) -> None:
    if _history_path is None:
        return
    payload = {
        "time_ns": time.time_ns(),
        "pid": os.getpid(),
        "worker": os.environ.get("PYTEST_XDIST_WORKER", "main"),
        "event": event,
        **details,
    }
    with _history_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload) + "\n")


def pytest_sessionstart(session):
    global _history_path
    _DIRECTORY.mkdir(parents=True, exist_ok=True)
    worker = os.environ.get("PYTEST_XDIST_WORKER", "main")
    _history_path = _DIRECTORY / f"{worker}-{os.getpid()}-{time.time_ns()}.jsonl"
    _record(
        "session_start",
        python=platform.python_version(),
        platform=platform.platform(),
        seed=getattr(session.config.option, "randomly_seed", None),
        args=list(session.config.invocation_params.args),
    )


def pytest_collection_finish(session):
    _record("collection", nodeids=[item.nodeid for item in session.items])


def pytest_runtest_logstart(nodeid, location):
    _record("start", nodeid=nodeid)


def pytest_runtest_logreport(report):
    _record("report", nodeid=report.nodeid, phase=report.when, outcome=report.outcome)


def pytest_runtest_logfinish(nodeid, location):
    _record("finish", nodeid=nodeid)


def pytest_sessionfinish(session, exitstatus):
    _record("session_finish", exitstatus=int(exitstatus))
