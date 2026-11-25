"""Direct Meta boundaries using signed events, isolated SQLite, and mocked HTTP."""

import hashlib
import hmac
import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from core import config
from core.billing import StripeBillingClient, subscription_price_plan
from core.channel_access import channel_allowed
from core.error_handling import ValidationError
from core.time_utilities import now_datetime_full
from core.whatsapp_enrollment import begin_whatsapp_enrollment, connect_whatsapp, whatsapp_user_for_phone
from communication.communication_channels.base.base_channel import ChannelStatus
from communication.communication_channels.whatsapp.bot import WhatsAppBot
from communication.communication_channels.whatsapp.transport import MetaTransport
from storage.whatsapp_state import WhatsAppState

pytestmark = [pytest.mark.behavior, pytest.mark.communication, pytest.mark.user]
PHONE = "+15555550101"
SID = "wamid.test-message"


@pytest.fixture
def live(monkeypatch, tmp_path):
    settings = {
        "WHATSAPP_ENABLED": True, "WHATSAPP_ACCESS_TOKEN": "test-token",
        "WHATSAPP_APP_SECRET": "test-secret", "WHATSAPP_VERIFY_TOKEN": "test-verify",
        "WHATSAPP_PHONE_NUMBER_ID": "123456", "WHATSAPP_BUSINESS_ACCOUNT_ID": "654321",
        "WHATSAPP_PHONE_NUMBER": "+15555550102", "WHATSAPP_API_VERSION": "v27.0",
        "WHATSAPP_NOTIFICATION_TEMPLATE": "mhm_notification", "WHATSAPP_TEMPLATE_LANGUAGE": "en_US",
    }
    for key, value in settings.items():
        monkeypatch.setattr(config, key, value)
    accounts = {"one": {"user_id": "one", "account_status": "active", "subscription_status": "active",
                        "subscription_plan": "whatsapp", "billing_livemode": True, "whatsapp_phone": PHONE}}
    state = WhatsAppState(tmp_path / "whatsapp.sqlite3")
    token = state.begin_enrollment(PHONE, "one")
    assert state.verify_enrollment(PHONE, token)
    assert state.bind_enrollment("one", PHONE, token, "one")
    monkeypatch.setattr("core.whatsapp_enrollment.WhatsAppState", lambda: state)
    monkeypatch.setattr("communication.communication_channels.whatsapp.transport.WhatsAppState", lambda: state)
    monkeypatch.setattr("core.whatsapp_enrollment.get_user_data", lambda uid, *_: {"account": accounts.get(uid, {})})

    def save(uid, patch, **_):
        accounts[uid].update(patch)
        return True

    monkeypatch.setattr("core.whatsapp_enrollment.update_user_account", save)
    post = Mock(return_value=SimpleNamespace(status_code=200, json=lambda: {"messages": [{"id": SID}]}))
    monkeypatch.setattr("communication.communication_channels.whatsapp.transport.requests.post", post)
    bot = WhatsAppBot()
    bot.status = ChannelStatus.READY
    transport = MetaTransport(bot)
    bot.transport = transport
    return bot, transport, post, accounts


def event(transport, text="help", sid=SID, phone=PHONE, timestamp=None, **value_extra):
    value = {"metadata": {"phone_number_id": config.WHATSAPP_PHONE_NUMBER_ID}, "messages": [
        {"id": sid, "from": phone[1:], "timestamp": str(timestamp or int(now_datetime_full().timestamp())),
         "type": "text", "text": {"body": text}}], **value_extra}
    data = {"object": "whatsapp_business_account", "entry": [{"id": config.WHATSAPP_BUSINESS_ACCOUNT_ID,
            "changes": [{"field": "messages", "value": value}]}]}
    raw = json.dumps(data).encode()
    return transport.process(raw, signature(raw))


def signature(raw):
    return "sha256=" + hmac.new(config.WHATSAPP_APP_SECRET.encode(), raw, hashlib.sha256).hexdigest()


@pytest.mark.parametrize("plan,status,mode,allowed", [
    ("whatsapp", "active", True, True), ("whatsapp", "active", False, False),
    ("whatsapp", "trialing", True, False), ("whatsapp", "past_due", True, False),
    ("whatsapp", "canceled", True, False), ("whatsapp", "comped", True, False),
    ("phone", "active", True, False), ("discord", "active", True, False),
])
def test_separate_plan_access(plan, status, mode, allowed):
    account = {"subscription_plan": plan, "subscription_status": status, "billing_livemode": mode}
    assert channel_allowed(account, "whatsapp") is allowed
    if plan == "whatsapp":
        assert not channel_allowed(account, "sms")


