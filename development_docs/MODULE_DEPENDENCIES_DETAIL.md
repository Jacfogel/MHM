# Module Dependencies - MHM Project

> **File**: `development_docs/MODULE_DEPENDENCIES_DETAIL.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-05-19 18:10:24
> **Source**: `python development_tools/generate_module_dependencies.py` - Module Dependencies Generator
> **Audience**: Human developer and AI collaborators  
> **Purpose**: Complete dependency map for all modules in the MHM codebase  
> **Status**: **ACTIVE** - Hybrid auto-generated and manually enhanced  

> **See [README.md](../README.md) for complete navigation and project overview**
> **See [ARCHITECTURE.md](../ARCHITECTURE.md) for system architecture and design**
> **See [TODO.md](../TODO.md) for current documentation priorities**

## Overview

### Module Dependencies Coverage: 100.0% - COMPLETED
- **Files Scanned**: 148
- **Total Imports Found**: 1501
- **Dependencies Documented**: 148 (100% coverage)
- **Standard Library Imports**: 428 (28.5%)
- **Third-Party Imports**: 234 (15.6%)
- **Local Imports**: 839 (55.9%)
- **Last Updated**: 2026-05-19

**Status**: COMPLETED - All module dependencies have been documented with detailed dependency and usage information.

**Note**: This dependency map uses a hybrid approach. Automated analysis discovers dependencies while manual enhancements record intent and reverse dependencies.

## Import Statistics

- **Standard Library**: 428 imports (28.5%)
- **Third-Party**: 234 imports (15.6%)
- **Local**: 839 imports (55.9%)

## Module Dependencies by Directory

### `ai/` - AI services and support modules

#### `ai/__init__.py`
- **Purpose**: Communication channel implementation for __init__
- **Dependencies**:
  - **Third-party**:
    - `cache_manager (CacheEntry, ContextCache, ResponseCache, get_context_cache, get_response_cache)`
    - `chatbot (AIChatBotSingleton, get_ai_chatbot)`
    - `command_interpreter (CommandInterpreter, get_command_interpreter)`
    - `command_registry (format_command_actions_for_prompt, get_command_intent_names, inject_command_actions_into_prompt)`
    - `context_builder (ContextAnalysis, ContextBuilder, ContextData, get_context_builder)`
    - `conversation_history (ConversationHistory, ConversationMessage, ConversationSession, get_conversation_history)`
    - `conversational_context (assemble_comprehensive_messages, build_context_parts)`
    - `fallback_responses (FallbackCategory, FallbackResponses, build_contextual_fallback, get_fallback_responses)`
    - `interaction_types (AIInteractionType, interaction_type_for_mode)`
    - `lm_studio_manager (LMStudioManager, ensure_lm_studio_ready, get_lm_studio_manager, is_lm_studio_ready)`
    - `prompt_manager (PromptManager, PromptTemplate, get_prompt_manager)`
    - `response_generator (ResponseGenerator, get_response_generator)`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/cache_manager.py`
- **Purpose**: Communication channel implementation for cache_manager
- **Dependencies**:
  - **Local**:
    - `core.config (AI_CACHE_RESPONSES, AI_RESPONSE_CACHE_TTL, CONTEXT_CACHE_TTL)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `dataclasses (dataclass, field)`
    - `hashlib`
    - `threading`
    - `time`
    - `typing (Any)`
- **Used by**:
  - `ai/chatbot.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger
- Removed: ai/chatbot.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/chatbot.py`
- **Purpose**: Communication channel implementation for chatbot
- **Dependencies**:
  - **Local**:
    - `ai.cache_manager (get_response_cache)`
    - `ai.command_interpreter (get_command_interpreter)` (NEW)
    - `ai.fallback_responses (get_fallback_responses)` (NEW)
    - `ai.interaction_types (AIInteractionType, interaction_type_for_mode)` (NEW)
    - `ai.lm_studio_manager (is_lm_studio_ready)`
    - `ai.prompt_manager (get_prompt_manager)`
    - `ai.response_generator (get_response_generator)` (NEW)
    - `core.config (AI_API_CALL_TIMEOUT, AI_CACHE_RESPONSES, AI_CHAT_TEMPERATURE, AI_CLARIFICATION_TEMPERATURE, AI_COMMAND_TEMPERATURE, AI_CONNECTION_TEST_TIMEOUT, AI_CONTEXTUAL_RESPONSE_TIMEOUT, AI_MAX_RESPONSE_LENGTH, AI_MAX_RESPONSE_TOKENS, AI_MAX_RESPONSE_WORDS, AI_PERSONALIZED_MESSAGE_TIMEOUT, AI_QUICK_RESPONSE_TIMEOUT, AI_SYSTEM_PROMPT_PATH, AI_TIMEOUT_SECONDS, AI_USE_CUSTOM_PROMPT, LM_STUDIO_API_KEY, LM_STUDIO_BASE_URL, LM_STUDIO_MODEL)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.response_tracking (get_recent_responses, store_chat_interaction)` (NEW)
    - `user.context_manager (user_context_manager)`
  - **Standard Library**:
    - `asyncio`
    - `collections`
    - `os`
    - `re`
    - `threading`
  - **Third-party**:
    - `psutil`
    - `requests`
- **Used by**:
  - `communication/core/channel_orchestrator.py`
  - `communication/message_processing/command_parser.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `communication/message_processing/interaction_manager.py`

**Dependency Changes**:
- Added: ai.command_interpreter, ai.fallback_responses, ai.interaction_types, ai.response_generator, core.config, core.error_handling, core.logger, core.response_tracking
- Removed: communication/core/channel_orchestrator.py, communication/message_processing/command_parser.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/interaction_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/command_interpreter.py`
- **Purpose**: Communication channel implementation for command_interpreter
- **Dependencies**:
  - **Local**:
    - `ai.prompt_manager (get_prompt_manager)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
  - **Standard Library**:
    - `json`
- **Used by**:
  - `ai/chatbot.py`

**Dependency Changes**:
- Added: ai.prompt_manager, core.error_handling
- Removed: ai/chatbot.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/command_registry.py`
- **Purpose**: Communication channel implementation for command_registry
- **Dependencies**:
  - **Local**:
    - `communication.message_processing.command_parser (get_rule_based_intent_names)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
  - **Standard Library**:
    - `re`
- **Used by**:
  - `ai/prompt_manager.py`

**Dependency Changes**:
- Added: communication.message_processing.command_parser, core.error_handling
- Removed: ai/prompt_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/context_builder.py`
- **Purpose**: Communication channel implementation for context_builder
- **Dependencies**:
  - **Local**:
    - `core (get_user_data)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.response_tracking (get_recent_responses)` (NEW)
    - `core.time_utilities (now_datetime_full)` (NEW)
    - `user.context_manager (user_context_manager)`
  - **Standard Library**:
    - `dataclasses (dataclass)`
    - `datetime`
    - `typing (Any)`
- **Used by**:
  - `ai/conversational_context/sections.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger, core.response_tracking, core.time_utilities

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/conversation_history.py`
- **Purpose**: Communication channel implementation for conversation_history
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.time_utilities (now_datetime_full, now_timestamp_filename)` (NEW)
  - **Standard Library**:
    - `dataclasses (dataclass)`
    - `datetime`
    - `typing (Any)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.time_utilities

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/conversational_context/__init__.py`
- **Purpose**: Communication channel implementation for __init__
- **Dependencies**:
  - **Local**:
    - `ai.conversational_context.assembly (assemble_comprehensive_messages, build_context_parts)` (NEW)
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: ai.conversational_context.assembly

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/conversational_context/assembly.py`
- **Purpose**: Communication channel implementation for assembly
- **Dependencies**:
  - **Local**:
    - `ai.conversational_context.instructions (CONVERSATIONAL_CONTEXT_INSTRUCTIONS)` (NEW)
    - `ai.conversational_context.sections (append_activity_and_mood_trends, append_checkin_summary, append_conversation_history, append_feature_enablement, append_profile_sections, append_recent_sent_messages, append_schedule_details, append_task_data, append_task_reminder, append_today_checkin_status)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `user.context_manager (user_context_manager)` (NEW)
  - **Standard Library**:
    - `typing (Any)`
- **Used by**:
  - `ai/conversational_context/__init__.py`

**Dependency Changes**:
- Added: ai.conversational_context.instructions, ai.conversational_context.sections, core.error_handling, user.context_manager

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/conversational_context/instructions.py`
- **Purpose**: Communication channel implementation for instructions
- **Dependencies**: None (no imports)
- **Used by**:
  - `ai/conversational_context/assembly.py`

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/conversational_context/sections.py`
- **Purpose**: Communication channel implementation for sections
- **Dependencies**:
  - **Local**:
    - `ai.context_builder (ContextData, get_context_builder)` (NEW)
    - `core (get_user_data)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.message_management (get_recent_messages)` (NEW)
    - `core.response_tracking (checkin_runtime_timestamp, get_recent_responses, is_user_checkins_enabled)` (NEW)
    - `core.time_utilities (TIME_ONLY_MINUTE, format_timestamp, parse_timestamp_full)` (NEW)
    - `tasks (are_tasks_enabled, get_tasks_due_soon, get_user_task_stats, load_active_tasks)` (NEW)
    - `tasks.task_data_handlers (runtime_task_due_date)` (NEW)
  - **Standard Library**:
    - `datetime (date)`
    - `typing (Any)`
- **Used by**:
  - `ai/conversational_context/assembly.py`

**Dependency Changes**:
- Added: ai.context_builder, core, core.error_handling, core.logger, core.message_management, core.response_tracking, core.time_utilities, tasks, tasks.task_data_handlers

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/fallback_responses/__init__.py`
- **Purpose**: Communication channel implementation for __init__
- **Dependencies**:
  - **Local**:
    - `ai.fallback_responses.categories (FallbackCategory)` (NEW)
    - `ai.fallback_responses.coordinator (build_contextual_fallback)` (NEW)
    - `ai.fallback_responses.data_access (get_recent_responses, get_user_data)` (NEW)
    - `ai.fallback_responses.personalized (build_personalized_message)` (NEW)
    - `ai.fallback_responses.profile_helpers (personalize_with_profile_name)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: ai.fallback_responses.categories, ai.fallback_responses.coordinator, ai.fallback_responses.data_access, ai.fallback_responses.personalized, ai.fallback_responses.profile_helpers, core.error_handling, core.logger

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/fallback_responses/categories.py`
- **Purpose**: Communication channel implementation for categories
- **Dependencies**:
  - **Standard Library**:
    - `enum (Enum)`
- **Used by**:
  - `ai/fallback_responses/__init__.py`
  - `ai/fallback_responses/checkin_summary.py`
  - `ai/fallback_responses/conversational.py`
  - `ai/fallback_responses/coordinator.py`
  - `ai/fallback_responses/personalized.py`

**Dependency Changes**:
- Removed: ai/fallback_responses/__init__.py, ai/fallback_responses/checkin_summary.py, ai/fallback_responses/conversational.py, ai/fallback_responses/coordinator.py, ai/fallback_responses/personalized.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/fallback_responses/checkin_summary.py`
- **Purpose**: Communication channel implementation for checkin_summary
- **Dependencies**:
  - **Local**:
    - `ai.fallback_responses.categories (FallbackCategory)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
  - **Standard Library**:
    - `dataclasses (dataclass)`
- **Used by**:
  - `ai/fallback_responses/coordinator.py`

**Dependency Changes**:
- Added: ai.fallback_responses.categories, core.error_handling
- Removed: ai/fallback_responses/coordinator.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/fallback_responses/conversational.py`
- **Purpose**: Communication channel implementation for conversational
- **Dependencies**:
  - **Local**:
    - `ai.fallback_responses.categories (FallbackCategory)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
- **Used by**:
  - `ai/fallback_responses/coordinator.py`

**Dependency Changes**:
- Added: ai.fallback_responses.categories, core.error_handling
- Removed: ai/fallback_responses/coordinator.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/fallback_responses/coordinator.py`
- **Purpose**: Communication channel implementation for coordinator
- **Dependencies**:
  - **Local**:
    - `ai.fallback_responses.categories (FallbackCategory)` (NEW)
    - `ai.fallback_responses.checkin_summary (compute_checkin_metrics, try_checkin_summary_response)` (NEW)
    - `ai.fallback_responses.conversational (default_contextual_response, try_conversational_support, try_new_user_no_context, try_technical_unavailable)` (NEW)
    - `ai.fallback_responses.data_access` (NEW)
    - `ai.fallback_responses.profile_helpers (load_user_context, name_prefix_from_context, preferred_name_from_context)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
- **Used by**:
  - `ai/fallback_responses/__init__.py`

**Dependency Changes**:
- Added: ai.fallback_responses.categories, ai.fallback_responses.checkin_summary, ai.fallback_responses.conversational, ai.fallback_responses.data_access, ai.fallback_responses.profile_helpers, core.error_handling
- Removed: ai/fallback_responses/__init__.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/fallback_responses/data_access.py`
- **Purpose**: Communication channel implementation for data_access
- **Dependencies**:
  - **Local**:
    - `core (get_user_data)` (NEW)
    - `core.response_tracking (get_recent_responses)` (NEW)
- **Used by**:
  - `ai/fallback_responses/__init__.py`
  - `ai/fallback_responses/coordinator.py`
  - `ai/fallback_responses/personalized.py`
  - `ai/fallback_responses/profile_helpers.py`

**Dependency Changes**:
- Added: core, core.response_tracking
- Removed: ai/fallback_responses/__init__.py, ai/fallback_responses/coordinator.py, ai/fallback_responses/personalized.py, ai/fallback_responses/profile_helpers.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/fallback_responses/personalized.py`
- **Purpose**: Communication channel implementation for personalized
- **Dependencies**:
  - **Local**:
    - `ai.fallback_responses.categories (FallbackCategory)` (NEW)
    - `ai.fallback_responses.data_access` (NEW)
    - `ai.fallback_responses.profile_helpers (name_prefix_from_context)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
- **Used by**:
  - `ai/fallback_responses/__init__.py`

**Dependency Changes**:
- Added: ai.fallback_responses.categories, ai.fallback_responses.data_access, ai.fallback_responses.profile_helpers, core.error_handling
- Removed: ai/fallback_responses/__init__.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/fallback_responses/profile_helpers.py`
- **Purpose**: Communication channel implementation for profile_helpers
- **Dependencies**:
  - **Local**:
    - `ai.fallback_responses.data_access` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
- **Used by**:
  - `ai/fallback_responses/__init__.py`
  - `ai/fallback_responses/coordinator.py`
  - `ai/fallback_responses/personalized.py`

**Dependency Changes**:
- Added: ai.fallback_responses.data_access, core.error_handling
- Removed: ai/fallback_responses/__init__.py, ai/fallback_responses/coordinator.py, ai/fallback_responses/personalized.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/interaction_types.py`
- **Purpose**: Communication channel implementation for interaction_types
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
  - **Standard Library**:
    - `enum (StrEnum)`
- **Used by**:
  - `ai/chatbot.py`

**Dependency Changes**:
- Added: core.error_handling
- Removed: ai/chatbot.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/lm_studio_manager.py`
- **Purpose**: Communication channel implementation for lm_studio_manager
- **Dependencies**:
  - **Local**:
    - `core.config (AI_CONNECTION_TEST_TIMEOUT, LM_STUDIO_API_KEY, LM_STUDIO_BASE_URL, LM_STUDIO_MODEL)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `subprocess`
  - **Third-party**:
    - `requests`
- **Used by**:
  - `ai/chatbot.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger
- Removed: ai/chatbot.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/prompt_manager.py`
- **Purpose**: Communication channel implementation for prompt_manager
- **Dependencies**:
  - **Local**:
    - `ai.command_registry (inject_command_actions_into_prompt)` (NEW)
    - `core.config (AI_SYSTEM_PROMPT_PATH, AI_USE_CUSTOM_PROMPT)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `dataclasses (dataclass)`
    - `os`
    - `sys`
- **Used by**:
  - `ai/chatbot.py`
  - `ai/command_interpreter.py`
  - `ai/response_generator.py`

**Dependency Changes**:
- Added: ai.command_registry, core.config, core.error_handling, core.logger
- Removed: ai/chatbot.py, ai/command_interpreter.py, ai/response_generator.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/response_generator.py`
- **Purpose**: Communication channel implementation for response_generator
- **Dependencies**:
  - **Local**:
    - `ai.conversational_context (assemble_comprehensive_messages)` (NEW)
    - `ai.prompt_manager (get_prompt_manager)` (NEW)
    - `core.config (AI_MIN_RESPONSE_LENGTH)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
- **Used by**:
  - `ai/chatbot.py`

**Dependency Changes**:
- Added: ai.conversational_context, ai.prompt_manager, core.config, core.error_handling, core.logger
- Removed: ai/chatbot.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

### `communication/` - Communication services and orchestration

#### `communication/__init__.py`
- **Purpose**: Communication channel implementation for __init__
- **Dependencies**:
  - **Local**:
    - `core.channel_monitor (ChannelMonitor)` (NEW)
    - `core.channel_orchestrator (BotInitializationError, CommunicationManager, MessageSendError)` (NEW)
    - `core.factory (ChannelFactory)` (NEW)
    - `core.retry_manager (QueuedMessage, RetryManager)` (NEW)
  - **Third-party**:
    - `command_handlers.analytics_handler (AnalyticsHandler)`
    - `command_handlers.base_handler (InteractionHandler)`
    - `command_handlers.checkin_handler (CheckinHandler)`
    - `command_handlers.interaction_handlers (HelpHandler, get_all_handlers, get_interaction_handler)`
    - `command_handlers.profile_handler (ProfileHandler)`
    - `command_handlers.schedule_handler (ScheduleManagementHandler)`
    - `command_handlers.shared_types (InteractionResponse, ParsedCommand)`
    - `command_handlers.task_handler (TaskManagementHandler)`
    - `communication_channels.base.base_channel (BaseChannel, ChannelConfig, ChannelStatus, ChannelType)`
    - `communication_channels.base.command_registry (CommandRegistry, DiscordCommandRegistry, EmailCommandRegistry, get_command_registry)`
    - `communication_channels.base.message_formatter (EmailMessageFormatter, MessageFormatter, TextMessageFormatter, get_message_formatter)`
    - `communication_channels.base.rich_formatter (DiscordRichFormatter, EmailRichFormatter, RichFormatter, get_rich_formatter)`
    - `communication_channels.discord.api_client (DiscordAPIClient, MessageData, SendMessageOptions, get_discord_api_client)`
    - `communication_channels.discord.bot (DiscordBot, DiscordConnectionStatus)`
    - `communication_channels.discord.event_handler (DiscordEventHandler, EventContext, EventType, get_discord_event_handler)`
    - `communication_channels.email.bot (EmailBot, EmailBotError)`
    - `message_processing.command_parser (EnhancedCommandParser, ParsingResult, get_enhanced_command_parser, parse_command)`
    - `message_processing.conversation_flow_manager (ConversationManager, conversation_manager)`
    - `message_processing.interaction_manager (CommandDefinition, InteractionManager, get_interaction_manager, handle_user_message)`
    - `message_processing.message_router (MessageRouter, MessageType, RoutingResult, get_message_router)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.channel_monitor, core.channel_orchestrator, core.factory, core.retry_manager
