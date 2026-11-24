# Changelog Brief
> **File**: `development_docs/CHANGELOG_BRIEF.md`
> **Audience**: Developers and AI collaborators
> **Purpose**: Lightweight summary of recent changes
> **Style**: Concise, essential-only, scannable
> **See [CHANGELOG_DETAIL.md](CHANGELOG_DETAIL.md) for the full history**

## Overview

This file is a lightweight summary of recent changes for all contributors. It provides essential context without overwhelming detail. For the complete historical record, see [CHANGELOG_DETAIL.md](CHANGELOG_DETAIL.md).

## How to Update This File
1. Add a new entry at the top summarising the change in 1-3 bullets.
2. Keep the title short: "YYYY-MM-DD - Brief Title **COMPLETED**".
3. Reference affected areas only when essential for decision-making.
4. Move older entries to [CHANGELOG_BRIEF_ARCHIVE.md](changelog_history/CHANGELOG_BRIEF_ARCHIVE.md) to stay within 10 total.
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
- Limit entries to 1 per chat session; update the existing session entry as work progresses.
- Maintain chronological order (most recent first)
- REMOVE OLDER ENTRIES when adding new ones to keep context short
- Target 10 recent entries maximum for optimal AI context window usage

## Recent Changes (Most Recent First)

### 2026-11-24 - Repair nightly test classification **COMPLETED**
- Added the missing behavior and communication markers to the standalone help regression test that failed the nightly suite's category policy guard.

### 2026-11-23 - Correct social signup account selection **COMPLETED**
- Prevented Google/Facebook signup and login from linking to an unrelated signed-in browser account; Connect now requires explicit intent and a live session.
- Passed 129 account-service, website-page, and browser/proxy checks, published the website, restarted the gateway, and verified live signup/Connect responses. Any previously incorrect saved link still needs identification.

### 2026-11-23 - Clearer website delivery choices **COMPLETED**
- Corrected the Tier 3 website test that still expected the old free-trial wording.
- Made Messages manage categories and delivery as well as editable default and custom messages, preserving libraries when paused.
- Kept the Home chat welcome after replies and moved the full command list out of basic help into the existing commands request.
- Simplified signup copy and delivery cards, labeled the phone plan SMS, and gated phone enrollment on paid access.
- Added a profile-completion reminder under personalized messages, Email trial wording and made setup progress show feature details only from Features onward, with no Free trial step for SMS/WhatsApp.


### 2026-11-23 - Resume interrupted account signup **COMPLETED**
- Corrected two Tier 3 test failures and the changelog guide link; both affected Python files pass (82 tests).
- Moved channel connection and paid signup to a subsequent Connect step; phone fields accept drafts and validate/normalize international numbers.
- First-run delivery now uses responsive option cards, highlights Discord as recommended, and clarifies trial pricing and included Email/Discord.
- Retrying account creation now emails a sign-in code for an existing active account, preserving its password and setup progress.

### 2026-11-23 - Setup delivery and paid phone enrollment **COMPLETED**
- Audit follow-up corrected the outdated website assertion and five billing-test type findings; all 44 affected tests passed and full-project Pyright is clean.
- Fixed setup delivery layout, conditional connection controls, recovery errors, and paid phone checkout returning to verification.

### 2026-11-21 - Direct Meta WhatsApp channel and separate plan **COMPLETED**

