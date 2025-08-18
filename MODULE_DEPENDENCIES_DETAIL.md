# Module Dependencies - MHM Project

> **Audience**: Human developer and AI collaborators  
> **Purpose**: Complete dependency map for all modules in the MHM codebase  
> **Status**: **ACTIVE** - Hybrid auto-generated and manually enhanced  
> **Last Updated**: 2025-08-07 23:03:14

> **See [README.md](README.md) for complete navigation and project overview**
> **See [ARCHITECTURE.md](ARCHITECTURE.md) for system architecture and design**
> **See [TODO.md](TODO.md) for current documentation priorities**

## 📋 **Overview**

### **Module Dependencies Coverage: 100.0% ✅ COMPLETED**
- **Files Scanned**: 162
- **Total Imports Found**: 1678
- **Dependencies Documented**: 162 (100% coverage)
- **Standard Library Imports**: 608
- **Third-Party Imports**: 270
- **Local Imports**: 800
- **Last Updated**: 2025-08-07

**Status**: ✅ **COMPLETED** - All module dependencies have been documented with comprehensive dependency and usage information.

**Note**: This dependency map uses a hybrid approach - auto-generated dependency information with manual enhancements for detailed descriptions and reverse dependencies.

## 🔍 **Import Statistics**

- **Standard Library**: 608 imports (36.2%)
- **Third-party**: 270 imports (16.1%)
- **Local**: 800 imports (47.7%)

## 📁 **Module Dependencies by Directory**

### `bot/` - Communication Channel Implementations

#### `bot/ai_chatbot.py`
- **Purpose**: AI chatbot implementation using LM Studio API
- **Dependencies**: 
  - **Local**:
    - `bot.user_context_manager (user_context_manager)` (🆕)
    - `core.config (LM_STUDIO_BASE_URL, LM_STUDIO_API_KEY, LM_STUDIO_MODEL, AI_TIMEOUT_SECONDS, AI_CACHE_RESPONSES, CONTEXT_CACHE_TTL, AI_SYSTEM_PROMPT_PATH, AI_USE_CUSTOM_PROMPT, AI_CONNECTION_TEST_TIMEOUT, AI_API_CALL_TIMEOUT, AI_PERSONALIZED_MESSAGE_TIMEOUT, AI_CONTEXTUAL_RESPONSE_TIMEOUT, AI_QUICK_RESPONSE_TIMEOUT, AI_MAX_RESPONSE_LENGTH)` (🆕)
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.response_tracking (get_recent_responses, store_chat_interaction)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
  - **Standard Library**:
    - `asyncio`
    - `datetime`
    - `hashlib`
    - `json`
    - `os`
    - `psutil`
    - `requests`
    - `threading`
    - `time`
    - `typing (Dict, Optional, Tuple)`
- **Used by**: 
  - `bot/communication_manager.py`
  - `bot/conversation_manager.py`
  - `bot/enhanced_command_parser.py`
  - `bot/interaction_manager.py`
  - `scripts/debug/debug_comprehensive_prompt.py`
  - `scripts/test_ai_raw.py`
  - `scripts/test_centralized_config.py`
  - `scripts/testing/ai/test_ai_with_clear_cache.py`
  - `scripts/testing/ai/test_comprehensive_ai.py`
  - `scripts/testing/ai/test_lm_studio.py`
  - `scripts/testing/test_user_data_analysis.py`
  - `tests/behavior/test_ai_chatbot_behavior.py`

**Dependency Changes**:
- Added: bot.user_context_manager, core.config, core.error_handling, core.logger, core.response_tracking, core.user_data_handlers
- Removed: bot/communication_manager.py, bot/conversation_manager.py, bot/enhanced_command_parser.py, bot/interaction_manager.py, scripts/debug/debug_comprehensive_prompt.py, scripts/test_ai_raw.py, scripts/test_centralized_config.py, scripts/testing/ai/test_ai_with_clear_cache.py, scripts/testing/ai/test_comprehensive_ai.py, scripts/testing/ai/test_lm_studio.py, scripts/testing/test_user_data_analysis.py, tests/behavior/test_ai_chatbot_behavior.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: AI chatbot implementation using LM Studio API

<!-- MANUAL_ENHANCEMENT_END -->

#### `bot/base_channel.py`
- **Purpose**: Abstract base class for communication channels
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
  - **Standard Library**:
    - `asyncio`
    - `typing (Optional, Dict, Any, List)`
  - **Third-party**:
    - `abc (ABC, abstractmethod)`
    - `dataclasses (dataclass)`
    - `enum (Enum)`
- **Used by**: 
  - `bot/channel_factory.py`
  - `bot/communication_manager.py`
  - `bot/discord_bot.py`
  - `bot/email_bot.py`
  - `bot/telegram_bot.py`
  - `scripts/test_discord_connection.py`
  - `tests/behavior/test_communication_behavior.py`
  - `tests/behavior/test_discord_bot_behavior.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger
- Removed: bot/channel_factory.py, bot/communication_manager.py, bot/discord_bot.py, bot/email_bot.py, bot/telegram_bot.py, scripts/test_discord_connection.py, tests/behavior/test_communication_behavior.py, tests/behavior/test_discord_bot_behavior.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Abstract base class for communication channels

<!-- MANUAL_ENHANCEMENT_END -->

#### `bot/channel_factory.py`
- **Purpose**: Factory for creating communication channels
- **Dependencies**: 
  - **Local**:
    - `bot.base_channel (BaseChannel, ChannelConfig)` (🆕)
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
  - **Standard Library**:
    - `typing (Dict, Type, Optional)`
- **Used by**: 
  - `bot/channel_registry.py`
  - `bot/communication_manager.py`

**Dependency Changes**:
- Added: bot.base_channel, core.error_handling, core.logger
- Removed: bot/channel_registry.py, bot/communication_manager.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Factory for creating communication channels

<!-- MANUAL_ENHANCEMENT_END -->

#### `bot/channel_registry.py`
- **Purpose**: Registry for all available communication channels
- **Dependencies**: 
  - **Local**:
    - `bot.channel_factory (ChannelFactory)` (🆕)
    - `bot.discord_bot (DiscordBot)` (🆕)
    - `bot.email_bot (EmailBot)` (🆕)
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
- **Used by**: 
  - `core/service.py`
  - `tests/ui/test_dialogs.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: bot.channel_factory, bot.discord_bot, bot.email_bot, core.error_handling
- Removed: core/service.py, tests/ui/test_dialogs.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Registry for all available communication channels

<!-- MANUAL_ENHANCEMENT_END -->

#### `bot/communication_manager.py`
- **Purpose**: Manages communication across all channels
- **Dependencies**: 
  - **Local**:
    - `bot.ai_chatbot (get_ai_chatbot)` (🆕)
    - `bot.base_channel (BaseChannel, ChannelConfig, ChannelStatus, ChannelType)` (🆕)
    - `bot.channel_factory (ChannelFactory)` (🆕)
    - `bot.conversation_manager (conversation_manager)` (🆕)
    - `bot.conversation_manager (conversation_manager)` (🆕)
    - `bot.conversation_manager (conversation_manager)` (🆕)
    - `core.config (EMAIL_SMTP_SERVER, DISCORD_BOT_TOKEN, get_user_data_dir)` (🆕)
    - `core.error_handling (handle_errors)` (🆕)
    - `core.file_operations (determine_file_path, load_json_data)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.logger (force_restart_logging)` (🆕)
    - `core.message_management (store_sent_message)` (🆕)
    - `core.response_tracking (get_recent_checkins)` (🆕)
    - `core.schedule_management (get_current_time_periods_with_validation, get_current_day_names)` (🆕)
    - `core.service_utilities (wait_for_network)` (🆕)
    - `core.user_data_handlers (get_user_data, get_all_user_ids)` (🆕)
    - `tasks.task_management (get_task_by_id, are_tasks_enabled)` (🆕)
  - **Standard Library**:
    - `asyncio`
    - `asyncio`
    - `datetime (datetime, timedelta)`
    - `logging`
    - `os`
    - `random`
    - `threading`
    - `threading`
    - `time`
    - `time`
    - `typing (Dict, List, Optional, Any)`
    - `uuid`
  - **Third-party**:
    - `dataclasses (dataclass)`
    - `queue`
- **Used by**: 
  - `core/scheduler.py`
  - `core/service.py`
  - `scripts/debug/discord_connectivity_diagnostic.py`
  - `tests/behavior/test_communication_behavior.py`
  - `tests/ui/test_dialogs.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: bot.ai_chatbot, bot.base_channel, bot.channel_factory, bot.conversation_manager, core.config, core.error_handling, core.file_operations, core.logger, core.message_management, core.response_tracking, core.schedule_management, core.service_utilities, core.user_data_handlers, tasks.task_management
- Removed: core/scheduler.py, core/service.py, scripts/debug/discord_connectivity_diagnostic.py, tests/behavior/test_communication_behavior.py, tests/ui/test_dialogs.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Manages communication across all channels

<!-- MANUAL_ENHANCEMENT_END -->

#### `bot/conversation_manager.py`
- **Purpose**: Manages conversation flows and check-ins
- **Dependencies**: 
  - **Local**:
    - `bot.ai_chatbot (get_ai_chatbot)` (🆕)
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.response_tracking (is_user_checkins_enabled, get_user_checkin_preferences, get_recent_checkins, store_checkin_response)` (🆕)
  - **Standard Library**:
    - `json`
    - `os`
- **Used by**: 
  - `bot/communication_manager.py`
  - `bot/discord_bot.py`
  - `bot/interaction_handlers.py`
  - `bot/interaction_manager.py`
  - `tests/behavior/test_ai_chatbot_behavior.py`
  - `tests/behavior/test_conversation_behavior.py`
  - `tests/behavior/test_discord_bot_behavior.py`

**Dependency Changes**:
- Added: bot.ai_chatbot, core.error_handling, core.logger, core.response_tracking
- Removed: bot/communication_manager.py, bot/discord_bot.py, bot/interaction_handlers.py, bot/interaction_manager.py, tests/behavior/test_ai_chatbot_behavior.py, tests/behavior/test_conversation_behavior.py, tests/behavior/test_discord_bot_behavior.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Manages conversation flows and check-ins

<!-- MANUAL_ENHANCEMENT_END -->

