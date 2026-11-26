# MHM Multi-User Roadmap

> **File**: `development_docs/MULTI_USER_ROADMAP.md`
> **Purpose**: Implementation phases for safely supporting additional MHM users
> **Last Updated**: 2026-11-25

## 1. Implementation status

**ACTIVE.** The first code changes harden AI cache identity boundaries, prevent shared mutable context, validate ownership of reused AI envelopes, remove prompt/context previews from diagnostics, and clear initialized AI runtime state after website account deletion. See the paired changelogs for validation. These changes do not complete the private-memory controls or certify a public launch.

The confirmed pilot policy in [PLANS.md](PLANS.md#73-messaging-pilot-launch-policy) governs: 10 to 25 adults in Canada or the United States, current plan prices, and provider-owned spending controls. It supersedes conflicting suggestions from the original Page, including Canada-only scope and application cost ledgers/caps. Operational launch gates remain unverified until evidenced; WhatsApp stays disabled.

**Next implementation work:** complete user-controlled conversational retention and correction/deletion, serialize deletion against in-flight work across channels, review object-level authorization and identity uniqueness, then validate enrollment and dispatch recovery. Shared session/database migration follows measured capacity requirements. Provider activation, incorporation/verification, staffing, and observed pilot milestones cannot be completed through repository changes alone.

**Second milestone implementation (2026-11-25):** Phone connection retries now
recognize an existing matching verified connection without renewing consent, while
enforcing active-account, plan, owner, and opt-out boundaries. SMS and WhatsApp
persist an account-scoped attempt before provider submission, including unresolved
outcomes without a provider ID. Connection refresh exposes only that account's
review counts and STOP status. Export/deletion and retention cover the new records.
The paired changelogs record automated validation; no fresh live provider evidence
or deployment is implied.

**M2 release evidence still required:** Observe a new participant completing setup
and receiving a useful message unaided; validate destination-specific phone
delivery and current provider setup; record support coverage, provider spending
thresholds, alert recipients and review cadence; exercise manual pause and
uncertain-send reconciliation. Do not mark the operational milestone complete
from repository tests alone.

**Queue assessment:** The existing RetryManager owns an in-memory retry queue and
deduplicates pending delivery keys. It is not a durable outbound job queue. This
stage adds durable phone submission/recovery evidence with no automatic replay.
A general durable queue with expiry, atomic claiming and shared state remains
part of the infrastructure work before multiple dispatchers are introduced.

## 2. Roadmap

Planning baseline recorded 25 November 2026. MHM's next product step is a controlled service for other users, built on its existing shared core, account system, website, Discord, and SMS support. Prioritize account isolation, private memory, dependable delivery, and cost controls before public acquisition. Treat WhatsApp as a conditional channel expansion, so provider approval cannot block the rest of the product.

This roadmap develops the goal stated in [WhatsApp Cost Comparison](https://chatgpt.com/c/6b010752-0978-83e8-9878-7a7278a9a52b): supporting other users through one assistant with several messaging channels. It complements the existing [Messaging Expansion Roadmap](https://chatgpt.com/space/page_577c22d08ac881918fac8e9076be4e76), with broader priorities for onboarding, identity, privacy, infrastructure, pricing, and commercialization.

### 2.1. Existing capabilities and launch gaps

**Existing means documented implementation, not certification of production readiness.** The current project guides are the baseline below. Proposed work and release gates follow separately.

- **Discord exists:** Bot conversations, natural language commands, task reminders, check-ins, interactive controls, and account creation/linking use a shared communication pipeline. Discord transport cost and MHM subscription price are different concepts.

- **SMS exists:** Twilio delivery, account-bound phone verification, explicit consent, signed callbacks, persistent inbound deduplication, STOP/START, and paid-plan eligibility checks are documented. The channel still needs evidence from a broader user pilot.

- **Website onboarding and authentication exist:** Verified email signup, passwords stored as salted scrypt hashes, emailed sign-in codes, password recovery, optional configured social sign-ins, first-run setup, settings, inbox, tasks, notebook, and private insights. Signup does not require a messaging connection. New website accounts receive a 30-day trial.

- **Billing exists:** Stripe-hosted Checkout and Customer Portal, subscription reconciliation, and channel entitlement checks. Documented prices are CAD 10/month for Discord and CAD 20/month for Discord plus SMS. WhatsApp has a separate CAD 20/month plan definition; it does not grant SMS access.

- **Per-user data foundations exist:** Internal user IDs, user-scoped files under `data/users/{user_id}`, centralized storage helpers, account lifecycle functions, conversation history, and contextual AI. AI response cache keys include user ID. These mechanisms need adversarial isolation testing before wider access.

- **WhatsApp adapter exists but activation is blocked:** The 21 November activation record reports an unpublished app, restricted account pending business verification, failed saved test credentials, no registered production sender, and no approved notification template. WhatsApp is disabled and its Stripe product/price are inactive. Privacy-page updates are recorded as awaiting deployment. Recheck these operational facts before activation.

**Existing scaling constraint:** Website sessions and verification codes are held in memory; restart signs browsers out. The website guide requires one gateway process and shared session storage plus coordinated account creation before scaling. Per-user JSON storage and channel SQLite state are not, by themselves, a distributed deployment architecture.

### 2.2. Recommended technical decisions

#### One account across all channels

Keep the internal user ID as the canonical identity. Map verified Discord identities and verified phone enrollments to it; never derive ownership from a display name, phone number alone, or a client-supplied user ID. Require an authenticated account and proof of control for linking, with expiry, single use, uniqueness checks, and an audited recovery path for recycled phone numbers. Changing channels must preserve the same tasks, schedules, preferences, and permitted history.

Keep authentication, channel connection, consent, and subscription eligibility as separate checks. A paid subscription does not verify a phone, and SMS consent does not authorize WhatsApp. Require recent authentication for account linking, export, deletion, and recovery-sensitive changes. Add administrator MFA and separate support permissions before a wider launch; evaluate passkeys or a managed identity provider when operational burden justifies migration, rather than rebuilding the existing signup flow now.

#### Shared core with explicit user scope

Retain the channel-independent interaction manager and thin channel adapters. All reads and writes must use `storage.*` or the stable `core` facade. Resolve account identity at the trusted boundary, then carry explicit user scope through handlers, scheduling, exports, background jobs, AI context, and delivery. Deny ambiguous or absent ownership for personalized operations.

Authorize every object operation on the server, including access by task/note ID and website endpoints. Enforce unique identity ownership transactionally. Use canonical time utilities, centralized configuration, shared safe errors, and canonical component logging. Keep secrets and provider SDKs at service boundaries.

#### Private memory with user control

Treat conversation history, saved profile facts, inferred summaries, and optional health data as different data classes. Proposed memory controls should let each user inspect, correct, delete, and disable long-term memory while keeping essential account and billing records separately governed. Offer a conversation mode that does not add persistent conversational memory, with clear disclosure of any necessary short-lived processing.

Partition sessions, response/context caches, retrieval indexes, embeddings, analytics, and exports by user. Never share personal context through a global prompt or a shared cache entry. If semantic retrieval is introduced, enforce ownership before and after retrieval. Version memory updates so deleting or correcting a fact invalidates derived summaries, embeddings, and cached responses; prevent deleted content from being recreated by background summarization.

Default channel notifications to neutral content and direct users to the authenticated inbox for sensitive detail. Explain which providers receive message content and AI context. Restrict support access to the minimum required, record privileged access, redact content from operational logs, encrypt storage and backups, and define key access. Publish retention periods, export/deletion behavior, and the expiry of backup copies. Encryption at rest does not prevent an authorized service from reading content; do not promise end-to-end confidentiality across the whole assistant.

#### Durable delivery and measured infrastructure

Start with one active gateway and one scheduler/dispatcher on a managed host, with HTTPS, secret management, health checks, encrypted off-host backups, and a tested restore procedure. Avoid multiple uncoordinated processes reading separate copies of local state.

Proposed delivery work: assess a durable outbound queue through the storage layer, atomic job claims, and per-user ordering for conflicting mutations. Distinguish queued, accepted, delivered, failed, expired, and unconfirmed outcomes; retain provider-specific uncertainty safeguards. Check consent, quiet hours, and plan eligibility at dispatch. Preserve the confirmed pilot decision to keep spending controls, alerts, and usage review with providers. An MHM cost ledger, automatic overages, and application-enforced spending caps remain outside the authorized pilot policy.

Before horizontal scaling, migrate required accounts, delivery state, jobs, and sessions to shared transactional storage behind existing APIs. Managed PostgreSQL is the recommended first candidate; use a shared session store with revocation and expiry, and a durable queue once load warrants separate workers. Add database ownership constraints and, where practical, row-level access policies as defense in depth. Preserve current user data, validate migration, create a safety backup, and prove rollback before switching production.

### 2.3. Phased development roadmap

Dates below are relative planning ranges for one primary developer with product/operations support. Exit criteria govern release; provider waiting time is additional. Product owner, developer, and operations roles must be assigned to named people before a pilot.

#### Phase 0 Confirm the product and baseline

**Priority P0 * Approximately one week * Product owner and developer.** Choose an initial audience, the confirmed 10 to 25 adult pilot in Canada and the United States, and define the promise: supportive planning, reminders, check-ins, and personal organization. Specify supported hours, boundaries, retention, and the first pilot's workload. Inventory the actual deployed versions, enabled channels, billing configuration, and existing capabilities above. Review the owning behavior specs before implementation.

**Milestone M0:** A signed-off pilot scope, capability inventory, risk register, and prioritized backlog. Decide whether WhatsApp can qualify under current provider terms for MHM's actual AI behavior and target market. A generic productivity label does not establish eligibility. Proceed with existing channels if that decision remains blocked.

#### Phase 1 Prove account and memory isolation

**Priority P0 * Approximately two to three weeks * Developer with privacy/security review.** Trace identity from login or provider event through data access, AI context, caches, and background work. Complete object authorization, identity uniqueness, memory controls, redaction, administrator access boundaries, retention, and deletion/export behavior. Exercise existing authentication and recovery rather than assuming they need replacement.

**Milestone M1:** Isolated tests with at least two deliberately different users prove that guessed IDs, overlapping prompts, concurrent tasks, account switching, forged webhooks, exports, and recovery cannot reveal or alter another user's data. Deleted memory stays absent from caches and derived summaries. Backup restoration succeeds on isolated data. No unresolved critical isolation or authentication issues enter the pilot.

#### Phase 2 Make onboarding and delivery dependable

**Priority P0 * Approximately two to three weeks * Developer and operations.** Validate signup through first useful task/check-in, time zone and quiet hours, channel linking, consent, billing, disconnection, and account recovery. Assess shared queue requirements and operator recovery views; document provider spending alerts and manual review. Keep email and Discord as trial routes; preserve existing restrictions on live paid phone channels.

**Milestone M2:** A new tester completes setup and receives a useful message without developer intervention. Duplicate and out-of-order callbacks, restart, provider timeout, expired codes, STOP, late payment updates, cancellation, and subscription downgrade produce safe results. Every uncertain mutation or send has a visible recovery path. Provider alerts and manual pause procedures are documented and exercised.

#### Phase 3 Run an invitation pilot

**Priority P1 * At least two weeks of observation * Product owner and operations.** Enroll 10 to 25 consenting people using email/Discord, with a paid SMS subset only when eligible. Observe activation, useful task completion, reminder timeliness, quiet-hour correctness, support minutes, AI usage, segments, and recurring costs. Interview users about value and willingness to pay.

**Milestone M3:** Proposed pilot targets are at least 80% unaided setup completion and 95% of eligible reminders handed to providers within two minutes of schedule. Track handset delivery separately. Require zero observed cross-user disclosures or duplicate state-changing actions, all uncertain sends visible, and reconciled transport estimates within 10% of provider charges. Any isolation incident pauses enrollment for investigation; an incident-free pilot does not establish absolute security.

#### Phase 4 Validate paid beta and conditional WhatsApp

**Priority P1 * Approximately two to four development weeks after M3 * Product owner and developer.** Expand toward 50 to 100 users only after the pilot gates pass. Publish allowances, limits, renewal/cancellation/refund terms, support expectations, and provider disclosures. Exercise the full billing lifecycle, including failed payment, plan change, and account closure.

Run a separate 5 to 10 person WhatsApp pilot only after business verification and current AI eligibility are resolved, credentials are valid, the production sender and template are approved, privacy changes are deployed, and signed live webhooks work. Activate purchase availability only when delivery and entitlement checks pass. Continue with other channels if approval fails.

**Milestone M4:** Demonstrate live channel linking, message retrieval, full check-in/task replies, opt-out, callback handling, and paid entitlement reconciliation. Complete at least one measured billing cycle. Confirm acceptable contribution margin and a clear reason for users to renew before broader sales.

#### Phase 5 Scale operations and commercial distribution

**Priority P2 * Capacity gates rather than a promised launch date * Developer and operations.** Grow from 100 toward 1,000 active users after shared storage/session migration and atomic job claiming. Load-test twice the forecast peak, including a morning burst and provider outage recovery. Track queue age, failure rate, tenant fairness, AI latency/cost, and spend variance. Introduce more workers only when measured demand requires them.

**Milestone M5:** Meet pilot delivery targets at forecast peak, restore within an agreed recovery target, and demonstrate bounded backlog recovery without duplicate mutations. Proposed initial recovery objectives are four hours to restore service and no more than 24 hours of data loss; validate backup frequency against the promise before publishing it. At 10,000 users, obtain new capacity and staffing estimates, verify sender limits, and reassess regional operations before committing.

### 2.4. Messaging priorities

1. **Harden existing email and Discord first.** Use the authenticated website inbox as the durable place to review assistant content. Discord can be the recommended messaging route where users are comfortable with it; inexpensive transport does not make the product free to operate.

2. **Offer SMS with explicit allowances.** Budget actual billable segments, inbound traffic, carrier fees, and sender rental. Never describe SMS as an emergency or guaranteed medication-adherence channel.

3. **Activate the existing direct Meta WhatsApp adapter conditionally.** Avoid unofficial WhatsApp Web automation. Retain separate channel consent, verification, entitlement, and opt-out.

4. **Add category-level channel choices after central policy enforcement.** Let users choose where reminders, check-ins, and summaries go, with quiet hours and an explicitly consented fallback. Do not duplicate sensitive notifications automatically or use fallback to bypass an opt-out.

5. **Defer more integrations until retention supports them.** Telegram, native apps, voice, and organizational dashboards should follow demonstrated demand.

### 2.5. Infrastructure costs and pricing

#### Cost model to operate the service

Track monthly cost as fixed hosting, database, storage, backups, monitoring, email, and sender rental, plus per-user AI, messaging, payment fees, support, and incident work. Separate active users from paying subscribers. Keep provider costs in their invoice currency and compare them with CAD revenue using the actual billing exchange rate.

For planning only, use infrastructure envelopes of **USD 50 to 150/month for 10 to 25 pilot users**, **USD 150 to 400/month near 100 users**, and **USD 400 to 1,500/month near 1,000 users**, excluding AI, transport, payment processing, support labor, taxes, and setup. These are proposed spending envelopes, not vendor quotes or capacity guarantees. Obtain hosting and database quotes after measuring storage, peak jobs, backup retention, and deployment region.

An illustrative variable-cost stress test assumes 150 scheduled notifications and 30 conversational turns per active user each month, with USD 0.50 to 3.00 of AI expense per user. At 100 users that is USD 50 to 300/month for AI alone; at 1,000 it is USD 500 to 3,000. A turn means one user message and its reply. Measure tokens, model mix, context length, retries, and tool calls rather than treating this allowance as a model-price quote.

Calculate SMS from outbound segments x outbound rate, inbound segments x inbound rate, plus carrier and sender fees. Calculate WhatsApp from delivered messages by destination market and approved category, applying only the free treatment or allowances confirmed for the account's current rate schedule. Keep an allowance for service replies, template reclassification, verification traffic, and any intermediary fee. [Twilio Canada SMS pricing](https://www.twilio.com/en-us/sms/pricing/ca) and [Meta platform pricing](https://business.whatsapp.com/products/platform-pricing) are the vendor references.

The earlier discussion and Messaging Expansion Roadmap contain illustrative WhatsApp rates and a service-message allowance. Do not use those figures as a live price commitment: confirm the effective rate card, any AI-provider terms, and actual invoices before setting a channel allowance. The public pricing material and earlier assumptions do not establish MHM's account-specific charges.

#### Pricing decisions

Preserve the documented CAD 10 Discord and CAD 20 SMS pricing as the beta baseline. Keep WhatsApp unavailable for purchase until activation gates pass. A permanent free Discord tier was an earlier suggestion, not the implemented subscription policy; test it later only if acquisition and support economics justify it.

Keep the confirmed provider-owned budget approach for the pilot. Measure costs through provider invoices and manual review. An application-enforced allowance, automatic overage charges, or new prepaid plans require a separate product decision before implementation. Keep the current plan prices and live-paid eligibility.

Use **contribution per subscriber = net subscription revenue - variable AI - transport - payment fees - variable support**. Track fixed infrastructure separately and include acquisition, tax, and founder labor in the full business plan. A proposed paid-beta gate is at least 60% contribution margin after variable service costs, with a viable heavy-user scenario. This is a planning target, not a claim about current margins. Review pricing if actual usage fails that gate.

### 2.6. Commercialization milestones

- **Invitation pilot:** Validate that people beyond the owner can onboard, trust the service, and return weekly. Recruit a defined audience and record consent; avoid broad paid acquisition.

- **Paid beta:** Establish a named operator, support channel, incident process, business/banking and tax setup, payment terms, refund policy, and privacy review appropriate to the launch audience. Review applicable privacy and electronic-messaging obligations before selling; do not assume a general wellness label resolves them.

- **Public individual offering:** Publish accurate product claims and service boundaries. MHM supports organization and wellbeing; do not promise diagnosis, therapy, emergency response, or guaranteed message delivery. Measure four-week retention, paid conversion, churn, refunds, support load, and contribution margin before spending materially on acquisition.

- **Organizational offering later:** Require explicit demand, contracts, role permissions, organizational isolation, and clear consent rules before employer, clinician, or caregiver access. Do not reuse individual users' private memory for sponsor reporting or training by default.

### 2.7. Development checklist

#### Before the first external pilot

- [ ] Confirm deployed capability inventory and initial audience.

- [ ] Assign product, engineering, privacy/security, support, and incident owners.

- [ ] Read the relevant shared specs and record acceptance criteria.

- [ ] Trace authenticated user identity through every route, handler, job, cache, and AI context.

- [ ] Prove cross-user read/write denial with two-user tests and concurrent jobs.

- [ ] Verify signup, login, recovery, session expiry, linking, unlinking, and recycled-number recovery.

- [ ] Add private-memory inspection, correction, disablement, and deletion with derived-data cleanup.

- [ ] Define retention, provider disclosures, administrator access, and redacted logging.

- [ ] Validate durable dispatch, idempotency, expiry, uncertain-send review, and provider spending procedures.

- [ ] Test consent, STOP/START, plan denial, failed payment, and cancellation at dispatch.

- [ ] Encrypt and isolate backups; validate backup and create a safety backup before restore.

- [ ] Restore isolated test data and document service recovery.

#### Before paid beta

- [ ] Complete the observed pilot and review activation, retention, support time, incidents, and costs.

- [ ] Reconcile AI and messaging usage with invoices; confirm current vendor rate schedules.

- [ ] Confirm provider spending thresholds, review cadence, margin targets, cancellation, and refund terms.

- [ ] Test live billing and entitlements without treating test payments as live phone access.

- [ ] Publish accurate privacy, retention, support, and product-boundary information.

- [ ] Complete WhatsApp eligibility and business verification only if pursuing that channel.

- [ ] Validate WhatsApp credentials, sender, template, live callbacks, deployment, and separate plan before activation.

#### Before scaling beyond the first host

- [ ] Migrate shared transactional state through storage APIs and preserve existing data.

- [ ] Add shared sessions, unique identity constraints, atomic job claims, and tenant fairness.

- [ ] Load-test twice forecast peak and simulate provider outages, restart, and recovery.

- [ ] Verify monitoring, budget alerts, key rotation, access reviews, and operational runbooks.

- [ ] Run focused isolated tests and appropriate broader checks; use isolated test logs and mock Windows Task Scheduler.

- [ ] Update the owning guides/specs, detailed and brief changelogs, and active follow-ups when implementation occurs; refresh generated reports through their generator and run documentation synchronization.

### 2.8. Sources and decision record

Product context: [WhatsApp Cost Comparison](https://chatgpt.com/c/6b010752-0978-83e8-9878-7a7278a9a52b) and [Messaging Expansion Roadmap](https://chatgpt.com/space/page_577c22d08ac881918fac8e9076be4e76). Implementation baseline: repository [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md), Discord/SMS/WhatsApp channel guides, [WEBSITE_GUIDE.md](../website/WEBSITE_GUIDE.md), [USER_DATA_MODEL.md](../core/USER_DATA_MODEL.md), [SYSTEM_AI_GUIDE.md](../ai/SYSTEM_AI_GUIDE.md), and `ai/client/cache_manager.py`. The WhatsApp activation status is the dated 21 November record, not a fresh provider-console check.

Provider launch checks: [Meta platform pricing](https://business.whatsapp.com/products/platform-pricing), [WhatsApp Business terms](https://www.whatsapp.com/legal/business-solution-terms), and [Twilio Canada SMS pricing](https://www.twilio.com/en-us/sms/pricing/ca). Resolve current contractual eligibility and account-specific charges before activation. Proposed durations, infrastructure envelopes, usage assumptions, margin targets, and release metrics above are planning decisions to validate.
