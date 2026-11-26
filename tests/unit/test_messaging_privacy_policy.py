"""Account isolation, retention, user schedules, and disconnect policy."""

from datetime import timedelta
from unittest.mock import Mock

import pytest

from core.time_utilities import (
    now_timestamp_full,
    now_datetime_full,
    format_timestamp,
    TIMESTAMP_FULL,
)
from storage.sms_state import SmsState
from storage.whatsapp_state import WhatsAppState

pytestmark = [pytest.mark.unit, pytest.mark.communication, pytest.mark.storage]


def enroll(state, uid, phone):
    with state.connection() as db:
        db.execute(
            "INSERT INTO enrollments VALUES (?, ?, ?, ?)",
            (phone, uid, now_timestamp_full(), now_timestamp_full()),
        )


@pytest.mark.parametrize("factory", [SmsState, WhatsAppState])
def test_submission_attempts_survive_restart_and_remain_account_scoped(tmp_path, factory):
    state = factory(tmp_path / "attempts.sqlite3")
    one = state.begin_delivery_attempt("one")
    two = state.begin_delivery_attempt("two")
    state.claim("needs-review", user_id="one")
    state.finish("needs-review", "reply_unconfirmed")
    restored = factory(state.path)
    assert restored.delivery_health("one") == {"unresolved_attempts": 1, "inbound_needing_review": 1}
    assert restored.delivery_health("two") == {"unresolved_attempts": 1, "inbound_needing_review": 0}
    assert restored.delivery_health("third")["unresolved_attempts"] == 0
    assert [row["id"] for row in restored.export_user("one")["delivery_attempts"]] == [one]
    restored.finish_delivery_attempt(one, "accepted", "provider-receipt")
    assert restored.delivery_health("one")["unresolved_attempts"] == 0
    restored.delete_user("one")
    assert restored.export_user("one")["delivery_attempts"] == []
    assert restored.export_user("two")["delivery_attempts"][0]["id"] == two


def test_attempt_retention_preserves_unconfirmed_and_interrupted_submissions(tmp_path):
    state = SmsState(tmp_path / "attempts.sqlite3")
    for outcome in ("accepted", "rejected", "unconfirmed", "submitting"):
        identifier = state.begin_delivery_attempt("one")
        if outcome != "submitting":
            state.finish_delivery_attempt(identifier, outcome)
    old = format_timestamp(now_datetime_full() - timedelta(days=91), TIMESTAMP_FULL)
    with state.connection() as db:
        db.execute("UPDATE delivery_attempts SET updated=?", (old,))
    state.cleanup_retention()
    assert {row["state"] for row in state.export_user("one")["delivery_attempts"]} == {"unconfirmed", "submitting"}


def test_invalid_submission_metadata_raises_project_data_errors(tmp_path):
    from core.error_handling import DataError

    state = SmsState(tmp_path / "attempts.sqlite3")
    with pytest.raises(DataError, match="account identity"):
        state.begin_delivery_attempt("")
    identifier = state.begin_delivery_attempt("one")
    with pytest.raises(DataError, match="Unknown phone submission outcome"):
        state.finish_delivery_attempt(identifier, "invalid")
    assert state.export_user("one")["delivery_attempts"][0]["state"] == "submitting"


@pytest.mark.parametrize("factory", [SmsState, WhatsAppState])
def test_export_and_deletion_keep_other_account_and_replay_protection(
    tmp_path, factory
):
    state = factory(tmp_path / "state.sqlite3")
    enroll(state, "one", "+13065550101")
    enroll(state, "two", "+13065550102")
    for uid, phone in [("one", "+13065550101"), ("two", "+13065550102")]:
        assert state.claim("in-" + uid, user_id=uid)
        state.finish("in-" + uid, "handled")
        state.record_outbound("out-" + uid, "delivered", user_id=uid)
        state.add_context(phone, "checkin")
    state.set_stopped("+13065550101", True)
    if isinstance(state, WhatsAppState):
        state.save_pending("p1", "+13065550101", "one", "private one", "checkin", "")
        state.save_pending("p2", "+13065550102", "two", "private two", "checkin", "")
    exported = state.export_user("one")
    assert [r["sid"] for r in exported["outbound"]] == ["out-one"]
    assert [r["sid"] for r in exported["inbound"]] == ["in-one"]
    assert "digest" not in str(exported)
    state.delete_user("one")
    assert not state.enrolled_user("+13065550101")
    assert state.enrolled_user("+13065550102") == "two"
    assert state.export_user("one")["outbound"] == []
    assert not state.claim("in-one")
    assert state.stopped("+13065550101")
    assert [r["sid"] for r in state.export_user("two")["outbound"]] == ["out-two"]
    if isinstance(state, WhatsAppState):
        assert state.pending("+13065550101", "one") == []
        assert state.pending("+13065550102", "two")[0][1] == "private two"


