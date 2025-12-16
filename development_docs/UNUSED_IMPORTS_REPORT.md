# Unused Imports Report

> **File**: `development_docs/UNUSED_IMPORTS_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2025-12-16 03:31:08
> **Source**: `python development_tools/run_development_tools.py unused-imports` - Unused Imports Detection Tool

## Summary Statistics

- **Total Files Scanned**: 371
- **Files with Unused Imports**: 147
- **Total Unused Imports**: 424

## Breakdown by Category

- **Obvious Unused**: 126 imports
- **Type Hints Only**: 2 imports
- **Re Exports**: 0 imports
- **Conditional Imports**: 9 imports
- **Star Imports**: 0 imports
- **Test Mocking**: 131 imports
- **Qt Testing**: 54 imports
- **Test Infrastructure**: 99 imports
- **Production Test Mocking**: 3 imports
- **Ui Imports**: 0 imports

## Obvious Unused

**Recommendation**: These imports can likely be safely removed.

### `communication/command_handlers/account_handler.py`

**Count**: 1 unused import(s)

- **Line 382**: Unused import time
  - Symbol: `unused-import`

### `communication/communication_channels/discord/webhook_handler.py`

**Count**: 3 unused import(s)

- **Line 9**: Unused import hmac
  - Symbol: `unused-import`
- **Line 10**: Unused import hashlib
  - Symbol: `unused-import`
- **Line 11**: Unused import os
  - Symbol: `unused-import`

### `communication/communication_channels/discord/webhook_server.py`

**Count**: 4 unused import(s)

- **Line 9**: Unused Optional imported from typing
  - Symbol: `unused-import`
- **Line 9**: Unused Callable imported from typing
  - Symbol: `unused-import`
- **Line 12**: Unused verify_webhook_signature imported from communication.communication_channels.discord.webhook_handler
  - Symbol: `unused-import`
- **Line 12**: Unused EVENT_APPLICATION_AUTHORIZED imported from communication.communication_channels.discord.webhook_handler
  - Symbol: `unused-import`

### `communication/communication_channels/discord/welcome_handler.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused Optional imported from typing
  - Symbol: `unused-import`

### `communication/core/welcome_manager.py`

**Count**: 1 unused import(s)

- **Line 7**: Unused import os
  - Symbol: `unused-import`

### `core/file_locking.py`

**Count**: 2 unused import(s)

- **Line 13**: Unused Callable imported from typing
  - Symbol: `unused-import`
- **Line 13**: Unused Any imported from typing
  - Symbol: `unused-import`

### `core/message_analytics.py`

**Count**: 3 unused import(s)

- **Line 10**: Unused datetime imported from datetime
  - Symbol: `unused-import`
- **Line 10**: Unused timedelta imported from datetime
  - Symbol: `unused-import`
- **Line 11**: Unused List imported from typing
  - Symbol: `unused-import`

### `core/schedule_management.py`

**Count**: 1 unused import(s)

- **Line 16**: Unused DataError imported from core.error_handling
  - Symbol: `unused-import`

### `core/scheduler.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused Optional imported from typing
  - Symbol: `unused-import`

### `core/user_data_manager.py`

**Count**: 1 unused import(s)

- **Line 19**: Unused save_json_data imported from core.file_operations
  - Symbol: `unused-import`

### `development_tools/config/analyze_config.py`

**Count**: 2 unused import(s)

- **Line 15**: Unused import json
  - Symbol: `unused-import`
- **Line 16**: Unused datetime imported from datetime
  - Symbol: `unused-import`

### `development_tools/error_handling/analyze_error_handling.py`

**Count**: 2 unused import(s)

- **Line 15**: Unused import json
  - Symbol: `unused-import`
- **Line 16**: Unused import os
  - Symbol: `unused-import`

### `development_tools/functions/analyze_function_patterns.py`

**Count**: 1 unused import(s)

- **Line 14**: Unused List imported from typing
  - Symbol: `unused-import`

### `development_tools/functions/analyze_package_exports.py`

**Count**: 1 unused import(s)

- **Line 26**: Unused Optional imported from typing
  - Symbol: `unused-import`

### `development_tools/functions/generate_function_registry.py`

**Count**: 2 unused import(s)

- **Line 13**: Unused import ast
  - Symbol: `unused-import`
- **Line 17**: Unused Any imported from typing
  - Symbol: `unused-import`

### `development_tools/imports/analyze_module_dependencies.py`

**Count**: 2 unused import(s)

- **Line 9**: Unused import ast
  - Symbol: `unused-import`
- **Line 13**: Unused Optional imported from typing
  - Symbol: `unused-import`

### `development_tools/imports/analyze_unused_imports.py`

**Count**: 1 unused import(s)

- **Line 29**: Unused partial imported from functools
  - Symbol: `unused-import`

### `development_tools/imports/generate_module_dependencies.py`

**Count**: 2 unused import(s)

- **Line 11**: Unused Any imported from typing
  - Symbol: `unused-import`
- **Line 32**: Unused analyze_dependency_patterns imported from analyze_dependency_patterns
  - Symbol: `unused-import`

### `development_tools/reports/decision_support.py`

**Count**: 1 unused import(s)

- **Line 12**: Unused import ast
  - Symbol: `unused-import`

### `development_tools/run_development_tools.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused import warnings
  - Symbol: `unused-import`

### `development_tools/shared/mtime_cache.py`

**Count**: 1 unused import(s)

- **Line 31**: Unused List imported from typing
  - Symbol: `unused-import`

### `development_tools/shared/output_storage.py`

**Count**: 2 unused import(s)

- **Line 11**: Unused import os
  - Symbol: `unused-import`
- **Line 17**: Unused create_output_file imported from file_rotation
  - Symbol: `unused-import`

### `development_tools/shared/service/audit_orchestration.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused Any imported from typing
  - Symbol: `unused-import`

### `development_tools/shared/service/commands.py`

**Count**: 2 unused import(s)

- **Line 8**: Unused Path imported from pathlib
  - Symbol: `unused-import`
- **Line 9**: Unused Any imported from typing
  - Symbol: `unused-import`

### `development_tools/shared/service/core.py`

**Count**: 2 unused import(s)

- **Line 21**: Unused SCRIPT_REGISTRY imported from tool_wrappers
  - Symbol: `unused-import`
- **Line 27**: Unused COMMAND_TIERS imported from common
  - Symbol: `unused-import`

### `development_tools/shared/service/data_loading.py`

**Count**: 2 unused import(s)

- **Line 18**: Unused extract_first_int imported from utilities
  - Symbol: `unused-import`
- **Line 18**: Unused create_standard_format_result imported from utilities
  - Symbol: `unused-import`

### `development_tools/tests/fix_test_markers.py`

