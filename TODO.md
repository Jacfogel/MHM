# TODO.md - MHM Project Tasks

> **File**: `TODO.md`
> **Audience**: Human developer and AI collaborators
> **Purpose**: Actionable non-testing backlog
> **Style**: Prioritized tasks with scope and completion criteria
> **Last Updated**: 2026-11-05

## 1. Tracking rules

- Keep unfinished work here; record completed work in the changelogs and remove it from this list.
- Give each task a scope, concrete next steps, completion criteria, effort, and created date. Dates below identify when a task was first recorded where known; otherwise they identify this clarification.
- Keep testing work in [TEST_PLAN.md](development_docs/TEST_PLAN.md), current development-tool triage in [AI_PRIORITIES.md](development_tools/AI_PRIORITIES.md), and multi-stage product work in [PLANS.md](development_docs/PLANS.md).
- Prompt tuning, NLP expansion, response-quality work, and live AI tone review remain deferred until separately selected. Billing, budgets, and price tracking belong to the provider, not MHM.
- Follow the deprecation inventory and [AI_LEGACY_COMPATIBILITY_GUIDE.md](ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md) for legacy cleanup. Archived plans are historical references, not additional active task lists.

## 2. High priority

No standalone high-priority items remain in this list. Active product plans retain their own priorities in [PLANS.md](development_docs/PLANS.md).

## 3. Medium priority

### 3.1. Finish precise documentation cross-references

- *Created*: 2026-11-05 (clarified existing item)
- *Scope*: Root contributor/setup docs and their AI counterparts first; module guides second. Exclude archives, changelogs, generated reports, and whole-document navigation links.
- *Next steps*:
  - [ ] Inventory links to specific behavior that omit the destination heading; record source path, destination path, and actual heading.
  - [ ] Update those links to include the existing section number, title, and anchor; verify targets rather than inventing section numbers.
- *Done when*: In-scope behavior references resolve to real headings and paired guides agree. The section-reference standard is already present in DOCUMENTATION_GUIDE.md section 3.3.
- *Progress (2026-11-05)*: Expanded verified references across root, AI, and module guides; corrected stale architecture, testing, logging, setup, and session-starter headings. Added `analyze_documentation_sync.py --json --check-section-links` with repeatable `--section-path` scoping. The configured-doc inventory records source/line/destination/heading and currently resolves 177 references with zero broken anchors and 36 unanchored-reference hints. Pairing checks pass and 25 tooling tests pass. Remaining: review those hints (including navigation/other-document false positives), finish multiline/multiple-section citations and number/title normalization; the checker does not interpret prose or automatically rewrite it.
- *Why it helps*: Readers can find the exact rule without searching an entire guide.
- *Estimated effort*: Medium

## 4. Low priority / deferred

### 4.1. Google Health optional follow-ups

- *Created*: 2026-07-28
- *Scope*: Optional additions to the shipped integration. Operations guidance remains in [GOOGLE_HEALTH_GUIDE.md](integrations/google_health/GOOGLE_HEALTH_GUIDE.md).
- *Next steps* (independent slices):
  - [ ] Define per-user `health_personalization.use_in_messages` and `use_in_chat` preferences, including defaults that preserve existing account-flag behavior. Enforce each preference at its context/message boundary; the account feature flag remains authoritative.
  - [ ] Inspect the supported identity response in `integrations/google_health/client.py` and `integrations/google_health/auth.py`; persist `google_user_id` only from a verified identity response during connect/reconnect. Existing accounts without it must still load.
  - [ ] Measure pagination counts in `integrations/google_health/sync_manager.py` before increasing non-sleep page sizes in `integrations/google_health/client.py`; retain complete pagination and validate provider limits.
  - [ ] Define a bounded baseline-window setting for `integrations/google_health/signal_builder.py`, preserving the current window by default; document how sparse history is handled.
- *Done when*: Each selected slice has code, matching configuration/guide updates, and focused validation. Unselected slices stay deferred; none is required for personal use.
- *Estimated effort*: Small-Medium per slice

### 4.2. Measure and reduce retained memory

- *Created*: 2026-11-05 (clarified existing item)
- *Scope*: Long-running service caches in `ai/client/cache_manager.py`, conversation/context state, and repeated message handling. Test-worker and Windows file-cache measurements belong to TEST_PLAN section 2.9.
- *Next steps*:
  - [ ] Record process memory before/after an isolated repeated-message workload, then after idle/cache expiry.
  - [ ] Identify retained objects or unbounded containers; distinguish expected warm caches from continued growth.
  - [ ] Bound or expire the largest confirmed source while preserving per-user isolation and cache invalidation.
- *Done when*: The same workload demonstrates lower retained memory without stale settings, cross-user replies, or degraded command behavior.
- *Why it helps*: Keeps the service stable during extended use.
- *Estimated effort*: Medium

### 4.4. Refresh user-facing setup and feature instructions

- *Created*: 2026-11-05 (clarified existing item)
- *Scope*: HOW_TO_RUN.md, Discord and email channel guides, and the Google Health guide; README.md remains the navigation entry point.
- *Next steps*:
  - [ ] Walk through startup, account linking, task-list actions, check-ins, email replies, and health reconnect instructions against current controls and command help.
  - [ ] Replace obsolete button labels, screenshots, commands, and setup steps; update the corresponding AI guide where paired.
  - [ ] Use shared configuration references rather than duplicating environment-setting definitions.
- *Progress (2026-11-05)*: Corrected outbound-only email claims in README/configuration reference, added verified email reply and recovery instructions in HOW_TO_RUN section 3.1, corrected startup step numbering and its AI workflow reference, and removed the obsolete Discord skip-button instruction. Remaining: complete startup/linking/task/check-in/health walkthrough and corresponding guide-reference verification.
- *Done when*: Each supported flow has one current set of steps and all referenced controls/commands exist.
- *Why it helps*: Prevents users following instructions for removed behavior.
- *Estimated effort*: Small-Medium

### 4.5. Fill troubleshooting gaps in existing guides

- *Created*: 2026-11-05 (clarified existing deferred item)
- *Status*: Deferred until a recurring support issue or guide refresh supplies evidence.
- *Progress (2026-11-05)*: Guide refresh supplied two concrete email recovery cases: no new reply text and an unregistered sender. HOW_TO_RUN section 3.1 now documents checks and recovery verified against inbound processing. Other troubleshooting areas remain deferred.
- *Scope*: Existing startup, Discord, email, UI, and Google Health troubleshooting sections; avoid a duplicate standalone guide.
- *Next steps*:
  - [ ] Collect reproducible symptoms and relevant log locations for startup/configuration errors, Discord linking, email replies, and health reconnects.
  - [ ] Add symptom -> checks -> recovery -> expected result steps, linking to the canonical configuration and logging guides.
  - [ ] Include safe recovery for invalid AI admin settings; never advise deleting user data as a routine fix.
- *Done when*: Each documented issue has a verified recovery path and no contradictory duplicate instructions.
- *Estimated effort*: Small
