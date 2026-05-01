# User Data Model

> **File**: `core/USER_DATA_MODEL.md`  
> **Audience**: Developers and AI assistants working on MHM  
> **Purpose**: Canonical description of `data/users/{user_id}/...` layout, persisted artifacts, and validation expectations  
> **Style**: Contract-style, explicit guarantees only

This document defines the expected on-disk layout for per-user persisted state.

Key implementation references:
- `core/user_data_registry.py`, `core/user_data_read.py`, `core/user_data_write.py` (centralized loader/saver API for top-level user files)
- `core/user_item_storage.py` (shared helpers for user-scoped subdir JSON: notebook, tasks, future events)
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
  **Retention**: Historical v1 `messages[]` records older than **365 days** (UTC cutoff; see `core.message_management.archive_old_messages`) are moved into `messages/archives/sent_messages_archive_<timestamp>.json` when scheduled cleanup runs. Current v2 `deliveries[]` retention/archiving still needs a v2-native cleanup pass; existing archive files may remain in the historical v1 archive format.

### 2.3. Notebook subtree

- `notebook/entries.json`  
  Notebook entry storage.

### 2.4. Tasks subtree

- `tasks/tasks.json`

This file is the canonical v2 task collection. Active/completed state lives in each task's `status` and `completion`, not in separate files. Historical v1 files (`tasks/active_tasks.json`, `tasks/completed_tasks.json`, `tasks/task_schedules.json`) were replaced for migrated users and should not be recreated for migrated data. Access via `tasks.task_data_handlers` (which uses `core.user_item_storage`). To add a new item type (e.g. events), use the same pattern: `ensure_user_subdir`, `load_user_json_file`, `save_user_json_file` from `core.user_item_storage`, and `is_valid_user_id` from `core.user_data_validation` (non-empty string, max length 100, alphanumeric plus `_` and `-` only, aligned with command-handler validation).

### 2.5. Canonical v2 item model

The v2 user-data migration defines canonical JSON structures in `core.user_data_v2`.
The migration target is intentionally stricter than the current runtime files:
obsolete v1 field names are transformed by migration tooling and rejected by v2
validation.

Shared v2 item fields:

- `id`: stable internal identifier, usually a UUID string.
- `short_id`: mobile-friendly no-dash identifier derived from `id`, with a kind prefix such as `t`, `n`, `l`, `j`, `m`, `d`, or `c`.
- `kind`: canonical item kind, such as `task`, `note`, `list`, or `journal_entry`.
- `title`, `description`, `category`, `group`, `tags`, `status`.
- `source`: object describing best-known origin (`system`, `channel`, `actor`, optional `migration`).
- `linked_item_ids`: list of related canonical item IDs.
- `created_at`, `updated_at`, `archived_at`, `deleted_at`: canonical timestamps from `core.time_utilities`; nullable timestamps use `null` when absent.
- `metadata`: only for still-useful values that cannot be safely mapped to canonical fields.

**Task field semantics (category vs priority)**

For `kind: "task"` records in `tasks/tasks.json`:

- **`priority`**: urgency/importance only. Allowed values are the `VALID_PRIORITIES` set in `tasks/task_schemas.py` (`low`, `medium`, `high`, `urgent`, `critical`). Runtime validation rejects unknown values (defaulting where appropriate).
- **`category`**: broad semantic domain (examples: `health`, `home`, `family`, `personal`). Free string; avoid storing priority words here. Set `priority` explicitly on new data (older v1 upgrades once mapped priority-like `category` values into `priority` when `priority` was absent).
- **`group`**: user-facing organizational bucket (free string).
- **`tags`**: flexible multi-label metadata (`list[str]`).
- **Convention**: avoid copying the same token into `category`, `group`, and `tags` unless you mean three different roles; this is a modeling convention, not a runtime constraint.

**Short IDs (no dash)**