**Count**: 3 unused import(s)

- **Line 12**: Unused import re
  - Symbol: `unused-import`
- **Line 14**: Unused List imported from typing
  - Symbol: `unused-import`
- **Line 14**: Unused Tuple imported from typing
  - Symbol: `unused-import`

### `development_tools/tests/generate_test_coverage_reports.py`

**Count**: 1 unused import(s)

- **Line 19**: Unused Any imported from typing
  - Symbol: `unused-import`

### `run_mhm.py`

**Count**: 3 unused import(s)

- **Line 15**: Unused error_handler imported from core.error_handling
  - Symbol: `unused-import`
- **Line 15**: Unused DataError imported from core.error_handling
  - Symbol: `unused-import`
- **Line 15**: Unused FileOperationError imported from core.error_handling
  - Symbol: `unused-import`

### `run_tests.py`

**Count**: 1 unused import(s)

- **Line 19**: Unused Tuple imported from typing
  - Symbol: `unused-import`

### `tests/behavior/test_communication_manager_behavior.py`

**Count**: 2 unused import(s)

- **Line 12**: Unused BotInitializationError imported from communication.core.channel_orchestrator
  - Symbol: `unused-import`
- **Line 12**: Unused MessageSendError imported from communication.core.channel_orchestrator
  - Symbol: `unused-import`

### `tests/behavior/test_conversation_flow_manager_behavior.py`

**Count**: 2 unused import(s)

- **Line 16**: Unused CHECKIN_START imported from communication.message_processing.conversation_flow_manager
  - Symbol: `unused-import`
- **Line 16**: Unused CHECKIN_COMPLETE imported from communication.message_processing.conversation_flow_manager
  - Symbol: `unused-import`

### `tests/behavior/test_discord_checkin_retry_behavior.py`

**Count**: 2 unused import(s)

- **Line 11**: Unused call imported from unittest.mock
  - Symbol: `unused-import`
- **Line 12**: Unused import asyncio
  - Symbol: `unused-import`

### `tests/behavior/test_discord_task_reminder_followup.py`

**Count**: 4 unused import(s)

- **Line 9**: Unused timedelta imported from datetime
  - Symbol: `unused-import`
- **Line 12**: Unused ParsedCommand imported from communication.command_handlers.shared_types
  - Symbol: `unused-import`
- **Line 13**: Unused create_task imported from tasks.task_management
  - Symbol: `unused-import`
- **Line 13**: Unused get_task_by_id imported from tasks.task_management
  - Symbol: `unused-import`

### `tests/behavior/test_task_cleanup_bug.py`

**Count**: 1 unused import(s)

- **Line 12**: Unused complete_task imported from tasks.task_management
  - Symbol: `unused-import`

### `tests/behavior/test_task_reminder_followup_behavior.py`

**Count**: 4 unused import(s)

- **Line 12**: Unused ConversationManager imported from communication.message_processing.conversation_flow_manager
  - Symbol: `unused-import`
- **Line 12**: Unused FLOW_NONE imported from communication.message_processing.conversation_flow_manager
  - Symbol: `unused-import`
- **Line 19**: Unused ParsedCommand imported from communication.command_handlers.shared_types
  - Symbol: `unused-import`
- **Line 20**: Unused load_active_tasks imported from tasks.task_management
  - Symbol: `unused-import`

### `tests/behavior/test_user_data_flow_architecture.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused call imported from unittest.mock
  - Symbol: `unused-import`

### `tests/behavior/test_webhook_server_behavior.py`

**Count**: 2 unused import(s)

- **Line 14**: Unused HTTPServer imported from http.server
  - Symbol: `unused-import`
- **Line 15**: Unused BytesIO imported from io
  - Symbol: `unused-import`

### `tests/behavior/test_welcome_manager_behavior.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused WELCOME_TRACKING_FILE imported from communication.core.welcome_manager
  - Symbol: `unused-import`

### `tests/development_tools/conftest.py`

**Count**: 1 unused import(s)

- **Line 7**: Unused import warnings
  - Symbol: `unused-import`

### `tests/development_tools/test_analysis_tool_validation.py`

**Count**: 2 unused import(s)

- **Line 12**: Unused demo_project_root imported from tests.development_tools.conftest
  - Symbol: `unused-import`
- **Line 12**: Unused test_config_path imported from tests.development_tools.conftest
  - Symbol: `unused-import`

### `tests/development_tools/test_analyze_ai_work.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused demo_project_root imported from tests.development_tools.conftest
  - Symbol: `unused-import`

### `tests/development_tools/test_analyze_documentation.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused demo_project_root imported from tests.development_tools.conftest
  - Symbol: `unused-import`

### `tests/development_tools/test_analyze_missing_addresses.py`

**Count**: 2 unused import(s)

- **Line 11**: Unused demo_project_root imported from tests.development_tools.conftest
  - Symbol: `unused-import`
- **Line 11**: Unused test_config_path imported from tests.development_tools.conftest
  - Symbol: `unused-import`

### `tests/development_tools/test_audit_status_updates.py`

**Count**: 2 unused import(s)

- **Line 12**: Unused call imported from unittest.mock
  - Symbol: `unused-import`
- **Line 14**: Unused temp_project_copy imported from tests.development_tools.conftest
  - Symbol: `unused-import`

### `tests/development_tools/test_documentation_sync_checker.py`

**Count**: 2 unused import(s)

- **Line 9**: Unused import sys
  - Symbol: `unused-import`
- **Line 11**: Unused defaultdict imported from collections
  - Symbol: `unused-import`

### `tests/development_tools/test_error_scenarios.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused import stat
  - Symbol: `unused-import`

### `tests/development_tools/test_fix_documentation.py`

**Count**: 1 unused import(s)

- **Line 12**: Unused load_development_tools_module imported from tests.development_tools.conftest
  - Symbol: `unused-import`

### `tests/development_tools/test_fix_documentation_addresses.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused test_config_path imported from tests.development_tools.conftest
  - Symbol: `unused-import`

### `tests/development_tools/test_generate_function_registry.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused import sys
  - Symbol: `unused-import`

### `tests/development_tools/test_generate_module_dependencies.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused import sys
  - Symbol: `unused-import`

### `tests/development_tools/test_legacy_reference_cleanup.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused import sys
  - Symbol: `unused-import`

### `tests/development_tools/test_output_storage_archiving.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused temp_project_copy imported from tests.development_tools.conftest
  - Symbol: `unused-import`

### `tests/development_tools/test_path_drift_detection.py`

**Count**: 4 unused import(s)

- **Line 9**: Unused import pytest
  - Symbol: `unused-import`
- **Line 10**: Unused import tempfile
  - Symbol: `unused-import`
- **Line 11**: Unused import shutil
  - Symbol: `unused-import`
