"""Authenticated Google Health integration routes."""

import asyncio

from aiohttp import web

from core.error_handling import handle_errors


class WebHealthRoutes:
    """Manage Google Health integration state using gateway infrastructure."""

    @handle_errors(
        "initializing website health routes",
        user_friendly=False,
        re_raise=True,
    )
    def __init__(self, gateway):
        """Keep the shared gateway services used by health endpoints."""
        self.gateway = gateway

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by gateway middleware.
    async def health_settings(self, request):
        """Read or change the signed-in user's Google Health integration."""
        uid, _ = await self.gateway.authenticated_account(request)
        from integrations.google_health.user_settings import (
            delete_health_integration,
            enable_health_integration,
            get_connect_authorization_url,
            get_connect_readiness,
            get_health_integration_status,
            pause_health_integration,
            run_connect_flow_async,
            sync_health_integration,
        )

        @handle_errors(
            "building Google Health website status",
            user_friendly=False,
            re_raise=True,
        )
        def snapshot():
            """Return the browser-safe Google Health state."""
            status = get_health_integration_status(uid)
            ready, readiness_error = get_connect_readiness()
            return {
                "feature_state": status.feature_state if status else "disabled",
                "connected": bool(status and status.connected),
                "last_success_at": status.last_success_at if status else "never",
                "has_recent_error": bool(status and status.has_recent_error),
                "connect_available": ready,
                "connect_error": readiness_error,
                "connecting": uid in self.gateway.health_connecting,
            }

        if request.method == "GET":
            return web.json_response(await asyncio.to_thread(snapshot))
        data = await self.gateway.body(request)
        if set(data) != {"action"} or data.get("action") not in {
            "connect",
            "pause",
            "enable",
            "sync",
            "delete",
        }:
            raise web.HTTPBadRequest(text="Choose a valid Google Health action.")
        action = data["action"]
        self.gateway.throttle(("health", uid), 12, 600)
        async with self.gateway.health_lock:
            await self.gateway.authenticated_account(request)
            if action == "connect":
                ready, error = await asyncio.to_thread(get_connect_readiness)
                if not ready:
                    raise web.HTTPServiceUnavailable(text=error)
                if uid in self.gateway.health_connecting:
                    raise web.HTTPConflict(
                        text="Google Health connection is already in progress."
                    )
                url = await asyncio.to_thread(get_connect_authorization_url, uid)
                if not url:
                    raise web.HTTPServiceUnavailable(
                        text="Google Health could not start connecting."
                    )
                self.gateway.health_connecting.add(uid)

                @handle_errors(
                    "finishing Google Health website connection",
                    user_friendly=False,
                    default_return=None,
                )
                def finished(_success, _error):
                    """Release the single in-progress connect slot for this user."""
                    self.gateway.health_connecting.discard(uid)

                run_connect_flow_async(uid, finished)
                return web.json_response({"ok": True, "url": url, **snapshot()})
            if action == "pause":
                ok = await asyncio.to_thread(pause_health_integration, uid)
                message = "Google Health personalization is paused."
            elif action == "enable":
                ok, error = await asyncio.to_thread(enable_health_integration, uid)
                message = "Google Health personalization is enabled."
                if not ok and error:
                    raise web.HTTPBadRequest(text=error)
            elif action == "sync":
                ok = await asyncio.to_thread(sync_health_integration, uid)
                message = "Google Health sync finished."
            else:
                ok = await asyncio.to_thread(delete_health_integration, uid)
                message = (
                    "Google Health data was deleted and the integration was disabled."
                )
            if not ok:
                raise web.HTTPServiceUnavailable(
                    text="Google Health could not complete that action."
                )
            return web.json_response({"ok": True, "message": message, **snapshot()})


@handle_errors(
    "registering website health routes",
    user_friendly=False,
    re_raise=True,
)
def register_health_routes(app, gateway):
    """Register Google Health endpoints on a gateway application."""
    routes = WebHealthRoutes(gateway)
    app.router.add_get("/api/health", routes.health_settings)
    app.router.add_post("/api/health", routes.health_settings)
