# Unused Imports Report

> **File**: `development_docs/UNUSED_IMPORTS_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-01-19 05:46:08
> **Source**: `python development_tools/run_development_tools.py unused-imports-report` - Unused Imports Report Generator

## Summary Statistics

- **Total Files Scanned**: 412
- **Files with Unused Imports**: 190
- **Total Unused Imports**: 543

## Breakdown by Category

- **Obvious Unused**: 155 imports
- **Type Hints Only**: 29 imports
- **Re Exports**: 0 imports
- **Conditional Imports**: 1 imports
- **Star Imports**: 0 imports
- **Test Mocking**: 147 imports
- **Qt Testing**: 54 imports
- **Test Infrastructure**: 152 imports
- **Production Test Mocking**: 4 imports
- **Ui Imports**: 1 imports

## Obvious Unused

**Recommendation**: These imports can likely be safely removed.

### `ai/cache_manager.py`

**Count**: 3 unused import(s)

- **Line 6**: Unused Dict imported from typing
- **Line 6**: Unused Optional imported from typing
- **Line 6**: Unused Tuple imported from typing

### `ai/chatbot.py`

**Count**: 2 unused import(s)

- **Line 16**: Unused Optional imported from typing
- **Line 44**: Unused datetime imported from datetime

### `ai/context_builder.py`

**Count**: 2 unused import(s)

- **Line 3**: Unused Dict imported from typing
- **Line 3**: Unused List imported from typing

### `ai/conversation_history.py`

**Count**: 2 unused import(s)

- **Line 3**: Unused Dict imported from typing
- **Line 3**: Unused List imported from typing

### `ai/prompt_manager.py`

**Count**: 2 unused import(s)

- **Line 4**: Unused Dict imported from typing
- **Line 4**: Unused Optional imported from typing

### `communication/command_handlers/account_handler.py`

**Count**: 3 unused import(s)

- **Line 7**: Unused Dict imported from typing
- **Line 7**: Unused List imported from typing
- **Line 7**: Unused Optional imported from typing

### `communication/command_handlers/analytics_handler.py`

**Count**: 2 unused import(s)

- **Line 3**: Unused Dict imported from typing
- **Line 3**: Unused List imported from typing

### `communication/command_handlers/base_handler.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused List imported from typing

### `communication/command_handlers/checkin_handler.py`

**Count**: 2 unused import(s)

- **Line 3**: Unused Dict imported from typing
- **Line 3**: Unused List imported from typing

### `communication/command_handlers/interaction_handlers.py`

**Count**: 3 unused import(s)

- **Line 11**: Unused Dict imported from typing
- **Line 11**: Unused List imported from typing
- **Line 11**: Unused Optional imported from typing

### `communication/command_handlers/notebook_handler.py`

**Count**: 4 unused import(s)

- **Line 10**: Unused Dict imported from typing
- **Line 10**: Unused List imported from typing
- **Line 10**: Unused Optional imported from typing
- **Line 14**: Unused TIMESTAMP_FULL imported from core.time_utilities

### `communication/command_handlers/profile_handler.py`

**Count**: 2 unused import(s)

- **Line 3**: Unused Dict imported from typing
- **Line 3**: Unused List imported from typing

### `communication/command_handlers/schedule_handler.py`

**Count**: 2 unused import(s)

- **Line 3**: Unused Dict imported from typing
- **Line 3**: Unused List imported from typing

### `communication/command_handlers/shared_types.py`

**Count**: 3 unused import(s)

- **Line 3**: Unused Dict imported from typing
- **Line 3**: Unused List imported from typing
- **Line 3**: Unused Optional imported from typing

### `communication/command_handlers/task_handler.py`

**Count**: 2 unused import(s)

- **Line 10**: Unused Dict imported from typing
- **Line 10**: Unused Optional imported from typing

### `communication/communication_channels/base/base_channel.py`

**Count**: 3 unused import(s)

- **Line 3**: Unused Optional imported from typing
- **Line 3**: Unused Dict imported from typing
- **Line 3**: Unused List imported from typing

### `communication/communication_channels/base/command_registry.py`

**Count**: 3 unused import(s)

- **Line 3**: Unused Dict imported from typing
- **Line 3**: Unused List imported from typing
- **Line 3**: Unused Optional imported from typing

### `communication/communication_channels/base/message_formatter.py`

**Count**: 3 unused import(s)

- **Line 3**: Unused Dict imported from typing
- **Line 3**: Unused List imported from typing
- **Line 3**: Unused Optional imported from typing

### `communication/communication_channels/base/rich_formatter.py`

**Count**: 2 unused import(s)

- **Line 3**: Unused Dict imported from typing
- **Line 3**: Unused List imported from typing

### `communication/communication_channels/discord/api_client.py`

**Count**: 4 unused import(s)

- **Line 6**: Unused Dict imported from typing
- **Line 6**: Unused List imported from typing
- **Line 6**: Unused Optional imported from typing
- **Line 6**: Unused Union imported from typing

### `communication/communication_channels/discord/bot.py`

**Count**: 3 unused import(s)

- **Line 8**: Unused List imported from typing
- **Line 8**: Unused Dict imported from typing
- **Line 8**: Unused Optional imported from typing

### `communication/communication_channels/discord/event_handler.py`

**Count**: 3 unused import(s)

- **Line 5**: Unused Dict imported from typing
- **Line 5**: Unused List imported from typing
- **Line 5**: Unused Optional imported from typing

### `communication/communication_channels/discord/webhook_handler.py`

**Count**: 2 unused import(s)

- **Line 9**: Unused Dict imported from typing
- **Line 9**: Unused Optional imported from typing

### `communication/communication_channels/discord/welcome_handler.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused Optional imported from typing

### `communication/communication_channels/email/bot.py`

**Count**: 4 unused import(s)

- **Line 10**: Unused List imported from typing
- **Line 10**: Unused Dict imported from typing
- **Line 10**: Unused Optional imported from typing
- **Line 10**: Unused Tuple imported from typing

### `communication/core/channel_monitor.py`

**Count**: 2 unused import(s)

- **Line 5**: Unused Dict imported from typing
- **Line 5**: Unused Optional imported from typing

### `communication/core/channel_orchestrator.py`

**Count**: 2 unused import(s)

- **Line 8**: Unused Dict imported from typing
- **Line 8**: Unused Optional imported from typing

### `communication/core/factory.py`

**Count**: 3 unused import(s)

- **Line 1**: Unused Dict imported from typing
- **Line 1**: Unused Type imported from typing
- **Line 1**: Unused Optional imported from typing

### `communication/core/welcome_manager.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused Dict imported from typing

### `communication/message_processing/command_parser.py`

**Count**: 3 unused import(s)

