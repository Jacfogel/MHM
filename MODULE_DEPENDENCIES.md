> **NOTE (2025-07-18)**: Core refactor is complete.  Regenerate dependency map using `ai_tools/audit_module_dependencies.py` to reflect updated handlers structure.

# Module Dependencies - MHM Project

> **Purpose**: Complete dependency map for all modules in the MHM codebase  
> **Status**: **ACTIVE** - Generated from audit data  
> **Last Updated**: 2025-07-17

> **See [README.md](README.md) for complete navigation and project overview**
> **See [ARCHITECTURE.md](ARCHITECTURE.md) for system architecture and design**
> **See [TODO.md](TODO.md) for current documentation priorities**

## 📋 **Overview**

### **Module Dependencies Coverage: 0% ⚠️ NEEDS ATTENTION**
- **Files Scanned**: 133
- **Total Imports Found**: 1,160
- **Dependencies Documented**: 0 (0% coverage)
- **Standard Library Imports**: 483
- **Third-Party Imports**: 189
- **Local Imports**: 488
- **Last Updated**: 2025-07-20

**Status**: ⚠️ **CRITICAL GAP** - All 133 files need dependency documentation. This represents a significant documentation gap that affects system understanding and maintenance.

**Note**: The audit shows that while this file contains some dependency information, it's not comprehensive and doesn't match the actual import structure found in the codebase. The audit found 1160 imports across 133 files that need to be properly documented.

## 🔍 **Import Statistics**

- **Standard Library**: 495 imports (41.1%)
- **Third-party**: 191 imports (15.9%)
- **Local**: 518 imports (43.0%)

## 📁 **Module Dependencies by Directory**

### `bot/` - Communication Channel Implementations

#### `bot/ai_chatbot.py`
- **Purpose**: AI chatbot implementation using LM Studio API
- **Dependencies**: 
  - `bot.user_context_manager`
  - `core.config`
  - `core.error_handling`
  - `core.logger`
  - `core.response_tracking`
  - `core.user_management`
- **Used by**: 
  - `bot.conversation_manager`
  - `scripts/clear_cache_and_test_discord.py`
  - `scripts/debug_comprehensive_prompt.py`
  - `scripts/test_ai_with_clear_cache.py`
  - `scripts/test_comprehensive_ai.py`
  - `scripts/test_lm_studio.py`
  - `scripts/test_user_data_analysis.py`

#### `bot/base_channel.py`
- **Purpose**: Abstract base class for communication channels
- **Dependencies**: 
  - `core.error_handling`
  - `core.logger`
- **Used by**: 
  - `bot.channel_factory`
  - `bot.discord_bot`
  - `bot.email_bot`
  - `bot.telegram_bot`
  - `tests/behavior/test_communication_behavior.py`

#### `bot/channel_factory.py`
- **Purpose**: Factory for creating communication channels
- **Dependencies**: 
  - `bot.base_channel`
  - `core.error_handling`
  - `core.logger`
- **Used by**: 
  - `bot.channel_registry`

#### `bot/channel_registry.py`
- **Purpose**: Registry for all available communication channels
- **Dependencies**: 
  - `bot.channel_factory`
  - `bot.discord_bot`
  - `bot.email_bot`
  - `core.error_handling`
- **Used by**: 
  - `core.service`
  - `ui.ui_app`
  - `ui.ui_app_qt`
  - `tests/ui/test_dialogs.py`

#### `bot/conversation_manager.py`
- **Purpose**: Manages conversation flows and check-ins
- **Dependencies**: 
  - `bot.ai_chatbot`
  - `core.error_handling`
  - `core.logger`
  - `core.response_tracking`
- **Used by**: 
  - `bot.communication_manager`

#### `bot/email_bot.py`
- **Purpose**: Email communication channel implementation
- **Dependencies**: 
  - `bot.base_channel`
  - `core.config`
  - `core.error_handling`
  - `core.logger`
- **Used by**: 
  - `bot.channel_registry`

#### `bot/telegram_bot.py`
- **Purpose**: Telegram communication channel implementation
- **Dependencies**: 
  - `bot.base_channel`
  - `core.config`
  - `core.error_handling`
  - `core.logger`
- **Used by**: 
  - `bot.channel_registry`

