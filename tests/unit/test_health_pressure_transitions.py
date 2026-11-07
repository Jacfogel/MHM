"""Health guidance transitions must respect freshness and immediate user controls."""

from datetime import datetime

import pytest

from core import health_signals
from core.message_pressure import MessagePressureSettings, resolve_message_pressure

pytestmark = [pytest.mark.unit, pytest.mark.communication]


@pytest.fixture
def health_pressure_state(monkeypatch):
    state = {
        "enabled": True,
        "use_in_messages": True,
        "signals": [],
        "energy": None,
        "cooldown": False,
    }

    def read_user(_user_id, kind):
        if kind == "account":
            return {
                "account": {
                    "features": {
                        "google_health": "enabled" if state["enabled"] else "disabled"
                    }
                }
            }
        return {
            "preferences": {
                "health_personalization": {"use_in_messages": state["use_in_messages"]}
            }
        }

    monkeypatch.setattr(health_signals, "get_user_data", read_user)
    monkeypatch.setattr(
        health_signals, "load_health_signals", lambda _: {"signals": state["signals"]}
    )
    monkeypatch.setattr(
        health_signals, "now_datetime_full", lambda: datetime(2026, 11, 7, 12)
    )
    monkeypatch.setattr(
        "scheduler.user_timezone.user_local_now_naive",
        lambda _: datetime(2026, 11, 7, 12),
    )
    monkeypatch.setattr(
        "core.message_pressure.load_message_pressure_settings",
        lambda _: MessagePressureSettings(),
    )
    monkeypatch.setattr(
        "checkins.checkin_service.today_checkin_energy", lambda _: state["energy"]
    )
    monkeypatch.setattr(
        "checkins.checkin_service.recent_low_energy_cooldown",
        lambda *a, **kw: state["cooldown"],
    )
    return state


def signal(day="2026-11-07", *, confidence="high", gentle=True):
    """Build an already-derived signal without raw wearable measurements."""
    return {
        "date": day,
        "confidence": confidence,
        "message_guidance": ["use_gentle_tone", "avoid_nagging_movement_prompts"]
        if gentle
        else [],
    }


def test_corrected_health_guidance_takes_effect_without_an_energy_cooldown(
    health_pressure_state,
):
    state = health_pressure_state
    state["signals"] = [signal()]
    before = resolve_message_pressure("u1")
    assert before.gentle and before.avoid_nagging
    assert not before.energy_cooldown

    state["signals"] = [signal(gentle=False)]
    after = resolve_message_pressure("u1")
    assert not after.gentle
    assert not after.avoid_nagging
    assert not after.energy_cooldown


@pytest.mark.parametrize("control", ["enabled", "use_in_messages"])
def test_disabling_health_support_removes_health_pressure_immediately(
    health_pressure_state, control
):
    state = health_pressure_state
    state["signals"] = [signal()]
    assert resolve_message_pressure("u1").gentle
    state[control] = False
    policy = resolve_message_pressure("u1")
    assert policy.guidance == ()
    assert not policy.gentle
    assert not policy.energy_cooldown


@pytest.mark.parametrize(
    "replacement",
    [[], [signal("2026-11-04")], [signal(confidence="low")], [signal("2026-11-08")]],
)
def test_unusable_health_data_does_not_retain_previous_pressure(
    health_pressure_state, replacement
):
    state = health_pressure_state
    state["signals"] = [signal()]
    assert resolve_message_pressure("u1").gentle
    state["signals"] = replacement
    policy = resolve_message_pressure("u1")
    assert not policy.gentle
    assert policy.guidance == ()
    assert not policy.energy_cooldown


def test_recent_health_fallback_stays_gentle_without_a_new_timer(health_pressure_state):
    health_pressure_state["signals"] = [signal("2026-11-05")]
    policy = resolve_message_pressure("u1")
    assert policy.gentle and policy.avoid_nagging
    assert not policy.low_energy
    assert not policy.energy_cooldown


def test_future_signal_cannot_override_a_valid_recent_fallback(health_pressure_state):
    health_pressure_state["signals"] = [
        signal("2026-11-08", gentle=False),
        signal("2026-11-06"),
    ]
    policy = resolve_message_pressure("u1")
    assert policy.gentle and policy.avoid_nagging
    assert not policy.energy_cooldown


def test_checkin_recovery_hold_survives_health_opt_out(health_pressure_state):
    state = health_pressure_state
    state.update(signals=[signal()], energy=4, cooldown=True)
    state["use_in_messages"] = False
    policy = resolve_message_pressure("u1")
    assert policy.guidance == ()
    assert policy.gentle and policy.low_energy and policy.energy_cooldown
    assert "30 minutes" in policy.explanation