- **Line 14**: Unused Dict imported from typing
- **Line 14**: Unused List imported from typing
- **Line 14**: Unused Optional imported from typing

### `communication/message_processing/conversation_flow_manager.py`

**Count**: 2 unused import(s)

- **Line 19**: Unused import os
- **Line 23**: Unused Optional imported from typing

### `communication/message_processing/interaction_manager.py`

**Count**: 3 unused import(s)

- **Line 13**: Unused Optional imported from typing
- **Line 13**: Unused Dict imported from typing
- **Line 13**: Unused List imported from typing

### `communication/message_processing/message_router.py`

**Count**: 2 unused import(s)

- **Line 3**: Unused Optional imported from typing
- **Line 3**: Unused List imported from typing

### `core/checkin_analytics.py`

**Count**: 3 unused import(s)

- **Line 11**: Unused Dict imported from typing
- **Line 11**: Unused List imported from typing
- **Line 11**: Unused Optional imported from typing

### `core/checkin_dynamic_manager.py`

**Count**: 3 unused import(s)

- **Line 7**: Unused Dict imported from typing
- **Line 7**: Unused Optional imported from typing
- **Line 7**: Unused Tuple imported from typing

### `core/config.py`

**Count**: 3 unused import(s)

- **Line 9**: Unused Dict imported from typing
- **Line 9**: Unused Tuple imported from typing
- **Line 9**: Unused Optional imported from typing

### `core/error_handling.py`

**Count**: 2 unused import(s)

- **Line 14**: Unused Dict imported from typing
- **Line 14**: Unused List imported from typing

### `core/file_auditor.py`

**Count**: 3 unused import(s)

- **Line 24**: Unused Dict imported from typing
- **Line 24**: Unused Optional imported from typing
- **Line 24**: Unused List imported from typing

### `core/file_operations.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused datetime imported from datetime

### `core/headless_service.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused Optional imported from typing

### `core/response_tracking.py`

**Count**: 1 unused import(s)

- **Line 12**: Unused TIMESTAMP_FULL imported from core.time_utilities

### `core/schedule_management.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused Dict imported from typing

### `core/schedule_utilities.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused Optional imported from typing

### `core/scheduler.py`

**Count**: 2 unused import(s)

- **Line 12**: Unused Dict imported from typing
- **Line 17**: Unused DATE_DISPLAY_WEEKDAY imported from core.time_utilities

### `core/schemas.py`

**Count**: 2 unused import(s)

- **Line 12**: Unused Dict imported from typing
- **Line 12**: Unused Optional imported from typing

### `core/service.py`

**Count**: 1 unused import(s)

- **Line 35**: Unused TIMESTAMP_FULL imported from core.time_utilities

### `core/user_data_handlers.py`

**Count**: 5 unused import(s)

- **Line 12**: Unused datetime imported from datetime
- **Line 14**: Unused Dict imported from typing
- **Line 14**: Unused List imported from typing
- **Line 14**: Unused Union imported from typing
- **Line 14**: Unused Optional imported from typing

### `core/user_data_manager.py`

**Count**: 1 unused import(s)

- **Line 12**: Unused Optional imported from typing

### `core/user_data_validation.py`

**Count**: 5 unused import(s)

- **Line 9**: Unused Tuple imported from typing
- **Line 9**: Unused List imported from typing
- **Line 9**: Unused Optional imported from typing
- **Line 12**: Unused DATE_ONLY imported from core.time_utilities
- **Line 12**: Unused TIME_ONLY_MINUTE imported from core.time_utilities

### `development_tools/docs/generate_directory_tree.py`

**Count**: 1 unused import(s)

- **Line 20**: Unused datetime imported from datetime

### `development_tools/functions/generate_function_docstrings.py`

**Count**: 1 unused import(s)

- **Line 20**: Unused datetime imported from datetime

### `development_tools/imports/generate_unused_imports_report.py`

**Count**: 1 unused import(s)

- **Line 25**: Unused datetime imported from datetime

### `development_tools/shared/common.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused get_exclusions imported from development_tools.shared.standard_exclusions

### `notebook/notebook_data_handlers.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused List imported from typing

### `notebook/notebook_data_manager.py`

**Count**: 4 unused import(s)

- **Line 9**: Unused List imported from typing
- **Line 9**: Unused Optional imported from typing
- **Line 9**: Unused Dict imported from typing
- **Line 15**: Unused TIMESTAMP_FULL imported from core.time_utilities

### `notebook/notebook_validation.py`

**Count**: 2 unused import(s)

- **Line 10**: Unused Optional imported from typing
- **Line 10**: Unused Tuple imported from typing

### `notebook/schemas.py`

**Count**: 4 unused import(s)

- **Line 8**: Unused List imported from typing
- **Line 8**: Unused Optional imported from typing
- **Line 10**: Unused datetime imported from datetime
- **Line 15**: Unused TIMESTAMP_FULL imported from core.time_utilities

### `tasks/task_management.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused Optional imported from typing

### `tests/ai/ai_response_validator.py`

**Count**: 2 unused import(s)

- **Line 9**: Unused Dict imported from typing
- **Line 9**: Unused Tuple imported from typing

### `tests/behavior/test_checkin_analytics_behavior.py`

**Count**: 1 unused import(s)

- **Line 15**: Unused TIMESTAMP_FULL imported from core.time_utilities

### `tests/behavior/test_scheduler_behavior.py`

**Count**: 2 unused import(s)

- **Line 14**: Unused TIME_ONLY_MINUTE imported from core.time_utilities
- **Line 14**: Unused TIMESTAMP_MINUTE imported from core.time_utilities

### `tests/behavior/test_scheduler_coverage_expansion.py`

**Count**: 2 unused import(s)

- **Line 21**: Unused TIME_ONLY_MINUTE imported from core.time_utilities
- **Line 21**: Unused TIMESTAMP_MINUTE imported from core.time_utilities

### `tests/conftest.py`

**Count**: 3 unused import(s)

- **Line 27**: Unused List imported from typing
- **Line 27**: Unused Optional imported from typing
- **Line 27**: Unused Type imported from typing

### `tests/test_utilities.py`

**Count**: 1 unused import(s)

- **Line 23**: Unused format_timestamp imported from core.time_utilities

### `tests/ui/test_account_creation_ui.py`

**Count**: 1 unused import(s)

- **Line 22**: Unused Optional imported from typing

### `tests/unit/test_cleanup.py`

**Count**: 2 unused import(s)

- **Line 18**: Unused Dict imported from typing
- **Line 18**: Unused Optional imported from typing

### `ui/generate_ui_files.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused datetime imported from datetime

### `ui/ui_app_qt.py`

**Count**: 1 unused import(s)