- Removed: command_handlers.analytics_handler, command_handlers.base_handler, command_handlers.checkin_handler, command_handlers.interaction_handlers, command_handlers.profile_handler, command_handlers.schedule_handler, command_handlers.shared_types, command_handlers.task_handler, communication_channels.base.base_channel, communication_channels.base.command_registry, communication_channels.base.message_formatter, communication_channels.base.rich_formatter, communication_channels.discord.api_client, communication_channels.discord.bot, communication_channels.discord.event_handler, communication_channels.email.bot, message_processing.command_parser, message_processing.conversation_flow_manager, message_processing.interaction_manager, message_processing.message_router

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/command_handlers/__init__.py`
- **Purpose**: Communication channel implementation for __init__
- **Dependencies**:
  - **Third-party**:
    - `base_handler (InteractionHandler)`
    - `interaction_handlers (get_all_handlers, get_interaction_handler)`
    - `shared_types (InteractionResponse, ParsedCommand)`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/command_handlers/account_handler.py`
- **Purpose**: Communication channel implementation for account_handler
- **Dependencies**:
  - **Local**:
    - `communication.command_handlers.base_handler (InteractionHandler)`
    - `communication.command_handlers.shared_types (InteractionResponse, ParsedCommand)`
    - `communication.core.channel_orchestrator (CommunicationManager)`
    - `core (create_new_user, get_all_user_ids, get_user_data, get_user_id_by_identifier, update_user_account)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `secrets`
    - `string`
    - `typing (Any)`
  - **Third-party**:
    - `storage.user_data_operations (update_user_index)`
- **Used by**:
  - `communication/command_handlers/interaction_handlers.py`
  - `communication/communication_channels/discord/account_flow_handler.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger
- Removed: communication/command_handlers/interaction_handlers.py, communication/communication_channels/discord/account_flow_handler.py, storage.user_data_operations

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/command_handlers/analytics_handler.py`
- **Purpose**: Communication channel implementation for analytics_handler
- **Dependencies**:
  - **Local**:
    - `communication.command_handlers.base_handler (InteractionHandler)`
    - `communication.command_handlers.shared_types (InteractionResponse, ParsedCommand)`
    - `core (get_user_data)` (NEW)
    - `core.checkin_analytics (CheckinAnalytics)` (NEW)
    - `core.checkin_dynamic_manager (dynamic_checkin_manager)` (NEW)
    - `core.error_handling (handle_ai_error, handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.response_tracking (checkin_runtime_timestamp, get_checkins_by_days, get_recent_checkins)` (NEW)
    - `core.time_utilities (parse_timestamp_full)` (NEW)
    - `tasks (get_user_task_stats, load_active_tasks, load_completed_tasks)` (NEW)
  - **Standard Library**:
    - `collections (Counter)`
    - `typing (Any)`
- **Used by**:
  - `communication/command_handlers/interaction_handlers.py`
  - `communication/message_processing/conversation_flow_manager.py`

**Dependency Changes**:
- Added: core, core.checkin_analytics, core.checkin_dynamic_manager, core.error_handling, core.logger, core.response_tracking, core.time_utilities, tasks
- Removed: communication/command_handlers/interaction_handlers.py, communication/message_processing/conversation_flow_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/command_handlers/base_handler.py`
- **Purpose**: Communication channel implementation for base_handler
- **Dependencies**:
  - **Local**:
    - `communication.command_handlers.shared_types (InteractionResponse, ParsedCommand)`
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `abc (ABC, abstractmethod)`
  - **Third-party**:
    - `storage.user_data_validation (is_valid_user_id)`
- **Used by**:
  - `communication/command_handlers/account_handler.py`
  - `communication/command_handlers/analytics_handler.py`
  - `communication/command_handlers/checkin_handler.py`
  - `communication/command_handlers/interaction_handlers.py`
  - `communication/command_handlers/notebook_handler.py`
  - `communication/command_handlers/profile_handler.py`
  - `communication/command_handlers/schedule_handler.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger
- Removed: communication/command_handlers/account_handler.py, communication/command_handlers/analytics_handler.py, communication/command_handlers/checkin_handler.py, communication/command_handlers/interaction_handlers.py, communication/command_handlers/notebook_handler.py, communication/command_handlers/profile_handler.py, communication/command_handlers/schedule_handler.py, storage.user_data_validation

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/command_handlers/checkin_handler.py`
- **Purpose**: Communication channel implementation for checkin_handler
- **Dependencies**:
  - **Local**:
    - `communication.command_handlers.base_handler (InteractionHandler)`
    - `communication.command_handlers.shared_types (InteractionResponse, ParsedCommand)`
    - `communication.message_processing.conversation_flow_manager (conversation_manager)`
    - `core.checkin_service (checkin_display_date, get_checkin_start_status, get_recent_checkin_summary)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.response_tracking (checkin_runtime_timestamp, get_recent_checkins, is_user_checkins_enabled)` (NEW)
  - **Standard Library**:
    - `typing (Any)`
- **Used by**:
  - `communication/command_handlers/interaction_handlers.py`

**Dependency Changes**:
- Added: core.checkin_service, core.error_handling, core.logger, core.response_tracking
- Removed: communication/command_handlers/interaction_handlers.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/command_handlers/interaction_handlers.py`
- **Purpose**: Communication channel implementation for interaction_handlers
- **Dependencies**:
  - **Local**:
    - `communication.command_handlers.account_handler (AccountManagementHandler)`
    - `communication.command_handlers.analytics_handler (AnalyticsHandler)`
    - `communication.command_handlers.base_handler (InteractionHandler)`
    - `communication.command_handlers.checkin_handler (CheckinHandler)`
    - `communication.command_handlers.notebook_handler (NotebookHandler)`
    - `communication.command_handlers.profile_handler (ProfileHandler)`
    - `communication.command_handlers.schedule_handler (ScheduleManagementHandler)`
    - `communication.command_handlers.shared_types (InteractionResponse, ParsedCommand)`
    - `communication.command_handlers.task_handler (TaskManagementHandler)`
    - `core (get_user_data)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.response_tracking (get_recent_checkins, is_user_checkins_enabled)` (NEW)
    - `tasks (load_active_tasks)` (NEW)
  - **Standard Library**:
    - `typing (Any)`
- **Used by**:
  - `communication/communication_channels/discord/bot.py`
  - `communication/message_processing/command_parser.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `communication/message_processing/interaction_manager.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger, core.response_tracking, tasks
- Removed: communication/communication_channels/discord/bot.py, communication/message_processing/command_parser.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/interaction_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/command_handlers/notebook_handler.py`
- **Purpose**: Communication channel implementation for notebook_handler
- **Dependencies**:
  - **Local**:
    - `communication.command_handlers.base_handler (InteractionHandler)`
    - `communication.command_handlers.shared_types (InteractionResponse, PaginationAction, ParsedCommand)`
    - `communication.message_processing.conversation_flow_manager (FLOW_LIST_ITEMS, FLOW_NOTE_BODY, conversation_manager)`
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.pagination (PageRequest, paginate_items)` (NEW)
    - `core.tags (parse_tags_from_text)` (NEW)
    - `core.time_utilities (now_timestamp_full)` (NEW)
    - `notebook.notebook_schemas (Entry)`
    - `notebook.notebook_service (add_entry_tags, add_item_to_list, append_entry_body, archive_notebook_entry, create_journal_from_command, create_list_from_command, create_note_from_command, create_quick_note_from_command, delete_list_item, get_entry, list_archived_entries, list_entries_by_group, list_entries_by_tag, list_inbox_entries, list_pinned_entries, list_recent_entries, pin_notebook_entry, remove_entry_tags, replace_entry_body, search_entries_for_display, set_entry_group, set_list_item_done)` (NEW)
    - `notebook.notebook_validation (format_short_id)`
  - **Standard Library**:
    - `collections.abc (Callable)`
    - `typing (Any)`
- **Used by**:
  - `communication/command_handlers/interaction_handlers.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.pagination, core.tags, core.time_utilities, notebook.notebook_service
- Removed: collections.abc, communication/command_handlers/interaction_handlers.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/command_handlers/profile_handler.py`
- **Purpose**: Communication channel implementation for profile_handler
- **Dependencies**:
  - **Local**:
    - `communication.command_handlers.base_handler (InteractionHandler)`
    - `communication.command_handlers.shared_types (InteractionResponse, ParsedCommand)`
    - `core (get_user_data, save_user_data)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.response_tracking (get_recent_checkins)` (NEW)
    - `tasks` (NEW)
    - `user.profile_service (apply_profile_updates, load_profile_sections)` (NEW)
  - **Standard Library**:
    - `typing (Any)`
- **Used by**:
  - `communication/command_handlers/interaction_handlers.py`
  - `communication/message_processing/conversation_flow_manager.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger, core.response_tracking, tasks, user.profile_service
- Removed: communication/command_handlers/interaction_handlers.py, communication/message_processing/conversation_flow_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/command_handlers/schedule_handler.py`
- **Purpose**: Communication channel implementation for schedule_handler
- **Dependencies**:
  - **Local**:
    - `communication.command_handlers.base_handler (InteractionHandler)`
    - `communication.command_handlers.shared_types (InteractionResponse, ParsedCommand)`
    - `core (get_user_categories)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.schedule_runtime (get_schedule_time_periods, set_schedule_periods)` (NEW)
  - **Standard Library**:
    - `typing (Any)`
- **Used by**:
  - `communication/command_handlers/interaction_handlers.py`
  - `communication/message_processing/conversation_flow_manager.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger, core.schedule_runtime
- Removed: communication/command_handlers/interaction_handlers.py, communication/message_processing/conversation_flow_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/command_handlers/shared_types.py`
- **Purpose**: Communication channel implementation for shared_types
- **Dependencies**:
  - **Standard Library**:
    - `dataclasses (dataclass)`
    - `typing (Any)`
- **Used by**:
  - `communication/command_handlers/account_handler.py`
  - `communication/command_handlers/analytics_handler.py`
  - `communication/command_handlers/base_handler.py`
  - `communication/command_handlers/checkin_handler.py`
  - `communication/command_handlers/interaction_handlers.py`
  - `communication/command_handlers/notebook_handler.py`
  - `communication/command_handlers/profile_handler.py`
  - `communication/command_handlers/schedule_handler.py`
  - `communication/communication_channels/discord/account_flow_handler.py`
  - `communication/communication_channels/discord/bot.py`
  - `communication/message_processing/command_parser.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `communication/message_processing/interaction_manager.py`

**Dependency Changes**:
- Removed: communication/command_handlers/account_handler.py, communication/command_handlers/analytics_handler.py, communication/command_handlers/base_handler.py, communication/command_handlers/checkin_handler.py, communication/command_handlers/interaction_handlers.py, communication/command_handlers/notebook_handler.py, communication/command_handlers/profile_handler.py, communication/command_handlers/schedule_handler.py, communication/communication_channels/discord/account_flow_handler.py, communication/communication_channels/discord/bot.py, communication/message_processing/command_parser.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/interaction_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/command_handlers/task_handler.py`
- **Purpose**: Communication channel implementation for task_handler
- **Dependencies**:
  - **Local**:
    - `core.checkin_analytics (CheckinAnalytics)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.time_utilities (now_datetime_full)` (NEW)
    - `tasks (task_service)` (NEW)
    - `tasks.task_data_handlers (runtime_task_due_date, runtime_task_recurrence_interval, runtime_task_recurrence_pattern)` (NEW)
  - **Standard Library**:
    - `datetime`
    - `importlib`
    - `typing (Any)`
  - **Third-party**:
    - `base_handler (InteractionHandler, InteractionResponse, ParsedCommand)`
- **Used by**:
  - `communication/command_handlers/interaction_handlers.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `communication/message_processing/interaction_manager.py`

**Dependency Changes**:
- Added: core.checkin_analytics, core.error_handling, core.logger, core.time_utilities, tasks, tasks.task_data_handlers
- Removed: communication/command_handlers/interaction_handlers.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/interaction_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/__init__.py`
- **Purpose**: Communication channel implementation for __init__
- **Dependencies**: None (no imports)
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/base/base_channel.py`
- **Purpose**: Abstract base class for communication channels
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, get_logger)` (NEW)
  - **Standard Library**:
    - `abc (ABC, abstractmethod)`
    - `dataclasses (dataclass)`
    - `enum (Enum)`
    - `typing (Any)`
- **Used by**:
  - `communication/communication_channels/discord/bot.py`
  - `communication/communication_channels/email/bot.py`
  - `communication/core/channel_monitor.py`
  - `communication/core/channel_orchestrator.py`
  - `communication/core/factory.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger
- Removed: communication/communication_channels/discord/bot.py, communication/communication_channels/email/bot.py, communication/core/channel_monitor.py, communication/core/channel_orchestrator.py, communication/core/factory.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/base/command_registry.py`
- **Purpose**: Communication channel implementation for command_registry
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `abc (ABC, abstractmethod)`
    - `collections.abc (Callable)`
    - `dataclasses (dataclass)`
  - **Third-party**:
    - `discord (app_commands)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling, core.logger
