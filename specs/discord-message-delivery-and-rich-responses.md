# Discord message delivery and rich responses

> **File**: `specs/discord-message-delivery-and-rich-responses.md`  
> **Audience**: Developers, AI collaborators, and reviewers  
> **Purpose**: Behavior requirements for Discord send paths, embeds, views, suggestions, direct messages, and delivery failure handling  
> **Style**: Behavior requirements and scenarios (see [SPECS_GUIDE.md](SPECS_GUIDE.md))  
> **Last Updated**: 2026-05-16  
> **Implementation**: `communication/communication_channels/discord/bot.py`, `communication/communication_channels/discord/api_client.py`, `communication/communication_channels/discord/checkin_view.py`, `communication/communication_channels/discord/task_reminder_view.py`, `communication/communication_channels/base/rich_formatter.py`, `communication/delivery/message_dispatcher.py`  
> **Related**: [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md), [DISCORD_GUIDE.md](../communication/communication_channels/discord/DISCORD_GUIDE.md), [discord-message-and-command-routing.md](discord-message-and-command-routing.md)  
> **Automated tests**: `tests/behavior/test_discord_bot_behavior.py`, `tests/unit/test_discord_api_client.py`, `tests/unit/test_message_formatter.py`, `tests/unit/test_rich_formatter.py`, `tests/communication/test_retry_manager.py`  
> **Coverage matrix**: [SPEC_COVERAGE_MATRIX.md](SPEC_COVERAGE_MATRIX.md#discord-message-delivery-and-rich-responses)

## 1. Purpose

Discord delivery converts channel-agnostic messages and rich response data into Discord messages, embeds, and buttons. Delivery code SHALL validate inputs, use the correct recipient path, and return truthful success/failure results so callers can retry or avoid false state changes.

## 2. Recipient forms

Discord delivery currently supports these recipient forms:

- `discord_user:<internal_user_id>` - look up the internal user's linked Discord user ID and send a DM.
- `discord_direct:<discord_user_id>` - send a DM directly to a Discord user ID without requiring an internal user lookup.
- `<channel_id>` - send to a Discord channel when the recipient parses as a Discord channel ID.

## 3. Requirements

### 3.1. Requirement: Public send path validates required inputs

`DiscordBot.send_message` SHALL validate recipient and message before queuing delivery to the Discord event-loop thread.

#### Scenario: Missing or invalid recipient

- **GIVEN** `send_message` is called with a missing, blank, or non-string recipient  
- **WHEN** validation runs  
- **THEN** the method returns `False`  
- **AND** no Discord send command is queued  

#### Scenario: Missing or invalid message

- **GIVEN** `send_message` is called with a missing, blank, or non-string message  
- **WHEN** validation runs  
- **THEN** the method returns `False`  
- **AND** no Discord send command is queued  

#### Scenario: Bot not ready

- **GIVEN** `send_message` is called while the Discord bot is not ready  
- **WHEN** validation reaches readiness checks  
- **THEN** the method returns `False`  
- **AND** no successful-delivery side effect is reported to callers  

#### Scenario: Delivery result timeout

- **GIVEN** a send command is queued  
- **AND** no result is returned within the send timeout  
- **WHEN** `send_message` finishes waiting  
- **THEN** the method returns `False`  
- **AND** logs the timeout  

### 3.2. Requirement: Internal send path selects the correct Discord destination

`_send_message_internal` SHALL route messages to internal-user DMs, direct Discord DMs, or channel sends according to recipient prefix and parseability.

#### Scenario: Send to linked internal user's Discord DM

- **GIVEN** recipient starts with `discord_user:`  
- **AND** the internal user account has a linked `discord_user_id`  
- **WHEN** `_send_message_internal` runs  
- **THEN** it fetches or resolves the Discord user  
- **AND** sends a DM with message content and optional embed/view  
- **AND** returns `True` only after the send succeeds  

#### Scenario: Internal user has no linked Discord ID

- **GIVEN** recipient starts with `discord_user:`  
- **AND** account data does not contain a linked `discord_user_id`  
- **WHEN** `_send_message_internal` runs  
- **THEN** it returns `False`  
- **AND** logs that no Discord user ID was found  

#### Scenario: Direct Discord DM

- **GIVEN** recipient starts with `discord_direct:`  
- **WHEN** `_send_message_internal` runs  
- **THEN** it treats the suffix as a Discord user ID  
- **AND** fetches or resolves the user  
- **AND** sends a DM without requiring an internal MHM user lookup  

#### Scenario: Channel send

- **GIVEN** recipient is parseable as a Discord channel ID  
- **AND** the bot can resolve the channel  
- **WHEN** `_send_message_internal` runs  
- **THEN** it sends the message to the channel  
- **AND** includes optional embed/view when provided  
- **AND** returns `True` only after the send succeeds  

#### Scenario: Recipient cannot be resolved

- **GIVEN** recipient does not resolve to a supported DM or channel destination  
- **WHEN** `_send_message_internal` runs  
- **THEN** it returns `False`  
- **AND** logs that the recipient could not be found  

### 3.3. Requirement: Rich data is rendered as Discord embeds only when display fields exist

Discord SHALL create embeds for response `rich_data` only when it contains display-oriented data, not metadata-only keys.

#### Scenario: Rich data contains display fields

- **GIVEN** a response includes rich data such as title, description, type, fields, footer, or timestamp  
- **WHEN** Discord renders the response  
- **THEN** it creates a Discord embed  
- **AND** maps known response types to Discord embed colors  
- **AND** includes fields, footer, and timestamp when present  

#### Scenario: Rich data contains only button metadata

- **GIVEN** `rich_data` contains only metadata such as `suggestion_payloads` or `pagination_actions`  
- **WHEN** Discord checks whether display rich data exists  
- **THEN** it does not create an embed only for those metadata keys  
- **AND** may still create buttons from the metadata  

#### Scenario: Rich data or message validation fails

- **GIVEN** embed creation receives invalid message or rich data  
- **WHEN** validation runs  
- **THEN** embed creation returns `None`  
- **AND** the caller may still send plain text or buttons when possible  

### 3.4. Requirement: Suggestions and pagination render as Discord buttons

Discord SHALL render channel-agnostic suggestions and pagination actions as Discord buttons while respecting Discord limits.

#### Scenario: Suggestions present

- **GIVEN** an interaction response includes suggestion labels  
- **WHEN** Discord sends the response  
- **THEN** it creates a Discord `View`  
- **AND** adds one button per suggestion up to Discord's five-button row limit  
- **AND** stores hidden payloads for suggestion buttons when provided  

#### Scenario: Pagination actions present

- **GIVEN** an interaction response includes pagination metadata  
- **WHEN** Discord prepares action row inputs  
- **THEN** it adds pagination buttons after suggestion buttons where capacity allows  
- **AND** stores payloads that include the next intent and pagination entities  

#### Scenario: Stored suggestion payload cache grows too large

- **GIVEN** suggestion payloads are being stored for Discord buttons  
- **WHEN** the payload cache exceeds its implementation limit  
- **THEN** the oldest payload is removed  
- **SO THAT** long-running bot sessions do not accumulate unbounded button payload state  

### 3.5. Requirement: Custom views take precedence over generated suggestion views

When a caller provides a custom Discord view, the send path SHALL use it instead of generating a generic suggestion-button view.

#### Scenario: Custom view provided

- **GIVEN** `send_message` or `_send_message_internal` receives a custom view  
- **WHEN** the message is rendered  
- **THEN** the custom view is attached  
- **AND** generic suggestion buttons are not generated in place of that custom view  

#### Scenario: Custom view factory provided

- **GIVEN** a callable view factory is provided  
- **WHEN** the internal send path runs inside the Discord async context  
- **THEN** it calls the factory to create the view  
- **AND** logs and continues without the view if factory creation fails  

### 3.6. Requirement: Discord API client exposes lower-level send helpers

`DiscordAPIClient` SHALL provide direct message, channel/user lookup, guild/channel/user listing, permission checks, and connection status helpers for adapter-level use and tests.

#### Scenario: API client send message with options

- **GIVEN** `DiscordAPIClient.send_message` receives a recipient, message, and `SendMessageOptions`  
- **WHEN** the recipient resolves to a user or channel  
- **THEN** it sends message content with optional embed, view, TTS, and delete-after options  
- **AND** returns `True` only on successful send  

#### Scenario: API client handles Discord permission errors

- **GIVEN** Discord raises a forbidden/permission error while sending  
- **WHEN** the API client handles the exception  
- **THEN** it returns `False`  
- **AND** does not claim the message was delivered  

## 4. Out of scope

- Business logic that decides which message should be sent.
- Exact formatting of every command handler response.
- Welcome/onboarding buttons, check-in buttons, and task reminder buttons except where they are custom views attached to delivery.
- Discord gateway connection and reconnect rules.

## 5. Manual test checklist

Run after changing Discord delivery or rich response rendering:

1. [ ] Send to `discord_user:<internal_user_id>` -> DM reaches linked Discord user.
2. [ ] Send to `discord_direct:<discord_user_id>` -> DM reaches Discord user without internal lookup.
3. [ ] Send to channel ID -> message reaches channel.
4. [ ] Missing recipient or blank message -> returns `False` and sends nothing.
5. [ ] Bot not ready -> returns `False` and sends nothing.
6. [ ] Rich response with title/fields -> Discord embed renders.
7. [ ] Response with suggestions -> buttons render, max five.
8. [ ] Response with pagination metadata -> "Show More" style button renders and works.
9. [ ] Custom check-in/task view supplied -> custom view attaches instead of generic suggestions.
10. [ ] Forbidden/NotFound/HTTP error -> returns `False` and caller can retry or skip state mutation.

## 6. Related documentation

- [SPECS_GUIDE.md](SPECS_GUIDE.md) - how behavior specs fit the project  
- [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md) - channel-agnostic architecture  
- [DISCORD_GUIDE.md](../communication/communication_channels/discord/DISCORD_GUIDE.md) - Discord adapter overview  
- [TESTING_GUIDE.md](../tests/TESTING_GUIDE.md) - running automated tests  