- **Line 31**: Unused TIMESTAMP_FULL imported from core.time_utilities

### `ui/widgets/period_row_widget.py`

**Count**: 3 unused import(s)

- **Line 3**: Unused Dict imported from typing
- **Line 3**: Unused List imported from typing
- **Line 3**: Unused Optional imported from typing

### `ui/widgets/user_profile_settings_widget.py`

**Count**: 2 unused import(s)

- **Line 3**: Unused Dict imported from typing
- **Line 3**: Unused Optional imported from typing

### `user/context_manager.py`

**Count**: 2 unused import(s)

- **Line 14**: Unused Dict imported from typing
- **Line 14**: Unused List imported from typing

## Type Hints Only

**Recommendation**: Consider using `TYPE_CHECKING` guard for these imports.

### `ai/context_builder.py`

**Count**: 1 unused import(s)

- **Line 3**: Unused Optional imported from typing

### `ai/conversation_history.py`

**Count**: 1 unused import(s)

- **Line 3**: Unused Optional imported from typing

### `communication/command_handlers/base_handler.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused Optional imported from typing

### `communication/command_handlers/task_handler.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused List imported from typing

### `communication/communication_channels/discord/account_flow_handler.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused Optional imported from typing

### `communication/core/channel_orchestrator.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused List imported from typing

### `communication/core/welcome_manager.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused Optional imported from typing

### `communication/message_processing/message_router.py`

**Count**: 1 unused import(s)

- **Line 3**: Unused Dict imported from typing

### `core/config.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused List imported from typing

### `core/error_handling.py`

**Count**: 1 unused import(s)

- **Line 14**: Unused Optional imported from typing

### `core/message_management.py`

**Count**: 3 unused import(s)

- **Line 12**: Unused List imported from typing
- **Line 12**: Unused Dict imported from typing
- **Line 12**: Unused Optional imported from typing

### `core/schedule_management.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused Optional imported from typing

### `core/schedule_utilities.py`

**Count**: 2 unused import(s)

- **Line 9**: Unused Dict imported from typing
- **Line 9**: Unused List imported from typing

### `core/scheduler.py`

**Count**: 1 unused import(s)

- **Line 12**: Unused List imported from typing

### `core/schemas.py`

**Count**: 1 unused import(s)

- **Line 12**: Unused List imported from typing

### `core/user_data_manager.py`

**Count**: 2 unused import(s)

- **Line 12**: Unused Dict imported from typing
- **Line 12**: Unused List imported from typing

### `core/user_data_validation.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused Dict imported from typing

### `tasks/task_management.py`

**Count**: 2 unused import(s)

- **Line 10**: Unused Dict imported from typing
- **Line 10**: Unused List imported from typing

### `tests/ai/ai_response_validator.py`

**Count**: 2 unused import(s)

- **Line 9**: Unused List imported from typing
- **Line 9**: Unused Optional imported from typing

### `tests/test_utilities.py`

**Count**: 3 unused import(s)

- **Line 16**: Unused Dict imported from typing
- **Line 16**: Unused Optional imported from typing
- **Line 16**: Unused List imported from typing

### `tests/unit/test_cleanup.py`

**Count**: 1 unused import(s)

- **Line 18**: Unused List imported from typing

## Conditional Imports

**Recommendation**: Review carefully - these may be for optional dependencies.

### `tests/ui/test_signal_handler_integration.py`

**Count**: 1 unused import(s)

- **Line 35**: Unused QtWidgets imported from PySide6

## Test Mocking

**Recommendation**: These imports are required for test mocking with `@patch` decorators and `patch.object()` calls.

### `tests/ai/test_ai_functionality_manual.py`

**Count**: 2 unused import(s)

- **Line 20**: Unused Mock imported from unittest.mock
- **Line 27**: Unused get_user_data imported from core.user_data_handlers

### `tests/ai/test_cache_manager.py`

**Count**: 1 unused import(s)

- **Line 7**: Unused Mock imported from unittest.mock

### `tests/behavior/test_base_handler_behavior.py`

**Count**: 2 unused import(s)

- **Line 11**: Unused patch imported from unittest.mock
- **Line 11**: Unused MagicMock imported from unittest.mock

### `tests/behavior/test_checkin_handler_behavior.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused MagicMock imported from unittest.mock

### `tests/behavior/test_communication_manager_behavior.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused MagicMock imported from unittest.mock

### `tests/behavior/test_interaction_handlers_behavior.py`

**Count**: 2 unused import(s)

- **Line 21**: Unused get_user_data imported from core.user_data_handlers
- **Line 21**: Unused save_user_data imported from core.user_data_handlers

### `tests/behavior/test_logger_coverage_expansion.py`

**Count**: 1 unused import(s)

- **Line 19**: Unused mock_open imported from unittest.mock

### `tests/behavior/test_message_router_behavior.py`

**Count**: 2 unused import(s)

- **Line 10**: Unused patch imported from unittest.mock
- **Line 10**: Unused MagicMock imported from unittest.mock

### `tests/behavior/test_notebook_handler_behavior.py`

**Count**: 2 unused import(s)

- **Line 9**: Unused patch imported from unittest.mock
- **Line 9**: Unused MagicMock imported from unittest.mock

### `tests/behavior/test_profile_handler_behavior.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused MagicMock imported from unittest.mock

### `tests/behavior/test_schedule_handler_behavior.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused MagicMock imported from unittest.mock

### `tests/behavior/test_scheduler_coverage_expansion.py`

**Count**: 2 unused import(s)

- **Line 14**: Unused get_user_categories imported from core.user_data_handlers
- **Line 14**: Unused get_user_data imported from core.user_data_handlers

### `tests/behavior/test_task_handler_behavior.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused MagicMock imported from unittest.mock

### `tests/behavior/test_user_data_flow_architecture.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused MagicMock imported from unittest.mock

### `tests/behavior/test_webhook_server_behavior.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused Mock imported from unittest.mock

### `tests/behavior/test_welcome_handler_behavior.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused MagicMock imported from unittest.mock

### `tests/core/test_file_auditor.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused Mock imported from unittest.mock

### `tests/core/test_message_management.py`

**Count**: 2 unused import(s)

- **Line 8**: Unused Mock imported from unittest.mock
- **Line 10**: Unused load_default_messages imported from core.message_management

### `tests/core/test_schedule_utilities.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused Mock imported from unittest.mock

### `tests/development_tools/test_analyze_ai_work.py`

**Count**: 2 unused import(s)

- **Line 11**: Unused patch imported from unittest.mock
- **Line 11**: Unused MagicMock imported from unittest.mock

### `tests/development_tools/test_analyze_error_handling.py`

**Count**: 2 unused import(s)

