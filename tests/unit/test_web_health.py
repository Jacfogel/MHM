"""Focused ownership checks for Google Health website routes."""

import asyncio
import json
from types import SimpleNamespace

from aiohttp import web
import pytest

from core.error_handling import error_handler
from core.web_health import WebHealthRoutes, register_health_routes

pytestmark = [pytest.mark.unit, pytest.mark.user, pytest.mark.asyncio]


class _Gateway:
    def __init__(self, action):
        self.action = action
        self.health_connecting = set()
        self.health_lock = asyncio.Lock()
        self.auth_calls = 0
        self.throttle_calls = []

    async def authenticated_account(self, _request):
        self.auth_calls += 1
        return "user-1", {}

    async def body(self, _request):
        return {"action": self.action}

    def throttle(self, *args):
        self.throttle_calls.append(args)


def _patch_health_functions(monkeypatch, **overrides):
    from integrations.google_health import user_settings

    values = {
        "get_health_integration_status": lambda _uid: SimpleNamespace(
            feature_state="enabled",
            connected=True,
            last_success_at="2026-10-02T12:00:00Z",
            has_recent_error=False,
        ),
        "get_connect_readiness": lambda: (True, ""),
        "get_connect_authorization_url": lambda _uid: "https://health.example/connect",
        "pause_health_integration": lambda _uid: True,
        "enable_health_integration": lambda _uid: (True, ""),
        "sync_health_integration": lambda _uid: True,
        "delete_health_integration": lambda _uid: True,
        "run_connect_flow_async": lambda _uid, _callback: None,
    }
    values.update(overrides)
    for name, value in values.items():
        monkeypatch.setattr(user_settings, name, value)


async def test_health_route_initialization_reports_and_reraises_errors(monkeypatch):
    calls = []
    monkeypatch.setattr(
        error_handler,
        "handle_error",
        lambda error, context, operation, user_friendly=True: calls.append(
            (error, operation, user_friendly)
        )
        or False,
    )

    class BrokenHealthRoutes(WebHealthRoutes):
        def __setattr__(self, _name, _value):
            raise RuntimeError("cannot initialize routes")

    with pytest.raises(RuntimeError, match="cannot initialize routes"):
        BrokenHealthRoutes(object())

    assert len(calls) == 1
    assert calls[0][1:] == ("initializing website health routes", False)


async def test_health_route_registration_reports_and_reraises_errors(monkeypatch):
    calls = []
    monkeypatch.setattr(
        error_handler,
        "handle_error",
        lambda error, context, operation, user_friendly=True: calls.append(
            (error, operation, user_friendly)
        )
        or False,
    )

    class BrokenRouter:
        def add_get(self, *_args, **_kwargs):
            raise RuntimeError("cannot register routes")

    app = SimpleNamespace(router=BrokenRouter())
    with pytest.raises(RuntimeError, match="cannot register routes"):
        register_health_routes(app, object())

    assert len(calls) == 1
    assert calls[0][1:] == ("registering website health routes", False)


async def test_health_get_returns_the_existing_browser_safe_snapshot(monkeypatch):
    from integrations.google_health import user_settings

    monkeypatch.setattr(
        user_settings,
        "get_health_integration_status",
        lambda _uid: SimpleNamespace(
            feature_state="enabled",
            connected=True,
            last_success_at="2026-10-02T12:00:00Z",
            has_recent_error=False,
        ),
    )
    monkeypatch.setattr(
        user_settings,
        "get_connect_readiness",
        lambda: (True, ""),
    )

    class Gateway:
        health_connecting = {"someone-else"}

        async def authenticated_account(self, _request):
            return "user-1", {}

    response = await WebHealthRoutes(Gateway()).health_settings(
        SimpleNamespace(method="GET")
    )

    response_text = response.text
    assert response_text is not None
    assert json.loads(response_text) == {
        "feature_state": "enabled",
        "connected": True,
        "last_success_at": "2026-10-02T12:00:00Z",
        "has_recent_error": False,
        "connect_available": True,
        "connect_error": "",
        "connecting": False,
    }


