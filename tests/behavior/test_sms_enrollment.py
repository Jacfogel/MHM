"""Verified, consenting SMS enrollment and paid-plan routing boundaries."""

from datetime import timedelta
from unittest.mock import Mock

import pytest

from core.channel_access import channel_allowed
from core.error_handling import ValidationError
from core.sms_enrollment import begin_sms_enrollment, connect_sms, sms_user_for_phone
from core.time_utilities import now_datetime_full, format_timestamp, TIMESTAMP_FULL
from storage.sms_state import SmsState
from tests.behavior.test_twilio_sms import live as sms_live_fixture, request, PHONE
from tests.unit.test_web_account_service import gateway as website_fixture, request_code, verify

sms_connection = sms_live_fixture
website_gateway = website_fixture

pytestmark = [pytest.mark.behavior, pytest.mark.communication, pytest.mark.user]


@pytest.fixture
def enrollment(monkeypatch, tmp_path):
    state = SmsState(tmp_path / "enrollment.sqlite3")
    accounts = {"one": {"account_status": "active", "subscription_status": "active", "subscription_plan": "phone", "billing_livemode": True, "phone": PHONE}}
    monkeypatch.setattr("core.sms_enrollment.SmsState", lambda: state)
    monkeypatch.setattr("core.web_sms.SmsState", lambda: state)
    monkeypatch.setattr("core.sms_enrollment.sms_available", lambda: True)
    monkeypatch.setattr("core.web_sms.sms_available", lambda: True)
    monkeypatch.setattr("core.sms_enrollment.get_user_data", lambda uid, *_: {"account": accounts.get(uid, {})})

    def save(uid, patch, **_kwargs):
        accounts[uid].update(patch)
        return True

    monkeypatch.setattr("core.sms_enrollment.update_user_account", save)
    return state, accounts


@pytest.mark.parametrize("status,channel,allowed", [
    ("trialing", "discord", True), ("trialing", "email", True), ("trialing", "sms", False),
    ("active", "sms", True), ("past_due", "sms", False), ("canceled", "sms", False),
    ("comped", "sms", False), ("active", "email", True),
])
def test_channel_plan_rules(status, channel, allowed):
    assert channel_allowed({"subscription_status": status, "subscription_plan": "phone", "billing_livemode": True}, channel) is allowed


@pytest.mark.parametrize("plan,allowed", [("discord", False), ("phone", True), ("", False)])
def test_sms_requires_phone_tier_even_when_paid(plan, allowed):
    assert channel_allowed({"subscription_status": "active", "subscription_plan": plan, "billing_livemode": True}, "sms") is allowed
    assert channel_allowed({"subscription_status": "active", "subscription_plan": plan, "billing_livemode": True}, "discord")


def test_test_mode_subscription_cannot_unlock_real_sms():
    assert not channel_allowed({"subscription_status": "active", "subscription_plan": "phone", "billing_livemode": False}, "sms")


def test_enrollment_requires_matching_phone_proof_consent_and_paid_account(enrollment):
    state, accounts = enrollment
    with pytest.raises(ValidationError):
        begin_sms_enrollment(PHONE, False, "one")
    token = begin_sms_enrollment(PHONE, True, "one")
    assert not state.verify_enrollment("+15555550199", token)
    with pytest.raises(ValidationError):
        connect_sms("one", PHONE, token, True, "one")
    assert state.verify_enrollment(PHONE, token)
    assert not state.enrollment_verified(PHONE, token, "another-account")
    accounts["one"]["subscription_status"] = "trialing"
    with pytest.raises(ValidationError):
        connect_sms("one", PHONE, token, True, "one")
    accounts["one"]["subscription_status"] = "active"
    assert connect_sms("one", PHONE, token, True, "one")
    assert sms_user_for_phone(PHONE) == "one"
    assert not state.enrollment_verified(PHONE, token, "one")
    assert SmsState(state.path).enrolled_user(PHONE) == "one"


