"""Critical onboarding tests for Discord account creation and linking."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

import communication.communication_channels.discord.onboarding.account_flow_handler as flow


pytestmark = [pytest.mark.unit, pytest.mark.communication, pytest.mark.asyncio]


def _interaction():
    interaction = MagicMock(spec=discord.Interaction)
    interaction.response = SimpleNamespace(
        defer=AsyncMock(),
        send_message=AsyncMock(),
        send_modal=AsyncMock(),
    )
    interaction.followup = SimpleNamespace(send=AsyncMock())
    interaction.message = SimpleNamespace(edit=AsyncMock())
    return interaction


async def test_feature_selection_defaults_and_timeout():
    view = flow.FeatureSelectionView("Julie", "discord-1")
    message = SimpleNamespace(edit=AsyncMock())
    setattr(view, "message", message)  # noqa: B010 - Discord attaches this dynamically.

    assert view.tasks_enabled is True
    assert view.checkins_enabled is True
    assert view.messages_enabled is False
    assert view.timezone == "America/Regina"
    assert len(view.children) == 5

    await view.on_timeout()

    assert all(getattr(item, "disabled", False) for item in view.children)
    message.edit.assert_awaited_once_with(view=view)


@pytest.mark.parametrize(
    ("select_type", "attribute", "value", "expected"),
    [
        (flow.TaskFeatureSelect, "tasks_enabled", "false", False),
        (flow.CheckinFeatureSelect, "checkins_enabled", "false", False),
        (flow.MessageFeatureSelect, "messages_enabled", "true", True),
        (flow.TimezoneSelect, "timezone", "UTC", "UTC"),
    ],
)
async def test_feature_select_callbacks_update_parent(
    select_type, attribute, value, expected
):
    parent = flow.FeatureSelectionView("Julie", "discord-1")
    select = select_type(parent)
    select._values = [value]
    interaction = _interaction()

    await select.callback(interaction)

    assert getattr(parent, attribute) == expected
    interaction.response.defer.assert_awaited_once()


async def test_create_account_button_submits_selected_features(monkeypatch):
    parent = flow.FeatureSelectionView("Julie", "discord-1")
    parent.tasks_enabled = False
    parent.messages_enabled = True
    interaction = _interaction()
    response = SimpleNamespace(message="Created", completed=True)
    handle = MagicMock(return_value=response)
    monkeypatch.setattr(flow._account_handler, "handle", handle)

    await flow.CreateAccountButton(parent).callback(interaction)

    interaction.response.defer.assert_awaited_once()
    interaction.followup.send.assert_awaited_once_with("Created", ephemeral=True)
    command = handle.call_args.args[1]
    assert command.intent == "create_account"
    assert command.entities["tasks_enabled"] is False
    assert command.entities["messages_enabled"] is True
    interaction.message.edit.assert_awaited_once()


async def test_creation_flow_rejects_non_discord_interaction(monkeypatch):
    handle = MagicMock()
    monkeypatch.setattr(flow._account_handler, "handle", handle)

    await flow.start_account_creation_flow(object(), "discord-1")

    handle.assert_not_called()


async def test_creation_flow_stops_when_account_already_exists(monkeypatch):
    interaction = _interaction()
    monkeypatch.setattr(
        flow._account_handler,
        "handle",
        MagicMock(
            return_value=SimpleNamespace(
                message="Already linked",
                rich_data={"has_account": True},
            )
        ),
    )

    await flow.start_account_creation_flow(interaction, "discord-1", "Julie")

    interaction.response.send_message.assert_awaited_once_with(
        "Already linked", ephemeral=True
    )
    interaction.response.send_modal.assert_not_awaited()


async def test_creation_flow_opens_prefilled_modal_for_new_account(monkeypatch):
    interaction = _interaction()
    monkeypatch.setattr(
        flow._account_handler,
        "handle",
        MagicMock(
            return_value=SimpleNamespace(message="Create", rich_data={"has_account": False})
        ),
    )

    await flow.start_account_creation_flow(interaction, "discord-1", "Julie")

    interaction.response.send_modal.assert_awaited_once()
    modal = interaction.response.send_modal.await_args.args[0]
    assert modal.preferred_name_input.default == "Julie"


async def test_linking_flow_stops_when_account_already_exists(monkeypatch):
    interaction = _interaction()
    monkeypatch.setattr(
        flow._account_handler,
        "handle",
        MagicMock(
            return_value=SimpleNamespace(
                message="Already linked",
                rich_data={"has_account": True},
            )
        ),
    )

    await flow.start_account_linking_flow(interaction, "discord-1")

    interaction.response.send_message.assert_awaited_once_with(
        "Already linked", ephemeral=True
    )
    interaction.response.send_modal.assert_not_awaited()


async def test_linking_flow_opens_identifier_modal(monkeypatch):
    interaction = _interaction()
    monkeypatch.setattr(
        flow._account_handler,
        "handle",
        MagicMock(
            return_value=SimpleNamespace(message="Link", rich_data={"has_account": False})
        ),
    )

    await flow.start_account_linking_flow(interaction, "discord-1")

    interaction.response.send_modal.assert_awaited_once()
    modal = interaction.response.send_modal.await_args.args[0]
    assert modal.account_identifier_input.required is True
