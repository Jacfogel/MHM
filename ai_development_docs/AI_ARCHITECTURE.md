# AI Architecture - Quick Reference

> **File**: `ai_development_docs/AI_ARCHITECTURE.md`  
> **Purpose**: Route AI tools to the right modules and human docs with minimal context use.  
> For more detailed guidance, examples, and rationale for any topic in this file, use the
> matching sections in `ARCHITECTURE.md`.

Use this file as a router. Decide what you are changing, then jump to the right modules and
sections in `ARCHITECTURE.md` and other detailed guides.

Typical questions and starting points:

- User data access or schema changes  
  -> `core/user_data_handlers.py`, `core/user_data_validation.py`  
  -> Details: see section 2. User Data Model and section 3. Data Handling Patterns in
     `ARCHITECTURE.md`.

- UI layout, dialogs, or widgets  
  -> `ui/ui_app_qt.py`, `ui/dialogs/`, `ui/widgets/`  
  -> Details: see section 5. UI Architecture and Naming Conventions in `ARCHITECTURE.md`.

- Scheduling or reminder logic  
  -> `core/service.py`, `tasks/`  
  -> Details: see section 4. Key Modules and Responsibilities in `ARCHITECTURE.md`.

- Channel behavior (Discord, email, etc.)  
  -> `communication/` modules  
  -> Details: see section 4. Key Modules and Responsibilities and section 6.
     Channel-Agnostic Architecture in `ARCHITECTURE.md`, plus section 2.
     Channel Layers and Boundaries in `communication/COMMUNICATION_GUIDE.md`.

- Configuration and environment variables  
  -> `.env`, `.env.example`, `core/config.py`  
  -> Details: see configuration notes in section 4. Key Modules and Responsibilities in
     `ARCHITECTURE.md` and section 5. Configuration (Environment Variables) in
     `logs/LOGGING_GUIDE.md`.

- Logging and error handling  
  -> `core/logger.py`, `core/error_handling.py`, `logs/`  
  -> Details: see section 2. Logging Architecture in `logs/LOGGING_GUIDE.md` and
     section 2. Architecture Overview in `core/ERROR_HANDLING_GUIDE.md`.

---

## 1. Directory Overview

Top-level routing only; do not duplicate full descriptions here.

- `core/` – core logic, config, logging, error handling, service, schedulers, user data helpers.  
- `communication/` – channel orchestrators and adapters (Discord, email, etc.).  
- `ui/` – PySide6 admin app (designs, generated code, dialogs, widgets, `ui/ui_app_qt.py`).  
- `data/` – per-user runtime data under `data/users/{user_id}/` (use handlers, not raw file IO).  
- `resources/` – shared templates and assets (`resources/default_messages/` for message templates).  
- `ai/` – AI integration (LM Studio and helpers).  
- `ai_development_docs/` – AI-focused documentation for routing and constraints.  
- `ai_development_tools/` – tools runner and commands such as `doc-sync`, `config`, `coverage`.  
- `development_docs/` – human references (changelog, dependencies, plans).  
- `tasks/` – reminder and task definitions.  
- `tests/` – tests, fixtures, `tests/data/`, `tests/logs/`. See section 2. Test Layout and Discovery
  in `tests/TESTING_GUIDE.md`.  
- `logs/` – runtime logs. See section 2. Logging Architecture in `logs/LOGGING_GUIDE.md`.  
- `styles/` – QSS themes.  
- `user/` – instance-level preferences and settings.

If you introduce or remove top-level directories, update this list and the matching section
in `ARCHITECTURE.md`.

---

## 2. User Data Model

Per-user directory: `data/users/{user_id}/`.

Common files:

- `account.json` – identity and channel identifiers.  
- `preferences.json` – flat preference dictionary (no nested root key).  
- `schedules.json` – time periods, categories, and frequencies.  
- `user_context.json` – extra context for messaging and AI.  
- `messages/` – per-category messages copied from `resources/default_messages/`.

AI rules:

- Always use `core/user_data_handlers.py` and `core/user_data_validation.py` for reads and writes.  
- Treat preferences as flat; build nested structures in memory only.  
- New per-user files must be documented in both this section and section 2. User Data Model in
  `ARCHITECTURE.md`.

