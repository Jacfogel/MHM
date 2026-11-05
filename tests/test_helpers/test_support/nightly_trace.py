"""Temporary opt-in recorder for the Linux nightly crash investigation."""

import json
import os
from pathlib import Path
import sys
import time


def _record(event, **details):
    worker = os.environ.get("PYTEST_XDIST_WORKER", "main")
    directory = Path("tests/logs/diagnostic_history")
    directory.mkdir(parents=True, exist_ok=True)
    payload = {"time": time.time(), "pid": os.getpid(), "worker": worker,
               "event": event, **details}
    with (directory / f"{worker}-{os.getpid()}.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload) + "\n")


def pytest_sessionstart(session):
    _record("session_start", python=sys.version,
            seed=getattr(session.config.option, "randomly_seed", None))


def pytest_runtest_logstart(nodeid, location):
    _record("start", nodeid=nodeid)


def pytest_runtest_logreport(report):
    _record("report", nodeid=report.nodeid, phase=report.when,
            outcome=report.outcome)


def pytest_runtest_logfinish(nodeid, location):
    _record("finish", nodeid=nodeid)


def pytest_sessionfinish(session, exitstatus):
    _record("session_finish", exitstatus=int(exitstatus))
