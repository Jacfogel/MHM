# User Data Model

> **File**: `core/USER_DATA_MODEL.md`  
> **Audience**: Developers and AI assistants working on MHM  
> **Purpose**: Canonical description of `data/users/{user_id}/...` layout, persisted artifacts, and validation expectations  
> **Style**: Contract-style, explicit guarantees only

This document defines the expected on-disk layout for per-user persisted state.

Key implementation references:
- `storage/user_data_registry.py`, `storage/user_data_read.py`, `storage/user_data_write.py` (centralized loader/saver API for top-level user files; section updates live in `storage/user_data_write.py`)
- `storage/user_item_storage.py` (shared helpers for user-scoped subdir JSON: notebook, tasks, future events)
- `core/schemas.py` (tolerant account/preferences/schedules validation on the read/save path)
- `storage/user_data_v2_base.py` / `storage/user_data_v2_envelopes.py` (strict v2 primitives and envelopes for versioned JSON files)
- `core/config.py` (root path configuration: `BASE_DATA_DIR`, `USER_INFO_DIR_PATH`)

---

## 0. User data and schedule module map

One line per core module (plus related packages). **Read here first** when you are lost in filenames.

| Module | Read this path when you need... |
|--------|-------------------------------|
| `core/file_operations.py` | Generic JSON load/save, user file path helpers, creating default user files on disk. |
| `storage/user_item_storage.py` | Paths and load/save for user **subdirs** (`notebook/`, `tasks/`) without domain rules. |
| `storage/user_data_registry.py` | Loader table, caches, default load/save for `account`, `preferences`, `context`, `schedules`. |
| `storage/user_data_read.py` | `get_user_data`, cache clearing, ID helpers on the read path. |
| `storage/user_data_write.py` | `save_user_data`, transactions, and **centralised** `update_user_*` helpers (single save pipeline). |
| `storage/user_data_validation.py` | Primitive checks (email, phone, time formats) and rules used by handlers. |
| `core/schemas.py` | **Tolerant** in-memory normalizer for account/preferences/schedules after v2 unwrap (coerce/normalize; `extra` may allow/ignore). |
| `core/profile_v2_schemas.py` | **Strict** v2 envelope models for account, preferences, schedules (`categories` wrapper), context, tags, chat interactions. |
| `core/profile_v2_io.py` | Unwrap v2 on-disk envelopes to in-memory shapes; always wrap on save. |
| `storage/user_data_v2_base.py` | **Strict** shared v2 item layer: `SCHEMA_VERSION`, `BaseItemModel`, `generate_short_id` (dependency **leaf**: no `tasks/` or `notebook/` imports). |
| `storage/user_data_v2_envelopes.py` | **Strict** v2 **envelopes** for check-ins, messages, deliveries, and profile/tags/chat; `validate_v2_document` orchestration. |
| `tasks/task_schemas.py`, `tasks/task_validation.py` | Task v2 disk models and `validate_tasks_v2_document`. |
| `notebook/notebook_schemas.py`, `notebook/notebook_validation.py` | Notebook v2 disk models and `validate_notebook_v2_document`. |
| `core/message_management.py` | User message **categories**, template files, deliveries, archive behaviour. |
| `core/schedule_runtime.py` | **Runtime** schedule periods (active windows, caches, manipulation against live `get_user_data`). |
| `core/schedule_document_defaults.py` | **On-disk** default period shapes and migrations for `schedules.json`. |
| `core/schedule_utilities.py` | Small shared schedule helpers (active period lists) without user I/O. |
| `storage/user_data_operations.py` | **Ops/admin**: `UserDataManager` class - backup, export, user index, analytics summaries (not the hot read/write path). |
| `core/user_management.py` | User **lifecycle**: list users, create user, categories. |
| `storage/user_data_presets.py` | Static preset options (e.g. form dropdowns). |
| `core/tags.py` | Shared tag normalization used by notebook and elsewhere. |
| `core/response_tracking.py` | Check-in and chat interaction persistence and queries. |
| `core/checkin_dynamic_manager.py` | Bundled default check-in **prompt** JSON from `resources/`, not per-user `checkins.json`. |

### 0.0. "Leaf" and two validation styles

**Leaf module** (informal graph term): a module near the bottom of the import graph that does **not** pull in heavier neighbours-so other modules can safely import it first. Example: `user_data_v2_base` must stay free of `tasks` and `notebook` imports so `notebook_schemas` and `user_data_v2_envelopes` can share `BaseItemModel` without circular imports.

**Two validation layers (intentional):**

1. **`schemas.py` (+ `storage/user_data_validation.py`)** - **tolerant / ergonomic** validation for **in-memory** profile shapes after v2 unwrap. Loaders apply these validators to unwrapped data from ``get_user_data`` / ``save_user_data``.

