# Discord check-in flow

> **File**: `specs/discord-checkin-flow.md`  
> **Audience**: Developers, AI collaborators, and reviewers  
> **Purpose**: Behavior requirements for Discord check-in prompts, check-in buttons, and retry-safe check-in delivery  
> **Style**: Behavior requirements and scenarios (see [SPECS_GUIDE.md](SPECS_GUIDE.md))  
> **Last Updated**: 2026-05-16  
> **Implementation**: `communication/communication_channels/discord/checkin_view.py`, `communication/communication_channels/discord/bot.py`, `communication/reminders/checkin_prompt_dispatcher.py`, `communication/message_processing/interaction_manager.py`, `communication/command_handlers/checkin_handler.py`, `checkins/checkin_service.py`, `checkins/checkin_data_manager.py`  
> **Related**: [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md), [DISCORD_GUIDE.md](../communication/communication_channels/discord/DISCORD_GUIDE.md), [discord-message-and-command-routing.md](discord-message-and-command-routing.md)  
> **Automated tests**: `tests/unit/test_checkin_view.py`, `tests/behavior/test_discord_checkin_retry_behavior.py`, `tests/behavior/test_discord_bot_behavior.py`, `tests/behavior/test_discord_automation_complete.py`, `tests/behavior/test_checkin_handler_behavior.py`  
> **Coverage matrix**: [SPEC_COVERAGE_MATRIX.md](SPEC_COVERAGE_MATRIX.md#discord-check-in-flow)

## 1. Purpose

Discord check-ins allow a linked user to start, answer, skip, cancel, and get help for check-in flows from Discord. Discord-specific UI SHALL remain an adapter around channel-agnostic check-in handling.

## 2. Requirements

### 2.1. Requirement: Check-in messages use the channel-agnostic interaction path

Discord SHALL route check-in text and button actions through `handle_user_message` so check-in behavior stays consistent across channels.

#### Scenario: User starts a check-in from Discord

- **GIVEN** a linked Discord user asks to start a check-in  
- **WHEN** the Discord message or command reaches the interaction manager  
- **THEN** the check-in handler starts the active check-in flow for that user  
- **AND** Discord sends the returned prompt to the user  
- **AND** Discord may attach check-in buttons when a custom check-in view is supplied  

#### Scenario: User answers a check-in question

- **GIVEN** a linked Discord user has an active check-in  
- **WHEN** they send a response in Discord  
- **THEN** the Discord adapter calls `handle_user_message(internal_user_id, message.content, "discord")`  
- **AND** the check-in flow interprets the answer using channel-agnostic logic  
- **AND** Discord sends the next prompt or completion response returned by the handler  

### 2.2. Requirement: Check-in view provides persistent action buttons

`get_checkin_view(user_id)` SHALL create a persistent Discord `View` with Cancel Check-in, Skip Question, and More buttons.

#### Scenario: Check-in view creation

- **GIVEN** the Discord adapter needs check-in action buttons for an internal user ID  
- **WHEN** `get_checkin_view(user_id)` is called  
- **THEN** it returns a Discord `View`  
- **AND** the view uses `timeout=None`  
- **AND** the view contains custom IDs scoped to that user ID  

#### Scenario: Cancel Check-in button

- **GIVEN** a check-in message includes a `Cancel Check-in` button  
- **WHEN** the user clicks it  
- **THEN** the button handler defers the Discord interaction  
- **AND** looks up the internal user ID from the clicker's Discord ID  
- **AND** routes `/cancel` through `handle_user_message(..., "discord")`  
- **AND** sends the handler response ephemerally  

#### Scenario: Skip Question button

- **GIVEN** a check-in message includes a `Skip Question` button  
- **WHEN** the user clicks it  
- **THEN** the button handler defers the Discord interaction  
- **AND** looks up the internal user ID from the clicker's Discord ID  
- **AND** routes `skip` through `handle_user_message(..., "discord")`  
- **AND** sends the handler response ephemerally  

#### Scenario: More button

- **GIVEN** a check-in message includes a `More` button  
- **WHEN** the user clicks it  
- **THEN** Discord sends ephemeral help text  
- **AND** the help explains numeric answers, word answers, skipping, cancelling, and starting a new check-in  
- **AND** the help does not mutate the active check-in state  

#### Scenario: Check-in button clicked by unlinked user

- **GIVEN** a check-in button interaction is received  
- **AND** the clicker's Discord ID cannot be mapped to an internal MHM user  
- **WHEN** the button handler runs  
- **THEN** it sends an ephemeral account-not-found error  
- **AND** does not call check-in business logic  

### 2.3. Requirement: Check-in delivery must not falsely log successful delivery

A check-in prompt SHALL only be logged to user activity as started after the Discord send succeeds. The current implementation initializes the dynamic check-in flow before attempting delivery, then records the user-activity "User check-in started" event only after successful send.

#### Scenario: Check-in prompt send succeeds

- **GIVEN** the scheduler or dispatcher sends a check-in prompt to Discord  
- **WHEN** Discord delivery succeeds  
- **THEN** the system logs the check-in as started once in user activity  
- **AND** duplicate send attempts do not create duplicate user-activity started records for the same prompt delivery  

#### Scenario: Check-in prompt send fails

- **GIVEN** the scheduler or dispatcher attempts to send a check-in prompt to Discord  
- **AND** Discord delivery fails because the bot is disconnected, unavailable, or cannot send  
- **WHEN** the send attempt completes unsuccessfully  
- **THEN** the system does not log the check-in as started in user activity  
- **AND** the prompt remains eligible for retry according to the reminder/dispatch retry behavior  

#### Scenario: Retry after reconnect

- **GIVEN** a check-in prompt could not be delivered while Discord was disconnected  
- **WHEN** Discord reconnects and queued or pending delivery is retried  
- **THEN** the prompt may be delivered  
- **AND** the check-in is logged as started only after the successful delivery  

### 2.4. Requirement: Discord check-in UI stays adapter-only

Discord-specific modules SHALL only map button clicks and messages into channel-agnostic check-in commands.

#### Scenario: Check-in state changes remain outside Discord view code

- **GIVEN** a user clicks Cancel or Skip  
- **WHEN** `communication/communication_channels/discord/checkin_view.py` handles the click  
- **THEN** it SHALL NOT directly mutate check-in state files  
- **AND** it SHALL use `handle_user_message` so `checkin_handler` and check-in services own state changes  

## 3. Out of scope

- Exact check-in question wording and scoring rules.
- Analytics calculations after check-in responses are stored.
- UI settings for configuring check-in schedules.
- Email check-in prompt behavior.
- Welcome/onboarding for users without linked accounts.

## 4. Manual test checklist

Run after changing Discord check-in behavior:

1. [ ] Linked Discord user starts `/checkin` or equivalent -> first check-in prompt appears.
2. [ ] User answers with a number -> next check-in prompt appears.
3. [ ] User answers with words like `three and a half` -> answer is accepted where supported.
4. [ ] `Skip Question` button -> current question is skipped and the next handler response appears ephemerally.
5. [ ] `Cancel Check-in` button -> active check-in is cancelled through the normal flow.
6. [ ] `More` button -> help appears ephemerally without changing check-in state.
7. [ ] Unlinked user clicks a check-in button -> account-not-found message appears.
8. [ ] Discord disconnected during scheduled check-in -> no false started log.
9. [ ] Discord reconnects -> pending/retry delivery logs started once only after successful send.

## 5. Related documentation

- [SPECS_GUIDE.md](SPECS_GUIDE.md) - how behavior specs fit the project  
- [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md) - channel-agnostic architecture  
- [DISCORD_GUIDE.md](../communication/communication_channels/discord/DISCORD_GUIDE.md) - Discord adapter overview  
- [TESTING_GUIDE.md](../tests/TESTING_GUIDE.md) - running automated tests  
