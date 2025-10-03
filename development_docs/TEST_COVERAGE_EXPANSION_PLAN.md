# Test Coverage Expansion Plan

## 📊 **Current Status**

### **Overall Coverage: 0%**
- **Total Statements**: 0
- **Covered Statements**: 0
- **Uncovered Statements**: 0
- **Goal**: Expand to **80%+ coverage** for comprehensive reliability

### **Coverage Summary by Category**

### **Detailed Module Coverage**

## Overview
- Last updated: 2025-10-01
- Latest suite run: `python run_tests.py` (1519 passed, 1 skipped)
- Coverage snapshot: 65% (11,687 / 17,855 statements) from `python ai_development_tools/regenerate_coverage_metrics.py --update-plan`
- Scope: application modules under `ai/`, `communication/`, `core/`, `tasks/`, `ui/`, and `user/`

## Coverage Snapshot by Category
| Category         | Module Count | Average Coverage |
|------------------|--------------|------------------|
| Excellent >=80%  | 21           | 89.3%            |
| Good 60-79%      | 25           | 70.4%            |
| Moderate 40-59%  | 14           | 51.3%            |
| Needs work 20-39%| 2            | 30.2%            |
| Critical <20%    | 2            | 5.6%             |

*Percentages derived from `ai_development_tools/coverage.json` generated on 2025-10-01.*

## Coverage Targets and Trend
- Goal: raise overall coverage to 80%+ while keeping the full suite stable.
- Thresholds: lift every module above 50% before working on polish items.
- Audit signal: documentation coverage sits at 92.51%; code coverage is the outstanding gap.

## Modules Requiring Immediate Attention (<50% coverage)
| Module | Coverage | Covered / Total | Recommended Action |
|--------|----------|-----------------|--------------------|
| ui/generate_ui_files.py | 72.0% | 47 / 65 | ✅ **COMPLETED** - Comprehensive test suite added with 14 tests covering all functionality |
| ui/dialogs/task_crud_dialog.py | 11.2% | 25 / 224 | Expand dialog behavior tests for CRUD flows and validation |
| ui/ui_app_qt.py | 27.6% | 276 / 999 | Build deterministic harness for app bootstrap, signal wiring |
| core/schedule_utilities.py | 32.8% | 20 / 61 | Cover edge cases for helper schedulers and formatting utilities |
| communication/message_processing/interaction_manager.py | 43.5% | 131 / 301 | Exercise multi-channel routing and fallback logic |
| communication/communication_channels/discord/bot.py | 46.9% | 371 / 791 | Simulate lifecycle and reconnection scenarios |
| communication/core/channel_monitor.py | 48.0% | 47 / 98 | Cover restart monitoring and health check logic |
| ui/dialogs/account_creator_dialog.py | 48.1% | 245 / 509 | Add account creation error-path coverage |
| ai/cache_manager.py | 48.5% | 80 / 165 | Extend cache eviction and expiry tests |
| ui/dialogs/checkin_management_dialog.py | 49.0% | 50 / 102 | Expand tests for legacy-enabled fields and validation |

## Tier 2 Backlog (50-59% coverage)
| Module | Coverage | Covered / Total | Focus |
|--------|----------|-----------------|-------|
| user/user_context.py | 50.0% | 53 / 106 | Add preference round-trip checks |
| ui/widgets/task_settings_widget.py | 50.6% | 86 / 170 | Cover combinations of reminder and tag widgets |
| ui/dialogs/task_management_dialog.py | 51.1% | 46 / 90 | Exercise bulk actions and validation warnings |
| ui/dialogs/category_management_dialog.py | 51.5% | 50 / 97 | Cover category CRUD flows and error paths |
| communication/command_handlers/interaction_handlers.py | 55.5% | 758 / 1365 | Add profile/task scheduling scenarios before refactor |
| ui/widgets/channel_selection_widget.py | 57.0% | 49 / 86 | Test channel toggles with mixed configurations |
| ui/widgets/checkin_settings_widget.py | 59.1% | 97 / 164 | Cover legacy enabled_fields transitions |
| ai/chatbot.py | 59.6% | 304 / 510 | Add story-based tests for prompt assembly fallbacks |

