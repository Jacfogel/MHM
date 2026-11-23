"""Authenticated WhatsApp connection and revocation routes."""

import asyncio
from aiohttp import web
from core import config
from core.error_handling import ValidationError, handle_errors
from core.whatsapp_enrollment import begin_whatsapp_enrollment, connect_whatsapp, disconnect_whatsapp, whatsapp_available, whatsapp_user_for_phone
from core.channel_access import channel_allowed


@handle_errors("registering WhatsApp account routes", user_friendly=False, re_raise=True)
def register_whatsapp_routes(app, gateway):
    """Keep connection proofs scoped to the authenticated account."""
    # ERROR_HANDLING_EXCLUDE: Route failures are translated by gateway middleware.
    async def enrollment(request):
        """Create a connection proof or consume it after signed phone verification."""
        uid, account = await gateway.authenticated_account(request)
        if request.method == "GET":
            phone = account.get("whatsapp_phone", "")
            ready = await asyncio.to_thread(whatsapp_user_for_phone, phone, require_paid=False)
            return web.json_response({"available": whatsapp_available(), "connected": ready == uid,
                                      "phone": phone, "sender": config.WHATSAPP_PHONE_NUMBER,
                                      "eligible": channel_allowed(account, "whatsapp"),
                                      "trial": account.get("subscription_status") == "trialing"})
        data = await gateway.body(request)
        action = data.get("action")
        try:
            if action == "start" and set(data) == {"action", "phone", "consent"}:
                token = await asyncio.to_thread(begin_whatsapp_enrollment, data["phone"], data["consent"], uid)
                return web.json_response({"token": token, "sender": config.WHATSAPP_PHONE_NUMBER})
            if action == "connect" and set(data) == {"action", "phone", "consent", "token"}:
                if not isinstance(data["token"], str) or len(data["token"]) != 32:
                    raise ValidationError("Request a new connection code.")
                await asyncio.to_thread(connect_whatsapp, uid, data["phone"], data["token"], data["consent"], uid)
                return web.json_response({"connected": True})
            if action == "disconnect" and set(data) == {"action"}:
                await asyncio.to_thread(disconnect_whatsapp, uid)
                return web.json_response({"connected": False})
            raise ValidationError("Choose a valid WhatsApp connection action.")
        except ValidationError as exc:
            raise web.HTTPBadRequest(text=str(exc)) from None

    app.router.add_get("/api/whatsapp/enrollment", enrollment)
    app.router.add_post("/api/whatsapp/enrollment", enrollment)
