"""Email-verified browser access to the existing MHM account store.

Run one gateway process beside MHM. Challenges and sessions are intentionally
ephemeral: restarting the gateway signs browsers out, without changing accounts.
"""

import asyncio
import hashlib
import re
import secrets
import smtplib
import ssl
import time
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import aiohttp
from aiohttp import web

from core import config
from core.error_handling import (
    CommunicationError,
    ConfigurationError,
    DataError,
    ValidationError,
    handle_errors,
)
from core.logger import get_component_logger

logger = get_component_logger("main")
COOKIE = "mhm_session"
CODE_TTL = 600
SESSION_TTL = 12 * 60 * 60
DISCORD_STATE_TTL = 600
DISCORD_AUTHORIZE_URL = "https://discord.com/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_USER_URL = "https://discord.com/api/users/@me"


class MHMAccounts:
    """Use product persistence; never maintain a separate website account database."""

    @handle_errors("listing website accounts", user_friendly=False, default_return=[])
    def all(self):
        """Return account documents paired with their canonical user IDs."""
        from core import get_all_user_ids, get_user_data

        return [
            (uid, get_user_data(uid, "account").get("account") or {})
            for uid in get_all_user_ids()
        ]

    @handle_errors("finding website account by email", user_friendly=False)
    def by_email(self, email):
        """Return the unique account matching an email address, if one exists."""
        matches = [
            (uid, account)
            for uid, account in self.all()
            if account.get("email", "").strip().casefold() == email.casefold()
        ]
        # Email addresses must identify exactly one account.
        return matches[0] if len(matches) == 1 else None

    @handle_errors("checking website account email", user_friendly=False, default_return=False)
    def email_exists(self, email):
        """Return whether any account already uses an email address."""
        return any(
            account.get("email", "").casefold() == email.casefold()
            for _, account in self.all()
        )

    @handle_errors("checking website account username", user_friendly=False, default_return=False)
    def username_exists(self, username):
        """Return whether any account already uses an internal username."""
        return any(
            account.get("internal_username", "").casefold() == username.casefold()
            for _, account in self.all()
        )

    @handle_errors("loading website account", user_friendly=False, default_return={})
    def get(self, uid):
        """Load one account document by canonical user ID."""
        from core import get_user_data

        return get_user_data(uid, "account").get("account") or {}

    @handle_errors("loading website account documents", user_friendly=False, re_raise=True)
    def documents(self, uid):
        """Load the account documents exposed through self-service settings."""
        from core import get_user_data

        return get_user_data(uid, ["account", "preferences", "context", "schedules"])

    @handle_errors("loading website settings options", user_friendly=False, re_raise=True)
    def settings_options(self, uid):
        """Load the allowed settings choices for one account."""
        from core.web_user_settings import settings_options

        return settings_options(uid)

    @handle_errors("saving website account settings", user_friendly=False, default_return=False)
    def save_settings(self, uid, updates):
        """Persist validated self-service settings updates for one account."""
        from core.web_user_settings import save_settings

        return save_settings(uid, updates)

    @handle_errors("linking website Discord account", user_friendly=False, default_return="failed")
    def link_discord(self, uid, discord_user_id, discord_username):
        """Link a unique Discord identity to an existing MHM account."""
        from core import get_all_user_ids, get_user_data, update_user_account

        current = get_user_data(uid, "account").get("account") or {}
        current_discord_id = str(current.get("discord_user_id", ""))
        if current_discord_id and current_discord_id != discord_user_id:
            return "different_linked"
        for other_uid in get_all_user_ids():
            if other_uid == uid:
                continue
            other = get_user_data(other_uid, "account").get("account") or {}
            if str(other.get("discord_user_id", "")) == discord_user_id:
                return "already_linked"
        return (
            "linked"
            if update_user_account(
                uid,
                {
                    "discord_user_id": discord_user_id,
                    "discord_username": discord_username,
                },
                auto_create=False,
            )
            else "failed"
        )

    @handle_errors("creating website account", user_friendly=False)
    def create(self, email, username, timezone):
        """Create an MHM account after website email verification succeeds."""
        from core import create_new_user

        return create_new_user(
            {
                "internal_username": username,
                "email": email,
                "chat_id": email,
                "timezone": timezone,
                "channel": {"type": "email"},
                "categories": [],
                "messages_enabled": False,
                "task_settings": {"enabled": False},
                "checkin_settings": {"enabled": False},
            }
        )


def send_code(email, code):
    """Use MHM's configured SMTP account, with TLS and no code logging."""
    smtp_server = config.EMAIL_SMTP_SERVER
    smtp_username = config.EMAIL_SMTP_USERNAME
    smtp_password = config.EMAIL_SMTP_PASSWORD
    if (
        not isinstance(smtp_server, str)
        or not smtp_server
        or not isinstance(smtp_username, str)
        or not smtp_username
        or not isinstance(smtp_password, str)
        or not smtp_password
    ):
        raise ConfigurationError("Website email delivery is not configured")
    message = EmailMessage()
    message["From"] = smtp_username
    message["To"] = email
    message["Subject"] = "Your MHM sign-in code"
    message.set_content(
        f"Your MHM code is: {code}\n\nIt expires in 10 minutes.\nIf you did not request this, ignore this email."
    )
    try:
        with smtplib.SMTP_SSL(
            smtp_server, 465, timeout=10, context=ssl.create_default_context()
        ) as smtp:
            smtp.login(smtp_username, smtp_password)
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        raise CommunicationError("Website verification email delivery failed") from exc