#### `bot/user_context_manager.py`
- **Purpose**: Manages rich user context for AI conversations
- **Dependencies**: 
  - `core.error_handling`
  - `core.logger`
  - `core.message_management`
  - `core.response_tracking`
  - `core.user_management`
  - `user.user_context`
  - `user.user_preferences`
- **Used by**: 
  - `bot.ai_chatbot`

### `core/` - Core System Modules

#### `core/auto_cleanup.py`
- **Purpose**: Automatic cache cleanup and maintenance
- **Dependencies**: 
  - `core.config`
  - `core.error_handling`
- **Used by**: 
  - `core.service`

#### `core/backup_manager.py`
- **Purpose**: Manages automatic backups and rollback operations
- **Dependencies**: 
  - `core.config`
  - `core.error_handling`
  - `core.logger`
  - `core.user_management`
- **Used by**: 
  - `core.service`

#### `core/checkin_analytics.py`
- **Purpose**: Analyzes check-in data and provides insights
- **Dependencies**: 
  - `core.error_handling`
  - `core.logger`
  - `core.response_tracking`
- **Used by**: 
  - `ui.account_manager`

#### `core/config.py`
- **Purpose**: Configuration management and validation
- **Dependencies**: 
  - `core.error_handling`
- **Used by**: 
  - `core.auto_cleanup`
  - `core.backup_manager`
  - `core.file_operations`
  - `core.service`
  - `core.service_utilities`
  - `core.user_data_manager`
  - `core.user_management`
  - `scripts/debug_lm_studio_timeout.py`
  - `scripts/migrate_sent_messages.py`
  - `scripts/migrate_user_data_structure.py`
  - `scripts/utilities/cleanup_duplicate_messages.py`
  - `tests/behavior/test_communication_behavior.py`
  - `tests/behavior/test_message_behavior.py`
  - `tests/behavior/test_service_behavior.py`
  - `tests/behavior/test_task_behavior.py`
  - `tests/conftest.py`
  - `tests/integration/test_account_lifecycle.py`
  - `tests/unit/test_cleanup.py`
  - `tests/unit/test_config.py`
  - `tests/unit/test_file_operations.py`
  - `ui.account_creator`
  - `ui.account_manager`
  - `ui.ui_app`
  - `ui.ui_app_qt`

#### `core/error_handling.py`
- **Purpose**: Centralized error handling and recovery
- **Dependencies**: None (base module)
- **Used by**: 
  - `bot.ai_chatbot`
  - `bot.base_channel`
  - `bot.channel_factory`
  - `bot.channel_registry`
  - `bot.conversation_manager`
  - `bot.email_bot`
  - `bot.telegram_bot`
  - `bot.user_context_manager`
  - `core.auto_cleanup`
  - `core.backup_manager`
  - `core.checkin_analytics`
  - `core.config`
  - `core.file_operations`
  - `core.logger`
  - `core.message_management`
  - `core.response_tracking`
  - `core.scheduler`
  - `core.schedule_management`
  - `core.service`
  - `core.service_utilities`
  - `core.ui_management`
  - `core.user_data_manager`
  - `core.user_management`
  - `core.validation`
  - `run_mhm.py`
  - `scripts/legacy_schedule_editor_qt.py`
  - `tasks.task_management`
  - `tests/unit/test_error_handling.py`
  - `ui.account_creator`
  - `ui.account_manager`
  - `ui.dialogs.account_creator_dialog`
  - `ui.dialogs.category_management_dialog`
  - `ui.dialogs.checkin_management_dialog`
  - `ui.dialogs.schedule_editor_dialog`
  - `ui.dialogs.task_management_dialog`
  - `ui.dialogs.user_profile_dialog`
  - `ui.ui_app`
  - `ui.ui_app_qt`
  - `ui.widgets.checkin_settings_widget`
  - `ui.widgets.period_row_widget`
  - `ui.widgets.task_settings_widget`
  - `user.user_context`
  - `user.user_preferences`

#### `core/file_operations.py`
- **Purpose**: File operations and data management
- **Dependencies**: 
  - `core.config`
  - `core.error_handling`
  - `core.logger`
  - `core.message_management`
  - `core.user_data_manager`