- Removed: collections.abc

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/base/message_formatter.py`
- **Purpose**: Communication channel implementation for message_formatter
- **Dependencies**:
  - **Local**:
    - `core.error_handling (DataError, handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `abc (ABC, abstractmethod)`
    - `typing (Any)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling, core.logger

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/base/rich_formatter.py`
- **Purpose**: Communication channel implementation for rich_formatter
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `abc (ABC, abstractmethod)`
    - `typing (Any)`
  - **Third-party**:
    - `discord`
- **Used by**:
  - `communication/communication_channels/discord/event_handler.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger
- Removed: communication/communication_channels/discord/event_handler.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/discord/account_flow_handler.py`
- **Purpose**: Communication channel implementation for account_flow_handler
- **Dependencies**:
  - **Local**:
    - `communication.command_handlers.account_handler (AccountManagementHandler)`
    - `communication.command_handlers.shared_types (ParsedCommand)`
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `contextlib`
  - **Third-party**:
    - `discord`
    - `storage.user_data_presets (TIMEZONE_OPTIONS)`
- **Used by**:
  - `communication/communication_channels/discord/bot.py`
  - `communication/communication_channels/discord/welcome_handler.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger
- Removed: communication/communication_channels/discord/bot.py, communication/communication_channels/discord/welcome_handler.py, storage.user_data_presets

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/discord/api_client.py`
- **Purpose**: Communication channel implementation for api_client
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `asyncio`
    - `dataclasses (dataclass)`
    - `time`
    - `typing (Any)`
  - **Third-party**:
    - `discord`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling, core.logger

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/discord/bot.py`
- **Purpose**: Communication channel implementation for bot
- **Dependencies**:
  - **Local**:
    - `communication.command_handlers.interaction_handlers (get_interaction_handler)` (NEW)
    - `communication.command_handlers.shared_types (InteractionResponse, ParsedCommand)` (NEW)
    - `communication.communication_channels.base.base_channel (BaseChannel, ChannelConfig, ChannelStatus, ChannelType)`
    - `communication.communication_channels.discord.account_flow_handler (start_account_creation_flow, start_account_linking_flow)`
    - `communication.communication_channels.discord.webhook_server (WebhookServer)`
    - `communication.communication_channels.discord.welcome_handler (get_welcome_message, has_been_welcomed, mark_as_welcomed)`
    - `communication.message_processing.interaction_manager (get_interaction_manager, handle_user_message)`
    - `core (get_user_data, get_user_id_by_identifier, save_user_data)` (NEW)
    - `core.config (DISCORD_APPLICATION_ID, DISCORD_AUTO_NGROK, DISCORD_BOT_TOKEN, DISCORD_WEBHOOK_PORT)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `asyncio`
    - `collections.abc (Awaitable)`
    - `contextlib`
    - `enum`
    - `gc`
    - `os`
    - `queue`
    - `shutil`
    - `socket`
    - `subprocess`
    - `threading`
    - `time`
    - `typing (Any, cast)`
  - **Third-party**:
    - `aiohttp`
    - `discord (app_commands, discord)`
    - `discord.ext (commands)`
    - `dns.resolver`
    - `psutil`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: communication.command_handlers.interaction_handlers, communication.command_handlers.shared_types, core, core.config, core.error_handling, core.logger
- Removed: collections.abc, discord.ext, dns.resolver

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/discord/checkin_view.py`
- **Purpose**: Communication channel implementation for checkin_view
- **Dependencies**:
  - **Local**:
    - `communication.message_processing.interaction_manager (handle_user_message)`
    - `core (get_user_id_by_identifier)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `typing (Optional)`
  - **Third-party**:
    - `discord`
- **Used by**:
  - `communication/reminders/checkin_prompt_dispatcher.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger
- Removed: communication/reminders/checkin_prompt_dispatcher.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/discord/event_handler.py`
- **Purpose**: Communication channel implementation for event_handler
- **Dependencies**:
  - **Local**:
    - `communication.communication_channels.base.rich_formatter (get_rich_formatter)`
    - `communication.message_processing.interaction_manager (handle_user_message)`
    - `core (get_user_id_by_identifier)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `collections.abc (Callable)`
    - `dataclasses (dataclass)`
    - `enum (Enum)`
    - `time`
    - `typing (Any)`
  - **Third-party**:
    - `discord`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core, core.error_handling, core.logger
- Removed: collections.abc

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/discord/task_reminder_view.py`
- **Purpose**: Communication channel implementation for task_reminder_view
- **Dependencies**:
  - **Local**:
    - `communication.message_processing.interaction_manager (handle_user_message)`
    - `core (get_user_id_by_identifier)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `typing (Optional)`
  - **Third-party**:
    - `discord`
- **Used by**:
  - `communication/reminders/reminder_dispatcher.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger
- Removed: communication/reminders/reminder_dispatcher.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/discord/webhook_handler.py`
- **Purpose**: Communication channel implementation for webhook_handler
- **Dependencies**:
  - **Local**:
    - `communication.communication_channels.discord.welcome_handler (get_welcome_message, get_welcome_message_view)`
    - `communication.core.welcome_manager (clear_welcomed_status, has_been_welcomed, mark_as_welcomed)`
    - `core (get_user_id_by_identifier, update_user_account)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (_is_testing_environment, get_component_logger)` (NEW)
  - **Standard Library**:
    - `asyncio`
    - `concurrent.futures (Future)`
    - `json`
    - `typing (Any)`
- **Used by**:
  - `communication/communication_channels/discord/webhook_server.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger
- Removed: communication/communication_channels/discord/webhook_server.py, concurrent.futures

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/discord/webhook_server.py`
- **Purpose**: Communication channel implementation for webhook_server
- **Dependencies**:
  - **Local**:
    - `communication.communication_channels.discord.webhook_handler (handle_webhook_event, parse_webhook_event)`
    - `core.config (DISCORD_PUBLIC_KEY)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `http.server (BaseHTTPRequestHandler, HTTPServer)`
    - `json`
    - `threading`
  - **Third-party**:
    - `nacl.exceptions (BadSignatureError)`
    - `nacl.signing (VerifyKey)`
- **Used by**:
  - `communication/communication_channels/discord/bot.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger
- Removed: communication/communication_channels/discord/bot.py, http.server, nacl.exceptions, nacl.signing

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/discord/welcome_handler.py`
- **Purpose**: Communication channel implementation for welcome_handler
- **Dependencies**:
  - **Local**:
    - `communication.communication_channels.discord.account_flow_handler (start_account_creation_flow, start_account_linking_flow)`
    - `communication.core.welcome_manager (clear_welcomed_status, get_welcome_message, has_been_welcomed, mark_as_welcomed)`
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `typing (TYPE_CHECKING)`
  - **Third-party**:
    - `discord`
- **Used by**:
  - `communication/communication_channels/discord/bot.py`
  - `communication/communication_channels/discord/webhook_handler.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger
- Removed: communication/communication_channels/discord/bot.py, communication/communication_channels/discord/webhook_handler.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/email/bot.py`
- **Purpose**: Communication channel implementation for bot
- **Dependencies**:
  - **Local**:
    - `communication.communication_channels.base.base_channel (BaseChannel, ChannelConfig, ChannelStatus, ChannelType)`
    - `core.config (EMAIL_IMAP_SERVER, EMAIL_SMTP_PASSWORD, EMAIL_SMTP_SERVER, EMAIL_SMTP_USERNAME)` (NEW)
    - `core.error_handling (ConfigurationError, handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `asyncio`
    - `email.header (decode_header)`
    - `email.message (EmailMessage)`
    - `email.mime.text (MIMEText)`
    - `email.parser (BytesParser)`
    - `email.policy (default)`
    - `imaplib`
    - `re`
    - `smtplib`
    - `socket`
    - `time`
    - `typing (Any)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger
- Removed: email.header, email.message, email.mime.text, email.parser, email.policy

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/core/__init__.py`
- **Purpose**: Communication channel implementation for __init__
- **Dependencies**:
  - **Standard Library**:
    - `importlib.util`
    - `sys`
  - **Third-party**:
    - `channel_monitor (ChannelMonitor)`
    - `factory (ChannelFactory)`
    - `retry_manager (QueuedMessage, RetryManager)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Removed: importlib.util

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/core/channel_monitor.py`
- **Purpose**: Communication channel implementation for channel_monitor
- **Dependencies**:
  - **Local**:
    - `communication.communication_channels.base.base_channel (BaseChannel)`
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.time_utilities (now_datetime_full)` (NEW)
  - **Standard Library**:
    - `threading`
    - `time`
    - `typing (Any)`
- **Used by**:
  - `communication/core/channel_orchestrator.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.time_utilities
- Removed: communication/core/channel_orchestrator.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/core/channel_orchestrator.py`
- **Purpose**: Communication channel implementation for channel_orchestrator
- **Dependencies**:
  - **Local**:
    - `ai.chatbot (get_ai_chatbot)`
    - `communication.communication_channels.base.base_channel (BaseChannel, ChannelConfig, ChannelStatus)`
    - `communication.core.channel_monitor (ChannelMonitor)`
    - `communication.core.factory (ChannelFactory)`
    - `communication.core.message_send_result (MessageSendResult)` (NEW)
    - `communication.core.retry_manager (RetryManager)`
    - `communication.delivery.message_dispatcher (PredefinedMessageDispatcher)` (NEW)
    - `communication.message_processing.conversation_flow_manager (conversation_manager)`
    - `communication.message_processing.interaction_manager (handle_user_message)`
    - `communication.reminders.checkin_prompt_dispatcher (CheckinPromptDispatcher)` (NEW)
    - `communication.reminders.reminder_dispatcher (TaskReminderDispatcher)` (NEW)
    - `core (get_user_data, get_user_id_by_identifier)` (NEW)
    - `core.config (DISCORD_BOT_TOKEN, EMAIL_SMTP_SERVER, get_available_channels)` (NEW)
    - `core.error_handling (handle_communication_error, handle_errors, handle_network_error)` (NEW)
    - `core.logger (force_restart_logging, get_component_logger)` (NEW)
    - `core.message_management (store_sent_message)` (NEW)
    - `core.network_probe (wait_for_network)` (NEW)
    - `core.schedule_runtime (get_current_time_periods_with_validation)` (NEW)
  - **Standard Library**:
    - `asyncio`
    - `contextlib`
    - `re`
    - `threading`
    - `time`
    - `typing (Any)`
    - `uuid`
- **Used by**:
  - `communication/command_handlers/account_handler.py`
  - `core/service.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: communication.core.message_send_result, communication.delivery.message_dispatcher, communication.reminders.checkin_prompt_dispatcher, communication.reminders.reminder_dispatcher, core, core.config, core.error_handling, core.logger, core.message_management, core.network_probe, core.schedule_runtime
- Removed: communication/command_handlers/account_handler.py, core/service.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/core/factory.py`
- **Purpose**: Communication channel implementation for factory
- **Dependencies**:
  - **Local**:
    - `communication.communication_channels.base.base_channel (BaseChannel, ChannelConfig)`
    - `core.config` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `importlib`
- **Used by**:
  - `communication/core/channel_orchestrator.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger
- Removed: communication/core/channel_orchestrator.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/core/message_send_result.py`
- **Purpose**: Communication channel implementation for message_send_result
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
  - **Standard Library**:
    - `__future__ (annotations)`
    - `dataclasses (dataclass)`
- **Used by**:
  - `communication/core/channel_orchestrator.py`
  - `communication/reminders/reminder_dispatcher.py`

**Dependency Changes**:
- Added: core.error_handling
- Removed: communication/core/channel_orchestrator.py, communication/reminders/reminder_dispatcher.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/core/retry_manager.py`
- **Purpose**: Communication channel implementation for retry_manager
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.time_utilities (now_datetime_full)` (NEW)
  - **Standard Library**:
    - `dataclasses (dataclass)`
    - `datetime`
    - `queue`
    - `threading`
    - `time`
- **Used by**:
  - `communication/core/channel_orchestrator.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.time_utilities
- Removed: communication/core/channel_orchestrator.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/core/welcome_manager.py`
- **Purpose**: Communication channel implementation for welcome_manager
- **Dependencies**:
  - **Local**:
    - `core.config (BASE_DATA_DIR)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.time_utilities (now_timestamp_full, now_timestamp_utc_iso)` (NEW)
  - **Standard Library**:
    - `pathlib (Path)`
    - `typing (Any)`
  - **Third-party**:
    - `storage.runtime_state_storage (get_runtime_state_path, load_runtime_state_json, save_runtime_state_json)`
- **Used by**:
  - `communication/communication_channels/discord/webhook_handler.py`
  - `communication/communication_channels/discord/welcome_handler.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger, core.time_utilities
- Removed: communication/communication_channels/discord/webhook_handler.py, communication/communication_channels/discord/welcome_handler.py, storage.runtime_state_storage

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/delivery/__init__.py`
- **Purpose**: Communication channel implementation for __init__
- **Dependencies**:
  - **Local**:
    - `communication.delivery.message_dispatcher (PredefinedMessageDispatcher)` (NEW)
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: communication.delivery.message_dispatcher

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/delivery/message_dispatcher.py`
- **Purpose**: Communication channel implementation for message_dispatcher
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.message_management (get_recent_messages, load_user_messages, store_sent_message)` (NEW)
    - `core.schedule_runtime (get_current_day_names, get_current_time_periods_with_validation)` (NEW)
  - **Standard Library**:
    - `__future__ (annotations)`
    - `random`
    - `typing (Any)`
- **Used by**:
  - `communication/core/channel_orchestrator.py`
  - `communication/delivery/__init__.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.message_management, core.schedule_runtime
- Removed: communication/core/channel_orchestrator.py, communication/delivery/__init__.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/message_processing/__init__.py`
- **Purpose**: Communication channel implementation for __init__
- **Dependencies**:
  - **Third-party**:
    - `interaction_manager (CommandDefinition, InteractionManager, get_interaction_manager, handle_user_message)`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/message_processing/command_parser.py`
- **Purpose**: Communication channel implementation for command_parser
- **Dependencies**:
  - **Local**:
    - `ai.chatbot (get_ai_chatbot)`
    - `communication.command_handlers.interaction_handlers (get_all_handlers)`
    - `communication.command_handlers.shared_types (ParsedCommand)`
    - `communication.message_processing.intent_validation (is_valid_intent)`
    - `core.config (AI_AI_ENHANCED_CONFIDENCE_THRESHOLD, AI_AI_PARSING_BASE_CONFIDENCE, AI_AI_PARSING_PARTIAL_CONFIDENCE, AI_COMMAND_PARSING_TIMEOUT, AI_RULE_BASED_FALLBACK_THRESHOLD, AI_RULE_BASED_HIGH_CONFIDENCE_THRESHOLD)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.tags (parse_tags_from_text)` (NEW)
  - **Standard Library**:
    - `contextlib (suppress)`
    - `dataclasses (dataclass)`
    - `json`
    - `re`
    - `typing (Any)`
- **Used by**:
  - `ai/command_registry.py`
  - `communication/message_processing/interaction_manager.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger, core.tags
- Removed: ai/command_registry.py, communication/message_processing/interaction_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/message_processing/conversation_flow_manager.py`
- **Purpose**: Communication channel implementation for conversation_flow_manager
- **Dependencies**:
  - **Local**:
    - `ai.chatbot (get_ai_chatbot)`
    - `communication.command_handlers.analytics_handler (AnalyticsHandler)`
    - `communication.command_handlers.interaction_handlers (get_interaction_handler)`
    - `communication.command_handlers.profile_handler (ProfileHandler)`
    - `communication.command_handlers.schedule_handler (ScheduleManagementHandler)`
    - `communication.command_handlers.shared_types (ParsedCommand)`
    - `communication.command_handlers.task_handler (TaskManagementHandler)`
    - `core (get_user_data)` (NEW)
    - `core.checkin_dynamic_manager (dynamic_checkin_manager)` (NEW)
    - `core.config (BASE_DATA_DIR)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.response_tracking (get_recent_checkins, is_user_checkins_enabled, store_user_response)` (NEW)
    - `core.tags (parse_tags_from_text)` (NEW)
    - `core.time_utilities (DATE_ONLY, TIME_ONLY_MINUTE, format_timestamp, now_datetime_full, now_timestamp_full, parse_date_and_time_minute, parse_date_only, parse_time_only_minute, parse_timestamp_full)` (NEW)
    - `notebook.notebook_data_manager (create_list, create_note)`
    - `tasks (get_task_by_id, update_task)` (NEW)
    - `tasks.task_data_handlers (runtime_task_due_date, runtime_task_due_time)` (NEW)
    - `tasks.task_schemas (VALID_PRIORITIES)` (NEW)
  - **Standard Library**:
    - `contextlib (suppress)`
    - `datetime (datetime, timedelta)`
    - `importlib`
    - `random`
    - `re`
    - `typing (Any)`
  - **Third-party**:
    - `storage.runtime_state_storage (get_runtime_state_path, load_runtime_state_json, save_runtime_state_json)`
    - `storage.user_data_v2_base (generate_short_id)`
- **Used by**:
  - `communication/command_handlers/checkin_handler.py`
  - `communication/command_handlers/notebook_handler.py`
  - `communication/core/channel_orchestrator.py`
  - `communication/message_processing/interaction_manager.py`
  - `communication/reminders/checkin_prompt_dispatcher.py`
  - `core/service_requests.py`

**Dependency Changes**:
- Added: core, core.checkin_dynamic_manager, core.config, core.error_handling, core.logger, core.response_tracking, core.tags, core.time_utilities, tasks, tasks.task_data_handlers, tasks.task_schemas
- Removed: communication/command_handlers/checkin_handler.py, communication/command_handlers/notebook_handler.py, communication/core/channel_orchestrator.py, communication/message_processing/interaction_manager.py, communication/reminders/checkin_prompt_dispatcher.py, core/service_requests.py, storage.runtime_state_storage, storage.user_data_v2_base

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/message_processing/intent_validation.py`
- **Purpose**: Communication channel implementation for intent_validation
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
  - **Standard Library**:
    - `collections.abc (Mapping)`
    - `typing (Any)`
- **Used by**:
  - `communication/message_processing/command_parser.py`
  - `communication/message_processing/interaction_manager.py`

**Dependency Changes**:
- Added: core.error_handling
- Removed: collections.abc, communication/message_processing/command_parser.py, communication/message_processing/interaction_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/message_processing/interaction_manager.py`
- **Purpose**: Communication channel implementation for interaction_manager
- **Dependencies**:
  - **Local**:
    - `ai.chatbot (get_ai_chatbot)`
    - `communication.command_handlers.interaction_handlers (get_all_handlers, get_interaction_handler)`
    - `communication.command_handlers.shared_types (InteractionResponse, ParsedCommand)`
    - `communication.command_handlers.task_handler (TaskManagementHandler)`
    - `communication.message_processing.command_parser (ParsingResult, get_enhanced_command_parser)`
    - `communication.message_processing.conversation_flow_manager (FLOW_TASK_REMINDER, conversation_manager)`
    - `communication.message_processing.intent_validation (is_valid_intent)`
    - `core (get_user_categories)` (NEW)
    - `core.config (AI_MAX_RESPONSE_LENGTH)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.response_tracking (checkin_runtime_timestamp, get_recent_checkins, is_user_checkins_enabled)` (NEW)
    - `core.time_format_constants (DATE_DISPLAY_MONTH_DAY)` (NEW)
    - `core.time_utilities (format_timestamp, now_datetime_full, parse_date_and_time_minute, parse_date_only, parse_timestamp_full)` (NEW)
    - `tasks (load_active_tasks)` (NEW)
    - `tasks.task_data_handlers (runtime_task_due_date, runtime_task_due_time)` (NEW)
  - **Standard Library**:
    - `dataclasses (dataclass)`
    - `datetime`
    - `json`
    - `re`
    - `typing (Any)`
- **Used by**:
  - `communication/communication_channels/discord/bot.py`
  - `communication/communication_channels/discord/checkin_view.py`
  - `communication/communication_channels/discord/event_handler.py`
  - `communication/communication_channels/discord/task_reminder_view.py`
  - `communication/core/channel_orchestrator.py`

**Dependency Changes**:
- Added: core, core.config, core.error_handling, core.logger, core.response_tracking, core.time_format_constants, core.time_utilities, tasks, tasks.task_data_handlers
- Removed: communication/communication_channels/discord/bot.py, communication/communication_channels/discord/checkin_view.py, communication/communication_channels/discord/event_handler.py, communication/communication_channels/discord/task_reminder_view.py, communication/core/channel_orchestrator.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/message_processing/message_router.py`
- **Purpose**: Communication channel implementation for message_router
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `dataclasses (dataclass)`
    - `enum (Enum)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling, core.logger

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/reminders/__init__.py`
- **Purpose**: Communication channel implementation for __init__
- **Dependencies**:
  - **Local**:
    - `communication.reminders.checkin_prompt_dispatcher (CheckinPromptDispatcher)` (NEW)
    - `communication.reminders.reminder_dispatcher (TaskReminderDispatcher)` (NEW)
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: communication.reminders.checkin_prompt_dispatcher, communication.reminders.reminder_dispatcher

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/reminders/checkin_prompt_dispatcher.py`
- **Purpose**: Communication channel implementation for checkin_prompt_dispatcher
- **Dependencies**:
  - **Local**:
    - `communication.communication_channels.discord.checkin_view (get_checkin_view)` (NEW)
    - `communication.core (channel_orchestrator)` (NEW)
    - `communication.message_processing.conversation_flow_manager (conversation_manager)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `__future__ (annotations)`
    - `asyncio`
    - `typing (Any)`
- **Used by**:
  - `communication/core/channel_orchestrator.py`
  - `communication/reminders/__init__.py`

**Dependency Changes**:
- Added: communication.communication_channels.discord.checkin_view, communication.core, communication.message_processing.conversation_flow_manager, core.error_handling, core.logger
- Removed: communication/core/channel_orchestrator.py, communication/reminders/__init__.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/reminders/reminder_dispatcher.py`
- **Purpose**: Communication channel implementation for reminder_dispatcher
- **Dependencies**:
  - **Local**:
    - `communication.communication_channels.discord.task_reminder_view (get_task_reminder_view)` (NEW)
    - `communication.core (channel_orchestrator)` (NEW)
    - `communication.core.message_send_result (MessageSendResult)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `tasks (are_tasks_enabled, get_task_by_id)` (NEW)
    - `tasks.task_data_handlers (runtime_task_due_date, runtime_task_is_completed)` (NEW)
  - **Standard Library**:
    - `__future__ (annotations)`
    - `asyncio`
    - `typing (Any)`
- **Used by**:
  - `communication/core/channel_orchestrator.py`
  - `communication/reminders/__init__.py`

**Dependency Changes**:
- Added: communication.communication_channels.discord.task_reminder_view, communication.core, communication.core.message_send_result, core.error_handling, core.logger, tasks, tasks.task_data_handlers
- Removed: communication/core/channel_orchestrator.py, communication/reminders/__init__.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

### `core/` - Core system modules (foundation)

#### `core/__init__.py`
- **Purpose**: Core system module for __init__
- **Dependencies**:
  - **Standard Library**:
    - `importlib (import_module)`
    - `typing (Any, TYPE_CHECKING)`
  - **Third-party**:
    - `storage.user_data_read (get_user_data)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Removed: storage.user_data_read

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/auto_cleanup.py`
- **Purpose**: Automatic cache cleanup and maintenance
- **Dependencies**:
  - **Local**:
    - `core (get_all_user_ids)` (NEW)
    - `core.config (BASE_DATA_DIR, get_backups_dir)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.message_management (archive_old_messages)` (NEW)
    - `core.time_utilities (DATE_ONLY, format_timestamp, now_datetime_full, now_timestamp_full)` (NEW)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
    - `time`
- **Used by**:
  - `core/service.py`
  - `scheduler/jobs.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core, core.config, core.error_handling, core.logger, core.message_management, core.time_utilities
- Removed: core/service.py, scheduler/jobs.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Automatic cache cleanup and maintenance
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/backup_manager.py`
- **Purpose**: Manages automatic backups and rollback operations
- **Dependencies**:
  - **Local**:
    - `core (get_all_user_ids, get_user_data)` (NEW)
    - `core.config (LOG_AI_FILE, LOG_DISCORD_FILE, LOG_ERRORS_FILE, LOG_MAIN_FILE, LOG_USER_ACTIVITY_FILE, core.config)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.file_locking (file_lock)` (NEW)
    - `core.logger (get_component_logger, get_logger)` (NEW)
    - `core.time_utilities (TIMESTAMP_FULL, format_timestamp, now_timestamp_filename, now_timestamp_full)` (NEW)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `time`
    - `traceback`
    - `typing (Dict, List, Optional, Tuple)`
- **Used by**:
  - `scheduler/maintenance.py`

**Dependency Changes**:
- Added: core, core.config, core.error_handling, core.file_locking, core.logger, core.time_utilities
- Removed: scheduler/maintenance.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Manages automatic backups and rollback operations
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/checkin_analytics.py`
- **Purpose**: Analyzes check-in data and provides insights
- **Dependencies**:
  - **Local**:
    - `core (get_user_data)` (NEW)
    - `core.checkin_dynamic_manager (dynamic_checkin_manager)` (NEW)
    - `core.error_handling (ValidationError, handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.response_tracking (checkin_runtime_timestamp, get_checkins_by_days)` (NEW)
    - `core.time_utilities (parse_time_only_minute, parse_timestamp_full)` (NEW)
  - **Standard Library**:
    - `datetime (timedelta)`
    - `statistics`
    - `typing (Any)`
- **Used by**:
  - `communication/command_handlers/analytics_handler.py`
  - `communication/command_handlers/task_handler.py`
  - `ui/dialogs/user_analytics_dialog.py`

**Dependency Changes**:
- Added: core, core.checkin_dynamic_manager, core.error_handling, core.logger, core.response_tracking, core.time_utilities
- Removed: communication/command_handlers/analytics_handler.py, communication/command_handlers/task_handler.py, ui/dialogs/user_analytics_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Analyzes check-in data and provides insights
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/checkin_dynamic_manager.py`
- **Purpose**: Core system module for checkin_dynamic_manager
- **Dependencies**:
  - **Local**:
    - `core (get_user_data, update_user_preferences)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.file_operations (load_json_data)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `pathlib (Path)`
    - `random`
    - `re`
    - `typing (Any)`
- **Used by**:
  - `communication/command_handlers/analytics_handler.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `core/checkin_analytics.py`
  - `ui/widgets/checkin_settings_widget.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.file_operations, core.logger
- Removed: communication/command_handlers/analytics_handler.py, communication/message_processing/conversation_flow_manager.py, core/checkin_analytics.py, ui/widgets/checkin_settings_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/checkin_service.py`
- **Purpose**: Main service orchestration and management
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.response_tracking (checkin_runtime_timestamp, get_recent_checkins, is_user_checkins_enabled)` (NEW)
    - `core.time_utilities (parse_timestamp_full)` (NEW)
  - **Standard Library**:
    - `__future__ (annotations)`
    - `dataclasses (dataclass)`
    - `datetime (date)`
    - `typing (Any)`
- **Used by**:
  - `communication/command_handlers/checkin_handler.py`

**Dependency Changes**:
- Added: core.error_handling, core.response_tracking, core.time_utilities
- Removed: communication/command_handlers/checkin_handler.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/config.py`
- **Purpose**: Configuration management and validation
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_configuration_error, handle_errors)` (NEW)
  - **Standard Library**:
    - `contextlib`
    - `logging`
    - `os`
    - `pathlib (Path)`
    - `typing (Any)`
  - **Third-party**:
    - `dotenv (load_dotenv)`
- **Used by**:
  - `ai/cache_manager.py`
  - `ai/chatbot.py`
  - `ai/lm_studio_manager.py`
  - `ai/prompt_manager.py`
  - `ai/response_generator.py`
  - `communication/communication_channels/discord/bot.py`
  - `communication/communication_channels/discord/webhook_server.py`
  - `communication/communication_channels/email/bot.py`
  - `communication/core/channel_orchestrator.py`
  - `communication/core/factory.py`
  - `communication/core/welcome_manager.py`
  - `communication/message_processing/command_parser.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `communication/message_processing/interaction_manager.py`
  - `core/auto_cleanup.py`
  - `core/backup_manager.py`
  - `core/file_operations.py`
  - `core/logger.py`
  - `core/message_management.py`
  - `core/service.py`
  - `core/service_utilities.py`
  - `core/tags.py`
  - `core/user_lookup.py`
  - `core/user_management.py`
  - `scheduler/manager.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/schedule_editor_dialog.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling
- Removed: ai/cache_manager.py, ai/chatbot.py, ai/lm_studio_manager.py, ai/prompt_manager.py, ai/response_generator.py, communication/communication_channels/discord/bot.py, communication/communication_channels/discord/webhook_server.py, communication/communication_channels/email/bot.py, communication/core/channel_orchestrator.py, communication/core/factory.py, communication/core/welcome_manager.py, communication/message_processing/command_parser.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/interaction_manager.py, core/auto_cleanup.py, core/backup_manager.py, core/file_operations.py, core/logger.py, core/message_management.py, core/service.py, core/service_utilities.py, core/tags.py, core/user_lookup.py, core/user_management.py, scheduler/manager.py, ui/dialogs/account_creator_dialog.py, ui/dialogs/schedule_editor_dialog.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Configuration management and validation
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/delivery.py`
- **Purpose**: Core system module for delivery
- **Dependencies**:
  - **Standard Library**:
    - `__future__ (annotations)`
    - `typing (Any, Protocol, runtime_checkable)`
- **Used by**:
  - `core/service_requests.py`
  - `scheduler/manager.py`

**Dependency Changes**:
- Removed: core/service_requests.py, scheduler/manager.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/error_handling.py`
- **Purpose**: Centralized error handling and recovery
- **Dependencies**:
  - **Local**:
    - `core.network_probe (wait_for_network)` (NEW)
    - `core.time_utilities (now_datetime_full, now_timestamp_filename, now_timestamp_full)` (NEW)
  - **Standard Library**:
    - `asyncio`
    - `collections.abc (Callable)`
    - `contextlib`
    - `functools`
    - `json`
    - `logging`
    - `os`
    - `shutil`
    - `sys`
    - `threading`
    - `traceback`
    - `typing (Any)`
- **Used by**:
  - `ai/cache_manager.py`
  - `ai/chatbot.py`
  - `ai/command_interpreter.py`
  - `ai/command_registry.py`
  - `ai/context_builder.py`
  - `ai/conversation_history.py`
  - `ai/conversational_context/assembly.py`
  - `ai/conversational_context/sections.py`
  - `ai/fallback_responses/__init__.py`
  - `ai/fallback_responses/checkin_summary.py`
  - `ai/fallback_responses/conversational.py`
  - `ai/fallback_responses/coordinator.py`
  - `ai/fallback_responses/personalized.py`
  - `ai/fallback_responses/profile_helpers.py`
  - `ai/interaction_types.py`
  - `ai/lm_studio_manager.py`
  - `ai/prompt_manager.py`
  - `ai/response_generator.py`
  - `communication/command_handlers/account_handler.py`
  - `communication/command_handlers/analytics_handler.py`
  - `communication/command_handlers/base_handler.py`
  - `communication/command_handlers/checkin_handler.py`
  - `communication/command_handlers/interaction_handlers.py`
  - `communication/command_handlers/notebook_handler.py`
  - `communication/command_handlers/profile_handler.py`
  - `communication/command_handlers/schedule_handler.py`
  - `communication/command_handlers/task_handler.py`
  - `communication/communication_channels/base/base_channel.py`
  - `communication/communication_channels/base/command_registry.py`
  - `communication/communication_channels/base/message_formatter.py`
  - `communication/communication_channels/base/rich_formatter.py`
  - `communication/communication_channels/discord/account_flow_handler.py`
  - `communication/communication_channels/discord/api_client.py`
  - `communication/communication_channels/discord/bot.py`
  - `communication/communication_channels/discord/checkin_view.py`
  - `communication/communication_channels/discord/event_handler.py`
  - `communication/communication_channels/discord/task_reminder_view.py`
  - `communication/communication_channels/discord/webhook_handler.py`
  - `communication/communication_channels/discord/webhook_server.py`
  - `communication/communication_channels/discord/welcome_handler.py`
  - `communication/communication_channels/email/bot.py`
  - `communication/core/channel_monitor.py`
  - `communication/core/channel_orchestrator.py`
  - `communication/core/factory.py`
  - `communication/core/message_send_result.py`
  - `communication/core/retry_manager.py`
  - `communication/core/welcome_manager.py`
  - `communication/delivery/message_dispatcher.py`
  - `communication/message_processing/command_parser.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `communication/message_processing/intent_validation.py`
  - `communication/message_processing/interaction_manager.py`
  - `communication/message_processing/message_router.py`
  - `communication/reminders/checkin_prompt_dispatcher.py`
  - `communication/reminders/reminder_dispatcher.py`
  - `core/auto_cleanup.py`
  - `core/backup_manager.py`
  - `core/checkin_analytics.py`
  - `core/checkin_dynamic_manager.py`
  - `core/checkin_service.py`
  - `core/config.py`
  - `core/file_auditor.py`
  - `core/file_locking.py`
  - `core/file_operations.py`
  - `core/headless_service.py`
  - `core/logger.py`
  - `core/message_analytics.py`
  - `core/message_management.py`
  - `core/message_preview.py`
  - `core/pagination.py`
  - `core/response_tracking.py`
  - `core/schedule_document_defaults.py`
  - `core/schedule_runtime.py`
  - `core/schedule_utilities.py`
  - `core/schemas.py`
  - `core/service.py`
  - `core/service_requests.py`
  - `core/service_utilities.py`
  - `core/tags.py`
  - `core/ui_management.py`
  - `core/user_lookup.py`
  - `core/user_management.py`
  - `run_headless_service.py`
  - `scheduler/jobs.py`
  - `scheduler/maintenance.py`
  - `scheduler/manager.py`
  - `scheduler/task_reminders.py`
  - `tasks/task_data_handlers.py`
  - `tasks/task_data_manager.py`
  - `tasks/task_service.py`
  - `tasks/task_validation.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/admin_panel.py`
  - `ui/dialogs/category_management_dialog.py`
  - `ui/dialogs/channel_management_dialog.py`
  - `ui/dialogs/checkin_management_dialog.py`
  - `ui/dialogs/dialog_helpers.py`
  - `ui/dialogs/message_editor_dialog.py`
  - `ui/dialogs/process_watcher_dialog.py`
  - `ui/dialogs/schedule_editor_dialog.py`
  - `ui/dialogs/task_completion_dialog.py`
  - `ui/dialogs/task_crud_dialog.py`
  - `ui/dialogs/task_edit_dialog.py`
  - `ui/dialogs/task_management_dialog.py`
  - `ui/dialogs/user_analytics_dialog.py`
  - `ui/dialogs/user_profile_dialog.py`
  - `ui/generate_ui_files.py`
  - `ui/period_row_management.py`
  - `ui/ui_app_qt.py`
  - `ui/widgets/category_selection_widget.py`
  - `ui/widgets/channel_selection_widget.py`
  - `ui/widgets/checkin_settings_widget.py`
  - `ui/widgets/dynamic_list_container.py`
  - `ui/widgets/dynamic_list_field.py`
  - `ui/widgets/period_row_widget.py`
  - `ui/widgets/tag_widget.py`
  - `ui/widgets/task_settings_widget.py`
  - `ui/widgets/user_profile_settings_widget.py`
  - `user/context_manager.py`
  - `user/profile_service.py`
  - `user/user_context.py`
  - `user/user_preferences.py`

**Dependency Changes**:
- Added: core.network_probe, core.time_utilities
- Removed: ai/cache_manager.py, ai/chatbot.py, ai/command_interpreter.py, ai/command_registry.py, ai/context_builder.py, ai/conversation_history.py, ai/fallback_responses/__init__.py, ai/interaction_types.py, ai/lm_studio_manager.py, ai/prompt_manager.py, ai/response_generator.py, collections.abc, communication/command_handlers/account_handler.py, communication/command_handlers/analytics_handler.py, communication/command_handlers/base_handler.py, communication/command_handlers/checkin_handler.py, communication/command_handlers/interaction_handlers.py, communication/command_handlers/notebook_handler.py, communication/command_handlers/profile_handler.py, communication/command_handlers/schedule_handler.py, communication/command_handlers/task_handler.py, communication/communication_channels/base/base_channel.py, communication/communication_channels/base/command_registry.py, communication/communication_channels/base/message_formatter.py, communication/communication_channels/base/rich_formatter.py, communication/communication_channels/discord/account_flow_handler.py, communication/communication_channels/discord/api_client.py, communication/communication_channels/discord/bot.py, communication/communication_channels/discord/checkin_view.py, communication/communication_channels/discord/event_handler.py, communication/communication_channels/discord/task_reminder_view.py, communication/communication_channels/discord/webhook_handler.py, communication/communication_channels/discord/webhook_server.py, communication/communication_channels/discord/welcome_handler.py, communication/communication_channels/email/bot.py, communication/core/channel_monitor.py, communication/core/channel_orchestrator.py, communication/core/factory.py, communication/core/message_send_result.py, communication/core/retry_manager.py, communication/core/welcome_manager.py, communication/delivery/message_dispatcher.py, communication/message_processing/command_parser.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/intent_validation.py, communication/message_processing/interaction_manager.py, communication/message_processing/message_router.py, communication/reminders/checkin_prompt_dispatcher.py, communication/reminders/reminder_dispatcher.py, core/auto_cleanup.py, core/backup_manager.py, core/checkin_analytics.py, core/checkin_dynamic_manager.py, core/checkin_service.py, core/config.py, core/file_auditor.py, core/file_locking.py, core/file_operations.py, core/headless_service.py, core/logger.py, core/message_analytics.py, core/message_management.py, core/message_preview.py, core/pagination.py, core/response_tracking.py, core/schedule_document_defaults.py, core/schedule_runtime.py, core/schedule_utilities.py, core/schemas.py, core/service.py, core/service_requests.py, core/service_utilities.py, core/tags.py, core/ui_management.py, core/user_lookup.py, core/user_management.py, run_headless_service.py, scheduler/jobs.py, scheduler/maintenance.py, scheduler/manager.py, scheduler/task_reminders.py, tasks/task_data_handlers.py, tasks/task_data_manager.py, tasks/task_service.py, tasks/task_validation.py, ui/dialogs/account_creator_dialog.py, ui/dialogs/admin_panel.py, ui/dialogs/category_management_dialog.py, ui/dialogs/channel_management_dialog.py, ui/dialogs/checkin_management_dialog.py, ui/dialogs/dialog_helpers.py, ui/dialogs/message_editor_dialog.py, ui/dialogs/process_watcher_dialog.py, ui/dialogs/schedule_editor_dialog.py, ui/dialogs/task_completion_dialog.py, ui/dialogs/task_crud_dialog.py, ui/dialogs/task_edit_dialog.py, ui/dialogs/task_management_dialog.py, ui/dialogs/user_analytics_dialog.py, ui/dialogs/user_profile_dialog.py, ui/generate_ui_files.py, ui/period_row_management.py, ui/ui_app_qt.py, ui/widgets/category_selection_widget.py, ui/widgets/channel_selection_widget.py, ui/widgets/checkin_settings_widget.py, ui/widgets/dynamic_list_container.py, ui/widgets/dynamic_list_field.py, ui/widgets/period_row_widget.py, ui/widgets/tag_widget.py, ui/widgets/task_settings_widget.py, ui/widgets/user_profile_settings_widget.py, user/context_manager.py, user/profile_service.py, user/user_context.py, user/user_preferences.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Centralized error handling and recovery
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/file_auditor.py`
- **Purpose**: Core system module for file_auditor
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `__future__ (annotations)`
    - `contextlib`
    - `os`
    - `traceback`
- **Used by**:
  - `core/file_operations.py`
  - `core/service.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger
- Removed: core/file_operations.py, core/service.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/file_locking.py`
- **Purpose**: Core system module for file_locking
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `contextlib (contextmanager, suppress)`
    - `fcntl`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
    - `tempfile`
    - `time`
- **Used by**:
  - `core/backup_manager.py`
  - `core/user_lookup.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger
- Removed: core/backup_manager.py, core/user_lookup.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/file_operations.py`
- **Purpose**: File operations and data management
- **Dependencies**:
  - **Local**:
    - `core.config (DEFAULT_MESSAGES_DIR_PATH, ensure_user_directory, get_user_data_dir, get_user_file_path)` (NEW)
    - `core.error_handling (FileOperationError, handle_errors, handle_file_error)` (NEW)
    - `core.file_auditor (record_created)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.time_utilities (now_timestamp_full)` (NEW)
    - `tasks.task_schemas (TASKS_V2_FILENAME)` (NEW)
  - **Standard Library**:
    - `importlib`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `re`
    - `shutil`
    - `time`
  - **Third-party**:
    - `storage.user_data_v2_base (SCHEMA_VERSION)`
- **Used by**:
  - `core/checkin_dynamic_manager.py`
  - `core/message_management.py`
  - `core/response_tracking.py`
  - `core/service.py`
  - `core/tags.py`
  - `ui/dialogs/account_creator_dialog.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.file_auditor, core.logger, core.time_utilities, tasks.task_schemas
- Removed: core/checkin_dynamic_manager.py, core/message_management.py, core/response_tracking.py, core/service.py, core/tags.py, storage.user_data_v2_base, ui/dialogs/account_creator_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: File operations and data management
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/headless_service.py`
- **Purpose**: Main service orchestration and management
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.launch_env (prepare_launch_environment, resolve_python_interpreter)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.service_utilities (get_flags_dir, get_service_processes, is_headless_service_running, is_ui_service_running)` (NEW)
  - **Standard Library**:
    - `argparse`
    - `os`
    - `pathlib (Path)`
    - `subprocess`
    - `sys`
    - `time`
  - **Third-party**:
    - `psutil`
    - `storage.service_flag_storage (write_service_flag_json)`
- **Used by**:
  - `run_headless_service.py`

**Dependency Changes**:
- Added: core.error_handling, core.launch_env, core.logger, core.service_utilities
- Removed: run_headless_service.py, storage.service_flag_storage

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/logger.py`
- **Purpose**: Logging system configuration and management
- **Dependencies**:
  - **Local**:
    - `core.config` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.time_utilities (format_time_tuple)` (NEW)
  - **Standard Library**:
    - `contextlib`
    - `glob`
    - `gzip`
    - `json`
    - `logging`
    - `logging.handlers (RotatingFileHandler, TimedRotatingFileHandler)`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
    - `time`
    - `typing (Any)`
- **Used by**:
  - `ai/cache_manager.py`
  - `ai/chatbot.py`
  - `ai/context_builder.py`
  - `ai/conversation_history.py`
  - `ai/conversational_context/sections.py`
  - `ai/fallback_responses/__init__.py`
  - `ai/lm_studio_manager.py`
  - `ai/prompt_manager.py`
  - `ai/response_generator.py`
  - `communication/command_handlers/account_handler.py`
  - `communication/command_handlers/analytics_handler.py`
  - `communication/command_handlers/base_handler.py`
  - `communication/command_handlers/checkin_handler.py`
  - `communication/command_handlers/interaction_handlers.py`
  - `communication/command_handlers/notebook_handler.py`
  - `communication/command_handlers/profile_handler.py`
  - `communication/command_handlers/schedule_handler.py`
  - `communication/command_handlers/task_handler.py`
  - `communication/communication_channels/base/base_channel.py`
  - `communication/communication_channels/base/command_registry.py`
  - `communication/communication_channels/base/message_formatter.py`
  - `communication/communication_channels/base/rich_formatter.py`
  - `communication/communication_channels/discord/account_flow_handler.py`
  - `communication/communication_channels/discord/api_client.py`
  - `communication/communication_channels/discord/bot.py`
  - `communication/communication_channels/discord/checkin_view.py`
  - `communication/communication_channels/discord/event_handler.py`
  - `communication/communication_channels/discord/task_reminder_view.py`
  - `communication/communication_channels/discord/webhook_handler.py`
  - `communication/communication_channels/discord/webhook_server.py`
  - `communication/communication_channels/discord/welcome_handler.py`
  - `communication/communication_channels/email/bot.py`
  - `communication/core/channel_monitor.py`
  - `communication/core/channel_orchestrator.py`
  - `communication/core/factory.py`
  - `communication/core/retry_manager.py`
  - `communication/core/welcome_manager.py`
  - `communication/delivery/message_dispatcher.py`
  - `communication/message_processing/command_parser.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `communication/message_processing/interaction_manager.py`
  - `communication/message_processing/message_router.py`
  - `communication/reminders/checkin_prompt_dispatcher.py`
  - `communication/reminders/reminder_dispatcher.py`
  - `core/auto_cleanup.py`
  - `core/backup_manager.py`
  - `core/checkin_analytics.py`
  - `core/checkin_dynamic_manager.py`
  - `core/file_auditor.py`
  - `core/file_locking.py`
  - `core/file_operations.py`
  - `core/headless_service.py`
  - `core/message_analytics.py`
  - `core/message_management.py`
  - `core/response_tracking.py`
  - `core/schedule_document_defaults.py`
  - `core/schedule_runtime.py`
  - `core/schedule_utilities.py`
  - `core/schemas.py`
  - `core/service.py`
  - `core/service_requests.py`
  - `core/service_utilities.py`
  - `core/tags.py`
  - `core/user_lookup.py`
  - `core/user_management.py`
  - `run_headless_service.py`
  - `scheduler/jobs.py`
  - `scheduler/maintenance.py`
  - `scheduler/manager.py`
  - `scheduler/task_reminders.py`
  - `tasks/task_data_handlers.py`
  - `tasks/task_data_manager.py`
  - `tasks/task_validation.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/admin_panel.py`
  - `ui/dialogs/category_management_dialog.py`
  - `ui/dialogs/channel_management_dialog.py`
  - `ui/dialogs/checkin_management_dialog.py`
  - `ui/dialogs/message_editor_dialog.py`
  - `ui/dialogs/process_watcher_dialog.py`
  - `ui/dialogs/schedule_editor_dialog.py`
  - `ui/dialogs/task_completion_dialog.py`
  - `ui/dialogs/task_crud_dialog.py`
  - `ui/dialogs/task_edit_dialog.py`
  - `ui/dialogs/task_management_dialog.py`
  - `ui/dialogs/user_analytics_dialog.py`
  - `ui/dialogs/user_profile_dialog.py`
  - `ui/period_row_management.py`
  - `ui/ui_app_qt.py`
  - `ui/widgets/category_selection_widget.py`
  - `ui/widgets/channel_selection_widget.py`
  - `ui/widgets/checkin_settings_widget.py`
  - `ui/widgets/dynamic_list_container.py`
  - `ui/widgets/dynamic_list_field.py`
  - `ui/widgets/period_row_widget.py`
  - `ui/widgets/tag_widget.py`
  - `ui/widgets/task_settings_widget.py`
  - `ui/widgets/user_profile_settings_widget.py`
  - `user/context_manager.py`
  - `user/user_context.py`
  - `user/user_preferences.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.time_utilities
- Removed: ai/cache_manager.py, ai/chatbot.py, ai/context_builder.py, ai/conversation_history.py, ai/fallback_responses/__init__.py, ai/lm_studio_manager.py, ai/prompt_manager.py, ai/response_generator.py, communication/command_handlers/account_handler.py, communication/command_handlers/analytics_handler.py, communication/command_handlers/base_handler.py, communication/command_handlers/checkin_handler.py, communication/command_handlers/interaction_handlers.py, communication/command_handlers/notebook_handler.py, communication/command_handlers/profile_handler.py, communication/command_handlers/schedule_handler.py, communication/command_handlers/task_handler.py, communication/communication_channels/base/base_channel.py, communication/communication_channels/base/command_registry.py, communication/communication_channels/base/message_formatter.py, communication/communication_channels/base/rich_formatter.py, communication/communication_channels/discord/account_flow_handler.py, communication/communication_channels/discord/api_client.py, communication/communication_channels/discord/bot.py, communication/communication_channels/discord/checkin_view.py, communication/communication_channels/discord/event_handler.py, communication/communication_channels/discord/task_reminder_view.py, communication/communication_channels/discord/webhook_handler.py, communication/communication_channels/discord/webhook_server.py, communication/communication_channels/discord/welcome_handler.py, communication/communication_channels/email/bot.py, communication/core/channel_monitor.py, communication/core/channel_orchestrator.py, communication/core/factory.py, communication/core/retry_manager.py, communication/core/welcome_manager.py, communication/delivery/message_dispatcher.py, communication/message_processing/command_parser.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/interaction_manager.py, communication/message_processing/message_router.py, communication/reminders/checkin_prompt_dispatcher.py, communication/reminders/reminder_dispatcher.py, core/auto_cleanup.py, core/backup_manager.py, core/checkin_analytics.py, core/checkin_dynamic_manager.py, core/file_auditor.py, core/file_locking.py, core/file_operations.py, core/headless_service.py, core/message_analytics.py, core/message_management.py, core/response_tracking.py, core/schedule_document_defaults.py, core/schedule_runtime.py, core/schedule_utilities.py, core/schemas.py, core/service.py, core/service_requests.py, core/service_utilities.py, core/tags.py, core/user_lookup.py, core/user_management.py, logging.handlers, run_headless_service.py, scheduler/jobs.py, scheduler/maintenance.py, scheduler/manager.py, scheduler/task_reminders.py, tasks/task_data_handlers.py, tasks/task_data_manager.py, tasks/task_validation.py, ui/dialogs/account_creator_dialog.py, ui/dialogs/admin_panel.py, ui/dialogs/category_management_dialog.py, ui/dialogs/channel_management_dialog.py, ui/dialogs/checkin_management_dialog.py, ui/dialogs/message_editor_dialog.py, ui/dialogs/process_watcher_dialog.py, ui/dialogs/schedule_editor_dialog.py, ui/dialogs/task_completion_dialog.py, ui/dialogs/task_crud_dialog.py, ui/dialogs/task_edit_dialog.py, ui/dialogs/task_management_dialog.py, ui/dialogs/user_analytics_dialog.py, ui/dialogs/user_profile_dialog.py, ui/period_row_management.py, ui/ui_app_qt.py, ui/widgets/category_selection_widget.py, ui/widgets/channel_selection_widget.py, ui/widgets/checkin_settings_widget.py, ui/widgets/dynamic_list_container.py, ui/widgets/dynamic_list_field.py, ui/widgets/period_row_widget.py, ui/widgets/tag_widget.py, ui/widgets/task_settings_widget.py, ui/widgets/user_profile_settings_widget.py, user/context_manager.py, user/user_context.py, user/user_preferences.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Logging system configuration and management
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/message_analytics.py`
- **Purpose**: Core system module for message_analytics
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.message_management (get_recent_messages)` (NEW)
  - **Standard Library**:
    - `collections (defaultdict)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.message_management

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/message_management.py`
- **Purpose**: Message management and storage
- **Dependencies**:
  - **Local**:
    - `core.config (DEFAULT_MESSAGES_DIR_PATH, get_user_data_dir)` (NEW)
    - `core.error_handling (ValidationError, handle_errors)` (NEW)
    - `core.file_operations (determine_file_path, load_json_data, save_json_data)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.time_utilities (now_datetime_utc, now_timestamp_filename, now_timestamp_full, parse_timestamp_full)` (NEW)
  - **Standard Library**:
    - `contextlib`
    - `datetime (datetime, timedelta, timezone)`
    - `importlib`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `typing (Any, cast)`
    - `uuid`
  - **Third-party**:
    - `storage.user_data_v2_base (SCHEMA_VERSION, generate_short_id)`
    - `storage.user_data_v2_envelopes (MessageTemplateV2Model)`
- **Used by**:
  - `ai/conversational_context/sections.py`
  - `communication/core/channel_orchestrator.py`
  - `communication/delivery/message_dispatcher.py`
  - `core/auto_cleanup.py`
  - `core/message_analytics.py`
  - `core/message_preview.py`
  - `ui/dialogs/message_editor_dialog.py`
  - `user/context_manager.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.file_operations, core.logger, core.time_utilities
- Removed: ai/response_generator.py, communication/core/channel_orchestrator.py, communication/delivery/message_dispatcher.py, core/auto_cleanup.py, core/message_analytics.py, core/message_preview.py, storage.user_data_v2_base, storage.user_data_v2_envelopes, ui/dialogs/message_editor_dialog.py, user/context_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Message management and storage
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/message_preview.py`
- **Purpose**: Core system module for message_preview
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.message_management (get_recent_messages, load_user_messages)` (NEW)
    - `core.schedule_runtime (get_current_day_names, get_current_time_periods_with_validation)` (NEW)
  - **Standard Library**:
    - `__future__ (annotations)`
    - `random`
    - `typing (Any)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling, core.message_management, core.schedule_runtime

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/network_probe.py`
- **Purpose**: Core system module for network_probe
- **Dependencies**:
  - **Standard Library**:
    - `logging`
    - `socket`
    - `time`
- **Used by**:
  - `communication/core/channel_orchestrator.py`
  - `core/error_handling.py`

**Dependency Changes**:
- Removed: communication/core/channel_orchestrator.py, core/error_handling.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/pagination.py`
- **Purpose**: Core system module for pagination
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
  - **Standard Library**:
    - `collections.abc (Sequence)`
    - `dataclasses (dataclass)`
    - `typing (Generic, TypeVar)`
- **Used by**:
  - `communication/command_handlers/notebook_handler.py`

**Dependency Changes**:
- Added: core.error_handling
- Removed: collections.abc, communication/command_handlers/notebook_handler.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/response_tracking.py`
- **Purpose**: Tracks user responses and interactions
- **Dependencies**:
  - **Local**:
    - `core (get_user_data)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.file_operations (get_user_file_path, load_json_data, save_json_data)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.time_utilities (now_datetime_full, now_timestamp_full, parse_timestamp_full)` (NEW)
  - **Standard Library**:
    - `datetime (timedelta)`
    - `typing (Any)`
    - `uuid`
  - **Third-party**:
    - `storage.user_data_v2_base (SCHEMA_VERSION)`
- **Used by**:
  - `ai/chatbot.py`
  - `ai/context_builder.py`
  - `ai/conversational_context/sections.py`
  - `ai/fallback_responses/data_access.py`
  - `communication/command_handlers/analytics_handler.py`
  - `communication/command_handlers/checkin_handler.py`
  - `communication/command_handlers/interaction_handlers.py`
  - `communication/command_handlers/profile_handler.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `communication/message_processing/interaction_manager.py`
  - `core/checkin_analytics.py`
  - `core/checkin_service.py`
  - `ui/dialogs/user_analytics_dialog.py`
  - `user/context_manager.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.file_operations, core.logger, core.time_utilities
- Removed: ai/chatbot.py, ai/context_builder.py, ai/fallback_responses/data_access.py, ai/response_generator.py, communication/command_handlers/analytics_handler.py, communication/command_handlers/checkin_handler.py, communication/command_handlers/interaction_handlers.py, communication/command_handlers/profile_handler.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/interaction_manager.py, core/checkin_analytics.py, core/checkin_service.py, storage.user_data_v2_base, ui/dialogs/user_analytics_dialog.py, user/context_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Tracks user responses and interactions
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/schedule_document_defaults.py`
- **Purpose**: Core system module for schedule_document_defaults
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `typing (Any)`
  - **Third-party**:
    - `storage.user_data_read (get_user_data)`
    - `storage.user_data_registry (_get_user_data__load_schedules, _save_user_data__save_schedules)`
- **Used by**:
  - `core/user_management.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger
- Removed: core/user_management.py, storage.user_data_read, storage.user_data_registry

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/schedule_runtime.py`
- **Purpose**: Schedule management and time period handling
- **Dependencies**:
  - **Local**:
    - `core (get_user_data, update_user_schedules)` (NEW)
    - `core.error_handling (ValidationError, handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.service_requests (create_reschedule_request)` (NEW)
    - `core.time_utilities (TIME_ONLY_MINUTE, format_timestamp, now_datetime_full, parse_time_only_minute)` (NEW)
    - `user.user_context (UserContext)`
  - **Standard Library**:
    - `calendar`
    - `contextlib`
    - `datetime`
    - `re`
    - `time`
    - `typing (Any)`
- **Used by**:
  - `communication/command_handlers/schedule_handler.py`
  - `communication/core/channel_orchestrator.py`
  - `communication/delivery/message_dispatcher.py`
  - `core/message_preview.py`
  - `scheduler/manager.py`
  - `scheduler/task_reminders.py`
  - `ui/dialogs/category_management_dialog.py`
  - `ui/dialogs/checkin_management_dialog.py`
  - `ui/dialogs/schedule_editor_dialog.py`
  - `ui/dialogs/task_management_dialog.py`
  - `ui/period_row_management.py`
  - `ui/widgets/period_row_widget.py`
  - `user/user_preferences.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger, core.service_requests, core.time_utilities
- Removed: communication/command_handlers/schedule_handler.py, communication/core/channel_orchestrator.py, communication/delivery/message_dispatcher.py, core/message_preview.py, scheduler/manager.py, scheduler/task_reminders.py, ui/dialogs/category_management_dialog.py, ui/dialogs/checkin_management_dialog.py, ui/dialogs/schedule_editor_dialog.py, ui/dialogs/task_management_dialog.py, ui/period_row_management.py, ui/widgets/period_row_widget.py, user/user_preferences.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Schedule management and time period handling
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/schedule_utilities.py`
- **Purpose**: Core system module for schedule_utilities
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.time_format_constants (DATE_DISPLAY_WEEKDAY)` (NEW)
    - `core.time_utilities (TIME_ONLY_MINUTE, format_timestamp, now_datetime_full, parse_time_only_minute)` (NEW)
  - **Standard Library**:
    - `datetime`
- **Used by**:
  - `user/context_manager.py`
  - `user/user_context.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.time_format_constants, core.time_utilities
- Removed: user/context_manager.py, user/user_context.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/schemas.py`
- **Purpose**: Core system module for schemas
- **Dependencies**:
  - **Local**:
    - `core.error_handling (ValidationError, handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `__future__ (annotations)`
    - `importlib`
    - `re`
    - `typing (Any, Literal)`
  - **Third-party**:
    - `pydantic (BaseModel, ConfigDict, Field, RootModel, field_validator, model_validator)`
    - `pytz`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling, core.logger

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/service.py`
- **Purpose**: Main service orchestration and management
- **Dependencies**:
  - **Local**:
    - `communication.core.channel_orchestrator (CommunicationManager)`
    - `core.auto_cleanup (auto_cleanup_if_needed, cleanup_data_directory, cleanup_tests_data_directory)` (NEW)
    - `core.config` (NEW)
    - `core.error_handling (CommunicationError, ConfigurationError, FileOperationError, SchedulerError, handle_errors)` (NEW)
    - `core.file_auditor (start_auditor, stop_auditor)` (NEW)
    - `core.file_operations (verify_file_access)` (NEW)
    - `core.logger (force_restart_logging, get_component_logger, setup_logging)` (NEW)
    - `core.service_requests` (NEW)
    - `core.service_utilities (get_flags_dir)` (NEW)
    - `core.time_utilities (now_datetime_full, parse_timestamp_full)` (NEW)
    - `core.user_management (get_all_user_ids)` (NEW)
    - `scheduler.manager (SchedulerManager, set_scheduler_delivery_factory)`
  - **Standard Library**:
    - `atexit`
    - `contextlib`
    - `logging`
    - `os`
    - `pathlib (Path)`
    - `re`
    - `signal`
    - `time`
    - `typing (Any)`
  - **Third-party**:
    - `psutil`
    - `storage.user_data_read (get_user_data)`
- **Used by**:
  - `tasks/task_data_manager.py`
  - `ui/dialogs/account_creator_dialog.py`

**Dependency Changes**:
- Added: core.auto_cleanup, core.config, core.error_handling, core.file_auditor, core.file_operations, core.logger, core.service_requests, core.service_utilities, core.time_utilities, core.user_management
- Removed: storage.user_data_read, tasks/task_data_manager.py, ui/dialogs/account_creator_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Main service orchestration and management
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/service_requests.py`
- **Purpose**: Main service orchestration and management
- **Dependencies**:
  - **Local**:
    - `communication.message_processing.conversation_flow_manager (conversation_manager)` (NEW)
    - `core (get_user_data)` (NEW)
    - `core.delivery (ServiceRequestDeliveryPort)` (NEW)
    - `core.error_handling (FileOperationError, ValidationError, handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.service_utilities (get_flags_dir, is_service_running)` (NEW)
    - `core.time_utilities (now_timestamp_filename, now_timestamp_full)` (NEW)
  - **Standard Library**:
    - `__future__ (annotations)`
    - `collections.abc (Callable)`
    - `contextlib`
    - `dataclasses (dataclass)`
    - `os`
    - `pathlib (Path)`
    - `time`
    - `typing (Any)`
  - **Third-party**:
    - `storage.service_flag_storage (read_service_flag_json, write_service_flag_json)`
- **Used by**:
  - `core/schedule_runtime.py`
  - `core/service.py`

**Dependency Changes**:
- Added: communication.message_processing.conversation_flow_manager, core, core.delivery, core.error_handling, core.logger, core.service_utilities, core.time_utilities
- Removed: collections.abc, core/schedule_runtime.py, core/service.py, storage.service_flag_storage

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/service_utilities.py`
- **Purpose**: Main service orchestration and management
- **Dependencies**:
  - **Local**:
    - `core.config (SCHEDULER_INTERVAL)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `contextlib`
    - `os`
    - `pathlib (Path)`
    - `time`
  - **Third-party**:
    - `psutil`
- **Used by**:
  - `core/headless_service.py`
  - `core/service.py`
  - `core/service_requests.py`
  - `ui/dialogs/process_watcher_dialog.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger
- Removed: core/headless_service.py, core/service.py, core/service_requests.py, ui/dialogs/process_watcher_dialog.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Utility functions for service operations
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/tags.py`
- **Purpose**: Core system module for tags
- **Dependencies**:
  - **Local**:
    - `core.config (get_user_data_dir, get_user_file_path)` (NEW)
    - `core.error_handling (ValidationError, handle_errors)` (NEW)
    - `core.file_operations (load_json_data, save_json_data)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.time_utilities (now_timestamp_full)` (NEW)
  - **Standard Library**:
    - `json`
    - `pathlib (Path)`
    - `re`
    - `typing (Any)`
- **Used by**:
  - `communication/command_handlers/notebook_handler.py`
  - `communication/message_processing/command_parser.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `tasks/task_data_manager.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.file_operations, core.logger, core.time_utilities
- Removed: communication/command_handlers/notebook_handler.py, communication/message_processing/command_parser.py, communication/message_processing/conversation_flow_manager.py, tasks/task_data_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/time_format_constants.py`
- **Purpose**: Core system module for time_format_constants
- **Dependencies**: None (no imports)
- **Used by**:
  - `communication/message_processing/interaction_manager.py`
  - `core/schedule_utilities.py`
  - `core/time_utilities.py`

**Dependency Changes**:
- Removed: communication/message_processing/interaction_manager.py, core/schedule_utilities.py, core/time_utilities.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/time_utilities.py`
- **Purpose**: Core system module for time_utilities
- **Dependencies**:
  - **Local**:
    - `core.time_format_constants (DATE_ONLY, EXTERNAL_TIMESTAMP_VARIANTS, TIMESTAMP_FILENAME, TIMESTAMP_FULL, TIMESTAMP_MINUTE, TIMESTAMP_WITH_MICROSECONDS, TIME_COMPACT_HOUR_MINUTE, TIME_ONLY_MINUTE)` (NEW)
  - **Standard Library**:
    - `__future__ (annotations)`
    - `collections.abc (Callable, Iterable)`
    - `datetime (datetime, timezone)`
    - `functools`
    - `logging`
    - `time`
    - `typing (Literal, TypeVar, cast)`
  - **Third-party**:
    - `pytz`
- **Used by**:
  - `ai/context_builder.py`
  - `ai/conversation_history.py`
  - `ai/conversational_context/sections.py`
  - `communication/command_handlers/analytics_handler.py`
  - `communication/command_handlers/notebook_handler.py`
  - `communication/command_handlers/task_handler.py`
  - `communication/core/channel_monitor.py`
  - `communication/core/retry_manager.py`
  - `communication/core/welcome_manager.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `communication/message_processing/interaction_manager.py`
  - `core/auto_cleanup.py`
  - `core/backup_manager.py`
  - `core/checkin_analytics.py`
  - `core/checkin_service.py`
  - `core/error_handling.py`
  - `core/file_operations.py`
  - `core/logger.py`
  - `core/message_management.py`
  - `core/response_tracking.py`
  - `core/schedule_runtime.py`
  - `core/schedule_utilities.py`
  - `core/service.py`
  - `core/service_requests.py`
  - `core/tags.py`
  - `core/user_management.py`
  - `scheduler/maintenance.py`
  - `scheduler/manager.py`
  - `scheduler/task_reminders.py`
  - `tasks/task_data_handlers.py`
  - `tasks/task_data_manager.py`
  - `tasks/task_schemas.py`
  - `tasks/task_service.py`
  - `tasks/task_validation.py`
  - `ui/dialogs/message_editor_dialog.py`
  - `ui/dialogs/process_watcher_dialog.py`
  - `ui/dialogs/schedule_editor_dialog.py`
  - `ui/dialogs/user_profile_dialog.py`
  - `ui/generate_ui_files.py`
  - `ui/ui_app_qt.py`
  - `user/context_manager.py`

**Dependency Changes**:
- Added: core.time_format_constants
- Removed: ai/context_builder.py, ai/conversation_history.py, ai/response_generator.py, collections.abc, communication/command_handlers/analytics_handler.py, communication/command_handlers/notebook_handler.py, communication/command_handlers/task_handler.py, communication/core/channel_monitor.py, communication/core/retry_manager.py, communication/core/welcome_manager.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/interaction_manager.py, core/auto_cleanup.py, core/backup_manager.py, core/checkin_analytics.py, core/checkin_service.py, core/error_handling.py, core/file_operations.py, core/logger.py, core/message_management.py, core/response_tracking.py, core/schedule_runtime.py, core/schedule_utilities.py, core/service.py, core/service_requests.py, core/tags.py, core/user_management.py, scheduler/maintenance.py, scheduler/manager.py, scheduler/task_reminders.py, tasks/task_data_handlers.py, tasks/task_data_manager.py, tasks/task_schemas.py, tasks/task_service.py, tasks/task_validation.py, ui/dialogs/message_editor_dialog.py, ui/dialogs/process_watcher_dialog.py, ui/dialogs/schedule_editor_dialog.py, ui/dialogs/user_profile_dialog.py, ui/generate_ui_files.py, ui/ui_app_qt.py, user/context_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/ui_management.py`
- **Purpose**: UI management and widget utilities
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
  - **Standard Library**:
    - `collections.abc (Callable)`
    - `re`
    - `typing (Any)`
- **Used by**:
  - `ui/dialogs/schedule_editor_dialog.py`
  - `ui/period_row_management.py`
  - `ui/widgets/checkin_settings_widget.py`
  - `ui/widgets/task_settings_widget.py`

**Dependency Changes**:
- Added: core.error_handling
- Removed: collections.abc, ui/dialogs/schedule_editor_dialog.py, ui/period_row_management.py, ui/widgets/checkin_settings_widget.py, ui/widgets/task_settings_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: UI management and widget utilities
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/user_lookup.py`
- **Purpose**: Centralized user data access and management
- **Dependencies**:
  - **Local**:
    - `core.config (BASE_DATA_DIR)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.file_locking (safe_json_read)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.user_management (get_all_user_ids)` (NEW)
  - **Standard Library**:
    - `os`
    - `pathlib (Path)`
  - **Third-party**:
    - `storage.user_data_read (get_user_data)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config, core.error_handling, core.file_locking, core.logger, core.user_management
- Removed: storage.user_data_read

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/user_management.py`
- **Purpose**: Centralized user data access and management
- **Dependencies**:
  - **Local**:
    - `core.config (_normalize_path, core.config)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.schedule_document_defaults (ensure_category_has_default_schedule)` (NEW)
    - `core.time_utilities (now_timestamp_full)` (NEW)
  - **Standard Library**:
    - `importlib`
    - `os`
    - `pathlib (Path)`
    - `typing (Any)`
    - `uuid`
  - **Third-party**:
    - `storage.user_data_read (get_user_data)`
    - `storage.user_data_write (save_user_data)`
- **Used by**:
  - `core/service.py`
  - `core/user_lookup.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger, core.schedule_document_defaults, core.time_utilities
- Removed: core/service.py, core/user_lookup.py, storage.user_data_read, storage.user_data_write

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

### `root/` - Project root files

#### `run_headless_service.py`
- **Purpose**: Main entry point for the application
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.headless_service (HeadlessServiceManager)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
  - **Standard Library**:
    - `argparse`
    - `sys`
    - `typing (Any)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling, core.headless_service, core.logger

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

### `scheduler/`

#### `scheduler/__init__.py`
- **Purpose**: Module for scheduler/__init__.py
- **Dependencies**:
  - **Local**:
    - `scheduler.manager (SchedulerManager, clear_all_accumulated_jobs_standalone, process_category_schedule, process_user_schedules, run_category_scheduler_standalone, run_full_scheduler_standalone, run_user_scheduler_standalone, schedule_all_task_reminders, set_scheduler_delivery_factory)` (NEW)
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: scheduler.manager

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scheduler/jobs.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**:
  - **Local**:
    - `core.auto_cleanup (cleanup_data_directory, cleanup_tests_data_directory)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Third-party**:
    - `schedule`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.auto_cleanup, core.error_handling, core.logger

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scheduler/maintenance.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**:
  - **Local**:
    - `core (get_all_user_ids)` (NEW)
    - `core.backup_manager (backup_manager)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (cleanup_old_archives, compress_old_logs, get_component_logger)` (NEW)
    - `core.time_utilities (now_datetime_full, now_timestamp_filename, parse_timestamp_full)` (NEW)
  - **Standard Library**:
    - `subprocess`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core, core.backup_manager, core.error_handling, core.logger, core.time_utilities

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scheduler/manager.py`
- **Purpose**: Module for scheduler/manager.py
- **Dependencies**:
  - **Local**:
    - `core (get_all_user_ids, get_user_data)` (NEW)
    - `core.config (BASE_DATA_DIR, get_user_data_dir)` (NEW)
    - `core.delivery (SchedulerDeliveryPort)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, suppress_noisy_logging)` (NEW)
    - `core.schedule_runtime (get_schedule_time_periods)` (NEW)
    - `core.time_utilities (DATE_ONLY, TIMESTAMP_FULL, TIMESTAMP_MINUTE, TIME_ONLY_MINUTE, format_time_compact_hour_minute, format_timestamp, load_and_localize_datetime, now_datetime_full, parse_time_only_minute)` (NEW)
    - `scheduler (jobs, maintenance, task_reminders)` (NEW)
    - `tasks (are_tasks_enabled)` (NEW)
    - `user.user_context (UserContext)` (NEW)
  - **Standard Library**:
    - `calendar`
    - `collections.abc (Callable)`
    - `datetime (datetime, timedelta)`
    - `os`
    - `random`
    - `subprocess`
    - `threading`
    - `time`
    - `typing (Any)`
  - **Third-party**:
    - `pytz`
    - `schedule`
- **Used by**:
  - `core/service.py`
  - `scheduler/__init__.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core, core.config, core.delivery, core.error_handling, core.logger, core.schedule_runtime, core.time_utilities, scheduler, tasks, user.user_context
- Removed: collections.abc, core/service.py, scheduler/__init__.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scheduler/task_reminders.py`
- **Purpose**: Module for scheduler/task_reminders.py
- **Dependencies**:
  - **Local**:
    - `core (get_all_user_ids)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.schedule_runtime (get_schedule_time_periods)` (NEW)
    - `core.time_utilities (TIME_ONLY_MINUTE, format_timestamp, now_datetime_full, parse_date_only, parse_time_only_minute, parse_timestamp_minute)` (NEW)
    - `tasks (are_tasks_enabled, get_task_by_id, load_active_tasks, update_task)` (NEW)
    - `tasks.task_data_handlers (runtime_task_due_date, runtime_task_is_completed)` (NEW)
  - **Standard Library**:
    - `__future__ (annotations)`
    - `datetime (datetime, timedelta)`
    - `random`
    - `time`
    - `typing (Any)`
  - **Third-party**:
    - `pytz`
    - `schedule`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core, core.error_handling, core.logger, core.schedule_runtime, core.time_utilities, tasks, tasks.task_data_handlers

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

### `tasks/` - Task management

#### `tasks/__init__.py`
- **Purpose**: Task management and scheduling
- **Dependencies**:
  - **Third-party**:
    - `task_data_handlers (ensure_task_directory, load_active_tasks, load_completed_tasks, save_active_tasks, save_completed_tasks)`
    - `task_data_manager (add_user_task_tag, are_tasks_enabled, cleanup_task_reminders, complete_task, create_task, delete_task, get_task_by_id, get_tasks_due_soon, get_user_task_stats, remove_user_task_tag, restore_task, schedule_task_reminders, setup_default_task_tags, update_task)`
    - `task_schemas (TaskManagementError)`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tasks/task_data_handlers.py`
- **Purpose**: Task management and scheduling
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.time_utilities (now_timestamp_full, parse_timestamp_full)` (NEW)
    - `tasks.task_schemas (TASKS_V2_FILENAME, TaskV2Model)`
  - **Standard Library**:
    - `typing (Any, cast)`
  - **Third-party**:
    - `storage.user_data_v2_base (SCHEMA_VERSION, generate_short_id)`
    - `storage.user_data_validation (is_valid_user_id)`
    - `storage.user_item_storage (ensure_user_subdir, get_user_subdir_path, load_user_json_file, save_user_json_file)`
- **Used by**:
  - `ai/conversational_context/sections.py`
  - `communication/command_handlers/task_handler.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `communication/message_processing/interaction_manager.py`
  - `communication/reminders/reminder_dispatcher.py`
  - `scheduler/task_reminders.py`
  - `tasks/task_data_manager.py`
  - `tasks/task_service.py`
  - `ui/dialogs/task_crud_dialog.py`
  - `ui/dialogs/task_edit_dialog.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.time_utilities
- Removed: ai/response_generator.py, communication/command_handlers/task_handler.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/interaction_manager.py, communication/reminders/reminder_dispatcher.py, scheduler/task_reminders.py, storage.user_data_v2_base, storage.user_data_validation, storage.user_item_storage, tasks/task_data_manager.py, tasks/task_service.py, ui/dialogs/task_crud_dialog.py, ui/dialogs/task_edit_dialog.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tasks/task_data_manager.py`
- **Purpose**: Task management and scheduling
- **Dependencies**:
  - **Local**:
    - `core (get_user_data)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.service (get_scheduler_manager)` (NEW)
    - `core.tags (add_user_tag, get_user_tags, remove_user_tag)` (NEW)
    - `core.time_utilities (DATE_ONLY, format_timestamp, now_datetime_full, now_timestamp_full, parse_date_only, parse_timestamp_full)` (NEW)
    - `tasks.task_data_handlers (load_active_tasks, load_completed_tasks, save_active_tasks, save_completed_tasks)`
    - `tasks.task_validation (is_valid_priority, is_valid_task_title, validate_update_field)`
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `typing (Any)`
    - `uuid`
  - **Third-party**:
    - `storage.user_data_v2_base (generate_short_id)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core, core.error_handling, core.logger, core.service, core.tags, core.time_utilities
- Removed: storage.user_data_v2_base

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tasks/task_schemas.py`
- **Purpose**: Task management and scheduling
- **Dependencies**:
  - **Local**:
    - `core.time_utilities (parse_date_only, parse_time_only_minute)` (NEW)
  - **Standard Library**:
    - `__future__ (annotations)`
    - `typing (Any, Literal)`
  - **Third-party**:
    - `pydantic (BaseModel, ConfigDict, Field, field_validator, model_validator)`
    - `storage.user_data_v2_base (BaseItemModel, SCHEMA_VERSION, v2_schema_validation_error, validate_optional_v2_timestamp)`
- **Used by**:
  - `communication/message_processing/conversation_flow_manager.py`
  - `core/file_operations.py`
  - `tasks/task_data_handlers.py`
  - `tasks/task_service.py`
  - `tasks/task_validation.py`

**Dependency Changes**:
- Added: core.time_utilities
- Removed: communication/message_processing/conversation_flow_manager.py, core/file_operations.py, storage.user_data_v2_base, tasks/task_data_handlers.py, tasks/task_service.py, tasks/task_validation.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tasks/task_service.py`
- **Purpose**: Task management and scheduling
- **Dependencies**:
  - **Local**:
    - `core (get_user_data)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.time_utilities (DATE_ONLY, format_timestamp, now_datetime_full, parse_date_only)` (NEW)
    - `tasks` (NEW)
    - `tasks.task_data_handlers (runtime_task_due_date)` (NEW)
    - `tasks.task_schemas (VALID_PRIORITIES)` (NEW)
  - **Standard Library**:
    - `__future__ (annotations)`
    - `calendar`
    - `dataclasses (dataclass)`
    - `datetime (datetime, timedelta)`
    - `re`
    - `typing (Any)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core, core.error_handling, core.time_utilities, tasks, tasks.task_data_handlers, tasks.task_schemas

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tasks/task_validation.py`
- **Purpose**: Task management and scheduling
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.time_utilities (parse_date_only)` (NEW)
    - `tasks.task_schemas (ALLOWED_UPDATE_FIELDS, TaskCollectionV2Model, VALID_PRIORITIES)`
  - **Standard Library**:
    - `typing (Any)`
- **Used by**:
  - `tasks/task_data_manager.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.time_utilities
- Removed: tasks/task_data_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

### `ui/` - User interface components

#### `ui/__init__.py`
- **Purpose**: User interface component for __init__
- **Dependencies**:
  - **Third-party**:
    - `dialogs.account_creator_dialog (AccountCreatorDialog, create_account_dialog)`
    - `dialogs.admin_panel (AdminPanelDialog)`
    - `dialogs.category_management_dialog (CategoryManagementDialog)`
    - `dialogs.channel_management_dialog (ChannelManagementDialog)`
    - `dialogs.checkin_management_dialog (CheckinManagementDialog)`
    - `dialogs.message_editor_dialog (MessageEditDialog, MessageEditorDialog, open_message_editor_dialog)`
    - `dialogs.process_watcher_dialog (ProcessWatcherDialog)`
    - `dialogs.schedule_editor_dialog (ScheduleEditorDialog, open_schedule_editor)`
    - `dialogs.task_completion_dialog (TaskCompletionDialog)`
    - `dialogs.task_crud_dialog (TaskCrudDialog)`
    - `dialogs.task_edit_dialog (TaskEditDialog)`
    - `dialogs.task_management_dialog (TaskManagementDialog)`
    - `dialogs.user_analytics_dialog (UserAnalyticsDialog, open_user_analytics_dialog)`
    - `dialogs.user_profile_dialog (UserProfileDialog, open_personalization_dialog)`
    - `generate_ui_files (generate_all_ui_files, generate_ui_file)`
    - `ui_app_qt (MHMManagerUI, ServiceManager, main)`
    - `widgets.category_selection_widget (CategorySelectionWidget)`
    - `widgets.channel_selection_widget (ChannelSelectionWidget)`
    - `widgets.checkin_settings_widget (CheckinSettingsWidget)`
    - `widgets.dynamic_list_container (DynamicListContainer)`
    - `widgets.dynamic_list_field (DynamicListField)`
    - `widgets.period_row_widget (PeriodRowWidget)`
    - `widgets.tag_widget (TagWidget)`
    - `widgets.task_settings_widget (TaskSettingsWidget)`
    - `widgets.user_profile_settings_widget (UserProfileSettingsWidget)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Removed: dialogs.account_creator_dialog, dialogs.admin_panel, dialogs.category_management_dialog, dialogs.channel_management_dialog, dialogs.checkin_management_dialog, dialogs.message_editor_dialog, dialogs.process_watcher_dialog, dialogs.schedule_editor_dialog, dialogs.task_completion_dialog, dialogs.task_crud_dialog, dialogs.task_edit_dialog, dialogs.task_management_dialog, dialogs.user_analytics_dialog, dialogs.user_profile_dialog, widgets.category_selection_widget, widgets.channel_selection_widget, widgets.checkin_settings_widget, widgets.dynamic_list_container, widgets.dynamic_list_field, widgets.period_row_widget, widgets.tag_widget, widgets.task_settings_widget, widgets.user_profile_settings_widget

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/__init__.py`
- **Purpose**: Dialog component for   init  
- **Dependencies**:
  - **Third-party**:
    - `account_creator_dialog (AccountCreatorDialog)`
    - `checkin_management_dialog (CheckinManagementDialog)`
    - `message_editor_dialog (MessageEditDialog, MessageEditorDialog)`
    - `schedule_editor_dialog (ScheduleEditorDialog)`
    - `task_management_dialog (TaskManagementDialog)`
    - `user_analytics_dialog (UserAnalyticsDialog)`
    - `user_profile_dialog (UserProfileDialog)`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/account_creator_dialog.py`
- **Purpose**: Dialog component for account creator dialog
- **Dependencies**:
  - **Local**:
    - `core (get_user_data, get_user_id_by_identifier)` (NEW)
    - `core.config (get_user_data_dir)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.file_operations (create_user_files)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.service (get_scheduler_manager)` (NEW)
    - `tasks (add_user_task_tag, setup_default_task_tags)` (NEW)
    - `ui.dialogs.dialog_helpers (handle_dialog_escape_enter_keys)`
    - `ui.dialogs.user_profile_dialog (open_personalization_dialog)`
    - `ui.generated.account_creator_dialog_pyqt (Ui_Dialog_create_account)`
    - `ui.widgets.category_selection_widget (CategorySelectionWidget)`
    - `ui.widgets.channel_selection_widget (ChannelSelectionWidget)`
    - `ui.widgets.checkin_settings_widget (CheckinSettingsWidget)`
    - `ui.widgets.task_settings_widget (TaskSettingsWidget)`
  - **Standard Library**:
    - `contextlib`
    - `pathlib (Path)`
    - `time`
    - `typing (Any)`
    - `uuid`
    - `warnings`
  - **Third-party**:
    - `PySide6.QtCore (Qt, Signal)`
    - `PySide6.QtWidgets (QDialog, QDialogButtonBox, QMessageBox, QSizePolicy)`
    - `storage.user_data_operations (update_user_index)`
    - `storage.user_data_validation (is_valid_discord_id, is_valid_email, is_valid_phone, validate_schedule_periods)`
- **Used by**:
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core, core.config, core.error_handling, core.file_operations, core.logger, core.service, tasks
- Removed: PySide6.QtCore, PySide6.QtWidgets, storage.user_data_operations, storage.user_data_validation, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/admin_panel.py`
- **Purpose**: Dialog component for admin panel
- **Dependencies**:
  - **Local**:
    - `core.error_handling (DataError, handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Third-party**:
    - `PySide6.QtCore (Qt)`
    - `PySide6.QtWidgets (QDialog, QLabel, QVBoxLayout, QWidget)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling, core.logger
- Removed: PySide6.QtCore, PySide6.QtWidgets

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/category_management_dialog.py`
- **Purpose**: Dialog component for category management dialog
- **Dependencies**:
  - **Local**:
    - `core (get_user_data, update_user_account, update_user_preferences)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.schedule_runtime (clear_schedule_periods_cache)` (NEW)
    - `ui.generated.category_management_dialog_pyqt (Ui_Dialog_category_management)`
    - `ui.widgets.category_selection_widget (CategorySelectionWidget)`
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QDialog, QMessageBox)`
- **Used by**:
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger, core.schedule_runtime
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/channel_management_dialog.py`
- **Purpose**: Dialog component for channel management dialog
- **Dependencies**:
  - **Local**:
    - `core (get_user_data, update_channel_preferences, update_user_account)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `ui.generated.channel_management_dialog_pyqt (Ui_Dialog)`
    - `ui.widgets.channel_selection_widget (ChannelSelectionWidget)`
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QDialog, QMessageBox)`
    - `storage.user_data_validation (is_valid_email)`
- **Used by**:
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger
- Removed: PySide6.QtCore, PySide6.QtWidgets, storage.user_data_validation, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/checkin_management_dialog.py`
- **Purpose**: Dialog component for checkin management dialog
- **Dependencies**:
  - **Local**:
    - `core (get_user_data, update_user_account, update_user_preferences)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.schedule_runtime (clear_schedule_periods_cache, set_schedule_periods)` (NEW)
    - `ui.generated.checkin_management_dialog_pyqt (Ui_Dialog_checkin_management)`
    - `ui.widgets.checkin_settings_widget (CheckinSettingsWidget)`
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QDialog, QMessageBox, QWidget)`
    - `storage.user_data_validation (validate_schedule_periods)`
- **Used by**:
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger, core.schedule_runtime
- Removed: PySide6.QtCore, PySide6.QtWidgets, storage.user_data_validation, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/dialog_helpers.py`
- **Purpose**: Dialog component for dialog helpers
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
  - **Standard Library**:
    - `collections.abc (Callable)`
    - `typing (Any)`
  - **Third-party**:
    - `PySide6.QtCore (Qt)`
    - `PySide6.QtGui (QKeyEvent)`
    - `PySide6.QtWidgets (QMessageBox)`
- **Used by**:
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/user_profile_dialog.py`

**Dependency Changes**:
- Added: core.error_handling
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, collections.abc, ui/dialogs/account_creator_dialog.py, ui/dialogs/user_profile_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/message_editor_dialog.py`
- **Purpose**: Dialog component for message editor dialog
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.message_management (add_message, delete_message, edit_message, load_user_messages)` (NEW)
    - `core.time_utilities (now_timestamp_full)` (NEW)
    - `ui.generated.message_editor_dialog_pyqt (Ui_Dialog_message_editor)`
  - **Standard Library**:
    - `uuid`
  - **Third-party**:
    - `PySide6.QtWidgets (QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget)`
- **Used by**:
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.message_management, core.time_utilities
- Removed: PySide6.QtWidgets, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/process_watcher_dialog.py`
- **Purpose**: Dialog component for process watcher dialog
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.service_utilities (get_service_processes)` (NEW)
    - `core.time_utilities (TIMESTAMP_FULL, format_timestamp)` (NEW)
  - **Standard Library**:
    - `datetime`
  - **Third-party**:
    - `PySide6.QtCore (QTimer, Qt)`
    - `PySide6.QtGui (QFont)`
    - `PySide6.QtWidgets (QDialog, QHBoxLayout, QHeaderView, QLabel, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget)`
    - `psutil`
- **Used by**:
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.service_utilities, core.time_utilities
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/schedule_editor_dialog.py`
- **Purpose**: Dialog component for schedule editor dialog
- **Dependencies**:
  - **Local**:
    - `core.config` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.schedule_runtime (clear_schedule_periods_cache, set_schedule_periods)` (NEW)
    - `core.time_utilities (now_timestamp_filename, now_timestamp_full)` (NEW)
    - `core.ui_management (_number_from_regex, find_lowest_available_period_number)` (NEW)
    - `ui.generated.schedule_editor_dialog_pyqt (Ui_Dialog_edit_schedule)`
    - `ui.period_row_management (DEFAULT_PERIOD_DATA, add_period_row_to_layout, collect_period_data_from_widgets, load_period_widgets_for_category, remove_period_row_from_layout)` (NEW)
    - `ui.widgets.period_row_widget (PeriodRowWidget)`
  - **Standard Library**:
    - `collections.abc (Callable)`
    - `json`
    - `pathlib (Path)`
    - `typing (Any)`
  - **Third-party**:
    - `PySide6.QtWidgets (QDialog, QMessageBox)`
    - `storage.user_data_validation (_shared__title_case, validate_schedule_periods)`
- **Used by**:
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger, core.schedule_runtime, core.time_utilities, core.ui_management, ui.period_row_management
- Removed: PySide6.QtWidgets, collections.abc, storage.user_data_validation, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/task_completion_dialog.py`
- **Purpose**: Dialog component for task completion dialog
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `ui.generated.task_completion_dialog_pyqt (Ui_Dialog_task_completion)`
  - **Third-party**:
    - `PySide6.QtCore (QDate, QTime)`
    - `PySide6.QtWidgets (QButtonGroup, QDialog)`
- **Used by**:
  - `ui/dialogs/task_crud_dialog.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/dialogs/task_crud_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/task_crud_dialog.py`
- **Purpose**: Dialog component for task crud dialog
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `tasks (complete_task, delete_task, get_task_by_id, get_tasks_due_soon, get_user_task_stats, load_active_tasks, load_completed_tasks, restore_task)` (NEW)
    - `tasks.task_data_handlers (runtime_task_completed_at, runtime_task_due_date, runtime_task_due_time)` (NEW)
    - `ui.dialogs.task_completion_dialog (TaskCompletionDialog)`
    - `ui.dialogs.task_edit_dialog (TaskEditDialog)`
    - `ui.generated.task_crud_dialog_pyqt (Ui_Dialog_task_crud)`
  - **Third-party**:
    - `PySide6.QtCore (Qt)`
    - `PySide6.QtWidgets (QDialog, QHeaderView, QMessageBox, QTableWidgetItem)`
- **Used by**:
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, tasks, tasks.task_data_handlers
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/task_edit_dialog.py`
- **Purpose**: Dialog component for task edit dialog
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `tasks (create_task, update_task)` (NEW)
    - `tasks.task_data_handlers (runtime_task_due_date, runtime_task_due_time)` (NEW)
    - `ui.generated.task_edit_dialog_pyqt (Ui_Dialog_task_edit)`
    - `ui.widgets.tag_widget (TagWidget)`
  - **Third-party**:
    - `PySide6.QtCore (QDate, QTime)`
    - `PySide6.QtWidgets (QButtonGroup, QComboBox, QDateEdit, QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QWidget)`
- **Used by**:
  - `ui/dialogs/task_crud_dialog.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, tasks, tasks.task_data_handlers
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/dialogs/task_crud_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/task_management_dialog.py`
- **Purpose**: Dialog component for task management dialog
- **Dependencies**:
  - **Local**:
    - `core (get_user_data, update_user_account)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.schedule_runtime (clear_schedule_periods_cache, set_schedule_periods)` (NEW)
    - `tasks (setup_default_task_tags)` (NEW)
    - `ui.generated.task_management_dialog_pyqt (Ui_Dialog_task_management)`
    - `ui.widgets.task_settings_widget (TaskSettingsWidget)`
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QDialog, QMessageBox, QWidget)`
    - `storage.user_data_validation (validate_schedule_periods)`
- **Used by**:
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger, core.schedule_runtime, tasks
- Removed: PySide6.QtCore, PySide6.QtWidgets, storage.user_data_validation, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/user_analytics_dialog.py`
- **Purpose**: Dialog component for user analytics dialog
- **Dependencies**:
  - **Local**:
    - `core (get_user_data)` (NEW)
    - `core.checkin_analytics (CheckinAnalytics)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.response_tracking (get_checkins_by_days)` (NEW)
    - `ui.generated.user_analytics_dialog_pyqt (Ui_Dialog_user_analytics)`
  - **Standard Library**:
    - `os`
  - **Third-party**:
    - `PySide6.QtWidgets (QDialog)`
