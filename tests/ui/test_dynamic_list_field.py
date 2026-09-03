"""Behavior tests for DynamicListField row helpers."""

from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()

import pytest
from PySide6.QtWidgets import QApplication

from ui.widgets.dynamic_list_field import DynamicListField

pytestmark = [pytest.mark.ui]


@pytest.fixture(scope="module")
def qapp():
    """Provide a process-wide QApplication for widget tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_editable_row_auto_checks_when_text_entered(qapp):
    widget = DynamicListField(preset_label="", editable=True, checked=False)
    assert widget.is_blank() is True

    widget.on_text_changed("")
    widget.ui.lineEdit_dynamic_list_field.setText("custom item")
    widget.on_text_changed("custom item")

    assert widget.is_checked() is True
    assert widget.is_blank() is False
    widget.deleteLater()


def test_preset_row_uses_checkbox_label_and_hides_delete(qapp):
    widget = DynamicListField(preset_label="Reading", editable=False, checked=True)
    assert widget.get_text() == "Reading"
    assert widget.is_checked() is True
    assert widget.ui.pushButton_delete_DynamicListField.isVisible() is False
    assert widget.ui.lineEdit_dynamic_list_field.isEnabled() is False
    widget.deleteLater()


def test_delete_and_editing_finished_emit(qapp):
    widget = DynamicListField(preset_label="x", editable=True, checked=True)
    deleted = []
    changed = []
    widget.delete_requested.connect(lambda row: deleted.append(row))
    widget.value_changed.connect(lambda: changed.append(True))

    widget._on_delete()
    widget.on_editing_finished()
    widget.on_checkbox_toggled(True)

    assert deleted == [widget]
    assert changed
    widget.deleteLater()


def test_set_text_coerces_non_string(qapp):
    widget = DynamicListField(preset_label="", editable=True)
    widget.set_text(12)
    assert widget.get_text() == "12"
    widget.deleteLater()