- **Line 10**: Unused patch imported from unittest.mock
- **Line 10**: Unused MagicMock imported from unittest.mock

### `tests/development_tools/test_analyze_function_registry.py`

**Count**: 2 unused import(s)

- **Line 11**: Unused patch imported from unittest.mock
- **Line 11**: Unused MagicMock imported from unittest.mock

### `tests/development_tools/test_analyze_functions.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused MagicMock imported from unittest.mock

### `tests/development_tools/test_analyze_module_dependencies.py`

**Count**: 2 unused import(s)

- **Line 11**: Unused MagicMock imported from unittest.mock
- **Line 11**: Unused mock_open imported from unittest.mock

### `tests/development_tools/test_analyze_unused_imports.py`

**Count**: 1 unused import(s)

- **Line 12**: Unused mock_open imported from unittest.mock

### `tests/development_tools/test_decision_support.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused MagicMock imported from unittest.mock

### `tests/development_tools/test_false_negative_detection.py`

**Count**: 1 unused import(s)

- **Line 15**: Unused patch imported from unittest.mock

### `tests/development_tools/test_fix_documentation.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused MagicMock imported from unittest.mock

### `tests/development_tools/test_generate_error_handling_report.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused MagicMock imported from unittest.mock

### `tests/development_tools/test_generate_function_docstrings.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused MagicMock imported from unittest.mock

### `tests/development_tools/test_generate_unused_imports_report.py`

**Count**: 2 unused import(s)

- **Line 10**: Unused patch imported from unittest.mock
- **Line 10**: Unused MagicMock imported from unittest.mock

### `tests/development_tools/test_output_storage_archiving.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused patch imported from unittest.mock

### `tests/development_tools/test_regenerate_coverage_metrics.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused MagicMock imported from unittest.mock

### `tests/integration/test_task_cleanup_real_bug_verification.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused MagicMock imported from unittest.mock

### `tests/integration/test_task_cleanup_silent_failure.py`

**Count**: 2 unused import(s)

- **Line 9**: Unused patch imported from unittest.mock
- **Line 9**: Unused MagicMock imported from unittest.mock

### `tests/integration/test_user_creation.py`

**Count**: 3 unused import(s)

- **Line 19**: Unused update_user_account imported from core.user_data_handlers
- **Line 19**: Unused update_user_schedules imported from core.user_data_handlers
- **Line 28**: Unused validate_schedule_periods__validate_time_format imported from core.user_data_validation

### `tests/test_error_handling_improvements.py`

**Count**: 4 unused import(s)

- **Line 13**: Unused patch imported from unittest.mock
- **Line 13**: Unused MagicMock imported from unittest.mock
- **Line 16**: Unused DataError imported from core.error_handling
- **Line 16**: Unused FileOperationError imported from core.error_handling

### `tests/test_utilities.py`

**Count**: 4 unused import(s)

- **Line 21**: Unused create_new_user imported from core.user_data_handlers
- **Line 21**: Unused save_user_data imported from core.user_data_handlers
- **Line 21**: Unused get_user_data imported from core.user_data_handlers
- **Line 22**: Unused ensure_user_directory imported from core.file_operations

### `tests/ui/test_account_creation_ui.py`

**Count**: 5 unused import(s)

- **Line 23**: Unused MagicMock imported from unittest.mock
- **Line 37**: Unused create_user_files imported from core.file_operations
- **Line 37**: Unused get_user_file_path imported from core.file_operations
- **Line 38**: Unused is_valid_email imported from core.user_data_validation
- **Line 38**: Unused validate_schedule_periods__validate_time_format imported from core.user_data_validation

### `tests/ui/test_account_creator_dialog_validation.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused patch imported from unittest.mock

### `tests/ui/test_category_management_dialog.py`

**Count**: 2 unused import(s)

- **Line 16**: Unused Mock imported from unittest.mock
- **Line 16**: Unused MagicMock imported from unittest.mock

### `tests/ui/test_channel_management_dialog_coverage_expansion.py`

**Count**: 5 unused import(s)

- **Line 16**: Unused get_user_data imported from core.user_data_handlers
- **Line 16**: Unused update_channel_preferences imported from core.user_data_handlers
- **Line 16**: Unused update_user_account imported from core.user_data_handlers
- **Line 17**: Unused is_valid_email imported from core.user_data_validation
- **Line 17**: Unused is_valid_phone imported from core.user_data_validation

### `tests/ui/test_dialog_behavior.py`

**Count**: 6 unused import(s)

- **Line 23**: Unused patch imported from unittest.mock
- **Line 23**: Unused Mock imported from unittest.mock
- **Line 23**: Unused MagicMock imported from unittest.mock
- **Line 32**: Unused save_user_data imported from core.user_data_handlers
- **Line 33**: Unused create_user_files imported from core.file_operations
- **Line 33**: Unused get_user_file_path imported from core.file_operations

### `tests/ui/test_dialog_coverage_expansion.py`

**Count**: 7 unused import(s)

- **Line 26**: Unused Mock imported from unittest.mock
- **Line 26**: Unused MagicMock imported from unittest.mock
- **Line 35**: Unused save_user_data imported from core.user_data_handlers
- **Line 35**: Unused get_user_data imported from core.user_data_handlers
- **Line 36**: Unused create_user_files imported from core.file_operations
- **Line 37**: Unused get_schedule_time_periods imported from core.schedule_management
- **Line 37**: Unused set_schedule_periods imported from core.schedule_management

### `tests/ui/test_message_editor_dialog.py`

**Count**: 1 unused import(s)

- **Line 16**: Unused Mock imported from unittest.mock

### `tests/ui/test_process_watcher_dialog.py`

**Count**: 1 unused import(s)

- **Line 16**: Unused Mock imported from unittest.mock

### `tests/ui/test_signal_handler_integration.py`

**Count**: 2 unused import(s)

- **Line 40**: Unused patch imported from unittest.mock
- **Line 40**: Unused MagicMock imported from unittest.mock

### `tests/ui/test_task_crud_dialog.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused Mock imported from unittest.mock

### `tests/ui/test_task_management_dialog.py`

**Count**: 1 unused import(s)

- **Line 18**: Unused MagicMock imported from unittest.mock

### `tests/ui/test_task_settings_widget.py`

**Count**: 2 unused import(s)

- **Line 18**: Unused Mock imported from unittest.mock
- **Line 18**: Unused MagicMock imported from unittest.mock

### `tests/ui/test_ui_button_verification.py`

**Count**: 2 unused import(s)

- **Line 14**: Unused Mock imported from unittest.mock
- **Line 14**: Unused patch imported from unittest.mock

### `tests/ui/test_ui_components_headless.py`

**Count**: 1 unused import(s)

- **Line 14**: Unused patch imported from unittest.mock

