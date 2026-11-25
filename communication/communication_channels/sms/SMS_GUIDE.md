# SMS: Twilio pilot and simulator


> **File**: `communication/communication_channels/sms/SMS_GUIDE.md`
> **Audience**: Developers and pilot operators
> **Purpose**: Configure, operate, and validate SMS simulation and the Twilio owner pilot

For shared delivery boundaries, see [COMMUNICATION_GUIDE.md](../../COMMUNICATION_GUIDE.md). Browser/gateway deployment is covered by [WEBSITE_GUIDE.md](../../../website/WEBSITE_GUIDE.md), and health OAuth/sync setup by [GOOGLE_HEALTH_GUIDE.md](../../../integrations/google_health/GOOGLE_HEALTH_GUIDE.md).

Live SMS supports verified, consenting accounts with an active paid Discord + SMS plan.
The phone tier is $20 CAD/month and includes Discord; the $10 Discord tier does not include SMS. Test-mode Stripe subscriptions cannot unlock real SMS. Trial accounts can use Email or Discord. Complimentary, past-due, canceled, and trial accounts
cannot send SMS, even if an SMS preference was saved earlier.

## 1. Connect SMS

### 1.1. Operator configuration

Install the declared Twilio dependency in the project environment. Configure these
private `.env` fields, then restart MHM:

- `SMS_SIMULATION_ENABLED=false`
- `SMS_TWILIO_ENABLED=true`
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_PHONE_NUMBER`
- `SMS_PUBLIC_BASE_URL`: public HTTPS origin, with no path or query
- `SMS_WEBHOOK_PORT=8082`

Forward `/sms/incoming` and `/sms/status` on that origin to `http://127.0.0.1:8082`.
In Twilio's number configuration, set **A message comes in** to **POST**
`https://your-host/sms/incoming`. MHM supplies the status callback on each send.
Complete applicable Twilio sender/destination registration before enrolling users.
MHM and the HTTPS tunnel must remain running.

The former global pilot-account, pilot-phone, and pilot-consent settings are retired.
The existing owner's previously verified and approved phone/consent were migrated
into the account enrollment table. Billing eligibility is checked separately; migration
does not mark a complimentary account as paid.

### 1.2. Account connection

Website users can connect SMS in the first-run delivery step or Account > Delivery.
Desktop administrators can create new accounts with Email or Discord and use Channel Settings later.
After an active paid Discord + SMS plan is recorded, SMS becomes available in management
and in any unfinished website setup.

1. Enter the recipient's international mobile number and record explicit consent.
2. Select **Get connection code**.
3. From that phone, text the displayed `LINK <code>` to the MHM Twilio number.
4. Select **verify phone**. Website verification saves the enrollment immediately;
   desktop verification stages it until Channel Settings is saved.
5. Select SMS delivery and save. Connection alone does not redirect scheduled messages.

The code expires in 15 minutes, is phone/account-bound, and cannot be reused after
connection. Wait one minute before requesting another code. The server stores its
hash rather than the displayed secret. One phone can belong to only one account.
Disconnect SMS to revoke consent; opt-out and receipt history are retained. A stopped
number must send START to resume, even after reconnection.

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
Terminal outgoing details and completed inbound account attribution expire after 90 days during activity, export, or maintenance; unresolved records remain for review. Unlinked inbound IDs retain replay protection. Website exports include attributed records, and account deletion clears enrollments, contexts and account associations. A stopped number retains only a suppression digest after deletion. An operator status screen remains future work. Do not run two
live MHM instances against separate databases for the same Twilio account/number.

## 4. Simulation

Set `SMS_TWILIO_ENABLED=false`, `SMS_SIMULATION_ENABLED=true`, and restart.
Simulator tests explicitly disable live Twilio mode regardless of the host `.env`;
they must never start the live listener or contact the provider. The
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

Owner pilot evidence (2026-11-20): the connection test and `sms status` response
were delivered to the owner's phone. MHM accepted the signed inbound reply and
stored the signed delivery callbacks through the HTTPS tunnel. Scheduled reminders
remain on Discord. A later live task reminder accepted `done`, completed the labeled
test task, and cleared its reply context. STOP persisted the opt-out and blocked a
production-transport test before any Twilio API submission; START cleared it and
a final text received a delivered callback. The owner confirmed both provider
keyword confirmations. `start checkin` correctly refused a second completed
check-in that day, preserving history. A full SMS question/answer/save exchange
remains unverified until the next eligible check-in.

Before enrolling additional people, validate provider registration and live delivery for their destinations. Automated multi-account tests do not establish carrier delivery.

Run with the project environment active:

```powershell
python -m pytest tests/behavior/test_twilio_sms.py tests/behavior/test_sms_simulation.py -q
```
