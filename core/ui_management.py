# ui_management.py
"""
UI management utilities for MHM.
Contains functions for UI-specific operations like widget management and layout handling.
"""

import re
from typing import Any, Callable

from core.logger import get_component_logger
from core.error_handling import handle_errors

logger = get_component_logger("ui")
ui_logger = get_component_logger("main")

# Default period data for new rows (start_time, end_time, active, days)
_DEFAULT_PERIOD_DATA = {
    "start_time": "18:00",
    "end_time": "20:00",
    "active": True,
    "days": ["ALL"],
}


@handle_errors("clearing period widgets from layout", default_return=None)
def clear_period_widgets_from_layout(layout, widget_list=None):
    """
    Clear all period widgets from a layout.

    Args:
        layout: The QVBoxLayout to clear
        widget_list: Optional list to track widgets (will be cleared if provided)

    Returns:
        None
    """
    if layout is None:
        logger.warning("clear_period_widgets_from_layout: layout is None")
        return

    # Remove all widgets from layout
    for i in reversed(range(layout.count())):
        item = layout.itemAt(i)
        widget = item.widget()
        if widget:
            layout.removeWidget(widget)
            widget.setParent(None)
            widget.deleteLater()

    # Clear widget list if provided
    if widget_list is not None:
        widget_list.clear()

    logger.debug(f"Cleared {layout.count()} widgets from layout")


@handle_errors("adding period widget to layout", default_return=None)
def add_period_widget_to_layout(
    layout,
    period_name: str,
    period_data: dict,
    category: str,
    parent_widget=None,
    widget_list=None,
    delete_callback=None,
):
    """
    Add a period widget to a layout with proper display formatting.

    Args:
        layout: The QVBoxLayout to add the widget to
        period_name: The period name
        period_data: The period data dictionary
        category: The category (tasks, checkin, or schedule category)
        parent_widget: The parent widget for the period widget
        widget_list: Optional list to track widgets
        delete_callback: Optional callback for delete signal

    Returns:
        The created PeriodRowWidget or None if failed
    """
    try:
        from ui.widgets.period_row_widget import PeriodRowWidget

        # Skip "ALL" periods for tasks and checkins
        if category in ("tasks", "checkin") and period_name.upper() == "ALL":
            logger.debug(f"Skipping ALL period for category {category}")
            return None

        # Convert period name for display using existing logic
        display_name = period_name_for_display(period_name, category)

        # Create the period widget
        period_widget = PeriodRowWidget(parent_widget, display_name, period_data)

        # Note: ALL periods are automatically made read-only in the PeriodRowWidget constructor
        # No need to call set_read_only here as it's already handled

        # Connect delete signal if callback provided
        if delete_callback:
            period_widget.delete_requested.connect(delete_callback)

        # Add to layout
        layout.addWidget(period_widget)

        # Add to widget list if provided
        if widget_list is not None:
            widget_list.append(period_widget)

        logger.debug(f"Added period widget: {display_name} for category {category}")
        return period_widget

    except Exception as e:
        logger.error(
            f"Error adding period widget {period_name} for category {category}: {e}"
        )
        return None


@handle_errors("loading period widgets for category", default_return=None)
def load_period_widgets_for_category(
    layout,
    user_id: str,
    category: str,
    parent_widget=None,
    widget_list=None,
    delete_callback=None,
):
    """
    Load and display period widgets for a specific category.

    Args:
        layout: The QVBoxLayout to add widgets to
        user_id: The user ID
        category: The category (tasks, checkin, or schedule category)
        parent_widget: The parent widget for period widgets
        widget_list: Optional list to track widgets
        delete_callback: Optional callback for delete signal

    Returns:
        List of created widgets
    """
    try:
        from core.schedule_management import get_schedule_time_periods
        from ui.widgets.period_row_widget import PeriodRowWidget

        # Clear existing widgets
        clear_period_widgets_from_layout(layout, widget_list)

        # Get periods for this category
        periods = get_schedule_time_periods(user_id, category) or {}
        # periods is already a dict of period_name: period_data in the new format

        created_widgets = []

        # Add widgets for each period
        for period_name, period_data in periods.items():
            widget = add_period_widget_to_layout(
                layout,
                period_name,
                period_data,
                category,
                parent_widget,
                widget_list,
                delete_callback,
            )
            if widget:
                created_widgets.append(widget)

        logger.info(
            f"Loaded {len(created_widgets)} period widgets for category {category}"
        )
        return created_widgets

    except Exception as e:
        logger.error(f"Error loading period widgets for category {category}: {e}")
        return []


