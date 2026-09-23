"""Browser auth checks with isolated accounts and captured email only."""

from contextlib import asynccontextmanager
from urllib.parse import parse_qs, urlsplit

import pytest
import pytest_asyncio
from aiohttp import CookieJar
from aiohttp.test_utils import TestClient, TestServer

from core import web_account_service
from core.error_handling import ConfigurationError
from core.web_account_service import (
    OAuthIdentity,
    create_web_app,
    MHMAccounts,
    _account_features,
    _feature_enabled,
    _oauth_email_verified,
    _setup_flags,
    _signed_in_path,
)

pytestmark = [pytest.mark.unit, pytest.mark.user, pytest.mark.asyncio]
ORIGIN = "http://localhost:8080"


class Accounts:
    def __init__(self):
        self.users: dict[str, dict] = {
            "existing": {
                "internal_username": "river",
                "email": "river@example.com",
                "account_status": "active",
                "timezone": "America/Regina",
            }
        }
        self.contexts: dict[str, dict] = {
            "existing": {"preferred_name": "River"}
        }

    def by_email(self, email):
        matches = [
            (uid, user)
            for uid, user in self.users.items()
            if user["email"].casefold() == email.casefold()
        ]
        return matches[0] if len(matches) == 1 else None

    def email_exists(self, email):
        return any(
            user["email"].casefold() == email.casefold() for user in self.users.values()
        )

    def get(self, uid):
        return self.users.get(uid, {})

    def create(self, email, preferred_name, timezone, password_hash):
        uid = f"new-{len(self.users)}"
        self.users[uid] = {
            "email": email,
            "internal_username": f"mhm_{uid}",
            "timezone": timezone,
            "account_status": "active",
            "password_hash": password_hash,
        }
        self.contexts[uid] = {"preferred_name": preferred_name}
        return uid

    def documents(self, uid):
        return {
            "account": self.users.get(uid, {}),
            "context": self.contexts.get(uid, {}),
        }

    def set_password(self, uid, password_hash):
        self.users[uid]["password_hash"] = password_hash
        return True

    def by_oauth(self, provider, subject):
        matches = [
            (uid, user)
            for uid, user in self.users.items()
            if user.get("oauth_identities", {}).get(provider) == subject
        ]
        return matches[0] if len(matches) == 1 else None

    def link_oauth(self, uid, provider, subject):
        for other_uid, user in self.users.items():
            if other_uid != uid and user.get("oauth_identities", {}).get(provider) == subject:
                return "already_linked"
        identities = dict(self.users[uid].get("oauth_identities", {}))
        if identities.get(provider) not in {None, subject}:
            return "different_linked"
        identities[provider] = subject
        self.users[uid]["oauth_identities"] = identities
        return "linked"

    def link_discord(self, uid, discord_user_id, discord_username):
        for other_uid, user in self.users.items():
            if other_uid != uid and user.get("discord_user_id") == discord_user_id:
                return "already_linked"
        self.users[uid]["discord_user_id"] = discord_user_id
        self.users[uid]["discord_username"] = discord_username
        return "linked"

    def unlink_oauth(self, uid, provider):
        identities = dict(self.users[uid].get("oauth_identities", {}))
        identities.pop(provider, None)
        self.users[uid]["oauth_identities"] = identities
        return True

    def unlink_discord(self, uid):
        self.users[uid]["discord_user_id"] = ""
        self.users[uid]["discord_username"] = ""
        return True


@asynccontextmanager
async def web_client(app, **kwargs):
    """Yield an aiohttp TestClient whose server shutdown cannot block for 60s."""
    server = TestServer(app)
    await server.start_server(shutdown_timeout=1)
    client = TestClient(server, **kwargs)
    try:
        await client.start_server()
        yield client
    finally:
        await client.close()


@pytest_asyncio.fixture
async def gateway():
    accounts, sent, now = Accounts(), [], [100.0]
    app = create_web_app(
        accounts=accounts,
        mailer=lambda email, code: sent.append((email, code)),
        origin=ORIGIN,
        proxy_secret="",
        clock=lambda: now[0],
    )
    async with web_client(app, cookie_jar=CookieJar(unsafe=True)) as client:
        yield client, accounts, sent, now


async def request_code(
    client, email="river@example.com", mode="login", preferred_name=None
):
    return await client.post(
        "/api/auth/request-code",
        json={
            "email": email,
            "mode": mode,
            "preferred_name": (
                preferred_name
                if preferred_name is not None
                else ("Brook" if mode == "create" else "")
            ),
            "timezone": "America/Regina",
        },
        headers={"Origin": ORIGIN},
    )


async def verify(client, token, code, password=None):
    payload = {"challenge": token, "code": code}
    if password is not None:
        payload["password"] = password
    return await client.post(
        "/api/auth/verify",
        json=payload,
        headers={"Origin": ORIGIN},
    )