@dataclass
class Challenge:
    digest: str
    expires: float
    email: str
    mode: str
    username: str
    timezone: str
    user_id: str | None
    eligible: bool
    attempts: int = 0


async def _fetch_discord_identity(code, *, client_id, client_secret, redirect_uri):
    """Exchange a Discord OAuth code and return the verified user identity."""
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                DISCORD_TOKEN_URL,
                data={
                    "client_id": str(client_id),
                    "client_secret": client_secret,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            ) as response:
                if response.status != 200:
                    raise CommunicationError(
                        "Discord authorization could not be completed"
                    )
                token = await response.json()
            access_token = (
                token.get("access_token") if isinstance(token, dict) else None
            )
            if not isinstance(access_token, str) or not access_token:
                raise DataError(
                    "Discord authorization did not return an access token"
                )
            async with session.get(
                DISCORD_USER_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            ) as response:
                if response.status != 200:
                    raise CommunicationError("Discord identity could not be read")
                identity = await response.json()
    except (CommunicationError, DataError, ValidationError):
        raise
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as exc:
        raise CommunicationError("Discord identity request failed") from exc
    if not isinstance(identity, dict):
        raise ValidationError("Discord identity was invalid")
    discord_user_id = str(identity.get("id", ""))
    if not re.fullmatch(r"\d{1,30}", discord_user_id):
        raise ValidationError("Discord identity was invalid")
    username = identity.get("global_name") or identity.get("username") or ""
    if not isinstance(username, str):
        username = ""
    return discord_user_id, username[:100]


