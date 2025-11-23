# Discord Channel Guide

> **File**: `communication/communication_channels/discord/DISCORD_GUIDE.md`  
> **Audience**: Developers and maintainers working on the Discord channel  
> **Purpose**: Document the Discord channel architecture, webhook-based onboarding, and integration points with the channel-agnostic core  
> **Style**: Technical, concise, implementation-focused  

This guide describes how the Discord channel is wired into the MHM communication layer: bot lifecycle, event handling, UI views, webhook-based onboarding, configuration, and how it interacts with the channel-agnostic message-processing core.

For overall communication architecture, see section 2. “Architecture Layers” in `communication/COMMUNICATION_GUIDE.md`.  
For system-wide architecture, see section 2. “High-Level Architecture” in `ARCHITECTURE.md`.  
For error-handling and logging patterns, see section 2. “Architecture Overview” in `core/ERROR_HANDLING_GUIDE.md` and section 2. “Logging Architecture” in `logs/LOGGING_GUIDE.md`.

---

## 1. Purpose and Scope

The Discord channel provides:

- A real-time chat interface for MHM (commands, natural language, check-ins, tasks).  
- Interactive UI (buttons, views) for check-ins and task reminders.  
- A webhook-based onboarding flow that automatically welcomes users who authorize the MHM Discord app.

This document focuses on implementation details and integration points, *not* end-user instructions.

---

## 2. Discord Channel Architecture

The Discord implementation is split into clear responsibilities:

- **Bot and API client**
  - `bot.py` – Creates and configures the Discord client/bot instance.  
  - `api_client.py` – Lower-level wrapper for REST calls to Discord where needed.

- **Event wiring**
  - `event_handler.py` – `DiscordEventHandler` wires Discord events (`on_ready`, `on_message`, etc.) to the channel-agnostic pipeline and any custom handlers. :contentReference[oaicite:6]{index=6}  

- **Views (UI adapters)**
  - `checkin_view.py` – Builds `discord.ui.View` for check-in buttons (cancel, skip, more info). :contentReference[oaicite:7]{index=7}  
  - `task_reminder_view.py` – Builds `discord.ui.View` for task reminder buttons (complete, remind later, more info). :contentReference[oaicite:8]{index=8}  

- **Onboarding and account flow**
  - `welcome_handler.py` – Composes and sends welcome DMs, tracks welcomed users.  
  - `account_flow_handler.py` – Handles account-related flows specific to Discord.

- **Webhook-based onboarding**
  - `webhook_server.py` – HTTP server receiving Discord webhook events (e.g., app authorization).  
  - `webhook_handler.py` – Parses and routes webhook events (e.g., `APPLICATION_AUTHORIZED`).

All of these modules ultimately route user actions into the **channel-agnostic interaction manager** in `communication/message_processing/interaction_manager.py`, which returns response objects that the Discord layer renders.

---

## 3. Bot Lifecycle and Connection Management

### 3.1. Startup

At startup:

1. The bot reads configuration from `core.config`:
   - `DISCORD_BOT_TOKEN` – Bot token for authentication.  
   - `DISCORD_APPLICATION_ID` – Application ID used for slash command registration (optional but recommended).  
   - Webhook-related settings (see section 7).

2. The Discord client is created and wired with:
   - `DiscordEventHandler` (for core events). :contentReference[oaicite:9]{index=9}  
   - Any additional handlers that need to subscribe to events.

3. When `on_ready` fires:
   - The bot logs that it is ready.  
   - Custom “ready” handlers are executed.  
   - Presence is updated (e.g., “watching your wellness”). :contentReference[oaicite:10]{index=10}  
   - The webhook server (if enabled) may be started in a background thread (see section 5).

### 3.2. Shutdown and Disconnects

The Discord event handler also tracks:

- `on_disconnect` – Logs disconnects and runs any registered cleanup. :contentReference[oaicite:11]{index=11}  
- `on_error` – Logs Discord-level errors; inner exceptions should still be managed via the shared error-handling system. :contentReference[oaicite:12]{index=12}  

When modifying shutdown behavior, follow the patterns in section 2. “Architecture Overview” and section 3. “Usage Patterns” in `core/ERROR_HANDLING_GUIDE.md`.

---

## 4. Message and Interaction Flow

### 4.1. Messages

Discord messages are handled by `DiscordEventHandler.on_message`:

1. Ignores messages from the bot itself or messages without content. :contentReference[oaicite:13]{index=13}  
2. Builds an `EventContext` containing:
   - Event type (MESSAGE).
   - User, channel, guild, message IDs.
   - Content, attachments, and embeds. :contentReference[oaicite:14]{index=14}  
3. Optionally passes the message through a set of custom message handlers. :contentReference[oaicite:15]{index=15}  
4. Resolves the internal user ID using `core.user_management.get_user_id_by_identifier(...)`. :contentReference[oaicite:16]{index=16}  
5. Routes the content through `handle_user_message(internal_user_id, message.content, "discord")` in the interaction manager. :contentReference[oaicite:17]{index=17}  
6. Sends the response to the channel via `_send_response(...)`. :contentReference[oaicite:18]{index=18}  

