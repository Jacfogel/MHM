"""Twilio pilot boundaries with real signatures/storage and a fake paid API."""

from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from twilio.request_validator import RequestValidator
from twilio.base.exceptions import TwilioRestException

from core import config
from core.error_handling import ConfigurationError
from communication.communication_channels.base.base_channel import ChannelStatus
from communication.communication_channels.sms.bot import SmsBot
from communication.communication_channels.sms.twilio_transport import TwilioTransport
from storage.sms_state import SmsState

pytestmark = [pytest.mark.behavior, pytest.mark.communication]
PHONE = "+15555550101"
SENDER = "+15555550102"
SID = "SM" + "a" * 32


@pytest.fixture
def live(monkeypatch, tmp_path):
    settings = {
        "SMS_SIMULATION_ENABLED": False, "SMS_TWILIO_ENABLED": True,
        "TWILIO_ACCOUNT_SID": "AC" + "a" * 32, "TWILIO_AUTH_TOKEN": "test-secret",
        "TWILIO_PHONE_NUMBER": SENDER, "SMS_PUBLIC_BASE_URL": "https://sms.example.test",
    }
    for name, value in settings.items():
        monkeypatch.setattr(config, name, value)
    monkeypatch.setattr("core.sms_enrollment.get_user_data", lambda *a: {"account": {
        "phone": PHONE, "account_status": "active", "subscription_status": "active", "subscription_plan": "phone", "billing_livemode": True}})
    state = SmsState(tmp_path / "sms.sqlite3")
    token = state.begin_enrollment(PHONE)
    assert state.verify_enrollment(PHONE, token)
    assert state.bind_enrollment("pilot-test", PHONE, token)
    monkeypatch.setattr("core.sms_enrollment.SmsState", lambda: state)
    monkeypatch.setattr("communication.communication_channels.sms.twilio_transport.SmsState", lambda: SmsState(tmp_path / "sms.sqlite3"))
    bot = SmsBot()
    bot.status = ChannelStatus.READY
    transport = TwilioTransport(bot)
    bot.transport = transport
    monkeypatch.setattr(transport, "client", SimpleNamespace(messages=SimpleNamespace(create=Mock(return_value=SimpleNamespace(sid=SID, status="queued")))))
    return bot, transport


def request(transport, body="hello", sid=SID, path="/sms/incoming", **extra):
    params = {"AccountSid": config.TWILIO_ACCOUNT_SID, "MessageSid": sid,
              "From": PHONE, "To": SENDER, "Body": body, **extra}
    signature = RequestValidator(config.TWILIO_AUTH_TOKEN).compute_signature(config.SMS_PUBLIC_BASE_URL + path, params)
    return transport.process(path, params, signature)


def test_send_tracks_acceptance_and_restricts_pilot(live):
    bot, transport = live
    assert transport.send(PHONE, "Hello", reply_kind="task_reminder", task_id="task-1") is True
    assert bot.last_outbound_message_id == SID
    assert transport.state.contexts(PHONE) == [("task_reminder", "task-1")]
    args = transport.client.messages.create.call_args.kwargs
    assert args["status_callback"] == "https://sms.example.test/sms/status"
    assert args["body"] == "Hello"
    assert transport.send("+15555550103", "Hello") is False
    assert transport.send(PHONE, "Other account data", user_id="someone-else") is False
    assert transport.send(PHONE, "x" * 1601) is False
    assert transport.client.messages.create.call_count == 1


@pytest.mark.parametrize("failure", [TimeoutError(), TwilioRestException(503, "uri", msg="SECRET")])
def test_uncertain_send_never_retries(live, failure):
    bot, transport = live
    transport.client.messages.create.side_effect = failure
    assert transport.send(PHONE, "Hello") == "unconfirmed"
    assert transport.client.messages.create.call_count == 1
    assert "SECRET" not in bot.get_error()


def test_provider_optout_rejection_blocks_future_sends(live):
    _, transport = live
    transport.client.messages.create.side_effect = TwilioRestException(400, "uri", msg="SECRET", code=21610)
    assert transport.send(PHONE, "hello") is False
    assert transport.state.stopped(PHONE)
    assert transport.send(PHONE, "hello again") is False
    assert transport.client.messages.create.call_count == 1


