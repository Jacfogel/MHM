"""Behavior tests for Google Health command handler."""

import pytest

from communication.command_handlers.health_handler import HealthHandler
from communication.command_handlers.shared_types import ParsedCommand


@pytest.mark.behavior
@pytest.mark.user
def test_connect_google_health_returns_auth_url(test_data_dir, monkeypatch):
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    monkeypatch.setenv("GOOGLE_HEALTH_ENABLED", "true")
    monkeypatch.setattr("core.config.GOOGLE_HEALTH_ENABLED", True)
    monkeypatch.setattr(
        "communication.command_handlers.health_handler.GOOGLE_HEALTH_ENABLED", True
    )
    monkeypatch.setattr(
        "integrations.google_health.user_settings.GOOGLE_HEALTH_CLIENT_ID", "test-client"
    )
    monkeypatch.setattr(
        "integrations.google_health.user_settings.GOOGLE_HEALTH_CLIENT_SECRET",
        "test-secret",
    )
    monkeypatch.setattr(
        "integrations.google_health.user_settings.build_authorization_url",
        lambda state="": "https://accounts.google.com/o/oauth2/v2/auth?client_id=test",
    )
    monkeypatch.setattr(
        "communication.command_handlers.health_handler.run_connect_flow_async",
        lambda user_id, on_finished: None,
    )

    user_id = "health-connect-user"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    handler = HealthHandler()
    response = handler.handle(
        user_id,
        ParsedCommand(
            intent="connect_google_health",
            entities={},
            confidence=1.0,
            original_message="connect google health",
        ),
    )
    assert response.completed is True
    assert "accounts.google.com" in response.message
    assert "Could not start" not in response.message

    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = "health-behavior-user"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    handler = HealthHandler()
    response = handler.handle(
        user_id,
        ParsedCommand(
            intent="google_health_status",
            entities={},
            confidence=1.0,
            original_message="health status",
        ),
    )
    assert response.completed is True
    assert "**Feature:**" in response.message or "Google Health" in response.message


@pytest.mark.behavior
@pytest.mark.user
def test_pause_health(test_data_dir):
    from core import get_user_data, update_user_account
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = "health-pause-user"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    update_user_account(user_id, {"features": {"google_health": "enabled"}})
    handler = HealthHandler()
    response = handler.handle(
        user_id,
        ParsedCommand(
            intent="pause_google_health",
            entities={},
            confidence=1.0,
            original_message="pause health",
        ),
    )
    assert response.completed is True
    account = get_user_data(user_id, "account").get("account") or {}
    assert account.get("features", {}).get("google_health") == "paused"


@pytest.mark.behavior
@pytest.mark.user
def test_delete_health_data(test_data_dir):
    from core import get_user_data
    from integrations.google_health.data_handlers import ensure_health_directory
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = "health-delete-user"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    ensure_health_directory(user_id)
    handler = HealthHandler()
    response = handler.handle(
        user_id,
        ParsedCommand(
            intent="delete_google_health_data",
            entities={},
            confidence=1.0,
            original_message="delete health data",
        ),
    )
    assert response.completed is True
    account = get_user_data(user_id, "account").get("account") or {}
    assert account.get("features", {}).get("google_health") == "disabled"
