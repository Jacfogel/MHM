# System AI Functionality Testing Guide

> **File**: `tests/ai/SYSTEM_AI_FUNCTIONALITY_TESTING_GUIDE.md`  
> **Audience**: Developers and AI assistants working on MHM AI functionality  
> **Purpose**: Quick reference for running and understanding **automated** AI functionality tests  
> **Style**: Technical, concise, actionable  
> **Parent**: [TESTING_GUIDE.md](../TESTING_GUIDE.md)  
> This document is subordinate to [TESTING_GUIDE.md](../TESTING_GUIDE.md) and should be kept consistent with its standards and terminology.

This guide describes how to run and interpret the **AI functionality test suite**.

Use it when you change AI-related behavior (prompts, context building, caching, routing, integrations), or when manual AI behavior testing (see section 7 of [MANUAL_TESTING_GUIDE.md](../MANUAL_TESTING_GUIDE.md#7-ai-behavior-manual-tests)) indicates regressions.

---

## 1. Quick Start

**Run AI Functionality Tests**:

```powershell
& c:/Users/Julie/projects/MHM/MHM/.venv/Scripts/Activate.ps1
python -m tests.ai.run_ai_functionality_tests
```

Notes:
- This is the canonical runner for the AI functionality suite.
- Default `python run_tests.py` does not run the full AI functionality suite from this guide.
- Run suites sequentially: the functionality runner cleans shared test users and logs.

**Complementary checks** (use the project virtual environment):

```powershell
python -m pytest -m ai -q
python -m tests.ai.evaluate_prompts --live --output tests/ai/results/prompt_evaluation_current.json
```

The pytest selection covers mocked behavior, context, planning, execution, and
post-processing contracts. The opt-in prompt evaluator sends paid requests using
synthetic inputs; it stops on a connection failure and never counts a fallback as
model success. It currently contains 24 cases, with optional `--repeat 3`.
Before inference, it checks the request, reference data, history roles, execution
metadata, and case-specific instruction prerequisites after context-budget fitting.
Failed preflight skips the model call. `failure_diagnosis` separates application
context/prompt/parser/post-processing problems from service/configuration errors
and candidate model-output problems. Arbitrary semantic instruction conflicts and
model-quality judgments still require review; a failed keyword check is evidence
to inspect, not definitive blame.

For the six adversarial cases alone:

```powershell
python -m tests.ai.evaluate_prompts --live --safety-only --repeat 3 --output tests/ai/results/safety_evaluation.json
```

These use a real model with synthetic crisis, harmful wellness, cross-account
disclosure, history-injection, action-result-injection, and failed-save-pressure
inputs. They do not test storage authorization or perform real saves. Safety
checks apply to raw output as well as final output. Every case retains its review
rubric, full input messages, raw/final replies, model, and token/latency data.

### 1.1. Contract results, response sources, and semantic review

Automatic PASS means the named contract passed. It is not semantic-quality
approval. Conversational responses retain `review_status: pending`; missing
turn evidence is `insufficient_evidence`. Mode/post-process/cache fixtures are
`not_applicable` for semantic review. Review request fulfillment, grounding,
capability truthfulness, safety, tone, and concision before approving quality.

The functionality suite observes each synchronous chatbot turn and records
model output, cache retrieval, fallback, deterministic repairs, and simulated
provider errors. A successful model source requires observed HTTP transport and
text on that call. Uninstrumented paths stay `unknown`, rather than inheriting
availability from an earlier check. Source events preserve raw text when a guard
replaces it; a repaired answer is not evidence of model-quality success.

The report includes counts by source/scenario and contract status, plus a
lossless companion `ai_functionality_test_results_latest.json`. Full turn
prompts/replies, provider input messages, exceptions, disabled flags, zero counts,
and empty context values are preserved. Cache cases seed distinct per-user and
per-mode payloads, assert exact retrieval/misses, and actually exercise expiry;
identical model replies and timing alone cannot pass isolation.

Do not interpret the functionality runner's exit code as a quality approval:
PARTIAL results currently return zero. Check availability (T-1.4), read the actual
responses, and distinguish model responses, deterministic guards, mocks, and
fallbacks. Its latency summary mixes these paths and is not a model benchmark.
Future reports preserve full responses and explicit zero/false context values.

**Test Results Location**:
- [ai_functionality_test_results_latest.md](results/ai_functionality_test_results_latest.md)

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
- `tests/ai/test_ai_postprocess.py`: Deterministic post-process leak contract tests (category 17)
- `tests/ai/test_ai_advanced.py`: Advanced tests (multi-turn conversations, personality consistency, error recovery)
- `tests/ai/test_ai_live_journeys.py`: Live safety/honesty journeys (T-18.x; FAIL on false CRUD, invented check-ins, fake creates)
- `tests/ai/run_ai_functionality_tests.py`: Main runner that orchestrates all tests

---

## 3. Prerequisites

- A valid OpenAI API key (**optional** - deterministic tests use mocks and fallbacks)
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
9. OpenAI connection handling
10. Performance and resource management
11. Advanced multi-turn and coherence checks
12. Post-process leak contract (T-17.x fixture tests; deterministic, no OpenAI)
13. Live safety and honesty journeys (T-18.x; real model when OpenAI is accessible)

Do **not** re-review mocked routing after a pytest-green run of [test_ai_user_journeys.py](../behavior/test_ai_user_journeys.py). When you run this live suite, treat **T-18.x failures as blockers** (false CRUD, invented check-ins, fake creates). Skip re-reading categories 3, 4, 5, and 6 for those same contracts if T-18 passed.

Keep live OpenAI **tone** review for categories 1, 2, and 11.

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

- Active work items should be tracked in [TODO.md](../../TODO.md) and [PLANS.md](../../development_docs/PLANS.md).
- This doc should stay focused on *running and interpreting* the AI functionality test suite (not long-term planning).
