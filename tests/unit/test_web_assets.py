"""Focused ownership checks for website asset and font routes."""

from pathlib import Path
from types import SimpleNamespace

from aiohttp import web
import pytest

from core.error_handling import error_handler
from core.web_assets import WebAssetRoutes, register_asset_routes

pytestmark = [pytest.mark.unit, pytest.mark.user, pytest.mark.asyncio]


async def test_asset_route_initialization_reports_and_reraises_errors(monkeypatch):
    calls = []
    monkeypatch.setattr(
        error_handler,
        "handle_error",
        lambda error, context, operation, user_friendly=True: calls.append(
            (error, operation, user_friendly)
        )
        or False,
    )

    class BrokenAssetRoutes(WebAssetRoutes):
        def __setattr__(self, _name, _value):
            raise RuntimeError("cannot initialize routes")

    with pytest.raises(RuntimeError, match="cannot initialize routes"):
        BrokenAssetRoutes(object())

    assert len(calls) == 1
    assert calls[0][1:] == ("initializing website asset routes", False)


async def test_asset_route_registration_reports_and_reraises_errors(monkeypatch):
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
        register_asset_routes(app, object())

    assert len(calls) == 1
    assert calls[0][1:] == ("registering website asset routes", False)


async def test_asset_routes_keep_files_inside_explicit_allowlists(tmp_path):
    routes = WebAssetRoutes(SimpleNamespace(root=tmp_path))

    asset = await routes.asset(SimpleNamespace(match_info={}))
    font = await routes.font_asset(
        SimpleNamespace(match_info={"name": "inter-latin.woff2"})
    )

    assert Path(asset._path) == tmp_path / "index.html"
    assert Path(font._path) == tmp_path / "fonts" / "inter-latin.woff2"
    with pytest.raises(web.HTTPNotFound) as asset_error:
        await routes.asset(SimpleNamespace(match_info={"name": "worker.mjs"}))
    assert asset_error.value.text == "Page not found."
    with pytest.raises(web.HTTPNotFound) as font_error:
        await routes.font_asset(SimpleNamespace(match_info={"name": "secret.txt"}))
    assert font_error.value.text == "Page not found."