### `tests/ui/test_ui_widgets_coverage_expansion.py`

**Count**: 2 unused import(s)

- **Line 22**: Unused Mock imported from unittest.mock
- **Line 22**: Unused MagicMock imported from unittest.mock

### `tests/ui/test_user_analytics_dialog.py`

**Count**: 1 unused import(s)

- **Line 16**: Unused Mock imported from unittest.mock

### `tests/ui/test_user_profile_dialog_coverage_expansion.py`

**Count**: 1 unused import(s)

- **Line 13**: Unused MagicMock imported from unittest.mock

### `tests/ui/test_widget_behavior.py`

**Count**: 7 unused import(s)

- **Line 24**: Unused patch imported from unittest.mock
- **Line 24**: Unused Mock imported from unittest.mock
- **Line 24**: Unused MagicMock imported from unittest.mock
- **Line 33**: Unused save_user_data imported from core.user_data_handlers
- **Line 33**: Unused get_user_data imported from core.user_data_handlers
- **Line 34**: Unused create_user_files imported from core.file_operations
- **Line 34**: Unused get_user_file_path imported from core.file_operations

### `tests/ui/test_widget_behavior_simple.py`

**Count**: 2 unused import(s)

- **Line 15**: Unused patch imported from unittest.mock
- **Line 15**: Unused Mock imported from unittest.mock

### `tests/unit/test_admin_panel.py`

**Count**: 2 unused import(s)

- **Line 17**: Unused Mock imported from unittest.mock
- **Line 17**: Unused MagicMock imported from unittest.mock

### `tests/unit/test_ai_chatbot_helpers.py`

**Count**: 2 unused import(s)

- **Line 8**: Unused Mock imported from unittest.mock
- **Line 8**: Unused MagicMock imported from unittest.mock

### `tests/unit/test_channel_orchestrator.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused MagicMock imported from unittest.mock

### `tests/unit/test_checkin_management_dialog.py`

**Count**: 1 unused import(s)

- **Line 19**: Unused MagicMock imported from unittest.mock

### `tests/unit/test_checkin_view.py`

**Count**: 2 unused import(s)

- **Line 9**: Unused Mock imported from unittest.mock
- **Line 9**: Unused MagicMock imported from unittest.mock

### `tests/unit/test_command_parser_helpers.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused MagicMock imported from unittest.mock

### `tests/unit/test_communication_core_init.py`

**Count**: 2 unused import(s)

- **Line 12**: Unused patch imported from unittest.mock
- **Line 12**: Unused MagicMock imported from unittest.mock

### `tests/unit/test_communication_init.py`

**Count**: 2 unused import(s)

- **Line 12**: Unused patch imported from unittest.mock
- **Line 12**: Unused MagicMock imported from unittest.mock

### `tests/unit/test_email_bot_body_extraction.py`

**Count**: 1 unused import(s)

- **Line 12**: Unused MagicMock imported from unittest.mock

### `tests/unit/test_enhanced_checkin_responses.py`

**Count**: 1 unused import(s)

- **Line 12**: Unused MagicMock imported from unittest.mock

### `tests/unit/test_file_operations.py`

**Count**: 1 unused import(s)

- **Line 20**: Unused FileOperationError imported from core.error_handling

### `tests/unit/test_interaction_handlers_helpers.py`

**Count**: 2 unused import(s)

- **Line 9**: Unused Mock imported from unittest.mock
- **Line 9**: Unused MagicMock imported from unittest.mock

### `tests/unit/test_logger_unit.py`

**Count**: 2 unused import(s)

- **Line 13**: Unused Mock imported from unittest.mock
- **Line 13**: Unused mock_open imported from unittest.mock

### `tests/unit/test_message_formatter.py`

**Count**: 2 unused import(s)

- **Line 12**: Unused MagicMock imported from unittest.mock
- **Line 19**: Unused DataError imported from core.error_handling

### `tests/unit/test_prompt_manager.py`

**Count**: 2 unused import(s)

- **Line 19**: Unused Mock imported from unittest.mock
- **Line 19**: Unused MagicMock imported from unittest.mock

### `tests/unit/test_recurring_tasks.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused _create_next_recurring_task_instance imported from tasks.task_management

### `tests/unit/test_ui_management.py`

**Count**: 1 unused import(s)

- **Line 16**: Unused MagicMock imported from unittest.mock

### `tests/unit/test_user_context.py`

**Count**: 2 unused import(s)

- **Line 16**: Unused Mock imported from unittest.mock
- **Line 16**: Unused MagicMock imported from unittest.mock

### `tests/unit/test_user_data_handlers.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused MagicMock imported from unittest.mock

### `tests/unit/test_user_data_manager.py`

**Count**: 3 unused import(s)

- **Line 14**: Unused Mock imported from unittest.mock
- **Line 14**: Unused MagicMock imported from unittest.mock
- **Line 14**: Unused mock_open imported from unittest.mock

### `tests/unit/test_user_management.py`

**Count**: 3 unused import(s)

- **Line 10**: Unused patch imported from unittest.mock
- **Line 12**: Unused update_user_account imported from core.user_data_handlers
- **Line 12**: Unused update_user_context imported from core.user_data_handlers

### `tests/unit/test_user_preferences.py`

**Count**: 3 unused import(s)

- **Line 16**: Unused Mock imported from unittest.mock
- **Line 16**: Unused MagicMock imported from unittest.mock
- **Line 20**: Unused get_user_data imported from core.user_data_handlers

## Qt Testing

**Recommendation**: These Qt imports are required for UI testing and signal handling.

### `tests/ui/test_account_creation_ui.py`

**Count**: 4 unused import(s)

- **Line 26**: Unused QWidget imported from PySide6.QtWidgets
- **Line 26**: Unused QMessageBox imported from PySide6.QtWidgets
- **Line 27**: Unused Qt imported from PySide6.QtCore
- **Line 27**: Unused QTimer imported from PySide6.QtCore

### `tests/ui/test_category_management_dialog.py`

**Count**: 3 unused import(s)

- **Line 17**: Unused QMessageBox imported from PySide6.QtWidgets
- **Line 18**: Unused Qt imported from PySide6.QtCore
- **Line 19**: Unused QTest imported from PySide6.QtTest

### `tests/ui/test_dialog_behavior.py`

**Count**: 5 unused import(s)

- **Line 26**: Unused QWidget imported from PySide6.QtWidgets
- **Line 26**: Unused QMessageBox imported from PySide6.QtWidgets
- **Line 26**: Unused QDialog imported from PySide6.QtWidgets
- **Line 27**: Unused Qt imported from PySide6.QtCore
- **Line 27**: Unused QTimer imported from PySide6.QtCore

