"""Authenticated website settings and insights routes."""

import asyncio
import json

from aiohttp import web

from core.error_handling import ValidationError, handle_errors
from core.web_user_settings import (
    build_settings_updates,
    remember_setup_complete,
    settings_snapshot,
)


class WebSettingsRoutes:
    """Handle self-service settings and insights using gateway infrastructure."""

    @handle_errors(
        "initializing website settings routes",
        user_friendly=False,
        re_raise=True,
    )
    def __init__(self, gateway):
        """Keep the shared gateway services used by settings endpoints."""
        self.gateway = gateway

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by gateway middleware.
    async def settings(self, request):
        """Read or atomically save one allowlisted self-service settings section."""
        uid, _ = await self.gateway.authenticated_account(request)
        async with self.gateway.settings_lock:
            documents = await asyncio.to_thread(self.gateway.accounts.documents, uid)
            options = await asyncio.to_thread(
                self.gateway.accounts.settings_options, uid
            )
            snapshot = settings_snapshot(documents, options)
            if request.method == "GET":
                return web.json_response(snapshot)
            data = await self.gateway.body(request)
            section = data.get("section")
            complete_setup = data.get("complete_setup") is True
            expected = {"section", "values", "revision"}
            if complete_setup:
                expected.add("complete_setup")
            if (
                set(data) != expected
                or not isinstance(section, str)
                or section not in snapshot["sections"]
            ):
                raise web.HTTPBadRequest(text="Choose a valid settings section.")
            if data["revision"] != snapshot["revisions"][section]:
                raise web.HTTPConflict(
                    text="These settings changed elsewhere. Reload them before saving your edits."
                )
            try:
                updates = build_settings_updates(
                    documents, options, section, data["values"]
                )
            except ValidationError as exc:
                raise web.HTTPBadRequest(text=str(exc)) from None
            if not await asyncio.to_thread(
                self.gateway.accounts.save_settings, uid, updates
            ):
                raise web.HTTPServiceUnavailable(
                    text="MHM could not finish saving. Reload these settings to check their current values before trying again."
                )
            if complete_setup and section in {"messages", "tasks", "checkins"}:
                account_doc = documents.get("account")
                if isinstance(account_doc, dict):
                    remember_setup_complete(account_doc)
                mark = getattr(self.gateway.accounts, "mark_setup_complete", None)
                if mark is not None:
                    await asyncio.to_thread(mark, uid)
            latest = await asyncio.to_thread(self.gateway.accounts.documents, uid)
            return web.json_response(settings_snapshot(latest, options))

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by gateway middleware.
    async def insights(self, request):
        """Return authenticated wellness, habit, and check-in analytics."""
        uid, _ = await self.gateway.authenticated_account(request)
        try:
            days = int(request.query.get("days", "30"))
        except ValueError:
            raise web.HTTPBadRequest(
                text="Choose a valid analysis period."
            ) from None
        if days not in {7, 14, 30, 60, 90}:
            raise web.HTTPBadRequest(text="Choose 7, 14, 30, 60, or 90 days.")

        @handle_errors(
            "building website insights",
            user_friendly=False,
            re_raise=True,
        )
        def build_insights():
            """Build one JSON-safe analytics snapshot off the event loop."""
            from checkins.checkin_analytics import CheckinAnalytics

            analytics = CheckinAnalytics()
            result = {
                "days": days,
                "available": analytics.get_available_data_types(uid, days),
                "wellness": analytics.get_wellness_score(uid, days),
                "mood": analytics.get_mood_trends(uid, days),
                "energy": analytics.get_energy_trends(uid, days),
                "habits": analytics.get_habit_analysis(uid, days),
                "sleep": analytics.get_sleep_analysis(uid, days),
                "quantitative": analytics.get_quantitative_summaries(uid, days),
                "completion": analytics.get_completion_rate(uid, days),
                "history": analytics.get_checkin_history(uid, days)[:100],
            }
            return json.loads(json.dumps(result, default=str))

        return web.json_response(await asyncio.to_thread(build_insights))


@handle_errors(
    "registering website settings routes",
    user_friendly=False,
    re_raise=True,
)
def register_settings_routes(app, gateway):
    """Register settings and insights endpoints on a gateway application."""
    routes = WebSettingsRoutes(gateway)
    app.router.add_get("/api/settings", routes.settings)
    app.router.add_post("/api/settings", routes.settings)
    app.router.add_get("/api/insights", routes.insights)
