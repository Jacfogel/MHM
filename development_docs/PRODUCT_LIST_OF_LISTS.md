# Product List of Lists - Runtime Canonical Sources

> **File**: `development_docs/PRODUCT_LIST_OF_LISTS.md`
> **Purpose**: Single reference for product/runtime list-like data (commands, prompts, categories, channels). Sibling to [LIST_OF_LISTS.md](LIST_OF_LISTS.md) (dev-tools lists only).
> **Audience**: Maintainers, AI collaborators.
> **Last updated**: 2026-07-18

**Principles**: (1) One canonical source per list. (2) Prefer code registries over duplicated prose/help examples. (3) Align docs to code after the catalog is stable.

## 1. Channel-agnostic commands

| What | Canonical source | Uses | Other locations / overlap |
|------|------------------|------|---------------------------|
| **Base slash/bang command definitions** | `communication/message_processing/command_registry.py` - `build_base_command_definitions()` | Route maps, Discord registration, help | Do not add a second hardcoded command inventory in channel code |
| **Analytics alias commands** | `communication/message_processing/command_registry.py` - `build_analytics_alias_commands()` | Merged by `build_command_definitions()` | |
| **Full command definition set** | `communication/message_processing/command_registry.py` - `build_command_definitions()` | `MessageRouteClassifier`, Discord bot | |
| **Slash / classic route maps** | `communication/message_processing/message_route_classifier.py` | Message routing | Derived from command definitions |
| **Discord application + classic registration** | `communication/communication_channels/discord/bot.py` | Registers every definition as slash; every command except `help` as `!` | |
| **Help classic-commands example text** | `communication/message_processing/help_responses.py` - `get_commands_response()` | User-facing help | Example subset only; must not invent commands absent from `build_command_definitions()` |

**Alignment note**: When adding a product command, update `communication/message_processing/command_registry.py` first, then Discord/help consumers. Prefer deriving help text from the registry over a parallel bullet list.

## 2. Product AI prompts

| What | Canonical source | Uses | Other locations / overlap |
|------|------------------|------|---------------------------|
| **Product AI category to filename map** | `ai/prompts/manager.py` - `_PRODUCT_AI_CATEGORY_FILENAMES` | Loads `resources/prompts/product_ai/*.txt` | |
| **Product AI fragment files** | `resources/prompts/product_ai/persona.txt`, `resources/prompts/product_ai/reply_rules.txt`, `resources/prompts/product_ai/data_honesty.txt`, `resources/prompts/product_ai/action_boundaries.txt` | Prompt assembly | Edit files; keep map in sync when adding categories |
| **Prompt flows / category ownership** | `ai/prompts/flows.py` - `PRODUCT_AI_PROMPT_FLOWS` | Which categories each flow includes | |
| **Runtime-only prompt categories** | `ai/prompts/flows.py` - `RUNTIME_PROMPT_CATEGORIES` (e.g. `available_actions`) | Generated at runtime, not a file | Do not add a `.txt` for these |
| **Assistant / command system prompts** | `resources/prompts/assistant_system_prompt.txt`, `resources/prompts/command.txt`; filename constants in `ai/prompts/manager.py` | LM Studio / command interpretation | |

**Alignment note**: Conversational behavior rules belong in category files under `resources/prompts/product_ai/`, not duplicated in `ai/chat/chatbot.py` (see [SYSTEM_AI_GUIDE.md](../ai/SYSTEM_AI_GUIDE.md)).

## 3. Message / user categories

| What | Canonical source | Uses | Other locations / overlap |
|------|------------------|------|---------------------------|
| **Configured message categories** | Environment `CATEGORIES` (see `.env.example`); parsed by `messages/message_data_manager.py` - `get_message_categories()` | Message templates, schedules | Not a `core.config` constant |
| **AI-generated outbound categories** | `messages/message_data_manager.py` - `AI_GENERATED_MESSAGE_CATEGORIES` | Subset treated as AI-generated | Keep small and explicit |

## 4. Channels

| What | Canonical source | Uses | Other locations / overlap |
|------|------------------|------|---------------------------|
| **Available channels at runtime** | `core/config.py` - `get_available_channels()` | Which transports are enabled from credentials | Conditional: email and/or discord |
| **Channel class mapping** | `core/config.py` - `get_channel_class_mapping()` | Instantiation | |
| **Default orchestrator channel configs** | `communication/core/channel_orchestrator.py` - `_get_default_channel_configs()` | Defaults when user/channel config missing | |
| **Transport execution type** | `communication/communication_channels/base/base_channel.py` - `ChannelType` (`SYNC` / `ASYNC`) | Execution model (not channel name) | Email sync; Discord async |

## 5. Quick reference

| I need to... | Canonical source |
|--------------|------------------|
| Add a Discord / bang command | `communication/message_processing/command_registry.py` |
| Add a product-AI reply rule category | Add `resources/prompts/product_ai/<name>.txt` and update `_PRODUCT_AI_CATEGORY_FILENAMES` + flow ownership in `ai/prompts/flows.py` |
| Change message categories | `.env` / `CATEGORIES` and document in `.env.example` |
| Add a communication channel type | `get_available_channels` / `get_channel_class_mapping` in `core/config.py` plus channel package |

## 6. Relation to LIST_OF_LISTS

Dev-tools arrays, audit tiers, paired docs, and exclusions stay in [LIST_OF_LISTS.md](LIST_OF_LISTS.md). This file owns product/runtime lists only. Planning ownership remains in [PLANS.md](PLANS.md) Section 2.
