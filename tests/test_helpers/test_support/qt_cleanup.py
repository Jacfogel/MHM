"""Explicit widget teardown for synchronous tests without a running Qt loop."""

from contextlib import contextmanager
import weakref


@contextmanager
def qt_widget_scope():
    """Dispose new top-level widgets, including mock-layout and detached rows.

    Preserve existing windows and the process-wide QApplication. Process only
    deferred deletions, not general events that could run timers or dialogs.
    """
    from PySide6.QtCore import QCoreApplication, QEvent
    from PySide6.QtWidgets import QApplication
    from shiboken6 import isValid

    if QApplication.instance() is None:
        raise RuntimeError("qt_widget_scope requires an existing QApplication")
    existing = {
        id(widget): weakref.ref(widget) for widget in QApplication.topLevelWidgets()
    }
    try:
        yield
    finally:
        created = []
        for widget in QApplication.topLevelWidgets():
            previous = existing.get(id(widget))
            if previous is not None and previous() is widget:
                continue
            if isValid(widget):
                created.append(widget)
                widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        assert all(not isValid(widget) for widget in created), (
            "Test widgets survived deferred deletion"
        )