`_send_response`:

- Builds a Discord embed from `response.rich_data` using a rich formatter, if present.  
- Builds an interactive `discord.ui.View` from `response.suggestions`, if present.  
- Sends the appropriate combination of content, embed, and view. :contentReference[oaicite:19]{index=19}  

### 4.2. Reactions and Membership Events

Additional methods on `DiscordEventHandler` handle:

- `on_reaction_add` / `on_reaction_remove` – Currently log reactions; can be expanded for reaction-based flows. :contentReference[oaicite:20]{index=20}  
- `on_member_join` / `on_member_remove` – Log member joins/leaves and their context. :contentReference[oaicite:21]{index=21}  

These events still follow the same pattern: minimal logging + channel-agnostic integration where it makes sense.

### 4.3. UI Views and Button Callbacks

UI views are adapters between Discord’s UI and the core message pipeline:

- `get_checkin_view(user_id)` in `checkin_view.py` returns a `discord.ui.View` with:
  - “Cancel Check-in” – Routes `/cancel` through the interaction manager. :contentReference[oaicite:22]{index=22}  
  - “Skip Question” – Routes `skip` through the interaction manager. :contentReference[oaicite:23]{index=23}  
  - “More” – Sends static help text explaining how check-ins work. :contentReference[oaicite:24]{index=24}  

- `get_task_reminder_view(user_id, task_id, task_title)` in `task_reminder_view.py` returns a `discord.ui.View` with: :contentReference[oaicite:25]{index=25}  
  - “Complete Task” – Routes `complete task {task_id}` through the interaction manager.  
  - “Remind Me Later” – Sends an acknowledgement (future snooze behavior can be added).  
  - “More” – Sends a brief help message including a short task ID and example commands.

Each button callback:

- Is wrapped with `handle_errors` from `core.error_handling`, supplying a clear context string.  
- Resolves the internal user ID using `core.user_management.get_user_id_by_identifier` and the Discord user ID.  
- Uses `handle_user_message(internal_user_id, command_text, "discord")` to keep all real logic in the shared pipeline.

---

## 5. Webhook-Based Authorization and Welcome Flow

When a user authorizes the MHM Discord app (via the OAuth2 “Add to Server” / direct app authorization flow), Discord can send webhook events to the app.

### 5.1. Webhook Server

`webhook_server.py` implements a small HTTP server to receive Discord webhook events:

- Runs on `DISCORD_WEBHOOK_PORT` (see section 7).  
- Uses `DiscordWebhookHandler` (a `BaseHTTPRequestHandler` subclass) to:
  - Read request headers and body.  
  - Delegate signature verification to `verify_webhook_signature`.  
  - Parse events using `parse_webhook_event`.  
  - Call `handle_webhook_event` with the parsed data and a handle to the running bot instance.  

In development, this server may be started in a background thread when the bot becomes ready.

### 5.2. Webhook Event Handler

`webhook_handler.py` implements the event handling:

- Parses the JSON payload into a normalized event structure.  
- Distinguishes event types such as:
  - `APPLICATION_AUTHORIZED` – User/client has authorized the MHM app.  
  - `APPLICATION_DEAUTHORIZED` – User/client has removed the app (where implemented).  
- For `APPLICATION_AUTHORIZED`:
  - Extracts the user’s Discord ID from the payload.  
  - Checks whether the user already has an MHM account.  
  - Checks whether they have already been welcomed (using `welcome_handler` tracking).  
  - Sends a welcome DM via the running bot instance.  
  - Records that the user has been welcomed to avoid duplicates.

The current implementation of `verify_webhook_signature` is a **placeholder**. It logs and performs basic checks but does not yet perform full ed25519 verification against Discord’s public key. Before using this flow in production, upgrade this to a proper ed25519 implementation and update this section accordingly.

### 5.3. Welcome Handler and Tracking

`welcome_handler.py`:

- Generates a personalized welcome message, usually including:
  - A brief explanation of what MHM does.  
  - A prompt or link to create or link an account.  
- Tracks welcomed users in a JSON file (e.g., `data/discord_welcome_tracking.json`) to avoid sending multiple welcome messages to the same user.

The webhook path is the *preferred* way to detect initial authorization. If webhook delivery fails, you can supplement onboarding using join events or first-message heuristics.

---

## 6. Commands and Interaction Patterns (Developer View)

This section is **not** a user manual. It exists to help developers understand which patterns are expected in the Discord implementation.

### 6.1. Channel-Agnostic Commands

The Discord layer should treat commands and natural language the same way as other channels:

