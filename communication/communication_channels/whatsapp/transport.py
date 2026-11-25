"""Signed Meta events and single-attempt Cloud API submission."""

import hashlib
import hmac
import json
import re
import secrets
import threading
from typing import Any

import requests

from core import config
from core.error_handling import CommunicationError, ConfigurationError, handle_errors
from core.logger import get_component_logger
from core.time_utilities import now_datetime_full
from core.whatsapp_enrollment import whatsapp_available, whatsapp_user_for_phone
from communication.communication_channels.sms.phone import normalize_phone
from communication.message_processing.phone_reply_routing import route_phone_reply
from storage.whatsapp_state import WhatsAppState

logger = get_component_logger("communication_manager")


class MetaTransport:
    """Keep provider I/O and identity checks outside shared business handlers."""

    @handle_errors("initializing Meta WhatsApp transport", re_raise=True, user_friendly=False, retry_after_recovery=False)
    def __init__(self, bot):
        if (not whatsapp_available() or not config.WHATSAPP_PHONE_NUMBER_ID.isdigit()
                or not config.WHATSAPP_BUSINESS_ACCOUNT_ID.isdigit()
                or not re.fullmatch(r"v[0-9]+\.0", config.WHATSAPP_API_VERSION)):
            raise ConfigurationError("Complete the WhatsApp Meta credentials, business and phone IDs, sending number, and API version.")
        self.bot = bot
        self.state = WhatsAppState()
        self.lock = threading.RLock()
        self.url = f"https://graph.facebook.com/{config.WHATSAPP_API_VERSION}/{config.WHATSAPP_PHONE_NUMBER_ID}/messages"

    @handle_errors("sending Meta WhatsApp message", default_return="unconfirmed", user_friendly=False, retry_after_recovery=False)
    def send(self, recipient, message, **kwargs):
        with self.lock:
            self.bot.last_outbound_message_id = None
            number = normalize_phone(recipient)
            uid = whatsapp_user_for_phone(number)
            if (not self.bot.is_ready() or not number or not uid
                    or kwargs.get("user_id", uid) != uid or self.state.stopped(number)
                    or not isinstance(message, str) or not message.strip() or len(message) > 4096):
                self.bot.error_message = "Message not submitted. Check WhatsApp connection, paid plan, consent, recipient, and the 4,096-character limit."
                return False
            kind, task_id = kwargs.get("reply_kind", ""), str(kwargs.get("task_id", ""))
            payload: dict[str, Any] = {"messaging_product": "whatsapp", "to": number[1:]}
            pending_id = None
            if self.state.window_open(number):
                payload.update(type="text", text={"body": message, "preview_url": False})
                if kind in {"task_reminder", "checkin"}:
                    self.state.add_context(number, kind, task_id)
            else:
                template = config.WHATSAPP_NOTIFICATION_TEMPLATE
                if not re.fullmatch(r"[a-z0-9_]+", template):
                    self.bot.error_message = "WhatsApp's reply window is closed. Configure an approved MHM notification template before sending scheduled messages."
                    return False
                payload.update(type="template", template={"name": template, "language": {"code": config.WHATSAPP_TEMPLATE_LANGUAGE}})
                pending_id = secrets.token_hex(16)
                self.state.save_pending(pending_id, number, uid, message, kind, task_id)
            outcome = self._submit(payload)
            if outcome is False and pending_id:
                self.state.remove_pending(pending_id)
            return outcome

    # error_handling_exclude: decorated send owns failures; never retry a possibly accepted provider submission.
    def _submit(self, payload):
        try:
            response = requests.post(self.url, headers={"Authorization": f"Bearer {config.WHATSAPP_ACCESS_TOKEN}"},
                                     json=payload, timeout=10, allow_redirects=False)
            if 400 <= response.status_code < 500:
                self.bot.error_message = f"WhatsApp rejected the message (HTTP {response.status_code}). Check Meta settings before retrying."
                return False
            if not 200 <= response.status_code < 300:
                self.bot.error_message = "WhatsApp acceptance is uncertain. Check Meta delivery history before sending another copy."
                return "unconfirmed"
            data = response.json()
            identifier = data["messages"][0]["id"]
            if not isinstance(identifier, str) or not identifier.startswith("wamid."):
                raise CommunicationError("WhatsApp did not return a valid provider receipt")
        except Exception:
            logger.warning("WhatsApp submission outcome uncertain; automatic resend suppressed")
            self.bot.error_message = "WhatsApp acceptance is uncertain. Check Meta delivery history before sending another copy."
            return "unconfirmed"
        self.bot.last_outbound_message_id = identifier
        self.state.record_outbound(identifier, "accepted", user_id=whatsapp_user_for_phone("+" + payload["to"], require_paid=False))
        self.bot.error_message = None
        return True

    @handle_errors("processing Meta WhatsApp event", default_return=503, user_friendly=False, retry_after_recovery=False)
    def process(self, raw, signature):
        expected = "sha256=" + hmac.new(config.WHATSAPP_APP_SECRET.encode(), raw, hashlib.sha256).hexdigest()
        if not signature or not hmac.compare_digest(signature, expected):
            return 403
        if not self.bot.is_ready():
            return 503
        try:
            payload = json.loads(raw)
            if not isinstance(payload, dict) or payload.get("object") != "whatsapp_business_account":
                return 400
            entries = payload.get("entry", [])
            # Validate all destinations before processing any part of a batch.
            for entry in entries:
                if entry.get("id") != config.WHATSAPP_BUSINESS_ACCOUNT_ID:
                    return 403
                for change in entry.get("changes", []):
                    if change.get("field") != "messages":
                        continue
                    if change["value"].get("metadata", {}).get("phone_number_id") != config.WHATSAPP_PHONE_NUMBER_ID:
                        return 403
        except (ValueError, TypeError, AttributeError, KeyError):
            return 400
        with self.lock:
            for entry in entries:
                for change in entry.get("changes", []):
                    if change.get("field") != "messages":
                        continue
                    value = change["value"]
                    for status in value.get("statuses", []):
                        identifier = status.get("id", "")
                        if isinstance(identifier, str) and identifier.startswith("wamid."):
                            self.state.update_status(identifier, status.get("status", ""))
                    for message in value.get("messages", []):
                        self._incoming(message)
        return 200

    # error_handling_exclude: process owns the boundary; claimed commands must never be automatically replayed.
    def _incoming(self, message):
        identifier = message.get("id", "")
        number = normalize_phone("+" + str(message.get("from", "")))
        if not number or not isinstance(identifier, str) or not identifier.startswith("wamid.") or len(identifier) > 512:
            return
        try:
            timestamp = int(message.get("timestamp", ""))
        except (ValueError, TypeError):
            return
        if timestamp <= 0 or timestamp > now_datetime_full().timestamp() + 60:
            return
        if not self.state.claim(identifier, user_id=whatsapp_user_for_phone(number, require_paid=False) or ""):
            return
        try:
            if message.get("type") != "text":
                self.state.finish(identifier, "unsupported")
                return
            text = message.get("text", {}).get("body", "").strip()
            self.state.record_inbound(number, timestamp)
            link = re.fullmatch(r"LINK ([0-9a-fA-F]{32})", text, re.IGNORECASE)
            if link:
                self.state.verify_enrollment(number, link[1].lower())
                self.state.finish(identifier, "handled")
                return
            uid = whatsapp_user_for_phone(number, require_paid=False)
            if not uid:
                self.state.finish(identifier, "unregistered")
                return
            if text.upper() in {"STOP", "START"}:
                self.state.set_stopped(number, text.upper() == "STOP")
                # STOP produces no outbound application message. START can be used even after paid access ends.
                self.state.finish(identifier, "handled")
                return
            if self.state.stopped(number) or whatsapp_user_for_phone(number) != uid or not text or len(text) > 4096:
                self.state.finish(identifier, "ignored")
                return
            if not self.state.window_open(number):
                # A delayed webhook cannot authorize fresh business mutations.
                self.state.finish(identifier, "expired")
                return
            if text.upper() == "OPEN":
                outcome = self._open_pending(number, uid)
            else:
                reply = route_phone_reply(self.state, text, uid, number, "whatsapp")
                if len(reply) > 4096:
                    reply = reply[:3990] + "\n[Reply shortened. Open MHM for the full details.]"
                outcome = self.send(number, reply, user_id=uid)
            self.state.finish(identifier, "handled" if outcome is True else "reply_unconfirmed")
        except Exception:
            self.state.finish(identifier, "needs_review")
            logger.error("WhatsApp processing outcome uncertain; receipt retained for manual review")

    # error_handling_exclude: process owns failures; remove each saved body before submission to prevent uncertain sends from replaying.
    def _open_pending(self, number, uid):
        """Submit and remove saved messages after the user reopens the reply window."""
        pending = self.state.pending(number, uid)
        if not pending:
            return self.send(number, "No saved WhatsApp messages. Send help for available commands.", user_id=uid)
        for identifier, body, kind, task_id in pending:
            self.state.remove_pending(identifier)
            outcome = self.send(number, body, user_id=uid, reply_kind=kind, task_id=task_id)
            if outcome is not True:
                return outcome
        return True
