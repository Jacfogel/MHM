# Test Coverage Report

> **File**: `development_docs/TEST_COVERAGE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-02-06 02:43:06
> **Source**: `python development_tools/tests/generate_test_coverage.py --update-plan` - Coverage Metrics Regenerator

## Current Status

### **Overall Coverage: 63.9%**
- **Total Statements**: 29,831
- **Covered Statements**: 19,054
- **Uncovered Statements**: 10,777
- **Goal**: Expand to **80%+ coverage** for comprehensive reliability

### **Coverage Summary by Category**
- **Excellent (93% avg)**: 52 modules
- **Good (70% avg)**: 35 modules
- **Moderate (49% avg)**: 12 modules
- **Needs_Work (30% avg)**: 8 modules
- **Critical (16% avg)**: 2 modules

### **Detailed Module Coverage**
- **X ui\dialogs\user_analytics_dialog.py**: 15% (44/290 lines)
- **X ui\dialogs\task_crud_dialog.py**: 18% (38/216 lines)
- **X communication\communication_channels\discord\webhook_server.py**: 20% (26/129 lines)
- **X ui\generate_ui_files.py**: 21% (14/66 lines)
- **X ai\context_builder.py**: 26% (69/267 lines)
- **X communication\command_handlers\interaction_handlers.py**: 33% (87/260 lines)
- **X communication\command_handlers\base_handler.py**: 34% (27/80 lines)
- **X communication\communication_channels\email\bot.py**: 35% (84/241 lines)
- **X ui\ui_app_qt.py**: 36% (509/1408 lines)
- **X communication\message_processing\interaction_manager.py**: 38% (223/583 lines)
- **X communication\command_handlers\analytics_handler.py**: 40% (240/600 lines)
- **X ui\widgets\tag_widget.py**: 43% (91/214 lines)
- **X ui\widgets\checkin_settings_widget.py**: 44% (291/663 lines)
- **X communication\communication_channels\discord\bot.py**: 45% (571/1265 lines)
- **X communication\message_processing\conversation_flow_manager.py**: 46% (461/1009 lines)
- **X communication\communication_channels\discord\welcome_handler.py**: 49% (19/39 lines)
- **X ui\dialogs\channel_management_dialog.py**: 50% (57/114 lines)
- **X communication\command_handlers\notebook_handler.py**: 51% (265/522 lines)
- **X communication\communication_channels\discord\webhook_handler.py**: 51% (77/150 lines)
- **X communication\command_handlers\checkin_handler.py**: 55% (42/77 lines)
- **X communication\core\channel_orchestrator.py**: 58% (603/1039 lines)
- **X ui\widgets\dynamic_list_container.py**: 58% (118/204 lines)
- **! ai\chatbot.py**: 61% (509/837 lines)
- **! core\checkin_analytics.py**: 61% (425/697 lines)
- **! ui\dialogs\message_editor_dialog.py**: 61% (129/211 lines)
- **! communication\command_handlers\profile_handler.py**: 62% (180/290 lines)
- **! core\scheduler.py**: 62% (629/1016 lines)
- **! core\service.py**: 62% (431/699 lines)
- **! notebook\notebook_data_manager.py**: 62% (216/349 lines)
- **! ui\dialogs\process_watcher_dialog.py**: 62% (184/297 lines)
- **! communication\command_handlers\task_handler.py**: 64% (392/610 lines)
- **! ui\dialogs\schedule_editor_dialog.py**: 64% (152/239 lines)
- **! ui\widgets\period_row_widget.py**: 64% (157/245 lines)
- **! core\logger.py**: 65% (475/727 lines)
- **! tasks\task_management.py**: 65% (353/542 lines)
- **! ui\widgets\channel_selection_widget.py**: 67% (55/82 lines)
- **! ui\dialogs\account_creator_dialog.py**: 68% (442/649 lines)
- **! core\user_data_handlers.py**: 69% (983/1417 lines)
- **! core\file_locking.py**: 70% (73/105 lines)
- **! core\user_data_manager.py**: 70% (611/867 lines)
- **! ui\widgets\user_profile_settings_widget.py**: 70% (202/287 lines)
- **! core\auto_cleanup.py**: 72% (309/427 lines)
- **! core\message_management.py**: 72% (303/420 lines)
- **! ui\dialogs\task_completion_dialog.py**: 72% (84/116 lines)
- **! core\backup_manager.py**: 73% (319/438 lines)
- **! core\file_operations.py**: 74% (292/396 lines)
- **! ui\widgets\dynamic_list_field.py**: 74% (89/121 lines)
- **! core\config.py**: 76% (306/405 lines)
- **! core\tags.py**: 76% (163/214 lines)
- **! ui\dialogs\task_edit_dialog.py**: 76% (301/395 lines)
- **! core\file_auditor.py**: 77% (69/90 lines)
- **! core\checkin_dynamic_manager.py**: 78% (266/339 lines)
- **! core\error_handling.py**: 78% (302/388 lines)
- **! ai\conversation_history.py**: 79% (171/216 lines)
- **! communication\message_processing\command_parser.py**: 79% (503/635 lines)
- **! core\time_utilities.py**: 79% (84/106 lines)
- **! ui\dialogs\user_profile_dialog.py**: 79% (209/263 lines)
- *** communication\core\channel_monitor.py**: 80% (111/138 lines)
- *** communication\core\factory.py**: 80% (37/46 lines)
- *** ui\dialogs\checkin_management_dialog.py**: 80% (130/162 lines)
- *** core\schedule_management.py**: 81% (245/304 lines)
- *** communication\communication_channels\base\base_channel.py**: 82% (76/93 lines)
- *** communication\communication_channels\base\message_formatter.py**: 82% (107/131 lines)
- *** ui\dialogs\admin_panel.py**: 82% (41/50 lines)
- *** core\headless_service.py**: 83% (177/213 lines)
- *** communication\command_handlers\account_handler.py**: 84% (153/182 lines)
- *** communication\command_handlers\schedule_handler.py**: 84% (210/251 lines)
- *** core\schemas.py**: 86% (265/308 lines)
- *** notebook\notebook_data_handlers.py**: 86% (51/59 lines)
- *** core\response_tracking.py**: 87% (102/117 lines)
- *** core\service_utilities.py**: 87% (135/156 lines)
- *** notebook\schemas.py**: 87% (72/83 lines)
- *** communication\communication_channels\base\rich_formatter.py**: 89% (116/131 lines)
- *** communication\communication_channels\discord\api_client.py**: 90% (165/184 lines)
- *** communication\communication_channels\discord\event_handler.py**: 90% (170/188 lines)
- *** communication\core\retry_manager.py**: 90% (94/104 lines)
- *** core\__init__.py**: 90% (38/42 lines)
- *** communication\communication_channels\base\command_registry.py**: 92% (119/129 lines)
- *** core\message_analytics.py**: 92% (59/64 lines)
- *** core\user_data_validation.py**: 92% (278/301 lines)
- *** user\context_manager.py**: 92% (143/155 lines)
- *** communication\message_processing\message_router.py**: 93% (113/121 lines)
- *** ui\dialogs\task_management_dialog.py**: 95% (88/93 lines)
- *** ui\widgets\task_settings_widget.py**: 95% (173/183 lines)
- *** ai\lm_studio_manager.py**: 96% (111/116 lines)
- *** ui\dialogs\category_management_dialog.py**: 97% (114/117 lines)
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
- *** core\schedule_utilities.py**: 100% (62/62 lines)
- *** core\ui_management.py**: 100% (85/85 lines)
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