"""Shutdown evidence must preserve ownership, attribution, and object lifetimes."""

import gc
import json
import sys
from types import SimpleNamespace
import weakref

import pytest

from tests.test_helpers.test_support import nightly_diagnostics as diagnostics

pytestmark = [pytest.mark.unit, pytest.mark.suite]


@pytest.fixture
def recorder(monkeypatch, tmp_path):
    class QObject:
        def objectName(self):
            raise AssertionError("Diagnostics must not call Qt object methods")

        def __repr__(self):
            raise AssertionError("Diagnostics must not expose object contents")

    monkeypatch.setitem(sys.modules, "PySide6.QtCore", SimpleNamespace(QObject=QObject))
    monkeypatch.setitem(
        sys.modules,
        "shiboken6",
        SimpleNamespace(
            isValid=lambda obj: obj.valid,
            ownedByPython=lambda obj: obj.owned,
            createdByPython=lambda obj: True,
        ),
    )
    monkeypatch.setattr(diagnostics, "_history_path", tmp_path / "history.jsonl")
    monkeypatch.setattr(diagnostics, "_qt_objects", {})
    monkeypatch.setattr(diagnostics, "_qt_refs", {})
    monkeypatch.setattr(diagnostics, "_qt_exit_registered", False)
    registrations = []
    monkeypatch.setattr(diagnostics.atexit, "register", registrations.append)

    def events():
        return [
            json.loads(line)
            for line in diagnostics._history_path.read_text().splitlines()
        ]

    return QObject, events, registrations


def test_qt_inventory_tracks_invalidation_and_original_test(recorder):
    QObject, events, registrations = recorder
    obj = QObject()
    obj.valid, obj.owned = True, True
    diagnostics._qt_snapshot("setup", "tests/example.py::test_creator")
    obj.valid, obj.owned = False, False
    diagnostics._qt_snapshot("teardown", "tests/example.py::test_later")
    metadata = events()[-1]["changed"][0]
    assert metadata["first_seen_nodeid"] == "tests/example.py::test_creator"
    assert metadata["valid"] is False
    assert metadata["owned_by_python"] is False
    assert registrations == [diagnostics._qt_before_exit]
    diagnostics._qt_snapshot("before_qt_atexit")
    assert events()[-1]["objects"] == [metadata]
    assert events()[-1]["threads"]


def test_qt_inventory_does_not_keep_wrappers_alive(recorder):
    QObject, events, _ = recorder
    obj = QObject()
    obj.valid, obj.owned = True, True
    identity, reference = hex(id(obj)), weakref.ref(obj)
    diagnostics._qt_snapshot("setup", "creator")
    del obj
    gc.collect()
    assert reference() is None
    diagnostics._qt_snapshot("teardown", "creator")
    assert events()[-1]["removed"] == [identity]
    assert events()[-1]["total"] == 0


def test_qt_inventory_does_not_import_qt_when_unused(recorder, monkeypatch):
    _, events, registrations = recorder
    monkeypatch.delitem(sys.modules, "PySide6.QtCore")
    diagnostics._record("start", nodeid="plain_test")
    before, registered = len(events()), list(registrations)
    diagnostics._qt_snapshot("setup", "plain_test")
    assert len(events()) == before
    assert registrations == registered


def test_qt_inventory_ignores_dead_weak_proxies(recorder):
    QObject, events, _ = recorder
    obj = QObject()
    proxy = weakref.proxy(obj)
    del obj
    diagnostics._qt_snapshot("teardown", "dead-proxy-test")
    assert type(proxy) is weakref.ProxyType
    assert events()[-1]["total"] == 0
