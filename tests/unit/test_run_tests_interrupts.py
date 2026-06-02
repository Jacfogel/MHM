import signal
import types

import pytest

import run_tests as rt


pytestmark = [pytest.mark.user]


@pytest.fixture(autouse=True)
def _two_tap_stop_for_tests(monkeypatch):
    """Keep unit tests fast: production default is 5 taps."""
    monkeypatch.setattr(rt, "_SIGINT_TAPS_TO_STOP", 2, raising=False)


@pytest.mark.unit
@pytest.mark.user
def test_interrupt_handler_single_sigint_ignored_with_message(monkeypatch, capsys):
    """First SIGINT should be ignored and show remaining tap count."""
    monkeypatch.setattr(rt, "_interrupt_requested", False, raising=False)
    monkeypatch.setattr(rt, "_sigint_count_in_window", 0, raising=False)
    monkeypatch.setattr(rt, "_last_sigint_count_time", None, raising=False)
    monkeypatch.setattr(
        rt, "_captured_output_lines", ["tests\\foo\\test_bar.py .... [ 10%]"], raising=False
    )

    assert isinstance(rt.time, types.ModuleType)
    monkeypatch.setattr(rt.time, "time", lambda: 1000.0, raising=False)

    rt.interrupt_handler(signal.SIGINT, None)
    out = capsys.readouterr().out

    assert "[SIGINT]" in out
    assert "1 more within" in out
    assert not rt._interrupt_requested
    assert rt._sigint_count_in_window == 1
    assert rt._last_sigint_count_time == 1000.0


@pytest.mark.unit
@pytest.mark.user
def test_interrupt_handler_burst_sigint_within_debounce_is_ignored(monkeypatch, capsys):
    """Duplicate SIGINT bursts (spurious on Windows) must not increment the tap count."""
    monkeypatch.setattr(rt, "_interrupt_requested", False, raising=False)
    monkeypatch.setattr(rt, "_sigint_count_in_window", 1, raising=False)
    monkeypatch.setattr(rt, "_last_sigint_count_time", 1000.0, raising=False)
    monkeypatch.setattr(rt, "_captured_output_lines", [], raising=False)
    monkeypatch.setattr(rt.time, "time", lambda: 1000.1, raising=False)

    rt.interrupt_handler(signal.SIGINT, None)
    out = capsys.readouterr().out

    assert out == ""
    assert not rt._interrupt_requested
    assert rt._sigint_count_in_window == 1


@pytest.mark.unit
@pytest.mark.user
def test_interrupt_handler_second_sigint_within_window_sets_interrupt(monkeypatch, capsys):
    """Second distinct SIGINT within the window should request interrupt (when taps=2)."""
    monkeypatch.setattr(rt, "_interrupt_requested", False, raising=False)
    monkeypatch.setattr(rt, "_sigint_count_in_window", 1, raising=False)
    monkeypatch.setattr(rt, "_last_sigint_count_time", 1000.0, raising=False)
    monkeypatch.setattr(rt, "_captured_output_lines", [], raising=False)
    monkeypatch.setattr(rt.time, "time", lambda: 1000.5, raising=False)

    rt.interrupt_handler(signal.SIGINT, None)
    out = capsys.readouterr().out

    assert "[INTERRUPT]" in out
    assert "stopping run" in out
    assert rt._interrupt_requested
    assert rt._sigint_count_in_window == 0
    assert rt._last_sigint_count_time is None


@pytest.mark.unit
@pytest.mark.user
def test_interrupt_handler_sigint_after_window_resets_count(monkeypatch, capsys):
    """SIGINT after the window expires should restart the tap counter."""
    monkeypatch.setattr(rt, "_interrupt_requested", False, raising=False)
    monkeypatch.setattr(rt, "_sigint_count_in_window", 1, raising=False)
    monkeypatch.setattr(rt, "_last_sigint_count_time", 1000.0, raising=False)
    monkeypatch.setattr(rt, "_captured_output_lines", [], raising=False)
    monkeypatch.setattr(rt.time, "time", lambda: 1003.5, raising=False)

    rt.interrupt_handler(signal.SIGINT, None)
    out = capsys.readouterr().out

    assert "[SIGINT]" in out
    assert "1 more within" in out
    assert not rt._interrupt_requested
    assert rt._sigint_count_in_window == 1
    assert rt._last_sigint_count_time == 1003.5


@pytest.mark.unit
@pytest.mark.user
def test_interrupt_handler_five_taps_required_by_default(monkeypatch, capsys):
    """Production default needs five distinct taps before stopping."""
    monkeypatch.setattr(rt, "_SIGINT_TAPS_TO_STOP", 5, raising=False)
    monkeypatch.setattr(rt, "_interrupt_requested", False, raising=False)
    monkeypatch.setattr(rt, "_sigint_count_in_window", 0, raising=False)
    monkeypatch.setattr(rt, "_last_sigint_count_time", None, raising=False)
    monkeypatch.setattr(rt, "_captured_output_lines", [], raising=False)

    times = [1000.0, 1000.5, 1001.0, 1001.5, 1002.0]
    index = {"i": 0}

    def _time():
        i = index["i"]
        index["i"] = min(i + 1, len(times) - 1)
        return times[i]

    monkeypatch.setattr(rt.time, "time", _time, raising=False)

    for _ in range(4):
        rt.interrupt_handler(signal.SIGINT, None)
        assert not rt._interrupt_requested

    rt.interrupt_handler(signal.SIGINT, None)
    out = capsys.readouterr().out

    assert rt._interrupt_requested
    assert "[INTERRUPT]" in out
    assert "5 Ctrl+C" in out
