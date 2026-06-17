# Discord message and command routing

> **File**: `specs/discord-message-and-command-routing.md`  
> **Audience**: Developers, AI collaborators, and reviewers  
> **Purpose**: Behavior requirements for routing Discord messages, slash commands, classic commands, and suggestion buttons into the channel-agnostic interaction system  
> **Style**: Behavior requirements and scenarios (see [SPECS_GUIDE.md](SPECS_GUIDE.md))  
> **Last Updated**: 2026-05-16  
> **Implementation**: `communication/communication_channels/discord/bot.py`, `communication/message_processing/interaction_manager.py`, `communication/message_processing/command_parser.py`, `communication/command_handlers/interaction_handlers.py`, `communication/command_handlers/shared_types.py`  
> **Related**: [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md), [DISCORD_GUIDE.md](../communication/communication_channels/discord/DISCORD_GUIDE.md), [discord-welcome-and-onboarding.md](discord-welcome-and-onboarding.md)  
> **Automated tests**: `tests/behavior/test_discord_bot_behavior.py`, `tests/behavior/test_discord_automation_complete.py`, `tests/behavior/test_discord_advanced_automation.py`, `tests/behavior/test_communication_interaction_manager_behavior.py`, `tests/behavior/test_message_route_classifier_behavior.py`  
> **Coverage matrix**: [SPEC_COVERAGE_MATRIX.md](SPEC_COVERAGE_MATRIX.md#discord-message-and-command-routing)

## 1. Purpose

Discord is an adapter around the channel-agnostic interaction pipeline. Discord-specific code SHALL identify the Discord user, map the Discord event into a text command or `ParsedCommand`, call the interaction layer, and render the returned message, rich data, and suggestions back into Discord.

The Discord adapter SHALL NOT duplicate task, profile, schedule, notebook, check-in, or AI business logic that already belongs in command handlers or the interaction manager.

## 2. Requirements

### 2.1. Requirement: Discord user identity maps to an internal MHM user

Incoming Discord interactions SHALL map `interaction.user.id` or `message.author.id` to an internal MHM user ID before executing protected features.

#### Scenario: Recognized Discord message

- **GIVEN** a Discord message is received from a non-bot user  
- **AND** the author's Discord ID is linked to an internal MHM user  
- **WHEN** `on_message` processes the message  
- **THEN** the system calls `handle_user_message(internal_user_id, message.content, "discord")`  
- **AND** sends the returned response to the same Discord channel  
- **AND** renders supported rich data and suggestion buttons when present  

#### Scenario: Unrecognized Discord message

- **GIVEN** a Discord message is received from a non-bot user  
- **AND** the author's Discord ID is not linked to an internal MHM user  
- **WHEN** `on_message` processes the message  
- **THEN** the system does not route the message into protected feature handlers  
- **AND** sends create/link account guidance through the welcome/onboarding path  

#### Scenario: Bot-authored message is ignored

- **GIVEN** a Discord message is authored by the MHM bot itself  
- **WHEN** `on_message` receives the message  
- **THEN** the system ignores the message  
- **AND** does not call the interaction manager  
- **AND** does not send a response  

### 2.2. Requirement: Slash commands are generated from the central interaction command map

Discord slash commands SHALL be dynamically registered from `get_interaction_manager().get_command_definitions()` instead of maintaining a separate Discord-only command list.

#### Scenario: Slash command registration

- **GIVEN** the Discord bot is initialized  
- **AND** commands have not already been registered  
- **WHEN** `initialize__register_commands` runs  
- **THEN** each command definition becomes a Discord application command  
- **AND** the command callback routes the command's mapped message to `handle_user_message(..., "discord")`  
- **AND** duplicate command registration attempts are suppressed  

#### Scenario: Slash command from linked user

- **GIVEN** a linked Discord user invokes a generated slash command  
- **WHEN** the command callback runs  
- **THEN** the system sends the command's mapped message to `handle_user_message`  
- **AND** replies to the Discord interaction with the returned response  
- **AND** includes an embed, buttons, or both when the response includes renderable rich data or suggestions  

#### Scenario: Slash command from unlinked user

- **GIVEN** an unlinked Discord user invokes a generated slash command  
- **WHEN** the command callback runs  
- **THEN** the system does not call the feature handler  
- **AND** replies ephemerally that the user must create or link an MHM account  
- **AND** includes the user's Discord ID for setup  

### 2.3. Requirement: Classic commands mirror central command definitions where appropriate

Classic `!command` style Discord commands MAY be registered from the same command definition list so that Discord users can access common features without slash command UI.

#### Scenario: Classic command from linked user

- **GIVEN** a generated classic command is registered  
- **AND** a linked Discord user invokes it  
- **WHEN** the dynamic command callback runs  
- **THEN** the system routes the mapped message to `handle_user_message(..., "discord")`  
- **AND** sends the returned message to the command context  

#### Scenario: Classic command from unlinked user

- **GIVEN** a generated classic command is registered  
- **AND** an unlinked Discord user invokes it  
- **WHEN** the dynamic command callback runs  
- **THEN** the system sends a registration-required message  
- **AND** does not execute the protected feature  

#### Scenario: Help command duplication avoided

- **GIVEN** command definitions include help-style commands  
- **WHEN** classic commands are registered  
- **THEN** commands that would duplicate Discord's native help handling are skipped where the implementation excludes them  

### 2.4. Requirement: Suggestion buttons are translated back into interaction requests

Suggestion buttons returned by channel-agnostic handlers SHALL be rendered as Discord buttons. Button clicks SHALL either use stored hidden payloads or fall back to the button label as a user message.

#### Scenario: Suggestion button with structured payload

- **GIVEN** a previous response produced a suggestion button  
- **AND** the button has a stored payload containing an `intent` and optional `entities`  
- **WHEN** the user clicks the button  
- **THEN** the Discord adapter builds a `ParsedCommand` from the payload  
- **AND** routes it to the matching interaction handler  
- **AND** sends the returned response as a Discord follow-up message  

#### Scenario: Suggestion button without structured payload

- **GIVEN** a previous response produced a suggestion button  
- **AND** the button does not have a structured payload  
- **WHEN** the user clicks the button  
- **THEN** the Discord adapter processes the button label, or stored string payload, as a normal user message  
- **AND** routes it through `handle_user_message(..., "discord")`  

#### Scenario: Suggestion button cannot be resolved

- **GIVEN** a suggestion button interaction is received  
- **AND** the adapter cannot determine a button label or payload  
- **WHEN** the click is processed  
- **THEN** the system sends a user-facing error  
- **AND** asks the user to type the command instead  

### 2.5. Requirement: Pagination actions are rendered as Discord buttons

Channel-neutral pagination metadata SHALL be converted into Discord action buttons without requiring each command handler to know about Discord UI.

#### Scenario: Pagination metadata is present

- **GIVEN** an interaction response includes `rich_data["pagination_actions"]`  
- **WHEN** Discord renders the response  
- **THEN** each valid pagination action is converted into a Discord button  
- **AND** the button label indicates how many additional items can be shown  
- **AND** the hidden payload stores the next intent, offset, and limit  

#### Scenario: Too many buttons are available

- **GIVEN** a response includes more than five possible buttons  
- **WHEN** Discord renders the action row  
- **THEN** only the first five buttons are rendered  
- **SO THAT** the adapter respects Discord component limits  

### 2.6. Requirement: Discord adapter errors do not break the interaction pipeline

Discord-specific errors SHALL be logged and surfaced as practical user-facing fallback messages where possible.

#### Scenario: Interaction manager raises during message processing

- **GIVEN** a linked user sends a message  
- **AND** an exception occurs while routing through the enhanced interaction layer  
- **WHEN** `on_message` handles the exception  
- **THEN** the system logs the failure  
- **AND** sends a generic retry-later message to the Discord channel  
- **AND** does not fall back to legacy conversation-manager behavior  

## 3. Out of scope

- Welcome and account onboarding; see [discord-welcome-and-onboarding.md](discord-welcome-and-onboarding.md).
- Details of task CRUD, notebook CRUD, profile, schedule, analytics, or check-in business logic after routing reaches command handlers.
- Discord webhook authorization/deauthorization events.
- Low-level network reconnect behavior.

## 4. Manual test checklist

Run after changing Discord message or command routing:

1. [ ] Linked user sends `show my tasks` in Discord -> response comes from the interaction manager.
2. [ ] Linked user uses generated `/tasks` command -> mapped command response is returned.
3. [ ] Linked user uses generated `!tasks` command -> mapped command response is returned.
4. [ ] Unlinked user uses a slash command -> ephemeral create/link account guidance appears with Discord ID.
5. [ ] Bot-authored message -> no response loop.
6. [ ] Response with suggestions -> Discord buttons render.
7. [ ] Suggestion click with stored payload -> correct handler receives the payload intent/entities.
8. [ ] Suggestion click without payload -> label is processed as a user message.
9. [ ] Paginated response -> "Show More" button routes to next page.
10. [ ] Handler failure -> user sees a generic retry-later message and logs contain the error.

## 5. Related documentation

- [SPECS_GUIDE.md](SPECS_GUIDE.md) - how behavior specs fit the project  
- [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md) - channel-agnostic architecture  
- [DISCORD_GUIDE.md](../communication/communication_channels/discord/DISCORD_GUIDE.md) - Discord adapter overview  
- [TESTING_GUIDE.md](../tests/TESTING_GUIDE.md) - running automated tests  