def test_transport_retention_keeps_uncertain_records_and_duplicate_ids(tmp_path):
    state = SmsState(tmp_path / "state.sqlite3")
    state.claim("in", user_id="one")
    state.finish("in", "handled")
    state.record_outbound("done", "delivered", user_id="one")
    state.record_outbound("uncertain", "accepted", user_id="one")
    old = format_timestamp(now_datetime_full() - timedelta(days=91), TIMESTAMP_FULL)
    with state.connection() as db:
        db.execute("UPDATE outbound SET updated=?", (old,))
        db.execute("UPDATE inbound SET updated=?", (old,))
    state.cleanup_retention()
    assert [r["sid"] for r in state.export_user("one")["outbound"]] == ["uncertain"]
    assert state.export_user("one")["inbound"] == []
    assert not state.claim("in")


def test_pending_content_expires_after_24_hours(tmp_path):
    state = WhatsAppState(tmp_path / "state.sqlite3")
    state.save_pending("old", "+13065550101", "one", "expired", "checkin", "")
    state.save_pending("new", "+13065550101", "one", "current", "checkin", "")
    with state.connection() as db:
        db.execute(
            "UPDATE pending SET created=? WHERE id='old'",
            (
                format_timestamp(
                    now_datetime_full() - timedelta(hours=25), TIMESTAMP_FULL
                ),
            ),
        )
    assert [r[0] for r in state.pending("+13065550101", "one")] == ["new"]


def test_account_delete_stops_on_storage_failure(tmp_path, monkeypatch):
    from storage import user_data_backup as backup

    user_dir = tmp_path / "one"
    user_dir.mkdir()
    (user_dir / "account.json").write_text("{}")
    state = Mock()
    state.delete_user.side_effect = OSError("locked")
    monkeypatch.setattr(
        "storage.phone_state_lifecycle.existing_phone_states", lambda: {"sms": state}
    )
    monkeypatch.setattr(backup, "get_user_message_files", lambda uid: {})
    monkeypatch.setattr(backup, "get_user_data_dir", lambda uid: str(user_dir))
    assert backup.delete_user_completely("one", create_backup=False) is False
    assert user_dir.exists()


def test_unlink_discord_does_not_enroll_email(monkeypatch):
    from core.web_account_service import MHMAccounts

    repo = MHMAccounts()
    monkeypatch.setattr(
        repo,
        "documents",
        lambda uid: {
            "account": {
                "email": "one@example.com",
                "discord_user_id": "123",
                "chat_id": "123",
            },
            "preferences": {"channel": {"type": "discord"}},
        },
    )
    saved = {}

    def save(uid, docs, **kwargs):
        saved.update(docs)
        return True

    monkeypatch.setattr("core.save_user_data_transaction", save)
    assert repo.unlink_discord("one")
    assert saved["preferences"]["channel"]["type"] == "discord"
    assert saved["account"]["chat_id"] == ""
    assert saved["account"]["discord_user_id"] == ""


