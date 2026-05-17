# Discord connection and webhook lifecycle

> **File**: `specs/discord-connection-and-webhook-lifecycle.md`  
> **Audience**: Developers, AI collaborators, and reviewers  
> **Purpose**: Behavior requirements for Discord bot initialization, connection health, reconnect handling, webhook server lifecycle, and guild join messaging  
> **Style**: Behavior requirements and scenarios (see [SPECS_GUIDE.md](SPECS_GUIDE.md))  
> **Last Updated**: 2026-05-16  
> **Implementation**: `communication/communication_channels/discord/bot.py`, `communication/communication_channels/discord/webhook_server.py`, `communication/communication_channels/discord/webhook_handler.py`, `communication/communication_channels/discord/event_handler.py`, `core/network_probe.py`, `communication/core/channel_monitor.py`  
> **Related**: [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md), [DISCORD_GUIDE.md](../communication/communication_channels/discord/DISCORD_GUIDE.md), [discord-welcome-and-onboarding.md](discord-welcome-and-onboarding.md)  
> **Automated tests**: `tests/behavior/test_discord_bot_behavior.py`, `tests/behavior/test_webhook_server_behavior.py`, `tests/behavior/test_webhook_handler_behavior.py`, `tests/unit/test_discord_event_handler.py`, `tests/unit/test_webhook_handler_gap_coverage.py`

## Purpose

The Discord channel has lifecycle behavior beyond message routing: initialization, gateway readiness, network checks, reconnect handling, webhook server startup, webhook request validation, and guild join messages. These behaviours SHALL provide truthful channel status and avoid blocking core service startup where possible.

## Requirements

### Requirement: Discord bot initialization validates configuration and network readiness

The Discord bot SHALL initialize only when required configuration and basic connectivity checks pass, and SHALL expose detailed connection status for operators and health checks.

#### Scenario: Valid token and network available

- **GIVEN** a Discord bot token is configured  
- **AND** DNS and network checks pass  
- **WHEN** the Discord bot initializes  
- **THEN** it creates the Discord client/bot structure  
- **AND** starts its isolated Discord event loop thread  
- **AND** progresses toward ready status through Discord's normal login flow  

#### Scenario: Missing token

- **GIVEN** no Discord bot token is configured  
- **WHEN** initialization is attempted  
- **THEN** initialization fails safely  
- **AND** the channel does not report itself as ready  
- **AND** a useful status/error is logged  

#### Scenario: DNS or network failure

- **GIVEN** Discord host resolution or network connectivity checks fail  
- **WHEN** initialization or recovery checks run  
- **THEN** detailed connection status reflects DNS or network failure  
- **AND** the bot does not claim it can send messages  

### Requirement: Ready event starts command sync and webhook support once

The Discord ready path SHALL run once per ready cycle and SHALL avoid duplicate command/event startup work.

#### Scenario: First ready event

- **GIVEN** the Discord gateway reports ready  
- **WHEN** `on_ready` runs for the first time  
- **THEN** the bot logs the connected identity  
- **AND** resets reconnect attempts  
- **AND** sets channel status to ready/connected  
- **AND** schedules ready tasks such as application command sync  
- **AND** starts the webhook server if configured  

#### Scenario: Duplicate ready event

- **GIVEN** the ready handler has already run for the current lifecycle  
- **WHEN** another ready event is received  
- **THEN** duplicate ready work is skipped  
- **AND** commands and webhook server startup are not duplicated  

#### Scenario: Events registered while bot is already ready

- **GIVEN** event handlers are registered after the bot is already ready  
- **WHEN** registration completes  
- **THEN** the implementation may manually trigger ready startup work on the bot loop  
- **AND** it must not create unawaited coroutine warnings if the loop is unavailable or closed  

### Requirement: Disconnect and error events update connection status without fighting discord.py reconnect

Discord lifecycle handlers SHALL record useful status but allow discord.py to handle ordinary gateway reconnects.

#### Scenario: Disconnect from ready state

- **GIVEN** the channel was ready  
- **WHEN** Discord disconnects  
- **THEN** the channel status is moved to an error/disconnected state  
- **AND** detailed connection status is updated to disconnected  
- **AND** logs state that discord.py will handle automatic reconnection  

#### Scenario: Connection-related error

- **GIVEN** `on_error` receives an error whose details suggest connection, DNS, timeout, or network failure  
- **WHEN** the error handler runs  
- **THEN** it performs DNS and network checks  
- **AND** updates detailed connection status to DNS failure or network failure when checks fail  

#### Scenario: Manual reconnect

- **GIVEN** the Discord channel is disconnected or unhealthy  
- **WHEN** manual reconnect is requested  
- **THEN** the bot attempts recovery only when reconnection rules allow it  
- **AND** reconnect attempts are tracked to avoid uncontrolled retry loops  

### Requirement: Health status reflects actual Discord readiness

Health checks SHALL use actual bot state, connection status, and latency rather than only assuming initialization success.

#### Scenario: Bot is actually connected

- **GIVEN** the bot object exists  
- **AND** Discord reports the bot is ready and not closed  
- **WHEN** `is_actually_connected`, `can_send_messages`, or health status helpers run  
- **THEN** they report connected/sendable status  
- **AND** include useful latency/status details where available  

