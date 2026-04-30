"""Unit tests for ``checkin_runtime_timestamp`` helper."""

import pytest

from core.response_tracking import checkin_runtime_timestamp


@pytest.mark.unit
@pytest.mark.core
def test_checkin_runtime_timestamp_prefers_submitted_at():
    assert (
        checkin_runtime_timestamp(
            {"submitted_at": "2026-01-02 10:00:00", "timestamp": "1999-01-01 00:00:00"}
        )
        == "2026-01-02 10:00:00"
    )


@pytest.mark.unit
@pytest.mark.core
def test_checkin_runtime_timestamp_falls_back_to_top_level_timestamp():
    assert checkin_runtime_timestamp({"timestamp": "2026-01-03 12:00:00"}) == "2026-01-03 12:00:00"


@pytest.mark.unit
@pytest.mark.core
def test_checkin_runtime_timestamp_empty_when_missing():
    assert checkin_runtime_timestamp({}) == ""


@pytest.mark.unit
@pytest.mark.core
def test_checkin_runtime_timestamp_returns_empty_when_stringify_fails():
    """Hostile values are logged and suppressed via @handle_errors (default_return=\"\")."""

    class _BadStr:
        def __str__(self):
            raise ValueError("not a displayable timestamp")

    assert checkin_runtime_timestamp({"submitted_at": _BadStr()}) == ""