def test_invalid_signature_account_and_sender_do_not_mutate(live, monkeypatch):
    _, transport = live
    route = Mock(return_value="reply")
    monkeypatch.setattr(transport, "route", route)
    assert transport.process("/sms/incoming", {}, "invalid") == 403
    assert request(transport, AccountSid="ACwrong") == 403
    assert request(transport, From="+15555550103") == 403
    assert request(transport, To="+15555550103") == 403
    route.assert_not_called()


def test_duplicate_webhooks_are_durable_and_concurrent(live, monkeypatch):
    _, transport = live
    route = Mock(return_value="Saved")
    monkeypatch.setattr(transport, "route", route)
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(lambda _: request(transport), range(2))) == [200, 200]
    assert route.call_count == 1
    transport.state = SmsState(transport.state.path)
    assert request(transport) == 200
    assert route.call_count == 1
    assert transport.client.messages.create.call_count == 1


def test_processing_failure_is_not_replayed(live, monkeypatch):
    _, transport = live
    route = Mock(side_effect=RuntimeError("private detail"))
    monkeypatch.setattr(transport, "route", route)
    assert request(transport) == 200
    assert request(transport) == 200
    assert route.call_count == 1
    with transport.state.connection() as db:
        assert db.execute("SELECT state FROM inbound").fetchone()[0] == "needs_review"


def test_stop_start_and_help_do_not_run_commands_or_duplicate_provider_reply(live, monkeypatch):
    _, transport = live
    route = Mock(return_value="Saved")
    monkeypatch.setattr(transport, "route", route)
    assert request(transport, "STOP", OptOutType="STOP") == 200
    assert transport.send(PHONE, "hello") is False
    assert request(transport, "done", "SM" + "b" * 32) == 200
    route.assert_not_called()
    assert request(transport, "START", "SM" + "c" * 32, OptOutType="START") == 200
    assert not transport.state.stopped(PHONE)
    assert request(transport, "HELP", "SM" + "d" * 32, OptOutType="HELP") == 200
    transport.client.messages.create.assert_not_called()


def test_delivery_callbacks_are_monotonic_and_can_arrive_early(live):
    _, transport = live
    assert request(transport, path="/sms/status", MessageStatus="delivered") == 200
    assert request(transport, path="/sms/status", MessageStatus="queued") == 200
    transport.state.record_outbound(SID, "queued")
    with transport.state.connection() as db:
        assert db.execute("SELECT status FROM outbound WHERE sid=?", (SID,)).fetchone()[0] == "delivered"


def test_ambiguous_or_missing_short_reply_takes_no_action(live, monkeypatch):
    _, transport = live
    route = Mock()
    monkeypatch.setattr("communication.message_processing.email_reply_routing.route_task_reply", route)
    assert "No action was taken" in transport.route("done", "pilot-test", PHONE)
    transport.state.add_context(PHONE, "task_reminder", "task-1")
    transport.state.add_context(PHONE, "checkin")
    assert "More than one prompt" in transport.route("done", "pilot-test", PHONE)
    route.assert_not_called()
    shared = Mock(return_value=SimpleNamespace(message="Task completed", completed=True))
    monkeypatch.setattr("communication.message_processing.interaction_manager.handle_user_message", shared)
    assert transport.route("complete task task-1", "pilot-test", PHONE) == "Task completed"
    shared.assert_called_once_with("pilot-test", "complete task task-1", "sms")


def test_checkin_replies_use_shared_flow_and_clear_completed_context(live, monkeypatch):
    _, transport = live
    transport.state.add_context(PHONE, "checkin")
    answer = Mock(return_value=SimpleNamespace(message="Check-in saved", completed=True))
    monkeypatch.setattr("communication.message_processing.email_reply_routing.route_checkin_reply", answer)
    assert transport.route("3", "pilot-test", PHONE) == "Check-in saved"
    answer.assert_called_once_with("pilot-test", "3")
    assert transport.state.contexts(PHONE) == []


