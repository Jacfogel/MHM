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
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiohttp import web

from core import config
from core.logger import get_component_logger

logger = get_component_logger("main")
COOKIE = "mhm_session"
CODE_TTL = 600
SESSION_TTL = 12 * 60 * 60


class MHMAccounts:
    """Use product persistence; never maintain a separate website account database."""

    def all(self):
        from core import get_all_user_ids, get_user_data

        return [
            (uid, get_user_data(uid, "account").get("account") or {})
            for uid in get_all_user_ids()
        ]

    def by_email(self, email):
        matches = [
            (uid, account)
            for uid, account in self.all()
            if account.get("email", "").strip().casefold() == email.casefold()
        ]
        # Email addresses must identify exactly one account.
        return matches[0] if len(matches) == 1 else None

    def email_exists(self, email):
        return any(
            account.get("email", "").casefold() == email.casefold()
            for _, account in self.all()
        )

    def username_exists(self, username):
        return any(
            account.get("internal_username", "").casefold() == username.casefold()
            for _, account in self.all()
        )

    def get(self, uid):
        from core import get_user_data

        return get_user_data(uid, "account").get("account") or {}

    def documents(self, uid):
        from core import get_user_data

        return get_user_data(uid, ["account", "preferences", "context", "schedules"])

    def settings_options(self, uid):
        from core.web_user_settings import settings_options

        return settings_options(uid)

    def save_settings(self, uid, updates):
        from core.web_user_settings import save_settings

        return save_settings(uid, updates)

    def create(self, email, username, timezone):
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
    message = EmailMessage()
    message["From"] = config.EMAIL_SMTP_USERNAME
    message["To"] = email
    message["Subject"] = "Your MHM sign-in code"
    message.set_content(
        f"Your MHM code is: {code}\n\nIt expires in 10 minutes.\nIf you did not request this, ignore this email."
    )
    with smtplib.SMTP_SSL(
        config.EMAIL_SMTP_SERVER, 465, timeout=10, context=ssl.create_default_context()
    ) as smtp:
        smtp.login(config.EMAIL_SMTP_USERNAME, config.EMAIL_SMTP_PASSWORD)
        smtp.send_message(message)


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


def create_web_app(
    *, accounts=None, mailer=None, origin=None, proxy_secret=None, clock=time.monotonic
):
    """Construct an injectable gateway; tests use isolated account and email adapters."""
    accounts = accounts or MHMAccounts()
    test_mailer = mailer is not None
    mailer = mailer or send_code
    origin = origin or config.WEB_PUBLIC_ORIGIN
    proxy_secret = config.WEB_PROXY_SECRET if proxy_secret is None else proxy_secret
    parsed = urlsplit(origin)
    local = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}
    if (
        parsed.path
        or parsed.query
        or parsed.fragment
        or not parsed.netloc
        or parsed.username
        or parsed.password
    ):
        raise ValueError("WEB_PUBLIC_ORIGIN must be an exact origin without a path")
    if not local and (parsed.scheme != "https" or len(proxy_secret) < 32):
        raise ValueError(
            "Production web access requires HTTPS and a WEB_PROXY_SECRET of at least 32 characters"
        )
    challenges = {}
    sessions = {}
    limits = {}
    verification_lock = asyncio.Lock()
    settings_lock = asyncio.Lock()

    def prune():
        now = clock()
        for key in [key for key, value in challenges.items() if value.expires <= now]:
            del challenges[key]
        for key in [key for key, value in sessions.items() if value[1] <= now]:
            del sessions[key]
        for key in [key for key, value in limits.items() if value[1] <= now]:
            del limits[key]

    def throttle(key, maximum, window):
        count, expires = limits.get(key, (0, clock() + window))
        if count >= maximum:
            raise web.HTTPTooManyRequests(
                text="Too many attempts. Please wait before trying again."
            )
        if len(limits) >= 10000 and key not in limits:
            raise web.HTTPTooManyRequests(text="MHM is busy. Please try again later.")
        limits[key] = (count + 1, expires)

    @web.middleware
    async def guard(request, handler):
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

    async def body(request):
        try:
            data = await request.json()
        except (ValueError, UnicodeDecodeError):
            raise web.HTTPBadRequest(
                text="Please check the form and try again."
            ) from None
        if not isinstance(data, dict):
            raise web.HTTPBadRequest(text="Please check the form and try again.")
        return data

    async def request_code(request):
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
            except (smtplib.SMTPException, OSError) as exc:
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

    async def verify(request):
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
            samesite="Strict",
            max_age=SESSION_TTL,
            path="/api/",
        )
        return response

    async def authenticated_account(request):
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

    async def account(request):
        _, current = await authenticated_account(request)
        app_id = str(config.DISCORD_APPLICATION_ID or "")
        return web.json_response(
            {
                "username": current.get("internal_username", ""),
                "email": current.get("email", ""),
                "timezone": current.get("timezone", ""),
                "discord_linked": bool(current.get("discord_user_id")),
                "discord_url": (
                    f"https://discord.com/users/{app_id}" if app_id.isdigit() else None
                ),
            }
        )

    async def settings(request):
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
            except ValueError as exc:
                raise web.HTTPBadRequest(text=str(exc)) from None
            if not await asyncio.to_thread(accounts.save_settings, uid, updates):
                raise web.HTTPServiceUnavailable(
                    text="MHM could not finish saving. Reload these settings to check their current values before trying again."
                )
            latest = await asyncio.to_thread(accounts.documents, uid)
            return web.json_response(settings_snapshot(latest, options))

    async def logout(request):
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
    app.router.add_get("/api/account", account)
    app.router.add_get("/api/settings", settings)
    app.router.add_post("/api/settings", settings)
    root = Path(__file__).resolve().parent.parent / "website"

    # Explicit allowlist keeps configs, Worker source, and docs off the local server.
    async def asset(request):
        name = request.match_info.get("name", "index.html")
        if name not in {
            "index.html",
            "login.html",
            "app.html",
            "styles.css",
            "script.js",
            "auth.js",
            "app.js",
            "settings.js",
        }:
            raise web.HTTPNotFound(text="Page not found.")
        return web.FileResponse(root / name)

    app.router.add_get("/", asset)
    app.router.add_get("/{name}", asset)
    return app