- **Used by**: 
  - `core.backup_manager`
  - `core.message_management`
  - `core.response_tracking`
  - `core.schedule_management`
  - `core.user_data_manager`
  - `core.user_management`
  - `scripts/add_checkin_schedules.py`
  - `scripts/cleanup_user_message_files.py`
  - `scripts/consolidate_message_time_periods.py`
  - `scripts/debug_preferences.py`
  - `scripts/migrate_messaging_service.py`
  - `scripts/migrate_user_data_structure.py`
  - `scripts/test_data_integrity.py`
  - `scripts/test_new_modules.py`
  - `scripts/utilities/user_data_cli.py`
  - `tasks.task_management`
  - `tests/integration/test_account_lifecycle.py`
  - `tests/integration/test_account_management.py`
  - `tests/integration/test_user_creation.py`
  - `tests/ui/test_account_creation_ui.py`
  - `tests/unit/test_file_operations.py`
  - `tests/unit/test_user_management.py`
  - `ui.account_creator`
  - `ui.account_manager`
  - `ui.dialogs.account_creator_dialog`
  - `ui.dialogs.user_profile_dialog`

#### `core/logger.py`
- **Purpose**: Logging system configuration and management
- **Dependencies**: None (base module)
- **Used by**: 
  - `bot.ai_chatbot`
  - `bot.base_channel`
  - `bot.channel_factory`
  - `bot.email_bot`
  - `bot.telegram_bot`
  - `bot.user_context_manager`
  - `core.backup_manager`
  - `core.checkin_analytics`
  - `core.file_operations`
  - `core.message_management`
  - `core.response_tracking`
  - `core.scheduler`
  - `core.schedule_management`
  - `core.service`
  - `core.service_utilities`
  - `core.ui_management`
  - `core.user_data_manager`
  - `core.user_management`
  - `core.validation`
  - `scripts/add_checkin_schedules.py`
  - `scripts/check_checkin_schedules.py`
  - `scripts/cleanup_user_message_files.py`
  - `scripts/consolidate_message_time_periods.py`
  - `scripts/legacy_schedule_editor_qt.py`
  - `scripts/migrate_messaging_service.py`
  - `scripts/migrate_schedule_format.py`
  - `scripts/migrate_sent_messages.py`
  - `scripts/migrate_user_data_structure.py`
  - `scripts/rebuild_index.py`
  - `scripts/restore_custom_periods.py`
  - `scripts/test_checkin_fix.py`
  - `scripts/test_migration.py`
  - `scripts/utilities/cleanup_test_data.py`
  - `scripts/utilities/user_data_cli.py`
  - `tasks.task_management`
  - `tests/unit/test_cleanup.py`
  - `ui.account_creator`
  - `ui.account_manager`
  - `ui.dialogs.account_creator_dialog`
  - `ui.dialogs.category_management_dialog`
  - `ui.dialogs.checkin_management_dialog`
  - `ui.dialogs.schedule_editor_dialog`
  - `ui.dialogs.task_management_dialog`
  - `ui.dialogs.user_profile_dialog`
  - `ui.ui_app`
  - `ui.ui_app_qt`
  - `ui.widgets.checkin_settings_widget`
  - `ui.widgets.period_row_widget`
  - `ui.widgets.task_settings_widget`
  - `ui.widgets.user_profile_settings_widget`
  - `user.user_context`
  - `user.user_preferences`

#### `core/message_management.py`
- **Purpose**: Message management and storage
- **Dependencies**: 
  - `core.config`
  - `core.error_handling`
  - `core.file_operations`
  - `core.logger`
  - `core.user_data_manager`
- **Used by**: 
  - `bot.user_context_manager`
  - `core.file_operations`
  - `core.user_data_manager`
  - `core.user_management`
  - `scripts/test_new_modules.py`
  - `tests/behavior/test_message_behavior.py`
  - `tests/behavior/test_account_management_real_behavior.py`
  - `tests/integration/test_account_management.py`
  - `ui.account_creator`
  - `ui.account_manager`
  - `ui.dialogs.account_creator_dialog`
  - `ui.dialogs.user_profile_dialog`

#### `core/response_tracking.py`
- **Purpose**: Tracks user responses and interactions
- **Dependencies**: 
  - `core.config`
  - `core.error_handling`
  - `core.file_operations`
  - `core.logger`
  - `core.user_management`
