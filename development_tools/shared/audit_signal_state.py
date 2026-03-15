"""
Shared state and handler for audit SIGINT (multi-tap to stop).

Requires multiple SIGINTs within the time window to stop the audit. This reduces
false stops from spurious control events on Windows (e.g. from pytest/coverage
subprocesses during Tier 3) when the user has not pressed Ctrl+C.
"""

import signal
import time

# Time window (seconds). We require this many SIGINTs within the window to stop.
AUDIT_SIGINT_DOUBLE_TAP_SECONDS = 2.0
# Number of SIGINTs within window required to request stop. Set to 5 to better
# withstand propagation from coverage/test subprocesses during full audit.
AUDIT_SIGINT_TAPS_TO_STOP = 5

_last_sigint_time: float | None = None
_sigint_count_in_window: int = 0
_interrupt_requested: bool = False
# True when the signal handler just ran; clear when record_audit_keyboard_interrupt sees it
_first_sigint_handled_by_handler: bool = False


def reset_audit_sigint_state() -> None:
    """Reset state at start of each audit run (e.g. start of Tier 3)."""
    global _last_sigint_time, _sigint_count_in_window, _interrupt_requested, _first_sigint_handled_by_handler
    _last_sigint_time = None
    _sigint_count_in_window = 0
    _interrupt_requested = False
    _first_sigint_handled_by_handler = False


def audit_sigint_requested() -> bool:
    """True if enough interrupts within window requested audit stop."""
    return _interrupt_requested


def handle_audit_sigint(signum: int, frame: object | None) -> None:
    """
    Handle SIGINT during audit: require multiple taps within window to stop.
    Reduces false stops from Windows control-event propagation from child processes.
    """
    global _last_sigint_time, _sigint_count_in_window, _interrupt_requested, _first_sigint_handled_by_handler
    now = time.time()
    if _last_sigint_time is not None and (now - _last_sigint_time) > AUDIT_SIGINT_DOUBLE_TAP_SECONDS:
        _sigint_count_in_window = 0
    _sigint_count_in_window += 1
    _last_sigint_time = now
    _first_sigint_handled_by_handler = True
    if _sigint_count_in_window >= AUDIT_SIGINT_TAPS_TO_STOP:
        _interrupt_requested = True
        _sigint_count_in_window = 0
        _last_sigint_time = None
        print(
            f"\n[INTERRUPT] {AUDIT_SIGINT_TAPS_TO_STOP} Ctrl+C within {int(AUDIT_SIGINT_DOUBLE_TAP_SECONDS)}s - stopping audit."
        )
        return
    try:
        sig_name = signal.Signals(signum).name
    except Exception:
        sig_name = f"SIG({signum})"
    remaining = AUDIT_SIGINT_TAPS_TO_STOP - _sigint_count_in_window
    print(
        f"\n[SIGINT] Received {sig_name} - ignoring ({remaining} more within {int(AUDIT_SIGINT_DOUBLE_TAP_SECONDS)}s to stop)."
    )


def record_audit_keyboard_interrupt() -> bool:
    """
    Call when a KeyboardInterrupt was caught (e.g. in a worker or as_completed).
    Returns True only if the handler already set stop (e.g. user did 3 taps).
    Ignores propagated KeyboardInterrupt from workers so spurious events don't stop the audit.
    """
    global _first_sigint_handled_by_handler
    if _first_sigint_handled_by_handler:
        _first_sigint_handled_by_handler = False
        return False
    return _interrupt_requested
