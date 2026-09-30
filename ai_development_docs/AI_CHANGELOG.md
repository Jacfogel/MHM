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

### 2026-09-30 - Website copies follow an accepted send **COMPLETED**
- Scheduled messages and the Google Health reconnect notice are copied to the website inbox only after the channel accepts them, including an unconfirmed handoff.
- A failed send leaves Home unchanged, so a retry does not add a second copy.

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

### 2026-09-28 - Wellness replies and task identifier cleanup **COMPLETED**
- A wellness reply keeps one sleep note, one movement note, and one readiness note.
- The reply and the AI prompt share one phrase helper. The prompt still lists every note.
- Task name cleanup lives in one helper, and profile updates are no longer parsed inside the task extractor.

### 2026-09-28 - Website chat, smaller steps, and dialogs **COMPLETED**
- Suggest smaller steps, adding those steps, and separating a step now pass through the public site proxy. Before this, the tasks page showed "Page not found."
- Clicking the dimmed area around a dialog closes it. A click that starts inside the box leaves it open.
- A scheduled message in Talk to MHM has More like this and Not for me, the same as a Discord reaction. A conversation reply and a check-in do not.
- The registry lists those inbox helpers, a link to an existing website test is not reported as a missing module, and the reaction lookup no longer trips the inbox type warning.

### 2026-09-27 - Discord reactions replace message buttons **COMPLETED**
- Scheduled Discord messages no longer include More like this and Not for me buttons.
- A clearly positive reaction, such as a smile, heart, or celebration, still requests more messages like that one. A clearly negative reaction, such as a frown, anger, or a broken heart, still turns that message off. Ambiguous emoji are ignored.

### 2026-09-27 - Task steps stay with the parent **COMPLETED**
- Completing or deleting a task now completes or deletes its steps. Restoring that task can bring the finished steps back. A repeating task copies those step titles onto the next occurrence.
- Reminders name the oldest open step and say which task it is part of. Done finishes that step. Later and Skip still apply to the parent reminder.
- Home and the Tasks page can add a step you type. A step can become its own task.
- `break that into steps` and `break it down` start the same breakdown as `simplify`.
- Bulk task ranking uses the shared error handler, so a bad rank cannot stop the rest of the selection.

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.