- **Used by**: 
  - `bot.ai_chatbot`
  - `bot.user_context_manager`
  - `core.checkin_analytics`
  - `core.file_operations`
  - `core.user_data_manager`
  - `scripts/test_checkin_fix.py`
  - `scripts/test_new_modules.py`

#### `core/schedule_management.py`
- **Purpose**: Schedule management and time period handling
- **Dependencies**: 
  - `core.error_handling`
  - `core.file_operations`
  - `core.logger`
  - `core.service_utilities`
  - `core.user_management`
  - `user.user_context`
- **Used by**: 
  - `core.scheduler`
  - `core.ui_management`
  - `scripts/check_checkin_schedules.py`
  - `scripts/consolidate_message_time_periods.py`
  - `scripts/legacy_schedule_editor_qt.py`
  - `scripts/migrate_schedule_format.py`
  - `scripts/restore_custom_periods.py`
  - `scripts/test_new_modules.py`
  - `ui.account_creator`
  - `ui.account_manager`
  - `ui.dialogs.checkin_management_dialog`
  - `ui.dialogs.schedule_editor_dialog`
  - `ui.dialogs.task_management_dialog`
  - `ui.widgets.checkin_settings_widget`
  - `ui.widgets.period_row_widget`
  - `ui.widgets.task_settings_widget`
  - `user.user_preferences`

#### `core/scheduler.py`
- **Purpose**: Task scheduling and job management
- **Dependencies**: 
  - `core.error_handling`
  - `core.logger`
  - `core.schedule_management`
  - `core.service_utilities`
  - `core.user_management`
  - `tasks.task_management`
  - `user.user_context`
- **Used by**: 
  - `core.service`
  - `tests/behavior/test_scheduler_behavior.py`

#### `core/service.py`
- **Purpose**: Main service orchestration and management
- **Dependencies**: 
  - `bot.channel_registry`
  - `bot.communication_manager`
  - `core.auto_cleanup`
  - `core.config`
  - `core.error_handling`
  - `core.file_operations`
  - `core.logger`
  - `core.scheduler`
  - `core.user_management`
- **Used by**: 
  - `tests/behavior/test_service_behavior.py`

#### `core/service_utilities.py`
- **Purpose**: Utility functions for service operations
- **Dependencies**: 
  - `core.config`
  - `core.error_handling`
  - `core.logger`
- **Used by**: 
  - `core.schedule_management`
  - `core.scheduler`
  - `scripts/test_new_modules.py`
  - `ui.account_manager`

#### `core/ui_management.py`
- **Purpose**: UI management and widget utilities
- **Dependencies**: 
  - `core.error_handling`
  - `core.logger`
  - `core.schedule_management`
  - `core.validation`
  - `ui.widgets.period_row_widget`
- **Used by**: 
  - `ui.widgets.checkin_settings_widget`
  - `ui.widgets.task_settings_widget`

#### `core/user_data_manager.py`
- **Purpose**: Enhanced user data management with references and indexing
- **Dependencies**: 
  - `core.config`
  - `core.error_handling`
  - `core.file_operations`
  - `core.logger`
  - `core.message_management`
  - `core.response_tracking`
  - `core.user_management`
- **Used by**: 
  - `core.file_operations`
  - `core.message_management`
  - `core.user_management`
  - `scripts/rebuild_index.py`
  - `scripts/utilities/user_data_cli.py`
  - `tests/conftest.py`
  - `tests/integration/test_account_management.py`
  - `tests/ui/test_account_creation_ui.py`
  - `ui.account_manager`
  - `ui.dialogs.account_creator_dialog`
  - `ui.dialogs.user_profile_dialog`
  - `ui.ui_app_qt`

#### `core/user_management.py`
- **Purpose**: Centralized user data access and management
- **Dependencies**: 
  - `core.config`
  - `core.error_handling`
  - `core.file_operations`
  - `core.logger`
  - `core.message_management`
  - `core.user_data_manager`
  - `core.validation`
