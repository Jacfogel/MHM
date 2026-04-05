# Test Coverage Report

> **File**: `development_docs/TEST_COVERAGE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-04-05 03:22:24
> **Source**: `python development_tools/tests/generate_test_coverage_report.py` - Test Coverage Report Generator

## Current Status

### **Overall Coverage: 76.0%**
- **Total Statements**: 29,967
- **Covered Statements**: 22,773
- **Uncovered Statements**: 7,194
- **Coverage Scope**: Main project domains only (`ai`, `communication`, `core`, `notebook`, `tasks`, `ui`, `user`); `development_tools/` coverage is tracked separately.
- **Goal**: Expand to **80%+ coverage** for comprehensive reliability

### **Coverage by Domain**
- **ai**: 78.7% (1383/1758 lines, 375 missing)
- **communication**: 76.5% (7253/9487 lines, 2234 missing)
- **core**: 77.1% (8209/10643 lines, 2434 missing)
- **notebook**: 95.6% (580/607 lines, 27 missing)
- **tasks**: 89.0% (403/453 lines, 50 missing)
- **ui**: 69.3% (4661/6723 lines, 2062 missing)
- **user**: 95.9% (284/296 lines, 12 missing)

### **Coverage Summary by Category**
- **Excellent (92% avg)**: 93 modules
- **Good (71% avg)**: 27 modules
- **Moderate (51% avg)**: 4 modules
- **Needs_Work (25% avg)**: 1 modules

### **Detailed Module Coverage**
- **X ui\dialogs\schedule_editor_dialog.py**: 25% (55/217 lines)
- **X ui\widgets\checkin_settings_widget.py**: 45% (295/656 lines)
- **X communication\communication_channels\discord\bot.py**: 51% (651/1275 lines)
- **X ui\ui_app_qt.py**: 52% (759/1446 lines)
- **X communication\core\__init__.py**: 57% (13/23 lines)
- **! core\checkin_analytics.py**: 62% (443/718 lines)
- **! core\user_data_schedule_defaults.py**: 64% (59/92 lines)
- **! communication\message_processing\conversation_flow_manager.py**: 65% (669/1033 lines)
- **! core\scheduler.py**: 65% (663/1025 lines)
- **! ai\chatbot.py**: 66% (569/865 lines)
- **! core\auto_cleanup.py**: 66% (289/441 lines)
- **! core\time_utilities.py**: 66% (71/108 lines)
- **! ui\widgets\dynamic_list_container.py**: 66% (134/203 lines)
- **! ui\widgets\channel_selection_widget.py**: 67% (55/82 lines)
- **! communication\message_processing\interaction_manager.py**: 68% (407/601 lines)
- **! core\logger.py**: 68% (506/743 lines)
- **! ui\dialogs\account_creator_dialog.py**: 68% (434/635 lines)
- **! communication\core\channel_orchestrator.py**: 69% (722/1054 lines)
- **! ui\widgets\user_profile_settings_widget.py**: 70% (201/286 lines)
- **! core\user_data_manager.py**: 71% (613/862 lines)
- **! communication\command_handlers\notebook_handler.py**: 72% (373/516 lines)
- **! ui\dialogs\task_completion_dialog.py**: 72% (83/115 lines)
- **! ui\dialogs\task_crud_dialog.py**: 72% (154/215 lines)
- **! core\user_lookup.py**: 73% (110/150 lines)
- **! ui\widgets\dynamic_list_field.py**: 75% (91/121 lines)
- **! core\service.py**: 76% (544/715 lines)
- **! core\user_data_write.py**: 76% (267/352 lines)
- **! ui\dialogs\task_edit_dialog.py**: 76% (302/400 lines)
- **! core\user_data_read.py**: 77% (232/303 lines)
- **! core\message_management.py**: 78% (315/403 lines)
- **! ai\conversation_history.py**: 79% (168/213 lines)
- **! ui\dialogs\user_profile_dialog.py**: 79% (204/257 lines)
- *** communication\command_handlers\task_handler.py**: 80% (503/631 lines)
- *** communication\core\channel_monitor.py**: 80% (112/140 lines)
- *** ui\dialogs\checkin_management_dialog.py**: 80% (126/157 lines)
- *** core\checkin_dynamic_manager.py**: 81% (323/400 lines)
- *** core\error_handling.py**: 81% (260/321 lines)
- *** core\file_operations.py**: 81% (320/395 lines)
- *** communication\communication_channels\base\message_formatter.py**: 82% (95/116 lines)
- *** communication\communication_channels\discord\welcome_handler.py**: 82% (32/39 lines)
- *** core\backup_manager.py**: 82% (421/516 lines)
- *** ui\dialogs\admin_panel.py**: 82% (40/49 lines)
- *** ui\widgets\period_row_widget.py**: 82% (198/240 lines)
- *** communication\communication_channels\base\base_channel.py**: 83% (55/66 lines)
- *** communication\message_processing\command_parser.py**: 83% (535/646 lines)
- *** core\headless_service.py**: 83% (172/206 lines)
- *** communication\command_handlers\schedule_handler.py**: 84% (212/253 lines)
- *** core\schedule_management.py**: 84% (248/297 lines)
- *** core\user_data_presets.py**: 84% (26/31 lines)
- *** core\user_data_registry.py**: 84% (228/270 lines)
- *** core\config.py**: 86% (349/405 lines)
- *** core\schemas.py**: 86% (265/308 lines)
- *** notebook\notebook_data_handlers.py**: 86% (50/58 lines)
- *** ui\widgets\tag_widget.py**: 86% (184/213 lines)
- *** communication\command_handlers\account_handler.py**: 87% (159/183 lines)
- *** core\response_tracking.py**: 87% (102/117 lines)
- *** communication\command_handlers\interaction_handlers.py**: 88% (228/258 lines)
- *** tasks\task_data_handlers.py**: 88% (46/52 lines)
- *** communication\communication_channels\base\rich_formatter.py**: 89% (102/114 lines)
- *** communication\communication_channels\discord\api_client.py**: 89% (164/184 lines)
- *** notebook\notebook_schemas.py**: 89% (71/80 lines)
- *** tasks\task_data_manager.py**: 89% (311/351 lines)
- *** ui\dialogs\process_watcher_dialog.py**: 89% (262/296 lines)
- *** ai\context_builder.py**: 90% (243/271 lines)
- *** communication\communication_channels\discord\event_handler.py**: 90% (168/186 lines)
- *** communication\core\retry_manager.py**: 90% (92/102 lines)
- *** core\ui_management.py**: 90% (129/144 lines)
- *** core\user_data_updates.py**: 90% (80/89 lines)
- *** tasks\task_validation.py**: 90% (35/39 lines)
- *** core\network_probe.py**: 91% (20/22 lines)
- *** communication\command_handlers\analytics_handler.py**: 92% (568/619 lines)
- *** core\__init__.py**: 92% (47/51 lines)
- *** core\message_analytics.py**: 92% (59/64 lines)
- *** core\service_utilities.py**: 92% (130/142 lines)
- *** user\context_manager.py**: 92% (140/152 lines)
- *** communication\command_handlers\base_handler.py**: 93% (42/45 lines)
- *** communication\communication_channels\base\command_registry.py**: 93% (109/117 lines)
- *** communication\communication_channels\discord\webhook_handler.py**: 93% (139/149 lines)
- *** core\user_data_validation.py**: 93% (291/314 lines)
- *** core\user_management.py**: 93% (70/75 lines)
- *** ui\dialogs\channel_management_dialog.py**: 93% (103/111 lines)
- *** communication\communication_channels\discord\webhook_server.py**: 94% (118/126 lines)
- *** core\file_locking.py**: 94% (99/105 lines)
- *** ui\generate_ui_files.py**: 94% (58/62 lines)
- *** ui\widgets\task_settings_widget.py**: 94% (150/160 lines)
- *** communication\command_handlers\checkin_handler.py**: 95% (71/75 lines)
- *** communication\message_processing\message_router.py**: 95% (112/118 lines)
- *** ui\dialogs\task_management_dialog.py**: 95% (88/93 lines)
- *** ui\dialogs\user_analytics_dialog.py**: 95% (271/286 lines)
- *** ai\lm_studio_manager.py**: 96% (109/114 lines)
- *** communication\command_handlers\profile_handler.py**: 97% (287/295 lines)
- *** communication\communication_channels\email\bot.py**: 97% (235/242 lines)
- *** core\launch_env.py**: 97% (28/29 lines)
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
- *** communication\core\factory.py**: 100% (55/55 lines)
- *** communication\core\welcome_manager.py**: 100% (47/47 lines)
- *** communication\message_processing\__init__.py**: 100% (2/2 lines)
- *** communication\message_processing\intent_validation.py**: 100% (6/6 lines)
- *** core\file_auditor.py**: 100% (93/93 lines)
- *** core\schedule_utilities.py**: 100% (64/64 lines)
- *** core\tags.py**: 100% (209/209 lines)
- *** core\time_format_constants.py**: 100% (9/9 lines)
- *** core\user_item_storage.py**: 100% (55/55 lines)
- *** notebook\__init__.py**: 100% (0/0 lines)
- *** notebook\notebook_validation.py**: 100% (123/123 lines)
- *** tasks\__init__.py**: 100% (4/4 lines)
- *** tasks\task_schemas.py**: 100% (7/7 lines)
- *** ui\__init__.py**: 100% (29/29 lines)
- *** ui\dialogs\__init__.py**: 100% (8/8 lines)
- *** ui\dialogs\dialog_helpers.py**: 100% (18/18 lines)
- *** ui\widgets\__init__.py**: 100% (8/8 lines)
- *** ui\widgets\category_selection_widget.py**: 100% (37/37 lines)
- *** user\__init__.py**: 100% (12/12 lines)
- *** user\user_context.py**: 100% (84/84 lines)
- *** user\user_preferences.py**: 100% (48/48 lines)

## Test Markers

**Note**: Marker counts are generated from test decorators in `tests/test_*.py` files.

- **Total discovered test nodes**: 4941
- **Marker usage counts**:
  - `unit`: 2572
  - `behavior`: 1807
  - `communication`: 1047
  - `ui`: 583
  - `file_io`: 437
  - `critical`: 406
  - `regression`: 327
  - `user_management`: 255
  - `ai`: 198
  - `scheduler`: 159
  - `integration`: 147
  - `analytics`: 130
  - `notebook`: 123
  - `tasks`: 108
  - `no_parallel`: 104
  - `slow`: 85
  - `checkins`: 63
  - `parametrize`: 56
  - `messages`: 52
  - `smoke`: 47
  - `fast`: 2
  - `skipif`: 2
  - `e2e`: 1
  - `filterwarnings`: 1