- **Used by**:
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core, core.checkin_analytics, core.error_handling, core.logger, core.response_tracking
- Removed: PySide6.QtWidgets, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/user_profile_dialog.py`
- **Purpose**: Dialog component for user profile dialog
- **Dependencies**:
  - **Local**:
    - `core (get_predefined_options, update_user_context)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.time_utilities (now_timestamp_full)` (NEW)
    - `ui.dialogs.dialog_helpers (handle_dialog_escape_enter_keys)`
    - `ui.generated.user_profile_management_dialog_pyqt (Ui_Dialog_user_profile)`
    - `ui.widgets.dynamic_list_container (DynamicListContainer)`
    - `ui.widgets.user_profile_settings_widget (UserProfileSettingsWidget)`
  - **Standard Library**:
    - `collections.abc (Callable)`
    - `re`
    - `typing (Any)`
  - **Third-party**:
    - `PySide6.QtCore (Qt, Signal)`
    - `PySide6.QtWidgets (QCheckBox, QComboBox, QDialog, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTextEdit, QVBoxLayout)`
    - `storage.user_data_validation (validate_personalization_data)`
- **Used by**:
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger, core.time_utilities
- Removed: PySide6.QtCore, PySide6.QtWidgets, collections.abc, storage.user_data_validation, ui/dialogs/account_creator_dialog.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generate_ui_files.py`
- **Purpose**: User interface component for generate_ui_files
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.time_utilities (now_timestamp_full)` (NEW)
  - **Standard Library**:
    - `os`
    - `pathlib (Path)`
    - `subprocess`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling, core.time_utilities

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/period_row_management.py`
- **Purpose**: User interface component for period_row_management
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.schedule_runtime (get_schedule_time_periods)` (NEW)
    - `core.ui_management (period_name_for_display, period_name_for_storage)` (NEW)
    - `ui.widgets.period_row_widget (PeriodRowWidget)` (NEW)
  - **Standard Library**:
    - `collections.abc (Callable)`
    - `typing (Any)`
- **Used by**:
  - `ui/dialogs/schedule_editor_dialog.py`
  - `ui/widgets/checkin_settings_widget.py`
  - `ui/widgets/task_settings_widget.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.schedule_runtime, core.ui_management, ui.widgets.period_row_widget
