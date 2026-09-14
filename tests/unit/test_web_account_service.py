"""Browser auth checks with isolated accounts and captured email only."""

import pytest
import pytest_asyncio
from aiohttp.test_utils import TestClient, TestServer
from aiohttp import CookieJar

from core.web_account_service import create_web_app, MHMAccounts

pytestmark = [pytest.mark.unit, pytest.mark.user_management, pytest.mark.asyncio]
ORIGIN = "http://localhost:8080"


class Accounts:
    def __init__(self):
        self.users = {
            "existing": {
                "internal_username": "river",
                "email": "river@example.com",
                "account_status": "active",
                "timezone": "America/Regina",
            }
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

    def username_exists(self, username):
        return any(
            user["internal_username"].casefold() == username.casefold()
            for user in self.users.values()
        )

    def get(self, uid):
        return self.users.get(uid, {})

    def create(self, email, username, timezone):
        uid = f"new-{len(self.users)}"
        self.users[uid] = {
            "email": email,
            "internal_username": username,
            "timezone": timezone,
            "account_status": "active",
        }
        return uid


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
    client = TestClient(TestServer(app), cookie_jar=CookieJar(unsafe=True))
    await client.start_server()
    yield client, accounts, sent, now
    await client.close()


async def request_code(client, email="river@example.com", mode="login", username=None):
    return await client.post(
        "/api/auth/request-code",
        json={
            "email": email,
            "mode": mode,
            "username": (
                username
                if username is not None
                else ("brook" if mode == "create" else "")
            ),
            "timezone": "America/Regina",
        },
        headers={"Origin": ORIGIN},
    )


async def verify(client, token, code):
    return await client.post(
        "/api/auth/verify",
        json={"challenge": token, "code": code},
        headers={"Origin": ORIGIN},
    )


async def test_existing_login_session_logout_and_replay(gateway):
    client, _, sent, _ = gateway
    assert (await client.get("/api/account")).status == 401
    token = (await (await request_code(client)).json())["challenge"]
    result = await verify(client, token, sent[-1][1])
    assert result.status == 200
    assert "HttpOnly" in result.headers["Set-Cookie"]
    assert "SameSite=Strict" in result.headers["Set-Cookie"]
    assert result.headers["Cache-Control"] == "no-store"
    profile = await (await client.get("/api/account")).json()
    assert profile["username"] == "river"
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
    assert (await verify(client, token, sent[-1][1])).status == 200
    assert accounts.email_exists("brook@example.com")
    assert (await (await client.get("/api/account")).json())["username"] == "brook"


async def test_creation_rechecks_duplicates_after_verification(gateway):
    client, accounts, sent, _ = gateway
    token = (await (await request_code(client, "brook@example.com", "create")).json())[
        "challenge"
    ]
    accounts.users["racing"] = {
        "internal_username": "BROOK",
        "email": "other@example.com",
        "account_status": "active",
    }
    assert (await verify(client, token, sent[-1][1])).status == 409
    assert not accounts.email_exists("brook@example.com")


async def test_unknown_email_and_duplicate_signup_are_not_signed_in(gateway):
    client, _, sent, _ = gateway
    for email, mode in [
        ("missing@example.com", "login"),
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
    async with TestClient(TestServer(app)) as client:
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
    with pytest.raises(ValueError):
        create_web_app(origin=origin, proxy_secret="")


async def test_product_adapter_uses_shared_creation_and_casefolded_lookup(monkeypatch):
    import core

    captured = []
    monkeypatch.setattr(
        core, "create_new_user", lambda data: captured.append(data) or "new-id"
    )
    adapter = MHMAccounts()
    assert adapter.create("new@example.com", "new-user", "America/Regina") == "new-id"
    assert captured[0]["channel"] == {"type": "email"}
    assert not captured[0]["messages_enabled"]
    monkeypatch.setattr(
        adapter,
        "all",
        lambda: [("one", {"email": "River@Example.com", "internal_username": "River"})],
    )
    assert adapter.by_email("river@example.com")[0] == "one"
    assert adapter.username_exists("RIVER")
    monkeypatch.setattr(
        adapter,
        "all",
        lambda: [
            ("one", {"email": "same@example.com"}),
            ("two", {"email": "same@example.com"}),
        ],
    )
    assert adapter.by_email("same@example.com") is None


async def test_duplicate_email_cannot_be_selected_by_username(gateway):
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
    token = (await (await request_code(client, username="BROOK")).json())["challenge"]
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
    async with TestClient(TestServer(app)) as client:
        response = await request_code(client)
        assert response.status == 503
        message = (await response.json())["error"]
        assert "couldn't send your code" in message
        assert "private diagnostic details" not in message
