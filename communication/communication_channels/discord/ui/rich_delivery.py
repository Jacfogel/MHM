"""Discord rich-message delivery, embeds, buttons, and pagination helpers."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import Any, cast

import discord

from communication.message_processing.flows.flow_constants import (
    FLOW_CONTROL_SKIP_LABELS,
    FLOW_UNDO_BUTTON_PREFIX,
)
from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("discord")
discord_logger = logger


class DiscordRichDeliveryMixin:
    """Rich delivery surface shared by the thin Discord bot host."""

    bot: Any
    _suggestion_button_payloads: dict[str, Any]
    _suggestion_button_counter: int

    @handle_errors(
        "validating Discord user accessibility",
        user_friendly=False,
        default_return=False,
    )
    async def _validate_discord_user_accessibility(self, user_id: str) -> bool:
        """Validate if a Discord user ID is still accessible."""
        bot = self.bot
        if not bot:
            logger.error("Discord bot not initialized")
            return False
        user_id_int = int(user_id)
        user = bot.get_user(user_id_int)
        if not user:
            try:
                await bot.fetch_user(user_id_int)
                return True
            except discord.NotFound:
                logger.warning(f"Discord user {user_id} not found (404)")
                return False
            except discord.Forbidden:
                logger.warning(
                    f"Bot forbidden from accessing Discord user {user_id} (403)"
                )
                return False
        return True

    @handle_errors(
        "sending message to Discord channel", user_friendly=False, default_return=False
    )
    async def _send_to_channel(
        self,
        channel: Any,
        message: str,
        rich_data: dict[str, Any] | None = None,
        suggestions: list[str] | None = None,
    ) -> bool:
        """Send a message directly to a Discord channel."""
        rich_data = rich_data or {}
        suggestions = suggestions or []
        embed = (
            self._create_discord_embed(message, rich_data)
            if self._has_display_rich_data(rich_data)
            else None
        )
        view = self._resolve_interaction_view_from_rich_data(rich_data)
        if not view:
            labels, payloads = self._get_action_row_inputs(suggestions, rich_data)
            if labels:
                view = self._create_action_row(labels, payloads)

        if embed and view:
            await channel.send(content=message or None, embed=embed, view=view)
        elif embed:
            await channel.send(content=message or None, embed=embed)
        elif view:
            await channel.send(content=message, view=view)
        else:
            await channel.send(content=message)

        logger.info(f"Message sent to Discord channel {channel.id}")
        discord_logger.info(
            "Discord channel message sent",
            channel_id=str(channel.id),
            message_length=len(message),
            has_embed=bool(embed),
            has_components=bool(view),
        )
        return True

    @handle_errors("sending Discord message internally", default_return=False)
    async def _send_message_internal(
        self,
        recipient: str,
        message: str,
        rich_data: dict[str, Any] | None = None,
        suggestions: list[str] | None = None,
        custom_view: Any | None = None,
    ) -> bool:
        """Send a Discord message inside the bot event loop."""
        bot = self.bot
        if not bot:
            logger.error("Discord bot not initialized")
            return False
        if not recipient or not isinstance(recipient, str) or not recipient.strip():
            logger.error(f"Invalid recipient: {recipient}")
            return False
        if not message or not isinstance(message, str) or not message.strip():
            logger.error(f"Invalid message: {message}")
            return False
        if rich_data is not None and not isinstance(rich_data, dict):
            logger.error(f"Invalid rich_data: {type(rich_data)}")
            return False
        if suggestions is not None and not isinstance(suggestions, list):
            logger.error(f"Invalid suggestions: {type(suggestions)}")
            return False

        rich_data = rich_data or {}
        suggestions = suggestions or []
        embed = (
            self._create_discord_embed(message, rich_data)
            if self._has_display_rich_data(rich_data)
            else None
        )
        view = None
        if custom_view:
            if callable(custom_view) and not isinstance(custom_view, type):
                try:
                    view = custom_view()
                except Exception as exc:
                    logger.error(f"Error creating view from factory function: {exc}")
            else:
                view = custom_view
        else:
            labels, payloads = self._get_action_row_inputs(suggestions, rich_data)
            if labels:
                view = self._create_action_row(labels, payloads)

        if recipient.startswith("discord_user:"):
            internal_user_id = recipient.split(":", 1)[1]
            try:
                from core import get_user_data

                account_data = get_user_data(internal_user_id, "account").get(
                    "account", {}
                )
                discord_user_id = account_data.get("discord_user_id")
                if not discord_user_id:
                    logger.warning(
                        f"No Discord user ID found for internal user {internal_user_id}"
                    )
                    return False
                user = bot.get_user(int(discord_user_id)) or await bot.fetch_user(
                    int(discord_user_id)
                )
                if not user:
                    logger.warning(
                        f"Could not find Discord user {discord_user_id} for internal user {internal_user_id}"
                    )
                    return False
                kwargs: dict[str, Any] = {"content": message}
                if embed:
                    kwargs["embed"] = embed
                if view:
                    kwargs["view"] = view
                await user.send(**kwargs)
                logger.info(
                    f'Discord DM sent | {{"user_id": "{discord_user_id}", "message_length": {len(message)}, '
                    f'"has_embed": {bool(embed)}, "has_components": {bool(view)}, '
                    f'"message_preview": "{message[:50]}..."}}'
                )
                return True
            except Exception as exc:
                logger.error(
                    f"Error sending DM to Discord user {internal_user_id}: {exc}"
                )
                return False

        if recipient.startswith("discord_direct:"):
            discord_user_id = recipient.split(":", 1)[1]
            try:
                user = bot.get_user(int(discord_user_id)) or await bot.fetch_user(
                    int(discord_user_id)
                )
                if not user:
                    logger.warning(f"Could not find Discord user {discord_user_id}")
                    return False
                kwargs = {"content": message}
                if embed:
                    kwargs["embed"] = embed
                if view:
                    kwargs["view"] = view
                await user.send(**kwargs)
                logger.info(
                    f'Discord DM sent directly | {{"discord_user_id": "{discord_user_id}", '
                    f'"message_length": {len(message)}, "has_embed": {bool(embed)}, '
                    f'"has_components": {bool(view)}, "message_preview": "{message[:50]}..."}}'
                )
                return True
            except Exception as exc:
                logger.error(
                    f"Error sending DM directly to Discord user {discord_user_id}: {exc}"
                )
                return False

        try:
            channel = bot.get_channel(int(recipient))
            if channel:
                kwargs = {"content": message}
                if embed:
                    kwargs["embed"] = embed
                if view:
                    kwargs["view"] = view
                send_fn = getattr(channel, "send", None)
                if callable(send_fn):
                    await cast(Awaitable[Any], send_fn(**kwargs))
                    logger.info(f"Message sent to Discord channel {recipient}")
                    discord_logger.info(
                        "Discord channel message sent",
                        channel_id=recipient,
                        message_length=len(message),
                        has_embed=bool(embed),
                        has_components=bool(view),
                    )
                    return True
                logger.warning(
                    f"Channel {recipient} does not support sending messages (e.g. category channel)"
                )
            else:
                logger.warning(f"Could not find Discord channel with ID {recipient}")
        except (ValueError, TypeError):
            logger.warning(f"Invalid channel ID format: {recipient}")

        logger.error(f"Could not find Discord channel or user with ID {recipient}")
        discord_logger.error(
            "Discord message send failed - recipient not found", recipient=recipient
        )
        return False

    @handle_errors("creating Discord embed", default_return=None)
    def _create_discord_embed(
        self, message: str, rich_data: dict[str, Any]
    ) -> discord.Embed | None:
        """Create a Discord embed from rich response data."""
        if not message or not isinstance(message, str) or not message.strip():
            logger.error(f"Invalid message: {message}")
            return None
        if not rich_data or not isinstance(rich_data, dict):
            logger.error(f"Invalid rich_data: {rich_data}")
            return None
        embed = discord.Embed()
        if "title" in rich_data:
            embed.title = rich_data["title"]
        elif message.startswith("**") and "**" in message[2:]:
            title_end = message.find("**", 2)
            embed.title = message[2:title_end]
            message = message[title_end + 2 :].strip()
        embed.description = rich_data.get("description", message)
        color_map = {
            "success": discord.Color.green(),
            "error": discord.Color.red(),
            "warning": discord.Color.yellow(),
            "info": discord.Color.blue(),
            "task": discord.Color.purple(),
            "profile": discord.Color.orange(),
            "schedule": discord.Color.blue(),
            "analytics": discord.Color.green(),
        }
        embed.color = color_map.get(rich_data.get("type", "info"), discord.Color.blue())
        for field in rich_data.get("fields", []):
            embed.add_field(
                name=field.get("name", ""),
                value=field.get("value", ""),
                inline=field.get("inline", False),
            )
        if "footer" in rich_data:
            embed.set_footer(text=rich_data["footer"])
        if "timestamp" in rich_data:
            embed.timestamp = rich_data["timestamp"]
        return embed

    @handle_errors("checking Discord display rich data", default_return=False)
    def _has_display_rich_data(self, rich_data: dict[str, Any] | None) -> bool:
        if not isinstance(rich_data, dict):
            return False
        metadata_only_keys = {
            "suggestion_payloads",
            "pagination_actions",
            "interaction_view",
            "user_id",
            "task_list_items",
        }
        return any(key not in metadata_only_keys for key in rich_data)

    @handle_errors("getting Discord suggestion payloads", default_return=None)
    def _get_suggestion_payloads(
        self, rich_data: dict[str, Any] | None
    ) -> list[Any] | None:
        if not isinstance(rich_data, dict):
            return None
        payloads = rich_data.get("suggestion_payloads")
        return payloads if isinstance(payloads, list) else None

    @handle_errors("getting Discord pagination actions", default_return=[])
    def _get_pagination_actions(self, rich_data: dict[str, Any] | None) -> list[Any]:
        if not isinstance(rich_data, dict):
            return []
        actions = rich_data.get("pagination_actions")
        return actions if isinstance(actions, list) else []

    @handle_errors("reading pagination action field", default_return=None)
    def _pagination_action_value(
        self, action: Any, field: str, default: Any = None
    ) -> Any:
        return action.get(field, default) if isinstance(action, dict) else getattr(
            action, field, default
        )

    @handle_errors("converting pagination action to Discord button", default_return=None)
    def _pagination_action_button_data(
        self, action: Any
    ) -> tuple[str, dict[str, Any]] | None:
        action_name = self._pagination_action_value(action, "action")
        if not action_name:
            return None
        params = self._pagination_action_value(action, "params", {})
        if not isinstance(params, dict):
            params = {}
        limit = int(self._pagination_action_value(action, "limit", 0) or 0)
        next_offset = int(
            self._pagination_action_value(action, "next_offset", 0) or 0
        )
        remaining_count = int(
            self._pagination_action_value(action, "remaining_count", 0) or 0
        )
        button_count = min(limit, remaining_count) if limit > 0 else remaining_count
        if button_count < 1:
            return None
        entities = dict(params)
        entities["offset"] = next_offset
        entities["limit"] = limit
        return (
            f"Show More ({button_count} more)",
            {"intent": str(action_name), "entities": entities},
        )

    @handle_errors("resolving Discord interaction view from rich data", default_return=None)
    def _resolve_interaction_view_from_rich_data(
        self, rich_data: dict[str, Any] | None
    ) -> Any | None:
        if not rich_data or not isinstance(rich_data, dict):
            return None
        view_type = rich_data.get("interaction_view")
        user_id = rich_data.get("user_id")
        if not view_type or not user_id:
            return None
        from communication.communication_channels.interaction_view_factory import (
            create_interaction_view,
        )

        view = create_interaction_view(
            "discord",
            str(view_type),
            str(user_id),
            discord_bot=self,
            task_list_items=rich_data.get("task_list_items"),
            pagination_actions=rich_data.get("pagination_actions"),
        )
        if callable(view) and not isinstance(view, type):
            try:
                return view()
            except Exception as exc:
                logger.error(f"Error creating interaction view '{view_type}': {exc}")
                return None
        return view

    @handle_errors("building Discord action row inputs", default_return=([], None))
    def _get_action_row_inputs(
        self,
        suggestions: list[str] | None,
        rich_data: dict[str, Any] | None,
    ) -> tuple[list[str], list[Any] | None]:
        labels = list(suggestions or [])
        suggestion_payloads = self._get_suggestion_payloads(rich_data) or []
        payloads: list[Any] = [
            suggestion_payloads[index] if index < len(suggestion_payloads) else None
            for index, _label in enumerate(labels)
        ]
        for action in self._get_pagination_actions(rich_data):
            button_data = self._pagination_action_button_data(action)
            if button_data is not None:
                label, payload = button_data
                labels.append(label)
                payloads.append(payload)
        if not labels:
            return [], None
        return labels[:25], payloads[:25]

    @handle_errors(
        "selecting Discord suggestion button style",
        default_return=discord.ButtonStyle.primary,
    )
    def _discord_button_style_for_suggestion(
        self, label: str
    ) -> discord.ButtonStyle:
        """Choose Discord button style from suggestion label semantics."""
        if label.startswith(FLOW_UNDO_BUTTON_PREFIX):
            return discord.ButtonStyle.danger
        if label in FLOW_CONTROL_SKIP_LABELS:
            return discord.ButtonStyle.secondary
        return discord.ButtonStyle.primary

    @handle_errors("creating Discord action row", default_return=None)
    def _create_action_row(
        self,
        suggestions: list[str],
        suggestion_payloads: list[Any] | None = None,
    ) -> discord.ui.View | None:
        if not suggestions or not isinstance(suggestions, list):
            logger.error(f"Invalid suggestions: {suggestions}")
            return None
        view = discord.ui.View()
        for index, suggestion in enumerate(suggestions[:25]):
            self._suggestion_button_counter += 1
            custom_id = f"suggestion_{self._suggestion_button_counter}_{index}"
            payload = (
                suggestion_payloads[index]
                if suggestion_payloads
                and index < len(suggestion_payloads)
                and suggestion_payloads[index] is not None
                else suggestion
            )
            self._suggestion_button_payloads[custom_id] = payload
            if len(self._suggestion_button_payloads) > 500:
                oldest_key = next(iter(self._suggestion_button_payloads))
                self._suggestion_button_payloads.pop(oldest_key, None)
            view.add_item(
                discord.ui.Button(
                    style=self._discord_button_style_for_suggestion(suggestion),
                    label=suggestion[:80],
                    custom_id=custom_id,
                )
            )
        return view
