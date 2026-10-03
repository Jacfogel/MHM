"""Focused ownership checks for website settings and insights routes."""

from types import SimpleNamespace

import pytest

from core.error_handling import error_handler
from core.web_settings import WebSettingsRoutes, register_settings_routes

pytestmark = [pytest.mark.unit, pytest.mark.user, pytest.mark.asyncio]


async def test_settings_route_initialization_reports_and_reraises_errors(monkeypatch):
    calls = []
    monkeypatch.setattr(
        error_handler,
        "handle_error",
        lambda error, context, operation, user_friendly=True: calls.append(
            (error, operation, user_friendly)
        )
        or False,
    )

    class BrokenSettingsRoutes(WebSettingsRoutes):
        def __setattr__(self, _name, _value):
            raise RuntimeError("cannot initialize routes")

    with pytest.raises(RuntimeError, match="cannot initialize routes"):
        BrokenSettingsRoutes(object())

    assert len(calls) == 1
    assert calls[0][1:] == ("initializing website settings routes", False)


async def test_settings_route_registration_reports_and_reraises_errors(monkeypatch):
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
        register_settings_routes(app, object())

    assert len(calls) == 1
    assert calls[0][1:] == ("registering website settings routes", False)