def test_catalog_and_reconciled_stripe_price(monkeypatch):
    assert config.BILLING_PLANS["whatsapp"] == {"name": "WhatsApp", "amount": 2000, "currency": "cad"}
    monkeypatch.setattr(config, "STRIPE_WHATSAPP_PRICE_ID", "price_whatsapp")
    assert StripeBillingClient.from_config().price_ids["whatsapp"] == "price_whatsapp"
    assert subscription_price_plan({"items": {"data": [{"price": {"id": "price_whatsapp"}}]}}) == ("whatsapp", "price_whatsapp")
    assert subscription_price_plan({"metadata": {"plan": "whatsapp"}, "items": {"data": [{"price": {"id": "price_unknown"}}]}})[0] == ""


def test_raw_signature_and_destination_checks(live):
    _, transport, post, _ = live
    assert transport.process(b'{}', "invalid") == 403
    malformed = b'{'
    assert transport.process(malformed, signature(malformed)) == 400
    assert event(transport, metadata={"phone_number_id": "other"}) == 403
    raw = json.dumps({"object": "whatsapp_business_account", "entry": [{"id": "other"}]}).encode()
    assert transport.process(raw, signature(raw)) == 403
    post.assert_not_called()


def test_duplicate_concurrent_events_and_restart_run_command_once(live, monkeypatch):
    _, transport, post, _ = live
    route = Mock(return_value="Saved")
    monkeypatch.setattr("communication.communication_channels.whatsapp.transport.route_phone_reply", route)
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(lambda _: event(transport), range(8))) == [200] * 8
    assert route.call_count == post.call_count == 1
    transport.state = WhatsAppState(transport.state.path)
    assert event(transport) == 200
    assert route.call_count == 1
    args = post.call_args.kwargs
    assert args["json"]["type"] == "text"
    assert args["json"]["to"] == PHONE[1:]
    assert args["allow_redirects"] is False


def test_window_timestamp_and_future_or_delayed_events(live, monkeypatch):
    _, transport, post, _ = live
    route = Mock(return_value="Saved")
    monkeypatch.setattr("communication.communication_channels.whatsapp.transport.route_phone_reply", route)
    now = int(now_datetime_full().timestamp())
    assert event(transport, timestamp=now - 86401) == 200
    assert not transport.state.window_open(PHONE)
    assert event(transport, sid="wamid.future", timestamp=now + 3600) == 200
    route.assert_not_called()
    post.assert_not_called()


def test_notification_then_open_delivers_saved_text_and_context(live):
    _, transport, post, _ = live
    assert transport.send(PHONE, "Task details", user_id="one", reply_kind="task_reminder", task_id="task-1") is True
    payload = post.call_args.kwargs["json"]
    assert payload["type"] == "template"
    assert payload["template"] == {"name": "mhm_notification", "language": {"code": "en_US"}}
    assert transport.state.contexts(PHONE) == []
    assert transport.state.pending(PHONE, "one")[0][1] == "Task details"
    assert event(transport, "OPEN", sid="wamid.open") == 200
    assert post.call_args.kwargs["json"]["text"]["body"] == "Task details"
    assert transport.state.contexts(PHONE) == [("task_reminder", "task-1")]
    assert transport.state.pending(PHONE, "one") == []


def test_missing_template_and_wrong_user_do_not_submit(live, monkeypatch):
    _, transport, post, _ = live
    monkeypatch.setattr(config, "WHATSAPP_NOTIFICATION_TEMPLATE", "")
    assert transport.send(PHONE, "Body") is False
    assert transport.send(PHONE, "Body", user_id="other") is False
    assert transport.send(PHONE, "x" * 4097) is False
    post.assert_not_called()


@pytest.mark.parametrize("failure", [TimeoutError(), SimpleNamespace(status_code=503)])
def test_uncertain_submission_never_retries(live, failure):
    bot, transport, post, _ = live
    if isinstance(failure, Exception):
        post.side_effect = failure
    else:
        post.return_value = failure
    assert transport.send(PHONE, "Body") == "unconfirmed"
    assert post.call_count == 1
    assert "uncertain" in bot.error_message
    assert transport.state.pending(PHONE, "one")


def test_explicit_rejection_discards_unsent_notification(live):
    _, transport, post, _ = live
    post.return_value = SimpleNamespace(status_code=400)
    assert transport.send(PHONE, "Body") is False
    assert transport.state.pending(PHONE, "one") == []