async def test_web_client_uses_a_short_server_shutdown_timeout():
    app = create_web_app(
        accounts=Accounts(),
        mailer=lambda email, code: None,
        origin=ORIGIN,
        proxy_secret="",
    )
    async with web_client(app) as client:
        runner = client.server.runner
        assert runner is not None
        assert runner._shutdown_timeout == 1


async def test_existing_login_session_logout_and_replay(gateway):
    client, _, sent, _ = gateway
    assert (await client.get("/api/account")).status == 401


async def test_account_needs_setup_until_a_support_feature_is_enabled(gateway):
    client, accounts, sent, _ = gateway
    token = (await (await request_code(client)).json())["challenge"]
    assert (await verify(client, token, sent[-1][1])).status == 200
    account = await (await client.get("/api/account")).json()
    assert account["needs_setup"] is True
    assert account["messages_enabled"] is False
    assert account["tasks_enabled"] is False
    assert account["checkins_enabled"] is False
    accounts.users["existing"]["features"] = {"task_management": "enabled"}
    account = await (await client.get("/api/account")).json()
    assert account["needs_setup"] is False
    assert account["messages_enabled"] is False
    assert account["tasks_enabled"] is True
    assert account["checkins_enabled"] is False
    accounts.users["existing"]["features"] = {"checkins": "enabled"}
    account = await (await client.get("/api/account")).json()
    assert account["needs_setup"] is False
    assert account["tasks_enabled"] is False
    assert account["checkins_enabled"] is True
    accounts.users["existing"]["features"] = {"automated_messages": "enabled"}
    account = await (await client.get("/api/account")).json()
    assert account["needs_setup"] is False
    assert account["messages_enabled"] is True
    assert account["tasks_enabled"] is False
    assert account["checkins_enabled"] is False


async def test_setup_helpers_use_safe_defaults_for_malformed_accounts():
    class Broken(dict):
        def get(self, *args, **kwargs):
            raise RuntimeError("broken account document")

    assert _account_features(None) == {}
    assert _account_features(Broken()) == {}
    assert _feature_enabled(["not-a-map"], "checkins") is False
    flags = _setup_flags({"features": ["bad"]})
    assert flags["needs_setup"] is True
    assert flags["messages_enabled"] is False
    assert _signed_in_path({"features": ["bad"]}) == "/setup.html"
    assert _signed_in_path({}, linking=True) == "/app.html"


async def test_connected_accounts_can_be_disconnected_without_removing_last_sign_in(
    gateway,
):
    client, accounts, sent, _ = gateway
    accounts.users["existing"].update(
        password_hash="saved",
        oauth_identities={"google": "google-subject", "facebook": "facebook-subject"},
        discord_user_id="discord-1",
        discord_username="river",
    )
    token = (await (await request_code(client)).json())["challenge"]
    assert (await verify(client, token, sent[-1][1])).status == 200

    disconnected = await client.post(
        "/api/account/connections",
        json={"provider": "google"},
        headers={"Origin": ORIGIN},
    )
    assert disconnected.status == 200
    assert accounts.users["existing"]["oauth_identities"] == {
        "facebook": "facebook-subject"
    }
    discord = await client.post(
        "/api/account/connections",
        json={"provider": "discord"},
        headers={"Origin": ORIGIN},
    )
    assert discord.status == 200
    assert accounts.users["existing"]["discord_user_id"] == ""

    accounts.users["existing"].pop("password_hash")
    last = await client.post(
        "/api/account/connections",
        json={"provider": "facebook"},
        headers={"Origin": ORIGIN},
    )
    assert last.status == 400
    assert accounts.users["existing"]["oauth_identities"] == {
        "facebook": "facebook-subject"
    }


async def test_account_export_strips_authentication_secrets(gateway, monkeypatch):
    from storage import user_data_operations
    from tasks import task_service
    from notebook import notebook_data_manager

    client, _, sent, _ = gateway
    monkeypatch.setattr(
        user_data_operations,
        "export_user_data",
        lambda uid, export_format: {
            "user_id": uid,
            "profile": {"email": "river@example.com", "password_hash": "secret"},
            "nested": [{"password_hash": "also-secret", "safe": True}],
        },
    )
    monkeypatch.setattr(task_service, "load_active_tasks", lambda uid: [])
    monkeypatch.setattr(task_service, "load_completed_tasks", lambda uid: [])
    monkeypatch.setattr(
        notebook_data_manager,
        "list_recent",
        lambda uid, n=10000, include_archived=True: [],
    )
    token = (await (await request_code(client)).json())["challenge"]
    assert (await verify(client, token, sent[-1][1])).status == 200
    response = await client.get("/api/account/export")
    assert response.status == 200
    assert response.headers["Content-Disposition"] == (
        'attachment; filename="mhm-data.json"'
    )
    exported = await response.json()
    assert exported["profile"] == {"email": "river@example.com"}
    assert exported["nested"] == [{"safe": True}]
    assert exported["tasks"] == {"active": [], "completed": []}
    assert exported["notebook"] == []


