"""Focused ownership checks for website message-template routes."""

from types import SimpleNamespace

import pytest

from core.error_handling import error_handler
from core.web_messages import WebMessageRoutes, register_message_routes

pytestmark = [pytest.mark.unit, pytest.mark.messages, pytest.mark.asyncio]


async def test_message_route_initialization_reports_and_reraises_errors(
    monkeypatch,
):
    calls = []
    monkeypatch.setattr(
        error_handler,
        "handle_error",
        lambda error, context, operation, user_friendly=True: calls.append(
            (error, operation, user_friendly)
        )
        or False,
    )

    class BrokenMessageRoutes(WebMessageRoutes):
        def __setattr__(self, _name, _value):
            raise RuntimeError("cannot initialize routes")

    with pytest.raises(RuntimeError, match="cannot initialize routes"):
        BrokenMessageRoutes(object())

    assert len(calls) == 1
    assert calls[0][1:] == ("initializing website message routes", False)


async def test_message_route_registration_reports_and_reraises_errors(
    monkeypatch,
):
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
        register_message_routes(app, object())

    assert len(calls) == 1
    assert calls[0][1:] == ("registering website message routes", False)
