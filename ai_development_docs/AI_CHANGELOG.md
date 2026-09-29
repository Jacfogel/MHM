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

### 2026-09-26 - Home Today panel sits under chat **COMPLETED**
- The home page stacks Talk to MHM above Today. Next task and Check-in sit side by side under the chat, and stack on a narrow screen.
- Break it down asks for smaller steps and saves the ones you keep as subtasks. The original task title stays. Home then focuses on an open subtask.
- Discord Break it down, and simplify in Discord or email, adds those steps under the task instead of replacing the title. The breakdown helpers use the shared error handler, and the task-load tests store a valid task record.

### 2026-09-25 - File locks time out instead of hanging nightly tests **COMPLETED**
- Linux file-lock waits use a monotonic clock and re-enter when the same thread already holds the sidecar lock.
- A lock timeout no longer starts a network probe, so one stuck user-index write cannot run until the 300s test limit.

### 2026-09-25 - Smaller notebook slice for the model **COMPLETED**
- The model now gets recent note titles, pinned entries, and a short summary when a note has no title. Full note text stays out of that slice.
- Home shows a few recent titles under the capture box.
- The notebook plan now records groups as removed and the website notebook as a current surface.
- The notebook slice for the model should be recent titles, pinned entries, and a short summary when there is no title, so the prompt stays small. The code still sends the last 10 full entries.

### 2026-09-24 - Talk to MHM on the home page **COMPLETED**
- Home suggests what to focus on with a weighted roll. The model estimates minutes, and shorter tasks are more likely. Done, Later, and Break it down act on that task. The effort cache key uses the shared error handler, and the function registry includes those functions.
- Home chat shows website, Discord, and email messages in one timeline, oldest first, opens at the newest message, and starts with the last 48 hours. More loads the previous 48 hours. Personalized messages are check-ins, Google Health, and profile.
- Home uses one check-in action: start, continue, or you're checked in. Account deletion is on Account, under Your data, after typing DELETE. Inter and Nunito are self-hosted, so pages do not request fonts from Google. Email check-ins skip channel buttons when that channel has none.
- Home chat lists action names only, and leaves out actions for features that are turned off, so the prompt fits a 2048-token model. The notebook title field uses the rest of the create row. Ordinary website use is allowed 240 API calls per 10 minutes instead of 60. A website check-in saves when the check-in file is an empty list. Notebook replies no longer crash when an entry has no metadata, and the unused website inbox helper is gone. Insights says sleep length is not recorded yet instead of null hours, and Answer a check-in uses the same button as Home. Message creation keeps the message visible and tucks days and reminder windows behind More options. Every day and Any reminder window stay in step with the individual choices. Scheduled Discord messages use More like this and Not for me buttons instead of the bot adding both thumbs. Those buttons use the shared error handler. Account and Integrations are choices in the account side list. A scheduled check-in no longer replaces one that is still open, so an email reply is scored for the question in that email. Home chat shows the date and time on each message.
- The signed-in home page sends a message through `handle_user_message` as the `website` channel and shows the reply plus suggestion buttons.
- Your messages on Home use the preferred name when one is set. Account is the last page tab, and Log out is a dark button separate from the tabs. Extra home-page instructions are gone. Check-in is no longer a tab. Opening it from Home starts at the first question. The check-in page says MHM can send you one from Home. Discord linking is only on delivery settings. CPAP use is no longer a question template. Password and data download are on Account settings. The task list sits under the create form. Extra task and notebook instructions are gone. The notebook page no longer has groups. Notebook creation starts with the type and title. The notebook does not show who is signed in. Turned-off task reminders and check-ins link to those settings. The logo line stays on one line when the header has room. Check-in answer types are yes/no, 1 to 5, time, time pair, and text. A text answer is also saved as a check-in journal entry. Illegal check-in question counts reset to a legal minimum and maximum. With Sometimes questions, the maximum stays above the number of Always questions. Custom questions have no templates and no minimum or maximum fields. The public site proxy allows `/api/chat`. The website is an always-on extra delivery channel. Scheduled messages, check-ins, task reminders, and health notices are copied into the website inbox and shown on Home, while email or Discord delivery stays in place. Turning every support feature off no longer returns the account to setup. Insights shows only while check-ins are on. Google Health is on Integrations, opened from Account settings. Connected sign-ins, including Google, are on Integrations too. The account summary card is gone, and email is shown in Account settings. Home chat messages stay on the account across logout and the next login. The notebook create line sits beside the title field, the same way the task page does. Website chat helpers use the shared error handler, and the function registry includes them. Task and notebook files no longer store a group. AI actions, Discord create forms, task and notebook commands, quick notes, and the website notes API no longer accept one.
- An open check-in or task flow stays in charge. The typed transcript lasts for the browser visit and clears on logout.

### 2026-09-23 - Website check-ins, groups, and custom snooze **COMPLETED**
- Notebook groups are tabs again, and entries can be assigned or cleared from those groups.
- The Check-in page starts, answers, skips, and cancels a check-in in the browser. Task help accepts a typed reminder time.
- Talk to MHM on the website is planned in [PLANS.md](../development_docs/PLANS.md) Section 7.4 and is not built yet.
- Scheduled Discord messages no longer repeat themselves in an embed. The reaction flag only adds thumbs. The two check-in Pyright warnings are cleared.
- The first question starts on its own line after the opening, and later questions start on their own line after the transition phrase. The website answer box clears for the next question. Scale questions offer 1-5 and yes/no questions offer Yes and No, without a text box. Sleep times use dropdowns. Other typed questions still use the text box. Home shows an open check-in. Logging out drops an in-progress check-in. An idle check-in expires after the same two hours used by Discord and email. Check-in, Tasks, and Messages tabs show only when that feature is enabled. Tasks stay available, like the notebook. Home and Insights hide check-in actions when check-ins are off, and the Messages tab hides when messages are off.

### 2026-09-23 - Two-way email replies **COMPLETED**
- A reply keeps the new text, stays in the same email thread, and the inbox message is marked read only after MHM handles it.
- Replying to a check-in answers that check-in. Replying to a task reminder with done, later, skip, or simplify to a real smaller step applies to that task. The words after "to" become the new title.
- Behavior is specified in [email-reply-loop.md](../specs/email-reply-loop.md).
- The communication guide path, function registry, and Pyright check for this reply code are clean.

### 2026-09-22 - Planned SMS, Apple Health, and subscription scaffolds **COMPLETED**
- [PLANS.md](../development_docs/PLANS.md) Section 7 records SMS, Apple Health ingest, and a 30-day trial then monthly subscription as **PLANNED**. None of that behavior is implemented.
- SMS uses a paid provider. Apple Health is a phone push into the existing daily-summary path. The alpha account stays comped when billing exists.

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.