def test_storage_export_and_delete_include_phone_records(tmp_path, monkeypatch):
    from storage import user_data_backup as backup

    state = WhatsAppState(tmp_path / "state.sqlite3")
    enroll(state, "one", "+13065550101")
    state.save_pending("pending", "+13065550101", "one", "private", "checkin", "")
    state.record_outbound("out", "delivered", user_id="one")
    user_dir = tmp_path / "one"
    user_dir.mkdir()
    monkeypatch.setattr(
        "storage.phone_state_lifecycle.existing_phone_states", lambda: {"whatsapp": state}
    )
    monkeypatch.setattr(backup, "get_user_info_for_data_manager", lambda uid: {})
    monkeypatch.setattr(backup, "get_user_message_files", lambda uid: {})
    monkeypatch.setattr(
        backup, "get_user_file_path", lambda uid, kind: str(user_dir / (kind + ".json"))
    )
    monkeypatch.setattr(backup, "get_user_data_dir", lambda uid: str(user_dir))
    monkeypatch.setattr(backup, "remove_from_index", lambda *a, **kw: True)
    exported = backup.export_user_data("one")
    assert exported["phone_channels"]["whatsapp"]["pending"][0]["body"] == "private"
    assert backup.delete_user_completely("one", create_backup=False) is True
    assert not user_dir.exists()
    assert state.export_user("one")["pending"] == []
    assert state.export_user("one")["outbound"] == []


def test_delete_stopped_number_removes_raw_number_but_keeps_suppression(tmp_path):
    state = SmsState(tmp_path / "state.sqlite3")
    phone = "+13065550101"
    enroll(state, "one", phone)
    state.set_stopped(phone, True)
    state.delete_user("one")
    with state.connection() as db:
        assert (
            db.execute("SELECT * FROM optouts WHERE phone=?", (phone,)).fetchall() == []
        )
    assert state.stopped(phone)
    state.set_stopped(phone, False)
    assert not state.stopped(phone)


def test_existing_pending_rows_are_migrated_without_loss(tmp_path):
    import sqlite3

    path = tmp_path / "old.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute(
            "CREATE TABLE pending (id TEXT PRIMARY KEY,phone TEXT,user_id TEXT,body TEXT,kind TEXT,task_id TEXT)"
        )
        db.execute(
            "INSERT INTO pending VALUES ('old','+13065550101','one','keep me','checkin','')"
        )
    state = WhatsAppState(path)
    assert state.pending("+13065550101", "one")[0][1] == "keep me"
    assert state.export_user("one")["pending"][0]["created"]


@pytest.mark.parametrize("category", ["motivational", "checkin"])
def test_user_schedules_do_not_consult_night_morning_clocks(monkeypatch, category):
    from communication.core.channel_orchestrator import CommunicationManager
    from communication.core.message_send_result import MessageSendResult

    monkeypatch.setattr(
        "core.message_pressure.user_quiet_mode_is_active", lambda uid: False
    )
    phrase_defaults = Mock(
        side_effect=AssertionError("Phrase clocks must not suppress user schedules")
    )
    monkeypatch.setattr(
        "core.natural_language_defaults.get_natural_language_defaults", phrase_defaults
    )
    monkeypatch.setattr(
        "communication.core.channel_orchestrator.get_user_data",
        lambda *a, **kw: {"preferences": {"channel": {"type": "discord"}}},
    )
    manager = Mock()
    manager.get_recipient_for_service.return_value = "discord_user:one"
    manager.checkin_dispatcher.handle_scheduled_checkin.return_value = (
        MessageSendResult.sent("one", "checkin")
    )
    manager.predefined_dispatcher.send_predefined_message.return_value = (
        True,
        "Scheduled by you",
    )
    result = CommunicationManager.handle_message_sending(
        manager, "one", category, is_scheduled_trigger=True, allow_deferral=False
    )
    assert result.status == MessageSendResult.sent("one", category).status
    manager.get_recipient_for_service.assert_called_once()
    phrase_defaults.assert_not_called()


def test_phone_store_discovery_opens_only_existing_databases(tmp_path, monkeypatch):
    from storage.phone_state_lifecycle import existing_phone_states

    monkeypatch.setattr("core.config.BASE_DATA_DIR", str(tmp_path))
    assert existing_phone_states() == {}
    SmsState(tmp_path / "sms_state.sqlite3")
    assert set(existing_phone_states()) == {"sms"}
    assert not (tmp_path / "whatsapp_state.sqlite3").exists()
    WhatsAppState(tmp_path / "whatsapp_state.sqlite3")
    assert set(existing_phone_states()) == {"sms", "whatsapp"}
