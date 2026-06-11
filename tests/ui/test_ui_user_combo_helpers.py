from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock, patch

import pytest

from ui.user_selection_controller import UserSelectionController
from ui.user_list_provider import USER_COMBO_PLACEHOLDER, UserListProvider


class _FakeComboBox:
    def __init__(self):
        self.items = []
        self.current_index = None

    def clear(self):
        self.items.clear()

    def addItem(self, text):
        self.items.append(text)

    def count(self):
        return len(self.items)

    def itemText(self, index):
        return self.items[index]

    def setCurrentIndex(self, index):
        self.current_index = index


@pytest.fixture
def controller():
    ui = cast(Any, SimpleNamespace(comboBox_users=_FakeComboBox()))
    return UserSelectionController(ui, UserListProvider())


@pytest.mark.ui
class TestUIUserComboHelpers:
    def test_reset_user_combo_box(self, controller):
        controller.ui.comboBox_users.addItem("old")
        controller.reset_user_combo_box()
        assert controller.ui.comboBox_users.items == [USER_COMBO_PLACEHOLDER]

    def test_reselect_user_if_present_selects_and_calls_handler(self, controller):
        combo = controller.ui.comboBox_users
        combo.items = [
            USER_COMBO_PLACEHOLDER,
            "alpha (email) - user-alpha",
            "beta (discord) - user-beta",
        ]

        with patch.object(controller, "on_user_selected") as selected:
            controller.reselect_user_if_present("user-beta")

        assert combo.current_index == 2
        selected.assert_called_once_with("beta (discord) - user-beta", parent_window=None)

    def test_refresh_user_list_fallback_populates_display_names(self, controller):
        with patch.object(
            controller.provider,
            "collect_fallback_display_names",
            return_value=["Preferred (name-u1) - u1", "name-u2 - u2"],
        ):
            controller.refresh_user_list_fallback(Mock(), Exception("primary failed"))

        assert controller.ui.comboBox_users.items == [
            USER_COMBO_PLACEHOLDER,
            "Preferred (name-u1) - u1",
            "name-u2 - u2",
        ]
