"""Authenticated website WhatsApp connection through isolated state."""

import pytest

from core import config
from tests.behavior.test_whatsapp import live as whatsapp_fixture, PHONE
from tests.unit.test_web_account_service import gateway as website_fixture, request_code, verify

live = whatsapp_fixture
website_gateway = website_fixture
pytestmark = [pytest.mark.behavior, pytest.mark.communication, pytest.mark.user]


@pytest.mark.asyncio
async def test_website_whatsapp_requires_session_consent_proof_and_matching_plan(website_gateway, live, monkeypatch):
    client, fake_accounts, sent, _ = website_gateway
    _, transport, _, accounts = live
    assert (await client.get("/api/whatsapp/enrollment")).status == 401
    accounts["existing"] = fake_accounts.users["existing"]
    accounts["existing"].update(subscription_status="active", subscription_plan="whatsapp", billing_livemode=True)
    token = (await (await request_code(client)).json())["challenge"]
    assert (await verify(client, token, sent[-1][1])).status == 200
    headers = {"Origin": "http://localhost:8080"}
    phone = "+15555550199"
    payload = {"action": "start", "phone": phone, "consent": True}
    assert (await client.post("/api/whatsapp/enrollment", headers={"Origin": "https://other.example"}, json=payload)).status == 403
    assert (await client.post("/api/whatsapp/enrollment", headers=headers, json={**payload, "consent": False})).status == 400
    response = await client.post("/api/whatsapp/enrollment", headers=headers, json=payload)
    assert response.status == 200
    proof = (await response.json())["token"]
    payload = {"action": "connect", "phone": phone, "consent": True, "token": proof}
    assert (await client.post("/api/whatsapp/enrollment", headers=headers, json=payload)).status == 400
    assert transport.state.verify_enrollment(phone, proof)
    assert (await client.post("/api/whatsapp/enrollment", headers=headers, json=payload)).status == 200
    info = await (await client.get("/api/whatsapp/enrollment")).json()
    assert info["connected"] and info["eligible"] and info["sender"] == config.WHATSAPP_PHONE_NUMBER
    assert info["phone"] == phone
    accounts["existing"]["subscription_plan"] = "phone"
    info = await (await client.get("/api/whatsapp/enrollment")).json()
    assert info["connected"] and not info["eligible"]
    assert (await client.post("/api/whatsapp/enrollment", headers=headers, json=payload)).status == 400
    transport.state.set_stopped(phone, True)
    monkeypatch.setattr("core.update_user_preferences", lambda *_, **__: True)
    assert (await client.post("/api/whatsapp/enrollment", headers=headers, json={"action": "disconnect"})).status == 200
    assert transport.state.enrolled_user(phone) is None
    assert transport.state.stopped(phone)
    assert transport.state.enrolled_user(PHONE) == "one"