def create_web_app(
    *,
    accounts=None,
    mailer=None,
    origin=None,
    proxy_secret=None,
    clock=time.monotonic,
    discord_identity=None,
):
    """Construct an injectable gateway; tests use isolated account and email adapters."""
    accounts = accounts or MHMAccounts()
    test_mailer = mailer is not None
    mailer = mailer or send_code
    origin = origin or config.WEB_PUBLIC_ORIGIN
    proxy_secret = config.WEB_PROXY_SECRET if proxy_secret is None else proxy_secret
    try:
        parsed = urlsplit(origin)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError("WEB_PUBLIC_ORIGIN must be a valid URL origin") from exc
    local = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}
    if (
        parsed.path
        or parsed.query
        or parsed.fragment
        or not parsed.netloc
        or parsed.username
        or parsed.password
    ):
        raise ConfigurationError(
            "WEB_PUBLIC_ORIGIN must be an exact origin without a path"
        )
    if not local and (parsed.scheme != "https" or len(proxy_secret) < 32):
        raise ConfigurationError(
            "Production web access requires HTTPS and a WEB_PROXY_SECRET of at least 32 characters"
        )
    challenges = {}
    sessions = {}
    limits = {}
    verification_lock = asyncio.Lock()
    settings_lock = asyncio.Lock()
    discord_link_lock = asyncio.Lock()
    discord_states = {}
    discord_identity = discord_identity or _fetch_discord_identity

    # ERROR_HANDLING_EXCLUDE: Pure closure protected by the gateway middleware.
    def discord_redirect_uri():
        """Return the configured Discord callback URI or the website default."""
        configured = str(
            getattr(config, "DISCORD_OAUTH_REDIRECT_URI", "") or ""
        ).strip()
        return configured or f"{origin}/api/auth/discord/callback"

    # ERROR_HANDLING_EXCLUDE: Pure closure protected by the gateway middleware.
    def discord_available():
        """Return whether the Discord OAuth credentials are configured."""
        return bool(config.DISCORD_APPLICATION_ID and config.DISCORD_CLIENT_SECRET)

    # ERROR_HANDLING_EXCLUDE: Pure closure protected by the gateway middleware.
    def website_redirect(path, **params):
        """Build a same-origin website redirect with encoded query parameters."""
        query = urlencode(params)
        return f"{origin}{path}{('?' + query) if query else ''}"

    # ERROR_HANDLING_EXCLUDE: In-memory cleanup runs inside the gateway middleware.
    def prune():
        """Remove expired challenges, sessions, rate limits, and OAuth states."""
        now = clock()
        for key in [key for key, value in challenges.items() if value.expires <= now]:
            del challenges[key]
        for key in [key for key, value in sessions.items() if value[1] <= now]:
            del sessions[key]
        for key in [key for key, value in limits.items() if value[1] <= now]:
            del limits[key]
        for key in [key for key, value in discord_states.items() if value[1] <= now]:
            del discord_states[key]

    # ERROR_HANDLING_EXCLUDE: Validation helper raises HTTP errors for the middleware.
    def throttle(key, maximum, window):
        """Count a rate-limit key and reject requests beyond its active window."""
        count, expires = limits.get(key, (0, clock() + window))
        if count >= maximum:
            raise web.HTTPTooManyRequests(
                text="Too many attempts. Please wait before trying again."
            )
        if len(limits) >= 10000 and key not in limits:
            raise web.HTTPTooManyRequests(text="MHM is busy. Please try again later.")
        limits[key] = (count + 1, expires)

    # ERROR_HANDLING_EXCLUDE: This is the central request error boundary by design.
    @web.middleware
    async def guard(request, handler):
        """Enforce proxy, origin, JSON, security-header, and safe-error policies."""
        try:
            if request.path.startswith("/api/"):
                prune()
                if proxy_secret and not secrets.compare_digest(
                    request.headers.get("X-MHM-Proxy-Secret", ""), proxy_secret
                ):
                    raise web.HTTPForbidden(text="This request cannot be accepted.")
                if request.method != "GET":
                    if request.headers.get("Origin") != origin:
                        raise web.HTTPForbidden(
                            text="Please sign in through the MHM website."
                        )
                    if request.content_type != "application/json":
                        raise web.HTTPUnsupportedMediaType(
                            text="A JSON request is required."
                        )
                # Trust the client address only after authenticating the Worker.
                client = (
                    request.headers.get("X-MHM-Client-IP", "unknown")
                    if proxy_secret
                    else request.remote
                )
                throttle(("ip", client), 60, 600)
            response = await handler(request)
        except web.HTTPException as exc:
            response = web.json_response({"error": exc.text}, status=exc.status)
        except Exception:
            logger.error("Website account request failed")
            response = web.json_response(
                {"error": "MHM could not complete this request. Please try again."},
                status=503,
            )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    # ERROR_HANDLING_EXCLUDE: Request parsing is protected by the gateway middleware.
    async def body(request):
        """Parse a request body as a JSON object or return a safe HTTP error."""
        try:
            data = await request.json()
        except (ValueError, UnicodeDecodeError):
            raise web.HTTPBadRequest(
                text="Please check the form and try again."
            ) from None
        if not isinstance(data, dict):
            raise web.HTTPBadRequest(text="Please check the form and try again.")
        return data

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def request_code(request):
        """Validate a login or signup request and send an eligible email code."""
        data = await body(request)
        email = data.get("email")
        mode = data.get("mode")
        if (
            not isinstance(email, str)
            or len(email) > 254
            or not re.fullmatch(
                r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", email.strip()
            )
        ):
            raise web.HTTPBadRequest(text="Enter a valid email address.")
        email = email.strip().casefold()
        if mode not in {"login", "create"}:
            raise web.HTTPBadRequest(text="Choose log in or create account.")
        username = data.get("username", "")
        timezone = data.get("timezone", "America/Regina")
        if mode == "create":
            if not isinstance(username, str) or not re.fullmatch(
                r"[A-Za-z0-9_-]{3,32}", username
            ):
                raise web.HTTPBadRequest(
                    text="Choose a username with 3–32 letters, numbers, underscores, or hyphens."
                )
            try:
                ZoneInfo(timezone)
            except (ZoneInfoNotFoundError, ValueError, TypeError):
                raise web.HTTPBadRequest(
                    text="Your time zone could not be recognized."
                ) from None
        else:
            username, timezone = "", "America/Regina"
        throttle(("email", email), 3, 600)
        if len(challenges) >= 10000:
            raise web.HTTPTooManyRequests(text="MHM is busy. Please try again later.")
        if not test_mailer and not all(
            [
                config.EMAIL_SMTP_SERVER,
                config.EMAIL_SMTP_USERNAME,
                config.EMAIL_SMTP_PASSWORD,
            ]
        ):
            raise web.HTTPServiceUnavailable(
                text="Email sign-in is not available yet. Please try again later."
            )
        existing = await asyncio.to_thread(accounts.by_email, email)
        eligible = (
            bool(existing and existing[1].get("account_status") == "active")
            if mode == "login"
            else not await asyncio.to_thread(accounts.email_exists, email)
        )
        code = f"{secrets.randbelow(1000000):06d}"
        token = secrets.token_urlsafe(32)
        if eligible:
            try:
                await asyncio.to_thread(mailer, email, code)
            except (CommunicationError, smtplib.SMTPException, OSError) as exc:
                logger.error(f"Website verification email failed: {type(exc).__name__}")
                raise web.HTTPServiceUnavailable(
                    text="We couldn't send your code. Please ask your MHM administrator to check email delivery."
                ) from None
            logger.info("Website verification email accepted by the mail sender")
        elif mode == "login":
            logger.info(
                "Website sign-in email skipped: no unique active account matched"
            )
        challenges[token] = Challenge(
            hashlib.sha256(code.encode()).hexdigest(),
            clock() + CODE_TTL,
            email,
            mode,
            username,
            timezone,
            existing[0] if existing else None,
            eligible,
        )
        return web.json_response({"challenge": token})

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def verify(request):
        """Verify a one-time code, create accounts when requested, and start a session."""
        data = await body(request)
        token, code = data.get("challenge"), data.get("code")
        if (
            not isinstance(token, str)
            or not isinstance(code, str)
            or not re.fullmatch(r"\d{6}", code)
        ):
            raise web.HTTPBadRequest(text="Enter the 6-digit code from your email.")
        async with verification_lock:
            challenge = challenges.get(token)
            if not challenge or challenge.expires <= clock() or challenge.attempts >= 5:
                challenges.pop(token, None)
                raise web.HTTPUnauthorized(
                    text="This code has expired. Please request a new one."
                )
            challenge.attempts += 1
            if not challenge.eligible or not secrets.compare_digest(
                challenge.digest, hashlib.sha256(code.encode()).hexdigest()
            ):
                raise web.HTTPUnauthorized(
                    text="That code did not work. Check it or request a new code. Existing users should choose Log in."
                )
            uid = challenge.user_id
            if challenge.mode == "create":
                if await asyncio.to_thread(accounts.email_exists, challenge.email):
                    del challenges[token]
                    raise web.HTTPConflict(
                        text="An account already uses this email. Please log in."
                    )
                if await asyncio.to_thread(
                    accounts.username_exists, challenge.username
                ):
                    del challenges[token]
                    raise web.HTTPConflict(
                        text="That username is taken. Please choose another username."
                    )
                uid = await asyncio.to_thread(
                    accounts.create,
                    challenge.email,
                    challenge.username,
                    challenge.timezone,
                )
                if not uid:
                    raise web.HTTPServiceUnavailable(
                        text="Your account could not be created. Please try again."
                    )
            account = await asyncio.to_thread(accounts.get, uid)
            if (
                account.get("account_status") != "active"
                or account.get("email", "").casefold() != challenge.email
            ):
                del challenges[token]
                raise web.HTTPUnauthorized(
                    text="This account cannot sign in. Please contact your MHM administrator."
                )
            del challenges[token]
            session = secrets.token_urlsafe(32)
            if len(sessions) >= 10000:
                raise web.HTTPServiceUnavailable(
                    text="MHM is busy. Please try again later."
                )
            sessions[hashlib.sha256(session.encode()).hexdigest()] = (
                uid,
                clock() + SESSION_TTL,
                challenge.email,
            )
        response = web.json_response({"ok": True})
        response.set_cookie(
            COOKIE,
            session,
            httponly=True,
            secure=not local,
            # Discord returns through a top-level cross-site GET. POST requests
            # remain protected by exact Origin and JSON checks in guard().
            samesite="Lax",
            max_age=SESSION_TTL,
            path="/api/",
        )
        return response

    # ERROR_HANDLING_EXCLUDE: Authentication failures are HTTP responses by design.
    async def authenticated_account(request):
        """Resolve an active account from the request session cookie."""
        key = hashlib.sha256(request.cookies.get(COOKIE, "").encode()).hexdigest()
        session = sessions.get(key)
        if not session or session[1] <= clock():
            raise web.HTTPUnauthorized(text="Please log in to continue.")
        current = await asyncio.to_thread(accounts.get, session[0])
        if (
            current.get("account_status") != "active"
            or current.get("email", "").casefold() != session[2]
        ):
            sessions.pop(key, None)
            raise web.HTTPUnauthorized(text="Please log in to continue.")
        return session[0], current

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def account(request):
        """Return the signed-in account summary used by website pages."""
        _, current = await authenticated_account(request)
        app_id = str(config.DISCORD_APPLICATION_ID or "")
        return web.json_response(
            {
                "username": current.get("internal_username", ""),
                "email": current.get("email", ""),
                "timezone": current.get("timezone", ""),
                "discord_linked": bool(current.get("discord_user_id")),
                "discord_available": discord_available(),
                "discord_url": (
                    f"https://discord.com/users/{app_id}" if app_id.isdigit() else None
                ),
            }
        )

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def discord_start(request):
        """Create a short-lived Discord OAuth state and authorization URL."""
        await authenticated_account(request)
        if not discord_available():
            raise web.HTTPServiceUnavailable(
                text="Discord connection is not configured yet. Please ask your MHM administrator."
            )
        if len(discord_states) >= 10000:
            raise web.HTTPTooManyRequests(text="MHM is busy. Please try again later.")
        state = secrets.token_urlsafe(32)
        discord_states[hashlib.sha256(state.encode()).hexdigest()] = (
            hashlib.sha256(request.cookies.get(COOKIE, "").encode()).hexdigest(),
            clock() + DISCORD_STATE_TTL,
        )
        query = urlencode(
            {
                "client_id": str(config.DISCORD_APPLICATION_ID),
                "response_type": "code",
                "redirect_uri": discord_redirect_uri(),
                "scope": "identify",
                "state": state,
                "prompt": "consent",
            }
        )
        return web.json_response({"url": f"{DISCORD_AUTHORIZE_URL}?{query}"})

    # ERROR_HANDLING_EXCLUDE: OAuth callback intentionally maps all failures to safe redirects.
    async def discord_callback(request):
        """Validate the Discord callback and link the identity to the active account."""
        error = request.query.get("error")
        state = request.query.get("state", "")
        state_key = hashlib.sha256(state.encode()).hexdigest()
        pending = discord_states.pop(state_key, None)
        if error or not pending or pending[1] <= clock():
            return web.HTTPFound(website_redirect("/app.html", discord="cancelled"))
        if not discord_available():
            return web.HTTPFound(website_redirect("/app.html", discord="unavailable"))
        code = request.query.get("code", "")
        if not code or len(code) > 2048:
            return web.HTTPFound(website_redirect("/app.html", discord="error"))
        try:
            uid, _ = await authenticated_account(request)
            session_key = hashlib.sha256(
                request.cookies.get(COOKIE, "").encode()
            ).hexdigest()
            if not secrets.compare_digest(session_key, pending[0]):
                raise web.HTTPUnauthorized(text="Please log in to continue.")
            discord_user_id, discord_username = await discord_identity(
                code,
                client_id=config.DISCORD_APPLICATION_ID,
                client_secret=config.DISCORD_CLIENT_SECRET,
                redirect_uri=discord_redirect_uri(),
            )
            async with discord_link_lock:
                # Logout, expiry, or suspension during Discord's network request
                # must prevent the subsequent account write.
                await authenticated_account(request)
                result = await asyncio.to_thread(
                    accounts.link_discord, uid, discord_user_id, discord_username
                )
            if result == "already_linked":
                return web.HTTPFound(website_redirect("/app.html", discord="in-use"))
            if result == "different_linked":
                return web.HTTPFound(
                    website_redirect("/app.html", discord="account-linked")
                )
            if result != "linked":
                raise DataError("Discord account could not be linked")
        except web.HTTPUnauthorized:
            return web.HTTPFound(website_redirect("/login.html", discord="expired"))
        except Exception:
            logger.error("Website Discord connection failed")
            return web.HTTPFound(website_redirect("/app.html", discord="error"))
        return web.HTTPFound(website_redirect("/app.html", discord="connected"))

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def settings(request):
        """Read or atomically save one allowlisted self-service settings section."""
        from core.web_user_settings import settings_snapshot, build_settings_updates

        uid, _ = await authenticated_account(request)
        async with settings_lock:
            documents = await asyncio.to_thread(accounts.documents, uid)
            options = await asyncio.to_thread(accounts.settings_options, uid)
            snapshot = settings_snapshot(documents, options)
            if request.method == "GET":
                return web.json_response(snapshot)
            data = await body(request)
            section = data.get("section")
            if (
                set(data) != {"section", "values", "revision"}
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
            if not await asyncio.to_thread(accounts.save_settings, uid, updates):
                raise web.HTTPServiceUnavailable(
                    text="MHM could not finish saving. Reload these settings to check their current values before trying again."
                )
            latest = await asyncio.to_thread(accounts.documents, uid)
            return web.json_response(settings_snapshot(latest, options))

    # ERROR_HANDLING_EXCLUDE: Pure serializer is called only by the guarded task route.
    def task_view(task):
        """Return the stable, browser-safe task shape used by the website."""
        due = task.get("due") if isinstance(task.get("due"), dict) else {}
        recurrence = task.get("recurrence") if isinstance(task.get("recurrence"), dict) else {}
        completion = task.get("completion") if isinstance(task.get("completion"), dict) else {}
        reminders = []
        for reminder in task.get("reminders") if isinstance(task.get("reminders"), list) else []:
            period = reminder.get("period") if isinstance(reminder, dict) else None
            if (
                isinstance(period, dict)
                and reminder.get("kind") == "scheduled"
                and all(isinstance(period.get(key), str) for key in ("date", "start_time", "end_time"))
            ):
                reminders.append({
                    "kind": "scheduled",
                    "period": {
                        "date": period.get("date"),
                        "start_time": period.get("start_time"),
                        "end_time": period.get("end_time"),
                    },
                })
        return {
            "id": str(task.get("id") or ""),
            "short_id": str(task.get("short_id") or ""),
            "title": str(task.get("title") or ""),
            "description": str(task.get("description") or ""),
            "priority": str(task.get("priority") or "medium"),
            "status": str(task.get("status") or "active"),
            "due_date": due.get("date"),
            "due_time": due.get("time"),
            "recurrence": {
                "pattern": recurrence.get("pattern"),
                "interval": recurrence.get("interval", 1),
                "repeat_after_completion": recurrence.get("repeat_after_completion", True),
                "next_due_date": recurrence.get("next_due_date"),
            },
            "reminders": reminders,
            "completion": {
                "completed": bool(completion.get("completed")),
                "completed_at": completion.get("completed_at"),
                "notes": str(completion.get("notes") or ""),
            },
            "tags": task.get("tags") if isinstance(task.get("tags"), list) else [],
            "links": task.get("links") if isinstance(task.get("links"), list) else [],
            "created_at": task.get("created_at"),
            "updated_at": task.get("updated_at"),
        }

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def tasks_api(request):
        """Authenticated website CRUD facade over the canonical MHM task service."""
        uid, _ = await authenticated_account(request)
        from core.time_utilities import parse_date_only, parse_time_only_minute
        from tasks.task_service import (
            complete_task,
            create_task,
            delete_task,
            load_active_tasks,
            load_completed_tasks,
            restore_task,
            update_task,
        )
        from tasks.task_data_manager import get_task_by_id
        task_id = request.match_info.get("task_id")
        action = request.match_info.get("action")

        # ERROR_HANDLING_EXCLUDE: Lookup helper raises an intentional HTTP response.
        def find(identifier):
            """Resolve a task identifier or raise the route's not-found response."""
            task = get_task_by_id(uid, identifier)
            if not task:
                raise web.HTTPNotFound(text="That task could not be found.")
            return task

        # ERROR_HANDLING_EXCLUDE: Validation helper raises intentional HTTP responses.
        def clean_reminder_periods(value):
            """Validate and normalize scheduled reminder periods from the browser."""
            if value is None:
                return []
            if not isinstance(value, list) or len(value) > 20:
                raise web.HTTPBadRequest(text="Add at most 20 scheduled reminders.")
            cleaned = []
            for period in value:
                if not isinstance(period, dict) or set(period) != {"date", "start_time", "end_time"}:
                    raise web.HTTPBadRequest(text="Each reminder needs a date, start time, and end time.")
                date = period["date"]
                start = period["start_time"]
                end = period["end_time"]
                if (
                    not isinstance(date, str) or parse_date_only(date) is None
                    or not isinstance(start, str) or parse_time_only_minute(start) is None
                    or not isinstance(end, str) or parse_time_only_minute(end) is None
                    or start >= end
                ):
                    raise web.HTTPBadRequest(text="Reminder dates and times must be valid, with the start before the end.")
                cleaned.append({"date": date, "start_time": start, "end_time": end})
            return cleaned

        if request.method == "GET":
            status = request.query.get("status", "active")
            if status not in {"active", "completed", "all"}:
                raise web.HTTPBadRequest(text="Choose active, completed, or all tasks.")
            active = await asyncio.to_thread(load_active_tasks, uid)
            completed = await asyncio.to_thread(load_completed_tasks, uid)
            selected = active if status == "active" else completed if status == "completed" else active + completed
            return web.json_response({
                "tasks": [task_view(task) for task in selected],
                "active_count": len(active),
                "completed_count": len(completed),
            })

        if request.method == "POST" and not task_id:
            data = await body(request)
            allowed = {
                "title", "description", "due_date", "due_time", "priority",
                "recurrence_pattern", "recurrence_interval", "repeat_after_completion",
                "tags", "reminder_periods",
            }
            if set(data) - allowed:
                raise web.HTTPBadRequest(text="Please submit only supported task fields.")
            title = data.get("title")
            if not isinstance(title, str) or not title.strip():
                raise web.HTTPBadRequest(text="Give your task a title.")
            description = data.get("description", "")
            if not isinstance(description, str) or len(description) > 10000:
                raise web.HTTPBadRequest(text="Task descriptions must be 10,000 characters or fewer.")
            tags = data.get("tags", [])
            if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
                raise web.HTTPBadRequest(text="Tags must be a list of words.")
            from tasks.task_tag_helpers import sanitize_task_tags
            tags = sanitize_task_tags(tags)
            reminder_periods = clean_reminder_periods(data.get("reminder_periods", []))
            due_date = data.get("due_date")
            if due_date == "":
                due_date = None
            if due_date is not None and (not isinstance(due_date, str) or parse_date_only(due_date) is None):
                raise web.HTTPBadRequest(text="Due dates must use YYYY-MM-DD.")
            due_time = data.get("due_time")
            if due_time == "":
                due_time = None
            if due_time is not None and (not isinstance(due_time, str) or parse_time_only_minute(due_time) is None):
                raise web.HTTPBadRequest(text="Due times must use HH:MM.")
            priority = data.get("priority", "medium")
            from tasks.task_schemas import VALID_PRIORITIES
            if not isinstance(priority, str) or priority.lower() not in VALID_PRIORITIES:
                raise web.HTTPBadRequest(text="Choose a valid priority.")
            pattern = data.get("recurrence_pattern") or None
            if pattern is not None and pattern not in {"daily", "weekly", "monthly", "yearly"}:
                raise web.HTTPBadRequest(text="Choose a valid repeat pattern.")
            interval = data.get("recurrence_interval", 1)
            if type(interval) is not int or not 1 <= interval <= 365:
                raise web.HTTPBadRequest(text="Repeat intervals must be between 1 and 365.")
            repeat_after = data.get("repeat_after_completion", True)
            if type(repeat_after) is not bool:
                raise web.HTTPBadRequest(text="Choose whether repeats count from completion.")
            created_id = await asyncio.to_thread(
                create_task,
                uid,
                title=title.strip(), description=description,
                due_date=due_date, due_time=due_time, priority=priority.lower(),
                recurrence_pattern=pattern, recurrence_interval=interval,
                repeat_after_completion=repeat_after,
                tags=tags, reminder_periods=reminder_periods,
            )
            if not created_id:
                raise web.HTTPServiceUnavailable(text="MHM could not create that task. Please try again.")
            return web.json_response({"task": task_view(find(created_id))}, status=201)

        if not task_id:
            raise web.HTTPBadRequest(text="A task ID is required.")
        if action == "complete" and request.method == "POST":
            if not await asyncio.to_thread(complete_task, uid, task_id):
                raise web.HTTPNotFound(text="That active task could not be completed.")
        elif action == "restore" and request.method == "POST":
            if not await asyncio.to_thread(restore_task, uid, task_id):
                raise web.HTTPNotFound(text="That completed task could not be restored.")
        elif action is None and request.method == "PATCH":
            data = await body(request)
            allowed = {"title", "description", "due_date", "due_time", "priority", "recurrence_pattern", "recurrence_interval", "repeat_after_completion", "tags", "reminder_periods"}
            if not data or set(data) - allowed:
                raise web.HTTPBadRequest(text="Please submit supported task changes.")
            if "title" in data and (not isinstance(data["title"], str) or not data["title"].strip()):
                raise web.HTTPBadRequest(text="Give your task a title.")
            if "description" in data and (not isinstance(data["description"], str) or len(data["description"]) > 10000):
                raise web.HTTPBadRequest(text="Task descriptions must be 10,000 characters or fewer.")
            if "tags" in data:
                if not isinstance(data["tags"], list) or any(not isinstance(tag, str) for tag in data["tags"]):
                    raise web.HTTPBadRequest(text="Tags must be a list of words.")
                from tasks.task_tag_helpers import sanitize_task_tags
                data["tags"] = sanitize_task_tags(data["tags"])
            if "reminder_periods" in data:
                data["reminder_periods"] = clean_reminder_periods(data["reminder_periods"])
            for key, parser, message in (("due_date", parse_date_only, "Due dates must use YYYY-MM-DD."), ("due_time", parse_time_only_minute, "Due times must use HH:MM.")):
                if key in data and data[key] not in (None, "") and (not isinstance(data[key], str) or parser(data[key]) is None):
                    raise web.HTTPBadRequest(text=message)
            if "priority" in data:
                from tasks.task_schemas import VALID_PRIORITIES
                if not isinstance(data["priority"], str) or data["priority"].lower() not in VALID_PRIORITIES:
                    raise web.HTTPBadRequest(text="Choose a valid priority.")
                data["priority"] = data["priority"].lower()
            if "recurrence_pattern" in data and data["recurrence_pattern"] not in (None, "", "daily", "weekly", "monthly", "yearly"):
                raise web.HTTPBadRequest(text="Choose a valid repeat pattern.")
            if "recurrence_interval" in data and (type(data["recurrence_interval"]) is not int or not 1 <= data["recurrence_interval"] <= 365):
                raise web.HTTPBadRequest(text="Repeat intervals must be between 1 and 365.")
            if "repeat_after_completion" in data and type(data["repeat_after_completion"]) is not bool:
                raise web.HTTPBadRequest(text="Choose whether repeats count from completion.")
            if not await asyncio.to_thread(update_task, uid, task_id, data):
                raise web.HTTPNotFound(text="That active task could not be updated.")
        elif action is None and request.method == "DELETE":
            if not await asyncio.to_thread(delete_task, uid, task_id):
                raise web.HTTPNotFound(text="That task could not be deleted.")
            return web.json_response({"ok": True})
        else:
            raise web.HTTPMethodNotAllowed(request.method, {"GET", "POST", "PATCH", "DELETE"})
        return web.json_response({"task": task_view(find(task_id))})

    # ERROR_HANDLING_EXCLUDE: Pure serializer is called only by the guarded notebook route.
    def note_view(entry):
        """Return the stable, browser-safe representation of a notebook entry."""
        items = []
        for item in getattr(entry, "items", None) or []:
            items.append({
                "id": str(item.id),
                "text": str(item.text),
                "done": bool(item.done),
                "order": int(item.order),
            })
        return {
            "id": str(entry.id),
            "short_id": str(entry.short_id or ""),
            "kind": str(entry.kind),
            "title": str(entry.title or ""),
            "description": str(entry.description or ""),
            "items": items,
            "tags": [str(tag) for tag in (entry.tags or [])],
            "group": str(entry.group or ""),
            "pinned": bool(entry.pinned),
            "status": str(entry.status),
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
            "submitted_at": getattr(entry, "submitted_at", None),
        }

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def notes_api(request):
        """Authenticated website facade over the canonical notebook service."""
        uid, _ = await authenticated_account(request)
        from notebook import notebook_data_manager as notes
        from core.tags import normalize_tags

        note_id = request.match_info.get("note_id")
        action = request.match_info.get("action")

        # ERROR_HANDLING_EXCLUDE: Lookup helper raises an intentional HTTP response.
        def find(identifier, include_archived=True):
            """Resolve a notebook entry identifier or raise a not-found response."""
            entries = notes.list_recent(uid, n=1000, include_archived=include_archived)
            for entry in entries:
                if str(entry.id) == identifier or str(entry.short_id or "").casefold() == identifier.casefold():
                    return entry
            raise web.HTTPNotFound(text="That note could not be found.")

        # ERROR_HANDLING_EXCLUDE: Validation helper raises intentional HTTP responses.
        def clean_list_items(value):
            """Validate and normalize list item edits from the browser."""
            if not isinstance(value, list) or not 1 <= len(value) <= 50:
                raise web.HTTPBadRequest(text="Lists need between 1 and 50 items.")
            cleaned = []
            for item in value:
                if (
                    not isinstance(item, dict)
                    or set(item) != {"text", "done"}
                    or not isinstance(item["text"], str)
                    or not item["text"].strip()
                    or len(item["text"]) > 500
                    or type(item["done"]) is not bool
                ):
                    raise web.HTTPBadRequest(text="Each list item needs text and a valid completion state.")
                cleaned.append({"text": item["text"].strip(), "done": item["done"]})
            return cleaned

        if request.method == "GET":
            status = request.query.get("status", "active")
            if status not in {"active", "archived", "all"}:
                raise web.HTTPBadRequest(text="Choose active, archived, or all notes.")
            query = request.query.get("q", "").strip()
            if query:
                entries = notes.search_entries(uid, query, limit=100)
            else:
                entries = notes.list_recent(uid, n=100, include_archived=status != "active")
            entries = [entry for entry in entries if status == "all" or entry.status == status]
            return web.json_response({"notes": [note_view(entry) for entry in entries], "count": len(entries)})

        if request.method == "POST" and not note_id:
            data = await body(request)
            allowed = {"kind", "title", "description", "items", "tags", "group"}
            if set(data) - allowed:
                raise web.HTTPBadRequest(text="Please submit only supported note fields.")
            kind = data.get("kind", "note")
            if kind not in {"note", "journal_entry", "list"}:
                raise web.HTTPBadRequest(text="Choose note, journal, or list.")
            title = data.get("title")
            description = data.get("description", "")
            if not isinstance(title, str) or not title.strip():
                raise web.HTTPBadRequest(text="Give your entry a title.")
            if len(title.strip()) > 200:
                raise web.HTTPBadRequest(text="Entry titles must be 200 characters or fewer.")
            if not isinstance(description, str) or len(description) > 10000:
                raise web.HTTPBadRequest(text="Entry text must be 10,000 characters or fewer.")
            tags = data.get("tags", [])
            if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
                raise web.HTTPBadRequest(text="Tags must be a list of words.")
            tags = normalize_tags(tags)
            group = data.get("group")
            if group is not None and (not isinstance(group, str) or len(group.strip()) > 50):
                raise web.HTTPBadRequest(text="Note groups must be text.")
            if kind == "list":
                items = clean_list_items(data.get("items"))
                entry = await asyncio.to_thread(notes.create_list, uid, title=title.strip(), items=[item["text"] for item in items], tags=tags, group=group)
                if entry and any(item["done"] for item in items):
                    entry = await asyncio.to_thread(notes.set_list_items, uid, str(entry.id), items)
            elif kind == "journal_entry":
                entry = await asyncio.to_thread(notes.create_journal, uid, title=title.strip(), description=description, tags=tags, group=group)
            else:
                entry = await asyncio.to_thread(notes.create_note, uid, title=title.strip(), description=description, tags=tags, group=group)
            if not entry:
                raise web.HTTPBadRequest(text="MHM could not create that entry.")
            return web.json_response({"note": note_view(entry)}, status=201)

        if not note_id:
            raise web.HTTPBadRequest(text="A note ID is required.")
        if action in {"archive", "restore"} and request.method == "POST":
            entry = find(note_id, include_archived=True)
            if not await asyncio.to_thread(notes.archive_entry, uid, note_id, action == "archive"):
                raise web.HTTPNotFound(text="That note could not be updated.")
            return web.json_response({"note": note_view(find(note_id, include_archived=True))})
        if action is None and request.method == "PATCH":
            data = await body(request)
            allowed = {"title", "description", "items", "tags", "group", "pinned"}
            if not data or set(data) - allowed:
                raise web.HTTPBadRequest(text="Please submit supported note changes.")
            if "title" in data and (not isinstance(data["title"], str) or not data["title"].strip() or len(data["title"].strip()) > 200):
                raise web.HTTPBadRequest(text="Entry titles must be between 1 and 200 characters.")
            if "description" in data and (not isinstance(data["description"], str) or len(data["description"]) > 10000):
                raise web.HTTPBadRequest(text="Entry text must be 10,000 characters or fewer.")
            if "tags" in data and (not isinstance(data["tags"], list) or any(not isinstance(tag, str) for tag in data["tags"])):
                raise web.HTTPBadRequest(text="Tags must be a list of words.")
            if "tags" in data:
                data["tags"] = normalize_tags(data["tags"])
            if "group" in data and data["group"] is not None and (not isinstance(data["group"], str) or len(data["group"].strip()) > 50):
                raise web.HTTPBadRequest(text="Note groups must be text.")
            current_entry = find(note_id, include_archived=False)
            if "items" in data:
                data["items"] = clean_list_items(data["items"])
                if current_entry.kind != "list":
                    raise web.HTTPBadRequest(text="Only list entries can have list items.")
            if "description" in data and current_entry.kind == "list":
                raise web.HTTPBadRequest(text="List entries are edited through their list items.")
            if "title" in data and not await asyncio.to_thread(notes.set_entry_title, uid, note_id, data["title"]):
                raise web.HTTPNotFound(text="That entry could not be updated.")
            if "description" in data and not await asyncio.to_thread(notes.set_entry_body, uid, note_id, data["description"]):
                raise web.HTTPNotFound(text="That note could not be updated.")
            if "items" in data and not await asyncio.to_thread(notes.set_list_items, uid, note_id, data["items"]):
                raise web.HTTPNotFound(text="That list could not be updated.")
            if "tags" in data:
                current = find(note_id, include_archived=False)
                await asyncio.to_thread(notes.remove_tags, uid, note_id, list(current.tags))
                if data["tags"] and not await asyncio.to_thread(notes.add_tags, uid, note_id, data["tags"]):
                    raise web.HTTPNotFound(text="That note could not be updated.")
            if "group" in data and not await asyncio.to_thread(notes.set_group, uid, note_id, data["group"]):
                raise web.HTTPNotFound(text="That note could not be updated.")
            if "pinned" in data and type(data["pinned"]) is not bool:
                raise web.HTTPBadRequest(text="Choose whether the entry is pinned.")
            if "pinned" in data and not await asyncio.to_thread(notes.pin_entry, uid, note_id, data["pinned"]):
                raise web.HTTPNotFound(text="That note could not be updated.")
            return web.json_response({"note": note_view(find(note_id, include_archived=False))})
        raise web.HTTPMethodNotAllowed(request.method, {"GET", "POST", "PATCH"})

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def logout(request):
        """Revoke the current session cookie and clear it from the browser."""
        sessions.pop(
            hashlib.sha256(request.cookies.get(COOKIE, "").encode()).hexdigest(), None
        )
        response = web.json_response({"ok": True})
        response.del_cookie(COOKIE, path="/api/")
        return response

    app = web.Application(middlewares=[guard], client_max_size=32768)
    app.router.add_post("/api/auth/request-code", request_code)
    app.router.add_post("/api/auth/verify", verify)
    app.router.add_post("/api/auth/logout", logout)
    app.router.add_get("/api/auth/discord/start", discord_start)
    app.router.add_get("/api/auth/discord/callback", discord_callback)
    app.router.add_get("/api/account", account)
    app.router.add_get("/api/settings", settings)
    app.router.add_post("/api/settings", settings)
    app.router.add_get("/api/tasks", tasks_api)
    app.router.add_post("/api/tasks", tasks_api)
    app.router.add_route("PATCH", "/api/tasks/{task_id}", tasks_api)
    app.router.add_route("DELETE", "/api/tasks/{task_id}", tasks_api)
    app.router.add_post("/api/tasks/{task_id}/{action:complete|restore}", tasks_api)
    app.router.add_get("/api/notes", notes_api)
    app.router.add_post("/api/notes", notes_api)
    app.router.add_route("PATCH", "/api/notes/{note_id}", notes_api)
    app.router.add_post("/api/notes/{note_id}/{action:archive|restore}", notes_api)
    root = Path(__file__).resolve().parent.parent / "website"

    # Explicit allowlist keeps configs, Worker source, and docs off the local server.
    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def asset(request):
        """Serve one explicitly allowlisted website asset from the local gateway."""
        name = request.match_info.get("name", "index.html")
        if name not in {
            "index.html",
            "login.html",
            "app.html",
            "tasks.html",
            "notes.html",
            "styles.css",
            "mhm-logo.png",
            "script.js",
            "auth.js",
            "app.js",
            "settings.js",
            "tasks.js",
            "notes.js",
        }:
            raise web.HTTPNotFound(text="Page not found.")
        return web.FileResponse(root / name)

    app.router.add_get("/", asset)
    app.router.add_get("/{name}", asset)
    return app
