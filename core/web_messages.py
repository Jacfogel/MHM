"""Authenticated website routes for reusable message templates."""

import asyncio
import secrets

from aiohttp import web

from core.error_handling import handle_errors


class WebMessageRoutes:
    """Handle the message-template route family using gateway infrastructure."""

    @handle_errors(
        "initializing website message routes",
        user_friendly=False,
        re_raise=True,
    )
    def __init__(self, gateway):
        self.gateway = gateway

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by gateway middleware.
    async def messages_api(self, request):
        """Manage the signed-in user's reusable message templates."""
        uid, _ = await self.gateway.authenticated_account(request)
        from messages.message_data_manager import (
            add_message,
            delete_message,
            edit_message,
            is_ai_generated_message_category,
            load_user_messages,
        )

        options = await asyncio.to_thread(
            self.gateway.accounts.settings_options, uid
        )
        categories = [
            category
            for category in options.get("categories", [])
            if isinstance(category, str)
            and not is_ai_generated_message_category(category)
        ]
        category = request.match_info.get("category") or request.query.get(
            "category"
        )
        if not category and categories:
            category = categories[0]
        if category not in categories:
            raise web.HTTPBadRequest(
                text="Choose an available message category."
            )

        documents = await asyncio.to_thread(
            self.gateway.accounts.documents, uid
        )
        from core.profile_v2_io import schedule_categories

        schedule = schedule_categories(documents.get("schedules") or {})
        period_names = [
            name
            for name in (schedule.get(category, {}).get("periods") or {})
            if name != "ALL"
        ]

        @handle_errors(
            "serializing website message template",
            user_friendly=False,
            re_raise=True,
        )
        def view(message):
            """Return one browser-safe message template."""
            message_schedule = message.get("schedule") or {}
            return {
                "id": str(message.get("id") or ""),
                "text": str(message.get("text") or ""),
                "active": bool(message.get("active", True)),
                "days": [
                    str(day)
                    for day in message_schedule.get("days") or ["ALL"]
                ],
                "periods": [
                    str(period)
                    for period in message_schedule.get("periods") or ["ALL"]
                ],
                "updated_at": message.get("updated_at"),
            }

        # error_handling_exclude: Raises intentional HTTP validation responses;
        # unexpected failures propagate to the guarded messages_api boundary.
        def clean(data):
            """Validate an editable message template payload."""
            if set(data) != {"text", "active", "days", "periods"}:
                raise web.HTTPBadRequest(
                    text=(
                        "Submit the message text, schedule, and enabled state."
                    )
                )
            text = data["text"]
            days = data["days"]
            periods = data["periods"]
            valid_days = {
                "ALL",
                "MONDAY",
                "TUESDAY",
                "WEDNESDAY",
                "THURSDAY",
                "FRIDAY",
                "SATURDAY",
                "SUNDAY",
            }
            allowed_periods = {"ALL", *period_names}
            if (
                not isinstance(text, str)
                or not text.strip()
                or len(text.strip()) > 5000
            ):
                raise web.HTTPBadRequest(
                    text="Messages must be between 1 and 5,000 characters."
                )
            if type(data["active"]) is not bool:
                raise web.HTTPBadRequest(
                    text="Choose whether this message is enabled."
                )
            if (
                not isinstance(days, list)
                or not days
                or len(days) > 7
                or any(
                    not isinstance(day, str) or day not in valid_days
                    for day in days
                )
                or len(set(days)) != len(days)
                or ("ALL" in days and len(days) != 1)
            ):
                raise web.HTTPBadRequest(
                    text="Choose valid days for this message."
                )
            if (
                not isinstance(periods, list)
                or not periods
                or len(periods) > 20
                or any(
                    not isinstance(period, str)
                    or period not in allowed_periods
                    for period in periods
                )
                or len(set(periods)) != len(periods)
                or ("ALL" in periods and len(periods) != 1)
            ):
                raise web.HTTPBadRequest(
                    text="Choose valid reminder windows for this message."
                )
            return {
                "text": text.strip(),
                "active": data["active"],
                "schedule": {"days": days, "periods": periods},
            }

        if request.method == "GET":
            messages = await asyncio.to_thread(
                load_user_messages, uid, category
            )
            return web.json_response(
                {
                    "category": category,
                    "categories": categories,
                    "period_names": period_names,
                    "messages": [view(message) for message in messages],
                }
            )
        if request.method == "POST" and not request.match_info.get(
            "message_id"
        ):
            values = clean(await self.gateway.body(request))
            message_id = secrets.token_urlsafe(18)
            await asyncio.to_thread(
                add_message,
                uid,
                category,
                {"id": message_id, **values},
            )
        else:
            message_id = request.match_info.get("message_id")
            if not message_id or len(message_id) > 200:
                raise web.HTTPBadRequest(text="Choose a valid message.")
            existing = await asyncio.to_thread(
                load_user_messages, uid, category
            )
            if not any(
                str(message.get("id")) == message_id
                for message in existing
            ):
                raise web.HTTPNotFound(
                    text="That message could not be found."
                )
            if request.method == "PATCH":
                values = clean(await self.gateway.body(request))
                await asyncio.to_thread(
                    edit_message,
                    uid,
                    category,
                    message_id,
                    values,
                )
            elif request.method == "DELETE":
                if await self.gateway.body(request):
                    raise web.HTTPBadRequest(
                        text=(
                            "Deleting a message does not need a request body."
                        )
                    )
                await asyncio.to_thread(
                    delete_message, uid, category, message_id
                )
                return web.json_response({"ok": True})
            else:
                raise web.HTTPMethodNotAllowed(
                    request.method,
                    {"GET", "POST", "PATCH", "DELETE"},
                )
        saved = await asyncio.to_thread(load_user_messages, uid, category)
        message = next(
            (
                item
                for item in saved
                if str(item.get("id")) == message_id
            ),
            None,
        )
        if not message:
            raise web.HTTPServiceUnavailable(
                text="MHM could not finish saving that message."
            )
        return web.json_response(
            {"message": view(message)},
            status=201 if request.method == "POST" else 200,
        )


@handle_errors(
    "registering website message routes",
    user_friendly=False,
    re_raise=True,
)
def register_message_routes(app, gateway):
    """Register all message-template endpoints on a gateway application."""
    routes = WebMessageRoutes(gateway)
    app.router.add_get("/api/messages", routes.messages_api)
    app.router.add_post("/api/messages", routes.messages_api)
    app.router.add_route(
        "PATCH", "/api/messages/{category}/{message_id}", routes.messages_api
    )
    app.router.add_route(
        "DELETE", "/api/messages/{category}/{message_id}", routes.messages_api
    )
