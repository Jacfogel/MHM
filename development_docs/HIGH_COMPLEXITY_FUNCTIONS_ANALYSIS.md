# High Complexity Functions Analysis & Test Coverage Status

> **File**: `development_docs/HIGH_COMPLEXITY_FUNCTIONS_ANALYSIS.md`

## Overview
- Last updated: 2025-10-01
- Source data: `python ai_development_tools/function_discovery.py` (application modules only, tests excluded)
- Latest test run: `python run_tests.py` (1519 passed, 1 skipped)
- Coverage baseline: 65% overall (11,687 / 17,855 statements) from `python ai_development_tools/regenerate_coverage_metrics.py --update-plan`

## Complexity Snapshot (application modules)
| Complexity Range | Count | Percentage |
|------------------|-------|------------|
| >500 nodes       | 35    | 2.7%       |
| 200-499 nodes    | 200   | 15.4%      |
| 100-199 nodes    | 321   | 24.8%      |
| 50-99 nodes      | 341   | 26.3%      |
| <50 nodes        | 398   | 30.7%      |
| Total functions  | 1,295 | 100%       |

*Complexity measured as AST node count per function. Functions under `tests/` are excluded to focus on shipped application code.*

## Audit Cross-Check
- 2025-10-01 19:49 comprehensive audit totals: 3,217 functions scanned, 154 moderate, 137 high, 98 critical.
- Audit counts include test helpers; the table above filters to application modules only (1,295 functions) to highlight shipped code risk.
- Documentation coverage during the same audit was 92.51%, confirming complexity - not documentation drift - is the primary backlog.

## Critical Functions (>=500 nodes)
| Function | Location | Complexity | File Coverage |
|----------|----------|------------|---------------|
| get_user_data | core/user_data_handlers.py | 1,962 | 64.9% |
| _handle_show_profile | communication/command_handlers/profile_handler.py | 1,102 | 0.0% (not executed) |
| _handle_show_profile | communication/command_handlers/interaction_handlers.py | 992 | 55.5% |
| _get_contextual_fallback | ai/chatbot.py | 986 | 59.6% |
| handle_message | communication/message_processing/interaction_manager.py | 929 | 43.5% |
| _create_comprehensive_context_prompt | ai/chatbot.py | 888 | 59.6% |
| _handle_update_profile | communication/command_handlers/interaction_handlers.py | 815 | 55.5% |
| _handle_update_profile | communication/command_handlers/profile_handler.py | 815 | 0.0% (not executed) |
| _extract_entities_rule_based | communication/message_processing/command_parser.py | 810 | 74.3% |
| initialize__register_events | communication/communication_channels/discord/bot.py | 808 | 46.9% |

Key observations:
- Profile management handlers remain the largest risk: they contain 1,900+ nodes across two files and never execute during the coverage run, so refactors would be unguarded today.
- Interaction routing (`interaction_manager.py`) and Discord bot bootstrap code are still large and only about 45-47% covered, leaving many branches untested.
- AI prompt construction functions carry roughly 900 nodes while hovering below 60% coverage, so regression-proofing requires additional scenario tests.

## High Complexity Focus (200-499 nodes)
- `communication/command_handlers/interaction_handlers.py`: 22 functions in this band, 55.5% file coverage. Prioritise scenario-driven tests for profile, task, and scheduling handlers before attempting more extractions.
- `ui/ui_app_qt.py`: 13 functions at or above 200 nodes with only 27.6% coverage. The UI bootstrap path needs deterministic harnesses to exercise signal wiring and validation logic.
- `communication/command_handlers/analytics_handler.py`: 11 high-complexity helpers and no recorded coverage. Add integration tests for analytics commands so refactors are safe.
- `core/user_data_manager.py`: 10 high-complexity functions at 65.6% coverage. Focus on index rebuild and migration paths that remain partially uncovered.
- `core/scheduler.py` and `core/logger.py`: 14 and 9 high-complexity functions respectively, each around 66% coverage. Extend behavior tests to cover failure paths (scheduler recovery, rollover edge cases).

## Moderate Complexity Queue (100-199 nodes)
- 321 functions (24.8% of the codebase) fall in this range; many are helper slices extracted during earlier refactors.
- Concentrate on modules that combine moderate complexity with low coverage, notably `ai/cache_manager.py` (48.5%) and `ui/widgets/task_settings_widget.py` (50.6%).
- Maintain vigilance on refactored helpers in `core/auto_cleanup.py` and `core/checkin_analytics.py`; they currently exceed 85% coverage and act as positive examples for future breaks.

## Next Steps
1. Add coverage for profile and analytics command handlers before refactoring; these files contain 13 of the top 20 complexity hotspots yet remain untested.
2. Build targeted UI harnesses for `ui/ui_app_qt.py` to cover validation, signal registration, and system health checks; this will de-risk the 27% coverage gap on high-complexity UI paths.
3. Expand behavior tests around `interaction_manager.handle_message` to exercise multi-channel fallback logic, then break the handler into composable units.
4. Schedule follow-up complexity scans after each refactor with `python ai_development_tools/function_discovery.py` to track reductions and keep this document fresh.
