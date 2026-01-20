# Module Dependencies - MHM Project

> **File**: `development_docs/MODULE_DEPENDENCIES_DETAIL.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-01-20 03:43:52
> **Source**: `python development_tools/generate_module_dependencies.py` - Module Dependencies Generator
> **Audience**: Human developer and AI collaborators  
> **Purpose**: Complete dependency map for all modules in the MHM codebase  
> **Status**: **ACTIVE** - Hybrid auto-generated and manually enhanced  

> **See [README.md](README.md) for complete navigation and project overview**
> **See [ARCHITECTURE.md](../ARCHITECTURE.md) for system architecture and design**
> **See [TODO.md](../TODO.md) for current documentation priorities**

## Overview

### Module Dependencies Coverage: 100.0% - COMPLETED
- **Files Scanned**: 108
- **Total Imports Found**: 1468
- **Dependencies Documented**: 108 (100% coverage)
- **Standard Library Imports**: 400 (27.2%)
- **Third-Party Imports**: 230 (15.7%)
- **Local Imports**: 838 (57.1%)
- **Last Updated**: 2026-01-20

**Status**: COMPLETED - All module dependencies have been documented with detailed dependency and usage information.

**Note**: This dependency map uses a hybrid approach. Automated analysis discovers dependencies while manual enhancements record intent and reverse dependencies.

## Import Statistics

- **Standard Library**: 400 imports (27.2%)
- **Third-Party**: 230 imports (15.7%)
- **Local**: 838 imports (57.1%)

## Module Dependencies by Directory

### `ai/` - AI services and support modules

#### `ai/__init__.py`
- **Purpose**: Communication channel implementation for __init__
- **Dependencies**: 
  - **Third-party**:
    - `cache_manager (CacheEntry, ContextCache, ResponseCache, get_context_cache, get_response_cache)`
    - `chatbot (AIChatBotSingleton, get_ai_chatbot)`
    - `context_builder (ContextAnalysis, ContextBuilder, ContextData, get_context_builder)`
    - `conversation_history (ConversationHistory, ConversationMessage, ConversationSession, get_conversation_history)`
    - `lm_studio_manager (LMStudioManager, ensure_lm_studio_ready, get_lm_studio_manager, is_lm_studio_ready)`
    - `prompt_manager (PromptManager, PromptTemplate, get_prompt_manager)`
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
    - `typing (Any, Dict, Optional, Tuple)`
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
    - `ai.lm_studio_manager (is_lm_studio_ready)` (NEW)
    - `ai.prompt_manager (get_prompt_manager)`
    - `core.config (AI_API_CALL_TIMEOUT, AI_CACHE_RESPONSES, AI_CHAT_TEMPERATURE, AI_CLARIFICATION_TEMPERATURE, AI_COMMAND_TEMPERATURE, AI_CONNECTION_TEST_TIMEOUT, AI_CONTEXTUAL_RESPONSE_TIMEOUT, AI_MAX_RESPONSE_LENGTH, AI_MAX_RESPONSE_TOKENS, AI_MAX_RESPONSE_WORDS, AI_MIN_RESPONSE_LENGTH, AI_PERSONALIZED_MESSAGE_TIMEOUT, AI_QUICK_RESPONSE_TIMEOUT, AI_SYSTEM_PROMPT_PATH, AI_TIMEOUT_SECONDS, AI_USE_CUSTOM_PROMPT, LM_STUDIO_API_KEY, LM_STUDIO_BASE_URL, LM_STUDIO_MODEL)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.message_management (get_recent_messages)` (NEW)
    - `core.response_tracking (get_recent_responses, is_user_checkins_enabled, store_chat_interaction)` (NEW)
    - `core.time_utilities (TIME_ONLY_MINUTE, format_timestamp, parse_timestamp_full)` (NEW)
    - `core.user_data_handlers (get_user_data)` (NEW)
    - `tasks.task_management (are_tasks_enabled, get_tasks_due_soon, get_user_task_stats, load_active_tasks)` (NEW)
    - `user.context_manager (user_context_manager)` (NEW)
  - **Standard Library**:
    - `asyncio`
    - `collections`
    - `datetime (date, datetime)`
    - `json`
    - `os`
    - `re`
    - `threading`
    - `typing (Optional)`
  - **Third-party**:
    - `psutil`
    - `requests`
- **Used by**: 
  - `communication/core/channel_orchestrator.py`
  - `communication/message_processing/command_parser.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `communication/message_processing/interaction_manager.py`

**Dependency Changes**:
- Added: ai.lm_studio_manager, core.config, core.error_handling, core.logger, core.message_management, core.response_tracking, core.time_utilities, core.user_data_handlers, tasks.task_management, user.context_manager
- Removed: communication/core/channel_orchestrator.py, communication/message_processing/command_parser.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/interaction_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: AI chatbot implementation using LM Studio API
<!-- MANUAL_ENHANCEMENT_END -->

#### `ai/context_builder.py`
- **Purpose**: Communication channel implementation for context_builder
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.response_tracking (get_recent_responses)` (NEW)
    - `core.time_utilities (now_datetime_full)` (NEW)
    - `core.user_data_handlers (get_user_data)` (NEW)
    - `user.context_manager (user_context_manager)` (NEW)
  - **Standard Library**:
    - `dataclasses (dataclass)`
    - `datetime`
    - `typing (Any, Dict, List, Optional)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.response_tracking, core.time_utilities, core.user_data_handlers, user.context_manager

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
    - `typing (Any, Dict, List, Optional)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.time_utilities

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
    - `core.config (AI_SYSTEM_PROMPT_PATH, AI_USE_CUSTOM_PROMPT)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `dataclasses (dataclass)`
    - `os`
    - `typing (Dict, Optional)`
- **Used by**: 
  - `ai/chatbot.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger
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
    - `communication.command_handlers.account_handler (_generate_confirmation_code, _pending_link_operations, _send_confirmation_code)` (NEW)
    - `communication.command_handlers.base_handler (InteractionHandler)` (NEW)
    - `communication.command_handlers.shared_types (InteractionResponse, ParsedCommand)` (NEW)
    - `communication.core.channel_orchestrator (CommunicationManager)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.user_data_handlers (create_new_user, get_all_user_ids, get_user_data, get_user_id_by_identifier, update_user_account)` (NEW)
    - `core.user_data_manager (update_user_index)` (NEW)
  - **Standard Library**:
    - `secrets`
    - `string`
    - `typing (Any, Dict, List, Optional)`
- **Used by**: 
  - `communication/command_handlers/account_handler.py`
  - `communication/command_handlers/interaction_handlers.py`
  - `communication/communication_channels/discord/account_flow_handler.py`

**Dependency Changes**:
- Added: communication.command_handlers.account_handler, communication.command_handlers.base_handler, communication.command_handlers.shared_types, communication.core.channel_orchestrator, core.error_handling, core.logger, core.user_data_handlers, core.user_data_manager
- Removed: communication/command_handlers/account_handler.py, communication/command_handlers/interaction_handlers.py, communication/communication_channels/discord/account_flow_handler.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/command_handlers/analytics_handler.py`
- **Purpose**: Communication channel implementation for analytics_handler
- **Dependencies**: 
  - **Local**:
    - `communication.command_handlers.base_handler (InteractionHandler)`
    - `communication.command_handlers.shared_types (InteractionResponse, ParsedCommand)`
    - `core.checkin_analytics (CheckinAnalytics)` (NEW)
    - `core.error_handling (handle_ai_error, handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.response_tracking (get_recent_checkins)` (NEW)
    - `core.user_data_handlers (get_user_data)` (NEW)
    - `tasks.task_management (get_user_task_stats, load_active_tasks, load_completed_tasks)` (NEW)
  - **Standard Library**:
    - `collections (Counter)`
    - `typing (Any, Dict, List)`
- **Used by**: 
  - `communication/command_handlers/interaction_handlers.py`
  - `communication/message_processing/conversation_flow_manager.py`

**Dependency Changes**:
- Added: core.checkin_analytics, core.error_handling, core.logger, core.response_tracking, core.user_data_handlers, tasks.task_management
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
    - `typing (List, Optional)`
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
- Removed: communication/command_handlers/account_handler.py, communication/command_handlers/analytics_handler.py, communication/command_handlers/checkin_handler.py, communication/command_handlers/interaction_handlers.py, communication/command_handlers/notebook_handler.py, communication/command_handlers/profile_handler.py, communication/command_handlers/schedule_handler.py

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
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.response_tracking (get_recent_checkins, is_user_checkins_enabled)` (NEW)
    - `core.time_utilities (parse_timestamp_full)` (NEW)
  - **Standard Library**:
    - `datetime (date)`
    - `typing (Any, Dict, List)`
- **Used by**: 
  - `communication/command_handlers/interaction_handlers.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.response_tracking, core.time_utilities
- Removed: communication/command_handlers/interaction_handlers.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/command_handlers/interaction_handlers.py`
- **Purpose**: Communication channel implementation for interaction_handlers
- **Dependencies**: 
  - **Local**:
    - `communication.command_handlers.account_handler (AccountManagementHandler)` (NEW)
    - `communication.command_handlers.analytics_handler (AnalyticsHandler)` (NEW)
    - `communication.command_handlers.base_handler (InteractionHandler)` (NEW)
    - `communication.command_handlers.checkin_handler (CheckinHandler)` (NEW)
    - `communication.command_handlers.notebook_handler (NotebookHandler)` (NEW)
    - `communication.command_handlers.profile_handler (ProfileHandler)` (NEW)
    - `communication.command_handlers.schedule_handler (ScheduleManagementHandler)` (NEW)
    - `communication.command_handlers.shared_types (InteractionResponse, ParsedCommand)`
    - `communication.command_handlers.task_handler (TaskManagementHandler)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.response_tracking (get_recent_checkins, is_user_checkins_enabled)` (NEW)
    - `core.user_data_handlers (get_user_data, save_user_data)` (NEW)
    - `tasks.task_management (load_active_tasks)` (NEW)
  - **Standard Library**:
    - `typing (Any, Dict, List, Optional)`
- **Used by**: 
  - `communication/message_processing/command_parser.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `communication/message_processing/interaction_manager.py`

**Dependency Changes**:
- Added: communication.command_handlers.account_handler, communication.command_handlers.analytics_handler, communication.command_handlers.base_handler, communication.command_handlers.checkin_handler, communication.command_handlers.notebook_handler, communication.command_handlers.profile_handler, communication.command_handlers.schedule_handler, communication.command_handlers.task_handler, core.error_handling, core.logger, core.response_tracking, core.user_data_handlers, tasks.task_management
- Removed: communication/message_processing/command_parser.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/interaction_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/command_handlers/notebook_handler.py`
- **Purpose**: Communication channel implementation for notebook_handler
- **Dependencies**: 
  - **Local**:
    - `communication.command_handlers.base_handler (InteractionHandler)` (NEW)
    - `communication.command_handlers.shared_types (InteractionResponse, ParsedCommand)` (NEW)
    - `communication.message_processing.conversation_flow_manager (FLOW_LIST_ITEMS, FLOW_NOTE_BODY, conversation_manager)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.tags (parse_tags_from_text)` (NEW)
    - `core.time_utilities (TIMESTAMP_FULL, now_timestamp_full)` (NEW)
  - **Standard Library**:
    - `typing (Any, Dict, List, Optional)`
  - **Third-party**:
    - `notebook.notebook_data_manager (add_list_item, add_tags, append_to_entry_body, archive_entry, create_journal, create_list, create_note, get_entry, list_archived, list_by_group, list_by_tag, list_inbox, list_pinned, list_recent, pin_entry, remove_list_item, remove_tags, search_entries, set_entry_body, set_group, toggle_list_item_done)`
    - `notebook.notebook_validation (format_short_id)`
    - `notebook.schemas (Entry)`
- **Used by**: 
  - `communication/command_handlers/interaction_handlers.py`

**Dependency Changes**:
- Added: communication.command_handlers.base_handler, communication.command_handlers.shared_types, communication.message_processing.conversation_flow_manager, core.error_handling, core.logger, core.tags, core.time_utilities
- Removed: communication/command_handlers/interaction_handlers.py, notebook.notebook_data_manager, notebook.notebook_validation, notebook.schemas

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/command_handlers/profile_handler.py`
- **Purpose**: Communication channel implementation for profile_handler
- **Dependencies**: 
  - **Local**:
    - `communication.command_handlers.base_handler (InteractionHandler)`
    - `communication.command_handlers.shared_types (InteractionResponse, ParsedCommand)`
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.response_tracking (get_recent_checkins)` (NEW)
    - `core.user_data_handlers (get_user_data, save_user_data)` (NEW)
    - `tasks.task_management (get_user_task_stats)` (NEW)
  - **Standard Library**:
    - `typing (Any, Dict, List)`
- **Used by**: 
  - `communication/command_handlers/interaction_handlers.py`
  - `communication/message_processing/conversation_flow_manager.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.response_tracking, core.user_data_handlers, tasks.task_management
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
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.schedule_management (add_schedule_period, get_schedule_time_periods, set_schedule_periods)` (NEW)
    - `core.user_data_handlers (get_user_categories)` (NEW)
  - **Standard Library**:
    - `typing (Any, Dict, List)`
- **Used by**: 
  - `communication/command_handlers/interaction_handlers.py`
  - `communication/message_processing/conversation_flow_manager.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.schedule_management, core.user_data_handlers
