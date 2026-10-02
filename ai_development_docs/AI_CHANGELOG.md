# AI Changelog - Brief Summary for AI Context
> **File**: `ai_development_docs/AI_CHANGELOG.md`
> **Audience**: AI collaborators (Cursor, Codex, etc.)
> **Purpose**: Lightweight summary of recent changes
> **Style**: Concise, essential-only, scannable
> **See [development_docs/CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the full history**

## Overview
This file is a lightweight summary of recent changes for AI collaborators. It provides essential context without overwhelming detail. For the complete historical record, see [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md).

## How to Update This File
1. Add a new entry at the top summarising the change in 2-4 bullets.
2. Keep the title short: "YYYY-MM-DD - Brief Title **COMPLETED**".
3. Reference affected areas only when essential for decision-making.
4. Move older entries to archive\AI_CHANGELOG_ARCHIVE.md to stay within 10-15 total.
Template:
```markdown
### YYYY-MM-DD - Brief Title **COMPLETED**
- Key accomplishment in one sentence
- Extra critical detail if needed
- User impact or follow-up note
```
Guidelines:
- Keep entries concise
- Focus on what was accomplished and why it matters
- Limit entries to 1 per chat session. Exceptions may be made for multiple unrelated changes
- Maintain chronological order (most recent first)
- REMOVE OLDER ENTRIES when adding new ones to keep context short
- Target 10-15 recent entries maximum for optimal AI context window usage

## Recent Changes (Most Recent First)

### 2026-10-01 - Internal account username compatibility field retired **COMPLETED**
- Account identity now uses canonical UUIDs and optional contact identifiers; preferred names remain display-only.
- Removed the compatibility field from schemas, persistence, lookups, indexes, admin/UI flows, prompts, and test fixtures.
- Existing account files require the documented backup, migration, and index-rebuild step before normal reads.

### 2026-10-01 - Linux locks clean up after themselves **COMPLETED**
- Unix file locks remove their `.lock` sidecar on release, so user directories no longer keep `account.json.lock` and similar files.
- The frozen-clock lock test times only its body, so session cleanup cannot trip the 5-second limit.
- Unix lock tests restore the real `fcntl` module before reload, so a busy-lock stand-in cannot make later JSON reads return `{}`.

### 2026-09-30 - Delivery and reply state fail safely **COMPLETED**
- Channels accept only explicit success or `unconfirmed`; unexpected truthy results remain failed and retryable.
- Email reply context is updated transactionally and must be stored before SMTP starts. Save failures are no longer reported as success.
- IMAP duplicate and acknowledgement identity includes UIDVALIDITY, so a rebuilt mailbox cannot reuse an old UID as the same message.
- Windows JSON locks use a crash-safe OS byte lock with same-thread re-entry. Focused verification passed 201 tests; Ruff, Pyright, and diff checks passed.

### 2026-09-30 - Inbound mail stays attached to the right message **COMPLETED**
- Incoming mail uses stable IMAP UIDs, processes the oldest unread batch first, and retries one temporary mailbox disconnect without changing the application's global network timeout.
- A handled email is marked complete only after the server confirms `\\Seen`. If that acknowledgement fails, later polls retry it without sending the reply again.
- Encoded subjects retain every fragment and declared charset. Pyright is clean after correcting the IMAP call and scheduler positional-argument lookup.
- Focused email, message-processing, orchestrator, and scheduler suites passed; Ruff and diff checks passed.

### 2026-09-30 - Website delivery records stay exact and concurrent-safe **COMPLETED**
- Scheduled messages are copied to Home only after an accepted or unconfirmed handoff. Sent history and the website row share one exact delivery ID; repeated text no longer redirects reactions to the newest copy.
- JSON writes use unique temporary files and locked read-modify-write transactions. Failed sent-history writes return failure. A backed-up manual migration linked 83 legacy rows; seven check-ins and one task reminder remain intentionally non-reactable.
- Note requests allow 128 KiB end to end, enough for a valid 10,000-character Unicode description.
- All new transaction helpers use centralized error handling. Generated registries were refreshed, and the standard audit reports 100% error-handling coverage with no missing handlers, Phase 1/2 candidates, or registry watch items.

### 2026-09-30 - Unconfirmed mail is not sent twice, model failures stay with the call **COMPLETED**
- An SMTP timeout after the message body is written returns `unconfirmed`. Check-ins, reminders, and scheduled messages stop there instead of sending another copy. The body watch logs a failed write and raises it again. It stays off the error decorator so recovery cannot write the body twice.
- A dropped connection before the body is sent is still retried once.
- Each LM Studio call carries its own failure reason, including invalid JSON. Command fallbacks still log that reason.

### 2026-09-30 - Mail retries, command failures stay unparsed, empty inbox stays quiet **COMPLETED**
- A dropped SMTP connection is retried once with the same Message-ID. The sync bridge stays open long enough for that second attempt.
- When command interpretation fails, the reply is `ACTION: unknown` and the log includes why the model call failed. Chat still uses a conversational fallback.
- A missing website inbox loads as an empty inbox. It is no longer logged as a file error.

### 2026-09-30 - One-time jobs end, and recovery stays a leaf **COMPLETED**
- A finished scheduled message is removed. Cleanup and conflict checks read the user and category from the keyword arguments `schedule` actually stores.
- File recovery builds an empty chat file from a leaf module, so error handling and profile loading no longer import each other.
- Both helpers are in the function registry. The scheduler test checks each job callable before reading it, so Pyright is clean on that file.

### 2026-09-30 - Failed sends stay unsent **COMPLETED**
- A task reminder is marked sent only after the channel accepts it. A failed email is retried, and the retry reuses the same Message-ID.
- A scheduled check-in reports failure when the send fails, and the check-in flow is cleared so the retry can send it. The website copy is stored after the channel accepts the message.
- A failed scheduled send waits and retries a limited number of times, then the job is removed.

### 2026-09-29 - Failed emails stay failed **COMPLETED**
- A timed-out email now returns failure, so the scheduler can retry instead of marking the message sent.
- The send waits up to 30 seconds for the server to accept the body.
- The two empty chat files that were still plain lists are v2 envelopes. Chat loads only accept that envelope.

### 2026-09-29 - Prompts fit, guesses stay uncached, breakfast is allowed **COMPLETED**
- A long user message is shortened with the instructions so the local model stays inside its 2048-token window.
- A minute guess used when the model is down or silent is not saved. The next Home load can ask the model again.
- A hello or a task confirmation may mention breakfast. A reply is dropped only when it quotes a check-in rate the user did not ask about.
- The task-step tests now use a new user id on every run. Task files live under that id, so a later full suite was reading tasks left by the previous run.

### 2026-09-28 - Home loads first, greetings stay greetings **COMPLETED**
- Home shows the next task before minute estimates come back, so a slow or failed model call no longer holds the page.
- A hello is answered as a hello. Check-in statistics are only used when that question was asked, and only for the check-ins that included it.
- Chat prompts are shortened to fit the 2048-token local model. A failed rewrite keeps the real handler reply.

### 2026-09-28 - Function scan sees async routes **COMPLETED**
- Complexity and registry scans now include `async def`, score each function without its nested helpers, and match handler keywords on whole name parts.
- Website routes are methods on `WebGateway`. `create_web_app` only builds the app and registers them.
- The next `audit` refreshes `AI_PRIORITIES.md`. `tasks_api` is now visible to that ranking.
- Six nested helpers now have docstrings. The website mailer is typed so Pyright accepts `asyncio.to_thread`. Task and note route descriptions no longer use the word facade, so they are not compatibility shims.
- `handle_errors` now documents the inner `decorator` that wraps both sync functions and coroutines.

### 2026-09-28 - Small counts, lighter sleep, and low-energy focus **COMPLETED**
- A positive count that would round to zero is written as "under 100 steps", "under 5 active minutes", or "under 30 minutes of sleep". A real zero stays zero.
- "Shorter sleep" is a run of short nights. Restless nights of ordinary length say "lighter sleep" and leave the hours out.
- Home calls a task the easiest one only when it is about 15 minutes or less. A longer task due today says it will take a while.
- Today's check-in energy of 1 or 2 prefers a task around 15 minutes and stops boosting longer ones.

### 2026-09-28 - Wellness streaks, honest rounding, and a quiet inbox **COMPLETED**
- A wellness reply keeps a multi-day sleep or activity streak. The number beside it is the rounded middle of those days, written once as "about 5 hours".
- Sleep, steps, and active minutes round a .5 tie away from zero, so 50 steps is about 100, not 0.
- Opening website chat before any message exists no longer logs a missing inbox as an error. A failed read still returns an empty inbox.

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.