- Removed: collections.abc, ui/dialogs/schedule_editor_dialog.py, ui/widgets/checkin_settings_widget.py, ui/widgets/task_settings_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/ui_app_qt.py`
- **Purpose**: Main UI application (PyQt6)
- **Dependencies**:
  - **Local**:
    - `communication.core.channel_orchestrator (CommunicationManager)`
    - `core (get_all_user_ids, get_user_data, save_user_data)` (NEW)
    - `core.auto_cleanup (calculate_cache_size, find_pyc_files, find_pycache_dirs, get_cleanup_status, perform_cleanup, update_cleanup_timestamp)` (NEW)
    - `core.config (AI_TIMEOUT_SECONDS, BASE_DATA_DIR, DISCORD_BOT_TOKEN, EMAIL_IMAP_SERVER, EMAIL_SMTP_PASSWORD, EMAIL_SMTP_SERVER, EMAIL_SMTP_USERNAME, LM_STUDIO_BASE_URL, LOG_LEVEL, LOG_MAIN_FILE, SCHEDULER_INTERVAL, core.config, validate_all_configuration)` (NEW)
    - `core.error_handling (DataError, handle_errors)` (NEW)
    - `core.launch_env (prepare_launch_environment, resolve_python_interpreter)` (NEW)
    - `core.logger (get_component_logger, setup_logging, toggle_verbose_logging)` (NEW)
    - `core.service_utilities (get_flags_dir)` (NEW)
    - `core.time_utilities (now_datetime_full, now_timestamp_full, parse_timestamp_full)` (NEW)
    - `scheduler.manager (SchedulerManager, run_category_scheduler_standalone, run_full_scheduler_standalone, run_user_scheduler_standalone, set_scheduler_delivery_factory)`
    - `tasks (are_tasks_enabled, load_active_tasks)` (NEW)
    - `tasks.task_data_handlers (runtime_task_is_completed)` (NEW)
    - `ui.dialogs.account_creator_dialog (AccountCreatorDialog)`
    - `ui.dialogs.category_management_dialog (CategoryManagementDialog)`
    - `ui.dialogs.channel_management_dialog (ChannelManagementDialog)`
    - `ui.dialogs.checkin_management_dialog (CheckinManagementDialog)`
    - `ui.dialogs.message_editor_dialog (open_message_editor_dialog)`
    - `ui.dialogs.process_watcher_dialog (ProcessWatcherDialog)`
    - `ui.dialogs.schedule_editor_dialog (open_schedule_editor)`
    - `ui.dialogs.task_crud_dialog (TaskCrudDialog)`
    - `ui.dialogs.task_management_dialog (TaskManagementDialog)`
    - `ui.dialogs.user_analytics_dialog (open_user_analytics_dialog)`
    - `ui.dialogs.user_profile_dialog (UserProfileDialog)`
    - `ui.generated.admin_panel_pyqt (Ui_ui_app_mainwindow)`
    - `user.user_context (UserContext)`
  - **Standard Library**:
    - `contextlib`
    - `json`
    - `os`
    - `pathlib (Path, pathlib)`
    - `re`
    - `subprocess`
    - `sys`
    - `threading`
    - `time`
    - `webbrowser`
  - **Third-party**:
    - `PySide6.QtCore (QTimer)`
    - `PySide6.QtGui (QFont)`
    - `PySide6.QtWidgets (QApplication, QDialog, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QTabWidget, QTextEdit, QVBoxLayout, QWidget)`
    - `psutil`
    - `storage.user_data_operations (rebuild_user_index)`
    - `storage.user_data_validation (_shared__title_case)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core, core.auto_cleanup, core.config, core.error_handling, core.launch_env, core.logger, core.service_utilities, core.time_utilities, tasks, tasks.task_data_handlers
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, storage.user_data_operations, storage.user_data_validation

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/__init__.py`
- **Purpose**: UI widget component for   init  
- **Dependencies**:
  - **Third-party**:
    - `category_selection_widget (CategorySelectionWidget)`
    - `channel_selection_widget (ChannelSelectionWidget)`
    - `checkin_settings_widget (CheckinSettingsWidget)`
    - `period_row_widget (PeriodRowWidget)`
    - `tag_widget (TagWidget)`
    - `task_settings_widget (TaskSettingsWidget)`
    - `user_profile_settings_widget (UserProfileSettingsWidget)`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/category_selection_widget.py`
