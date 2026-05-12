"""Period row UI helpers.

This module owns PeriodRowWidget creation and layout operations so core modules
do not depend on UI widgets.
"""

from collections.abc import Callable
from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.ui_management import period_name_for_display, period_name_for_storage
from ui.widgets.period_row_widget import PeriodRowWidget

logger = get_component_logger("ui")

DEFAULT_PERIOD_DATA = {
    "start_time": "18:00",
    "end_time": "20:00",
    "active": True,
    "days": ["ALL"],
}


@handle_errors("clearing period widgets from layout", default_return=None)
def clear_period_widgets_from_layout(layout, widget_list=None):
    """Clear all period widgets from a layout."""
    if layout is None:
        logger.warning("clear_period_widgets_from_layout: layout is None")
        return

    for i in reversed(range(layout.count())):
        item = layout.itemAt(i)
        widget = item.widget()
        if widget:
            layout.removeWidget(widget)
            widget.setParent(None)
            widget.deleteLater()

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
    """Add a PeriodRowWidget to a layout with display-name normalization."""
    try:
        if category in ("tasks", "checkin") and period_name.upper() == "ALL":
            logger.debug(f"Skipping ALL period for category {category}")
            return None

        display_name = period_name_for_display(period_name, category)
        period_widget = PeriodRowWidget(parent_widget, display_name, period_data)

        if delete_callback:
            period_widget.delete_requested.connect(delete_callback)

        layout.addWidget(period_widget)

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
    """Load and display period widgets for a specific category."""
    try:
        from core.schedule_runtime import get_schedule_time_periods

        clear_period_widgets_from_layout(layout, widget_list)

        periods = get_schedule_time_periods(user_id, category) or {}
        created_widgets = []

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
    """Collect period data from PeriodRowWidget-like objects."""
    periods = {}

    logger.info(
        f"Collecting period data from {len(widget_list)} widgets for category {category}"
    )

    for widget in widget_list:
        try:
            period_data = widget.get_period_data()
            display_name = period_data["name"]
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
    """Create a period row widget, connect delete, add to layout and list."""
    try:
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
    """Remove a period row from layout and list, storing data for undo."""
    if guard_fn and guard_fn(row_widget):
        return
    try:
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
