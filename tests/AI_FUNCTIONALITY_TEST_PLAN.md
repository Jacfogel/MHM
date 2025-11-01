# AI Functionality Test Plan

> **Created**: 2025-10-27  
> **Updated**: 2025-11-01  
> **Purpose**: Comprehensive test plan for system AI functionality  
> **Status**: ✅ Modular test suite implemented and executed successfully

## Overview

This document outlines a comprehensive test plan for validating all AI functionality in the MHM system. The test suite has been refactored into modular test files for better maintainability.

**Latest Test Results**: 38 passed, 1 partial, 0 failed (out of 39+ tests)  
**Test Runner**: `python tests/ai/run_ai_functionality_tests.py`  
**Reports Location**: `tests/ai/results/ai_functionality_test_results_latest.md`  
**Test Suite Structure**: Modular (split across 7 test modules + base utilities)

## Test Suite Architecture

The test suite has been refactored from a single large file into focused, maintainable modules:

- **`ai_test_base.py`**: Shared utilities (logging, user management, base class)
- **`test_ai_core.py`**: Core functionality (basic responses, contextual, mode detection, commands)
- **`test_ai_integration.py`**: Integration tests (context with check-ins, conversation history)
- **`test_ai_errors.py`**: Error handling and API error scenarios
- **`test_ai_cache.py`**: Cache behavior and isolation tests
- **`test_ai_performance.py`**: Performance metrics and response time validation
- **`test_ai_quality.py`**: Response quality validation and edge cases
- **`run_ai_functionality_tests.py`**: Main runner that orchestrates all tests

## Test Categories

### 1. Basic AI Response Generation ✅ IMPLEMENTED

**Objective**: Verify basic AI chatbot response generation works correctly

**Tests**:
1. ✅ Test singleton pattern (already covered in automated tests)
2. ✅ Test `generate_response()` with simple prompts (T-1.1)
3. ✅ Test `generate_response()` with different modes (chat, command) (T-1.2, T-1.3)
4. ✅ Test AI availability check (T-1.4)
5. ⚠️ Test response caching behavior (T-1.5 - PARTIAL: Cache not used when AI available)
6. ⏳ Test timeout handling (not yet implemented)

**Expected Results**:
- ✅ Responses are generated successfully
- ✅ AI availability detected correctly
- ⚠️ Cache behavior needs investigation (may be expected if AI is available)
- ⏳ Timeout handling not yet tested

**Status**: Tests passing, cache behavior needs review

---

### 2. Contextual Response Generation ✅ IMPLEMENTED

**Objective**: Verify AI generates context-aware responses using user data

**Tests**:
1. ✅ Test `generate_contextual_response()` with new user (minimal context) (T-2.1)
2. ✅ Test context building with user profile data (T-2.2)
3. ✅ Test contextual response includes user name (T-2.3)
4. ⏳ Test `generate_contextual_response()` with recent check-in data (covered in Category 4)
5. ⏳ Test `generate_contextual_response()` with mood trends (covered in Category 4)
6. ⏳ Test `generate_contextual_response()` with conversation history (covered in Category 7)
7. ⏳ Test `generate_contextual_response()` with task data (not yet implemented)
8. ⏳ Test `generate_contextual_response()` with recent automated messages (not yet implemented)

**Expected Results**:
- ✅ Responses incorporate user context appropriately
- ✅ User names included when available
- ✅ Context includes user profile, recent activity, conversation insights, preferences, mood trends
- ✅ Context builder handles missing data gracefully

**Status**: Core tests passing, additional context types can be added

---

### 3. Command Parsing and Mode Detection ✅ IMPLEMENTED

**Objective**: Verify AI correctly parses commands and detects intent

**Tests**:
1. ✅ Test `_detect_mode()` with clear commands (T-3.1)
2. ✅ Test `_detect_mode()` with ambiguous requests (T-3.2)
3. ✅ Test clarification mode triggered for ambiguous inputs (T-3.2)
4. ✅ Test command parsing creates structured JSON output (T-5.6)
5. ⏳ Test clarification prompt used when needed (not yet implemented)
6. ✅ Test various command phrasings ("add task", "create task", "new task") (T-5.1, T-5.2, T-5.3, T-5.4)
   - ⚠️ "I need to buy groceries" detected as chat instead of command (T-5.5 - PARTIAL)

**Expected Results**:
- ✅ Clear commands detected as "command" mode
- ✅ Ambiguous requests trigger "command_with_clarification" mode
- ✅ Structured JSON output generated for commands
- ✅ Chat messages detected correctly (T-3.3)
- ⚠️ Natural language task requests may need improvement

**Status**: Core functionality passing, natural language detection could be enhanced

---

### 4. Context Building with Check-in Data ✅ IMPLEMENTED

**Objective**: Verify context builder assembles accurate user context including check-in data

**Tests**:
1. ✅ Test context includes check-in data (T-4.1)
2. ✅ Test context includes user profile data (T-2.2)
3. ✅ Test context includes mood/energy trends (T-2.2 shows mood_trends in context)
4. ✅ Test context includes conversation history (T-7.2)
5. ⏳ Test context includes recent automated messages (not yet implemented)
6. ⏳ Test context includes task reminders (not yet implemented)
7. ✅ Test context builder handles missing data gracefully (T-6.2)

