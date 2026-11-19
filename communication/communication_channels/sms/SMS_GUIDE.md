# SMS: Twilio pilot and simulator


> **File**: `communication/communication_channels/sms/SMS_GUIDE.md`
> **Audience**: Developers and pilot operators
> **Purpose**: Configure, operate, and validate SMS simulation and the Twilio owner pilot

For shared delivery boundaries, see [COMMUNICATION_GUIDE.md](../../COMMUNICATION_GUIDE.md). Browser/gateway deployment is covered by [WEBSITE_GUIDE.md](../../../website/WEBSITE_GUIDE.md), and health OAuth/sync setup by [GOOGLE_HEALTH_GUIDE.md](../../../integrations/google_health/GOOGLE_HEALTH_GUIDE.md).

Live SMS is implemented for one explicitly approved account and phone number.
It remains disabled until configured. Simulation is a separate mode and never
contacts Twilio. Public self-service signup and additional recipients are not enabled.

## 1. Connect the Twilio pilot

1. Install the project requirements in `.venv`. The Twilio SDK is required for live mode.
2. Obtain a two-way SMS-capable Twilio number and complete the provider registration
   applicable to that number and destination. See [Twilio sender setup](https://www.twilio.com/docs/messaging/tutorials/how-to-send-sms-messages).
3. On your existing MHM account, save your own international phone number (for example
   `+15555550101`). Use the existing account settings; do not create a second account.
4. Configure the following private `.env` fields, then restart MHM:
   - `SMS_SIMULATION_ENABLED=false`
   - `SMS_TWILIO_ENABLED=true`
   - `TWILIO_ACCOUNT_SID`: the account that owns the sending number
   - `TWILIO_AUTH_TOKEN`: that account's Auth Token, used for both API calls and signatures
   - `TWILIO_PHONE_NUMBER`: your Twilio sending number, in international format
   - `SMS_PILOT_USER_ID`: your existing internal MHM account ID
   - `SMS_PILOT_PHONE_NUMBER`: your recipient number, matching the saved account phone
   - `SMS_PILOT_CONSENT=true`: your explicit approval to receive MHM texts on that number
   - `SMS_PUBLIC_BASE_URL`: your public HTTPS origin, for example `https://sms.example.com`
   - `SMS_WEBHOOK_PORT=8082`: the local listener port
5. Forward that HTTPS origin's `/sms/incoming` and `/sms/status` paths to
   `http://127.0.0.1:8082`. Use a tunnel for development or a stable HTTPS reverse
   proxy for ongoing operation. The application binds only to loopback; it does
   not obtain certificates or start a tunnel automatically. MHM must remain running.
6. In Twilio's number configuration, set **A message comes in** to **POST**
   `https://your-host/sms/incoming`. MHM supplies the `/sms/status` callback address
   on each outgoing API request. Keep the default Auth Token webhook signatures.
   The exact public origin must match `.env`; forwarded headers are never trusted.
7. Select SMS as the existing account's preferred channel for scheduled reminders.
   If the current settings screen does not expose SMS, the supported storage API is
   `update_user_preferences(user_id, {"channel": {"type": "sms"}}, auto_create=False)`
   in `storage.user_data_write`; check its returned boolean before treating it as saved.
   Changing the preference redirects future scheduled messages. Restore the previous
   channel to return to Discord or email.

Only the configured pilot account/number can send commands or receive texts.
The saved account phone is rechecked for each operation. Configuring another
number requires restarting and explicit consent. This pilot is manually approved
by its owner; it is not an automated phone-ownership verification flow.

## 2. Using SMS

- Send `sms status` to confirm the connection.
- A task reminder accepts `done`, `snooze`, `skip`, and the shared task-reply options.
- A check-in accepts its answers, including numeric answers.
- When multiple reminder contexts are open, a short reply takes no action. Use
  `complete task <task name or ID>` or `checkin <answer>` to make the target explicit.
- Send `STOP` to stop SMS and `START` to resume. MHM persists the opt-out locally.
  Twilio owns keyword confirmations, including `HELP`; MHM does not send duplicates.
  SMS stop words such as bare `CANCEL` belong to the provider. Use `cancel checkin`
  to cancel a check-in. [Twilio keyword behavior](https://www.twilio.com/docs/messaging/tutorials/advanced-opt-out)

All SMS is plain text. Twilio handles actual GSM-7/UCS-2 segmentation and billing;
MHM submits a message once rather than sending character chunks as separate texts.
Outbound messages above 1,600 characters are rejected before submission. Incoming
command responses are shortened to fit. Simulated chunks do not predict billing.

## 3. Delivery and recovery

Provider acceptance is not handset delivery. Twilio IDs and signed status callbacks
are stored in `BASE_DATA_DIR/sms_state.sqlite3`. Terminal delivery states are not
replaced by late queued/sent events. [Twilio status definitions](https://www.twilio.com/docs/messaging/api/message-resource)

Inbound IDs are claimed transactionally before commands run. Duplicate or concurrent
webhook requests, including after restart, cannot run that command again. A crash
between claiming and finishing can leave an action unprocessed or unconfirmed:
check the task/check-in before retrying manually. Receipts marked `needs_review`,
`processing`, or `reply_unconfirmed` need operator review; they are never replayed
automatically. This favors preventing duplicate mutations over automatic recovery.

If an outgoing API call times out or returns a server error, acceptance is reported
as `unconfirmed`, suppressing automatic resend. Inspect Twilio message history before
sending another copy. A timeout without a returned message ID may require matching
by time and recipient in Twilio. Provider rejections show a safe numeric error code.

The state database retains receipt IDs, statuses, opt-outs, recipient numbers, and
prompt references; no message bodies or credentials are stored there. Existing
shared conversation/task storage still applies. Keep this file across restarts and
back it up with application data. Deleting it removes deduplication and stop history.
Retention cleanup and an operator status screen remain future work. Do not run two
live MHM instances against separate databases for the same Twilio account/number.

## 4. Simulation

Set `SMS_TWILIO_ENABLED=false`, `SMS_SIMULATION_ENABLED=true`, and restart. The
`SmsBot` development API supports `await bot.initialize()`,
`await bot.send_message(number, text)`, and `await bot.simulate_incoming(number, text)`.
Captured messages are in `bot.outbox`; they are volatile and never delivered.
Simulated inbound commands **can save real changes**, so use isolated test accounts.
Local simulated input is rejected when live transport is attached.

## 5. Validation and expansion

Automated tests use the real signature validator, SQLite state, shared task completion,
and a loopback HTTP listener with mocked paid API calls. They do not establish live
carrier delivery. Before enabling regular reminders, verify one outbound text, a task
reply, a check-in, STOP/START, and the Twilio delivery callback from your own phone.

For additional people, replace the one-account pilot allowlist with verified
per-account phone enrollment and recorded consent, add onboarding/management UI,
and validate provider registration for the expanded use. Existing receipt and
opt-out handling can be reused. Never simply remove the allowlist.

Run with the project environment active:

```powershell
python -m pytest tests/behavior/test_twilio_sms.py tests/behavior/test_sms_simulation.py -q
```
