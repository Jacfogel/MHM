"""Settings, account creation and task shortcuts retain safe recovery replies."""

from unittest.mock import Mock

import pytest

from communication.command_handlers import account_handler, health_handler, task_handler

pytestmark = [pytest.mark.behavior, pytest.mark.communication]


@pytest.mark.tasks
@pytest.mark.parametrize(
    "method,module,operation,entities",
    [
        ("_handle_snooze_task_reminder", "tasks.task_reminder_snooze", "snooze_task_reminder",
         {"task_identifier": "1", "snooze_option": "1 hour"}),
        ("_handle_skip_task_occurrence", "tasks.task_occurrence_skip", "skip_task_occurrence",
         {"task_identifier": "1"}),
        ("_handle_simplify_task", "tasks.task_breakdown", "add_task_subtasks",
         {"task_identifier": "1", "simplified_title": "PRIVATE STEP"}),
    ],
)
@pytest.mark.parametrize("raises", [False, True])
def test_task_shortcut_failure_never_returns_none(monkeypatch, method, module, operation, entities, raises):
    from importlib import import_module
    persist = Mock(return_value=None)
    if raises:
        persist.side_effect = RuntimeError("PRIVATE ERROR")
    monkeypatch.setattr(import_module(module), operation, persist)
    handler = task_handler.TaskManagementHandler()
    monkeypatch.setattr(handler, "_resolve_active_task_for_command", lambda *_args, **_kw: {"id": "task-1"})
    response = getattr(handler, method)("shortcut-user", entities)
    persist.assert_called_once()
    assert response is not None
    assert "list tasks" in response.message
    assert "PRIVATE" not in response.message


@pytest.mark.parametrize("raises", [False, True])
def test_phrase_save_failure_has_check_before_retry(monkeypatch, raises):
    from core import natural_language_defaults as defaults
    monkeypatch.setattr(defaults, "get_user_data", lambda *_: {"preferences": {}})
    save = Mock(return_value=False)
    if raises:
        save.side_effect = RuntimeError("PRIVATE ERROR")
    result = defaults.apply_natural_language_defaults_update(
        "phrase-user", "tonight", "8pm", save_preferences=save
    )
    save.assert_called_once()
    assert not result.success
    assert "show phrase settings" in result.error_message
    assert "PRIVATE" not in result.error_message


@pytest.mark.parametrize("url", [None, "", "  "])
def test_health_empty_link_never_starts_connect_flow(monkeypatch, url):
    monkeypatch.setattr("core.config.is_google_health_enabled", lambda: True)
    monkeypatch.setattr(health_handler, "get_connect_readiness", lambda: (True, ""))
    monkeypatch.setattr(health_handler, "get_connect_authorization_url", lambda _: url)
    start = Mock()
    monkeypatch.setattr(health_handler, "run_connect_flow_async", start)
    response = health_handler.HealthHandler()._handle_connect("health-user")
    start.assert_not_called()
    assert "couldn't create" in response.message
    assert "health status" in response.message
    assert "Open this link" not in response.message


@pytest.mark.parametrize("raises", [False, True])
def test_account_creation_failure_does_not_encourage_duplicate(monkeypatch, raises):
    create = Mock(return_value=None)
    if raises:
        create.side_effect = RuntimeError("PRIVATE ERROR")
    monkeypatch.setattr(account_handler, "create_new_user", create)
    response = account_handler.AccountManagementHandler()._handle_create_account("channel-1", {
        "preferred_name": "Name", "tasks_enabled": True, "checkins_enabled": True,
        "messages_enabled": False, "channel_identifier": "channel-1",
    })
    create.assert_called_once()
    assert "check account status" in response.message
    assert "duplicate" in response.message
    assert "PRIVATE" not in response.message


def test_blank_preferred_name_never_reaches_creation(monkeypatch):
    create = Mock()
    monkeypatch.setattr(account_handler, "create_new_user", create)
    response = account_handler.AccountManagementHandler()._handle_create_account(
        "channel-1", {"preferred_name": "   "}
    )
    create.assert_not_called()
    assert "non-space character" in response.message
