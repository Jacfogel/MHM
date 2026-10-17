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


async def test_create_account_button_keeps_failed_result_visible(monkeypatch):
    parent = flow.FeatureSelectionView("Julie", "discord-1")
    interaction = _interaction()
    monkeypatch.setattr(
        flow._account_handler,
        "handle",
        MagicMock(
            return_value=SimpleNamespace(message="Could not create", completed=False)
        ),
    )

    await flow.CreateAccountButton(parent).callback(interaction)

    assert all(getattr(item, "disabled", False) for item in parent.children)
    interaction.followup.send.assert_awaited_once_with(
        "Could not create", ephemeral=True
    )
    interaction.message.edit.assert_not_awaited()


async def test_create_account_button_tolerates_result_message_edit_failure(monkeypatch):
    parent = flow.FeatureSelectionView("Julie", "discord-1")
    interaction = _interaction()
    interaction.message.edit.side_effect = RuntimeError("message was deleted")
    monkeypatch.setattr(
        flow._account_handler,
        "handle",
        MagicMock(return_value=SimpleNamespace(message="Created", completed=True)),
    )

    await flow.CreateAccountButton(parent).callback(interaction)

    interaction.followup.send.assert_awaited_once_with("Created", ephemeral=True)
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
            return_value=SimpleNamespace(
                message="Create", rich_data={"has_account": False}
            )
        ),
    )

    await flow.start_account_creation_flow(interaction, "discord-1", "Julie")

    interaction.response.send_modal.assert_awaited_once()
    modal = interaction.response.send_modal.await_args.args[0]
    assert modal.preferred_name_input.default == "Julie"


async def test_creation_modal_rejects_a_blank_preferred_name(monkeypatch):
    interaction = _interaction()
    monkeypatch.setattr(
        flow._account_handler,
        "handle",
        MagicMock(
            return_value=SimpleNamespace(
                message="Create", rich_data={"has_account": False}
            )
        ),
    )
    await flow.start_account_creation_flow(interaction, "discord-1")
    modal = interaction.response.send_modal.await_args.args[0]
    modal.preferred_name_input._value = "   "
    submission = _interaction()

    await modal.on_submit(submission)

    submission.response.send_message.assert_awaited_once_with(
        "❌ Please enter a preferred name.", ephemeral=True
    )


async def test_creation_modal_opens_feature_selection_with_trimmed_name(monkeypatch):
    interaction = _interaction()
    monkeypatch.setattr(
        flow._account_handler,
        "handle",
        MagicMock(
            return_value=SimpleNamespace(
                message="Create", rich_data={"has_account": False}
            )
        ),
    )
    await flow.start_account_creation_flow(interaction, "discord-1")
    modal = interaction.response.send_modal.await_args.args[0]
    modal.preferred_name_input._value = "  Julie  "
    submission = _interaction()

    await modal.on_submit(submission)

    kwargs = submission.response.send_message.await_args.kwargs
    assert kwargs["ephemeral"] is True
    assert kwargs["view"].preferred_name == "Julie"
    assert kwargs["view"].discord_user_id == "discord-1"


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
            return_value=SimpleNamespace(
                message="Link", rich_data={"has_account": False}
            )
        ),
    )

    await flow.start_account_linking_flow(interaction, "discord-1")

    interaction.response.send_modal.assert_awaited_once()
    modal = interaction.response.send_modal.await_args.args[0]
    assert modal.account_identifier_input.required is True


def _status_response():
    return SimpleNamespace(message="Link", rich_data={"has_account": False})


async def _open_link_modal(monkeypatch, *submit_responses):
    interaction = _interaction()
    handle = MagicMock(side_effect=[_status_response(), *submit_responses])
    monkeypatch.setattr(flow._account_handler, "handle", handle)
    await flow.start_account_linking_flow(interaction, "discord-1")
    return interaction.response.send_modal.await_args.args[0], handle


async def test_linking_modal_rejects_a_blank_identifier(monkeypatch):
    modal, handle = await _open_link_modal(monkeypatch)
    modal.account_identifier_input._value = "   "
    submission = _interaction()

    await modal.on_submit(submission)

    submission.response.send_message.assert_awaited_once_with(
        "❌ Enter an account ID or contact identifier.", ephemeral=True
    )
    assert handle.call_count == 1


@pytest.mark.parametrize(
    ("link_response", "expects_confirmation_view"),
    [
        (SimpleNamespace(message="Linked", completed=True, rich_data={}), False),
        (
            SimpleNamespace(
                message="Check your email",
                completed=False,
                rich_data={"type": "confirmation_code_sent"},
            ),
            True,
        ),
        (
            SimpleNamespace(
                message="Account not found",
                completed=False,
                rich_data={"type": "not_found"},
            ),
            False,
        ),
    ],
)
async def test_linking_modal_surfaces_handler_outcomes(
    monkeypatch, link_response, expects_confirmation_view
):
    modal, handle = await _open_link_modal(monkeypatch, link_response)
    modal.account_identifier_input._value = "person@example.com"
    submission = _interaction()

    await modal.on_submit(submission)

    submission.response.send_message.assert_awaited_once()
    sent_args = submission.response.send_message.await_args
    assert sent_args.args[0] == link_response.message
    assert sent_args.kwargs["ephemeral"] is True
    if expects_confirmation_view:
        confirmation_view = sent_args.kwargs["view"]
        assert confirmation_view.account_identifier == "person@example.com"
        assert confirmation_view.discord_user_id == "discord-1"
    else:
        assert "view" not in sent_args.kwargs
    submission.followup.send.assert_not_awaited()
    command = handle.call_args.args[1]
    assert command.intent == "link_account"
    assert command.entities["account_identifier"] == "person@example.com"
    assert command.entities["channel_identifier"] == "discord-1"