### `tests/ui/test_dialog_coverage_expansion.py`

**Count**: 4 unused import(s)

- **Line 29**: Unused QWidget imported from PySide6.QtWidgets
- **Line 30**: Unused Qt imported from PySide6.QtCore
- **Line 30**: Unused QTimer imported from PySide6.QtCore
- **Line 31**: Unused QTest imported from PySide6.QtTest

### `tests/ui/test_message_editor_dialog.py`

**Count**: 3 unused import(s)

- **Line 17**: Unused QTableWidgetItem imported from PySide6.QtWidgets
- **Line 18**: Unused Qt imported from PySide6.QtCore
- **Line 19**: Unused QTest imported from PySide6.QtTest

### `tests/ui/test_process_watcher_dialog.py`

**Count**: 3 unused import(s)

- **Line 19**: Unused Qt imported from PySide6.QtCore
- **Line 19**: Unused QTimer imported from PySide6.QtCore
- **Line 20**: Unused QTest imported from PySide6.QtTest

### `tests/ui/test_signal_handler_integration.py`

**Count**: 3 unused import(s)

- **Line 41**: Unused QLineEdit imported from PySide6.QtWidgets
- **Line 42**: Unused Qt imported from PySide6.QtCore
- **Line 43**: Unused QTest imported from PySide6.QtTest

### `tests/ui/test_task_crud_dialog.py`

**Count**: 1 unused import(s)

- **Line 14**: Unused QTableWidgetItem imported from PySide6.QtWidgets

### `tests/ui/test_task_management_dialog.py`

**Count**: 3 unused import(s)

- **Line 19**: Unused QMessageBox imported from PySide6.QtWidgets
- **Line 20**: Unused Qt imported from PySide6.QtCore
- **Line 21**: Unused QTest imported from PySide6.QtTest

### `tests/ui/test_task_settings_widget.py`

**Count**: 4 unused import(s)

- **Line 19**: Unused QWidget imported from PySide6.QtWidgets
- **Line 19**: Unused QMessageBox imported from PySide6.QtWidgets
- **Line 20**: Unused Qt imported from PySide6.QtCore
- **Line 21**: Unused QTest imported from PySide6.QtTest

### `tests/ui/test_ui_widgets_coverage_expansion.py`

**Count**: 5 unused import(s)

- **Line 26**: Unused QWidget imported from PySide6.QtWidgets
- **Line 26**: Unused QListWidgetItem imported from PySide6.QtWidgets
- **Line 26**: Unused QInputDialog imported from PySide6.QtWidgets
- **Line 27**: Unused QTimer imported from PySide6.QtCore
- **Line 28**: Unused QTest imported from PySide6.QtTest

### `tests/ui/test_user_analytics_dialog.py`

**Count**: 2 unused import(s)

- **Line 19**: Unused Qt imported from PySide6.QtCore
- **Line 20**: Unused QTest imported from PySide6.QtTest

### `tests/ui/test_user_profile_dialog_coverage_expansion.py`

**Count**: 1 unused import(s)

- **Line 18**: Unused QTest imported from PySide6.QtTest

### `tests/ui/test_widget_behavior.py`

**Count**: 5 unused import(s)

- **Line 27**: Unused QMessageBox imported from PySide6.QtWidgets
- **Line 27**: Unused QDialog imported from PySide6.QtWidgets
- **Line 28**: Unused Qt imported from PySide6.QtCore
- **Line 28**: Unused QTimer imported from PySide6.QtCore
- **Line 29**: Unused QTest imported from PySide6.QtTest

### `tests/ui/test_widget_behavior_simple.py`

**Count**: 3 unused import(s)

- **Line 16**: Unused QWidget imported from PySide6.QtWidgets
- **Line 17**: Unused Qt imported from PySide6.QtCore
- **Line 18**: Unused QTest imported from PySide6.QtTest

### `tests/unit/test_admin_panel.py`

**Count**: 2 unused import(s)

- **Line 19**: Unused Qt imported from PySide6.QtCore
- **Line 20**: Unused QTest imported from PySide6.QtTest

### `tests/unit/test_checkin_management_dialog.py`

**Count**: 3 unused import(s)

- **Line 20**: Unused QMessageBox imported from PySide6.QtWidgets
- **Line 21**: Unused Qt imported from PySide6.QtCore
- **Line 22**: Unused QTest imported from PySide6.QtTest

## Test Infrastructure

**Recommendation**: These imports are required for test infrastructure (fixtures, data creation, etc.).

### `tests/ai/test_ai_core.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused import time

### `tests/ai/test_context_includes_recent_messages.py`

**Count**: 1 unused import(s)

- **Line 1**: Unused import os

### `tests/behavior/test_checkin_expiry_semantics.py`

**Count**: 1 unused import(s)

- **Line 1**: Unused import os

### `tests/behavior/test_communication_manager_behavior.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused import time

### `tests/behavior/test_conversation_flow_manager_behavior.py`

**Count**: 3 unused import(s)

- **Line 10**: Unused import json
- **Line 11**: Unused import os
- **Line 13**: Unused datetime imported from datetime

### `tests/behavior/test_discord_checkin_retry_behavior.py`

**Count**: 1 unused import(s)

- **Line 12**: Unused datetime imported from datetime

### `tests/behavior/test_discord_task_reminder_followup.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused datetime imported from datetime

### `tests/behavior/test_headless_service_behavior.py`

**Count**: 4 unused import(s)

- **Line 10**: Unused import os
- **Line 11**: Unused import json
- **Line 14**: Unused Path imported from pathlib
- **Line 18**: Unused TestUserFactory imported from tests.test_utilities

### `tests/behavior/test_notebook_handler_behavior.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused datetime imported from datetime

### `tests/behavior/test_task_error_handling.py`

**Count**: 2 unused import(s)

- **Line 10**: Unused import json
- **Line 11**: Unused import os

### `tests/behavior/test_user_data_flow_architecture.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused import json

### `tests/behavior/test_webhook_server_behavior.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused import threading

### `tests/behavior/test_welcome_manager_behavior.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused import os

### `tests/communication/test_retry_manager.py`

**Count**: 2 unused import(s)

- **Line 6**: Unused import time
- **Line 7**: Unused import threading

### `tests/core/test_message_management.py`

**Count**: 2 unused import(s)

- **Line 7**: Unused import json
- **Line 9**: Unused datetime imported from datetime

### `tests/core/test_schedule_utilities.py`

**Count**: 1 unused import(s)

- **Line 7**: Unused time imported from datetime

### `tests/debug_file_paths.py`

**Count**: 1 unused import(s)

- **Line 1**: Unused import pytest

### `tests/development_tools/test_analysis_tool_validation.py`

**Count**: 2 unused import(s)

