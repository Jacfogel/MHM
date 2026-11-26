# Messaging schedules and account data controls

> **File**: `specs/messaging-quiet-hours-and-data-controls.md`
> **Last Updated**: 2026-11-25
> **Implementation**: `core/message_pressure.py`, `core/web_account_service.py`, `core/sms_enrollment.py`, `core/whatsapp_enrollment.py`, `core/web_sms.py`, `core/web_whatsapp.py`, `communication/core/channel_orchestrator.py`, `communication/reminders/reminder_dispatcher.py`, `communication/communication_channels/sms/twilio_transport.py`, `communication/communication_channels/whatsapp/transport.py`, `storage/user_data_backup.py`, `storage/sms_state.py`, `storage/whatsapp_state.py`
> **Automated tests**: `tests/unit/test_messaging_privacy_policy.py`, `tests/unit/test_web_account_service.py`, `tests/behavior/test_twilio_sms.py`, `tests/behavior/test_whatsapp.py`

## Purpose

Honor user-defined delivery schedules, prevent unsolicited channel switching, and include phone records in website account data controls.

## Requirements

- User-configured messages, check-ins and task reminders SHALL follow their saved schedules without automatic Night-to-Morning suppression. Phrases clocks SHALL remain parsing defaults. Explicit Support mode quiet controls and existing delivery eligibility checks SHALL remain independent.

- Disconnecting Discord SHALL clear its identity and recipient without selecting email or any other replacement. Disconnecting SMS or WhatsApp SHALL also preserve the selected delivery channel without choosing another. The channel preference SHALL remain Discord until the user explicitly chooses another channel; delivery remains unavailable while disconnected. Existing transport failure and unconfirmed results SHALL NOT trigger cross-channel resends.
- Website JSON exports SHALL include the account's attributed SMS/WhatsApp enrollments, delivery records, contexts, opt-out state and unexpired pending WhatsApp bodies, without other users' records or enrollment proof digests. Historical receipts lacking attribution SHALL NOT be guessed from a phone number or exported as another user's data.
- Account deletion SHALL revoke phone enrollment, remove challenges, pending bodies, sessions, contexts, recorded phone associations, attributed outgoing receipts and receipt ownership. It SHALL preserve unlinked inbound IDs to prevent replay. Stopped numbers SHALL retain only a number digest for suppression after deletion, until START clears it; this digest is pseudonymous, not anonymous.
- Failed storage cleanup or index removal SHALL NOT report successful account deletion. Website deletion SHALL not create a new backup. Existing backup expiry and provider-held copies SHALL be disclosed separately.
- Routine terminal outgoing records and completed inbound attribution SHALL expire after 90 days. Unresolved records SHALL remain for recovery. Inbound IDs SHALL remain for replay protection; active consent and opt-out protection SHALL not expire merely with receipt retention.
- Pending WhatsApp bodies SHALL expire after 24 hours; an existing pending table SHALL gain timestamps without discarding its rows. Expiry SHALL run before pending retrieval/export and during transport activity and scheduled maintenance.
- Existing user-created tasks, notes and check-in history SHALL remain until user/account deletion. Sent history SHALL retain the existing 365-day active-history archiving policy; archiving SHALL NOT be described as immediate deletion.

## Delivery recovery and setup retries

- Phone transports SHALL durably record an account-scoped submission attempt before calling the provider. A crash or timeout without a provider ID SHALL remain visible as unresolved and SHALL NOT trigger automatic replay.
- Submission-attempt records SHALL contain identifiers, timestamps, outcomes and attribution, never message bodies, tokens, credentials or phone numbers. Exports and deletion SHALL include the account's attempts. Resolved attempts SHALL follow phone delivery retention; unresolved attempts SHALL remain for review.
- Authenticated phone connection status SHALL report unresolved submission and inbound-processing counts for only the signed-in account, plus its current opt-out state. Connection controls SHALL show recovery guidance and SHALL NOT present acceptance as handset delivery.
- Retrying connection after a lost success response SHALL report the already verified connection without consuming a new proof or changing consent timestamps. It SHALL still require the same account/number, explicit consent, configured channel and current paid eligibility. It SHALL NOT reconnect a disconnected number or clear STOP.

## Manual test checklist

- Schedule messages, check-ins and task reminders during the saved Night-to-Morning interval and verify normal delivery eligibility; verify that an explicitly selected Support mode pause still works.
- Disconnect Discord and confirm no email is sent and Delivery permits explicitly choosing another eligible channel.
- On isolated test accounts, download phone records, delete one account and verify the other remains intact; retry an old inbound ID and confirm no command reruns.
- In setup or Delivery, refresh after a lost verification response and verify the saved connection is recognized. Confirm STOP remains visible and only START from the recipient clears it.
- With a mocked provider timeout, restart the test channel and verify its unresolved attempt remains visible only to its owning account; no automatic resend occurs.

## Related documentation

- [Communication guide](../communication/COMMUNICATION_GUIDE.md)
- [Website guide](../website/WEBSITE_GUIDE.md)
- [User data model](../core/USER_DATA_MODEL.md)
