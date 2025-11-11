# Plan a Refactor

## Overview
Design and execute a safe, incremental refactor while honouring project safety rules.

## Steps
### Plan
1. Confirm a recent status or audit snapshot; note impacted modules.
2. Define scope, risks, and success criteria; record in TODO/PLANS if multi-step.
3. Identify tests that must cover the change.

### Execute
1. Work in small slices; after each slice run targeted tests and, when relevant, `python run_headless_service.py start`.
2. Update documentation and changelogs when behaviour changes.
3. Any necessary legacy code must include `LEGACY COMPATIBILITY` headers, logging, and a removal plan.
4. **Removing legacy code**: Use search-and-close approach - find all references with `--find`, update them, verify with `--verify`, then remove. See `ai_development_docs/AI_LEGACY_REMOVAL_GUIDE.md`.

### Validate
1. Run `python run_tests.py`.
2. Optionally refresh metrics with `python -m ai_development_tools.ai_tools_runner audit`.
3. Sync paired docs and confirm TODO/changelog updates.

## Response Template
#### Refactor Plan
- Scope & Goals: ...
- Risks & Mitigations: ...
- Test Strategy: ...

#### Execution Summary
- Slices Completed: ...
- Files Updated: ...
- Docs/Changelogs: ...

#### Validation
- Test Results: ...
- Audit/Status Follow-up: ...
- Outstanding Tasks: ...
