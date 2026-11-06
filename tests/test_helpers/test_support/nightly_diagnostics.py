"""Opt-in pytest history recorder, independent of application logging.

Each process writes flushed JSONL events so crashes preserve the active test.
Load with PYTEST_PLUGINS=tests.test_helpers.test_support.nightly_diagnostics.
"""

import atexit
import gc
import json
import os
from pathlib import Path
import platform
import sys
import threading
import time
import weakref

import pytest

_DIRECTORY = Path(__file__).resolve().parents[2] / "logs" / "nightly_diagnostics"
_history_path: Path | None = None
_qt_objects: dict[int, dict] = {}
_qt_refs: dict[int, weakref.ReferenceType] = {}
_qt_exit_registered = False
_last_nodeid: str | None = None


def _qt_snapshot(stage: str, nodeid: str | None = None) -> None:
    """Record wrapper metadata without retaining objects or calling Qt methods.

    First-seen attribution is an observation boundary, not a creation stack.
    GC inventory includes invalid wrappers but may miss untracked C++ objects.
    """
    global _qt_objects, _qt_refs, _qt_exit_registered
    if _history_path is None:
        return
    qtcore = sys.modules.get("PySide6.QtCore")
    shiboken = sys.modules.get("shiboken6")
    if qtcore is None or shiboken is None:
        return
    # Register after Qt has installed its atexit cleanup, so this runs before it.
    if not _qt_exit_registered:
        atexit.register(_qt_before_exit)
        _qt_exit_registered = True
    _record("qt_snapshot_begin", stage=stage, nodeid=nodeid)
    current = {}
    current_refs = {}
    for obj in gc.get_objects():
        # Inspect the real type: isinstance can dereference dead weak proxies.
        if not issubclass(type(obj), qtcore.QObject):
            continue
        identity = id(obj)
        previous_ref = _qt_refs.get(identity)
        previous = (
            _qt_objects.get(identity, {})
            if previous_ref is not None and previous_ref() is obj
            else {}
        )
        metadata = {
            "id": hex(identity),
            "type": f"{type(obj).__module__}.{type(obj).__qualname__}",
            "first_seen_nodeid": previous.get("first_seen_nodeid", nodeid),
            "first_seen_stage": previous.get("first_seen_stage", stage),
            "valid": shiboken.isValid(obj),
            "owned_by_python": shiboken.ownedByPython(obj),
            "created_by_python": shiboken.createdByPython(obj),
        }
        current[identity] = metadata
        current_refs[identity] = weakref.ref(obj)
    changed = [
        meta for identity, meta in current.items() if _qt_objects.get(identity) != meta
    ]
    removed = [hex(identity) for identity in _qt_objects.keys() - current.keys()]
    _qt_objects = current  # Metadata only: never extend Qt wrapper lifetimes.
    _qt_refs = current_refs
    _record(
        "qt_snapshot",
        stage=stage,
        nodeid=nodeid,
        total=len(current),
        changed=changed,
        removed=removed,
        # Full inventory at shutdown makes the final evidence self-contained.
        objects=list(current.values())
        if stage in ("session_finish", "unconfigure", "before_qt_atexit")
        else None,
        threads=[
            {"name": thread.name, "ident": thread.ident, "daemon": thread.daemon}
            for thread in threading.enumerate()
        ]
        if stage == "before_qt_atexit"
        else None,
    )


def _qt_before_exit() -> None:
    _qt_snapshot("before_qt_atexit", _last_nodeid)


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
    global _last_nodeid
    _last_nodeid = nodeid
    _record("start", nodeid=nodeid)


def pytest_runtest_logreport(report):
    _record("report", nodeid=report.nodeid, phase=report.when, outcome=report.outcome)
    if report.when in ("setup", "teardown"):
        _qt_snapshot(report.when, report.nodeid)


def pytest_runtest_logfinish(nodeid, location):
    _record("finish", nodeid=nodeid)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    yield
    _record("session_finish", exitstatus=int(exitstatus))
    _qt_snapshot("session_finish", _last_nodeid)


def pytest_unconfigure(config):
    _qt_snapshot("unconfigure", _last_nodeid)
