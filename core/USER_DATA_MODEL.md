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

Canonical v2 files:

- `tasks/tasks.json`: versioned task collection with `tasks[]`. Active/completed state lives in each task's `status` and `completion`, not in separate storage files.
- `notebook/entries.json`: versioned notebook collection with `entries[]` containing `note`, `list`, and `journal_entry` records. Notes and journals use `description` for their main text. Lists preserve list items in `items`.
- `checkins.json`: versioned check-in collection with `checkins[]`. Individual answers live under `responses`, and `questions_asked` records the prompt set used at submission time.
- `messages/<category>.json`: versioned message template collection with `messages[]`, `text`, `active`, and nested `schedule`.
- `messages/sent_messages.json`: versioned delivery collection with `deliveries[]`, distinct from reusable templates.

The one-time migration implementation entry point is `scripts.user_data_migration.migrate_user_data_root`; the local operator CLI remains `scripts/migrate_user_data_v2.py`. Use dry-run mode first, then `--write` only after reviewing the generated report. Write mode stores migration backups under the configured backups directory (`data/backups` by default), removes v1 task split files replaced by `tasks/tasks.json`, and only persists a migration report when `--save-report` is provided.

### 2.6. V2 migration field mapping

The v2 migration handled old fields using one of four outcomes: direct migration, transformation into a canonical field/nested shape, drop after replacement, or `metadata` preservation for still-useful data that could not be safely mapped.

Task mappings:

- `tasks/active_tasks.json`, `tasks/completed_tasks.json`, and `tasks/task_schedules.json` were consolidated into `tasks/tasks.json`.
- `task_id` became `id`, and `short_id` was generated from the canonical ID.
- `completed`, `completed_at`, and `completion_notes` became `status` and `completion`.
- `due_date` and `due_time` became `due.date` and `due.time`.
- `reminder_periods` and `quick_reminders` became `reminders[]`.
- `recurrence_pattern`, `recurrence_interval`, `repeat_after_completion`, and `next_due_date` became `recurrence`.
- `last_updated` became `updated_at`.
- Priority-like legacy `category` values (`low`, `medium`, `high`, `urgent`, `critical`) became `priority` when no explicit priority existed.

Notebook mappings:

- `notebook/entries.json` remains the destination file, with `schema_version: 2`.
- Note/list IDs, titles, tags, groups, pins, and timestamps were preserved where valid.
- `kind: "journal"` became `kind: "journal_entry"`.
- `body` became `description`.
- `archived` became `status` and `archived_at`.
- List entries preserve list-specific `items`.

Check-in mappings:

- Bare `checkins.json` arrays became `{"schema_version": 2, "updated_at": "...", "checkins": [...]}`.
- `timestamp` became `submitted_at`.
- Flat answer fields such as `mood`, `energy`, `ate_breakfast`, and `brushed_teeth` moved under `responses`.
- `questions_asked`, existing `responses`, source/link/timestamp fields, and metadata were preserved where present.

Message mappings:

- `messages/<category>.json` files became versioned template collections with category, `updated_at`, and `messages[]`.
- Template `message_id` became `id`; `message` became `text`; `days` and `time_periods` became `schedule.days` and `schedule.periods`.
- `messages/sent_messages.json` became a versioned delivery collection with `deliveries[]`.
- Delivery `message_id` became `message_template_id`; `message` became `sent_text`; `delivery_status` became `status`; `timestamp` became `sent_at`; missing delivery IDs were generated.

Files outside this migration slice (`account.json`, `preferences.json`, `schedules.json`, `tags.json`, `user_context.json`, and `chat_interactions.json`) remain in their existing model unless a later migration explicitly scopes them in.

### 2.7. Runtime contract (v2-native)

On-disk user data and bundled message resources are **v2**. Runtime code treats v2 shapes as canonical: tasks in `tasks/tasks.json`, notebook entries with `description` / `journal_entry`, check-ins in `checkins.json` with `responses` and `submitted_at`, templates with `id`/`text`/`schedule`, and deliveries with `deliveries[]` (`message_template_id`, `sent_text`, `sent_at`, `status`). New check-ins are **always** persisted under the v2 envelope (`schema_version: 2`, `checkins[]`); if a legacy bare array file is still present, the next write migrates those rows into `checkins[]` before appending.

Reads may still tolerate a bare array in `checkins.json` only long enough for that first write to normalize the file-operators should rely on migration tooling or normal app usage rather than hand-editing list-shaped check-ins. Broader legacy cleanup tracking (unrelated v1 terms, docs, and dev-tools mirrors) remains in `development_tools/config/jsons/DEPRECATION_INVENTORY.json` and [AI_LEGACY_COMPATIBILITY_GUIDE.md](ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md).

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

- Read user data via `core/user_data_read.py` and related core user data modules
- Write only to files defined in this model
- Avoid creating ad-hoc files outside documented subtrees

AI components must not assume exclusive access to user files and must tolerate concurrent updates.

---
