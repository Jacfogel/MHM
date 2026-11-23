# TODO.md - MHM Project Tasks

> **File**: `TODO.md`
> **Audience**: Human developer and AI collaborators
> **Purpose**: Actionable non-testing backlog
> **Style**: Prioritized tasks with scope and completion criteria
> **Last Updated**: 2026-11-06

## 1. Tracking rules

- Keep unfinished work here; record completed work in the changelogs and remove it from this list.
- Give each task a scope, concrete next steps, completion criteria, effort, and created date. Dates below identify when a task was first recorded where known; otherwise they identify this clarification.
- Keep testing work in [TEST_PLAN.md](development_docs/TEST_PLAN.md), current development-tool triage in [Priorities Brief](development_tools/PRIORITIES_BRIEF.md), and multi-stage product work in [PLANS.md](development_docs/PLANS.md).
- Prompt tuning, NLP expansion, response-quality work, and live AI tone review remain deferred until separately selected. Billing, budgets, and price tracking belong to the provider, not MHM.
- Follow the deprecation inventory and [LEGACY_COMPATIBILITY_GUIDE.md](development_docs/LEGACY_COMPATIBILITY_GUIDE.md) for legacy cleanup. Archived plans are historical references, not additional active task lists.

## 2. High priority

- **Activate direct Meta WhatsApp (created 2026-11-21; provider setup blocked):** The MHM Messaging app/portfolio and connected Meta test sender exist. The owner-authorized dashboard token is saved privately and initially passed a read-only API check, but the latest check rejected it (HTTP 401 / code 190); replace it before testing. Meta marks the account restricted and requires business verification; the owner confirms MHM is not registered. Obtain legitimate registration/verification evidence before production activation. App-secret retrieval still needs owner re-authentication. The intended production sender is the existing Twilio SMS business number; it is not registered with Meta. Approve the notification template, verify the routed webhook, check production credential lifetime and deploy the staged privacy/data-deletion disclosures, publish the app, and only then activate the staged $20 CAD/month Stripe price, portal choice, and website release. Complete when live enrollment, delivery/read callbacks, task/check-in replies, STOP/START, and notification/OPEN are verified. Effort: provider onboarding dependent. See [WhatsApp guide](communication/communication_channels/whatsapp/WHATSAPP_GUIDE.md).

## 3. Medium priority

No standalone medium-priority items remain. The documentation reference review was completed on 2026-11-06; evidence and completion details are in the paired changelogs.

## 4. Low priority / deferred

No standalone low-priority items remain. Google Health follow-ups, measured service-state retention limits, the setup/feature walkthrough, and evidenced troubleshooting recovery steps were implemented and documented on 2026-11-06.

Testing follow-ups remain in [TEST_PLAN.md](development_docs/TEST_PLAN.md#28-intermittent-failure-triage), section 2.8. "Intermittent failure triage", including the incomplete full-suite run. Product plans remain in [PLANS.md](development_docs/PLANS.md). The separate deferrals in section 1 still apply.
