"""
Google OAuth 2.0 for Google Health API (read-only).

One-time browser connect + automated refresh thereafter.
"""

from __future__ import annotations

import os
import threading
import urllib.parse
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import requests

from core.config import (
    GOOGLE_HEALTH_CLIENT_ID,
    GOOGLE_HEALTH_CLIENT_SECRET,
    GOOGLE_HEALTH_OAUTH_CALLBACK_TIMEOUT_SECONDS,
    GOOGLE_HEALTH_REDIRECT_URI,
    GOOGLE_HEALTH_TOKEN_REFRESH_MARGIN_MINUTES,
    get_google_health_oauth_scopes,
)
from core.error_handling import CommunicationError, handle_errors
from core.logger import get_component_logger
from core.time_utilities import now_datetime_full, now_timestamp_full, parse_timestamp_full
from integrations.google_health.data_handlers import load_auth, save_auth

logger = get_component_logger("google_health")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


def _testing_mode() -> bool:
    return os.getenv("MHM_TESTING") == "1"


@handle_errors("building Google Health authorization URL", default_return="")
def build_authorization_url(state: str = "") -> str:
    """Build OAuth authorization URL (never include include_granted_scopes)."""
    params = {
        "client_id": GOOGLE_HEALTH_CLIENT_ID,
        "redirect_uri": GOOGLE_HEALTH_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(get_google_health_oauth_scopes()),
        "access_type": "offline",
        "prompt": "consent",
    }
    if state:
        params["state"] = state
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


@handle_errors("exchanging authorization code", default_return=None)
def exchange_code_for_tokens(code: str) -> dict[str, Any] | None:
    """Exchange OAuth authorization code for access + refresh tokens."""
    if _testing_mode():
        logger.info("Skipping real token exchange in testing mode")
        return None

    response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": GOOGLE_HEALTH_CLIENT_ID,
            "client_secret": GOOGLE_HEALTH_CLIENT_SECRET,
            "redirect_uri": GOOGLE_HEALTH_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    if response.status_code != 200:
        logger.error(
            f"Token exchange failed with status {response.status_code} (body redacted)"
        )
        raise CommunicationError("Google Health token exchange failed")
    return response.json()


@handle_errors("refreshing Google Health access token", default_return=None)
def refresh_access_token(refresh_token: str) -> dict[str, Any] | None:
    """Refresh an access token using a stored refresh token."""
    if _testing_mode():
        logger.info("Skipping real token refresh in testing mode")
        return None

    response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": GOOGLE_HEALTH_CLIENT_ID,
            "client_secret": GOOGLE_HEALTH_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    if response.status_code != 200:
        logger.error(
            f"Token refresh failed with status {response.status_code} (body redacted)"
        )
        return None
    return response.json()


def _expires_at_from_token_response(token_data: dict[str, Any]) -> str:
    expires_in = token_data.get("expires_in")
    if isinstance(expires_in, (int, float)):
        when = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
        return when.strftime("%Y-%m-%d %H:%M:%S")
    return ""


def _token_needs_refresh(auth: dict[str, Any]) -> bool:
    expires_at = auth.get("expires_at") or ""
    parsed = parse_timestamp_full(expires_at) if expires_at else None
    if parsed is None:
        return True
    margin = timedelta(minutes=GOOGLE_HEALTH_TOKEN_REFRESH_MARGIN_MINUTES)
    return parsed - now_datetime_full() <= margin


@handle_errors("ensuring valid access token for user", default_return=None)
def ensure_valid_access_token(user_id: str) -> str | None:
    """
    Return a valid access token, refreshing automatically when needed.

    Updates google_health_auth.json on refresh.
    """
    auth = load_auth(user_id)
    if not auth:
        return None

    access = auth.get("access_token") or ""
    refresh = auth.get("refresh_token") or ""

    if access and not _token_needs_refresh(auth):
        return access

    if not refresh:
        logger.warning(f"No refresh token for user {user_id} — reconnect required")
        return None

    token_data = refresh_access_token(refresh)
    if not token_data:
        return None

    now = now_timestamp_full()
    auth["access_token"] = token_data.get("access_token", "")
    auth["token_type"] = token_data.get("token_type", "Bearer")
    auth["expires_at"] = _expires_at_from_token_response(token_data)
    auth["last_refresh_at"] = now
    if token_data.get("refresh_token"):
        auth["refresh_token"] = token_data["refresh_token"]
    save_auth(user_id, auth)
    logger.info(f"Refreshed Google Health access token for user {user_id}")
    return auth.get("access_token") or None


@handle_errors("persisting OAuth tokens for user", default_return=False)
def save_tokens_for_user(user_id: str, token_data: dict[str, Any]) -> bool:
    """Store token response after initial connect."""
    now = now_timestamp_full()
    auth = load_auth(user_id) or {}
    auth.update(
        {
            "access_token": token_data.get("access_token", ""),
            "refresh_token": token_data.get("refresh_token", auth.get("refresh_token", "")),
            "token_type": token_data.get("token_type", "Bearer"),
            "expires_at": _expires_at_from_token_response(token_data),
            "scopes": get_google_health_oauth_scopes(),
            "connected_at": auth.get("connected_at") or now,
            "last_refresh_at": now,
        }
    )
    return save_auth(user_id, auth)


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Single-use OAuth callback handler."""

    auth_code: str | None = None
    error_message: str | None = None

    def log_message(self, format: str, *args: Any) -> None:
        logger.debug(f"OAuth callback: {format % args}")

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "error" in params:
            _OAuthCallbackHandler.error_message = params["error"][0]
            self._respond(400, "Authorization failed. You can close this window.")
            return
        code = params.get("code", [None])[0]
        if not code:
            self._respond(400, "Missing authorization code.")
            return
        _OAuthCallbackHandler.auth_code = code
        self._respond(200, "Google Health connected. You can close this window.")

    def _respond(self, status: int, message: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        body = f"<html><body><p>{message}</p></body></html>"
        self.wfile.write(body.encode("utf-8"))


@handle_errors("running OAuth connect flow", default_return=None)
def run_oauth_connect_flow(
    user_id: str,
    *,
    on_complete: Callable[[str], None] | None = None,
) -> dict[str, Any] | None:
    """
    Start local callback server, return authorization URL, wait for code, exchange tokens.

    Blocks until callback or timeout. Intended for one-time connect.
    """
    if _testing_mode():
        logger.info(f"OAuth connect flow skipped in testing mode for user {user_id}")
        return None

    _OAuthCallbackHandler.auth_code = None
    _OAuthCallbackHandler.error_message = None

    redirect = urllib.parse.urlparse(GOOGLE_HEALTH_REDIRECT_URI)
    port = redirect.port or 8765
    server = HTTPServer(("127.0.0.1", port), _OAuthCallbackHandler)

    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()

    auth_url = build_authorization_url(state=user_id)
    if on_complete:
        on_complete(auth_url)

    thread.join(timeout=GOOGLE_HEALTH_OAUTH_CALLBACK_TIMEOUT_SECONDS)
    server.server_close()

    if _OAuthCallbackHandler.error_message:
        raise CommunicationError(
            f"Google OAuth error: {_OAuthCallbackHandler.error_message}"
        )
    code = _OAuthCallbackHandler.auth_code
    if not code:
        raise CommunicationError("Google OAuth timed out waiting for callback")

    token_data = exchange_code_for_tokens(code)
    if not token_data:
        raise CommunicationError("Failed to exchange authorization code")

    save_tokens_for_user(user_id, token_data)
    return token_data
