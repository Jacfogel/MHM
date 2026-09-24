"""Email-verified browser access to the existing MHM account store.

Run one gateway process beside MHM. Challenges and sessions are intentionally
ephemeral: restarting the gateway signs browsers out, without changing accounts.
"""

import asyncio
import base64
import hashlib
import json
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
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"  # nosec B105
DISCORD_USER_URL = "https://discord.com/api/users/@me"
PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
OAUTH_STATE_TTL = 600
OAUTH_PROVIDERS = ("google", "facebook")
OAUTH_AUTHORIZE_URLS = {
    "google": "https://accounts.google.com/o/oauth2/v2/auth",
    "facebook": "https://www.facebook.com/dialog/oauth",
}
OAUTH_TOKEN_URLS = {
    "google": "https://oauth2.googleapis.com/token",
    "facebook": "https://graph.facebook.com/oauth/access_token",
}


# ERROR_HANDLING_EXCLUDE: Pure bounded crypto helper; callers own user-facing errors.
def _password_hash(password: str, *, salt: bytes | None = None) -> str:
    """Hash a password with scrypt and a per-password random salt."""
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=32,
    )
    encoded_salt = base64.urlsafe_b64encode(salt).decode().rstrip("=")
    encoded_digest = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return (
        f"$mhm$scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}"
        f"${encoded_salt}${encoded_digest}"
    )


def _password_matches(password: str, encoded: str) -> bool:
    """Verify an MHM scrypt hash without exposing parsing failures."""
    try:
        marker, product, algorithm, n, r, p, salt, expected = encoded.split("$")
        if marker or product != "mhm" or algorithm != "scrypt":
            return False
        parameters = (int(n), int(r), int(p))
        if parameters != (SCRYPT_N, SCRYPT_R, SCRYPT_P):
            return False
        salt_bytes = base64.urlsafe_b64decode(salt + "=" * (-len(salt) % 4))
        expected_bytes = base64.urlsafe_b64decode(
            expected + "=" * (-len(expected) % 4)
        )
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt_bytes,
            n=parameters[0],
            r=parameters[1],
            p=parameters[2],
            dklen=len(expected_bytes),
        )
        return len(expected_bytes) == 32 and secrets.compare_digest(
            actual, expected_bytes
        )
    except (ValueError, TypeError, UnicodeError):
        return False