def test_stop_start_and_plan_downgrade(live):
    _, transport, post, accounts = live
    assert event(transport, "STOP") == 200
    assert transport.state.stopped(PHONE)
    assert transport.send(PHONE, "Body") is False
    accounts["one"]["subscription_plan"] = "phone"
    assert event(transport, "START", sid="wamid.start") == 200
    assert not transport.state.stopped(PHONE)
    assert event(transport, "help", sid="wamid.denied") == 200
    assert transport.send(PHONE, "Body") is False
    post.assert_not_called()


def test_processing_failure_is_not_replayed(live, monkeypatch):
    _, transport, _, _ = live
    route = Mock(side_effect=RuntimeError("private content"))
    monkeypatch.setattr("communication.communication_channels.whatsapp.transport.route_phone_reply", route)
    assert event(transport) == event(transport) == 200
    assert route.call_count == 1
    with transport.state.connection() as db:
        assert db.execute("SELECT state FROM inbound WHERE sid=?", (SID,)).fetchone()[0] == "needs_review"


def test_read_callback_cannot_regress(live):
    _, transport, _, _ = live
    for status in ["read", "sent", "delivered"]:
        assert event(transport, messages=[], statuses=[{"id": SID, "status": status}]) == 200
    transport.state.record_outbound(SID, "accepted")
    with transport.state.connection() as db:
        assert db.execute("SELECT status FROM outbound WHERE sid=?", (SID,)).fetchone()[0] == "read"


def test_link_proves_phone_and_consumes_account_bound_consent(live):
    _, transport, post, accounts = live
    accounts["two"] = {**accounts["one"], "user_id": "two", "whatsapp_phone": ""}
    second = "+15555550199"
    with pytest.raises(ValidationError):
        begin_whatsapp_enrollment(second, False, "two")
    token = begin_whatsapp_enrollment(second, True, "two")
    with pytest.raises(ValidationError):
        connect_whatsapp("two", second, token, True, "two")
    assert event(transport, "LINK " + token, phone=second) == 200
    with pytest.raises(ValidationError):
        connect_whatsapp("two", second, token, True, "one")
    assert connect_whatsapp("two", second, token, True, "two") is True
    assert whatsapp_user_for_phone(second) == "two"
    assert not transport.state.enrollment_verified(second, token, "two")
    assert accounts["two"]["whatsapp_phone"] == second
    post.assert_not_called()


def test_disconnect_retains_receipts_and_stop_but_revokes_pending(live):
    _, transport, _, _ = live
    assert transport.send(PHONE, "Body") is True
    transport.state.set_stopped(PHONE, True)
    transport.state.disconnect_enrollment("one")
    assert transport.state.pending(PHONE, "one") == []
    assert transport.state.enrolled_user(PHONE) is None
    assert transport.state.stopped(PHONE)


@pytest.mark.parametrize("selected,expected", [("sms", "sms"), ("whatsapp", "whatsapp")])
def test_disconnect_preserves_other_delivery_and_updates_selected_contact(live, monkeypatch, selected, expected):
    from core.whatsapp_enrollment import disconnect_whatsapp

    _, transport, _, accounts = live
    account = {**accounts["one"], "email": "test@example.test"}
    monkeypatch.setattr("core.whatsapp_enrollment.get_user_data", lambda *_: {
        "account": account, "preferences": {"channel": {"type": selected}}})
    save_preferences = Mock(return_value=True)
    save_account = Mock(return_value=True)
    monkeypatch.setattr("core.update_user_preferences", save_preferences)
    monkeypatch.setattr("core.whatsapp_enrollment.update_user_account", save_account)
    assert disconnect_whatsapp("one") == expected
    assert transport.state.enrolled_user(PHONE) is None
    if selected == "whatsapp":
        save_preferences.assert_not_called()
        save_account.assert_called_once_with("one", {"chat_id": ""}, auto_create=False)
    else:
        save_preferences.assert_not_called()
        save_account.assert_not_called()


def test_factory_discovery_and_delivery_access(live, monkeypatch):
    from core.channel_access import delivery_channel_allowed
    from communication.core.factory import ChannelFactory
    from communication.communication_channels.base.base_channel import ChannelConfig

    assert "whatsapp" in config.get_available_channels()
    with monkeypatch.context() as context:
        context.setattr(ChannelFactory, "_initialized", False)
        context.setattr(ChannelFactory, "_channel_registry", {})
        assert isinstance(ChannelFactory.create_channel("whatsapp", ChannelConfig(name="whatsapp")), WhatsAppBot)
    monkeypatch.setattr("core.get_user_data", lambda *_: {"account": {
        "subscription_plan": "phone", "subscription_status": "active", "billing_livemode": True}})
    assert not delivery_channel_allowed("one", "whatsapp")