async def _open_confirmation_modal(monkeypatch, confirmation_result):
    code_sent = SimpleNamespace(
        message="Check your email",
        completed=False,
        rich_data={"type": "confirmation_code_sent"},
    )
    identifier_modal, handle = await _open_link_modal(
        monkeypatch, code_sent, confirmation_result
    )
    identifier_modal.account_identifier_input._value = "person@example.com"
    identifier_submission = _interaction()
    await identifier_modal.on_submit(identifier_submission)

    confirmation_view = (
        identifier_submission.response.send_message.await_args.kwargs["view"]
    )
    button = next(
        child
        for child in confirmation_view.children
        if child.label == "Enter confirmation code"
    )
    button_interaction = _interaction()
    await button.callback(button_interaction)

    button_interaction.response.send_modal.assert_awaited_once()
    return button_interaction.response.send_modal.await_args.args[0], handle


async def test_confirmation_button_opens_code_modal(monkeypatch):
    modal, handle = await _open_confirmation_modal(
        monkeypatch,
        SimpleNamespace(message="Linked", completed=True, rich_data={}),
    )

    assert modal.account_identifier == "person@example.com"
    assert modal.discord_user_id == "discord-1"
    assert modal.code_input.min_length == 6
    assert modal.code_input.max_length == 6
    assert handle.call_count == 2


async def test_confirmation_modal_submits_code_without_putting_it_in_message_or_log(
    monkeypatch,
):
    modal, handle = await _open_confirmation_modal(
        monkeypatch,
        SimpleNamespace(message="Linked", completed=True, rich_data={}),
    )
    modal.code_input._value = "123456"
    submission = _interaction()
    info_log = MagicMock()
    monkeypatch.setattr(flow.logger, "info", info_log)

    await modal.on_submit(submission)

    submission.response.send_message.assert_awaited_once_with(
        "Linked", ephemeral=True
    )
    command = handle.call_args.args[1]
    assert command.intent == "link_account"
    assert command.entities == {
        "account_identifier": "person@example.com",
        "confirmation_code": "123456",
        "channel_identifier": "discord-1",
        "channel_type": "discord",
    }
    assert command.original_message == "link account with confirmation code"
    assert "123456" not in repr(info_log.call_args)
    assert "person@example.com" not in repr(info_log.call_args)


@pytest.mark.parametrize("entered_code", ["", "12345", "12345x", "１２３４５６"])
async def test_confirmation_modal_rejects_malformed_codes(
    monkeypatch, entered_code
):
    modal, handle = await _open_confirmation_modal(
        monkeypatch,
        SimpleNamespace(message="Linked", completed=True, rich_data={}),
    )
    modal.code_input._value = entered_code
    submission = _interaction()

    await modal.on_submit(submission)

    submission.response.send_message.assert_awaited_once_with(
        "❌ Enter the 6-digit confirmation code from your email.",
        ephemeral=True,
    )
    assert handle.call_count == 2


async def test_confirmation_modal_redacts_handler_exception(monkeypatch):
    modal, _handle = await _open_confirmation_modal(
        monkeypatch, RuntimeError("secret provider detail")
    )
    modal.code_input._value = "123456"
    submission = _interaction()
    exception_log = MagicMock()
    monkeypatch.setattr(flow.logger, "exception", exception_log)

    await modal.on_submit(submission)

    submission.response.send_message.assert_awaited_once_with(
        "❌ An error occurred while linking your account. Please try again.",
        ephemeral=True,
    )
    exception_log.assert_called_once()
    assert exception_log.call_args.kwargs["redact_exception"] is True
    assert exception_log.call_args.kwargs["error_type"] == "RuntimeError"
    assert "secret provider detail" not in repr(exception_log.call_args)


async def test_linking_modal_converts_handler_exception_to_safe_response(monkeypatch):
    modal, _handle = await _open_link_modal(
        monkeypatch, RuntimeError("sensitive provider detail")
    )
    modal.account_identifier_input._value = "person@example.com"
    submission = _interaction()
    exception_log = MagicMock()
    monkeypatch.setattr(flow.logger, "exception", exception_log)

    await modal.on_submit(submission)

    submission.response.send_message.assert_awaited_once_with(
        "❌ An error occurred. Please try again.", ephemeral=True
    )
    assert (
        "sensitive provider detail"
        not in submission.response.send_message.await_args.args[0]
    )
    exception_log.assert_called_once()
    assert exception_log.call_args.kwargs["redact_exception"] is True
    assert exception_log.call_args.kwargs["error_type"] == "RuntimeError"
    assert "sensitive provider detail" not in repr(exception_log.call_args)
    assert "person@example.com" not in repr(exception_log.call_args)
