# Test Coverage Report

> **File**: `development_docs/TEST_COVERAGE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-03-04 19:35:16
> **Source**: `python development_tools/tests/generate_test_coverage_report.py` - Test Coverage Report Generator

## Current Status

### **Overall Coverage: 76.4%**
- **Total Statements**: 30,170
- **Covered Statements**: 23,054
- **Uncovered Statements**: 7,116
- **Coverage Scope**: Main project domains only (`ai`, `communication`, `core`, `notebook`, `tasks`, `ui`, `user`); `development_tools/` coverage is tracked separately.
- **Goal**: Expand to **80%+ coverage** for comprehensive reliability

### **Coverage by Domain**
- **ai**: 79.5% (1399/1760 lines, 361 missing)
- **communication**: 76.3% (7236/9484 lines, 2248 missing)
- **core**: 76.7% (8364/10902 lines, 2538 missing)
- **notebook**: 95.6% (580/607 lines, 27 missing)
- **tasks**: 89.0% (403/453 lines, 50 missing)
- **ui**: 71.8% (4788/6668 lines, 1880 missing)
- **user**: 95.9% (284/296 lines, 12 missing)

### **Coverage Summary by Category**
- **Excellent (93% avg)**: 86 modules
- **Good (70% avg)**: 25 modules
- **Moderate (53% avg)**: 3 modules

### **Detailed Module Coverage**
- **X communication\communication_channels\discord\bot.py**: 51% (650/1276 lines)
- **X ui\ui_app_qt.py**: 53% (742/1408 lines)
- **X ui\widgets\checkin_settings_widget.py**: 54% (354/653 lines)
- **! core\checkin_analytics.py**: 62% (443/718 lines)
- **! core\scheduler.py**: 64% (662/1028 lines)
- **! communication\message_processing\conversation_flow_manager.py**: 65% (668/1032 lines)
- **! ui\dialogs\schedule_editor_dialog.py**: 65% (142/217 lines)
- **! ui\widgets\dynamic_list_container.py**: 66% (134/203 lines)
- **! ai\chatbot.py**: 67% (585/867 lines)
- **! core\backup_manager.py**: 67% (510/760 lines)
- **! ui\widgets\channel_selection_widget.py**: 67% (55/82 lines)
- **! communication\command_handlers\notebook_handler.py**: 68% (354/519 lines)
- **! communication\message_processing\interaction_manager.py**: 68% (406/600 lines)
- **! core\logger.py**: 68% (503/743 lines)
- **! ui\dialogs\account_creator_dialog.py**: 68% (437/642 lines)
- **! communication\core\channel_orchestrator.py**: 69% (722/1054 lines)
- **! ui\widgets\user_profile_settings_widget.py**: 70% (201/286 lines)
- **! core\user_data_manager.py**: 71% (617/867 lines)
- **! ui\dialogs\task_completion_dialog.py**: 72% (83/115 lines)
- **! ui\dialogs\task_crud_dialog.py**: 72% (154/215 lines)
- **! core\message_management.py**: 75% (308/413 lines)
- **! core\user_data_handlers.py**: 75% (998/1339 lines)
- **! ui\widgets\dynamic_list_field.py**: 75% (90/120 lines)
- **! core\service.py**: 76% (548/719 lines)
- **! ui\dialogs\task_edit_dialog.py**: 76% (300/394 lines)
- **! core\error_handling.py**: 77% (300/389 lines)
- **! ai\conversation_history.py**: 79% (168/213 lines)
- **! communication\command_handlers\task_handler.py**: 79% (495/625 lines)
- *** communication\core\channel_monitor.py**: 80% (112/140 lines)
- *** ui\dialogs\checkin_management_dialog.py**: 80% (126/157 lines)
- *** ui\dialogs\user_profile_dialog.py**: 80% (208/261 lines)
- *** core\checkin_dynamic_manager.py**: 81% (323/400 lines)
- *** core\file_operations.py**: 81% (319/395 lines)
- *** communication\communication_channels\base\message_formatter.py**: 82% (95/116 lines)
- *** communication\communication_channels\discord\welcome_handler.py**: 82% (32/39 lines)
- *** core\time_utilities.py**: 82% (88/107 lines)
- *** ui\dialogs\admin_panel.py**: 82% (40/49 lines)
- *** communication\communication_channels\base\base_channel.py**: 83% (55/66 lines)
- *** communication\message_processing\command_parser.py**: 83% (535/646 lines)
- *** core\headless_service.py**: 83% (176/211 lines)
- *** core\schedule_management.py**: 83% (246/297 lines)
- *** communication\command_handlers\schedule_handler.py**: 84% (212/253 lines)
- *** core\config.py**: 86% (348/406 lines)
- *** core\schemas.py**: 86% (265/308 lines)
- *** notebook\notebook_data_handlers.py**: 86% (50/58 lines)
- *** ui\widgets\tag_widget.py**: 86% (184/213 lines)
- *** communication\command_handlers\account_handler.py**: 87% (162/186 lines)
- *** core\response_tracking.py**: 87% (102/117 lines)
- *** communication\command_handlers\interaction_handlers.py**: 88% (228/258 lines)
- *** tasks\task_data_handlers.py**: 88% (46/52 lines)
- *** ui\widgets\period_row_widget.py**: 88% (210/240 lines)
- *** communication\communication_channels\base\rich_formatter.py**: 89% (102/114 lines)
- *** communication\communication_channels\discord\api_client.py**: 89% (164/184 lines)
- *** notebook\notebook_schemas.py**: 89% (71/80 lines)
- *** tasks\task_data_manager.py**: 89% (311/351 lines)
- *** ui\dialogs\process_watcher_dialog.py**: 89% (262/296 lines)
- *** ai\context_builder.py**: 90% (243/271 lines)
- *** communication\communication_channels\discord\event_handler.py**: 90% (168/186 lines)
- *** communication\core\retry_manager.py**: 90% (92/102 lines)
- *** core\__init__.py**: 90% (38/42 lines)
- *** tasks\task_validation.py**: 90% (35/39 lines)
- *** communication\command_handlers\analytics_handler.py**: 92% (568/619 lines)
- *** core\message_analytics.py**: 92% (59/64 lines)
- *** core\service_utilities.py**: 92% (142/154 lines)
- *** core\ui_management.py**: 92% (133/144 lines)
- *** user\context_manager.py**: 92% (140/152 lines)
- *** communication\communication_channels\base\command_registry.py**: 93% (109/117 lines)
- *** core\user_data_validation.py**: 93% (287/310 lines)
- *** ui\dialogs\channel_management_dialog.py**: 93% (103/111 lines)
- *** communication\communication_channels\discord\webhook_server.py**: 94% (118/126 lines)
- *** core\file_locking.py**: 94% (99/105 lines)
- *** ui\generate_ui_files.py**: 94% (58/62 lines)
- *** ui\widgets\task_settings_widget.py**: 94% (150/160 lines)
- *** communication\command_handlers\base_handler.py**: 95% (53/56 lines)
- *** communication\command_handlers\checkin_handler.py**: 95% (71/75 lines)
- *** communication\communication_channels\discord\webhook_handler.py**: 95% (141/149 lines)
- *** communication\message_processing\message_router.py**: 95% (112/118 lines)
- *** ui\dialogs\task_management_dialog.py**: 95% (88/93 lines)
- *** ui\dialogs\user_analytics_dialog.py**: 95% (271/286 lines)
- *** ai\lm_studio_manager.py**: 96% (109/114 lines)
- *** core\auto_cleanup.py**: 96% (425/441 lines)
- *** communication\command_handlers\profile_handler.py**: 97% (287/295 lines)
- *** communication\communication_channels\email\bot.py**: 97% (235/242 lines)
- *** notebook\notebook_data_manager.py**: 97% (336/346 lines)
- *** ui\dialogs\category_management_dialog.py**: 97% (114/117 lines)
- *** ui\dialogs\message_editor_dialog.py**: 97% (200/206 lines)
- *** communication\communication_channels\discord\checkin_view.py**: 98% (40/41 lines)
- *** ai\cache_manager.py**: 99% (173/174 lines)
- *** ai\__init__.py**: 100% (7/7 lines)
- *** ai\prompt_manager.py**: 100% (114/114 lines)
- *** communication\__init__.py**: 100% (110/110 lines)
- *** communication\command_handlers\__init__.py**: 100% (4/4 lines)
- *** communication\command_handlers\shared_types.py**: 100% (15/15 lines)
- *** communication\communication_channels\__init__.py**: 100% (1/1 lines)
- *** communication\core\__init__.py**: 100% (10/10 lines)
- *** communication\core\factory.py**: 100% (55/55 lines)
- *** communication\core\welcome_manager.py**: 100% (47/47 lines)
- *** communication\message_processing\__init__.py**: 100% (2/2 lines)
- *** communication\message_processing\intent_validation.py**: 100% (6/6 lines)
- *** core\file_auditor.py**: 100% (93/93 lines)
- *** core\schedule_utilities.py**: 100% (63/63 lines)
- *** core\tags.py**: 100% (214/214 lines)
- *** core\user_item_storage.py**: 100% (55/55 lines)
- *** notebook\__init__.py**: 100% (0/0 lines)
- *** notebook\notebook_validation.py**: 100% (123/123 lines)
- *** tasks\__init__.py**: 100% (4/4 lines)
- *** tasks\task_schemas.py**: 100% (7/7 lines)
- *** ui\__init__.py**: 100% (29/29 lines)
- *** ui\dialogs\__init__.py**: 100% (8/8 lines)
- *** ui\widgets\__init__.py**: 100% (8/8 lines)
- *** ui\widgets\category_selection_widget.py**: 100% (37/37 lines)
- *** user\__init__.py**: 100% (12/12 lines)
- *** user\user_context.py**: 100% (84/84 lines)
- *** user\user_preferences.py**: 100% (48/48 lines)

## Test Markers

**Note**: Marker counts are generated from test decorators in `tests/test_*.py` files.

- **Total discovered test nodes**: 4775
- **Marker usage counts**:
  - `unit`: 2405
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
  - `no_parallel`: 100
  - `slow`: 85
  - `checkins`: 63
  - `parametrize`: 55
  - `messages`: 47
  - `smoke`: 47
  - `skipif`: 2
  - `filterwarnings`: 1

