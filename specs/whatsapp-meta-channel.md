# WhatsApp through Meta Cloud API

> **File**: `specs/whatsapp-meta-channel.md`
> **Last Updated**: 2026-11-23
> **Implementation**: `communication/communication_channels/whatsapp/`, `core/whatsapp_enrollment.py`, `core/web_whatsapp.py`, `storage/whatsapp_state.py`, `core/channel_access.py`, `core/billing.py`
> **Automated tests**: `tests/behavior/test_whatsapp.py`

## Purpose

Provide WhatsApp delivery and replies directly through Meta, with its own $20 CAD/month plan.

## Requirements

- WhatsApp SHALL be disabled by default and require operator credentials, a versioned Graph API, and a signed webhook. No Twilio calls SHALL be made.
- WhatsApp SHALL require an active, live-paid `whatsapp` subscription. SMS and Discord plans SHALL NOT grant WhatsApp; WhatsApp SHALL NOT grant SMS. Trials may use Email or Discord but remain ineligible for WhatsApp.
- Each account SHALL explicitly consent and prove its WhatsApp number by sending a single-use, account-bound LINK code to MHM. SMS enrollment SHALL NOT count as WhatsApp consent or proof.
- Inbound raw bodies SHALL be authenticated using the Meta app secret before parsing. Only the configured business account and receiving phone ID SHALL be processed. Webhook verification SHALL compare the configured verify token.
- Inbound IDs SHALL be claimed durably before commands run, including concurrent requests and restart. Uncertain outcomes SHALL require manual review, never automatic replay.
- STOP and START SHALL persist independently of SMS, including after paid access ends. Reconnection SHALL NOT erase an opt-out.
- Business actions SHALL use shared task/check-in/interaction handlers. Short replies SHALL require one unambiguous prompt context.
- Free-form text SHALL be sent only within 24 hours of the signed inbound message timestamp. Outside that window, an approved, parameterless notification template SHALL invite the recipient to reply OPEN. The original message SHALL be saved through storage and delivered after OPEN; task/check-in contexts SHALL attach when that text is submitted.
- Missing template configuration SHALL reject out-of-window sends before any provider submission. Templates SHALL NOT substitute arbitrary wellness content into an unrestricted placeholder.
- Provider acceptance SHALL be distinct from delivery. Network/server failures SHALL return unconfirmed with no automatic resend. Callbacks SHALL NOT regress delivery status.
- Website setup/account delivery and desktop Channel Settings SHALL offer separate WhatsApp connection, selection, and disconnection. Disconnecting SHALL revoke enrollment and pending messages while retaining receipt/opt-out history.

### Requirement: Paid delivery during website setup

- Delivery SHALL offer horizontal channel cards with Email selected by default and Discord highlighted as Recommended. Connection and subscription controls SHALL appear on the subsequent Connect step for Discord, SMS, or WhatsApp; Email SHALL proceed directly to feature setup.
- Feature-specific setup progress steps SHALL remain hidden until Features is reached. SMS or WhatsApp selection SHALL omit the Free trial step from progress and the setup flow; Email and Discord SHALL show a 30-day free trial note.
- SMS and WhatsApp phone fields and consent controls SHALL be disabled and visually muted until the matching paid subscription is eligible and enrollment is available. Refresh SHALL recheck eligibility and enable these controls when access becomes available. They SHALL reject invalid international formats and missing consent before submitting enrollment, strip display punctuation, and convert an explicit 00 international prefix to +. Requests SHALL use the canonical +country-code-and-digits format. Server-side eligibility, consent, and ownership verification SHALL remain required.
- Selecting an unpaid phone channel SHALL offer its matching subscription with an explicit immediate $20 CAD/month charge. Checkout SHALL return to the selected setup channel without completing setup. Verification and live-paid access SHALL remain required before saving phone delivery.
- A missing enrollment route SHALL show recovery guidance and a refresh action rather than raw server errors. Setup transitions SHALL preserve unavailable enrollment controls.

## Manual test checklist

- Configure Meta credentials and public webhook; verify challenge and a signed event.
- Connect from the recipient phone, choose WhatsApp, and send a test message.
- Validate a task reply, check-in save, STOP/START, and delivery/read callbacks.
- After the conversation window expires, confirm the approved notification and OPEN delivery.
- Verify plan switching disables the former channel without deleting user data.

## Related documentation

- [WhatsApp setup](../communication/communication_channels/whatsapp/WHATSAPP_GUIDE.md)
- [Communication architecture](../communication/COMMUNICATION_GUIDE.md)
