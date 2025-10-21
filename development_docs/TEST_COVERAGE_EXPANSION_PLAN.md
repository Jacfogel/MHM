# Test Coverage Expansion Plan

> **Last Updated**: 2025-10-21

## Current Status

### **Overall Coverage: 62%**
- **Total Statements**: 21,063
- **Covered Statements**: 13,143
- **Uncovered Statements**: 7,920
- **Goal**: Expand to **80%+ coverage** for comprehensive reliability

### **Coverage Summary by Category**
- **Excellent (89% avg)**: 19 modules
- **Good (69% avg)**: 33 modules
- **Moderate (48% avg)**: 13 modules
- **Needs_Work (34% avg)**: 2 modules
- **Critical (4% avg)**: 4 modules

### **Detailed Module Coverage**
- **X ai\lm_studio_manager.py**: 0% (0/112 lines)
- **X core\headless_service.py**: 0% (0/210 lines)
- **X user\user_preferences.py**: 0% (0/48 lines)
- **X communication\command_handlers\task_handler.py**: 17% (69/415 lines)
- **X ui\ui_app_qt.py**: 33% (358/1100 lines)
- **X communication\command_handlers\profile_handler.py**: 35% (89/252 lines)
- **X communication\command_handlers\base_handler.py**: 41% (24/59 lines)
- **X communication\message_processing\interaction_manager.py**: 42% (148/350 lines)
- **X communication\message_processing\message_router.py**: 44% (52/119 lines)
- **X core\user_data_manager.py**: 44% (321/735 lines)
- **X communication\communication_channels\discord\bot.py**: 45% (407/907 lines)
- **X ui\dialogs\checkin_management_dialog.py**: 45% (55/121 lines)
- **X ui\dialogs\account_creator_dialog.py**: 48% (279/577 lines)
- **X ui\dialogs\category_management_dialog.py**: 48% (56/117 lines)
- **X user\user_context.py**: 48% (51/106 lines)
- **X ui\dialogs\task_management_dialog.py**: 53% (49/93 lines)
- **X ui\widgets\task_settings_widget.py**: 55% (102/186 lines)
- **X ai\chatbot.py**: 58% (315/545 lines)
- **X communication\command_handlers\interaction_handlers.py**: 58% (830/1439 lines)
- **! communication\core\channel_orchestrator.py**: 60% (507/851 lines)
- **! communication\message_processing\command_parser.py**: 61% (197/323 lines)
- **! core\logger.py**: 61% (371/608 lines)
- **! ui\dialogs\task_crud_dialog.py**: 61% (137/224 lines)
- **! ui\widgets\checkin_settings_widget.py**: 62% (109/176 lines)
- **! ui\widgets\dynamic_list_container.py**: 62% (126/203 lines)
- **! TOTAL**: 62% (13143/21063 lines)
- **! ai\prompt_manager.py**: 63% (71/113 lines)
- **! core\user_data_handlers.py**: 63% (436/689 lines)
- **! ui\dialogs\schedule_editor_dialog.py**: 63% (147/233 lines)
- **! ui\widgets\dynamic_list_field.py**: 63% (76/120 lines)
- **! core\scheduler.py**: 64% (563/874 lines)
- **! ui\widgets\channel_selection_widget.py**: 64% (54/85 lines)
- **! communication\message_processing\conversation_flow_manager.py**: 65% (237/364 lines)
- **! core\file_operations.py**: 66% (254/382 lines)
- **! ui\widgets\category_selection_widget.py**: 68% (28/41 lines)
- **! core\message_management.py**: 69% (259/377 lines)
- **! ui\widgets\user_profile_settings_widget.py**: 71% (204/289 lines)
- **! core\ui_management.py**: 72% (60/83 lines)
- **! core\user_management.py**: 72% (498/690 lines)
- **! core\service_utilities.py**: 73% (98/135 lines)
- **! ui\dialogs\task_completion_dialog.py**: 73% (83/114 lines)
- **! ui\generate_ui_files.py**: 73% (47/64 lines)
- **! core\config.py**: 76% (313/410 lines)
- **! core\file_auditor.py**: 77% (70/91 lines)
- **! core\service.py**: 77% (396/515 lines)
- **! tasks\task_management.py**: 77% (425/553 lines)
- **! ui\dialogs\task_edit_dialog.py**: 77% (300/392 lines)
- **! ai\conversation_history.py**: 78% (160/206 lines)
- **! communication\core\channel_monitor.py**: 78% (105/134 lines)
- **! core\error_handling.py**: 78% (273/348 lines)
- **! core\schemas.py**: 78% (218/280 lines)
- **! core\checkin_dynamic_manager.py**: 79% (157/199 lines)
- *** core\checkin_analytics.py**: 80% (314/394 lines)
- *** ui\dialogs\user_profile_dialog.py**: 80% (210/264 lines)
- *** core\schedule_management.py**: 81% (235/290 lines)
- *** core\backup_manager.py**: 82% (282/344 lines)
- *** communication\communication_channels\base\base_channel.py**: 83% (55/66 lines)
- *** ui\widgets\period_row_widget.py**: 87% (215/247 lines)
- *** ui\widgets\tag_widget.py**: 87% (187/216 lines)
- *** core\response_tracking.py**: 88% (100/114 lines)
- *** ai\context_builder.py**: 89% (235/263 lines)
- *** ui\dialogs\channel_management_dialog.py**: 89% (102/114 lines)
- *** core\auto_cleanup.py**: 90% (179/199 lines)
- *** communication\communication_channels\email\bot.py**: 92% (108/117 lines)
- *** core\user_data_validation.py**: 92% (222/242 lines)
- *** user\context_manager.py**: 92% (141/153 lines)
- *** communication\core\retry_manager.py**: 93% (81/87 lines)
- *** communication\core\factory.py**: 96% (44/46 lines)
- *** ai\cache_manager.py**: 99% (173/174 lines)
- *** communication\command_handlers\shared_types.py**: 100% (15/15 lines)
- *** core\schedule_utilities.py**: 100% (61/61 lines)