Persisted `short_id` values use `core.user_data_v2.generate_short_id` (prefix + hex fragment, **no hyphen**), e.g. tasks `t...`, notes `n...`, lists `l...`, journal entries `j...`. User-facing confirmations and entry references should use this canonical form; dashed `n-...` / `kind[0]-uuid6` display is obsolete.

Canonical v2 files:

- `tasks/tasks.json`: versioned task collection with `tasks[]`. Active/completed state lives in each task's `status` and `completion`, not in separate storage files.
- `notebook/entries.json`: versioned notebook collection with `entries[]` containing `note`, `list`, and `journal_entry` records. Notes and journals use `description` for their main text. Lists preserve list items in `items`.
- `checkins.json`: versioned check-in collection with `checkins[]`. Individual answers live under `responses`, and `questions_asked` records the prompt set used at submission time.
- `messages/<category>.json`: versioned message template collection with `messages[]`, `text`, `active`, and nested `schedule`.
- `messages/sent_messages.json`: versioned delivery collection with `deliveries[]`, distinct from reusable templates.

**Migration tooling:** There is **no** shipped migration or verification CLI under `scripts/` for user data. The tree is v2-native. Recover stale trees from backups or project history; validate in code with `core.user_data_v2.validate_v2_document` (or hand-fix using Section 2.6). Do not expect an in-repo one-click migrator.

### 2.6. Legacy field rejection (v2 validation)

`core.user_data_v2.validate_v2_document` rejects known v1 field names that must not appear in v2 documents (for example `task_id` on tasks, `body` on notebook rows, top-level `timestamp` on check-ins, template `message_id` / flat `days`). The authoritative set is `FORBIDDEN_V1_FIELD_NAMES_BY_DOCUMENT` in [`core/user_data_v2.py`](user_data_v2.py). Use that list when hand-fixing stale JSON; for shape reference, see Section 2.7 and archived changelog entries from 2026-04 and earlier.

### 2.7. Runtime contract (v2-native)

On-disk user data and bundled message resources are **v2**. Runtime code treats v2 shapes as canonical: tasks in `tasks/tasks.json`, notebook entries with `description` / `journal_entry`, check-ins in `checkins.json` with `responses` and `submitted_at`, templates with `id`/`text`/`schedule`, and deliveries with `deliveries[]` (`message_template_id`, `sent_text`, `sent_at`, `status`). Check-in **writes** and **reads** require the v2 envelope (`schema_version: 2`, `checkins[]`). Legacy bare arrays or other non-v2 shapes are skipped on read and rejected on append (see logs). To fix a bad file offline: back it up, load JSON, pass it through `core.response_tracking.normalize_checkins_envelope_for_repair`, run `validate_v2_document('checkins', envelope)`, then write with `core.file_operations.save_json_data`. New users get an empty v2 file from `core.file_operations._create_user_files__checkins_file`. Missing or corrupted `checkins.json` recreated by centralized recovery (`core.error_handling` file-not-found / JSON-decode strategies) uses that same empty v2 envelope, not a bare list. Broader legacy cleanup tracking (unrelated v1 terms, docs, and dev-tools mirrors) remains in `development_tools/config/jsons/DEPRECATION_INVENTORY.json` and [AI_LEGACY_COMPATIBILITY_GUIDE.md](../ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md).

---

## 3. Access rules (developer contract)

### 3.1. Code must use centralized handlers

All reads/writes of user data should go through `core/user_data_registry.py`, `core/user_data_read.py`, and `core/user_data_write.py` (and their internal helpers), not ad-hoc `json.load`/`json.dump` in random modules.

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
- [TESTING_GUIDE.md](../tests/TESTING_GUIDE.md)
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

- Read user data via `core/user_data_read.py` and related core user data modules
- Write only to files defined in this model
- Avoid creating ad-hoc files outside documented subtrees

AI components must not assume exclusive access to user files and must tolerate concurrent updates.

---
