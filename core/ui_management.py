# ui_management.py
"""UI-neutral helpers shared by UI management code."""

import re
from typing import Any
from collections.abc import Callable

from core.error_handling import handle_errors


def _number_after_prefix(name: str, prefix: str) -> int | None:
    """Extract integer after prefix in name, or None."""
    if prefix not in name:
        return None
    try:
        return int(name.split(prefix, 1)[1].strip())
    except (ValueError, IndexError):
        return None


def _number_from_regex(name: str, pattern: str) -> int | None:
    """Extract first capture group as int from name using regex, or None."""
    match = re.search(pattern, name)
    if not match:
        return None
    try:
        return int(match.group(1))
    except (ValueError, IndexError):
        return None


@handle_errors("finding lowest available period number", default_return=2)
def find_lowest_available_period_number(
    period_items: list,
    number_from_item: Callable[[Any], int | None],
) -> int:
    """
    Return the smallest integer >= 2 not used in period names.

    Args:
        period_items: List of period-like objects.
        number_from_item: Callable that takes an item and returns the
            number extracted from its name if it matches the pattern, else None.

    Returns:
        Lowest available number (>= 2).
    """
    used = set()
    for item in period_items:
        num = number_from_item(item)
        if num is not None:
            used.add(num)
    number = 2
    while number in used:
        number += 1
    return number


@handle_errors("converting period name for display", default_return="")
def period_name_for_display(period_name: str, category: str) -> str:
    """
    Convert period name to display format using existing logic.

    Args:
        period_name: The period name to convert
        category: The category (tasks, checkin, or schedule category)

    Returns:
        Display-formatted period name
    """
    if not period_name:
        return ""

    # For all categories, preserve the original case
    # Users should be able to name their periods as they prefer
    if period_name.upper() == "ALL":
        return "ALL"
    else:
        return period_name


@handle_errors("converting period name for storage", default_return="")
def period_name_for_storage(display_name: str, category: str) -> str:
    """
    Convert display period name to storage format.

    Args:
        display_name: The display-formatted period name
        category: The category (tasks, checkin, or schedule category)

    Returns:
        Storage-formatted period name (preserve original case)
    """
    if not display_name:
        return ""

    # For all categories, preserve the original case
    # The display name is already in the user's preferred format
    if display_name.upper() == "ALL":
        return "ALL"
    else:
        return display_name
