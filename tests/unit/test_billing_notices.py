from datetime import datetime
from unittest.mock import MagicMock

import pytest

from core.billing_notices import pending_billing_notice, process_billing_notices

pytestmark = [pytest.mark.unit, pytest.mark.scheduler]


def test_trial_notice_is_sent_once_inside_three_day_window():
    account = {
        "subscription_status": "trialing",
        "trial_ends_at": "2026-10-11 12:00:00",
        "billing_notice_keys": [],
    }
    notice = pending_billing_notice(account, now=datetime(2026, 10, 9, 12, 0, 0))
    assert notice is not None
    key, message = notice
    assert key == "trial-ending:2026-10-11 12:00:00"
    assert "2 days" in message

    account["billing_notice_keys"] = [key]
    assert (
        pending_billing_notice(account, now=datetime(2026, 10, 9, 12, 0, 0))
        is None
    )


def test_failed_payment_has_attention_then_paused_notice():
    account = {
        "subscription_status": "past_due",
        "billing_grace_ends_at": "2026-10-10 12:00:00",
        "billing_notice_keys": [],
    }
    attention = pending_billing_notice(account, now=datetime(2026, 10, 9, 12, 0, 0))
    assert attention is not None
    assert attention[0].startswith("payment-attention:")

    account["billing_notice_keys"] = [attention[0]]
    paused = pending_billing_notice(account, now=datetime(2026, 10, 10, 12, 0, 1))
    assert paused is not None
    assert paused[0].startswith("payment-paused:")
    assert "paused" in paused[1]


def test_notice_processor_persists_key_only_after_delivery(monkeypatch):
    import core

    account = {
        "subscription_status": "canceled",
        "stripe_subscription_id": "sub_1",
        "billing_notice_keys": [],
    }
    saved = []
    monkeypatch.setattr(core, "get_all_user_ids", lambda: ["user-1"])
    monkeypatch.setattr(
        core, "get_user_data", lambda *_args, **_kwargs: {"account": account}
    )
    monkeypatch.setattr(
        core,
        "update_user_account",
        lambda user_id, updates, auto_create=False: saved.append(
            (user_id, updates, auto_create)
        )
        or True,
    )
    delivery = MagicMock()
    delivery.send_account_notice.return_value = True

    assert process_billing_notices(delivery) == 1
    delivery.send_account_notice.assert_called_once()
    assert saved[0][1]["billing_notice_keys"] == ["subscription-canceled:sub_1"]
    assert saved[0][2] is False
