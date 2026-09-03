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


def test_manage_google_health_settings_opens_dialog():
    actions = DialogActions()
    parent = Mock()
    on_user_changed = Mock()

    mock_dialog = MagicMock()
    mock_dialog_class = Mock(return_value=mock_dialog)
    with patch("ui.dialog_actions._load_attr", return_value=mock_dialog_class):
        with patch("ui.dialog_actions._require_current_user", return_value=True):
            actions.manage_google_health_settings(
                parent,
                "user-1",
                on_user_changed=on_user_changed,
            )

    mock_dialog_class.assert_called_once_with(parent, "user-1")
    mock_dialog.user_changed.connect.assert_called_once_with(on_user_changed)
    mock_dialog.exec.assert_called_once()


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


def test_edit_user_category_unknown_label_does_not_open():
    actions = DialogActions()
    with patch.object(actions, "prepare_current_user_category_editor") as prepare:
        actions.edit_user_category(Mock(), "user-1", Mock(), "unknown")
    prepare.assert_not_called()


def test_edit_user_messages_and_schedules_delegate():
    actions = DialogActions()
    parent = Mock()
    combo = Mock()
    with patch.object(actions, "edit_user_category") as edit:
        actions.edit_user_messages(parent, "user-1", combo)
        actions.edit_user_schedules(parent, "user-1", combo)
    assert edit.call_args_list[0].args[-1] == "message"
    assert edit.call_args_list[1].args[-1] == "schedule"


def test_create_new_user_opens_dialog_and_stops_temp_manager():
    actions = DialogActions()
    parent = Mock()
    refresh = Mock()
    comm = Mock()
    dialog = MagicMock()
    dialog_cls = Mock(return_value=dialog)

    with patch("ui.dialog_actions._load_attr", return_value=dialog_cls):
        actions.create_new_user(
            parent,
            refresh_user_list=refresh,
            create_comm_manager=Mock(return_value=comm),
        )

    dialog_cls.assert_called_once_with(parent, comm)
    dialog.user_changed.connect.assert_called_once_with(refresh)
    dialog.exec.assert_called_once()
    comm.stop_all.assert_called_once()


def test_create_new_user_cleanup_error_is_ignored():
    actions = DialogActions()
    comm = Mock()
    comm.stop_all.side_effect = RuntimeError("cleanup failed")
    dialog_cls = Mock(return_value=MagicMock())

    with patch("ui.dialog_actions._load_attr", return_value=dialog_cls):
        actions.create_new_user(
            Mock(),
            refresh_user_list=Mock(),
            create_comm_manager=Mock(return_value=comm),
        )

    comm.stop_all.assert_called_once()


def test_create_new_user_reports_open_failure():
    actions = DialogActions()
    parent = Mock()
    with patch("ui.dialog_actions._load_attr", side_effect=ImportError("missing")), \
        patch("ui.dialog_actions.QMessageBox") as msgbox:
        actions.create_new_user(
            parent,
            refresh_user_list=Mock(),
            create_comm_manager=Mock(),
        )
    msgbox.critical.assert_called_once()
    assert "create account" in msgbox.critical.call_args.args[2]


@pytest.mark.parametrize(
    ("method", "kwargs"),
    [
        ("manage_communication_settings", {"on_user_changed": "cb"}),
        ("manage_checkins", {"on_user_changed": "cb"}),
        ("manage_tasks", {"on_user_changed": "cb"}),
        ("manage_google_health_settings", {"on_user_changed": "cb"}),
        ("manage_phrase_settings", {"on_user_changed": "cb"}),
        ("manage_task_crud", {}),
    ],
)
def test_manage_dialogs_open_and_exec(method, kwargs):
    actions = DialogActions()
    parent = Mock()
    on_user_changed = Mock()
    call_kwargs = {key: on_user_changed if value == "cb" else value for key, value in kwargs.items()}
    dialog = MagicMock()
    dialog_cls = Mock(return_value=dialog)

    with patch("ui.dialog_actions._load_attr", return_value=dialog_cls), \
        patch("ui.dialog_actions._require_current_user", return_value=True):
        getattr(actions, method)(parent, "user-1", **call_kwargs)

    dialog.exec.assert_called_once()
    if "on_user_changed" in kwargs:
        dialog.user_changed.connect.assert_called_once_with(on_user_changed)


@pytest.mark.parametrize(
    "method",
    [
        "manage_communication_settings",
        "manage_checkins",
        "manage_tasks",
        "manage_google_health_settings",
        "manage_phrase_settings",
        "manage_task_crud",
        "manage_personalization",
        "manage_user_analytics",
    ],
)
def test_manage_dialogs_report_open_failure(method):
    actions = DialogActions()
    parent = Mock()
    kwargs = {}
    if method not in {"manage_task_crud", "manage_user_analytics"}:
        kwargs["on_user_changed"] = Mock()

    with patch("ui.dialog_actions._require_current_user", return_value=True), \
        patch("ui.dialog_actions._load_attr", side_effect=RuntimeError("boom")), \
        patch("ui.dialog_actions.get_user_data", return_value={"context": {}, "account": {}}), \
        patch("ui.dialog_actions.QMessageBox") as msgbox:
        getattr(actions, method)(parent, "user-1", **kwargs)

    msgbox.critical.assert_called_once()