**Expected Results**:
- ✅ Check-in data found in context and referenced in responses
- ✅ All relevant user data included in context
- ✅ Context structure validated (user_profile, recent_activity, conversation_insights, preferences, mood_trends)
- ✅ Missing data handled without errors

**Status**: Core tests passing, additional context elements can be added

---

### 5. Command Parsing Variations ✅ IMPLEMENTED

**Objective**: Test various command phrasings and parsing accuracy

**Tests**:
1. ✅ "add task buy groceries" (T-5.1)
2. ✅ "create task buy groceries" (T-5.2)
3. ✅ "new task buy groceries" (T-5.3)
4. ✅ "task: buy groceries" (T-5.4)
5. ⚠️ "I need to buy groceries" (T-5.5 - PARTIAL: detected as chat)
6. ✅ Command parsing creates structured output (T-5.6)

**Status**: Core phrasings work, natural language could be improved

---

### 6. Error Handling and Fallbacks ✅ IMPLEMENTED

**Objective**: Verify AI handles errors gracefully and provides appropriate fallbacks

**Tests**:
1. ✅ Test invalid user_id (None) handling (T-6.1)
2. ✅ Test missing context data handling (T-6.2)
3. ✅ Test empty prompt handling (T-6.3)
4. ✅ Test API connection failures (T-10.1 - mocked)
5. ✅ Test API timeout scenarios (T-10.2 - mocked)
6. ✅ Test malformed API responses (T-10.3 - mocked)
7. ✅ Test server error (5xx) handling (T-10.4 - mocked)

**Expected Results**:
- ✅ Errors don't crash the system
- ✅ Appropriate fallback responses provided
- ✅ Invalid inputs handled gracefully
- ✅ API/network error handling tested with mocks

**Status**: Error handling comprehensive, all error scenarios tested

---

### 7. Conversation History Integration ✅ IMPLEMENTED

**Objective**: Verify conversation history is tracked and used appropriately

**Tests**:
1. ✅ Test conversation exchanges stored correctly (T-8.1)
2. ✅ Test recent conversations retrieved accurately (T-8.2)
3. ✅ Test conversation history included in context prompts (T-7.2)
4. ✅ Test conversation history affects subsequent responses (T-7.1)
5. ⏳ Test conversation history limits (last N exchanges) (not yet implemented)

**Expected Results**:
- ✅ Exchanges stored correctly
- ✅ Recent conversations retrieved accurately
- ✅ History included in context when requested
- ✅ Responses show awareness of previous exchanges
- ⏳ History limits not yet tested

**Status**: Core functionality working, limits testing can be added

---

### 8. Conversation History Storage ✅ IMPLEMENTED

**Objective**: Verify conversation history is persistently stored and retrieved

**Tests**:
1. ✅ Store conversation exchanges (T-8.1)
2. ✅ Retrieve recent interactions (T-8.2)

**Status**: Implementation complete and tested

---

### 9. Integration with Conversation Manager

**Objective**: Verify AI integrates properly with conversation flow manager

**Tests**:
1. ⏳ Test default contextual chat for general messages
2. ⏳ Test AI responses generated through conversation manager
3. ⏳ Test check-in flow doesn't trigger AI chat
4. ⏳ Test `/cancel` command handled correctly
5. ⏳ Test conversation manager uses AI for contextual responses

**Status**: Not yet implemented in test runner (requires full system integration testing)

---

### 10. Cache Functionality ✅ IMPLEMENTED

**Objective**: Verify response caching works correctly

**Tests**:
1. ✅ Test response caching behavior (T-1.5 - Cache working correctly)
2. ✅ Test cache stores responses with correct keys (T-11.3)
3. ✅ Test cache retrieves responses correctly (T-11.3)
4. ✅ Test cache isolates responses by user (T-11.1)
5. ✅ Test cache isolates responses by mode (T-11.2)
6. ⏳ Test cache skipped for data analysis questions (not yet implemented)
7. ⏳ Test cache performance improvement (timing data collected in T-1.5)

**Status**: Cache functionality verified - isolation by user and mode working correctly

---

### 11. LM Studio Connection Handling

**Objective**: Verify LM Studio connection detection and handling

**Tests**:
1. ✅ Test connection detection when LM Studio running (T-1.4 shows AI available: True)
2. ⏳ Test connection detection when LM Studio not running
3. ⏳ Test fallback mode when connection unavailable
4. ⏳ Test connection retry behavior
5. ⏳ Test model availability detection

**Status**: Basic availability check working, additional scenarios need testing

---

### 12. Performance and Resource Management ✅ IMPLEMENTED

**Objective**: Verify AI performs well under various conditions

**Tests**:
1. ✅ Test response time for simple queries (T-9.1 - target <5s)
2. ✅ Test response time for contextual queries (T-9.2 - target <10s)
3. ⏳ Test concurrent request handling (not yet implemented)
4. ⏳ Test memory usage during AI operations (not yet implemented)
5. ⏳ Test adaptive timeout under resource constraints (not yet implemented)
6. ✅ Test response length validation (T-9.3)

