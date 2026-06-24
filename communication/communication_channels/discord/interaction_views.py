"""Discord interaction view factories."""

from __future__ import annotations

from typing import Any

from core.error_handling import handle_errors


@handle_errors("creating Discord check-in view", default_return=None)
def create_checkin_view(user_id: str, **kwargs: Any) -> Any | None:
    from communication.communication_channels.discord.checkin_view import (
        get_checkin_view,
    )

    return _defer_if_no_running_loop(get_checkin_view, user_id)


@handle_errors("creating Discord create hub view", default_return=None)
def create_create_hub_view(user_id: str, **kwargs: Any) -> Any | None:
    from communication.communication_channels.discord.create_item_ui import (
        get_create_hub_view,
    )

    return _defer_if_no_running_loop(
        get_create_hub_view, user_id, kwargs.get("discord_bot")
    )


@handle_errors("creating Discord task list view", default_return=None)
def create_task_list_view(user_id: str, **kwargs: Any) -> Any | None:
    from communication.communication_channels.discord.task_list_ui import (
        get_task_list_view,
    )

    return _defer_if_no_running_loop(
        get_task_list_view,
        user_id,
        kwargs.get("task_list_items"),
        kwargs.get("pagination_actions"),
        kwargs.get("discord_bot"),
    )


@handle_errors("creating Discord task reminder view", default_return=None)
def create_task_reminder_view(user_id: str, **kwargs: Any) -> Any | None:
    from communication.communication_channels.discord.task_reminder_view import (
        get_task_reminder_view,
    )

    task_identifier = kwargs.get("task_identifier")
    task_title = kwargs.get("task_title", "Untitled Task")
    return _defer_if_no_running_loop(
        get_task_reminder_view, user_id, task_identifier, task_title
    )


def _defer_if_no_running_loop(factory, *args: Any) -> Any:
    """Return a view immediately when in an event loop, otherwise defer creation."""
    import asyncio

    try:
        asyncio.get_running_loop()
        return factory(*args)
    except RuntimeError:

        @handle_errors("creating Discord interaction view", default_return=None)
        def create_view():
            """Create the Discord interaction view inside the channel loop."""
            return factory(*args)

        return create_view
