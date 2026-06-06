from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock, patch

import pytest

from ui.ui_app_qt import MHMManagerUI
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
def ui_instance():
    obj = MHMManagerUI.__new__(MHMManagerUI)
    obj.ui = cast(Any, SimpleNamespace(comboBox_users=_FakeComboBox()))
    obj.user_list_provider = UserListProvider()
    obj.on_user_selected = Mock()
    return obj


@pytest.mark.ui
class TestUIUserComboHelpers:
    def test_reset_user_combo_box(self, ui_instance):
        ui_instance.ui.comboBox_users.addItem("old")
        ui_instance._reset_user_combo_box()
        assert ui_instance.ui.comboBox_users.items == [USER_COMBO_PLACEHOLDER]

    def test_reselect_user_if_present_selects_and_calls_handler(self, ui_instance):
        combo = ui_instance.ui.comboBox_users
        combo.items = [
            USER_COMBO_PLACEHOLDER,
            "alpha (email) - user-alpha",
            "beta (discord) - user-beta",
        ]

        ui_instance._reselect_user_if_present("user-beta")

        assert combo.current_index == 2
        ui_instance.on_user_selected.assert_called_once_with("beta (discord) - user-beta")

    def test_refresh_user_list_fallback_populates_display_names(self, ui_instance):
        with patch.object(
            ui_instance.user_list_provider,
            "collect_fallback_display_names",
            return_value=["Preferred (name-u1) - u1", "name-u2 - u2"],
        ):
            ui_instance._refresh_user_list_fallback(Exception("primary failed"))

        assert ui_instance.ui.comboBox_users.items == [
            USER_COMBO_PLACEHOLDER,
            "Preferred (name-u1) - u1",
            "name-u2 - u2",
        ]