def test_expired_proof_and_phone_ownership_conflict_fail_closed(enrollment, monkeypatch):
    state, accounts = enrollment
    token = state.begin_enrollment(PHONE, "one")
    assert state.verify_enrollment(PHONE, token)
    assert state.bind_enrollment("one", PHONE, token, "one")
    accounts["two"] = {"account_status": "active", "subscription_status": "active", "subscription_plan": "phone", "billing_livemode": True}
    token2 = state.begin_enrollment(PHONE, "two")
    assert state.verify_enrollment(PHONE, token2)
    with pytest.raises(ValidationError):
        connect_sms("two", PHONE, token2, True, "two")
    future = format_timestamp(now_datetime_full() + timedelta(minutes=16), TIMESTAMP_FULL)
    monkeypatch.setattr("storage.sms_state.now_timestamp_full", lambda: future)
    assert not state.enrollment_verified(PHONE, token2, "two")
    assert not state.bind_enrollment("two", PHONE, token2, "two")


def test_revocation_preserves_stop_history_and_downgrade_blocks_sms(enrollment):
    state, accounts = enrollment
    token = state.begin_enrollment(PHONE, "one")
    state.verify_enrollment(PHONE, token)
    assert connect_sms("one", PHONE, token, True, "one")
    state.set_stopped(PHONE, True)
    state.add_context(PHONE, "task_reminder", "task-one")
    accounts["one"]["subscription_status"] = "past_due"
    assert sms_user_for_phone(PHONE) is None
    assert sms_user_for_phone(PHONE, require_paid=False) == "one"
    state.disconnect_enrollment("one")
    assert state.enrolled_user(PHONE) is None
    assert state.contexts(PHONE) == []
    assert state.stopped(PHONE)


def test_saved_phone_changes_and_suspension_revoke_routing(enrollment):
    state, accounts = enrollment
    token = state.begin_enrollment(PHONE, "one")
    state.verify_enrollment(PHONE, token)
    assert connect_sms("one", PHONE, token, True, "one")
    accounts["one"]["phone"] = "+15555550199"
    assert sms_user_for_phone(PHONE) is None
    accounts["one"]["phone"] = PHONE
    accounts["one"]["account_status"] = "suspended"
    assert sms_user_for_phone(PHONE) is None


def test_connection_retry_preserves_consent_and_does_not_bypass_revocation(enrollment):
    state, accounts = enrollment
    token = begin_sms_enrollment(PHONE, True, "one")
    assert state.verify_enrollment(PHONE, token)
    assert connect_sms("one", PHONE, token, True, "one")
    before = state.export_user("one")["enrollments"]
    state.set_stopped(PHONE, True)
    assert connect_sms("one", PHONE, token, True, "one")
    assert state.export_user("one")["enrollments"] == before
    assert state.stopped(PHONE)
    with pytest.raises(ValidationError):
        connect_sms("one", PHONE, token, False, "one")
    with pytest.raises(ValidationError):
        connect_sms("one", PHONE, token, True, "another-owner")
    accounts["one"]["account_status"] = "suspended"
    with pytest.raises(ValidationError):
        connect_sms("one", PHONE, token, True, "one")
    accounts["one"]["account_status"] = "active"
    state.disconnect_enrollment("one")
    with pytest.raises(ValidationError):
        connect_sms("one", PHONE, token, True, "one")


def test_repeated_connection_requests_are_throttled(enrollment):
    _state, _accounts = enrollment
    begin_sms_enrollment(PHONE, True, "one")
    with pytest.raises(ValidationError, match="one minute"):
        begin_sms_enrollment("+15555550199", True, "one")


def test_trial_sms_delivery_is_blocked_before_channel_submission(monkeypatch):
    from communication.core.channel_orchestrator import CommunicationManager
    from unittest.mock import MagicMock

    monkeypatch.setattr("core.get_user_data", lambda *args: {"account": {"subscription_status": "trialing"}})
    manager = MagicMock()
    assert CommunicationManager.send_message_sync(manager, "sms", "recipient", "body", user_id="trial-user") is False
    manager._check_logging_health.assert_not_called()


