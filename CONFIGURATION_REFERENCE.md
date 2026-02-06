# Configuration Reference

> **File**: `CONFIGURATION_REFERENCE.md`  
> **Audience**: Developers and AI assistants working on MHM  
> **Purpose**: Canonical reference for `.env` / `core/config.py` settings, what they do, and common failure modes  
> **Style**: Reference-oriented, explicit, non-marketing

This is the single canonical description of configuration for MHM.

- Source of truth for available settings: `.env.example`
- Loader/normalization/validation: `core/config.py`
- If information elsewhere conflicts with this doc, fix the other doc(s) to point here.

---

## 1. How configuration is loaded

1. `core/config.py` loads environment variables via `python-dotenv` (`load_dotenv(...)`) and normalizes certain values (notably path-like variables).  
2. Settings are then read by the application and used to compute paths, logging behavior, channel credentials, and AI behavior.  
3. During tests, configuration is expected to redirect user/data paths to test-safe locations (see `MHM_TESTING` and related settings).

**Validation:** If you suspect config issues, prefer running configuration validation (where supported) instead of debugging "weird behavior" downstream.

---

## 2. Core paths and data roots

These variables control where MHM reads/writes local state.

- `BASE_DATA_DIR`  
  **Used for**: the base directory for `data/` storage (user directories, state, etc.).  
  **Breaks if wrong**: user data can't be found, schedules/messages appear "missing," or new data is created in an unexpected location.

- `USER_INFO_DIR_PATH`  
  **Used for**: the root folder where user directories live (for example `data/users`).  
  **Breaks if wrong**: users cannot be loaded; account creation may write to a different tree.

- `DEFAULT_MESSAGES_DIR_PATH`  
  **Used for**: location for default message templates.  
  **Breaks if wrong**: categories may appear empty or message initialization may fail.

---

## 3. Logging

MHM supports global logging settings and per-component log files.

### 3.1. General logging

- `LOG_LEVEL`  
  Controls the base logging verbosity (common values: `DEBUG`, `INFO`, `WARNING`, `ERROR`).

- `LOGS_DIR`, `LOG_BACKUP_DIR`, `LOG_ARCHIVE_DIR`  
  Base locations for logs, backups, and archives.

- `LOG_FILE_PATH`  
  Default main log output path.

- `LOG_MAX_BYTES`, `LOG_BACKUP_COUNT`, `LOG_COMPRESS_BACKUPS`, `DISABLE_LOG_ROTATION`  
  Rotation controls.

- `TEST_VERBOSE_LOGS`  
  Extra verbosity for tests.

### 3.2. Per-component log files

Each of these controls where a specific component writes logs:

- `LOG_MAIN_FILE`
- `LOG_DISCORD_FILE`
- `LOG_AI_FILE`
- `LOG_USER_ACTIVITY_FILE`
- `LOG_ERRORS_FILE`
- `LOG_COMMUNICATION_MANAGER_FILE`
- `LOG_EMAIL_FILE`
- `LOG_TELEGRAM_FILE`
- `LOG_UI_FILE`
- `LOG_FILE_OPS_FILE`
- `LOG_SCHEDULER_FILE`

**Breaks if wrong:** you may think "nothing is happening" because logs are going somewhere unexpected; or log file creation fails due to missing directories / permissions.

---

## 4. Email configuration

Email is supported primarily for outbound automated messages.

- `EMAIL_SMTP_USERNAME`
- `EMAIL_SMTP_PASSWORD`
- `EMAIL_SMTP_SERVER`
- `EMAIL_SMTP_PORT`
- `EMAIL_IMAP_SERVER`
- `EMAIL_IMAP_PORT`

**Breaks if wrong:** outbound email fails; errors should appear in the configured log files.

---

## 5. Channel credentials

### 5.1. Telegram (legacy/mostly removed)

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

If Telegram is being removed, these should remain unused/ignored in code.

### 5.2. Discord (primary channel)

- `DISCORD_BOT_TOKEN`
- `DISCORD_PUBLIC_KEY`
- `DISCORD_AUTO_NGROK`
- `DISCORD_WEBHOOK_PORT`

**Breaks if wrong:** Discord bot fails to start, slash command verification fails, webhook cannot bind, or messages do not send.

---

## 6. LM Studio and AI behavior

These settings control the optional local AI integration.

### 6.1. LM Studio connection