async def test_insights_are_authenticated_bounded_and_json_safe(gateway, monkeypatch):
    from checkins.checkin_analytics import CheckinAnalytics

    client, _, sent, _ = gateway
    assert (await client.get("/api/insights")).status == 401
    token = (await (await request_code(client)).json())["challenge"]
    assert (await verify(client, token, sent[-1][1])).status == 200
    monkeypatch.setattr(CheckinAnalytics, "get_available_data_types", lambda self, uid, days: ["mood"])
    monkeypatch.setattr(CheckinAnalytics, "get_wellness_score", lambda self, uid, days: {"score": 4.2})
    monkeypatch.setattr(CheckinAnalytics, "get_mood_trends", lambda self, uid, days: {"average": 4})
    monkeypatch.setattr(CheckinAnalytics, "get_energy_trends", lambda self, uid, days: {})
    monkeypatch.setattr(CheckinAnalytics, "get_habit_analysis", lambda self, uid, days: {})
    monkeypatch.setattr(CheckinAnalytics, "get_sleep_analysis", lambda self, uid, days: {})
    monkeypatch.setattr(CheckinAnalytics, "get_quantitative_summaries", lambda self, uid, days: {})
    monkeypatch.setattr(CheckinAnalytics, "get_completion_rate", lambda self, uid, days: {"rate": 50})
    monkeypatch.setattr(CheckinAnalytics, "get_checkin_history", lambda self, uid, days: [{"when": object()}])

    assert (await client.get("/api/insights?days=31")).status == 400
    response = await client.get("/api/insights?days=14")
    assert response.status == 200
    insights = await response.json()
    assert insights["days"] == 14
    assert insights["wellness"] == {"score": 4.2}
    assert isinstance(insights["history"][0]["when"], str)
    token = (await (await request_code(client)).json())["challenge"]
    result = await verify(client, token, sent[-1][1])
    assert result.status == 200
    assert "HttpOnly" in result.headers["Set-Cookie"]
    assert "SameSite=Lax" in result.headers["Set-Cookie"]
    assert result.headers["Cache-Control"] == "no-store"
    profile = await (await client.get("/api/account")).json()
    assert profile["preferred_name"] == "River"
    assert profile["needs_setup"] is True
    assert profile["messages_enabled"] is False
    assert profile["checkins_enabled"] is False
    assert "username" not in profile
    assert "user_id" not in profile
    assert (await verify(client, token, sent[-1][1])).status == 401
    assert (
        await client.post("/api/auth/logout", json={}, headers={"Origin": ORIGIN})
    ).status == 200
    assert (await client.get("/api/account")).status == 401


async def test_creation_waits_for_verified_email(gateway):
    client, accounts, sent, _ = gateway
    token = (await (await request_code(client, "brook@example.com", "create")).json())[
        "challenge"
    ]
    assert not accounts.email_exists("brook@example.com")
    assert (await verify(client, token, sent[-1][1], "a secure password phrase")).status == 200
    assert accounts.email_exists("brook@example.com")
    assert accounts.users["new-1"]["password_hash"].startswith("$mhm$scrypt$")
    assert "a secure password phrase" not in accounts.users["new-1"]["password_hash"]
    account = await (await client.get("/api/account")).json()
    assert account["preferred_name"] == "Brook"
    assert account["password_change_requires_current"] is True
    replacement = "a replacement password phrase"
    missing_current = await client.post(
        "/api/auth/password/setup",
        json={"password": replacement},
        headers={"Origin": ORIGIN},
    )
    assert missing_current.status == 401
    changed = await client.post(
        "/api/auth/password/setup",
        json={
            "current_password": "a secure password phrase",
            "password": replacement,
        },
        headers={"Origin": ORIGIN},
    )
    assert changed.status == 200


async def test_password_login_and_authenticated_password_setup(gateway):
    client, accounts, sent, _ = gateway
    token = (await (await request_code(client)).json())["challenge"]
    assert (await verify(client, token, sent[-1][1])).status == 200
    account = await (await client.get("/api/account")).json()
    assert account["password_set"] is False
    assert account["password_change_requires_current"] is False

    phrase = "a memorable password phrase"
    setup = await client.post(
        "/api/auth/password/setup",
        json={"password": phrase},
        headers={"Origin": ORIGIN},
    )
    assert setup.status == 200
    assert accounts.users["existing"]["password_hash"].startswith("$mhm$scrypt$")
    await client.post("/api/auth/logout", json={}, headers={"Origin": ORIGIN})

    bad = await client.post(
        "/api/auth/password",
        json={"email": "river@example.com", "password": "the wrong password"},
        headers={"Origin": ORIGIN},
    )
    assert bad.status == 401
    login = await client.post(
        "/api/auth/password",
        json={"email": "RIVER@example.com", "password": phrase},
        headers={"Origin": ORIGIN},
    )
    assert login.status == 200
    assert "HttpOnly" in login.headers["Set-Cookie"]
    account = await (await client.get("/api/account")).json()
    assert account["password_change_requires_current"] is True

    replacement = "a newer memorable password phrase"
    missing_current = await client.post(
        "/api/auth/password/setup",
        json={"password": replacement},
        headers={"Origin": ORIGIN},
    )
    assert missing_current.status == 401
    changed = await client.post(
        "/api/auth/password/setup",
        json={"current_password": phrase, "password": replacement},
        headers={"Origin": ORIGIN},
    )
    assert changed.status == 200

    await client.post("/api/auth/logout", json={}, headers={"Origin": ORIGIN})
    token = (await (await request_code(client)).json())["challenge"]
    assert (await verify(client, token, sent[-1][1])).status == 200
    account = await (await client.get("/api/account")).json()
    assert account["password_change_requires_current"] is False
    reset = await client.post(
        "/api/auth/password/setup",
        json={"password": "reset after verified email code"},
        headers={"Origin": ORIGIN},
    )
    assert reset.status == 200