- Added direct Meta Cloud API delivery, signed webhook verification, independent WhatsApp phone consent/LINK proof, STOP/START, durable inbound deduplication, delivery/read receipts, shared task/check-in reply routing, and website/desktop channel selection.
- Added a separate $20 CAD/month WhatsApp plan and Stripe price configuration; SMS and WhatsApp require their own active live-paid tier. Outside the reply window, an approved generic notification invites OPEN to read saved text. Updated the behavior spec, operator guide, configuration, and user-data documentation.
- Validation: 110 channel/billing/UI checks and 156 website/settings/orchestration checks passed; 65 website JavaScript checks and a final 37-check WhatsApp/UI batch passed. Style and targeted type checks passed with zero warnings; doc-sync completed successfully. Local-network test runs required execution outside the restricted environment. Meta credentials, template approval, HTTPS webhook, live Stripe price setup, and phone validation remain operator follow-ups in TODO.md; live WhatsApp is disabled by default. Activation follow-up created and privately configured the live $20 CAD/month Stripe price with purchases disabled, generated the private webhook verification secret, and added/read-back verified the exact WhatsApp path on the existing Cloudflare tunnel. Meta sign-in is complete. The existing Facebook Login app cannot add WhatsApp; the MHM Messaging business portfolio and WhatsApp app were created with explicit owner authorization for the submitted contact details and terms. The separately presented WhatsApp Platform/Cloud API agreement was accepted with explicit authorization. Meta production setup is available and its test sender is provisioned; the owner-authorized access token was saved privately and a read-only API call confirmed the Meta test sender is connected. The intended production sender is the existing Twilio SMS number. Real inbound webhooks require publishing the app. Meta now restricts the account pending business verification; the owner confirms MHM is unregistered, so no verification was submitted. The app secret still needs owner re-authentication. Template approval, production sender registration, live validation, portal inclusion, and purchase activation remain pending; the running MHM service was not restarted. Follow-up found the dashboard token rejected with HTTP 401 / Meta code 190 and the app-secret password prompt still open. Prepared local privacy/data-page disclosures for WhatsApp sharing and retained transport records; deployment remains pending. Audit follow-up on 2026-11-23 cleared the docstring, registry, error-typing, duplicate, unused-entry-point, test, and Pyright findings; the fresh Tier 3 audit passed 6,772 parallel and 127 serial tests with all static-analysis tracks clean.

### 2026-11-20 - Paid SMS tiers, website refactors, and reminder validation **COMPLETED**

- Added verified SMS enrollment plus $10 CAD/month Discord and $20 CAD/month Discord + SMS plans. Trials can use Email or Discord; only the active phone tier grants SMS. Preserved existing account data and billing status. Published both plan choices; switched to matching live Stripe prices, portal, and signed webhook on 2026-11-21 and restarted MHM. Verified and expired unpaid live checkouts; no payment was taken. Test payments cannot unlock real SMS. Tier regressions: 184 Python and 62 website checks passed.
- Refactored settings/OAuth handling and tested reminder restart recovery. Regression batches passed: 330 broad Python checks, 140 overlapping follow-ups, and 54 website checks; type/style/documentation checks passed. Audit follow-up fixed all seven reported failures (64 focused tests passed), protected billing-mode detection, documented eight intentional duplicate groups, and corrected SMS heading numbers.
- Earlier live tests confirmed Discord check-in saving and SMS delivery, callbacks, task replies, and STOP/START. Scheduled delivery remains Discord; full SMS check-in saving and expanded paid-user carrier validation remain open.
- Nightly follow-up: run `45031042870` exposed an implementation regression that rejected Email for new accounts. Restored Email as a valid desktop and website trial-delivery choice while retaining paid-only SMS and WhatsApp access; all 48 focused checks passed.

### 2026-11-19 - Google Health nightly native crash **COMPLETED**

- Registered background connect/sync callbacks as Qt slots to keep window updates on the UI thread after the nightly bus error. Added thread-affinity regression coverage; Linux nightly confirmation remains pending.
- Updated stale message-editor/process-watcher recovery assertions and Qt metadata typing; all 78 affected dialog tests passed with two workers.
- The Linux rerun found no native crash but exposed a missing Twilio package declaration and health/SMS test domain markers. Added the dependency to editable installs and supplied the communication markers; all 39 affected tests and policy checks passed, plus six packaging/domain checks.
- Fixed the final audit process-cleanup checker's package import when launched as a script; two startup regressions and the standalone JSON probe pass.

### 2026-11-19 - Helpful failures and audit fixes **COMPLETED**

- Improved vague desktop, browser, chat, Discord, task, and launcher failures with saved-state guidance and concrete recovery steps.
- Kept drafts open on failed saves, checked storage results before success, retained failed question undo, and preserved earlier planned-action results.
- Completed priority actions 1, 2, 4 and quick wins: 68 affected tests pass, four Pyright errors are fixed, and three stale references plus ten broken links are repaired. Pyright and documentation checks are clean; Vulture reports zero findings. Full audits remain owner-run.

### 2026-11-19 - Shared documentation consolidation **COMPLETED**