- `LM_STUDIO_BASE_URL`
- `LM_STUDIO_MODEL`
- `LM_STUDIO_API_KEY`

**Breaks if wrong:** AI calls fail or fall back (depending on implementation); the rest of MHM should continue functioning without AI.

### 6.2. Prompt and timeouts

- `AI_SYSTEM_PROMPT_PATH`
- `AI_USE_CUSTOM_PROMPT`

Timeout controls:
- `AI_TIMEOUT_SECONDS`
- `AI_CONNECTION_TEST_TIMEOUT`
- `AI_API_CALL_TIMEOUT`
- `AI_COMMAND_PARSING_TIMEOUT`
- `AI_PERSONALIZED_MESSAGE_TIMEOUT`
- `AI_CONTEXTUAL_RESPONSE_TIMEOUT`
- `AI_QUICK_RESPONSE_TIMEOUT`

Response size/shape controls:
- `AI_MAX_RESPONSE_LENGTH`
- `AI_MAX_RESPONSE_WORDS`
- `AI_MAX_RESPONSE_TOKENS`
- `AI_MIN_RESPONSE_LENGTH`

Sampling controls:
- `AI_CHAT_TEMPERATURE`
- `AI_COMMAND_TEMPERATURE`
- `AI_CLARIFICATION_TEMPERATURE`

**Breaks if wrong:** long stalls / timeouts, truncated responses, inconsistent parsing behavior, or overly-random command interpretation.

---

## 7. Caching and scheduler

- `CONTEXT_CACHE_TTL`
- `CONTEXT_CACHE_MAX_SIZE`
- `SCHEDULER_INTERVAL`
- `AUTO_CREATE_USER_DIRS`

**Breaks if wrong:** excessive API calls, stale context, delayed scheduling, or missing user directory creation.

---

## 8. Categories

- `CATEGORIES`

Defines the enabled categories list (comma-separated).  
**Breaks if wrong:** categories vanish, message loading does not match expectations, or UI lists are incomplete.

---

## 9. Backups and developer diagnostics

- `BACKUP_RETENTION_DAYS`
- `FILE_AUDIT_ENABLED`
- `FILE_AUDIT_DIRS`
- `FILE_AUDIT_POLL_INTERVAL`
- `FILE_AUDIT_IGNORE_DIRS`
- `FILE_AUDIT_STACK`

**Breaks if wrong:** backups are not retained as expected, file auditing becomes noisy, or auditing misses important directories.

---

## 10. Testing settings

- `MHM_TESTING`

This flag is used to indicate test mode. In test mode, the project is expected to:
- Redirect user/data writes to test directories
- Avoid touching real OS scheduler resources
- Keep logs and artifacts under `tests/`

**Breaks if wrong:** tests may touch real data, create real artifacts, or fail unpredictably due to path mismatches.

---

## 11. Updating configuration docs

- When adding a new setting:
  - Add it to `.env.example` with a clear comment header.
  - Add it to this doc with "used for" and "breaks if wrong" notes.
  - Remove any duplicate explanation elsewhere and replace with a link to this doc.


---

## 12. Context cache behavior (canonical semantics)

The context cache controls reuse of recently computed AI context to reduce recomputation and external API calls.

- `CONTEXT_CACHE_TTL`  
  **Used for**: maximum time (in seconds) a cached context entry remains valid.  
  **Behavior**:
  - Cached entries older than this value are treated as expired and recomputed.
  - Expiration is time-based only; cache entries are not refreshed automatically.
  **Breaks if wrong**:
  - Too high: stale context may be reused longer than intended.
  - Too low: excessive recomputation and AI calls.

- `CONTEXT_CACHE_MAX_SIZE`  
  **Used for**: upper bound on the number of cached context entries.  
  **Behavior**:
  - When the cache exceeds this size, older entries may be evicted (implementation-defined).
  **Breaks if wrong**:
  - Too low: cache provides little benefit.
  - Too high: unnecessary memory growth.

This cache is an optimization only. Correctness must not depend on cached context.

---

## 13. Scheduler timing semantics

- `SCHEDULER_INTERVAL`  
  **Used for**: base interval (in seconds) at which the scheduler loop wakes and evaluates pending work.  
  **Behavior**:
  - This value controls *polling frequency*, not execution guarantees.
  - Scheduled actions may run later than their nominal time depending on load.
  **Breaks if wrong**:
  - Too low: unnecessary CPU wakeups.
  - Too high: delayed message delivery or task execution.