def test_real_task_completion_through_signed_webhook(live, test_data_dir, monkeypatch):
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory
    from tasks.task_data_manager import create_task, get_task_by_id
    from core import get_user_data
    from storage.user_data_write import update_user_preferences

    _, transport = live
    assert TestUserFactory.create_basic_user("pilot-test", test_data_dir=test_data_dir)
    user_id = TestUserFactory.get_test_user_id_by_label("pilot-test", test_data_dir)
    assert user_id
    monkeypatch.setattr("communication.communication_channels.sms.twilio_transport.sms_user_for_phone", lambda number, **kwargs: user_id if number == PHONE else None)
    assert update_user_preferences(user_id, {"channel": {"type": "sms"}}, auto_create=False)
    assert get_user_data(user_id, "preferences")["preferences"]["channel"]["type"] == "sms"
    task_id = create_task(user_id, "SMS test task")
    assert task_id
    transport.state.add_context(PHONE, "task_reminder", task_id)
    assert request(transport, "done") == 200
    assert get_task_by_id(user_id, task_id)["status"] == "completed"
    assert request(transport, "done") == 200
    assert transport.state.contexts(PHONE) == []


@pytest.mark.asyncio
async def test_live_listener_lifecycle_and_signed_http(live, monkeypatch):
    from http.client import HTTPConnection
    from urllib.parse import urlencode

    _, transport = live
    monkeypatch.setattr(config, "SMS_WEBHOOK_PORT", 0)
    monkeypatch.setattr("communication.communication_channels.sms.twilio_transport.TwilioTransport", lambda bot: transport)
    route = Mock(return_value="Saved")
    monkeypatch.setattr(transport, "route", route)
    bot = SmsBot()
    transport.bot = bot
    assert await bot.initialize()
    assert await bot.health_check()
    assert bot.webhook_server is not None
    port = bot.webhook_server.server.server_address[1]
    params = {"AccountSid": config.TWILIO_ACCOUNT_SID, "MessageSid": SID,
              "From": PHONE, "To": SENDER, "Body": "hello"}
    signature = RequestValidator(config.TWILIO_AUTH_TOKEN).compute_signature(config.SMS_PUBLIC_BASE_URL + "/sms/incoming", params)
    try:
        for header, expected in [("invalid", 403), (signature, 200), (signature, 200)]:
            connection = HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request("POST", "/sms/incoming", urlencode(params),
                               {"Content-Type": "application/x-www-form-urlencoded", "X-Twilio-Signature": header})
            response = connection.getresponse()
            assert response.status == expected
            response.read()
            connection.close()
        assert route.call_count == 1
        assert not await bot.simulate_incoming(PHONE, "hello")
    finally:
        assert await bot.shutdown()
    assert not await bot.health_check()


@pytest.mark.parametrize("setting,value", [("TWILIO_AUTH_TOKEN", ""), ("SMS_SIMULATION_ENABLED", True), ("SMS_PUBLIC_BASE_URL", "http://example.test")])
def test_live_configuration_fails_closed(live, monkeypatch, setting, value):
    bot, _ = live
    monkeypatch.setattr(config, setting, value)
    with pytest.raises(ConfigurationError):
        TwilioTransport(bot)


def test_receipt_storage_failure_does_not_run_command(live, monkeypatch):
    import sqlite3

    _, transport = live
    route = Mock(return_value="Saved")
    claim = Mock(side_effect=sqlite3.OperationalError("storage unavailable"))
    monkeypatch.setattr(transport, "route", route)
    monkeypatch.setattr(transport.state, "claim", claim)
    assert request(transport) == 503
    claim.assert_called_once()
    route.assert_not_called()
    transport.client.messages.create.assert_not_called()


def test_optout_storage_failure_propagates_without_sending(live, monkeypatch):
    import sqlite3

    _, transport = live
    failed = Mock(side_effect=sqlite3.OperationalError("storage unavailable"))
    monkeypatch.setattr(transport.state, "connection", failed)
    assert transport.send(PHONE, "hello") == "unconfirmed"
    failed.assert_called_once()
    transport.client.messages.create.assert_not_called()


def test_sms_state_transaction_rolls_back_on_failure(tmp_path):
    state = SmsState(tmp_path / "rollback.sqlite3")
    with pytest.raises(RuntimeError):
        with state.connection() as db:
            db.execute("INSERT INTO optouts VALUES (?, ?)", (PHONE, 1))
            raise RuntimeError("abort transaction")
    assert state.stopped(PHONE) is False
