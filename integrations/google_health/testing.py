"""
Shared testing-mode guard for Google Health live network calls.
"""

from __future__ import annotations

import os

from core.error_handling import handle_errors


@handle_errors("checking Google Health testing mode", default_return=False)
def is_google_health_testing_mode() -> bool:
    """Return True when MHM_TESTING skips live Google Health OAuth and API calls."""
    return os.getenv("MHM_TESTING") == "1"