- **Line 12**: Unused Path imported from pathlib
  - Symbol: `unused-import`

### `tests/development_tools/test_path_drift_integration.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused temp_project_copy imported from tests.development_tools.conftest
  - Symbol: `unused-import`

### `tests/development_tools/test_regenerate_coverage_metrics.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused import sys
  - Symbol: `unused-import`

### `tests/development_tools/test_run_development_tools.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused import warnings
  - Symbol: `unused-import`

### `tests/development_tools/test_status_file_timing.py`

**Count**: 2 unused import(s)

- **Line 10**: Unused import warnings
  - Symbol: `unused-import`
- **Line 21**: Unused demo_project_root imported from tests.development_tools.conftest
  - Symbol: `unused-import`

### `tests/integration/test_task_cleanup_real.py`

**Count**: 1 unused import(s)

- **Line 12**: Unused timedelta imported from datetime
  - Symbol: `unused-import`

### `tests/integration/test_task_cleanup_real_bug_verification.py`

**Count**: 2 unused import(s)

- **Line 16**: Unused delete_task imported from tasks.task_management
  - Symbol: `unused-import`
- **Line 16**: Unused update_task imported from tasks.task_management
  - Symbol: `unused-import`

### `tests/integration/test_task_cleanup_silent_failure.py`

**Count**: 2 unused import(s)

- **Line 10**: Unused timedelta imported from datetime
  - Symbol: `unused-import`
- **Line 13**: Unused delete_task imported from tasks.task_management
  - Symbol: `unused-import`

### `tests/integration/test_task_reminder_integration.py`

**Count**: 5 unused import(s)

- **Line 8**: Unused call imported from unittest.mock
  - Symbol: `unused-import`
- **Line 12**: Unused get_task_by_id imported from tasks.task_management
  - Symbol: `unused-import`
- **Line 16**: Unused TaskManagementHandler imported from communication.command_handlers.task_handler
  - Symbol: `unused-import`
- **Line 17**: Unused ParsedCommand imported from communication.command_handlers.shared_types
  - Symbol: `unused-import`
- **Line 17**: Unused InteractionResponse imported from communication.command_handlers.shared_types
  - Symbol: `unused-import`

### `tests/test_error_handling_improvements.py`

**Count**: 1 unused import(s)

- **Line 16**: Unused MHMError imported from core.error_handling
  - Symbol: `unused-import`

### `tests/ui/test_signal_handler_integration.py`

**Count**: 1 unused import(s)

- **Line 20**: Unused QCheckBox imported from PySide6.QtWidgets
  - Symbol: `unused-import`

### `tests/unit/test_ai_chatbot_helpers.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused AIChatBotSingleton imported from ai.chatbot
  - Symbol: `unused-import`

### `tests/unit/test_command_registry.py`

**Count**: 2 unused import(s)

- **Line 13**: Unused AsyncMock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 22**: Unused import discord
  - Symbol: `unused-import`

### `tests/unit/test_config.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused import core.config
  - Symbol: `unused-import`

### `tests/unit/test_discord_api_client.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused import asyncio
  - Symbol: `unused-import`

### `tests/unit/test_discord_event_handler.py`

**Count**: 2 unused import(s)

- **Line 12**: Unused import asyncio
  - Symbol: `unused-import`
- **Line 21**: Unused import discord
  - Symbol: `unused-import`

### `tests/unit/test_email_bot_body_extraction.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused import email
  - Symbol: `unused-import`

### `tests/unit/test_logger_unit.py`

**Count**: 1 unused import(s)

- **Line 16**: Unused _get_log_paths_for_environment imported from core.logger
  - Symbol: `unused-import`

### `tests/unit/test_message_formatter.py`

**Count**: 1 unused import(s)

- **Line 14**: Unused MessageFormatter imported from communication.communication_channels.base.message_formatter
  - Symbol: `unused-import`

### `tests/unit/test_prompt_manager.py`

**Count**: 2 unused import(s)

- **Line 23**: Unused AI_SYSTEM_PROMPT_PATH imported from core.config
  - Symbol: `unused-import`
- **Line 23**: Unused AI_USE_CUSTOM_PROMPT imported from core.config
  - Symbol: `unused-import`

### `tests/unit/test_rich_formatter.py`

**Count**: 1 unused import(s)

- **Line 14**: Unused RichFormatter imported from communication.communication_channels.base.rich_formatter
  - Symbol: `unused-import`

### `tests/unit/test_user_data_manager.py`

**Count**: 1 unused import(s)

- **Line 22**: Unused delete_user_completely imported from core.user_data_manager
  - Symbol: `unused-import`

### `tests/unit/test_user_preferences.py`

**Count**: 3 unused import(s)

- **Line 20**: Unused update_user_preferences imported from core.user_data_handlers
  - Symbol: `unused-import`
- **Line 21**: Unused set_schedule_period_active imported from core.schedule_management
  - Symbol: `unused-import`
- **Line 21**: Unused is_schedule_period_active imported from core.schedule_management
  - Symbol: `unused-import`

## Type Hints Only

**Recommendation**: Consider using `TYPE_CHECKING` guard for these imports.

### `communication/communication_channels/discord/account_flow_handler.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused Optional imported from typing
  - Symbol: `unused-import`

### `communication/core/welcome_manager.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused Optional imported from typing
  - Symbol: `unused-import`

## Conditional Imports

**Recommendation**: Review carefully - these may be for optional dependencies.

### `development_tools/docs/fix_documentation_links.py`

**Count**: 1 unused import(s)

- **Line 33**: Unused ALL_GENERATED_FILES imported from shared.standard_exclusions
  - Symbol: `unused-import`

### `development_tools/functions/analyze_function_registry.py`

**Count**: 2 unused import(s)

- **Line 25**: Unused summary_block imported from shared.common
  - Symbol: `unused-import`
- **Line 25**: Unused write_text imported from shared.common
  - Symbol: `unused-import`

### `development_tools/imports/analyze_dependency_patterns.py`

**Count**: 1 unused import(s)

- **Line 23**: Unused ensure_ascii imported from shared.common
  - Symbol: `unused-import`

### `development_tools/imports/analyze_module_dependencies.py`

**Count**: 1 unused import(s)

- **Line 27**: Unused should_exclude_file imported from shared.standard_exclusions
  - Symbol: `unused-import`

### `development_tools/imports/generate_module_dependencies.py`

**Count**: 1 unused import(s)

- **Line 24**: Unused scan_all_python_files imported from analyze_module_imports
  - Symbol: `unused-import`

### `development_tools/reports/decision_support.py`

**Count**: 1 unused import(s)

- **Line 22**: Unused categorize_functions imported from functions.analyze_functions
  - Symbol: `unused-import`

### `development_tools/run_dev_tools.py`