- **Line 12**: Unused demo_project_root imported from tests.development_tools.conftest
- **Line 12**: Unused test_config_path imported from tests.development_tools.conftest

### `tests/development_tools/test_analyze_ai_work.py`

**Count**: 3 unused import(s)

- **Line 9**: Unused import tempfile
- **Line 10**: Unused Path imported from pathlib
- **Line 13**: Unused demo_project_root imported from tests.development_tools.conftest

### `tests/development_tools/test_analyze_ascii_compliance.py`

**Count**: 2 unused import(s)

- **Line 10**: Unused demo_project_root imported from tests.development_tools.conftest
- **Line 10**: Unused test_config_path imported from tests.development_tools.conftest

### `tests/development_tools/test_analyze_documentation.py`

**Count**: 2 unused import(s)

- **Line 9**: Unused import tempfile
- **Line 13**: Unused demo_project_root imported from tests.development_tools.conftest

### `tests/development_tools/test_analyze_error_handling.py`

**Count**: 2 unused import(s)

- **Line 12**: Unused demo_project_root imported from tests.development_tools.conftest
- **Line 12**: Unused test_config_path imported from tests.development_tools.conftest

### `tests/development_tools/test_analyze_function_registry.py`

**Count**: 3 unused import(s)

- **Line 10**: Unused Path imported from pathlib
- **Line 13**: Unused demo_project_root imported from tests.development_tools.conftest
- **Line 13**: Unused test_config_path imported from tests.development_tools.conftest

### `tests/development_tools/test_analyze_functions.py`

**Count**: 3 unused import(s)

- **Line 8**: Unused Path imported from pathlib
- **Line 11**: Unused demo_project_root imported from tests.development_tools.conftest
- **Line 11**: Unused test_config_path imported from tests.development_tools.conftest

### `tests/development_tools/test_analyze_heading_numbering.py`

**Count**: 2 unused import(s)

- **Line 10**: Unused demo_project_root imported from tests.development_tools.conftest
- **Line 10**: Unused test_config_path imported from tests.development_tools.conftest

### `tests/development_tools/test_analyze_missing_addresses.py`

**Count**: 4 unused import(s)

- **Line 8**: Unused import tempfile
- **Line 9**: Unused Path imported from pathlib
- **Line 11**: Unused demo_project_root imported from tests.development_tools.conftest
- **Line 11**: Unused test_config_path imported from tests.development_tools.conftest

### `tests/development_tools/test_analyze_module_dependencies.py`

**Count**: 3 unused import(s)

- **Line 9**: Unused import tempfile
- **Line 10**: Unused Path imported from pathlib
- **Line 13**: Unused demo_project_root imported from tests.development_tools.conftest

### `tests/development_tools/test_analyze_unconverted_links.py`

**Count**: 2 unused import(s)

- **Line 10**: Unused demo_project_root imported from tests.development_tools.conftest
- **Line 10**: Unused test_config_path imported from tests.development_tools.conftest

### `tests/development_tools/test_analyze_unused_imports.py`

**Count**: 3 unused import(s)

- **Line 10**: Unused import tempfile
- **Line 11**: Unused Path imported from pathlib
- **Line 14**: Unused test_config_path imported from tests.development_tools.conftest

### `tests/development_tools/test_audit_tier_e2e_verification.py`

**Count**: 1 unused import(s)

- **Line 45**: Unused temp_project_copy imported from tests.development_tools.conftest

### `tests/development_tools/test_decision_support.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused Path imported from pathlib

### `tests/development_tools/test_documentation_sync_checker.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused Path imported from pathlib

### `tests/development_tools/test_error_scenarios.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused import shutil

### `tests/development_tools/test_exclusion_utilities.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused Path imported from pathlib

### `tests/development_tools/test_false_negative_detection.py`

**Count**: 3 unused import(s)

- **Line 14**: Unused Path imported from pathlib
- **Line 17**: Unused demo_project_root imported from tests.development_tools.conftest
- **Line 17**: Unused test_config_path imported from tests.development_tools.conftest

### `tests/development_tools/test_fix_documentation.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused Path imported from pathlib

### `tests/development_tools/test_fix_documentation_addresses.py`

**Count**: 2 unused import(s)

- **Line 8**: Unused import tempfile
- **Line 9**: Unused Path imported from pathlib

### `tests/development_tools/test_fix_documentation_ascii.py`

**Count**: 2 unused import(s)

- **Line 8**: Unused import tempfile
- **Line 9**: Unused Path imported from pathlib

### `tests/development_tools/test_fix_documentation_headings.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused temp_project_copy imported from tests.development_tools.conftest

### `tests/development_tools/test_fix_documentation_links.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused temp_project_copy imported from tests.development_tools.conftest

### `tests/development_tools/test_fix_project_cleanup.py`

**Count**: 2 unused import(s)

- **Line 9**: Unused import tempfile
- **Line 13**: Unused temp_project_copy imported from tests.development_tools.conftest

### `tests/development_tools/test_generate_consolidated_report.py`

**Count**: 1 unused import(s)

- **Line 12**: Unused temp_project_copy imported from tests.development_tools.conftest

### `tests/development_tools/test_generate_directory_tree.py`

**Count**: 2 unused import(s)

- **Line 12**: Unused demo_project_root imported from tests.development_tools.conftest
- **Line 12**: Unused test_config_path imported from tests.development_tools.conftest

### `tests/development_tools/test_generate_error_handling_report.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused Path imported from pathlib

### `tests/development_tools/test_generate_function_docstrings.py`

**Count**: 3 unused import(s)

- **Line 9**: Unused Path imported from pathlib
- **Line 12**: Unused demo_project_root imported from tests.development_tools.conftest
- **Line 12**: Unused test_config_path imported from tests.development_tools.conftest

### `tests/development_tools/test_generate_function_registry.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused Path imported from pathlib

### `tests/development_tools/test_generate_module_dependencies.py`

**Count**: 1 unused import(s)

- **Line 8**: Unused Path imported from pathlib

### `tests/development_tools/test_generate_unused_imports_report.py`

**Count**: 3 unused import(s)

- **Line 8**: Unused import json
- **Line 9**: Unused Path imported from pathlib
- **Line 12**: Unused temp_project_copy imported from tests.development_tools.conftest

### `tests/development_tools/test_legacy_reference_cleanup.py`

**Count**: 1 unused import(s)

- **Line 11**: Unused Path imported from pathlib

### `tests/development_tools/test_output_storage_archiving.py`

**Count**: 2 unused import(s)

- **Line 10**: Unused Path imported from pathlib
- **Line 13**: Unused temp_project_copy imported from tests.development_tools.conftest

### `tests/development_tools/test_path_drift_detection.py`

**Count**: 3 unused import(s)