async def test_password_validation_and_unknown_account_are_safe(gateway):
    client, _, _, _ = gateway
    short = await client.post(
        "/api/auth/password",
        json={"email": "river@example.com", "password": "too-short"},
        headers={"Origin": ORIGIN},
    )
    assert short.status == 400
    unknown = await client.post(
        "/api/auth/password",
        json={"email": "missing@example.com", "password": "a valid length password"},
        headers={"Origin": ORIGIN},
    )
    assert unknown.status == 401
    assert "email or password" in (await unknown.json())["error"]


async def test_forgot_password_verifies_email_replaces_password_and_logs_in(gateway):
    client, accounts, sent, _ = gateway
    old_password = "the original memorable password"
    accounts.users["existing"]["password_hash"] = web_account_service._password_hash(
        old_password
    )

    response = await request_code(client, mode="reset")
    assert response.status == 200
    token = (await response.json())["challenge"]
    new_password = "a newly recovered password phrase"
    reset = await verify(client, token, sent[-1][1], new_password)

    assert reset.status == 200
    assert "HttpOnly" in reset.headers["Set-Cookie"]
    assert accounts.users["existing"]["password_hash"].startswith("$mhm$scrypt$")
    assert new_password not in accounts.users["existing"]["password_hash"]
    assert (await client.get("/api/account")).status == 200

    await client.post("/api/auth/logout", json={}, headers={"Origin": ORIGIN})
    old_login = await client.post(
        "/api/auth/password",
        json={"email": "river@example.com", "password": old_password},
        headers={"Origin": ORIGIN},
    )
    new_login = await client.post(
        "/api/auth/password",
        json={"email": "river@example.com", "password": new_password},
        headers={"Origin": ORIGIN},
    )
    assert old_login.status == 401
    assert new_login.status == 200


async def test_creation_rechecks_duplicates_after_verification(gateway):
    client, accounts, sent, _ = gateway
    token = (await (await request_code(client, "brook@example.com", "create")).json())[
        "challenge"
    ]
    accounts.users["racing"] = {
        "internal_username": "mhm_racing",
        "email": "brook@example.com",
        "account_status": "active",
    }
    assert (await verify(client, token, sent[-1][1], "a secure password phrase")).status == 409
    assert len(accounts.users) == 2


async def test_unknown_email_and_duplicate_signup_are_not_signed_in(gateway):
    client, _, sent, _ = gateway
    for email, mode in [
        ("missing@example.com", "login"),
        ("missing@example.com", "reset"),
        ("river@example.com", "create"),
    ]:
        response = await request_code(client, email, mode)
        assert response.status == 200
        token = (await response.json())["challenge"]
        assert (await verify(client, token, "000000")).status == 401
    assert not sent


async def test_codes_expire_and_lock_after_five_wrong_attempts(gateway):
    client, _, sent, now = gateway
    token = (await (await request_code(client)).json())["challenge"]
    code = sent[-1][1]
    wrong = "111111" if code != "111111" else "222222"
    for _ in range(5):
        assert (await verify(client, token, wrong)).status == 401
    assert (await verify(client, token, code)).status == 401
    token = (await (await request_code(client)).json())["challenge"]
    now[0] += 601
    assert (await verify(client, token, sent[-1][1])).status == 401


async def test_suspension_revokes_existing_session(gateway):
    client, accounts, sent, _ = gateway
    token = (await (await request_code(client)).json())["challenge"]
    assert (await verify(client, token, sent[-1][1])).status == 200
    accounts.users["existing"]["account_status"] = "suspended"
    assert (await client.get("/api/account")).status == 401


async def test_session_expires(gateway):
    client, _, sent, now = gateway
    token = (await (await request_code(client)).json())["challenge"]
    assert (await verify(client, token, sent[-1][1])).status == 200
    now[0] += 43201
    assert (await client.get("/api/account")).status == 401


async def test_signup_preferred_name_is_optional_and_bounded(gateway):
    client, _, _, _ = gateway
    assert (
        await request_code(
            client,
            "long-name@example.com",
            "create",
            preferred_name="x" * 101,
        )
    ).status == 400
    assert (
        await request_code(
            client, "no-name@example.com", "create", preferred_name=""
        )
    ).status == 200