- **Purpose**: UI widget component for category selection widget
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `ui.generated.category_selection_widget_pyqt (Ui_Form_category_selection_widget)`
  - **Third-party**:
    - `PySide6.QtWidgets (QWidget)`
    - `storage.user_data_validation (_shared__title_case)`
- **Used by**:
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/category_management_dialog.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger
- Removed: PySide6.QtWidgets, storage.user_data_validation, ui/dialogs/account_creator_dialog.py, ui/dialogs/category_management_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/channel_selection_widget.py`
- **Purpose**: UI widget component for channel selection widget
- **Dependencies**:
  - **Local**:
    - `core (get_timezone_options)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `ui.generated.channel_selection_widget_pyqt (Ui_Form_channel_selection)`
  - **Third-party**:
    - `PySide6.QtWidgets (QWidget)`
- **Used by**:
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/channel_management_dialog.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger
- Removed: PySide6.QtWidgets, ui/dialogs/account_creator_dialog.py, ui/dialogs/channel_management_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/checkin_settings_widget.py`
- **Purpose**: UI widget component for checkin settings widget
- **Dependencies**:
  - **Local**:
    - `core (get_user_data)` (NEW)
    - `core.checkin_dynamic_manager (dynamic_checkin_manager)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.ui_management (_number_after_prefix, find_lowest_available_period_number)` (NEW)
    - `ui.generated.checkin_settings_widget_pyqt (Ui_Form_checkin_settings)`
    - `ui.period_row_management (DEFAULT_PERIOD_DATA, add_period_row_to_layout, collect_period_data_from_widgets, load_period_widgets_for_category, remove_period_row_from_layout)` (NEW)
  - **Standard Library**:
    - `re`
  - **Third-party**:
    - `PySide6.QtCore (Qt)`
    - `PySide6.QtWidgets (QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTextEdit, QVBoxLayout, QWidget)`
- **Used by**:
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/checkin_management_dialog.py`

