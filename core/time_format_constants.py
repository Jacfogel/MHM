# core/time_format_constants.py
"""
Canonical time format strings only (no imports from logger, config, or error_handling).

Used by time_utilities and anywhere that needs filename-safe timestamps before the
full time_utilities stack is safe to import (e.g. error recovery paths).
"""

# Primary internal timestamp (full precision to seconds)
TIMESTAMP_FULL = "%Y-%m-%d %H:%M:%S"

# Timestamp rounded to minutes (scheduler, UI state)
TIMESTAMP_MINUTE = "%Y-%m-%d %H:%M"

# Date only (no time)
DATE_ONLY = "%Y-%m-%d"

# Time only (hour + minute)
TIME_ONLY_MINUTE = "%H:%M"

# Filename-safe timestamp (no spaces or colons)
TIMESTAMP_FILENAME = "%Y-%m-%d_%H-%M-%S"

# Display-only formats (never for parsing critical state)
DATE_DISPLAY_MONTH_DAY = "%b %d"
DATE_DISPLAY_WEEKDAY = "%A"

# Full timestamp with sub-second precision (debug only)
TIMESTAMP_WITH_MICROSECONDS = "%Y-%m-%d %H:%M:%S.%f"

# External timestamp inputs we may encounter (parse-only; never emit)
EXTERNAL_TIMESTAMP_VARIANTS: list[str] = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S.%fZ",
]