- **Used by**: 
  - `bot.ai_chatbot`
  - `bot.user_context_manager`
  - `core.backup_manager`
  - `core.file_operations`
  - `core.response_tracking`
  - `core.schedule_management`
  - `core.scheduler`
  - `core.service`
  - `core.user_data_manager`
  - `scripts/add_checkin_schedules.py`
  - `scripts/check_checkin_schedules.py`
  - `scripts/cleanup_user_message_files.py`
  - `scripts/consolidate_message_time_periods.py`
  - `scripts/debug_preferences.py`
  - `scripts/fix_user_schedules.py`
  - `scripts/migrate_messaging_service.py`
  - `scripts/migrate_schedule_format.py`
  - `scripts/restore_custom_periods.py`
  - `scripts/test_checkin_fix.py`
  - `scripts/test_new_modules.py`
  - `tasks.task_management`
  - `tests/behavior/test_account_management_real_behavior.py`
  - `tests/integration/test_account_lifecycle.py`
  - `tests/integration/test_account_management.py`
  - `tests/integration/test_user_creation.py`
  - `tests/ui/test_account_creation_ui.py`
  - `tests/ui/test_dialogs.py`
  - `tests/unit/test_user_management.py`
  - `ui.account_creator`
  - `ui.account_manager`
  - `ui.dialogs.account_creator_dialog`
  - `ui.dialogs.category_management_dialog`
  - `ui.dialogs.checkin_management_dialog`
  - `ui.dialogs.task_management_dialog`
  - `ui.dialogs.user_profile_dialog`
  - `ui.ui_app`
  - `ui.ui_app_qt`
  - `ui.widgets.channel_selection_widget`
  - `ui.widgets.checkin_settings_widget`
  - `ui.widgets.task_settings_widget`
  - `ui.widgets.user_profile_settings_widget`
  - `user.user_context`
  - `user.user_preferences`

#### `core/validation.py`
- **Purpose**: Data validation utilities
- **Dependencies**: 
  - `core.error_handling`
  - `core.logger`
- **Used by**: 
  - `core.ui_management`
  - `core.user_management`
  - `tests/integration/test_user_creation.py`
  - `ui.account_creator`
  - `ui.dialogs.account_creator_dialog`
  - `ui.widgets.category_selection_widget`
  - `ui.widgets.period_row_widget`

### `tasks/` - Task Management

#### `tasks/task_management.py`
- **Purpose**: Task management and scheduling
- **Dependencies**: 
  - `core.config`
  - `core.error_handling`
  - `core.file_operations`
  - `core.logger`
  - `core.user_management`
- **Used by**: 
  - `core.scheduler`
  - `ui.account_manager`
  - `ui.widgets.task_settings_widget`
  - `tests/behavior/test_task_behavior.py`

### `user/` - User Context and Preferences

#### `user/user_context.py`
- **Purpose**: User context management
- **Dependencies**: 
  - `core.error_handling`
  - `core.logger`
  - `core.user_management`
- **Used by**: 
  - `bot.user_context_manager`
  - `core.schedule_management`
  - `core.scheduler`
  - `tests/integration/test_account_management.py`
  - `ui.account_creator`
  - `ui.account_manager`
  - `ui.dialogs.account_creator_dialog`
  - `ui.dialogs.user_profile_dialog`
  - `ui.ui_app`
  - `ui.ui_app_qt`

#### `user/user_preferences.py`
- **Purpose**: User preferences management
- **Dependencies**: 
  - `core.error_handling`
  - `core.logger`
  - `core.schedule_management`
  - `core.user_management`
- **Used by**: 
  - `bot.user_context_manager`

### `ui/` - User Interface

#### `ui/account_creator.py`
- **Purpose**: Account creation functionality
- **Dependencies**: 
  - `core.error_handling`
  - `core.file_operations`
  - `core.logger`
  - `core.message_management`
  - `core.schedule_management`
  - `core.user_management`
  - `core.validation`
  - `ui.dialogs.user_profile_dialog`
  - `user.user_context`
- **Used by**: 
  - `ui.ui_app`

#### `ui/account_manager.py`
- **Purpose**: Account management functionality
- **Dependencies**: 
  - `core.checkin_analytics`
  - `core.error_handling`
  - `core.file_operations`
  - `core.logger`
  - `core.message_management`
  - `core.schedule_management`
  - `core.service_utilities`
  - `core.user_management`
  - `core.validation`
  - `tasks.task_management`
  - `ui.dialogs.user_profile_dialog`
  - `user.user_context`
