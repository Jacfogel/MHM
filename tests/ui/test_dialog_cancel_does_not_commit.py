"""Cancel/save contract tests that avoid fragile Qt widget trees where possible."""

from __future__ import annotations

from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()

from unittest.mock import MagicMock, patch

import pytest

from ui.dialogs.category_management_dialog import CategoryManagementDialog
from ui.dialogs.channel_management_dialog import ChannelManagementDialog


@pytest.mark.ui
@pytest.mark.unit
def test_category_save_persists_and_is_separate_from_reject():
    assert CategoryManagementDialog.save_category_settings is not CategoryManagementDialog.reject

    dialog = MagicMock()
    dialog.user_id = "user-1"
    dialog.ui = MagicMock()
    dialog.ui.groupBox_enable_automated_messages.isChecked.return_value = True
    dialog.category_widget = MagicMock()
    dialog.category_widget.get_selected_categories.return_value = ["motivational"]
    dialog.accept = MagicMock()
    dialog.user_changed = MagicMock()

    with (
        patch(
            "ui.dialogs.category_management_dialog.get_user_data",
            return_value={
                "account": {"features": {"checkins": "enabled"}},
                "preferences": {},
            },
        ),
        patch(
            "ui.dialogs.category_management_dialog.update_user_preferences"
        ) as update_prefs,
        patch(
            "ui.dialogs.category_management_dialog.update_user_account"
        ) as update_account,
        patch("ui.dialogs.category_management_dialog.QMessageBox"),
    ):
        CategoryManagementDialog.save_category_settings(dialog)

    update_prefs.assert_called()
    update_account.assert_called()


@pytest.mark.ui
@pytest.mark.unit
def test_channel_save_is_not_reject():
    assert ChannelManagementDialog.save_channel_settings is not ChannelManagementDialog.reject