- Messages are passed raw to the interaction manager.  
- The interaction manager and command parser decide whether the message maps to:
  - Tasks (`/tasks`, “show my tasks”).  
  - Check-ins (`/checkin`).  
  - Cancellations (`/cancel`).  
  - Task completion (“complete task 1234”).  
  - General AI chat, etc.

UI buttons *simulate* those same commands by sending text like:

- `"skip"`  
- `"/cancel"`  
- `"complete task {task_id}"`  

through `handle_user_message`.

### 6.2. Slash Commands and Prefixes

Where slash commands or prefixed commands are implemented:

- Slash commands should map to the same core handlers as natural language where possible.  
- If both `/tasks` and `!tasks` exist, they should route into the same interaction path.  
- Keep the set of supported commands in sync between Discord, docs, and tests; avoid hard-coding different behavior for the same logical command across channels.

Any changes to command behavior should be reflected in:

- The core interaction handlers.  
- Relevant tests in `tests/TESTING_GUIDE.md` (sections 2 and 6).  
- This section if the mapping strategy changes.

---

## 7. Configuration and Environment Variables

Discord-related configuration lives in `core.config` and `.env` keys. Key variables include:

- `DISCORD_BOT_TOKEN`  
  - Required. Bot token used to authenticate with Discord.  
  - Must **never** be hard-coded in source; only loaded from environment.

- `DISCORD_APPLICATION_ID`  
  - Optional but recommended.  
  - Used for slash command registration and some application-level operations.

- `DISCORD_PUBLIC_KEY`  
  - Intended for webhook signature verification (webhook server).  
  - Currently used as a placeholder; proper ed25519 verification is not yet implemented.  
  - Before production use of webhooks, implement real signature verification.

- `DISCORD_WEBHOOK_PORT`  
  - Port on which the webhook HTTP server listens (default e.g. 8080).  
  - If exposing this externally (or via ngrok), this port must be reachable from Discord.

- `DISCORD_AUTO_NGROK` (if implemented)  
  - When `true`, the bot may automatically start an ngrok tunnel for development.  
  - If used, ensure that:
    - ngrok is installed and on the PATH.  
    - The resulting public URL is configured as the interactions/webhook endpoint in the Discord Developer Portal.

When changing or adding configuration:

- Update `.env.example` and related documentation (e.g., section 5. “Configuration (Environment Variables)” in `logs/LOGGING_GUIDE.md` and section 6. “Configuration and Integration” in `core/ERROR_HANDLING_GUIDE.md`) as appropriate.  
- Avoid introducing new Discord-specific environment keys unless necessary.

---

## 8. Logging, Error Handling, and Testing

### 8.1. Logging

Discord modules should log through component-specific loggers:

- `get_component_logger('discord')` – For general Discord operations.   
- `get_component_logger('discord_events')` – For event-specific logging in `event_handler.py`. :contentReference[oaicite:27]{index=27}  

Use log levels consistently:

- `info` for normal lifecycle events (bot ready, webhook server started).  
- `warning` for recoverable issues (temporary failures, missing config that can be defaulted).  
- `error` for failed operations that impact a specific user or event.  
- `debug` for diagnostic details.

See section 2. “Logging Architecture” and section 4. “Component Log Files and Layout” in `logs/LOGGING_GUIDE.md` for detailed behavior.

### 8.2. Error Handling

Most functions that touch Discord APIs or user-facing behavior should be wrapped with `handle_errors`:

- Button callbacks in `checkin_view.py` and `task_reminder_view.py` already use `@handle_errors(...)`.   
- Core events (`on_ready`, `on_message`, etc.) in `DiscordEventHandler` are decorated with `@handle_errors(...)` as well. :contentReference[oaicite:29]{index=29}  

Use clear context strings (e.g., `"creating check-in view"`, `"handling Discord message event"`) to make log messages and error categories easier to interpret.

For guidance on error categories and severity, see section 4. “Error Categories and Severity” and section 3. “Usage Patterns” in `core/ERROR_HANDLING_GUIDE.md`.

### 8.3. Testing

When modifying the Discord channel:

- **Automated tests**
  - Add unit tests for:
    - Event handler behavior (e.g., handling of missing internal user IDs).  
    - Parsing and routing behaviors that interact with the core pipeline.
  - See section 2. “Test Layout and Types” and section 6. “Writing and Extending Tests” in `tests/TESTING_GUIDE.md`.

- **Manual tests**
  - Use the manual testing guides for channel-specific flows:
    - Section 8. “Manual and Channel-Specific Testing Overview” in `tests/TESTING_GUIDE.md`.  
    - `tests/MANUAL_TESTING_GUIDE.md` and related Discord-specific sections.

- **Webhook onboarding**
  - Manually verify that:
    - The webhook server receives events on `DISCORD_WEBHOOK_PORT`.  
    - `APPLICATION_AUTHORIZED` events trigger a welcome DM *once per user*.  
    - Invalid or malformed webhook requests are logged and do not crash the bot.

Keep this section up to date when new major flows (like additional interactive views or webhook event types) are added.

---
