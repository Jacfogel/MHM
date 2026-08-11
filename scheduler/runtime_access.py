"""Process-wide scheduler manager handle for domain modules.

Domain code (e.g. tasks) should depend on this narrow accessor instead of
importing the MHMService composition root. The service registers the live
SchedulerManager during start and clears it on shutdown.
"""

from __future__ import annotations

from typing import Any

from core.error_handling import handle_errors

_scheduler_manager: Any | None = None


@handle_errors("setting scheduler manager runtime handle", default_return=None)
def set_scheduler_manager(manager: Any | None) -> None:
    """Register the live SchedulerManager for this process (or clear with None)."""
    global _scheduler_manager
    _scheduler_manager = manager


@handle_errors("clearing scheduler manager runtime handle", default_return=None)
def clear_scheduler_manager() -> None:
    """Clear the registered SchedulerManager handle."""
    global _scheduler_manager
    _scheduler_manager = None


@handle_errors("getting scheduler manager", default_return=None)
def get_scheduler_manager():
    """Return the registered SchedulerManager, or None if the service is not up."""
    return _scheduler_manager
