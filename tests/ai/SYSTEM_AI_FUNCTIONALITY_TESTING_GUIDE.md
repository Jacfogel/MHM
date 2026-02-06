# System AI Functionality Testing Guide

> **File**: `tests/ai/SYSTEM_AI_FUNCTIONALITY_TESTING_GUIDE.md`  
> **Audience**: Developers and AI assistants working on MHM AI functionality  
> **Purpose**: Quick reference for running and understanding **automated** AI functionality tests  
> **Style**: Technical, concise, actionable  
> **Parent**: [TESTING_GUIDE.md](tests/TESTING_GUIDE.md)  
> This document is subordinate to [TESTING_GUIDE.md](tests/TESTING_GUIDE.md) and should be kept consistent with its standards and terminology.

This guide describes how to run and interpret the **AI functionality test suite**.

Use it when you change AI-related behavior (prompts, context building, caching, routing, integrations), or when manual AI behavior testing (see section 7 of [MANUAL_TESTING_GUIDE.md](tests/MANUAL_TESTING_GUIDE.md)) indicates regressions.

---

## 1. Quick Start

**Run AI Functionality Tests**:

```powershell
& c:/Users/Julie/projects/MHM/MHM/.venv/Scripts/Activate.ps1
python tests\ai\run_ai_functionality_tests.py
```

**Test Results Location**:
- [ai_functionality_test_results_latest.md](tests/ai/results/ai_functionality_test_results_latest.md)

---

## 2. Test Suite Structure

The AI functionality test suite is organized into focused, maintainable modules:

- `tests/ai/ai_test_base.py`: Shared utilities (logging, user management, base class)
- `tests/ai/test_ai_core.py`: Core functionality (basic responses, contextual, mode detection, commands)
- `tests/ai/test_ai_integration.py`: Integration tests (context with check-ins, conversation history)
- `tests/ai/test_ai_errors.py`: Error handling and API error scenarios
- `tests/ai/test_ai_cache.py`: Cache behavior and isolation tests
- `tests/ai/test_ai_performance.py`: Performance metrics and response time validation
- `tests/ai/test_ai_quality.py`: Response quality validation and edge cases
- `tests/ai/test_ai_advanced.py`: Advanced tests (multi-turn conversations, personality consistency, error recovery)
- `tests/ai/run_ai_functionality_tests.py`: Main runner that orchestrates all tests

---

## 3. Prerequisites

- LM Studio running (**optional** - tests should work with fallbacks)
- Test user data scenarios available (created by the runner / fixtures as applicable)
- Service running (if required by the suite): `python run_headless_service.py start`

---

## 4. Test Data Scenarios

Typical scenarios exercised by the suite:

1. **New User**: Minimal profile, no check-ins, no history
2. **Active User**: Full profile, recent check-ins, conversation history
3. **Mood Tracking User**: Check-ins with mood/energy data
4. **Task User**: Tasks created, some completed

---

## 5. Logging Behavior

- **Consolidated Logging**: All logs are consolidated into two files:
  - `tests/logs/test_consolidated.log` (component logs from `mhm.*` loggers - AI, communication, scheduler, etc.)
  - `tests/logs/test_run.log` (test execution logs from the runner itself)
- **No Individual Component Logs**: Individual component log files are NOT created; all component logs go to `test_consolidated.log`
- **Test Isolation**:
  - Test data directories are created under `tests/data/tmp/` and automatically cleaned up
  - Test activity does NOT appear in main system logs; all test logs go to `tests/logs/`

---

## 6. Test Features

- Modular test organization for maintainability
- Automatic test execution across multiple AI behavior categories
- Detailed logging with prompts and responses
- Automatic response validation for quality issues (meta-text, code fragments)
- Performance metrics tracking (response times)
- Report generation to `tests/ai/results/` with context information
- Test result file rotation (keeps last 10 files)
- Automatic test data directory cleanup

---

## 7. Test Categories

The test suite covers categories such as:

1. Basic AI response generation
2. Contextual response generation
3. Command parsing and mode detection
4. Context building with check-in data
5. Command parsing variations
6. Error handling and fallbacks
7. Conversation history integration and storage
8. Cache functionality
9. LM Studio connection handling
10. Performance and resource management
11. Advanced multi-turn and coherence checks

---

## 8. Known Issues

- **Unicode/Emoji**: Windows console encoding issues with emojis - the suite uses Unicode-safe characters instead.

---

## 9. Cleanup

- **Test Data**: Test data directories are cleaned up after test execution
- **Result Files**: Test result files are automatically rotated (keeps last 10 timestamped files)
- **Temporary Files**: All test artifacts are created under `tests/data/tmp/` which is cleaned up

---

## 10. Where to Track Active Work

- Active work items should be tracked in [TODO.md](TODO.md) and [PLANS.md](development_docs/PLANS.md).
- This doc should stay focused on *running and interpreting* the AI functionality test suite (not long-term planning).