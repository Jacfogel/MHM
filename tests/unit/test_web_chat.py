"""Website chat sends through the shared handler as the website channel."""

import pytest
import pytest_asyncio
from aiohttp import CookieJar

from communication.command_handlers.shared_types import InteractionResponse
from core.web_account_service import create_web_app
from core.web_chat import chat_payload, website_chat_reply
from tests.unit.test_web_account_service import web_client

pytestmark = [pytest.mark.unit, pytest.mark.communication, pytest.mark.asyncio]
ORIGIN = "http://localhost:8080"


class Accounts:
    def __init__(self):
        self.user = {
            "internal_username": "river",
            "email": "river@example.com",
            "account_status": "active",
        }

    def by_email(self, email):
        return ("existing", self.user) if email.casefold() == self.user["email"] else None

    def email_exists(self, email):
        return email.casefold() == self.user["email"]

    def username_exists(self, username):
        return False

    def get(self, uid):
        return self.user


@pytest_asyncio.fixture
async def chat_gateway(monkeypatch):
    captured = {}

    def reply(user_id, message, channel_type):
        captured.update(user_id=user_id, message=message, channel_type=channel_type)
        return InteractionResponse(
            "I can help with that.",
            completed=False,
            suggestions=["show my tasks", "  ", "cancel", "cancel"],
        )

    monkeypatch.setattr(
        "communication.message_processing.interaction_manager.handle_user_message",
        reply,
    )
    sent = []
    async with web_client(
        create_web_app(
            accounts=Accounts(),
            mailer=lambda email, code: sent.append(code),
            origin=ORIGIN,
            proxy_secret="",
        ),
        cookie_jar=CookieJar(unsafe=True),
    ) as client:
        challenge = (
            await (
                await client.post(
                    "/api/auth/request-code",
                    json={"email": "river@example.com", "mode": "login"},
                    headers={"Origin": ORIGIN},
                )
            ).json()
        )["challenge"]
        assert (
            await client.post(
                "/api/auth/verify",
                json={"challenge": challenge, "code": sent[-1]},
                headers={"Origin": ORIGIN},
            )
        ).status == 200
        yield client, captured


def test_chat_payload_keeps_plain_text_and_unique_suggestions():
    payload = chat_payload(
        InteractionResponse(
            "Here you go.",
            suggestions=["yes", "yes", "  ", 4, "not now"],
            completed=True,
        )
    )
    assert payload == {
        "reply": "Here you go.",
        "suggestions": ["yes", "not now"],
        "completed": True,
    }


def test_website_chat_reply_uses_the_website_channel(monkeypatch):
    seen = {}

    def reply(user_id, message, channel_type):
        seen.update(user_id=user_id, message=message, channel_type=channel_type)
        return InteractionResponse("Noted.", suggestions=["cancel"])

    monkeypatch.setattr(
        "communication.message_processing.interaction_manager.handle_user_message",
        reply,
    )
    payload = website_chat_reply("existing", "add a task")
    assert seen == {
        "user_id": "existing",
        "message": "add a task",
        "channel_type": "website",
    }
    assert payload["reply"] == "Noted."
    assert payload["suggestions"] == ["cancel"]


async def test_signed_in_chat_returns_the_reply_and_suggestions(chat_gateway):
    client, captured = chat_gateway
    response = await client.post(
        "/api/chat",
        json={"message": "  help me add a task  "},
        headers={"Origin": ORIGIN},
    )
    assert response.status == 200
    body = await response.json()
    assert body["reply"] == "I can help with that."
    assert body["suggestions"] == ["show my tasks", "cancel"]
    assert body["completed"] is False
    assert captured["channel_type"] == "website"
    assert captured["user_id"] == "existing"
    assert captured["message"] == "help me add a task"


def test_website_inbox_stores_a_copy_without_replacing_the_primary_channel(tmp_path, monkeypatch):
    from communication.communication_channels.website import inbox

    path = tmp_path / "website_inbox.json"
    monkeypatch.setattr(inbox, "get_user_file_path", lambda user_id, file_type: str(path))
    monkeypatch.setattr(inbox, "ensure_user_directory", lambda user_id: True)

    assert inbox.deliver_to_website("existing", "  Good morning.  ", "motivational") is True
    assert inbox.deliver_to_website("existing", "   ", "motivational") is False
    messages = inbox.list_website_messages("existing")
    assert len(messages) == 1
    assert messages[0]["text"] == "Good morning."
    assert messages[0]["category"] == "motivational"
    assert messages[0]["id"]


def test_predefined_send_also_keeps_a_website_copy(monkeypatch):
    from communication.delivery.message_dispatcher import PredefinedMessageDispatcher

    seen = {}

    def remember(user_id, message, category=""):
        seen.update(user_id=user_id, message=message, category=category)
        return True

    monkeypatch.setattr(
        "communication.communication_channels.website.inbox.deliver_to_website",
        remember,
    )
    monkeypatch.setattr(
        "communication.delivery.message_dispatcher.store_sent_message",
        lambda *args, **kwargs: None,
    )

    class Manager:
        def send_message_sync(self, channel_name, recipient, message, **kwargs):
            seen["channel_name"] = channel_name
            return True

    sent, text = PredefinedMessageDispatcher(Manager()).send_and_store_predefined_message(
        "existing",
        "motivational",
        "email",
        "river@example.com",
        {"id": "msg-1", "text": "Hello from MHM"},
        ["morning"],
    )
    assert sent is True
    assert text == "Hello from MHM"
    assert seen["channel_name"] == "email"
    assert seen["message"] == "Hello from MHM"
    assert seen["category"] == "motivational"


async def test_chat_inbox_returns_website_deliveries(chat_gateway, monkeypatch):
    client, _captured = chat_gateway
    monkeypatch.setattr(
        "communication.communication_channels.website.inbox.list_website_messages",
        lambda user_id: [{"id": "one", "text": "A reminder", "category": "tasks", "created_at": ""}],
    )
    body = await (await client.get("/api/chat")).json()
    assert body["messages"][0]["text"] == "A reminder"


async def test_chat_rejects_empty_extra_fields_and_signed_out_requests(chat_gateway):
    client, _captured = chat_gateway
    assert (
        await client.post("/api/chat", json={"message": "   "}, headers={"Origin": ORIGIN})
    ).status == 400
    assert (
        await client.post(
            "/api/chat",
            json={"message": "hi", "channel": "discord"},
            headers={"Origin": ORIGIN},
        )
    ).status == 400
    assert (await client.post("/api/auth/logout", json={}, headers={"Origin": ORIGIN})).status == 200
    assert (
        await client.post("/api/chat", json={"message": "hi"}, headers={"Origin": ORIGIN})
    ).status == 401