#### `bot/discord_bot.py`
- **Purpose**: Discord bot implementation
- **Dependencies**: 
  - **Local**:
    - `bot.base_channel (BaseChannel, ChannelType, ChannelStatus, ChannelConfig)` (🆕)
    - `bot.conversation_manager (conversation_manager)` (🆕)
    - `bot.interaction_manager (handle_user_message)` (🆕)
    - `bot.interaction_manager (handle_user_message)` (🆕)
    - `bot.interaction_manager (handle_user_message)` (🆕)
    - `bot.interaction_manager (handle_user_message)` (🆕)
    - `bot.interaction_manager (handle_user_message)` (🆕)
    - `bot.interaction_manager (handle_user_message)` (🆕)
    - `bot.interaction_manager (handle_user_message)` (🆕)
    - `bot.interaction_manager (handle_user_message)` (🆕)
    - `bot.interaction_manager (handle_user_message)` (🆕)
    - `bot.interaction_manager (handle_user_message)` (🆕)
    - `core.config (DISCORD_BOT_TOKEN)` (🆕)
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.user_management (get_user_id_by_discord_user_id)` (🆕)
  - **Standard Library**:
    - `asyncio`
    - `os`
    - `random`
    - `socket`
    - `threading`
    - `time`
    - `typing (List, Dict, Any, Optional)`
  - **Third-party**:
    - `discord`
    - `discord.ext (commands)`
    - `dns.resolver`
    - `enum`
    - `queue`
- **Used by**: 
  - `bot/channel_registry.py`
  - `scripts/debug/discord_connectivity_diagnostic.py`
  - `scripts/debug/test_dns_fallback.py`
  - `scripts/test_discord_connection.py`
  - `tests/behavior/test_discord_bot_behavior.py`

**Dependency Changes**:
- Added: bot.base_channel, bot.conversation_manager, bot.interaction_manager, core.config, core.error_handling, core.logger, core.user_management
- Removed: bot/channel_registry.py, discord.ext, dns.resolver, scripts/debug/discord_connectivity_diagnostic.py, scripts/debug/test_dns_fallback.py, scripts/test_discord_connection.py, tests/behavior/test_discord_bot_behavior.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Discord bot implementation

<!-- MANUAL_ENHANCEMENT_END -->

#### `bot/email_bot.py`
- **Purpose**: Email bot implementation
- **Dependencies**: 
  - **Local**:
    - `bot.base_channel (BaseChannel, ChannelType, ChannelStatus, ChannelConfig)` (🆕)
    - `core.config (EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD)` (🆕)
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
  - **Standard Library**:
    - `asyncio`
    - `email`
    - `smtplib`
    - `typing (List, Dict, Any)`
  - **Third-party**:
    - `email.header (decode_header)`
    - `email.mime.text (MIMEText)`
    - `imaplib`
- **Used by**: 
  - `bot/channel_registry.py`

**Dependency Changes**:
- Added: bot.base_channel, core.config, core.error_handling, core.logger
- Removed: bot/channel_registry.py, email.header, email.mime.text

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Email communication channel implementation

<!-- MANUAL_ENHANCEMENT_END -->

#### `bot/enhanced_command_parser.py`
- **Purpose**: Communication channel implementation for enhanced_command_parser
- **Dependencies**: 
  - **Local**:
    - `bot.ai_chatbot (get_ai_chatbot)` (🆕)
    - `bot.interaction_handlers (ParsedCommand, get_all_handlers)` (🆕)
    - `core.config (AI_RULE_BASED_HIGH_CONFIDENCE_THRESHOLD, AI_AI_ENHANCED_CONFIDENCE_THRESHOLD, AI_RULE_BASED_FALLBACK_THRESHOLD, AI_AI_PARSING_BASE_CONFIDENCE, AI_AI_PARSING_PARTIAL_CONFIDENCE, AI_COMMAND_PARSING_TIMEOUT)` (🆕)
    - `core.error_handling (handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
  - **Standard Library**:
    - `json`
    - `re`
    - `typing (Dict, List, Optional, Any, Tuple)`
  - **Third-party**:
    - `dataclasses (dataclass)`
- **Used by**: 
  - `bot/interaction_manager.py`
  - `scripts/test_ai_parsing.py`
  - `scripts/test_centralized_config.py`
  - `scripts/test_comprehensive_fixes.py`
  - `scripts/test_discord_commands.py`
  - `scripts/test_enhanced_discord_commands.py`
  - `scripts/test_enhanced_parser_direct.py`
  - `scripts/test_task_response_formatting.py`

**Dependency Changes**:
- Added: bot.ai_chatbot, bot.interaction_handlers, core.config, core.error_handling, core.logger
- Removed: bot/interaction_manager.py, scripts/test_ai_parsing.py, scripts/test_centralized_config.py, scripts/test_comprehensive_fixes.py, scripts/test_discord_commands.py, scripts/test_enhanced_discord_commands.py, scripts/test_enhanced_parser_direct.py, scripts/test_task_response_formatting.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `bot/interaction_handlers.py`
- **Purpose**: Communication channel implementation for interaction_handlers
- **Dependencies**: 
  - **Local**:
    - `bot.conversation_manager (conversation_manager)` (🆕)
    - `core.checkin_analytics (CheckinAnalytics)` (🆕)
    - `core.checkin_analytics (CheckinAnalytics)` (🆕)
    - `core.checkin_analytics (CheckinAnalytics)` (🆕)
    - `core.checkin_analytics (CheckinAnalytics)` (🆕)
    - `core.checkin_analytics (CheckinAnalytics)` (🆕)
    - `core.checkin_analytics (CheckinAnalytics)` (🆕)
    - `core.checkin_analytics (CheckinAnalytics)` (🆕)
    - `core.checkin_analytics (CheckinAnalytics)` (🆕)
    - `core.error_handling (handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.response_tracking (is_user_checkins_enabled, get_user_checkin_preferences, get_recent_checkins)` (🆕)
    - `core.response_tracking (is_user_checkins_enabled)` (🆕)
    - `core.response_tracking (get_recent_checkins)` (🆕)
    - `core.schedule_management (get_schedule_time_periods)` (🆕)
    - `core.schedule_management (get_schedule_time_periods, set_schedule_periods)` (🆕)
    - `core.schedule_management (get_schedule_time_periods)` (🆕)
    - `core.schedule_management (add_schedule_period, get_schedule_time_periods, set_schedule_periods)` (🆕)
    - `core.schedule_management (get_schedule_time_periods, set_schedule_periods)` (🆕)
    - `core.user_management (load_user_account_data, load_user_preferences_data, load_user_context_data, save_user_context_data, get_user_categories)` (🆕)
    - `core.user_management (load_user_schedules_data)` (🆕)
    - `core.user_management (load_user_account_data)` (🆕)
    - `core.user_management (load_user_account_data)` (🆕)
    - `core.user_management (get_user_categories)` (🆕)
    - `core.user_management (get_user_categories)` (🆕)
    - `tasks.task_management (create_task, load_active_tasks, complete_task, delete_task, update_task, get_user_task_stats, get_tasks_due_soon)` (🆕)
    - `tasks.task_management (load_active_tasks)` (🆕)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `datetime (datetime, timedelta)`
    - `datetime (datetime, date)`
    - `datetime`
    - `datetime`
    - `datetime`
    - `datetime`
    - `json`
    - `re`
    - `typing (Dict, List, Optional, Any, Tuple)`
  - **Third-party**:
    - `abc (ABC, abstractmethod)`
    - `dataclasses (dataclass)`
- **Used by**: 
  - `bot/enhanced_command_parser.py`
  - `bot/interaction_manager.py`
  - `scripts/test_comprehensive_fixes.py`
  - `scripts/test_discord_commands.py`
  - `scripts/test_enhanced_discord_commands.py`
  - `scripts/test_task_response_formatting.py`
  - `tests/behavior/test_interaction_handlers_behavior.py`

**Dependency Changes**:
- Added: bot.conversation_manager, core.checkin_analytics, core.error_handling, core.logger, core.response_tracking, core.schedule_management, core.user_management, tasks.task_management
- Removed: bot/enhanced_command_parser.py, bot/interaction_manager.py, scripts/test_comprehensive_fixes.py, scripts/test_discord_commands.py, scripts/test_enhanced_discord_commands.py, scripts/test_task_response_formatting.py, tests/behavior/test_interaction_handlers_behavior.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `bot/interaction_manager.py`
- **Purpose**: Communication channel implementation for interaction_manager
- **Dependencies**: 
  - **Local**:
    - `bot.ai_chatbot (get_ai_chatbot)` (🆕)
    - `bot.conversation_manager (conversation_manager)` (🆕)
    - `bot.enhanced_command_parser (get_enhanced_command_parser, ParsingResult)` (🆕)
    - `bot.interaction_handlers (InteractionResponse, get_interaction_handler, get_all_handlers, ParsedCommand)` (🆕)
    - `bot.interaction_handlers (ParsedCommand)` (🆕)
    - `core.config (AI_MAX_RESPONSE_LENGTH)` (🆕)
    - `core.error_handling (handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.response_tracking (is_user_checkins_enabled)` (🆕)
    - `core.response_tracking (get_recent_checkins)` (🆕)
    - `core.user_management (get_user_categories)` (🆕)
    - `tasks.task_management (load_active_tasks)` (🆕)
  - **Standard Library**:
    - `typing (Optional, Dict, Any)`
- **Used by**: 
  - `bot/discord_bot.py`
  - `scripts/test_comprehensive_fixes.py`
  - `scripts/test_task_response_formatting.py`

**Dependency Changes**:
- Added: bot.ai_chatbot, bot.conversation_manager, bot.enhanced_command_parser, bot.interaction_handlers, core.config, core.error_handling, core.logger, core.response_tracking, core.user_management, tasks.task_management
- Removed: bot/discord_bot.py, scripts/test_comprehensive_fixes.py, scripts/test_task_response_formatting.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `bot/telegram_bot.py`
- **Purpose**: Telegram bot implementation
- **Dependencies**: 
  - **Local**:
    - `bot.base_channel (BaseChannel, ChannelType, ChannelStatus, ChannelConfig)` (🆕)
    - `core.config (TELEGRAM_BOT_TOKEN)` (🆕)
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.message_management (add_message)` (🆕)
    - `core.schedule_management (get_schedule_time_periods, add_schedule_period)` (🆕)
    - `core.scheduler` (🆕)
    - `core.service_utilities (wait_for_network, title_case)` (🆕)
    - `core.service_utilities (InvalidTimeFormatError)` (🆕)
    - `core.user_management (get_user_id_by_chat_id)` (🆕)
    - `core.user_management (create_new_user)` (🆕)
    - `user.user_context (UserContext)` (🆕)
  - **Standard Library**:
    - `asyncio`
    - `json`
    - `os`
    - `requests`
    - `threading`
    - `threading (Lock)`
    - `time`
    - `typing (List, Dict, Any)`
    - `uuid`
    - `warnings`
  - **Third-party**:
    - `telegram`
    - `telegram (Update, InlineKeyboardMarkup, InlineKeyboardButton, Bot)`
    - `telegram.constants (ParseMode)`
    - `telegram.ext (Application, CommandHandler, MessageHandler, CallbackContext, CallbackQueryHandler, ConversationHandler, filters)`
    - `telegram.warnings (PTBUserWarning)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.base_channel, core.config, core.error_handling, core.logger, core.message_management, core.schedule_management, core.scheduler, core.service_utilities, core.user_management, user.user_context
- Removed: telegram.constants, telegram.ext, telegram.warnings

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Telegram communication channel implementation

<!-- MANUAL_ENHANCEMENT_END -->

#### `bot/user_context_manager.py`
- **Purpose**: Manages user context for AI conversations
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.message_management (get_last_10_messages)` (🆕)
    - `core.response_tracking (get_recent_checkins, get_recent_chat_interactions)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `user.user_context (UserContext)` (🆕)
    - `user.user_preferences (UserPreferences)` (🆕)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `json`
    - `time`
    - `typing (Dict, List, Optional, Any)`
- **Used by**: 
  - `bot/ai_chatbot.py`
  - `tests/behavior/test_ai_chatbot_behavior.py`
  - `tests/behavior/test_user_context_behavior.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.message_management, core.response_tracking, core.user_data_handlers, user.user_context, user.user_preferences
- Removed: bot/ai_chatbot.py, tests/behavior/test_ai_chatbot_behavior.py, tests/behavior/test_user_context_behavior.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Manages rich user context for AI conversations

<!-- MANUAL_ENHANCEMENT_END -->

### `core/` - Core System Modules (Foundation)

#### `core/auto_cleanup.py`
- **Purpose**: Automatic cache cleanup and maintenance
- **Dependencies**: 
  - **Local**:
    - `core.config` (🆕)
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
    - `core.logger (get_component_logger)` (🆕)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `json`
    - `logging`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
    - `time`
- **Used by**: 
  - `core/service.py`
  - `tests/behavior/test_auto_cleanup_behavior.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger
- Removed: core/service.py, tests/behavior/test_auto_cleanup_behavior.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Automatic cache cleanup and maintenance

<!-- MANUAL_ENHANCEMENT_END -->

#### `core/backup_manager.py`
- **Purpose**: Manages automatic backups and rollback operations
- **Dependencies**: 
  - **Local**:
    - `core.config (BASE_DATA_DIR, USER_INFO_DIR_PATH)` (🆕)
    - `core.error_handling (handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.user_data_handlers (get_user_data, get_all_user_ids)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `time`
    - `typing (Dict, List, Optional, Tuple)`
    - `zipfile`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger, core.user_data_handlers

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Manages automatic backups and rollback operations

<!-- MANUAL_ENHANCEMENT_END -->

#### `core/checkin_analytics.py`
- **Purpose**: Analyzes check-in data and provides insights
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.response_tracking (get_recent_checkins)` (🆕)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `json`
    - `statistics`
    - `typing (Dict, List, Optional, Tuple)`
- **Used by**: 
  - `bot/interaction_handlers.py`
  - `tests/behavior/test_checkin_analytics_behavior.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.response_tracking
- Removed: bot/interaction_handlers.py, tests/behavior/test_checkin_analytics_behavior.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Analyzes check-in data and provides insights

<!-- MANUAL_ENHANCEMENT_END -->

#### `core/config.py`
- **Purpose**: Configuration management and validation
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (ConfigurationError, ValidationError, handle_configuration_error, handle_errors, error_handler)` (🆕)
  - **Standard Library**:
    - `logging`
    - `os`
    - `pathlib (Path)`
    - `typing (Dict, List, Tuple, Optional)`
  - **Third-party**:
    - `dotenv (load_dotenv)`
- **Used by**: 
  - `bot/ai_chatbot.py`
  - `bot/communication_manager.py`
  - `bot/discord_bot.py`
  - `bot/email_bot.py`
  - `bot/enhanced_command_parser.py`
  - `bot/interaction_manager.py`
  - `bot/telegram_bot.py`
  - `core/auto_cleanup.py`
  - `core/backup_manager.py`
  - `core/file_operations.py`
  - `core/message_management.py`
  - `core/response_tracking.py`
  - `core/service.py`
  - `core/service_utilities.py`
  - `core/user_data_handlers.py`
  - `core/user_data_manager.py`
  - `core/user_data_validation.py`
  - `core/user_management.py`
  - `scripts/debug/debug_discord_connectivity.py`
  - `scripts/debug/debug_lm_studio_timeout.py`
  - `scripts/migration/migrate_sent_messages.py`
  - `scripts/migration/migrate_user_data_structure.py`
  - `scripts/test_centralized_config.py`
  - `scripts/testing/ai/test_lm_studio.py`
  - `scripts/testing/validate_config.py`
  - `scripts/utilities/cleanup/cleanup_test_data.py`
  - `scripts/utilities/cleanup/cleanup_user_message_files.py`
  - `scripts/utilities/cleanup_duplicate_messages.py`
  - `tasks/task_management.py`
  - `tests/behavior/test_account_management_real_behavior.py`
  - `tests/behavior/test_ai_chatbot_behavior.py`
  - `tests/behavior/test_communication_behavior.py`
  - `tests/behavior/test_discord_bot_behavior.py`
  - `tests/behavior/test_message_behavior.py`
  - `tests/behavior/test_service_behavior.py`
  - `tests/behavior/test_task_behavior.py`
  - `tests/behavior/test_utilities_demo.py`
  - `tests/conftest.py`
  - `tests/integration/test_account_lifecycle.py`
  - `tests/test_utilities.py`
  - `tests/unit/test_cleanup.py`
  - `tests/unit/test_config.py`
  - `tests/unit/test_file_operations.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling
- Removed: bot/ai_chatbot.py, bot/communication_manager.py, bot/discord_bot.py, bot/email_bot.py, bot/enhanced_command_parser.py, bot/interaction_manager.py, bot/telegram_bot.py, core/auto_cleanup.py, core/backup_manager.py, core/file_operations.py, core/message_management.py, core/response_tracking.py, core/service.py, core/service_utilities.py, core/user_data_handlers.py, core/user_data_manager.py, core/user_data_validation.py, core/user_management.py, scripts/debug/debug_discord_connectivity.py, scripts/debug/debug_lm_studio_timeout.py, scripts/migration/migrate_sent_messages.py, scripts/migration/migrate_user_data_structure.py, scripts/test_centralized_config.py, scripts/testing/ai/test_lm_studio.py, scripts/testing/validate_config.py, scripts/utilities/cleanup/cleanup_test_data.py, scripts/utilities/cleanup/cleanup_user_message_files.py, scripts/utilities/cleanup_duplicate_messages.py, tasks/task_management.py, tests/behavior/test_account_management_real_behavior.py, tests/behavior/test_ai_chatbot_behavior.py, tests/behavior/test_communication_behavior.py, tests/behavior/test_discord_bot_behavior.py, tests/behavior/test_message_behavior.py, tests/behavior/test_service_behavior.py, tests/behavior/test_task_behavior.py, tests/behavior/test_utilities_demo.py, tests/conftest.py, tests/integration/test_account_lifecycle.py, tests/test_utilities.py, tests/unit/test_cleanup.py, tests/unit/test_config.py, tests/unit/test_file_operations.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Configuration management and validation

<!-- MANUAL_ENHANCEMENT_END -->

#### `core/error_handling.py`
- **Purpose**: Centralized error handling and recovery
- **Dependencies**: 
  - **Local**:
    - `core.logger (get_component_logger)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `json`
    - `json`
    - `logging`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
    - `typing (Optional, Dict, Any, Callable, List, Tuple)`
  - **Third-party**:
    - `traceback`
- **Used by**: 
  - `bot/ai_chatbot.py`
  - `bot/base_channel.py`
  - `bot/channel_factory.py`
  - `bot/channel_registry.py`
  - `bot/communication_manager.py`
  - `bot/conversation_manager.py`
  - `bot/discord_bot.py`
  - `bot/email_bot.py`
  - `bot/enhanced_command_parser.py`
  - `bot/interaction_handlers.py`
  - `bot/interaction_manager.py`
  - `bot/telegram_bot.py`
  - `bot/user_context_manager.py`
  - `core/auto_cleanup.py`
  - `core/backup_manager.py`
  - `core/checkin_analytics.py`
  - `core/config.py`
  - `core/file_operations.py`
  - `core/message_management.py`
  - `core/response_tracking.py`
  - `core/schedule_management.py`
  - `core/scheduler.py`
  - `core/service.py`
  - `core/service_utilities.py`
  - `core/ui_management.py`
  - `core/user_data_handlers.py`
  - `core/user_data_manager.py`
  - `core/user_data_validation.py`
  - `core/user_management.py`
  - `run_mhm.py`
  - `tasks/task_management.py`
  - `tests/behavior/test_scheduler_behavior.py`
  - `tests/unit/test_error_handling.py`
  - `tests/unit/test_file_operations.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/category_management_dialog.py`
  - `ui/dialogs/checkin_management_dialog.py`
  - `ui/dialogs/schedule_editor_dialog.py`
  - `ui/dialogs/task_completion_dialog.py`
  - `ui/dialogs/task_crud_dialog.py`
  - `ui/dialogs/task_edit_dialog.py`
  - `ui/dialogs/task_management_dialog.py`
  - `ui/dialogs/user_profile_dialog.py`
  - `ui/ui_app_qt.py`
  - `ui/widgets/checkin_settings_widget.py`
  - `ui/widgets/period_row_widget.py`
  - `ui/widgets/tag_widget.py`
  - `ui/widgets/task_settings_widget.py`
  - `user/user_context.py`
  - `user/user_preferences.py`

**Dependency Changes**:
- Added: core.logger
- Removed: bot/ai_chatbot.py, bot/base_channel.py, bot/channel_factory.py, bot/channel_registry.py, bot/communication_manager.py, bot/conversation_manager.py, bot/discord_bot.py, bot/email_bot.py, bot/enhanced_command_parser.py, bot/interaction_handlers.py, bot/interaction_manager.py, bot/telegram_bot.py, bot/user_context_manager.py, core/auto_cleanup.py, core/backup_manager.py, core/checkin_analytics.py, core/config.py, core/file_operations.py, core/message_management.py, core/response_tracking.py, core/schedule_management.py, core/scheduler.py, core/service.py, core/service_utilities.py, core/ui_management.py, core/user_data_handlers.py, core/user_data_manager.py, core/user_data_validation.py, core/user_management.py, run_mhm.py, tasks/task_management.py, tests/behavior/test_scheduler_behavior.py, tests/unit/test_error_handling.py, tests/unit/test_file_operations.py, ui/dialogs/account_creator_dialog.py, ui/dialogs/category_management_dialog.py, ui/dialogs/checkin_management_dialog.py, ui/dialogs/schedule_editor_dialog.py, ui/dialogs/task_completion_dialog.py, ui/dialogs/task_crud_dialog.py, ui/dialogs/task_edit_dialog.py, ui/dialogs/task_management_dialog.py, ui/dialogs/user_profile_dialog.py, ui/ui_app_qt.py, ui/widgets/checkin_settings_widget.py, ui/widgets/period_row_widget.py, ui/widgets/tag_widget.py, ui/widgets/task_settings_widget.py, user/user_context.py, user/user_preferences.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Centralized error handling and recovery

<!-- MANUAL_ENHANCEMENT_END -->

#### `core/file_operations.py`
- **Purpose**: File operations and data management
- **Dependencies**: 
  - **Local**:
    - `core.config (USER_INFO_DIR_PATH, DEFAULT_MESSAGES_DIR_PATH, get_user_file_path, ensure_user_directory, get_user_data_dir)` (🆕)
    - `core.error_handling (error_handler, FileOperationError, DataError, handle_file_error, handle_errors, safe_file_operation)` (🆕)
    - `core.logger (get_logger)` (🆕)
    - `core.message_management (create_message_file_from_defaults)` (🆕)
    - `core.user_data_manager (update_message_references, update_user_index)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `re`
    - `shutil`
    - `time`
- **Used by**: 
  - `bot/communication_manager.py`
  - `core/message_management.py`
  - `core/response_tracking.py`
  - `core/schedule_management.py`
  - `core/service.py`
  - `core/user_data_handlers.py`
  - `core/user_data_manager.py`
  - `core/user_management.py`
  - `scripts/debug/debug_preferences.py`
  - `scripts/migration/migrate_messaging_service.py`
  - `scripts/migration/migrate_user_data_structure.py`
  - `scripts/testing/ai/test_data_integrity.py`
  - `scripts/testing/ai/test_new_modules.py`
  - `scripts/utilities/add_checkin_schedules.py`
  - `scripts/utilities/cleanup/cleanup_user_message_files.py`
  - `tasks/task_management.py`
  - `tests/integration/test_account_management.py`
  - `tests/integration/test_user_creation.py`
  - `tests/test_utilities.py`
  - `tests/ui/test_account_creation_ui.py`
  - `tests/ui/test_dialog_behavior.py`
  - `tests/ui/test_widget_behavior.py`
  - `tests/unit/test_file_operations.py`
  - `tests/unit/test_user_management.py`
  - `ui/dialogs/account_creator_dialog.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger, core.message_management, core.user_data_manager
- Removed: bot/communication_manager.py, core/message_management.py, core/response_tracking.py, core/schedule_management.py, core/service.py, core/user_data_handlers.py, core/user_data_manager.py, core/user_management.py, scripts/debug/debug_preferences.py, scripts/migration/migrate_messaging_service.py, scripts/migration/migrate_user_data_structure.py, scripts/testing/ai/test_data_integrity.py, scripts/testing/ai/test_new_modules.py, scripts/utilities/add_checkin_schedules.py, scripts/utilities/cleanup/cleanup_user_message_files.py, tasks/task_management.py, tests/integration/test_account_management.py, tests/integration/test_user_creation.py, tests/test_utilities.py, tests/ui/test_account_creation_ui.py, tests/ui/test_dialog_behavior.py, tests/ui/test_widget_behavior.py, tests/unit/test_file_operations.py, tests/unit/test_user_management.py, ui/dialogs/account_creator_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: File operations and data management

<!-- MANUAL_ENHANCEMENT_END -->

#### `core/logger.py`
- **Purpose**: Logging system configuration and management
- **Dependencies**: 
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `json`
    - `logging`
    - `os`
    - `re`
    - `shutil`
    - `time`
  - **Third-party**:
    - `glob`
    - `glob`
    - `glob`
    - `glob`
    - `gzip`
    - `logging.handlers (RotatingFileHandler, TimedRotatingFileHandler)`
- **Used by**: 
  - `bot/ai_chatbot.py`
  - `bot/base_channel.py`
  - `bot/channel_factory.py`
  - `bot/communication_manager.py`
  - `bot/conversation_manager.py`
  - `bot/discord_bot.py`
  - `bot/email_bot.py`
  - `bot/enhanced_command_parser.py`
  - `bot/interaction_handlers.py`
  - `bot/interaction_manager.py`
  - `bot/telegram_bot.py`
  - `bot/user_context_manager.py`
  - `core/auto_cleanup.py`
  - `core/backup_manager.py`
  - `core/checkin_analytics.py`
  - `core/error_handling.py`
  - `core/file_operations.py`
  - `core/message_management.py`
  - `core/response_tracking.py`
  - `core/schedule_management.py`
  - `core/scheduler.py`
  - `core/service.py`
  - `core/service_utilities.py`
  - `core/ui_management.py`
  - `core/user_data_handlers.py`
  - `core/user_data_manager.py`
  - `core/user_data_validation.py`
  - `core/user_management.py`
  - `scripts/debug/debug_discord_connectivity.py`
  - `scripts/debug/discord_connectivity_diagnostic.py`
  - `scripts/debug/test_dns_fallback.py`
  - `scripts/migration/migrate_messaging_service.py`
  - `scripts/migration/migrate_schedule_format.py`
  - `scripts/migration/migrate_sent_messages.py`
  - `scripts/migration/migrate_user_data_structure.py`
  - `scripts/test_comprehensive_fixes.py`
  - `scripts/test_discord_commands.py`
  - `scripts/test_enhanced_discord_commands.py`
  - `scripts/test_task_response_formatting.py`
  - `scripts/utilities/add_checkin_schedules.py`
  - `scripts/utilities/check_checkin_schedules.py`
  - `scripts/utilities/cleanup/cleanup_test_data.py`
  - `scripts/utilities/cleanup/cleanup_user_message_files.py`
  - `scripts/utilities/rebuild_index.py`
  - `scripts/utilities/restore_custom_periods.py`
  - `scripts/utilities/user_data_cli.py`
  - `tasks/task_management.py`
  - `tests/behavior/test_logger_behavior.py`
  - `tests/unit/test_cleanup.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/category_management_dialog.py`
  - `ui/dialogs/checkin_management_dialog.py`
  - `ui/dialogs/schedule_editor_dialog.py`
  - `ui/dialogs/task_completion_dialog.py`
  - `ui/dialogs/task_crud_dialog.py`
  - `ui/dialogs/task_edit_dialog.py`
  - `ui/dialogs/task_management_dialog.py`
  - `ui/dialogs/user_profile_dialog.py`
  - `ui/ui_app_qt.py`
  - `ui/widgets/checkin_settings_widget.py`
  - `ui/widgets/period_row_widget.py`
  - `ui/widgets/tag_widget.py`
  - `ui/widgets/task_settings_widget.py`
  - `ui/widgets/user_profile_settings_widget.py`
  - `user/user_context.py`
  - `user/user_preferences.py`

**Dependency Changes**:
- Removed: bot/ai_chatbot.py, bot/base_channel.py, bot/channel_factory.py, bot/communication_manager.py, bot/conversation_manager.py, bot/discord_bot.py, bot/email_bot.py, bot/enhanced_command_parser.py, bot/interaction_handlers.py, bot/interaction_manager.py, bot/telegram_bot.py, bot/user_context_manager.py, core/auto_cleanup.py, core/backup_manager.py, core/checkin_analytics.py, core/error_handling.py, core/file_operations.py, core/message_management.py, core/response_tracking.py, core/schedule_management.py, core/scheduler.py, core/service.py, core/service_utilities.py, core/ui_management.py, core/user_data_handlers.py, core/user_data_manager.py, core/user_data_validation.py, core/user_management.py, logging.handlers, scripts/debug/debug_discord_connectivity.py, scripts/debug/discord_connectivity_diagnostic.py, scripts/debug/test_dns_fallback.py, scripts/migration/migrate_messaging_service.py, scripts/migration/migrate_schedule_format.py, scripts/migration/migrate_sent_messages.py, scripts/migration/migrate_user_data_structure.py, scripts/test_comprehensive_fixes.py, scripts/test_discord_commands.py, scripts/test_enhanced_discord_commands.py, scripts/test_task_response_formatting.py, scripts/utilities/add_checkin_schedules.py, scripts/utilities/check_checkin_schedules.py, scripts/utilities/cleanup/cleanup_test_data.py, scripts/utilities/cleanup/cleanup_user_message_files.py, scripts/utilities/rebuild_index.py, scripts/utilities/restore_custom_periods.py, scripts/utilities/user_data_cli.py, tasks/task_management.py, tests/behavior/test_logger_behavior.py, tests/unit/test_cleanup.py, ui/dialogs/account_creator_dialog.py, ui/dialogs/category_management_dialog.py, ui/dialogs/checkin_management_dialog.py, ui/dialogs/schedule_editor_dialog.py, ui/dialogs/task_completion_dialog.py, ui/dialogs/task_crud_dialog.py, ui/dialogs/task_edit_dialog.py, ui/dialogs/task_management_dialog.py, ui/dialogs/user_profile_dialog.py, ui/ui_app_qt.py, ui/widgets/checkin_settings_widget.py, ui/widgets/period_row_widget.py, ui/widgets/tag_widget.py, ui/widgets/task_settings_widget.py, ui/widgets/user_profile_settings_widget.py, user/user_context.py, user/user_preferences.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Logging system configuration and management

<!-- MANUAL_ENHANCEMENT_END -->

#### `core/message_management.py`
- **Purpose**: Message management and storage
- **Dependencies**: 
  - **Local**:
    - `core.config (DEFAULT_MESSAGES_DIR_PATH, get_user_data_dir)` (🆕)
    - `core.error_handling (error_handler, DataError, FileOperationError, ValidationError, handle_file_error, handle_errors)` (🆕)
    - `core.file_operations (load_json_data, save_json_data, determine_file_path)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.user_data_manager (update_user_index)` (🆕)
    - `core.user_data_manager (update_user_index)` (🆕)
    - `core.user_data_manager (update_user_index)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `datetime (timedelta)`
    - `json`
    - `os`
    - `typing (List)`
    - `uuid`
- **Used by**: 
  - `bot/communication_manager.py`
  - `bot/telegram_bot.py`
  - `bot/user_context_manager.py`
  - `core/file_operations.py`
  - `core/user_data_handlers.py`
  - `core/user_data_manager.py`
  - `core/user_data_validation.py`
  - `core/user_management.py`
  - `scripts/testing/ai/test_new_modules.py`
  - `scripts/utilities/cleanup/cleanup_user_message_files.py`
  - `tests/behavior/test_account_management_real_behavior.py`
  - `tests/behavior/test_message_behavior.py`
  - `ui/dialogs/account_creator_dialog.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.file_operations, core.logger, core.user_data_manager
- Removed: bot/communication_manager.py, bot/telegram_bot.py, bot/user_context_manager.py, core/file_operations.py, core/user_data_handlers.py, core/user_data_manager.py, core/user_data_validation.py, core/user_management.py, scripts/testing/ai/test_new_modules.py, scripts/utilities/cleanup/cleanup_user_message_files.py, tests/behavior/test_account_management_real_behavior.py, tests/behavior/test_message_behavior.py, ui/dialogs/account_creator_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Message management and storage

<!-- MANUAL_ENHANCEMENT_END -->

#### `core/response_tracking.py`
- **Purpose**: Tracks user responses and interactions
- **Dependencies**: 
  - **Local**:
    - `core.config (USER_INFO_DIR_PATH, get_user_file_path, ensure_user_directory)` (🆕)
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
    - `core.file_operations (load_json_data, save_json_data, get_user_file_path)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `time`
    - `typing (List, Dict, Any, Optional)`
- **Used by**: 
  - `bot/ai_chatbot.py`
  - `bot/communication_manager.py`
  - `bot/conversation_manager.py`
  - `bot/interaction_handlers.py`
  - `bot/interaction_manager.py`
  - `bot/user_context_manager.py`
  - `core/checkin_analytics.py`
  - `core/user_data_manager.py`
  - `scripts/testing/ai/test_new_modules.py`
  - `tests/behavior/test_ai_chatbot_behavior.py`
  - `tests/behavior/test_response_tracking_behavior.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.file_operations, core.logger, core.user_data_handlers
- Removed: bot/ai_chatbot.py, bot/communication_manager.py, bot/conversation_manager.py, bot/interaction_handlers.py, bot/interaction_manager.py, bot/user_context_manager.py, core/checkin_analytics.py, core/user_data_manager.py, scripts/testing/ai/test_new_modules.py, tests/behavior/test_ai_chatbot_behavior.py, tests/behavior/test_response_tracking_behavior.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Tracks user responses and interactions

<!-- MANUAL_ENHANCEMENT_END -->

#### `core/schedule_management.py`
- **Purpose**: Schedule management and time period handling
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
    - `core.file_operations (determine_file_path, load_json_data, save_json_data, get_user_file_path)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.service_utilities (create_reschedule_request)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (update_user_schedules)` (🆕)
    - `core.user_data_handlers (update_user_schedules)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `user.user_context (UserContext)` (🆕)
  - **Standard Library**:
    - `calendar`
    - `datetime (datetime, timedelta)`
    - `re`
    - `time`
    - `typing (List, Dict, Any, Optional)`
- **Used by**: 
  - `bot/communication_manager.py`
  - `bot/interaction_handlers.py`
  - `bot/telegram_bot.py`
  - `core/scheduler.py`
  - `core/ui_management.py`
  - `scripts/testing/ai/test_new_modules.py`
  - `scripts/utilities/check_checkin_schedules.py`
  - `tests/behavior/test_schedule_management_behavior.py`
  - `ui/dialogs/category_management_dialog.py`
  - `ui/dialogs/checkin_management_dialog.py`
  - `ui/dialogs/schedule_editor_dialog.py`
  - `ui/dialogs/task_management_dialog.py`
  - `ui/widgets/checkin_settings_widget.py`
  - `ui/widgets/period_row_widget.py`
  - `ui/widgets/task_settings_widget.py`
  - `user/user_preferences.py`

**Dependency Changes**:
- Added: core.error_handling, core.file_operations, core.logger, core.service_utilities, core.user_data_handlers, user.user_context
- Removed: bot/communication_manager.py, bot/interaction_handlers.py, bot/telegram_bot.py, core/scheduler.py, core/ui_management.py, scripts/testing/ai/test_new_modules.py, scripts/utilities/check_checkin_schedules.py, tests/behavior/test_schedule_management_behavior.py, ui/dialogs/category_management_dialog.py, ui/dialogs/checkin_management_dialog.py, ui/dialogs/schedule_editor_dialog.py, ui/dialogs/task_management_dialog.py, ui/widgets/checkin_settings_widget.py, ui/widgets/period_row_widget.py, ui/widgets/task_settings_widget.py, user/user_preferences.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Schedule management and time period handling

<!-- MANUAL_ENHANCEMENT_END -->

#### `core/scheduler.py`
- **Purpose**: Task scheduling and job management
- **Dependencies**: 
  - **Local**:
    - `bot.communication_manager (CommunicationManager)` (🆕)
    - `core.error_handling (error_handler, SchedulerError, CommunicationError, handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.schedule_management (get_schedule_time_periods, is_schedule_period_active, get_current_time_periods_with_validation)` (🆕)
    - `core.schedule_management (get_schedule_time_periods)` (🆕)
    - `core.service_utilities (load_and_localize_datetime)` (🆕)
    - `core.user_data_handlers (get_all_user_ids)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `tasks.task_management (are_tasks_enabled)` (🆕)
    - `tasks.task_management (load_active_tasks, are_tasks_enabled)` (🆕)
    - `tasks.task_management (get_task_by_id)` (🆕)
    - `tasks.task_management (get_task_by_id)` (🆕)
    - `tasks.task_management (get_task_by_id, update_task)` (🆕)
    - `user.user_context (UserContext)` (🆕)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `datetime`
    - `datetime (datetime, timedelta)`
    - `datetime (datetime, timedelta)`
    - `logging`
    - `os`
    - `pytz`
    - `random`
    - `random`
    - `random`
    - `subprocess`
    - `threading`
    - `time`
    - `typing (List, Dict, Any)`
  - **Third-party**:
    - `schedule`
- **Used by**: 
  - `bot/telegram_bot.py`
  - `core/service.py`
  - `tests/behavior/test_scheduler_behavior.py`

**Dependency Changes**:
- Added: bot.communication_manager, core.error_handling, core.logger, core.schedule_management, core.service_utilities, core.user_data_handlers, tasks.task_management, user.user_context
- Removed: bot/telegram_bot.py, core/service.py, tests/behavior/test_scheduler_behavior.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Task scheduling and job management

<!-- MANUAL_ENHANCEMENT_END -->

#### `core/service.py`
- **Purpose**: Main service orchestration and management
- **Dependencies**: 
  - **Local**:
    - `bot.channel_registry (register_all_channels)` (🆕)
    - `bot.communication_manager (CommunicationManager)` (🆕)
    - `core.auto_cleanup (auto_cleanup_if_needed)` (🆕)
    - `core.config (validate_and_raise_if_invalid, print_configuration_report, ConfigValidationError)` (🆕)
    - `core.config (LOG_FILE_PATH, USER_INFO_DIR_PATH, get_user_data_dir)` (🆕)
    - `core.config (LOG_FILE_PATH)` (🆕)
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
    - `core.file_operations (verify_file_access, determine_file_path)` (🆕)
    - `core.logger (setup_logging, get_logger, get_component_logger)` (🆕)
    - `core.logger (force_restart_logging)` (🆕)
    - `core.scheduler (SchedulerManager)` (🆕)
    - `core.user_data_handlers (get_all_user_ids)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
  - **Standard Library**:
    - `atexit`
    - `datetime`
    - `json`
    - `json`
    - `logging`
    - `os`
    - `re`
    - `signal`
    - `sys`
    - `time`
    - `typing (List)`
- **Used by**: 
  - `tasks/task_management.py`
  - `tests/behavior/test_service_behavior.py`

**Dependency Changes**:
- Added: bot.channel_registry, bot.communication_manager, core.auto_cleanup, core.config, core.error_handling, core.file_operations, core.logger, core.scheduler, core.user_data_handlers
- Removed: tasks/task_management.py, tests/behavior/test_service_behavior.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Main service orchestration and management

<!-- MANUAL_ENHANCEMENT_END -->

#### `core/service_utilities.py`
- **Purpose**: Main service orchestration and management
- **Dependencies**: 
  - **Local**:
    - `core.config (SCHEDULER_INTERVAL)` (🆕)
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `json`
    - `os`
    - `psutil`
    - `pytz`
    - `requests`
    - `socket`
    - `time`
    - `typing (Optional)`
- **Used by**: 
  - `bot/communication_manager.py`
  - `bot/telegram_bot.py`
  - `core/schedule_management.py`
  - `core/scheduler.py`
  - `scripts/testing/ai/test_new_modules.py`
  - `tests/behavior/test_service_utilities_behavior.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger
- Removed: bot/communication_manager.py, bot/telegram_bot.py, core/schedule_management.py, core/scheduler.py, scripts/testing/ai/test_new_modules.py, tests/behavior/test_service_utilities_behavior.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Utility functions for service operations

<!-- MANUAL_ENHANCEMENT_END -->

#### `core/ui_management.py`
- **Purpose**: UI management and widget utilities
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.schedule_management (get_schedule_time_periods)` (🆕)
    - `ui.widgets.period_row_widget (PeriodRowWidget)` (🆕)
    - `ui.widgets.period_row_widget (PeriodRowWidget)` (🆕)
  - **Standard Library**:
    - `typing (Dict, Any, List, Optional)`
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
    - `core.config (get_user_file_path)` (🆕)
    - `core.config (get_user_data_dir)` (🆕)
    - `core.config (get_user_file_path)` (🆕)
    - `core.error_handling (handle_errors)` (🆕)
    - `core.file_operations (save_json_data)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.message_management (ensure_user_message_files)` (🆕)
    - `core.user_data_manager (UserDataManager)` (🆕)
    - `core.user_data_manager (UserDataManager)` (🆕)
    - `core.user_data_manager (update_user_index)` (🆕)
    - `core.user_data_manager (update_user_index)` (🆕)
    - `core.user_data_validation (validate_new_user_data, validate_user_update)` (🆕)
    - `core.user_management (USER_DATA_LOADERS, get_available_data_types)` (🆕)
    - `core.user_management (USER_DATA_LOADERS, register_data_loader)` (🆕)
    - `core.user_management (get_all_user_ids)` (🆕)
    - `core.user_management (update_user_schedules)` (🆕)
    - `core.user_management (clear_user_caches)` (🆕)
    - `core.user_management (ensure_category_has_default_schedule, ensure_all_categories_have_schedules)` (🆕)
  - **Standard Library**:
    - `os`
    - `typing (Dict, Any, List, Union, Optional)`
  - **Third-party**:
    - `traceback`
- **Used by**: 
  - `bot/ai_chatbot.py`
  - `bot/communication_manager.py`
  - `bot/user_context_manager.py`
  - `core/backup_manager.py`
  - `core/response_tracking.py`
  - `core/schedule_management.py`
  - `core/scheduler.py`
  - `core/service.py`
  - `core/user_data_manager.py`
  - `core/user_data_validation.py`
  - `core/user_management.py`
  - `scripts/debug/debug_category_dialog.py`
  - `scripts/debug/debug_preferences.py`
  - `scripts/migration/migrate_messaging_service.py`
  - `scripts/migration/migrate_schedule_format.py`
  - `scripts/migration/migrate_user_data_structure.py`
  - `scripts/utilities/add_checkin_schedules.py`
  - `scripts/utilities/check_checkin_schedules.py`
  - `scripts/utilities/cleanup/cleanup_user_message_files.py`
  - `scripts/utilities/restore_custom_periods.py`
  - `tasks/task_management.py`
  - `tests/behavior/test_account_management_real_behavior.py`
  - `tests/behavior/test_ai_chatbot_behavior.py`
  - `tests/behavior/test_interaction_handlers_behavior.py`
  - `tests/behavior/test_utilities_demo.py`
  - `tests/integration/test_account_lifecycle.py`
  - `tests/integration/test_account_management.py`
  - `tests/integration/test_user_creation.py`
  - `tests/ui/test_account_creation_ui.py`
  - `tests/ui/test_dialog_behavior.py`
  - `tests/ui/test_dialogs.py`
  - `tests/ui/test_widget_behavior.py`
  - `tests/unit/test_user_management.py`
  - `ui/dialogs/category_management_dialog.py`
  - `ui/dialogs/channel_management_dialog.py`
  - `ui/dialogs/checkin_management_dialog.py`
  - `ui/dialogs/task_management_dialog.py`
  - `ui/dialogs/user_profile_dialog.py`
  - `ui/ui_app_qt.py`
  - `ui/widgets/checkin_settings_widget.py`
  - `ui/widgets/task_settings_widget.py`
  - `user/user_context.py`
  - `user/user_preferences.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.file_operations, core.logger, core.message_management, core.user_data_manager, core.user_data_validation, core.user_management
- Removed: bot/ai_chatbot.py, bot/communication_manager.py, bot/user_context_manager.py, core/backup_manager.py, core/response_tracking.py, core/schedule_management.py, core/scheduler.py, core/service.py, core/user_data_manager.py, core/user_data_validation.py, core/user_management.py, scripts/debug/debug_category_dialog.py, scripts/debug/debug_preferences.py, scripts/migration/migrate_messaging_service.py, scripts/migration/migrate_schedule_format.py, scripts/migration/migrate_user_data_structure.py, scripts/utilities/add_checkin_schedules.py, scripts/utilities/check_checkin_schedules.py, scripts/utilities/cleanup/cleanup_user_message_files.py, scripts/utilities/restore_custom_periods.py, tasks/task_management.py, tests/behavior/test_account_management_real_behavior.py, tests/behavior/test_ai_chatbot_behavior.py, tests/behavior/test_interaction_handlers_behavior.py, tests/behavior/test_utilities_demo.py, tests/integration/test_account_lifecycle.py, tests/integration/test_account_management.py, tests/integration/test_user_creation.py, tests/ui/test_account_creation_ui.py, tests/ui/test_dialog_behavior.py, tests/ui/test_dialogs.py, tests/ui/test_widget_behavior.py, tests/unit/test_user_management.py, ui/dialogs/category_management_dialog.py, ui/dialogs/channel_management_dialog.py, ui/dialogs/checkin_management_dialog.py, ui/dialogs/task_management_dialog.py, ui/dialogs/user_profile_dialog.py, ui/ui_app_qt.py, ui/widgets/checkin_settings_widget.py, ui/widgets/task_settings_widget.py, user/user_context.py, user/user_preferences.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: User data handlers - provides centralized access to user data with caching and validation

<!-- MANUAL_ENHANCEMENT_END -->

#### `core/user_data_manager.py`
- **Purpose**: Enhanced user data management with references
- **Dependencies**: 
  - **Local**:
    - `core.config (USER_INFO_DIR_PATH, get_user_file_path, ensure_user_directory, get_user_data_dir, BASE_DATA_DIR)` (🆕)
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
    - `core.file_operations (load_json_data, save_json_data, get_user_file_path, get_user_data_dir)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.message_management (ensure_user_message_files)` (🆕)
    - `core.response_tracking (get_recent_checkins)` (🆕)
    - `core.response_tracking (get_recent_responses)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (get_all_user_ids)` (🆕)
    - `core.user_data_handlers (USER_DATA_LOADERS)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `time`
    - `typing (Dict, List, Optional, Any)`
    - `zipfile`
- **Used by**: 
  - `core/file_operations.py`
  - `core/message_management.py`
  - `core/user_data_handlers.py`
  - `core/user_management.py`
  - `scripts/utilities/rebuild_index.py`
  - `scripts/utilities/user_data_cli.py`
  - `tests/conftest.py`
  - `tests/integration/test_account_lifecycle.py`
  - `tests/integration/test_account_management.py`
  - `tests/ui/test_account_creation_ui.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.file_operations, core.logger, core.message_management, core.response_tracking, core.user_data_handlers
- Removed: core/file_operations.py, core/message_management.py, core/user_data_handlers.py, core/user_management.py, scripts/utilities/rebuild_index.py, scripts/utilities/user_data_cli.py, tests/conftest.py, tests/integration/test_account_lifecycle.py, tests/integration/test_account_management.py, tests/ui/test_account_creation_ui.py, ui/dialogs/account_creator_dialog.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Enhanced user data management with references and indexing

<!-- MANUAL_ENHANCEMENT_END -->

#### `core/user_data_validation.py`
- **Purpose**: User data validation and integrity checks
- **Dependencies**: 
  - **Local**:
    - `core.config (get_user_data_dir)` (🆕)
    - `core.config (get_user_file_path)` (🆕)
    - `core.error_handling (handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.message_management (get_message_categories)` (🆕)
    - `core.message_management (get_message_categories)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `datetime`
    - `datetime`
    - `datetime`
    - `os`
    - `os`
    - `re`
    - `typing (Dict, Any, Tuple, List)`
- **Used by**: 
  - `core/user_data_handlers.py`
  - `core/user_management.py`
  - `core/validation.py`
  - `tests/integration/test_account_management.py`
  - `tests/integration/test_user_creation.py`
  - `tests/ui/test_account_creation_ui.py`
  - `tests/unit/test_validation.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/channel_management_dialog.py`
  - `ui/dialogs/checkin_management_dialog.py`
  - `ui/dialogs/schedule_editor_dialog.py`
  - `ui/dialogs/task_management_dialog.py`
  - `ui/dialogs/user_profile_dialog.py`
  - `ui/ui_app_qt.py`
  - `ui/widgets/category_selection_widget.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.logger, core.message_management, core.user_data_handlers
- Removed: core/user_data_handlers.py, core/user_management.py, core/validation.py, tests/integration/test_account_management.py, tests/integration/test_user_creation.py, tests/ui/test_account_creation_ui.py, tests/unit/test_validation.py, ui/dialogs/account_creator_dialog.py, ui/dialogs/channel_management_dialog.py, ui/dialogs/checkin_management_dialog.py, ui/dialogs/schedule_editor_dialog.py, ui/dialogs/task_management_dialog.py, ui/dialogs/user_profile_dialog.py, ui/ui_app_qt.py, ui/widgets/category_selection_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: User data validation - validates user input and data integrity

<!-- MANUAL_ENHANCEMENT_END -->

#### `core/user_management.py`
- **Purpose**: Centralized user data access and management
- **Dependencies**: 
  - **Local**:
    - `core.config (ensure_user_directory)` (🆕)
    - `core.config (USER_INFO_DIR_PATH)` (🆕)
    - `core.error_handling (handle_errors)` (🆕)
    - `core.file_operations (load_json_data, save_json_data, get_user_file_path, get_user_data_dir, determine_file_path)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.message_management (get_message_categories)` (🆕)
    - `core.message_management (ensure_user_message_files)` (🆕)
    - `core.user_data_handlers (save_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data_transaction)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data)` (🆕)
    - `core.user_data_manager (update_user_index)` (🆕)
    - `core.user_data_manager (update_user_index)` (🆕)
    - `core.user_data_manager (update_user_index)` (🆕)
    - `core.user_data_manager (update_user_index)` (🆕)
    - `core.user_data_validation (validate_personalization_data)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `json`
    - `os`
    - `os`
    - `pytz`
    - `time`
    - `typing (List, Dict, Any, Optional, Union, Tuple)`
    - `uuid`
  - **Third-party**:
    - `inspect`
    - `pkgutil`
- **Used by**: 
  - `bot/discord_bot.py`
  - `bot/interaction_handlers.py`
  - `bot/interaction_manager.py`
  - `bot/telegram_bot.py`
  - `core/user_data_handlers.py`
  - `scripts/migration/migrate_schedule_format.py`
  - `scripts/migration/migrate_user_data_structure.py`
  - `scripts/test_discord_commands.py`
  - `scripts/testing/ai/test_data_integrity.py`
  - `scripts/testing/ai/test_new_modules.py`
  - `scripts/utilities/fix_user_schedules.py`
  - `scripts/utilities/restore_custom_periods.py`
  - `tasks/task_management.py`
  - `tests/behavior/test_account_management_real_behavior.py`
  - `tests/behavior/test_ai_chatbot_behavior.py`
  - `tests/behavior/test_conversation_behavior.py`
  - `tests/behavior/test_discord_bot_behavior.py`
  - `tests/behavior/test_interaction_handlers_behavior.py`
  - `tests/behavior/test_user_context_behavior.py`
  - `tests/behavior/test_utilities_demo.py`
  - `tests/integration/test_account_lifecycle.py`
  - `tests/integration/test_user_creation.py`
  - `tests/test_utilities.py`
  - `tests/ui/test_account_creation_ui.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/user_profile_dialog.py`
  - `ui/widgets/channel_selection_widget.py`
  - `ui/widgets/dynamic_list_container.py`
  - `ui/widgets/user_profile_settings_widget.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.file_operations, core.logger, core.message_management, core.user_data_handlers, core.user_data_manager, core.user_data_validation
- Removed: bot/discord_bot.py, bot/interaction_handlers.py, bot/interaction_manager.py, bot/telegram_bot.py, core/user_data_handlers.py, scripts/migration/migrate_schedule_format.py, scripts/migration/migrate_user_data_structure.py, scripts/test_discord_commands.py, scripts/testing/ai/test_data_integrity.py, scripts/testing/ai/test_new_modules.py, scripts/utilities/fix_user_schedules.py, scripts/utilities/restore_custom_periods.py, tasks/task_management.py, tests/behavior/test_account_management_real_behavior.py, tests/behavior/test_ai_chatbot_behavior.py, tests/behavior/test_conversation_behavior.py, tests/behavior/test_discord_bot_behavior.py, tests/behavior/test_interaction_handlers_behavior.py, tests/behavior/test_user_context_behavior.py, tests/behavior/test_utilities_demo.py, tests/integration/test_account_lifecycle.py, tests/integration/test_user_creation.py, tests/test_utilities.py, tests/ui/test_account_creation_ui.py, ui/dialogs/account_creator_dialog.py, ui/dialogs/user_profile_dialog.py, ui/widgets/channel_selection_widget.py, ui/widgets/dynamic_list_container.py, ui/widgets/user_profile_settings_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Centralized user data access and management

<!-- MANUAL_ENHANCEMENT_END -->

#### `core/validation.py`
- **Purpose**: Data validation utilities
- **Dependencies**: 
  - **Local**:
    - `core.user_data_validation` (🆕)
  - **Standard Library**:
    - `warnings`
- **Used by**: 
  - `scripts/testing/ai/test_new_modules.py`

**Dependency Changes**:
- Added: core.user_data_validation
- Removed: scripts/testing/ai/test_new_modules.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Data validation utilities

<!-- MANUAL_ENHANCEMENT_END -->

### `root/` - Root Files

#### `run_mhm.py`
- **Purpose**: Main entry point for the MHM application
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
  - **Standard Library**:
    - `os`
    - `subprocess`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Main entry point for the MHM application that launches the Qt-based admin interface

**Key Functions**:
- `main()`: Primary entry function that handles UI launch with proper environment setup
- Environment management: Ensures virtual environment Python is used for subprocesses
- Error handling: Comprehensive error handling with graceful fallbacks

**Special Considerations**:
- **Virtual Environment Management**: Explicitly uses `.venv/Scripts/python.exe` on Windows to ensure consistent Python environment
- **Subprocess Launch**: Launches `ui/ui_app_qt.py` as a subprocess with proper environment variables
- **Working Directory**: Sets working directory to project root for consistent file paths
- **Error Recovery**: Returns appropriate exit codes and handles keyboard interrupts gracefully
- **Cross-Platform**: Uses `CREATE_NO_WINDOW` flag on Windows to prevent console window flashing

**Usage**: This is the primary entry point for users to start the MHM system. It should be run from the project root directory.
<!-- MANUAL_ENHANCEMENT_END -->

#### `run_tests.py`
- **Purpose**: Test runner for the MHM application
- **Dependencies**: 
  - **Standard Library**:
    - `os`
    - `pathlib (Path)`
    - `subprocess`
    - `sys`
  - **Third-party**:
    - `argparse`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Comprehensive test runner for the MHM application with multiple testing modes and detailed reporting

**Key Functions**:
- `run_tests_with_pytest()`: Main test execution function with pytest integration
- `run_specific_module()`: Targeted testing for individual modules
- `run_test_categories()`: Category-based test filtering (unit, integration, behavior)
- `show_test_summary()`: Test results analysis and reporting
- `main()`: Command-line interface with argument parsing

**Special Considerations**:
- **Test Categories**: Supports unit, integration, behavior, and UI test categories
- **Coverage Analysis**: Optional coverage reporting with HTML output
- **Module-Specific Testing**: Predefined test mappings for core modules
- **Verbose Output**: Configurable verbosity levels for different testing needs
- **Error Handling**: Graceful handling of test failures and missing test files
- **Cross-Platform**: Works on Windows, Linux, and macOS

**Usage**: Primary test execution script for developers. Supports various command-line options for different testing scenarios.
<!-- MANUAL_ENHANCEMENT_END -->

### `scripts/`

#### `scripts/audit_legacy_channels.py`
- **Purpose**: Module for scripts/audit_legacy_channels.py
- **Dependencies**: 
  - **Standard Library**:
    - `json`
    - `os`
    - `pathlib (Path)`
    - `re`
    - `sys`
    - `typing (List, Dict, Tuple, Set)`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/debug/debug_category_dialog.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.user_data_handlers (get_user_data, update_user_account, update_user_preferences)` (🆕)
    - `core.user_data_handlers (get_all_user_ids)` (🆕)
    - `core.user_data_handlers (get_user_data, update_user_preferences)` (🆕)
    - `core.user_data_handlers (get_all_user_ids)` (🆕)
    - `ui.widgets.category_selection_widget (CategorySelectionWidget)` (🆕)
  - **Standard Library**:
    - `json`
    - `os`
    - `pathlib (Path)`
    - `sys`
  - **Third-party**:
    - `PySide6.QtWidgets (QApplication)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.user_data_handlers, ui.widgets.category_selection_widget
- Removed: PySide6.QtWidgets

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/debug/debug_comprehensive_prompt.py`
- **Purpose**: Bot-related module with communication dependencies
- **Dependencies**: 
  - **Local**:
    - `bot.ai_chatbot (get_ai_chatbot)` (🆕)
  - **Standard Library**:
    - `os`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.ai_chatbot

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/debug/debug_discord_connectivity.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.config (DISCORD_BOT_TOKEN)` (🆕)
    - `core.logger (get_logger)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `requests`
    - `socket`
    - `sys`
    - `time`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config, core.logger

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/debug/debug_lm_studio_timeout.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.config (LM_STUDIO_BASE_URL, LM_STUDIO_API_KEY, LM_STUDIO_MODEL)` (🆕)
  - **Standard Library**:
    - `json`
    - `os`
    - `psutil`
    - `requests`
    - `socket`
    - `sys`
    - `time`
  - **Third-party**:
    - `urllib.parse (urlparse)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config
- Removed: urllib.parse

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/debug/debug_preferences.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.file_operations (get_user_file_path, load_json_data)` (🆕)
    - `core.user_data_handlers (get_all_user_ids, update_user_preferences)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
  - **Standard Library**:
    - `json`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.file_operations, core.user_data_handlers

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/debug/discord_connectivity_diagnostic.py`
- **Purpose**: Bot-related module with communication dependencies
- **Dependencies**: 
  - **Local**:
    - `bot.communication_manager (CommunicationManager)` (🆕)
    - `bot.discord_bot (DiscordBot, DiscordConnectionStatus)` (🆕)
    - `core.logger (get_logger)` (🆕)
  - **Standard Library**:
    - `asyncio`
    - `datetime`
    - `json`
    - `os`
    - `socket`
    - `sys`
    - `time`
    - `typing (Dict, Any, List)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.communication_manager, bot.discord_bot, core.logger

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/debug/test_dns_fallback.py`
- **Purpose**: Bot-related module with communication dependencies
- **Dependencies**: 
  - **Local**:
    - `bot.discord_bot (DiscordBot)` (🆕)
    - `core.logger (get_logger)` (🆕)
  - **Standard Library**:
    - `os`
    - `sys`
    - `time`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.discord_bot, core.logger

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/focused_legacy_audit.py`
- **Purpose**: Module for scripts/focused_legacy_audit.py
- **Dependencies**: 
  - **Standard Library**:
    - `os`
    - `pathlib (Path)`
    - `re`
    - `sys`
    - `typing (List, Dict)`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/migration/migrate_messaging_service.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.file_operations (get_user_file_path, load_json_data, save_json_data)` (🆕)
    - `core.logger (get_logger)` (🆕)
    - `core.user_data_handlers (get_all_user_ids)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `shutil`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.file_operations, core.logger, core.user_data_handlers

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/migration/migrate_schedule_format.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.logger (setup_logging, get_logger)` (🆕)
    - `core.user_data_handlers (get_all_user_ids, update_user_account, update_user_preferences)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_management (load_user_schedules_data, save_user_schedules_data)` (🆕)
  - **Standard Library**:
    - `json`
    - `os`
    - `pathlib (Path)`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.logger, core.user_data_handlers, core.user_management

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/migration/migrate_schedules_cleanup.py`
- **Purpose**: Module for scripts/migration/migrate_schedules_cleanup.py
- **Dependencies**: 
  - **Standard Library**:
    - `json`
    - `os`
  - **Third-party**:
    - `glob`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/migration/migrate_sent_messages.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.config (USER_INFO_DIR_PATH)` (🆕)
    - `core.logger (get_logger)` (🆕)
  - **Standard Library**:
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config, core.logger

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/migration/migrate_user_data_structure.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.config (BASE_DATA_DIR, USE_USER_SUBDIRECTORIES)` (🆕)
    - `core.file_operations (load_json_data, save_json_data)` (🆕)
    - `core.logger (setup_logging, get_logger)` (🆕)
    - `core.personalization_management (load_personalization_data)` (🆕)
    - `core.user_data_handlers (get_all_user_ids)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_management (get_user_info)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
    - `typing (Dict, Any, Optional)`
  - **Third-party**:
    - `argparse`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config, core.file_operations, core.logger, core.personalization_management, core.user_data_handlers, core.user_management

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/test_ai_parsing.py`
- **Purpose**: Bot-related module with communication dependencies
- **Dependencies**: 
  - **Local**:
    - `bot.enhanced_command_parser (get_enhanced_command_parser, ParsingResult, ParsedCommand)` (🆕)
  - **Standard Library**:
    - `os`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.enhanced_command_parser

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/test_ai_raw.py`
- **Purpose**: Bot-related module with communication dependencies
- **Dependencies**: 
  - **Local**:
    - `bot.ai_chatbot (get_ai_chatbot)` (🆕)
  - **Standard Library**:
    - `json`
    - `os`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.ai_chatbot

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/test_centralized_config.py`
- **Purpose**: Bot-related module with communication dependencies
- **Dependencies**: 
  - **Local**:
    - `bot.ai_chatbot (get_ai_chatbot)` (🆕)
    - `bot.enhanced_command_parser (get_enhanced_command_parser)` (🆕)
    - `core.config (AI_CONNECTION_TEST_TIMEOUT, AI_API_CALL_TIMEOUT, AI_COMMAND_PARSING_TIMEOUT, AI_PERSONALIZED_MESSAGE_TIMEOUT, AI_CONTEXTUAL_RESPONSE_TIMEOUT, AI_QUICK_RESPONSE_TIMEOUT, AI_RULE_BASED_HIGH_CONFIDENCE_THRESHOLD, AI_AI_ENHANCED_CONFIDENCE_THRESHOLD, AI_RULE_BASED_FALLBACK_THRESHOLD, AI_AI_PARSING_BASE_CONFIDENCE, AI_AI_PARSING_PARTIAL_CONFIDENCE)` (🆕)
  - **Standard Library**:
    - `os`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.ai_chatbot, bot.enhanced_command_parser, core.config

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/test_comprehensive_fixes.py`
- **Purpose**: Bot-related module with communication dependencies
- **Dependencies**: 
  - **Local**:
    - `bot.enhanced_command_parser (get_enhanced_command_parser)` (🆕)
    - `bot.interaction_handlers (TaskManagementHandler)` (🆕)
    - `bot.interaction_manager (handle_user_message)` (🆕)
    - `core.logger (get_logger)` (🆕)
  - **Standard Library**:
    - `os`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.enhanced_command_parser, bot.interaction_handlers, bot.interaction_manager, core.logger

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/test_discord_commands.py`
- **Purpose**: Bot-related module with communication dependencies
- **Dependencies**: 
  - **Local**:
    - `bot.enhanced_command_parser (EnhancedCommandParser)` (🆕)
    - `bot.interaction_handlers (TaskManagementHandler, CheckinHandler, ProfileHandler, HelpHandler, ScheduleManagementHandler, AnalyticsHandler, ParsedCommand, get_interaction_handler, get_all_handlers)` (🆕)
    - `core.logger (get_logger)` (🆕)
    - `core.user_management (load_user_account_data)` (🆕)
  - **Standard Library**:
    - `asyncio`
    - `datetime`
    - `json`
    - `os`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.enhanced_command_parser, bot.interaction_handlers, core.logger, core.user_management

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/test_discord_connection.py`
- **Purpose**: Bot-related module with communication dependencies
- **Dependencies**: 
  - **Local**:
    - `bot.base_channel (ChannelConfig)` (🆕)
    - `bot.discord_bot (DiscordBot)` (🆕)
  - **Standard Library**:
    - `asyncio`
    - `os`
    - `sys`
  - **Third-party**:
    - `traceback`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.base_channel, bot.discord_bot

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/test_enhanced_discord_commands.py`
- **Purpose**: Bot-related module with communication dependencies
- **Dependencies**: 
  - **Local**:
    - `bot.enhanced_command_parser (EnhancedCommandParser)` (🆕)
    - `bot.interaction_handlers (get_interaction_handler, get_all_handlers)` (🆕)
    - `core.logger (get_logger)` (🆕)
  - **Standard Library**:
    - `os`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.enhanced_command_parser, bot.interaction_handlers, core.logger

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/test_enhanced_parser_direct.py`
- **Purpose**: Bot-related module with communication dependencies
- **Dependencies**: 
  - **Local**:
    - `bot.enhanced_command_parser (get_enhanced_command_parser, ParsingResult, ParsedCommand)` (🆕)
  - **Standard Library**:
    - `logging`
    - `os`
    - `sys`
  - **Third-party**:
    - `traceback`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.enhanced_command_parser

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/test_task_response_formatting.py`
- **Purpose**: Bot-related module with communication dependencies
- **Dependencies**: 
  - **Local**:
    - `bot.enhanced_command_parser (get_enhanced_command_parser)` (🆕)
    - `bot.interaction_handlers (TaskManagementHandler)` (🆕)
    - `bot.interaction_handlers (ParsedCommand)` (🆕)
    - `bot.interaction_manager (handle_user_message)` (🆕)
    - `core.logger (get_logger)` (🆕)
  - **Standard Library**:
    - `os`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.enhanced_command_parser, bot.interaction_handlers, bot.interaction_manager, core.logger

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/testing/ai/test_ai_with_clear_cache.py`
- **Purpose**: Bot-related module with communication dependencies
- **Dependencies**: 
  - **Local**:
    - `bot.ai_chatbot (get_ai_chatbot)` (🆕)
  - **Standard Library**:
    - `os`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.ai_chatbot

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/testing/ai/test_comprehensive_ai.py`
- **Purpose**: Bot-related module with communication dependencies
- **Dependencies**: 
  - **Local**:
    - `bot.ai_chatbot (get_ai_chatbot)` (🆕)
  - **Standard Library**:
    - `os`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.ai_chatbot

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/testing/ai/test_data_integrity.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.file_operations (get_user_file_path, load_json_data)` (🆕)
    - `core.user_management (get_all_user_ids, load_user_account_data, load_user_preferences_data, load_user_context_data, update_user_account, update_user_preferences, update_user_context, create_new_user)` (🆕)
  - **Standard Library**:
    - `json`
    - `os`
    - `shutil`
  - **Third-party**:
    - `tempfile`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.file_operations, core.user_management

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/testing/ai/test_lm_studio.py`
- **Purpose**: Bot-related module with communication dependencies
- **Dependencies**: 
  - **Local**:
    - `bot.ai_chatbot (get_ai_chatbot)` (🆕)
    - `core.config (LM_STUDIO_BASE_URL, LM_STUDIO_API_KEY, LM_STUDIO_MODEL)` (🆕)
  - **Standard Library**:
    - `os`
    - `requests`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.ai_chatbot, core.config

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/testing/ai/test_new_modules.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.file_operations (verify_file_access, determine_file_path, load_json_data, save_json_data, create_user_files)` (🆕)
    - `core.message_management (get_message_categories, load_default_messages)` (🆕)
    - `core.response_tracking (get_recent_checkins, is_user_checkins_enabled, get_user_checkin_preferences)` (🆕)
    - `core.schedule_management (get_schedule_time_periods, get_current_day_names, validate_and_format_time)` (🆕)
    - `core.service_utilities (create_reschedule_request, is_service_running, Throttler, InvalidTimeFormatError, throttler)` (🆕)
    - `core.user_management (get_all_user_ids, get_user_info, get_user_preferences)` (🆕)
    - `core.validation (is_valid_email, is_valid_phone, title_case)` (🆕)
  - **Standard Library**:
    - `os`
    - `sys`
  - **Third-party**:
    - `traceback`
    - `traceback`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.file_operations, core.message_management, core.response_tracking, core.schedule_management, core.service_utilities, core.user_management, core.validation

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/testing/analyze_documentation_overlap.py`
- **Purpose**: Module for scripts/testing/analyze_documentation_overlap.py
- **Dependencies**: 
  - **Standard Library**:
    - `os`
    - `pathlib (Path)`
    - `re`
    - `typing (Dict, List, Set)`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/testing/test_user_data_analysis.py`
- **Purpose**: Bot-related module with communication dependencies
- **Dependencies**: 
  - **Local**:
    - `bot.ai_chatbot (get_ai_chatbot)` (🆕)
  - **Standard Library**:
    - `os`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.ai_chatbot

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/testing/test_utils_functions.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.utils` (🆕)
    - `core.utils (load_json_data, save_json_data, get_all_user_ids, get_user_info, get_user_preferences, get_message_categories)` (🆕)
    - `core.utils` (🆕)
    - `core.utils` (🆕)
    - `core.utils` (🆕)
  - **Standard Library**:
    - `os`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.utils

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/testing/validate_config.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.config (validate_all_configuration, print_configuration_report)` (🆕)
    - `core.config (validate_core_paths)` (🆕)
  - **Standard Library**:
    - `os`
    - `pathlib (Path)`
    - `sys`
  - **Third-party**:
    - `argparse`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/utilities/add_checkin_schedules.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.file_operations (get_user_file_path, load_json_data, save_json_data)` (🆕)
    - `core.logger (get_logger)` (🆕)
    - `core.user_data_handlers (get_all_user_ids)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.file_operations, core.logger, core.user_data_handlers

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/utilities/check_checkin_schedules.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.logger (get_logger)` (🆕)
    - `core.schedule_management (get_schedule_time_periods)` (🆕)
    - `core.user_data_handlers (get_all_user_ids)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.logger, core.schedule_management, core.user_data_handlers

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/utilities/cleanup/cleanup_data_test_users.py`
- **Purpose**: Module for scripts/utilities/cleanup/cleanup_data_test_users.py
- **Dependencies**: 
  - **Standard Library**:
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/utilities/cleanup/cleanup_real_test_users.py`
- **Purpose**: Module for scripts/utilities/cleanup/cleanup_real_test_users.py
- **Dependencies**: 
  - **Standard Library**:
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/utilities/cleanup/cleanup_test_data.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.config (BASE_DATA_DIR, USER_INFO_DIR_PATH)` (🆕)
    - `core.logger (get_logger)` (🆕)
  - **Standard Library**:
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config, core.logger

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/utilities/cleanup/cleanup_user_message_files.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.config (get_user_data_dir, DEFAULT_MESSAGES_DIR_PATH)` (🆕)
    - `core.file_operations (load_json_data, save_json_data)` (🆕)
    - `core.logger (get_logger)` (🆕)
    - `core.message_management (populate_user_messages_from_defaults)` (🆕)
    - `core.user_data_handlers (get_all_user_ids)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config, core.file_operations, core.logger, core.message_management, core.user_data_handlers

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/utilities/cleanup_duplicate_messages.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.config (MESSAGES_BY_CATEGORY_DIR_PATH)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
  - **Third-party**:
    - `argparse`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/utilities/cleanup_test_users.py`
- **Purpose**: Module for scripts/utilities/cleanup_test_users.py
- **Dependencies**: 
  - **Standard Library**:
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/utilities/fix_user_schedules.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.user_management (load_user_schedules_data, save_user_schedules_data)` (🆕)
  - **Standard Library**:
    - `os`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.user_management

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/utilities/rebuild_index.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.logger (setup_logging, get_logger)` (🆕)
    - `core.user_data_manager (rebuild_user_index)` (🆕)
  - **Standard Library**:
    - `os`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.logger, core.user_data_manager

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/utilities/refactoring/analyze_migration_needs.py`
- **Purpose**: Module for scripts/utilities/refactoring/analyze_migration_needs.py
- **Dependencies**: 
  - **Standard Library**:
    - `os`
    - `re`
  - **Third-party**:
    - `ast`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/utilities/refactoring/find_legacy_get_user_data.py`
- **Purpose**: Module for scripts/utilities/refactoring/find_legacy_get_user_data.py
- **Dependencies**: 
  - **Standard Library**:
    - `os`
    - `re`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/utilities/refactoring/find_legacy_imports.py`
- **Purpose**: Module for scripts/utilities/refactoring/find_legacy_imports.py
- **Dependencies**: 
  - **Standard Library**:
    - `os`
    - `re`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/utilities/refactoring/fix_broken_imports.py`
- **Purpose**: Module for scripts/utilities/refactoring/fix_broken_imports.py
- **Dependencies**: 
  - **Standard Library**:
    - `datetime`
    - `os`
    - `re`
    - `shutil`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/utilities/refactoring/migrate_legacy_imports.py`
- **Purpose**: Module for scripts/utilities/refactoring/migrate_legacy_imports.py
- **Dependencies**: 
  - **Standard Library**:
    - `datetime`
    - `os`
    - `re`
    - `shutil`
- **Used by**: None (not imported by other modules)

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/utilities/restore_custom_periods.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.logger (setup_logging, get_logger)` (🆕)
    - `core.user_data_handlers (get_all_user_ids)` (🆕)
    - `core.user_management (load_user_schedules_data, save_user_schedules_data)` (🆕)
  - **Standard Library**:
    - `json`
    - `os`
    - `pathlib (Path)`
    - `sys`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.logger, core.user_data_handlers, core.user_management

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `scripts/utilities/user_data_cli.py`
- **Purpose**: Core system module with heavy core dependencies
- **Dependencies**: 
  - **Local**:
    - `core.logger (get_logger)` (🆕)
    - `core.user_data_manager (user_data_manager, update_message_references, backup_user_data, get_user_data_summary, update_user_index, rebuild_user_index)` (🆕)
    - `core.utils (get_all_user_ids)` (🆕)
    - `core.utils (load_user_info_data)` (🆕)
  - **Standard Library**:
    - `json`
    - `os`
    - `sys`
  - **Third-party**:
    - `argparse`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.logger, core.user_data_manager, core.utils

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

### `tasks/` - Task Management

#### `tasks/task_management.py`
- **Purpose**: Task management and scheduling
- **Dependencies**: 
  - **Local**:
    - `core.config (get_user_data_dir)` (🆕)
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
    - `core.file_operations (load_json_data, save_json_data, determine_file_path)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.service (get_scheduler_manager)` (🆕)
    - `core.service (get_scheduler_manager)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_management (load_user_preferences_data)` (🆕)
    - `core.user_management (save_user_preferences_data)` (🆕)
    - `core.user_management (save_user_preferences_data)` (🆕)
    - `core.user_management (save_user_preferences_data)` (🆕)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `json`
    - `os`
    - `typing (Dict, List, Optional, Any)`
    - `uuid`
- **Used by**: 
  - `bot/communication_manager.py`
  - `bot/interaction_handlers.py`
  - `bot/interaction_manager.py`
  - `core/scheduler.py`
  - `tests/behavior/test_account_management_real_behavior.py`
  - `tests/behavior/test_interaction_handlers_behavior.py`
  - `tests/behavior/test_task_behavior.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/task_crud_dialog.py`
  - `ui/dialogs/task_edit_dialog.py`
  - `ui/dialogs/task_management_dialog.py`
  - `ui/widgets/tag_widget.py`
  - `ui/widgets/task_settings_widget.py`

**Dependency Changes**:
- Added: core.config, core.error_handling, core.file_operations, core.logger, core.service, core.user_data_handlers, core.user_management
- Removed: bot/communication_manager.py, bot/interaction_handlers.py, bot/interaction_manager.py, core/scheduler.py, tests/behavior/test_account_management_real_behavior.py, tests/behavior/test_interaction_handlers_behavior.py, tests/behavior/test_task_behavior.py, ui/dialogs/account_creator_dialog.py, ui/dialogs/task_crud_dialog.py, ui/dialogs/task_edit_dialog.py, ui/dialogs/task_management_dialog.py, ui/widgets/tag_widget.py, ui/widgets/task_settings_widget.py

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

### `tests/` - Test Files

#### `tests/behavior/test_account_management_real_behavior.py`
- **Purpose**: Behavior tests for account management real behavior
- **Dependencies**: 
  - **Local**:
    - `core.config` (🆕)
    - `core.config` (🆕)
    - `core.config` (🆕)
    - `core.config` (🆕)
    - `core.config` (🆕)
    - `core.config` (🆕)
    - `core.config` (🆕)
    - `core.message_management (create_message_file_from_defaults)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_management (save_user_schedules_data)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (save_user_schedules_data)` (🆕)
    - `tasks.task_management (ensure_task_directory)` (🆕)
    - `tests.test_utilities (TestDataManager)` (🆕)
    - `tests.test_utilities (TestUserFactory, TestDataFactory)` (🆕)
    - `tests.test_utilities (TestDataManager)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
    - `time`
  - **Third-party**:
    - `pytest`
    - `tempfile`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config, core.message_management, core.user_data_handlers, core.user_management, tasks.task_management, tests.test_utilities

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Real behavior tests for account management

<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/behavior/test_ai_chatbot_behavior.py`
- **Purpose**: Behavior tests for ai chatbot behavior
- **Dependencies**: 
  - **Local**:
    - `bot.ai_chatbot (AIChatBotSingleton, SystemPromptLoader, ResponseCache, get_ai_chatbot)` (🆕)
    - `bot.conversation_manager (ConversationManager)` (🆕)
    - `bot.user_context_manager (UserContextManager)` (🆕)
    - `core.config (ensure_user_directory)` (🆕)
    - `core.response_tracking (get_recent_chat_interactions, store_chat_interaction)` (🆕)
    - `core.user_data_handlers (get_user_data, save_user_data)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (load_user_account_data)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `json`
    - `os`
    - `threading`
    - `time`
    - `time`
  - **Third-party**:
    - `pytest`
    - `tempfile`
    - `unittest.mock (patch, MagicMock, mock_open)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.ai_chatbot, bot.conversation_manager, bot.user_context_manager, core.config, core.response_tracking, core.user_data_handlers, core.user_management, tests.test_utilities
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/behavior/test_auto_cleanup_behavior.py`
- **Purpose**: Behavior tests for auto cleanup behavior
- **Dependencies**: 
  - **Local**:
    - `core.auto_cleanup (get_last_cleanup_timestamp, update_cleanup_timestamp, should_run_cleanup, find_pycache_dirs, find_pyc_files, calculate_cache_size, perform_cleanup, auto_cleanup_if_needed, get_cleanup_status, CLEANUP_TRACKER_FILE, DEFAULT_CLEANUP_INTERVAL_DAYS)` (🆕)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
    - `time`
  - **Third-party**:
    - `pytest`
    - `unittest.mock (patch, Mock)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.auto_cleanup
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/behavior/test_checkin_analytics_behavior.py`
- **Purpose**: Behavior tests for checkin analytics behavior
- **Dependencies**: 
  - **Local**:
    - `core.checkin_analytics (CheckinAnalytics)` (🆕)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `json`
    - `pathlib (Path)`
    - `statistics`
    - `sys`
  - **Third-party**:
    - `pytest`
    - `unittest.mock (patch, Mock)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.checkin_analytics
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/behavior/test_communication_behavior.py`
- **Purpose**: Behavior tests for communication behavior
- **Dependencies**: 
  - **Local**:
    - `bot.base_channel (BaseChannel, ChannelConfig, ChannelStatus, ChannelType)` (🆕)
    - `bot.communication_manager (CommunicationManager, QueuedMessage, BotInitializationError, MessageSendError)` (🆕)
    - `core.config (get_user_data_dir)` (🆕)
  - **Standard Library**:
    - `asyncio`
    - `datetime`
    - `os`
    - `shutil`
    - `sys`
  - **Third-party**:
    - `pytest`
    - `tempfile`
    - `unittest.mock (Mock, patch, MagicMock, AsyncMock)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.base_channel, bot.communication_manager, core.config
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Behavior tests for communication system

<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/behavior/test_conversation_behavior.py`
- **Purpose**: Behavior tests for conversation behavior
- **Dependencies**: 
  - **Local**:
    - `bot.conversation_manager (ConversationManager, FLOW_NONE, FLOW_checkin, CHECKIN_START, CHECKIN_MOOD, CHECKIN_REFLECTION)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (update_user_preferences)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `json`
    - `os`
  - **Third-party**:
    - `pytest`
    - `unittest.mock (patch, MagicMock)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.conversation_manager, core.user_management, tests.test_utilities
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/behavior/test_discord_bot_behavior.py`
- **Purpose**: Behavior tests for discord bot behavior
- **Dependencies**: 
  - **Local**:
    - `bot.base_channel (ChannelStatus, ChannelType)` (🆕)
    - `bot.conversation_manager (conversation_manager)` (🆕)
    - `bot.discord_bot (DiscordBot, DiscordConnectionStatus)` (🆕)
    - `core.config (ensure_user_directory)` (🆕)
    - `core.user_management (save_user_account_data, save_user_preferences_data)` (🆕)
    - `core.user_management (get_user_id_by_discord_user_id, get_all_user_ids)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
  - **Standard Library**:
    - `asyncio`
    - `socket`
    - `threading`
    - `time`
  - **Third-party**:
    - `discord`
    - `discord.ext (commands)`
    - `pytest`
    - `queue`
    - `unittest.mock (patch, MagicMock, AsyncMock, call)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.base_channel, bot.conversation_manager, bot.discord_bot, core.config, core.user_management, tests.test_utilities
- Removed: discord.ext, unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/behavior/test_interaction_handlers_behavior.py`
- **Purpose**: Behavior tests for interaction handlers behavior
- **Dependencies**: 
  - **Local**:
    - `bot.interaction_handlers (InteractionHandler, TaskManagementHandler, CheckinHandler, ProfileHandler, ScheduleManagementHandler, AnalyticsHandler, HelpHandler, InteractionResponse, ParsedCommand, get_interaction_handler, get_all_handlers)` (🆕)
    - `core.user_data_handlers (get_user_data, save_user_data)` (🆕)
    - `core.user_management (load_user_account_data, save_user_account_data)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (update_user_context)` (🆕)
    - `tasks.task_management (create_task, load_active_tasks, complete_task, delete_task)` (🆕)
    - `tests.test_utilities (TestUserFactory, create_test_user)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `json`
    - `os`
  - **Third-party**:
    - `pytest`
    - `tempfile`
    - `unittest.mock (patch, MagicMock, mock_open)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.interaction_handlers, core.user_data_handlers, core.user_management, tasks.task_management, tests.test_utilities
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/behavior/test_logger_behavior.py`
- **Purpose**: Behavior tests for logger behavior
- **Dependencies**: 
  - **Local**:
    - `core.logger (get_logger, setup_logging, suppress_noisy_logging, set_console_log_level, toggle_verbose_logging, get_verbose_mode, set_verbose_mode, disable_module_logging, get_log_file_info, cleanup_old_logs, force_restart_logging, BackupDirectoryRotatingFileHandler, get_log_level_from_env)` (🆕)
  - **Standard Library**:
    - `logging`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
  - **Third-party**:
    - `pytest`
    - `tempfile`
    - `unittest.mock (patch, Mock)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.logger
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/behavior/test_message_behavior.py`
- **Purpose**: Behavior tests for message behavior
- **Dependencies**: 
  - **Local**:
    - `core.config (get_user_data_dir)` (🆕)
    - `core.config (DEFAULT_MESSAGES_DIR_PATH)` (🆕)
    - `core.message_management (get_message_categories, load_default_messages, add_message, edit_message, update_message, delete_message, get_last_10_messages, store_sent_message, create_message_file_from_defaults, ensure_user_message_files)` (🆕)
  - **Standard Library**:
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
  - **Third-party**:
    - `pytest`
    - `tempfile`
    - `unittest.mock (Mock, patch, MagicMock, mock_open)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config, core.message_management
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Behavior tests for message system

<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/behavior/test_response_tracking_behavior.py`
- **Purpose**: Behavior tests for response tracking behavior
- **Dependencies**: 
  - **Local**:
    - `core.response_tracking (store_user_response, store_checkin_response, store_chat_interaction, get_recent_responses, get_recent_checkins, get_recent_chat_interactions, get_user_checkin_preferences, is_user_checkins_enabled, get_user_checkin_questions, get_user_info_for_tracking, track_user_response)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
  - **Third-party**:
    - `pytest`
    - `unittest.mock (patch, MagicMock)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.response_tracking
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/behavior/test_schedule_management_behavior.py`
- **Purpose**: Behavior tests for schedule management behavior
- **Dependencies**: 
  - **Local**:
    - `core.schedule_management (get_schedule_time_periods, set_schedule_period_active, is_schedule_period_active, get_current_time_periods_with_validation, add_schedule_period, edit_schedule_period, delete_schedule_period, clear_schedule_periods_cache, validate_and_format_time, time_24h_to_12h_display, time_12h_display_to_24h, get_current_day_names, set_schedule_periods, get_schedule_days, set_schedule_days)` (🆕)
    - `core.schedule_management (_schedule_periods_cache)` (🆕)
    - `core.schedule_management (_schedule_periods_cache)` (🆕)
    - `core.schedule_management (_schedule_periods_cache)` (🆕)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `json`
    - `os`
    - `time`
  - **Third-party**:
    - `pytest`
    - `unittest.mock (patch, Mock)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.schedule_management
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/behavior/test_scheduler_behavior.py`
- **Purpose**: Behavior tests for scheduler behavior
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (SchedulerError)` (🆕)
    - `core.scheduler (SchedulerManager, schedule_all_task_reminders, cleanup_task_reminders, get_user_categories, process_user_schedules, get_user_task_preferences, get_user_checkin_preferences)` (🆕)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `json`
    - `os`
    - `pytz`
    - `time`
  - **Third-party**:
    - `pytest`
    - `tempfile`
    - `unittest.mock (patch, Mock, MagicMock)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling, core.scheduler
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Behavior tests for scheduler system

<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/behavior/test_service_behavior.py`
- **Purpose**: Behavior tests for service behavior
- **Dependencies**: 
  - **Local**:
    - `core.config (get_user_data_dir)` (🆕)
    - `core.service (MHMService, InitializationError, main, get_user_categories)` (🆕)
  - **Standard Library**:
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `signal`
    - `sys`
    - `time`
  - **Third-party**:
    - `pytest`
    - `tempfile`
    - `unittest.mock (Mock, patch, MagicMock)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config, core.service
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Behavior tests for service system

<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/behavior/test_service_utilities_behavior.py`
- **Purpose**: Behavior tests for service utilities behavior
- **Dependencies**: 
  - **Local**:
    - `core.service_utilities (Throttler, InvalidTimeFormatError, create_reschedule_request, is_service_running, wait_for_network, load_and_localize_datetime, title_case)` (🆕)
    - `core.service_utilities (is_service_running)` (🆕)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `json`
    - `os`
    - `time`
  - **Third-party**:
    - `pytest`
    - `unittest.mock (patch, MagicMock, mock_open)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.service_utilities
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/behavior/test_task_behavior.py`
- **Purpose**: Behavior tests for task behavior
- **Dependencies**: 
  - **Local**:
    - `core.config (get_user_data_dir)` (🆕)
    - `tasks.task_management (ensure_task_directory, load_active_tasks, save_active_tasks, load_completed_tasks, save_completed_tasks, create_task, update_task, complete_task, delete_task, get_task_by_id, get_tasks_due_soon, are_tasks_enabled, get_user_task_stats, TaskManagementError)` (🆕)
  - **Standard Library**:
    - `datetime (datetime, date, timedelta)`
    - `json`
    - `os`
    - `shutil`
    - `sys`
  - **Third-party**:
    - `pytest`
    - `tempfile`
    - `unittest.mock (Mock, patch, MagicMock)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config, tasks.task_management
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Behavior tests for task management

<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/behavior/test_ui_app_behavior.py`
- **Purpose**: Behavior tests for ui app behavior
- **Dependencies**: 
  - **Local**:
    - `ui.ui_app_qt (MHMManagerUI, ServiceManager)` (🆕)
  - **Standard Library**:
    - `json`
    - `os`
    - `sys`
  - **Third-party**:
    - `PySide6.QtCore (QTimer)`
    - `PySide6.QtWidgets (QApplication)`
    - `pytest`
    - `unittest.mock (patch, MagicMock, mock_open)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: ui.ui_app_qt
- Removed: PySide6.QtCore, PySide6.QtWidgets, unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/behavior/test_user_context_behavior.py`
- **Purpose**: Behavior tests for user context behavior
- **Dependencies**: 
  - **Local**:
    - `bot.user_context_manager (UserContextManager)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (update_user_context)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
    - `user.user_context (UserContext)` (🆕)
    - `user.user_preferences (UserPreferences)` (🆕)
  - **Standard Library**:
    - `datetime (datetime, timedelta)`
    - `json`
    - `os`
  - **Third-party**:
    - `pytest`
    - `unittest.mock (patch, MagicMock)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.user_context_manager, core.user_management, tests.test_utilities, user.user_context, user.user_preferences
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/behavior/test_utilities_demo.py`
- **Purpose**: Behavior tests for utilities demo
- **Dependencies**: 
  - **Local**:
    - `core.config (get_user_data_dir)` (🆕)
    - `core.config (get_user_data_dir)` (🆕)
    - `core.config (get_user_data_dir)` (🆕)
    - `core.config (get_user_data_dir)` (🆕)
    - `core.config` (🆕)
    - `core.config (get_user_data_dir)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (load_user_account_data)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (load_user_account_data)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (load_user_context_data)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (load_user_schedules_data)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `tests.test_utilities (TestUserFactory, TestDataManager, TestUserDataFactory, create_test_user, setup_test_data_environment, cleanup_test_data_environment)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
  - **Standard Library**:
    - `json`
    - `os`
  - **Third-party**:
    - `pytest`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config, core.user_data_handlers, core.user_management, tests.test_utilities

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/conftest.py`
- **Purpose**: Test file for conftest
- **Dependencies**: 
  - **Local**:
    - `core.config (BASE_DATA_DIR, USER_INFO_DIR_PATH)` (🆕)
    - `core.config` (🆕)
    - `core.user_data_manager (update_user_index)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `logging`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
    - `uuid`
    - `uuid`
  - **Third-party**:
    - `pytest`
    - `tempfile`
    - `unittest.mock (Mock, patch)`
    - `unittest.mock (patch)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config, core.user_data_manager
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Test configuration and fixtures

<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/integration/test_account_lifecycle.py`
- **Purpose**: Integration tests for account lifecycle
- **Dependencies**: 
  - **Local**:
    - `core.config` (🆕)
    - `core.config (BASE_DATA_DIR)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data)` (🆕)
    - `core.user_data_manager (load_json_data)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (update_user_account, update_user_preferences)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (save_user_schedules_data)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
    - `tests.test_utilities (TestUserFactory, TestDataFactory)` (🆕)
  - **Standard Library**:
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
  - **Third-party**:
    - `pytest`
    - `tempfile`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config, core.user_data_handlers, core.user_data_manager, core.user_management, tests.test_utilities

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Integration tests for account lifecycle

<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/integration/test_account_management.py`
- **Purpose**: Integration tests for account management
- **Dependencies**: 
  - **Local**:
    - `core.file_operations (get_user_file_path)` (🆕)
    - `core.user_data_handlers (get_user_data, update_user_account, update_user_preferences, update_user_context, save_user_data, get_all_user_ids)` (🆕)
    - `core.user_data_handlers (get_user_data, save_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data, save_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data, save_user_data)` (🆕)
    - `core.user_data_manager (UserDataManager)` (🆕)
    - `core.user_data_manager (update_user_index)` (🆕)
    - `core.user_data_validation (validate_user_update)` (🆕)
    - `user.user_context (UserContext)` (🆕)
  - **Standard Library**:
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
    - `time`
  - **Third-party**:
    - `pytest`
    - `tempfile`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.file_operations, core.user_data_handlers, core.user_data_manager, core.user_data_validation, user.user_context

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Integration tests for account management

<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/integration/test_user_creation.py`
- **Purpose**: Integration tests for user creation
- **Dependencies**: 
  - **Local**:
    - `core.file_operations (create_user_files)` (🆕)
    - `core.user_data_handlers (get_user_data, save_user_data, update_user_account, update_user_preferences, update_user_context, update_user_schedules)` (🆕)
    - `core.user_data_validation (is_valid_email, validate_time_format)` (🆕)
    - `core.user_management (create_new_user)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (update_user_context)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `pathlib (Path)`
  - **Third-party**:
    - `pytest`
    - `tempfile`
    - `unittest.mock (patch, Mock)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.file_operations, core.user_data_handlers, core.user_data_validation, core.user_management, tests.test_utilities
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Integration tests for user creation

<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/test_utilities.py`
- **Purpose**: Test file for utilities
- **Dependencies**: 
  - **Local**:
    - `core.config` (🆕)
    - `core.config` (🆕)
    - `core.config (get_user_data_dir)` (🆕)
    - `core.config` (🆕)
    - `core.config` (🆕)
    - `core.file_operations (ensure_user_directory)` (🆕)
    - `core.user_management (create_new_user, save_user_account_data, save_user_preferences_data)` (🆕)
    - `core.user_management (create_new_user)` (🆕)
    - `core.user_management (create_new_user)` (🆕)
    - `core.user_management (create_new_user)` (🆕)
    - `core.user_management (create_new_user)` (🆕)
    - `core.user_management (create_new_user)` (🆕)
    - `core.user_management (create_new_user)` (🆕)
    - `core.user_management (create_new_user)` (🆕)
    - `core.user_management (save_user_schedules_data)` (🆕)
    - `core.user_management (create_new_user)` (🆕)
    - `core.user_management (create_new_user)` (🆕)
    - `core.user_management (create_new_user)` (🆕)
    - `core.user_management (create_new_user)` (🆕)
    - `core.user_management (create_new_user)` (🆕)
    - `core.user_management (create_new_user)` (🆕)
    - `core.user_management (create_new_user)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
    - `core.user_management (get_user_id_by_internal_username)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `datetime (datetime, timedelta)`
    - `datetime (datetime, timedelta)`
    - `json`
    - `logging`
    - `os`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
    - `typing (Dict, Any, Optional, List)`
    - `uuid`
    - `uuid`
    - `uuid`
  - **Third-party**:
    - `tempfile`
    - `unittest.mock (patch)`
    - `unittest.mock (patch)`
    - `unittest.mock (patch)`
    - `unittest.mock (patch)`
- **Used by**: 
  - `tests/behavior/test_account_management_real_behavior.py`
  - `tests/behavior/test_ai_chatbot_behavior.py`
  - `tests/behavior/test_conversation_behavior.py`
  - `tests/behavior/test_discord_bot_behavior.py`
  - `tests/behavior/test_interaction_handlers_behavior.py`
  - `tests/behavior/test_user_context_behavior.py`
  - `tests/behavior/test_utilities_demo.py`
  - `tests/integration/test_account_lifecycle.py`
  - `tests/integration/test_user_creation.py`
  - `tests/ui/test_account_creation_ui.py`
  - `tests/ui/test_widget_behavior.py`
  - `tests/unit/test_file_operations.py`
  - `tests/unit/test_user_management.py`

**Dependency Changes**:
- Added: core.config, core.file_operations, core.user_management
- Removed: tests/behavior/test_account_management_real_behavior.py, tests/behavior/test_ai_chatbot_behavior.py, tests/behavior/test_conversation_behavior.py, tests/behavior/test_discord_bot_behavior.py, tests/behavior/test_interaction_handlers_behavior.py, tests/behavior/test_user_context_behavior.py, tests/behavior/test_utilities_demo.py, tests/integration/test_account_lifecycle.py, tests/integration/test_user_creation.py, tests/ui/test_account_creation_ui.py, tests/ui/test_widget_behavior.py, tests/unit/test_file_operations.py, tests/unit/test_user_management.py, unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/ui/test_account_creation_ui.py`
- **Purpose**: UI tests for account creation ui
- **Dependencies**: 
  - **Local**:
    - `core.file_operations (create_user_files, get_user_file_path)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `core.user_data_manager (update_user_index, rebuild_user_index)` (🆕)
    - `core.user_data_manager (update_user_index, rebuild_user_index)` (🆕)
    - `core.user_data_validation (is_valid_email, validate_time_format)` (🆕)
    - `core.user_management (update_user_context)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
    - `tests.test_utilities (TestUserFactory)` (🆕)
    - `ui.dialogs.account_creator_dialog (AccountCreatorDialog)` (🆕)
    - `ui.widgets.category_selection_widget (CategorySelectionWidget)` (🆕)
    - `ui.widgets.channel_selection_widget (ChannelSelectionWidget)` (🆕)
    - `ui.widgets.checkin_settings_widget (CheckinSettingsWidget)` (🆕)
    - `ui.widgets.task_settings_widget (TaskSettingsWidget)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `json`
    - `json`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
  - **Third-party**:
    - `PySide6.QtCore (Qt, QTimer)`
    - `PySide6.QtTest (QTest)`
    - `PySide6.QtWidgets (QApplication, QWidget, QMessageBox)`
    - `pytest`
    - `tempfile`
    - `unittest.mock (patch, Mock, MagicMock)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.file_operations, core.user_data_handlers, core.user_data_manager, core.user_data_validation, core.user_management, tests.test_utilities, ui.dialogs.account_creator_dialog, ui.widgets.category_selection_widget, ui.widgets.channel_selection_widget, ui.widgets.checkin_settings_widget, ui.widgets.task_settings_widget
- Removed: PySide6.QtCore, PySide6.QtTest, PySide6.QtWidgets, unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: UI tests for account creation

<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/ui/test_dialog_behavior.py`
- **Purpose**: Behavior tests for dialog behavior
- **Dependencies**: 
  - **Local**:
    - `core.file_operations (create_user_files, get_user_file_path)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `ui.dialogs.category_management_dialog (CategoryManagementDialog)` (🆕)
    - `ui.dialogs.channel_management_dialog (ChannelManagementDialog)` (🆕)
    - `ui.dialogs.checkin_management_dialog (CheckinManagementDialog)` (🆕)
    - `ui.dialogs.schedule_editor_dialog (open_schedule_editor)` (🆕)
    - `ui.dialogs.task_completion_dialog (TaskCompletionDialog)` (🆕)
    - `ui.dialogs.task_crud_dialog (TaskCrudDialog)` (🆕)
    - `ui.dialogs.task_edit_dialog (TaskEditDialog)` (🆕)
    - `ui.dialogs.task_management_dialog (TaskManagementDialog)` (🆕)
    - `ui.dialogs.user_profile_dialog (UserProfileDialog)` (🆕)
  - **Standard Library**:
    - `datetime (datetime, time)`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
  - **Third-party**:
    - `PySide6.QtCore (Qt, QTimer)`
    - `PySide6.QtTest (QTest)`
    - `PySide6.QtWidgets (QApplication, QWidget, QMessageBox, QDialog)`
    - `pytest`
    - `tempfile`
    - `unittest.mock (patch, Mock, MagicMock)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.file_operations, core.user_data_handlers, ui.dialogs.category_management_dialog, ui.dialogs.channel_management_dialog, ui.dialogs.checkin_management_dialog, ui.dialogs.schedule_editor_dialog, ui.dialogs.task_completion_dialog, ui.dialogs.task_crud_dialog, ui.dialogs.task_edit_dialog, ui.dialogs.task_management_dialog, ui.dialogs.user_profile_dialog
- Removed: PySide6.QtCore, PySide6.QtTest, PySide6.QtWidgets, unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/ui/test_dialogs.py`
- **Purpose**: UI tests for dialogs
- **Dependencies**: 
  - **Local**:
    - `bot.channel_registry (register_all_channels)` (🆕)
    - `bot.communication_manager (CommunicationManager)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (get_all_user_ids)` (🆕)
    - `ui.dialogs.account_creator_dialog (AccountCreatorDialog)` (🆕)
    - `ui.dialogs.user_profile_dialog (UserProfileDialog)` (🆕)
  - **Standard Library**:
    - `os`
    - `pathlib (Path)`
    - `sys`
    - `sys`
    - `time`
  - **Third-party**:
    - `PySide6.QtWidgets (QApplication)`
    - `pytest`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: bot.channel_registry, bot.communication_manager, core.user_data_handlers, ui.dialogs.account_creator_dialog, ui.dialogs.user_profile_dialog
- Removed: PySide6.QtWidgets

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Comprehensive UI testing script for all dialog and widget components with systematic import and functionality validation

**Key Functions**:
- `test_dialog_imports()`: Tests importability of all dialog modules without errors
- `test_widget_imports()`: Tests importability of all widget modules without errors
- `test_ui_files_exist()`: Validates existence of required UI design files
- `test_generated_files_exist()`: Validates existence of auto-generated UI files
- `test_user_data_access()`: Tests user data access functionality with mock data
- `test_dialog_instantiation()`: Tests dialog instantiation with proper Qt application context

**Special Considerations**:
- **Read-Only Testing**: Designed to test functionality without modifying user data
- **Systematic Coverage**: Tests all major UI components including dialogs, widgets, and generated files
- **Import Validation**: Ensures all UI modules can be imported without errors
- **Qt Integration**: Properly initializes Qt application context for dialog testing
- **Mock Data**: Uses temporary test data to avoid affecting real user data
- **Comprehensive Reporting**: Provides detailed success/failure reporting for each test

**Usage**: Development tool for validating UI component integrity and identifying import or initialization issues.
<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/ui/test_widget_behavior.py`
- **Purpose**: Behavior tests for widget behavior
- **Dependencies**: 
  - **Local**:
    - `core.file_operations (create_user_files, get_user_file_path)` (🆕)
    - `core.user_data_handlers (save_user_data, get_user_data)` (🆕)
    - `tests.test_utilities (TestUserFactory, TestUserDataFactory)` (🆕)
    - `ui.widgets.category_selection_widget (CategorySelectionWidget)` (🆕)
    - `ui.widgets.channel_selection_widget (ChannelSelectionWidget)` (🆕)
    - `ui.widgets.checkin_settings_widget (CheckinSettingsWidget)` (🆕)
    - `ui.widgets.dynamic_list_container (DynamicListContainer)` (🆕)
    - `ui.widgets.dynamic_list_field (DynamicListField)` (🆕)
    - `ui.widgets.period_row_widget (PeriodRowWidget)` (🆕)
    - `ui.widgets.tag_widget (TagWidget)` (🆕)
    - `ui.widgets.task_settings_widget (TaskSettingsWidget)` (🆕)
    - `ui.widgets.user_profile_settings_widget (UserProfileSettingsWidget)` (🆕)
  - **Standard Library**:
    - `datetime (datetime, time)`
    - `json`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
  - **Third-party**:
    - `PySide6.QtCore (Qt, QTimer)`
    - `PySide6.QtTest (QTest)`
    - `PySide6.QtWidgets (QApplication, QWidget, QMessageBox, QDialog, QVBoxLayout)`
    - `pytest`
    - `tempfile`
    - `unittest.mock (patch, Mock, MagicMock)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.file_operations, core.user_data_handlers, tests.test_utilities, ui.widgets.category_selection_widget, ui.widgets.channel_selection_widget, ui.widgets.checkin_settings_widget, ui.widgets.dynamic_list_container, ui.widgets.dynamic_list_field, ui.widgets.period_row_widget, ui.widgets.tag_widget, ui.widgets.task_settings_widget, ui.widgets.user_profile_settings_widget
- Removed: PySide6.QtCore, PySide6.QtTest, PySide6.QtWidgets, unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/ui/test_widget_behavior_simple.py`
- **Purpose**: Behavior tests for widget behavior simple
- **Dependencies**: 
  - **Local**:
    - `ui.widgets.category_selection_widget (CategorySelectionWidget)` (🆕)
    - `ui.widgets.channel_selection_widget (ChannelSelectionWidget)` (🆕)
    - `ui.widgets.checkin_settings_widget (CheckinSettingsWidget)` (🆕)
    - `ui.widgets.dynamic_list_container (DynamicListContainer)` (🆕)
    - `ui.widgets.dynamic_list_field (DynamicListField)` (🆕)
    - `ui.widgets.tag_widget (TagWidget)` (🆕)
    - `ui.widgets.tag_widget (TagWidget)` (🆕)
    - `ui.widgets.task_settings_widget (TaskSettingsWidget)` (🆕)
    - `ui.widgets.user_profile_settings_widget (UserProfileSettingsWidget)` (🆕)
  - **Standard Library**:
    - `json`
    - `os`
    - `pathlib (Path)`
    - `sys`
  - **Third-party**:
    - `PySide6.QtCore (Qt)`
    - `PySide6.QtTest (QTest)`
    - `PySide6.QtWidgets (QApplication, QWidget)`
    - `pytest`
    - `unittest.mock (patch, Mock)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: ui.widgets.category_selection_widget, ui.widgets.channel_selection_widget, ui.widgets.checkin_settings_widget, ui.widgets.dynamic_list_container, ui.widgets.dynamic_list_field, ui.widgets.tag_widget, ui.widgets.task_settings_widget, ui.widgets.user_profile_settings_widget
- Removed: PySide6.QtCore, PySide6.QtTest, PySide6.QtWidgets, unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/unit/test_cleanup.py`
- **Purpose**: Unit tests for cleanup
- **Dependencies**: 
  - **Local**:
    - `core.config (BASE_DATA_DIR, USER_INFO_DIR_PATH)` (🆕)
    - `core.logger (get_logger)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `logging`
    - `os`
    - `pathlib (Path)`
    - `shutil`
    - `sys`
    - `typing (List, Dict, Any, Optional)`
  - **Third-party**:
    - `argparse`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config, core.logger

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Unit tests for cleanup functionality

<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/unit/test_config.py`
- **Purpose**: Unit tests for config
- **Dependencies**: 
  - **Local**:
    - `core.config (validate_core_paths, validate_ai_configuration, validate_communication_channels, validate_logging_configuration, validate_scheduler_configuration, validate_file_organization_settings, validate_environment_variables, validate_all_configuration, validate_and_raise_if_invalid, ConfigValidationError, BASE_DATA_DIR, USER_INFO_DIR_PATH, DEFAULT_MESSAGES_DIR_PATH)` (🆕)
    - `core.config` (🆕)
  - **Standard Library**:
    - `os`
    - `pathlib (Path)`
  - **Third-party**:
    - `importlib`
    - `pytest`
    - `tempfile`
    - `unittest.mock (patch, Mock)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Unit tests for configuration

<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/unit/test_error_handling.py`
- **Purpose**: Unit tests for error handling
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors, MHMError, DataError, FileOperationError, ConfigurationError, ValidationError, handle_file_error, handle_configuration_error)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `logging`
    - `os`
  - **Third-party**:
    - `pytest`
    - `tempfile`
    - `unittest.mock (patch, Mock, call)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.error_handling
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Unit tests for error handling

<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/unit/test_file_operations.py`
- **Purpose**: Unit tests for file operations
- **Dependencies**: 
  - **Local**:
    - `core.config (BASE_DATA_DIR)` (🆕)
    - `core.config (BASE_DATA_DIR)` (🆕)
    - `core.error_handling (FileOperationError)` (🆕)
    - `core.file_operations (load_json_data, save_json_data, determine_file_path, verify_file_access, get_user_file_path, ensure_user_directory)` (🆕)
    - `tests.test_utilities (TestUserDataFactory)` (🆕)
  - **Standard Library**:
    - `json`
    - `os`
    - `pathlib (Path)`
    - `psutil`
    - `time`
  - **Third-party**:
    - `gc`
    - `pytest`
    - `tempfile`
    - `tempfile`
    - `tempfile`
    - `unittest.mock (patch, Mock, mock_open)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.config, core.error_handling, core.file_operations, tests.test_utilities
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Unit tests for file operations

<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/unit/test_user_management.py`
- **Purpose**: Unit tests for user management
- **Dependencies**: 
  - **Local**:
    - `core.file_operations (create_user_files)` (🆕)
    - `core.user_data_handlers (get_all_user_ids, get_user_data, update_user_preferences, save_user_data, update_user_account, update_user_context)` (🆕)
    - `tests.test_utilities (TestUserDataFactory)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
  - **Third-party**:
    - `pytest`
    - `tempfile`
    - `unittest.mock (patch, Mock)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.file_operations, core.user_data_handlers, tests.test_utilities
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Unit tests for user management

<!-- MANUAL_ENHANCEMENT_END -->

#### `tests/unit/test_validation.py`
- **Purpose**: Unit tests for validation
- **Dependencies**: 
  - **Local**:
    - `core.user_data_validation (is_valid_email, is_valid_phone, validate_time_format, title_case, validate_user_update, validate_schedule_periods, validate_new_user_data, validate_personalization_data)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `os`
    - `shutil`
  - **Third-party**:
    - `pytest`
    - `tempfile`
    - `unittest.mock (patch, MagicMock)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Added: core.user_data_validation
- Removed: unittest.mock

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

### `ui/` - User Interface Components

#### `ui/dialogs/account_creator_dialog.py`
- **Purpose**: Dialog component for account creator dialog
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (🆕)
    - `core.file_operations (create_user_files)` (🆕)
    - `core.file_operations (create_user_files)` (🆕)
    - `core.logger (setup_logging, get_logger, get_component_logger)` (🆕)
    - `core.message_management (get_message_categories)` (🆕)
    - `core.user_data_manager (update_user_index)` (🆕)
    - `core.user_data_validation (title_case, validate_schedule_periods)` (🆕)
    - `core.user_data_validation (is_valid_email, is_valid_phone)` (🆕)
    - `core.user_data_validation (is_valid_email)` (🆕)
    - `core.user_data_validation (is_valid_phone)` (🆕)
    - `core.user_management (create_new_user, get_user_id_by_internal_username)` (🆕)
    - `tasks.task_management (setup_default_task_tags)` (🆕)
    - `ui.dialogs.user_profile_dialog (open_personalization_dialog)` (🆕)
    - `ui.dialogs.user_profile_dialog (open_personalization_dialog)` (🆕)
    - `ui.generated.account_creator_dialog_pyqt (Ui_Dialog_create_account)` (🆕)
    - `ui.widgets.category_selection_widget (CategorySelectionWidget)` (🆕)
    - `ui.widgets.channel_selection_widget (ChannelSelectionWidget)` (🆕)
    - `ui.widgets.checkin_settings_widget (CheckinSettingsWidget)` (🆕)
    - `ui.widgets.task_settings_widget (TaskSettingsWidget)` (🆕)
    - `user.user_context (UserContext)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `os`
    - `sys`
    - `typing (Dict, Any, List, Optional)`
    - `uuid`
  - **Third-party**:
    - `PySide6.QtCore (Qt, Signal, QTime)`
    - `PySide6.QtGui (QFont)`
    - `PySide6.QtWidgets (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QRadioButton, QCheckBox, QComboBox, QGroupBox, QGridLayout, QWidget, QMessageBox, QButtonGroup, QDialogButtonBox, QScrollArea, QTimeEdit, QSpinBox, QTextEdit, QFrame, QSizePolicy)`
- **Used by**: 
  - `tests/ui/test_account_creation_ui.py`
  - `tests/ui/test_dialogs.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.file_operations, core.logger, core.message_management, core.user_data_manager, core.user_data_validation, core.user_management, tasks.task_management, ui.dialogs.user_profile_dialog, ui.generated.account_creator_dialog_pyqt, ui.widgets.category_selection_widget, ui.widgets.channel_selection_widget, ui.widgets.checkin_settings_widget, ui.widgets.task_settings_widget, user.user_context
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, tests/ui/test_account_creation_ui.py, tests/ui/test_dialogs.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Account creation dialog

<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/admin_panel.py`
- **Purpose**: Dialog component for admin panel
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (Qt)`
    - `PySide6.QtWidgets (QDialog, QVBoxLayout, QLabel, QWidget)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
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
    - `core.error_handling (handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.schedule_management (clear_schedule_periods_cache)` (🆕)
    - `core.user_data_handlers (update_user_preferences, update_user_account)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `ui.generated.category_management_dialog_pyqt (Ui_Dialog_category_management)` (🆕)
    - `ui.widgets.category_selection_widget (CategorySelectionWidget)` (🆕)
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QDialog, QMessageBox)`
- **Used by**: 
  - `tests/ui/test_dialog_behavior.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.schedule_management, core.user_data_handlers, ui.generated.category_management_dialog_pyqt, ui.widgets.category_selection_widget
- Removed: PySide6.QtCore, PySide6.QtWidgets, tests/ui/test_dialog_behavior.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Category management dialog

<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/channel_management_dialog.py`
- **Purpose**: Dialog component for channel management dialog
- **Dependencies**: 
  - **Local**:
    - `core.user_data_handlers (get_user_data, update_channel_preferences, update_user_account)` (🆕)
    - `core.user_data_validation (is_valid_email, is_valid_phone)` (🆕)
    - `ui.generated.channel_management_dialog_pyqt (Ui_Dialog)` (🆕)
    - `ui.widgets.channel_selection_widget (ChannelSelectionWidget)` (🆕)
  - **Standard Library**:
    - `logging`
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QDialog, QMessageBox)`
- **Used by**: 
  - `tests/ui/test_dialog_behavior.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.user_data_handlers, core.user_data_validation, ui.generated.channel_management_dialog_pyqt, ui.widgets.channel_selection_widget
