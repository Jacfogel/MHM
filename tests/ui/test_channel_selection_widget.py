"""Behavior tests for ChannelSelectionWidget get/set helpers."""

from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()

from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from ui.widgets.channel_selection_widget import ChannelSelectionWidget

pytestmark = [pytest.mark.ui]


@pytest.fixture(scope="module")
def qapp():
    """Provide a process-wide QApplication for widget tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_get_and_set_discord_channel(qapp):
    widget = ChannelSelectionWidget()
    widget.set_selected_channel("Discord", "123456")
    channel, value = widget.get_selected_channel()
    assert channel == "Discord"
    assert value == "123456"
    assert widget.get_all_contact_info()["discord_id"] == "123456"
    widget.deleteLater()


def test_whatsapp_selection_uses_independent_number_and_proof(qapp, monkeypatch, tmp_path):
    from storage.whatsapp_state import WhatsAppState

    state = WhatsAppState(tmp_path / "whatsapp.sqlite3")
    monkeypatch.setattr("core.whatsapp_enrollment.whatsapp_available", lambda: True)
    monkeypatch.setattr("core.whatsapp_enrollment.whatsapp_user_for_phone", lambda *_: None)
    monkeypatch.setattr("storage.whatsapp_state.WhatsAppState", lambda: state)
    widget = ChannelSelectionWidget()
    widget.whatsapp_owner = "account-one"
    widget.ui.radioButton_WhatsApp.setEnabled(True)
    widget.set_selected_channel("WhatsApp", "+15555550199")
    widget.ui.lineEdit_phone.setText("+15555550188")
    widget.ui.checkBox_whatsapp_consent.setChecked(True)
    widget.whatsapp_token = state.begin_enrollment("+15555550199", "account-one")
    assert not widget.whatsapp_selection_valid()
    assert state.verify_enrollment("+15555550199", widget.whatsapp_token)
    assert widget.whatsapp_selection_valid()
    assert widget.get_selected_channel() == ("WhatsApp", "+15555550199")
    assert widget.get_all_contact_info()["phone"] == "+15555550188"
    widget.ui.checkBox_whatsapp_consent.setChecked(False)
    assert not widget.whatsapp_selection_valid()
    widget.deleteLater()


def test_get_and_set_email_channel(qapp):
    widget = ChannelSelectionWidget()
    widget.set_selected_channel("Email", "user@example.com")
    channel, value = widget.get_selected_channel()
    assert channel == "Email"
    assert value == "user@example.com"
    assert widget.get_all_contact_info()["email"] == "user@example.com"
    widget.deleteLater()


def test_get_selected_channel_when_none_checked(qapp):
    widget = ChannelSelectionWidget()
    widget.ui.radioButton_Discord.setChecked(False)
    widget.ui.radioButton_Email.setChecked(False)
    channel, value = widget.get_selected_channel()
    assert channel is None
    assert value is None
    widget.deleteLater()


def test_sms_selection_retains_phone_and_requires_verification(qapp, monkeypatch):
    widget = ChannelSelectionWidget()
    widget.set_selected_channel("SMS", "+13065550101")
    assert widget.get_selected_channel() == ("SMS", "+13065550101")
    assert widget.get_all_contact_info()["phone"] == "+13065550101"
    monkeypatch.setattr("core.sms_enrollment.sms_available", lambda: True)
    assert not widget.sms_selection_valid()
    widget.ui.checkBox_sms_consent.setChecked(True)
    monkeypatch.setattr("storage.sms_state.SmsState.enrollment_verified", lambda *args: True)
    assert widget.sms_selection_valid()
    widget.deleteLater()


def test_set_contact_info_and_timezone(qapp):
    widget = ChannelSelectionWidget()
    widget.set_contact_info(
        email="a@example.com",
        discord_id="99",
        timezone="UTC",
    )
    info = widget.get_all_contact_info()
    assert info["email"] == "a@example.com"
    assert info["discord_id"] == "99"
    assert widget.get_timezone()
    widget.deleteLater()


def test_timezone_falls_back_to_utc_when_regina_missing(qapp):
    with patch(
        "ui.widgets.channel_selection_widget.get_timezone_options",
        return_value=["UTC", "America/New_York"],
    ):
        widget = ChannelSelectionWidget()
    assert widget.get_timezone() == "UTC"
    widget.set_timezone("new_york")
    assert "New_York" in widget.get_timezone()
    widget.deleteLater()


def test_timezone_warns_when_combo_missing(qapp):
    widget = ChannelSelectionWidget()
    del widget.ui.comboBox_timezone
    widget.populate_timezones()
    assert widget.get_timezone() == "America/Regina"
    widget.set_timezone("UTC")
    widget.deleteLater()
