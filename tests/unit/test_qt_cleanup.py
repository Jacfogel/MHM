"""Widget disposal must complete without a running event loop or window close."""

import pytest

from tests.conftest import ensure_qt_runtime
from tests.test_helpers.test_support.qt_cleanup import qt_widget_scope

ensure_qt_runtime()

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QDialog, QWidget
from shiboken6 import isValid

pytestmark = [pytest.mark.unit, pytest.mark.ui]


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def test_pending_dialog_and_children_are_destroyed_before_scope_returns(qapp):
    with qt_widget_scope():
        dialog = QDialog()
        child = QWidget(dialog)
        dialog.deleteLater()
        # Reproduce the old fixture: merely scheduling deletion leaves both live.
        assert isValid(dialog) and isValid(child)
    assert not isValid(dialog)
    assert not isValid(child)
    assert QApplication.instance() is qapp


def test_exception_teardown_removes_detached_rows_and_preserves_existing_window(qapp):
    existing = QWidget()
    try:
        with pytest.raises(ValueError, match="test failure"):
            with qt_widget_scope():
                dialog = QDialog()
                detached = QWidget(dialog)
                detached.setParent(None)
                raise ValueError("test failure")
        assert not isValid(dialog)
        assert not isValid(detached)
        assert isValid(existing)
    finally:
        existing.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_teardown_does_not_invoke_user_close_handlers(qapp):
    closed = []

    class ConfirmingDialog(QDialog):
        def closeEvent(self, event):
            closed.append(True)
            event.ignore()

    with qt_widget_scope():
        dialog = ConfirmingDialog()
    assert not isValid(dialog)
    assert closed == []