- Removed: PySide6.QtCore, PySide6.QtWidgets, tests/ui/test_dialog_behavior.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Channel management dialog

<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/checkin_management_dialog.py`
- **Purpose**: Dialog component for checkin management dialog
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (🆕)
    - `core.logger (setup_logging, get_logger, get_component_logger)` (🆕)
    - `core.schedule_management (set_schedule_periods, clear_schedule_periods_cache)` (🆕)
    - `core.user_data_handlers (update_user_preferences, update_user_account)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_validation (validate_schedule_periods)` (🆕)
    - `ui.generated.checkin_management_dialog_pyqt (Ui_Dialog_checkin_management)` (🆕)
    - `ui.widgets.checkin_settings_widget (CheckinSettingsWidget)` (🆕)
  - **Standard Library**:
    - `os`
    - `sys`
    - `typing (Dict, Any, Optional)`
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QDialog, QMessageBox, QWidget)`
- **Used by**: 
  - `tests/ui/test_dialog_behavior.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.schedule_management, core.user_data_handlers, core.user_data_validation, ui.generated.checkin_management_dialog_pyqt, ui.widgets.checkin_settings_widget
- Removed: PySide6.QtCore, PySide6.QtWidgets, tests/ui/test_dialog_behavior.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Check-in management dialog

<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/schedule_editor_dialog.py`
- **Purpose**: Dialog component for schedule editor dialog
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (🆕)
    - `core.logger (setup_logging, get_logger, get_component_logger)` (🆕)
    - `core.schedule_management (get_schedule_time_periods, set_schedule_periods, clear_schedule_periods_cache, validate_and_format_time, time_24h_to_12h_display, time_12h_display_to_24h)` (🆕)
    - `core.ui_management (load_period_widgets_for_category, collect_period_data_from_widgets)` (🆕)
    - `core.user_data_validation (title_case, validate_schedule_periods)` (🆕)
    - `ui.generated.schedule_editor_dialog_pyqt (Ui_Dialog_edit_schedule)` (🆕)
    - `ui.widgets.period_row_widget (PeriodRowWidget)` (🆕)
  - **Standard Library**:
    - `os`
    - `re`
    - `sys`
    - `typing (Dict, Any, List, Optional, Callable)`
  - **Third-party**:
    - `PySide6.QtCore (Qt, QTime)`
    - `PySide6.QtGui (QFont)`
    - `PySide6.QtWidgets (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QCheckBox, QComboBox, QGroupBox, QGridLayout, QWidget, QMessageBox, QScrollArea, QFrame, QDialogButtonBox, QTimeEdit, QSpinBox, QButtonGroup, QRadioButton, QSizePolicy)`
    - `PySide6.QtWidgets (QMessageBox)`