2. **`profile_v2_schemas` + `user_data_v2_base` + `user_data_v2_envelopes` + domain validators** - **strict** validation for **versioned v2 on-disk documents**: tasks, notebook, check-ins, messages, deliveries, and profile/tags/chat files. Pydantic `extra="forbid"`, canonical timestamps; `validate_v2_document` for tooling and recovery.

**Profile v2 on disk:** Runtime load expects v2 envelopes only. Saves always emit v2 via `core/profile_v2_io.py`.

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

### 2.0. Top-level JSON files

- `account.json`  
  User identity and feature enablement flags (for example, automated messages, check-ins, task management).  
  Validation: tolerant `core/schemas.py` in memory; strict `core/profile_v2_schemas.py` on disk.

- `preferences.json`  
  User preferences (presentation, defaults, and other user-tunable settings).  
  Validation: tolerant `core/schemas.py` in memory; strict v2 envelope on disk.  
  **Natural-language phrase defaults** (optional, under `natural_language_defaults` at the preferences root): `tonight_start_time` (default `18:00`), `after_work_school_time` (default `17:00`, used for both "after work" and "after school"), `time_of_day_defaults` (`morning`, `afternoon`, `evening`, `night`), and `weekend_this_week_means_coming_week` (boolean, default `true` for Sat/Sun "this week" parsing). Shipped defaults live in [`resources/default_natural_language_defaults.json`](../resources/default_natural_language_defaults.json); loaded by `core/natural_language_defaults.py`. Used by task due-date parsing and other phrase interpretation. View or change from Discord (`show phrase settings`, `set tonight to 8pm`) or admin **Phrase Settings** dialog.

- `schedules.json`  
  Schedule periods / time windows and schedule-related persisted configuration.  
  Validation: tolerant `core/schemas.py` + `core/schedule_document_defaults.py` in memory; v2 on-disk shape uses a `categories` map wrapper.

- `tags.json`  
  User tag taxonomy (`core/tags.py`). v2 envelope on disk.

- `user_context.json`  
  Persisted contextual/user-profile style data used by messaging/AI and other components.  
  Validation: `storage/user_data_validation.py` for partial updates; strict v2 envelope on disk.

- `chat_interactions.json`  
  Stored chat interaction history (`core/response_tracking.py`). v2 `interactions[]` envelope on disk.

- `checkins.json`  
  Check-in history, responses, and state.

### 2.1. Messages subtree

- `messages/motivational.json`  
  Category message definitions / templates (category-specific; the file names may vary by category list).

- `messages/word_of_the_day.json`  
  Example of a category-specific message file.

- `messages/sent_messages.json`  
  Tracking for messages sent (used to prevent spam/repeats and to support analytics).  
  **Retention**: Historical v1 `messages[]` records older than **365 days** (UTC cutoff; see `core.message_management.archive_old_messages`) are moved into `messages/archives/sent_messages_archive_<timestamp>.json` when scheduled cleanup runs. Current v2 `deliveries[]` retention/archiving still needs a v2-native cleanup pass; existing archive files may remain in the historical v1 archive format.

### 2.2. Notebook subtree

- `notebook/entries.json`  
  Notebook entry storage.

### 2.3. Tasks subtree

- `tasks/tasks.json`

This file is the canonical v2 task collection. Active/completed state lives in each task's `status` and `completion`, not in separate files. Historical v1 files (`tasks/active_tasks.json`, `tasks/completed_tasks.json`, `tasks/task_schedules.json`) were replaced for migrated users and should not be recreated for migrated data. Access via `tasks.task_data_handlers` (which uses `storage.user_item_storage`). To add a new item type (e.g. events), use the same pattern: `ensure_user_subdir`, `load_user_json_file`, `save_user_json_file` from `storage.user_item_storage`, and `is_valid_user_id` from `storage.user_data_validation` (non-empty string, max length 100, alphanumeric plus `_` and `-` only, aligned with command-handler validation).

### 2.4. Health subtree (Google Health integration)

- `health/google_health_auth.json` - OAuth tokens and refresh metadata (**sensitive**; never log token values; optional Fernet encryption via `GOOGLE_HEALTH_TOKEN_ENCRYPTION_KEY`, field `tokens_encrypted`).
- `health/daily_summaries.json` - v2 collection of normalized daily raw metrics (sleep, steps, HR/HRV).
- `health/health_signals.json` - v2 collection of derived wellness signals and `message_guidance` tokens.
- `health/sync_state.json` - last sync timestamps, error counts, baseline metadata, `last_scheduled_slot` (per-user timezone slot dedupe), `reconnect_notice_sent`.