**Count**: 1 unused import(s)

- **Line 21**: Unused config imported from development_tools
  - Symbol: `unused-import`

### `development_tools/run_development_tools.py`

**Count**: 1 unused import(s)

- **Line 36**: Unused import config
  - Symbol: `unused-import`

## Test Mocking

**Recommendation**: These imports are required for test mocking with `@patch` decorators and `patch.object()` calls.

### `tests/ai/test_ai_functionality_manual.py`

**Count**: 2 unused import(s)

- **Line 18**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 24**: Unused get_user_data imported from core.user_data_handlers
  - Symbol: `unused-import`

### `tests/ai/test_cache_manager.py`

**Count**: 1 unused import(s)

- **Line 7**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/behavior/test_base_handler_behavior.py`

**Count**: 2 unused import(s)

- **Line 11**: Unused patch imported from unittest.mock
  - Symbol: `unused-import`
- **Line 11**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/behavior/test_checkin_handler_behavior.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/behavior/test_communication_manager_behavior.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/behavior/test_interaction_handlers_behavior.py`

**Count**: 2 unused import(s)

- **Line 18**: Unused get_user_data imported from core.user_data_handlers
  - Symbol: `unused-import`
- **Line 18**: Unused save_user_data imported from core.user_data_handlers
  - Symbol: `unused-import`

### `tests/behavior/test_logger_coverage_expansion.py`

**Count**: 1 unused import(s)

- **Line 19**: Unused mock_open imported from unittest.mock
  - Symbol: `unused-import`

### `tests/behavior/test_message_router_behavior.py`

**Count**: 2 unused import(s)

- **Line 10**: Unused patch imported from unittest.mock
  - Symbol: `unused-import`
- **Line 10**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/behavior/test_profile_handler_behavior.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/behavior/test_schedule_handler_behavior.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/behavior/test_scheduler_coverage_expansion.py`

**Count**: 2 unused import(s)

- **Line 14**: Unused get_user_data imported from core.user_data_handlers
  - Symbol: `unused-import`
- **Line 21**: Unused get_user_categories imported from core.user_management
  - Symbol: `unused-import`

### `tests/behavior/test_task_handler_behavior.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/behavior/test_user_data_flow_architecture.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/behavior/test_webhook_server_behavior.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/behavior/test_welcome_handler_behavior.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/core/test_file_auditor.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/core/test_message_management.py`

**Count**: 2 unused import(s)

- **Line 8**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 10**: Unused load_default_messages imported from core.message_management
  - Symbol: `unused-import`

### `tests/core/test_schedule_utilities.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/development_tools/test_analyze_ai_work.py`

**Count**: 2 unused import(s)

- **Line 11**: Unused patch imported from unittest.mock
  - Symbol: `unused-import`
- **Line 11**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/development_tools/test_fix_documentation.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/development_tools/test_output_storage_archiving.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused patch imported from unittest.mock
  - Symbol: `unused-import`

### `tests/development_tools/test_regenerate_coverage_metrics.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/integration/test_task_cleanup_real_bug_verification.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/integration/test_task_cleanup_silent_failure.py`

**Count**: 2 unused import(s)

- **Line 9**: Unused patch imported from unittest.mock
  - Symbol: `unused-import`
- **Line 9**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/integration/test_user_creation.py`

**Count**: 3 unused import(s)

- **Line 19**: Unused update_user_account imported from core.user_data_handlers
  - Symbol: `unused-import`
- **Line 19**: Unused update_user_schedules imported from core.user_data_handlers
  - Symbol: `unused-import`
- **Line 28**: Unused validate_schedule_periods__validate_time_format imported from core.user_data_validation
  - Symbol: `unused-import`

### `tests/test_error_handling_improvements.py`

**Count**: 4 unused import(s)

- **Line 13**: Unused patch imported from unittest.mock
  - Symbol: `unused-import`
- **Line 13**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 16**: Unused DataError imported from core.error_handling
  - Symbol: `unused-import`
- **Line 16**: Unused FileOperationError imported from core.error_handling
  - Symbol: `unused-import`

### `tests/test_utilities.py`

**Count**: 3 unused import(s)

- **Line 19**: Unused create_new_user imported from core.user_management
  - Symbol: `unused-import`
- **Line 20**: Unused save_user_data imported from core.user_data_handlers
  - Symbol: `unused-import`
- **Line 21**: Unused ensure_user_directory imported from core.file_operations
  - Symbol: `unused-import`

### `tests/ui/test_account_creation_ui.py`

**Count**: 5 unused import(s)

- **Line 21**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 33**: Unused create_user_files imported from core.file_operations
  - Symbol: `unused-import`
- **Line 33**: Unused get_user_file_path imported from core.file_operations
  - Symbol: `unused-import`
- **Line 34**: Unused is_valid_email imported from core.user_data_validation
  - Symbol: `unused-import`
- **Line 34**: Unused validate_schedule_periods__validate_time_format imported from core.user_data_validation
  - Symbol: `unused-import`

### `tests/ui/test_account_creator_dialog_validation.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused patch imported from unittest.mock
  - Symbol: `unused-import`

### `tests/ui/test_category_management_dialog.py`

**Count**: 2 unused import(s)

- **Line 16**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 16**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/ui/test_channel_management_dialog_coverage_expansion.py`

**Count**: 5 unused import(s)

- **Line 16**: Unused get_user_data imported from core.user_data_handlers
  - Symbol: `unused-import`
- **Line 16**: Unused update_channel_preferences imported from core.user_data_handlers
  - Symbol: `unused-import`
- **Line 16**: Unused update_user_account imported from core.user_data_handlers
  - Symbol: `unused-import`
- **Line 17**: Unused is_valid_email imported from core.user_data_validation
  - Symbol: `unused-import`
- **Line 17**: Unused is_valid_phone imported from core.user_data_validation
  - Symbol: `unused-import`

### `tests/ui/test_dialog_behavior.py`

**Count**: 6 unused import(s)

- **Line 23**: Unused patch imported from unittest.mock
  - Symbol: `unused-import`
- **Line 23**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 23**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 32**: Unused save_user_data imported from core.user_data_handlers
  - Symbol: `unused-import`
- **Line 33**: Unused create_user_files imported from core.file_operations
  - Symbol: `unused-import`
- **Line 33**: Unused get_user_file_path imported from core.file_operations
  - Symbol: `unused-import`

### `tests/ui/test_dialog_coverage_expansion.py`

**Count**: 7 unused import(s)

- **Line 26**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 26**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 35**: Unused save_user_data imported from core.user_data_handlers
  - Symbol: `unused-import`
- **Line 35**: Unused get_user_data imported from core.user_data_handlers
  - Symbol: `unused-import`
- **Line 36**: Unused create_user_files imported from core.file_operations
  - Symbol: `unused-import`
- **Line 37**: Unused get_schedule_time_periods imported from core.schedule_management
  - Symbol: `unused-import`
- **Line 37**: Unused set_schedule_periods imported from core.schedule_management
  - Symbol: `unused-import`

### `tests/ui/test_message_editor_dialog.py`

**Count**: 1 unused import(s)

- **Line 16**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/ui/test_process_watcher_dialog.py`

