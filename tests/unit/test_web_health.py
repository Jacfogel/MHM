"""Focused ownership checks for Google Health website routes."""

import asyncio
import json
from types import SimpleNamespace

from aiohttp import web
import pytest

from core.error_handling import error_handler
from core.web_health import WebHealthRoutes, register_health_routes

pytestmark = [pytest.mark.unit, pytest.mark.user, pytest.mark.asyncio]


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