async def test_csrf_validation_rate_limits_and_static_allowlist(gateway):
    client, _, sent, now = gateway
    assert (await client.post("/api/auth/request-code", json={})).status == 403
    assert (
        await client.post(
            "/api/auth/request-code",
            json={},
            headers={"Origin": "https://other.example"},
        )
    ).status == 403
    assert (await request_code(client, "invalid")).status == 400
    for _ in range(3):
        assert (await request_code(client)).status == 200
    assert (await request_code(client)).status == 429
    now[0] += 601
    assert (await request_code(client)).status == 200
    assert len(sent) == 4
    assert (await client.get("/login.html")).status == 200
    assert (await client.get("/home.html")).status == 200
    assert (await client.get("/home.js")).status == 200
    assert (await client.get("/setup.html")).status == 200
    assert (await client.get("/setup.js")).status == 200
    assert (await client.get("/tasks.js")).status == 200
    assert (await client.get("/tasks.html")).status == 200
    assert (await client.get("/notes.html")).status == 200
    assert (await client.get("/notes.js")).status == 200
    assert (await client.get("/checkin.html")).status == 200
    assert (await client.get("/checkin.js")).status == 200
    assert (await client.get("/privacy.html")).status == 200
    assert (await client.get("/terms.html")).status == 200
    assert (await client.get("/data.html")).status == 200
    logo = await client.get("/mhm-logo.png")
    assert logo.status == 200
    assert logo.content_type == "image/png"
    assert (await logo.read()).startswith(b"\x89PNG\r\n\x1a\n")
    assert (await client.get("/other-image.png")).status == 404
    assert (await client.get("/wrangler.jsonc")).status == 404
    assert (await client.get("/worker.mjs")).status == 404


async def test_production_requires_authenticated_proxy_and_secure_cookie():
    origin, secret, sent = "https://mhm.example", "s" * 32, []
    app = create_web_app(
        accounts=Accounts(),
        mailer=lambda email, code: sent.append(code),
        origin=origin,
        proxy_secret=secret,
    )
    async with web_client(app) as client:
        assert (await client.get("/api/account")).status == 403
        response = await client.post(
            "/api/auth/request-code",
            json={"email": "river@example.com", "mode": "login"},
            headers={"Origin": origin, "X-MHM-Proxy-Secret": secret},
        )
        token = (await response.json())["challenge"]
        response = await client.post(
            "/api/auth/verify",
            json={"challenge": token, "code": sent[0]},
            headers={"Origin": origin, "X-MHM-Proxy-Secret": secret},
        )
        assert response.status == 200
        assert "Secure" in response.headers["Set-Cookie"]
    with pytest.raises(ConfigurationError):
        create_web_app(origin=origin, proxy_secret="")


async def test_product_adapter_uses_shared_creation_and_casefolded_lookup(monkeypatch):
    import core

    captured = []
    monkeypatch.setattr(
        core, "create_new_user", lambda data: captured.append(data) or "new-id"
    )
    adapter = MHMAccounts()
    assert adapter.create(
        "new@example.com",
        "New User",
        "America/Regina",
        "$mhm$scrypt$16384$8$1$salt$digest",
    ) == "new-id"
    assert captured[0]["channel"] == {"type": "email"}
    assert captured[0]["preferred_name"] == "New User"
    assert "internal_username" not in captured[0]
    assert not captured[0]["messages_enabled"]
    monkeypatch.setattr(
        adapter,
        "all",
        lambda: [("one", {"email": "River@Example.com", "internal_username": "River"})],
    )
    match = adapter.by_email("river@example.com")
    assert match is not None
    assert match[0] == "one"
    monkeypatch.setattr(
        adapter,
        "all",
        lambda: [
            ("one", {"email": "same@example.com"}),
            ("two", {"email": "same@example.com"}),
        ],
    )
    assert adapter.by_email("same@example.com") is None


async def test_duplicate_email_cannot_be_disambiguated_by_preferred_name(gateway):
    client, accounts, sent, _ = gateway
    accounts.users["second"] = {
        "email": "river@example.com",
        "internal_username": "brook",
        "account_status": "active",
        "timezone": "America/Regina",
    }
    response = await request_code(client)
    assert response.status == 200
    assert not sent
    token = (await (await request_code(client, preferred_name="Brook")).json())["challenge"]
    assert not sent
    assert (await client.get("/api/account")).status == 401
    assert (await verify(client, token, "000000")).status == 401


async def test_suspended_accounts_receive_no_code(gateway):
    client, accounts, sent, _ = gateway
    accounts.users["existing"]["account_status"] = "suspended"
    assert (await request_code(client)).status == 200
    assert not sent


async def test_smtp_failure_reports_delivery_problem_without_leaking_details():
    import smtplib

    def fail(email, code):
        raise smtplib.SMTPAuthenticationError(535, b"private diagnostic details")

    app = create_web_app(
        accounts=Accounts(), mailer=fail, origin=ORIGIN, proxy_secret=""
    )
    async with web_client(app) as client:
        response = await request_code(client)
        assert response.status == 503
        message = (await response.json())["error"]
        assert "couldn't send your code" in message
        assert "private diagnostic details" not in message