**Dependency Changes**:
- Added: core, core.checkin_dynamic_manager, core.error_handling, core.logger, core.ui_management, ui.period_row_management
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/dialogs/account_creator_dialog.py, ui/dialogs/checkin_management_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/dynamic_list_container.py`
- **Purpose**: UI widget component for dynamic list container
- **Dependencies**:
  - **Local**:
    - `core (get_predefined_options)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `ui.widgets.dynamic_list_field (DynamicListField)`
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QGridLayout, QMessageBox, QVBoxLayout, QWidget)`
- **Used by**:
  - `ui/dialogs/user_profile_dialog.py`
  - `ui/widgets/user_profile_settings_widget.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/dialogs/user_profile_dialog.py, ui/widgets/user_profile_settings_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/dynamic_list_field.py`
- **Purpose**: UI widget component for dynamic list field
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `ui.generated.dynamic_list_field_template_pyqt (Ui_Form_dynamic_list_field_template)`
  - **Standard Library**:
    - `importlib`
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QSizePolicy, QWidget)`
- **Used by**:
  - `ui/widgets/dynamic_list_container.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/widgets/dynamic_list_container.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/period_row_widget.py`
- **Purpose**: UI widget component for period row widget
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.schedule_runtime (get_period_data__time_12h_display_to_24h, get_period_data__time_24h_to_12h_display)` (NEW)
    - `ui.generated.period_row_template_pyqt (Ui_Form_period_row_template)`
  - **Standard Library**:
    - `typing (Any)`
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QButtonGroup, QWidget)`
- **Used by**:
  - `ui/dialogs/schedule_editor_dialog.py`
  - `ui/period_row_management.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.schedule_runtime
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/dialogs/schedule_editor_dialog.py, ui/period_row_management.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/tag_widget.py`
- **Purpose**: UI widget component for tag widget
- **Dependencies**:
  - **Local**:
    - `core (get_user_data)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `tasks (add_user_task_tag, remove_user_task_tag)` (NEW)
    - `ui.generated.tag_widget_pyqt (Ui_Widget_tag)`
  - **Third-party**:
    - `PySide6.QtCore (Qt, Signal)`
    - `PySide6.QtWidgets (QInputDialog, QListWidgetItem, QMessageBox, QWidget)`
- **Used by**:
  - `ui/dialogs/task_edit_dialog.py`
  - `ui/widgets/task_settings_widget.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger, tasks
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/dialogs/task_edit_dialog.py, ui/widgets/task_settings_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/task_settings_widget.py`
- **Purpose**: UI widget component for task settings widget
- **Dependencies**:
  - **Local**:
    - `core (get_user_data, update_user_preferences)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.ui_management (_number_after_prefix, find_lowest_available_period_number)` (NEW)
    - `tasks (get_user_task_stats)` (NEW)
    - `ui.generated.task_settings_widget_pyqt (Ui_Form_task_settings)`
    - `ui.period_row_management (DEFAULT_PERIOD_DATA, add_period_row_to_layout, collect_period_data_from_widgets, load_period_widgets_for_category, remove_period_row_from_layout)` (NEW)
    - `ui.widgets.tag_widget (TagWidget)`
  - **Third-party**:
    - `PySide6.QtWidgets (QMessageBox, QWidget)`
- **Used by**:
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/task_management_dialog.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger, core.ui_management, tasks, ui.period_row_management
- Removed: PySide6.QtWidgets, ui/dialogs/account_creator_dialog.py, ui/dialogs/task_management_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/user_profile_settings_widget.py`
- **Purpose**: UI widget component for user profile settings widget
- **Dependencies**:
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `ui.generated.user_profile_settings_widget_pyqt (Ui_Form_user_profile_settings)`
    - `ui.widgets.dynamic_list_container (DynamicListContainer)`
  - **Standard Library**:
    - `typing (Any)`
  - **Third-party**:
    - `PySide6.QtCore (QDate, Qt)`
    - `PySide6.QtWidgets (QLabel, QLineEdit, QVBoxLayout, QWidget)`
