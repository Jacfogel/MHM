"""Website conversation replies and authenticated chat routes."""

import asyncio

from aiohttp import web

from core.error_handling import handle_errors

WEBSITE_CHANNEL = "website"
MAX_SUGGESTIONS = 8
FALLBACK_REPLY = (
    "I'm having trouble processing your request right now. Please try again in a moment."
)


@handle_errors("shaping website chat reply", default_return=None)
def chat_payload(response) -> dict | None:
    """Return the plain reply and suggestion buttons a browser can render."""
    message = getattr(response, "message", "")
    if not isinstance(message, str) or not message.strip():
        message = "MHM could not answer that just now. Please try again."
    raw = getattr(response, "suggestions", None) or []
    suggestions = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, str):
                continue
            text = item.strip()
            if text and text not in suggestions:
                suggestions.append(text)
            if len(suggestions) >= MAX_SUGGESTIONS:
                break
    return {
        "reply": message,
        "suggestions": suggestions,
        "completed": bool(getattr(response, "completed", True)),
    }


@handle_errors(
    "building website chat reply",
    default_return={
        "reply": FALLBACK_REPLY,
        "suggestions": [],
        "completed": True,
    },
)
def website_chat_reply(user_id: str, message: str) -> dict:
    """Send one website message through the same path as Discord and email."""
    from communication.message_processing.interaction_manager import handle_user_message

    payload = chat_payload(handle_user_message(user_id, message, WEBSITE_CHANNEL))
    if payload is None:
        return {
            "reply": FALLBACK_REPLY,
            "suggestions": [],
            "completed": True,
        }
    return payload


class WebChatRoutes:
    """Handle the website chat route family using shared gateway infrastructure."""

    @handle_errors(
        "initializing website chat routes",
        user_friendly=False,
        re_raise=True,
    )
    def __init__(self, gateway):
        self.gateway = gateway

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by gateway middleware.
    async def chat_api(self, request):
        """Send one signed-in message through the website conversation channel."""
        uid, _current = await self.gateway.authenticated_account(request)
        data = await self.gateway.body(request)
        message = data.get("message")
        if set(data) != {"message"} or not isinstance(message, str):
            raise web.HTTPBadRequest(text="Enter a message to send.")
        message = message.strip()
        if not message or len(message) > 2000:
            raise web.HTTPBadRequest(
                text="Enter a message of up to 2000 characters."
            )
        self.gateway.throttle(("chat", uid), 30, 600)
        result = await asyncio.to_thread(website_chat_reply, uid, message)
        from communication.communication_channels.website.inbox import (
            append_website_chat_exchange,
        )

        await asyncio.to_thread(
            append_website_chat_exchange,
            uid,
            message,
            result.get("reply", ""),
        )
        return web.json_response(result)

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by gateway middleware.
    async def chat_inbox(self, request):
        """Return outbound messages stored for the always-on website channel."""
        from communication.communication_channels.website.inbox import (
            list_home_conversation,
            list_website_messages,
        )

        uid, _current = await self.gateway.authenticated_account(request)
        messages = await asyncio.to_thread(list_website_messages, uid)
        turns = await asyncio.to_thread(list_home_conversation, uid)
        return web.json_response({"messages": messages, "turns": turns})

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by gateway middleware.
    async def chat_reaction(self, request):
        """Apply More like this or Not for me to one scheduled chat message."""
        from messages.message_reactions import apply_message_reaction

        uid, _current = await self.gateway.authenticated_account(request)
        data = await self.gateway.body(request)
        kind = data.get("kind")
        delivery_id = data.get("delivery_id")
        if (
            set(data) != {"kind", "delivery_id"}
            or kind not in {"up", "down"}
            or not isinstance(delivery_id, str)
            or not delivery_id.strip()
            or len(delivery_id.strip()) > 80
        ):
            raise web.HTTPBadRequest(
                text="Choose more like this or not for me."
            )
        self.gateway.throttle(("reaction", uid), 30, 600)
        result = await asyncio.to_thread(
            apply_message_reaction,
            uid,
            "",
            kind,
            delivery_id=delivery_id.strip(),
        )
        status = str(result.get("status") or "")
        if status == "ignored":
            raise web.HTTPNotFound(
                text="That message cannot change later messages."
            )
        return web.json_response(
            {"status": status, "reply": str(result.get("reply") or "")}
        )


@handle_errors(
    "registering website chat routes",
    user_friendly=False,
    re_raise=True,
)
def register_chat_routes(app, gateway):
    """Register all website chat endpoints on a gateway application."""
    routes = WebChatRoutes(gateway)
    app.router.add_get("/api/chat", routes.chat_inbox)
    app.router.add_post("/api/chat", routes.chat_api)
    app.router.add_post("/api/chat/reactions", routes.chat_reaction)
