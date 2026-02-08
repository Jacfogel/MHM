# Test Coverage Report

> **File**: `development_docs/TEST_COVERAGE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-02-08 04:20:35
> **Source**: `python development_tools/tests/generate_test_coverage.py --update-plan` - Coverage Metrics Regenerator

## Current Status

### **Overall Coverage: 72.1%**
- **Total Statements**: 29,799
- **Covered Statements**: 21,474
- **Uncovered Statements**: 8,325
- **Goal**: Expand to **80%+ coverage** for comprehensive reliability

### **Coverage Summary by Category**
- **Excellent (92% avg)**: 68 modules
- **Good (70% avg)**: 38 modules
- **Moderate (48% avg)**: 4 modules

### **Detailed Module Coverage**
- **X communication\communication_channels\discord\bot.py**: 45% (573/1265 lines)
- **X ui\widgets\checkin_settings_widget.py**: 45% (286/642 lines)
- **X ui\ui_app_qt.py**: 50% (710/1408 lines)
- **X communication\command_handlers\notebook_handler.py**: 52% (272/522 lines)
- **! communication\message_processing\conversation_flow_manager.py**: 60% (604/1009 lines)
- **! communication\core\channel_orchestrator.py**: 61% (637/1039 lines)
- **! core\checkin_analytics.py**: 61% (429/698 lines)
- **! communication\command_handlers\analytics_handler.py**: 62% (374/600 lines)
- **! core\service.py**: 62% (432/700 lines)
- **! notebook\notebook_data_manager.py**: 63% (220/349 lines)
- **! ai\chatbot.py**: 64% (536/832 lines)
- **! communication\command_handlers\interaction_handlers.py**: 65% (168/260 lines)
- **! core\scheduler.py**: 65% (657/1016 lines)
- **! communication\message_processing\interaction_manager.py**: 66% (383/581 lines)
- **! ui\dialogs\schedule_editor_dialog.py**: 66% (143/218 lines)
- **! ui\widgets\dynamic_list_container.py**: 66% (135/204 lines)
- **! core\logger.py**: 67% (488/732 lines)
- **! ui\widgets\channel_selection_widget.py**: 67% (55/82 lines)
- **! communication\communication_channels\email\bot.py**: 68% (165/241 lines)
- **! ui\dialogs\account_creator_dialog.py**: 68% (444/649 lines)
- **! core\user_data_handlers.py**: 69% (930/1344 lines)
- **! core\file_locking.py**: 70% (74/106 lines)
- **! ui\widgets\user_profile_settings_widget.py**: 70% (202/287 lines)
- **! core\user_data_manager.py**: 71% (615/869 lines)
- **! ui\dialogs\task_completion_dialog.py**: 72% (84/116 lines)
- **! ui\dialogs\task_crud_dialog.py**: 72% (155/216 lines)
- **! communication\communication_channels\discord\webhook_handler.py**: 73% (110/150 lines)
- **! core\message_management.py**: 73% (309/421 lines)
- **! ui\generate_ui_files.py**: 73% (48/66 lines)
- **! core\auto_cleanup.py**: 74% (316/428 lines)
- **! ui\widgets\dynamic_list_field.py**: 75% (91/121 lines)
- **! communication\command_handlers\profile_handler.py**: 76% (219/290 lines)
- **! core\tags.py**: 76% (164/215 lines)
- **! ui\dialogs\task_edit_dialog.py**: 76% (301/395 lines)
- **! core\backup_manager.py**: 77% (338/440 lines)
- **! core\config.py**: 77% (313/407 lines)
- **! core\file_auditor.py**: 77% (71/92 lines)
- **! core\file_operations.py**: 78% (309/397 lines)
- **! ai\conversation_history.py**: 79% (171/216 lines)
- **! core\checkin_dynamic_manager.py**: 79% (268/341 lines)
- **! core\error_handling.py**: 79% (320/405 lines)
- **! ui\dialogs\user_profile_dialog.py**: 79% (209/263 lines)
- *** communication\core\channel_monitor.py**: 80% (111/138 lines)
- *** ui\dialogs\checkin_management_dialog.py**: 80% (130/162 lines)
- *** communication\command_handlers\task_handler.py**: 81% (492/604 lines)
- *** core\schedule_management.py**: 81% (247/305 lines)
- *** tasks\task_management.py**: 81% (440/542 lines)
- *** communication\communication_channels\base\base_channel.py**: 82% (76/93 lines)
- *** communication\communication_channels\base\message_formatter.py**: 82% (107/131 lines)
- *** core\time_utilities.py**: 82% (88/107 lines)
- *** ui\dialogs\admin_panel.py**: 82% (41/50 lines)
- *** core\headless_service.py**: 83% (179/215 lines)
- *** communication\command_handlers\base_handler.py**: 84% (67/80 lines)
- *** communication\command_handlers\schedule_handler.py**: 84% (211/251 lines)
- *** communication\communication_channels\discord\welcome_handler.py**: 85% (33/39 lines)
- *** communication\message_processing\command_parser.py**: 86% (547/633 lines)
- *** core\schemas.py**: 86% (266/309 lines)
- *** notebook\notebook_data_handlers.py**: 86% (51/59 lines)
- *** ui\widgets\tag_widget.py**: 86% (185/214 lines)
- *** core\response_tracking.py**: 87% (103/118 lines)
- *** core\service_utilities.py**: 87% (138/159 lines)
- *** notebook\schemas.py**: 87% (72/83 lines)
- *** ui\widgets\period_row_widget.py**: 87% (213/245 lines)
- *** communication\communication_channels\base\rich_formatter.py**: 89% (116/131 lines)
- *** ui\dialogs\process_watcher_dialog.py**: 89% (263/297 lines)
- *** ai\context_builder.py**: 90% (239/267 lines)
- *** communication\command_handlers\account_handler.py**: 90% (164/182 lines)
- *** communication\communication_channels\discord\api_client.py**: 90% (165/184 lines)
- *** communication\communication_channels\discord\event_handler.py**: 90% (170/188 lines)
- *** communication\core\retry_manager.py**: 90% (94/104 lines)
- *** core\__init__.py**: 91% (39/43 lines)
- *** communication\communication_channels\base\command_registry.py**: 92% (119/129 lines)
- *** core\message_analytics.py**: 92% (60/65 lines)
- *** core\ui_management.py**: 92% (134/145 lines)
- *** core\user_data_validation.py**: 92% (279/302 lines)
- *** user\context_manager.py**: 92% (143/155 lines)
- *** ui\dialogs\channel_management_dialog.py**: 93% (106/114 lines)
- *** communication\communication_channels\discord\webhook_server.py**: 94% (121/129 lines)
- *** ui\widgets\task_settings_widget.py**: 94% (150/160 lines)
- *** communication\command_handlers\checkin_handler.py**: 95% (73/77 lines)
- *** communication\message_processing\message_router.py**: 95% (115/121 lines)
- *** ui\dialogs\task_management_dialog.py**: 95% (88/93 lines)
- *** ui\dialogs\user_analytics_dialog.py**: 95% (275/290 lines)
- *** ai\lm_studio_manager.py**: 96% (111/116 lines)
- *** communication\core\factory.py**: 96% (44/46 lines)
- *** ui\dialogs\category_management_dialog.py**: 97% (114/117 lines)
- *** ui\dialogs\message_editor_dialog.py**: 97% (205/211 lines)
- *** communication\communication_channels\discord\checkin_view.py**: 98% (41/42 lines)
- *** ai\cache_manager.py**: 99% (176/177 lines)
- *** ai\__init__.py**: 100% (8/8 lines)
- *** ai\prompt_manager.py**: 100% (116/116 lines)
- *** communication\__init__.py**: 100% (111/111 lines)
- *** communication\command_handlers\__init__.py**: 100% (5/5 lines)
- *** communication\command_handlers\shared_types.py**: 100% (17/17 lines)
- *** communication\communication_channels\__init__.py**: 100% (2/2 lines)
- *** communication\core\__init__.py**: 100% (11/11 lines)
- *** communication\core\welcome_manager.py**: 100% (48/48 lines)
- *** communication\message_processing\__init__.py**: 100% (3/3 lines)
- *** communication\message_processing\intent_validation.py**: 100% (9/9 lines)
- *** core\schedule_utilities.py**: 100% (63/63 lines)
- *** notebook\__init__.py**: 100% (1/1 lines)
- *** notebook\notebook_validation.py**: 100% (125/125 lines)
- *** tasks\__init__.py**: 100% (3/3 lines)
- *** ui\__init__.py**: 100% (30/30 lines)
- *** ui\dialogs\__init__.py**: 100% (9/9 lines)
- *** ui\widgets\__init__.py**: 100% (9/9 lines)
- *** ui\widgets\category_selection_widget.py**: 100% (37/37 lines)
- *** user\__init__.py**: 100% (5/5 lines)
- *** user\user_context.py**: 100% (84/84 lines)
- *** user\user_preferences.py**: 100% (49/49 lines)

## Test Markers

**Note**: This section documents test execution markers. For detailed testing guidance, see [TESTING_GUIDE.md](../tests/TESTING_GUIDE.md).

### E2E Marker

Tests marked with `@pytest.mark.e2e` are end-to-end verification tests that run real audits with actual tool execution (no mocks). These tests are:

- **Excluded by default**: The `e2e` marker is excluded from regular test runs via `pytest.ini` configuration (`-m "not e2e"`).
- **Slow**: Tier 3 E2E tests can take ~9-10 minutes due to coverage generation.
- **For verification**: Use these tests to verify actual audit tier execution before releases.

**Running E2E tests**:
```bash
# Run all E2E tests
pytest -m e2e tests/development_tools/test_audit_tier_e2e_verification.py

# Run specific E2E test
pytest -m e2e tests/development_tools/test_audit_tier_e2e_verification.py::TestAuditTierE2E::test_tier1_e2e
```

**Note**: This section may be overwritten when the coverage report is regenerated. See [TESTING_GUIDE.md](../tests/TESTING_GUIDE.md) section 6.5 for authoritative documentation.