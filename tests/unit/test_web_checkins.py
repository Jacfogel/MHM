"""Website check-in answers use the same flow as Discord and email."""

from types import SimpleNamespace

import pytest
import pytest_asyncio
from aiohttp import CookieJar

from communication.message_processing.flows.flow_constants import FLOW_CHECKIN
from core.web_account_service import create_web_app
from tests.unit.test_web_account_service import web_client

pytestmark = [pytest.mark.unit, pytest.mark.checkins, pytest.mark.asyncio]
ORIGIN = "http://localhost:8080"


class Accounts:
    def __init__(self):
        self.user = {"internal_username": "river", "email": "river@example.com", "account_status": "active"}

    def by_email(self, email):
        return ("existing", self.user) if email.casefold() == self.user["email"] else None

    def email_exists(self, email):
        return email.casefold() == self.user["email"]

    def username_exists(self, username):
        return False

    def get(self, uid):
        return self.user


@pytest_asyncio.fixture
async def checkin_gateway(monkeypatch):
    import checkins.checkin_data_manager as checkin_data
    import checkins.checkin_service as checkin_service
    import communication.message_processing.conversation_flow_manager as flows

    state = {"prompt": None, "enabled": True, "completed_today": False}

    def start(_uid):
        state["prompt"] = {"message": "How is your mood?", "index": 1, "total": 2}
        return "Let's start: How is your mood?", False

    def answer(_uid, text):
        if state["prompt"] is None:
            return None
        if text == "/cancel":
            state["prompt"] = None
            return "Check-in canceled. You can start again anytime with /checkin", True
        if text == "skip":
            state["prompt"] = {"message": "How is your energy?", "index": 2, "total": 2}
            return "How is your energy?", False
        state["prompt"] = None
        return "Thanks for checking in.", True

    monkeypatch.setattr(flows.conversation_manager, "start_checkin", start)
    monkeypatch.setattr(flows.conversation_manager, "answer_active_checkin", answer)
    monkeypatch.setattr(flows.conversation_manager, "current_checkin_prompt", lambda _uid: state["prompt"])
    monkeypatch.setattr(checkin_data, "is_user_checkins_enabled", lambda _uid: state["enabled"])
    monkeypatch.setattr(
        checkin_service,
        "get_checkin_start_status",
        lambda _uid, **_kwargs: SimpleNamespace(
            enabled=state["enabled"],
            already_completed_today=state["completed_today"],
            last_checkin_timestamp="2026-09-23 08:00:00",
        ),
    )
    sent = []
    async with web_client(
        create_web_app(accounts=Accounts(), mailer=lambda email, code: sent.append(code), origin=ORIGIN, proxy_secret=""),
        cookie_jar=CookieJar(unsafe=True),
    ) as client:
        challenge = (await (await client.post(
            "/api/auth/request-code",
            json={"email": "river@example.com", "mode": "login"},
            headers={"Origin": ORIGIN},
        )).json())["challenge"]
        assert (await client.post(
            "/api/auth/verify",
            json={"challenge": challenge, "code": sent[-1]},
            headers={"Origin": ORIGIN},
        )).status == 200
        yield client, state


async def test_website_checkin_can_be_started_answered_skipped_and_canceled(checkin_gateway):
    client, state = checkin_gateway
    idle = await (await client.get("/api/checkins")).json()
    assert idle["enabled"] is True
    assert idle["active"] is False

    started = await client.post("/api/checkins", json={"action": "start"}, headers={"Origin": ORIGIN})
    assert started.status == 200
    started_body = await started.json()
    assert started_body["active"] is True
    assert started_body["index"] == 1
    assert "mood" in started_body["message"]

    skipped = await (await client.post("/api/checkins", json={"action": "skip"}, headers={"Origin": ORIGIN})).json()
    assert skipped["active"] is True
    assert skipped["message"] == "How is your energy?"
    assert skipped["index"] == 2

    answered = await (await client.post(
        "/api/checkins", json={"action": "answer", "answer": "4"}, headers={"Origin": ORIGIN}
    )).json()
    assert answered["completed"] is True
    assert answered["active"] is False
    assert "Thanks" in answered["message"]

    state["prompt"] = {"message": "How is your mood?", "index": 1, "total": 1}
    canceled = await (await client.post("/api/checkins", json={"action": "cancel"}, headers={"Origin": ORIGIN})).json()
    assert canceled["completed"] is True
    assert "canceled" in canceled["message"]
    assert (await client.post(
        "/api/checkins", json={"action": "answer", "answer": "4"}, headers={"Origin": ORIGIN}
    )).status == 400


async def test_website_checkin_respects_disabled_and_already_completed(checkin_gateway):
    client, state = checkin_gateway
    state["enabled"] = False
    disabled = await (await client.get("/api/checkins")).json()
    assert disabled["enabled"] is False
    assert "Account" in disabled["message"]
    assert (await client.post("/api/checkins", json={"action": "start"}, headers={"Origin": ORIGIN})).status == 200

    state["enabled"] = True
    state["completed_today"] = True
    done = await (await client.post("/api/checkins", json={"action": "start"}, headers={"Origin": ORIGIN})).json()
    assert done["completed_today"] is True
    assert done["active"] is False
    assert "already completed" in done["message"]
    assert (await client.post("/api/checkins", json={"action": "later"}, headers={"Origin": ORIGIN})).status == 400


async def test_current_checkin_prompt_reads_the_open_question(monkeypatch):
    from communication.message_processing.conversation_flow_manager import conversation_manager

    user_id = "website-checkin-prompt"
    conversation_manager.user_states[user_id] = {
        "flow": FLOW_CHECKIN,
        "question_order": ["mood"],
        "current_question_index": 0,
        "data": {},
    }
    monkeypatch.setattr(
        conversation_manager,
        "_get_question_text",
        lambda key, data, uid: "How is your mood?",
    )
    try:
        assert conversation_manager.current_checkin_prompt(user_id) == {
            "message": "How is your mood?",
            "index": 1,
            "total": 1,
        }
        conversation_manager.user_states.pop(user_id)
        assert conversation_manager.current_checkin_prompt(user_id) is None
    finally:
        conversation_manager.user_states.pop(user_id, None)