- Removed: communication/command_handlers/interaction_handlers.py, communication/message_processing/conversation_flow_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/command_handlers/shared_types.py`
- **Purpose**: Communication channel implementation for shared_types
- **Dependencies**: 
  - **Standard Library**:
    - `dataclasses (dataclass)`
    - `typing (Any, Dict, List, Optional)`
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
  - `communication/message_processing/command_parser.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `communication/message_processing/interaction_manager.py`

**Dependency Changes**:
- Removed: communication/command_handlers/account_handler.py, communication/command_handlers/analytics_handler.py, communication/command_handlers/base_handler.py, communication/command_handlers/checkin_handler.py, communication/command_handlers/interaction_handlers.py, communication/command_handlers/notebook_handler.py, communication/command_handlers/profile_handler.py, communication/command_handlers/schedule_handler.py, communication/communication_channels/discord/account_flow_handler.py, communication/message_processing/command_parser.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/interaction_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/command_handlers/task_handler.py`
- **Purpose**: Communication channel implementation for task_handler
- **Dependencies**: 
  - **Local**:
    - `communication.message_processing.conversation_flow_manager (conversation_manager)` (NEW)
    - `core.checkin_analytics (CheckinAnalytics)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.time_utilities (DATE_ONLY, format_timestamp, now_datetime_full, parse_date_only)` (NEW)
    - `core.user_data_handlers (get_user_data)` (NEW)
    - `tasks.task_management (complete_task, create_task, delete_task, get_tasks_due_soon, get_user_task_stats, load_active_tasks, update_task)` (NEW)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `re`
    - `typing (Any, Dict, List, Optional)`
  - **Third-party**:
    - `base_handler (InteractionHandler, InteractionResponse, ParsedCommand)`
- **Used by**: 
  - `communication/command_handlers/interaction_handlers.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `communication/message_processing/interaction_manager.py`

**Dependency Changes**:
- Added: communication.message_processing.conversation_flow_manager, core.checkin_analytics, core.error_handling, core.logger, core.time_utilities, core.user_data_handlers, tasks.task_management
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
    - `typing (Any, Dict, List, Optional)`
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
**Enhanced Purpose**: Abstract base class for communication channels
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/base/command_registry.py`
- **Purpose**: Communication channel implementation for command_registry
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `abc (ABC, abstractmethod)`
    - `dataclasses (dataclass)`
    - `typing (Callable, Dict, List, Optional)`
  - **Third-party**:
    - `discord (app_commands)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling, core.logger

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Registry for all available communication channels
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/base/message_formatter.py`
- **Purpose**: Communication channel implementation for message_formatter
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (DataError, handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `abc (ABC, abstractmethod)`
    - `typing (Any, Dict, List, Optional)`
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
    - `typing (Any, Dict, List)`
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
    - `communication.command_handlers.account_handler (AccountManagementHandler)` (NEW)
    - `communication.command_handlers.shared_types (ParsedCommand)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.user_data_handlers (TIMEZONE_OPTIONS)` (NEW)
  - **Standard Library**:
    - `typing (Optional)`
  - **Third-party**:
    - `discord`
- **Used by**: 
  - `communication/communication_channels/discord/bot.py`
  - `communication/communication_channels/discord/welcome_handler.py`

**Dependency Changes**:
- Added: communication.command_handlers.account_handler, communication.command_handlers.shared_types, core.error_handling, core.logger, core.user_data_handlers
- Removed: communication/communication_channels/discord/bot.py, communication/communication_channels/discord/welcome_handler.py

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
    - `typing (Any, Dict, List, Optional, Union)`
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
    - `communication.communication_channels.base.base_channel (BaseChannel, ChannelConfig, ChannelStatus, ChannelType)`
    - `communication.communication_channels.discord.account_flow_handler (start_account_creation_flow, start_account_linking_flow)` (NEW)
    - `communication.communication_channels.discord.webhook_server (WebhookServer)` (NEW)
    - `communication.communication_channels.discord.welcome_handler (get_welcome_message, has_been_welcomed, mark_as_welcomed)` (NEW)
    - `communication.message_processing.interaction_manager (get_interaction_manager, handle_user_message)`
    - `core.config (DISCORD_APPLICATION_ID, DISCORD_AUTO_NGROK, DISCORD_BOT_TOKEN, DISCORD_WEBHOOK_PORT)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.user_data_handlers (get_user_data, get_user_id_by_identifier, save_user_data)` (NEW)
  - **Standard Library**:
    - `asyncio`
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
    - `typing (Any, Dict, List, Optional)`
  - **Third-party**:
    - `aiohttp`
    - `discord (app_commands, discord)`
    - `discord.ext (commands)`
    - `dns.resolver`
    - `psutil`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: communication.communication_channels.discord.account_flow_handler, communication.communication_channels.discord.webhook_server, communication.communication_channels.discord.welcome_handler, core.config, core.error_handling, core.logger, core.user_data_handlers
- Removed: discord.ext, dns.resolver

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Discord bot implementation
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/discord/checkin_view.py`
- **Purpose**: Communication channel implementation for checkin_view
- **Dependencies**: 
  - **Local**:
    - `communication.message_processing.interaction_manager (handle_user_message)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.user_data_handlers (get_user_id_by_identifier)` (NEW)
  - **Standard Library**:
    - `typing (Optional)`
  - **Third-party**:
    - `discord`
- **Used by**: 
  - `communication/core/channel_orchestrator.py`

**Dependency Changes**:
- Added: communication.message_processing.interaction_manager, core.error_handling, core.logger, core.user_data_handlers
- Removed: communication/core/channel_orchestrator.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/discord/event_handler.py`
- **Purpose**: Communication channel implementation for event_handler
- **Dependencies**: 
  - **Local**:
    - `communication.communication_channels.base.rich_formatter (get_rich_formatter)`
    - `communication.message_processing.interaction_manager (handle_user_message)`
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.user_data_handlers (get_user_id_by_identifier)` (NEW)
  - **Standard Library**:
    - `dataclasses (dataclass)`
    - `enum (Enum)`
    - `time`
    - `typing (Any, Callable, Dict, List, Optional)`
  - **Third-party**:
    - `discord`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.user_data_handlers

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/discord/task_reminder_view.py`
- **Purpose**: Communication channel implementation for task_reminder_view
- **Dependencies**: 
  - **Local**:
    - `communication.message_processing.interaction_manager (handle_user_message)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.user_data_handlers (get_user_id_by_identifier)` (NEW)
  - **Standard Library**:
    - `typing (Optional)`
  - **Third-party**:
    - `discord`
- **Used by**: 
  - `communication/core/channel_orchestrator.py`

**Dependency Changes**:
- Added: communication.message_processing.interaction_manager, core.error_handling, core.logger, core.user_data_handlers
- Removed: communication/core/channel_orchestrator.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/discord/webhook_handler.py`
- **Purpose**: Communication channel implementation for webhook_handler
- **Dependencies**: 
  - **Local**:
    - `communication.communication_channels.discord.welcome_handler (get_welcome_message, get_welcome_message_view)` (NEW)
    - `communication.core.welcome_manager (clear_welcomed_status, has_been_welcomed, mark_as_welcomed)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (_is_testing_environment, get_component_logger)` (NEW)
    - `core.user_data_handlers (get_user_id_by_identifier, update_user_account)` (NEW)
  - **Standard Library**:
    - `asyncio`
    - `concurrent.futures (Future)`
    - `json`
    - `typing (Any, Dict, Optional)`
- **Used by**: 
  - `communication/communication_channels/discord/webhook_server.py`

**Dependency Changes**:
- Added: communication.communication_channels.discord.welcome_handler, communication.core.welcome_manager, core.error_handling, core.logger, core.user_data_handlers
- Removed: communication/communication_channels/discord/webhook_server.py, concurrent.futures

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/discord/webhook_server.py`
- **Purpose**: Communication channel implementation for webhook_server
- **Dependencies**: 
  - **Local**:
    - `communication.communication_channels.discord.webhook_handler (handle_webhook_event, parse_webhook_event)` (NEW)
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
- Added: communication.communication_channels.discord.webhook_handler, core.config, core.error_handling, core.logger
- Removed: communication/communication_channels/discord/bot.py, http.server, nacl.exceptions, nacl.signing

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/communication_channels/discord/welcome_handler.py`
- **Purpose**: Communication channel implementation for welcome_handler
- **Dependencies**: 
  - **Local**:
    - `communication.communication_channels.discord.account_flow_handler (start_account_creation_flow, start_account_linking_flow)` (NEW)
    - `communication.core.welcome_manager (clear_welcomed_status, get_welcome_message, has_been_welcomed, mark_as_welcomed)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `typing (Optional, TYPE_CHECKING)`
  - **Third-party**:
    - `discord`
- **Used by**: 
  - `communication/communication_channels/discord/bot.py`
  - `communication/communication_channels/discord/webhook_handler.py`

**Dependency Changes**:
- Added: communication.communication_channels.discord.account_flow_handler, communication.core.welcome_manager, core.error_handling, core.logger
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
    - `email`
    - `email.header (decode_header)`
    - `email.mime.text (MIMEText)`
    - `imaplib`
    - `re`
    - `smtplib`
    - `socket`
    - `time`
    - `typing (Any, Dict, List, Optional, Tuple)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger
- Removed: email.header, email.mime.text

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Email communication channel implementation
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/core/__init__.py`
- **Purpose**: Communication channel implementation for __init__
- **Dependencies**: 
  - **Third-party**:
    - `channel_monitor (ChannelMonitor)`
    - `factory (ChannelFactory)`
    - `retry_manager (QueuedMessage, RetryManager)`
- **Used by**: None (not imported by other modules)

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
    - `datetime`
    - `threading`
    - `time`
    - `typing (Any, Dict, Optional)`
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
    - `communication.communication_channels.discord.checkin_view (get_checkin_view)` (NEW)
    - `communication.communication_channels.discord.task_reminder_view (get_task_reminder_view)` (NEW)
    - `communication.core.channel_monitor (ChannelMonitor)`
    - `communication.core.factory (ChannelFactory)`
    - `communication.core.retry_manager (RetryManager)`
    - `communication.message_processing.conversation_flow_manager (conversation_manager)`
    - `communication.message_processing.interaction_manager (handle_user_message)` (NEW)
    - `core.config (DISCORD_BOT_TOKEN, EMAIL_SMTP_SERVER, get_available_channels, get_user_data_dir)` (NEW)
    - `core.error_handling (handle_communication_error, handle_errors, handle_network_error)` (NEW)
    - `core.file_operations (determine_file_path, load_json_data)` (NEW)
    - `core.logger (force_restart_logging, get_component_logger)` (NEW)
    - `core.message_management (get_recent_messages, store_sent_message)` (NEW)
    - `core.schedule_management (get_current_day_names, get_current_time_periods_with_validation)` (NEW)
    - `core.schemas (validate_messages_file_dict)` (NEW)
    - `core.service_utilities (wait_for_network)` (NEW)
    - `core.user_data_handlers (get_user_data, get_user_id_by_identifier)` (NEW)
    - `tasks.task_management (are_tasks_enabled, get_task_by_id)` (NEW)
  - **Standard Library**:
    - `asyncio`
    - `pathlib (Path)`
    - `random`
    - `re`
    - `threading`
    - `time`
    - `typing (Any, Dict, List, Optional)`
    - `uuid`
- **Used by**: 
  - `communication/command_handlers/account_handler.py`
  - `core/scheduler.py`
  - `core/service.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: communication.communication_channels.discord.checkin_view, communication.communication_channels.discord.task_reminder_view, communication.message_processing.interaction_manager, core.config, core.error_handling, core.file_operations, core.logger, core.message_management, core.schedule_management, core.schemas, core.service_utilities, core.user_data_handlers, tasks.task_management
- Removed: communication/command_handlers/account_handler.py, core/scheduler.py, core/service.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Manages communication across all channels
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/core/factory.py`
- **Purpose**: Communication channel implementation for factory
- **Dependencies**: 
  - **Local**:
    - `communication.communication_channels.base.base_channel (BaseChannel, ChannelConfig)`
    - `core.config (get_available_channels, get_channel_class_mapping)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `importlib`
    - `typing (Dict, Optional, Type)`
- **Used by**: 
  - `communication/core/channel_orchestrator.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger
- Removed: communication/core/channel_orchestrator.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Factory for creating communication channels
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
    - `core.time_utilities (now_timestamp_full)` (NEW)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `pathlib (Path)`
    - `typing (Any, Dict, Optional)`
- **Used by**: 
  - `communication/communication_channels/discord/webhook_handler.py`
  - `communication/communication_channels/discord/welcome_handler.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger, core.time_utilities
