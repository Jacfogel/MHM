"""Health failures explain save uncertainty and safe recovery without raw errors."""

import pytest
from communication.command_handlers.health_handler import HealthHandler
from communication.command_handlers.shared_types import ParsedCommand

pytestmark = pytest.mark.communication


@pytest.mark.behavior
@pytest.mark.parametrize("intent,dependency,result,expected", [
    ("google_health_status", "get_health_integration_status", None, "did not change your settings"),
    ("enable_google_health", "enable_health_integration", (False, "private database detail"), "setting may have been saved"),
    ("sync_google_health", "sync_health_integration", False, "whether new data was saved"),
])
@pytest.mark.parametrize("raises", [False, True])
def test_health_failure_recovery(monkeypatch, intent, dependency, result, expected, raises):
    def operation(*args):
        if raises:
            raise RuntimeError("private database detail")
        return result

    monkeypatch.setattr(f"communication.command_handlers.health_handler.{dependency}", operation)
    response = HealthHandler().handle("health-error-test", ParsedCommand(intent, {}, 1.0, "health"))
    assert response.completed
    assert expected in response.message
    assert "health status" in response.message
    assert "private database detail" not in response.message
