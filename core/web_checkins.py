"""Authenticated website routes for daily check-ins."""

import asyncio

from aiohttp import web

from core.error_handling import handle_errors


class WebCheckinRoutes:
    """Handle the check-in route family using shared gateway infrastructure."""

    @handle_errors(
        "initializing website check-in routes",
        user_friendly=False,
        re_raise=True,
    )
    def __init__(self, gateway):
        self.gateway = gateway

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by gateway middleware.
    async def checkins_api(self, request):
        """Start or answer the signed-in user's check-in in the browser."""
        uid, _ = await self.gateway.authenticated_account(request)
        from checkins.checkin_data_manager import is_user_checkins_enabled
        from checkins.checkin_service import (
            get_checkin_start_status,
            today_checkin_energy,
        )
        from communication.message_processing.conversation_flow_manager import (
            conversation_manager,
        )

        enabled = bool(
            await asyncio.to_thread(is_user_checkins_enabled, uid)
        )
        energy_today = (
            await asyncio.to_thread(today_checkin_energy, uid)
            if enabled
            else None
        )

        # ERROR_HANDLING_EXCLUDE: Serializer is used only by this guarded route.
        def view(
            message,
            *,
            active,
            completed,
            completed_today,
            index,
            total,
            question_type,
        ):
            """Return the browser check-in state."""
            return {
                "enabled": enabled,
                "active": active,
                "completed": completed,
                "completed_today": completed_today,
                "message": message,
                "index": index,
                "total": total,
                "question_type": question_type if active else None,
                "energy_today": energy_today,
            }

        snapshot = (
            await asyncio.to_thread(
                conversation_manager.current_checkin_prompt, uid
            )
            or {}
        )
        status = (
            await asyncio.to_thread(get_checkin_start_status, uid)
            if enabled
            else None
        )
        completed_today = (
            status is not None
            and status.already_completed_today
            and not snapshot
        )
        finished_today = (
            f"You've already completed a check-in today at "
            f"{status.last_checkin_timestamp}. You can start a new check-in tomorrow."
            if completed_today and status is not None
            else ""
        )
        if request.method == "GET":
            if snapshot:
                message = snapshot.get("message") or ""
            elif not enabled:
                message = "Check-ins are off. You can turn them on in Account."
            elif completed_today:
                message = finished_today
            else:
                message = ""
            return web.json_response(
                view(
                    message,
                    active=bool(snapshot),
                    completed=False,
                    completed_today=completed_today,
                    index=snapshot.get("index"),
                    total=snapshot.get("total"),
                    question_type=snapshot.get("question_type"),
                )
            )

        data = await self.gateway.body(request)
        action = data.get("action")
        if action == "start" and set(data) == {"action"}:
            if not enabled:
                return web.json_response(
                    view(
                        "Check-ins are off. You can turn them on in Account.",
                        active=False,
                        completed=True,
                        completed_today=False,
                        index=None,
                        total=None,
                        question_type=None,
                    )
                )
            if completed_today:
                return web.json_response(
                    view(
                        finished_today,
                        active=False,
                        completed=True,
                        completed_today=True,
                        index=None,
                        total=None,
                        question_type=None,
                    )
                )
            message, completed = await asyncio.to_thread(
                conversation_manager.start_checkin, uid
            )
        elif action == "answer" and set(data) == {"action", "answer"}:
            answer = data.get("answer")
            if (
                not isinstance(answer, str)
                or not answer.strip()
                or len(answer.strip()) > 2000
            ):
                raise web.HTTPBadRequest(
                    text="Enter an answer, or skip this question."
                )
            result = await asyncio.to_thread(
                conversation_manager.answer_active_checkin,
                uid,
                answer.strip(),
            )
            if result is None:
                raise web.HTTPBadRequest(text="Start a check-in first.")
            message, completed = result
        elif action in {"skip", "cancel"} and set(data) == {"action"}:
            command = "skip" if action == "skip" else "/cancel"
            result = await asyncio.to_thread(
                conversation_manager.answer_active_checkin, uid, command
            )
            if result is None:
                raise web.HTTPBadRequest(text="Start a check-in first.")
            message, completed = result
        else:
            raise web.HTTPBadRequest(
                text="Choose start, answer, skip, or cancel."
            )
        if not isinstance(message, str):
            message = "MHM could not continue that check-in. Please try again."
        latest = (
            await asyncio.to_thread(
                conversation_manager.current_checkin_prompt, uid
            )
            or {}
        )
        active = bool(latest) and not completed
        return web.json_response(
            view(
                message,
                active=active,
                completed=bool(completed),
                completed_today=False,
                index=latest.get("index") if active else None,
                total=latest.get("total") if active else None,
                question_type=(
                    latest.get("question_type") if active else None
                ),
            )
        )


@handle_errors(
    "registering website check-in routes",
    user_friendly=False,
    re_raise=True,
)
def register_checkin_routes(app, gateway):
    """Register all check-in endpoints on a website gateway application."""
    routes = WebCheckinRoutes(gateway)
    app.router.add_get("/api/checkins", routes.checkins_api)
    app.router.add_post("/api/checkins", routes.checkins_api)