- **Used by**: 
  - `tests/ui/test_dialog_behavior.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.schedule_management, core.ui_management, core.user_data_validation, ui.generated.schedule_editor_dialog_pyqt, ui.widgets.period_row_widget
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, tests/ui/test_dialog_behavior.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Schedule editor dialog

<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/task_completion_dialog.py`
- **Purpose**: Dialog component for task completion dialog
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (🆕)
    - `core.logger (setup_logging, get_logger, get_component_logger)` (🆕)
    - `ui.generated.task_completion_dialog_pyqt (Ui_Dialog_task_completion)` (🆕)
  - **Third-party**:
    - `PySide6.QtCore (Qt, QDate, QTime)`
    - `PySide6.QtWidgets (QDialog, QMessageBox, QButtonGroup)`
- **Used by**: 
  - `tests/ui/test_dialog_behavior.py`
  - `ui/dialogs/task_crud_dialog.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, ui.generated.task_completion_dialog_pyqt
- Removed: PySide6.QtCore, PySide6.QtWidgets, tests/ui/test_dialog_behavior.py, ui/dialogs/task_crud_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/task_crud_dialog.py`
- **Purpose**: Dialog component for task crud dialog
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (🆕)
    - `core.logger (setup_logging, get_logger, get_component_logger)` (🆕)
    - `tasks.task_management (load_active_tasks, load_completed_tasks, get_user_task_stats, get_tasks_due_soon, complete_task, delete_task)` (🆕)
    - `tasks.task_management (get_task_by_id)` (🆕)
    - `tasks.task_management (get_task_by_id)` (🆕)
    - `tasks.task_management (get_task_by_id)` (🆕)
    - `tasks.task_management (get_task_by_id)` (🆕)
    - `tasks.task_management (get_task_by_id)` (🆕)
    - `tasks.task_management (restore_task)` (🆕)
    - `ui.dialogs.task_completion_dialog (TaskCompletionDialog)` (🆕)
    - `ui.dialogs.task_edit_dialog (TaskEditDialog)` (🆕)
    - `ui.dialogs.task_edit_dialog (TaskEditDialog)` (🆕)
    - `ui.generated.task_crud_dialog_pyqt (Ui_Dialog_task_crud)` (🆕)
  - **Third-party**:
    - `PySide6.QtCore (Qt, Signal)`
    - `PySide6.QtWidgets (QDialog, QMessageBox, QTableWidgetItem, QHeaderView)`
