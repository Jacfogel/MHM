"""SMS simulation exercises the transport boundary without external delivery."""

import pytest

from communication.communication_channels.sms.bot import SmsBot
from communication.command_handlers.shared_types import InteractionResponse
from communication.delivery.recipient_resolver import RecipientResolver

pytestmark = pytest.mark.behavior


@pytest.mark.asyncio
async def test_sms_requires_opt_in_and_ready_state(monkeypatch):
    monkeypatch.setattr("core.config.SMS_SIMULATION_ENABLED", False)
    bot = SmsBot()
    assert not await bot.initialize()
    assert not await bot.send_message("+15555550101", "hello")
    assert bot.outbox == []
    monkeypatch.setattr("core.config.SMS_SIMULATION_ENABLED", True)
    assert await bot.initialize()
    assert await bot.health_check()
    assert await bot.send_message("+1 (555) 555-0101", "x" * 321)
    record = bot.outbox[0]
    assert record["simulated"] is True
    assert record["recipient"] == "+15555550101"
    assert list(map(len, record["segments"])) == [160, 160, 1]
    assert "".join(record["segments"]) == record["message"]
    assert not await bot.send_message("5555550101", "hello")
    assert not await bot.send_message("+15555550101", " ")
    assert len(bot.outbox) == 1
    assert await bot.shutdown()
    assert not await bot.health_check()
    assert not await bot.send_message("+15555550101", "hello")


@pytest.mark.asyncio
async def test_incoming_sms_routes_unique_account_and_saves_reply(monkeypatch):
    monkeypatch.setattr("core.config.SMS_SIMULATION_ENABLED", True)
    monkeypatch.setattr("core.user_management.get_all_user_ids", lambda: ["sms-test"])
    monkeypatch.setattr("core.get_user_data", lambda *a, **k: {"account": {"phone": "+1 (555) 555-0101"}})
    calls = []

    def handle(user, text, channel):
        calls.append((user, text, channel))
        return InteractionResponse("Task completed.", True)

    monkeypatch.setattr("communication.message_processing.interaction_manager.handle_user_message", handle)
    bot = SmsBot()
    assert await bot.initialize()
    assert await bot.simulate_incoming("+15555550101", "done")
    assert calls == [("sms-test", "done", "sms")]
    assert bot.outbox[0]["message"] == "Task completed."
    assert not await bot.simulate_incoming("+15555550102", "done")
    monkeypatch.setattr("core.user_management.get_all_user_ids", lambda: ["sms-test", "duplicate"])
    assert not await bot.simulate_incoming("+15555550101", "done")
    assert len(calls) == 1


def test_sms_discovery_factory_and_recipient(monkeypatch):
    from core import config
    from communication.core.factory import ChannelFactory
    from communication.communication_channels.base.base_channel import ChannelConfig

    monkeypatch.setattr(config, "SMS_SIMULATION_ENABLED", False)
    assert "sms" not in config.get_available_channels()
    monkeypatch.setattr(config, "SMS_SIMULATION_ENABLED", True)
    assert "sms" in config.get_available_channels()
    monkeypatch.setattr(ChannelFactory, "_initialized", False)
    monkeypatch.setattr(ChannelFactory, "_channel_registry", {})
    assert isinstance(ChannelFactory.create_channel("sms", ChannelConfig("sms")), SmsBot)
    monkeypatch.setattr("communication.delivery.recipient_resolver.get_user_data", lambda *a, **k: {"account": {"phone": "+1 555 555 0101"}})
    assert RecipientResolver().get_recipient_for_service("sms-test", "sms", {"channel": {"type": "sms"}}) == "+15555550101"


@pytest.mark.asyncio
async def test_reply_failure_does_not_repeat_command(monkeypatch):
    monkeypatch.setattr("core.config.SMS_SIMULATION_ENABLED", True)
    monkeypatch.setattr("core.user_management.get_all_user_ids", lambda: ["sms-test"])
    monkeypatch.setattr("core.get_user_data", lambda *a, **k: {"account": {"phone": "+15555550101"}})
    calls = []
    monkeypatch.setattr("communication.message_processing.interaction_manager.handle_user_message", lambda *args: calls.append(args) or InteractionResponse("Saved", True))
    bot = SmsBot()
    await bot.initialize()

    async def fail_send(*args, **kwargs):
        return False

    monkeypatch.setattr(bot, "send_message", fail_send)
    assert not await bot.simulate_incoming("+15555550101", "done")
    assert len(calls) == 1
    assert "Check the affected task" in bot.get_error()


@pytest.mark.asyncio
async def test_simulated_status_uses_real_shared_routing(test_data_dir, monkeypatch):
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory
    from core import update_user_account

    user_id = "sms-routing-test"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    assert update_user_account(user_id, {"phone": "+15555550101"})
    monkeypatch.setattr("core.config.SMS_SIMULATION_ENABLED", True)
    monkeypatch.setattr("core.user_management.get_all_user_ids", lambda: [user_id])
    monkeypatch.setattr("communication.command_handlers.health_handler.get_health_integration_status", lambda _: None)
    monkeypatch.setattr("communication.message_processing.interaction_manager._interaction_manager_instance", None)
    bot = SmsBot()
    assert await bot.initialize()
    assert await bot.simulate_incoming("+15555550101", "health status")
    assert "did not change your settings" in bot.outbox[0]["message"]