def test_manage_personalization_saves_timezone_on_profile_save():
    actions = DialogActions()
    parent = Mock()
    on_user_changed = Mock()
    dialog = MagicMock()

    def dialog_cls(_parent, _user, on_save, existing_data=None):
        on_save({"preferred_name": "Ada", "timezone": "America/Regina"})
        return dialog

    with patch("ui.dialog_actions._require_current_user", return_value=True), \
        patch("ui.dialog_actions._load_attr", return_value=dialog_cls), \
        patch(
            "ui.dialog_actions.get_user_data",
            return_value={
                "context": {"preferred_name": "Ada"},
                "account": {"timezone": "UTC"},
            },
        ), \
        patch("ui.dialog_actions.save_user_data") as save:
        actions.manage_personalization(
            parent, "user-1", on_user_changed=on_user_changed
        )

    save.assert_called_once_with(
        "user-1",
        {"context": {"preferred_name": "Ada"}, "account": {"timezone": "America/Regina"}},
    )
    dialog.user_changed.connect.assert_called_once_with(on_user_changed)
    dialog.exec.assert_called_once()


def test_manage_user_analytics_opens_dialog():
    actions = DialogActions()
    opener = Mock()
    with patch("ui.dialog_actions._require_current_user", return_value=True), \
        patch("ui.dialog_actions._load_attr", return_value=opener):
        actions.manage_user_analytics(Mock(), "user-1")
    opener.assert_called_once()


def test_prepare_category_editor_loads_user_context():
    actions = DialogActions()
    parent = Mock()
    combo = Mock()
    combo.currentIndex.return_value = 2
    combo.itemData.return_value = "motivational"
    context = MagicMock()

    def fake_get_user_data(_user, section):
        if section == "account":
            return {"account": {"internal_username": "ada"}}
        return {"context": {"preferred_name": "Ada"}}

    with patch("ui.dialog_actions._require_current_user", return_value=True), \
        patch("ui.dialog_actions.UserContext", return_value=context), \
        patch("ui.dialog_actions.get_user_data", side_effect=fake_get_user_data):
        result = actions.prepare_current_user_category_editor(
            parent, "user-1", combo, "message"
        )

    assert result == "motivational"
    context.set_user_id.assert_called_with("user-1")
    context.set_internal_username.assert_called_once_with("ada")
    context.set_preferred_name.assert_called_once_with("Ada")
    context.load_user_data.assert_called_once_with("user-1")


def test_open_message_editor_rejects_invalid_category():
    actions = DialogActions()
    with patch("ui.dialog_actions._load_attr") as load:
        assert actions.open_message_editor(Mock(), "user-1", None, None) is None
        assert actions.open_message_editor(Mock(), "user-1", None, "   ") is None
    load.assert_not_called()


def test_open_message_editor_accepts_parent_and_opens():
    actions = DialogActions()
    parent = Mock()
    parent_dialog = Mock()
    opener = Mock()
    with patch("ui.dialog_actions._load_attr", return_value=opener):
        actions.open_message_editor(parent, "user-1", parent_dialog, "motivational")
    parent_dialog.accept.assert_called_once()
    opener.assert_called_once_with(parent, "user-1", "motivational")


def test_open_message_editor_reports_failure():
    actions = DialogActions()
    parent = Mock()
    with patch("ui.dialog_actions._load_attr", side_effect=RuntimeError("boom")), \
        patch("ui.dialog_actions.QMessageBox") as msgbox:
        actions.open_message_editor(parent, "user-1", None, "motivational")
    msgbox.critical.assert_called_once()


def test_open_schedule_editor_success_and_cancel():
    actions = DialogActions()
    parent = Mock()
    parent_dialog = Mock()
    opener = Mock(side_effect=[True, False])
    with patch("ui.dialog_actions._load_attr", return_value=opener):
        actions.open_schedule_editor(parent, "user-1", parent_dialog, "motivational")
        actions.open_schedule_editor(parent, "user-1", None, "motivational")
    parent_dialog.accept.assert_called_once()
    assert opener.call_count == 2
    opener.call_args.args[3]()


def test_open_schedule_editor_rejects_invalid_category():
    actions = DialogActions()
    with patch("ui.dialog_actions._load_attr") as load:
        assert actions.open_schedule_editor(Mock(), "user-1", None, None) is None
        assert actions.open_schedule_editor(Mock(), "user-1", None, "") is None
    load.assert_not_called()


def test_open_schedule_editor_reports_failure():
    actions = DialogActions()
    with patch("ui.dialog_actions._load_attr", side_effect=RuntimeError("boom")), \
        patch("ui.dialog_actions.QMessageBox") as msgbox:
        actions.open_schedule_editor(Mock(), "user-1", None, "motivational")
    msgbox.critical.assert_called_once()