# Unknown accounts take the same expensive password path as known accounts.
_DUMMY_PASSWORD_HASH = _password_hash("MHM dummy password used only for timing")


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

    @handle_errors("loading website account", user_friendly=False, default_return={})
    def get(self, uid):
        """Load one account document by canonical user ID."""
        from core import get_user_data

        return get_user_data(uid, "account").get("account") or {}

    @handle_errors("finding website OAuth account", user_friendly=False)
    def by_oauth(self, provider, subject):
        """Return the unique account linked to one provider subject."""
        matches = [
            (uid, account)
            for uid, account in self.all()
            if (account.get("oauth_identities") or {}).get(provider) == subject
        ]
        return matches[0] if len(matches) == 1 else None

    @handle_errors("saving website password", user_friendly=False, default_return=False)
    def set_password(self, uid, password_hash):
        """Store a password hash in the canonical account document."""
        from core import update_user_account

        return update_user_account(
            uid, {"password_hash": password_hash}, auto_create=False
        )

    @handle_errors("linking website OAuth account", user_friendly=False, default_return="failed")
    def link_oauth(self, uid, provider, subject):
        """Link a provider subject once, without storing provider tokens."""
        from core import update_user_account

        current = self.get(uid)
        identities = dict(current.get("oauth_identities") or {})
        current_subject = identities.get(provider)
        if current_subject and current_subject != subject:
            return "different_linked"
        for other_uid, other in self.all():
            if other_uid != uid and (other.get("oauth_identities") or {}).get(
                provider
            ) == subject:
                return "already_linked"
        identities[provider] = subject
        return (
            "linked"
            if update_user_account(
                uid, {"oauth_identities": identities}, auto_create=False
            )
            else "failed"
        )

    @handle_errors("unlinking website OAuth account", user_friendly=False, default_return=False)
    def unlink_oauth(self, uid, provider):
        """Remove one social sign-in identity from an account."""
        from core import update_user_account

        current = self.get(uid)
        identities = dict(current.get("oauth_identities") or {})
        if provider not in identities:
            return True
        identities.pop(provider)
        return bool(
            update_user_account(
                uid, {"oauth_identities": identities}, auto_create=False
            )
        )

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

    @handle_errors("unlinking website Discord account", user_friendly=False, default_return=False)
    def unlink_discord(self, uid):
        """Remove Discord and fall back to verified email delivery when needed."""
        from core import save_user_data_transaction

        documents = self.documents(uid)
        account = dict(documents.get("account") or {})
        preferences = dict(documents.get("preferences") or {})
        account.update(
            {
                "discord_user_id": "",
                "discord_username": "",
            }
        )
        if (preferences.get("channel") or {}).get("type") == "discord":
            preferences["channel"] = {"type": "email"}
            account["chat_id"] = account.get("email", "")
        return bool(
            save_user_data_transaction(
                uid,
                {"account": account, "preferences": preferences},
                auto_create=False,
            )
        )

    @handle_errors("creating website account", user_friendly=False)
    def create(self, email, preferred_name, timezone, password_hash):
        """Create an MHM account after website email verification succeeds."""
        from core import create_new_user

        return create_new_user(
            {
                "email": email,
                "chat_id": email,
                "timezone": timezone,
                "preferred_name": preferred_name,
                "password_hash": password_hash,
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
    message["Subject"] = "Your MHM verification code"
    message.set_content(
        f"Your MHM verification code is: {code}\n\nIt expires in 10 minutes.\nIf you did not request this, ignore this email."
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
    preferred_name: str
    timezone: str
    user_id: str | None
    eligible: bool
    attempts: int = 0


@dataclass(frozen=True)
class OAuthIdentity:
    """Minimal verified identity returned by an external sign-in provider."""

    subject: str
    email: str
    email_verified: bool
    display_name: str = ""


_DEFAULT_SETUP_FLAGS = {
    "messages_enabled": False,
    "tasks_enabled": False,
    "checkins_enabled": False,
    "needs_setup": True,
}


@handle_errors("reading account feature flags", user_friendly=False, default_return={})
def _account_features(account):
    """Return the feature-flag map from an account envelope or nested document."""
    if not isinstance(account, dict):
        return {}
    features = account.get("features")
    if isinstance(features, dict):
        return features
    nested = account.get("account")
    if isinstance(nested, dict) and nested is not account:
        nested_features = nested.get("features")
        if isinstance(nested_features, dict):
            return nested_features
    return {}


@handle_errors("checking OAuth email confirmation", user_friendly=False, default_return=False)
def _oauth_email_verified(provider, identity):
    """Return whether this provider identity includes an email MHM can trust."""
    if not isinstance(identity, dict):
        return False
    if provider == "google":
        return identity.get("email_verified") in {True, "true"}
    if provider == "facebook":
        email = identity.get("email", "")
        return isinstance(email, str) and bool(email.strip())
    return False


@handle_errors("checking website account email", user_friendly=False, default_return=False)
def _valid_account_email(email):
    """Return whether an address can be stored as an MHM account email."""
    return (
        isinstance(email, str)
        and len(email) <= 254
        and re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", email)
        is not None
    )


@handle_errors("checking website support feature", user_friendly=False, default_return=False)
def _feature_enabled(features, key):
    """True when a support feature is stored as enabled."""
    if not isinstance(features, dict):
        return False
    value = features.get(key)
    if value is True:
        return True
    return isinstance(value, str) and value.strip().lower() == "enabled"


@handle_errors(
    "computing website first-run flags",
    user_friendly=False,
    default_return=_DEFAULT_SETUP_FLAGS,
)
def _setup_flags(account):
    """Return website first-run flags from one account document."""
    features = _account_features(account)
    messages_enabled = _feature_enabled(features, "automated_messages")
    tasks_enabled = _feature_enabled(features, "task_management")
    checkins_enabled = _feature_enabled(features, "checkins")
    return {
        "messages_enabled": messages_enabled,
        "tasks_enabled": tasks_enabled,
        "checkins_enabled": checkins_enabled,
        "needs_setup": not (messages_enabled or tasks_enabled or checkins_enabled),
    }


@handle_errors("choosing signed-in website path", user_friendly=False, default_return="/home.html")
def _signed_in_path(account, *, linking=False):
    """Return Home, setup, or Account after a successful website sign-in."""
    if linking:
        return "/app.html"
    return "/setup.html" if _setup_flags(account).get("needs_setup") else "/home.html"


async def _fetch_oauth_identity(
    provider,
    code,
    *,
    client_id,
    client_secret,
    redirect_uri,
):
    """Exchange an authorization code and read a verified provider identity."""
    try:
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                OAUTH_TOKEN_URLS[provider],
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            ) as response:
                if response.status != 200:
                    raise CommunicationError(
                        f"{provider.title()} authorization could not be completed"
                    )
                token = await response.json(content_type=None)
            if not isinstance(token, dict):
                raise DataError("OAuth token response was invalid")
            access_token = token.get("access_token")
            if not isinstance(access_token, str) or not access_token:
                raise DataError("OAuth authorization returned no access token")
            identity_url = (
                "https://openidconnect.googleapis.com/v1/userinfo"
                if provider == "google"
                else "https://graph.facebook.com/me?fields=id,name,email"
            )
            async with session.get(
                identity_url,
                headers={"Authorization": f"Bearer {access_token}"},
            ) as response:
                if response.status != 200:
                    raise CommunicationError(
                        f"{provider.title()} identity could not be read"
                    )
                identity = await response.json(content_type=None)
    except (CommunicationError, DataError, ValidationError):
        raise
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, KeyError) as exc:
        raise CommunicationError("OAuth identity request failed") from exc
    if not isinstance(identity, dict):
        raise ValidationError("OAuth identity was invalid")
    subject = identity.get("sub") if provider == "google" else identity.get("id")
    email = identity.get("email", "")
    if not isinstance(subject, str) or not 1 <= len(subject) <= 255:
        raise ValidationError("OAuth identity was invalid")
    if not isinstance(email, str):
        email = ""
    # Google exposes an explicit email_verified claim. Facebook returns email
    # only after the person grants it and Facebook has a valid primary address,
    # so a present email is the confirmation MHM can use.
    verified = _oauth_email_verified(provider, identity)
    display_name = identity.get("name", "")
    return OAuthIdentity(
        subject,
        email.casefold(),
        verified,
        display_name if isinstance(display_name, str) else "",
    )


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
    oauth_identity=None,
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
    health_lock = asyncio.Lock()
    discord_link_lock = asyncio.Lock()
    oauth_link_lock = asyncio.Lock()
    discord_states = {}
    oauth_states = {}
    health_connecting = set()
    discord_identity = discord_identity or _fetch_discord_identity
    oauth_identity = oauth_identity or _fetch_oauth_identity

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
    def oauth_provider_config(provider):
        """Return provider credentials and callback settings from configuration."""
        if provider not in OAUTH_PROVIDERS:
            return None
        prefix = provider.upper()
        client_id = str(getattr(config, f"{prefix}_OAUTH_CLIENT_ID", "") or "").strip()
        client_secret = str(
            getattr(config, f"{prefix}_OAUTH_CLIENT_SECRET", "") or ""
        ).strip()
        redirect_uri = str(
            getattr(config, f"{prefix}_OAUTH_REDIRECT_URI", "") or ""
        ).strip() or f"{origin}/api/auth/oauth/{provider}/callback"
        if not client_id or not client_secret:
            return None
        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        }

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
        for key in [key for key, value in oauth_states.items() if value["expires"] <= now]:
            del oauth_states[key]

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

    # ERROR_HANDLING_EXCLUDE: Pure validation helper used inside guarded routes.
    def valid_password(value):
        """Accept long passphrases without brittle composition requirements."""
        return (
            isinstance(value, str)
            and PASSWORD_MIN_LENGTH <= len(value) <= PASSWORD_MAX_LENGTH
        )

    # ERROR_HANDLING_EXCLUDE: Session creation runs inside guarded routes.
    def start_session(uid, email, response, *, auth_method):
        """Attach a new opaque browser session to a response."""
        if len(sessions) >= 10000:
            raise web.HTTPServiceUnavailable(
                text="MHM is busy. Please try again later."
            )
        session = secrets.token_urlsafe(32)
        sessions[hashlib.sha256(session.encode()).hexdigest()] = (
            uid,
            clock() + SESSION_TTL,
            email.casefold(),
            auth_method,
        )
        response.set_cookie(
            COOKIE,
            session,
            httponly=True,
            secure=not local,
            samesite="Lax",
            max_age=SESSION_TTL,
            path="/api/",
        )
        return response

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def password_login(request):
        """Authenticate an active account with its saved password."""
        data = await body(request)
        email, password = data.get("email"), data.get("password")
        if (
            not isinstance(email, str)
            or len(email) > 254
            or not isinstance(password, str)
            or not valid_password(password)
        ):
            raise web.HTTPBadRequest(
                text=f"Enter your email and a password of {PASSWORD_MIN_LENGTH}–{PASSWORD_MAX_LENGTH} characters."
            )
        email = email.strip().casefold()
        throttle(("password", email), 8, 600)
        existing = await asyncio.to_thread(accounts.by_email, email)
        saved_hash = (
            existing[1].get("password_hash", "")
            if existing and existing[1].get("account_status") == "active"
            else ""
        )
        matches = await asyncio.to_thread(
            _password_matches, password, saved_hash or _DUMMY_PASSWORD_HASH
        )
        if not existing or not saved_hash or not matches:
            raise web.HTTPUnauthorized(
                text="That email or password did not work. You can use an emailed code instead."
            )
        response = web.json_response({"ok": True})
        return start_session(existing[0], email, response, auth_method="password")

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def password_setup(request):
        """Set or replace the password for the signed-in account."""
        uid, current = await authenticated_account(request)
        data = await body(request)
        password = data.get("password")
        if not isinstance(password, str) or not valid_password(password):
            raise web.HTTPBadRequest(
                text=f"Use a password of {PASSWORD_MIN_LENGTH}–{PASSWORD_MAX_LENGTH} characters."
            )
        saved_hash = current.get("password_hash", "")
        current_key = hashlib.sha256(
            request.cookies.get(COOKIE, "").encode()
        ).hexdigest()
        current_session = sessions.get(current_key)
        code_reauthenticated = bool(
            current_session
            and len(current_session) > 3
            and current_session[3] == "email_code"
        )
        if saved_hash and not code_reauthenticated:
            current_password = data.get("current_password")
            throttle(("password-change", current.get("email", "").casefold()), 8, 600)
            if not isinstance(current_password, str) or not await asyncio.to_thread(
                _password_matches, current_password, saved_hash
            ):
                raise web.HTTPUnauthorized(text="Your current password did not work.")
        encoded = await asyncio.to_thread(_password_hash, password)
        if not await asyncio.to_thread(accounts.set_password, uid, encoded):
            raise web.HTTPServiceUnavailable(
                text="Your password could not be saved. Please try again."
            )
        for key in [
            key
            for key, session in sessions.items()
            if session[0] == uid and key != current_key
        ]:
            sessions.pop(key, None)
        if current_session:
            sessions[current_key] = (
                current_session[0],
                current_session[1],
                current_session[2],
                "password",
            )
        return web.json_response(
            {"ok": True, "email": current.get("email", "")}
        )

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
        if mode not in {"login", "create", "reset"}:
            raise web.HTTPBadRequest(
                text="Choose log in, create account, or reset password."
            )
        preferred_name = data.get("preferred_name", data.get("username", ""))
        timezone = data.get("timezone", "America/Regina")
        if mode == "create":
            if not isinstance(preferred_name, str) or len(preferred_name) > 100:
                raise web.HTTPBadRequest(
                    text="Use a preferred name of at most 100 characters."
                )
            preferred_name = preferred_name.strip()
            try:
                ZoneInfo(timezone)
            except (ZoneInfoNotFoundError, ValueError, TypeError):
                raise web.HTTPBadRequest(
                    text="Your time zone could not be recognized."
                ) from None
        else:
            preferred_name, timezone = "", "America/Regina"
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
            if mode in {"login", "reset"}
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
        elif mode in {"login", "reset"}:
            logger.info(
                "Website account verification email skipped: no unique active account matched"
            )
        challenges[token] = Challenge(
            hashlib.sha256(code.encode()).hexdigest(),
            clock() + CODE_TTL,
            email,
            mode,
            preferred_name,
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
                password = data.get("password")
                if not isinstance(password, str) or not valid_password(password):
                    raise web.HTTPBadRequest(
                        text=f"Use a password of {PASSWORD_MIN_LENGTH}–{PASSWORD_MAX_LENGTH} characters."
                    )
                if await asyncio.to_thread(accounts.email_exists, challenge.email):
                    del challenges[token]
                    raise web.HTTPConflict(
                        text="An account already uses this email. Please log in."
                    )
                encoded = await asyncio.to_thread(_password_hash, password)
                uid = await asyncio.to_thread(
                    accounts.create,
                    challenge.email,
                    challenge.preferred_name,
                    challenge.timezone,
                    encoded,
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
            if challenge.mode == "reset":
                password = data.get("password")
                if not isinstance(password, str) or not valid_password(password):
                    raise web.HTTPBadRequest(
                        text=f"Use a password of {PASSWORD_MIN_LENGTH}–{PASSWORD_MAX_LENGTH} characters."
                    )
                encoded = await asyncio.to_thread(_password_hash, password)
                if not await asyncio.to_thread(accounts.set_password, uid, encoded):
                    raise web.HTTPServiceUnavailable(
                        text="Your password could not be saved. Please try again."
                    )
                for key in [
                    key for key, session in sessions.items() if session[0] == uid
                ]:
                    sessions.pop(key, None)
            del challenges[token]
        response = web.json_response({"ok": True})
        auth_method = (
            "password" if challenge.mode in {"create", "reset"} else "email_code"
        )
        return start_session(uid, challenge.email, response, auth_method=auth_method)

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
        uid, current = await authenticated_account(request)
        documents = await asyncio.to_thread(accounts.documents, uid)
        preferred_name = str(
            (documents.get("context") or {}).get("preferred_name", "")
        ).strip()
        session_key = hashlib.sha256(
            request.cookies.get(COOKIE, "").encode()
        ).hexdigest()
        current_session = sessions.get(session_key)
        code_reauthenticated = bool(
            current_session
            and len(current_session) > 3
            and current_session[3] == "email_code"
        )
        app_id = str(config.DISCORD_APPLICATION_ID or "")
        account_doc = documents.get("account")
        if not isinstance(account_doc, dict) or not _account_features(account_doc):
            account_doc = current
        flags = _setup_flags(account_doc)
        return web.json_response(
            {
                "preferred_name": preferred_name,
                "email": current.get("email", ""),
                "timezone": current.get("timezone", ""),
                "discord_linked": bool(current.get("discord_user_id")),
                "discord_available": discord_available(),
                "password_set": bool(current.get("password_hash")),
                "password_change_requires_current": bool(current.get("password_hash"))
                and not code_reauthenticated,
                "needs_setup": flags["needs_setup"],
                "messages_enabled": flags["messages_enabled"],
                "tasks_enabled": flags["tasks_enabled"],
                "checkins_enabled": flags["checkins_enabled"],
                "oauth": {
                    provider: {
                        "available": oauth_provider_config(provider) is not None,
                        "linked": bool(
                            (current.get("oauth_identities") or {}).get(provider)
                        ),
                    }
                    for provider in OAUTH_PROVIDERS
                },
                "discord_url": (
                    f"https://discord.com/users/{app_id}" if app_id.isdigit() else None
                ),
            }
        )

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def account_connections(request):
        """Disconnect one optional sign-in or communication provider."""
        uid, current = await authenticated_account(request)
        data = await body(request)
        provider = data.get("provider")
        if set(data) != {"provider"} or provider not in {
            "discord",
            *OAUTH_PROVIDERS,
        }:
            raise web.HTTPBadRequest(text="Choose a connected account to disconnect.")
        password_set = bool(current.get("password_hash"))
        identities = current.get("oauth_identities") or {}
        if provider != "discord" and provider not in identities:
            return web.json_response({"ok": True, "provider": provider})
        other_oauth = (set(identities) & set(OAUTH_PROVIDERS)) - {provider}
        if provider != "discord" and not password_set and not other_oauth:
            raise web.HTTPBadRequest(
                text="Set a password before disconnecting your only social sign-in."
            )
        if provider == "discord":
            ok = await asyncio.to_thread(accounts.unlink_discord, uid)
        else:
            ok = await asyncio.to_thread(accounts.unlink_oauth, uid, provider)
        if not ok:
            raise web.HTTPServiceUnavailable(text="That account could not be disconnected.")
        return web.json_response({"ok": True, "provider": provider})

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def account_export(request):
        """Download a JSON copy of the signed-in user's stored MHM data."""
        uid, current = await authenticated_account(request)
        from storage.user_data_operations import export_user_data

        exported = await asyncio.to_thread(export_user_data, uid, "json")
        if not exported:
            raise web.HTTPServiceUnavailable(text="Your data export could not be prepared.")
        from tasks.task_service import load_active_tasks, load_completed_tasks
        from notebook.notebook_data_manager import list_recent

        active_tasks, completed_tasks, notebook_entries = await asyncio.gather(
            asyncio.to_thread(load_active_tasks, uid),
            asyncio.to_thread(load_completed_tasks, uid),
            asyncio.to_thread(list_recent, uid, n=10000, include_archived=True),
        )
        exported["tasks"] = {
            "active": [task_view(task) for task in active_tasks],
            "completed": [task_view(task) for task in completed_tasks],
        }
        exported["notebook"] = [note_view(entry) for entry in notebook_entries]

        @handle_errors(
            "removing secrets from website export",
            user_friendly=False,
            re_raise=True,
        )
        def remove_secrets(value):
            """Remove authentication secrets from an otherwise complete export."""
            if isinstance(value, dict):
                return {
                    key: remove_secrets(item)
                    for key, item in value.items()
                    if key not in {"password_hash"}
                }
            if isinstance(value, list):
                return [remove_secrets(item) for item in value]
            return value

        payload = json.dumps(remove_secrets(exported), indent=2, default=str)
        return web.Response(
            text=payload,
            content_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="mhm-data.json"'},
        )
    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def oauth_providers(request):
        """Report which optional social sign-in providers are configured."""
        return web.json_response(
            {
                "providers": {
                    provider: oauth_provider_config(provider) is not None
                    for provider in OAUTH_PROVIDERS
                }
            }
        )

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def oauth_start(request):
        """Create one-time state and return a provider authorization URL."""
        provider = request.match_info["provider"]
        provider_config = oauth_provider_config(provider)
        if not provider_config:
            raise web.HTTPServiceUnavailable(
                text=f"{provider.title()} sign-in is not configured yet."
            )
        if len(oauth_states) >= 10000:
            raise web.HTTPTooManyRequests(text="MHM is busy. Please try again later.")
        session_key = hashlib.sha256(
            request.cookies.get(COOKIE, "").encode()
        ).hexdigest()
        active_session = sessions.get(session_key)
        linked_uid = active_session[0] if active_session and active_session[1] > clock() else None
        state = secrets.token_urlsafe(32)
        timezone = str(request.query.get("timezone", "") or "").strip()
        try:
            ZoneInfo(timezone)
        except (ZoneInfoNotFoundError, ValueError, TypeError):
            timezone = "America/Regina"
        oauth_states[hashlib.sha256(state.encode()).hexdigest()] = {
            "provider": provider,
            "expires": clock() + OAUTH_STATE_TTL,
            "session_key": session_key if linked_uid else "",
            "linked_uid": linked_uid,
            "timezone": timezone,
        }
        query = {
            "client_id": provider_config["client_id"],
            "redirect_uri": provider_config["redirect_uri"],
            "response_type": "code",
            "state": state,
        }
        if provider == "google":
            query.update({"scope": "openid email profile", "prompt": "select_account"})
        else:
            query.update({"scope": "public_profile,email"})
        return web.json_response(
            {"url": f"{OAUTH_AUTHORIZE_URLS[provider]}?{urlencode(query)}"}
        )

    # ERROR_HANDLING_EXCLUDE: OAuth callback intentionally maps all failures to safe redirects.
    async def oauth_callback(request):
        """Validate a social callback, link its identity, and start a session."""
        provider = request.match_info["provider"]
        values = request.query
        state = values.get("state", "")
        state_key = hashlib.sha256(str(state).encode()).hexdigest()
        pending = oauth_states.pop(state_key, None)
        return_path = "/app.html" if pending and pending.get("linked_uid") else "/login.html"
        if (
            provider not in OAUTH_PROVIDERS
            or values.get("error")
            or not pending
            or pending["provider"] != provider
            or pending["expires"] <= clock()
        ):
            return web.HTTPFound(website_redirect(return_path, social="cancelled"))
        provider_config = oauth_provider_config(provider)
        code = values.get("code", "")
        if not provider_config or not isinstance(code, str) or not 1 <= len(code) <= 2048:
            return web.HTTPFound(website_redirect(return_path, social="unavailable"))
        try:
            identity = await oauth_identity(
                provider,
                code,
                client_id=provider_config["client_id"],
                client_secret=provider_config["client_secret"],
                redirect_uri=provider_config["redirect_uri"],
            )
            if not isinstance(identity, OAuthIdentity):
                raise ValidationError("OAuth identity was invalid")
            linked_match = await asyncio.to_thread(
                accounts.by_oauth, provider, identity.subject
            )
            target = None
            if pending.get("linked_uid"):
                saved_session = sessions.get(pending["session_key"])
                if (
                    not saved_session
                    or saved_session[1] <= clock()
                    or saved_session[0] != pending["linked_uid"]
                ):
                    return web.HTTPFound(
                        website_redirect("/login.html", social="expired")
                    )
                current = await asyncio.to_thread(accounts.get, saved_session[0])
                if (
                    current.get("account_status") != "active"
                    or current.get("email", "").casefold() != saved_session[2]
                ):
                    return web.HTTPFound(
                        website_redirect("/login.html", social="expired")
                    )
                target = (saved_session[0], current)
                if linked_match and linked_match[0] != target[0]:
                    return web.HTTPFound(
                        website_redirect("/app.html", social="in-use")
                    )
            elif linked_match:
                target = linked_match
            elif identity.email and identity.email_verified:
                target = await asyncio.to_thread(accounts.by_email, identity.email)
            if (
                not pending.get("linked_uid")
                and (not target or target[1].get("account_status") != "active")
                and provider in {"google", "facebook"}
                and identity.email_verified
                and _valid_account_email(identity.email)
                and not await asyncio.to_thread(accounts.email_exists, identity.email)
            ):
                async with oauth_link_lock:
                    linked_match = await asyncio.to_thread(
                        accounts.by_oauth, provider, identity.subject
                    )
                    if (
                        linked_match
                        and linked_match[1].get("account_status") == "active"
                    ):
                        target = linked_match
                    elif not await asyncio.to_thread(
                        accounts.email_exists, identity.email
                    ):
                        uid = await asyncio.to_thread(
                            accounts.create,
                            identity.email,
                            identity.display_name.strip()[:100],
                            pending.get("timezone") or "America/Regina",
                            "",
                        )
                        if not uid:
                            raise DataError("OAuth account could not be created")
                        created_account = await asyncio.to_thread(accounts.get, uid)
                        result = await asyncio.to_thread(
                            accounts.link_oauth,
                            uid,
                            provider,
                            identity.subject,
                        )
                        if result not in {"linked", "already_linked"}:
                            raise DataError("OAuth account could not be linked")
                        target = (uid, created_account)
                        linked_match = target
            if (
                not target
                and provider == "facebook"
                and not identity.email
                and not pending.get("linked_uid")
            ):
                return web.HTTPFound(
                    website_redirect("/login.html", social="no-email")
                )
            if not target or target[1].get("account_status") != "active":
                return web.HTTPFound(
                    website_redirect("/login.html", social="not-linked")
                )
            if not linked_match:
                async with oauth_link_lock:
                    # Recheck uniqueness after provider I/O and before the write.
                    linked_match = await asyncio.to_thread(
                        accounts.by_oauth, provider, identity.subject
                    )
                    if linked_match and linked_match[0] != target[0]:
                        return web.HTTPFound(
                            website_redirect(return_path, social="in-use")
                        )
                    result = await asyncio.to_thread(
                        accounts.link_oauth,
                        target[0],
                        provider,
                        identity.subject,
                    )
                    if result not in {"linked", "already_linked"}:
                        raise DataError("OAuth account could not be linked")
            landing = _signed_in_path(
                target[1], linking=bool(pending.get("linked_uid"))
            )
            response = web.HTTPFound(
                website_redirect(landing, social=f"{provider}-connected")
            )
            return start_session(
                target[0],
                target[1].get("email", ""),
                response,
                auth_method="oauth",
            )
        except Exception:
            logger.error(f"Website {provider} sign-in failed")
            return web.HTTPFound(website_redirect(return_path, social="error"))

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
        next_path = request.query.get("next", "/app.html")
        if next_path not in {"/app.html", "/setup.html"}:
            raise web.HTTPBadRequest(text="Choose a valid return page.")
        state = secrets.token_urlsafe(32)
        discord_states[hashlib.sha256(state.encode()).hexdigest()] = (
            hashlib.sha256(request.cookies.get(COOKIE, "").encode()).hexdigest(),
            clock() + DISCORD_STATE_TTL,
            next_path,
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
        return_path = (
            pending[2]
            if pending and len(pending) > 2 and pending[2] in {"/app.html", "/setup.html"}
            else "/app.html"
        )
        if error or not pending or pending[1] <= clock():
            return web.HTTPFound(website_redirect(return_path, discord="cancelled"))
        if not discord_available():
            return web.HTTPFound(website_redirect(return_path, discord="unavailable"))
        code = request.query.get("code", "")
        if not code or len(code) > 2048:
            return web.HTTPFound(website_redirect(return_path, discord="error"))
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
                return web.HTTPFound(website_redirect(return_path, discord="in-use"))
            if result == "different_linked":
                return web.HTTPFound(
                    website_redirect(return_path, discord="account-linked")
                )
            if result != "linked":
                raise DataError("Discord account could not be linked")
        except web.HTTPUnauthorized:
            return web.HTTPFound(website_redirect("/login.html", discord="expired"))
        except Exception:
            logger.error("Website Discord connection failed", exc_info=True)
            return web.HTTPFound(website_redirect(return_path, discord="error"))
        return web.HTTPFound(website_redirect(return_path, discord="connected"))

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

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def insights(request):
        """Return authenticated wellness, habit, and check-in analytics."""
        uid, _ = await authenticated_account(request)
        try:
            days = int(request.query.get("days", "30"))
        except ValueError:
            raise web.HTTPBadRequest(text="Choose a valid analysis period.") from None
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

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def health_settings(request):
        """Read or change the signed-in user's Google Health integration."""
        uid, _ = await authenticated_account(request)
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
                "connecting": uid in health_connecting,
            }

        if request.method == "GET":
            return web.json_response(await asyncio.to_thread(snapshot))
        data = await body(request)
        if set(data) != {"action"} or data.get("action") not in {
            "connect",
            "pause",
            "enable",
            "sync",
            "delete",
        }:
            raise web.HTTPBadRequest(text="Choose a valid Google Health action.")
        action = data["action"]
        throttle(("health", uid), 12, 600)
        async with health_lock:
            await authenticated_account(request)
            if action == "connect":
                ready, error = await asyncio.to_thread(get_connect_readiness)
                if not ready:
                    raise web.HTTPServiceUnavailable(text=error)
                if uid in health_connecting:
                    raise web.HTTPConflict(text="Google Health connection is already in progress.")
                url = await asyncio.to_thread(get_connect_authorization_url, uid)
                if not url:
                    raise web.HTTPServiceUnavailable(text="Google Health could not start connecting.")
                health_connecting.add(uid)

                @handle_errors(
                    "finishing Google Health website connection",
                    user_friendly=False,
                    default_return=None,
                )
                def finished(_success, _error):
                    """Release the single in-progress connect slot for this user."""
                    health_connecting.discard(uid)

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
                message = "Google Health data was deleted and the integration was disabled."
            if not ok:
                raise web.HTTPServiceUnavailable(text="Google Health could not complete that action.")
            return web.json_response({"ok": True, "message": message, **snapshot()})

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
                and isinstance(period.get("date"), str)
                and isinstance(period.get("start_time"), str)
                and (period.get("end_time") is None or isinstance(period.get("end_time"), str))
            ):
                reminders.append({
                    "kind": "scheduled",
                    "period": {
                        "date": period.get("date"),
                        "start_time": period.get("start_time"),
                        "end_time": period.get("end_time"),
                    },
                })
            elif (
                isinstance(reminder, dict)
                and reminder.get("kind") == "quick"
                and isinstance(reminder.get("value"), str)
            ):
                reminders.append({"kind": "quick", "value": reminder["value"]})
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
            get_tasks_due_soon,
            load_active_tasks,
            load_completed_tasks,
            restore_task,
            update_task,
        )
        from tasks.task_data_manager import get_task_by_id
        task_id = request.match_info.get("task_id")
        action = request.match_info.get("action")
        quick_reminder_values = {
            "5-10min", "30min-1hour", "1-2hour", "1-2day", "3-5day", "1-2week"
        }

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
                if (
                    not isinstance(period, dict)
                    or set(period) - {"date", "start_time", "end_time"}
                    or not {"date", "start_time"}.issubset(period)
                ):
                    raise web.HTTPBadRequest(text="Each reminder needs a date and time; end time is optional.")
                date = period["date"]
                start = period["start_time"]
                end = period.get("end_time") or None
                if (
                    not isinstance(date, str) or parse_date_only(date) is None
                    or not isinstance(start, str) or parse_time_only_minute(start) is None
                    or (end is not None and (not isinstance(end, str) or parse_time_only_minute(end) is None or start >= end))
                ):
                    raise web.HTTPBadRequest(text="Reminder dates and times must be valid, and an optional end must be after the reminder time.")
                cleaned.append({"date": date, "start_time": start, "end_time": end})
            return cleaned

        # ERROR_HANDLING_EXCLUDE: Validation helper raises intentional HTTP responses.
        def clean_quick_reminders(value):
            """Validate the canonical relative reminder choices."""
            if value is None:
                return []
            if (
                not isinstance(value, list)
                or len(value) > len(quick_reminder_values)
                or len(set(value)) != len(value)
                or any(item not in quick_reminder_values for item in value)
            ):
                raise web.HTTPBadRequest(text="Choose valid relative reminders.")
            return value

        # ERROR_HANDLING_EXCLUDE: Validation helper raises intentional HTTP responses.
        def clean_completion(value):
            """Validate optional completion date, time, and notes."""
            if value in (None, {}):
                return None
            if not isinstance(value, dict) or set(value) != {
                "completion_date", "completion_time", "completion_notes"
            }:
                raise web.HTTPBadRequest(text="Please submit valid completion details.")
            completion_date = value["completion_date"]
            completion_time = value["completion_time"]
            completion_notes = value["completion_notes"]
            if (
                not isinstance(completion_date, str)
                or parse_date_only(completion_date) is None
                or not isinstance(completion_time, str)
                or parse_time_only_minute(completion_time) is None
                or not isinstance(completion_notes, str)
                or len(completion_notes) > 5000
            ):
                raise web.HTTPBadRequest(text="Use a valid completion date, time, and notes.")
            return {
                "completion_date": completion_date,
                "completion_time": completion_time,
                "completion_notes": completion_notes,
            }

        if request.method == "GET":
            status = request.query.get("status", "active")
            if status not in {"active", "completed", "all"}:
                raise web.HTTPBadRequest(text="Choose active, completed, or all tasks.")
            active = await asyncio.to_thread(load_active_tasks, uid)
            completed = await asyncio.to_thread(load_completed_tasks, uid)
            due_soon = await asyncio.to_thread(get_tasks_due_soon, uid, days_ahead=7)
            from core.tags import get_user_tags

            saved_tags = await asyncio.to_thread(get_user_tags, uid)
            selected = active if status == "active" else completed if status == "completed" else active + completed
            tags = sorted(
                {
                    str(tag).strip()
                    for tag in [
                        *saved_tags,
                        *[
                            task_tag
                            for task in active + completed
                            for task_tag in (task.get("tags") or [])
                        ],
                    ]
                    if str(tag).strip()
                },
                key=str.casefold,
            )
            return web.json_response({
                "tasks": [task_view(task) for task in selected],
                "active_count": len(active),
                "completed_count": len(completed),
                "due_soon_count": len(due_soon),
                "tags": tags,
            })

        if request.method == "POST" and not task_id:
            data = await body(request)
            allowed = {
                "title", "description", "due_date", "due_time", "priority",
                "recurrence_pattern", "recurrence_interval", "repeat_after_completion",
                "tags", "reminder_periods", "quick_reminders",
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
            quick_reminders = clean_quick_reminders(data.get("quick_reminders", []))
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
            if quick_reminders and not due_date:
                raise web.HTTPBadRequest(text="Relative reminders need a due date.")
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
                quick_reminders=quick_reminders,
            )
            if not created_id:
                raise web.HTTPServiceUnavailable(text="MHM could not create that task. Please try again.")
            return web.json_response({"task": task_view(find(created_id))}, status=201)

        if not task_id:
            raise web.HTTPBadRequest(text="A task ID is required.")
        action_message = ""
        if action == "complete" and request.method == "POST":
            completion_data = clean_completion(await body(request))
            if not await asyncio.to_thread(
                complete_task, uid, task_id, completion_data
            ):
                raise web.HTTPNotFound(text="That active task could not be completed.")
        elif action == "restore" and request.method == "POST":
            if not await asyncio.to_thread(restore_task, uid, task_id):
                raise web.HTTPNotFound(text="That completed task could not be restored.")
        elif action == "snooze" and request.method == "POST":
            data = await body(request)
            option = data.get("option")
            custom_when = data.get("custom_when")
            if (
                set(data) - {"option", "custom_when"}
                or option not in {"1_hour", "tonight", "next_week", "custom"}
                or (
                    custom_when is not None
                    and (not isinstance(custom_when, str) or len(custom_when) > 200)
                )
                or (option == "custom" and not str(custom_when or "").strip())
            ):
                raise web.HTTPBadRequest(
                    text="Choose one hour, tonight, next week, or enter a custom reminder time."
                )
            from tasks.task_reminder_snooze import snooze_task_reminder

            result = await asyncio.to_thread(
                snooze_task_reminder,
                uid,
                task_id,
                option,
                custom_when=str(custom_when or "").strip() or None,
            )
            if not result or not result.success:
                raise web.HTTPBadRequest(
                    text=(result.message if result else "That reminder could not be snoozed.")
                )
            action_message = result.message
        elif action == "skip" and request.method == "POST":
            if await body(request):
                raise web.HTTPBadRequest(text="Skipping this occurrence does not need any other details.")
            from tasks.task_occurrence_skip import skip_task_occurrence

            result = await asyncio.to_thread(skip_task_occurrence, uid, task_id)
            if not result or not result.success:
                raise web.HTTPBadRequest(
                    text=(result.message if result else "That task occurrence could not be skipped.")
                )
            action_message = result.message
        elif action == "simplify" and request.method == "POST":
            data = await body(request)
            new_title = data.get("new_title")
            if (
                set(data) != {"new_title"}
                or not isinstance(new_title, str)
                or not new_title.strip()
                or len(new_title.strip()) > 500
            ):
                raise web.HTTPBadRequest(text="Enter a smaller next step for this task.")
            from tasks.task_simplify import simplify_task

            result = await asyncio.to_thread(
                simplify_task, uid, task_id, new_title.strip()
            )
            if not result or not result.success or result.needs_title:
                raise web.HTTPBadRequest(
                    text=(result.message if result else "That task could not be simplified.")
                )
            action_message = result.message
        elif action is None and request.method == "PATCH":
            data = await body(request)
            allowed = {"title", "description", "due_date", "due_time", "priority", "recurrence_pattern", "recurrence_interval", "repeat_after_completion", "tags", "reminder_periods", "quick_reminders"}
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
            if "quick_reminders" in data:
                data["quick_reminders"] = clean_quick_reminders(data["quick_reminders"])
            for key, parser, message in (("due_date", parse_date_only, "Due dates must use YYYY-MM-DD."), ("due_time", parse_time_only_minute, "Due times must use HH:MM.")):
                if key in data and data[key] not in (None, "") and (not isinstance(data[key], str) or parser(data[key]) is None):
                    raise web.HTTPBadRequest(text=message)
                if key in data and data[key] == "":
                    data[key] = None
            current_task = find(task_id)
            resulting_due_date = data.get("due_date", (current_task.get("due") or {}).get("date"))
            if "quick_reminders" in data:
                resulting_quick = data["quick_reminders"]
            else:
                resulting_quick = [
                    reminder.get("value")
                    for reminder in current_task.get("reminders", [])
                    if isinstance(reminder, dict) and reminder.get("kind") == "quick"
                ]
            if resulting_quick and not resulting_due_date:
                raise web.HTTPBadRequest(text="Relative reminders need a due date.")
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
        return web.json_response(
            {"task": task_view(find(task_id)), **({"message": action_message} if action_message else {})}
        )

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def tasks_bulk(request):
        """Apply one task action to an explicit set of the signed-in user's tasks."""
        uid, _ = await authenticated_account(request)
        data = await body(request)
        task_ids = data.get("task_ids")
        if (
            set(data) != {"task_ids"}
            or not isinstance(task_ids, list)
            or not 1 <= len(task_ids) <= 100
            or len(set(task_ids)) != len(task_ids)
            or any(
                not isinstance(task_id, str) or not 1 <= len(task_id) <= 100
                for task_id in task_ids
            )
        ):
            raise web.HTTPBadRequest(text="Choose between 1 and 100 unique tasks.")
        action = request.match_info["action"]
        from tasks.task_service import complete_task, delete_task, restore_task

        operation = {
            "complete": complete_task,
            "restore": restore_task,
            "delete": delete_task,
        }[action]

        @handle_errors(
            "applying bulk website task actions",
            user_friendly=False,
            re_raise=True,
        )
        def apply_actions():
            """Return the requested task identifiers successfully changed in bulk."""
            return [task_id for task_id in task_ids if operation(uid, task_id)]

        throttle(("tasks-bulk", uid), 20, 60)
        changed = await asyncio.to_thread(apply_actions)
        if not changed:
            raise web.HTTPNotFound(text="None of those tasks could be updated.")
        return web.json_response(
            {
                "ok": True,
                "changed": changed,
                "failed": [task_id for task_id in task_ids if task_id not in changed],
            }
        )

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def task_templates(request):
        """Return safe built-in task templates for quick website creation."""
        await authenticated_account(request)
        from tasks.task_service import list_task_templates

        templates = await asyncio.to_thread(list_task_templates)
        return web.json_response(
            {
                "templates": [
                    {
                        "id": template.template_id,
                        "name": template.display_name,
                        "title": template.title,
                        "description": template.description,
                        "priority": template.priority,
                        "tags": list(template.tags),
                        "due_time": template.default_due_time,
                        "recurrence_pattern": template.recurrence_pattern,
                        "recurrence_interval": template.recurrence_interval,
                    }
                    for template in templates
                ]
            }
        )

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def messages_api(request):
        """Manage the signed-in user's reusable message templates."""
        uid, _ = await authenticated_account(request)
        from messages.message_data_manager import (
            add_message,
            delete_message,
            edit_message,
            is_ai_generated_message_category,
            load_user_messages,
        )

        options = await asyncio.to_thread(accounts.settings_options, uid)
        categories = [
            category
            for category in options.get("categories", [])
            if isinstance(category, str)
            and not is_ai_generated_message_category(category)
        ]
        category = request.match_info.get("category") or request.query.get("category")
        if not category and categories:
            category = categories[0]
        if category not in categories:
            raise web.HTTPBadRequest(text="Choose an available message category.")

        documents = await asyncio.to_thread(accounts.documents, uid)
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
                "days": [str(day) for day in message_schedule.get("days") or ["ALL"]],
                "periods": [str(period) for period in message_schedule.get("periods") or ["ALL"]],
                "updated_at": message.get("updated_at"),
            }

        # error_handling_exclude: Raises intentional HTTP validation responses;
        # unexpected failures propagate to the guarded messages_api boundary.
        def clean(data):
            """Validate an editable message template payload."""
            if set(data) != {"text", "active", "days", "periods"}:
                raise web.HTTPBadRequest(text="Submit the message text, schedule, and enabled state.")
            text = data["text"]
            days = data["days"]
            periods = data["periods"]
            valid_days = {"ALL", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"}
            allowed_periods = {"ALL", *period_names}
            if not isinstance(text, str) or not text.strip() or len(text.strip()) > 5000:
                raise web.HTTPBadRequest(text="Messages must be between 1 and 5,000 characters.")
            if type(data["active"]) is not bool:
                raise web.HTTPBadRequest(text="Choose whether this message is enabled.")
            if (
                not isinstance(days, list)
                or not days
                or len(days) > 7
                or any(not isinstance(day, str) or day not in valid_days for day in days)
                or len(set(days)) != len(days)
                or ("ALL" in days and len(days) != 1)
            ):
                raise web.HTTPBadRequest(text="Choose valid days for this message.")
            if (
                not isinstance(periods, list)
                or not periods
                or len(periods) > 20
                or any(not isinstance(period, str) or period not in allowed_periods for period in periods)
                or len(set(periods)) != len(periods)
                or ("ALL" in periods and len(periods) != 1)
            ):
                raise web.HTTPBadRequest(text="Choose valid reminder windows for this message.")
            return {
                "text": text.strip(),
                "active": data["active"],
                "schedule": {"days": days, "periods": periods},
            }

        if request.method == "GET":
            messages = await asyncio.to_thread(load_user_messages, uid, category)
            return web.json_response(
                {
                    "category": category,
                    "categories": categories,
                    "period_names": period_names,
                    "messages": [view(message) for message in messages],
                }
            )
        if request.method == "POST" and not request.match_info.get("message_id"):
            values = clean(await body(request))
            message_id = secrets.token_urlsafe(18)
            await asyncio.to_thread(
                add_message, uid, category, {"id": message_id, **values}
            )
        else:
            message_id = request.match_info.get("message_id")
            if not message_id or len(message_id) > 200:
                raise web.HTTPBadRequest(text="Choose a valid message.")
            existing = await asyncio.to_thread(load_user_messages, uid, category)
            if not any(str(message.get("id")) == message_id for message in existing):
                raise web.HTTPNotFound(text="That message could not be found.")
            if request.method == "PATCH":
                values = clean(await body(request))
                await asyncio.to_thread(edit_message, uid, category, message_id, values)
            elif request.method == "DELETE":
                if await body(request):
                    raise web.HTTPBadRequest(text="Deleting a message does not need a request body.")
                await asyncio.to_thread(delete_message, uid, category, message_id)
                return web.json_response({"ok": True})
            else:
                raise web.HTTPMethodNotAllowed(request.method, {"GET", "POST", "PATCH", "DELETE"})
        saved = await asyncio.to_thread(load_user_messages, uid, category)
        message = next((item for item in saved if str(item.get("id")) == message_id), None)
        if not message:
            raise web.HTTPServiceUnavailable(text="MHM could not finish saving that message.")
        return web.json_response({"message": view(message)}, status=201 if request.method == "POST" else 200)

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def request_action(request):
        """Queue an authenticated one-off delivery request for the MHM service."""
        uid, _ = await authenticated_account(request)
        data = await body(request)
        action = data.get("action")
        allowed_fields = {
            "test_message": {"action", "category"},
            "checkin_prompt": {"action"},
        }
        if action not in allowed_fields or set(data) != allowed_fields[action]:
            raise web.HTTPBadRequest(text="Choose a valid request action.")
        documents = await asyncio.to_thread(accounts.documents, uid)
        account_data = documents.get("account") or {}
        features = account_data.get("features") or {}
        preferences = documents.get("preferences") or {}
        channel = (preferences.get("channel") or {}).get("type")
        if channel not in {"email", "discord"}:
            raise web.HTTPBadRequest(text="Choose a delivery channel in your settings first.")

        from core.service_utilities import get_flags_dir
        from core.time_utilities import now_timestamp_full
        from storage.service_flag_storage import write_service_flag_json

        if action == "test_message":
            category = data["category"]
            options = await asyncio.to_thread(accounts.settings_options, uid)
            if not isinstance(category, str) or category not in options.get("categories", []):
                raise web.HTTPBadRequest(text="Choose an available message category.")
            filename = f"test_message_request_{uid}_{category}.flag"
            payload = {
                "user_id": uid,
                "category": category,
                "timestamp": now_timestamp_full(),
                "source": "website",
            }
            message = "Your test message was queued for delivery."
        elif action == "checkin_prompt":
            if features.get("checkins") != "enabled":
                raise web.HTTPBadRequest(text="Enable check-ins before requesting one.")
            filename = f"checkin_prompt_request_{uid}.flag"
            payload = {
                "user_id": uid,
                "timestamp": now_timestamp_full(),
                "source": "website",
            }
            message = "Your check-in was queued for delivery."
        throttle(("request-action", uid), 10, 60)
        request_file = Path(get_flags_dir()) / filename
        if not await asyncio.to_thread(
            write_service_flag_json,
            request_file,
            payload,
            audit_reason="website_delivery_request",
            audit_extra={"user_id": uid, "action": action},
        ):
            raise web.HTTPServiceUnavailable(text="MHM could not queue that request.")
        return web.json_response({"ok": True, "message": message})

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
            "pinned": bool(entry.pinned) if str(entry.status) == "active" else False,
            "group": str(entry.group).strip() if str(entry.group or "").strip() else None,
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
        from notebook.notebook_validation import is_valid_entry_group
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

        # ERROR_HANDLING_EXCLUDE: Validation helper raises intentional HTTP responses.
        def clean_group(value):
            """Validate an optional notebook group. Blank clears the group."""
            if value is None or (isinstance(value, str) and not value.strip()):
                return None
            if not isinstance(value, str) or not is_valid_entry_group(value):
                raise web.HTTPBadRequest(
                    text="Group names can use letters, numbers, spaces, hyphens, and underscores."
                )
            return value.strip()

        if request.method == "GET":
            status = request.query.get("status", "active")
            if status not in {"active", "pinned", "inbox", "archived", "all", "group"}:
                raise web.HTTPBadRequest(text="Choose active, pinned, inbox, archived, a group, or all notes.")
            query = request.query.get("q", "").strip()
            tag_filter = request.query.get("tag", "").strip()
            group_name = request.query.get("group", "").strip()
            if len(query) > 500 or len(tag_filter) > 100 or len(group_name) > 50:
                raise web.HTTPBadRequest(text="Keep notebook filters brief.")
            if status == "group" and not is_valid_entry_group(group_name):
                raise web.HTTPBadRequest(
                    text="Choose a group name using letters, numbers, spaces, hyphens, or underscores."
                )
            if query:
                entries = notes.search_entries(uid, query, limit=100)
            elif status == "pinned":
                entries = notes.list_pinned(uid, limit=100)
            elif status == "inbox":
                entries = notes.list_inbox(uid, limit=100)
            elif status == "group":
                entries = notes.list_by_group(uid, group_name, limit=100)
            else:
                entries = notes.list_recent(uid, n=100, include_archived=status != "active")
            if status == "group":
                entries = [
                    entry
                    for entry in entries
                    if entry.status == "active"
                    and str(entry.group or "").casefold() == group_name.casefold()
                ]
            elif status not in {"all", "pinned", "inbox"}:
                entries = [entry for entry in entries if entry.status == status]
            if tag_filter:
                entries = [
                    entry
                    for entry in entries
                    if tag_filter.casefold()
                    in {str(tag).casefold() for tag in (entry.tags or [])}
                ]
            all_entries = notes.list_recent(uid, n=1000, include_archived=True)
            from core.tags import get_user_tags
            saved_tags = await asyncio.to_thread(get_user_tags, uid)
            tags = sorted(
                {
                    str(tag).strip()
                    for tag in [
                        *saved_tags,
                        *[tag for entry in all_entries for tag in (entry.tags or [])],
                    ]
                    if str(tag).strip()
                },
                key=str.casefold,
            )
            groups = sorted(
                {
                    str(entry.group).strip()
                    for entry in all_entries
                    if entry.status == "active" and str(entry.group or "").strip()
                },
                key=str.casefold,
            )
            return web.json_response({
                "notes": [note_view(entry) for entry in entries],
                "count": len(entries),
                "tags": tags,
                "groups": groups,
            })

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
            group = clean_group(data.get("group")) if "group" in data else None
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
            allowed = {"title", "description", "items", "tags", "pinned", "group"}
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
            if "pinned" in data and type(data["pinned"]) is not bool:
                raise web.HTTPBadRequest(text="Choose whether the entry is pinned.")
            if "pinned" in data and not await asyncio.to_thread(notes.pin_entry, uid, note_id, data["pinned"]):
                raise web.HTTPNotFound(text="That note could not be updated.")
            if "group" in data and not await asyncio.to_thread(
                notes.set_group, uid, note_id, clean_group(data.get("group"))
            ):
                raise web.HTTPNotFound(text="That note could not be updated.")
            return web.json_response({"note": note_view(find(note_id, include_archived=False))})
        raise web.HTTPMethodNotAllowed(request.method, {"GET", "POST", "PATCH"})

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def checkins_api(request):
        """Start or answer the signed-in user's check-in in the browser."""
        uid, _ = await authenticated_account(request)
        from checkins.checkin_data_manager import is_user_checkins_enabled
        from checkins.checkin_service import get_checkin_start_status
        from communication.message_processing.conversation_flow_manager import (
            conversation_manager,
        )

        enabled = bool(await asyncio.to_thread(is_user_checkins_enabled, uid))

        # ERROR_HANDLING_EXCLUDE: Serializer is only used by this guarded route.
        def view(message, *, active, completed, completed_today, index, total, question_type):
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
            }

        snapshot = await asyncio.to_thread(conversation_manager.current_checkin_prompt, uid) or {}
        status = await asyncio.to_thread(get_checkin_start_status, uid) if enabled else None
        completed_today = (
            status is not None and status.already_completed_today and not snapshot
        )
        finished_today = (
            f"You've already completed a check-in today at {status.last_checkin_timestamp}. "
            "You can start a new check-in tomorrow."
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
            return web.json_response(view(
                message,
                active=bool(snapshot),
                completed=False,
                completed_today=completed_today,
                index=snapshot.get("index"),
                total=snapshot.get("total"),
                question_type=snapshot.get("question_type"),
            ))

        data = await body(request)
        action = data.get("action")
        if action == "start" and set(data) == {"action"}:
            if not enabled:
                return web.json_response(view(
                    "Check-ins are off. You can turn them on in Account.",
                    active=False, completed=True, completed_today=False, index=None, total=None,
                    question_type=None,
                ))
            if completed_today:
                return web.json_response(view(
                    finished_today,
                    active=False, completed=True, completed_today=True, index=None, total=None,
                    question_type=None,
                ))
            message, completed = await asyncio.to_thread(conversation_manager.start_checkin, uid)
        elif action == "answer" and set(data) == {"action", "answer"}:
            answer = data.get("answer")
            if not isinstance(answer, str) or not answer.strip() or len(answer.strip()) > 2000:
                raise web.HTTPBadRequest(text="Enter an answer, or skip this question.")
            result = await asyncio.to_thread(
                conversation_manager.answer_active_checkin, uid, answer.strip()
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
            raise web.HTTPBadRequest(text="Choose start, answer, skip, or cancel.")
        if not isinstance(message, str):
            message = "MHM could not continue that check-in. Please try again."
        latest = await asyncio.to_thread(conversation_manager.current_checkin_prompt, uid) or {}
        active = bool(latest) and not completed
        return web.json_response(view(
            message,
            active=active,
            completed=bool(completed),
            completed_today=False,
            index=latest.get("index") if active else None,
            total=latest.get("total") if active else None,
            question_type=latest.get("question_type") if active else None,
        ))

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def logout(request):
        """Revoke the current session cookie and clear it from the browser."""
        key = hashlib.sha256(request.cookies.get(COOKIE, "").encode()).hexdigest()
        session = sessions.pop(key, None)
        if session:
            uid = session[0]

            # ERROR_HANDLING_EXCLUDE: Logout cleanup runs inside the gateway route.
            def clear_open_checkin():
                """Drop an in-progress check-in so the next login starts fresh."""
                from communication.message_processing.conversation_flow_manager import (
                    conversation_manager,
                )
                from communication.message_processing.flows.flow_constants import (
                    FLOW_CHECKIN,
                )

                state = conversation_manager.user_states.get(uid)
                if isinstance(state, dict) and state.get("flow") == FLOW_CHECKIN:
                    conversation_manager._clear_flow_state(uid, mark_completion=False)

            await asyncio.to_thread(clear_open_checkin)
        response = web.json_response({"ok": True})
        response.del_cookie(COOKIE, path="/api/")
        return response

    app = web.Application(middlewares=[guard], client_max_size=32768)
    app.router.add_post("/api/auth/password", password_login)
    app.router.add_post("/api/auth/password/setup", password_setup)
    app.router.add_post("/api/auth/request-code", request_code)
    app.router.add_post("/api/auth/verify", verify)
    app.router.add_post("/api/auth/logout", logout)
    app.router.add_get("/api/auth/oauth/providers", oauth_providers)
    app.router.add_get("/api/auth/oauth/{provider}/start", oauth_start)
    app.router.add_get("/api/auth/oauth/{provider}/callback", oauth_callback)
    app.router.add_get("/api/auth/discord/start", discord_start)
    app.router.add_get("/api/auth/discord/callback", discord_callback)
    app.router.add_get("/api/account", account)
    app.router.add_post("/api/account/connections", account_connections)
    app.router.add_get("/api/account/export", account_export)
    app.router.add_get("/api/settings", settings)
    app.router.add_post("/api/settings", settings)
    app.router.add_get("/api/insights", insights)
    app.router.add_get("/api/health", health_settings)
    app.router.add_post("/api/health", health_settings)
    app.router.add_get("/api/tasks", tasks_api)
    app.router.add_post("/api/tasks", tasks_api)
    app.router.add_get("/api/task-templates", task_templates)
    app.router.add_post(
        "/api/tasks/bulk/{action:complete|restore|delete}", tasks_bulk
    )
    app.router.add_route("PATCH", "/api/tasks/{task_id}", tasks_api)
    app.router.add_route("DELETE", "/api/tasks/{task_id}", tasks_api)
    app.router.add_post(
        "/api/tasks/{task_id}/{action:complete|restore|snooze|skip|simplify}",
        tasks_api,
    )
    app.router.add_get("/api/messages", messages_api)
    app.router.add_post("/api/messages", messages_api)
    app.router.add_post("/api/actions", request_action)
    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def chat_api(request):
        """Send one signed-in message through the website conversation channel."""
        from core.web_chat import website_chat_reply

        uid, _current = await authenticated_account(request)
        data = await body(request)
        message = data.get("message")
        if set(data) != {"message"} or not isinstance(message, str):
            raise web.HTTPBadRequest(text="Enter a message to send.")
        message = message.strip()
        if not message or len(message) > 2000:
            raise web.HTTPBadRequest(text="Enter a message of up to 2000 characters.")
        throttle(("chat", uid), 30, 600)
        result = await asyncio.to_thread(website_chat_reply, uid, message)
        return web.json_response(result)

    # ERROR_HANDLING_EXCLUDE: Route failures are translated by the gateway middleware.
    async def chat_inbox(request):
        """Return outbound messages stored for the always-on website channel."""
        from communication.communication_channels.website.inbox import list_website_messages

        uid, _current = await authenticated_account(request)
        messages = await asyncio.to_thread(list_website_messages, uid)
        return web.json_response({"messages": messages})

    app.router.add_get("/api/checkins", checkins_api)
    app.router.add_post("/api/checkins", checkins_api)
    app.router.add_get("/api/chat", chat_inbox)
    app.router.add_post("/api/chat", chat_api)
    app.router.add_route("PATCH", "/api/messages/{category}/{message_id}", messages_api)
    app.router.add_route("DELETE", "/api/messages/{category}/{message_id}", messages_api)
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
            "home.html",
            "setup.html",
            "app.html",
            "tasks.html",
            "notes.html",
            "insights.html",
            "messages.html",
            "checkin.html",
            "privacy.html",
            "terms.html",
            "data.html",
            "styles.css",
            "mhm-logo.png",
            "script.js",
            "auth.js",
            "app.js",
            "home.js",
            "setup.js",
            "settings.js",
            "tasks.js",
            "notes.js",
            "insights.js",
            "messages.js",
            "checkin.js",
        }:
            raise web.HTTPNotFound(text="Page not found.")
        return web.FileResponse(root / name)

    app.router.add_get("/", asset)
    app.router.add_get("/{name}", asset)
    return app