@handle_errors("collecting period data from widgets", default_return={})
def collect_period_data_from_widgets(widget_list, category: str) -> dict:
    """
    Collect period data from a list of period widgets.

    Args:
        widget_list: List of PeriodRowWidget instances
        category: The category (tasks, checkin, or schedule category)

    Returns:
        Dictionary of period data with storage-formatted names, each with only 'active', 'days', 'start_time', 'end_time'.
    """
    periods = {}

    logger.info(
        f"Collecting period data from {len(widget_list)} widgets for category {category}"
    )

    for widget in widget_list:
        try:
            period_data = widget.get_period_data()
            display_name = period_data["name"]

            # Convert display name to storage format
            storage_name = period_name_for_storage(display_name, category)

            periods[storage_name] = {
                "start_time": period_data["start_time"],
                "end_time": period_data["end_time"],
                "active": period_data["active"],
                "days": period_data["days"],
            }

            logger.info(f"Collected period '{storage_name}': {periods[storage_name]}")

        except Exception as e:
            logger.error(f"Error collecting data from period widget: {e}")
            continue

    logger.info(f"Final collected periods for category {category}: {periods}")
    return periods


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
    period_widgets: list,
    number_from_widget: Callable[[Any], int | None],
) -> int:
    """
    Return the smallest integer >= 2 not used in period names.

    Args:
        period_widgets: List of period row widgets (e.g. PeriodRowWidget).
        number_from_widget: Callable that takes a widget and returns the
            number extracted from its name if it matches the pattern, else None.

    Returns:
        Lowest available number (>= 2).
    """
    used = set()
    for widget in period_widgets:
        num = number_from_widget(widget)
        if num is not None:
            used.add(num)
    number = 2
    while number in used:
        number += 1
    return number


@handle_errors("adding period row to layout", default_return=None)
def add_period_row_to_layout(
    layout,
    period_widgets: list,
    period_name: str,
    period_data: dict,
    parent_widget,
    delete_callback: Callable[[Any], None],
    after_add_callback: Callable[[Any], None] | None = None,
):
    """
    Create a period row widget, connect delete, add to layout and list.

    Args:
        layout: QVBoxLayout to add the widget to.
        period_widgets: List to append the new widget to.
        period_name: Display name for the period.
        period_data: Dict with start_time, end_time, active, days.
        parent_widget: Parent for the PeriodRowWidget.
        delete_callback: Callback for delete_requested signal.
        after_add_callback: Optional callback(widget) after adding (e.g. for sort).

    Returns:
        The created PeriodRowWidget or None on failure.
    """
    try:
        from ui.widgets.period_row_widget import PeriodRowWidget

        widget = PeriodRowWidget(parent_widget, period_name, period_data)
        widget.delete_requested.connect(delete_callback)
        layout.addWidget(widget)
        period_widgets.append(widget)
        if after_add_callback:
            after_add_callback(widget)
        return widget
    except Exception as e:
        logger.error(f"Error adding period row {period_name}: {e}")
        return None


@handle_errors("removing period row from layout", default_return=None)
def remove_period_row_from_layout(
    row_widget,
    layout,
    period_widgets: list,
    deleted_periods: list,
    guard_fn: Callable[[object], bool] | None = None,
) -> None:
    """
    Remove a period row from layout and list, store data for undo.

    Args:
        row_widget: The period row widget to remove.
        layout: Layout to remove the widget from.
        period_widgets: List to remove the widget from.
        deleted_periods: List to append deleted data dict (period_name, start_time, end_time, active, days).
        guard_fn: If provided, callable(row_widget) returning True to abort removal (e.g. show message and return).
    """
    if guard_fn and guard_fn(row_widget):
        return
    try:
        from ui.widgets.period_row_widget import PeriodRowWidget

        if isinstance(row_widget, PeriodRowWidget):
            data = row_widget.get_period_data()
            deleted_periods.append(
                {
                    "period_name": data["name"],
                    "start_time": data["start_time"],
                    "end_time": data["end_time"],
                    "active": data["active"],
                    "days": data["days"],
                }
            )
        layout.removeWidget(row_widget)
        row_widget.setParent(None)
        row_widget.deleteLater()
        if row_widget in period_widgets:
            period_widgets.remove(row_widget)
    except Exception as e:
        logger.error(f"Error removing period row: {e}")


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
