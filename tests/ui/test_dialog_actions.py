from unittest.mock import MagicMock, Mock, patch

import pytest

from ui.dialog_actions import DialogActions, _require_current_user


pytestmark = [pytest.mark.ui, pytest.mark.unit]


def test_require_current_user_warns_when_missing():
    parent = Mock()
    with patch("ui.dialog_actions.QMessageBox") as mock_msgbox:
        assert _require_current_user(parent, None) is False
    mock_msgbox.warning.assert_called_once()


def test_require_current_user_passes_when_set():
    parent = Mock()
    with patch("ui.dialog_actions.QMessageBox") as mock_msgbox:
        assert _require_current_user(parent, "user-1") is True
    mock_msgbox.warning.assert_not_called()


def test_manage_categories_opens_dialog_and_reloads_categories():
    actions = DialogActions()
    parent = Mock()
    reload_categories = Mock()

    mock_dialog = MagicMock()
    mock_dialog_class = Mock(return_value=mock_dialog)
    with patch("ui.dialog_actions._load_attr", return_value=mock_dialog_class):
        actions.manage_categories(
            parent,
            "user-1",
            on_user_changed=Mock(),
            reload_categories=reload_categories,
        )

    mock_dialog_class.assert_called_once_with(parent, "user-1")
    mock_dialog.exec.assert_called_once()
    reload_categories.assert_called_once()


def test_manage_categories_skips_without_user():
    actions = DialogActions()
    parent = Mock()

    with patch("ui.dialog_actions._load_attr") as mock_load:
        with patch("ui.dialog_actions._require_current_user", return_value=False):
            actions.manage_categories(
                parent,
                None,
                on_user_changed=Mock(),
                reload_categories=Mock(),
            )

    mock_load.assert_not_called()


def test_prepare_category_editor_returns_none_without_category():
    actions = DialogActions()
    parent = Mock()
    category_combo = Mock()
    category_combo.currentIndex.return_value = 0

    with patch("ui.dialog_actions._require_current_user", return_value=True):
        with patch("ui.dialog_actions.QMessageBox") as mock_msgbox:
            result = actions.prepare_current_user_category_editor(
                parent, "user-1", category_combo, "message"
            )

    assert result is None
    mock_msgbox.warning.assert_called_once()


def test_edit_user_category_opens_message_editor():
    actions = DialogActions()
    parent = Mock()
    category_combo = Mock()

    with patch.object(
        actions,
        "prepare_current_user_category_editor",
        return_value="motivational",
    ):
        with patch.object(actions, "open_message_editor") as mock_open:
            actions.edit_user_category(parent, "user-1", category_combo, "message")

    mock_open.assert_called_once_with(parent, "user-1", None, "motivational")