**Count**: 1 unused import(s)

- **Line 16**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/ui/test_signal_handler_integration.py`

**Count**: 2 unused import(s)

- **Line 19**: Unused patch imported from unittest.mock
  - Symbol: `unused-import`
- **Line 19**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/ui/test_task_crud_dialog.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/ui/test_task_management_dialog.py`

**Count**: 1 unused import(s)

- **Line 18**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/ui/test_task_settings_widget.py`

**Count**: 2 unused import(s)

- **Line 18**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 18**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/ui/test_ui_app_qt_main.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/ui/test_ui_button_verification.py`

**Count**: 2 unused import(s)

- **Line 14**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 14**: Unused patch imported from unittest.mock
  - Symbol: `unused-import`

### `tests/ui/test_ui_components_headless.py`

**Count**: 1 unused import(s)

- **Line 14**: Unused patch imported from unittest.mock
  - Symbol: `unused-import`

### `tests/ui/test_ui_widgets_coverage_expansion.py`

**Count**: 2 unused import(s)

- **Line 22**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 22**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/ui/test_user_analytics_dialog.py`

**Count**: 1 unused import(s)

- **Line 16**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/ui/test_user_profile_dialog_coverage_expansion.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/ui/test_widget_behavior.py`

**Count**: 7 unused import(s)

- **Line 24**: Unused patch imported from unittest.mock
  - Symbol: `unused-import`
- **Line 24**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 24**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 33**: Unused save_user_data imported from core.user_data_handlers
  - Symbol: `unused-import`
- **Line 33**: Unused get_user_data imported from core.user_data_handlers
  - Symbol: `unused-import`
- **Line 34**: Unused create_user_files imported from core.file_operations
  - Symbol: `unused-import`
- **Line 34**: Unused get_user_file_path imported from core.file_operations
  - Symbol: `unused-import`

### `tests/ui/test_widget_behavior_simple.py`

**Count**: 2 unused import(s)

- **Line 15**: Unused patch imported from unittest.mock
  - Symbol: `unused-import`
- **Line 15**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/unit/test_admin_panel.py`

**Count**: 2 unused import(s)

- **Line 17**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 17**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/unit/test_ai_chatbot_helpers.py`

**Count**: 2 unused import(s)

- **Line 8**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 8**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/unit/test_channel_orchestrator.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/unit/test_checkin_management_dialog.py`

**Count**: 1 unused import(s)

- **Line 19**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/unit/test_checkin_view.py`

**Count**: 2 unused import(s)

- **Line 9**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 9**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/unit/test_command_parser_helpers.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/unit/test_communication_core_init.py`

**Count**: 2 unused import(s)

- **Line 12**: Unused patch imported from unittest.mock
  - Symbol: `unused-import`
- **Line 12**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/unit/test_communication_init.py`

**Count**: 2 unused import(s)

- **Line 12**: Unused patch imported from unittest.mock
  - Symbol: `unused-import`
- **Line 12**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/unit/test_email_bot_body_extraction.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/unit/test_enhanced_checkin_responses.py`

**Count**: 1 unused import(s)

- **Line 12**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/unit/test_file_operations.py`

**Count**: 1 unused import(s)

- **Line 20**: Unused FileOperationError imported from core.error_handling
  - Symbol: `unused-import`

### `tests/unit/test_interaction_handlers_helpers.py`

**Count**: 2 unused import(s)

- **Line 9**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 9**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/unit/test_logger_unit.py`

**Count**: 2 unused import(s)

- **Line 13**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 13**: Unused mock_open imported from unittest.mock
  - Symbol: `unused-import`

### `tests/unit/test_message_formatter.py`

**Count**: 2 unused import(s)

- **Line 12**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 20**: Unused DataError imported from core.error_handling
  - Symbol: `unused-import`

### `tests/unit/test_prompt_manager.py`

**Count**: 2 unused import(s)

- **Line 19**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 19**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/unit/test_recurring_tasks.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused _create_next_recurring_task_instance imported from tasks.task_management
  - Symbol: `unused-import`

### `tests/unit/test_ui_management.py`

**Count**: 1 unused import(s)

- **Line 16**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/unit/test_user_context.py`

**Count**: 2 unused import(s)

