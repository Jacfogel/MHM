# MHM contributor instructions

> **File**: `AGENTS.md`
> **Purpose**: Essential project constraints and navigation for AI collaborators

## 1. Working in this project

- MHM is a communication-first mental health assistant. Explain changes plainly, in small steps when useful.
- Use PowerShell-safe commands and the project `.venv`; do not install dependencies globally. Setup and entry points: [HOW_TO_RUN.md](HOW_TO_RUN.md).
- Read the relevant behavior spec in [SPECS_GUIDE.md](specs/SPECS_GUIDE.md) before changing its implementation. Shared topic guides serve humans and AI; do not create parallel AI versions.
- Inspect the user-referenced file first, follow existing patterns, and ground changes in files and behavior you have checked. Clarify material uncertainty rather than inventing missing context.
- Verify command outcomes (`$LASTEXITCODE` in PowerShell); inspect the failure before retrying and report unresolved failures.
- Keep changes focused. Run checks appropriate to the changed behavior and report actual results and remaining limits.

## 2. Essential boundaries

- Persist user data through `storage.*` helpers or the stable `core` package facade, never direct feature-level file access. See [USER_DATA_MODEL.md](core/USER_DATA_MODEL.md).
- Use `core/time_utilities.py` for current time, parsing, and formatting. Centralize configuration in `core/config.py`; document changes in [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md).
- Use canonical component names with `core.logger.get_component_logger`; use shared error handling and safe recovery messages. See [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md) and [ERROR_HANDLING_GUIDE.md](core/ERROR_HANDLING_GUIDE.md).
- Keep shared business logic independent of channel adapters and UI types. See [ARCHITECTURE.md](ARCHITECTURE.md) and [COMMUNICATION_GUIDE.md](communication/COMMUNICATION_GUIDE.md).
- Edit `.ui` sources and regenerate UI code; do not hand-edit generated Python. See [UI_GUIDE.md](ui/UI_GUIDE.md).
- Tests must write only to isolated test paths or fixture temporary directories, never production data or logs. Mock Windows Task Scheduler integrations. Use canonical time helpers and shared fixtures. See [TESTING_GUIDE.md](tests/TESTING_GUIDE.md).
- MHM is alpha software. Migrate current callers, tests, and active data directly; do not add or preserve compatibility shims solely for older MHM versions. Exceptions require an explicit user request or an external contract. Preserve user-created data; ask before irreversible deletion when migration is not possible. See [LEGACY_COMPATIBILITY_GUIDE.md](development_docs/LEGACY_COMPATIBILITY_GUIDE.md).
- Before restoring, validate the backup and create a safety backup. Use existing backup APIs; see [BACKUP_GUIDE.md](development_docs/BACKUP_GUIDE.md).
- Diagnose failures from `logs/errors.log`, then the relevant component log; use isolated test logs for test failures. Preserve the documented service entry points and check service state before starting another instance.
- Before changing audit scope, check `development_tools/shared/standard_exclusions.py` and host configuration so caches, generated artifacts, scripts, and test results remain excluded as intended. Distinguish cached status from freshly collected audit evidence.
- For feature setup and operating constraints, read the relevant [SMS_GUIDE.md](communication/communication_channels/sms/SMS_GUIDE.md), [WEBSITE_GUIDE.md](website/WEBSITE_GUIDE.md), [GOOGLE_HEALTH_GUIDE.md](integrations/google_health/GOOGLE_HEALTH_GUIDE.md), or [SYSTEM_AI_GUIDE.md](ai/SYSTEM_AI_GUIDE.md).

## 3. Completing work

- Update the shared guide or spec that owns changed behavior. Generated reports must be refreshed through their generator.
- Record meaningful work in [CHANGELOG_DETAIL.md](development_docs/CHANGELOG_DETAIL.md), with one short session summary in [CHANGELOG_BRIEF.md](development_docs/CHANGELOG_BRIEF.md). No heading synchronization is required.
- Track removals and deprecated paths in `development_docs/devtools/DEPRECATION_INVENTORY.json`. Active follow-ups belong in [TODO.md](TODO.md); longer plans belong in [PLANS.md](development_docs/PLANS.md).
- Tool commands, audit tiers, and reports: [README.md](development_tools/README.md). Use targeted tests for focused changes and broader validation when warranted. Documentation checks use `python development_tools/run_development_tools.py doc-sync`.