- **Used by**: 
  - `tests/ui/test_dialog_behavior.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, tasks.task_management, ui.dialogs.task_completion_dialog, ui.dialogs.task_edit_dialog, ui.generated.task_crud_dialog_pyqt
- Removed: PySide6.QtCore, PySide6.QtWidgets, tests/ui/test_dialog_behavior.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/task_edit_dialog.py`
- **Purpose**: Dialog component for task edit dialog
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (🆕)
    - `core.logger (setup_logging, get_logger, get_component_logger)` (🆕)
    - `tasks.task_management (create_task, update_task)` (🆕)
    - `ui.generated.task_edit_dialog_pyqt (Ui_Dialog_task_edit)` (🆕)
    - `ui.widgets.tag_widget (TagWidget)` (🆕)
  - **Third-party**:
    - `PySide6.QtCore (Qt, QDate, QTime)`
    - `PySide6.QtWidgets (QDialog, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QDateEdit, QTimeEdit, QCheckBox, QPushButton, QListWidget, QListWidgetItem, QButtonGroup, QRadioButton)`
- **Used by**: 
  - `tests/ui/test_dialog_behavior.py`
  - `ui/dialogs/task_crud_dialog.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, tasks.task_management, ui.generated.task_edit_dialog_pyqt, ui.widgets.tag_widget
- Removed: PySide6.QtCore, PySide6.QtWidgets, tests/ui/test_dialog_behavior.py, ui/dialogs/task_crud_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/task_management_dialog.py`
- **Purpose**: Dialog component for task management dialog
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (🆕)
    - `core.logger (setup_logging, get_logger, get_component_logger)` (🆕)
    - `core.schedule_management (set_schedule_periods, clear_schedule_periods_cache)` (🆕)
    - `core.user_data_handlers (update_user_preferences, update_user_account)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_validation (validate_schedule_periods)` (🆕)
    - `tasks.task_management (setup_default_task_tags)` (🆕)
    - `ui.generated.task_management_dialog_pyqt (Ui_Dialog_task_management)` (🆕)
    - `ui.widgets.task_settings_widget (TaskSettingsWidget)` (🆕)
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QDialog, QMessageBox, QWidget)`
- **Used by**: 
  - `tests/ui/test_dialog_behavior.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.schedule_management, core.user_data_handlers, core.user_data_validation, tasks.task_management, ui.generated.task_management_dialog_pyqt, ui.widgets.task_settings_widget
