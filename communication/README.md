# Communication Module - Channel-Agnostic Architecture


> **File**: `communication/README.md`
> **Purpose**: Guide to channel-agnostic architecture principles and structure

---

## Core Principle

**Business logic is channel-agnostic; UI and channel-specific features are adapters.**

Core modules work across all channels (Discord, Email, future channels). Channel-specific adapters handle UI elements (buttons, modals, embeds) and delegate to core logic.

---

## Architecture Layers

### 1. Core (`communication/core/`)
Channel-agnostic business logic:
- `welcome_manager.py` - Welcome message logic and tracking
- `channel_orchestrator.py` - CommunicationManager orchestrates all channels
- `factory.py`, `retry_manager.py`, `channel_monitor.py` - Supporting utilities

### 2. Command Handlers (`communication/command_handlers/`)
Channel-agnostic command processing:
- `base_handler.py` - Abstract base class (`InteractionHandler`)
- `account_handler.py` - Account creation/linking logic
- `task_handler.py`, `profile_handler.py`, etc. - Feature handlers
- Handlers receive `ParsedCommand`, return `InteractionResponse` (no channel-specific types)

### 3. Message Processing (`communication/message_processing/`)
Channel-agnostic parsing and routing:
- `command_parser.py` - Natural language parsing
- `interaction_manager.py` - Message routing to handlers
- `conversation_flow_manager.py` - Multi-turn conversation flows

### 4. Channel Base (`communication/communication_channels/base/`)
Abstract base classes:
- `base_channel.py` - `BaseChannel` abstract class (all channels inherit)
- `message_formatter.py`, `rich_formatter.py` - Formatting utilities

### 5. Channel Adapters (`communication/communication_channels/{channel}/`)
Channel-specific UI and implementation:
- `discord/bot.py` - DiscordBot implementation
- `discord/welcome_handler.py` - Discord UI adapter (buttons, uses `welcome_manager` for logic)
- `discord/account_flow_handler.py` - Discord UI adapter (modals, uses `account_handler` for logic)
- `email/bot.py` - EmailBot implementation

---

## Key Patterns

### Handler + Adapter
**Core Logic** (channel-agnostic):
```python
# communication/command_handlers/account_handler.py
class AccountManagementHandler(InteractionHandler):
    def handle(self, user_id: str, parsed_command: ParsedCommand) -> InteractionResponse:
        return InteractionResponse("Account created!", completed=True)
```

**Channel Adapter** (Discord-specific):
```python
# communication/communication_channels/discord/account_flow_handler.py
async def start_account_creation_flow(interaction: discord.Interaction, ...):
    response = _account_handler.handle(discord_user_id, parsed_command)
    await interaction.response.send_modal(CreateAccountModal())
```

### Manager + Adapter
**Core Manager** (`communication/core/welcome_manager.py`):
```python
def get_welcome_message(channel_identifier: str, channel_type: str) -> str:
    return "Welcome to MHM! ..."
```

**Channel Adapter** (`communication/communication_channels/discord/welcome_handler.py`):
```python
def get_welcome_message_view(discord_user_id: str) -> discord.ui.View:
    message = get_welcome_message(discord_user_id, channel_type='discord')
    return WelcomeView(discord_user_id)  # Discord buttons
```

---

## Principles

### ✅ DO
- Put business logic in `core/` or `command_handlers/`
- Use abstract types (`ParsedCommand`, `InteractionResponse`)
- Delegate core logic from channel adapters
- Keep channel-specific code in `communication_channels/{channel}/`

### ❌ DON'T
- Import Discord/Email modules in core logic
- Create channel-specific UI in command handlers
- Duplicate logic across channels
- Mix business logic with UI code

---

## Adding a New Channel

1. **Create channel implementation** (`communication/communication_channels/{channel}/bot.py`):
   ```python
   class NewChannelBot(BaseChannel):
       async def send_message(self, recipient: str, message: str) -> bool:
           # Channel-specific implementation
   ```

2. **Create adapters** (if needed) - handle channel-specific UI, delegate to core handlers

3. **Register in factory** (`communication/core/factory.py`)

4. **Use existing handlers** - all handlers work automatically with new channel

---

## Directory Structure

```
communication/
├── core/                    # Channel-agnostic business logic
├── command_handlers/        # Channel-agnostic handlers
├── message_processing/      # Parsing, routing, flows
└── communication_channels/
    ├── base/               # BaseChannel, utilities
    ├── discord/            # Discord adapters
    └── email/              # Email adapters
```

---

## Current Status

**✅ Channel-Agnostic**: `welcome_manager`, `account_handler`, `task_handler`, `profile_handler`, `interaction_manager`, `conversation_flow_manager`

**🔄 Channel Adapters**: `discord/welcome_handler`, `discord/account_flow_handler`, `discord/bot`, `email/bot`

**⚠️ Needs Review**: Some email-specific code in `channel_orchestrator.py` (see TODO.md)

---

**See**: `communication/communication_channels/discord/DISCORD.md` for Discord-specific usage