- Consolidated AI mirrors and session safeguards into shared guides and AGENTS.md; removed paired-heading requirements.
- Moved this brief and its archive into development_docs; removed the old AI-doc folder and Cursor rules, commands, and plans.
- Updated tooling in MHM and both upstream branches (development 352201b, published 02ca5d2). All 170 focused tests and published runtime smoke checks passed.

### 2026-11-19 - Feature guides and brief retirement **COMPLETED**

- Renamed the website README to [WEBSITE_GUIDE.md](../website/WEBSITE_GUIDE.md) and updated maintained references/anchors.
- Indexed SMS, website, and Google Health guides in human/AI navigation, communication guidance, and tracked/local tools configuration. Standalone guides remain unpaired.
- Numbered website/health headings and refreshed documentation checks and generated references.
- Retired function/dependency brief generation, outputs, brief-only settings/helpers, and navigation references. Detailed inventories remain; development c76c393 and published b5affed were pushed upstream. Tools tests: 115 passed, 1 skipped; published/MHM default and custom output checks passed.

### 2026-11-19 - Health recovery and Twilio SMS pilot **COMPLETED**

- Health status, enable, and sync failures describe unchanged or unconfirmed saved state and safe recovery without exposing service errors.
- Added separate opt-in simulation and Twilio owner-pilot modes, signed loopback webhooks, durable receipts, delivery callbacks, STOP/START, SMS preference persistence, and shared task/check-in reply handling. Pilot recipient/account/consent checks remain mandatory; live credentials and HTTPS forwarding are unconfigured.
- Final combined SMS/profile/email/reminder regression run: 75 passed; Ruff and whitespace checks passed. Paid API calls are mocked; setup/live validation and additional-user enrollment remain open in the SMS guide and plan.
- Audit follow-up: SMS docstrings/error boundaries, shared phone helper (no circular import), supported-channel test assertion, and test type fixes. Serial 102 passed; two-worker 77 passed; Pyright zero errors/warnings. Regenerated documentation and fixed metadata/headings/links.

### 2026-11-18 - Refresh Google Health before messages **COMPLETED**

- Google Health personalized messages refresh data before building context, including fallback messages when AI is unavailable. Recent pulls and failed attempts suppress repeat requests for five minutes.
- Refresh respects message personalization permissions, feature state, and testing mode. Failures retain saved-data/general-message fallback behavior; background syncing remains active.
- Updated the AI guide. All 41 targeted refresh, sync-manager, and health-context tests passed; targeted Ruff and diff checks passed.

### 2026-11-18 - AI response quality and prompt contracts **COMPLETED**

- Strengthened command and cache assertions, separated automatic contracts from semantic review, and retained full response/context evidence with observed response sources. Expanded the synthetic prompt suite to 24 cases with adversarial safety coverage and app-versus-model failure diagnostics.
- Narrowed topic-based response guards so valid clarifications, conversation replies, and grounded wellness summaries survive. Replayed all seven unnecessarily replaced model replies successfully while retaining missing-data and false-completion protections.
- Aligned planner prompts and parsing, tightened wellness and venting instructions, and made task creation explicitly always available independently of scheduled reminders. Execution summaries distinguish verified saves, pending follow-ups, failures, and unattempted actions.
- All 850 AI-marked tests and 12 follow-up live checks passed, including six medication cases. Audit follow-up repaired documentation links/numbering, guarded and registered the new helper, and cleared Pyright warnings; all 41 focused maintenance tests passed.

### 2026-11-17 - AI replies, task availability, and test fixes **COMPLETED**

- Reply trimming now applies character and word limits together and prefers complete sentences. Replayed both cut-off capability replies successfully, and all 158 focused tests passed.
- Task creation and task context remain available with scheduled reminders off. Updated AI capabilities, fallbacks, and evaluation expectations. Both final live capability checks passed.
- The initial 30-request prompt rerun passed 29 checks. Manual review also found parser recovery of malformed venting output and a weak ambiguous-selection clarification.
- Fixed the nightly test category marker, three stale catalog expectations, and environment leakage in the missing encryption-key test. All 24 affected unit tests passed in parallel. Corrected the changelog ASCII issue and completed documentation sync.
