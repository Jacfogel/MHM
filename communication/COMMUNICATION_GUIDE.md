# Communication Module – Channel-Agnostic Architecture

> **File**: `communication/COMMUNICATION_GUIDE.md`  
> **Audience**: Developers and maintainers working on communication channels and message flow  
> **Purpose**: Explain the channel-agnostic communication architecture and how to safely extend or modify it  
> **Style**: Technical, architecture-focused, example-backed  

This guide describes how messages flow through MHM independent of channel (Discord, email, future channels), how the communication modules are structured, and how to extend them without leaking channel-specific behavior into core logic.

For the system-wide view, see section 2. “High-Level Architecture” in `ARCHITECTURE.md`.  
For Discord-specific details, see section 2. “Discord Channel Architecture” in `communication/communication_channels/discord/DISCORD_GUIDE.md`.  
For error handling and logging patterns, see section 2. “Architecture Overview” in `core/ERROR_HANDLING_GUIDE.md` and section 2. “Logging Architecture” in `logs/LOGGING_GUIDE.md`.

---

## 1. Core Principle

**Business logic is channel-agnostic; UI and channel-specific features are adapters.**

That means:

- Core modules should not know *where* a message came from (Discord, email, etc.).  
- Channel adapters are responsible for:
  - Converting channel-specific events/messages into channel-agnostic request objects.
  - Calling the shared message-processing pipeline.
  - Converting channel-agnostic responses back into channel-native primitives (messages, embeds, buttons, etc.).
- All persistent state and “real work” (tasks, schedules, AI interaction, user state) lives in core modules.

If you find yourself importing `discord`, email client libraries, or other channel SDKs into non-channel packages, that’s almost certainly a design mistake.

---

## 2. Architecture Layers

### 2.1. High-Level Flow

At a high level, every incoming message or event follows this shape:

1. **Channel event**  
   - Discord: message, interaction, button click, webhook event.  
   - Email: inbound message, reply, etc.

2. **Channel adapter**  
   - Extracts the user identity and raw content.  
   - Normalizes metadata (channel type, message IDs, timestamps).

3. **Message processing core**  
   - Parses natural language and explicit commands.  
   - Resolves the appropriate handler (task, check-in, AI chat, etc.).  
   - Produces a channel-agnostic response object.

4. **Channel adapter (outgoing)**  
   - Formats text, rich data (embeds), and interactive elements (buttons, views).  
   - Sends via the channel SDK.

The communication module owns steps **2–4**; the channel SDK only appears at the edges.

### 2.2. Message Models

Core flow is based on channel-agnostic models (names may evolve, but the pattern matters):

- **Parsed command / intent models** – Output of natural language and command parsing; contains:
  - The user’s internal ID.
  - The raw message text.
  - Parsed intent (verb, object, qualifiers).
  - Channel identifier (e.g., `"discord"`, `"email"`).
- **Response models** – Objects returned by handlers that contain:
  - Primary message text.
  - Optional rich data payload (for embeds / structured data).
  - Optional interactive suggestions (buttons, follow-up options).
  - Flags like “ephemeral” where supported.

Channel adapters must *only* work with these models, not raw business objects where possible.

### 2.3. Message Processing (`communication/message_processing/`)

Key modules (names may vary slightly, but responsibilities are stable):

- `command_parser.py`  
  - Turns raw text into parsed commands/intents.  
  - Understands both explicit commands (e.g., `/tasks`) and natural language.

- `interaction_manager.py`  
  - Central entry point for user messages from any channel.  
  - Routes parsed commands to the correct interaction handlers.  
  - Returns channel-agnostic response objects.

- `conversation_flow_manager.py` (if present)  
  - Manages multi-step flows (check-ins, onboarding, etc.).  
  - Keeps minimal state needed between messages.

See section 4. “Error Categories and Severity” in `core/ERROR_HANDLING_GUIDE.md` for how errors in these modules should be classified and handled.

### 2.4. Channel Base and Adapters (`communication/communication_channels/`)

The base layer defines contracts and utilities:

- `communication/communication_channels/base/base_channel.py`  
  - Abstract base for channel implementations (naming may differ).  
  - Exposes a standardized interface for sending messages and handling responses.

- `communication/communication_channels/base/message_formatter.py` and `rich_formatter.py`  
  - Functions/classes for formatting text, rich data, and interactive elements into channel-native structures.

Each channel then implements an adapter under `communication/communication_channels/{channel}/`, consistent with:

- **Discord**:  
  - Event wiring, bot lifecycle, and views are documented in section 2. “Discord Channel Architecture” in `communication/communication_channels/discord/DISCORD_GUIDE.md`.

- **Email** (if present):  
  - Outbound messaging and any inbound handling should follow the same adapter pattern.

---

## 3. Key Patterns

### 3.1. Error Handling Boundaries

- Channel adapters should be heavily wrapped with the shared `handle_errors` decorator from `core.error_handling`.  
- The *outer boundary* (e.g., an event callback, a webhook handler, a view button callback) should catch and log, and then:
  - Return a safe fallback message to the user, or  
  - Fail quietly while logging, if the event is optional.

See section 2. “Architecture Overview” and section 3. “Usage Patterns” in `core/ERROR_HANDLING_GUIDE.md` for the canonical patterns.

