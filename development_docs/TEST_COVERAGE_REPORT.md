# Test Coverage Report

> **File**: `development_docs/TEST_COVERAGE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-02-06 00:11:15
> **Source**: `python development_tools/tests/generate_test_coverage.py --update-plan` - Coverage Metrics Regenerator

## Current Status

### **Overall Coverage: 59.4%**
- **Total Statements**: 29,578
- **Covered Statements**: 17,572
- **Uncovered Statements**: 12,006
- **Goal**: Expand to **80%+ coverage** for comprehensive reliability

### **Coverage Summary by Category**
- **Excellent (92% avg)**: 42 modules
- **Good (69% avg)**: 33 modules
- **Moderate (50% avg)**: 20 modules
- **Needs_Work (32% avg)**: 10 modules
- **Critical (16% avg)**: 4 modules

### **Detailed Module Coverage**
- **X core\headless_service.py**: 14% (29/211 lines)
- **X ui\dialogs\task_edit_dialog.py**: 14% (57/394 lines)
- **X communication\communication_channels\discord\checkin_view.py**: 17% (7/41 lines)
- **X communication\communication_channels\discord\webhook_server.py**: 18% (23/126 lines)
- **X ui\dialogs\schedule_editor_dialog.py**: 22% (53/238 lines)
- **X core\checkin_analytics.py**: 28% (198/697 lines)
- **X ui\dialogs\user_profile_dialog.py**: 28% (74/261 lines)
- **X ai\conversation_history.py**: 30% (63/213 lines)
- **X communication\communication_channels\discord\api_client.py**: 31% (56/181 lines)
- **X communication\core\channel_orchestrator.py**: 32% (332/1036 lines)
- **X core\schedule_utilities.py**: 35% (22/62 lines)
- **X communication\communication_channels\discord\bot.py**: 37% (469/1264 lines)
- **X communication\communication_channels\discord\event_handler.py**: 39% (72/185 lines)
- **X ui\dialogs\checkin_management_dialog.py**: 39% (63/160 lines)
- **X communication\command_handlers\base_handler.py**: 41% (23/56 lines)
- **X communication\message_processing\interaction_manager.py**: 42% (244/580 lines)
- **X ui\widgets\checkin_settings_widget.py**: 42% (279/662 lines)
- **X communication\communication_channels\discord\welcome_handler.py**: 46% (18/39 lines)
- **X core\scheduler.py**: 46% (468/1010 lines)
- **X core\message_analytics.py**: 47% (30/64 lines)
- **X ui\ui_app_qt.py**: 49% (692/1404 lines)
- **X ui\widgets\channel_selection_widget.py**: 49% (40/82 lines)
- **X ui\widgets\user_profile_settings_widget.py**: 49% (139/286 lines)
- **X communication\command_handlers\notebook_handler.py**: 51% (266/520 lines)
- **X communication\communication_channels\base\command_registry.py**: 51% (60/117 lines)
- **X communication\communication_channels\discord\webhook_handler.py**: 51% (76/149 lines)
- **X ai\chatbot.py**: 52% (433/835 lines)
- **X communication\message_processing\conversation_flow_manager.py**: 53% (536/1005 lines)
- **X communication\command_handlers\interaction_handlers.py**: 54% (139/258 lines)
- **X communication\communication_channels\base\message_formatter.py**: 54% (63/116 lines)
- **X communication\communication_channels\base\rich_formatter.py**: 55% (64/116 lines)
- **X core\service.py**: 55% (381/697 lines)
- **X ui\dialogs\message_editor_dialog.py**: 55% (115/208 lines)
- **X ai\cache_manager.py**: 58% (101/174 lines)
- **! core\checkin_dynamic_manager.py**: 60% (203/339 lines)
- **! core\logger.py**: 60% (427/711 lines)
- **! ui\dialogs\channel_management_dialog.py**: 60% (68/114 lines)
- **! ai\prompt_manager.py**: 62% (70/112 lines)
- **! communication\command_handlers\analytics_handler.py**: 62% (373/599 lines)
- **! notebook\notebook_data_manager.py**: 62% (215/348 lines)
- **! ui\widgets\dynamic_list_container.py**: 62% (126/203 lines)
- **! core\file_locking.py**: 63% (66/105 lines)
- **! tasks\task_management.py**: 63% (340/540 lines)
- **! ui\widgets\dynamic_list_field.py**: 63% (76/120 lines)
- **! core\user_data_manager.py**: 64% (552/867 lines)
- **! core\response_tracking.py**: 66% (77/117 lines)
- **! core\message_management.py**: 67% (283/420 lines)
- **! communication\communication_channels\email\bot.py**: 68% (164/240 lines)
- **! ui\dialogs\account_creator_dialog.py**: 68% (443/648 lines)
- **! core\config.py**: 69% (281/405 lines)
- **! core\user_data_handlers.py**: 69% (981/1417 lines)
- **! core\backup_manager.py**: 72% (314/438 lines)
- **! core\service_utilities.py**: 72% (112/156 lines)
- **! ui\dialogs\task_crud_dialog.py**: 72% (154/215 lines)
- **! core\schedule_management.py**: 73% (221/304 lines)
- **! ui\dialogs\user_analytics_dialog.py**: 73% (211/288 lines)
- **! ui\generate_ui_files.py**: 73% (46/63 lines)
- **! communication\command_handlers\profile_handler.py**: 74% (213/289 lines)
- **! core\auto_cleanup.py**: 74% (303/412 lines)
- **! core\file_auditor.py**: 74% (67/90 lines)
- **! ui\dialogs\task_completion_dialog.py**: 74% (85/115 lines)
- **! core\tags.py**: 76% (163/214 lines)
- **! ui\dialogs\process_watcher_dialog.py**: 76% (225/296 lines)
- **! communication\command_handlers\task_handler.py**: 77% (471/608 lines)
- **! core\error_handling.py**: 77% (298/386 lines)
- **! core\file_operations.py**: 77% (303/396 lines)
- **! core\time_utilities.py**: 78% (83/106 lines)
- *** communication\core\channel_monitor.py**: 80% (110/137 lines)
- *** communication\core\retry_manager.py**: 81% (83/102 lines)
- *** communication\message_processing\command_parser.py**: 81% (509/632 lines)
- *** user\user_context.py**: 81% (68/84 lines)
- *** ui\dialogs\admin_panel.py**: 82% (40/49 lines)
- *** ui\widgets\period_row_widget.py**: 82% (200/244 lines)
- *** communication\communication_channels\base\base_channel.py**: 83% (55/66 lines)
- *** communication\command_handlers\account_handler.py**: 84% (151/180 lines)
- *** communication\command_handlers\schedule_handler.py**: 84% (209/250 lines)
- *** core\user_data_validation.py**: 84% (252/301 lines)
- *** core\schemas.py**: 85% (263/308 lines)
- *** notebook\notebook_data_handlers.py**: 86% (50/58 lines)
- *** notebook\schemas.py**: 86% (69/80 lines)
- *** ui\widgets\tag_widget.py**: 86% (184/213 lines)
- *** ui\widgets\task_settings_widget.py**: 87% (160/183 lines)
- *** ai\context_builder.py**: 89% (236/264 lines)
- *** core\__init__.py**: 90% (38/42 lines)
- *** ui\dialogs\category_management_dialog.py**: 90% (105/117 lines)
- *** notebook\notebook_validation.py**: 91% (113/124 lines)
- *** ai\lm_studio_manager.py**: 92% (105/114 lines)
- *** user\context_manager.py**: 92% (141/153 lines)
- *** communication\command_handlers\checkin_handler.py**: 95% (72/76 lines)
- *** communication\message_processing\message_router.py**: 95% (112/118 lines)
- *** ui\dialogs\task_management_dialog.py**: 95% (88/93 lines)
- *** communication\core\factory.py**: 96% (43/45 lines)
- *** ai\__init__.py**: 100% (7/7 lines)
- *** communication\__init__.py**: 100% (110/110 lines)
- *** communication\command_handlers\__init__.py**: 100% (4/4 lines)
- *** communication\command_handlers\shared_types.py**: 100% (15/15 lines)
- *** communication\communication_channels\__init__.py**: 100% (1/1 lines)
- *** communication\core\__init__.py**: 100% (10/10 lines)
- *** communication\core\welcome_manager.py**: 100% (47/47 lines)
- *** communication\message_processing\__init__.py**: 100% (2/2 lines)
- *** core\ui_management.py**: 100% (85/85 lines)
- *** notebook\__init__.py**: 100% (0/0 lines)
- *** tasks\__init__.py**: 100% (2/2 lines)
- *** ui\__init__.py**: 100% (29/29 lines)
- *** ui\dialogs\__init__.py**: 100% (8/8 lines)
- *** ui\widgets\__init__.py**: 100% (8/8 lines)
- *** ui\widgets\category_selection_widget.py**: 100% (37/37 lines)
- *** user\__init__.py**: 100% (4/4 lines)
- *** user\user_preferences.py**: 100% (48/48 lines)

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