- Removed: PySide6.QtCore, PySide6.QtWidgets, tests/ui/test_dialog_behavior.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Task management dialog

<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/dialogs/user_profile_dialog.py`
- **Purpose**: Dialog component for user profile dialog
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (🆕)
    - `core.logger (setup_logging, get_logger, get_component_logger)` (🆕)
    - `core.user_data_handlers (update_user_context)` (🆕)
    - `core.user_data_validation (validate_personalization_data)` (🆕)
    - `core.user_management (get_predefined_options, get_timezone_options)` (🆕)
    - `ui.generated.user_profile_management_dialog_pyqt (Ui_Dialog_user_profile)` (🆕)
    - `ui.generated.user_profile_settings_widget_pyqt (Ui_Form_user_profile_settings)` (🆕)
    - `ui.widgets.dynamic_list_container (DynamicListContainer)` (🆕)
    - `ui.widgets.user_profile_settings_widget (UserProfileSettingsWidget)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `os`
    - `re`
    - `sys`
    - `typing (Dict, Any, List, Optional, Callable)`
  - **Third-party**:
    - `PySide6.QtCore (Qt, QTime, QDate, Signal)`
    - `PySide6.QtGui (QFont, QIcon)`
    - `PySide6.QtWidgets (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QCheckBox, QComboBox, QTextEdit, QGroupBox, QGridLayout, QWidget, QMessageBox, QScrollArea, QFrame, QButtonGroup, QDialogButtonBox, QSpinBox, QTimeEdit, QDateEdit, QTabWidget, QFormLayout)`