- **Line 16**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 16**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/unit/test_user_data_handlers.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`

### `tests/unit/test_user_data_manager.py`

**Count**: 3 unused import(s)

- **Line 14**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 14**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 14**: Unused mock_open imported from unittest.mock
  - Symbol: `unused-import`

### `tests/unit/test_user_management.py`

**Count**: 3 unused import(s)

- **Line 10**: Unused patch imported from unittest.mock
  - Symbol: `unused-import`
- **Line 12**: Unused update_user_account imported from core.user_data_handlers
  - Symbol: `unused-import`
- **Line 12**: Unused update_user_context imported from core.user_data_handlers
  - Symbol: `unused-import`

### `tests/unit/test_user_preferences.py`

**Count**: 3 unused import(s)

- **Line 16**: Unused Mock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 16**: Unused MagicMock imported from unittest.mock
  - Symbol: `unused-import`
- **Line 20**: Unused get_user_data imported from core.user_data_handlers
  - Symbol: `unused-import`

## Qt Testing

**Recommendation**: These Qt imports are required for UI testing and signal handling.

### `tests/ui/test_account_creation_ui.py`

**Count**: 4 unused import(s)

- **Line 24**: Unused QWidget imported from PySide6.QtWidgets
  - Symbol: `unused-import`
- **Line 24**: Unused QMessageBox imported from PySide6.QtWidgets
  - Symbol: `unused-import`
- **Line 25**: Unused Qt imported from PySide6.QtCore
  - Symbol: `unused-import`
- **Line 25**: Unused QTimer imported from PySide6.QtCore
  - Symbol: `unused-import`

### `tests/ui/test_category_management_dialog.py`

**Count**: 3 unused import(s)

- **Line 17**: Unused QMessageBox imported from PySide6.QtWidgets
  - Symbol: `unused-import`
- **Line 18**: Unused Qt imported from PySide6.QtCore
  - Symbol: `unused-import`
- **Line 19**: Unused QTest imported from PySide6.QtTest
  - Symbol: `unused-import`

### `tests/ui/test_dialog_behavior.py`

**Count**: 5 unused import(s)

- **Line 26**: Unused QWidget imported from PySide6.QtWidgets
  - Symbol: `unused-import`
- **Line 26**: Unused QMessageBox imported from PySide6.QtWidgets
  - Symbol: `unused-import`
- **Line 26**: Unused QDialog imported from PySide6.QtWidgets
  - Symbol: `unused-import`
- **Line 27**: Unused Qt imported from PySide6.QtCore
  - Symbol: `unused-import`
- **Line 27**: Unused QTimer imported from PySide6.QtCore
  - Symbol: `unused-import`

### `tests/ui/test_dialog_coverage_expansion.py`

**Count**: 4 unused import(s)

- **Line 29**: Unused QWidget imported from PySide6.QtWidgets
  - Symbol: `unused-import`
- **Line 30**: Unused Qt imported from PySide6.QtCore
  - Symbol: `unused-import`
- **Line 30**: Unused QTimer imported from PySide6.QtCore
  - Symbol: `unused-import`
- **Line 31**: Unused QTest imported from PySide6.QtTest
  - Symbol: `unused-import`

### `tests/ui/test_message_editor_dialog.py`

**Count**: 3 unused import(s)

- **Line 17**: Unused QTableWidgetItem imported from PySide6.QtWidgets
  - Symbol: `unused-import`
- **Line 18**: Unused Qt imported from PySide6.QtCore
  - Symbol: `unused-import`
- **Line 19**: Unused QTest imported from PySide6.QtTest
  - Symbol: `unused-import`

### `tests/ui/test_process_watcher_dialog.py`

**Count**: 3 unused import(s)

- **Line 19**: Unused Qt imported from PySide6.QtCore
  - Symbol: `unused-import`
- **Line 19**: Unused QTimer imported from PySide6.QtCore
  - Symbol: `unused-import`
- **Line 20**: Unused QTest imported from PySide6.QtTest
  - Symbol: `unused-import`

### `tests/ui/test_signal_handler_integration.py`

**Count**: 3 unused import(s)

- **Line 20**: Unused QLineEdit imported from PySide6.QtWidgets
  - Symbol: `unused-import`
- **Line 21**: Unused Qt imported from PySide6.QtCore
  - Symbol: `unused-import`
- **Line 22**: Unused QTest imported from PySide6.QtTest
  - Symbol: `unused-import`

### `tests/ui/test_task_crud_dialog.py`

**Count**: 1 unused import(s)

- **Line 14**: Unused QTableWidgetItem imported from PySide6.QtWidgets
  - Symbol: `unused-import`

### `tests/ui/test_task_management_dialog.py`

**Count**: 3 unused import(s)

- **Line 19**: Unused QMessageBox imported from PySide6.QtWidgets
  - Symbol: `unused-import`
- **Line 20**: Unused Qt imported from PySide6.QtCore
  - Symbol: `unused-import`
- **Line 21**: Unused QTest imported from PySide6.QtTest
  - Symbol: `unused-import`

### `tests/ui/test_task_settings_widget.py`

**Count**: 4 unused import(s)

- **Line 19**: Unused QWidget imported from PySide6.QtWidgets
  - Symbol: `unused-import`
- **Line 19**: Unused QMessageBox imported from PySide6.QtWidgets
  - Symbol: `unused-import`
- **Line 20**: Unused Qt imported from PySide6.QtCore
  - Symbol: `unused-import`
- **Line 21**: Unused QTest imported from PySide6.QtTest
  - Symbol: `unused-import`

### `tests/ui/test_ui_widgets_coverage_expansion.py`

**Count**: 5 unused import(s)

- **Line 26**: Unused QWidget imported from PySide6.QtWidgets
  - Symbol: `unused-import`
- **Line 26**: Unused QListWidgetItem imported from PySide6.QtWidgets
  - Symbol: `unused-import`
- **Line 26**: Unused QInputDialog imported from PySide6.QtWidgets
  - Symbol: `unused-import`
- **Line 27**: Unused QTimer imported from PySide6.QtCore
  - Symbol: `unused-import`
- **Line 28**: Unused QTest imported from PySide6.QtTest
  - Symbol: `unused-import`

### `tests/ui/test_user_analytics_dialog.py`

**Count**: 2 unused import(s)

- **Line 19**: Unused Qt imported from PySide6.QtCore
  - Symbol: `unused-import`
- **Line 20**: Unused QTest imported from PySide6.QtTest
  - Symbol: `unused-import`

### `tests/ui/test_user_profile_dialog_coverage_expansion.py`

**Count**: 1 unused import(s)

- **Line 18**: Unused QTest imported from PySide6.QtTest
  - Symbol: `unused-import`

### `tests/ui/test_widget_behavior.py`

**Count**: 5 unused import(s)

- **Line 27**: Unused QMessageBox imported from PySide6.QtWidgets
  - Symbol: `unused-import`
- **Line 27**: Unused QDialog imported from PySide6.QtWidgets
  - Symbol: `unused-import`
- **Line 28**: Unused Qt imported from PySide6.QtCore
  - Symbol: `unused-import`
- **Line 28**: Unused QTimer imported from PySide6.QtCore
  - Symbol: `unused-import`
- **Line 29**: Unused QTest imported from PySide6.QtTest
  - Symbol: `unused-import`

### `tests/ui/test_widget_behavior_simple.py`

**Count**: 3 unused import(s)

- **Line 16**: Unused QWidget imported from PySide6.QtWidgets
  - Symbol: `unused-import`
- **Line 17**: Unused Qt imported from PySide6.QtCore
  - Symbol: `unused-import`
- **Line 18**: Unused QTest imported from PySide6.QtTest
  - Symbol: `unused-import`

### `tests/unit/test_admin_panel.py`

**Count**: 2 unused import(s)

- **Line 19**: Unused Qt imported from PySide6.QtCore
  - Symbol: `unused-import`
- **Line 20**: Unused QTest imported from PySide6.QtTest
  - Symbol: `unused-import`

### `tests/unit/test_checkin_management_dialog.py`

**Count**: 3 unused import(s)

- **Line 20**: Unused QMessageBox imported from PySide6.QtWidgets
  - Symbol: `unused-import`
- **Line 21**: Unused Qt imported from PySide6.QtCore
  - Symbol: `unused-import`
- **Line 22**: Unused QTest imported from PySide6.QtTest
  - Symbol: `unused-import`

## Test Infrastructure

**Recommendation**: These imports are required for test infrastructure (fixtures, data creation, etc.).

### `development_tools/tests/generate_test_coverage.py`

**Count**: 1 unused import(s)

- **Line 17**: Unused import json
  - Symbol: `unused-import`

### `tests/ai/test_ai_core.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused import time
  - Symbol: `unused-import`

### `tests/ai/test_context_includes_recent_messages.py`