- **Line 13**: Unused import tempfile
- **Line 14**: Unused import shutil
- **Line 15**: Unused Path imported from pathlib

### `tests/development_tools/test_path_drift_integration.py`

**Count**: 3 unused import(s)

- **Line 9**: Unused import tempfile
- **Line 10**: Unused Path imported from pathlib
- **Line 13**: Unused temp_project_copy imported from tests.development_tools.conftest

### `tests/development_tools/test_path_drift_verification_comprehensive.py`

**Count**: 2 unused import(s)

- **Line 9**: Unused Path imported from pathlib
- **Line 11**: Unused temp_project_copy imported from tests.development_tools.conftest

### `tests/development_tools/test_regenerate_coverage_metrics.py`

**Count**: 1 unused import(s)

- **Line 9**: Unused Path imported from pathlib

### `tests/development_tools/test_status_file_timing.py`

**Count**: 2 unused import(s)

- **Line 10**: Unused import time
- **Line 19**: Unused temp_project_copy imported from tests.development_tools.conftest

### `tests/integration/test_account_management.py`

**Count**: 2 unused import(s)

- **Line 11**: Unused import time
- **Line 12**: Unused import tempfile

### `tests/integration/test_task_cleanup_real.py`

**Count**: 1 unused import(s)

- **Line 12**: Unused datetime imported from datetime

### `tests/integration/test_task_cleanup_silent_failure.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused datetime imported from datetime

### `tests/integration/test_task_reminder_integration.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused import time

### `tests/integration/test_user_creation.py`

**Count**: 3 unused import(s)

- **Line 14**: Unused import json
- **Line 15**: Unused import tempfile
- **Line 17**: Unused datetime imported from datetime

### `tests/test_error_handling_improvements.py`

**Count**: 1 unused import(s)

- **Line 14**: Unused Path imported from pathlib

### `tests/test_utilities.py`

**Count**: 3 unused import(s)

- **Line 8**: Unused import tempfile
- **Line 15**: Unused Path imported from pathlib
- **Line 17**: Unused datetime imported from datetime

### `tests/ui/test_account_creation_ui.py`

**Count**: 7 unused import(s)

- **Line 21**: Unused import shutil
- **Line 24**: Unused datetime imported from datetime
- **Line 25**: Unused Path imported from pathlib
- **Line 43**: Unused CategorySelectionWidget imported from ui.widgets.category_selection_widget
- **Line 44**: Unused ChannelSelectionWidget imported from ui.widgets.channel_selection_widget
- **Line 45**: Unused TaskSettingsWidget imported from ui.widgets.task_settings_widget
- **Line 46**: Unused CheckinSettingsWidget imported from ui.widgets.checkin_settings_widget

### `tests/ui/test_dialog_behavior.py`

**Count**: 7 unused import(s)

- **Line 22**: Unused import shutil
- **Line 24**: Unused datetime imported from datetime
- **Line 24**: Unused time imported from datetime
- **Line 39**: Unused open_schedule_editor imported from ui.dialogs.schedule_editor_dialog
- **Line 40**: Unused TaskEditDialog imported from ui.dialogs.task_edit_dialog
- **Line 41**: Unused TaskCrudDialog imported from ui.dialogs.task_crud_dialog
- **Line 42**: Unused TaskCompletionDialog imported from ui.dialogs.task_completion_dialog

### `tests/ui/test_dialog_coverage_expansion.py`

**Count**: 6 unused import(s)

- **Line 25**: Unused import shutil
- **Line 27**: Unused datetime imported from datetime
- **Line 27**: Unused time imported from datetime
- **Line 28**: Unused Path imported from pathlib
- **Line 40**: Unused TaskCrudDialog imported from ui.dialogs.task_crud_dialog
- **Line 43**: Unused TestDataFactory imported from tests.test_utilities

### `tests/ui/test_dialogs.py`

**Count**: 1 unused import(s)

- **Line 15**: Unused Path imported from pathlib

### `tests/ui/test_ui_widgets_coverage_expansion.py`

**Count**: 1 unused import(s)

- **Line 23**: Unused datetime imported from datetime

### `tests/ui/test_user_analytics_dialog.py`

**Count**: 1 unused import(s)

- **Line 17**: Unused datetime imported from datetime

### `tests/ui/test_user_profile_dialog_coverage_expansion.py`

**Count**: 4 unused import(s)

- **Line 11**: Unused import os
- **Line 12**: Unused import tempfile
- **Line 14**: Unused datetime imported from datetime
- **Line 21**: Unused TestDataFactory imported from tests.test_utilities

### `tests/ui/test_widget_behavior.py`

**Count**: 5 unused import(s)

- **Line 22**: Unused import tempfile
- **Line 23**: Unused import shutil
- **Line 25**: Unused datetime imported from datetime
- **Line 25**: Unused time imported from datetime
- **Line 35**: Unused TestUserDataFactory imported from tests.test_utilities

### `tests/unit/test_file_locking.py`

**Count**: 1 unused import(s)

- **Line 14**: Unused Path imported from pathlib

### `tests/unit/test_file_operations.py`

**Count**: 1 unused import(s)

- **Line 10**: Unused Path imported from pathlib

### `tests/unit/test_logger_unit.py`

**Count**: 1 unused import(s)

- **Line 12**: Unused import json

### `tests/unit/test_prompt_manager.py`

**Count**: 3 unused import(s)

- **Line 17**: Unused import os
- **Line 18**: Unused import tempfile
- **Line 20**: Unused Path imported from pathlib

### `tests/unit/test_user_data_manager.py`

**Count**: 2 unused import(s)

- **Line 19**: Unused Path imported from pathlib
- **Line 20**: Unused datetime imported from datetime

### `tests/unit/test_user_preferences.py`

**Count**: 1 unused import(s)

- **Line 17**: Unused Path imported from pathlib

## Production Test Mocking

**Recommendation**: These imports are required in production code for test mocking. Keep them.

### `communication/command_handlers/interaction_handlers.py`

**Count**: 1 unused import(s)

- **Line 18**: Unused save_user_data imported from core.user_data_handlers

### `communication/core/channel_orchestrator.py`

**Count**: 1 unused import(s)

- **Line 19**: Unused determine_file_path imported from core.file_operations

### `communication/core/factory.py`

**Count**: 2 unused import(s)

- **Line 5**: Unused get_available_channels imported from core.config
- **Line 5**: Unused get_channel_class_mapping imported from core.config

## Ui Imports

**Recommendation**: These Qt imports are required for UI functionality. Keep them.

### `ui/widgets/checkin_settings_widget.py`

**Count**: 1 unused import(s)

- **Line 3**: Unused QComboBox imported from PySide6.QtWidgets

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