Access via `integrations.google_health.data_handlers` (uses `storage.user_item_storage`). Feature flag: `account.json` -> `features.google_health` (`enabled` | `disabled` | `paused`). Delete all local health data with `delete_user_health_data()` in the same module.

### 2.5. Canonical v2 item model

Shared v2 item primitives live in `storage.user_data_v2_base`. Task and notebook/journal
persistence models (`TaskV2Model`, `TaskCollectionV2Model`, `NotebookV2Model`,
`NotebookCollectionV2Model`) live in `tasks.task_schemas` and `notebook.notebook_schemas`.
Check-in, message template, and delivery models remain in `storage.user_data_v2_envelopes`.
`storage.user_data_v2_envelopes.validate_v2_document` validates against Pydantic models with `extra="forbid"`, so
any field that is not part of the v2 schema (including old v1-only keys) is rejected
with a normal validation error-there is no separate v1 key denylist.

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

Persisted `short_id` values use `storage.user_data_v2_base.generate_short_id` (prefix + hex fragment, **no hyphen**), e.g. tasks `t...`, notes `n...`, lists `l...`, journal entries `j...`. User-facing confirmations and entry references should use this canonical form; dashed `n-...` / `kind[0]-uuid6` display is obsolete.

Canonical v2 files:

- `tasks/tasks.json`: versioned task collection with `tasks[]`. Active/completed state lives in each task's `status` and `completion`, not in separate storage files.
- `notebook/entries.json`: versioned notebook collection with `entries[]` containing `note`, `list`, and `journal_entry` records. Notes and journals use `description` for their main text. Lists preserve list items in `items`.
- `checkins.json`: versioned check-in collection with `checkins[]`. Individual answers live under `responses`, and `questions_asked` records the prompt set used at submission time.
- `messages/<category>.json`: versioned message template collection with `messages[]`, `text`, `active`, and nested `schedule`.
- `messages/sent_messages.json`: versioned delivery collection with `deliveries[]`, distinct from reusable templates.

**Migration tooling:** There is **no** shipped migration or verification CLI under `scripts/` for user data. The tree is v2-native. Recover stale trees from backups or project history; validate in code with `storage.user_data_v2_envelopes.validate_v2_document` (or hand-fix using Section 2.6). Do not expect an in-repo one-click migrator.

### 2.6. Schema validation (v2)

`storage.user_data_v2_envelopes.validate_v2_document` dispatches to domain validators for tasks and notebook files (`tasks.task_validation.validate_tasks_v2_document`, `notebook.notebook_validation.validate_notebook_v2_document`) and runs collection models for check-ins, templates, and deliveries. Unknown or misspelled keys fail validation like any other schema error. For allowed fields and shapes, use Section 2.5 and 2.7.

### 2.7. Runtime contract (v2-native)

On-disk user data and bundled message resources are **v2**. Runtime code treats v2 shapes as canonical: tasks in `tasks/tasks.json`, notebook entries with `description` / `journal_entry`, check-ins in `checkins.json` with `responses` and `submitted_at`, templates with `id`/`text`/`schedule`, and deliveries with `deliveries[]` (`message_template_id`, `sent_text`, `sent_at`, `status`). Check-in **writes** and **reads** require the v2 envelope (`schema_version: 2`, `checkins[]`). Legacy bare arrays or other non-v2 shapes are skipped on read and rejected on append (see logs). There is no in-repo check-in repair helper: restore `checkins.json` from backup or hand-edit JSON to this section's shape, run `validate_v2_document('checkins', data)`, then `core.file_operations.save_json_data`. New users get an empty v2 file from `core.file_operations._create_user_files__checkins_file`. Missing or corrupted `checkins.json` recreated by centralized recovery (`core.error_handling` file-not-found / JSON-decode strategies) uses that same empty v2 envelope, not a bare list. Broader legacy cleanup tracking (unrelated v1 terms, docs, and dev-tools mirrors) remains in `development_tools/config/jsons/DEPRECATION_INVENTORY.json` and [AI_LEGACY_COMPATIBILITY_GUIDE.md](../ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md).

---

## 3. Access rules (developer contract)

### 3.0. Code must use centralized handlers

All reads/writes of user data should go through `storage/user_data_registry.py`, `storage/user_data_read.py`, and `storage/user_data_write.py` (and their internal helpers), not ad-hoc `json.load`/`json.dump` in random modules.

Rationale:
- Centralizes validation and normalization
- Centralizes caching behavior
- Centralizes path computation and directory creation
- Makes future migrations possible without hunting down dozens of call sites

### 3.1. Validation and tolerance

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

- Read user data via `storage/user_data_read.py` and related storage user data modules
- Write only to files defined in this model
- Avoid creating ad-hoc files outside documented subtrees

AI components must not assume exclusive access to user files and must tolerate concurrent updates.

---
