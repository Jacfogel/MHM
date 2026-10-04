"""Allowlisted website asset and font routes."""

from aiohttp import web

from core.error_handling import handle_errors


class WebAssetRoutes:
    """Serve public website files using the gateway's configured root."""

    @handle_errors(
        "initializing website asset routes",
        user_friendly=False,
        re_raise=True,
    )
    def __init__(self, gateway):
        """Keep the shared gateway root used by public asset endpoints."""
        self.gateway = gateway

    # Explicit allowlist keeps configs, Worker source, and docs off the local server.
    # ERROR_HANDLING_EXCLUDE: Route failures are translated by gateway middleware.
    async def asset(self, request):
        """Serve one explicitly allowlisted website asset from the local gateway."""
        name = request.match_info.get("name", "index.html")
        if name not in {
            "index.html",
            "login.html",
            "home.html",
            "setup.html",
            "app.html",
            "account-settings.html",
            "integrations.html",
            "tasks.html",
            "notes.html",
            "insights.html",
            "messages.html",
            "checkin.html",
            "privacy.html",
            "terms.html",
            "data.html",
            "styles.css",
            "mhm-logo.png",
            "script.js",
            "auth.js",
            "app.js",
            "home.js",
            "setup.js",
            "settings.js",
            "tasks.js",
            "notes.js",
            "insights.js",
            "integrations.js",
            "messages.js",
            "checkin.js",
        }:
            raise web.HTTPNotFound(text="Page not found.")
        return web.FileResponse(self.gateway.root / name)

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by gateway middleware.
    async def font_asset(self, request):
        """Serve one self-hosted typeface file."""
        name = request.match_info.get("name", "")
        if name not in {
            "inter-latin.woff2",
            "inter-latin-ext.woff2",
            "nunito-latin.woff2",
            "nunito-latin-ext.woff2",
        }:
            raise web.HTTPNotFound(text="Page not found.")
        return web.FileResponse(self.gateway.root / "fonts" / name)


@handle_errors(
    "registering website asset routes",
    user_friendly=False,
    re_raise=True,
)
def register_asset_routes(app, gateway):
    """Register public website asset endpoints on a gateway application."""
    routes = WebAssetRoutes(gateway)
    app.router.add_get("/", routes.asset)
    app.router.add_get("/fonts/{name}", routes.font_asset)
    app.router.add_get("/{name}", routes.asset)