@pytest.mark.parametrize("provider", ["google", "facebook"])
async def test_configured_social_provider_links_by_verified_email_and_logs_in(
    gateway, monkeypatch, provider
):
    client, accounts, sent, _ = gateway
    import core.web_account_service as service

    prefix = provider.upper()
    monkeypatch.setattr(service.config, f"{prefix}_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setattr(service.config, f"{prefix}_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setattr(service.config, f"{prefix}_OAUTH_REDIRECT_URI", "")
    calls = []

    async def identity(selected_provider, code, **kwargs):
        calls.append((selected_provider, code, kwargs))
        return OAuthIdentity(f"{provider}-subject", "river@example.com", True, "River")

    await client.close()
    app = service.create_web_app(
        accounts=accounts,
        mailer=lambda email, code: sent.append((email, code)),
        origin=ORIGIN,
        proxy_secret="",
        oauth_identity=identity,
    )
    async with web_client(app, cookie_jar=CookieJar(unsafe=True)) as client:
        providers = await (await client.get("/api/auth/oauth/providers")).json()
        assert providers["providers"][provider] is True
        start = await client.get(f"/api/auth/oauth/{provider}/start")
        assert start.status == 200
        authorize_url = (await start.json())["url"]
        state = parse_qs(urlsplit(authorize_url).query)["state"][0]
        callback = await client.get(
            f"/api/auth/oauth/{provider}/callback?code=oauth-code&state={state}",
            allow_redirects=False,
        )
        assert callback.status == 302
        assert callback.headers["Location"].endswith(
            f"/setup.html?social={provider}-connected"
        )
        assert accounts.users["existing"]["oauth_identities"][provider] == f"{provider}-subject"
        assert calls[0][0:2] == (provider, "oauth-code")
        assert (await client.get("/api/account")).status == 200


async def test_social_sign_in_does_not_link_unverified_or_conflicting_identity(
    gateway, monkeypatch
):
    client, accounts, sent, _ = gateway
    import core.web_account_service as service

    monkeypatch.setattr(service.config, "GOOGLE_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setattr(service.config, "GOOGLE_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setattr(service.config, "GOOGLE_OAUTH_REDIRECT_URI", "")

    async def identity(provider, code, **kwargs):
        return OAuthIdentity("unlinked-subject", "river@example.com", False)

    await client.close()
    app = service.create_web_app(
        accounts=accounts,
        mailer=lambda email, code: sent.append((email, code)),
        origin=ORIGIN,
        proxy_secret="",
        oauth_identity=identity,
    )
    async with web_client(app, cookie_jar=CookieJar(unsafe=True)) as client:
        url = (await (await client.get("/api/auth/oauth/google/start")).json())["url"]
        state = parse_qs(urlsplit(url).query)["state"][0]
        callback = await client.get(
            f"/api/auth/oauth/google/callback?code=oauth-code&state={state}",
            allow_redirects=False,
        )
        assert callback.headers["Location"].endswith("/login.html?social=not-linked")
        assert "oauth_identities" not in accounts.users["existing"]
        assert (await client.get("/api/account")).status == 401


async def test_google_sign_in_creates_an_account_when_the_verified_email_is_new(
    gateway, monkeypatch
):
    client, accounts, sent, _ = gateway
    import core.web_account_service as service

    monkeypatch.setattr(service.config, "GOOGLE_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setattr(service.config, "GOOGLE_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setattr(service.config, "GOOGLE_OAUTH_REDIRECT_URI", "")

    async def identity(provider, code, **kwargs):
        return OAuthIdentity("new-google-subject", "new@example.com", True, "New Person")

    await client.close()
    app = service.create_web_app(
        accounts=accounts,
        mailer=lambda email, code: sent.append((email, code)),
        origin=ORIGIN,
        proxy_secret="",
        oauth_identity=identity,
    )
    async with web_client(app, cookie_jar=CookieJar(unsafe=True)) as client:
        url = (
            await (
                await client.get(
                    "/api/auth/oauth/google/start?timezone=America/Denver"
                )
            ).json()
        )["url"]
        state = parse_qs(urlsplit(url).query)["state"][0]
        callback = await client.get(
            f"/api/auth/oauth/google/callback?code=oauth-code&state={state}",
            allow_redirects=False,
        )
        assert callback.status == 302
        assert callback.headers["Location"].endswith("/setup.html?social=google-connected")
        created = accounts.by_email("new@example.com")
        assert created is not None
        assert created[0] != "existing"
        assert created[1]["timezone"] == "America/Denver"
        assert created[1]["password_hash"] == ""
        assert created[1]["oauth_identities"]["google"] == "new-google-subject"
        assert accounts.contexts[created[0]]["preferred_name"] == "New Person"
        assert (await client.get("/api/account")).status == 200


def test_facebook_email_is_trusted_only_when_facebook_shares_one():
    assert _oauth_email_verified("facebook", {"email": "person@example.com"}) is True
    assert _oauth_email_verified("facebook", {"email": "  "}) is False
    assert _oauth_email_verified("google", {"email": "person@example.com", "email_verified": True}) is True
    assert _oauth_email_verified("google", {"email": "person@example.com"}) is False


async def test_facebook_sign_in_creates_an_account_when_an_email_is_shared(
    gateway, monkeypatch
):
    client, accounts, sent, _ = gateway
    import core.web_account_service as service

    monkeypatch.setattr(service.config, "FACEBOOK_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setattr(service.config, "FACEBOOK_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setattr(service.config, "FACEBOOK_OAUTH_REDIRECT_URI", "")

    async def identity(provider, code, **kwargs):
        return OAuthIdentity("facebook-subject", "new@example.com", True, "New Person")

    await client.close()
    app = service.create_web_app(
        accounts=accounts,
        mailer=lambda email, code: sent.append((email, code)),
        origin=ORIGIN,
        proxy_secret="",
        oauth_identity=identity,
    )
    async with web_client(app, cookie_jar=CookieJar(unsafe=True)) as client:
        url = (
            await (
                await client.get(
                    "/api/auth/oauth/facebook/start?timezone=America/Denver"
                )
            ).json()
        )["url"]
        assert "public_profile" in url
        assert "email" in url
        state = parse_qs(urlsplit(url).query)["state"][0]
        callback = await client.get(
            f"/api/auth/oauth/facebook/callback?code=oauth-code&state={state}",
            allow_redirects=False,
        )
        assert callback.headers["Location"].endswith(
            "/setup.html?social=facebook-connected"
        )
        created = accounts.by_email("new@example.com")
        assert created is not None
        assert created[1]["timezone"] == "America/Denver"
        assert created[1]["oauth_identities"]["facebook"] == "facebook-subject"
        assert (await client.get("/api/account")).status == 200


async def test_facebook_sign_in_without_an_email_does_not_create_an_account(
    gateway, monkeypatch
):
    client, accounts, sent, _ = gateway
    import core.web_account_service as service

    monkeypatch.setattr(service.config, "FACEBOOK_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setattr(service.config, "FACEBOOK_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setattr(service.config, "FACEBOOK_OAUTH_REDIRECT_URI", "")

    async def identity(provider, code, **kwargs):
        return OAuthIdentity("facebook-subject", "", False, "New Person")

    await client.close()
    app = service.create_web_app(
        accounts=accounts,
        mailer=lambda email, code: sent.append((email, code)),
        origin=ORIGIN,
        proxy_secret="",
        oauth_identity=identity,
    )
    async with web_client(app, cookie_jar=CookieJar(unsafe=True)) as client:
        url = (await (await client.get("/api/auth/oauth/facebook/start")).json())["url"]
        state = parse_qs(urlsplit(url).query)["state"][0]
        callback = await client.get(
            f"/api/auth/oauth/facebook/callback?code=oauth-code&state={state}",
            allow_redirects=False,
        )
        assert callback.headers["Location"].endswith("/login.html?social=no-email")
        assert accounts.by_email("new@example.com") is None
        assert (await client.get("/api/account")).status == 401


async def test_discord_oauth_links_the_authenticated_account(gateway, monkeypatch):
    client, accounts, sent, _ = gateway
    import core.web_account_service as service

    monkeypatch.setattr(service.config, "DISCORD_APPLICATION_ID", 123456789)
    monkeypatch.setattr(service.config, "DISCORD_CLIENT_SECRET", "client-secret")
    monkeypatch.setattr(service.config, "DISCORD_OAUTH_REDIRECT_URI", "")
    identity_calls = []

    async def discord_identity(code, **kwargs):
        identity_calls.append((code, kwargs))
        return "987654321", "River#1234"

    await client.close()
    app = service.create_web_app(
        accounts=accounts,
        mailer=lambda email, code: sent.append((email, code)),
        origin=ORIGIN,
        proxy_secret="",
        discord_identity=discord_identity,
    )
    async with web_client(app, cookie_jar=CookieJar(unsafe=True)) as client:
        token = (await (await request_code(client)).json())["challenge"]
        assert (await verify(client, token, sent[-1][1])).status == 200
        start = await client.get("/api/auth/discord/start")
        assert start.status == 200
        authorize_url = (await start.json())["url"]
        assert "scope=identify" in authorize_url
        assert (
            "redirect_uri=http%3A%2F%2Flocalhost%3A8080%2Fapi%2Fauth%2Fdiscord%2Fcallback"
            in authorize_url
        )
        callback = await client.get(
            "/api/auth/discord/callback?code=oauth-code&state="
            + authorize_url.split("state=", 1)[1].split("&", 1)[0],
            allow_redirects=False,
        )
        assert callback.status == 302
        assert callback.headers["Location"].endswith("/app.html?discord=connected")
        assert accounts.users["existing"]["discord_user_id"] == "987654321"
        assert identity_calls[0][0] == "oauth-code"
        replay = await client.get(
            "/api/auth/discord/callback?code=oauth-code&state="
            + authorize_url.split("state=", 1)[1].split("&", 1)[0],
            allow_redirects=False,
        )
        assert replay.headers["Location"].endswith("/app.html?discord=cancelled")
        assert len(identity_calls) == 1


async def test_discord_oauth_can_return_to_setup(gateway, monkeypatch):
    client, accounts, sent, _ = gateway
    import core.web_account_service as service

    monkeypatch.setattr(service.config, "DISCORD_APPLICATION_ID", 123456789)
    monkeypatch.setattr(service.config, "DISCORD_CLIENT_SECRET", "client-secret")

    async def discord_identity(code, **kwargs):
        return "987654321", "River"

    await client.close()
    app = service.create_web_app(
        accounts=accounts,
        mailer=lambda email, code: sent.append((email, code)),
        origin=ORIGIN,
        proxy_secret="",
        discord_identity=discord_identity,
    )
    async with web_client(app, cookie_jar=CookieJar(unsafe=True)) as client:
        token = (await (await request_code(client)).json())["challenge"]
        assert (await verify(client, token, sent[-1][1])).status == 200
        rejected = await client.get("/api/auth/discord/start?next=https://evil.example")
        assert rejected.status == 400
        start = await client.get("/api/auth/discord/start?next=/setup.html")
        state = (await start.json())["url"].split("state=", 1)[1].split("&", 1)[0]
        callback = await client.get(
            f"/api/auth/discord/callback?code=oauth-code&state={state}",
            allow_redirects=False,
        )
        assert callback.headers["Location"].endswith("/setup.html?discord=connected")
        assert accounts.users["existing"]["discord_user_id"] == "987654321"


@pytest.mark.parametrize("case", ["no_cookie", "new_session", "logout", "expired"])
async def test_discord_callback_requires_the_original_live_session(monkeypatch, case):
    import core.web_account_service as service

    monkeypatch.setattr(service.config, "DISCORD_APPLICATION_ID", 123456789)
    monkeypatch.setattr(service.config, "DISCORD_CLIENT_SECRET", "client-secret")
    accounts, sent, now, calls = Accounts(), [], [100.0], []

    async def identity(code, **kwargs):
        calls.append(code)
        return "987654321", "River"

    app = service.create_web_app(
        accounts=accounts,
        mailer=lambda email, code: sent.append(code),
        origin=ORIGIN,
        proxy_secret="",
        clock=lambda: now[0],
        discord_identity=identity,
    )
    async with web_client(app, cookie_jar=CookieJar(unsafe=True)) as client:
        token = (await (await request_code(client)).json())["challenge"]
        login = await verify(client, token, sent[-1])
        assert "SameSite=Lax" in login.headers["Set-Cookie"]
        url = (await (await client.get("/api/auth/discord/start")).json())["url"]
        state = parse_qs(urlsplit(url).query)["state"][0]
        if case == "no_cookie":
            client.session.cookie_jar.clear()
        elif case == "new_session":
            token = (await (await request_code(client)).json())["challenge"]
            assert (await verify(client, token, sent[-1])).status == 200
        elif case == "logout":
            await client.post("/api/auth/logout", json={}, headers={"Origin": ORIGIN})
        else:
            now[0] += 601
        response = await client.get(
            f"/api/auth/discord/callback?code=oauth-code&state={state}",
            allow_redirects=False,
        )
        assert response.status == 302
        assert not response.headers["Location"].endswith("discord=connected")
        assert not calls
        assert not accounts.users["existing"].get("discord_user_id")


async def test_discord_oauth_rejects_an_identity_linked_to_another_account(
    gateway, monkeypatch
):
    client, accounts, sent, _ = gateway
    import core.web_account_service as service

    monkeypatch.setattr(service.config, "DISCORD_APPLICATION_ID", 123456789)
    monkeypatch.setattr(service.config, "DISCORD_CLIENT_SECRET", "client-secret")
    accounts.users["other"] = {
        "email": "other@example.com",
        "internal_username": "other",
        "account_status": "active",
        "discord_user_id": "987654321",
    }

    async def discord_identity(code, **kwargs):
        return "987654321", "Other"

    await client.close()
    app = service.create_web_app(
        accounts=accounts,
        mailer=lambda email, code: sent.append((email, code)),
        origin=ORIGIN,
        proxy_secret="",
        discord_identity=discord_identity,
    )
    async with web_client(app, cookie_jar=CookieJar(unsafe=True)) as client:
        token = (await (await request_code(client)).json())["challenge"]
        assert (await verify(client, token, sent[-1][1])).status == 200
        start = await client.get("/api/auth/discord/start")
        state = (await start.json())["url"].split("state=", 1)[1].split("&", 1)[0]
        callback = await client.get(
            f"/api/auth/discord/callback?code=oauth-code&state={state}",
            allow_redirects=False,
        )
        assert callback.headers["Location"].endswith("/app.html?discord=in-use")
        assert "discord_user_id" not in accounts.users["existing"]
