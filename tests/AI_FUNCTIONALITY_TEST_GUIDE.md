# AI Functionality Testing Guide

> **File**: `tests/AI_FUNCTIONALITY_TEST_GUIDE.md`  
> **Audience**: Developers and AI assistants working on MHM AI functionality testing  
> **Purpose**: Quick reference guide for running and understanding AI functionality tests  
> **Style**: Technical, concise, actionable

## 1. Quick Start

**Run AI Functionality Tests**:
```powershell
& c:/Users/Julie/projects/MHM/MHM/.venv/Scripts/Activate.ps1
python tests\ai\run_ai_functionality_tests.py
```

**Test Results Location**: `tests/ai/results/ai_functionality_test_results_latest.md`

## 2. Test Suite Structure

The AI functionality test suite is organized into focused, maintainable modules:

- **`tests/ai/ai_test_base.py`**: Shared utilities (logging, user management, base class)
- **`tests/ai/test_ai_core.py`**: Core functionality (basic responses, contextual, mode detection, commands)
- **`tests/ai/test_ai_integration.py`**: Integration tests (context with check-ins, conversation history)
- **`tests/ai/test_ai_errors.py`**: Error handling and API error scenarios
- **`tests/ai/test_ai_cache.py`**: Cache behavior and isolation tests
- **`tests/ai/test_ai_performance.py`**: Performance metrics and response time validation
- **`tests/ai/test_ai_quality.py`**: Response quality validation and edge cases
- **`tests/ai/test_ai_advanced.py`**: Advanced tests (multi-turn conversations, personality consistency, error recovery)
- **`tests/ai/run_ai_functionality_tests.py`**: Main runner that orchestrates all tests

## 3. Prerequisites

- LM Studio running (optional - tests should work with fallbacks)
- Test user created with various data scenarios
- Service running: `python run_headless_service.py start`

## 4. Test Data Scenarios

1. **New User**: Minimal profile, no check-ins, no history
2. **Active User**: Full profile, recent check-ins, conversation history
3. **Mood Tracking User**: Check-ins with mood/energy data
4. **Task User**: Tasks created, some completed

## 5. Logging Behavior

- **Consolidated Logging**: All logs are consolidated into two files:
  - `tests/logs/test_consolidated.log` - Component logs from `mhm.*` loggers (AI, communication, scheduler, etc.)
  - `tests/logs/test_run.log` - Test execution logs from the test runner itself
- **No Individual Component Logs**: Individual component log files are NOT created - all component logs go to `test_consolidated.log`
- **Test Isolation**: Test data directories are created under `tests/data/tmp/` and automatically cleaned up
- **Log Isolation**: Test activity does NOT appear in main system logs - all test logs go to `tests/logs/` for proper isolation

## 6. Test Features

- **Modular test organization** for maintainability
- **Automatic test execution** across 16 test categories
- **Detailed logging** with prompts and responses
- **Automatic response validation** for quality issues (meta-text, code fragments)
- **Performance metrics tracking** (response times)
- **Report generation** to `tests/ai/results/` with context information
- **Test result file rotation** (keeps last 10 files)
- **Automatic test data directory cleanup**

## 7. Test Categories

The test suite covers 16 categories:
1. Basic AI Response Generation
2. Contextual Response Generation
3. Command Parsing and Mode Detection
4. Context Building with Check-in Data
5. Command Parsing Variations
6. Error Handling and Fallbacks
7. Conversation History Integration
8. Conversation History Storage
9. Integration with Conversation Manager
10. Cache Functionality
11. LM Studio Connection Handling
12. Performance and Resource Management
13-16. Advanced tests (multi-turn, coherence, personality, error recovery)

## 8. Known Issues

- **Unicode/Emoji**: Windows console encoding issues with emojis - test uses Unicode characters instead

## 9. Cleanup

- **Test Data**: Test data directories are cleaned up after test execution
- **Result Files**: Test result files are automatically rotated (keeps last 10 timestamped files)
- **Temporary Files**: All test artifacts are created under `tests/data/tmp/` which is cleaned up

---

**Note**: For detailed test plan information and historical test results, see the archived `tests/AI_FUNCTIONALITY_TEST_PLAN.md` (archived 2025-11-20). Active work items are tracked in `development_docs/PLANS.md` under "AI Chatbot Actionability Sprint".

