# Test Coverage Report

> **File**: `development_docs/TEST_COVERAGE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-03-19 09:26:38
> **Source**: `python development_tools/tests/generate_test_coverage_report.py` - Test Coverage Report Generator

## Current Status

### **Overall Coverage: 11.4%**
- **Total Statements**: 27,608
- **Covered Statements**: 3,158
- **Uncovered Statements**: 24,450
- **Coverage Scope**: Main project domains only (`core`, `communication`, `ui`, `tasks`, `user`, `ai`, `notebook`); `development_tools/` coverage is tracked separately.
- **Goal**: Expand to **80%+ coverage** for comprehensive reliability

### **Coverage by Domain**
- **core**: 16.8% (1830/10914 lines, 9084 missing)
- **communication**: 12.7% (877/6896 lines, 6019 missing)
- **ui**: 0.0% (0/6684 lines, 6684 missing)
- **tasks**: 0.0% (0/453 lines, 453 missing)
- **user**: 23.0% (68/296 lines, 228 missing)
- **ai**: 21.8% (383/1758 lines, 1375 missing)
- **notebook**: 0.0% (0/607 lines, 607 missing)

### **Coverage Summary by Category**
- **Excellent (96% avg)**: 8 modules
- **Moderate (47% avg)**: 6 modules
- **Needs_Work (27% avg)**: 19 modules
- **Critical (5% avg)**: 78 modules

### **Detailed Module Coverage**
- **X communication\command_handlers\account_handler.py**: 0% (0/186 lines)
- **X communication\command_handlers\notebook_handler.py**: 0% (0/508 lines)
- **X communication\core\welcome_manager.py**: 0% (0/47 lines)
- **X communication\message_processing\message_router.py**: 0% (0/118 lines)
- **X core\file_locking.py**: 0% (0/105 lines)
- **X core\message_analytics.py**: 0% (0/64 lines)
- **X core\tags.py**: 0% (0/209 lines)
- **X core\user_item_storage.py**: 0% (0/55 lines)
- **X notebook\notebook_data_handlers.py**: 0% (0/58 lines)
- **X notebook\notebook_data_manager.py**: 0% (0/346 lines)
- **X notebook\notebook_schemas.py**: 0% (0/80 lines)
- **X notebook\notebook_validation.py**: 0% (0/123 lines)
- **X tasks\__init__.py**: 0% (0/4 lines)
- **X tasks\task_data_handlers.py**: 0% (0/52 lines)
- **X tasks\task_data_manager.py**: 0% (0/351 lines)
- **X tasks\task_schemas.py**: 0% (0/7 lines)
- **X tasks\task_validation.py**: 0% (0/39 lines)
- **X ui\__init__.py**: 0% (0/29 lines)
- **X ui\dialogs\__init__.py**: 0% (0/8 lines)
- **X ui\dialogs\account_creator_dialog.py**: 0% (0/635 lines)
- **X ui\dialogs\admin_panel.py**: 0% (0/49 lines)
- **X ui\dialogs\category_management_dialog.py**: 0% (0/117 lines)
- **X ui\dialogs\channel_management_dialog.py**: 0% (0/111 lines)
- **X ui\dialogs\checkin_management_dialog.py**: 0% (0/157 lines)
- **X ui\dialogs\dialog_helpers.py**: 0% (0/18 lines)
- **X ui\dialogs\message_editor_dialog.py**: 0% (0/206 lines)
- **X ui\dialogs\process_watcher_dialog.py**: 0% (0/296 lines)
- **X ui\dialogs\schedule_editor_dialog.py**: 0% (0/217 lines)
- **X ui\dialogs\task_completion_dialog.py**: 0% (0/115 lines)
- **X ui\dialogs\task_crud_dialog.py**: 0% (0/215 lines)
- **X ui\dialogs\task_edit_dialog.py**: 0% (0/400 lines)
- **X ui\dialogs\task_management_dialog.py**: 0% (0/93 lines)
- **X ui\dialogs\user_analytics_dialog.py**: 0% (0/286 lines)
- **X ui\dialogs\user_profile_dialog.py**: 0% (0/257 lines)
- **X ui\generate_ui_files.py**: 0% (0/62 lines)
- **X ui\ui_app_qt.py**: 0% (0/1408 lines)
- **X ui\widgets\__init__.py**: 0% (0/8 lines)
- **X ui\widgets\category_selection_widget.py**: 0% (0/37 lines)
- **X ui\widgets\channel_selection_widget.py**: 0% (0/82 lines)
- **X ui\widgets\checkin_settings_widget.py**: 0% (0/656 lines)
- **X ui\widgets\dynamic_list_container.py**: 0% (0/203 lines)
- **X ui\widgets\dynamic_list_field.py**: 0% (0/120 lines)
- **X ui\widgets\period_row_widget.py**: 0% (0/240 lines)
- **X ui\widgets\tag_widget.py**: 0% (0/213 lines)
- **X ui\widgets\task_settings_widget.py**: 0% (0/160 lines)
- **X ui\widgets\user_profile_settings_widget.py**: 0% (0/286 lines)
- **X user\user_preferences.py**: 0% (0/48 lines)
- **X core\user_data_read.py**: 7% (21/302 lines)
- **X communication\command_handlers\profile_handler.py**: 10% (30/295 lines)
- **X communication\message_processing\command_parser.py**: 10% (65/646 lines)
- **X core\user_data_validation.py**: 10% (32/310 lines)
- **X communication\command_handlers\analytics_handler.py**: 11% (66/619 lines)
- **X communication\command_handlers\task_handler.py**: 11% (67/625 lines)
- **X core\message_management.py**: 11% (46/413 lines)
- **X core\scheduler.py**: 11% (112/1028 lines)
- **X core\user_data_write.py**: 11% (38/352 lines)
- **X ai\chatbot.py**: 12% (108/865 lines)
- **X communication\command_handlers\schedule_handler.py**: 12% (30/253 lines)
- **X communication\message_processing\interaction_manager.py**: 12% (74/600 lines)
- **X core\checkin_analytics.py**: 12% (86/718 lines)
- **X core\file_operations.py**: 12% (47/395 lines)
- **X core\user_data_manager.py**: 12% (103/860 lines)
- **X communication\command_handlers\interaction_handlers.py**: 13% (33/258 lines)
- **X communication\core\channel_orchestrator.py**: 13% (137/1054 lines)
- **X core\user_lookup.py**: 13% (19/150 lines)
- **X core\user_management.py**: 13% (10/75 lines)
- **X core\headless_service.py**: 14% (29/211 lines)
- **X communication\__init__.py**: 15% (16/110 lines)
- **X communication\message_processing\conversation_flow_manager.py**: 15% (159/1032 lines)
- **X core\backup_manager.py**: 15% (116/749 lines)
- **X core\user_data_schedule_defaults.py**: 15% (14/92 lines)
- **X core\auto_cleanup.py**: 16% (72/441 lines)
- **X core\schedule_management.py**: 16% (47/297 lines)
- **X core\schedule_utilities.py**: 17% (11/63 lines)
- **X user\__init__.py**: 17% (2/12 lines)
- **X core\checkin_dynamic_manager.py**: 18% (71/400 lines)
- **X core\service.py**: 18% (127/715 lines)
- **X core\ui_management.py**: 19% (28/144 lines)
- **X core\logger.py**: 20% (151/743 lines)
- **X communication\core\__init__.py**: 22% (5/23 lines)
- **X ai\lm_studio_manager.py**: 23% (26/114 lines)
- **X communication\command_handlers\base_handler.py**: 23% (13/56 lines)
- **X communication\core\channel_monitor.py**: 23% (32/140 lines)
- **X ai\context_builder.py**: 24% (66/271 lines)
- **X core\response_tracking.py**: 24% (28/117 lines)
- **X core\user_data_registry.py**: 24% (66/272 lines)
- **X user\context_manager.py**: 24% (37/152 lines)
- **X core\user_data_updates.py**: 25% (24/97 lines)
- **X ai\conversation_history.py**: 26% (56/213 lines)
- **X core\service_utilities.py**: 27% (42/154 lines)
- **X core\error_handling.py**: 28% (107/389 lines)
- **X core\config.py**: 32% (131/405 lines)
- **X communication\command_handlers\checkin_handler.py**: 33% (25/75 lines)
- **X ai\cache_manager.py**: 34% (59/174 lines)
- **X core\schemas.py**: 35% (109/308 lines)
- **X user\user_context.py**: 35% (29/84 lines)
- **X communication\core\retry_manager.py**: 37% (38/102 lines)
- **X communication\core\factory.py**: 40% (22/55 lines)
- **X core\file_auditor.py**: 42% (39/93 lines)
- **X core\time_utilities.py**: 44% (47/107 lines)
- **X core\user_data_presets.py**: 45% (14/31 lines)
- **X ai\prompt_manager.py**: 54% (61/114 lines)
- **X communication\communication_channels\base\base_channel.py**: 58% (38/66 lines)
- *** communication\message_processing\intent_validation.py**: 83% (5/6 lines)
- *** core\__init__.py**: 86% (43/50 lines)
- *** ai\__init__.py**: 100% (7/7 lines)
- *** communication\command_handlers\__init__.py**: 100% (4/4 lines)
- *** communication\command_handlers\shared_types.py**: 100% (15/15 lines)
- *** communication\communication_channels\__init__.py**: 100% (1/1 lines)
- *** communication\message_processing\__init__.py**: 100% (2/2 lines)
- *** notebook\__init__.py**: 100% (0/0 lines)

## Test Markers

**Note**: Marker counts are generated from test decorators in `tests/test_*.py` files.

- **Total discovered test nodes**: 4774
- **Marker usage counts**:
  - `unit`: 2415
  - `behavior`: 1806
  - `communication`: 1045
  - `ui`: 579
  - `file_io`: 437
  - `critical`: 406
  - `regression`: 327
  - `user_management`: 246
  - `ai`: 198
  - `scheduler`: 159
  - `integration`: 138
  - `analytics`: 130
  - `notebook`: 122
  - `tasks`: 108
  - `no_parallel`: 103
  - `slow`: 85
  - `checkins`: 63
  - `parametrize`: 55
  - `messages`: 47
  - `smoke`: 47
  - `skipif`: 2
  - `filterwarnings`: 1