**Status**: Performance metrics tracked, response times within acceptable ranges

---

## Test Execution Notes

### Prerequisites
- LM Studio running (optional - tests should work with fallbacks)
- Test user created with various data scenarios
- Service running: `python run_headless_service.py start`

### Test Data Scenarios
1. **New User**: Minimal profile, no check-ins, no history
2. **Active User**: Full profile, recent check-ins, conversation history
3. **Mood Tracking User**: Check-ins with mood/energy data
4. **Task User**: Tasks created, some completed

### Execution Order
1. Basic functionality (can work with fallbacks)
2. Context building (requires test user data)
3. Integration tests (requires full system)
4. Performance tests (can be last)

---

## Results Template

For each test:
```
**Test ID**: T-XXX
**Test Name**: [Test name]
**Status**: ✅ PASS / ❌ FAIL / ⚠️ PARTIAL
**Notes**: [Any observations]
**Issues Found**: [Any issues]
```

---

## Test Runner Implementation

**Main Runner**: `tests/ai/run_ai_functionality_tests.py`

**Usage**:
```powershell
& c:/Users/Julie/projects/MHM/MHM/.venv/Scripts/Activate.ps1
python tests\ai\run_ai_functionality_tests.py
```

**Test Module Structure**:
- `ai_test_base.py` - Base class with shared utilities
- `test_ai_core.py` - Core functionality tests (Categories 1-3, 5)
- `test_ai_integration.py` - Integration tests (Categories 4, 7-8)
- `test_ai_errors.py` - Error handling tests (Categories 6, 10)
- `test_ai_cache.py` - Cache tests (Categories 1.5, 11)
- `test_ai_performance.py` - Performance tests (Category 9)
- `test_ai_quality.py` - Quality and edge cases (Categories 12-13)

**Features**:
- Modular test organization for maintainability
- Automatic test execution across 13 test categories
- Detailed logging with prompts and responses
- Performance metrics tracking (response times)
- Report generation to `tests/ai/results/`
- Test result file rotation (keeps last 10 files)
- Automatic test data directory cleanup
- Windows console encoding safety (Unicode handling)

**Test Results Summary**:
- **Total Tests**: 39+
- **Passed**: 38+
- **Partial**: 1 (T-5.5 natural language command detection)
- **Failed**: 0

**Test Result File Rotation**: Automatically keeps only the 10 most recent timestamped result files

---

## Test Execution Notes

### Logging Behavior
- **Consolidated Logging**: All logs are consolidated into two files, matching the test suite pattern:
  - `tests/logs/test_consolidated.log` - Component logs from `mhm.*` loggers (AI, communication, scheduler, etc.)
  - `tests/logs/test_run.log` - Test execution logs from the test runner itself
- **No Individual Component Logs**: Individual component log files (ai.log, app.log, errors.log, etc.) are NOT created - all component logs go to `test_consolidated.log`
- **Environment Setup**: Test runner sets `MHM_TESTING=1`, `TEST_CONSOLIDATED_LOGGING=1`, `LOGS_DIR=tests/logs`, and `TEST_LOGS_DIR=tests/logs` before any logger initialization
- **Test Isolation**: Test data directories are created under `tests/data/tmp/` and automatically cleaned up
- **Log Isolation**: Test activity does NOT appear in main system logs - all test logs go to `tests/logs/` for proper isolation
- **Automatic Response Validation**: Tests automatically validate AI responses for quality issues (meta-text, code fragments) and update test status accordingly

### Cleanup
- **Test Data**: Test data directories are cleaned up after test execution
- **Result Files**: Test result files are automatically rotated (keeps last 10 timestamped files)
- **Temporary Files**: All test artifacts are created under `tests/data/tmp/` which is cleaned up

### Known Issues
- **Unicode/Emoji**: Windows console encoding issues with emojis - test uses Unicode characters instead

## Next Steps

### Completed ✅
1. ✅ Test runner implemented (modular architecture)
2. ✅ Core functionality tested (39+ tests across 13 categories)
3. ✅ Results documented with performance metrics
4. ✅ Error handling scenarios tested (mocked API errors)
5. ✅ Cache functionality verified (isolation, TTL, retrieval)
6. ✅ Performance metrics tracked (response times)
7. ✅ Quality validation tests implemented
8. ✅ Edge case handling tested
9. ✅ Test result file rotation implemented
10. ✅ Test data cleanup automated
11. ✅ Consolidated logging implemented (test_consolidated.log and test_run.log)
12. ✅ Automatic response validation integrated
13. ✅ Username validation updated (allows conversational name usage)

### To Do ⏳
1. Improve natural language command detection (T-5.5)
2. Add integration tests with conversation manager
3. Add concurrent request handling tests
4. Add memory usage monitoring tests
5. Add timeout handling tests with actual timeouts
6. ✅ Route test logs to `tests/logs/` instead of main `logs/` directory (implemented)
7. ✅ Clean up old test temp directories (old directories cleaned up)