**Count**: 1 unused import(s)

- **Line 1**: Unused import os
  - Symbol: `unused-import`

### `tests/behavior/test_checkin_expiry_semantics.py`

**Count**: 1 unused import(s)

- **Line 1**: Unused import os
  - Symbol: `unused-import`

### `tests/behavior/test_checkin_handler_behavior.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused datetime imported from datetime
  - Symbol: `unused-import`

### `tests/behavior/test_communication_manager_behavior.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused import time
  - Symbol: `unused-import`

### `tests/behavior/test_conversation_flow_manager_behavior.py`

**Count**: 3 unused import(s)

- **Line 10**: Unused import json
  - Symbol: `unused-import`
- **Line 11**: Unused import os
  - Symbol: `unused-import`
- **Line 13**: Unused datetime imported from datetime
  - Symbol: `unused-import`

### `tests/behavior/test_discord_checkin_retry_behavior.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused datetime imported from datetime
  - Symbol: `unused-import`

### `tests/behavior/test_discord_task_reminder_followup.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused datetime imported from datetime
  - Symbol: `unused-import`

### `tests/behavior/test_headless_service_behavior.py`

**Count**: 4 unused import(s)

- **Line 10**: Unused import os
  - Symbol: `unused-import`
- **Line 11**: Unused import json
  - Symbol: `unused-import`
- **Line 14**: Unused Path imported from pathlib
  - Symbol: `unused-import`
- **Line 18**: Unused TestUserFactory imported from tests.test_utilities
  - Symbol: `unused-import`

### `tests/behavior/test_task_error_handling.py`

**Count**: 2 unused import(s)

- **Line 10**: Unused import json
  - Symbol: `unused-import`
- **Line 11**: Unused import os
  - Symbol: `unused-import`

### `tests/behavior/test_user_data_flow_architecture.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused import json
  - Symbol: `unused-import`

### `tests/behavior/test_webhook_server_behavior.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused import threading
  - Symbol: `unused-import`

### `tests/behavior/test_welcome_manager_behavior.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused import os
  - Symbol: `unused-import`

### `tests/communication/test_retry_manager.py`

**Count**: 2 unused import(s)

- **Line 6**: Unused import time
  - Symbol: `unused-import`
- **Line 7**: Unused import threading
  - Symbol: `unused-import`

### `tests/core/test_message_management.py`

**Count**: 2 unused import(s)

- **Line 7**: Unused import json
  - Symbol: `unused-import`
- **Line 9**: Unused datetime imported from datetime
  - Symbol: `unused-import`

### `tests/core/test_schedule_utilities.py`

**Count**: 1 unused import(s)

- **Line 7**: Unused time imported from datetime
  - Symbol: `unused-import`

### `tests/debug_file_paths.py`

**Count**: 1 unused import(s)

- **Line 1**: Unused import pytest
  - Symbol: `unused-import`

### `tests/development_tools/test_analyze_ai_work.py`

**Count**: 2 unused import(s)

- **Line 9**: Unused import tempfile
  - Symbol: `unused-import`
- **Line 10**: Unused Path imported from pathlib
  - Symbol: `unused-import`

### `tests/development_tools/test_analyze_documentation.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused import tempfile
  - Symbol: `unused-import`

### `tests/development_tools/test_analyze_missing_addresses.py`

**Count**: 2 unused import(s)

- **Line 8**: Unused import tempfile
  - Symbol: `unused-import`
- **Line 9**: Unused Path imported from pathlib
  - Symbol: `unused-import`

### `tests/development_tools/test_documentation_sync_checker.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused Path imported from pathlib
  - Symbol: `unused-import`

### `tests/development_tools/test_error_scenarios.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused import shutil
  - Symbol: `unused-import`

### `tests/development_tools/test_fix_documentation.py`

**Count**: 2 unused import(s)

- **Line 8**: Unused import tempfile
  - Symbol: `unused-import`
- **Line 9**: Unused Path imported from pathlib
  - Symbol: `unused-import`

### `tests/development_tools/test_fix_documentation_addresses.py`

**Count**: 2 unused import(s)

- **Line 8**: Unused import tempfile
  - Symbol: `unused-import`
- **Line 9**: Unused Path imported from pathlib
  - Symbol: `unused-import`

### `tests/development_tools/test_fix_documentation_ascii.py`

**Count**: 2 unused import(s)

- **Line 8**: Unused import tempfile
  - Symbol: `unused-import`
- **Line 9**: Unused Path imported from pathlib
  - Symbol: `unused-import`

### `tests/development_tools/test_generate_function_registry.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused Path imported from pathlib
  - Symbol: `unused-import`

### `tests/development_tools/test_generate_module_dependencies.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused Path imported from pathlib
  - Symbol: `unused-import`

### `tests/development_tools/test_legacy_reference_cleanup.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused Path imported from pathlib
  - Symbol: `unused-import`

### `tests/development_tools/test_output_storage_archiving.py`

**Count**: 2 unused import(s)

- **Line 8**: Unused import json
  - Symbol: `unused-import`
- **Line 10**: Unused Path imported from pathlib
  - Symbol: `unused-import`

### `tests/development_tools/test_path_drift_integration.py`

**Count**: 2 unused import(s)

- **Line 9**: Unused import tempfile
  - Symbol: `unused-import`
- **Line 10**: Unused Path imported from pathlib
  - Symbol: `unused-import`

### `tests/development_tools/test_regenerate_coverage_metrics.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused Path imported from pathlib
  - Symbol: `unused-import`

### `tests/integration/test_account_management.py`

**Count**: 2 unused import(s)

- **Line 11**: Unused import time
  - Symbol: `unused-import`
- **Line 12**: Unused import tempfile
  - Symbol: `unused-import`

### `tests/integration/test_task_cleanup_real.py`

**Count**: 1 unused import(s)

- **Line 12**: Unused datetime imported from datetime
  - Symbol: `unused-import`

### `tests/integration/test_task_cleanup_silent_failure.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused datetime imported from datetime
  - Symbol: `unused-import`

### `tests/integration/test_task_reminder_integration.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused import time
  - Symbol: `unused-import`

### `tests/integration/test_user_creation.py`

**Count**: 3 unused import(s)

- **Line 14**: Unused import json
  - Symbol: `unused-import`
- **Line 15**: Unused import tempfile
  - Symbol: `unused-import`
- **Line 17**: Unused datetime imported from datetime
  - Symbol: `unused-import`

### `tests/test_error_handling_improvements.py`

**Count**: 1 unused import(s)

- **Line 14**: Unused Path imported from pathlib
  - Symbol: `unused-import`

### `tests/test_utilities.py`

**Count**: 2 unused import(s)

- **Line 8**: Unused import tempfile
  - Symbol: `unused-import`
