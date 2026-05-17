# Discord welcome and onboarding

> **File**: `specs/discord-welcome-and-onboarding.md`  
> **Audience**: Developers, AI collaborators, and reviewers  
> **Purpose**: Behavior requirements for Discord welcome messaging and create/link account onboarding  
> **Style**: Behavior requirements and scenarios (see [SPECS_GUIDE.md](SPECS_GUIDE.md))  
> **Last Updated**: 2026-05-16  
> **Implementation**: `communication/core/welcome_manager.py`, `communication/communication_channels/discord/welcome_handler.py`, `communication/communication_channels/discord/webhook_handler.py`, `communication/communication_channels/discord/account_flow_handler.py`, `communication/communication_channels/discord/bot.py`, `communication/command_handlers/account_handler.py`  
> **Related**: [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md), [DISCORD_GUIDE.md](../communication/communication_channels/discord/DISCORD_GUIDE.md)  
> **Automated tests**: `tests/behavior/test_welcome_manager_behavior.py`, `tests/behavior/test_welcome_handler_behavior.py`, `tests/behavior/test_webhook_handler_behavior.py`  
> **Coverage matrix**: [SPEC_COVERAGE_MATRIX.md](SPEC_COVERAGE_MATRIX.md#discord-welcome-and-onboarding)

## 1. Purpose

When someone connects or uses the MHM Discord application without a linked MHM account, they receive onboarding guidance to create or link an account. Welcome delivery is tracked so users are not spammed, while deauthorizing the app clears that tracking so a later reconnect can welcome them again.

## 2. Welcome tracking

- Persisted in `data/welcome_tracking.json` under `BASE_DATA_DIR` (resolved via `welcome_tracking_json_path()` in `communication/core/welcome_manager.py`).
- Each Discord user is keyed as `discord:<discord_user_id>`.
- Core helpers: `has_been_welcomed`, `mark_as_welcomed`, `clear_welcomed_status` (channel type `discord` for Discord paths).

## 3. Requirements

### 3.1. Requirement: One welcome cycle per authorization period

The system SHALL treat "welcomed" as a per-Discord-user flag that lasts from a successful welcome mark until the user deauthorizes the MHM application.

#### Scenario: Primary welcome on app authorization (webhook)

- **GIVEN** Discord sends an `APPLICATION_AUTHORIZED` webhook for a user  
- **AND** `has_been_welcomed(discord_user_id, channel_type="discord")` is false  
- **AND** the bot instance and event loop are available  
- **WHEN** `handle_application_authorized` runs  
- **THEN** the system schedules a welcome DM with authorization-style copy (`is_authorization=True`)  
- **AND** attaches a `WelcomeView` with "Create a New Account" and "Link to Existing Account" buttons (`timeout=None`)  
- **AND** calls `mark_as_welcomed` after a successful DM send  

#### Scenario: Already welcomed on authorization

- **GIVEN** the user is already marked welcomed for Discord  
- **WHEN** an `APPLICATION_AUTHORIZED` webhook is processed  
- **THEN** the system does not send another welcome DM  

#### Scenario: Deauthorize clears welcomed flag

- **GIVEN** a Discord user was previously welcomed  
- **WHEN** they deauthorize the MHM application (deauthorization webhook path in `communication/communication_channels/discord/webhook_handler.py`)  
- **THEN** `clear_welcomed_status(discord_user_id, channel_type="discord")` runs  
- **SO THAT** a later authorization can trigger welcome again  

#### Scenario: Welcome scheduling failure still marks welcomed

- **GIVEN** welcome DM scheduling or sending cannot complete (closed event loop, missing bot, scheduling error)  
- **WHEN** the webhook handler handles the failure paths documented in `communication/communication_channels/discord/webhook_handler.py`  
- **THEN** the system still calls `mark_as_welcomed` to avoid repeated welcome retries  

### 3.2. Requirement: Fallback welcome paths without buttons

If the webhook path does not run, the bot MAY send a **text-only** authorization-style welcome DM from interaction or message handlers in `communication/communication_channels/discord/bot.py` (no `WelcomeView`). These paths exist today for `/start`, first slash command without an MHM account, and some message-based heuristics.

#### Scenario: `/start` without linked account

- **GIVEN** a Discord user runs `/start`  
- **AND** they have no internal MHM user linked to their Discord ID  
- **WHEN** the interaction handler processes the command  
- **THEN** the system sends a text-only welcome DM (`get_welcome_message(..., is_authorization=True)`)  
- **AND** marks the user welcomed  
- **AND** replies ephemerally that setup instructions were sent via DM when DMs work  

#### Scenario: DMs disabled on `/start`

- **GIVEN** the user cannot receive DMs (`discord.Forbidden`)  
- **WHEN** `/start` welcome is attempted  
- **THEN** the system marks the user welcomed  
- **AND** sends ephemeral setup instructions including their Discord ID  

#### Scenario: First slash command without account

- **GIVEN** a user has authorized the app and runs a slash command  
- **AND** they have no internal MHM account  
- **AND** they have not been welcomed  
- **WHEN** the interaction handler runs (non-`/start` command)  
- **THEN** the system attempts a text-only welcome DM without blocking command processing  
- **AND** marks welcomed on success or on `discord.Forbidden`  

### 3.3. Requirement: Welcome message content (authorization)

Authorization-style welcome copy from `communication/core/welcome_manager.py` SHALL instruct the user to create or link an MHM account and mention tasks, check-ins, and help entry points.

#### Scenario: Authorization copy

- **GIVEN** `is_authorization=True` when building the welcome message  
- **WHEN** the message is returned to Discord adapters  
- **THEN** it describes creating or linking an account  
- **AND** references tasks, check-ins, and `/help` (or equivalent)  

### 3.4. Requirement: Welcome action buttons (webhook and WelcomeView)

When a `WelcomeView` is attached, the system SHALL provide create and link actions that start the Discord account flows.

#### Scenario: Create account button

- **GIVEN** a welcome DM includes `WelcomeView`  
- **WHEN** the user clicks "Create a New Account" (`custom_id` prefix `welcome_create_`)  
- **THEN** `start_account_creation_flow` runs  

#### Scenario: Link account button

- **GIVEN** a welcome DM includes `WelcomeView`  
- **WHEN** the user clicks "Link to Existing Account" (`custom_id` prefix `welcome_link_`)  
- **THEN** `start_account_linking_flow` runs  

#### Scenario: Persistent welcome buttons

- **GIVEN** `WelcomeView` is constructed with `timeout=None`  
- **WHEN** time passes without a click  
- **THEN** the welcome buttons remain valid (no view timeout)  
- **AND** `communication/communication_channels/discord/bot.py` may still dispatch clicks via `custom_id` after restarts  

### 3.5. Requirement: Account creation flow (Discord UI)

Discord account creation SHALL use `AccountManagementHandler` for business logic and SHALL follow the modal -> feature selection -> create sequence in `communication/communication_channels/discord/account_flow_handler.py`.

#### Scenario: User already has an account

- **GIVEN** the user clicks create or link from welcome  
- **WHEN** `check_account_status` reports an existing linked account  
- **THEN** the system responds with an ephemeral status message and does not start a new flow  

#### Scenario: Username modal and validation

- **GIVEN** the user starts account creation  
- **WHEN** they submit the create-account modal  
- **THEN** usernames must be at least 3 characters  
- **AND** taken usernames are rejected with an ephemeral error  
- **AND** a unique Discord username may be prefilled when not already taken in MHM  

#### Scenario: Feature selection defaults

- **GIVEN** the username is accepted  
- **WHEN** `FeatureSelectionView` is shown (ephemeral)  
- **THEN** task management defaults to **enabled**  
- **AND** check-ins default to **enabled**  
- **AND** automated messages default to **disabled**  
- **AND** timezone defaults to **America/Regina** until changed  

#### Scenario: Feature selection timeout

- **GIVEN** the user is on `FeatureSelectionView` (`timeout=300.0` seconds)  
- **WHEN** the view times out  
- **THEN** controls are disabled via `on_timeout`  
- **AND** the user must restart the flow to continue  

#### Scenario: Successful account creation

- **GIVEN** the user clicks "Create Account" on the feature view  
- **WHEN** `AccountManagementHandler` handles `create_account` with selected feature entities  
- **THEN** a new MHM user exists with Discord linked  
- **AND** the user receives ephemeral success feedback  
- **AND** the feature-selection message is updated to a success summary when possible  

### 3.6. Requirement: Account linking flow (Discord UI)

Linking SHALL use `AccountManagementHandler` with intent `link_account`. When the handler requests a confirmation-code step, the current Discord UI sends instructions to restart the link flow rather than presenting a second modal immediately.

#### Scenario: Link by username then confirmation-code instructions

- **GIVEN** the user starts linking and enters an existing MHM username  
- **WHEN** the handler responds with `confirmation_code_sent`  
- **THEN** the system sends the handler response ephemerally  
- **AND** sends follow-up instructions to use `/start` and select "Link Account" again to enter the confirmation code  
- **AND** does not complete linking until a later valid confirmation-code submission reaches `AccountManagementHandler`  

### 3.7. Requirement: Channel-agnostic business logic

Create, link, and status checks SHALL be implemented in `communication/command_handlers/account_handler.py` (`AccountManagementHandler`). Discord modules SHALL only provide UI and map interactions to `ParsedCommand` calls.

## 4. Out of scope

- Email or other channels' welcome wording (separate specs if needed).
- Guild-join channel messages in `communication/communication_channels/discord/bot.py` (`on_guild_join`) - server broadcast, not DM onboarding.
- Post-onboarding slash commands, check-in flows, and conversation cancel/back.
- Full email-delivery details for link confirmation codes (covered by account handler and email channel docs).

## 5. Manual test checklist

Run after changing welcome or account onboarding code:

1. [ ] New Discord test user authorizes app -> one welcome DM with **both** buttons (webhook path).
2. [ ] Re-authorize without deauthorizing -> no second welcome DM.
3. [ ] Deauthorize app -> `discord:<id>` entry removed from `data/welcome_tracking.json`.
4. [ ] Re-authorize -> welcome DM with buttons again.
5. [ ] "Create a New Account" -> modal -> feature UI -> account created; Discord ID linked.
6. [ ] "Link to Existing Account" -> username -> confirmation-code instructions appear; later valid code submission completes linking through `AccountManagementHandler`.
7. [ ] User with existing link clicks create/link -> ephemeral "already have account" style message, no duplicate account.
8. [ ] `/start` without account -> text welcome DM (no buttons) when webhook did not run first.

## 6. Related documentation

- [SPECS_GUIDE.md](SPECS_GUIDE.md) - how behavior specs fit the project  
- [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md) - channel-agnostic architecture  
- [DISCORD_GUIDE.md](../communication/communication_channels/discord/DISCORD_GUIDE.md) - Discord adapter and webhook overview  
- [TESTING_GUIDE.md](../tests/TESTING_GUIDE.md) - running automated tests  