#### Scenario: Bot is closed or unavailable

- **GIVEN** the bot object is missing, closed, or not ready  
- **WHEN** health status helpers run  
- **THEN** they report not connected/not sendable  
- **AND** the channel does not claim it can deliver Discord messages  

### Requirement: Webhook server accepts Discord webhook POSTs only with required security headers

`DiscordWebhookHandler` SHALL reject webhook POST requests missing Discord security headers and SHALL verify signatures when a public key is configured.

#### Scenario: Missing signature headers

- **GIVEN** a webhook POST lacks `X-Signature-Ed25519` or `X-Signature-Timestamp`  
- **WHEN** `do_POST` handles the request  
- **THEN** it responds with `401 Unauthorized`  
- **AND** does not route the event to `handle_webhook_event`  

#### Scenario: Signature public key configured

- **GIVEN** a webhook POST includes required signature headers  
- **AND** `DISCORD_PUBLIC_KEY` is configured  
- **WHEN** `do_POST` handles the request  
- **THEN** it verifies the request using Discord's Ed25519 signing format  
- **AND** rejects invalid signatures  
- **AND** routes only valid signed events to webhook event handling  

#### Scenario: Valid webhook event

- **GIVEN** a valid webhook POST body is received  
- **WHEN** the event is parsed  
- **THEN** the event type and payload are passed to `handle_webhook_event`  
- **AND** the handler has access to the current Discord bot instance supplied by `WebhookServer`  

#### Scenario: Unknown webhook event type

- **GIVEN** a webhook event type is not explicitly handled  
- **WHEN** `handle_webhook_event` receives it  
- **THEN** the event is acknowledged successfully  
- **AND** a debug log records that the event type was unhandled  

### Requirement: Webhook server lifecycle is explicit and stoppable

`WebhookServer` SHALL start the HTTP server on the configured port and SHALL support safe shutdown.

#### Scenario: Start webhook server

- **GIVEN** a `WebhookServer` is created with a port and bot instance  
- **WHEN** `start()` succeeds  
- **THEN** the HTTP server begins accepting requests  
- **AND** `DiscordWebhookHandler.bot_instance` is updated to the supplied bot instance  
- **AND** startup returns `True`  

#### Scenario: Stop webhook server

- **GIVEN** a webhook server is running  
- **WHEN** `stop()` is called  
- **THEN** the HTTP server is shut down safely  
- **AND** calling stop when no server exists does not raise  

### Requirement: Guild join message is server-facing and separate from user onboarding

Server/guild welcome messaging SHALL remain separate from DM onboarding and shall not mark individual Discord users as welcomed.

#### Scenario: Bot joins a guild with suitable system channel

- **GIVEN** the bot is added to a Discord server  
- **AND** the server system channel allows the bot to send messages  
- **WHEN** `on_guild_join` runs  
- **THEN** the bot sends a server-facing welcome message to the system channel  
- **AND** the message explains basic setup and quick commands  

#### Scenario: System channel unavailable but another text channel is sendable

- **GIVEN** the server system channel is unavailable or not sendable  
- **AND** another text channel allows sending  
- **WHEN** `on_guild_join` runs  
- **THEN** the bot sends the server-facing welcome message to the first suitable text channel  

#### Scenario: No sendable guild channel

- **GIVEN** no suitable server channel allows the bot to send messages  
- **WHEN** `on_guild_join` runs  
- **THEN** no welcome message is sent  
- **AND** the condition is logged  

## Out of scope

- Detailed welcome/account onboarding flow for individual Discord users; see [discord-welcome-and-onboarding.md](discord-welcome-and-onboarding.md).
- Command handler business logic after the Discord channel is ready.
- Exact ngrok tunnel setup beyond whether the webhook server can be exposed.
- Permanent Discord webhook registration in the Discord Developer Portal.

## Manual test checklist

Run after changing Discord lifecycle or webhook behavior:

1. [ ] Valid token + network -> bot reaches ready and reports connected.
2. [ ] Missing token -> bot does not report ready.
3. [ ] DNS/network failure -> detailed status reflects DNS/network failure.
4. [ ] Ready event runs once -> no duplicate command sync/webhook startup.
5. [ ] Disconnect while ready -> status becomes disconnected/error and discord.py reconnect is allowed.
6. [ ] Manual reconnect -> reconnect attempts are bounded and logged.
7. [ ] Webhook POST missing signature headers -> `401` and event not routed.
8. [ ] Valid signed webhook POST -> event routed to `handle_webhook_event` with bot instance.
9. [ ] Unknown webhook event -> acknowledged without crash.
10. [ ] Webhook server stop with no active server -> no exception.
11. [ ] Bot joins a server -> server welcome message appears in the first suitable channel.

## Related documentation

- [SPECS_GUIDE.md](SPECS_GUIDE.md) - how behavior specs fit the project  
- [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md) - channel-agnostic architecture  
- [DISCORD_GUIDE.md](../communication/communication_channels/discord/DISCORD_GUIDE.md) - Discord adapter and webhook overview  
- [TESTING_GUIDE.md](../tests/TESTING_GUIDE.md) - running automated tests  
