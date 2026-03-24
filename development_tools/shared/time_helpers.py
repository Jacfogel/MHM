#!/usr/bin/env python3
# TOOL_TIER: core

"""
Dev-tools-local time helpers for timestamp formatting.

Provides equivalents to core.time_utilities (now_timestamp_full, now_timestamp_filename)
using stdlib datetime only, so development_tools remains portable and does not
import from core beyond core.logger.
"""

from __future__ import annotations

from datetime import datetime

# Match core.time_utilities format strings
TIMESTAMP_FULL = "%Y-%m-%d %H:%M:%S"
TIMESTAMP_FILENAME = "%Y-%m-%d_%H-%M-%S"


def now_timestamp_full() -> str:
    """Current local timestamp formatted with TIMESTAMP_FULL."""
    return datetime.now().strftime(TIMESTAMP_FULL)


def now_timestamp_filename() -> str:
    """Current local timestamp formatted with TIMESTAMP_FILENAME."""
    return datetime.now().strftime(TIMESTAMP_FILENAME)
