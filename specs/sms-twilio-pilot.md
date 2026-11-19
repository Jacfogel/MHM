# Twilio SMS pilot


> **File**: `specs/sms-twilio-pilot.md`
> **Implementation**: `communication/communication_channels/sms/`, `storage/sms_state.py`, `communication/reminders/reminder_dispatcher.py`, `communication/reminders/checkin_prompt_dispatcher.py`
> **Automated tests**: `tests/behavior/test_twilio_sms.py`, `tests/behavior/test_sms_simulation.py`
> **Setup**: [SMS_GUIDE.md](../communication/communication_channels/sms/SMS_GUIDE.md)

## Requirements

- Live mode SHALL require explicit enablement, credentials, an HTTPS origin, owner consent, and a pilot phone matching the configured existing account. Simulation and live mode SHALL be mutually exclusive.
- Only the pilot recipient SHALL receive live SMS or invoke commands. No public account enrollment is provided.
- Webhooks SHALL validate the official Auth Token signature against the configured public URL, the account, and the receiving number before mutations. Invalid signatures SHALL return 403.
- A valid inbound message ID SHALL be claimed durably before business handling. Duplicate and concurrent deliveries SHALL NOT rerun the command, including after restart. Unconfirmed processing SHALL require manual inspection rather than replay.
- STOP/START SHALL update durable local stop state; provider keyword confirmations SHALL NOT be duplicated. Stopped numbers SHALL NOT receive application texts.
- Task and check-in mutations SHALL use existing shared handlers. A single linked prompt MAY accept a short reply. Multiple or missing prompt contexts SHALL require an explicit target and SHALL NOT guess a task.
- Outbound submission SHALL return acceptance separately from delivery. Timeouts/server errors SHALL be unconfirmed and SHALL NOT trigger automatic resending. Signed callbacks SHALL record delivery states without late events regressing a terminal result.
- The listener SHALL bind only to loopback, reject oversized/non-form requests and duplicate form fields, and avoid logging request bodies or credentials.

## Scenarios and evidence

- **Automated**: signed incoming `done` completes a test task, while replay does not run it twice.
- **Automated**: invalid signature/account/recipient does not run commands; actual loopback HTTP signature validation and lifecycle are tested.
- **Automated**: concurrent/restarted receipts, processing failures, STOP/START/HELP, late callbacks, uncertain sends, ambiguous targets, and check-in response routing.
- **Manual**: live carrier delivery, provider registration, a real check-in exchange, STOP/START on a phone, and HTTPS reverse-proxy configuration.

## Limits

One approved account only. No automated phone verification, additional-user signup,
receipt retention cleanup, or operator UI. Crash recovery trades automatic replay
for avoiding duplicate mutations. Simulator character chunks are not SMS encoding.