- **Used by**: 
  - `ui.ui_app`
  - `ui.ui_app_qt`

#### `ui/ui_app.py`
- **Purpose**: Main UI application (PySide6)
- **Dependencies**: 
  - `bot.channel_registry`
  - `bot.communication_manager`
  - `core.auto_cleanup`
  - `core.config`
  - `core.error_handling`
  - `core.logger`
  - `core.user_management`
  - `core.validation`
  - `ui.account_creator`
  - `ui.account_manager`
  - `user.user_context`
- **Used by**: 
  - `run_mhm.py`

#### `ui/ui_app_qt.py`
- **Purpose**: Main UI application (PyQt6)
- **Dependencies**: 
  - `bot.channel_registry`
  - `bot.communication_manager`
  - `core.auto_cleanup`
  - `core.config`
  - `core.error_handling`
  - `core.logger`
  - `core.user_data_manager`
  - `core.user_management`
  - `core.validation`
  - `ui.dialogs.account_creator_dialog`
  - `ui.dialogs.category_management_dialog`
  - `ui.dialogs.channel_management_dialog`
  - `ui.dialogs.checkin_management_dialog`
  - `ui.dialogs.schedule_editor_dialog`
  - `ui.dialogs.task_management_dialog`
  - `ui.dialogs.user_profile_dialog`
  - `user.user_context`
- **Used by**: 
  - `run_mhm.py`

### `ui/dialogs/` - Dialog Components

#### `ui/dialogs/account_creator_dialog.py`
- **Purpose**: Account creation dialog
- **Dependencies**: 
  - `core.error_handling`
  - `core.file_operations`
  - `core.logger`
  - `core.message_management`
  - `core.user_data_manager`
  - `core.user_management`
  - `core.validation`
  - `ui.dialogs.user_profile_dialog`
  - `ui.widgets.category_selection_widget`
  - `ui.widgets.channel_selection_widget`
  - `ui.widgets.checkin_settings_widget`
  - `ui.widgets.task_settings_widget`
  - `user.user_context`
- **Used by**: 
  - `scripts/test_category_dialog.py`
  - `tests/ui/test_account_creation_ui.py`
  - `tests/ui/test_dialogs.py`
  - `ui.ui_app_qt`

#### `ui/dialogs/category_management_dialog.py`
- **Purpose**: Category management dialog
- **Dependencies**: 
  - `core.error_handling`
  - `core.logger`
  - `core.user_management`
  - `ui.widgets.category_selection_widget`
- **Used by**: 
  - `ui.ui_app_qt`

#### `ui/dialogs/channel_management_dialog.py`
- **Purpose**: Channel management dialog
- **Dependencies**: 
  - `core.user_management`
  - `core.validation`
  - `ui.widgets.channel_selection_widget`
- **Used by**: 
  - `ui.ui_app_qt`

#### `ui/dialogs/checkin_management_dialog.py`
- **Purpose**: Check-in management dialog
- **Dependencies**: 
  - `core.error_handling`
  - `core.logger`
  - `core.schedule_management`
  - `core.user_management`
  - `ui.widgets.checkin_settings_widget`
- **Used by**: 
  - `ui.ui_app_qt`

#### `ui/dialogs/schedule_editor_dialog.py`
- **Purpose**: Schedule editor dialog
- **Dependencies**: 
  - `core.error_handling`
  - `core.logger`
  - `core.schedule_management`
  - `core.ui_management`
  - `core.validation`
  - `ui.widgets.period_row_widget`
- **Used by**: 
  - `scripts/test_schedule_editor.py`
  - `ui.ui_app_qt`

#### `ui/dialogs/task_management_dialog.py`
- **Purpose**: Task management dialog
- **Dependencies**: 
  - `core.error_handling`
  - `core.logger`
  - `core.schedule_management`
  - `core.user_management`
  - `ui.widgets.task_settings_widget`
- **Used by**: 
  - `ui.ui_app_qt`

#### `ui/dialogs/user_profile_dialog.py`
- **Purpose**: User profile dialog
- **Dependencies**: 
  - `core.error_handling`
  - `core.logger`
  - `core.user_management`
  - `ui.widgets.user_profile_settings_widget`