def test_signed_link_proves_phone_without_running_account_commands(sms_connection, monkeypatch):
    _bot, transport = sms_connection
    token = transport.state.begin_enrollment("+15555550199", "new-user")
    route = Mock()
    monkeypatch.setattr(transport, "route", route)
    assert request(transport, "LINK " + token, From="+15555550199") == 200
    assert transport.state.enrollment_verified("+15555550199", token, "new-user")
    assert transport.state.enrolled_user("+15555550199") is None
    route.assert_not_called()
    transport.client.messages.create.assert_not_called()


def test_two_accounts_route_by_verified_phone_and_preserve_stop_after_downgrade(sms_connection, monkeypatch):
    _bot, transport = sms_connection
    second = "+15555550199"
    state = transport.state
    token = state.begin_enrollment(second)
    state.verify_enrollment(second, token)
    state.bind_enrollment("second-user", second, token)
    accounts = {
        "pilot-test": {"phone": PHONE, "account_status": "active", "subscription_status": "active", "subscription_plan": "phone", "billing_livemode": True},
        "second-user": {"phone": second, "account_status": "active", "subscription_status": "active", "subscription_plan": "phone", "billing_livemode": True},
    }
    monkeypatch.setattr("core.sms_enrollment.get_user_data", lambda uid, *_: {"account": accounts[uid]})
    route = Mock(return_value="Saved")
    monkeypatch.setattr(transport, "route", route)
    assert request(transport, "hello", From=second) == 200
    route.assert_called_once_with("hello", "second-user", second)
    assert not transport.send(second, "Private first-account data", user_id="pilot-test")
    accounts["second-user"]["subscription_status"] = "trialing"
    assert request(transport, "STOP", From=second, sid="SM" + "b" * 32) == 200
    assert state.stopped(second)
    assert not transport.send(second, "Blocked", user_id="second-user")


@pytest.mark.asyncio
async def test_authenticated_website_connection_and_trial_rejection(website_gateway, enrollment, monkeypatch):
    client, fake_accounts, sent, _now = website_gateway
    state, accounts = enrollment
    accounts["existing"] = fake_accounts.users["existing"]
    accounts["existing"]["subscription_status"] = "active"
    accounts["existing"]["subscription_plan"] = "phone"
    accounts["existing"]["billing_livemode"] = True
    token = (await (await request_code(client)).json())["challenge"]
    assert (await verify(client, token, sent[-1][1])).status == 200
    headers = {"Origin": "http://localhost:8080"}
    response = await client.post("/api/sms/enrollment", headers=headers,
                                 json={"action": "start", "phone": PHONE, "consent": True})
    assert response.status == 200
    proof = (await response.json())["token"]
    payload = {"action": "connect", "phone": PHONE, "consent": True, "token": proof}
    assert (await client.post("/api/sms/enrollment", headers=headers, json=payload)).status == 400
    state.verify_enrollment(PHONE, proof)
    assert (await client.post("/api/sms/enrollment", headers=headers, json=payload)).status == 200
    before = state.export_user("existing")["enrollments"]
    assert (await client.post("/api/sms/enrollment", headers=headers, json=payload)).status == 200
    assert state.export_user("existing")["enrollments"] == before
    assert (await (await client.get("/api/sms/enrollment")).json())["connected"]
    accounts["existing"]["subscription_status"] = "trialing"
    info = await (await client.get("/api/sms/enrollment")).json()
    assert not info["eligible"] and info["connected"]
    assert (await client.post("/api/sms/enrollment", headers=headers,
                              json={"action": "start", "phone": PHONE, "consent": True})).status == 400
    state.set_stopped(PHONE, True)
    state.begin_delivery_attempt("existing")
    state.begin_delivery_attempt("another-user")
    info = await (await client.get("/api/sms/enrollment")).json()
    assert info["stopped"] is True
    assert info["delivery"]["unresolved_attempts"] == 1
    change_preferences = Mock(return_value=True)
    monkeypatch.setattr("core.update_user_preferences", change_preferences)
    assert (await client.post("/api/sms/enrollment", headers=headers,
                              json={"action": "disconnect"})).status == 200
    assert state.enrolled_user(PHONE) is None
    assert state.stopped(PHONE)
    change_preferences.assert_not_called()
