"""Unit tests for check-in settings helpers that do not need the full dialog."""

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="QtWidgets unavailable due to missing GUI system libraries",
)

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.error_handling import UserInterfaceError
from ui.widgets.checkin_settings_widget import (
    CheckinSettingsWidget,
    build_custom_question_payload,
    category_combo_label,
    clear_layout_widgets,
    compute_question_count_bounds,
    ensure_vbox_layout,
    QUESTION_TYPE_OPTIONS,
    DEFAULT_QUESTION_CATEGORY_KEYS,
)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.mark.unit
@pytest.mark.checkins
class TestCheckinSettingsWidgetHelpers:
    def test_strip_type_hint_from_display_name(self):
        strip = CheckinSettingsWidget._strip_type_hint_from_display_name
        assert strip("CPAP use (yes/no)") == "CPAP use"
        assert strip("Mood") == "Mood"

    def test_set_combo_current_by_data(self, qapp):
        combo = QComboBox()
        combo.addItem("Yes/No", "yes_no")
        combo.addItem("Number", "number")
        combo.setCurrentIndex(0)

        CheckinSettingsWidget._set_combo_current_by_data(combo, "number")
        assert combo.currentData() == "number"

    def test_question_count_bounds_keep_max_floor_independent_of_current_min(self):
        min_required, max_floor, max_allowed = compute_question_count_bounds(0, 0, 0)
        assert min_required == 1
        assert max_floor == 1
        assert max_allowed == 50

        min_required, max_floor, max_allowed = compute_question_count_bounds(1, 2, 3)
        assert min_required == 1
        assert max_floor == 2
        assert max_allowed == 2

        min_required, max_floor, max_allowed = compute_question_count_bounds(2, 0, 2)
        assert min_required == 2
        assert max_floor == 2
        assert max_allowed == 2

    def test_max_spinbox_accepts_value_below_current_min(self, qapp):
        min_required, max_floor, max_allowed = compute_question_count_bounds(0, 0, 0)
        max_box = QSpinBox()
        max_box.setRange(max_floor, max_allowed)
        max_box.setValue(8)
        max_box.setValue(3)
        assert max_box.value() == 3
        assert max_box.minimum() == min_required

    def test_ensure_vbox_layout_reuses_installed_layout(self, qapp):
        container = QWidget()
        first = ensure_vbox_layout(container)
        first.addWidget(QLabel("first"))
        clear_layout_widgets(first)
        second = ensure_vbox_layout(container)
        second.addWidget(QLabel("second"))

        assert second is first
        assert container.layout() is first
        assert first.count() == 1
        child = first.itemAt(0).widget()
        assert child is not None
        assert child.text() == "second"

    def test_ensure_vbox_layout_rejects_non_vbox(self, qapp):
        container = QWidget()
        QHBoxLayout(container)
        with pytest.raises(UserInterfaceError):
            ensure_vbox_layout(container)

    def test_orphaned_second_layout_leaves_installed_layout_empty(self, qapp):
        """Document the Qt trap the questions rebuild used to hit."""
        container = QWidget()
        layout1 = QVBoxLayout(container)
        layout1.addWidget(QLabel("first"))
        clear_layout_widgets(layout1)
        layout2 = QVBoxLayout(container)
        layout2.addWidget(QLabel("second"))

        assert container.layout() is layout1
        assert layout1.count() == 0
        assert layout2.count() == 1

    def test_category_combo_label_uses_name_or_key(self):
        assert category_combo_label("mental_health") == "Mental Health"
        assert category_combo_label("health", {"name": "physical"}) == "Physical"
        assert category_combo_label("health", {"name": ""}) == "Health"

    def test_build_custom_question_payload_defaults_new_and_preserves_edit(self):
        created = build_custom_question_payload(
            "yes_no",
            "Do you drink water?",
            "Water (yes/no)",
            "health",
            {"error_message": "yes or no"},
            is_new=True,
            existing_def=None,
        )
        assert created["always_include"] is True
        assert created["sometimes_include"] is False
        assert created["enabled"] is True
        assert created["type"] == "yes_no"

        edited = build_custom_question_payload(
            "number",
            "How many glasses?",
            "Glasses (number)",
            "health",
            {"min": 0, "max": 100},
            is_new=False,
            existing_def={"always_include": False},
        )
        assert edited["always_include"] is False
        assert edited["question_text"] == "How many glasses?"

    def test_populate_question_type_combo_selects_type(self, qapp):
        combo = QComboBox()
        CheckinSettingsWidget._populate_question_type_combo(combo, "number")
        assert combo.count() == len(QUESTION_TYPE_OPTIONS)
        assert combo.currentData() == "number"

    def test_populate_category_combo_uses_manager_names_and_fallback_keys(self, qapp):
        combo = QComboBox()
        CheckinSettingsWidget._populate_category_combo(
            combo,
            {"health": {"name": "physical"}, "mood": {"name": "mood"}},
            "mood",
        )
        assert combo.itemText(0) == "Physical"
        assert combo.currentData() == "mood"

        fallback = QComboBox()
        CheckinSettingsWidget._populate_category_combo(fallback, {})
        assert [fallback.itemData(i) for i in range(fallback.count())] == list(
            DEFAULT_QUESTION_CATEGORY_KEYS
        )