---

## 3. Data Handling Patterns

Preserve these patterns when generating or editing code:

- Centralized access  
  - Use helpers in `core/user_data_handlers.py`.  
  - Avoid direct `open()` on `data/users/...` in feature code.

- Validate before writing  
  - Use validators or models from `core/user_data_validation.py`.  
  - Log clear errors on invalid data.

- Template versus instance  
  - Templates: `resources/default_messages/`.  
  - Per-user instances: `data/users/{user_id}/messages/`.

- Legacy and migration  
  - Use explicit legacy branches and the logging pattern from section 7.
    Legacy Compatibility Logging Standard in `logs/LOGGING_GUIDE.md`.

If you need full rationale or examples, see section 3. Data Handling Patterns in `ARCHITECTURE.md`.

---

## 4. Key Modules and Responsibilities

Use this list to anchor AI changes to the right modules.

- `run_mhm.py` – UI entry point; launches the PySide6 admin app.  
- `run_headless_service.py` / `core/headless_service.py` – CLI and manager for the headless
  background service.  
- `core/service.py` – background service implementation and lifecycle.  
- `core/config.py` – configuration loader and validator (reads `.env` via python-dotenv).
  See section 5. Configuration (Environment Variables) in `logs/LOGGING_GUIDE.md`.  
- `core/logger.py` – logging configuration and component loggers. See section 2.
  Logging Architecture in `logs/LOGGING_GUIDE.md`.  
- `core/error_handling.py` – shared error handling decorators and integration with logging and
  basic metrics. See section 2. Architecture Overview in `core/ERROR_HANDLING_GUIDE.md`.  
- `core/user_data_handlers.py`, `core/user_data_validation.py` – user data entry points.  
- `communication/` – channel orchestrators and adapters that turn service events into messages on
  Discord, email, etc.  
- `tasks/` – task and reminder definitions used by schedulers.  
- `ui/ui_app_qt.py` – UI shell that wires dialogs to the service.

For more detailed descriptions, see section 4. Key Modules and Responsibilities in `ARCHITECTURE.md`.

---

## 5. UI Architecture and Naming Conventions

Follow the standard design-generated-implementation pattern:

- Designs: `.ui` files (for example `category_management_dialog.ui`).  
- Generated: Python modules from `.ui` (for example `category_management_dialog_pyqt.py`).  
- Implementations: dialog and widget classes (for example `ui/dialogs/category_management_dialog.py`).

AI rules:

- Do not edit generated code. Change behavior in dialogs, widgets, or `ui/ui_app_qt.py`.  
- Keep names aligned across design, generated, and implementation files.  
- For a new dialog or widget, follow the existing naming patterns and update `ARCHITECTURE.md`
  only if conventions change.

Details and examples live in section 5. UI Architecture and Naming Conventions in `ARCHITECTURE.md`.

---

## 6. Channel-Agnostic Architecture

When adding or modifying channel behavior:

- Put shared business logic in `core/` and `tasks/`.  
- Keep `communication/` modules focused on translating service events into channel-specific
  API calls and payloads.  
- UI components in `ui/` should act as another adapter layer, not a place for business rules.

Reference material:

- Section 6. Channel-Agnostic Architecture in `ARCHITECTURE.md`.  
- Section 1. Core Principle and section 2. Channel Layers and Boundaries in
  `communication/COMMUNICATION_GUIDE.md`.

---

## 7. Development Notes

- Use `run_mhm.py` for UI workflows and `run_headless_service.py` for headless workflows.  
- Use logs under `logs/` and error handling in `core/error_handling.py` to debug issues.
  See section 2. Logging Architecture in `logs/LOGGING_GUIDE.md` and section 2.
  Architecture Overview in `core/ERROR_HANDLING_GUIDE.md`.  
- Keep `ai_*` docs in sync with their human counterparts at the H2 level (use the documentation
  sync checker).  
- For any non-trivial refactor, read the relevant section in `ARCHITECTURE.md` before editing
  code. For overall workflow, see section 2. Standards and Templates in `DEVELOPMENT_WORKFLOW.md`.