def test_short_reply_refuses_ambiguous_context(live):
    from communication.message_processing.phone_reply_routing import route_phone_reply

    _, transport, _, _ = live
    assert "No action was taken" in route_phone_reply(transport.state, "done", "one", PHONE, "whatsapp")
    transport.state.add_context(PHONE, "task_reminder", "first")
    transport.state.add_context(PHONE, "task_reminder", "second")
    assert "More than one" in route_phone_reply(transport.state, "done", "one", PHONE, "whatsapp")


@pytest.mark.asyncio
async def test_listener_verification_and_signed_delivery(live, monkeypatch):
    from http.client import HTTPConnection
    from urllib.parse import urlencode

    _, transport, post, _ = live
    monkeypatch.setattr(config, "WHATSAPP_WEBHOOK_PORT", 0)
    monkeypatch.setattr("communication.communication_channels.whatsapp.transport.MetaTransport", lambda bot: transport)
    bot = WhatsAppBot()
    transport.bot = bot
    assert await bot.initialize()
    assert await bot.health_check()
    webhook_server = bot.webhook_server
    assert webhook_server is not None
    port = webhook_server.server.server_address[1]
    try:
        for token, expected in [("wrong", 403), (config.WHATSAPP_VERIFY_TOKEN, 200)]:
            conn = HTTPConnection("127.0.0.1", port, timeout=5)
            query = urlencode({"hub.mode": "subscribe", "hub.verify_token": token, "hub.challenge": "challenge"})
            conn.request("GET", "/whatsapp/webhook?" + query)
            response = conn.getresponse()
            assert response.status == expected
            assert response.read() == (b"challenge" if expected == 200 else b"")
            conn.close()
        raw = b'{"object":"whatsapp_business_account","entry":[]}'
        for path, body, content_type, sig, expected in [
            ("/whatsapp/webhook", raw, "application/json", signature(raw), 200),
            ("/whatsapp/webhook", raw, "application/json", "wrong", 403),
            ("/wrong", raw, "application/json", signature(raw), 404),
            ("/whatsapp/webhook", raw, "text/plain", signature(raw), 415),
            ("/whatsapp/webhook", b"x" * 131073, "application/json", "wrong", 413),
        ]:
            conn = HTTPConnection("127.0.0.1", port, timeout=5)
            conn.request("POST", path, body=body, headers={"Content-Type": content_type, "X-Hub-Signature-256": sig})
            response = conn.getresponse()
            assert response.status == expected
            response.read()
            conn.close()
    finally:
        assert await bot.shutdown()
    assert not await bot.health_check()
    assert not await bot.send_message(PHONE, "stopped")
    post.assert_not_called()


def test_persisted_whatsapp_contact_and_real_task_reply(live, test_data_dir, monkeypatch):
    from core import get_user_data, update_user_account
    from storage.user_data_write import update_user_preferences
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory
    from tasks.task_data_manager import create_task, get_task_by_id
    from communication.delivery.recipient_resolver import RecipientResolver

    _, transport, _, _ = live
    assert TestUserFactory.create_basic_user("whatsapp-test", test_data_dir=test_data_dir)
    uid = TestUserFactory.get_test_user_id_by_label("whatsapp-test", test_data_dir)
    assert uid
    number = "+15555550199"
    assert update_user_account(uid, {"whatsapp_phone": number, "subscription_plan": "whatsapp",
                                   "subscription_status": "active", "billing_livemode": True}, auto_create=False)
    assert update_user_preferences(uid, {"channel": {"type": "whatsapp"}}, auto_create=False)
    account = get_user_data(uid, "account")["account"]
    assert account["whatsapp_phone"] == number and account["subscription_plan"] == "whatsapp"
    prefs = get_user_data(uid, "preferences")["preferences"]
    assert RecipientResolver().get_recipient_for_service(uid, "whatsapp", prefs) == number
    monkeypatch.setattr("core.whatsapp_enrollment.get_user_data", get_user_data)
    token = transport.state.begin_enrollment(number, uid)
    assert transport.state.verify_enrollment(number, token)
    assert transport.state.bind_enrollment(uid, number, token, uid)
    task_id = create_task(uid, "WhatsApp test task")
    transport.state.add_context(number, "task_reminder", task_id)
    assert event(transport, "done", phone=number) == 200
    assert get_task_by_id(uid, task_id)["status"] == "completed"
    assert transport.state.contexts(number) == []