- **Used by**:
  - `ui/dialogs/user_profile_dialog.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/dialogs/user_profile_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

### `user/` - User data and context

#### `user/__init__.py`
- **Purpose**: User data module for __init__
- **Dependencies**:
  - **Third-party**:
    - `context_manager (UserContextManager, user_context_manager)`
    - `user_context (UserContext)`
    - `user_preferences (UserPreferences)`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `user/context_manager.py`
- **Purpose**: User data module for context_manager
- **Dependencies**:
  - **Local**:
    - `core (get_user_data)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.message_management (get_recent_messages)` (NEW)
    - `core.response_tracking (get_recent_chat_interactions, get_recent_checkins)` (NEW)
    - `core.schedule_utilities (get_active_schedules)` (NEW)
    - `core.time_utilities (now_timestamp_full)` (NEW)
    - `user.user_context (UserContext)`
  - **Standard Library**:
    - `typing (Any)`
- **Used by**:
  - `ai/chatbot.py`
  - `ai/context_builder.py`
  - `ai/conversational_context/assembly.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger, core.message_management, core.response_tracking, core.schedule_utilities, core.time_utilities
- Removed: ai/chatbot.py, ai/context_builder.py, ai/response_generator.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `user/profile_service.py`
- **Purpose**: User data module for profile_service
- **Dependencies**:
  - **Local**:
    - `core (get_user_data, save_user_data)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
  - **Standard Library**:
    - `__future__ (annotations)`
    - `dataclasses (dataclass)`
    - `typing (Any)`
- **Used by**:
  - `communication/command_handlers/profile_handler.py`

**Dependency Changes**:
- Added: core, core.error_handling
- Removed: communication/command_handlers/profile_handler.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `user/user_context.py`
- **Purpose**: User context management
- **Dependencies**:
  - **Local**:
    - `core (get_user_data, save_user_data)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.schedule_utilities (get_active_schedules)` (NEW)
  - **Standard Library**:
    - `threading`
- **Used by**:
  - `core/schedule_runtime.py`
  - `scheduler/manager.py`
  - `ui/ui_app_qt.py`
  - `user/context_manager.py`

**Dependency Changes**:
- Added: core, core.error_handling, core.logger, core.schedule_utilities
- Removed: core/schedule_runtime.py, scheduler/manager.py, ui/ui_app_qt.py, user/context_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `user/user_preferences.py`
- **Purpose**: User preferences management
- **Dependencies**:
  - **Local**:
    - `core (get_user_data, update_user_preferences)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.schedule_runtime (is_schedule_period_active, set_schedule_period_active)` (NEW)
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core, core.error_handling, core.logger, core.schedule_runtime

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->