## Tier 3 Backlog (60-69% coverage)
| Module | Coverage | Covered / Total | Focus |
|--------|----------|-----------------|-------|
| user/user_preferences.py | 60.0% | 30 / 50 | Extend persistence and migration tests |
| communication/core/channel_orchestrator.py | 61.1% | 463 / 758 | Cover retry loops and health checks |
| ai/prompt_manager.py | 61.1% | 66 / 108 | Exercise all prompt template branches |
| core/file_auditor.py | 62.7% | 52 / 83 | Cover watch start/stop edge cases |
| core/user_data_handlers.py | 64.9% | 366 / 564 | Add data corruption and recovery scenarios |
| core/user_data_manager.py | 65.6% | 359 / 547 | Extend index rebuild and migration coverage |
| core/logger.py | 66.1% | 363 / 549 | Cover rotation failure and recovery paths |
| communication/message_processing/conversation_flow_manager.py | 66.3% | 230 / 347 | Add structured flow branching tests |
| core/scheduler.py | 66.3% | 546 / 823 | Ensure recovery and catch-up logic is exercised |
| ui/widgets/category_selection_widget.py | 68.3% | 28 / 41 | Cover mixed selection workflows |
| communication/core/retry_manager.py | 69.3% | 61 / 88 | Add retry exhaustion and success scenarios |
| core/file_operations.py | 69.7% | 214 / 307 | Extend failure and permission handling tests |

## High-Coverage Reference Modules (>=90%)
| Module | Coverage | Covered / Total |
|--------|----------|-----------------|
| communication/command_handlers/shared_types.py | 100.0% | 15 / 15 |
| communication/core/factory.py | 95.7% | 44 / 46 |
| ui/dialogs/task_completion_dialog.py | 94.8% | 55 / 58 |
| communication/communication_channels/base/base_channel.py | 94.5% | 52 / 55 |
| ai/context_builder.py | 94.5% | 223 / 236 |
| ui/dialogs/channel_management_dialog.py | 94.2% | 98 / 104 |

These modules provide good patterns for fixture setup, deterministic behavior tests, and UI harnessing.

## Critical Testing Challenges & Prevention Strategies

### **Test Isolation Issues (CRITICAL)**
- **Tests affecting each other**: Use proper fixtures and cleanup
- **Tests affecting real system data**: Enforce test data directory isolation
- **Creating real Windows tasks**: Mock external system calls
- **Test logging isolation**: Use separate log files for tests
- **UI windows hanging**: Use headless mode and proper cleanup

### **Prevention Strategies**
1. **Data Isolation**: All tests must use `tests/data/` directory only
2. **Environment Isolation**: Use `monkeypatch.setenv()` for env vars
3. **Mock External Systems**: Never create real Windows tasks or system resources
4. **UI Testing**: Use headless mode, mock Qt applications
5. **Logging Isolation**: Use test-specific log files and cleanup

### **Critical Testing Methodology (CRITICAL)**
**Always investigate the actual implementation first** - Read the source code before writing tests
- **Understand the real behavior** - The actual implementation may import functions dynamically and have specific data structures
- **Test what actually exists** - Instead of assuming functions exist, verify what's actually available in the codebase
- **Start with basic functionality** - Begin with simple tests before attempting complex interaction tests
- **Verify imports and dependencies** - Check what modules and functions are actually imported and used

### **UI Component Testing Requirements**
- **Button functionality**: Test all button clicks and responses
- **Input validation**: Test all input fields and validation rules
- **Dialog workflows**: Test complete dialog open/close/save cycles
- **Widget interactions**: Test all widget combinations and states
- **Error handling**: Test UI error states and recovery

## Priority Actions
1. ✅ **COMPLETED**: `ui/generate_ui_files.py` - Added comprehensive test suite (14 tests, 72% coverage)
2. ✅ **COMPLETED**: `ui/dialogs/task_crud_dialog.py` - Added comprehensive test suite (19 tests, improved coverage)
3. **NEXT TARGET**: `ui/ui_app_qt.py` - Critical UI bootstrapping module, needs comprehensive testing
4. **NEXT TARGET**: `communication/command_handlers/profile_handler.py` and `analytics_handler.py` - High-complexity handlers need smoke tests
5. **NEXT TARGET**: Communication pathways - `interaction_manager.handle_message`, `channel_monitor`, Discord bot lifecycle
6. For modules already above 90%, keep regression tests lightweight and stable; use them as patterns when refactoring lower-coverage counterparts.
7. **CRITICAL**: Implement comprehensive UI component testing with proper isolation to prevent hanging and system interference.

## Tracking
- Regenerate metrics after major test additions with `python ai_development_tools/regenerate_coverage_metrics.py --update-plan > coverage.txt` to capture the printed summary without rewriting this file accidentally.
- Store structured data snapshots in `ai_development_tools/coverage.json` for diffable history.
