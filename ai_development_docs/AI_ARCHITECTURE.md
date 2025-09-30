# AI Architecture - Quick Reference

> **Purpose**: High-impact architectural cues for AI collaborators  
> **Style**: Concise, pattern-focused, cross-linked  
> **For details**: See [ARCHITECTURE.md](../ARCHITECTURE.md)

## Quick Reference

### Key Module Decision Guide
1. User data access -> `core/user_data_handlers.py`, `core/user_data_validation.py`
2. UI components -> `ui/dialogs/`, `ui/widgets/`, `ui/ui_app_qt.py`
3. Communication flows -> `communication/`
4. Scheduling/reminders -> `core/scheduler.py`, `core/schedule_management.py`
5. Configuration -> `core/config.py`

### Data Flow Overview
- User data: `data/users/{user_id}/` -> handlers -> UI/communication.
- Messages: `resources/default_messages/` -> per-user `messages/` folders.
- Config: `.env` -> `core/config.py` -> runtime.

### Critical Files
- `run_mhm.py` -> main entry point.
- `core/service.py` -> background service lifecycle.
- `ui/ui_app_qt.py` -> admin interface shell.
- `core/user_data_handlers.py` -> unified user data access.
- `communication/core/channel_orchestrator.py` -> channel coordination.

## Directory Overview
- `core/`: Core business logic, scheduling, analytics.
- `communication/`: Channel orchestrators and message flows.
- `ui/`: PySide6 admin app (designs, generated code, dialogs, widgets).
- `data/`: Per-user runtime stores plus logs.
- `resources/default_messages/`: Message templates copied per user.
- `resources/`: Additional presets, assets, and shared resources.
- `ai/`: Local AI integration modules.
- `ai_development_docs/`: AI-focused documentation for quick reference.
- `ai_development_tools/`: Automation for audits, documentation sync, and reporting.
- `development_docs/`: Human references (changelog, dependencies, plans).
- `scripts/`: Utilities for migrations, cleanup, and maintenance tasks.
- `tasks/`: Task and reminder definitions plus supporting helpers.
- `tests/`: Unit, integration, behavior, and UI tests plus supporting fixtures.
- `tests/logs/`: Captured test run logs kept separate from runtime logs.
- `styles/`: QSS themes for the UI.
- `.cursor/rules/`: Cursor rule files guiding AI collaborators.

## User Data Model
- Per-user directory with `account.json`, flat `preferences.json`, `schedules.json`, `user_context.json`, optional feature files.
- Message files only exist for enabled categories and live in `messages/` under each user.
- Access exclusively through `core/user_data_handlers.get_user_data()` and save helpers.

## Data Handling Patterns
- Read -> modify -> save full structures (no partial writes).
- Use validators in `core/user_data_validation.py`.
- Leverage `core/config.py` for all paths and environment details.
- Scheduler helpers manage timing and wake timers-do not bypass them.

## Key Modules and Responsibilities
- `core/user_data_handlers.py` / `core/user_management.py`: load/merge/save data.
- `core/message_management.py`, `core/response_tracking.py`: communication analytics.
- `core/scheduler.py`, `core/service.py`: background execution.
- `communication/core/channel_orchestrator.py`: channel coordination.
- `ui/ui_app_qt.py` plus `ui/dialogs/`, `ui/widgets/`: admin interface.
- `ai_development_tools/`: audits, docs analysis, reporting.

## UI Architecture and Naming Conventions
- Designs: `ui/designs/*.ui` -> Generated: `ui/generated/*_pyqt.py` -> Implementations: `ui/dialogs/` or `ui/widgets/`.
- Dialogs follow names like `ui/dialogs/category_management_dialog.py`; use `_dialog` or `_management_dialog` suffixes.
- Widgets follow names like `ui/widgets/task_settings_widget.py`; use `_widget` or `_settings_widget` suffixes.
- Avoid redundant prefixes-paths convey context.

### File Mapping Examples
- Category management: design `ui/designs/category_management_dialog.ui` -> generated `ui/generated/category_management_dialog_pyqt.py` -> implementation `ui/dialogs/category_management_dialog.py`.
- Account creation: design `ui/designs/account_creator_dialog.ui` -> generated `ui/generated/account_creator_dialog_pyqt.py` -> implementation `ui/dialogs/account_creator_dialog.py`.
- Task settings: design `ui/designs/task_settings_widget.ui` -> generated `ui/generated/task_settings_widget_pyqt.py` -> implementation `ui/widgets/task_settings_widget.py`.

## Adding New Features Safely
- Use `get_user_data()` helpers and preserve flat preference structure.
- Document new message templates and copy rules.
- Follow established naming when extending UI components; regenerate `.ui` outputs via tooling.
- Update `ARCHITECTURE.md` when altering flows or introducing subsystems.

## Development Notes
- IDE debug runs may spawn two service processes-prefer running from an activated terminal for clarity.
- Keep this quick reference aligned with the detailed architecture doc after refactors.