- **Used by**: 
  - `ui.account_creator`
  - `ui.account_manager`
  - `ui.dialogs.account_creator_dialog`
  - `ui.ui_app_qt`
  - `tests/ui/test_dialogs.py`

### `ui/widgets/` - UI Widgets

#### `ui/widgets/category_selection_widget.py`
- **Purpose**: Category selection widget
- **Dependencies**: 
  - `core.validation`
- **Used by**: 
  - `ui.dialogs.account_creator_dialog`
  - `ui.dialogs.category_management_dialog`
  - `tests/ui/test_account_creation_ui.py`

#### `ui/widgets/channel_selection_widget.py`
- **Purpose**: Channel selection widget
- **Dependencies**: 
  - `core.user_management`
- **Used by**: 
  - `ui.dialogs.account_creator_dialog`
  - `ui.dialogs.channel_management_dialog`
  - `tests/ui/test_account_creation_ui.py`

#### `ui/widgets/checkin_settings_widget.py`
- **Purpose**: Check-in settings widget
- **Dependencies**: 
  - `core.error_handling`
  - `core.logger`
  - `core.schedule_management`
  - `core.ui_management`
  - `core.user_management`
  - `ui.widgets.period_row_widget`
- **Used by**: 
  - `ui.dialogs.account_creator_dialog`
  - `ui.dialogs.checkin_management_dialog`
  - `tests/ui/test_account_creation_ui.py`

#### `ui/widgets/period_row_widget.py`
- **Purpose**: Period row widget
- **Dependencies**: 
  - `core.error_handling`
  - `core.logger`
  - `core.schedule_management`
  - `core.validation`
- **Used by**: 
  - `core.ui_management`
  - `scripts/test_period_widget.py`
  - `ui.dialogs.schedule_editor_dialog`
  - `ui.widgets.checkin_settings_widget`
  - `ui.widgets.task_settings_widget`

#### `ui/widgets/task_settings_widget.py`
- **Purpose**: Task settings widget
- **Dependencies**: 
  - `core.error_handling`
  - `core.logger`
  - `core.schedule_management`
  - `core.ui_management`
  - `core.user_management`
  - `tasks.task_management`
  - `ui.widgets.period_row_widget`
- **Used by**: 
  - `ui.dialogs.account_creator_dialog`
  - `ui.dialogs.task_management_dialog`
  - `tests/ui/test_account_creation_ui.py`

#### `ui/widgets/user_profile_settings_widget.py`
- **Purpose**: User profile settings widget
- **Dependencies**: 
  - `core.logger`
  - `core.user_management`
- **Used by**: 
  - `ui.dialogs.user_profile_dialog`
  - `tests/ui/test_account_creation_ui.py`

## 🔄 **Circular Dependencies**

**Analysis Result**: No circular dependencies detected

## 📊 **Dependency Statistics by Directory**

- **bot/**: 10 files, 60 imports, 30 local deps
- **core/**: 17 files, 216 imports, 104 local deps
- **root/**: 2 files, 10 imports, 1 local deps
- **scripts/**: 48 files, 260 imports, 79 local deps
- **tasks/**: 1 files, 10 imports, 5 local deps
- **tests/**: 18 files, 219 imports, 77 local deps
- **ui/**: 33 files, 334 imports, 175 local deps
- **user/**: 2 files, 12 imports, 7 local deps

## 🔧 **Next Steps**

1. **Document All Dependencies**: All 1,204 imports need proper documentation ⚠️ **CRITICAL**
2. **Review High Coupling**: Modules with many dependencies may need refactoring
3. **Optimize Imports**: Remove unused imports and consolidate common dependencies
4. **Update Tests**: Ensure all dependency relationships are properly tested
5. **Address Documentation Gap**: 0% of dependencies documented vs 100% function documentation

## 📊 **Statistics**

- **Total Files**: 131
- **Total Imports**: 1,204
- **Standard Library**: 495 (41.1%)
- **Third-party**: 191 (15.9%)
- **Local**: 518 (43.0%)
- **Circular Dependencies**: 0
- **Dependencies Documented**: 0% ⚠️ **CRITICAL GAP**

---

*This dependency map was generated from audit data on 2025-07-17. For the most current information, run `python ai_tools/quick_audit.py`.* 