- **Used by**: 
  - `tests/ui/test_dialog_behavior.py`
  - `tests/ui/test_dialogs.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.user_data_handlers, core.user_data_validation, core.user_management, ui.generated.user_profile_management_dialog_pyqt, ui.generated.user_profile_settings_widget_pyqt, ui.widgets.dynamic_list_container, ui.widgets.user_profile_settings_widget
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, tests/ui/test_dialog_behavior.py, tests/ui/test_dialogs.py, ui/dialogs/account_creator_dialog.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: User profile dialog - manages user profiles

<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/account_creator_dialog_pyqt.py`
- **Purpose**: Auto-generated UI component for account creator dialog pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QAbstractButton, QApplication, QCheckBox, QDialog, QDialogButtonBox, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy, QSpacerItem, QTabWidget, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/dialogs/account_creator_dialog.py`

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/dialogs/account_creator_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Auto-generated Qt UI class for account creation dialog with comprehensive user registration interface

**Key Functions**:
- `setupUi()`: Configures the complete UI layout with tabs, form fields, and widgets
- `retranslateUi()`: Sets up text labels and translations for all UI elements

**Special Considerations**:
- **Auto-Generated**: Created by Qt Designer compiler from `account_creator_dialog.ui` file
- **Warning**: All changes will be lost when UI file is recompiled
- **Complex Layout**: Multi-tab interface with basic info, features, contact info, and personalization tabs
- **Form Fields**: Comprehensive registration form including username, name, features, contact methods, and personalization
- **Qt Integration**: Uses PySide6 widgets for cross-platform compatibility
- **UI Class**: Provides `Ui_Dialog_create_account` class for integration with dialog logic

**Usage**: Imported by `ui/dialogs/account_creator_dialog.py` to provide the visual interface for user account creation.
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/admin_panel_pyqt.py`
- **Purpose**: Auto-generated UI component for admin panel pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QApplication, QComboBox, QGridLayout, QGroupBox, QLabel, QMainWindow, QMenu, QMenuBar, QPushButton, QSizePolicy, QStatusBar, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Auto-generated Qt UI class for main admin panel window with menu system and status bar

**Key Functions**:
- `setupUi()`: Configures the main window layout with menu bar, central widget, and status bar
- `retranslateUi()`: Sets up text labels and menu items for the admin interface

**Special Considerations**:
- **Auto-Generated**: Created by Qt Designer compiler from `admin_panel.ui` file
- **Warning**: All changes will be lost when UI file is recompiled
- **Main Window**: Uses QMainWindow as base class for full application window
- **Menu System**: Includes menu bar with File and Help menus
- **Status Bar**: Provides status information display at bottom of window
- **Qt Integration**: Uses PySide6 widgets for cross-platform compatibility
- **UI Class**: Provides `Ui_MainWindow` class for integration with main application logic

**Usage**: Imported by `ui/ui_app_qt.py` to provide the visual interface for the main admin panel window.
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/category_management_dialog_pyqt.py`
- **Purpose**: Auto-generated UI component for category management dialog pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QAbstractButton, QApplication, QDialog, QDialogButtonBox, QGroupBox, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/dialogs/category_management_dialog.py`

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/dialogs/category_management_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Auto-generated Qt UI class for category management dialog with category selection interface

**Key Functions**:
- `setupUi()`: Configures the dialog layout with category management widgets
- `retranslateUi()`: Sets up text labels and dialog elements

**Special Considerations**:
- **Auto-Generated**: Created by Qt Designer compiler from `category_management_dialog.ui` file
- **Warning**: All changes will be lost when UI file is recompiled
- **Dialog Interface**: Uses QDialog as base class for modal dialog behavior
- **Category Management**: Designed to integrate with CategorySelectionWidget for category operations
- **Qt Integration**: Uses PySide6 widgets for cross-platform compatibility
- **UI Class**: Provides `Ui_Dialog_category_management` class for integration with dialog logic

**Usage**: Imported by `ui/dialogs/category_management_dialog.py` to provide the visual interface for category management operations.
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/category_selection_widget_pyqt.py`
- **Purpose**: Auto-generated UI component for category selection widget pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QApplication, QCheckBox, QGridLayout, QSizePolicy, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/widgets/category_selection_widget.py`

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/widgets/category_selection_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Auto-generated Qt UI class for category selection widget with checkbox-based category interface

**Key Functions**:
- `setupUi()`: Configures the widget layout with category checkboxes in grid format
- `retranslateUi()`: Sets up text labels for category selection elements

**Special Considerations**:
- **Auto-Generated**: Created by Qt Designer compiler from `category_selection_widget.ui` file
- **Warning**: All changes will be lost when UI file is recompiled
- **Widget Interface**: Uses QWidget as base class for embeddable component
- **Checkbox Grid**: Provides grid layout for multiple category checkboxes
- **Qt Integration**: Uses PySide6 widgets for cross-platform compatibility
- **UI Class**: Provides `Ui_Form` class for integration with widget logic

**Usage**: Imported by `ui/widgets/category_selection_widget.py` to provide the visual interface for category selection functionality.
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/channel_management_dialog_pyqt.py`
- **Purpose**: Auto-generated UI component for channel management dialog pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QAbstractButton, QApplication, QDialog, QDialogButtonBox, QGroupBox, QLabel, QSizePolicy, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/dialogs/channel_management_dialog.py`

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/dialogs/channel_management_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Auto-generated Qt UI class for channel management dialog with communication channel configuration interface

**Key Functions**:
- `setupUi()`: Configures the dialog layout with channel management widgets
- `retranslateUi()`: Sets up text labels and dialog elements

**Special Considerations**:
- **Auto-Generated**: Created by Qt Designer compiler from `channel_management_dialog.ui` file
- **Warning**: All changes will be lost when UI file is recompiled
- **Dialog Interface**: Uses QDialog as base class for modal dialog behavior
- **Channel Management**: Designed to integrate with ChannelSelectionWidget for communication setup
- **Qt Integration**: Uses PySide6 widgets for cross-platform compatibility
- **UI Class**: Provides `Ui_Dialog` class for integration with dialog logic

**Usage**: Imported by `ui/dialogs/channel_management_dialog.py` to provide the visual interface for communication channel management.
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/channel_selection_widget_pyqt.py`
- **Purpose**: Auto-generated UI component for channel selection widget pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QApplication, QComboBox, QGridLayout, QLabel, QLayout, QLineEdit, QRadioButton, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/widgets/channel_selection_widget.py`

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/widgets/channel_selection_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Auto-generated Qt UI class for channel selection widget with communication channel and timezone configuration interface

**Key Functions**:
- `setupUi()`: Configures the widget layout with channel selection and timezone settings
- `retranslateUi()`: Sets up text labels for channel and timezone elements

**Special Considerations**:
- **Auto-Generated**: Created by Qt Designer compiler from `channel_selection_widget.ui` file
- **Warning**: All changes will be lost when UI file is recompiled
- **Widget Interface**: Uses QWidget as base class for embeddable component
- **Channel Selection**: Provides radio buttons for different communication channels (Email, Discord, Telegram)
- **Timezone Configuration**: Includes timezone selection dropdown for user preferences
- **Contact Fields**: Contains input fields for channel-specific contact information
- **Qt Integration**: Uses PySide6 widgets for cross-platform compatibility
- **UI Class**: Provides `Ui_Form` class for integration with widget logic

**Usage**: Imported by `ui/widgets/channel_selection_widget.py` to provide the visual interface for communication channel and timezone selection.
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/checkin_element_template_pyqt.py`
- **Purpose**: Auto-generated UI component for checkin element template pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QApplication, QCheckBox, QComboBox, QHBoxLayout, QLineEdit, QPushButton, QSizePolicy, QVBoxLayout, QWidget)`
- **Used by**: None (not imported by other modules)

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Auto-generated Qt UI class for checkin element template with dynamic form field configuration

**Key Functions**:
- `setupUi()`: Configures the template layout with checkin form elements
- `retranslateUi()`: Sets up text labels for checkin template elements

**Special Considerations**:
- **Auto-Generated**: Created by Qt Designer compiler from `checkin_element_template.ui` file
- **Warning**: All changes will be lost when UI file is recompiled
- **Template Interface**: Uses QWidget as base class for reusable form template
- **Dynamic Fields**: Provides form elements including checkboxes, comboboxes, line edits, and push buttons
- **Layout System**: Uses both horizontal and vertical layouts for flexible form arrangement
- **Qt Integration**: Uses PySide6 widgets for cross-platform compatibility
- **UI Class**: Provides `Ui_Form` class for integration with dynamic form systems

**Usage**: Template for creating dynamic checkin form elements with configurable field types and layouts.
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/checkin_management_dialog_pyqt.py`
- **Purpose**: Auto-generated UI component for checkin management dialog pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QAbstractButton, QApplication, QDialog, QDialogButtonBox, QGroupBox, QLabel, QSizePolicy, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/dialogs/checkin_management_dialog.py`

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/dialogs/checkin_management_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Auto-generated Qt UI class for checkin management dialog with checkin configuration interface

**Key Functions**:
- `setupUi()`: Configures the dialog layout with checkin management widgets
- `retranslateUi()`: Sets up text labels and dialog elements

**Special Considerations**:
- **Auto-Generated**: Created by Qt Designer compiler from `checkin_management_dialog.ui` file
- **Warning**: All changes will be lost when UI file is recompiled
- **Dialog Interface**: Uses QDialog as base class for modal dialog behavior
- **Checkin Management**: Designed to integrate with CheckinSettingsWidget for checkin configuration
- **Qt Integration**: Uses PySide6 widgets for cross-platform compatibility
- **UI Class**: Provides `Ui_Dialog_checkin_management` class for integration with dialog logic

**Usage**: Imported by `ui/dialogs/checkin_management_dialog.py` to provide the visual interface for checkin management operations.
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/checkin_settings_widget_pyqt.py`
- **Purpose**: Auto-generated UI component for checkin settings widget pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QApplication, QCheckBox, QGridLayout, QGroupBox, QHBoxLayout, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/widgets/checkin_settings_widget.py`

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/widgets/checkin_settings_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Auto-generated Qt UI class for checkin settings widget with comprehensive checkin configuration interface

**Key Functions**:
- `setupUi()`: Configures the widget layout with checkin settings and form elements
- `retranslateUi()`: Sets up text labels for checkin settings elements

**Special Considerations**:
- **Auto-Generated**: Created by Qt Designer compiler from `checkin_settings_widget.ui` file
- **Warning**: All changes will be lost when UI file is recompiled
- **Widget Interface**: Uses QWidget as base class for embeddable component
- **Scrollable Content**: Includes QScrollArea for handling large numbers of checkin elements
- **Dynamic Forms**: Provides interface for adding and configuring checkin form elements
- **Layout System**: Uses grid, horizontal, and vertical layouts for organized form arrangement
- **Qt Integration**: Uses PySide6 widgets for cross-platform compatibility
- **UI Class**: Provides `Ui_Form` class for integration with checkin settings logic

**Usage**: Imported by `ui/widgets/checkin_settings_widget.py` to provide the visual interface for checkin configuration and management.
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/dynamic_list_field_template_pyqt.py`
- **Purpose**: Auto-generated UI component for dynamic list field template pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QApplication, QCheckBox, QHBoxLayout, QLineEdit, QPushButton, QSizePolicy, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/widgets/dynamic_list_field.py`

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/widgets/dynamic_list_field.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Auto-generated Qt UI class for dynamic list field template with configurable form field interface

**Key Functions**:
- `setupUi()`: Configures the template layout with dynamic list field elements
- `retranslateUi()`: Sets up text labels for dynamic list field elements

**Special Considerations**:
- **Auto-Generated**: Created by Qt Designer compiler from `dynamic_list_field_template.ui` file
- **Warning**: All changes will be lost when UI file is recompiled
- **Template Interface**: Uses QWidget as base class for reusable form template
- **Dynamic Fields**: Provides form elements including checkboxes, line edits, and push buttons
- **Layout System**: Uses both horizontal and vertical layouts for flexible field arrangement
- **Qt Integration**: Uses PySide6 widgets for cross-platform compatibility
- **UI Class**: Provides `Ui_Form` class for integration with dynamic list field logic

**Usage**: Imported by `ui/widgets/dynamic_list_field.py` to provide template for dynamic list field elements with configurable input types.
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/period_row_template_pyqt.py`
- **Purpose**: Auto-generated UI component for period row template pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QApplication, QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton, QSizePolicy, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/widgets/period_row_widget.py`

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/widgets/period_row_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Auto-generated Qt UI class for period row template with time period configuration interface

**Key Functions**:
- `setupUi()`: Configures the template layout with period row form elements
- `retranslateUi()`: Sets up text labels for period row elements

**Special Considerations**:
- **Auto-Generated**: Created by Qt Designer compiler from `period_row_template.ui` file
- **Warning**: All changes will be lost when UI file is recompiled
- **Template Interface**: Uses QWidget as base class for reusable form template
- **Time Periods**: Provides interface for configuring time periods with start/end times
- **Form Elements**: Includes checkboxes, comboboxes, line edits, radio buttons, and push buttons
- **Layout System**: Uses both horizontal and vertical layouts with frames for organized arrangement
- **Qt Integration**: Uses PySide6 widgets for cross-platform compatibility
- **UI Class**: Provides `Ui_Form` class for integration with period row widget logic

**Usage**: Imported by `ui/widgets/period_row_widget.py` to provide template for time period configuration elements.
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/schedule_editor_dialog_pyqt.py`
- **Purpose**: Auto-generated UI component for schedule editor dialog pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QAbstractButton, QApplication, QDialog, QDialogButtonBox, QGroupBox, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/dialogs/schedule_editor_dialog.py`

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/dialogs/schedule_editor_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Auto-generated Qt UI class for schedule editor dialog with comprehensive scheduling interface

**Key Functions**:
- `setupUi()`: Configures the dialog layout with schedule editor widgets
- `retranslateUi()`: Sets up text labels and dialog elements

**Special Considerations**:
- **Auto-Generated**: Created by Qt Designer compiler from `schedule_editor_dialog.ui` file
- **Warning**: All changes will be lost when UI file is recompiled
- **Dialog Interface**: Uses QDialog as base class for modal dialog behavior
- **Schedule Editor**: Provides interface for creating and editing message schedules
- **Scrollable Content**: Includes QScrollArea for handling complex schedule configurations
- **Layout System**: Uses group boxes, horizontal and vertical layouts for organized arrangement
- **Qt Integration**: Uses PySide6 widgets for cross-platform compatibility
- **UI Class**: Provides `Ui_Dialog` class for integration with schedule editor logic

**Usage**: Imported by `ui/dialogs/schedule_editor_dialog.py` to provide the visual interface for schedule creation and editing.
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/tag_widget_pyqt.py`
- **Purpose**: Auto-generated UI component for tag widget pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QApplication, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QSizePolicy, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/widgets/tag_widget.py`

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/widgets/tag_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/task_completion_dialog_pyqt.py`
- **Purpose**: Auto-generated UI component for task completion dialog pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QAbstractButton, QApplication, QComboBox, QDateEdit, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel, QRadioButton, QSizePolicy, QTextEdit, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/dialogs/task_completion_dialog.py`

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/dialogs/task_completion_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/task_crud_dialog_pyqt.py`
- **Purpose**: Auto-generated UI component for task crud dialog pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QAbstractButton, QAbstractItemView, QApplication, QDialog, QDialogButtonBox, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QPushButton, QSizePolicy, QSpacerItem, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/dialogs/task_crud_dialog.py`

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/dialogs/task_crud_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/task_edit_dialog_pyqt.py`
- **Purpose**: Auto-generated UI component for task edit dialog pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QAbstractButton, QApplication, QCheckBox, QComboBox, QDateEdit, QDialog, QDialogButtonBox, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QRadioButton, QScrollArea, QSizePolicy, QSpacerItem, QTextEdit, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/dialogs/task_edit_dialog.py`

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/dialogs/task_edit_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/task_management_dialog_pyqt.py`
- **Purpose**: Auto-generated UI component for task management dialog pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QAbstractButton, QApplication, QDialog, QDialogButtonBox, QGridLayout, QGroupBox, QLabel, QSizePolicy, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/dialogs/task_management_dialog.py`

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/dialogs/task_management_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Auto-generated Qt UI class for task management dialog with task configuration interface

**Key Functions**:
- `setupUi()`: Configures the dialog layout with task management widgets
- `retranslateUi()`: Sets up text labels and dialog elements

**Special Considerations**:
- **Auto-Generated**: Created by Qt Designer compiler from `task_management_dialog.ui` file
- **Warning**: All changes will be lost when UI file is recompiled
- **Dialog Interface**: Uses QDialog as base class for modal dialog behavior
- **Task Management**: Designed to integrate with TaskSettingsWidget for task configuration
- **Layout System**: Uses grid layout with group boxes for organized task settings
- **Qt Integration**: Uses PySide6 widgets for cross-platform compatibility
- **UI Class**: Provides `Ui_Dialog` class for integration with task management dialog logic

**Usage**: Imported by `ui/dialogs/task_management_dialog.py` to provide the visual interface for task management operations.
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/task_settings_widget_pyqt.py`
- **Purpose**: Auto-generated UI component for task settings widget pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QApplication, QGroupBox, QHBoxLayout, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/widgets/task_settings_widget.py`

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/widgets/task_settings_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Auto-generated Qt UI class for task settings widget with task configuration interface

**Key Functions**:
- `setupUi()`: Configures the widget layout with task settings elements
- `retranslateUi()`: Sets up text labels for task settings elements

**Special Considerations**:
- **Auto-Generated**: Created by Qt Designer compiler from `task_settings_widget.ui` file
- **Warning**: All changes will be lost when UI file is recompiled
- **Widget Interface**: Uses QWidget as base class for embeddable component
- **Task Settings**: Provides interface for configuring task management preferences
- **Scrollable Content**: Includes QScrollArea for handling extensive task settings
- **Layout System**: Uses group boxes, horizontal and vertical layouts for organized arrangement
- **Qt Integration**: Uses PySide6 widgets for cross-platform compatibility
- **UI Class**: Provides `Ui_Form` class for integration with task settings logic

