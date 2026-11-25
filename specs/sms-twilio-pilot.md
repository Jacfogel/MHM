# Twilio SMS account enrollment


> **File**: `specs/sms-twilio-pilot.md`
> **Implementation**: `communication/communication_channels/sms/`, `storage/sms_state.py`, `communication/reminders/reminder_dispatcher.py`, `communication/reminders/checkin_prompt_dispatcher.py`
> **Automated tests**: `tests/behavior/test_twilio_sms.py`, `tests/behavior/test_sms_simulation.py`
> **Setup**: [SMS_GUIDE.md](../communication/communication_channels/sms/SMS_GUIDE.md)

## Requirements

- Live mode SHALL require explicit enablement, Twilio credentials, a sending number, and an HTTPS origin. Simulation and live mode SHALL be mutually exclusive.
- SMS SHALL require the $20 CAD/month Discord + SMS tier (`subscription_status=active`, `subscription_plan=phone`, `billing_livemode=true`). The $10 CAD/month Discord tier SHALL NOT grant SMS. The phone tier SHALL include Discord. Trial accounts MAY use Email or Discord. Complimentary, past-due, canceled, and trial accounts SHALL NOT send or invoke SMS business commands. Settings and delivery SHALL both enforce this rule.
- Website first-run setup and account delivery settings, and desktop channel management SHALL expose SMS with its paid-plan requirement. New accounts can select Email or Discord during the trial; SMS can be connected after an active paid phone-tier subscription is recorded. Selecting SMS SHALL NOT change subscription state.
- Each SMS account SHALL have an explicitly consenting, verified phone. Connection requires the owner to send a random, single-use LINK code from that phone through a signed webhook. Codes SHALL expire in 15 minutes, be stored only as hashes, and be scoped to the initiating authenticated account. The connection UI SHALL NOT send unsolicited verification texts.
- Enrollment SHALL enforce one phone per account and one account per phone. The saved account phone and active account status SHALL be rechecked for every operation. Outbound user IDs SHALL match the phone's enrolled account. Switching or disconnecting an enrollment SHALL clear its obsolete reply contexts and preserve opt-out and delivery-receipt history.
- STOP/START SHALL remain processable for enrolled numbers after paid access ends. Reconnection SHALL NOT clear a STOP opt-out. A downgraded account's saved SMS preference SHALL NOT bypass delivery enforcement.
- Webhooks SHALL validate the official Auth Token signature against the configured public URL, the account, and the receiving number before mutations. Invalid signatures SHALL return 403.
- A valid inbound message ID SHALL be claimed durably before business handling. Duplicate and concurrent deliveries SHALL NOT rerun the command, including after restart. Unconfirmed processing SHALL require manual inspection rather than replay.
- STOP/START SHALL update durable local stop state; provider keyword confirmations SHALL NOT be duplicated. Stopped numbers SHALL NOT receive application texts.
- Task and check-in mutations SHALL use existing shared handlers. A single linked prompt MAY accept a short reply. Multiple or missing prompt contexts SHALL require an explicit target and SHALL NOT guess a task.
- Outbound submission SHALL return acceptance separately from delivery. Timeouts/server errors SHALL be unconfirmed and SHALL NOT trigger automatic resending. Signed callbacks SHALL record delivery states without late events regressing a terminal result.
- The listener SHALL bind only to loopback, reject oversized/non-form requests and duplicate form fields, and avoid logging request bodies or credentials.

## Billing tier reconciliation

- Checkout SHALL accept only the named `discord` or `phone` plan and resolve its Price on the server. Prices SHALL be $10 and $20 CAD per month respectively.
- Signed billing events SHALL retrieve the current subscription and map its actual single-item Price to `subscription_plan`; requested metadata SHALL NOT grant SMS.
- Test-mode Stripe subscriptions SHALL NOT unlock real SMS. Public test-mode Checkout and Portal actions SHALL be disabled; local/provider test validation may still run.
- Unknown prices and malformed/multiple-item subscriptions SHALL NOT grant the phone tier. Subscription status SHALL still gate SMS delivery; trials remain ineligible for SMS even if a future phone plan is selected.
- Plan-specific Checkout idempotency keys SHALL prevent a Discord checkout request from returning a cached phone checkout, or vice versa.
- The dedicated hosted portal SHALL offer the two plans with prorated upgrades and period-end downgrades. Existing subscriptions SHALL NOT be changed automatically by catalog setup.

## Scenarios and evidence

- **Automated**: signed incoming `done` completes a test task, while replay does not run it twice.
- **Automated**: invalid signature/account/recipient does not run commands; actual loopback HTTP signature validation and lifecycle are tested.
- **Automated**: concurrent/restarted receipts, processing failures, STOP/START/HELP, late callbacks, uncertain sends, ambiguous targets, and check-in response routing.
- **Automated**: phone-bound, expiring, single-use enrollment proofs, account ownership conflicts, paid-plan enforcement, multi-account routing, revocation, and STOP after downgrade (`tests/behavior/test_sms_enrollment.py`).
- **Manual**: live carrier delivery, provider registration, a real check-in exchange, STOP/START on a phone, and HTTPS reverse-proxy configuration.

## Limits

Phone retention and account data controls follow [the messaging policy spec](messaging-quiet-hours-and-data-controls.md). A dedicated operator delivery-status UI remains unimplemented. Crash recovery trades automatic replay
for avoiding duplicate mutations. Simulator character chunks are not SMS encoding.
