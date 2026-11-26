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

### 2026-11-25 - Multi-user privacy and delivery foundations **COMPLETED**

- Hardened AI cache and context ownership, removed private previews from diagnostics, and cleared user-scoped AI runtime state after website deletion. All 213 regression tests and targeted style/type checks passed. Recovered the roadmap into the project; the wider multi-user roadmap remains active.
- Added M2 phone connection recovery, durable uncertain-submission records, and account-scoped STOP/review status. Validation passed: 279 broader checks, 88 focused phone checks, 58 browser checks, style/type checks and doc-sync. Live pilot and provider-budget evidence remain release gates in the roadmap.
- Resolved audit follow-ups: regenerated registry entries, typed submission-data errors, and normalized roadmap formatting/links. All 16 focused checks and targeted style/type checks pass; fresh registry/error-handling/doc-sync checks are clean.

### 2026-11-25 - Repair nightly cache probe policy failure **COMPLETED**

- Removed unnecessary success output from the standalone cache probe while preserving its behavioral assertions. All eight focused cache and no-print policy tests pass; doc-sync passes.

### 2026-11-24 - Restore audit test suite caching **COMPLETED**

- Fixed standalone cache imports and made cache disabling/failures visible; seven focused regressions pass.

### 2026-11-24 - Messaging pilot policy and data controls **COMPLETED**
- Recorded the Canada/US adult pilot decisions, preserved user-defined schedules without automatic overnight suppression, removed automatic channel switching on disconnection, and extended phone export/deletion and retention controls.
- Moved shared phone-store lifecycle coordination out of the SMS base to remove the SMS/WhatsApp circular import.

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