- Removed: communication/communication_channels/discord/webhook_handler.py, communication/communication_channels/discord/welcome_handler.py

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
    - `core.config (AI_AI_ENHANCED_CONFIDENCE_THRESHOLD, AI_AI_PARSING_BASE_CONFIDENCE, AI_AI_PARSING_PARTIAL_CONFIDENCE, AI_COMMAND_PARSING_TIMEOUT, AI_RULE_BASED_FALLBACK_THRESHOLD, AI_RULE_BASED_HIGH_CONFIDENCE_THRESHOLD)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.tags (parse_tags_from_text)` (NEW)
  - **Standard Library**:
    - `dataclasses (dataclass)`
    - `json`
    - `re`
    - `typing (Any, Dict, List, Optional)`
- **Used by**: 
  - `communication/message_processing/interaction_manager.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger, core.tags
- Removed: communication/message_processing/interaction_manager.py

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
    - `communication.command_handlers.shared_types (ParsedCommand)` (NEW)
    - `communication.command_handlers.task_handler (TaskManagementHandler)`
    - `communication.message_processing.interaction_manager (handle_user_message)`
    - `core.checkin_dynamic_manager (dynamic_checkin_manager)` (NEW)
    - `core.config (BASE_DATA_DIR)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.response_tracking (get_recent_checkins, is_user_checkins_enabled, store_user_response)` (NEW)
    - `core.tags (parse_tags_from_text)` (NEW)
    - `core.time_utilities (DATE_ONLY, TIME_ONLY_MINUTE, format_timestamp, now_datetime_full, now_timestamp_full, parse_date_and_time_minute, parse_date_only, parse_time_only_minute, parse_timestamp_full)` (NEW)
    - `core.user_data_handlers (get_user_data)` (NEW)
    - `tasks.task_management (get_task_by_id, update_task)` (NEW)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `random`
    - `re`
    - `typing (Optional)`
  - **Third-party**:
    - `notebook.notebook_data_manager (create_list, create_note)`
- **Used by**: 
  - `communication/command_handlers/checkin_handler.py`
  - `communication/command_handlers/notebook_handler.py`
  - `communication/command_handlers/task_handler.py`
  - `communication/core/channel_orchestrator.py`
  - `communication/message_processing/interaction_manager.py`
  - `core/service.py`

**Dependency Changes**:
- Added: communication.command_handlers.shared_types, core.checkin_dynamic_manager, core.config, core.error_handling, core.logger, core.response_tracking, core.tags, core.time_utilities, core.user_data_handlers, tasks.task_management
- Removed: communication/command_handlers/checkin_handler.py, communication/command_handlers/notebook_handler.py, communication/command_handlers/task_handler.py, communication/core/channel_orchestrator.py, communication/message_processing/interaction_manager.py, core/service.py, notebook.notebook_data_manager

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Manages conversation flows and check-ins
<!-- MANUAL_ENHANCEMENT_END -->

#### `communication/message_processing/interaction_manager.py`
- **Purpose**: Communication channel implementation for interaction_manager
- **Dependencies**: 
  - **Local**:
    - `ai.chatbot (get_ai_chatbot)`
    - `communication.command_handlers.interaction_handlers (get_all_handlers, get_interaction_handler)`
    - `communication.command_handlers.shared_types (InteractionResponse, ParsedCommand)`
    - `communication.command_handlers.task_handler (TaskManagementHandler)` (NEW)
    - `communication.message_processing.command_parser (ParsingResult, get_enhanced_command_parser)`
    - `communication.message_processing.conversation_flow_manager (FLOW_TASK_REMINDER, conversation_manager)`
    - `core.config (AI_MAX_RESPONSE_LENGTH)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.response_tracking (get_recent_checkins, is_user_checkins_enabled)` (NEW)
    - `core.time_utilities (DATE_DISPLAY_MONTH_DAY, format_timestamp, now_datetime_full, parse_date_and_time_minute, parse_date_only, parse_timestamp_full)` (NEW)
    - `core.user_data_handlers (get_user_categories)` (NEW)
    - `tasks.task_management (load_active_tasks)` (NEW)
  - **Standard Library**:
    - `dataclasses (dataclass)`
    - `datetime`
    - `json`
    - `re`
    - `typing (Any, Dict, List, Optional)`
- **Used by**: 
  - `communication/communication_channels/discord/bot.py`
  - `communication/communication_channels/discord/checkin_view.py`
  - `communication/communication_channels/discord/event_handler.py`
  - `communication/communication_channels/discord/task_reminder_view.py`
  - `communication/core/channel_orchestrator.py`
  - `communication/message_processing/conversation_flow_manager.py`

**Dependency Changes**:
- Added: communication.command_handlers.task_handler, core.config, core.error_handling, core.logger, core.response_tracking, core.time_utilities, core.user_data_handlers, tasks.task_management
- Removed: communication/communication_channels/discord/bot.py, communication/communication_channels/discord/checkin_view.py, communication/communication_channels/discord/event_handler.py, communication/communication_channels/discord/task_reminder_view.py, communication/core/channel_orchestrator.py, communication/message_processing/conversation_flow_manager.py

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
    - `typing (Dict, List, Optional)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling, core.logger

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

### `core/` - Core system modules (foundation)

#### `core/__init__.py`
- **Purpose**: Core system module for __init__
- **Dependencies**: 
  - **Third-party**:
    - `auto_cleanup (archive_old_messages_for_all_users, auto_cleanup_if_needed, cleanup_data_directory, cleanup_tests_data_directory, get_cleanup_status, get_last_cleanup_timestamp, perform_cleanup, should_run_cleanup, update_cleanup_timestamp)`
    - `backup_manager (BackupManager)`
    - `checkin_analytics (CheckinAnalytics)`
    - `checkin_dynamic_manager (DynamicCheckinManager, dynamic_checkin_manager)`
    - `config (CONTEXT_CACHE_TTL, ConfigValidationError, DISCORD_APPLICATION_ID, DISCORD_BOT_TOKEN, EMAIL_IMAP_SERVER, EMAIL_SMTP_PASSWORD, EMAIL_SMTP_SERVER, EMAIL_SMTP_USERNAME, LM_STUDIO_API_KEY, LM_STUDIO_BASE_URL, LM_STUDIO_MODEL, SCHEDULER_INTERVAL, ensure_user_directory, get_available_channels, get_backups_dir, get_channel_class_mapping, get_user_data_dir, get_user_file_path, print_configuration_report, validate_ai_configuration, validate_all_configuration, validate_and_raise_if_invalid, validate_communication_channels, validate_core_paths, validate_discord_config, validate_email_config, validate_environment_variables, validate_file_organization_settings, validate_logging_configuration, validate_minimum_config, validate_scheduler_configuration)`
    - `error_handling (AIError, CommunicationError, ConfigurationError, ConfigurationRecovery, DataError, ErrorHandler, ErrorRecoveryStrategy, FileOperationError, MHMError, RecoveryError, SchedulerError, UserInterfaceError, ValidationError, handle_ai_error, handle_errors, handle_network_error)`
    - `file_auditor (FileAuditor, record_created, start_auditor, stop_auditor)`
    - `file_operations (create_user_files, determine_file_path, load_json_data, save_json_data, verify_file_access)`
    - `headless_service (HeadlessServiceManager)`
    - `logger (BackupDirectoryRotatingFileHandler, ComponentLogger, ExcludeLoggerNamesFilter, PytestContextLogFormatter, get_component_logger, get_logger, get_verbose_mode, set_console_log_level, set_verbose_mode, setup_logging, setup_third_party_error_logging, suppress_noisy_logging, toggle_verbose_logging)`
    - `message_management (add_message, archive_old_messages, get_message_categories, get_recent_messages, load_user_messages, store_sent_message)`
    - `response_tracking (get_recent_checkins, get_recent_responses, is_user_checkins_enabled, store_chat_interaction)`
    - `schedule_management (add_schedule_period)`
    - `schedule_utilities (get_active_schedules, get_current_active_schedules, is_schedule_active)`
    - `scheduler (SchedulerManager)`
    - `schemas (AccountModel, CategoryScheduleModel, ChannelModel, FeaturesModel, MessageModel, MessagesFileModel, PeriodModel, PreferencesModel, SchedulesModel, validate_account_dict, validate_messages_file_dict, validate_preferences_dict, validate_schedules_dict)`
    - `service (InitializationError, MHMService)`
    - `service_utilities (InvalidTimeFormatError, Throttler, create_reschedule_request, get_service_processes, is_headless_service_running, is_service_running, is_ui_service_running, load_and_localize_datetime, wait_for_network)`
    - `ui_management (collect_period_data_from_widgets, load_period_widgets_for_category)`
    - `user_data_handlers (clear_user_caches, create_default_schedule_periods, ensure_all_categories_have_schedules, ensure_category_has_default_schedule, get_all_user_ids, get_available_data_types, get_data_type_info, get_user_categories, get_user_data, get_user_id_by_identifier, migrate_legacy_schedules_structure, register_data_loader, register_default_loaders, save_user_data, save_user_data_transaction, update_channel_preferences, update_user_account, update_user_context, update_user_preferences, update_user_schedules)`
    - `user_data_manager (UserDataManager, backup_user_data, build_user_index, delete_user_completely, export_user_data, get_all_user_summaries, get_user_analytics_summary, get_user_data_summary, get_user_info_for_data_manager, get_user_summary, rebuild_user_index, update_message_references, update_user_index)`
    - `user_data_validation (is_valid_email, validate_schedule_periods)`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/auto_cleanup.py`
- **Purpose**: Automatic cache cleanup and maintenance
- **Dependencies**: 
  - **Local**:
    - `core.config (BASE_DATA_DIR, get_backups_dir)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.message_management (archive_old_messages)` (NEW)
    - `core.time_utilities (DATE_ONLY, format_timestamp, now_datetime_full, now_timestamp_full)` (NEW)
    - `core.user_data_handlers (get_all_user_ids)` (NEW)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
    - `time`
- **Used by**: 
  - `core/scheduler.py`
  - `core/service.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger, core.message_management, core.time_utilities, core.user_data_handlers
- Removed: core/scheduler.py, core/service.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Automatic cache cleanup and maintenance
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/backup_manager.py`
- **Purpose**: Manages automatic backups and rollback operations
- **Dependencies**: 
  - **Local**:
    - `core.config (LOG_AI_FILE, LOG_DISCORD_FILE, LOG_ERRORS_FILE, LOG_MAIN_FILE, LOG_USER_ACTIVITY_FILE, core.config)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, get_logger)` (NEW)
    - `core.time_utilities (TIMESTAMP_FULL, format_timestamp, now_timestamp_filename, now_timestamp_full)` (NEW)
    - `core.user_data_handlers (get_all_user_ids, get_user_data)` (NEW)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `time`
    - `traceback`
    - `typing (Dict, List, Optional, Tuple)`
    - `zipfile`
- **Used by**: 
  - `core/scheduler.py`
  - `create_backup.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger, core.time_utilities, core.user_data_handlers
- Removed: core/scheduler.py, create_backup.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Manages automatic backups and rollback operations
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/checkin_analytics.py`
- **Purpose**: Analyzes check-in data and provides insights
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.response_tracking (get_checkins_by_days)` (NEW)
    - `core.time_utilities (parse_time_only_minute, parse_timestamp_full)` (NEW)
    - `core.user_data_handlers (get_user_data)` (NEW)
  - **Standard Library**:
    - `datetime (timedelta)`
    - `statistics`
    - `typing (Dict, List, Optional)`