**Usage**: Imported by `ui/widgets/task_settings_widget.py` to provide the visual interface for task configuration and preferences.
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/user_profile_management_dialog_pyqt.py`
- **Purpose**: Auto-generated UI component for user profile management dialog pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QAbstractButton, QApplication, QDialog, QDialogButtonBox, QLabel, QSizePolicy, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/dialogs/user_profile_dialog.py`

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/dialogs/user_profile_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Auto-generated Qt UI class for user profile management dialog with profile configuration interface

**Key Functions**:
- `setupUi()`: Configures the dialog layout with user profile management widgets
- `retranslateUi()`: Sets up text labels and dialog elements

**Special Considerations**:
- **Auto-Generated**: Created by Qt Designer compiler from `user_profile_management_dialog.ui` file
- **Warning**: All changes will be lost when UI file is recompiled
- **Dialog Interface**: Uses QDialog as base class for modal dialog behavior
- **Profile Management**: Designed to integrate with UserProfileSettingsWidget for profile configuration
- **Qt Integration**: Uses PySide6 widgets for cross-platform compatibility
- **UI Class**: Provides `Ui_Dialog` class for integration with user profile dialog logic

**Usage**: Imported by `ui/dialogs/user_profile_dialog.py` to provide the visual interface for user profile management operations.
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/generated/user_profile_settings_widget_pyqt.py`
- **Purpose**: Auto-generated UI component for user profile settings widget pyqt
- **Dependencies**: 
  - **Third-party**:
    - `PySide6.QtCore (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)`
    - `PySide6.QtGui (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)`
    - `PySide6.QtWidgets (QApplication, QCalendarWidget, QCheckBox, QGridLayout, QGroupBox, QLabel, QLineEdit, QScrollArea, QSizePolicy, QTabWidget, QTextEdit, QVBoxLayout, QWidget)`
- **Used by**: 
  - `ui/dialogs/user_profile_dialog.py`
  - `ui/widgets/user_profile_settings_widget.py`

**Dependency Changes**:
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, ui/dialogs/user_profile_dialog.py, ui/widgets/user_profile_settings_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Auto-generated Qt UI class for user profile settings widget with comprehensive profile configuration interface

**Key Functions**:
- `setupUi()`: Configures the widget layout with user profile settings elements
- `retranslateUi()`: Sets up text labels for user profile settings elements

**Special Considerations**:
- **Auto-Generated**: Created by Qt Designer compiler from `user_profile_settings_widget.ui` file
- **Warning**: All changes will be lost when UI file is recompiled
- **Widget Interface**: Uses QWidget as base class for embeddable component
- **Profile Settings**: Provides comprehensive interface for user profile configuration
- **Tabbed Interface**: Uses QTabWidget for organizing different profile sections
- **Rich Input**: Includes calendar widget, text edit, line edits, and checkboxes for various data types
- **Scrollable Content**: Includes QScrollArea for handling extensive profile settings
- **Layout System**: Uses grid layout with group boxes for organized form arrangement
- **Qt Integration**: Uses PySide6 widgets for cross-platform compatibility
- **UI Class**: Provides `Ui_Form` class for integration with user profile settings logic

**Usage**: Imported by both `ui/dialogs/user_profile_dialog.py` and `ui/widgets/user_profile_settings_widget.py` to provide the visual interface for comprehensive user profile configuration.
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/ui_app_qt.py`
- **Purpose**: Main UI application (PyQt6)
- **Dependencies**: 
  - **Local**:
    - `bot.channel_registry (register_all_channels)` (🆕)
    - `bot.communication_manager (CommunicationManager)` (🆕)
    - `bot.communication_manager (CommunicationManager)` (🆕)
    - `core.auto_cleanup (get_cleanup_status, find_pycache_dirs, find_pyc_files, calculate_cache_size)` (🆕)
    - `core.auto_cleanup (perform_cleanup, update_cleanup_timestamp)` (🆕)
    - `core.config (validate_all_configuration, ConfigValidationError)` (🆕)
    - `core.config (BASE_DATA_DIR, USER_INFO_DIR_PATH)` (🆕)
    - `core.config (LOG_FILE_PATH)` (🆕)
    - `core.config (validate_all_configuration)` (🆕)
    - `core.config (BASE_DATA_DIR, LOG_FILE_PATH, LOG_LEVEL, LM_STUDIO_BASE_URL, AI_TIMEOUT_SECONDS, SCHEDULER_INTERVAL, EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, DISCORD_BOT_TOKEN)` (🆕)
    - `core.config (BASE_DATA_DIR)` (🆕)
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
    - `core.logger (setup_logging, get_logger, get_component_logger)` (🆕)
    - `core.logger (toggle_verbose_logging, get_verbose_mode)` (🆕)
    - `core.user_data_handlers (get_all_user_ids)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `core.user_data_handlers (get_user_data, update_user_context)` (🆕)
    - `core.user_data_handlers (save_user_data)` (🆕)
    - `core.user_data_manager (rebuild_user_index)` (🆕)
    - `core.user_data_manager (load_json_data)` (🆕)
    - `core.user_data_validation (title_case)` (🆕)
    - `ui.dialogs.account_creator_dialog (AccountCreatorDialog)` (🆕)
    - `ui.dialogs.category_management_dialog (CategoryManagementDialog)` (🆕)
    - `ui.dialogs.channel_management_dialog (ChannelManagementDialog)` (🆕)
    - `ui.dialogs.checkin_management_dialog (CheckinManagementDialog)` (🆕)
    - `ui.dialogs.schedule_editor_dialog (open_schedule_editor)` (🆕)
    - `ui.dialogs.task_crud_dialog (TaskCrudDialog)` (🆕)
    - `ui.dialogs.task_management_dialog (TaskManagementDialog)` (🆕)
    - `ui.dialogs.user_profile_dialog (UserProfileDialog)` (🆕)
    - `ui.generated.admin_panel_pyqt (Ui_ui_app_mainwindow)` (🆕)
    - `user.user_context (UserContext)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `json`
    - `logging`
    - `os`
    - `os`
    - `pathlib (Path)`
    - `psutil`
    - `subprocess`
    - `sys`
    - `threading`
    - `time`
    - `time`
  - **Third-party**:
    - `PySide6.QtCore (Qt, QTimer, QThread, Signal)`
    - `PySide6.QtGui (QFont, QIcon)`
    - `PySide6.QtWidgets (QApplication, QMainWindow, QMessageBox, QFileDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QComboBox, QGroupBox, QGridLayout, QWidget, QTabWidget, QDialogButtonBox, QCheckBox)`
    - `PySide6.QtWidgets (QTabWidget, QTextEdit, QScrollArea)`
    - `webbrowser`
- **Used by**: 
  - `tests/behavior/test_ui_app_behavior.py`

**Dependency Changes**:
- Added: bot.channel_registry, bot.communication_manager, core.auto_cleanup, core.config, core.error_handling, core.logger, core.user_data_handlers, core.user_data_manager, core.user_data_validation, ui.dialogs.account_creator_dialog, ui.dialogs.category_management_dialog, ui.dialogs.channel_management_dialog, ui.dialogs.checkin_management_dialog, ui.dialogs.schedule_editor_dialog, ui.dialogs.task_crud_dialog, ui.dialogs.task_management_dialog, ui.dialogs.user_profile_dialog, ui.generated.admin_panel_pyqt, user.user_context
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, tests/behavior/test_ui_app_behavior.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Main UI application (PyQt6)

<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/category_selection_widget.py`
- **Purpose**: UI widget component for category selection widget
- **Dependencies**: 
  - **Local**:
    - `core.user_data_validation (title_case)` (🆕)
    - `ui.generated.category_selection_widget_pyqt (Ui_Form_category_selection_widget)` (🆕)
  - **Third-party**:
    - `PySide6.QtWidgets (QWidget, QCheckBox)`
- **Used by**: 
  - `scripts/debug/debug_category_dialog.py`
  - `tests/ui/test_account_creation_ui.py`
  - `tests/ui/test_widget_behavior.py`
  - `tests/ui/test_widget_behavior_simple.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/category_management_dialog.py`

**Dependency Changes**:
- Added: core.user_data_validation, ui.generated.category_selection_widget_pyqt
- Removed: PySide6.QtWidgets, scripts/debug/debug_category_dialog.py, tests/ui/test_account_creation_ui.py, tests/ui/test_widget_behavior.py, tests/ui/test_widget_behavior_simple.py, ui/dialogs/account_creator_dialog.py, ui/dialogs/category_management_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Category selection widget

<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/channel_selection_widget.py`
- **Purpose**: UI widget component for channel selection widget
- **Dependencies**: 
  - **Local**:
    - `core.user_management (get_timezone_options)` (🆕)
    - `ui.generated.channel_selection_widget_pyqt (Ui_Form_channel_selection)` (🆕)
  - **Standard Library**:
    - `os`
    - `pytz`
    - `sys`
  - **Third-party**:
    - `PySide6.QtWidgets (QWidget)`
- **Used by**: 
  - `tests/ui/test_account_creation_ui.py`
  - `tests/ui/test_widget_behavior.py`
  - `tests/ui/test_widget_behavior_simple.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/channel_management_dialog.py`

**Dependency Changes**:
- Added: core.user_management, ui.generated.channel_selection_widget_pyqt
- Removed: PySide6.QtWidgets, tests/ui/test_account_creation_ui.py, tests/ui/test_widget_behavior.py, tests/ui/test_widget_behavior_simple.py, ui/dialogs/account_creator_dialog.py, ui/dialogs/channel_management_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Channel selection widget

<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/checkin_settings_widget.py`
- **Purpose**: UI widget component for checkin settings widget
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (🆕)
    - `core.logger (setup_logging, get_logger, get_component_logger)` (🆕)
    - `core.schedule_management (get_schedule_time_periods, set_schedule_periods, clear_schedule_periods_cache)` (🆕)
    - `core.ui_management (load_period_widgets_for_category, collect_period_data_from_widgets)` (🆕)
    - `core.user_data_handlers (update_user_preferences)` (🆕)
    - `core.user_data_handlers (get_user_data)` (🆕)
    - `ui.generated.checkin_settings_widget_pyqt (Ui_Form_checkin_settings)` (🆕)
    - `ui.widgets.period_row_widget (PeriodRowWidget)` (🆕)
  - **Standard Library**:
    - `os`
    - `sys`
    - `typing (Dict, Any, List, Optional)`
  - **Third-party**:
    - `PySide6.QtCore (Qt, Signal)`
    - `PySide6.QtWidgets (QWidget, QVBoxLayout, QLabel, QRadioButton, QSpinBox, QPushButton, QMessageBox)`
    - `PySide6.QtWidgets (QInputDialog, QMessageBox)`
- **Used by**: 
  - `tests/ui/test_account_creation_ui.py`
  - `tests/ui/test_widget_behavior.py`
  - `tests/ui/test_widget_behavior_simple.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/checkin_management_dialog.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.schedule_management, core.ui_management, core.user_data_handlers, ui.generated.checkin_settings_widget_pyqt, ui.widgets.period_row_widget
- Removed: PySide6.QtCore, PySide6.QtWidgets, tests/ui/test_account_creation_ui.py, tests/ui/test_widget_behavior.py, tests/ui/test_widget_behavior_simple.py, ui/dialogs/account_creator_dialog.py, ui/dialogs/checkin_management_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Check-in settings widget

<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/dynamic_list_container.py`
- **Purpose**: UI widget component for dynamic list container
- **Dependencies**: 
  - **Local**:
    - `core.user_management (get_predefined_options)` (🆕)
    - `ui.widgets.dynamic_list_field (DynamicListField)` (🆕)
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QWidget, QVBoxLayout, QGridLayout)`
    - `PySide6.QtWidgets (QMessageBox)`
- **Used by**: 
  - `tests/ui/test_widget_behavior.py`
  - `tests/ui/test_widget_behavior_simple.py`
  - `ui/dialogs/user_profile_dialog.py`
  - `ui/widgets/dynamic_list_field.py`
  - `ui/widgets/user_profile_settings_widget.py`

**Dependency Changes**:
- Added: core.user_management, ui.widgets.dynamic_list_field
- Removed: PySide6.QtCore, PySide6.QtWidgets, tests/ui/test_widget_behavior.py, tests/ui/test_widget_behavior_simple.py, ui/dialogs/user_profile_dialog.py, ui/widgets/dynamic_list_field.py, ui/widgets/user_profile_settings_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Dynamic list container - UI component for managing dynamic lists

<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/dynamic_list_field.py`
- **Purpose**: UI widget component for dynamic list field
- **Dependencies**: 
  - **Local**:
    - `ui.generated.dynamic_list_field_template_pyqt (Ui_Form_dynamic_list_field_template)` (🆕)
    - `ui.widgets.dynamic_list_container (DynamicListContainer)` (🆕)
    - `ui.widgets.dynamic_list_container (DynamicListContainer)` (🆕)
    - `ui.widgets.dynamic_list_container (DynamicListContainer)` (🆕)
  - **Third-party**:
    - `PySide6.QtCore (Signal)`
    - `PySide6.QtWidgets (QWidget)`
    - `PySide6.QtWidgets (QSizePolicy)`
- **Used by**: 
  - `tests/ui/test_widget_behavior.py`
  - `tests/ui/test_widget_behavior_simple.py`
  - `ui/widgets/dynamic_list_container.py`

**Dependency Changes**:
- Added: ui.generated.dynamic_list_field_template_pyqt, ui.widgets.dynamic_list_container
- Removed: PySide6.QtCore, PySide6.QtWidgets, tests/ui/test_widget_behavior.py, tests/ui/test_widget_behavior_simple.py, ui/widgets/dynamic_list_container.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Dynamic list field - UI component for individual list items

<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/period_row_widget.py`
- **Purpose**: UI widget component for period row widget
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (🆕)
    - `core.logger (setup_logging, get_logger, get_component_logger)` (🆕)
    - `core.schedule_management (time_24h_to_12h_display, time_12h_display_to_24h)` (🆕)
    - `ui.generated.period_row_template_pyqt (Ui_Form_period_row_template)` (🆕)
  - **Standard Library**:
    - `os`
    - `sys`
    - `typing (Dict, Any, List, Optional)`
  - **Third-party**:
    - `PySide6.QtCore (Qt, Signal)`
    - `PySide6.QtGui (QFont)`
    - `PySide6.QtWidgets (QWidget, QButtonGroup, QMessageBox)`
- **Used by**: 
  - `core/ui_management.py`
  - `tests/ui/test_widget_behavior.py`
  - `ui/dialogs/schedule_editor_dialog.py`
  - `ui/widgets/checkin_settings_widget.py`
  - `ui/widgets/task_settings_widget.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.schedule_management, ui.generated.period_row_template_pyqt
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, core/ui_management.py, tests/ui/test_widget_behavior.py, ui/dialogs/schedule_editor_dialog.py, ui/widgets/checkin_settings_widget.py, ui/widgets/task_settings_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Period row widget - UI component for managing schedule periods

<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/tag_widget.py`
- **Purpose**: UI widget component for tag widget
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (🆕)
    - `core.logger (setup_logging, get_logger, get_component_logger)` (🆕)
    - `tasks.task_management (get_user_task_tags, add_user_task_tag, remove_user_task_tag)` (🆕)
    - `ui.generated.tag_widget_pyqt (Ui_Widget_tag)` (🆕)
  - **Standard Library**:
    - `os`
    - `sys`
    - `typing (List, Optional)`
  - **Third-party**:
    - `PySide6.QtCore (Qt, Signal)`
    - `PySide6.QtWidgets (QWidget, QListWidgetItem, QInputDialog, QMessageBox)`
- **Used by**: 
  - `tests/ui/test_widget_behavior.py`
  - `tests/ui/test_widget_behavior_simple.py`
  - `ui/dialogs/task_edit_dialog.py`
  - `ui/widgets/task_settings_widget.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, tasks.task_management, ui.generated.tag_widget_pyqt
- Removed: PySide6.QtCore, PySide6.QtWidgets, tests/ui/test_widget_behavior.py, tests/ui/test_widget_behavior_simple.py, ui/dialogs/task_edit_dialog.py, ui/widgets/task_settings_widget.py

<!-- MANUAL_ENHANCEMENT_START -->
<!-- Add any additional context, key functions, or special considerations here -->
<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/task_settings_widget.py`
- **Purpose**: UI widget component for task settings widget
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (handle_errors)` (🆕)
    - `core.logger (setup_logging, get_logger, get_component_logger)` (🆕)
    - `core.schedule_management (get_schedule_time_periods, set_schedule_periods, clear_schedule_periods_cache)` (🆕)
    - `core.ui_management (load_period_widgets_for_category, collect_period_data_from_widgets)` (🆕)
    - `core.user_data_handlers (update_user_preferences)` (🆕)
    - `tasks.task_management (get_user_task_stats)` (🆕)
    - `ui.generated.task_settings_widget_pyqt (Ui_Form_task_settings)` (🆕)
    - `ui.widgets.period_row_widget (PeriodRowWidget)` (🆕)
    - `ui.widgets.tag_widget (TagWidget)` (🆕)
  - **Standard Library**:
    - `os`
    - `sys`
    - `typing (Dict, Any, List, Optional)`
  - **Third-party**:
    - `PySide6.QtWidgets (QWidget, QMessageBox)`
- **Used by**: 
  - `tests/ui/test_account_creation_ui.py`
  - `tests/ui/test_widget_behavior.py`
  - `tests/ui/test_widget_behavior_simple.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/dialogs/task_management_dialog.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.schedule_management, core.ui_management, core.user_data_handlers, tasks.task_management, ui.generated.task_settings_widget_pyqt, ui.widgets.period_row_widget, ui.widgets.tag_widget
- Removed: PySide6.QtWidgets, tests/ui/test_account_creation_ui.py, tests/ui/test_widget_behavior.py, tests/ui/test_widget_behavior_simple.py, ui/dialogs/account_creator_dialog.py, ui/dialogs/task_management_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: Task settings widget - UI component for configuring tasks

<!-- MANUAL_ENHANCEMENT_END -->

#### `ui/widgets/user_profile_settings_widget.py`
- **Purpose**: UI widget component for user profile settings widget
- **Dependencies**: 
  - **Local**:
    - `core.logger (setup_logging, get_logger, get_component_logger)` (🆕)
    - `core.user_management (get_timezone_options)` (🆕)
    - `ui.generated.user_profile_settings_widget_pyqt (Ui_Form_user_profile_settings)` (🆕)
    - `ui.widgets.dynamic_list_container (DynamicListContainer)` (🆕)
  - **Standard Library**:
    - `datetime`
    - `os`
    - `sys`
    - `typing (Dict, Any, Optional)`
  - **Third-party**:
    - `PySide6.QtCore (Qt, QDate, QEvent)`
    - `PySide6.QtGui (QFont)`
    - `PySide6.QtWidgets (QWidget, QVBoxLayout, QLabel, QMessageBox, QScrollArea)`
    - `PySide6.QtWidgets (QLineEdit, QLabel)`
- **Used by**: 
  - `tests/ui/test_widget_behavior.py`
  - `tests/ui/test_widget_behavior_simple.py`
  - `ui/dialogs/user_profile_dialog.py`

**Dependency Changes**:
- Added: core.logger, core.user_management, ui.generated.user_profile_settings_widget_pyqt, ui.widgets.dynamic_list_container
- Removed: PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets, tests/ui/test_widget_behavior.py, tests/ui/test_widget_behavior_simple.py, ui/dialogs/user_profile_dialog.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: User profile settings widget

<!-- MANUAL_ENHANCEMENT_END -->

### `user/` - User Data and Context

#### `user/user_context.py`
- **Purpose**: User context management
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.user_data_handlers (get_user_data, update_user_account, update_user_preferences, update_user_context)` (🆕)
    - `core.user_data_handlers (save_user_data)` (🆕)
  - **Standard Library**:
    - `json`
    - `os`
    - `threading`
- **Used by**: 
  - `bot/telegram_bot.py`
  - `bot/user_context_manager.py`
  - `core/schedule_management.py`
  - `core/scheduler.py`
  - `tests/behavior/test_user_context_behavior.py`
  - `tests/integration/test_account_management.py`
  - `ui/dialogs/account_creator_dialog.py`
  - `ui/ui_app_qt.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.user_data_handlers
- Removed: bot/telegram_bot.py, bot/user_context_manager.py, core/schedule_management.py, core/scheduler.py, tests/behavior/test_user_context_behavior.py, tests/integration/test_account_management.py, ui/dialogs/account_creator_dialog.py, ui/ui_app_qt.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: User context management

<!-- MANUAL_ENHANCEMENT_END -->

#### `user/user_preferences.py`
- **Purpose**: User preferences management
- **Dependencies**: 
  - **Local**:
    - `core.error_handling (error_handler, DataError, FileOperationError, handle_errors)` (🆕)
    - `core.logger (get_logger, get_component_logger)` (🆕)
    - `core.schedule_management (set_schedule_period_active, is_schedule_period_active)` (🆕)
    - `core.user_data_handlers (get_user_data, update_user_preferences)` (🆕)
  - **Standard Library**:
    - `json`
    - `os`
- **Used by**: 
  - `bot/user_context_manager.py`
  - `tests/behavior/test_user_context_behavior.py`

**Dependency Changes**:
- Added: core.error_handling, core.logger, core.schedule_management, core.user_data_handlers
- Removed: bot/user_context_manager.py, tests/behavior/test_user_context_behavior.py

<!-- MANUAL_ENHANCEMENT_START -->
**Enhanced Purpose**: User preferences management

<!-- MANUAL_ENHANCEMENT_END -->