### 3.2. Logging

- Each channel adapter must use a component logger obtained via `core.logger.get_component_logger(...)`.  
- Use separate components for:
  - Core communication flow (e.g., `communication`).  
  - Channel-specific operations (e.g., `discord`, `email`).

See section 2. “Logging Architecture” and section 4. “Component Log Files and Layout” in `logs/LOGGING_GUIDE.md` for the logging structure and file layout.

### 3.3. Channel-Agnostic Message Handling

Patterns to preserve:

- The inner message-processing logic must not inspect channel-specific IDs, emoji, embeds, or button payloads.  
- Channel-specific handlers (e.g., Discord views) should translate clicks into **textual or structured commands** sent through the same `interaction_manager` path as normal messages.

Discord implementations in `checkin_view.py` and `task_reminder_view.py` follow this pattern by constructing synthetic commands (like `"skip"` or `"complete task {id}"`) and routing them through the shared interaction manager.   

### 3.4. Interactive Components

- Rich UI (buttons, dropdowns, embeds) must:
  - Be constructed in channel-specific code.
  - Use channel-agnostic data structures for their payloads where possible.
  - Defer real logic to the shared text/command pipeline.

When adding new interactive elements, follow existing Discord patterns before inventing new ones.

---

## 4. Design Principles

When modifying or extending the communication module:

- **No business logic in channels**  
  Channels should convert messages to/from core APIs, not implement task logic, AI behavior, or scheduling.

- **Narrow channel interfaces**  
  Keep channel adapters small and focused:
  - Event wiring.
  - Message conversion.
  - Calling core interaction handlers.
  - Rendering responses.

- **Consistent cross-channel behavior**  
  A task reminder or check-in should behave similarly regardless of channel:
  - Same intents.
  - Same broad response behavior (within channel constraints).

- **Idempotent handlers where feasible**  
  Where possible, duplicate events (e.g., retrying webhooks) should not do anything harmful.

---

## 5. Adding or Updating a Channel

Follow this checklist when adding a new channel or significantly changing an existing one:

1. **Understand the core flow**  
   - Re-read section 2. “Architecture Layers” in this guide.  
   - Re-read section 2. “High-Level Architecture” in `ARCHITECTURE.md`.

2. **Define the channel adapter surface**  
   - Decide how incoming events map to:
     - User identity (internal ID).
     - Raw text content.
     - Optional structured metadata.
   - Decide how the channel will represent:
     - Plain messages.
     - Rich data (embeds, cards).
     - Interactive elements (buttons, menus).

3. **Implement the adapter**  
   - Create or extend modules under `communication/communication_channels/{channel}/`.  
   - Implement:
     - Event registration and wiring.
     - Conversion into core request models.
     - Conversion from core responses into channel primitives.

4. **Integrate logging and error handling**  
   - Wrap appropriate boundaries with `handle_errors`.  
   - Use `get_component_logger('{channel}')` consistently.  
   - See `core/ERROR_HANDLING_GUIDE.md` and `logs/LOGGING_GUIDE.md` for patterns.

5. **Add tests**  
   - Unit tests for parsing and core interactions – see section 2. “Test Layout and Types” and section 6. “Writing and Extending Tests” in `tests/TESTING_GUIDE.md`.  
   - Manual channel-specific tests – see section 8. “Manual and Channel-Specific Testing Overview” in `tests/TESTING_GUIDE.md` and `tests/MANUAL_TESTING_GUIDE.md`.

6. **Document the channel**  
   - Add or update `{CHANNEL}_GUIDE.md` under `communication/communication_channels/{channel}/`.  
   - Cross-reference this guide and relevant testing/error-handling/logging sections.

---

## 6. Directory Structure

High-level structure (only communication-related parts):

- `communication/`  
  - `COMMUNICATION_GUIDE.md` – this document.  
  - `message_processing/`  
    - `command_parser.py` – natural language and command parsing.  
    - `interaction_manager.py` – central message routing and response handling.  
    - `conversation_flow_manager.py` (if present) – multi-step flow handling.  
  - `communication_channels/`  
    - `base/` – shared channel abstractions and formatters.  
    - `discord/` – Discord adapter modules (see `DISCORD_GUIDE.md`).  
    - `email/` – Email adapter modules (if present).  

Use this layout as the template when adding new channels.

---

## 7. Current Status and Future Work

- **Channel-agnostic core**  
  - Message parsing and routing are shared across channels.  
  - Error-handling and logging follow centralized patterns as documented in `core/ERROR_HANDLING_GUIDE.md` and `logs/LOGGING_GUIDE.md`.

- **Discord**  
  - Fully wired into the channel-agnostic pipeline via `event_handler`, the Discord bot, and view adapters for check-ins and task reminders.   
  - Webhook-based onboarding is implemented on the Discord side; see section 5. “Webhook-Based Authorization and Welcome Flow” in `communication/communication_channels/discord/DISCORD_GUIDE.md`.

- **Email and other channels**  
  - May be partially implemented; ensure any changes align with the patterns in sections 2–5 above.

When making structural changes to the communication module, keep this guide updated and ensure all cross-references (especially section numbers) remain valid.