- **Used by**: 
  - `communication/command_handlers/analytics_handler.py`
  - `communication/command_handlers/task_handler.py`
  - `ui/dialogs/user_analytics_dialog.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.response_tracking, core.time_utilities, core.user_data_handlers
- Removed: communication/command_handlers/analytics_handler.py, communication/command_handlers/task_handler.py, ui/dialogs/user_analytics_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Analyzes check-in data and provides insights
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/checkin_dynamic_manager.py`
- **Purpose**: Core system module for checkin_dynamic_manager
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.file_operations (load_json_data)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.user_data_handlers (get_user_data, update_user_preferences)` (NEW)
  - **Standard Library**:
    - `pathlib (Path)`
    - `random`
    - `re`
    - `typing (Any, Dict, Optional, Tuple)`
- **Used by**: 
  - `communication/message_processing/conversation_flow_manager.py`
  - `ui/widgets/checkin_settings_widget.py`

**Dependency Changes**:
- Added: core.error_handling, core.file_operations, core.logger, core.user_data_handlers
- Removed: communication/message_processing/conversation_flow_manager.py, ui/widgets/checkin_settings_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/config.py`
- **Purpose**: Configuration management and validation
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (ConfigurationError, handle_configuration_error, handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
  - **Standard Library**:
    - `os`
    - `pathlib (Path)`
    - `typing (Dict, List, Optional, Tuple)`
  - **Third-party**:
    - `dotenv (load_dotenv)`
- **Used by**: 
  - `ai/cache_manager.py`
  - `ai/chatbot.py`
  - `ai/lm_studio_manager.py`
  - `ai/prompt_manager.py`
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
  - `core/scheduler.py`
  - `core/service.py`
  - `core/service_utilities.py`
  - `core/tags.py`
  - `core/user_data_handlers.py`
  - `core/user_data_manager.py`
  - `core/user_data_validation.py`
  - `tasks/task_management.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/schedule_editor_dialog.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger
- Removed: ai/cache_manager.py, ai/chatbot.py, ai/lm_studio_manager.py, ai/prompt_manager.py, communication/communication_channels/discord/bot.py, communication/communication_channels/discord/webhook_server.py, communication/communication_channels/email/bot.py, communication/core/channel_orchestrator.py, communication/core/factory.py, communication/core/welcome_manager.py, communication/message_processing/command_parser.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/interaction_manager.py, core/auto_cleanup.py, core/backup_manager.py, core/file_operations.py, core/logger.py, core/message_management.py, core/scheduler.py, core/service.py, core/service_utilities.py, core/tags.py, core/user_data_handlers.py, core/user_data_manager.py, core/user_data_validation.py, tasks/task_management.py, ui/dialogs/account_creator_dialog.py, ui/dialogs/schedule_editor_dialog.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Configuration management and validation
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/error_handling.py`
- **Purpose**: Centralized error handling and recovery
- **Dependencies**: 
  - **Local**:
    - `core.logger (get_component_logger)` (NEW)
    - `core.service_utilities (wait_for_network)` (NEW)
    - `core.time_utilities (now_datetime_full, now_timestamp_filename, now_timestamp_full, parse_timestamp_full)` (NEW)
  - **Standard Library**:
    - `asyncio`
    - `datetime`
    - `functools`
    - `json`
    - `logging`
    - `os`
    - `shutil`
    - `sys`
    - `threading`
    - `time`
    - `traceback`
    - `typing (Any, Callable, Dict, List, Optional)`
- **Used by**: 
  - `ai/cache_manager.py`
  - `ai/chatbot.py`
  - `ai/context_builder.py`
  - `ai/conversation_history.py`
  - `ai/lm_studio_manager.py`
  - `ai/prompt_manager.py`
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
  - `communication/message_processing/command_parser.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `communication/message_processing/interaction_manager.py`
  - `communication/message_processing/message_router.py`
  - `core/auto_cleanup.py`
  - `core/backup_manager.py`
  - `core/checkin_analytics.py`
  - `core/checkin_dynamic_manager.py`
  - `core/config.py`
  - `core/file_auditor.py`
  - `core/file_locking.py`
  - `core/file_operations.py`
  - `core/headless_service.py`
  - `core/logger.py`
  - `core/message_analytics.py`
  - `core/message_management.py`
  - `core/response_tracking.py`
  - `core/schedule_management.py`
  - `core/schedule_utilities.py`
  - `core/scheduler.py`
  - `core/schemas.py`
  - `core/service.py`
  - `core/service_utilities.py`
  - `core/tags.py`
  - `core/ui_management.py`
  - `core/user_data_handlers.py`
  - `core/user_data_manager.py`
  - `core/user_data_validation.py`
  - `run_headless_service.py`
  - `tasks/task_management.py`
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
  - `ui/generate_ui_files.py`
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
- Added: core.logger, core.service_utilities, core.time_utilities
- Removed: ai/cache_manager.py, ai/chatbot.py, ai/context_builder.py, ai/conversation_history.py, ai/lm_studio_manager.py, ai/prompt_manager.py, communication/command_handlers/account_handler.py, communication/command_handlers/analytics_handler.py, communication/command_handlers/base_handler.py, communication/command_handlers/checkin_handler.py, communication/command_handlers/interaction_handlers.py, communication/command_handlers/notebook_handler.py, communication/command_handlers/profile_handler.py, communication/command_handlers/schedule_handler.py, communication/command_handlers/task_handler.py, communication/communication_channels/base/base_channel.py, communication/communication_channels/base/command_registry.py, communication/communication_channels/base/message_formatter.py, communication/communication_channels/base/rich_formatter.py, communication/communication_channels/discord/account_flow_handler.py, communication/communication_channels/discord/api_client.py, communication/communication_channels/discord/bot.py, communication/communication_channels/discord/checkin_view.py, communication/communication_channels/discord/event_handler.py, communication/communication_channels/discord/task_reminder_view.py, communication/communication_channels/discord/webhook_handler.py, communication/communication_channels/discord/webhook_server.py, communication/communication_channels/discord/welcome_handler.py, communication/communication_channels/email/bot.py, communication/core/channel_monitor.py, communication/core/channel_orchestrator.py, communication/core/factory.py, communication/core/retry_manager.py, communication/core/welcome_manager.py, communication/message_processing/command_parser.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/interaction_manager.py, communication/message_processing/message_router.py, core/auto_cleanup.py, core/backup_manager.py, core/checkin_analytics.py, core/checkin_dynamic_manager.py, core/config.py, core/file_auditor.py, core/file_locking.py, core/file_operations.py, core/headless_service.py, core/logger.py, core/message_analytics.py, core/message_management.py, core/response_tracking.py, core/schedule_management.py, core/schedule_utilities.py, core/scheduler.py, core/schemas.py, core/service.py, core/service_utilities.py, core/tags.py, core/ui_management.py, core/user_data_handlers.py, core/user_data_manager.py, core/user_data_validation.py, run_headless_service.py, tasks/task_management.py, ui/dialogs/account_creator_dialog.py, ui/dialogs/admin_panel.py, ui/dialogs/category_management_dialog.py, ui/dialogs/channel_management_dialog.py, ui/dialogs/checkin_management_dialog.py, ui/dialogs/message_editor_dialog.py, ui/dialogs/process_watcher_dialog.py, ui/dialogs/schedule_editor_dialog.py, ui/dialogs/task_completion_dialog.py, ui/dialogs/task_crud_dialog.py, ui/dialogs/task_edit_dialog.py, ui/dialogs/task_management_dialog.py, ui/dialogs/user_analytics_dialog.py, ui/dialogs/user_profile_dialog.py, ui/generate_ui_files.py, ui/ui_app_qt.py, ui/widgets/category_selection_widget.py, ui/widgets/channel_selection_widget.py, ui/widgets/checkin_settings_widget.py, ui/widgets/dynamic_list_container.py, ui/widgets/dynamic_list_field.py, ui/widgets/period_row_widget.py, ui/widgets/tag_widget.py, ui/widgets/task_settings_widget.py, ui/widgets/user_profile_settings_widget.py, user/context_manager.py, user/user_context.py, user/user_preferences.py

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
    - `os`
    - `traceback`
    - `typing (Dict, List, Optional)`
- **Used by**: 
  - `core/file_operations.py`
  - `core/service.py`
  - `core/service_utilities.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger
- Removed: core/file_operations.py, core/service.py, core/service_utilities.py

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
  - `core/user_data_handlers.py`
  - `core/user_data_manager.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger
- Removed: core/user_data_handlers.py, core/user_data_manager.py

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
    - `core.message_management (create_message_file_from_defaults)` (NEW)
    - `core.time_utilities (now_timestamp_full)` (NEW)
    - `core.user_data_manager (update_message_references, update_user_index)` (NEW)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `re`
    - `shutil`
    - `time`
- **Used by**: 
  - `communication/core/channel_orchestrator.py`
  - `core/checkin_dynamic_manager.py`
  - `core/message_management.py`
  - `core/response_tracking.py`
  - `core/service.py`
  - `core/tags.py`
  - `core/user_data_handlers.py`
  - `core/user_data_manager.py`
  - `tasks/task_management.py`
  - `ui/dialogs/account_creator_dialog.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.file_auditor, core.logger, core.message_management, core.time_utilities, core.user_data_manager
- Removed: communication/core/channel_orchestrator.py, core/checkin_dynamic_manager.py, core/message_management.py, core/response_tracking.py, core/service.py, core/tags.py, core/user_data_handlers.py, core/user_data_manager.py, tasks/task_management.py, ui/dialogs/account_creator_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: File operations and data management
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/headless_service.py`
- **Purpose**: Main service orchestration and management
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.service_utilities (get_flags_dir, get_service_processes, is_headless_service_running, is_ui_service_running)` (NEW)
  - **Standard Library**:
    - `argparse`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `subprocess`
    - `sys`
    - `time`
    - `typing (Optional)`
  - **Third-party**:
    - `psutil`
- **Used by**: 
  - `run_headless_service.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.service_utilities
- Removed: run_headless_service.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/logger.py`
- **Purpose**: Logging system configuration and management
- **Dependencies**: 
  - **Local**:
    - `core.config` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
  - **Standard Library**:
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
- **Used by**: 
  - `ai/cache_manager.py`
  - `ai/chatbot.py`
  - `ai/context_builder.py`
  - `ai/conversation_history.py`
  - `ai/lm_studio_manager.py`
  - `ai/prompt_manager.py`
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
  - `communication/message_processing/command_parser.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `communication/message_processing/interaction_manager.py`
  - `communication/message_processing/message_router.py`
  - `core/auto_cleanup.py`
  - `core/backup_manager.py`
  - `core/checkin_analytics.py`
  - `core/checkin_dynamic_manager.py`
  - `core/config.py`
  - `core/error_handling.py`
  - `core/file_auditor.py`
  - `core/file_locking.py`
  - `core/file_operations.py`
  - `core/headless_service.py`
  - `core/message_analytics.py`
  - `core/message_management.py`
  - `core/response_tracking.py`
  - `core/schedule_management.py`
  - `core/schedule_utilities.py`
  - `core/scheduler.py`
  - `core/schemas.py`
  - `core/service.py`
  - `core/service_utilities.py`
  - `core/tags.py`
  - `core/ui_management.py`
  - `core/user_data_handlers.py`
  - `core/user_data_manager.py`
  - `core/user_data_validation.py`
  - `run_headless_service.py`
  - `tasks/task_management.py`
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
- Added: core.config, core.error_handling
- Removed: ai/cache_manager.py, ai/chatbot.py, ai/context_builder.py, ai/conversation_history.py, ai/lm_studio_manager.py, ai/prompt_manager.py, communication/command_handlers/account_handler.py, communication/command_handlers/analytics_handler.py, communication/command_handlers/base_handler.py, communication/command_handlers/checkin_handler.py, communication/command_handlers/interaction_handlers.py, communication/command_handlers/notebook_handler.py, communication/command_handlers/profile_handler.py, communication/command_handlers/schedule_handler.py, communication/command_handlers/task_handler.py, communication/communication_channels/base/base_channel.py, communication/communication_channels/base/command_registry.py, communication/communication_channels/base/message_formatter.py, communication/communication_channels/base/rich_formatter.py, communication/communication_channels/discord/account_flow_handler.py, communication/communication_channels/discord/api_client.py, communication/communication_channels/discord/bot.py, communication/communication_channels/discord/checkin_view.py, communication/communication_channels/discord/event_handler.py, communication/communication_channels/discord/task_reminder_view.py, communication/communication_channels/discord/webhook_handler.py, communication/communication_channels/discord/webhook_server.py, communication/communication_channels/discord/welcome_handler.py, communication/communication_channels/email/bot.py, communication/core/channel_monitor.py, communication/core/channel_orchestrator.py, communication/core/factory.py, communication/core/retry_manager.py, communication/core/welcome_manager.py, communication/message_processing/command_parser.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/interaction_manager.py, communication/message_processing/message_router.py, core/auto_cleanup.py, core/backup_manager.py, core/checkin_analytics.py, core/checkin_dynamic_manager.py, core/config.py, core/error_handling.py, core/file_auditor.py, core/file_locking.py, core/file_operations.py, core/headless_service.py, core/message_analytics.py, core/message_management.py, core/response_tracking.py, core/schedule_management.py, core/schedule_utilities.py, core/scheduler.py, core/schemas.py, core/service.py, core/service_utilities.py, core/tags.py, core/ui_management.py, core/user_data_handlers.py, core/user_data_manager.py, core/user_data_validation.py, logging.handlers, run_headless_service.py, tasks/task_management.py, ui/dialogs/account_creator_dialog.py, ui/dialogs/admin_panel.py, ui/dialogs/category_management_dialog.py, ui/dialogs/channel_management_dialog.py, ui/dialogs/checkin_management_dialog.py, ui/dialogs/message_editor_dialog.py, ui/dialogs/process_watcher_dialog.py, ui/dialogs/schedule_editor_dialog.py, ui/dialogs/task_completion_dialog.py, ui/dialogs/task_crud_dialog.py, ui/dialogs/task_edit_dialog.py, ui/dialogs/task_management_dialog.py, ui/dialogs/user_analytics_dialog.py, ui/dialogs/user_profile_dialog.py, ui/ui_app_qt.py, ui/widgets/category_selection_widget.py, ui/widgets/channel_selection_widget.py, ui/widgets/checkin_settings_widget.py, ui/widgets/dynamic_list_container.py, ui/widgets/dynamic_list_field.py, ui/widgets/period_row_widget.py, ui/widgets/tag_widget.py, ui/widgets/task_settings_widget.py, ui/widgets/user_profile_settings_widget.py, user/context_manager.py, user/user_context.py, user/user_preferences.py

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
    - `core.schemas (validate_messages_file_dict)` (NEW)
    - `core.time_utilities (TIMESTAMP_FULL, now_timestamp_filename, now_timestamp_full, parse_timestamp, parse_timestamp_full)` (NEW)
    - `core.user_data_manager (update_user_index)` (NEW)
  - **Standard Library**:
    - `datetime (datetime, timedelta, timezone)`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `typing (Any, Dict, List, Optional)`
    - `uuid`
- **Used by**: 
  - `ai/chatbot.py`
  - `communication/core/channel_orchestrator.py`
  - `core/auto_cleanup.py`
  - `core/file_operations.py`
  - `core/message_analytics.py`
  - `core/schemas.py`
  - `core/service.py`
  - `core/user_data_handlers.py`
  - `core/user_data_manager.py`
  - `core/user_data_validation.py`
  - `ui/dialogs/message_editor_dialog.py`
  - `user/context_manager.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.file_operations, core.logger, core.schemas, core.time_utilities, core.user_data_manager
- Removed: ai/chatbot.py, communication/core/channel_orchestrator.py, core/auto_cleanup.py, core/file_operations.py, core/message_analytics.py, core/schemas.py, core/service.py, core/user_data_handlers.py, core/user_data_manager.py, core/user_data_validation.py, ui/dialogs/message_editor_dialog.py, user/context_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Message management and storage
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/response_tracking.py`
- **Purpose**: Tracks user responses and interactions
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.file_operations (get_user_file_path, load_json_data, save_json_data)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.time_utilities (now_datetime_full, now_timestamp_full, parse_timestamp_full)` (NEW)
    - `core.user_data_handlers (get_user_data)` (NEW)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `typing (Any)`
- **Used by**: 
  - `ai/chatbot.py`
  - `ai/context_builder.py`
  - `communication/command_handlers/analytics_handler.py`
  - `communication/command_handlers/checkin_handler.py`
  - `communication/command_handlers/interaction_handlers.py`
  - `communication/command_handlers/profile_handler.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `communication/message_processing/interaction_manager.py`
  - `core/checkin_analytics.py`
  - `core/user_data_manager.py`
  - `ui/dialogs/user_analytics_dialog.py`
  - `user/context_manager.py`

**Dependency Changes**:
- Added: core.error_handling, core.file_operations, core.logger, core.time_utilities, core.user_data_handlers
- Removed: ai/chatbot.py, ai/context_builder.py, communication/command_handlers/analytics_handler.py, communication/command_handlers/checkin_handler.py, communication/command_handlers/interaction_handlers.py, communication/command_handlers/profile_handler.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/interaction_manager.py, core/checkin_analytics.py, core/user_data_manager.py, ui/dialogs/user_analytics_dialog.py, user/context_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Tracks user responses and interactions
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/schedule_management.py`
- **Purpose**: Schedule management and time period handling
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (ValidationError, handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.service_utilities (create_reschedule_request)` (NEW)
    - `core.time_utilities (TIME_ONLY_MINUTE, format_timestamp, now_datetime_full, parse_time_only_minute)` (NEW)
    - `core.user_data_handlers (get_user_data, update_user_schedules)` (NEW)
    - `user.user_context (UserContext)` (NEW)
  - **Standard Library**:
    - `calendar`
    - `datetime`
    - `re`
    - `time`
    - `typing (Any, Dict, Optional)`
- **Used by**: 
  - `communication/command_handlers/schedule_handler.py`
  - `communication/core/channel_orchestrator.py`
  - `core/scheduler.py`
  - `core/service.py`
  - `core/ui_management.py`
  - `ui/dialogs/category_management_dialog.py`
  - `ui/dialogs/checkin_management_dialog.py`
  - `ui/dialogs/schedule_editor_dialog.py`
  - `ui/dialogs/task_management_dialog.py`
  - `ui/widgets/period_row_widget.py`
  - `user/user_preferences.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.service_utilities, core.time_utilities, core.user_data_handlers, user.user_context
- Removed: communication/command_handlers/schedule_handler.py, communication/core/channel_orchestrator.py, core/scheduler.py, core/service.py, core/ui_management.py, ui/dialogs/category_management_dialog.py, ui/dialogs/checkin_management_dialog.py, ui/dialogs/schedule_editor_dialog.py, ui/dialogs/task_management_dialog.py, ui/widgets/period_row_widget.py, user/user_preferences.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Schedule management and time period handling
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/schedule_utilities.py`
- **Purpose**: Core system module for schedule_utilities
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.time_utilities (DATE_DISPLAY_WEEKDAY, TIME_ONLY_MINUTE, format_timestamp, now_datetime_full, parse_time_only_minute)` (NEW)
  - **Standard Library**:
    - `datetime`
    - `typing (Dict, List, Optional)`
- **Used by**: 
  - `user/context_manager.py`
  - `user/user_context.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.time_utilities
- Removed: user/context_manager.py, user/user_context.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/scheduler.py`
- **Purpose**: Task scheduling and job management
- **Dependencies**: 
  - **Local**:
    - `communication.core.channel_orchestrator (CommunicationManager)` (NEW)
    - `core.auto_cleanup (cleanup_data_directory, cleanup_tests_data_directory)` (NEW)
    - `core.backup_manager (backup_manager)` (NEW)
    - `core.config (BASE_DATA_DIR, get_user_data_dir)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (cleanup_old_archives, compress_old_logs, get_component_logger, suppress_noisy_logging)` (NEW)
    - `core.schedule_management (get_schedule_time_periods)` (NEW)
    - `core.scheduler (SchedulerManager)` (NEW)
    - `core.service_utilities (load_and_localize_datetime)` (NEW)
    - `core.time_utilities (DATE_DISPLAY_WEEKDAY, DATE_ONLY, TIMESTAMP_FULL, TIMESTAMP_MINUTE, TIME_ONLY_MINUTE, format_timestamp, now_datetime_full, now_timestamp_filename, parse_date_only, parse_time_only_minute, parse_timestamp_full, parse_timestamp_minute)` (NEW)
    - `core.user_data_handlers (get_all_user_ids, get_user_data)` (NEW)
    - `tasks.task_management (are_tasks_enabled, get_task_by_id, load_active_tasks, update_task)` (NEW)
    - `user.user_context (UserContext)` (NEW)
  - **Standard Library**:
    - `calendar`
    - `datetime (datetime, timedelta)`
    - `os`
    - `random`
    - `subprocess`
    - `threading`
    - `time`
    - `typing (Any, Dict, List)`
  - **Third-party**:
    - `pytz`
    - `schedule`
- **Used by**: 
  - `core/scheduler.py`
  - `core/service.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: communication.core.channel_orchestrator, core.auto_cleanup, core.backup_manager, core.config, core.error_handling, core.logger, core.schedule_management, core.scheduler, core.service_utilities, core.time_utilities, core.user_data_handlers, tasks.task_management, user.user_context
- Removed: core/scheduler.py, core/service.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Task scheduling and job management
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/schemas.py`
- **Purpose**: Core system module for schemas
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (ValidationError, handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.message_management (get_message_categories)` (NEW)
    - `core.user_data_validation (is_valid_discord_id)` (NEW)
  - **Standard Library**:
    - `__future__ (annotations)`
    - `re`
    - `typing (Any, Dict, List, Literal, Optional)`
  - **Third-party**:
    - `pydantic (BaseModel, ConfigDict, Field, RootModel, field_validator, model_validator)`
    - `pytz`
- **Used by**: 
  - `communication/core/channel_orchestrator.py`
  - `core/message_management.py`
  - `core/user_data_handlers.py`
  - `core/user_data_manager.py`
  - `core/user_data_validation.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.message_management, core.user_data_validation
- Removed: communication/core/channel_orchestrator.py, core/message_management.py, core/user_data_handlers.py, core/user_data_manager.py, core/user_data_validation.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/service.py`
- **Purpose**: Main service orchestration and management
- **Dependencies**: 
  - **Local**:
    - `communication.core.channel_orchestrator (CommunicationManager)` (NEW)
    - `communication.message_processing.conversation_flow_manager (conversation_manager)` (NEW)
    - `core.auto_cleanup (auto_cleanup_if_needed, cleanup_data_directory, cleanup_tests_data_directory)` (NEW)
    - `core.config (LOG_MAIN_FILE, USER_INFO_DIR_PATH, get_user_data_dir, print_configuration_report, validate_and_raise_if_invalid)` (NEW)
    - `core.error_handling (FileOperationError, handle_errors)` (NEW)
    - `core.file_auditor (start_auditor, stop_auditor)` (NEW)
    - `core.file_operations (load_json_data, verify_file_access)` (NEW)
    - `core.logger (force_restart_logging, get_component_logger, setup_logging)` (NEW)
    - `core.message_management (get_recent_messages)` (NEW)
    - `core.schedule_management (get_current_day_names, get_current_time_periods_with_validation)` (NEW)
    - `core.scheduler (SchedulerManager)` (NEW)
    - `core.service_utilities (get_flags_dir)` (NEW)
    - `core.time_utilities (TIMESTAMP_FULL, now_datetime_full, now_timestamp_full, parse_timestamp_full)` (NEW)
    - `core.user_data_handlers (get_all_user_ids, get_user_data)` (NEW)
  - **Standard Library**:
    - `atexit`
    - `datetime`
    - `json`
    - `logging`
    - `os`
    - `pathlib (Path)`
    - `random`
    - `re`
    - `signal`
    - `time`
  - **Third-party**:
    - `psutil`
- **Used by**: 
  - `tasks/task_management.py`
  - `ui/dialogs/account_creator_dialog.py`

**Dependency Changes**:
- Added: communication.core.channel_orchestrator, communication.message_processing.conversation_flow_manager, core.auto_cleanup, core.config, core.error_handling, core.file_auditor, core.file_operations, core.logger, core.message_management, core.schedule_management, core.scheduler, core.service_utilities, core.time_utilities, core.user_data_handlers
- Removed: tasks/task_management.py, ui/dialogs/account_creator_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Main service orchestration and management
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/service_utilities.py`
- **Purpose**: Main service orchestration and management
- **Dependencies**: 
  - **Local**:
    - `core.config (SCHEDULER_INTERVAL)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.file_auditor (record_created)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.time_utilities (TIMESTAMP_MINUTE, now_timestamp_filename, now_timestamp_full, parse_timestamp_minute)` (NEW)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `socket`
    - `time`
  - **Third-party**:
    - `psutil`
    - `pytz`
- **Used by**: 
  - `communication/core/channel_orchestrator.py`
  - `core/error_handling.py`
  - `core/headless_service.py`
  - `core/schedule_management.py`
  - `core/scheduler.py`
  - `core/service.py`
  - `ui/dialogs/process_watcher_dialog.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.file_auditor, core.logger, core.time_utilities
- Removed: communication/core/channel_orchestrator.py, core/error_handling.py, core/headless_service.py, core/schedule_management.py, core/scheduler.py, core/service.py, ui/dialogs/process_watcher_dialog.py, ui/ui_app_qt.py

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
  - `core/user_data_handlers.py`
  - `tasks/task_management.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.file_operations, core.logger, core.time_utilities
- Removed: communication/command_handlers/notebook_handler.py, communication/message_processing/command_parser.py, communication/message_processing/conversation_flow_manager.py, core/user_data_handlers.py, tasks/task_management.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/time_utilities.py`
- **Purpose**: Core system module for time_utilities
- **Dependencies**: 
  - **Standard Library**:
    - `__future__ (annotations)`
    - `datetime`
    - `typing (Iterable, Literal)`
- **Used by**: 
  - `ai/chatbot.py`
  - `ai/context_builder.py`
  - `ai/conversation_history.py`
  - `communication/command_handlers/checkin_handler.py`
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
  - `core/error_handling.py`
  - `core/file_operations.py`
  - `core/message_management.py`
  - `core/response_tracking.py`
  - `core/schedule_management.py`
  - `core/schedule_utilities.py`
  - `core/scheduler.py`
  - `core/service.py`
  - `core/service_utilities.py`
  - `core/tags.py`
  - `core/user_data_handlers.py`
  - `core/user_data_manager.py`
  - `core/user_data_validation.py`
  - `tasks/task_management.py`
  - `ui/dialogs/message_editor_dialog.py`
  - `ui/dialogs/process_watcher_dialog.py`
  - `ui/dialogs/schedule_editor_dialog.py`
  - `ui/dialogs/user_profile_dialog.py`
  - `ui/generate_ui_files.py`
  - `ui/ui_app_qt.py`
  - `user/context_manager.py`

**Dependency Changes**:
- Removed: ai/chatbot.py, ai/context_builder.py, ai/conversation_history.py, communication/command_handlers/checkin_handler.py, communication/command_handlers/notebook_handler.py, communication/command_handlers/task_handler.py, communication/core/channel_monitor.py, communication/core/retry_manager.py, communication/core/welcome_manager.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/interaction_manager.py, core/auto_cleanup.py, core/backup_manager.py, core/checkin_analytics.py, core/error_handling.py, core/file_operations.py, core/message_management.py, core/response_tracking.py, core/schedule_management.py, core/schedule_utilities.py, core/scheduler.py, core/service.py, core/service_utilities.py, core/tags.py, core/user_data_handlers.py, core/user_data_manager.py, core/user_data_validation.py, tasks/task_management.py, ui/dialogs/process_watcher_dialog.py, ui/dialogs/schedule_editor_dialog.py, ui/generate_ui_files.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/ui_management.py`
- **Purpose**: UI management and widget utilities
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.schedule_management (get_schedule_time_periods)` (NEW)
    - `ui.widgets.period_row_widget (PeriodRowWidget)` (NEW)
- **Used by**: 
  - `ui/dialogs/schedule_editor_dialog.py`
  - `ui/widgets/checkin_settings_widget.py`
  - `ui/widgets/task_settings_widget.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.schedule_management, ui.widgets.period_row_widget
- Removed: ui/dialogs/schedule_editor_dialog.py, ui/widgets/checkin_settings_widget.py, ui/widgets/task_settings_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: UI management and widget utilities
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/user_data_handlers.py`
- **Purpose**: User data handlers with caching and validation
- **Dependencies**: 
  - **Local**:
    - `core.config (BASE_DATA_DIR, USER_INFO_DIR_PATH, ensure_user_directory, get_user_data_dir, get_user_file_path)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.file_locking (safe_json_read)` (NEW)
    - `core.file_operations (determine_file_path, load_json_data, save_json_data)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.message_management (ensure_user_message_files)` (NEW)
    - `core.schemas (validate_account_dict, validate_preferences_dict, validate_schedules_dict)` (NEW)
    - `core.tags (load_user_tags, save_user_tags)` (NEW)
    - `core.time_utilities (now_timestamp_full)` (NEW)
    - `core.user_data_manager (UserDataManager, update_user_index)` (NEW)
    - `core.user_data_validation (validate_new_user_data, validate_user_update)` (NEW)
  - **Standard Library**:
    - `copy`
    - `datetime`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `time`
    - `traceback`
    - `typing (Any, Dict, List, Optional, Union)`
    - `uuid`
  - **Third-party**:
    - `pytz`
- **Used by**: 
  - `ai/chatbot.py`
  - `ai/context_builder.py`
  - `communication/command_handlers/account_handler.py`
  - `communication/command_handlers/analytics_handler.py`
  - `communication/command_handlers/interaction_handlers.py`
  - `communication/command_handlers/profile_handler.py`
  - `communication/command_handlers/schedule_handler.py`
  - `communication/command_handlers/task_handler.py`
  - `communication/communication_channels/discord/account_flow_handler.py`
  - `communication/communication_channels/discord/bot.py`
  - `communication/communication_channels/discord/checkin_view.py`
  - `communication/communication_channels/discord/event_handler.py`
  - `communication/communication_channels/discord/task_reminder_view.py`
  - `communication/communication_channels/discord/webhook_handler.py`
  - `communication/core/channel_orchestrator.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `communication/message_processing/interaction_manager.py`
  - `core/auto_cleanup.py`
  - `core/backup_manager.py`
  - `core/checkin_analytics.py`
  - `core/checkin_dynamic_manager.py`
  - `core/response_tracking.py`
  - `core/schedule_management.py`
  - `core/scheduler.py`
  - `core/service.py`
  - `core/user_data_manager.py`
  - `core/user_data_validation.py`
  - `tasks/task_management.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/category_management_dialog.py`
  - `ui/dialogs/channel_management_dialog.py`
  - `ui/dialogs/checkin_management_dialog.py`
  - `ui/dialogs/task_management_dialog.py`
  - `ui/dialogs/user_analytics_dialog.py`
  - `ui/dialogs/user_profile_dialog.py`
  - `ui/ui_app_qt.py`
  - `ui/widgets/channel_selection_widget.py`
  - `ui/widgets/checkin_settings_widget.py`
  - `ui/widgets/dynamic_list_container.py`
  - `ui/widgets/tag_widget.py`
  - `ui/widgets/task_settings_widget.py`
  - `user/context_manager.py`
  - `user/user_context.py`
  - `user/user_preferences.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.file_locking, core.file_operations, core.logger, core.message_management, core.schemas, core.tags, core.time_utilities, core.user_data_manager, core.user_data_validation
- Removed: ai/chatbot.py, ai/context_builder.py, communication/command_handlers/account_handler.py, communication/command_handlers/analytics_handler.py, communication/command_handlers/interaction_handlers.py, communication/command_handlers/profile_handler.py, communication/command_handlers/schedule_handler.py, communication/command_handlers/task_handler.py, communication/communication_channels/discord/account_flow_handler.py, communication/communication_channels/discord/bot.py, communication/communication_channels/discord/checkin_view.py, communication/communication_channels/discord/event_handler.py, communication/communication_channels/discord/task_reminder_view.py, communication/communication_channels/discord/webhook_handler.py, communication/core/channel_orchestrator.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/interaction_manager.py, core/auto_cleanup.py, core/backup_manager.py, core/checkin_analytics.py, core/checkin_dynamic_manager.py, core/response_tracking.py, core/schedule_management.py, core/scheduler.py, core/service.py, core/user_data_manager.py, core/user_data_validation.py, tasks/task_management.py, ui/dialogs/account_creator_dialog.py, ui/dialogs/category_management_dialog.py, ui/dialogs/channel_management_dialog.py, ui/dialogs/checkin_management_dialog.py, ui/dialogs/task_management_dialog.py, ui/dialogs/user_analytics_dialog.py, ui/dialogs/user_profile_dialog.py, ui/ui_app_qt.py, ui/widgets/channel_selection_widget.py, ui/widgets/checkin_settings_widget.py, ui/widgets/dynamic_list_container.py, ui/widgets/tag_widget.py, ui/widgets/task_settings_widget.py, user/context_manager.py, user/user_context.py, user/user_preferences.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: User data handlers - provides centralized access to user data with caching and validation
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/user_data_manager.py`
- **Purpose**: Enhanced user data management with references
- **Dependencies**: 
  - **Local**:
    - `core.config (BASE_DATA_DIR, get_backups_dir, get_user_data_dir, get_user_file_path)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.file_locking (safe_json_read, safe_json_write)` (NEW)
    - `core.file_operations (get_user_data_dir, get_user_file_path, load_json_data)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.message_management (ensure_user_message_files)` (NEW)
    - `core.response_tracking (get_recent_checkins, get_recent_responses)` (NEW)
    - `core.schemas (validate_messages_file_dict)` (NEW)
    - `core.time_utilities (now_timestamp_filename, now_timestamp_full)` (NEW)
    - `core.user_data_handlers (USER_DATA_LOADERS, get_all_user_ids, get_user_categories, get_user_data)` (NEW)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `time`
    - `typing (Any, Dict, List, Optional)`
    - `zipfile`
- **Used by**: 
  - `communication/command_handlers/account_handler.py`
  - `core/file_operations.py`
  - `core/message_management.py`
  - `core/user_data_handlers.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.file_locking, core.file_operations, core.logger, core.message_management, core.response_tracking, core.schemas, core.time_utilities, core.user_data_handlers
- Removed: communication/command_handlers/account_handler.py, core/file_operations.py, core/message_management.py, core/user_data_handlers.py, ui/dialogs/account_creator_dialog.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Enhanced user data management with references and indexing
<!-- MANUAL_ENHANCEMENT_END -->

#### `core/user_data_validation.py`
- **Purpose**: User data validation and integrity checks
- **Dependencies**: 
  - **Local**:
    - `core.config (get_user_data_dir)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.message_management (get_message_categories)` (NEW)
    - `core.schemas (validate_account_dict, validate_preferences_dict, validate_schedules_dict)` (NEW)
    - `core.time_utilities (DATE_ONLY, TIME_ONLY_MINUTE, parse_date_only, parse_time_only_minute)` (NEW)
    - `core.user_data_handlers (get_user_data)` (NEW)
  - **Standard Library**:
    - `datetime`
    - `os`
    - `re`
    - `time`
    - `typing (Any, Dict, List, Optional, Tuple)`
- **Used by**: 
  - `core/schemas.py`
  - `core/user_data_handlers.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/channel_management_dialog.py`
  - `ui/dialogs/checkin_management_dialog.py`
  - `ui/dialogs/schedule_editor_dialog.py`
  - `ui/dialogs/task_management_dialog.py`
  - `ui/dialogs/user_profile_dialog.py`
  - `ui/ui_app_qt.py`
  - `ui/widgets/category_selection_widget.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger, core.message_management, core.schemas, core.time_utilities, core.user_data_handlers
- Removed: core/schemas.py, core/user_data_handlers.py, ui/dialogs/account_creator_dialog.py, ui/dialogs/channel_management_dialog.py, ui/dialogs/checkin_management_dialog.py, ui/dialogs/schedule_editor_dialog.py, ui/dialogs/task_management_dialog.py, ui/dialogs/user_profile_dialog.py, ui/ui_app_qt.py, ui/widgets/category_selection_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: User data validation - validates user input and data integrity
<!-- MANUAL_ENHANCEMENT_END -->

### `root/` - Project root files

#### `create_backup.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.backup_manager (BackupManager)` (NEW)
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.backup_manager

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `run_headless_service.py`
- **Purpose**: Main entry point for the application
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.headless_service (HeadlessServiceManager)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
  - **Standard Library**:
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling, core.headless_service, core.logger

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

### `tasks/` - Task management

#### `tasks/__init__.py`
- **Purpose**: Task management and scheduling
- **Dependencies**: 
  - **Third-party**:
    - `task_management (TaskManagementError, add_user_task_tag, are_tasks_enabled, cleanup_task_reminders, complete_task, create_task, delete_task, ensure_task_directory, get_task_by_id, get_tasks_due_soon, get_user_task_stats, load_active_tasks, load_completed_tasks, remove_user_task_tag, restore_task, save_active_tasks, save_completed_tasks, schedule_task_reminders, setup_default_task_tags, update_task)`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tasks/task_management.py`
- **Purpose**: Task management and scheduling
- **Dependencies**: 
  - **Local**:
    - `core.config (get_user_data_dir)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.file_operations (load_json_data, save_json_data)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.service (get_scheduler_manager)` (NEW)
    - `core.tags (add_user_tag, get_user_tags, remove_user_tag)` (NEW)
    - `core.time_utilities (DATE_ONLY, format_timestamp, now_datetime_full, now_timestamp_full, parse_date_only, parse_timestamp_full)` (NEW)
    - `core.user_data_handlers (get_user_data)` (NEW)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `pathlib (Path)`
    - `typing (Any, Dict, List, Optional)`
    - `uuid`
- **Used by**: 
  - `ai/chatbot.py`
  - `communication/command_handlers/analytics_handler.py`
  - `communication/command_handlers/interaction_handlers.py`
  - `communication/command_handlers/profile_handler.py`
  - `communication/command_handlers/task_handler.py`
  - `communication/core/channel_orchestrator.py`
  - `communication/message_processing/conversation_flow_manager.py`
  - `communication/message_processing/interaction_manager.py`
  - `core/scheduler.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/task_crud_dialog.py`
  - `ui/dialogs/task_edit_dialog.py`
  - `ui/dialogs/task_management_dialog.py`
  - `ui/ui_app_qt.py`
  - `ui/widgets/tag_widget.py`
  - `ui/widgets/task_settings_widget.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.file_operations, core.logger, core.service, core.tags, core.time_utilities, core.user_data_handlers
- Removed: ai/chatbot.py, communication/command_handlers/analytics_handler.py, communication/command_handlers/interaction_handlers.py, communication/command_handlers/profile_handler.py, communication/command_handlers/task_handler.py, communication/core/channel_orchestrator.py, communication/message_processing/conversation_flow_manager.py, communication/message_processing/interaction_manager.py, core/scheduler.py, ui/dialogs/account_creator_dialog.py, ui/dialogs/task_crud_dialog.py, ui/dialogs/task_edit_dialog.py, ui/dialogs/task_management_dialog.py, ui/ui_app_qt.py, ui/widgets/tag_widget.py, ui/widgets/task_settings_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Comprehensive task management system for user task CRUD operations, scheduling, and data persistence

**Key Functions**:
- `ensure_task_directory()`: Creates and initializes task directory structure for users
- `load_active_tasks()` / `save_active_tasks()`: Active task data management
- `load_completed_tasks()` / `save_completed_tasks()`: Completed task data management
- `create_task()`: Creates new tasks with full metadata (title, description, due dates, priority, category)
- `update_task()`: Updates existing task properties
- `complete_task()`: Marks tasks as completed and moves to completed tasks
- `delete_task()`: Removes tasks from active list
- `get_task_by_id()`: Retrieves specific task by ID
- `get_tasks_due_soon()`: Finds tasks due within specified timeframe
- `are_tasks_enabled()`: Checks if task features are enabled for user
- `get_user_task_stats()`: Provides task completion statistics

**Special Considerations**:
- **Data Persistence**: Uses JSON files for task storage (active_tasks.json, completed_tasks.json, task_schedules.json)
- **User Isolation**: All task data is user-specific with proper directory structure
- **Error Handling**: Comprehensive error handling with logging and graceful fallbacks
- **Task Metadata**: Supports rich task data including due dates, priorities, categories, and reminders
- **Directory Management**: Automatically creates necessary directory structure and initializes files
- **Validation**: Input validation for user IDs and task data integrity

**Usage**: Core task management functionality used by UI components and communication channels for task operations.
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
    - `core.config (get_user_data_dir)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.file_operations (create_user_files)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.service (get_scheduler_manager)` (NEW)
    - `core.user_data_handlers (get_user_data, get_user_id_by_identifier)` (NEW)
    - `core.user_data_manager (update_user_index)` (NEW)
    - `core.user_data_validation (is_valid_discord_id, is_valid_email, is_valid_phone, validate_schedule_periods)` (NEW)
    - `tasks.task_management (add_user_task_tag, setup_default_task_tags)` (NEW)
    - `ui.dialogs.user_profile_dialog (open_personalization_dialog)` (NEW)
    - `ui.generated.account_creator_dialog_pyqt (Ui_Dialog_create_account)` (NEW)
    - `ui.widgets.category_selection_widget (CategorySelectionWidget)` (NEW)
    - `ui.widgets.channel_selection_widget (ChannelSelectionWidget)` (NEW)
    - `ui.widgets.checkin_settings_widget (CheckinSettingsWidget)` (NEW)
    - `ui.widgets.task_settings_widget (TaskSettingsWidget)` (NEW)
  - **Standard Library**:
    - `pathlib (Path)`
    - `time`
    - `typing (Any, Dict)`
    - `uuid`
    - `warnings`
  - **Third-party**:
    - `PySide6.QtCore (Qt, Signal)`
    - `PySide6.QtWidgets (QDialog, QDialogButtonBox, QMessageBox, QSizePolicy)`
- **Used by**: 
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.file_operations, core.logger, core.service, core.user_data_handlers, core.user_data_manager, core.user_data_validation, tasks.task_management, ui.dialogs.user_profile_dialog, ui.generated.account_creator_dialog_pyqt, ui.widgets.category_selection_widget, ui.widgets.channel_selection_widget, ui.widgets.checkin_settings_widget, ui.widgets.task_settings_widget
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Account creation dialog
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
**Enhanced Purpose**: Qt-based dialog for admin panel functionality with placeholder implementation for future admin features

**Key Functions**:
- `__init__()`: Initializes dialog with modal behavior and window title
- `setup_ui()`: Creates basic UI layout with title and placeholder content
- `get_admin_data()`: Placeholder method for retrieving admin panel data
- `set_admin_data()`: Placeholder method for setting admin panel data

**Special Considerations**:
- **Placeholder Implementation**: Currently contains TODO comments for future admin panel widget integration
- **Modal Dialog**: Uses modal behavior for proper dialog interaction
- **Basic Layout**: Simple vertical layout with title and placeholder widget
- **Future Integration**: Designed to integrate with AdminPanelWidget when implemented
- **Minimal Dependencies**: Only uses basic Qt widgets for core dialog functionality

**Usage**: Currently unused but designed as foundation for future admin panel functionality in the MHM system.
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/category_management_dialog.py`
- **Purpose**: Dialog component for category management dialog
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.schedule_management (clear_schedule_periods_cache)` (NEW)
    - `core.user_data_handlers (get_user_data, update_user_account, update_user_preferences)` (NEW)
    - `ui.generated.category_management_dialog_pyqt (Ui_Dialog_category_management)` (NEW)
    - `ui.widgets.category_selection_widget (CategorySelectionWidget)` (NEW)
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QDialog, QMessageBox)`
- **Used by**: 
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.schedule_management, core.user_data_handlers, ui.generated.category_management_dialog_pyqt, ui.widgets.category_selection_widget
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Category management dialog
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/channel_management_dialog.py`
- **Purpose**: Dialog component for channel management dialog
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.user_data_handlers (get_user_data, update_channel_preferences, update_user_account)` (NEW)
    - `core.user_data_validation (is_valid_email)` (NEW)
    - `ui.generated.channel_management_dialog_pyqt (Ui_Dialog)` (NEW)
    - `ui.widgets.channel_selection_widget (ChannelSelectionWidget)` (NEW)
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QDialog, QMessageBox)`
- **Used by**: 
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.user_data_handlers, core.user_data_validation, ui.generated.channel_management_dialog_pyqt, ui.widgets.channel_selection_widget
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Channel management dialog
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/checkin_management_dialog.py`
- **Purpose**: Dialog component for checkin management dialog
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.schedule_management (clear_schedule_periods_cache, set_schedule_periods)` (NEW)
    - `core.user_data_handlers (get_user_data, update_user_account, update_user_preferences)` (NEW)
    - `core.user_data_validation (validate_schedule_periods)` (NEW)
    - `ui.generated.checkin_management_dialog_pyqt (Ui_Dialog_checkin_management)` (NEW)
    - `ui.widgets.checkin_settings_widget (CheckinSettingsWidget)` (NEW)
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QDialog, QMessageBox, QWidget)`
- **Used by**: 
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.schedule_management, core.user_data_handlers, core.user_data_validation, ui.generated.checkin_management_dialog_pyqt, ui.widgets.checkin_settings_widget
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Check-in management dialog
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/message_editor_dialog.py`
- **Purpose**: Dialog component for message editor dialog
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.message_management (add_message, delete_message, edit_message, load_user_messages)` (NEW)
    - `core.time_utilities (now_timestamp_full)` (NEW)
    - `ui.generated.message_editor_dialog_pyqt (Ui_Dialog_message_editor)` (NEW)
  - **Standard Library**:
    - `uuid`
  - **Third-party**:
    - `PySide6.QtCore (Qt, Signal)`
    - `PySide6.QtGui (QFont)`
    - `PySide6.QtWidgets (QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.message_management, core.time_utilities, ui.generated.message_editor_dialog_pyqt
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/ui_app_qt.py

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
    - `core.schedule_management (clear_schedule_periods_cache, set_schedule_periods)` (NEW)
    - `core.time_utilities (now_timestamp_filename, now_timestamp_full)` (NEW)
    - `core.ui_management (collect_period_data_from_widgets, load_period_widgets_for_category)` (NEW)
    - `core.user_data_validation (_shared__title_case, validate_schedule_periods)` (NEW)
    - `ui.generated.schedule_editor_dialog_pyqt (Ui_Dialog_edit_schedule)` (NEW)
    - `ui.widgets.period_row_widget (PeriodRowWidget)` (NEW)
  - **Standard Library**:
    - `json`
    - `os`
    - `pathlib (Path)`
    - `re`
    - `typing (Any, Callable, Dict, Optional)`
  - **Third-party**:
    - `PySide6.QtWidgets (QDialog, QMessageBox)`
- **Used by**: 
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger, core.schedule_management, core.time_utilities, core.ui_management, core.user_data_validation, ui.generated.schedule_editor_dialog_pyqt, ui.widgets.period_row_widget
- Removed: PySide6.QtWidgets, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Schedule editor dialog
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/task_completion_dialog.py`
- **Purpose**: Dialog component for task completion dialog
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `ui.generated.task_completion_dialog_pyqt (Ui_Dialog_task_completion)` (NEW)
  - **Third-party**:
    - `PySide6.QtCore (QDate, QTime)`
    - `PySide6.QtWidgets (QButtonGroup, QDialog)`
- **Used by**: 
  - `ui/dialogs/task_crud_dialog.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, ui.generated.task_completion_dialog_pyqt
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
    - `tasks.task_management (complete_task, delete_task, get_task_by_id, get_tasks_due_soon, get_user_task_stats, load_active_tasks, load_completed_tasks, restore_task)` (NEW)
    - `ui.dialogs.task_completion_dialog (TaskCompletionDialog)` (NEW)
    - `ui.dialogs.task_edit_dialog (TaskEditDialog)` (NEW)
    - `ui.generated.task_crud_dialog_pyqt (Ui_Dialog_task_crud)` (NEW)
  - **Third-party**:
    - `PySide6.QtCore (Qt)`
    - `PySide6.QtWidgets (QDialog, QHeaderView, QMessageBox, QTableWidgetItem)`
- **Used by**: 
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, tasks.task_management, ui.dialogs.task_completion_dialog, ui.dialogs.task_edit_dialog, ui.generated.task_crud_dialog_pyqt
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
    - `tasks.task_management (create_task, update_task)` (NEW)
    - `ui.generated.task_edit_dialog_pyqt (Ui_Dialog_task_edit)` (NEW)
    - `ui.widgets.tag_widget (TagWidget)` (NEW)
  - **Third-party**:
    - `PySide6.QtCore (QDate, QTime)`
    - `PySide6.QtWidgets (QButtonGroup, QComboBox, QDateEdit, QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QWidget)`
- **Used by**: 
  - `ui/dialogs/task_crud_dialog.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, tasks.task_management, ui.generated.task_edit_dialog_pyqt, ui.widgets.tag_widget
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/dialogs/task_crud_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/task_management_dialog.py`
- **Purpose**: Dialog component for task management dialog
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.schedule_management (clear_schedule_periods_cache, set_schedule_periods)` (NEW)
    - `core.user_data_handlers (get_user_data, update_user_account)` (NEW)
    - `core.user_data_validation (validate_schedule_periods)` (NEW)
    - `tasks.task_management (setup_default_task_tags)` (NEW)
    - `ui.generated.task_management_dialog_pyqt (Ui_Dialog_task_management)` (NEW)
    - `ui.widgets.task_settings_widget (TaskSettingsWidget)` (NEW)
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QDialog, QMessageBox, QWidget)`
- **Used by**: 
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.schedule_management, core.user_data_handlers, core.user_data_validation, tasks.task_management, ui.generated.task_management_dialog_pyqt, ui.widgets.task_settings_widget
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Task management dialog
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/user_analytics_dialog.py`
- **Purpose**: Dialog component for user analytics dialog
- **Dependencies**: 
  - **Local**:
    - `core.checkin_analytics (CheckinAnalytics)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.response_tracking (get_checkins_by_days)` (NEW)
    - `core.user_data_handlers (get_user_data)` (NEW)
    - `ui.generated.user_analytics_dialog_pyqt (Ui_Dialog_user_analytics)` (NEW)
  - **Standard Library**:
    - `os`
  - **Third-party**:
    - `PySide6.QtCore (QThread, Qt, Signal)`
    - `PySide6.QtGui (QBrush, QColor, QFont, QPainter, QPalette, QPen)`
    - `PySide6.QtWidgets (QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QTabWidget, QTextEdit, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.checkin_analytics, core.error_handling, core.logger, core.response_tracking, core.user_data_handlers, ui.generated.user_analytics_dialog_pyqt
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/user_profile_dialog.py`
- **Purpose**: Dialog component for user profile dialog
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.time_utilities (now_timestamp_full)` (NEW)
    - `core.user_data_handlers (get_predefined_options, update_user_context)` (NEW)
    - `core.user_data_validation (validate_personalization_data)` (NEW)
    - `ui.generated.user_profile_management_dialog_pyqt (Ui_Dialog_user_profile)` (NEW)
    - `ui.widgets.dynamic_list_container (DynamicListContainer)` (NEW)
    - `ui.widgets.user_profile_settings_widget (UserProfileSettingsWidget)` (NEW)
  - **Standard Library**:
    - `re`
    - `typing (Any, Callable, Dict, Optional)`
  - **Third-party**:
    - `PySide6.QtCore (Qt, Signal)`
    - `PySide6.QtWidgets (QCheckBox, QComboBox, QDialog, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTextEdit, QVBoxLayout)`
- **Used by**: 
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.time_utilities, core.user_data_handlers, core.user_data_validation, ui.generated.user_profile_management_dialog_pyqt, ui.widgets.dynamic_list_container, ui.widgets.user_profile_settings_widget
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/dialogs/account_creator_dialog.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: User profile dialog - manages user profiles
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generate_ui_files.py`
- **Purpose**: User interface component for generate_ui_files
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.time_utilities (now_timestamp_full)` (NEW)
  - **Standard Library**:
    - `datetime`
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

#### `ui/ui_app_qt.py`
- **Purpose**: Main UI application (PyQt6)
- **Dependencies**: 
  - **Local**:
    - `communication.core.channel_orchestrator (CommunicationManager)` (NEW)
    - `core.auto_cleanup (calculate_cache_size, find_pyc_files, find_pycache_dirs, get_cleanup_status, perform_cleanup, update_cleanup_timestamp)` (NEW)
    - `core.config (AI_TIMEOUT_SECONDS, BASE_DATA_DIR, DISCORD_BOT_TOKEN, EMAIL_IMAP_SERVER, EMAIL_SMTP_PASSWORD, EMAIL_SMTP_SERVER, EMAIL_SMTP_USERNAME, LM_STUDIO_BASE_URL, LOG_LEVEL, LOG_MAIN_FILE, SCHEDULER_INTERVAL, core.config, validate_all_configuration)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, get_verbose_mode, setup_logging, toggle_verbose_logging)` (NEW)
    - `core.scheduler (SchedulerManager, run_category_scheduler_standalone, run_full_scheduler_standalone, run_user_scheduler_standalone)` (NEW)
    - `core.service_utilities (get_flags_dir)` (NEW)
    - `core.time_utilities (TIMESTAMP_FULL, now_datetime_full, now_timestamp_full, parse_timestamp_full)` (NEW)
    - `core.user_data_handlers (get_all_user_ids, get_user_data, save_user_data, update_user_context)` (NEW)
    - `core.user_data_manager (rebuild_user_index)` (NEW)
    - `core.user_data_validation (_shared__title_case)` (NEW)
    - `tasks.task_management (are_tasks_enabled, load_active_tasks)` (NEW)
    - `ui.dialogs.account_creator_dialog (AccountCreatorDialog)` (NEW)
    - `ui.dialogs.category_management_dialog (CategoryManagementDialog)` (NEW)
    - `ui.dialogs.channel_management_dialog (ChannelManagementDialog)` (NEW)
    - `ui.dialogs.checkin_management_dialog (CheckinManagementDialog)` (NEW)
    - `ui.dialogs.message_editor_dialog (open_message_editor_dialog)` (NEW)
    - `ui.dialogs.process_watcher_dialog (ProcessWatcherDialog)` (NEW)
    - `ui.dialogs.schedule_editor_dialog (open_schedule_editor)` (NEW)
    - `ui.dialogs.task_crud_dialog (TaskCrudDialog)` (NEW)
    - `ui.dialogs.task_management_dialog (TaskManagementDialog)` (NEW)
    - `ui.dialogs.user_analytics_dialog (open_user_analytics_dialog)` (NEW)
    - `ui.dialogs.user_profile_dialog (UserProfileDialog)` (NEW)
    - `ui.generated.admin_panel_pyqt (Ui_ui_app_mainwindow)` (NEW)
    - `user.user_context (UserContext)` (NEW)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `re`
    - `subprocess`
    - `sys`
    - `threading`
    - `time`
    - `webbrowser`
  - **Third-party**:
    - `PySide6.QtCore (QTimer)`
    - `PySide6.QtGui (QFont)`
    - `PySide6.QtWidgets (QApplication, QDialog, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QScrollArea, QTabWidget, QTextEdit, QVBoxLayout, QWidget)`
    - `psutil`
    - `run_mhm (prepare_launch_environment, resolve_python_interpreter)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: communication.core.channel_orchestrator, core.auto_cleanup, core.config, core.error_handling, core.logger, core.scheduler, core.service_utilities, core.time_utilities, core.user_data_handlers, core.user_data_manager, core.user_data_validation, tasks.task_management, ui.dialogs.account_creator_dialog, ui.dialogs.category_management_dialog, ui.dialogs.channel_management_dialog, ui.dialogs.checkin_management_dialog, ui.dialogs.message_editor_dialog, ui.dialogs.process_watcher_dialog, ui.dialogs.schedule_editor_dialog, ui.dialogs.task_crud_dialog, ui.dialogs.task_management_dialog, ui.dialogs.user_analytics_dialog, ui.dialogs.user_profile_dialog, ui.generated.admin_panel_pyqt, user.user_context
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Main UI application (PyQt6)
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
    - `core.user_data_validation (_shared__title_case)` (NEW)
    - `ui.generated.category_selection_widget_pyqt (Ui_Form_category_selection_widget)` (NEW)
  - **Third-party**:
    - `PySide6.QtWidgets (QWidget)`
- **Used by**: 
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/category_management_dialog.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.user_data_validation, ui.generated.category_selection_widget_pyqt
- Removed: PySide6.QtWidgets, ui/dialogs/account_creator_dialog.py, ui/dialogs/category_management_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Category selection widget
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/channel_selection_widget.py`
- **Purpose**: UI widget component for channel selection widget
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.user_data_handlers (get_timezone_options)` (NEW)
    - `ui.generated.channel_selection_widget_pyqt (Ui_Form_channel_selection)` (NEW)
  - **Third-party**:
    - `PySide6.QtWidgets (QWidget)`
- **Used by**: 
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/channel_management_dialog.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.user_data_handlers, ui.generated.channel_selection_widget_pyqt
- Removed: PySide6.QtWidgets, ui/dialogs/account_creator_dialog.py, ui/dialogs/channel_management_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Channel selection widget
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/checkin_settings_widget.py`
- **Purpose**: UI widget component for checkin settings widget
- **Dependencies**: 
  - **Local**:
    - `core.checkin_dynamic_manager (dynamic_checkin_manager)` (NEW)
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.ui_management (collect_period_data_from_widgets, load_period_widgets_for_category)` (NEW)
    - `core.user_data_handlers (get_user_data)` (NEW)
    - `ui.generated.checkin_settings_widget_pyqt (Ui_Form_checkin_settings)` (NEW)
    - `ui.widgets.period_row_widget (PeriodRowWidget)` (NEW)
  - **Standard Library**:
    - `re`
  - **Third-party**:
    - `PySide6.QtCore (QTimer, Qt)`
    - `PySide6.QtWidgets (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTextEdit, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/checkin_management_dialog.py`

**Dependency Changes**:
- Added: core.checkin_dynamic_manager, core.error_handling, core.logger, core.ui_management, core.user_data_handlers, ui.generated.checkin_settings_widget_pyqt, ui.widgets.period_row_widget
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/dialogs/account_creator_dialog.py, ui/dialogs/checkin_management_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Check-in settings widget
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/dynamic_list_container.py`
- **Purpose**: UI widget component for dynamic list container
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.user_data_handlers (get_predefined_options)` (NEW)
    - `ui.widgets.dynamic_list_field (DynamicListField)` (NEW)
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QGridLayout, QMessageBox, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/dialogs/user_profile_dialog.py`
  - `ui/widgets/dynamic_list_field.py`
  - `ui/widgets/user_profile_settings_widget.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.user_data_handlers, ui.widgets.dynamic_list_field
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/dialogs/user_profile_dialog.py, ui/widgets/dynamic_list_field.py, ui/widgets/user_profile_settings_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Dynamic list container - UI component for managing dynamic lists
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/dynamic_list_field.py`
- **Purpose**: UI widget component for dynamic list field
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `ui.generated.dynamic_list_field_template_pyqt (Ui_Form_dynamic_list_field_template)` (NEW)
    - `ui.widgets.dynamic_list_container (DynamicListContainer)` (NEW)
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QSizePolicy, QWidget)`
- **Used by**: 
  - `ui/widgets/dynamic_list_container.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, ui.generated.dynamic_list_field_template_pyqt, ui.widgets.dynamic_list_container
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/widgets/dynamic_list_container.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Dynamic list field - UI component for individual list items
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/period_row_widget.py`
- **Purpose**: UI widget component for period row widget
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.schedule_management (get_period_data__time_12h_display_to_24h, get_period_data__time_24h_to_12h_display)` (NEW)
    - `ui.generated.period_row_template_pyqt (Ui_Form_period_row_template)` (NEW)
  - **Standard Library**:
    - `typing (Any, Dict, List, Optional)`
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QButtonGroup, QWidget)`
- **Used by**: 
  - `core/ui_management.py`
  - `ui/dialogs/schedule_editor_dialog.py`
  - `ui/widgets/checkin_settings_widget.py`
  - `ui/widgets/task_settings_widget.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.schedule_management, ui.generated.period_row_template_pyqt
- Removed: PySide6.QtCore, PySide6.QtWidgets, core/ui_management.py, ui/dialogs/schedule_editor_dialog.py, ui/widgets/checkin_settings_widget.py, ui/widgets/task_settings_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Period row widget - UI component for managing schedule periods
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/tag_widget.py`
- **Purpose**: UI widget component for tag widget
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.user_data_handlers (get_user_data)` (NEW)
    - `tasks.task_management (add_user_task_tag, remove_user_task_tag)` (NEW)
    - `ui.generated.tag_widget_pyqt (Ui_Widget_tag)` (NEW)
  - **Third-party**:
    - `PySide6.QtCore (Qt, Signal)`
    - `PySide6.QtWidgets (QInputDialog, QListWidgetItem, QMessageBox, QWidget)`
- **Used by**: 
  - `ui/dialogs/task_edit_dialog.py`
  - `ui/widgets/task_settings_widget.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.user_data_handlers, tasks.task_management, ui.generated.tag_widget_pyqt
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/dialogs/task_edit_dialog.py, ui/widgets/task_settings_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/task_settings_widget.py`
- **Purpose**: UI widget component for task settings widget
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `core.ui_management (collect_period_data_from_widgets, load_period_widgets_for_category)` (NEW)
    - `core.user_data_handlers (get_user_data, update_user_preferences)` (NEW)
    - `tasks.task_management (get_user_task_stats)` (NEW)
    - `ui.generated.task_settings_widget_pyqt (Ui_Form_task_settings)` (NEW)
    - `ui.widgets.period_row_widget (PeriodRowWidget)` (NEW)
    - `ui.widgets.tag_widget (TagWidget)` (NEW)
  - **Third-party**:
    - `PySide6.QtWidgets (QMessageBox, QWidget)`
- **Used by**: 
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/task_management_dialog.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.ui_management, core.user_data_handlers, tasks.task_management, ui.generated.task_settings_widget_pyqt, ui.widgets.period_row_widget, ui.widgets.tag_widget
- Removed: PySide6.QtWidgets, ui/dialogs/account_creator_dialog.py, ui/dialogs/task_management_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Task settings widget - UI component for configuring tasks
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/user_profile_settings_widget.py`
- **Purpose**: UI widget component for user profile settings widget
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger, setup_logging)` (NEW)
    - `ui.generated.user_profile_settings_widget_pyqt (Ui_Form_user_profile_settings)` (NEW)
    - `ui.widgets.dynamic_list_container (DynamicListContainer)` (NEW)
  - **Standard Library**:
    - `typing (Any, Dict, Optional)`
  - **Third-party**:
    - `PySide6.QtCore (QDate, Qt)`
    - `PySide6.QtWidgets (QLabel, QLineEdit, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/dialogs/user_profile_dialog.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, ui.generated.user_profile_settings_widget_pyqt, ui.widgets.dynamic_list_container
- Removed: PySide6.QtCore, PySide6.QtWidgets, ui/dialogs/user_profile_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: User profile settings widget
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
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.message_management (get_recent_messages)` (NEW)
    - `core.response_tracking (get_recent_chat_interactions, get_recent_checkins)` (NEW)
    - `core.schedule_utilities (get_active_schedules)` (NEW)
    - `core.time_utilities (now_timestamp_full)` (NEW)
    - `core.user_data_handlers (get_user_data)` (NEW)
    - `user.user_context (UserContext)` (NEW)
  - **Standard Library**:
    - `typing (Any, Dict, List)`
- **Used by**: 
  - `ai/chatbot.py`
  - `ai/context_builder.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.message_management, core.response_tracking, core.schedule_utilities, core.time_utilities, core.user_data_handlers, user.user_context
- Removed: ai/chatbot.py, ai/context_builder.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Manages rich user context for AI conversations
<!-- MANUAL_ENHANCEMENT_END -->

#### `user/user_context.py`
- **Purpose**: User context management
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.schedule_utilities (get_active_schedules)` (NEW)
    - `core.user_data_handlers (get_user_data, save_user_data)` (NEW)
  - **Standard Library**:
    - `threading`
- **Used by**: 
  - `core/schedule_management.py`
  - `core/scheduler.py`
  - `ui/ui_app_qt.py`
  - `user/context_manager.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.schedule_utilities, core.user_data_handlers
- Removed: core/schedule_management.py, core/scheduler.py, ui/ui_app_qt.py, user/context_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: User context management
<!-- MANUAL_ENHANCEMENT_END -->

#### `user/user_preferences.py`
- **Purpose**: User preferences management
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (NEW)
    - `core.logger (get_component_logger)` (NEW)
    - `core.schedule_management (is_schedule_period_active, set_schedule_period_active)` (NEW)
    - `core.user_data_handlers (get_user_data, update_user_preferences)` (NEW)
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.schedule_management, core.user_data_handlers

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: User preferences management
<!-- MANUAL_ENHANCEMENT_END -->