async def test_health_post_rejects_unknown_actions_before_mutation():
    class Gateway:
        health_connecting = set()
        health_lock = asyncio.Lock()

        async def authenticated_account(self, _request):
            return "user-1", {}

        async def body(self, _request):
            return {"action": "unknown"}

    with pytest.raises(web.HTTPBadRequest) as error:
        await WebHealthRoutes(Gateway()).health_settings(
            SimpleNamespace(method="POST")
        )
    assert error.value.text == "Choose a valid Google Health action."


@pytest.mark.parametrize(
    ("action", "message"),
    [
        ("pause", "Google Health personalization is paused."),
        ("enable", "Google Health personalization is enabled."),
        ("sync", "Google Health sync finished."),
        (
            "delete",
            "Google Health data was deleted and the integration was disabled.",
        ),
    ],
)
async def test_health_mutations_return_a_fresh_snapshot(monkeypatch, action, message):
    _patch_health_functions(monkeypatch)
    gateway = _Gateway(action)

    response = await WebHealthRoutes(gateway).health_settings(
        SimpleNamespace(method="POST")
    )

    assert response.text is not None
    payload = json.loads(response.text)
    assert payload["ok"] is True
    assert payload["message"] == message
    assert payload["connected"] is True
    assert gateway.auth_calls == 2
    assert gateway.throttle_calls == [(('health', 'user-1'), 12, 600)]


async def test_health_enable_surfaces_validation_error(monkeypatch):
    _patch_health_functions(
        monkeypatch,
        enable_health_integration=lambda _uid: (False, "Reconnect Google Health."),
    )

    with pytest.raises(web.HTTPBadRequest) as error:
        await WebHealthRoutes(_Gateway("enable")).health_settings(
            SimpleNamespace(method="POST")
        )
    assert error.value.text == "Reconnect Google Health."


async def test_health_failed_mutation_returns_service_unavailable(monkeypatch):
    _patch_health_functions(
        monkeypatch,
        sync_health_integration=lambda _uid: False,
    )

    with pytest.raises(web.HTTPServiceUnavailable) as error:
        await WebHealthRoutes(_Gateway("sync")).health_settings(
            SimpleNamespace(method="POST")
        )
    assert error.value.text == "Google Health could not complete that action."


async def test_health_connect_checks_readiness_and_single_flight(monkeypatch):
    _patch_health_functions(
        monkeypatch,
        get_connect_readiness=lambda: (False, "Missing Google credentials."),
    )
    with pytest.raises(web.HTTPServiceUnavailable) as error:
        await WebHealthRoutes(_Gateway("connect")).health_settings(
            SimpleNamespace(method="POST")
        )
    assert error.value.text == "Missing Google credentials."

    _patch_health_functions(monkeypatch)
    gateway = _Gateway("connect")
    gateway.health_connecting.add("user-1")
    with pytest.raises(web.HTTPConflict) as error:
        await WebHealthRoutes(gateway).health_settings(SimpleNamespace(method="POST"))
    assert error.value.text == "Google Health connection is already in progress."


async def test_health_connect_requires_authorization_url(monkeypatch):
    _patch_health_functions(
        monkeypatch,
        get_connect_authorization_url=lambda _uid: "",
    )

    with pytest.raises(web.HTTPServiceUnavailable) as error:
        await WebHealthRoutes(_Gateway("connect")).health_settings(
            SimpleNamespace(method="POST")
        )
    assert error.value.text == "Google Health could not start connecting."


async def test_health_connect_releases_slot_from_completion_callback(monkeypatch):
    callbacks = []
    _patch_health_functions(
        monkeypatch,
        run_connect_flow_async=lambda _uid, callback: callbacks.append(callback),
    )
    gateway = _Gateway("connect")

    response = await WebHealthRoutes(gateway).health_settings(
        SimpleNamespace(method="POST")
    )

    assert response.text is not None
    payload = json.loads(response.text)
    assert payload["url"] == "https://health.example/connect"
    assert payload["connecting"] is True
    assert "user-1" in gateway.health_connecting
    callbacks[0](True, "")
    assert "user-1" not in gateway.health_connecting
