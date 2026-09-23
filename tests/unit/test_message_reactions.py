"""Thumbs reactions retire one message or create similar ones."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from communication.communication_channels.discord.bot import DiscordBot
from communication.communication_channels.discord.events.message_reactions import (
    handle_message_reaction,
)
from messages.message_data_manager import add_message, get_recent_messages, load_user_messages, store_sent_message
from messages.message_reactions import (
    apply_message_reaction,
    exclude_retired_messages,
    parse_similar_messages,
    personalized_reaction_instructions,
)

pytestmark = [pytest.mark.unit, pytest.mark.messages]


def _isolate_user(monkeypatch, tmp_path):
    user_dir = tmp_path / "user-1"
    (user_dir / "messages").mkdir(parents=True)
    sent_file = user_dir / "messages" / "sent_messages.json"
    sent_file.write_text(
        json.dumps({"schema_version": 2, "updated_at": "2026-09-21 12:00:00", "deliveries": []}),
        encoding="utf-8",
    )

    def user_dir_for(_user_id):
        return str(user_dir)

    monkeypatch.setattr("messages.message_data_manager.get_user_data_dir", user_dir_for)
    monkeypatch.setattr("messages.message_reactions.get_user_data_dir", user_dir_for)
    monkeypatch.setattr(
        "messages.message_data_manager.determine_file_path",
        lambda _file_type, _identifier: str(sent_file),
    )
    monkeypatch.setattr("storage.user_data_operations.update_user_index", lambda _user_id: None)
    return user_dir


def test_parse_similar_messages_drops_copies_and_keeps_two():
    raw = "Keep going.\n---\nOne small step counts.\n---\nYou can start tiny."
    assert parse_similar_messages(raw, "Keep going.") == [
        "One small step counts.",
        "You can start tiny.",
    ]


def test_thumbs_down_retires_that_library_message(monkeypatch, tmp_path):
    _isolate_user(monkeypatch, tmp_path)
    add_message(
        "user-1",
        "motivational",
        {
            "id": "template-1",
            "text": "Keep going.",
            "category": "motivational",
            "schedule": {"days": ["Monday"], "periods": ["morning"]},
        },
    )
    assert store_sent_message(
        "user-1",
        "motivational",
        "template-1",
        "Keep going.",
        metadata={"discord_message_id": "42"},
    )

    result = apply_message_reaction("user-1", "42", "down")

    assert result["status"] == "retired"
    assert result["reply"] == "I won't send that message again."
    messages = load_user_messages("user-1", "motivational")
    assert messages[0]["active"] is False
    assert exclude_retired_messages("user-1", messages) == []


def test_thumbs_up_adds_similar_library_messages_once(monkeypatch, tmp_path):
    _isolate_user(monkeypatch, tmp_path)
    add_message(
        "user-1",
        "motivational",
        {
            "id": "template-1",
            "text": "Keep going.",
            "category": "motivational",
            "schedule": {"days": ["Monday"], "periods": ["morning"]},
        },
    )
    store_sent_message(
        "user-1",
        "motivational",
        "template-1",
        "Keep going.",
        metadata={"discord_message_id": "42"},
    )
    monkeypatch.setattr(
        "messages.message_reactions.generate_similar_message_texts",
        lambda _user_id, _text: ["One small step counts.", "You can start tiny."],
    )

    first = apply_message_reaction("user-1", "42", "up")
    second = apply_message_reaction("user-1", "42", "up")

    assert first["reply"] == "I'll send more messages like that."
    assert second["reply"] == "I'll keep sending more messages like that."
    messages = load_user_messages("user-1", "motivational")
    texts = [message["text"] for message in messages]
    assert texts == ["Keep going.", "One small step counts.", "You can start tiny."]
    assert messages[1]["schedule"] == {"days": ["Monday"], "periods": ["morning"]}
    stored = get_recent_messages("user-1", limit=5)
    assert stored[0]["metadata"]["discord_message_id"] == "42"
    assert stored[0]["metadata"]["similar_generated"] is True


def test_thumbs_on_checkin_question_do_nothing(monkeypatch, tmp_path):
    _isolate_user(monkeypatch, tmp_path)
    store_sent_message(
        "user-1",
        "checkin",
        "question-1",
        "How is your mood right now?",
        metadata={"discord_message_id": "15"},
    )

    result = apply_message_reaction("user-1", "15", "down")

    assert result == {"status": "ignored", "reply": ""}
    assert personalized_reaction_instructions("user-1", "checkin") == ""


def test_thumbs_up_on_personalized_message_steers_later_generation(monkeypatch, tmp_path):
    _isolate_user(monkeypatch, tmp_path)
    store_sent_message(
        "user-1",
        "personalized_checkin",
        "generated-1",
        "Your check-in showed a calmer afternoon.",
        metadata={"discord_message_id": "77"},
    )

    result = apply_message_reaction("user-1", "77", "up")

    assert result["reply"] == "I'll write more messages like that."
    assert personalized_reaction_instructions("user-1", "personalized_checkin").startswith(
        "Write in the same spirit"
    )
    assert not (tmp_path / "user-1" / "messages" / "personalized_checkin.json").exists()


@pytest.mark.communication
@pytest.mark.asyncio
async def test_discord_reaction_handler_ignores_the_bot_and_replies_for_the_user(monkeypatch):
    calls = []

    def fake_apply(_user_id, _message_id, _kind):
        calls.append((_user_id, _message_id, _kind))
        return {"status": "retired", "reply": "I won't send that message again."}

    monkeypatch.setattr(
        "communication.communication_channels.discord.events.message_reactions.get_user_id_by_identifier",
        lambda discord_id: "user-1" if discord_id == "8" else None,
    )
    monkeypatch.setattr(
        "communication.communication_channels.discord.events.message_reactions.apply_message_reaction",
        fake_apply,
    )
    channel = SimpleNamespace(send=AsyncMock())
    host = SimpleNamespace(
        bot=SimpleNamespace(
            user=SimpleNamespace(id=1),
            get_channel=lambda _channel_id: channel,
        )
    )

    await handle_message_reaction(
        host,
        SimpleNamespace(user_id=1, message_id=42, channel_id=3, emoji=SimpleNamespace(name="👎")),
    )
    await handle_message_reaction(
        host,
        SimpleNamespace(user_id=8, message_id=42, channel_id=3, emoji=SimpleNamespace(name="👎")),
    )

    assert calls == [("user-1", "42", "down")]
    channel.send.assert_awaited_once_with("I won't send that message again.")


@pytest.mark.communication
@pytest.mark.asyncio
async def test_scheduled_discord_send_offers_thumbs_reactions():
    sent = SimpleNamespace(id=42, add_reaction=AsyncMock())
    user = MagicMock()
    user.send = AsyncMock(return_value=sent)
    bot = DiscordBot()
    discord_bot = MagicMock()
    discord_bot.get_user.return_value = user
    bot.bot = discord_bot

    assert await bot._send_message_internal(
        "discord_direct:8",
        "Keep going.",
        rich_data={"offer_message_reactions": True},
    )

    assert bot.last_outbound_message_id == "42"
    user.send.assert_awaited_once_with(content="Keep going.")
    assert [call.args[0] for call in sent.add_reaction.await_args_list] == ["👍", "👎"]
