import signal
import types

import pytest

import run_tests as rt


pytestmark = [pytest.mark.user_management]

@pytest.mark.unit
@pytest.mark.user_management
def test_interrupt_handler_single_sigint_ignored_with_message(monkeypatch, capsys):
    """First SIGINT should be ignored and prompt for a second within the window."""
    # Arrange: reset globals
    monkeypatch.setattr(rt, "_interrupt_requested", False, raising=False)
    monkeypatch.setattr(rt, "_last_sigint_time", None, raising=False)
    monkeypatch.setattr(
        rt, "_captured_output_lines", ["tests\\foo\\test_bar.py .... [ 10%]"], raising=False
    )

    # Patch time.time to a fixed value
    assert isinstance(rt.time, types.ModuleType)
    monkeypatch.setattr(rt.time, "time", lambda: 1000.0, raising=False)

    # Act
    rt.interrupt_handler(signal.SIGINT, None)
    out = capsys.readouterr().out

    # Assert: first SIGINT is ignored but message is printed and last_sigint_time is set
    assert "[SIGINT]" in out
    assert "Press Ctrl+C again within" in out
    assert not rt._interrupt_requested
    assert rt._last_sigint_time == 1000.0


@pytest.mark.unit
@pytest.mark.user_management
def test_interrupt_handler_second_sigint_within_window_sets_interrupt(monkeypatch, capsys):
    """Second SIGINT within the double-tap window should request interrupt."""
    # Arrange: simulate a previous SIGINT shortly before
    monkeypatch.setattr(rt, "_interrupt_requested", False, raising=False)
    monkeypatch.setattr(rt, "_last_sigint_time", 1000.0, raising=False)
    monkeypatch.setattr(rt, "_captured_output_lines", [], raising=False)

    monkeypatch.setattr(rt.time, "time", lambda: 1001.0, raising=False)

    # Act
    rt.interrupt_handler(signal.SIGINT, None)
    out = capsys.readouterr().out

    # Assert: interrupt requested and last_sigint_time cleared
    assert "[INTERRUPT]" in out
    assert "Second Ctrl+C within 2s - stopping run." in out
    assert rt._interrupt_requested
    assert rt._last_sigint_time is None


@pytest.mark.unit
@pytest.mark.user_management
def test_interrupt_handler_second_sigint_outside_window_behaves_like_first(monkeypatch, capsys):
    """A second SIGINT after the window should behave like a fresh first SIGINT."""
    # Arrange: previous SIGINT too far in the past
    monkeypatch.setattr(rt, "_interrupt_requested", False, raising=False)
    monkeypatch.setattr(rt, "_last_sigint_time", 1000.0, raising=False)
    monkeypatch.setattr(rt, "_captured_output_lines", [], raising=False)

    # Move time beyond the double-tap window
    monkeypatch.setattr(rt.time, "time", lambda: 1003.5, raising=False)

    # Act
    rt.interrupt_handler(signal.SIGINT, None)
    out = capsys.readouterr().out

    # Assert: treated as first SIGINT again (ignore + prompt), no interrupt requested
    assert "[SIGINT]" in out
    assert "Press Ctrl+C again within" in out
    assert not rt._interrupt_requested
    # last_sigint_time updated to new timestamp
    assert rt._last_sigint_time == 1003.5