- **Line 13**: Unused Path imported from pathlib
  - Symbol: `unused-import`

### `tests/ui/test_account_creation_ui.py`

**Count**: 6 unused import(s)

- **Line 20**: Unused import shutil
  - Symbol: `unused-import`
- **Line 23**: Unused Path imported from pathlib
  - Symbol: `unused-import`
- **Line 36**: Unused CategorySelectionWidget imported from ui.widgets.category_selection_widget
  - Symbol: `unused-import`
- **Line 37**: Unused ChannelSelectionWidget imported from ui.widgets.channel_selection_widget
  - Symbol: `unused-import`
- **Line 38**: Unused TaskSettingsWidget imported from ui.widgets.task_settings_widget
  - Symbol: `unused-import`
- **Line 39**: Unused CheckinSettingsWidget imported from ui.widgets.checkin_settings_widget
  - Symbol: `unused-import`

### `tests/ui/test_dialog_behavior.py`

**Count**: 7 unused import(s)

- **Line 22**: Unused import shutil
  - Symbol: `unused-import`
- **Line 24**: Unused datetime imported from datetime
  - Symbol: `unused-import`
- **Line 24**: Unused time imported from datetime
  - Symbol: `unused-import`
- **Line 39**: Unused open_schedule_editor imported from ui.dialogs.schedule_editor_dialog
  - Symbol: `unused-import`
- **Line 40**: Unused TaskEditDialog imported from ui.dialogs.task_edit_dialog
  - Symbol: `unused-import`
- **Line 41**: Unused TaskCrudDialog imported from ui.dialogs.task_crud_dialog
  - Symbol: `unused-import`
- **Line 42**: Unused TaskCompletionDialog imported from ui.dialogs.task_completion_dialog
  - Symbol: `unused-import`

### `tests/ui/test_dialog_coverage_expansion.py`

**Count**: 6 unused import(s)

- **Line 25**: Unused import shutil
  - Symbol: `unused-import`
- **Line 27**: Unused datetime imported from datetime
  - Symbol: `unused-import`
- **Line 27**: Unused time imported from datetime
  - Symbol: `unused-import`
- **Line 28**: Unused Path imported from pathlib
  - Symbol: `unused-import`
- **Line 40**: Unused TaskCrudDialog imported from ui.dialogs.task_crud_dialog
  - Symbol: `unused-import`
- **Line 43**: Unused TestDataFactory imported from tests.test_utilities
  - Symbol: `unused-import`

### `tests/ui/test_dialogs.py`

**Count**: 1 unused import(s)

- **Line 15**: Unused Path imported from pathlib
  - Symbol: `unused-import`

### `tests/ui/test_ui_widgets_coverage_expansion.py`

**Count**: 1 unused import(s)

- **Line 23**: Unused datetime imported from datetime
  - Symbol: `unused-import`

### `tests/ui/test_user_analytics_dialog.py`

**Count**: 1 unused import(s)

- **Line 17**: Unused datetime imported from datetime
  - Symbol: `unused-import`

### `tests/ui/test_user_profile_dialog_coverage_expansion.py`

**Count**: 4 unused import(s)

- **Line 11**: Unused import os
  - Symbol: `unused-import`
- **Line 12**: Unused import tempfile
  - Symbol: `unused-import`
- **Line 14**: Unused datetime imported from datetime
  - Symbol: `unused-import`
- **Line 21**: Unused TestDataFactory imported from tests.test_utilities
  - Symbol: `unused-import`

### `tests/ui/test_widget_behavior.py`

**Count**: 5 unused import(s)

- **Line 22**: Unused import tempfile
  - Symbol: `unused-import`
- **Line 23**: Unused import shutil
  - Symbol: `unused-import`
- **Line 25**: Unused datetime imported from datetime
  - Symbol: `unused-import`
- **Line 25**: Unused time imported from datetime
  - Symbol: `unused-import`
- **Line 35**: Unused TestUserDataFactory imported from tests.test_utilities
  - Symbol: `unused-import`

### `tests/unit/test_file_locking.py`

**Count**: 1 unused import(s)

- **Line 14**: Unused Path imported from pathlib
  - Symbol: `unused-import`

### `tests/unit/test_file_operations.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused Path imported from pathlib
  - Symbol: `unused-import`

### `tests/unit/test_logger_unit.py`

**Count**: 1 unused import(s)

- **Line 12**: Unused import json
  - Symbol: `unused-import`

### `tests/unit/test_prompt_manager.py`

**Count**: 3 unused import(s)

- **Line 17**: Unused import os
  - Symbol: `unused-import`
- **Line 18**: Unused import tempfile
  - Symbol: `unused-import`
- **Line 20**: Unused Path imported from pathlib
  - Symbol: `unused-import`

### `tests/unit/test_scripts_exclusion_policy.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused import os
  - Symbol: `unused-import`

### `tests/unit/test_user_data_manager.py`

**Count**: 2 unused import(s)

- **Line 19**: Unused Path imported from pathlib
  - Symbol: `unused-import`
- **Line 20**: Unused datetime imported from datetime
  - Symbol: `unused-import`

### `tests/unit/test_user_preferences.py`

**Count**: 1 unused import(s)

- **Line 17**: Unused Path imported from pathlib
  - Symbol: `unused-import`

## Production Test Mocking

**Recommendation**: These imports are required in production code for test mocking. Keep them.

### `communication/core/channel_orchestrator.py`

**Count**: 1 unused import(s)

- **Line 19**: Unused determine_file_path imported from core.file_operations
  - Symbol: `unused-import`

### `communication/core/factory.py`

**Count**: 2 unused import(s)

- **Line 5**: Unused get_available_channels imported from core.config
  - Symbol: `unused-import`
- **Line 5**: Unused get_channel_class_mapping imported from core.config
  - Symbol: `unused-import`

## Overall Recommendations

1. **Obvious Unused**: Review and remove obvious unused imports to improve code cleanliness
2. **Type Hints**: For type hint imports, consider using `from __future__ import annotations` and `TYPE_CHECKING` (note: the word "annotations" here refers to the Python `__future__` feature name, not a module to import)
3. **Re-exports**: Verify `__init__.py` imports are intentional re-exports
4. **Conditional Imports**: Be cautious with conditional imports - they may be handling optional dependencies
5. **Star Imports**: Consider replacing star imports with explicit imports for better clarity
6. **Test Mocking**: Keep imports required for `@patch` decorators and `patch.object()` calls
7. **Qt Testing**: Keep Qt imports required for UI testing and signal handling
8. **Test Infrastructure**: Keep imports required for test fixtures and data creation
9. **Production Test Mocking**: Keep imports in production code that are mocked by tests
10. **UI Imports**: Keep Qt imports required for UI functionality
