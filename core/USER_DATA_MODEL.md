# User Data Model

> **File**: `core/USER_DATA_MODEL.md`  
> **Audience**: Developers and AI assistants working on MHM  
> **Purpose**: Canonical description of `data/users/{user_id}/...` layout, persisted artifacts, and validation expectations  
> **Style**: Contract-style, explicit guarantees only

This document defines the expected on-disk layout for per-user persisted state.

Key implementation references:
- `core/user_data_handlers.py` (centralized loader/saver API)
- `core/schemas.py` (schema validation and normalization rules)
- `core/config.py` (root path configuration: `BASE_DATA_DIR`, `USER_INFO_DIR_PATH`)

---

## 1. Root layout

User data is stored under:

- `data/users/{user_id}/...`

Where `{user_id}` is typically a UUID.

Example (typical user directory):

- `data/users/{user_id}/account.json`
- `data/users/{user_id}/preferences.json`
- `data/users/{user_id}/schedules.json`
- `data/users/{user_id}/tags.json`
- `data/users/{user_id}/user_context.json`
- `data/users/{user_id}/chat_interactions.json`
- `data/users/{user_id}/checkins.json`
- `data/users/{user_id}/messages/`
- `data/users/{user_id}/notebook/`
- `data/users/{user_id}/tasks/`

---

## 2. Canonical files and their roles

### 2.1. Top-level JSON files

- `account.json`  
  User identity and feature enablement flags (for example, automated messages, check-ins, task management).  
  Validation: `core/schemas.py` (account validators).

- `preferences.json`  
  User preferences (presentation, defaults, and other user-tunable settings).  
  Validation: `core/schemas.py` (preferences validators).

- `schedules.json`  
  Schedule periods / time windows and schedule-related persisted configuration.  
  Validation: `core/schemas.py` (schedule validators).

- `tags.json`  
  User tag taxonomy and tagging state (implementation-defined; treat as user-owned metadata).

- `user_context.json`  
  Persisted contextual/user-profile style data used by messaging/AI and other components.

- `chat_interactions.json`  
  Stored chat interaction history and metadata (used for analytics and/or AI context building depending on feature set).

- `checkins.json`  
  Check-in history, responses, and state.

### 2.2. Messages subtree

- `messages/motivational.json`  
  Category message definitions / templates (category-specific; the file names may vary by category list).

- `messages/word_of_the_day.json`  
  Example of a category-specific message file.

- `messages/sent_messages.json`  
  Tracking for messages sent (used to prevent spam/repeats and to support analytics).

### 2.3. Notebook subtree

- `notebook/entries.json`  
  Notebook entry storage.

### 2.4. Tasks subtree

- `tasks/active_tasks.json`
- `tasks/completed_tasks.json`
- `tasks/task_schedules.json`

These files represent the tasks framework state (open tasks, completed tasks, and scheduling metadata).

---

## 3. Access rules (developer contract)

### 3.1. Code must use centralized handlers

All reads/writes of user data should go through `core/user_data_handlers.py` (and its internal helpers), not ad-hoc `json.load`/`json.dump` in random modules.

Rationale:
- Centralizes validation and normalization
- Centralizes caching behavior
- Centralizes path computation and directory creation
- Makes future migrations possible without hunting down dozens of call sites

### 3.2. Validation and tolerance

`core/schemas.py` is designed to be tolerant of existing on-disk shapes:
- Unknown fields should generally be ignored (`extra="ignore"`) where configured.
- Fields may be normalized (for example, booleans coerced into `"enabled"` / `"disabled"` feature flags).
- Validation issues should be logged and recovered from where possible, rather than crashing.

**Do not** "tighten" schemas in a way that breaks existing real user data unless an explicit migration plan is in place.

---

## 4. Manual editing rules

Default posture: **do not edit user JSON files directly**.

Manual edits are allowed only when:
- You are doing recovery work on your own local data.
- You understand the expected shape for the file (check `core/schemas.py` and the loader code first).
- You make a backup of the user directory before editing.

If manual editing becomes a common need, that is a sign the UI/admin tools need additional repair/maintenance features.

---

## 5. Migration expectations

MHM uses file-based JSON persistence and will evolve over time.

Required expectations for new changes:
- New fields must be backward-compatible where possible.
- Removing/renaming fields must be accompanied by:
  - Tolerant reads for older shapes, and/or
  - A migration step/tool with clear documentation.

If you introduce new persisted files:
- Put them under the existing user root or an appropriate subtree (`messages/`, `tasks/`, `notebook/`).
- Add an entry to this doc describing the new file and its purpose.
- Ensure tests run in isolated test data directories (never write to real user data during tests).

---

## 6. Test isolation

During tests, user data must be redirected into test-controlled directories (for example under `tests/data/` or `tests/data/tmp/`).

If a test touches real `data/users/`, it is a defect.

See:
- [TESTING_GUIDE.md](tests/TESTING_GUIDE.md)
- `core/config.py` (test-mode redirection controls)

---

## 7. Quick "where is X stored?" map

- Feature enablement -> `account.json`
- User preferences -> `preferences.json`
- Schedules/time windows -> `schedules.json`
- Sent-message tracking -> `messages/sent_messages.json`
- Check-ins -> `checkins.json`
- Tasks -> `tasks/*.json`
- Notebook entries -> `notebook/entries.json`
- AI/chat history (if enabled) -> `chat_interactions.json` and/or `user_context.json` (implementation-defined)
## 8. Backup scope expectations

Backups are expected to include the full per-user directory tree under `data/users/{user_id}/`, including:

- All top-level JSON files
- All category message files under `messages/`
- Notebook and task subtrees

No guarantees are made about backup *frequency* or *retention* here; those are controlled by configuration and operational tooling.

This section defines **scope only**, not scheduling or retention behavior.

---

## 9. AI access expectations

AI-related components are expected to:

- Read user data via `core/user_data_handlers.py`
- Write only to files defined in this model
- Avoid creating ad-hoc files outside documented subtrees

AI components must not assume exclusive access to user files and must tolerate concurrent updates.

---
