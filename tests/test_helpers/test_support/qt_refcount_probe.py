"""Standalone Qt-only None-refcount probe; run on Python 3.11 for diagnosis.

No MHM modules, QApplication, pytest, threads, or shutdown bypass are involved.
Small batches expose reference loss without deliberately exhausting Py_None.
"""

import json
import platform
import sys

import PySide6
from PySide6.QtCore import QObject
import shiboken6


def measure_none_references(operation, count):
    before = sys.getrefcount(None)
    for _ in range(count):
        operation()
    after = sys.getrefcount(None)
    return {"calls": count, "before": before, "after": after, "delta": after - before}


def main():
    obj = QObject()

    def python_control():
        return None

    def qt_void_call():
        obj.setObjectName("refcount-probe")

    # Warm bound-method lookup/conversion paths before comparing batches.
    for _ in range(4):
        qt_void_call()
        python_control()
    payload = {
        "python": platform.python_version(),
        "pyside": PySide6.__version__,
        "shiboken": shiboken6.__version__,
        "none_is_immortal": sys.version_info >= (3, 12),
        "python_control": measure_none_references(python_control, 128),
        "qt_void_calls": [measure_none_references(qt_void_call, count) for count in (1, 32, 128)],
    }
    print(json.dumps(payload, indent=2), flush=True)
    # This test must not use Python 3.12's immortal None to clear an older build.
    if payload["none_is_immortal"]:
        print("Not a Python 3.11 refcount verdict: None is immortal on this interpreter.")
        return 0
    loss = sum(-batch["delta"] for batch in payload["qt_void_calls"])
    return int(loss > 20)


if __name__ == "__main__":
    raise SystemExit(main())
