# Test Coverage Report

> **File**: `development_docs/TEST_COVERAGE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-04-04 03:00:51
> **Source**: `python development_tools/tests/generate_test_coverage_report.py` - Test Coverage Report Generator

## Current Status

### **Overall Coverage: 76.1%**
- **Total Statements**: 30,313
- **Covered Statements**: 23,063
- **Uncovered Statements**: 7,250
- **Coverage Scope**: Main project domains only (`ai`, `communication`, `core`, `notebook`, `tasks`, `ui`, `user`); `development_tools/` coverage is tracked separately.
- **Goal**: Expand to **80%+ coverage** for comprehensive reliability

### **Coverage by Domain**
- **ai**: 79.3% (1406/1774 lines, 368 missing)
- **communication**: 76.7% (7379/9621 lines, 2242 missing)
- **core**: 77.0% (8296/10773 lines, 2477 missing)
- **notebook**: 95.6% (587/614 lines, 27 missing)
- **tasks**: 89.1% (409/459 lines, 50 missing)
- **ui**: 69.4% (4698/6772 lines, 2074 missing)
- **user**: 96.0% (288/300 lines, 12 missing)

### **Coverage Summary by Category**
- **Excellent (93% avg)**: 91 modules
- **Good (71% avg)**: 27 modules
- **Moderate (52% avg)**: 4 modules
- **Needs_Work (26% avg)**: 1 modules

### **Detailed Module Coverage**
- **X ui\dialogs\schedule_editor_dialog.py**: 26% (57/219 lines)
- **X ui\widgets\checkin_settings_widget.py**: 45% (297/658 lines)
- **X communication\communication_channels\discord\bot.py**: 51% (652/1276 lines)
- **X ui\ui_app_qt.py**: 52% (750/1449 lines)
- **X communication\core\__init__.py**: 58% (14/24 lines)
- **! core\checkin_analytics.py**: 62% (444/719 lines)
- **! core\scheduler.py**: 64% (660/1028 lines)
- **! communication\message_processing\conversation_flow_manager.py**: 65% (669/1033 lines)
- **! core\user_data_schedule_defaults.py**: 65% (60/93 lines)
- **! core\auto_cleanup.py**: 66% (293/443 lines)
- **! ui\widgets\dynamic_list_container.py**: 66% (136/205 lines)
- **! ai\chatbot.py**: 67% (578/867 lines)
- **! ui\widgets\channel_selection_widget.py**: 67% (56/83 lines)
- **! communication\message_processing\interaction_manager.py**: 68% (409/603 lines)
- **! core\logger.py**: 68% (508/748 lines)
- **! core\time_utilities.py**: 68% (73/108 lines)
- **! ui\dialogs\account_creator_dialog.py**: 68% (436/637 lines)
- **! communication\core\channel_orchestrator.py**: 69% (725/1057 lines)
- **! core\user_data_manager.py**: 70% (606/862 lines)
- **! ui\widgets\user_profile_settings_widget.py**: 70% (203/288 lines)
- **! communication\command_handlers\notebook_handler.py**: 71% (369/520 lines)
- **! ui\dialogs\task_crud_dialog.py**: 72% (156/217 lines)
- **! ui\dialogs\task_completion_dialog.py**: 73% (85/117 lines)
- **! core\user_lookup.py**: 74% (111/151 lines)
- **! ui\widgets\dynamic_list_field.py**: 75% (92/122 lines)
- **! core\service.py**: 76% (546/717 lines)
- **! core\user_data_write.py**: 76% (268/353 lines)
- **! ui\dialogs\task_edit_dialog.py**: 76% (304/402 lines)
- **! core\user_data_read.py**: 77% (232/303 lines)
- **! core\error_handling.py**: 78% (318/408 lines)
- **! core\message_management.py**: 78% (316/406 lines)
- **! ai\conversation_history.py**: 79% (171/216 lines)
- *** communication\command_handlers\task_handler.py**: 80% (504/632 lines)
- *** communication\core\channel_monitor.py**: 80% (113/141 lines)
- *** ui\dialogs\checkin_management_dialog.py**: 80% (128/159 lines)
- *** ui\dialogs\user_profile_dialog.py**: 80% (206/259 lines)
- *** core\checkin_dynamic_manager.py**: 81% (325/402 lines)
- *** core\file_operations.py**: 81% (320/396 lines)
- *** communication\communication_channels\discord\welcome_handler.py**: 82% (33/40 lines)
- *** core\backup_manager.py**: 82% (423/518 lines)
- *** ui\dialogs\admin_panel.py**: 82% (42/51 lines)
- *** communication\message_processing\command_parser.py**: 83% (538/649 lines)
- *** core\schedule_management.py**: 83% (247/298 lines)
- *** ui\widgets\period_row_widget.py**: 83% (200/242 lines)
- *** communication\command_handlers\schedule_handler.py**: 84% (213/254 lines)
- *** communication\communication_channels\base\message_formatter.py**: 84% (107/128 lines)
- *** core\headless_service.py**: 84% (175/209 lines)
- *** core\user_data_presets.py**: 84% (27/32 lines)
- *** core\user_data_registry.py**: 85% (231/273 lines)
- *** core\config.py**: 86% (351/407 lines)
- *** core\schemas.py**: 86% (266/309 lines)
- *** notebook\notebook_data_handlers.py**: 86% (51/59 lines)
- *** communication\command_handlers\account_handler.py**: 87% (164/188 lines)
- *** communication\communication_channels\base\base_channel.py**: 87% (76/87 lines)
- *** core\response_tracking.py**: 87% (103/118 lines)
- *** ui\widgets\tag_widget.py**: 87% (186/215 lines)
- *** communication\command_handlers\interaction_handlers.py**: 88% (230/260 lines)
- *** communication\communication_channels\discord\api_client.py**: 89% (167/187 lines)
- *** notebook\notebook_schemas.py**: 89% (74/83 lines)
- *** tasks\task_data_handlers.py**: 89% (47/53 lines)
- *** tasks\task_data_manager.py**: 89% (312/352 lines)
- *** ui\dialogs\process_watcher_dialog.py**: 89% (264/298 lines)
- *** ai\context_builder.py**: 90% (246/274 lines)
- *** communication\communication_channels\base\rich_formatter.py**: 90% (114/126 lines)
- *** communication\communication_channels\discord\event_handler.py**: 90% (171/189 lines)
- *** communication\core\retry_manager.py**: 90% (94/104 lines)
- *** core\ui_management.py**: 90% (130/145 lines)
- *** tasks\task_validation.py**: 90% (36/40 lines)
- *** core\user_data_updates.py**: 91% (89/98 lines)
- *** communication\command_handlers\analytics_handler.py**: 92% (569/620 lines)
- *** core\__init__.py**: 92% (47/51 lines)
- *** core\message_analytics.py**: 92% (60/65 lines)
- *** core\service_utilities.py**: 92% (152/165 lines)
- *** user\context_manager.py**: 92% (142/154 lines)
- *** communication\communication_channels\discord\webhook_handler.py**: 93% (140/150 lines)
- *** core\user_data_validation.py**: 93% (288/311 lines)
- *** core\user_management.py**: 93% (71/76 lines)
- *** ui\dialogs\channel_management_dialog.py**: 93% (104/112 lines)
- *** communication\communication_channels\base\command_registry.py**: 94% (119/127 lines)
- *** communication\communication_channels\discord\webhook_server.py**: 94% (121/129 lines)
- *** ui\generate_ui_files.py**: 94% (60/64 lines)
- *** ui\widgets\task_settings_widget.py**: 94% (151/161 lines)
- *** communication\command_handlers\checkin_handler.py**: 95% (72/76 lines)
- *** communication\message_processing\message_router.py**: 95% (115/121 lines)
- *** ui\dialogs\task_management_dialog.py**: 95% (89/94 lines)
- *** ui\dialogs\user_analytics_dialog.py**: 95% (273/288 lines)
- *** ai\lm_studio_manager.py**: 96% (111/116 lines)
- *** communication\command_handlers\base_handler.py**: 96% (67/70 lines)
- *** core\file_locking.py**: 96% (102/106 lines)
- *** communication\command_handlers\profile_handler.py**: 97% (288/296 lines)
- *** communication\communication_channels\email\bot.py**: 97% (236/243 lines)
- *** core\launch_env.py**: 97% (29/30 lines)
- *** notebook\notebook_data_manager.py**: 97% (337/347 lines)
- *** ui\dialogs\category_management_dialog.py**: 97% (115/118 lines)
- *** ui\dialogs\message_editor_dialog.py**: 97% (203/209 lines)
- *** communication\communication_channels\discord\checkin_view.py**: 98% (41/42 lines)
- *** ai\cache_manager.py**: 99% (176/177 lines)
- *** ai\__init__.py**: 100% (8/8 lines)
- *** ai\prompt_manager.py**: 100% (116/116 lines)
- *** communication\__init__.py**: 100% (111/111 lines)
- *** communication\command_handlers\__init__.py**: 100% (5/5 lines)
- *** communication\command_handlers\shared_types.py**: 100% (17/17 lines)
- *** communication\communication_channels\__init__.py**: 100% (2/2 lines)
- *** communication\core\factory.py**: 100% (56/56 lines)
- *** communication\core\welcome_manager.py**: 100% (48/48 lines)
- *** communication\message_processing\__init__.py**: 100% (3/3 lines)
- *** communication\message_processing\intent_validation.py**: 100% (7/7 lines)
- *** core\file_auditor.py**: 100% (95/95 lines)
- *** core\schedule_utilities.py**: 100% (64/64 lines)
- *** core\tags.py**: 100% (210/210 lines)
- *** core\user_item_storage.py**: 100% (56/56 lines)
- *** notebook\__init__.py**: 100% (1/1 lines)
- *** notebook\notebook_validation.py**: 100% (124/124 lines)
- *** tasks\__init__.py**: 100% (5/5 lines)
- *** tasks\task_schemas.py**: 100% (9/9 lines)
- *** ui\__init__.py**: 100% (30/30 lines)
- *** ui\dialogs\__init__.py**: 100% (9/9 lines)
- *** ui\dialogs\dialog_helpers.py**: 100% (19/19 lines)
- *** ui\widgets\__init__.py**: 100% (9/9 lines)
- *** ui\widgets\category_selection_widget.py**: 100% (38/38 lines)
- *** user\__init__.py**: 100% (13/13 lines)
- *** user\user_context.py**: 100% (84/84 lines)
- *** user\user_preferences.py**: 100% (49/49 lines)

## Test Markers

**Note**: Marker counts are generated from test decorators in `tests/test_*.py` files.

- **Total discovered test nodes**: 4937
- **Marker usage counts**:
  - `unit`: 2568
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

