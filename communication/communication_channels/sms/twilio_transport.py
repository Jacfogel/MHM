"""Live Twilio pilot: explicit account/number allowlist, durable inbound receipts."""

import re
import threading
from urllib.parse import urlsplit

from core import config
from core.sms_enrollment import sms_user_for_phone
from core.error_handling import ConfigurationError, handle_errors
from core.logger import get_component_logger
from storage.sms_state import SmsState

logger = get_component_logger("communication_manager")


class TwilioTransport:
    """Own provider boundaries; keep task/check-in mutations in shared handlers."""

    @handle_errors("initializing Twilio pilot", re_raise=True, user_friendly=False, retry_after_recovery=False)
    def __init__(self, bot):
        """Validate owner consent and pilot settings before creating the provider client."""
        from twilio.http.http_client import TwilioHttpClient
        from twilio.rest import Client
        from communication.communication_channels.sms.phone import normalize_phone

        public = urlsplit(config.SMS_PUBLIC_BASE_URL)
        if (config.SMS_SIMULATION_ENABLED or not config.SMS_TWILIO_ENABLED
                or not config.TWILIO_ACCOUNT_SID.startswith("AC")
                or not config.TWILIO_AUTH_TOKEN
                or not normalize_phone(config.TWILIO_PHONE_NUMBER)
                or public.scheme != "https" or not public.netloc
                or public.query or public.fragment or public.username or public.password
                or public.path not in {"", "/"}):
            raise ConfigurationError("Complete the Twilio credentials, sending number, and HTTPS URL; disable simulation before enabling live SMS.")
        self.bot = bot
        self.sender = normalize_phone(config.TWILIO_PHONE_NUMBER)
        self.state = SmsState()
        self.lock = threading.RLock()
        self.client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN,
                             http_client=TwilioHttpClient(timeout=10, max_retries=0))

    @handle_errors("checking SMS pilot recipient", default_return=False, user_friendly=False, retry_after_recovery=False)
    def allowed(self, number):
        """Confirm a verified recipient still belongs to an eligible paid account."""

        return sms_user_for_phone(number) is not None

    @handle_errors("sending Twilio SMS", default_return="unconfirmed", retry_after_recovery=False)
    def send(self, recipient, message, **kwargs):
        """Serialize one submission and preserve uncertain outcomes without automatic retry."""
        with self.lock:
            return self._send(recipient, message, **kwargs)

    # error_handling_exclude: decorated send owns failures; provider exceptions must distinguish rejection from uncertain acceptance without retry.
    def _send(self, recipient, message, **kwargs):
        """Submit once, distinguishing provider rejection from uncertain acceptance."""
        from twilio.base.exceptions import TwilioRestException
        from communication.communication_channels.sms.phone import normalize_phone

        self.bot.last_outbound_message_id = None
        number = normalize_phone(recipient)
        if (not self.bot.is_ready() or not number or not self.allowed(number)
                or kwargs.get("user_id", sms_user_for_phone(number)) != sms_user_for_phone(number)
                or self.state.stopped(number) or not isinstance(message, str)
                or not message.strip() or len(message) > 1600):
            self.bot.error_message = "Text not submitted. Check SMS status, consent, recipient, and the 1,600-character message limit."
            return False
        kind = kwargs.get("reply_kind", "")
        task_id = str(kwargs.get("task_id", ""))
        # Record possible context before submission so a very fast reply cannot
        # be applied to another prompt. An uncertain send retains its context.
        if kind in {"task_reminder", "checkin"}:
            self.state.add_context(number, kind, task_id)
        try:
            result = self.client.messages.create(
                to=number, from_=self.sender, body=message,
                status_callback=config.SMS_PUBLIC_BASE_URL + "/sms/status",
            )
        except TwilioRestException as exc:
            # Explicit 4xx rejection is safe to report as not accepted. Network
            # errors and server errors can follow acceptance: never auto-resend.
            if 400 <= exc.status < 500:
                self.bot.error_message = f"The SMS provider rejected this text (code {exc.code or exc.status}). Check provider settings before retrying."
                if exc.code == 21610:
                    self.state.set_stopped(number, True)
                return False
            self.bot.error_message = "SMS acceptance is uncertain. Check Twilio message history before sending another copy."
            return "unconfirmed"
        except Exception:
            logger.warning("Twilio submission outcome uncertain; automatic resend suppressed")
            self.bot.error_message = "SMS acceptance is uncertain. Check Twilio message history before sending another copy."
            return "unconfirmed"
        self.bot.last_outbound_message_id = result.sid
        self.state.record_outbound(result.sid, result.status or "queued")
        self.bot.error_message = None
        return True

    @handle_errors("processing signed SMS webhook", default_return=503, user_friendly=False, retry_after_recovery=False)
    def process(self, path, params, signature):
        """Validate the fixed public URL; never trust forwarded/Host headers."""
        from twilio.request_validator import RequestValidator

        if path not in {"/sms/incoming", "/sms/status"}:
            return 404
        url = config.SMS_PUBLIC_BASE_URL + path
        if not signature or not RequestValidator(config.TWILIO_AUTH_TOKEN).validate(url, params, signature):
            return 403
        if params.get("AccountSid") != config.TWILIO_ACCOUNT_SID:
            return 403
        if not self.bot.is_ready():
            return 503
        sid = params.get("MessageSid", "")
        if not re.fullmatch(r"SM[0-9a-fA-F]{32}", sid):
            return 400
        with self.lock:
            if path == "/sms/status":
                self.state.update_status(sid, params.get("MessageStatus", ""),
                                         params.get("ErrorCode", "")[:16])
                return 200
            from communication.communication_channels.sms.phone import normalize_phone

            if normalize_phone(params.get("To", "")) != self.sender:
                return 403

            number = normalize_phone(params.get("From", ""))
            # LINK only proves ownership; account binding requires the original UI secret and consent.
            link = re.fullmatch(r"LINK ([0-9a-fA-F]{32})", params.get("Body", "").strip(), re.IGNORECASE)
            if link:
                if not self.state.claim(sid):
                    return 200
                self.state.verify_enrollment(number, link[1].lower())
                self.state.finish(sid, "handled")
                return 200
            user_id = sms_user_for_phone(number, require_paid=False)
            if not user_id:
                return 403
            if not self.state.claim(sid):
                return 200
            try:
                text = params.get("Body", "").strip()
                opt = params.get("OptOutType", "").upper()
                keyword = text.upper()
                if opt in {"STOP", "START", "HELP"} or keyword in {"STOP", "STOPALL", "UNSUBSCRIBE", "CANCEL", "END", "QUIT", "START", "UNSTOP", "HELP", "INFO"}:
                    if opt == "STOP" or keyword in {"STOP", "STOPALL", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"}:
                        self.state.set_stopped(number, True)
                    elif opt == "START" or keyword in {"START", "UNSTOP"}:
                        self.state.set_stopped(number, False)
                    # Twilio sends keyword confirmations. Never send a duplicate.
                elif not self.state.stopped(number) and sms_user_for_phone(number) == user_id and text and len(text) <= 1600:
                    reply = self.route(text, user_id, number)
                    if len(reply) > 1600:
                        reply = reply[:1500] + "\n[Reply shortened for SMS. Open MHM for the full details.]"
                    result = self.send(number, reply, user_id=user_id)
                    self.state.finish(sid, "handled" if result is True else "reply_unconfirmed")
                    return 200
                self.state.finish(sid, "handled")
                return 200
            except Exception:
                # Claim remains durable even if a mutation succeeded before an
                # exception. Replaying it could complete another recurring task.
                self.state.finish(sid, "needs_review")
                logger.error("SMS processing outcome unconfirmed; receipt retained for manual review")
                return 200

    @handle_errors("routing SMS command", re_raise=True, user_friendly=False, retry_after_recovery=False)
    def route(self, text, user_id, number):
        """Route an explicit command or an unambiguous short reply through shared handlers."""
        from communication.message_processing.phone_reply_routing import route_phone_reply

        return route_phone_reply(self.state, text, user_id, number, "sms")
