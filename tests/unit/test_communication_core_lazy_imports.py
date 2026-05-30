"""Unit coverage for communication.core lazy package exports."""

from __future__ import annotations

import pytest


@pytest.mark.unit
@pytest.mark.communication
def test_communication_core_lazy_imports_resolve():
    import communication.core as core

    assert core.RetryManager is not None
    assert core.QueuedMessage is not None
    assert core.ChannelFactory is not None
    assert core.ChannelMonitor is not None
    assert core.welcome_manager is not None


@pytest.mark.unit
@pytest.mark.communication
def test_communication_core_unknown_attribute_raises():
    import communication.core as core

    with pytest.raises(AttributeError, match="has no attribute 'not_a_real_export'"):
        _ = core.not_a_real_export
