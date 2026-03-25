"""Unit tests for development_tools.shared.audit_signal_state (SIGINT multi-tap)."""

from unittest.mock import patch

import pytest

from development_tools.shared import audit_signal_state as sig


@pytest.fixture(autouse=True)
def _reset_sigint_state():
    sig.reset_audit_sigint_state()
    yield
    sig.reset_audit_sigint_state()


@pytest.mark.unit
def test_reset_clears_interrupt_and_counts(capsys):
    sig.handle_audit_sigint(2, None)
    sig.reset_audit_sigint_state()
    assert not sig.audit_sigint_requested()
    sig.handle_audit_sigint(2, None)
    out = capsys.readouterr().out
    assert "4 more" in out


@pytest.mark.unit
def test_handle_audit_sigint_requires_five_taps_within_window(capsys):
    """Five rapid taps set interrupt requested and print stop banner."""
    t = {"v": 0.0}

    def fake_time() -> float:
        t["v"] += 0.05
        return t["v"]

    with patch("development_tools.shared.audit_signal_state.time") as m_time:
        m_time.time = fake_time
        for _ in range(sig.AUDIT_SIGINT_TAPS_TO_STOP - 1):
            sig.handle_audit_sigint(2, None)
        assert not sig.audit_sigint_requested()
        sig.handle_audit_sigint(2, None)

    assert sig.audit_sigint_requested()
    out = capsys.readouterr().out
    assert "[INTERRUPT]" in out
    assert str(sig.AUDIT_SIGINT_TAPS_TO_STOP) in out


@pytest.mark.unit
def test_handle_audit_sigint_gap_resets_count(capsys):
    """SIGINTs farther apart than the window reset the tap counter."""
    times = iter([0.0, 10.0, 10.05])

    def fake_time() -> float:
        return next(times)

    with patch("development_tools.shared.audit_signal_state.time") as m_time:
        m_time.time = fake_time
        sig.handle_audit_sigint(2, None)
        sig.handle_audit_sigint(2, None)

    assert not sig.audit_sigint_requested()
    out = capsys.readouterr().out
    assert "[SIGINT]" in out
    assert out.count("4 more") >= 1


@pytest.mark.unit
def test_handle_audit_sigint_unknown_signal_name(capsys):
    """Invalid signal numbers fall back to SIG(n) in the user message."""
    with patch.object(sig.signal, "Signals", side_effect=ValueError("bad")):
        sig.handle_audit_sigint(999, None)
    assert "SIG(999)" in capsys.readouterr().out


@pytest.mark.unit
def test_record_audit_keyboard_interrupt_clears_handler_flag_first():
    """First call after handler ran consumes the handler flag and returns False."""
    t = {"v": 0.0}

    def fake_time() -> float:
        t["v"] += 0.05
        return t["v"]

    with patch("development_tools.shared.audit_signal_state.time") as m_time:
        m_time.time = fake_time
        for _ in range(sig.AUDIT_SIGINT_TAPS_TO_STOP):
            sig.handle_audit_sigint(2, None)

    assert sig.audit_sigint_requested()
    assert sig.record_audit_keyboard_interrupt() is False
    assert sig.record_audit_keyboard_interrupt() is True
